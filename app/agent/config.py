import os
from dotenv import load_dotenv

load_dotenv()

YOUTUBE_CHANNELS = [
    "UCzTKskwIc_-a0cGvCXA848Q",  # Nikkie Tutorials
    "UCbAwSkqJ1W_Eg7wr3cp5BUA",  # Safiya Nygaard
    "UC4qk9TtGhBKCkoWz5qGJcGg",  # Tati
]

YOUTUBE_CHANNEL_NAMES = {
    "UCzTKskwIc_-a0cGvCXA848Q": "Nikkie Tutorials",
    "UCbAwSkqJ1W_Eg7wr3cp5BUA": "Safiya Nygaard",
    "UC4qk9TtGhBKCkoWz5qGJcGg": "Tati",
}

SCRAPE_WINDOW_HOURS = int(os.getenv("SCRAPE_WINDOW_HOURS", "48"))

# SMTP configuration
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")

NEWSLETTER_FROM_EMAIL = os.getenv("NEWSLETTER_FROM_EMAIL")
NEWSLETTER_TO_EMAIL = os.getenv("NEWSLETTER_TO_EMAIL", "")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
