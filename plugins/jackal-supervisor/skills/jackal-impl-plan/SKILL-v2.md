---
name: jackal-impl-plan
description: Create an implementation plan for a Standard or Complex issue. Runs conflict gate, creates worktree, dispatches planner, and starts execution. Second step in the Jackal dev cycle.
user-invocable: true
---

# Jackal Implementation Plan

Wrapper that adds supervisor integration (conflict gate, worktree, TODO.md updates) around the plan skill.

---

## Step 0: Load Project Config

Read `## Jackal Config` from CLAUDE.md. Extract all config values.

## Step 1: Resolve Input

Accept: design plan path, issue doc path, or issue ID.

- Design plan provided → use it
- Issue doc for Standard issue → planner will auto-generate mini design
- Issue doc for Complex issue with no design plan → STOP, redirect to `/design`
- Simple issue → STOP, redirect to direct implementor dispatch

## Step 2: Conflict Gate

```bash
for branch in $(git branch --list 'feature/*' | tr -d ' '); do
  git diff --name-only main...$branch 2>/dev/null
done
```

Compare against design plan scope. Block on file-level conflict, warn on directory-level.

## Step 3: Create Worktree

Auto-name from issue ID + slug + module. No questions asked.

```bash
git worktree add .worktrees/${ISSUE_ID}-${SLUG} -b feature/${MODULE}/${ISSUE_ID}-${SLUG} main
```

Update issue doc and TODO.md.

## Step 4: Invoke Plan Skill

Use `Skill("jackal-plan-and-execute:plan")` with the design plan path and worktree path.

The plan skill dispatches the planner agent, writes phase files, and immediately starts execution.

## Step 5: Execution Starts Automatically

The plan skill flows directly into the execute skill. No handoff ceremony needed.

If running in autonomous mode (backlog execution), everything from this point is automatic until the issue is done or the orchestrator gets stuck.
