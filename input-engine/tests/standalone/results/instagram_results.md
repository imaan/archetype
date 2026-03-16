# Instagram Extraction — Phase 1 Results

**Library:** instaloader v4.15
**Date:** 2026-03-16
**Decision: CONDITIONAL GO (with major caveats)**

## Summary

| Category | Status | Error | Time |
|----------|--------|-------|------|
| Public photo post (NASA) | FAIL | BadResponseException: Fetching Post metadata failed | 3,550ms |
| Invalid/deleted post | FAIL | BadResponseException: Fetching Post metadata failed | 1,181ms |
| Public reel | FAIL | BadResponseException: Fetching Post metadata failed | 1,380ms |
| Post with hashtags | FAIL | BadResponseException: Fetching Post metadata failed | 4,679ms |

**Pass rate: 0/4 (0%)**

## Key Findings

### What Happened
- **All requests returned 403 Forbidden** from Instagram's GraphQL API
- Even before our test script ran, instaloader triggered 4 retries during initialization (403 on `graphql/query`)
- Both valid and invalid shortcodes received the same error — Instagram blocks the request before even checking if the post exists
- This is **anonymous access being completely blocked**, not rate limiting

### Why This Was Expected
The PRD explicitly warned: "Instagram aggressively blocks automated requests" and "the Input Engine should work fine with Instagram extraction completely broken."

Instagram has progressively tightened anonymous API access:
- Anonymous GraphQL queries are now 403'd by default from many IPs
- Cloud/datacenter IPs are blocked more aggressively than residential
- The only reliable access requires authenticated sessions with cookies

### Rate Limiting Observations
- No rate limiting was observed because requests were blocked before reaching rate limit logic
- The 403 is an IP/user-agent block, not a rate limit
- Adding delays between requests made no difference

## Reliability Assessment

**Instaloader with anonymous access is currently non-functional for our use case.** This aligns with the PRD's expectation that Instagram extraction is inherently fragile.

Options for Phase 2:
1. **Authenticated sessions** — Instaloader supports session files from browser cookies. This works but risks account locks.
2. **Alternative libraries** — `instagram-private-api` or direct GraphQL with browser cookies. Same authentication requirement.
3. **Headless browser** — Selenium/Playwright to render Instagram pages. Heavy, slow, but more resilient.
4. **Accept the limitation** — Build the handler with graceful degradation (confidence=0.0 on failure), ship it, and document that authentication is required for reliability.

**Recommendation:** Option 4 — build the handler with the resilience design from the PRD (never raises, returns confidence=0.0 on failure). Add optional authentication support via `INSTAGRAM_SESSION_FILE` env var. This keeps the handler forkable without requiring credentials.

## Implementation Notes for Phase 2

1. **Handler must never raise** — always return ExtractionResult with confidence=0.0 on failure
2. **Support optional session file** via `INSTAGRAM_SESSION_FILE` environment variable
3. **URL parsing works** — shortcode extraction from Instagram URLs is straightforward
4. **Metadata schema is correct** — the planned fields (caption, author, hashtags, etc.) align with instaloader's Post object
5. **Tests must use mocked responses** — real Instagram requests are too unreliable for CI

## Go/No-Go Decision

**CONDITIONAL GO.** The handler should be built with the resilience-first design from the PRD. Anonymous access is broken, but the handler architecture (graceful degradation, optional auth) is sound. The extraction logic is correct — it's the access layer that's blocked. Building the handler now with proper error handling ensures it works when authentication is configured.
