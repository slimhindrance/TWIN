# Total Life AI - Production Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy pyproject.toml and poetry.lock first (for better layer caching)
COPY pyproject.toml ./
COPY poetry.loc[k] ./
COPY README.md ./

# Install Python dependencies
RUN pip install poetry
RUN poetry config virtualenvs.create false
RUN poetry install --only main --no-root

# Copy backend application code and alembic migrations
COPY backend/app ./app
COPY backend/alembic ./alembic
COPY backend/alembic.ini ./alembic.ini

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app
RUN chown -R app:app /app
USER app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Start application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
