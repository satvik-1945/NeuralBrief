from __future__ import annotations

import logging
from typing import List, Optional, Tuple

from app.agent.email_agent import EmailAgent

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def process_email(
    digest_items: List,
    curated_ids: Optional[List[Tuple[str, int]]] = None,
    to_email: Optional[str] = None,
) -> None:
    """
    Email Service:
    Takes digest items, optionally filters by curated_ids (if provided),
    and sends via EmailAgent. curated_ids: [(content_type, id), ...].
    """
    items = digest_items

    if curated_ids is not None and curated_ids:
        curated_set = set(curated_ids)
        id_to_item = {
            (getattr(d, "content_type", "article"), getattr(d, "content_id", -1)): d
            for d in digest_items
        }
        items = [id_to_item[k] for k in curated_ids if k in id_to_item]
        logger.info("Filtered to %d curated items for email", len(items))

    if not items:
        logger.warning("No digest items to send")
        return

    agent = EmailAgent()
    agent.send(items, to_email=to_email)
    logger.info("✓ Email sent successfully")


if __name__ == "__main__":
    logger.info("Run process_digest first, then process_email with the result")


__all__ = ["process_email"]
