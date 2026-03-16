# Design: /dev-init Generator Skill

**Date:** 2026-03-16
**Status:** Draft

## Problem

Setting up consistent development workflow skills for each project is manual and repetitive. The workflow itself (PRD-first, branch, implement, test, PR, cleanup) is universal, but the project-specific details (commands, paths, conventions) differ.

## Goals

1. One command (`/dev-init`) sets up three project-level development skills tailored to the project
2. Generated skills contain exact commands, paths, and conventions — no runtime guessing
3. A separate command (`/dev-init:improve`) audits and updates existing skills when the project evolves
4. Generated skills support both interactive (default) and autonomous (`auto` argument) modes

## Non-Goals

- Universal skills that work across projects (rejected: lower quality due to runtime CLAUDE.md parsing)
- Separate `dev.md` config file (rejected: duplicates CLAUDE.md, drift risk)
- Subagent-based parallel generation (rejected: over-engineered for three files)

## Architecture

### Skill inventory

| Skill | Location | Type | Purpose |
|-------|----------|------|---------|
| `/dev-init` | `~/.claude/skills/dev-init/SKILL.md` | User-level (generator) | Analyze project, generate CLAUDE.md if missing, write three project skills |
| `/dev-init:improve` | `~/.claude/skills/dev-init/improve/SKILL.md` | User-level (auditor) | Audit existing skills against CLAUDE.md, propose and apply updates |
| `/dev` | `.claude/skills/dev/SKILL.md` | Project-level (generated) | Full feature development workflow |
| `/quick-fix` | `.claude/skills/quick-fix/SKILL.md` | Project-level (generated) | Streamlined small fix workflow |
| `/cleanup` | `.claude/skills/cleanup/SKILL.md` | Project-level (generated) | Post-work cleanup checklist |

### `/dev-init` workflow

```
┌─────────────────────┐
│  1. Pre-flight       │  Check for existing skills, warn if overwriting
└─────────┬───────────┘
          │
┌─────────▼───────────┐
│  2. CLAUDE.md gate   │  If missing → generate via /init-style analysis
└─────────┬───────────┘
          │
┌─────────▼───────────┐
│  3. Project analysis │  Read CLAUDE.md + detect from filesystem
└─────────┬───────────┘
          │
┌─────────▼───────────┐
│  4. Generate skills  │  Write three SKILL.md files with baked-in details
└─────────┬───────────┘
          │
┌─────────▼───────────┐
│  5. Verification     │  Show summary, remind about /dev-init:improve
└─────────────────────┘
```

#### Phase 1: Pre-flight

Check if `.claude/skills/dev/SKILL.md`, `.claude/skills/quick-fix/SKILL.md`, or `.claude/skills/cleanup/SKILL.md` already exist. If any do:
- List which exist
- Ask the user: overwrite all, overwrite selectively, or abort
- Do not silently overwrite

#### Phase 2: CLAUDE.md gate

Check if `CLAUDE.md` exists in the project root. If not:
- Analyze the codebase (language, framework, structure, commands)
- Generate a CLAUDE.md following the standard format (project overview, commands, architecture, conventions)
- Show the user what was generated
- Continue to Phase 3

If CLAUDE.md exists, proceed directly.

#### Phase 3: Project analysis

Extract project-specific details from two sources:

**From CLAUDE.md:**
- Project name and description
- Build/test/dev/lint commands
- Architecture overview
- Key conventions and gotchas

**From filesystem detection:**

| Signal | Detection method | Used for |
|--------|-----------------|----------|
| Language/runtime | `pyproject.toml`, `package.json`, `Cargo.toml`, `go.mod`, `*.xcodeproj` | Test runner, package manager, server command |
| Framework | Dependencies in manifest (FastAPI, Next.js, Rails, etc.) | Dev server command, health check URL |
| PRD location | Directories named `prds/`, `docs/`, `specs/` containing `.md` files | PRD workflow in /dev skill |
| Scratchpad | `scratchpad/` directory existence | Work queue and debt tracking steps |
| Docker | `Dockerfile`, `docker-compose.yml` | Build command |
| CI | `.github/workflows/`, `.circleci/` | Reference in skills |
| Supabase | `supabase/` directory | Database commands |
| Existing tests | `tests/`, `test/`, `__tests__/`, `*_test.*` patterns | Test command discovery |

**Derived values:**

| Value | Derivation |
|-------|-----------|
| Worktree prefix | `../{directory-name}-feature/` and `../{directory-name}-fix/` from `basename $PWD` |
| Branch convention | `feature/{description}` and `fix/{description}` (universal) |
| Health check | Framework-dependent: FastAPI → `/health`, Express → `/health`, Rails → `/up` |
| Port | From CLAUDE.md or framework default (FastAPI: 8000, Next.js: 3000, Rails: 3000) |

#### Phase 4: Generate skills

Write three files using the collected project details. Each generated file follows this structure:

```
---
name: {skill-name}
description: {one-line description with "Pass 'auto' for autonomous mode."}
---

# {Skill Title}

## Mode Selection
{Interactive vs auto mode behavior}

## {Workflow steps with project-specific commands baked in}

## Key Rules
{Universal rules}
```

**What gets baked in (project-specific):**
- Exact test command (e.g., `uv run pytest`, `npm test`, `cargo test`)
- Exact dev server command (e.g., `uv run uvicorn input_engine.main:app --port 8000 --reload`)
- Health check command (e.g., `curl -s http://localhost:8000/health`)
- Lint command if available
- PRD location and naming convention
- Worktree paths with project name
- Scratchpad/debt paths if they exist
- Framework-specific notes (e.g., "don't manually edit Framer exports")

