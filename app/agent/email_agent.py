from __future__ import annotations

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Optional

from app.config import (
    NEWSLETTER_FROM_EMAIL,
    NEWSLETTER_TO_EMAIL,
    SCRAPE_WINDOW_HOURS,
    SMTP_HOST,
    SMTP_PASSWORD,
    SMTP_PORT,
    SMTP_USERNAME,
)


class EmailAgent:
    """Agent responsible for rendering and sending the newsletter email."""

    def __init__(self):
        self.smtp_host = SMTP_HOST
        self.smtp_port = SMTP_PORT
        self.smtp_username = SMTP_USERNAME
        self.smtp_password = SMTP_PASSWORD
        self.from_email = NEWSLETTER_FROM_EMAIL

    def render_html(self, items: List, window_hours: int = SCRAPE_WINDOW_HOURS) -> str:
        """Render digest items into HTML email body."""
        if not items:
            body = "<p>No new stories in this period.</p>"
        else:
            rows = []
            for item in items:
                content_type = getattr(item, "content_type", "article")
                badge = "📺 Video" if content_type == "video" else "📄 Article"
                section = getattr(item, "section", "") or ""
                section_line = f"<span style='color:#888;font-size:12px'>{badge} • {section}</span>" if section else f"<span style='color:#888;font-size:12px'>{badge}</span>"
                row = f"""
                <tr>
                  <td style="padding:12px 0;border-bottom:1px solid #eee;">
                    <a href="{item.url}" style="font-size:16px;font-weight:bold;color:#111;text-decoration:none;">
                      {item.title}
                    </a><br/>
                    {section_line}<br/>
                    <p style="margin:8px 0 0 0;font-size:14px;line-height:1.5;color:#333;">
                      {item.summary}
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
                  <p style="font-size:14px;color:#555;">Your curated highlights from the last {window_hours} hours.</p>
                </td>
              </tr>
              {body}
            </table>
          </body>
        </html>
        """
        return html

    def send(
        self,
        items: List,
        to_email: Optional[str] = None,
        subject: str = "NeuralBrief – Beauty & Wellness Digest",
    ) -> None:
        """
        Render and send the newsletter email.
        items: List of objects with title, url, section, summary.
        """
        recipient = to_email or NEWSLETTER_TO_EMAIL
        if not recipient:
            raise ValueError("NEWSLETTER_TO_EMAIL is not configured.")

        html_body = self.render_html(items)

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self.from_email
        msg["To"] = recipient
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
            server.starttls()
            if self.smtp_username and self.smtp_password:
                server.login(self.smtp_username, self.smtp_password)
            server.sendmail(self.from_email, [recipient], msg.as_string())


__all__ = ["EmailAgent"]
