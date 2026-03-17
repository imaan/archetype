# Instagram Extraction — Phase 1 Results

**Libraries tested:** instaloader v4.15, ab-downloader (Node.js), yt-dlp
**Date:** 2026-03-17
**Decision: DEFER TO V2**

## Summary — Three Libraries Tested

### 1. instaloader (Python)

| Category | Status | Error | Time |
|----------|--------|-------|------|
| Public photo post (NASA) | FAIL | BadResponseException: Fetching Post metadata failed | 3,550ms |
| Invalid/deleted post | FAIL | BadResponseException: Fetching Post metadata failed | 1,181ms |
| Public reel | FAIL | BadResponseException: Fetching Post metadata failed | 1,380ms |
| Post with hashtags | FAIL | BadResponseException: Fetching Post metadata failed | 4,679ms |

**Pass rate: 0/4 (0%)** — All GraphQL queries return 403 Forbidden.

### 2. ab-downloader (Node.js — from working invisible-inbox project)

| Category | Status | Error | Time |
|----------|--------|-------|------|
| Public reel | FAIL | No data returned (empty array) | 6,096ms |
| Public photo (NASA) | FAIL | No data returned (empty array) | 7,479ms |
| Public reel (alt) | FAIL | No data returned (empty array) | 4,951ms |
| Invalid post | FAIL | No data returned (empty array) | 1,932ms |

**Pass rate: 0/4 (0%)** — The same library that works in invisible-inbox now returns empty arrays. Instagram has tightened access since it was built.

### 3. yt-dlp (with and without Chrome cookies)

| Category | Status | Error |
|----------|--------|-------|
| Public reel | FAIL | "Instagram sent an empty media response" — requires authenticated cookies |
| With --cookies-from-browser chrome | FAIL | "cannot decrypt v10 cookies" + same empty response |

**Pass rate: 0/2 (0%)** — yt-dlp explicitly says authentication is required.

## Key Findings

### All Three Approaches Fail
- **instaloader**: 403 Forbidden on GraphQL API
- **ab-downloader**: Returns empty arrays (was working in invisible-inbox, now broken)
- **yt-dlp**: "empty media response" — explicitly requests cookie authentication

### Root Cause
Instagram now requires **authenticated browser cookies** for ANY content access. This is not a rate limit — it's a hard authentication wall. All three libraries hit the same wall through different paths.

### The invisible-inbox parser is broken too
The `ab-downloader` library used in `/Users/iminaii/code/invisible-inbox/lib/instagram.ts` would also fail now. Instagram tightened access since that code was written.

## Reliability Assessment

**Instagram extraction without authentication is impossible as of March 2026.** No library bypasses this — it's an Instagram-side enforcement.

### Options for Phase 2 (if pursued)
1. **yt-dlp with exported cookies** — `yt-dlp --cookies cookies.txt` with manually exported browser cookies. Most promising but requires user setup.
2. **Playwright/browser automation** — Headless browser with logged-in session. Heavy dependency.
3. **Instagram Graph API** — Official API with app review. Reliable but limited to business accounts.
4. **Defer entirely** — Focus on the 4 working extractors and revisit Instagram when/if access loosens.

**Recommendation:** **Option 4 — Defer Instagram to v2.** The other 4 extractors (web, YouTube, PDF, email) all work excellently. Instagram adds complexity and fragility for uncertain value. If needed later, yt-dlp with exported cookies is the most viable path.

## Implementation Notes (if built anyway)

1. **Handler must never raise** — always return ExtractionResult with confidence=0.0 on failure
2. **yt-dlp is the best backend** — already a dependency for YouTube, supports Instagram with cookies
3. **Cookie authentication is mandatory** — document setup steps for users who need this
4. **URL parsing works** — shortcode extraction from Instagram URLs is straightforward
5. **Tests must use mocked responses** — real Instagram requests are too unreliable for CI

## Go/No-Go Decision

**DEFER TO V2.** All three tested libraries fail without authentication. The working invisible-inbox parser (`ab-downloader`) is also broken now. Instagram extraction adds fragility with no reliable anonymous path. Recommend building the 4 working extractors first and revisiting Instagram in v2 with cookie-based authentication via yt-dlp.
