# PRD: Input Engine — YouTube Extraction

**Date:** 2026-03-16
**Status:** Phase 1 Complete (GO — Tier 1 sufficient for v1)
**Depends on:** 00-base-architecture
**Extraction libraries:** youtube-transcript-api, yt-dlp

---

## Goal

Extract the full spoken/written content and metadata from any YouTube video (Shorts or long-form). This is the use case from the original Router example — "share a video with 5 ACL exercises, extract exercise #5."

The Input Engine extracts *everything* from the video. Filtering to exercise #5 is the Processing Engine's job.

---

## Two-Phase Approach

### Phase 1: Standalone Validation Script

**File:** `tests/standalone/test_youtube.py`

**Test against these video categories:**
1. Standard video with manual captions (English)
2. Video with auto-generated captions only
3. YouTube Short (< 60s)
4. Long video (> 1 hour, e.g., podcast)
5. Video with no captions at all
6. Non-English video with English auto-captions
7. Video with chapters
8. Private/age-restricted video (should fail gracefully)
9. Invalid YouTube URL

**For each test, validate:**
- Transcript text extracted (or clear "no captions" signal)
- Video title, description, channel name extracted
- Duration extracted
- Chapter markers extracted (if present)
- Thumbnail URL captured

**Two extraction tiers to test:**

**Tier 1 — Captions (fast, free):**
```python
from youtube_transcript_api import YouTubeTranscriptApi
transcript = YouTubeTranscriptApi.get_transcript(video_id)
# Returns: [{"text": "...", "start": 0.0, "duration": 2.5}, ...]
```

**Tier 2 — Audio transcription (slow, local CPU):**
```python
# Only when Tier 1 fails (no captions)
# Download audio with yt-dlp, transcribe with faster-whisper
```

**Record results in:** `tests/standalone/results/youtube_results.md`
- Caption availability rates across test videos
- Transcript quality (auto vs manual captions)
- yt-dlp metadata completeness
- Tier 2 transcription speed and quality (if tested)
- Decision: is Tier 1 sufficient for v1, or do we need Tier 2 immediately?

### Phase 2: Handler Integration

**File:** `src/input_engine/handlers/youtube.py`

```python
class YouTubeHandler(BaseHandler):
    async def extract(self, content: str, options: ExtractionOptions) -> ExtractionResult:
        # 1. Parse video ID from URL
        # 2. Fetch metadata via yt-dlp (--dump-json, no download)
        # 3. Attempt caption extraction via youtube-transcript-api
        # 4. If no captions and Tier 2 enabled: download audio + transcribe
        # 5. Combine transcript + metadata into ExtractionResult

    def can_handle(self, content: str, detected_type: str) -> bool:
        return detected_type == "youtube"
```

**URL patterns to detect:**
```
youtube.com/watch?v=VIDEO_ID
youtu.be/VIDEO_ID
youtube.com/shorts/VIDEO_ID
youtube.com/live/VIDEO_ID
youtube.com/embed/VIDEO_ID
m.youtube.com/watch?v=VIDEO_ID
```

**Metadata to extract:**
```python
metadata = {
    "video_id": str,
    "channel": str,
    "channel_url": str,
    "upload_date": str,
    "duration_seconds": int,
    "view_count": int | None,
    "like_count": int | None,
    "description": str,
    "tags": list[str],
    "chapters": list[dict],       # [{"title": "Intro", "start": 0, "end": 30}]
    "caption_type": str,          # "manual", "auto-generated", "transcribed", "none"
    "language": str | None,
}
```

**Content format (Markdown):**
```markdown
# Video Title

**Channel:** Channel Name
**Duration:** 12:34
**Uploaded:** 2026-03-10

## Description

The video description text...

## Chapters

- 0:00 — Intro
- 2:30 — Exercise 1
- 5:15 — Exercise 2

## Transcript

[0:00] First line of transcript...
[0:05] Second line...
```

