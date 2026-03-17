"""
Scraper Service: Scrapes YouTube and Allure, stores raw content in DB.
Run daily via cron. No digest, curation, or email.
"""
from __future__ import annotations

import logging

from dotenv import load_dotenv

load_dotenv()

from app.agent.config import SCRAPE_WINDOW_HOURS, YOUTUBE_CHANNELS
from app.database import ArticleRepository, SessionLocal, YouTubeRepository, init_db
from app.scraper.allure import AllureScraper
from app.scraper.youtube import YouTubeScraper

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


SCRAPER_ARTICLE_BATCH_SIZE = 10


def run_scraper(
    hours: int | None = None,
    article_batch_size: int = SCRAPER_ARTICLE_BATCH_SIZE,
) -> None:
    """
    Scrape YouTube + Allure, store raw content in database.
    YouTube: one channel at a time. Allure: articles in batches of 10.
    """
    window_hours = hours or SCRAPE_WINDOW_HOURS
    init_db()
    db = SessionLocal()

    try:
        youtube_repo = YouTubeRepository(db)
        article_repo = ArticleRepository(db)
        yt_scraper = YouTubeScraper()
        allure_scraper = AllureScraper()

        for channel_id in YOUTUBE_CHANNELS:
            videos = yt_scraper.scrape_channel(channel_id, hours=window_hours)
            youtube_repo.upsert_videos(channel_id, videos)
            logger.info("Upserted %d videos from channel %s", len(videos), channel_id)

        entries = allure_scraper.get_rss_entries(hours=window_hours)
        for i in range(0, len(entries), article_batch_size):
            batch = entries[i : i + article_batch_size]
            scraped = allure_scraper.scrape_articles_batch(batch)
            article_repo.upsert_articles("allure", scraped)
            logger.info("Upserted %d articles from Allure (batch %d-%d)", len(scraped), i + 1, i + len(scraped))
    finally:
        db.close()


if __name__ == "__main__":
    run_scraper(hours=SCRAPE_WINDOW_HOURS)
