"""
Cleanup Service: Deletes scraped and digested content older than RETENTION_DAYS.
Run after curator to free space. Keeps only people (subscribers).
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete

from app.agent.config import RETENTION_DAYS
from app.database import ArticleRecord, DigestedContent, SessionLocal, YouTubeVideo, init_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def run_cleanup(retention_days: int | None = None) -> dict[str, int]:
    """
    Delete articles, youtube_videos, and digested_content older than retention_days.
    Returns counts of deleted rows per table.
    """
    days = retention_days or RETENTION_DAYS
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    init_db()
    db = SessionLocal()

    counts: dict[str, int] = {}

    try:
        stmt_digested = delete(DigestedContent).where(DigestedContent.published_at < cutoff)
        result = db.execute(stmt_digested)
        counts["digested_content"] = result.rowcount or 0

        stmt_articles = delete(ArticleRecord).where(ArticleRecord.published_at < cutoff)
        result = db.execute(stmt_articles)
        counts["articles"] = result.rowcount or 0

        stmt_videos = delete(YouTubeVideo).where(YouTubeVideo.published_at < cutoff)
        result = db.execute(stmt_videos)
        counts["youtube_videos"] = result.rowcount or 0

        db.commit()

        total = sum(counts.values())
        logger.info(
            "Cleanup: deleted %d rows (digested: %d, articles: %d, videos: %d) older than %d days",
            total,
            counts["digested_content"],
            counts["articles"],
            counts["youtube_videos"],
            days,
        )
        return counts
    finally:
        db.close()


if __name__ == "__main__":
    run_cleanup()
