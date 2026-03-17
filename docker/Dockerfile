# NeuralBrief app services (scraper, digest, curator)
FROM python:3.12-slim

WORKDIR /app

# Copy project
COPY pyproject.toml uv.lock* ./
COPY app ./app
COPY main.py ./
COPY docker ./docker

# Install dependencies and project
RUN pip install uv && uv sync --no-dev && uv pip install --system -e .

# Default: run full pipeline (override in docker-compose)
CMD ["python", "main.py"]
