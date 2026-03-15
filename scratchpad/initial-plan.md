# Archetype - Initial Plan

**Date:** March 15, 2026
**Goal:** Ship consistently every day, share progress on Instagram

---

## The Vision

**Archetype** - Production-quality, forkable base apps. Like shadcn/ui, but for entire applications.

"Fork it. Own it. Ship it."

---

## First App: Inbox

An Inbox app for iPhone and Mac that lets you quickly capture and organize links, files, and anything else. The step *before* your todo list.

### Why Inbox First

1. **Universal pain point.** Everyone has links, screenshots, ideas, articles scattered across Notes, Safari tabs, Messages, Slack saves, bookmarks. No clean, fast "dump it here" app exists.

2. **Modern GTD gateway.** The GTD Inbox concept predates today's extreme info overload. A modern Inbox that's *just* capture + organize (not full task management) is genuinely missing.

3. **Technically diverse.** Share extensions (iOS), menu bar apps (Mac), drag-and-drop, link previews, tagging, search - teaches real patterns without being overwhelming.

4. **Perfect for daily shipping + Instagram.** Every day produces a tangible UI improvement to share: "Day 3: Added link preview cards", "Day 7: Share extension working on iPhone."

5. **Dogfooding.** We'll actually use it, which means we'll build something real.

### How It Fits the Archetype Vision

The Inbox app is the first Archetype base app - the "Inbox/Capture" archetype. It serves double duty:
- A real product people can use
- The first proof of concept for the Archetype platform

---

## Parallel Track: Waitlist Page

Get a waitlist landing page online early to start collecting emails and validate interest.

---

## Open Questions

1. **Tech stack for Inbox app** - Native Swift (SwiftUI) for iPhone + Mac? Or cross-platform?
2. **Waitlist page** - For "Archetype" (the platform) or the "Inbox app" specifically?
3. **Name** - Going with "Archetype"? Or Bedrock / Foundry?

---

## Proposed Week 1

### Day 1: Foundation + Waitlist
- Set up monorepo structure
- Create waitlist landing page
- Deploy (Vercel) - something live immediately
- First Instagram post: "Day 1"

### Days 2-3: Inbox App - Core Shell
- Swift/project setup for macOS + iOS
- Basic UI shell: inbox list view, add item button
- Local-first storage (SwiftData)

### Days 4-5: Inbox App - Capture
- iOS Share Extension
- macOS quick-capture (global keyboard shortcut, menu bar)
- Basic link preview fetching

### Days 6-7: Inbox App - Organize
- Tags/labels system
- Archive/delete
- Search

---

## Key Principles (from Market Research)

- **App-level, not component-level** - Full applications, not just UI pieces
- **Own the code** - Fork and customize, no dependency lock-in
- **AI-native** - AGENTS.md files, Claude Code friendly, designed for vibe coding on top of quality foundations
- **Educational production code** - Production-quality but deliberately readable and forkable
- **MIT licensed** - No barriers to adoption
- **Opinionated but ejectable** - Great defaults, easy to change
