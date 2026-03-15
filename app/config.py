import os
from dotenv import load_dotenv

load_dotenv()

YOUTUBE_CHANNELS = [
    "UCzTKskwIc_-a0cGvCXA848Q",
    "UCbAwSkqJ1W_Eg7wr3cp5BUA",
    "UC4qk9TtGhBKCkoWz5qGJcGg",
]

SCRAPE_WINDOW_HOURS = int(os.getenv("SCRAPE_WINDOW_HOURS", "48"))

# SMTP configuration
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")

# If these are None, the script will now correctly grab them from .env
NEWSLETTER_FROM_EMAIL = os.getenv("NEWSLETTER_FROM_EMAIL")
NEWSLETTER_TO_EMAIL = os.getenv("NEWSLETTER_TO_EMAIL", "")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")