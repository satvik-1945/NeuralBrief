# NeuralBrief

**NeuralBrief** is an AI-powered newsletter pipeline that scrapes beauty, wellness, and lifestyle content from YouTube and Allure, curates it using rule-based filters, generates summaries with OpenAI, and delivers a polished HTML digest to your inbox.

---

## Features

- **Multi-source ingestion**: Scrapes YouTube videos (with transcripts) and Allure articles
- **Rule-based curation**: Filters content by interests (skin, makeup, hair, wellness, etc.) without API costs
- **AI-powered digests**: Uses OpenAI to generate concise, engaging summaries in a single batch call
- **Modular architecture**: Three independent agents (Curator, Digest, Email) that can run in parallel or be deployed separately
- **Professional email template**: HTML newsletter with article/video badges, author attribution, and "See more" links

---

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Scrapers      │     │   Database      │     │   Agents        │
│  (YouTube,      │────▶│  (PostgreSQL/   │────▶│  Curator        │
│   Allure)       │     │   SQLite)       │     │  Digest (OpenAI)│
└─────────────────┘     └─────────────────┘     │  Email          │
                                                 └────────┬────────┘
                                                          │
                                                          ▼
                                                 ┌─────────────────┐
                                                 │  Newsletter     │
                                                 │  (HTML email)   │
                                                 └─────────────────┘
```

**Pipeline flow:**
1. **Ingestion** → Scrape YouTube channels and Allure RSS; store in DB
2. **Curator** (rule-based) → Select relevant articles/videos by profile interests
3. **Digest** (OpenAI) → Generate summaries for all content in one batch
4. **Email** → Filter by curated IDs, render HTML, send via SMTP

---

## Prerequisites

- **Python 3.12+**
- **PostgreSQL** (optional; SQLite works for local development)
- **OpenAI API key** (for digest summaries)
- **SMTP credentials** (Gmail App Password or similar for sending emails)

---

## Installation

### 1. Clone and enter the project

```bash
git clone <repository-url>
cd NeuralBrief
```

### 2. Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate   # On Windows: .venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -e .
```

If you use `httpx` and it's not installed:

```bash
pip install httpx
```

---

## Configuration

### 1. Create your environment file

```bash
cp .env.example .env
```

### 2. Edit `.env` with your values

```env
# Database (PostgreSQL or SQLite)
DATABASE_URL=postgresql://user:password@localhost:5432/neuralbrief
# Or for SQLite (default):
# DATABASE_URL=sqlite:///./neuralbrief.db

# Time window for scraping (hours)
SCRAPE_WINDOW_HOURS=48

# SMTP / Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password

NEWSLETTER_FROM_EMAIL=your_email@gmail.com
NEWSLETTER_TO_EMAIL=recipient@example.com

# OpenAI (required for digest summaries)
OPENAI_API_KEY=sk-your-openai-api-key
```

**Gmail users:** Use an [App Password](https://support.google.com/accounts/answer/185833), not your regular password.

---

## Usage

### Run the full pipeline

```bash
python main.py
```

This will:
1. Scrape YouTube channels and Allure articles from the last 48 hours (or `SCRAPE_WINDOW_HOURS`)
2. Store content in the database
3. Curate and digest in parallel
4. Send the newsletter to `NEWSLETTER_TO_EMAIL`

### Run services independently

```bash
# Curator only (returns curated IDs)
python -m app.services.process_curator

# Digest only (processes all content in window)
python -m app.services.process_digest
```

---

## Customization

### YouTube channels

Edit `app/agent/config.py`:

```python
YOUTUBE_CHANNELS = [
    "UCzTKskwIc_-a0cGvCXA848Q",  # Nikkie Tutorials
    "UCbAwSkqJ1W_Eg7wr3cp5BUA",  # Safiya Nygaard
    # Add your channel IDs
]

YOUTUBE_CHANNEL_NAMES = {
    "UCzTKskwIc_-a0cGvCXA848Q": "Nikkie Tutorials",
    # Map channel_id → display name for email
}
```

### User profile (interests & sources)

Edit `app/profile.py`:

```python
DEFAULT_PROFILE = UserProfile(
    name="Default User",
    interests=["skin", "makeup", "hair", "wellness", "celebrities"],
    sources=["allure", "youtube"],
)
```

---

## Project structure

```
NeuralBrief/
├── main.py                 # Entry point; runs full pipeline
├── app/
│   ├── agent/
│   │   ├── config.py       # Configuration (channels, SMTP, OpenAI)
│   │   ├── curator_agent.py # Rule-based curation
│   │   ├── digest_agent.py # OpenAI batch summarization
│   │   └── email_agent.py  # HTML rendering & SMTP send
│   ├── database/
│   │   ├── db.py           # SQLAlchemy models
│   │   └── repositories.py # DB access layer
│   ├── scraper/
│   │   ├── allure.py       # Allure RSS + article scraper
│   │   └── youtube.py      # YouTube RSS + transcript fetcher
│   ├── services/
│   │   ├── process_curator.py
│   │   ├── process_digest.py
│   │   └── process_email.py
│   └── profile.py          # User interests & sources
├── .env                    # Your secrets (not committed)
├── .env.example            # Template
└── pyproject.toml
```

---

## Deployment

### Cron (scheduled runs)

```cron
# Run daily at 8:00 AM
0 8 * * * cd /path/to/NeuralBrief && .venv/bin/python main.py
```

### Docker (example)

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN pip install -e .
CMD ["python", "main.py"]
```

Ensure `DATABASE_URL`, `OPENAI_API_KEY`, and SMTP vars are set as environment variables in your deployment.

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `Missing required .env variables` | Ensure all required vars in `main.py`'s `check_env()` are set in `.env` |
| `OPENAI_API_KEY` not found | Call `load_dotenv()` before reading config; ensure `.env` is in project root |
| No articles in digest | Check `SCRAPE_WINDOW_HOURS`; ensure Allure RSS is reachable |
| No videos | Verify YouTube channel IDs; some videos may have transcripts disabled |
| SMTP authentication failed | Use Gmail App Password; check `SMTP_USERNAME` and `SMTP_PASSWORD` |
| `author` column missing | For existing SQLite DB: `ALTER TABLE articles ADD COLUMN author VARCHAR(255);` |

---

## License

See repository for license details.
