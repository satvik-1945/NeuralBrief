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


DIGEST_ARTICLE_BATCH_SIZE = 50
DIGEST_VIDEO_BATCH_SIZE = 20


def _fetch_articles_batch(
    db, since: datetime, limit: int, offset: int
) -> Tuple[List[dict], List[Tuple[str, int]]]:
    """Fetch a batch of articles for digest."""
    stmt = (
        select(ArticleRecord)
        .where(ArticleRecord.published_at >= since)
        .order_by(ArticleRecord.published_at.desc())
        .limit(limit)
        .offset(offset)
    )
    articles = list(db.execute(stmt).scalars().all())
    payloads = []
    order = []
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
    return payloads, order


def _fetch_videos_batch(
    db, since: datetime, limit: int, offset: int
) -> Tuple[List[dict], List[Tuple[str, int]]]:
    """Fetch a batch of videos for digest."""
    stmt = (
        select(YouTubeVideo)
        .where(YouTubeVideo.published_at >= since)
        .order_by(YouTubeVideo.published_at.desc())
        .limit(limit)
        .offset(offset)
    )
    videos = list(db.execute(stmt).scalars().all())
    payloads = []
    order = []
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


def run_digest(
    hours: int | None = None,
    article_batch_size: int = DIGEST_ARTICLE_BATCH_SIZE,
    video_batch_size: int = DIGEST_VIDEO_BATCH_SIZE,
) -> int:
    """
    Fetch raw content from DB in batches, run DigestAgent, write to digested_content.
    Articles: batches of 50. Videos: batches of 20. Keeps memory within 512MB.
    """
    window_hours = hours or SCRAPE_WINDOW_HOURS
    since = datetime.now(timezone.utc) - timedelta(hours=window_hours)
    init_db()
    db = SessionLocal()

    try:
        agent = DigestAgent()
        digest_repo = DigestedContentRepository(db)
        count = 0

        article_offset = 0
        while True:
            payloads, order = _fetch_articles_batch(db, since, article_batch_size, article_offset)
            if not payloads:
                break

            logger.info("Processing article batch %d-%d", article_offset + 1, article_offset + len(payloads))
            result = agent.generate_digests_batch(payloads)

            for i, (ct, source_id) in enumerate(order):
                if i >= len(payloads):
                    break
                p = payloads[i]
                source_type = "article"
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

            article_offset += article_batch_size

        video_offset = 0
        while True:
            payloads, order = _fetch_videos_batch(db, since, video_batch_size, video_offset)
            if not payloads:
                break

            logger.info("Processing video batch %d-%d", video_offset + 1, video_offset + len(payloads))
            result = agent.generate_digests_batch(payloads)

            for i, (ct, source_id) in enumerate(order):
                if i >= len(payloads):
                    break
                p = payloads[i]
                source_type = "video"
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

            video_offset += video_batch_size

        logger.info("Upserted %d digests to digested_content", count)
        return count
    finally:
        db.close()


if __name__ == "__main__":
    run_digest(hours=SCRAPE_WINDOW_HOURS)
