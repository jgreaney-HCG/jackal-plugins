---
name: execute
description: Executes implementation plans or drives continuous issue execution from the GitHub Issues backlog. Model-adaptive — dispatches Sonnet implementors, reviews conditionally based on risk, and parallelizes independent work. Runs autonomously until genuinely stuck.
user-invocable: true
argument-hint: "[plan-directory] [working-directory]"
---

# Execute

Two modes:
1. **Plan mode** — execute a specific implementation plan (phase files in a directory)
2. **Backlog mode** — continuously pull and execute issues from the GitHub Issues backlog until stuck

**Subagent discipline:** every Agent dispatch prompt in this skill must include
the line "Do not dispatch or invoke any subagents — do the work directly with
your own tools." Workers never spawn workers.

---

## Harness Guidance

Resolve `.jackal/harness-guidance.md` by **walking up from the working directory to the repo root**,
reading every one found. This lets a monorepo scope overrides per module: a module-level
`.jackal/harness-guidance.md` overrides the repo-root one key-by-key (**nearest-wins**), and the
root provides the base. Single-package repos just have the one at root — same behavior as before.

```bash
# WORKDIR = the dispatch's working directory (a module dir, a worktree, or the repo root).
# Collect guidance files from repo root down to WORKDIR; later (deeper) files override earlier.
dir="$WORKDIR"; chain=""
while :; do
  [ -f "$dir/.jackal/harness-guidance.md" ] && chain="$dir/.jackal/harness-guidance.md
$chain"
  [ "$dir" = "$REPO_ROOT" ] && break
  parent=$(dirname "$dir"); [ "$parent" = "$dir" ] && break; dir="$parent"
done
printf '%s' "$chain" | while read -r f; do [ -n "$f" ] && { echo "=== $f ==="; cat "$f"; }; done
```

Apply overrides to defaults (review policy, parallel execution policy, stop
conditions). Precedence, lowest to highest: built-in defaults < Jackal Config keys < root
`.jackal/` < module `.jackal/`. If no guidance file exists anywhere in the chain, all defaults apply.

---

## Delegation Rules

The orchestrator manages state and makes routing decisions. It **never** writes code, runs project tests, or investigates the codebase for patterns.

| Do directly | Delegate |
|---|---|
| Read/write backlog state and issue docs | Code + tests → `implementor` |
| Run conflict gate git commands | Phase file generation → `planner` |
| Create/remove worktrees | Code review → `reviewer`/`reviewer-deep` (via `review` skill) |
| Decide whether and when to review | |
| Rebase, push, open PRs | |
| Update backlog state | |

If you find yourself about to write code, run `$TEST_CMD` for correctness, or grep through the codebase — stop and dispatch an `implementor` or `reviewer` instead.

---

## Mode 1: Execute an Implementation Plan

**Input:** path to plan directory (contains `phase_NN.md` files)

### Process

1. List phase files, read headers only (first 10 lines each)
2. For each phase sequentially:
   a. Read the phase file
   b. Dispatch `implementor` with the phase file path and working directory
      (prompt includes the no-subagents line)
   c. Relay a **3-line summary** of the implementor's report (files, tests,
      commits). Keep the full report only if it flagged uncertainty or issues.
   d. Decide whether to review (see Review Routing below)
3. After all phases: run final review, then invoke the `finish` skill (which
   rebases if behind, pushes, and opens the PR)

### Review Routing

After each phase completes, decide:

| Condition | Action |
|---|---|
| Phase touches auth, payments, user data, or crypto | Full review |
| Phase is the final phase | Full review |
| Implementor's self-review flagged uncertainty | Full review |
| Phase is pure infrastructure/config | Skip review |
| All other phases | Skip per-phase review; catch issues in final review |

**Final review is always mandatory**, and it is tiered by risk:

