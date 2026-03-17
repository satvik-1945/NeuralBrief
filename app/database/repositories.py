from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Iterable, List, Optional

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.db import ArticleRecord, DigestedContent, Person, YouTubeVideo
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


class PersonRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all_subscribers(self) -> List[Person]:
        stmt = select(Person).order_by(Person.id)
        return list(self.db.execute(stmt).scalars().all())

    def create(self, email: str, name: str | None = None, interests: str | None = None) -> Person:
        person = Person(email=email, name=name, interests=interests)
        self.db.add(person)
        try:
            self.db.commit()
            self.db.refresh(person)
            return person
        except IntegrityError:
            self.db.rollback()
            raise


class DigestedContentRepository:
    def __init__(self, db: Session):
        self.db = db

    def upsert(
        self,
        source_type: str,
        source_id: int,
        title: str,
        summary: str,
        url: str,
        author: str | None = None,
        section: str | None = None,
        published_at: datetime | None = None,
    ) -> None:
        existing = self.db.execute(
            select(DigestedContent).where(
                DigestedContent.source_type == source_type,
                DigestedContent.source_id == source_id,
            )
        ).scalar_one_or_none()

        if existing:
            existing.title = title
            existing.summary = summary
            existing.url = url
            existing.author = author
            existing.section = section
            existing.published_at = published_at or existing.published_at
        else:
            record = DigestedContent(
                source_type=source_type,
                source_id=source_id,
                title=title,
                summary=summary,
                url=url,
                author=author,
                section=section,
                published_at=published_at,
            )
            self.db.add(record)
        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()

    def get_all(self, limit: int = 100) -> List[DigestedContent]:
        stmt = (
            select(DigestedContent)
            .order_by(DigestedContent.published_at.desc())
            .limit(limit)
        )
        return list(self.db.execute(stmt).scalars().all())

    def get_recent(self, hours: int, limit: int = 100) -> List[DigestedContent]:
        """Fetch digested content published within the last `hours` to avoid duplicates across newsletters."""
        since = datetime.now(timezone.utc) - timedelta(hours=hours)
        stmt = (
            select(DigestedContent)
            .where(DigestedContent.published_at >= since)
            .order_by(DigestedContent.published_at.desc())
            .limit(limit)
        )
        return list(self.db.execute(stmt).scalars().all())

    def get_by_ids(self, ids: List[int]) -> List[DigestedContent]:
        if not ids:
            return []
        stmt = (
            select(DigestedContent)
            .filter(DigestedContent.id.in_(ids))
            .order_by(DigestedContent.published_at.desc())
        )
        return list(self.db.execute(stmt).scalars().all())

    def get_by_source_pairs(
        self, pairs: List[tuple[str, int]]
    ) -> List[DigestedContent]:
        """Fetch DigestedContent by (source_type, source_id) pairs, preserving order."""
        if not pairs:
            return []
        from sqlalchemy import or_

        pair_set = set(pairs)
        conditions = [
            (DigestedContent.source_type == st) & (DigestedContent.source_id == sid)
            for st, sid in pair_set
        ]
        stmt = select(DigestedContent).where(or_(*conditions))
        results = list(self.db.execute(stmt).scalars().all())
        order_map = {p: i for i, p in enumerate(pairs)}
        return sorted(
            [r for r in results if (r.source_type, r.source_id) in order_map],
            key=lambda r: order_map[(r.source_type, r.source_id)],
        )


__all__ = [
    "YouTubeRepository",
    "ArticleRepository",
    "PersonRepository",
    "DigestedContentRepository",
]

