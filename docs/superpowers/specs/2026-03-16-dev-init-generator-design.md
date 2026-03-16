# Design: /dev-init Generator Skill

**Date:** 2026-03-16
**Status:** Reviewed

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

Check if `CLAUDE.md` exists in the project root. If not, delegate to Claude Code's built-in `/init` command, which analyzes the codebase and generates a CLAUDE.md. This is a well-defined existing capability — `/dev-init` does not reimplement it.

After `/init` completes (or if CLAUDE.md already exists), proceed to Phase 3.

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

## Reference templates

The existing project-level skills in this repository serve as the canonical reference templates for what `/dev-init` should generate:

- `.claude/skills/dev/SKILL.md` — Reference for the `/dev` output
- `.claude/skills/quick-fix/SKILL.md` — Reference for the `/quick-fix` output
- `.claude/skills/cleanup/SKILL.md` — Reference for the `/cleanup` output

These were hand-crafted for the archetype project and represent the "gold standard" output. The generator should produce skills with the same structure, workflow steps, and universal rules — but with project-specific commands, paths, and conditional steps adapted to the target project.

**The generator does not use placeholder templates.** It reads the project context (Phase 3) and generates the skill content directly, following the structure and conventions of the reference templates. This gives Claude full flexibility to adapt the output to each project's specific needs rather than filling in rigid `{{placeholder}}` tokens.

### Generated skill structures

**`/dev` skill — 18 workflow steps:**
1. GitHub Issue → 2. Create PRD (conditional) → 3. PRD Review (interactive gate) → 4. Pre-implementation summary → 5. Create branch → 6. Implement → 7. Push PR → 8. Run existing tests → 9. Write new tests → 10. Manual testing → 11. Merge PR → 12. Sanity check → 13. Update PRD (conditional) → 14. Create follow-up issues → 15. Move PRD to done (conditional) → 16. Document debt (conditional) → 17. Update work queue (conditional) → 18. Suggest process improvements

Plus: Mode selection preamble, Roles preamble, Key rules footer.

**`/quick-fix` skill — 7 workflow steps:**
1. Confirm scope → 2. Create branch → 3. Implement → 4. Run tests → 5. Create PR → 6. Verify & merge → 7. Update work queue & document debt (conditional)

Plus: Mode selection, when to use / when not to use, Key rules.

**`/cleanup` skill — 10 checklist items:**
1. Git status & worktrees → 2. Stray files → 3. Open PRs → 4. Open issues → 5. Background processes → 6. Database/backend state (conditional) → 7. Environment verification → 8. Document debt (conditional) → 9. Update work queue (conditional) → 10. Final verification

Plus: Mode selection, Post-cleanup state checklist.

### Conditional steps across all skills

Steps marked (conditional) are only included when the relevant infrastructure is detected:

| Step | Condition | Applies to |
|------|-----------|------------|
| Create/Update PRD | PRD directory detected | /dev |
| Move PRD to done | `scratchpad/done/` pattern exists | /dev |
| Update work queue | `scratchpad/` exists | /dev, /quick-fix, /cleanup |
| Document debt | `scratchpad/` exists | /dev, /quick-fix, /cleanup |
| Docker build | Dockerfile detected | /dev, /cleanup |
| Database commands | Database tooling detected (Supabase, SQLite, Prisma, etc.) | /dev, /cleanup |
| Lint step | Linter config detected | /dev |

### "Suggest process improvements" step

The final step of `/dev` asks Claude to suggest improvements to the skill itself based on issues encountered during the session. This is advisory — it outputs suggestions to the user, it does not self-modify the skill file. The user can apply suggestions manually or run `/dev-init:improve` to do it systematically.

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

## Assumptions

- **GitHub-based workflow.** The generated skills assume GitHub for PRs and issues (`gh` CLI). Projects using other platforms (Linear, GitLab, Jira) would need manual adjustment after generation.
- **Single-service projects by default.** Monorepos require user input (see edge cases).
- **CLAUDE.md as source of truth.** When CLAUDE.md and filesystem detection disagree (e.g., CLAUDE.md says `npm test` but no test script in package.json), CLAUDE.md wins — the user wrote it intentionally. Filesystem detection fills gaps that CLAUDE.md doesn't cover.

## Provenance header

Every generated skill file includes a comment header:

```markdown
<!-- Generated by /dev-init on YYYY-MM-DD. Safe to customize — /dev-init:improve will propose updates, not overwrite. -->
```

This helps `/dev-init:improve` distinguish generated content from hand-written skills and avoids overwriting projects that were never generated by `/dev-init`.

## Edge cases

| Scenario | Behavior |
|----------|----------|
| No CLAUDE.md, no detectable tech stack | Run `/init` which will generate a minimal CLAUDE.md. Generate skills with placeholder commands marked `# TODO: fill in your test command` |
| Monorepo with multiple services | Detect top-level packages/services. Ask user which one to scope skills for. Skills are generated once, scoped to that service. Re-run for additional services is not supported — monorepo users should customize the generated skills manually. |
| Project uses `make` | Detect Makefile targets and use them (e.g., `make test`, `make dev`) |
| No tests exist yet | Include test step but note "no test suite detected — skip until tests are added" |
| No git remote | Skip PR-related steps, just commit locally |
| Multiple package manifests at root | Prioritize: CLAUDE.md commands > Makefile targets > primary manifest. For conflicting manifests (e.g., both `package.json` and `pyproject.toml`), ask the user which is the primary runtime. |
| Unrecognized framework/language | Generate skills with generic structure. Commands section uses `# TODO` placeholders. Workflow steps are still included — just without baked-in commands. |
