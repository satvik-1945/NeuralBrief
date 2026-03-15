from __future__ import annotations

from typing import Iterable, List, Optional

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.db import ArticleRecord, YouTubeVideo
from app.scraper.youtube import ChannelVideo
from app.scraper.allure import Article


class YouTubeRepository:
    def __init__(self, db: Session):
        self.db = db

    def upsert_videos(self, channel_id: str, videos: Iterable[ChannelVideo]) -> None:
        for video in videos:
            self._upsert_video(channel_id, video)

    def _upsert_video(self, channel_id: str, video: ChannelVideo) -> None:
        existing = self.db.execute(
            select(YouTubeVideo).where(YouTubeVideo.video_id == video.video_id)
        ).scalar_one_or_none()

        if existing:
            existing.title = video.title
            existing.url = video.url
            existing.description = video.description
            existing.transcript = video.transcript
            existing.channel_id = channel_id
            existing.published_at = video.published_at
        else:
            record = YouTubeVideo(
                video_id=video.video_id,
                title=video.title,
                url=video.url,
                description=video.description,
                transcript=video.transcript,
                channel_id=channel_id,
                published_at=video.published_at,
            )
            self.db.add(record)

        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()

    def get_recent_videos(self, limit: int = 50) -> List[YouTubeVideo]:
        stmt = (
            select(YouTubeVideo)
            .order_by(YouTubeVideo.published_at.desc())
            .limit(limit)
        )
        return list(self.db.execute(stmt).scalars().all())


class ArticleRepository:
    def __init__(self, db: Session):
        self.db = db

    def upsert_articles(self, source: str, articles: Iterable[Article]) -> None:
        for article in articles:
            self._upsert_article(source, article)

    def _upsert_article(self, source: str, article: Article) -> None:
        existing = self.db.execute(
            select(ArticleRecord).where(ArticleRecord.url == article.url)
        ).scalar_one_or_none()

        categories_str = ",".join(article.categories) if article.categories else None

        # We try to persist whichever representation is available:
        # - raw HTML (content_html)
        # - cleaned text (content_text)
        # - markdown-only version (content_markdown)
        content_html = getattr(article, "content_html", None)
        content_text = getattr(article, "content_text", None)
        markdown = getattr(article, "content_markdown", None)

        if existing:
            existing.title = article.title
            existing.description = article.description
            existing.author = getattr(article, "author", None)
            existing.section = article.section
            existing.categories = categories_str
            existing.content_html = content_html
            existing.content_text = content_text
            existing.markdown = markdown
            existing.source = source
            existing.published_at = article.published_at
        else:
            record = ArticleRecord(
                url=article.url,
                title=article.title,
                description=article.description,
                author=getattr(article, "author", None),
                section=article.section,
                categories=categories_str,
                content_html=content_html,
                content_text=content_text,
                markdown=markdown,
                source=source,
                published_at=article.published_at,
            )
            self.db.add(record)
        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()

    def get_recent_articles(
        self, source: Optional[str] = None, limit: int = 50
    ) -> List[ArticleRecord]:
        stmt = select(ArticleRecord).order_by(ArticleRecord.published_at.desc())
        if source:
            stmt = stmt.where(ArticleRecord.source == source)
        stmt = stmt.limit(limit)
        return list(self.db.execute(stmt).scalars().all())


__all__ = [
    "YouTubeRepository",
    "ArticleRepository",
]

