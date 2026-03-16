# PRD: Input Engine — Instagram Extraction

**Date:** 2026-03-16
**Status:** Draft
**Depends on:** 00-base-architecture
**Extraction library:** instaloader

---

## Goal

Extract caption, media, and metadata from Instagram posts and reels. This is the most fragile extraction type — Instagram actively fights scraping. The implementation must be designed for graceful degradation.

---

## Why This Is Different

Instagram extraction is inherently unreliable. Unlike YouTube (which has a public transcript API) or web articles (which serve HTML), Instagram:
- Aggressively blocks automated requests
- Changes its HTML/API structure regularly
- Rate-limits anonymous access to ~1-2 requests per 30 seconds
- Risks account locks for authenticated access

**Design principle: the Input Engine should work fine with Instagram extraction completely broken.** It's a nice-to-have, not a dependency.

---

## Two-Phase Approach

### Phase 1: Standalone Validation Script

**File:** `tests/standalone/test_instagram.py`

**Test against these content categories:**
1. Public photo post (single image)
2. Public carousel post (multiple images)
3. Public reel (video)
4. Post with long caption + hashtags
5. Post with tagged users and location
6. Private account post (should fail gracefully)
7. Invalid/deleted post URL
8. Instagram Story link (not supported — document)

**For each test, validate:**
- Caption text extracted
- Image/video URLs captured
- Like count, comment count available
- Hashtags parsed from caption
- Location data extracted (if present)
- Posted date extracted

**Important: record rate limiting behavior.**
- How many requests before throttling?
- Does authenticated vs anonymous matter?
- How long do cooldown periods last?

**Record results in:** `tests/standalone/results/instagram_results.md`

### Phase 2: Handler Integration

**File:** `src/input_engine/handlers/instagram.py`

```python
class InstagramHandler(BaseHandler):
    async def extract(self, content: str, options: ExtractionOptions) -> ExtractionResult:
        # content is an Instagram URL
        # 1. Parse shortcode from URL
        # 2. Fetch post metadata via instaloader
        # 3. Extract caption, media URLs, metadata
        # 4. For reels: extract video URL (for potential audio transcription by Processing Engine)
        # 5. Map to ExtractionResult

    def can_handle(self, content: str, detected_type: str) -> bool:
        return detected_type == "instagram"
```

**URL patterns to detect:**
```
instagram.com/p/SHORTCODE/            # Photo/carousel post
instagram.com/reel/SHORTCODE/         # Reel
instagram.com/reels/SHORTCODE/        # Reel (alternate)
www.instagram.com/p/SHORTCODE/
```

**Metadata to extract:**
```python
metadata = {
    "shortcode": str,
    "post_type": str,               # "photo", "carousel", "reel"
    "author": str,                  # Username
    "author_full_name": str | None,
    "posted_at": str,               # ISO 8601
    "like_count": int | None,       # May be hidden
    "comment_count": int | None,
    "location": str | None,
    "hashtags": list[str],
    "mentioned_users": list[str],
    "is_video": bool,
    "video_duration": float | None, # Seconds, for reels
}
```

**Content format (Markdown):**
```markdown
# Instagram Post by @username

**Posted:** 2026-03-15
**Type:** Reel (0:32)
**Location:** London, UK

---

The full caption text here, including #hashtags and @mentions.

---

**Hashtags:** #fitness #aclrehab #exercise
**Mentioned:** @trainer_name
```

**Media refs:**
```python
media = [
    MediaRef(type="image", url="https://...", description="Post image 1 of 3"),
    # or for reels:
    MediaRef(type="video", url="https://...", description="Reel video (0:32)"),
    MediaRef(type="image", url="https://...", description="Reel thumbnail"),
]
```

---

## Resilience Design

```python
class InstagramHandler(BaseHandler):
    # Retry once with backoff
    MAX_RETRIES = 1
    RETRY_DELAY = 5  # seconds

    async def extract(self, content, options):
        try:
            return await self._extract(content, options)
        except RateLimitError:
            return ExtractionResult(
                source_type="instagram",
                content="[Rate limited — try again in a few minutes]",
                confidence=0.0,
                extraction_method="instaloader_rate_limited",
                ...
            )
        except LoginRequiredError:
            return ExtractionResult(
                source_type="instagram",
                content="[Login required — post may be private]",
                confidence=0.0,
                ...
            )
        except Exception as e:
            return ExtractionResult(
                source_type="instagram",
                content=f"[Extraction failed: {str(e)}]",
                confidence=0.0,
                ...
            )
```

The handler **never raises** — it always returns an ExtractionResult, even on failure. Confidence=0.0 signals to the caller that extraction failed.

---

## Authentication

Instaloader supports authenticated sessions for better rate limits and access to some content. For v1:
- **Anonymous by default** (no config needed to get started)
- **Optional session file path** via environment variable: `INSTAGRAM_SESSION_FILE`
- Document how to create a session file (interactive instaloader login)
- Warn users about account lock risk

---

## Dependencies

```
instaloader>=4.13.0
```

---

## Acceptance Criteria

### Phase 1 (Standalone)
- [ ] Script extracts caption from a public photo post
- [ ] Script extracts caption + video URL from a public reel
- [ ] Rate limiting behavior documented
- [ ] Private posts fail gracefully (not crash)
- [ ] Results documented with honest assessment of reliability

### Phase 2 (Integration)
- [ ] `POST /extract` with Instagram URL returns caption + media
- [ ] Reel video URLs included in media refs
- [ ] Hashtags and mentions parsed into metadata
- [ ] Rate-limited requests return confidence=0.0, not an error
- [ ] Private/deleted posts return confidence=0.0, not an error
- [ ] Tests pass with mocked instaloader responses

---

## Known Limitations

- **Reliability**: Instagram extraction will break periodically. This is not a bug — it's the nature of scraping a platform that doesn't want to be scraped.
- **Rate limiting**: Anonymous access is severely rate-limited. Authenticated is better but risks account locks.
- **Stories**: Not supported. Stories are ephemeral and require authentication.
- **Carousel images**: May only get the first image without authentication.
- **Video transcription**: The Input Engine extracts the video URL. Transcribing reel audio is a Processing Engine concern (send video URL to YouTube handler's Tier 2 whisper pipeline, or similar).

---

## Test Plan

```bash
# Phase 1: standalone (will hit real Instagram — run manually, not in CI)
uv run python tests/standalone/test_instagram.py

# Phase 2: integration (mocked)
uv run pytest tests/test_instagram_handler.py
```

Note: Instagram tests MUST use mocked responses in CI. Real Instagram requests are too unreliable and rate-limited for automated testing.

---

## Out of Scope

- Instagram Stories extraction
- Comment extraction
- Profile/account extraction
- Instagram API (Graph API) integration
- Proxy rotation
- Audio transcription of reels (Processing Engine concern)

---

## What Was Done

_(To be filled after implementation)_
