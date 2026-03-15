from __future__ import annotations

import smtplib
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List

from app.config import (
    NEWSLETTER_FROM_EMAIL,
    NEWSLETTER_TO_EMAIL,
    SCRAPE_WINDOW_HOURS,
    SMTP_HOST,
    SMTP_PASSWORD,
    SMTP_PORT,
    SMTP_USERNAME,
)
from app.database import ArticleRecord, ArticleRepository, SessionLocal


@contextmanager
def get_db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@dataclass
class NewsletterItem:
    title: str
    url: str
    section: str | None
    source: str
    published_at: datetime
    excerpt: str


def _build_excerpt(article: ArticleRecord, max_chars: int = 280) -> str:
    text = article.content_text or article.description or ""
    text = text.strip()
    if not text:
        return ""
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3].rstrip() + "..."


def _build_newsletter_items(articles: List[ArticleRecord]) -> List[NewsletterItem]:
    items: List[NewsletterItem] = []
    for a in articles:
        items.append(
            NewsletterItem(
                title=a.title,
                url=a.url,
                section=a.section,
                source=a.source,
                published_at=a.published_at,
                excerpt=_build_excerpt(a),
            )
        )
    return items


def _render_html_email(items: List[NewsletterItem]) -> str:
    if not items:
        body = "<p>No new stories in this period.</p>"
    else:
        rows = []
        for item in items:
            section = f"<span style='color:#888;font-size:12px'>{item.section or ''}</span>"
            row = f"""
            <tr>
              <td style="padding:12px 0;border-bottom:1px solid #eee;">
                <a href="{item.url}" style="font-size:16px;font-weight:bold;color:#111;text-decoration:none;">
                  {item.title}
                </a><br/>
                {section}<br/>
                <p style="margin:8px 0 0 0;font-size:14px;line-height:1.5;color:#333;">
                  {item.excerpt}
                </p>
              </td>
            </tr>
            """
            rows.append(row)
        body = "\n".join(rows)

    html = f"""
    <html>
      <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background-color:#fafafa; padding:24px;">
        <table width="100%%" cellpadding="0" cellspacing="0" style="max-width:640px;margin:0 auto;background:#ffffff;border-radius:8px;padding:24px;">
          <tr>
            <td>
              <h1 style="margin-top:0;font-size:22px;">NeuralBrief – Beauty & Wellness Digest</h1>
              <p style="font-size:14px;color:#555;">Your curated highlights from the last {SCRAPE_WINDOW_HOURS} hours.</p>
            </td>
          </tr>
          {body}
        </table>
      </body>
    </html>
    """
    return html


def send_newsletter(hours: int | None = None, to_email: str | None = None) -> None:
    """
    Fetch recent articles from the database, build a simple HTML newsletter,
    and send it to the configured email address.
    """
    window_hours = hours or SCRAPE_WINDOW_HOURS
    recipient = to_email or NEWSLETTER_TO_EMAIL
    if not recipient:
        raise ValueError("NEWSLETTER_TO_EMAIL is not configured.")

    since = datetime.now(timezone.utc) - timedelta(hours=window_hours)

    with get_db_session() as db:
        article_repo = ArticleRepository(db)
        # Fetch articles newer than 'since'
        articles = (
            db.query(ArticleRecord)
            .filter(ArticleRecord.published_at >= since)
            .order_by(ArticleRecord.published_at.desc())
            .all()
        )

    items = _build_newsletter_items(articles)
    html_body = _render_html_email(items)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "NeuralBrief – Beauty & Wellness Digest"
    msg["From"] = NEWSLETTER_FROM_EMAIL
    msg["To"] = recipient

    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        if SMTP_USERNAME and SMTP_PASSWORD:
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.sendmail(NEWSLETTER_FROM_EMAIL, [recipient], msg.as_string())


__all__ = ["send_newsletter"]

