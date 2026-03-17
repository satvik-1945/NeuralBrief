from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import List, Optional

import feedparser
import httpx
from bs4 import BeautifulSoup
from pydantic import BaseModel
from markdownify import markdownify as md  


class Article(BaseModel):
    title: str
    url: str
    published_at: datetime
    description: str
    section: Optional[str] = None
    categories: List[str] = []
    content_markdown: Optional[str] = None
    author: Optional[str] = None


class AllureScraper:
    FEED_URL = "https://www.allure.com/feed/rss"

    def __init__(self, *, timeout: float = 10.0):
        self.client = httpx.Client(timeout=timeout, follow_redirects=True)

    def _parse_rss(self, hours: int) -> List[Article]:
        # feedparser handles the RSS translation
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
            author = entry.get("author") or getattr(entry, "dc_creator", "") or None

            articles.append(
                Article(
                    title=entry.title,
                    url=entry.link,
                    published_at=published_at,
                    description=summary,
                    categories=categories,
                    author=author,
                )
            )
        return articles

    def _scrape_article(self, article: Article) -> Article:
        try:
            resp = self.client.get(article.url)
            resp.raise_for_status()
        except httpx.HTTPError:
            return article

        soup = BeautifulSoup(resp.text, "html.parser")

        body_selectors = [
            "article .body__inner-container",
            "article .ArticlePage-articleBody",
            ".main-content",
        ]

        body_html = None
        for selector in body_selectors:
            found = soup.select_one(selector)
            if found:
                body_html = found
                break

        if not body_html:
            return article

        content_md = md(
            str(body_html), 
            heading_style="ATX", 
            strip=['script', 'style', 'button']
        )

        section = soup.select_one(".ContentHeaderEyebrow-eyebrow")
        section_text = section.get_text(strip=True) if section else "General"

        return article.model_copy(
            update={
                "content_markdown": content_md.strip(),
                "section": section_text,
            }
        )

    def scrape(self, hours: int = 24) -> List[Article]:
        base_articles = self._parse_rss(hours=hours)
        return [self._scrape_article(a) for a in base_articles]

    def get_rss_entries(self, hours: int = 24) -> List[Article]:
        """Return articles from RSS without scraping full content (for batch processing)."""
        return self._parse_rss(hours=hours)

    def scrape_articles_batch(self, articles: List[Article]) -> List[Article]:
        """Scrape full content for a batch of articles."""
        return [self._scrape_article(a) for a in articles]


if __name__ == "__main__":
    scraper = AllureScraper()
    results = scraper.scrape(hours=24)
    
    for art in results:
        print(f"--- {art.title} [{art.section}] ---")
        print(f"URL: {art.url}")
        print(f"date {art.published_at}")
        print(f"Content Preview: {art.content_markdown if art.content_markdown else 'No content'}...")
        print("\n")

    print(len(results))