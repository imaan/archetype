---
name: quick-fix
description: Streamlined process for small bug fixes and minor changes. Pass "auto" as argument for autonomous mode that only stops on blockers.
---

# Quick Fix Process

A streamlined process for small fixes and minor changes that don't require a full PRD.

## Mode Selection

Check the argument passed to this skill:

- **No argument or "interactive"** → **Interactive mode** (default). Confirm scope with user, wait for review before merge.
- **"auto"** → **Autonomous mode**. Execute the fix end-to-end. Only stop and ask if:
  - Tests fail and you can't fix them after 2 attempts
  - The fix turns out to be larger than expected (switch to /dev)
  - You're unsure which of multiple valid approaches to take

In autonomous mode, do NOT auto-merge — create the PR and tell the user it's ready.

---

## When to Use

- Bug fixes with clear scope
- Copy/UI text changes
- Small refactors
- Adding minor features (< 30 min work)
- Test fixes

## When NOT to Use (use full /dev process instead)

- New features requiring design decisions
- New extraction handlers (always need a PRD)
- Changes touching multiple systems
- Breaking changes
- Anything requiring stakeholder input

## Process

### 1. Confirm Scope
**Interactive:** Briefly state what you're fixing and confirm with User it's appropriate for quick-fix process.

**Autonomous:** State what you're fixing and why, then proceed.

### 2. Create Branch

**First, check for parallel sessions:**
```bash
git status
git worktree list
```

If there are uncommitted changes, or you're not on `main`, or other worktrees exist — another session is likely active. **Do NOT run `git checkout`**. Instead, use a worktree:

```bash
git fetch origin
git worktree add ../archetype-fix/{short-description} -b fix/{short-description} origin/main
```

Then **switch your working directory** to `../archetype-fix/{short-description}` for all remaining steps. Tell the User the new working directory.

**If no parallel session detected (clean working tree, on main):**
```bash
git checkout main && git pull
git checkout -b fix/{short-description}
```

### 3. Implement
Make the changes. Keep it focused — if scope grows, switch to full /dev process.

**Landing page fixes:** If it's a Framer export issue, the fix likely needs to happen in Framer and be re-exported via `landing-page/framer-deploy.sh`. Only fix `landing-page/index.html` directly for injected code (Supabase handler, custom scripts).

### 4. Run Tests
```bash
cd input-engine && uv run pytest    # if input-engine exists
```
Fix any failures. Update tests if the fix changes existing behavior.

### 5. Create PR
```bash
git add -A && git commit -m "..."
git push -u origin fix/{short-description}
gh pr create --title "..." --body "..."
```

Include in PR body:
- Brief summary of what was fixed
- Simple test plan (can be manual verification steps)

### 6. Verify & Merge
**Interactive:**
- User reviews PR
- If approved: merge, delete branch, pull main

**Autonomous:**
- Do NOT merge. Tell the user the PR is ready for review. Stop here.

```bash
gh pr merge {number} --squash --delete-branch
```

**If working in a worktree:**
```bash
cd /Users/iminaii/code/archetype
git worktree remove ../archetype-fix/{short-description}
git checkout main && git pull
```

**If working in main repo:**
```bash
git checkout main && git pull
```

### 7. Update Work Queue & Document Debt
Update `scratchpad/work-queue.md` if applicable.

If any work was skipped, document in `scratchpad/debt/{date}-{short-description}.md`.

## Key Rules

- **Stay focused** — if it grows beyond quick fix, pause and switch to /dev
- **Always branch** — never commit directly to main
- **Run tests** — don't skip automated tests
- **Update tests** — if you change behavior, update corresponding tests
- **Never auto-merge** — in autonomous mode, always leave PR for human review
