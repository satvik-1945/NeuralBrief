from app.config import YOUTUBE_CHANNELS
from app.database import (
    ArticleRecord,
    ArticleRepository,
    SessionLocal,
    YouTubeRepository,
    init_db,
)
from app.scraper.allure import AllureScraper
from app.scraper.youtube import YouTubeScraper


def run_ingestion(hours: int = 24) -> None:
    init_db()
    db = SessionLocal()

    youtube_repo = YouTubeRepository(db)
    article_repo = ArticleRepository(db)

    yt_scraper = YouTubeScraper()
    allure_scraper = AllureScraper()

    for channel_id in YOUTUBE_CHANNELS:
        videos = yt_scraper.scrape_channel(channel_id, hours=hours)
        youtube_repo.upsert_videos(channel_id, videos)

    articles = allure_scraper.scrape(hours=hours)
    article_repo.upsert_articles("allure", articles)


def main():
    run_ingestion(hours=48)


if __name__ == "__main__":
    main()

