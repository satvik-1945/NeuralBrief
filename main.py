"""
NeuralBrief pipeline orchestrator.

Run full pipeline: python main.py

Or run services separately:
  python -m app.services.run_scraper   # Scrape YouTube + Allure → DB
  python -m app.services.run_digest    # Digest raw content → digested_content
  python -m app.services.run_curator   # Curate per person, send emails
"""
from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()


def check_env() -> None:
    required = [
        "DATABASE_URL",
        "OPENAI_API_KEY",
        "SMTP_PASSWORD",
        "SMTP_USERNAME",
        "NEWSLETTER_FROM_EMAIL",
    ]
    missing = [r for r in required if not os.getenv(r)]
    if missing:
        raise ImportError(f"❌ Missing required .env variables: {', '.join(missing)}")


def main() -> None:
    check_env()

    from app.agent.config import SCRAPE_WINDOW_HOURS
    from app.services.run_scraper import run_scraper
    from app.services.run_digest import run_digest
    from app.services.run_curator import run_curator

    # 1) Scrape new content into the database
    run_scraper(hours=SCRAPE_WINDOW_HOURS)

    # 2) Digest raw content → digested_content
    run_digest(hours=SCRAPE_WINDOW_HOURS)

    # 3) Curate per person, send emails
    run_curator()


if __name__ == "__main__":
    main()
