---
name: jackal-design-plan
description: Start a design for a Complex issue. Runs conflict gate if not yet assigned, then invokes the design skill. Use for Complex issues that need architectural decisions.
user-invocable: true
---

# Jackal Design Plan

Wrapper that integrates the supervisor at entry/exit of the design phase.

---

## Step 0: Load Project Config

Read `## Jackal Config` from CLAUDE.md. Extract `repo_root`, `issue_prefix`, `issue_docs`, `design_plans`.

## Step 1: Resolve Input

Accept issue ID or issue doc path. Read the issue doc.

- If Complexity is not Complex → redirect to `/plan` (Standard) or implementor (Simple)
- If Status is Ready and no worktree → run conflict gate, create worktree, update issue doc
- If already In Progress → proceed

## Step 2: Investigate Codebase

Dispatch codebase-investigator with the issue doc as context. Carry findings forward.

## Step 3: Invoke Design Skill

Use `Skill("jackal-plan-and-execute:design")` with:
- Issue doc content as pre-gathered context
- Pre-determined slug: `{ISSUE-ID}-{kebab-title}`

The design skill runs its full flow (gather, clarify, brainstorm, write, commit).

## Step 4: Hand Off

After design commits:

```
Design complete for [ISSUE-ID].
Design plan: docs/design-plans/[filename]

Next: /plan docs/design-plans/[filename]
```

No /clear needed. Proceed directly if user says "go."
