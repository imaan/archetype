# PRD: Input Engine — Web Article Extraction

**Date:** 2026-03-16
**Status:** Draft
**Depends on:** 00-base-architecture
**Extraction library:** trafilatura

---

## Goal

Extract clean text, metadata, and structure from any web article URL. This is the highest-value extraction type — it covers blog posts, news articles, documentation pages, and most general web content.

---

## Two-Phase Approach

### Phase 1: Standalone Validation Script

Before integrating into the base architecture, validate trafilatura works for our needs with a standalone script.

**File:** `tests/standalone/test_web_article.py`

```python
"""
Standalone test: validate trafilatura extraction quality.
Run directly: uv run python tests/standalone/test_web_article.py
No FastAPI dependency required.
"""
```

**Test against these URL categories:**
1. Standard blog post (e.g., a Medium article)
2. News article (e.g., BBC, NYT)
3. Technical documentation (e.g., Python docs, MDN)
4. Long-form essay
5. Article with heavy ads/sidebars (extraction quality test)
6. Non-article page (product page, landing page — should degrade gracefully)
7. Paywalled article (should extract what's visible)
8. Page that requires JavaScript rendering (known limitation — document it)

**For each test, validate:**
- Title extracted correctly
- Author extracted (if present)
- Date extracted (if present)
- Main body text is clean (no nav, footer, ads, sidebar)
- Images referenced in the article are captured
- Output is valid Markdown

**Record results in:** `tests/standalone/results/web_article_results.md`
- Which URL categories work well
- Which fail or degrade
- Any surprising behaviors
- Decision: proceed with trafilatura or evaluate alternatives

### Phase 2: Handler Integration

**File:** `src/input_engine/handlers/web_article.py`

Implements `BaseHandler` interface:

```python
class WebArticleHandler(BaseHandler):
    async def extract(self, content: str, options: ExtractionOptions) -> ExtractionResult:
        # content is a URL
        # 1. Fetch page with trafilatura.fetch_url()
        # 2. Extract with trafilatura.extract() with metadata=True
        # 3. Map to ExtractionResult

    def can_handle(self, content: str, detected_type: str) -> bool:
        return detected_type == "url"
```

**Metadata to extract:**
```python
metadata = {
    "author": str | None,
    "date": str | None,          # Publication date
    "sitename": str | None,      # e.g., "The Verge"
    "categories": list[str],
    "tags": list[str],
    "language": str | None,
    "word_count": int,
    "reading_time_minutes": int,  # Calculated: word_count / 238
}
```

**Media extraction:**
- Extract image URLs from the article
- Map to MediaRef objects with type="image"
- Include alt text as description where available

---

## Dependencies

```
trafilatura>=1.12.0
```

---

## Acceptance Criteria

### Phase 1 (Standalone)
- [ ] Script runs independently with `uv run python tests/standalone/test_web_article.py`
- [ ] Results documented for all 8 URL categories
- [ ] Clear go/no-go decision on trafilatura recorded

### Phase 2 (Integration)
- [ ] `POST /extract` with a blog URL returns clean article text
- [ ] Title, author, date extracted into metadata
- [ ] Images extracted into media array
- [ ] Non-article URLs return partial content with lower confidence score
- [ ] Invalid URLs return clear error
- [ ] Timeout handling: requests that take > 30s return error, don't hang
- [ ] Tests pass with mocked HTTP responses (no real network calls in CI)

---

## Known Limitations

- **JavaScript-rendered pages**: trafilatura fetches raw HTML. SPAs and JS-heavy pages will return incomplete content. This is a known limitation — document it, don't try to solve it in v1 (headless browser is a v2 concern).
- **Paywalled content**: Only extracts what's in the public HTML. No bypass.
- **Rate limiting**: Some sites block rapid requests. No retry/proxy logic in v1.

---

## Test Plan

```bash
# Phase 1: standalone
uv run python tests/standalone/test_web_article.py

# Phase 2: integration
uv run pytest tests/test_web_article_handler.py

# Manual: real URL
curl -X POST localhost:8000/extract \
  -H "Content-Type: application/json" \
  -d '{"content": "https://example.com/blog/some-article"}'
```

---

## Out of Scope

- JavaScript rendering / headless browser
- Proxy rotation
- Caching fetched pages
- RSS/Atom feed parsing
- Readability fallback (trafilatura has this built in)

---

## What Was Done

_(To be filled after implementation)_