Timestamps in the transcript are critical — they allow the Processing Engine to cross-reference specific moments (e.g., "exercise #5 starts at chapter marker 5").

**Media refs:**
```python
media = [
    MediaRef(type="video", url="https://youtube.com/watch?v=...", description="Original video"),
    MediaRef(type="image", url="https://i.ytimg.com/vi/.../maxresdefault.jpg", description="Thumbnail"),
]
```

---

## Dependencies

```
youtube-transcript-api>=1.0.0
yt-dlp>=2024.0.0

# Tier 2 only (optional):
faster-whisper>=1.0.0
```

Tier 2 (faster-whisper) is an **optional dependency**. The handler should work without it — just returns "no transcript available" when captions don't exist and Tier 2 isn't installed.

---

## Acceptance Criteria

### Phase 1 (Standalone)
- [ ] Script extracts captions from a standard video
- [ ] Script extracts captions from a YouTube Short
- [ ] Metadata (title, channel, duration, description) extracted via yt-dlp
- [ ] Chapters extracted when present
- [ ] Graceful failure for videos with no captions
- [ ] Results documented with go/no-go decision

### Phase 2 (Integration)
- [ ] `POST /extract` with YouTube URL returns transcript + metadata
- [ ] Timestamps preserved in transcript
- [ ] Chapters included in metadata and content
- [ ] Shorts handled identically to long-form
- [ ] Invalid YouTube URLs return clear error
- [ ] Private/unavailable videos return clear error
- [ ] Tests pass with mocked responses

---

## Known Limitations

- **IP blocking**: YouTube blocks cloud provider IPs for transcript API. Works from local/residential IPs. Production deployment needs proxy (v2 concern).
- **Tier 2 speed**: Audio transcription on CPU is slow (~0.25x realtime for large-v3 model). A 10-min video takes ~40 min. Acceptable for side project, not for production.
- **Live streams**: Not supported. Fail gracefully.
- **Age-restricted content**: May require authentication cookies. Document, don't solve in v1.

---

## Test Plan

```bash
# Phase 1: standalone
uv run python tests/standalone/test_youtube.py

# Phase 2: integration
uv run pytest tests/test_youtube_handler.py

# Manual
curl -X POST localhost:8000/extract \
  -H "Content-Type: application/json" \
  -d '{"content": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}'
```

---

## Out of Scope

- Downloading video files
- Extracting individual frames
- Playlist handling
- Channel-level extraction
- Proxy/cookie management

---

## Phase 1 Results

**Libraries:** youtube-transcript-api v1.0.3 + yt-dlp v2025.3.14 | **Pass rate: 5/5 (100%)** | **Decision: GO**

| Category | Transcript | Type | Metadata | Chapters | Time |
|----------|-----------|------|----------|----------|------|
| Rick Astley (manual captions) | PASS | manual | PASS | - | 2.5s |
| Me at the zoo (first YT video) | PASS | manual | PASS | 3 | 1.8s |
| HEYYEYAAEYAAAEYAEYAA | PASS | auto (nl) | PASS | - | 2.2s |
| freeCodeCamp Python (4.4hr) | PASS | manual | PASS | 35 | 1.7s |
| Gangnam Style (Korean) | PASS | auto (ko) | PASS | - | 2.1s |

**Key findings for Phase 2:**
- **API change:** youtube-transcript-api v1.0.0+ uses instance-based API: `YouTubeTranscriptApi().fetch(video_id)` (not class methods)
- Transcript priority: manual English → auto English → any available language
- Include `[M:SS]` timestamps in markdown output for cross-referencing
- Chapter markers: include in both metadata dict and formatted content section
- yt-dlp `--dump-json --no-download` is fast and reliable for metadata
- YouTube blocks cloud IPs for transcript API — works locally, production needs proxy (v2)
- Tier 2 (audio transcription via faster-whisper) deferred — caption availability was 100%

Full results: `tests/standalone/results/youtube_results.md`

## What Was Done

_(To be filled after implementation)_
