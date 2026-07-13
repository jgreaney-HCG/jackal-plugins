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

Two override keys live here:
- `implementor_continuation` (`on` default / `off`) — see "Mode 1: Execute an
  Implementation Plan" below for what it controls.
- `simple_review` (`on` default / `off`) — see "Step 5: Execute by Complexity"
  below for what it controls (whether Simple backlog issues get a default
  Sonnet review pass).

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

**Single-named-file routing read (exception):** when, during routing/triage, an issue names exactly one explicit file path and the classification decision hinges on that file, the orchestrator MAY `Read` that one file in full to classify the issue — classification accuracy matters more than the marginal read, and a full read beats a capped peek.

**Scope guards (must be explicit):** the exception covers exactly one named file only, at triage time. It does NOT authorize: reading a second file, using `Glob`/`Grep` or any search to *find* files, reading files not named in the issue, or reading to *implement* rather than *classify*. Multi-file or search-driven reads still stop and dispatch (`codebase-investigator` / `implementor`).

---

## Mode 1: Execute an Implementation Plan

**Input:** path to plan directory (contains `phase_NN.md` files)

### Process

1. List phase files, read headers only (first 10 lines each)
2. Resolve `implementor_continuation` from Harness Guidance (default `on`). This
   controls how the implementor is dispatched across phases — see "Implementor
   Dispatch: Named Continuation" below.
