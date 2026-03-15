from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import List, Optional

import feedparser
import httpx
from bs4 import BeautifulSoup
from pydantic import BaseModel


class Article(BaseModel):
    title: str
    url: str
    published_at: datetime
    description: str
    section: Optional[str] = None
    categories: List[str] = []
    content_html: Optional[str] = None
    content_text: Optional[str] = None


class AllureScraper:
    FEED_URL = "https://www.allure.com/feed/rss"

    def __init__(self, *, timeout: float = 10.0):
        self.client = httpx.Client(timeout=timeout)

    def _parse_rss(self, hours: int) -> List[Article]:
        feed = feedparser.parse(self.FEED_URL)
        if not feed.entries:
            return []

        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        articles: List[Article] = []

        for entry in feed.entries:
            if not getattr(entry, "published_parsed", None):
                continue

            published_at = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            if published_at <= cutoff_time:
                continue

            tags = getattr(entry, "tags", []) or []
            categories = [getattr(tag, "term", "").strip() for tag in tags if getattr(tag, "term", "").strip()]

            summary = entry.get("description") or entry.get("summary", "") or ""

            articles.append(
                Article(
                    title=entry.title,
                    url=entry.link,
                    published_at=published_at,
                    description=summary,
                    section=None,
                    categories=categories,
                )
            )

        return articles

    def _extract_section(self, soup: BeautifulSoup) -> Optional[str]:
        # Allure often has a section / category label near the top; this may need tuning.
        # Try a few reasonable selectors and return the first non-empty text.
        candidates = [
            ".HeroBanners-contentTag",
            ".ContentHeaderEyebrow-eyebrow",
            ".ArticlePage-eyebrow",
            "header .eyebrow",
        ]
        for selector in candidates:
            el = soup.select_one(selector)
            if el:
                text = el.get_text(strip=True)
                if text:
                    return text
        return None

    def _scrape_article(self, article: Article) -> Article:
        try:
            resp = self.client.get(article.url)
            resp.raise_for_status()
        except httpx.HTTPError:
            return article

        soup = BeautifulSoup(resp.text, "html.parser")

        # These selectors are based on current Allure layout and may need adjustments over time.
        body_selectors = [
            "article .body__inner-container",
            "article .ArticlePage-articleBody",
            "article .ArticlePage-content",
            "article .ContentList-items",  # fallback
        ]

        body = None
        for selector in body_selectors:
            body = soup.select_one(selector)
            if body:
                break

        if not body:
            return article

        # Extract paragraphs and other relevant text elements
        text_blocks: List[str] = []
        for el in body.select("p, h2, h3, li"):
            text = el.get_text(strip=True)
            if text:
                text_blocks.append(text)

        content_text = "\n\n".join(text_blocks)
        section = article.section or self._extract_section(soup)

        return article.model_copy(
            update={
                "content_html": str(body),
                "content_text": content_text or article.content_text,
                "section": section,
            }
        )

    def scrape(self, hours: int = 24) -> List[Article]:
        base_articles = self._parse_rss(hours=hours)
        result: List[Article] = []
        for article in base_articles:
            full_article = self._scrape_article(article)
            result.append(full_article)
        return result


if __name__ == "__main__":
    scraper = AllureScraper()
    articles = scraper.scrape(hours=24)
    for article in articles:
        print(article.title, article.url, len(article.content_text or ""), article.section, article.categories)
        # print(article.content_html)
