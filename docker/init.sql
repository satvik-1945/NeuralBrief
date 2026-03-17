-- NeuralBrief schema: run by Postgres on first init
-- Tables: youtube_videos, articles, people, digested_content

CREATE TABLE IF NOT EXISTS youtube_videos (
    id SERIAL PRIMARY KEY,
    video_id VARCHAR(64) NOT NULL,
    title VARCHAR(512) NOT NULL,
    url VARCHAR(1024) NOT NULL,
    description TEXT,
    transcript TEXT,
    channel_id VARCHAR(64),
    published_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_youtube_video_id UNIQUE (video_id)
);
CREATE INDEX IF NOT EXISTS ix_youtube_videos_video_id ON youtube_videos (video_id);
CREATE INDEX IF NOT EXISTS ix_youtube_videos_channel_id ON youtube_videos (channel_id);
CREATE INDEX IF NOT EXISTS ix_youtube_videos_published_at ON youtube_videos (published_at);

CREATE TABLE IF NOT EXISTS articles (
    id SERIAL PRIMARY KEY,
    url VARCHAR(1024) NOT NULL,
    title VARCHAR(512) NOT NULL,
    description TEXT,
    author VARCHAR(255),
    section VARCHAR(255),
    categories TEXT,
    content_html TEXT,
    content_text TEXT,
    markdown TEXT,
    source VARCHAR(64) NOT NULL,
    published_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_article_url UNIQUE (url)
);
CREATE INDEX IF NOT EXISTS ix_articles_url ON articles (url);
CREATE INDEX IF NOT EXISTS ix_articles_published_at ON articles (published_at);

CREATE TABLE IF NOT EXISTS people (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    name VARCHAR(255),
    interests TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_person_email UNIQUE (email)
);
CREATE INDEX IF NOT EXISTS ix_people_email ON people (email);

CREATE TABLE IF NOT EXISTS digested_content (
    id SERIAL PRIMARY KEY,
    source_type VARCHAR(32) NOT NULL,
    source_id INTEGER NOT NULL,
    title VARCHAR(512) NOT NULL,
    summary TEXT NOT NULL,
    url VARCHAR(1024) NOT NULL,
    author VARCHAR(255),
    section VARCHAR(255),
    published_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_digested_source UNIQUE (source_type, source_id)
);
CREATE INDEX IF NOT EXISTS ix_digested_content_source_id ON digested_content (source_id);
CREATE INDEX IF NOT EXISTS ix_digested_content_published_at ON digested_content (published_at);
