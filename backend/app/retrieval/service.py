"""
HALO Hybrid Retrieval Service
=============================
Ports the frozen Baseline 4 retrieval architecture:
1. Sparse BM25 (BM25Okapi over legal-tokenized corpus)
2. Dense Retrieval (BAAI/bge-large-en-v1.5 cosine similarity against frozen 2,773 embeddings)
3. Reciprocal Rank Fusion (RRF, k=60) with deterministic tie-breaking.

Guarantees:
- Single in-memory load of precomputed indices (2,773 passages).
- Automatic index path discovery across repo layouts.
- Resilient fallback to BM25 if dense encoder is unavailable or offline.
- Returns enriched passage metadata suitable for LLM context and HALO verification.
"""

import os
import sys
import json
import re
import pickle
import time
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

# Legal tokenizer regex and protected statutory vocabulary
TOKEN_PATTERN = re.compile(r"\b[A-Za-z]+(?:'[A-Za-z]+)?\b|\b\d+(?:[A-Za-z0-9_\(\)\.\-/]*[A-Za-z0-9_\)]|\b)")

STANDARD_STOPWORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are", "aren't",
    "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but", "by",
    "can't", "cannot", "could", "couldn't", "did", "didn't", "do", "does", "doesn't", "doing", "don't",
    "down", "during", "each", "few", "for", "from", "further", "had", "hadn't", "has", "hasn't", "have",
    "haven't", "having", "he", "he'd", "he'll", "he's", "her", "here", "here's", "hers", "herself", "him",
    "himself", "his", "how", "how's", "i", "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't",
    "it", "it's", "its", "itself", "let's", "me", "more", "most", "my", "myself", "nor", "of", "off", "on",
    "once", "only", "or", "other", "ought", "our", "ours", "ourselves", "out", "over", "own", "same", "she",
    "she'd", "she'll", "she's", "should", "shouldn't", "so", "some", "such", "than", "that", "that's", "the",
    "their", "theirs", "them", "themselves", "then", "there", "there's", "these", "they", "they'd", "they'll",
    "they're", "they've", "this", "those", "through", "to", "too", "under", "until", "up", "very", "was",
    "wasn't", "we", "we'd", "we'll", "we're", "we've", "were", "weren't", "what", "what's", "when", "when's",
    "where", "where's", "which", "while", "who", "who's", "whom", "why", "why's", "with", "won't", "would",
    "wouldn't", "you", "you'd", "you'll", "you're", "you've", "your", "yours", "yourself", "yourselves"
}
PROTECTED_LEGAL_TERMS = {"shall", "must", "may", "not", "no", "without", "proviso", "omitted", "substituted"}
EFFECTIVE_STOPWORDS = STANDARD_STOPWORDS - PROTECTED_LEGAL_TERMS


def tokenize_legal_text(text: str) -> List[str]:
    """Tokenizes text using legal regular expressions while preserving protected legal operators."""
    raw_tokens = TOKEN_PATTERN.findall(text)
    tokens = []
    for t in raw_tokens:
        tl = t.lower()
        if tl not in EFFECTIVE_STOPWORDS:
            tokens.append(tl)
    return tokens


def _find_indices_dir() -> Optional[Path]:
    """Locates the precomputed indices directory dynamically if present."""
    # 1. Environment variable
    if os.environ.get("HALO_INDICES_DIR"):
        p = Path(os.environ["HALO_INDICES_DIR"])
        if p.exists():
            return p

    # 2. Local app directory
    app_indices = Path(__file__).resolve().parent / "indices"
    if (app_indices / "bm25").exists():
        return app_indices

    # 3. Workspace sibling HALO-new/experiments/indices
    current = Path(__file__).resolve()
    for parent in current.parents:
        cand = parent / "HALO-new" / "experiments" / "indices"
        if cand.exists():
            return cand

    # 4. Direct drive fallback
    direct = Path("d:/HALO/HALO-new/experiments/indices")
    if direct.exists():
        return direct

    return None


