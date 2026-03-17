---
name: cleanup
description: Post-work cleanup checklist — git hygiene, stray files, open PRs/issues, background processes, and debt tracking. Pass "auto" for autonomous mode.
---

# Cleanup Process

A comprehensive checklist for cleaning up after development work to ensure no loose ends.

## Mode Selection

Check the argument passed to this skill:

- **No argument or "interactive"** → **Interactive mode** (default). Report findings and confirm actions with the user before making changes.
- **"auto"** → **Autonomous mode**. Execute the full cleanup. Only stop and ask if:
  - You find uncommitted changes that look like in-progress work (don't discard)
  - Worktrees exist that might belong to another active session
  - You're unsure whether a file/branch should be deleted

In autonomous mode, be conservative: don't delete anything you're unsure about. Document what you skipped and why.

---

## When to Use

- After completing a feature or fix
- Before ending a work session
- When switching contexts to a different task
- Periodically to maintain repo hygiene

## Cleanup Checklist

### 1. Git Status & Worktrees
```bash
git status
git worktree list
```

**Actions:**
- Commit or stash any work-in-progress
- Delete any temporary/scratch files
- Ensure you're on `main` branch if work is complete
- Remove any stale worktrees:
  ```bash
  git worktree remove ../archetype-feature/{name}  # or archetype-fix/{name}
  ```

### 2. Stray Files
Check for temporary files that shouldn't exist:
```bash
ls *.tmp *.log 2>/dev/null
ls scratchpad/
```

**Common cleanup targets:**
- One-off test/validation scripts
- Debug log files
- Temporary data exports
- Old PRD files that are now complete (move to `scratchpad/done/`)

### 3. Open PRs
```bash
gh pr list
```

**Actions:**
- Merge approved PRs (interactive: confirm first)
- Close stale/abandoned PRs (interactive: confirm first)
- Add reviewers to waiting PRs

### 4. Open Issues
```bash
gh issue list
```

**Actions:**
- Close completed issues
- Update issue labels/priorities
- Add context to stale issues

### 5. Background Processes
```bash
ps aux | grep -E 'uvicorn|supabase' | grep -v grep
lsof -i :8000,:8001,:54321 2>/dev/null
```

Kill any orphaned servers if needed.

### 6. Supabase State
```bash
supabase status    # check if local Supabase is running
```

- Is the local database in a consistent state?
- Any pending migrations not applied?
- Stop Supabase if not needed: `supabase stop`

### 7. Environment
```bash
# Verify dependencies (once input-engine exists)
cd input-engine && uv sync

# Verify .env exists with required keys
test -f .env && echo ".env exists" || echo "WARNING: .env missing"
```

### 8. Document Debt
If any technical debt was introduced or discovered:

**Location:** `scratchpad/debt/{date}-{description}.md`

**Include:**
- What was skipped and why
- Suggested approach to fix
- Priority/urgency
- Related issues or PRs

### 9. Update Work Queue
Update `scratchpad/work-queue.md`:
- Remove completed items (move to Completed section)
- Re-prioritize remaining issues
- List all outstanding GitHub issues
- Ensure queue matches reality after any work done this session

### 10. CLAUDE.md Audit
Run `/claude-md-improver` to check CLAUDE.md quality and currency against the current codebase state.

### 11. Dev Skills Audit
Run `/dev-init:improve` to check if the generated dev skills are still in sync with CLAUDE.md. Run this after the CLAUDE.md audit so skills are checked against the latest version.

### 12. Final Verification
```bash
git status
git log --oneline -5

# If input-engine exists:
cd input-engine && uv run pytest

# Quick app check:
# uv run uvicorn input_engine.main:app --port 8000 &
# curl -s http://localhost:8000/health
```

## Post-Cleanup State

After cleanup, the repo should be in this state:
- [ ] On `main` branch
- [ ] No uncommitted changes
- [ ] No stray temporary files
- [ ] All completed PRs merged
- [ ] Resolved issues closed
- [ ] No orphaned background processes
- [ ] Tests passing (if they exist)
- [ ] Any new debt documented
