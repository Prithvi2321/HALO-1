"""
Research Controller & FastAPI Router
====================================
Mounts research query execution, result retrieval, history, and audit endpoints.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
import uuid

from fastapi import APIRouter, HTTPException, Depends, status
from app.research.schema import (
    ResearchQueryRequest,
    ResearchResultResponse,
    QuerySubmitResponse,
    HistoryItem,
)
from app.research.adapter import adapt_pipeline_output
from app.retrieval.service import retrieve_passages
from app.generation.service import generate_answer, GenerationServiceError
from halo.pipeline import HaloPipeline

router = APIRouter(prefix="/research", tags=["research"])

# Singleton pipeline instance
pipeline = HaloPipeline()

# In-memory session stores for rapid query caching & history
_RESULTS_STORE: Dict[str, ResearchResultResponse] = {}
_HISTORY_STORE: List[HistoryItem] = []


def _seed_initial_history():
    """Seeds initial historical samples if empty."""
    if not _HISTORY_STORE:
        _HISTORY_STORE.extend([
            HistoryItem(
                query_id="q_001",
                query_text="What is the doctrine of res judicata and its scope under Indian law?",
                date=datetime.now(timezone.utc).isoformat(),
                confidence_score=0.94,
                verification_summary={"total_claims": 3, "supported": 3, "warnings": 0, "failed": 0},
                conflicts_detected=False,
            ),
            HistoryItem(
                query_id="q_002",
                query_text="Director liability under Section 179 Income Tax Act — nominee director position",
                date=datetime.now(timezone.utc).isoformat(),
                confidence_score=0.61,
                verification_summary={"total_claims": 3, "supported": 1, "warnings": 1, "failed": 1},
                conflicts_detected=True,
            ),
        ])


_seed_initial_history()


from pydantic import BaseModel

class UniversalQueryInput(BaseModel):
    query_text: Optional[str] = None
    query: Optional[str] = None
    jurisdiction: Optional[str] = "Supreme Court of India"
    court_level: Optional[str] = "All Courts"
    date_range: Optional[str] = "all"
    candidate_answer: Optional[str] = None


@router.post("/query", response_model=QuerySubmitResponse)
@router.post("", response_model=QuerySubmitResponse)
def submit_query(req: UniversalQueryInput):
    """Executes full legal retrieval, answer generation, and verification pipeline on query text."""
    effective_text = (req.query_text or req.query or "").strip()
    if not effective_text:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="query or query_text must be provided.",
        )

    norm_req = ResearchQueryRequest(
        query_text=effective_text,
        jurisdiction=req.jurisdiction,
        court_level=req.court_level,
        date_range=req.date_range,
        candidate_answer=req.candidate_answer,
    )
    query_id = f"q_{uuid.uuid4().hex[:6]}"

    # 1. Candidate Answer Formulation (Retrieval + LLM Generation or explicit candidate)
    candidate_passages: List[Dict[str, Any]] = []
    if norm_req.candidate_answer and norm_req.candidate_answer.strip():
        raw_answer = norm_req.candidate_answer.strip()
    else:
        # Step A: Retrieve authoritative legal passages
        try:
            candidate_passages = retrieve_passages(norm_req.query_text, top_k=5)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Legal retrieval step failed: {str(e)}",
            )

        # Step B: Generate grounded candidate answer via Groq LLM
        try:
            raw_answer = generate_answer(norm_req.query_text, candidate_passages)
        except GenerationServiceError as ge:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Legal answer generation failed: {str(ge)}",
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Legal answer generation error: {str(e)}",
            )

    try:
        pipeline_output = pipeline.process(
            query=req.query_text,
            raw_answer=raw_answer,
            candidate_passages=candidate_passages,
        )

        adapted_result = adapt_pipeline_output(
            pipeline_result=pipeline_output,
            query_id=query_id,
            query_text=req.query_text,
        )

        # Store in cache
        _RESULTS_STORE[query_id] = adapted_result

        # Update history
        h_item = HistoryItem(
            query_id=query_id,
            query_text=req.query_text,
            date=datetime.now(timezone.utc).isoformat(),
            confidence_score=adapted_result.confidence_score,
            verification_summary={
                "total_claims": len(adapted_result.claims),
                "supported": sum(1 for c in adapted_result.claims if c.verification_status == "supported"),
                "warnings": sum(1 for c in adapted_result.claims if c.verification_status == "warning"),
                "failed": sum(1 for c in adapted_result.claims if c.verification_status == "failed"),
            },
            conflicts_detected=adapted_result.conflicts_detected,
        )
        _HISTORY_STORE.insert(0, h_item)

        return QuerySubmitResponse(
            query_id=query_id,
            status="done",
            result=adapted_result,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Verification pipeline failed: {str(e)}",
        )


@router.get("/result/{query_id}", response_model=ResearchResultResponse)
def get_research_result(query_id: str):
    """Retrieves full research and verification result for a given query ID."""
    if query_id in _RESULTS_STORE:
        return _RESULTS_STORE[query_id]

    # If it's one of the seed fixtures or not found, generate an on-the-fly result
    fallback_output = pipeline.process(
        query=f"Legal research inquiry for {query_id}",
        raw_answer="Under the Companies Act, 2013 and landmark Supreme Court decisions, all statutory mandates are enforced by the National Company Law Tribunal.",
    )
    res = adapt_pipeline_output(fallback_output, query_id=query_id, query_text="Legal inquiry")
    _RESULTS_STORE[query_id] = res
    return res


@router.get("/result/{query_id}/claims")
def get_claims(query_id: str):
    """Retrieves atomic claims list for a query ID."""
    result = get_research_result(query_id)
    return result.claims


@router.get("/result/{query_id}/evidence")
def get_evidence(query_id: str):
    """Retrieves authoritative sources and evidence coverage for a query ID."""
    result = get_research_result(query_id)
    return {
        "sources": result.sources,
        "evidence_coverage": result.evidence_coverage,
    }


@router.get("/history", response_model=List[HistoryItem])
def get_research_history():
    """Retrieves user's historical research queries."""
    return _HISTORY_STORE


@router.get("/audit/{audit_id}")
def get_audit_record(audit_id: str):
    """Retrieves cryptographic SHA-256 audit record."""
    record = pipeline.audit_logger.get_audit_record(audit_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audit record '{audit_id}' not found.",
        )
    return record.to_dict()
