"""
News Controller & FastAPI Router
================================
Provides legal news endpoints for HALO.
Endpoints:
- GET /news/legal: Fetch latest Indian legal news, court cases, and judgments.
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Query
from app.news.service import get_indian_legal_news

router = APIRouter(prefix="/news", tags=["news"])


@router.get("/legal")
def api_get_indian_legal_news(
    query: Optional[str] = Query(None, description="Optional search keyword, e.g. 'SEBI', 'Supreme Court', 'Bail'"),
    limit: int = Query(5, ge=1, le=20, description="Max articles to return")
) -> Dict[str, Any]:
    """Returns top legal news and court case updates across India."""
    articles = get_indian_legal_news(query=query or "", limit=limit)
    return {
        "status": "ok",
        "query": query or "",
        "count": len(articles),
        "articles": articles
    }

