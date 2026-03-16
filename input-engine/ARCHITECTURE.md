# Input Engine - Architectural Review

**Date:** 2026-03-16
**Status:** Proposal (pre-implementation)
**Context:** First engine of the Router system. Standalone microservice that accepts any content type and extracts structured data from it.

---

## What the Input Engine Does

Takes in content (a URL, a file, raw text, an email) and outputs a structured, normalized representation of the core information in that content. Nothing more.

It does **not** decide what to do with the content (that's the Processing Engine).
It does **not** know about the user's projects or goals (that's the Context Engine).
It does **not** push anything anywhere (that's the Output Engine).

**Input**: content + content type hint (optional)
**Output**: structured extraction result (text, metadata, media references)

---

## Key Architectural Questions

### 1. Language & Framework

| Option | Pros | Cons |
|--------|------|------|
| **Python + FastAPI** | Best parsing ecosystem by far. yt-dlp, pymupdf, trafilatura, whisper all native Python. Auto-generates OpenAPI docs. Async. Huge community. | Deployment slightly heavier than Go/Node. |
| TypeScript + Hono/Express | Matches Invisible Inbox stack. Good for web-native deployments. | Content parsing ecosystem is weaker. yt-dlp/whisper require subprocess calls. Fighting the language for this task. |
| Go | Fast, small binaries, great for microservices. | Worst ecosystem for content parsing. Would shell out for everything. Wrong tool for this job. |

**Recommendation: Python + FastAPI.**

The input engine is fundamentally a *parsing* service. Python's ecosystem for content extraction is years ahead of everything else. FastAPI gives us automatic OpenAPI docs (great for the modular/forkable goal), Pydantic models for clean contracts, and async for I/O-heavy extraction work.

The other Router engines could be in different languages — that's the point of microservices. But this one should be Python.

### 2. Content Extraction Strategy

**The core question: libraries first, or LLM first?**

**Option A: Library-first (recommended)**
```
Content → Specialized library extracts raw text/metadata → Structured output
                                                        ↘ Optional: LLM enhances/summarizes
```
- Deterministic, fast, free for most content types
- Libraries handle 80%+ of extraction well
- LLM only needed for understanding, not extraction
- Cost: $0 for basic extraction

**Option B: LLM-first**
```
Content → Convert to format LLM can read → Send to multimodal LLM → Structured output
```
- Simpler code (one path for everything)
- Handles edge cases better (infographics, unusual layouts)
- Cost: $0.10-3.00 per 1M tokens depending on model
- Slower, non-deterministic, vendor-dependent

**Option C: Hybrid (recommended for v2)**
```
Content → Library extraction → If confidence low → LLM fallback
                             → If confidence high → Return directly
```

**Recommendation: Start with Option A (library-first). Add LLM enhancement as an optional flag.**

For a side project, deterministic + free beats smart + expensive. The extraction libraries are genuinely good now. Save LLM calls for the Processing Engine where they actually add value (understanding content in context).

### 3. Extraction Libraries Per Content Type

| Content Type | Primary Library | Why | Fallback |
|---|---|---|---|
| **Plain text** | Passthrough | Already structured | — |
| **Markdown** | Passthrough + frontmatter parser | Already structured | — |
| **PDF** | `pymupdf4llm` | Outputs clean Markdown, handles tables, fast (0.12s) | `pdfplumber` for surgical table work |
| **Web articles** | `trafilatura` | F1: 0.958 benchmark winner. Extracts text + metadata (author, date, tags) | `newspaper4k` |
| **General URLs** | `trafilatura` → fallback `html-to-markdown` | Article extraction first, raw HTML conversion if that fails | — |
| **YouTube** | `youtube-transcript-api` + `yt-dlp` | Captions + metadata. No API key needed. | `faster-whisper` when no captions exist |
| **Instagram** | `instaloader` | Best available, handles posts + reels + captions | Will break periodically — design for graceful degradation |
| **Email** | Python stdlib `email` | Zero dependencies, RFC-compliant, handles MIME + attachments | — |

### 4. API Design

**Option A: REST (recommended)**
```
POST /extract
{
  "content": "<url or raw content>",
  "content_type": "youtube",       // optional hint, auto-detected if omitted
  "options": {
    "include_metadata": true,
    "include_media_refs": true
  }
}
```
- Simple, well-understood, easy to test with curl
- FastAPI auto-generates interactive docs
- Each content type is an internal handler, but one unified endpoint

**Option B: One endpoint per content type**
```
POST /extract/youtube
POST /extract/pdf
POST /extract/url
```
- More explicit routing
- Easier to version/deprecate individual extractors
- But adds surface area and forces the caller to know the content type

**Option C: GraphQL**
- Overkill for a single-purpose service
- Skip

**Recommendation: Option A with auto-detection.** One endpoint, content type auto-detected from the input (URL patterns, MIME types, file extensions). The hint parameter lets callers override when auto-detection is wrong. Internally, each content type has its own handler module — easy to add new ones.

### 5. Output Schema

Every extraction returns the same shape:

```python
class ExtractionResult:
    source_type: str           # "youtube", "pdf", "url", "email", etc.
    source_url: str | None     # Original URL if applicable
    title: str | None
    content: str               # The core extracted text (Markdown)
    summary: str | None        # Brief summary (if LLM enhancement enabled)
    metadata: dict             # Type-specific metadata
    media: list[MediaRef]      # Images, videos, audio referenced in content
    extracted_at: datetime
    extraction_method: str     # "trafilatura", "pymupdf4llm", etc. (transparency)
    confidence: float          # 0-1, how confident we are in extraction quality

class MediaRef:
    type: str                  # "image", "video", "audio"
    url: str
    description: str | None
    timestamp: str | None      # For video timestamps like "2:34"
```

**Why a uniform schema matters:** The Processing Engine doesn't need to know whether content came from a YouTube video or a PDF. It just gets structured text + metadata. This is what makes the engines truly modular.

### 6. Content Type Auto-Detection

```
Input → Is it a URL?
         ├─ youtube.com / youtu.be → YouTube handler
         ├─ instagram.com → Instagram handler
         ├─ *.pdf (URL ending) → Download → PDF handler
         ├─ Other URL → Web article handler
         └─ No
              ├─ File upload?
              │    ├─ .pdf → PDF handler
              │    ├─ .md → Markdown handler
              │    ├─ .eml / .msg → Email handler
              │    └─ Other → Plain text handler
              └─ Raw text → Plain text handler
```

### 7. Async Processing

**Some extractions are fast (< 1s), some are slow (video transcription: 30s+).**

**Option A: Synchronous only (recommended for v1)**
- All requests block until extraction completes
- Simple to implement and test
- FastAPI's async handles concurrent requests fine
- Timeout at 120s, which covers even whisper transcription

**Option B: Sync for fast, async job queue for slow**
- Returns job ID for slow extractions, poll for result
- More complex but better UX for video transcription
- Needs Redis/RQ or similar

**Option C: Everything async**
- Overkill for most content types

**Recommendation: Start synchronous. Add async for YouTube/Instagram video transcription in v2 if needed.** The overhead of a job queue isn't worth it until you have a consumer that actually needs non-blocking behavior.

### 8. Storage & State

**The input engine should be stateless.**

It receives content, extracts data, returns structured output. No database. No user accounts. No session state. This makes it:
- Easy to deploy (no DB migrations, no persistence layer)
- Easy to test (pure input → output)
- Easy to fork (no infrastructure dependencies)
- Easy to scale (any instance can handle any request)

If caching is needed later (e.g., don't re-extract the same YouTube video twice), add an optional Redis/SQLite cache layer. But not in v1.

### 9. Deployment

| Option | Pros | Cons |
|--------|------|------|
| **Docker container** | Portable, reproducible, works everywhere. Perfect for forkability. | Slightly more setup than bare metal. |
| Railway/Render | One-click deploy, free tier. Good for public demo. | Vendor lock-in for a "forkable" project. |
| Local only | Simplest. No infra to manage. | Can't receive webhooks or serve other devices. |

**Recommendation: Docker-first, with a simple `docker-compose.yml`.** Matches the Archetype vision of forkable apps. Anyone can `docker compose up` and have it running. Deploy to Railway/Render/Fly for a public instance when needed.

### 10. Testing Strategy

For a side project optimizing for shipping cadence:

- **Unit tests per handler**: Each content type handler gets a test with a fixture file (sample PDF, sample email, etc.) or mocked HTTP response (YouTube, Instagram, web URLs)
- **Integration test**: Hit the `/extract` endpoint with real content, verify the output schema
- **No mocking the extraction libraries themselves** — test that they actually parse correctly
- **pytest + pytest-asyncio** — standard Python testing

Sample test fixtures to include in the repo:
```
tests/fixtures/
  sample.pdf
  sample.eml
  sample.md
  sample_article.html
```

YouTube/Instagram tests mock HTTP responses (don't hit real APIs in CI).

---

## Recommended Tech Stack Summary

```
Language:       Python 3.12+
Framework:      FastAPI + Uvicorn
Validation:     Pydantic v2
PDF:            pymupdf4llm
Web articles:   trafilatura
YouTube:        youtube-transcript-api + yt-dlp
Instagram:      instaloader
Email:          Python stdlib email
Audio (v2):     faster-whisper
LLM (optional): Anthropic Claude / Google Gemini Flash
Testing:        pytest + pytest-asyncio
Packaging:      uv (fast Python package manager)
Containerization: Docker
CI:             GitHub Actions
```

---

## Shipping Plan (Optimized for Daily Shipping)

The side project constraint changes how we build this. Instead of "design everything, build everything, ship once," we want **tiny incremental ships that each produce a working, testable, postable artifact**.

### Phase 1: Skeleton (1 session)
- FastAPI app with `/extract` endpoint
- Plain text handler only (passthrough)
- Pydantic models for request/response
- Docker setup
- README with "what this is"
- **Shippable**: Working API that accepts text and returns structured output

### Phase 2: Web Articles (1 session)
- Trafilatura handler
- URL auto-detection
- Metadata extraction (author, date, title)
- Test with 5 real article URLs
- **Shippable**: "Input Engine now extracts articles from any URL"

### Phase 3: YouTube (1-2 sessions)
- youtube-transcript-api for captions
- yt-dlp for metadata
- Handle both Shorts and long-form
- **Shippable**: "Paste a YouTube link, get the full transcript + metadata"

### Phase 4: PDF (1 session)
- pymupdf4llm handler
- File upload support on the endpoint
- Test with varied PDFs (text-heavy, tables, mixed)
- **Shippable**: "Upload a PDF, get clean Markdown back"

### Phase 5: Email + Markdown (1 session)
- Email parser (stdlib)
- Markdown passthrough with frontmatter
- **Shippable**: "Forward an email or drop a Markdown file — content extracted"

### Phase 6: Instagram (1-2 sessions)
- Instaloader integration
- Graceful degradation when it breaks
- Caption + media extraction
- **Shippable**: "Share an Instagram post link, get the content"

### Phase 7: LLM Enhancement (1 session)
- Optional `enhance` flag on `/extract`
- Sends extracted text to LLM for summary/entity extraction
- Configurable LLM provider (Claude, Gemini, etc.)
- **Shippable**: "Now with AI-powered content summarization"

Each phase is independently valuable and demo-able. Skip or reorder based on what you actually need first.

---

## Open Questions for You

1. **Package manager**: `uv` (fast, modern) or `pip` + `venv` (everyone knows it)?
2. **Do you want file upload support from v1**, or is URL + raw text enough to start?
3. **Instagram priority**: It's the most fragile extractor. Worth including early, or defer until the core is solid?
4. **Naming**: Is "Input Engine" the final name, or something catchier for the repo/package?
