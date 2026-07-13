---
name: jackal-sweep
description: Reclaim worktrees and local branches whose PRs have merged, flag PRs that need a rebase, and fast-forward main. Run after PRs merge, before starting new work, or whenever `git worktree list` looks crowded.
user-invocable: true
---

# Jackal Sweep

Branch and worktree hygiene in one pass. This is the harness-native version of
"pull main, prune what's gone" — but it removes worktrees **before** pruning
branches, which is exactly the step ad-hoc sync scripts miss (a branch checked
out in a worktree can't be deleted, and a worktree with stray files blocks
`git worktree remove`).

**Announce at start:** "Sweeping worktrees, branches, and PR state."

---

## Step 0: Fetch and Inventory

```bash
cd "$(git rev-parse --show-toplevel)"
git fetch --all --prune

git worktree list --porcelain
git branch -vv                       # [gone] marks branches whose upstream vanished
gh pr list --state all --limit 50 \
  --json number,state,headRefName,mergeStateStatus,url
```

Build one table keyed by branch: worktree path (if any), PR number/state,
`mergeStateStatus`, and whether the upstream is `[gone]`.

## Step 1: Classify Each Branch/Worktree

| State | Action |
|---|---|
| PR **merged** or **closed** | Reclaim: remove worktree, delete local branch |
| Upstream `[gone]`, no open PR | Reclaim (squash-merged and remote branch deleted) |
| PR **open**, `mergeStateStatus: BEHIND` | Keep; flag **needs rebase** |
| PR **open**, `mergeStateStatus: DIRTY` | Keep; flag **has conflicts — rebase + resolve** |
| PR **open**, clean | Keep; no action |
| No PR, has commits ahead of main | Keep; flag **unfinished work** (offer `/jackal-supervisor:jackal-finish-branch`) |
| No PR, no commits ahead | Flag **abandoned?** — ask before reclaiming |

## Step 2: Reclaim (merged/closed/gone only)

For each reclaimable branch:

```bash
# Worktree first — a checked-out branch cannot be deleted.
git worktree remove "$WORKTREE_PATH" 2>/dev/null || {
  # Leftover untracked files (caches, .env, node_modules) block removal.
  # Show what's in the way before forcing:
  git -C "$WORKTREE_PATH" status --porcelain
  # Only build artifacts / caches / untracked cruft → force. Real uncommitted
  # edits → STOP and ask.
  git worktree remove --force "$WORKTREE_PATH"
}
git branch -D "$BRANCH"
```

**The only judgment call:** uncommitted *tracked* changes in a merged branch's
worktree. Never force-remove those without asking — show the diff stat and let
the human decide.

## Step 3: Fast-Forward Main

```bash
git checkout main 2>/dev/null || true    # skip if a worktree holds main
git pull --ff-only "$GIT_REMOTE" main
git worktree prune
git remote prune origin
```

If `--ff-only` fails, local main has diverged from origin — report the
divergence (`git log --oneline origin/main..main`); never force-reset without
confirmation.

## Step 4: Rebase Flags

For every open PR flagged BEHIND or DIRTY, print the ready-to-run fix:

```
#NN feat/24-foo — BEHIND origin/main by [k] commits
  → cd .worktrees/24-foo && git fetch origin && git rebase origin/main && $TEST_CMD && git push --force-with-lease
```

Offer to run these now (one at a time, tests between rebase and push). DIRTY
PRs get the same command plus a warning that conflicts will need resolution —
apply the finish skill's rule: mechanical conflicts fine, semantic conflicts
stop and report.

## Step 5: Report

```
Swept: [n] worktrees removed, [n] branches deleted, main fast-forwarded to [sha]
Needs rebase: #NN (BEHIND), #MM (DIRTY — conflicts)
Unfinished:  feat/31-bar (12 commits, no PR)
Kept (open PRs): #22, #27
Stale-open (delivered by a merged PR, still OPEN — close, don't rank): #NN (PR #MM)
```

> **Stale-open issues.** This sweep reclaims *worktrees/branches*. Ranking a
> candidate OPEN issue that a merged PR already delivered is prevented by the
> **Merged-PR gate** in the jackal-supervisor agent ("Reading the backlog") and
> the `execute` skill (Step 4). If you spot a delivered-but-open issue here,
> list it under Stale-open and close it with `gh issue close <#> --reason completed`.
