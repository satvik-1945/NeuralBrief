from concurrent.futures import ThreadPoolExecutor, as_completed

from app.config import SCRAPE_WINDOW_HOURS, YOUTUBE_CHANNELS
from app.database import SessionLocal, YouTubeRepository, ArticleRepository, init_db
from app.scraper.allure import AllureScraper
from app.scraper.youtube import YouTubeScraper
from app.services import process_curator, process_digests, process_email


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

    # 2) Curator and Digest run in parallel (independent services)
    with ThreadPoolExecutor(max_workers=2) as executor:
        future_curator = executor.submit(process_curator, SCRAPE_WINDOW_HOURS)
        future_digest = executor.submit(
            process_digests, curated_ids=None, hours=SCRAPE_WINDOW_HOURS
        )
        curated_ids = future_curator.result()
        digest_items = future_digest.result()

    # 3) Email: filter digest by curated IDs, then send
    process_email(
        digest_items=digest_items,
        curated_ids=curated_ids,
    )


if __name__ == "__main__":
    main()
