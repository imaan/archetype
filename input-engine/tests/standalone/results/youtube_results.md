# YouTube Extraction — Phase 1 Results

**Libraries:** youtube-transcript-api v1.0.3 + yt-dlp v2025.3.14
**Date:** 2026-03-16
**Decision: GO (Tier 1 sufficient for v1)**

## Summary

| Category | Transcript | Type | Metadata | Chapters | Time |
|----------|-----------|------|----------|----------|------|
| Rick Astley (manual captions) | PASS | manual | PASS | - | 2.5s |
| Me at the zoo (first YT video) | PASS | manual | PASS | 3 | 1.8s |
| HEYYEYAAEYAAAEYAEYAA | PASS | auto (nl) | PASS | - | 2.2s |
| freeCodeCamp Python (4.4hr) | PASS | manual | PASS | 35 | 1.7s |
| Gangnam Style (Korean) | PASS | auto (ko) | PASS | - | 2.1s |
| Invalid video ID | FAIL (expected) | - | FAIL (expected) | - | 0.9s |

**Pass rate: 5/5 valid videos (100%)**

## Key Findings

### Transcript Extraction (youtube-transcript-api)
- **Excellent reliability.** All 5 valid videos returned transcripts.
- **Manual captions preferred.** The API correctly prioritizes manual captions over auto-generated.
- **Long content handled well.** The 4.4-hour freeCodeCamp tutorial returned 259K chars of transcript.
- **Non-English works.** Gangnam Style returned Korean auto-captions. The API supports language fallback.
- **Auto-generated quality varies.** The Dutch auto-captions for HEYYEYAAEYAAAEYAEYAA were mostly `[Muziek]` tags — expected for music videos.
- **Speed is good.** 650-1000ms per transcript fetch.

**IMPORTANT API NOTE:** youtube-transcript-api v1.0.0+ changed to instance-based API:
```python
# Old (broken): YouTubeTranscriptApi.list_transcripts(video_id)
# New (correct): YouTubeTranscriptApi().list(video_id)
```

### Metadata Extraction (yt-dlp)
- **Comprehensive.** Title, channel, duration, view count, description, chapters, thumbnail URL — all available.
- **Chapters extracted reliably.** freeCodeCamp video returned 35 chapters with titles and timestamps.
- **Speed is acceptable.** 1-1.5s per video (runs as subprocess, parses JSON).
- **Graceful failure.** Invalid video IDs return clear error messages.

### Tier 1 vs Tier 2 Decision
**Tier 1 (captions only) is sufficient for v1.** Caption availability was 100% across our test set. Tier 2 (audio transcription via faster-whisper) adds complexity, large model downloads, and slow CPU processing. Defer to v2.

## Implementation Notes for Phase 2

1. **Use instance-based API:** `ytt_api = YouTubeTranscriptApi()` then `ytt_api.list(video_id)` or `ytt_api.fetch(video_id)`
2. **Transcript priority:** Try manual English first, then auto-generated English, then any available language
3. **yt-dlp for metadata:** `yt-dlp --dump-json --no-download` is fast and reliable
4. **Timestamps are critical:** Include `[M:SS]` timestamps in the markdown output for cross-referencing
5. **Chapter markers:** Include in both metadata dict and as a formatted section in content
6. **IP blocking in production:** YouTube blocks cloud IPs for transcript API. Works locally. Production needs proxy (v2 concern).
7. **Error handling:** Both libraries provide specific exception types — use them for differentiated error messages

## Go/No-Go Decision

**GO.** youtube-transcript-api + yt-dlp provide excellent extraction quality for the YouTube use case. Tier 1 (captions) covers all tested scenarios. The combination gives us both the spoken content (transcript) and rich metadata (chapters, description, thumbnails) needed for the Input Engine.
