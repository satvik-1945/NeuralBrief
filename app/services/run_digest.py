"""
Digest Service: Reads raw content from DB, runs DigestAgent, writes to digested_content.
Run after scraper. No DB access for curator/email.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import List, Tuple

from sqlalchemy import select

from app.agent.config import SCRAPE_WINDOW_HOURS, YOUTUBE_CHANNEL_NAMES
from app.agent.digest_agent import DigestAgent
from app.database import (
    ArticleRecord,
    DigestedContentRepository,
    SessionLocal,
    YouTubeVideo,
    init_db,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def _make_summary_fallback(text: str, max_chars: int = 400) -> str:
    """Fallback when OpenAI is unavailable."""
    text = (text or "").strip()
    if not text:
        return ""
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3].rstrip() + "..."


def _fetch_raw_content(hours: int) -> Tuple[List[dict], List[Tuple[str, int]]]:
    """
    Fetch articles and videos from DB within time window.
    Returns (payloads for DigestAgent, list of (content_type, source_id) in order).
    """
    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    db = SessionLocal()

    try:
        payloads: List[dict] = []
        order: List[Tuple[str, int]] = []

        stmt_articles = (
            select(ArticleRecord)
            .where(ArticleRecord.published_at >= since)
            .order_by(ArticleRecord.published_at.desc())
        )
        articles = list(db.execute(stmt_articles).scalars().all())

        for a in articles:
            payloads.append(
                {
                    "id": a.id,
                    "title": a.title,
                    "content": a.content_text or a.markdown or a.description or "",
                    "url": a.url,
                    "section": a.section,
                    "article_type": "article",
                    "author": a.author,
                    "published_at": a.published_at,
                }
            )
            order.append(("article", a.id))

        stmt_videos = (
            select(YouTubeVideo)
            .where(YouTubeVideo.published_at >= since)
            .order_by(YouTubeVideo.published_at.desc())
        )
        videos = list(db.execute(stmt_videos).scalars().all())

        for v in videos:
            payloads.append(
                {
                    "id": v.id,
                    "title": v.title,
                    "content": v.transcript or v.description or "",
                    "url": v.url,
                    "section": None,
                    "article_type": "video",
                    "author": YOUTUBE_CHANNEL_NAMES.get(v.channel_id or "", "YouTube"),
                    "published_at": v.published_at,
                }
            )
            order.append(("video", v.id))

        return payloads, order
    finally:
        db.close()


def run_digest(hours: int | None = None) -> int:
    """
    Fetch raw content from DB, run DigestAgent, write to digested_content.
    Returns count of items upserted.
    """
    window_hours = hours or SCRAPE_WINDOW_HOURS
    init_db()
    db = SessionLocal()

    try:
        payloads, order = _fetch_raw_content(window_hours)
        if not payloads:
            logger.info("No raw content to digest")
            return 0

        logger.info(
            "Processing %d items (%d articles, %d videos) with DigestAgent",
            len(payloads),
            sum(1 for p in payloads if p.get("article_type") == "article"),
            sum(1 for p in payloads if p.get("article_type") == "video"),
        )

        agent = DigestAgent()
        result = agent.generate_digests_batch(payloads)

        digest_repo = DigestedContentRepository(db)
        count = 0

        for i, (ct, source_id) in enumerate(order):
            if i >= len(payloads):
                break
            p = payloads[i]
            source_type = "article" if ct == "article" else "video"
            title = p["title"]
            url = p["url"]
            author = p.get("author")
            section = p.get("section")
            published_at = p.get("published_at")

            if result and result.digests and i < len(result.digests):
                entry = result.digests[i]
                summary = entry.summary
                title = entry.title
            else:
                summary = _make_summary_fallback(p.get("content", ""))

            digest_repo.upsert(
                source_type=source_type,
                source_id=source_id,
                title=title,
                summary=summary,
                url=url,
                author=author,
                section=section,
                published_at=published_at,
            )
            count += 1

        logger.info("Upserted %d digests to digested_content", count)
        return count
    finally:
        db.close()


if __name__ == "__main__":
    run_digest(hours=SCRAPE_WINDOW_HOURS)
