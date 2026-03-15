from app.config import SCRAPE_WINDOW_HOURS, YOUTUBE_CHANNELS
from app.database import (
    ArticleRecord,
    ArticleRepository,
    SessionLocal,
    YouTubeRepository,
    init_db,
)
from app.scraper.allure import AllureScraper
from app.scraper.youtube import YouTubeScraper
from app.services import send_newsletter


def run_ingestion(hours: int) -> None:
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
    # 1) Scrape new content into the database
    run_ingestion(hours=SCRAPE_WINDOW_HOURS)
    # 2) Build and send the newsletter from the last window
    send_newsletter(hours=SCRAPE_WINDOW_HOURS)


if __name__ == "__main__":
    main()

