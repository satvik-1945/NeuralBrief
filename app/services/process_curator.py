from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple

from app.agent.curator_agent import CuratorAgent, CuratorItem
from app.config import SCRAPE_WINDOW_HOURS
from app.database import ArticleRecord, SessionLocal, YouTubeVideo
from app.profile import DEFAULT_PROFILE

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def process_curator(hours: Optional[int] = None) -> List[Tuple[str, int]]:
    """
    Curator Service:
    Fetches articles and YouTube videos from DB (within time window),
    runs CuratorAgent, returns curated IDs as [(content_type, id), ...].
    Fully independent - no dependency on digest.
    """
    window_hours = hours or SCRAPE_WINDOW_HOURS
    since = datetime.now(timezone.utc) - timedelta(hours=window_hours)

    db = SessionLocal()
    try:
        items: List[CuratorItem] = []

        # Fetch articles (Allure, etc.)
        if "allure" in DEFAULT_PROFILE.sources or any(
            s != "youtube" for s in DEFAULT_PROFILE.sources
        ):
            article_sources = [s for s in DEFAULT_PROFILE.sources if s != "youtube"]
            if article_sources:
                articles: List[ArticleRecord] = (
                    db.query(ArticleRecord)
                    .filter(ArticleRecord.published_at >= since)
                    .filter(ArticleRecord.source.in_(article_sources))
                    .order_by(ArticleRecord.published_at.desc())
                    .all()
                )
                for a in articles:
                    items.append(
                        CuratorItem(
                            content_type="article",
                            id=a.id,
                            title=a.title,
                            description=a.description,
                            section=a.section,
                            categories=a.categories,
                            published_at=a.published_at,
                            source=a.source,
                            content_text=a.content_text,
                        )
                    )

        # Fetch YouTube videos
        if "youtube" in DEFAULT_PROFILE.sources:
            videos: List[YouTubeVideo] = (
                db.query(YouTubeVideo)
                .filter(YouTubeVideo.published_at >= since)
                .order_by(YouTubeVideo.published_at.desc())
                .all()
            )
            for v in videos:
                items.append(
                    CuratorItem(
                        content_type="video",
                        id=v.id,
                        title=v.title,
                        description=v.description,
                        section=None,
                        categories=None,
                        published_at=v.published_at,
                        source="youtube",
                        content_text=v.transcript,
                    )
                )

        if not items:
            logger.info("No content in window, curator returns empty")
            return []

        agent = CuratorAgent()
        curated = agent.curate(items)
        logger.info(
            "Curator selected %d items (%d articles + %d videos) from %d candidates",
            len(curated),
            sum(1 for t, _ in curated if t == "article"),
            sum(1 for t, _ in curated if t == "video"),
            len(items),
        )
        return curated
    finally:
        db.close()


if __name__ == "__main__":
    result = process_curator(hours=SCRAPE_WINDOW_HOURS)
    logger.info("Curated: %s", result)


__all__ = ["process_curator"]
