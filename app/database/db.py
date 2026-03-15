from __future__ import annotations

import os
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    String,
    Text,
    UniqueConstraint,
    create_engine,
)
from sqlalchemy.orm import declarative_base, sessionmaker


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./neuralbrief.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class YouTubeVideo(Base):
    __tablename__ = "youtube_videos"
    __table_args__ = (UniqueConstraint("video_id", name="uq_youtube_video_id"),)

    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(String(64), nullable=False, index=True)
    title = Column(String(512), nullable=False)
    url = Column(String(1024), nullable=False)
    description = Column(Text, nullable=True)
    transcript = Column(Text, nullable=True)
    channel_id = Column(String(64), nullable=True, index=True)
    published_at = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )


class ArticleRecord(Base):
    __tablename__ = "articles"
    __table_args__ = (UniqueConstraint("url", name="uq_article_url"),)

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String(1024), nullable=False, index=True)
    title = Column(String(512), nullable=False)
    description = Column(Text, nullable=True)
    section = Column(String(255), nullable=True)
    categories = Column(Text, nullable=True)  # comma-separated list
    content_html = Column(Text, nullable=True)
    content_text = Column(Text, nullable=True)
    markdown = Column(Text, nullable=True)  # optional markdown-only version
    source = Column(String(64), nullable=False)  # e.g. allure, other sites later
    published_at = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )


def init_db() -> None:
    """
    Create tables if they don't exist. Call this once at startup.
    """
    Base.metadata.create_all(bind=engine)


__all__ = [
    "SessionLocal",
    "init_db",
    "YouTubeVideo",
    "ArticleRecord",
]

