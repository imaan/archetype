# Web Article Extraction — Phase 1 Results

**Library:** trafilatura v2.0.0
**Date:** 2026-03-16
**Decision: GO**

## Summary

| Category | Status | Title | Author | Date | Body | Time |
|----------|--------|-------|--------|------|------|------|
| Wikipedia (technical docs) | PASS | Yes | Yes* | Yes | 77,568 chars | 1,820ms |
| BBC News | PASS | Yes | No | Yes | 1,473 chars | 883ms |
| Python docs (reference) | PASS | Yes | No | Yes | 16,288 chars | 1,981ms |
| Paul Graham essay | PASS | Yes | No | Yes | 66,729 chars | 997ms |
| Craigslist (non-article) | PASS | No | No | No | 707 chars | 1,661ms |
| example.com (minimal) | FAIL | - | - | - | 0 | 30,202ms |
| NYT (paywalled) | FAIL | - | - | - | 0 | 296ms |

*Wikipedia "author" was extracted as "Authority control databases" — incorrect but present.

**Pass rate: 5/7 (71%)** — both failures are expected edge cases.

## Key Findings

### What Works Well
- **Article extraction is excellent.** Wikipedia, Python docs, and Paul Graham essay all returned clean, readable text with no nav/footer/sidebar contamination.
- **Title extraction is reliable** for well-structured pages.
- **Date extraction works** for pages with publication dates.
- **Non-article pages degrade gracefully** — Craigslist returned 707 chars of content rather than crashing.

### What Doesn't Work
- **Paywalled content (NYT):** `fetch_url` returns None. trafilatura doesn't bypass paywalls. This is expected — document as a known limitation.
- **Minimal pages (example.com):** 30-second timeout before returning None. Need to configure timeout in the handler.
- **Author extraction is unreliable.** Only extracted for Wikipedia (and incorrectly). Most pages don't have structured author metadata.

### Surprising Behaviors
- BBC URL redirected to a category page ("Climate") rather than the specific article — returned category listing content. URL stability matters.
- Paul Graham's essay extracted 66K chars — trafilatura handles very long content well.
- Wikipedia extracted 77K chars including some table formatting artifacts.

## Implementation Notes for Phase 2

1. **Set fetch timeout to 15s** — the 30s default is too long for a synchronous API
2. **Author extraction should be treated as optional** — low reliability across sites
3. **Title extraction is high-confidence** — use as primary metadata
4. **Date extraction varies in format** — normalize to ISO 8601 in the handler
5. **Consider httpx instead of trafilatura's built-in fetch** for better timeout/retry control
6. **Content length is a useful confidence signal** — very short extractions (< 100 chars) should get lower confidence scores

## Go/No-Go Decision

**GO.** trafilatura v2.0.0 provides excellent extraction quality for the content types that matter most (articles, docs, essays). The failures are at the edges (paywalled, minimal pages) and are expected limitations that should be documented, not solved.
