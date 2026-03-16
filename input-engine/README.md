# Input Engine

Content extraction microservice — extract structured data from any content type.

## Quick Start

```bash
# Install dependencies
uv sync --all-extras

# Run the server
uv run uvicorn input_engine.main:app --reload --port 8000

# Run tests
uv run pytest
```

## Docker

```bash
docker compose up
```

## API

### `POST /extract`

Extract structured data from content.

```bash
# Plain text
curl -X POST http://localhost:8000/extract \
  -H "Content-Type: application/json" \
  -d '{"content": "Hello world"}'

# Markdown with frontmatter
curl -X POST http://localhost:8000/extract \
  -H "Content-Type: application/json" \
  -d '{"content": "---\ntitle: My Post\n---\n# Hello\nBody text"}'

# With content type override
curl -X POST http://localhost:8000/extract \
  -H "Content-Type: application/json" \
  -d '{"content": "some text", "content_type": "text"}'
```

### `GET /health`

Health check endpoint.

### `GET /handlers`

List registered extraction handlers.

## Adding a New Handler

1. Create a file in `src/input_engine/handlers/` implementing `BaseHandler`
2. Implement `can_handle()` and `extract()` methods
3. Register it in `handlers/__init__.py`

No changes to `main.py` or `models.py` needed.
