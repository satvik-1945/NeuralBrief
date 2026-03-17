"""
Curator Service: Reads people and digested_content, curates per person, sends email per person.
Run after digest. No DB writes; calls Email Agent per subscriber.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import List, Tuple

from app.agent.config import NEWSLETTER_TO_EMAIL, SCRAPE_WINDOW_HOURS
from app.agent.curator_agent import CuratorAgent, CuratorItem
from app.database import (
    DigestedContent,
    DigestedContentRepository,
    PersonRepository,
    SessionLocal,
    init_db,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


@dataclass
class EmailDigestItem:
    """Item for EmailAgent: title, url, section, summary, author, content_type."""

    title: str
    url: str
    section: str | None
    summary: str
    author: str | None
    content_type: str


def _digested_to_curator_item(d: DigestedContent) -> CuratorItem:
    source = "allure" if d.source_type == "article" else "youtube"
    return CuratorItem(
        content_type=d.source_type,
        id=d.source_id,
        title=d.title,
        description=d.summary,
        section=d.section,
        categories=None,
        published_at=d.published_at,
        source=source,
        content_text=d.summary,
    )


def _digested_to_email_item(d: DigestedContent) -> EmailDigestItem:
    return EmailDigestItem(
        title=d.title,
        url=d.url,
        section=d.section,
        summary=d.summary,
        author=d.author,
        content_type=d.source_type,
    )


def run_curator(hours: int | None = None, limit_digested: int = 100) -> None:
    """
    For each subscriber: curate digested_content by their interests, send email.
    Only includes content published within `hours` (default SCRAPE_WINDOW_HOURS) to avoid duplicates.
    """
    init_db()
    db = SessionLocal()

    try:
        person_repo = PersonRepository(db)
        digest_repo = DigestedContentRepository(db)

        people = list(person_repo.get_all_subscribers())
        if not people and NEWSLETTER_TO_EMAIL:
            from app.profile import DEFAULT_PROFILE
            from types import SimpleNamespace

            people = [
                SimpleNamespace(
                    email=NEWSLETTER_TO_EMAIL,
                    interests=",".join(DEFAULT_PROFILE.interests),
                ),
            ]
        if not people:
            logger.warning("No subscribers in people table and no NEWSLETTER_TO_EMAIL fallback")
            return

        window_hours = hours or SCRAPE_WINDOW_HOURS
        all_digested = digest_repo.get_recent(hours=window_hours, limit=limit_digested)
        if not all_digested:
            logger.warning("No digested content; run run_digest first")
            return

        curator_items = [_digested_to_curator_item(d) for d in all_digested]
        agent = CuratorAgent()

        for person in people:
            curated_ids = agent.curate(curator_items, interests=person.interests)
            if not curated_ids:
                logger.info("No curated items for %s, skipping email", person.email)
                continue

            digest_items = digest_repo.get_by_source_pairs(curated_ids)
            email_items = [_digested_to_email_item(d) for d in digest_items]

            from app.agent.email_agent import EmailAgent

            email_agent = EmailAgent()
            email_agent.send(email_items, to_email=person.email)
            logger.info(
                "Sent %d items to %s",
                len(email_items),
                person.email,
            )
    finally:
        db.close()


if __name__ == "__main__":
    run_curator()