3. For each phase sequentially:
   a. Read the phase file
   b. Dispatch `implementor` per the continuation rules below
   c. Relay a **3-line summary** of the implementor's report (files, tests,
      commits). Keep the full report only if it flagged uncertainty or issues.
      **Relay rule (verify-don't-trust for delegated work).** Never restate a subagent's success or
      progress claim in your own status unless you have made a **same-turn on-disk observation** that
      backs it (`git log`/`git diff`/reading the changed file this turn) and you cite that evidence.
      An agent reporting "done" is a claim, not a fact — this is
      `verification-before-completion` applied to delegated work (its "Agent completed → VCS diff
      shows changes" / "Agent delegation: Agent reports success → Check VCS diff" rows). Cite it;
      do not duplicate it.
   d. Decide whether to review (see Review Routing below). If the review finds
      **Critical** issues, mark continuation as reset for this issue (see
      Fallback Conditions) before moving to the next phase.
4. After all phases: run final review, then invoke the `finish` skill (which
   rebases if behind, pushes, and opens the PR)

### Implementor Dispatch: Named Continuation

Each issue's implementor is a **named agent**, dispatched cold on phase 1 and
resumed via `SendMessage` for phases 2..N. A resumed agent keeps its prior
transcript warm, so prompt caching applies and it does not re-read stable
files (design plan, shared helpers, unchanged source) it already read in an
earlier phase.

**Phase 1 (or any fresh dispatch — see Fallback Conditions): named cold dispatch.**

```xml
<invoke name="Agent">
<parameter name="subagent_type">jackal-plan-and-execute:implementor</parameter>
<parameter name="name">implementor-<ISSUE_NUMBER></parameter>
<parameter name="description">Implementing phase 1 of #<ISSUE_NUMBER></parameter>
<parameter name="prompt">
PHASE_FILE: [path to phase_01.md]
Working directory: [worktree path]

Implement this phase: read the phase file fully and follow its Context, Goal, and AC
Coverage exactly. Write code, tests where applicable, run the project's verification
commands, and commit your work.

EXPECT: commit a resumable checkpoint within `<expect-seconds>` (a watcher is monitoring this
worktree's HEAD; going silent past EXPECT triggers a STALLED recovery). If you cannot finish
within EXPECT, commit what compiles and report your honest stopping point.

**Honest stopping point.** If you stop before the unit of work is fully done — context limit,
ambiguity, a blocking dependency, or a genuine stall — commit whatever compiles and report a
**resumable, disk-truthful** stopping point: what landed on disk (cite the commit SHA and changed
files), what remains, and the exact next step. Never claim autonomous progress you cannot back
with an on-disk observation, and never imply the work is further along than the committed state
proves. A truthful "stopped here, N of M done, resume at X" is correct behavior, not a failure.

Do not dispatch or invoke any subagents — do the work directly with your own tools.
</parameter>
</invoke>
```

**Phases 2..N (continuation active): resume the same named agent via `SendMessage`.**

```xml
<invoke name="SendMessage">
<parameter name="to">implementor-<ISSUE_NUMBER></parameter>
<parameter name="summary">Continue with phase <N> of #<ISSUE_NUMBER></parameter>
<parameter name="message">
Your context from prior phases is warm — trust what you already read (design plan,
shared helpers, unchanged source) and do NOT re-read it. DO re-read any file you
modified in a prior phase, and any file a prior phase's report flagged as changed,
since your own writes changed them.

PHASE_FILE: [path to phase_0N.md]

Treat this phase file as the complete spec for this phase. Implement it, test it,
verify it, and commit on the current branch.

EXPECT: commit a resumable checkpoint within `<expect-seconds>` (a watcher is monitoring this
worktree's HEAD; going silent past EXPECT triggers a STALLED recovery). If you cannot finish
within EXPECT, commit what compiles and report your honest stopping point.

**Honest stopping point.** If you stop before the unit of work is fully done — context limit,
ambiguity, a blocking dependency, or a genuine stall — commit whatever compiles and report a
**resumable, disk-truthful** stopping point: what landed on disk (cite the commit SHA and changed
files), what remains, and the exact next step. Never claim autonomous progress you cannot back
with an on-disk observation, and never imply the work is further along than the committed state
proves. A truthful "stopped here, N of M done, resume at X" is correct behavior, not a failure.

Do not dispatch or invoke any subagents — do the work directly with your own tools.
</parameter>
</invoke>
```

**Fallback Conditions — abandon continuation, start a fresh cold dispatch** (new
`name`, suffixed `-r2`, `-r3`, ...) when ANY of:
- The `SendMessage` continuation fails, or returns an empty or truncated
  response (same failure posture as the reviewer's Context Limit Handling in
  the `review` skill).
- A review cycle on a prior phase found **Critical** issues — the implementor's
  context may be contaminated by the mistake, so reset it rather than resuming.
- `.jackal/harness-guidance.md` sets `implementor_continuation: off` — in that
  case every phase gets a fresh named dispatch (step "Phase 1" above, repeated
  for every phase), which is exactly the pre-continuation behavior.

**Scope of continuation (per-issue, never crosses boundaries):**
- A **new issue always gets a new implementor** with its own name — continuation
  never crosses issue boundaries.
- **Parallel issues keep separate named agents** (`implementor-<issueA>`,
  `implementor-<issueB>`); their contexts and transcripts never merge. See
  "Parallel Dispatch" below — the two named-agent streams run and continue
  independently of each other.
- The **reviewer is never continued.** Every review dispatch (via the `review`
  skill) is a fresh, stateless `reviewer`/`reviewer-deep` invocation, regardless
  of implementor continuation state.

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
  auth, payments, user data, crypto, or contract boundaries (files under a
  contract source — the project's contracts package or per-component contract
  files named in `docs/canon/registry.md`).

(This table governs per-phase and final review inside Mode 1's plan-execution
loop. Simple issues never enter Mode 1 — they have no plan phase — so their
review is routed directly in Mode 2 / Step 5 below; the tier choice there
matches this one: Sonnet by default, escalating to `reviewer-deep` only when
security-sensitive.)

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

**Simple** (≤1 day, bug fix, single concern) — Standard and Complex routing below
are unaffected by this:
- Create worktree
- Dispatch `implementor` directly with issue doc
- No plan phase, no design phase
- **By default, run exactly one `reviewer` (Sonnet) pass** via the `review`
  skill (tier = `reviewer`, never `reviewer-deep` for a plain Simple issue).
  Route the verdict through the existing fix loop described in "Review
  Routing" above / Mode 1's "When review finds Critical or Important issues":
  on ISSUES_FOUND, dispatch `implementor` to fix and re-review, stopping after
  3 cycles (same stop condition as Mode 1).
  - Security carve-out: a security-sensitive Simple issue (touches auth,
    payments, user data, crypto, or contract boundaries) still escalates to
    `reviewer-deep` per the existing risk rules, instead of `reviewer`.
  - **Override:** if Harness Guidance resolves `simple_review: off` (see
    "Harness Guidance" above), skip the Simple-issue review entirely unless
    the security carve-out applies — this restores the old behavior (review
    only if security-sensitive).

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

**Reinforced non-goal.** No director message asserts progress unbacked by a same-turn
disk-verified observation — even when skipping the check would be faster.

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
  Agent(implementor, name=implementor-XX): CG-XX in worktree A
  Agent(implementor, name=implementor-YY): CG-YY in worktree B
```

Each gets its own named agent (see "Implementor Dispatch: Named Continuation" in
Mode 1) and its own continuation stream — phase 2..N of CG-XX resumes
`implementor-XX` only, phase 2..N of CG-YY resumes `implementor-YY` only. The two
transcripts never merge.

Both run concurrently. When both return:
- Review each independently
- Finish each (rebase if behind, push, PR) — higher-priority first
- If the second branch conflicts with the first's PR, note it in the second PR's
  body; after the first merges, rebase the second and force-push its branch

---

## Waiting for async work

The watcher **augments** `SendMessage` continuation above — it does not replace it.
`SendMessage` is still the default for in-band phase-to-phase resume; reach for the
watcher only for genuinely long-running or async phases.

1. **Watcher.** Launch `scripts/worktree-watcher.sh <worktree> <signal-file>
   <expect-seconds>` as a **background task** and end the foreground turn. It
   polls the worktree's HEAD every 60s inside the background task (that internal
   poll is exempt from the sleep rule below — do not "fix" it) and wakes you only
   on a real event: `NEW_COMMIT <sha>` when HEAD advances, or `STALLED <agent>
   <window>` when EXPECT elapses with no new commit — then it exits, and that
   completion is what generates your task-notification. Your context is touched
   only on a real notification, never on a schedule.

2. **Hard rule — never foreground-sleep to the timeout.** The Bash tool has a
   **120s default timeout** (a foreground `sleep 120` or longer returns exit 143 /
   SIGTERM, wasting the turn). Any foreground wait you schedule must be **≤100s**,
   comfortably under the 120s ceiling. Prefer the watcher (event-driven,
   background) over any foreground sleep at all.

3. **Batched status.** Emit at most one narration per meaningful state change
   (dispatch launched; watcher fired `NEW_COMMIT`; watcher fired `STALLED`; phase
   reviewed). "Still waiting" / "checking again" turns are prohibited — if
   nothing changed, say nothing and let the watcher wake you.

4. **On a `STALLED` notification:**
   1. **Verify disk state** — inspect the worktree (git log / git status / read
      the changed files) to establish what actually landed, per
      `verification-before-completion` — never trust the absence of a commit as
      proof of no work.
   2. **Instruct commit-and-report** — `SendMessage` the named agent to commit
      whatever is done and report a resumable stopping point.
   3. **If unrecoverable, resume from disk** — start a fresh cold implementor
      dispatch seeded from the on-disk state (same posture as the Fallback
      Conditions above), never from the stalled agent's unverified claims.

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
