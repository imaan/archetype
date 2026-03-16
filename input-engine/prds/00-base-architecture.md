# PRD: Input Engine — Base Architecture

**Date:** 2026-03-16
**Status:** Draft
**Depends on:** Nothing (this is the foundation)
**Blocks:** All extraction type PRDs

---

## Goal

Set up the Input Engine as a working FastAPI microservice with a single endpoint, shared data models, a plugin-style handler system, and a plain text/markdown passthrough handler as the first proof of concept.

After this PRD is complete, the service should be runnable, testable, and ready to receive new extraction handlers without touching the core.

---

## What We're Building

### Project Structure

```
input-engine/
├── pyproject.toml              # uv/pip project config
├── Dockerfile
├── docker-compose.yml
├── README.md
├── src/
│   └── input_engine/
│       ├── __init__.py
│       ├── main.py             # FastAPI app, /extract endpoint
│       ├── models.py           # Pydantic request/response schemas
│       ├── detector.py         # Content type auto-detection
│       ├── registry.py         # Handler registration & lookup
│       └── handlers/
│           ├── __init__.py
│           ├── base.py         # Abstract handler interface
│           └── text.py         # Plain text + markdown handler
├── tests/
│   ├── conftest.py             # Shared fixtures, test client
│   ├── test_api.py             # Endpoint integration tests
│   ├── test_detector.py        # Content type detection tests
│   └── test_text_handler.py    # Text/markdown handler tests
└── prds/                       # These PRD files
```

### Core Components

#### 1. Pydantic Models (`models.py`)

```python
class ExtractionRequest(BaseModel):
    content: str                          # URL, raw text, or base64 file
    content_type: str | None = None       # Optional hint: "youtube", "pdf", "url", etc.
    options: ExtractionOptions = ExtractionOptions()

class ExtractionOptions(BaseModel):
    include_metadata: bool = True
    include_media_refs: bool = True

class MediaRef(BaseModel):
    type: str                             # "image", "video", "audio"
    url: str
    description: str | None = None
    timestamp: str | None = None

class ExtractionResult(BaseModel):
    source_type: str                      # "text", "markdown", "youtube", "pdf", etc.
    source_url: str | None = None
    title: str | None = None
    content: str                          # Extracted text in Markdown
    metadata: dict = {}                   # Type-specific metadata
    media: list[MediaRef] = []
    extracted_at: datetime
    extraction_method: str                # "passthrough", "trafilatura", etc.
    confidence: float = 1.0               # 0-1

class ErrorResponse(BaseModel):
    error: str
    detail: str | None = None
    source_type: str | None = None
```

#### 2. Handler Interface (`handlers/base.py`)

```python
class BaseHandler(ABC):
    @abstractmethod
    async def extract(self, content: str, options: ExtractionOptions) -> ExtractionResult:
        ...

    @abstractmethod
    def can_handle(self, content: str, detected_type: str) -> bool:
        ...
```

Every extraction type implements this interface. The handler doesn't know about HTTP, routing, or other handlers. It just takes content in and returns an ExtractionResult.

#### 3. Handler Registry (`registry.py`)

Simple dict mapping content types to handler instances. Handlers self-register. The registry:
- Looks up handler by content type
- Falls back to text handler if no match
- Raises clear error if handler not found and no fallback

```python
registry: dict[str, BaseHandler] = {}

def register(content_type: str, handler: BaseHandler): ...
def get_handler(content_type: str) -> BaseHandler: ...
```

#### 4. Content Type Detector (`detector.py`)

Auto-detects content type from the input string:
- URL patterns: youtube.com → "youtube", instagram.com → "instagram", *.pdf → "pdf", other → "url"
- File extension hints in the content
- Falls back to "text" if nothing matches
- User-provided `content_type` always overrides auto-detection

#### 5. API Endpoint (`main.py`)

```
POST /extract
GET  /health
GET  /handlers    # Lists registered handlers (useful for debugging/docs)
```

The `/extract` endpoint:
1. Receives ExtractionRequest
2. Detects content type (or uses hint)
3. Looks up handler from registry
4. Calls handler.extract()
5. Returns ExtractionResult
6. On error, returns ErrorResponse with 422 or 500

#### 6. Text/Markdown Handler (`handlers/text.py`)

The simplest possible handler — proves the architecture works:
- Plain text: wraps in ExtractionResult as-is
- Markdown: parses frontmatter (if present) into metadata, passes body as content
- Detection: if content doesn't look like a URL and isn't a file, it's text. If it contains frontmatter (`---` header), it's markdown.

Uses `python-frontmatter` for markdown frontmatter parsing (only dependency beyond stdlib).

---

## Acceptance Criteria

- [ ] `uv run uvicorn input_engine.main:app` starts the service on port 8000
- [ ] `POST /extract` with plain text returns a valid ExtractionResult
- [ ] `POST /extract` with markdown (including frontmatter) returns content + metadata
- [ ] `GET /health` returns `{"status": "ok"}`
- [ ] `GET /handlers` returns list of registered handler types
- [ ] Content type auto-detection correctly identifies: URLs, text, markdown
- [ ] All tests pass: `uv run pytest`
- [ ] `docker compose up` builds and runs the service
- [ ] OpenAPI docs available at `/docs` (FastAPI auto-generates this)
- [ ] A new handler can be added by: creating a file in handlers/, implementing BaseHandler, registering in __init__.py — no changes to main.py or models.py needed

---

## Test Plan

```bash
# Unit: text handler
echo "Hello world" | curl -X POST localhost:8000/extract -d '{"content": "Hello world"}'
# → ExtractionResult with source_type="text", content="Hello world"

# Unit: markdown handler
curl -X POST localhost:8000/extract -d '{"content": "---\ntitle: Test\n---\n# Hello\nBody text"}'
# → ExtractionResult with source_type="markdown", metadata={"title": "Test"}

# Unit: auto-detection
curl -X POST localhost:8000/extract -d '{"content": "https://youtube.com/watch?v=abc"}'
# → Error: youtube handler not registered (or fallback behavior)

# Unit: content_type override
curl -X POST localhost:8000/extract -d '{"content": "some text", "content_type": "text"}'
# → Forces text handler regardless of detection

# Integration: health check
curl localhost:8000/health
# → {"status": "ok"}
```

---

## Out of Scope

- LLM enhancement (separate concern, added later)
- File upload support (URL + raw text for v1)
- Authentication / rate limiting (not needed for local/side project use)
- Any extraction type beyond text/markdown (each gets its own PRD)
- Persistent storage / caching
- Async job queue

---

## Shipping Checklist

- [ ] Code written and tests passing
- [ ] Docker build succeeds
- [ ] README with setup instructions and example curl commands
- [ ] OpenAPI spec accessible at /docs

---

## What Was Done

_(To be filled after implementation)_
