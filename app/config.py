import os

YOUTUBE_CHANNELS = [
    "UCzTKskwIc_-a0cGvCXA848Q",  # Nikkie Tutorials
    "UCbAwSkqJ1W_Eg7wr3cp5BUA",  # Safiya Nygaard
    "UC4qk9TtGhBKCkoWz5qGJcGg",  # Tati
]

# Global time window (in hours) for scraping and newsletter content
SCRAPE_WINDOW_HOURS = int(os.getenv("SCRAPE_WINDOW_HOURS", "48"))

# Email / SMTP configuration for sending the newsletter
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")

NEWSLETTER_FROM_EMAIL = os.getenv("NEWSLETTER_FROM_EMAIL", SMTP_USERNAME or "no-reply@example.com")
NEWSLETTER_TO_EMAIL = os.getenv("NEWSLETTER_TO_EMAIL", "")

# OpenAI (for Curator ranking and Digest summarization)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

