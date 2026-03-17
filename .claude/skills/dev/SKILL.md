---
name: dev
description: Full feature development process — PRD-first workflow with approval gates, worktree support, testing, and debt tracking. Pass "auto" as argument for autonomous mode.
---

# Development Process

## Mode Selection

Check the argument passed to this skill:

- **No argument or "interactive"** → **Interactive mode** (default). Follow all approval gates. Discuss decisions with the user. Wait for explicit approval at each checkpoint.
- **"auto"** → **Autonomous mode**. Execute the full workflow end-to-end without pausing for approval. Only stop and ask the user if:
  - Tests fail and you can't fix them after 2 attempts
  - A design decision has multiple valid approaches and no clear winner
  - Scope creep is discovered
  - You're blocked by a missing dependency, credential, or external service
  - Something unexpected happens that could lose work

In autonomous mode, still create the PRD and write the pre-implementation summary — but don't wait for approval. Proceed immediately. The user can review the PRD and PR asynchronously.

---

## Roles

- **You (User)**: Product owner, final decision maker on all steps
- **Me (Claude)**: Developer, follows this process, makes recommendations but always defers to you

## Standard Flow

### 1. GitHub Issue
**Interactive:** Have a discussion with the User about which issue to work on, or if they want to create a new one. Review existing issues and PRDs. Make recommendations.

**Autonomous:** If the user specified an issue or task, use that. Otherwise, review open issues and pick the highest-priority one. Briefly state what you chose and why, then move on.

Review outstanding work:
- `input-engine/prds/` for engine extraction handlers
- `scratchpad/` for general planning docs

### 2. Create PRD

**For Input Engine work:** PRDs go in `input-engine/prds/` following the existing numbered convention (e.g., `06-audio-extraction.md`). Follow the two-phase structure (standalone validation, then handler integration) established in the existing PRDs.

**For other work:** Write PRD in `scratchpad/YYYYMMDD-{description}-prd.md` containing:
- Issue reference at the top
- Problem statement
- Goals
- Current state analysis
  - Existing code patterns to build on
  - Cross-environment constraints (local vs production)
  - Dependencies or blockers
- Proposed solution
- Implementation plan
  - Files to create/modify
  - Migration or deployment considerations
- Acceptance criteria
- Test plan
- Empty "What Was Done" section

### 3. PRD Review
**Interactive:** Ask: **"Ready to implement?"**
- Wait for explicit approval before proceeding
- If feedback given, update PRD and ask again
- Never skip this step without explicit approval

**Autonomous:** Skip this gate. The PRD is written for the record — proceed to implementation.

### 4. Pre-Implementation Summary
Give a brief summary:
- Files I'll create/modify
- Rough approach
- Any assumptions

**Interactive:** Wait for acknowledgment before proceeding.

**Autonomous:** Output the summary and continue immediately.

### 5. Create Branch

**First, check for parallel sessions:**
```bash
git status
git worktree list
```

If there are uncommitted changes, or you're not on `main`, or other worktrees exist — another session is likely active. **Do NOT run `git checkout`**. Instead, use a worktree:

```bash
git fetch origin
git worktree add ../archetype-feature/{description} -b feature/{description} origin/main
```

Then **switch your working directory** to `../archetype-feature/{description}` for all remaining steps. Tell the User the new working directory.

**If no parallel session detected (clean working tree, on main):**
```bash
git checkout main && git pull
git checkout -b feature/{description}
```

**If branch already exists:** Verify it's rebased on latest main before starting work:
```bash
git checkout feature/{description}
git fetch origin
git rebase origin/main
```

### 6. Implement
Make the changes according to the PRD.

**If scope creep discovered** (related issues found during implementation):
- **Interactive:** Stop and ask if you want to add it to current PR or create separate issue
- **Autonomous:** Create a separate GitHub issue for the scope creep. Note it in the PR body. Continue with original scope.
- Never silently expand scope

**If stuck on something**:
- **Interactive:** Ask you directly rather than finding roundabout solutions
- **Autonomous:** Try 2 alternative approaches. If still stuck, stop and ask.

**Input Engine specifics:**
- New handlers must implement `BaseHandler` with `can_handle()` and `extract()` methods
- Register handlers in the registry — main.py should not need changes
- All handlers return `ExtractionResult` with confidence score and extraction method transparency
- Follow the two-phase validation: standalone script first, then handler integration

