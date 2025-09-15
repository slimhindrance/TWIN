# Digital Twin Backend

FastAPI backend service for the Digital Twin application.

## Quick Start

1. **Install dependencies**
   ```bash
   poetry install
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Run the server**
   ```bash
   poetry run uvicorn app.main:app --reload
   ```

4. **View API docs**
   - http://localhost:8000/docs (Swagger UI)
   - http://localhost:8000/redoc (ReDoc)

## Development

### Code Quality
```bash
# Format code
poetry run black app/
poetry run isort app/

# Lint code  
poetry run flake8 app/
poetry run mypy app/

# Run tests
poetry run pytest
```

### Environment Variables

See `.env.example` for all available configuration options.

Required:
- `OPENAI_API_KEY`: Your OpenAI API key
- `OBSIDIAN_VAULT_PATH`: Path to your Obsidian vault

## API Endpoints

- `POST /api/v1/chat/` - Send chat messages
- `GET /api/v1/chat/conversations/` - List conversations  
- `POST /api/v1/search/` - Search knowledge base
- `GET /api/v1/sync/status` - Get sync status
- `POST /api/v1/sync/full-sync` - Trigger full sync
- `GET /api/v1/health/` - Health check