- **`reviewer` (Sonnet)** — the default for Simple and Standard issues.
- **`reviewer-deep` (Opus)** — for Complex issues, and for any diff touching
  auth, payments, user data, crypto, or contract boundaries (files under the
  project's contracts package).

**If `docs/canon/` exists in the repo**, also run `/jackal-director:contract-check` (the
jackal-director conformance gate) in the same message as the final review
dispatch — they're independent and run in parallel. The bar before finish is
review PASS **and** contract-check CLEAN (or FLAGGED with every flag explained
in your report).

After the final review passes, check for UI changes — `finish` will invoke `jackal-ui-verify` automatically if UI files were touched. It covers the full diff from plan start to completion.

When review finds Critical or Important issues:
1. Dispatch `implementor` with the issues list and instruction to fix
2. Re-run review
3. If same issues persist after 3 cycles → stop, report to human

Minor issues from the final review: report them, don't block.

---

## Mode 2: Continuous Backlog Execution

**Input:** none (reads from the GitHub Issues backlog)

This is the autonomous orchestration loop. The orchestrator (you, running in the main conversation) drives issues to completion without human intervention, stopping only when genuinely stuck.

### The Loop

```
while true:
  1. Read backlog state (GitHub issues)
  2. Identify unblocked issues in Ready
  3. Run conflict gate on candidates
  4. Select issue(s) to work on
  5. Execute issue (route by complexity)
  6. Finish (rebase if behind, push, open PR)
  7. Report completion (one-liner)
  8. Loop back to step 1
```

### Step 1: Read Backlog State

Read `gh_repo` and `label_style` from `## Jackal Config` in CLAUDE.md. `label_style` is `slash` |
`colon` (default **slash**) — it sets the separator in status labels. The examples below use `/`;
substitute `:` if the project sets `label_style: colon`.

```bash
gh issue list --repo "$GH_REPO" \
  --label "status/ready" \
  --state open \
  --json number,title,labels,body
```

For each candidate, parse the issue body for `Blocked by:`, `Module:`, `Complexity:`, and `In scope:` sections (the issue doc on disk is still the source for rich detail; GH issue body mirrors the same structure).

**Readiness validation — don't trust the label alone.** Before treating a `status/ready` issue as workable, confirm its body is actually scoped:
- Acceptance Criteria exist and are filled in — **not** still placeholders (`- [ ] AC1:` with nothing after the colon, or template text like `[1-3 sentences]`).
- Scope has explicit `In scope:` paths (not `[explicit file paths]`).
- Complexity is one of Simple/Standard/Complex (not the unfilled `Simple | Standard | Complex` line), and a `complexity/*` label is present.

If an issue is labelled `status/ready` but its body is still a template skeleton, **do not work it.** Report it as mislabelled (ready label, unscoped body) and skip — surfacing it so a human or the supervisor can finish scoping. A label is a claim; the body is the evidence.

Issues are grouped by label:
- `status/ready` → eligible candidates (subject to the readiness validation above)
- `status/in-progress` → currently active (don't double-pick)
- `status/paused` / `status/blocked` → skip
- closed → resolved

### Step 2: Identify Unblocked Work

Read each Ready issue's doc. Check its `Blocked by:` field.
An issue is unblocked when all its blockers are in Resolved.

### Step 3: Conflict Gate

For each unblocked candidate:

```bash
for branch in $(git branch --list 'feature/*' '*/[0-9]*-*' | tr -d ' '); do
  echo "=== $branch ==="
  git diff --name-only main...$branch 2>/dev/null
done
```

Compare active branch file sets against candidate's `In scope:` paths.
- Same file touched → hard block
- Same directory, different files → soft warning (proceed with note)
- No overlap → clear

### Step 4: Select Work

Determine priority order from the `priority/*` label (`priority/high` > `priority/medium` > `priority/low`), falling back to issue number (lower = older = first) when a candidate has no priority label. Issues with no `priority/*` label sort *after* labelled ones at the same tier — flag any unprioritized `status/ready` issue so the backlog stays orderable.

If multiple candidates are unblocked and clear:
- Check for independence (no shared files, no dependency between them)
- If independent: dispatch in parallel (two implementors, two worktrees), highest-priority first
- If dependent: execute highest-priority first

### Step 5: Execute by Complexity

Read the issue doc's `Complexity` field:

**Simple** (≤1 day, bug fix, single concern):
- Create worktree
- Dispatch `implementor` directly with issue doc
- No plan phase, no design phase
- Review only if security-sensitive

**Standard** (multi-file, clear ACs):
- Create worktree
- Dispatch `planner` with issue doc (it generates a mini design plan + phase files)
- Execute phases sequentially (Mode 1 above)

**Complex** (architectural decisions, ambiguous scope):
- STOP. Report: "CG-XX is Complex — needs design decisions. Run /jackal-supervisor:jackal-design-plan to start."
- Do not attempt autonomous execution of Complex issues.

### Step 6: Complete and Update

After the issue passes review, invoke the `finish` skill (or `jackal-finish-branch`
when the supervisor wrappers are in use). It rebases onto origin/main if the
branch is behind, re-verifies, pushes, and opens a PR with `Closes #N`. **Never
merge locally** — the PR is the only completion path.

Then: remove `status/in-progress` (leave the issue open — GitHub closes it when
the PR merges), update the issue doc Status → In Review, record the PR URL, and
continue the loop to the next issue — do not block waiting for a human to merge.
Keep the worktree while its PR is open (you may need to push fixups); `/jackal-supervisor:jackal-sweep`
reclaims it after merge.

### Step 7: Report

Print one line:
```
✓ #24 PR opened (#NN). Starting #25 next (also dispatching #26 in parallel).
```

### Stop Conditions

Stop the loop and report to human when:
- No unblocked issues remain in Ready/Backlog
- All unblocked issues are Complex
- Conflict gate blocks all candidates
- An issue fails review 3 times
- A genuine ambiguity needs human decision (unclear AC, missing dependency, env issue)

Report clearly:
```
Stopped: [reason]
Completed this session: CG-X, CG-Y, CG-Z
Next unblocked: CG-A (waiting for [what])
Blocked: CG-B (conflict with [branch])
```

---

## Parallel Dispatch

When two issues are independent:

```
Dispatch in single message:
  Agent(implementor): CG-XX in worktree A
  Agent(implementor): CG-YY in worktree B
```

Both run concurrently. When both return:
- Review each independently
- Finish each (rebase if behind, push, PR) — higher-priority first
- If the second branch conflicts with the first's PR, note it in the second PR's
  body; after the first merges, rebase the second and force-push its branch

---

## Worktree Management

Every issue gets its own worktree:

```bash
ISSUE="24"             # GitHub issue number (the work-unit key)
SLUG="kebab-title"
TYPE="feat"            # conventional-commit type: feat|fix|docs|chore|refactor|...

# Ensure .worktrees is gitignored
grep -q "\.worktrees" .gitignore || echo ".worktrees/" >> .gitignore

BASE="$(git symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null | sed 's#origin/##')"
: "${BASE:=main}"

# Create (or reuse existing)
if [ ! -d ".worktrees/${ISSUE}-${SLUG}" ]; then
  git worktree add .worktrees/${ISSUE}-${SLUG} \
    -b ${TYPE}/${ISSUE}-${SLUG} "$BASE"
fi
```

Pass the worktree absolute path to every implementor dispatch.

---

## Context Strategy

With 1M context window:
- Never /clear between issues
- Accumulated knowledge improves each subsequent dispatch
- Phase files read just-in-time (not all upfront) to avoid noise
- Implementor reports kept in context (orchestrator learns patterns)

If context genuinely runs low (>600K tokens used), summarize completed work and continue. Don't clear.

---

## Integration with Supervisor

The supervisor (jackal-supervisor agent or skills) handles:
- Creating issues, managing backlog priority
- Assigning work (conflict gate + worktree creation)
- Pausing/resuming

This skill handles:
- Executing assigned work
- Merging completed work
- Updating backlog state post-completion

They can run together: supervisor assigns, execute runs. Or execute can self-serve from the GitHub Issues backlog in autonomous mode.
