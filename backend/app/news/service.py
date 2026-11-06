"""
Indian Legal News Service
=========================
Fetches live legal news and court case updates across Indian jurisdictions
(Supreme Court, High Courts, Tribunals, SEBI, NCLT, etc.).

Supports:
1. NewsAPI.org if NEWS_API_KEY is configured in environment / .env
2. High-reliability fallback to Google News India Legal RSS (Zero API key required)
"""

import os
import re
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
import httpx

load_dotenv()


def _clean_text(text: Optional[str]) -> str:
    """Removes HTML entities and tags."""
    if not text:
        return ""
    # Strip HTML tags
    clean = re.sub(r"<[^>]+>", "", text)
    # Normalize whitespace
    return " ".join(clean.split())


def _format_date(pub_date_str: str) -> str:
    """Formats standard RSS or ISO date to clean readable string."""
    if not pub_date_str:
        return ""
    try:
        # e.g., 'Wed, 04 Nov 2026 10:00:01 GMT'
        dt = datetime.strptime(pub_date_str[:25].strip(), "%a, %d %b %Y %H:%M:%S")
        return dt.strftime("%d %b %Y")
    except Exception:
        try:
            # ISO 8601 e.g. 2026-11-04T10:00:00Z
            dt = datetime.fromisoformat(pub_date_str.replace("Z", "+00:00"))
            return dt.strftime("%d %b %Y")
        except Exception:
            return pub_date_str[:16]


def fetch_from_newsapi(query: str, api_key: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Fetches articles using NewsAPI.org focused on Indian court and legal matters."""
    if query:
        search_q = f"({query}) AND (court OR legal OR judgment OR law OR tribunal OR bail) AND India"
    else:
        search_q = '(Supreme Court OR High Court OR "court case" OR judgment OR tribunal) AND India'

    url = "https://newsapi.org/v2/everything"
    params = {
        "q": search_q,
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": limit,
        "apiKey": api_key,
    }
    with httpx.Client(timeout=8.0) as client:
        resp = client.get(url, params=params)
        if resp.status_code != 200:
            return []
        data = resp.json()
        articles = data.get("articles", [])
        results = []
        for a in articles[:limit]:
            results.append({
                "title": _clean_text(a.get("title")),
                "source": a.get("source", {}).get("name") or "NewsAPI India",
                "link": a.get("url") or "",
                "published_at": _format_date(a.get("publishedAt", "")),
                "description": _clean_text(a.get("description", ""))[:140],
            })
        return results


def fetch_from_indian_legal_rss(query: str = "", limit: int = 5) -> List[Dict[str, Any]]:
    """
    Fetches real-time Indian legal news from Google News India legal feed.
    No API key required; covers LiveLaw, Bar & Bench, SCC Online, etc.
    """
    if query:
        search_query = f"{query} India (Supreme Court OR High Court OR judgment OR tribunal)"
    else:
        search_query = "Supreme Court High Court India legal cases judgments"

    encoded = urllib.parse.quote_plus(search_query)
    rss_url = f"https://news.google.com/rss/search?q={encoded}&hl=en-IN&gl=IN&ceid=IN:en"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    with httpx.Client(timeout=10.0, follow_redirects=True) as client:
        resp = client.get(rss_url, headers=headers)
        if resp.status_code != 200:
            return []
        root = ET.fromstring(resp.content)
        items = root.findall(".//item")
        results = []
        for item in items[:limit]:
            raw_title = item.find("title").text if item.find("title") is not None else "Legal Update"
            link = item.find("link").text if item.find("link") is not None else ""
            pub_date = item.find("pubDate").text if item.find("pubDate") is not None else ""
            source_elem = item.find("source")
            source_name = source_elem.text if source_elem is not None and source_elem.text else "Indian Legal News"

            # Clean publisher from title if title is "Headline - Publisher"
            clean_title = _clean_text(raw_title)
            if " - " in clean_title:
                clean_title = clean_title.rsplit(" - ", 1)[0].strip()

            results.append({
                "title": clean_title,
                "source": source_name,
                "link": link,
                "published_at": _format_date(pub_date),
                "description": "",
            })
        return results


def get_indian_legal_news(query: str = "", limit: int = 5) -> List[Dict[str, Any]]:
    """
    Primary legal news fetcher. Checks for NEWS_API_KEY first; falls back
    to Google News India RSS.
    """
    load_dotenv(override=True)
    api_key = os.environ.get("NEWS_API_KEY", "").strip()
    if api_key:
        try:
            articles = fetch_from_newsapi(query, api_key, limit=limit)
            if articles:
                return articles
        except Exception:
            pass  # Fallback to RSS

    try:
        return fetch_from_indian_legal_rss(query, limit=limit)
    except Exception as exc:
        return []


def format_news_for_telegram(articles: List[Dict[str, Any]], query: str = "") -> str:
    """Formats articles for clean Telegram Markdown display."""
    if not articles:
        topic_suffix = f" for *'{query}'*" if query else ""
        return (
            f"📰 *Indian Legal News*\n\n"
            f"No recent news articles found{topic_suffix}. Try another topic like:\n"
            f"`/news supreme court`\n"
            f"`/news sebi`\n"
            f"`/news bail`\n"
            f"`/news arbitration`"
        )

    header = f"📰 *Indian Legal News — '{query.title()}'*" if query else "📰 *Latest Indian Legal & Court Case News*"
    lines = [header, ""]

    for idx, art in enumerate(articles, 1):
        title = art.get("title", "Legal Update")
        source = art.get("source", "Legal Source")
        date_str = art.get("published_at", "")
        link = art.get("link", "")

        meta = f"_{source}_"
        if date_str:
            meta += f" • {date_str}"

        lines.append(f"*{idx}\\. {title}*")
        lines.append(f"   {meta}")
        if link:
            lines.append(f"   [Read Article]({link})")
        lines.append("")

    lines.append("💡 _Tip: Search specific topics with `/news <topic>` (e.g. `/news sebi`, `/news nclt`, `/news bail`)_")
    return "\n".join(lines)

