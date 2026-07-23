---
name: jackal-design-plan
description: Start a design for a Complex issue. Runs conflict gate if not yet assigned, then invokes the design skill. Use for Complex issues that need architectural decisions.
user-invocable: true
argument-hint: "[issue-id-or-doc-path]"
---

# Jackal Design Plan

Wrapper that integrates the supervisor at entry/exit of the design phase. **This skill owns worktree creation** for the issue. Downstream skills (`jackal-impl-plan`, `jackal-pause-session`, `jackal-finish-branch`) read the worktree path back from the issue doc.

---

## Step 0: Load Project Config

Read `## Jackal Config` from CLAUDE.md. Extract:
- `repo_root`, `issue_prefix`, `issue_docs`, `design_plans`, `modules`
- `gh_repo` — `owner/repo` (required)
- `label_style` — `slash` or `colon` (default: `slash`) — separator for status labels; examples
  below use `/`, substitute `:` if `colon`

## Step 1: Resolve Input

Accept issue ID or issue doc path. Read the issue doc.

- If Complexity is **Standard** → this issue doesn't need a design phase. Tell the user in
  one line ("Issue #N is Standard, not Complex — routing to jackal-impl-plan instead of
  design"), then invoke `Skill("jackal-supervisor:jackal-impl-plan")` with the same issue
  reference and stop processing this skill. Do not ask for confirmation first — this is a
  routing correction, not a judgment call the user needs to weigh in on.
- If Complexity is **Simple** → this issue doesn't need a design or implementation-plan
  phase at all. Tell the user in one line ("Issue #N is Simple — dispatching the implementor
  directly instead of design"), then dispatch the `jackal-plan-and-execute:implementor` agent
  directly with the issue doc as context (same routing the supervisor agent uses for Simple
  issues — see its Route to Execution table) and stop processing this skill.
- If a `## Worktree` block already exists in the issue doc → reuse it (skip step 2). This means design was started before and is being resumed.
- Otherwise → proceed to step 2

## Step 2: Conflict Gate + Create Worktree

Run conflict gate against active feature branches:

```bash
cd $REPO_ROOT
for branch in $(git branch --list 'feature/*' '*/[0-9]*-*' | tr -d ' '); do
  echo "=== $branch ==="
  git diff --name-only main...$branch 2>/dev/null
done
```

Compare candidate scope (from issue doc `In scope:`) against the active branch file sets.
- File-level overlap → block, name the conflicting branch
- Directory-level overlap, different files → warn, proceed
- No overlap → proceed

Derive names from the issue doc (never ask):

```bash
ISSUE="24"                # GitHub issue number (the work-unit key)
SLUG="kebab-title"        # from issue title
TYPE="feat"               # conventional-commit type: feat|fix|docs|chore|refactor|...

WORKTREE_PATH="$REPO_ROOT/.worktrees/${ISSUE}-${SLUG}"
BRANCH="${TYPE}/${ISSUE}-${SLUG}"

grep -q "\.worktrees" "$REPO_ROOT/.gitignore" || echo ".worktrees/" >> "$REPO_ROOT/.gitignore"

BASE="$(git -C "$REPO_ROOT" symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null | sed 's#origin/##')"
: "${BASE:=main}"
if [ ! -d "$WORKTREE_PATH" ]; then
  cd "$REPO_ROOT"
  git worktree add "$WORKTREE_PATH" -b "$BRANCH" "$BASE"
fi
```

## Step 3: Record the Worktree Assignment

**Do not commit anything to `main` here.** Worktree assignment and issue status are backlog
metadata, and this project's backlog is GitHub Issues — the durable record is the issue comment +
label written in Step 4, not a commit. Committing bookkeeping to `main` (the old behavior) left a
trail of `chore: assign worktree for #N` commits on the trunk; that route is removed.

The **authoritative record of what worktree/branch exists is git itself** (`git worktree list`,
`git branch`), which `jackal-impl-plan` reads back directly. So:

- Write the `## Worktree` block into the issue doc **on disk** as a local convenience for
  same-session reads (uncommitted — it lives in the repo-root working tree):

  ```markdown
  ## Worktree

  - branch: feat/24-slug
  - path: .worktrees/24-slug
  - created: 2026-05-28
  ```

  Use repo-root-relative paths so it's portable; skills convert to absolute via `$REPO_ROOT/<path>`.
- Set `**Status:** In Progress` in the on-disk issue doc.
- **Do not `git add`/`git commit` the issue doc on `main`.** If the issue doc itself needs to be
  versioned, it rides along on the feature branch when the design/impl commits land inside the
  worktree — never as a standalone bookkeeping commit on the trunk.

## Step 4: Update Backlog State (the durable record)

```bash
GH_ISSUE_NUM=$(echo "$ISSUE_ID" | grep -oE '[0-9]+$')

gh issue edit "$GH_ISSUE_NUM" --repo "$GH_REPO" \
  --add-label "status/in-progress" \
  --remove-label "status/ready" \
  --add-assignee "@me"

gh issue comment "$GH_ISSUE_NUM" --repo "$GH_REPO" --body "$(cat <<EOF
**Worktree assigned** — design phase starting

- Branch: \`${BRANCH}\`
- Worktree: \`${WORKTREE_PATH}\`
- Issue doc: \`${ISSUE_DOCS}/${ISSUE_ID}-${SLUG}.md\`
EOF
)"
```

If `gh issue edit` fails because a label doesn't exist, report the missing label to the user and continue (the comment is still useful).

## Step 5: Invoke Design Skill

Use `Skill("jackal-plan-and-execute:design")` with:
- `WORKTREE_PATH` — absolute path
- `BRANCH`
- `ISSUE_ID`, `SLUG`
- Issue doc content as pre-gathered context

The design skill runs from inside the worktree, so the design document commit lands on the feature branch.

## Step 6: Hand Off

After design commits, post the design doc link as an issue comment
(`gh issue comment "$GH_ISSUE_NUM" --body "**Design complete** — [design-plans/<filename>](<blob-url-or-path>)"`),
then hand off:

```
Design complete for #[issue].
Design plan: docs/design-plans/[filename]
Worktree: .worktrees/[issue#]-[slug]
Branch: [type]/[issue#]-[slug]

Next: /jackal-supervisor:jackal-impl-plan docs/design-plans/[filename]
```

Emit that `Next:` line **exactly as written with the real filename substituted** —
it is a literal command (defined in this plugin's `commands/`), not a
description. Do not invent command names.

No /clear needed. `jackal-impl-plan` reads the `## Worktree` block from the issue doc to find the existing worktree.