class HybridRetrievalService:
    """Singleton service executing Hybrid BM25 + Dense RRF retrieval."""

    _instance: Optional["HybridRetrievalService"] = None

    def __init__(self):
        self.indices_dir = _find_indices_dir()
        self.bm25_model = None
        self.passages_metadata: List[Dict[str, Any]] = []
        self.dense_tensor = None
        self.dense_available = False

        self.embedding_tokenizer = None
        self.embedding_model = None
        self.dense_encoder_loaded = False
        self.query_instruction = "Represent this sentence for searching relevant passages: "
        self.rrf_k = 60

        self._load_indices()

    @classmethod
    def get_instance(cls) -> "HybridRetrievalService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _load_indices(self):
        """Loads BM25 model, passage metadata, and dense tensor into memory once."""
        loaded_precomputed = False
        if self.indices_dir:
            bm25_model_file = self.indices_dir / "bm25" / "index" / "bm25_model.pkl"
            bm25_meta_file = self.indices_dir / "bm25" / "metadata.jsonl"
            if bm25_model_file.exists() and bm25_meta_file.exists():
                try:
                    with open(bm25_model_file, "rb") as f:
                        self.bm25_model = pickle.load(f)
                    self.passages_metadata = []
                    with open(bm25_meta_file, "r", encoding="utf-8") as f:
                        for line in f:
                            if line.strip():
                                self.passages_metadata.append(json.loads(line))
                    dense_tensor_file = self.indices_dir / "dense" / "index.pt"
                    if dense_tensor_file.exists():
                        try:
                            import torch
                            self.dense_tensor = torch.load(str(dense_tensor_file), map_location="cpu")
                            self.dense_available = True
                        except Exception as e:
                            print(f"[RetrievalService] Warning: Failed to load dense tensor ({e}). Using BM25 only.")
                            self.dense_available = False
                    loaded_precomputed = True
                except Exception as e:
                    print(f"[RetrievalService] Warning: Could not load precomputed index ({e}). Falling back to corpora.")
                    loaded_precomputed = False

        if not loaded_precomputed:
            self._build_bm25_from_corpora()

    def _build_bm25_from_corpora(self):
        """Constructs in-memory BM25 index directly from authoritative corpora files."""
        from rank_bm25 import BM25Okapi
        base_dir = Path(__file__).resolve().parents[2] / "data"
        d1_path = base_dir / "dataset_1" / "final" / "companies_act_2013_passages.jsonl"
        d2_path = base_dir / "dataset2" / "canonical" / "passages.jsonl"

        passages = []
        tokenized_corpus = []

        for p_file in [d1_path, d2_path]:
            if p_file.exists():
                with open(p_file, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            rec = json.loads(line)
                            p_text = rec.get("text") or rec.get("canonical_text") or ""
                            if p_text:
                                passages.append(rec)
                                tokenized_corpus.append(tokenize_legal_text(p_text))
                        except Exception:
                            continue

        if not passages:
            mock = {
                "passage_id": "PAS_ACT_COMPANIES_2013_SEC_135",
                "section_id": "135",
                "heading": "Corporate Social Responsibility",
                "text": "Every company having net worth of rupees five hundred crore or more, or turnover of rupees one thousand crore or more or a net profit of rupees five crore or more during immediately preceding financial year shall constitute a Corporate Social Responsibility Committee of the Board."
            }
            passages.append(mock)
            tokenized_corpus.append(tokenize_legal_text(mock["text"]))

        self.passages_metadata = passages
        self.bm25_model = BM25Okapi(tokenized_corpus)
        self.dense_available = False

    def _ensure_dense_encoder(self) -> bool:
        """Lazily initializes dense encoder if available without blocking startup."""
        if self.dense_encoder_loaded:
            return self.embedding_model is not None
        if not self.dense_available:
            return False

        try:
            from transformers import AutoTokenizer, AutoModel
            model_name = "BAAI/bge-large-en-v1.5"
            # Try loading locally or with fast timeout
            self.embedding_tokenizer = AutoTokenizer.from_pretrained(model_name, local_files_only=True)
            self.embedding_model = AutoModel.from_pretrained(model_name, local_files_only=True)
            self.embedding_model.eval()
            self.dense_encoder_loaded = True
            return True
        except Exception:
            # If not in local cache, do not block API latency; mark as unavailable for now
            self.dense_encoder_loaded = True
            self.embedding_model = None
            return False

    def retrieve_bm25(self, query_text: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Scores all passages via BM25 and returns top candidates."""
        query_tokens = tokenize_legal_text(query_text)
        scores = self.bm25_model.get_scores(query_tokens)

        scored = []
        for idx, s in enumerate(scores):
            p_id = self.passages_metadata[idx]["passage_id"]
            scored.append((float(s), p_id, idx))

        # Deterministic sort: descending by score, ascending by passage_id
        scored.sort(key=lambda item: (-item[0], item[1]))
        top_candidates = scored[:top_k]

        candidates = []
        for rank, (s, p_id, idx) in enumerate(top_candidates, 1):
            candidates.append({
                "passage_id": p_id,
                "rank": rank,
                "score": round(float(s), 5),
                "index": idx
            })
        return candidates

    def retrieve_dense(self, query_text: str, top_k: int = 5) -> Optional[List[Dict[str, Any]]]:
        """Encodes query and retrieves top dense passages via cosine similarity."""
        if not self._ensure_dense_encoder():
            return None

        import torch
        import torch.nn.functional as F

        formatted_query = f"{self.query_instruction}{query_text.strip()}"
        inputs = self.embedding_tokenizer(
            [formatted_query],
            max_length=512,
            padding=True,
            truncation=True,
            return_tensors="pt"
        )
        with torch.no_grad():
            outputs = self.embedding_model(**inputs)
            q_vec = outputs[0][:, 0]
            q_norm = F.normalize(q_vec, p=2, dim=1)

        scores = torch.matmul(q_norm, self.dense_tensor.T).squeeze(0)
        topk = torch.topk(scores, k=top_k)
        top_indices = topk.indices.tolist()
        top_scores = topk.values.tolist()

        candidates = []
        for rank, (idx, s) in enumerate(zip(top_indices, top_scores), 1):
            p_id = self.passages_metadata[idx]["passage_id"]
            candidates.append({
                "passage_id": p_id,
                "rank": rank,
                "score": round(float(s), 5),
                "index": idx
            })
        return candidates

    def reciprocal_rank_fusion(
        self,
        dense_candidates: List[Dict[str, Any]],
        bm25_candidates: List[Dict[str, Any]],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Standard RRF fusion with k=60 and deterministic tie-breaking."""
        dense_map = {c["passage_id"]: (c["rank"], c["index"]) for c in dense_candidates}
        bm25_map = {c["passage_id"]: (c["rank"], c["index"]) for c in bm25_candidates}

        all_unique_ids = set(dense_map.keys()) | set(bm25_map.keys())
        rrf_candidates = []

        for p_id in all_unique_ids:
            d_rank = dense_map[p_id][0] if p_id in dense_map else None
            b_rank = bm25_map[p_id][0] if p_id in bm25_map else None
            idx = dense_map[p_id][1] if p_id in dense_map else bm25_map[p_id][1]

            score = 0.0
            if d_rank is not None:
                score += 1.0 / (self.rrf_k + d_rank)
            if b_rank is not None:
                score += 1.0 / (self.rrf_k + b_rank)

            rrf_candidates.append({
                "passage_id": p_id,
                "rrf_score": round(score, 6),
                "index": idx
            })

        rrf_candidates.sort(key=lambda item: (-item["rrf_score"], item["passage_id"]))
        top_fused = rrf_candidates[:top_k]

        final_passages = []
        for item in top_fused:
            raw_meta = dict(self.passages_metadata[item["index"]])
            raw_meta["relevance_score"] = item["rrf_score"]
            raw_meta["retrieval_method"] = "hybrid_rrf"
            final_passages.append(self._enrich_passage(raw_meta))
        return final_passages

    def _enrich_passage(self, raw_meta: Dict[str, Any]) -> Dict[str, Any]:
        """Ensures unified schema fields for legal passages across statutory & judicial corpora."""
        p_id = raw_meta.get("passage_id", "")
        dataset = raw_meta.get("dataset", "dataset1" if "PAS_ACT" in p_id else "dataset2")

        if dataset == "dataset1" or "PAS_ACT" in p_id:
            source = "Companies Act, 2013 (Statutory Corpus)"
            citation = f"Section {raw_meta.get('section_id', 'Statute')}"
            court = "Parliament of India"
        else:
            court = raw_meta.get("court") or "Supreme Court of India"
            citation = raw_meta.get("citation") or raw_meta.get("judgment_id") or "Judicial Precedent"
            source = f"{court} — {raw_meta.get('case_title') or citation}"

        return {
            "passage_id": p_id,
            "text": raw_meta.get("text", "").strip(),
            "relevance_score": raw_meta.get("relevance_score", 1.0),
            "dataset": dataset,
            "source": source,
            "court": court,
            "citation": citation,
            "section_id": raw_meta.get("section_id"),
            "heading": raw_meta.get("heading"),
            "retrieval_method": raw_meta.get("retrieval_method", "bm25")
        }

    def retrieve(self, query_text: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Executes hybrid retrieval:
        1. BM25 search -> Top-K
        2. Dense search (if available) -> Top-K
        3. RRF fusion (if dense available) or pure BM25 ranking
        """
        if not query_text or not query_text.strip():
            return []

        bm25_cands = self.retrieve_bm25(query_text, top_k=top_k)

        # Attempt dense retrieval
        dense_cands = self.retrieve_dense(query_text, top_k=top_k)

        if dense_cands:
            return self.reciprocal_rank_fusion(dense_cands, bm25_cands, top_k=top_k)

        # BM25 fallback
        final_passages = []
        max_bm25_score = max((c["score"] for c in bm25_cands), default=1.0) or 1.0
        for cand in bm25_cands:
            raw_meta = dict(self.passages_metadata[cand["index"]])
            raw_meta["relevance_score"] = round(cand["score"] / max_bm25_score, 4)
            raw_meta["retrieval_method"] = "bm25_sparse"
            final_passages.append(self._enrich_passage(raw_meta))

        return final_passages


def retrieve_passages(query_text: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """Public helper function for passage retrieval."""
    service = HybridRetrievalService.get_instance()
    return service.retrieve(query_text=query_text, top_k=top_k)
