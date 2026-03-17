# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Archetype is a collection of production-quality, forkable base applications — "like shadcn/ui, but for entire applications." The first app is an Inbox (universal capture/organize tool). The project is MIT licensed.

## Repository Structure

- **input-engine/** — Content extraction microservice (Python/FastAPI, currently in PRD/architecture phase)
  - `ARCHITECTURE.md` — Comprehensive tech design with all architectural decisions and rationale
  - `prds/` — Numbered PRDs (00-05) covering base architecture and each extraction type
- **landing-page/** — Framer-exported waitlist site deployed to GitHub Pages
  - `index.html` — Auto-generated Framer export (~140KB). **Do not manually edit** — use `framer-deploy.sh` to regenerate
  - `framer-deploy.sh` — Pulls Framer site, strips branding badge, outputs clean HTML
- **supabase/** — Backend (waitlist table with RLS, local dev config on port 54321)
- **scratchpad/** — Market research and initial planning docs (reference only)
- **assets/** — Favicon and OG image (SVG + PNG)

## Key Commands

### Landing Page
```bash
# Re-export from Framer and strip branding
./landing-page/framer-deploy.sh <framer-url> ./landing-page [--cname <domain>]
```

### Supabase
```bash
supabase start          # Start local Supabase (API: 54321, Studio: 54323, DB: 54322)
supabase db reset       # Reset database and re-run migrations
supabase migration new <name>  # Create new migration
```

### Input Engine (planned — not yet implemented)
```bash
uv run uvicorn input_engine.main:app --reload  # Dev server on :8000
uv run pytest                                   # Run tests
docker compose up                               # Run via Docker
```

## Input Engine Architecture

The input engine uses a **plugin handler pattern**: a single `POST /extract` endpoint auto-detects content type and delegates to the appropriate handler. Each handler implements `BaseHandler` with `can_handle()` and `extract()` methods, registered via a handler registry.

**Key design decisions** (see `input-engine/ARCHITECTURE.md` for full rationale):
- **Library-first extraction** — Use specialized Python libraries (trafilatura, pymupdf4llm, yt-dlp, etc.) for deterministic extraction; LLM enhancement is optional
- **Unified output schema** — All handlers return `ExtractionResult` with content (markdown), metadata (type-specific dict), confidence score, and extraction method transparency
- **Stateless** — No database; enables easy forking and deployment
- **Two-phase validation** — Each new extractor is first validated standalone, then integrated as a handler

**Implementation order**: Plain text → Web articles → YouTube → PDF → Email → Instagram → LLM enhancement

## Conventions

- PRDs are numbered sequentially in `input-engine/prds/` and follow a two-phase structure (standalone validation → handler integration)
- The landing page HTML is a Framer export — all visual changes should be made in Framer, then re-exported via the deploy script
- Supabase migrations use descriptive names and always enable RLS on new tables
