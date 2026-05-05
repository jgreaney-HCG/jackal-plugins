---
name: jackal-finish-branch
description: Complete a development branch with project-specific overrides (remote, test command, PR method) and TODO.md updates.
user-invocable: true
---

# Jackal Finish Branch

Wrapper around the `finish` skill with project-specific configuration.

---

## Step 0: Load Project Config

Read `## Jackal Config` from CLAUDE.md. Extract: `test_cmd`, `git_remote`, `push_cmd`, `pr_method`, `ui_path`, `issue_docs`, `repo_root`.

## Step 1: UI Verification Gate

Only if `ui_path` is configured:

```bash
git diff --name-only main..$(git branch --show-current) | grep -q "$UI_PATH"
```

If UI files changed → invoke `jackal-ui-verify`. Block if it fails.

## Step 2: Invoke Finish Skill

Use `Skill("jackal-plan-and-execute:finish")` with overrides:
- Test command: `$TEST_CMD`
- Push command: `$PUSH_CMD`
- PR method: `$PR_METHOD`

### Autonomous Mode Override

When called from the continuous execution loop:
- Skip the 4-option menu
- Merge locally (Option 1)
- Use `$GIT_REMOTE` for pull

## Step 3: Post-Completion Updates

After the finish skill completes (Options 1 or 2):

1. Find issue: extract ISSUE_ID from branch name
2. Update issue doc: Status → Done
3. Update TODO.md: Active → Resolved, update "Last updated"

## Step 4: Jackal Config Review

Check if implementation revealed changes that should update Jackal Config:
- New module that needs a module map entry?
- Port change?
- New service?

If yes, update CLAUDE.md.
