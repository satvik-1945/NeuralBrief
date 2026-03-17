# NeuralBrief Docker

PostgreSQL 17 + one container per service (scraper, digest, curator).

## Prerequisites

- Docker & Docker Compose
- `.env` file in project root with `OPENAI_API_KEY`, SMTP credentials, etc.

## Usage

### Full pipeline (Postgres + init + scraper → digest → curator)

```bash
cd /path/to/NeuralBrief
docker compose -f docker/docker-compose.yml up --build
```

### Run services individually (e.g. for cron)

```bash
# Start Postgres (tables are created automatically on first init)
docker compose -f docker/docker-compose.yml up postgres -d

# Run pipeline steps
docker compose -f docker/docker-compose.yml run --rm scraper
docker compose -f docker/docker-compose.yml run --rm digest
docker compose -f docker/docker-compose.yml run --rm curator
```

### Postgres connection

- Host: `localhost` (or `postgres` from other containers)
- Port: 5432
- User: `neuralbrief`
- Password: `neuralbrief`
- Database: `neuralbrief`
