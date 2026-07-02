---
name: jackal-finish-branch
description: Complete a development branch with project-specific overrides (remote, test command, PR method) and GitHub issue updates. Always finishes with a Pull Request — never a local merge.
user-invocable: true
---

# Jackal Finish Branch

Wrapper around the `finish` skill with project-specific configuration. The
outcome is always a pushed branch and an open PR.

---

## Step 0: Load Project Config

Read `## Jackal Config` from CLAUDE.md. Extract:
- `test_cmd`, `git_remote`, `push_cmd`, `pr_method`, `ui_path`, `issue_docs`, `repo_root`
- `gh_repo` — `owner/repo` (required)
- `label_style` — `slash` or `colon` (default: `slash`) — separator for status labels

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

The finish skill rebases onto origin/main when behind, verifies, pushes, and
opens the PR. It never merges locally, and it never presents a menu.

## Step 3: Post-Completion Updates

After the finish skill reports the PR URL:

1. Find issue: extract the issue number from the branch name. New scheme
   `<type>/<issue#>-slug` (e.g. `feat/24-foo` → `24`); legacy `PREFIX-46` → `46`.
2. Update issue doc (if the project keeps them): Status → In Review, add PR URL.

```bash
# bare-integer scheme first (feat/24-foo → 24), then legacy PREFIX-NN tail.
GH_ISSUE_NUM=$(echo "$BRANCH" | grep -oE '(^|/)[0-9]+(-|$)' | grep -oE '[0-9]+' | head -1)
[ -z "$GH_ISSUE_NUM" ] && GH_ISSUE_NUM=$(echo "$ISSUE_ID" | grep -oE '[0-9]+$')

gh issue comment "$GH_ISSUE_NUM" --repo "$GH_REPO" --body "$(cat <<EOF
**PR opened** — ${PR_URL}

- Branch: \`${BRANCH}\`
- Review: [verdict one-liner]
- AC coverage: [table from the final review]
EOF
)"

gh issue edit "$GH_ISSUE_NUM" --repo "$GH_REPO" --remove-label "status/in-progress"
# Leave the issue open — "Closes #N" in the PR body closes it on merge.
```

Tick the satisfied `- [ ] AC` checkboxes in the issue body, and tick this
issue's line in its epic's task list if it has one.

## Step 4: Jackal Config Review

Check if implementation revealed changes that should update Jackal Config:
- New module that needs a module map entry?
- Port change?
- New service?

If yes, update CLAUDE.md.

## Step 5: Point at Sweep

The worktree stays until the PR merges. Remind the user (or the autonomous
loop's session notes): run `/jackal-sweep` periodically to reclaim worktrees and
branches for merged PRs and to spot PRs needing rebase.
