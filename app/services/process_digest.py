from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple

from app.agent.digest_agent import DigestAgent
from app.agent.config import SCRAPE_WINDOW_HOURS, YOUTUBE_CHANNEL_NAMES
from app.database import ArticleRecord, SessionLocal, YouTubeVideo
from app.profile import DEFAULT_PROFILE

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


@dataclass
class DigestItem:
    content_type: str  # "article" | "video"
    content_id: int
    title: str
    url: str
    section: Optional[str]
    source: str
    summary: str
    author: Optional[str] = None


def _make_summary_fallback(text: str, max_chars: int = 400) -> str:
    """Fallback when OpenAI is unavailable."""
    text = (text or "").strip()
    if not text:
        return ""
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3].rstrip() + "..."


def _fetch_content(
    curated_ids: Optional[List[Tuple[str, int]]],
    hours: Optional[int],
) -> Tuple[List[dict], List[Tuple[str, int]]]:
    """
    Fetch articles and videos from DB.
    Returns (payloads for DigestAgent, list of (content_type, id) in order).
    """
    window_hours = hours or SCRAPE_WINDOW_HOURS
    since = datetime.now(timezone.utc) - timedelta(hours=window_hours)

    db = SessionLocal()
    try:
        payloads: List[dict] = []
        order: List[Tuple[str, int]] = []

        if curated_ids is not None and len(curated_ids) > 0:
            article_ids = [i for t, i in curated_ids if t == "article"]
            video_ids = [i for t, i in curated_ids if t == "video"]

            if article_ids:
                articles = (
                    db.query(ArticleRecord)
                    .filter(ArticleRecord.id.in_(article_ids))
                    .all()
                )
                id_to_article = {a.id: a for a in articles}
                for ct, i in curated_ids:
                    if ct == "article" and i in id_to_article:
                        a = id_to_article[i]
                        payloads.append(
                            {
                                "id": a.id,
                                "title": a.title,
                                "content": a.content_text or a.markdown or a.description or "",
                                "url": a.url,
                                "section": a.section,
                                "article_type": "article",
                                "author": a.author,
                            }
                        )
                        order.append((ct, i))

            if video_ids:
                videos = (
                    db.query(YouTubeVideo)
                    .filter(YouTubeVideo.id.in_(video_ids))
                    .all()
                )
                id_to_video = {v.id: v for v in videos}
                for ct, i in curated_ids:
                    if ct == "video" and i in id_to_video:
                        v = id_to_video[i]
                        payloads.append(
                            {
                                "id": v.id,
                                "title": v.title,
                                "content": v.transcript or v.description or "",
                                "url": v.url,
                                "section": None,
                                "article_type": "video",
                                "author": YOUTUBE_CHANNEL_NAMES.get(v.channel_id or "", "YouTube"),
                            }
                        )
                        order.append((ct, i))
        else:
            # Independent mode: fetch all in window
            article_sources = [s for s in DEFAULT_PROFILE.sources if s != "youtube"]
            if article_sources:
                articles = (
                    db.query(ArticleRecord)
                    .filter(ArticleRecord.published_at >= since)
                    .filter(ArticleRecord.source.in_(article_sources))
                    .order_by(ArticleRecord.published_at.desc())
                    .all()
                )
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
                        }
                    )
                    order.append(("article", a.id))

            if "youtube" in DEFAULT_PROFILE.sources:
                videos = (
                    db.query(YouTubeVideo)
                    .filter(YouTubeVideo.published_at >= since)
                    .order_by(YouTubeVideo.published_at.desc())
                    .all()
                )
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
                        }
                    )
                    order.append(("video", v.id))

        return payloads, order
    finally:
        db.close()


def process_digests(
    curated_ids: Optional[List[Tuple[str, int]]] = None,
    hours: Optional[int] = None,
) -> List[DigestItem]:
    """
    Digest Service:
    Fetches articles and videos (by curated_ids or from DB within time window),
    runs DigestAgent, returns DigestItems. Supports both Allure and YouTube.
    When curated_ids is None, fetches all content in window.
    """
    payloads, order = _fetch_content(curated_ids, hours)

    if not payloads:
        logger.info("No content to digest")
        return []

    logger.info(
        "Processing %d items (%d articles, %d videos) with DigestAgent (batch)",
        len(payloads),
        sum(1 for p in payloads if p.get("article_type") == "article"),
        sum(1 for p in payloads if p.get("article_type") == "video"),
    )

    agent = DigestAgent()
    result = agent.generate_digests_batch(payloads)

    if result and result.digests:
        items: List[DigestItem] = []
        for i, (ct, cid) in enumerate(order):
            if i < len(payloads) and i < len(result.digests):
                p = payloads[i]
                entry = result.digests[i]
                items.append(
                    DigestItem(
                        content_type=ct,
                        content_id=cid,
                        title=entry.title,
                        url=p["url"],
                        section=p.get("section"),
                        source="allure" if ct == "article" else "youtube",
                        summary=entry.summary,
                        author=p.get("author"),
                    )
                )
            elif i < len(payloads):
                p = payloads[i]
                items.append(
                    DigestItem(
                        content_type=ct,
                        content_id=cid,
                        title=p["title"],
                        url=p["url"],
                        section=p.get("section"),
                        source="allure" if ct == "article" else "youtube",
                        summary=_make_summary_fallback(p.get("content", "")),
                        author=p.get("author"),
                    )
                )
        logger.info("✓ Successfully generated %d digests", len(items))
        return items

    logger.warning("DigestAgent failed, using fallback summaries")
    return [
        DigestItem(
            content_type=ct,
            content_id=cid,
            title=p["title"],
            url=p["url"],
            section=p.get("section"),
            source="allure" if ct == "article" else "youtube",
            summary=_make_summary_fallback(p.get("content", "")),
            author=p.get("author"),
        )
        for (ct, cid), p in zip(order, payloads)
    ]


if __name__ == "__main__":
    result = process_digests(curated_ids=None, hours=SCRAPE_WINDOW_HOURS)
    logger.info("Total digests: %d", len(result))


__all__ = ["DigestItem", "process_digests"]
