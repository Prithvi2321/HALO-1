"""
HALO Verification & Research Seams
===================================
Protocol: v2.1 PRD §13
Defines the clean boundary between practice management / drafting
and the verified HALO RAG & Verification core.
"""

from typing import Protocol, List, Dict, Any, Optional
from pydantic import BaseModel, Field


class ClauseInput(BaseModel):
    clause_id: str
    clause_text: str
    category: Optional[str] = None
    statutory_anchor: Optional[str] = None


class ClauseVerificationResult(BaseModel):
    clause_id: str
    status: str = "NOT_VERIFIED"  # "VERIFIED" | "WARNING" | "QUARANTINED" | "NOT_VERIFIED"
    confidence_score: float = 0.0
    evidence_coverage: float = 0.0
    statutory_anchor: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)
    explanation: str = "Verification pending RAG integration seam."


class VerificationReport(BaseModel):
    template_id: Optional[str] = None
    overall_status: str = "NOT_VERIFIED"
    verified_clauses_count: int = 0
    total_clauses: int = 0
    clauses: List[ClauseVerificationResult] = Field(default_factory=list)
    timestamp: Optional[str] = None


class VerifiedAnswerDTO(BaseModel):
    query_id: str
    query_text: str
    answer_text: str
    confidence_score: float
    evidence_coverage: float
    verification_status: str
    claims: List[Dict[str, Any]] = Field(default_factory=list)
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    conflicts_detected: bool = False


class VerificationPort(Protocol):
    """Port for verifying legal drafting clauses against authoritative corpora."""
    def verify_clauses(self, clauses: List[ClauseInput], *, anchor: Optional[str] = None) -> VerificationReport:
        ...


class ResearchPort(Protocol):
    """Port for querying the verified RAG pipeline."""
    def ask(self, query: str, *, user_id: str, filters: Optional[Dict[str, Any]] = None) -> VerifiedAnswerDTO:
        ...


class StubVerificationAdapter:
    """Default stub implementation before Phase 5 RAG wiring."""
    def verify_clauses(self, clauses: List[ClauseInput], *, anchor: Optional[str] = None) -> VerificationReport:
        results = []
        for c in clauses:
            results.append(
                ClauseVerificationResult(
                    clause_id=c.clause_id,
                    status="NOT_VERIFIED",
                    confidence_score=0.0,
                    evidence_coverage=0.0,
                    statutory_anchor=anchor or c.statutory_anchor,
                    warnings=[],
                    explanation="Verification pending RAG integration."
                )
            )
        return VerificationReport(
            overall_status="NOT_VERIFIED",
            verified_clauses_count=0,
            total_clauses=len(clauses),
            clauses=results
        )


class StubResearchAdapter:
    """Default stub implementation before Phase 5 Telegram RAG wiring."""
    def ask(self, query: str, *, user_id: str, filters: Optional[Dict[str, Any]] = None) -> VerifiedAnswerDTO:
        return VerifiedAnswerDTO(
            query_id="stub_query",
            query_text=query,
            answer_text="Legal research via Telegram is coming soon.",
            confidence_score=0.0,
            evidence_coverage=0.0,
            verification_status="PENDING",
            claims=[],
            sources=[],
            conflicts_detected=False
        )


# Singleton instances
verification_port: VerificationPort = StubVerificationAdapter()
research_port: ResearchPort = StubResearchAdapter()