**Landing page changes:** Visual changes go through Framer, then re-export via `landing-page/framer-deploy.sh`. Don't manually edit `landing-page/index.html`.

### 7. Push PR
```bash
git add -A && git commit -m "..."
git push -u origin feature/{description}
gh pr create --title "..." --body "Closes #{issue_number}..."
```

### 8. Run Existing Tests
```bash
cd input-engine
uv run pytest
uv run uvicorn input_engine.main:app --port 8000 --reload &
# verify http://localhost:8000/health returns {"status": "ok"}
# verify http://localhost:8000/docs loads OpenAPI docs
```
Fix any failures.

### 9. Write New Tests
For any new functionality, write tests covering:
- **Handler extraction** — unit tests with real fixture files (no mocking extraction libraries)
- **Content detection** — test auto-detection for new input patterns
- **API integration** — test `/extract` endpoint with various inputs
- **Error handling** — graceful degradation with confidence=0.0 for failures

Guidelines:
- Use pytest + pytest-asyncio
- Test both happy path and error cases
- Use real fixture files for extraction tests (store in `tests/fixtures/`)
- Run tests and fix any failures before proceeding

### 10. Manual Testing
Work through the test plan from the PRD, step by step:
- Review if test plan needs updates based on actual implementation
- Start the dev server: `cd input-engine && uv run uvicorn input_engine.main:app --port 8000 --reload`
- **Tick off items in the PR description** as we complete them
- Use Claude-in-Chrome MCP for browser-based testing when needed (API docs, landing page)
- Test with `curl` for API endpoints

**Interactive — always delegate to the user:**
- Visual polish on landing page
- Subjective quality assessment of extraction output
- Cross-browser testing

**Autonomous:** Do what you can with curl and automated checks. Note items that need human review in the PR body under a "Needs Human Review" section.

### 11. Merge PR
**Interactive:** Wait for user to approve, then:
```bash
gh pr merge {number} --squash --delete-branch
```

**Autonomous:** Do NOT auto-merge. Create the PR and stop here. Tell the user the PR is ready for review. The remaining steps (12-18) should be done after the user merges.

**If working in a worktree:**
```bash
cd /Users/iminaii/code/archetype
git worktree remove ../archetype-feature/{description}
git checkout main && git pull
```

**If working in main repo:**
```bash
git checkout main && git pull
```

### 12. Sanity Check
Quick check that everything still works after merge:
- Start the server, verify health endpoint
- Test the feature in merged state
- Catch any issues tests might have missed

### 13. Update PRD
Fill in "What Was Done" section:
- Implementation log
- Files changed
- Deviations from plan
- Lessons learned

### 14. Create Follow-up Issues
Review the PRD's "Future Enhancements" or "Out of Scope" sections:
- Create new GitHub issues with appropriate labels if needed
- Check existing issues for overlap first

### 15. Move to Done
```bash
mkdir -p scratchpad/done
mv scratchpad/{prd}.md scratchpad/done/
```
(Input Engine PRDs stay in `input-engine/prds/` — they're the living spec.)

### 16. Document Debt
Create a file in `scratchpad/debt/` documenting any work that was skipped or deferred:
- Tests that should be added
- Edge cases not covered
- Refactoring opportunities
- Related issues discovered but not addressed

Format: `scratchpad/debt/{date}-{short-description}.md`

### 17. Update Work Queue
Update `scratchpad/work-queue.md`:
- Remove completed items (move to Completed section)
- Re-prioritize remaining issues
- List all outstanding GitHub issues
- Note any new issues created during the session

### 18. Improve master document
Any suggestions on how to improve this process based on issues encountered during this session.

## Key Rules

- **Don't work on main** — always create a branch
- **Don't skip steps** — get explicit approval to skip any step (interactive) or document why you skipped (autonomous)
- **Don't start until PRD is approved** (interactive only) — after updating a PRD, always wait for explicit "ready to implement" approval
- **Don't update "What Was Done" until after merge**
- **PRD before code** — get alignment first (even in autonomous mode, write the PRD)
- **Stop and ask on scope creep** — don't silently expand scope
- **Ask when stuck** — don't waste time on roundabout solutions (autonomous: try 2 alternatives first)
- **Quality over tokens** — take time to do it right
- **Label GitHub issues** — priority and category
- **Keep a running checklist of how far we are through the process**
- **Keep tests in sync with production code** — when changing schemas, API contracts, or handler logic, update corresponding tests in the same PR
- **Autonomous mode never auto-merges** — always leave the PR for human review