**What stays universal (same across all projects):**
- Workflow structure (PRD → branch → implement → test → PR → merge → cleanup)
- Interactive vs auto mode behavior
- Git safety (don't work on main, check for parallel sessions, worktree detection)
- Approval gates (interactive) and stop conditions (auto)
- Scope creep handling
- Never auto-merge rule
- "Quality over tokens" principle

**Conditional steps — only included if relevant:**

| Step | Condition |
|------|-----------|
| Create PRD | PRD directory detected |
| Move PRD to done | `scratchpad/done/` pattern detected |
| Update work queue | `scratchpad/work-queue.md` exists or scratchpad/ exists |
| Document debt | `scratchpad/debt/` exists or scratchpad/ exists |
| Docker build | Dockerfile detected |
| Supabase commands | `supabase/` directory detected |
| Lint step | Linter config detected (.eslintrc, ruff.toml, .rubocop.yml, etc.) |

#### Phase 5: Verification

After generating:
- Show a summary table: which skills were created, key commands baked in
- Remind the user they can customize the generated files
- Remind them to run `/dev-init:improve` if CLAUDE.md changes significantly later

### `/dev-init:improve` workflow

Follows the claude-md-improver pattern:

```
┌─────────────────────┐
│  1. Discovery        │  Find existing dev/quick-fix/cleanup skills
└─────────┬───────────┘
          │
┌─────────▼───────────┐
│  2. Assessment       │  Compare skills against current CLAUDE.md & filesystem
└─────────┬───────────┘
          │
┌─────────▼───────────┐
│  3. Report           │  Output quality report with specific issues
└─────────┬───────────┘
          │
┌─────────▼───────────┐
│  4. Propose updates  │  Show diffs for each recommended change
└─────────┬───────────┘
          │
┌─────────▼───────────┐
│  5. Apply            │  After user approval, edit skill files
└─────────────────────┘
```

**Assessment criteria:**

| Check | What it looks for |
|-------|-------------------|
| Command accuracy | Do test/build/dev commands in skills match CLAUDE.md? |
| Path validity | Do referenced directories (PRDs, scratchpad, debt) still exist? |
| New capabilities | Are there commands in CLAUDE.md not reflected in skills? |
| Removed capabilities | Are there commands in skills that no longer exist in CLAUDE.md? |
| Step relevance | Are conditional steps still appropriate? (e.g., Docker removed) |

**Output format:**

```
## Dev Skills Audit Report

### /dev skill
- [OK] Test command: `uv run pytest` matches CLAUDE.md
- [STALE] Dev server: skill says port 8000, CLAUDE.md says port 3000
- [MISSING] New lint command in CLAUDE.md not in skill: `uv run ruff check`

### /quick-fix skill
- [OK] All commands current
- [STALE] References `scratchpad/debt/` but directory was removed

### /cleanup skill
- [OK] All checks pass

### Recommended Changes
1. Update dev server port in /dev skill (show diff)
2. Add lint step to /dev skill (show diff)
3. Remove debt reference from /quick-fix (show diff)
```

## Generated skill templates

### /dev template structure

1. Mode selection (interactive vs auto)
2. Roles
3. GitHub Issue (discuss or auto-pick)
4. Create PRD (if PRD location exists)
5. PRD Review (interactive gate)
6. Pre-implementation summary
7. Create branch (with worktree detection, project-specific paths)
8. Implement (with project-specific notes, scope creep handling)
9. Push PR
10. Run existing tests (exact command)
11. Write new tests (framework-specific guidelines)
12. Manual testing (exact dev server command, health check)
13. Merge PR (never auto-merge in auto mode)
14. Sanity check
15. Update PRD (if PRDs exist)
16. Create follow-up issues
17. Move PRD to done (if pattern exists)
18. Document debt (if scratchpad exists)
19. Update work queue (if work queue exists)
20. Improve master document
21. Key rules

### /quick-fix template structure

1. Mode selection
2. When to use / when not to use
3. Confirm scope
4. Create branch (with worktree detection)
5. Implement (project-specific notes)
6. Run tests (exact command)
7. Create PR
8. Verify & merge (never auto-merge in auto mode)
9. Update work queue & document debt (if applicable)
10. Key rules

### /cleanup template structure

1. Mode selection
2. When to use
3. Git status & worktrees (project-specific paths)
4. Stray files (project-specific locations)
5. Open PRs
6. Open issues
7. Background processes (project-specific process names and ports)
8. Database/backend state (project-specific: Supabase, SQLite, Postgres, etc.)
9. Environment verification (exact dependency command)
10. Document debt (if applicable)
11. Update work queue (if applicable)
12. Final verification (exact test and server commands)
13. Post-cleanup state checklist

## Auto mode behavior (universal across all generated skills)

**When to proceed without asking:**
- All routine workflow steps
- Creating branches, PRDs, PRs
- Running tests and fixing failures
- Writing code according to PRD

**When to stop and ask the user:**
- Tests fail after 2 fix attempts
- Design decision with multiple valid approaches and no clear winner
- Scope creep discovered (create issue, ask about current scope)
- Missing dependency, credential, or external service
- Something unexpected that could lose work

**Hard rule: never auto-merge.** Auto mode creates the PR and stops. The user reviews and merges.

## Edge cases

| Scenario | Behavior |
|----------|----------|
| No CLAUDE.md, no detectable tech stack | Generate minimal CLAUDE.md with just project name and directory structure. Generate skills with placeholder commands marked `# TODO: fill in` |
| Monorepo with multiple services | Detect top-level packages. Ask user which service to generate skills for. Generate skills scoped to that service's commands. |
| Project uses `make` | Detect Makefile targets and use them (e.g., `make test`, `make dev`) |
| No tests exist yet | Include test step but note "no test suite detected — skip until tests are added" |
| No git remote | Skip PR-related steps, just commit locally |
