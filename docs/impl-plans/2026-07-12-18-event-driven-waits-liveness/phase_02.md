# Phase 2: R1 skill text — waits, sleep rule, batched status

**Goal:** Document the watcher, the sleep<timeout hard rule + the 120s Bash timeout, the batched-status rule, and the stall-response procedure in `execute/SKILL.md`, with a director-side summary in `director-loop/SKILL.md`.
**AC Coverage:** 18-event-driven-waits-liveness.AC1.2, 18-event-driven-waits-liveness.AC3.2 (and the AC3.2 half of AC2 groundwork; the R2 relay/clause work is Phase 3)

---

## Context

**Before this phase:** `execute/SKILL.md` already waits correctly via `SendMessage` continuation
(cold dispatch at lines ~105–121, continuation at ~125–143, fallback at ~145–154). There is **no**
documented 120s Bash timeout and **no** sleep guardrail anywhere — a director in a live session
therefore *improvised* foreground sleep-polling (the audit's 93 sleep-poll turns). `director-loop/SKILL.md`
describes the two-tier review architecture and standing obligations but says nothing about waits.

**What this phase adds (R1 is preventive/additive — do NOT rip out `SendMessage`):**
- A "Waiting for async work" section in `execute/SKILL.md` that: (a) summarizes the Phase 1 watcher
  ("what it does / when to use") and references `scripts/worktree-watcher.sh` rather than
  duplicating its bash; (b) states the sleep<timeout **hard rule**; (c) documents the 120s Bash
  timeout explicitly; (d) states the batched-status rule; (e) states the stall-response procedure.
- A concise director-side mirror in `director-loop/SKILL.md`.

**Invariant:** the watcher augments `SendMessage` continuation for genuinely long/async phases — it
does not replace it. Say so in the text.

## Implementation

### execute/SKILL.md — new "Waiting for async work" section

**Files:**
- Modify: `plugins/jackal-plan-and-execute/skills/execute/SKILL.md`

**Where:** add a new top-level section titled `## Waiting for async work` immediately after the
`## Parallel Dispatch` section (before `## Worktree Management`). This keeps dispatch mechanics
together. Do not alter the existing `SendMessage` continuation blocks — reference them.

**What to implement — the section must contain all five rules below, worded so each is
independently checkable:**

1. **Watcher summary + reference (AC3.2 groundwork; DRY per design Option C).**
   > For genuinely long-running or async phases, launch `scripts/worktree-watcher.sh <worktree>
   > <signal-file> <expect-seconds>` as a **background task** and end the foreground turn. The
   > watcher polls the worktree's HEAD every 60s inside the background task and wakes you only on a
   > real event: it writes `NEW_COMMIT <sha>` when HEAD advances, or `STALLED <agent> <window>`
   > when EXPECT elapses with no new commit, then exits — and that completion is what generates
   > your task-notification. Your context is touched **only** on a real notification, never on a
   > schedule. The watcher augments `SendMessage` continuation (above); it does not replace it —
   > `SendMessage` is still the default for in-band phase-to-phase resume.

   Do not paste the script's bash into the skill — reference the file. (This is the whole point of
   the design's Option C.)

2. **Sleep<timeout hard rule (AC1.2).** State, as a hard rule:
   > **Hard rule — never foreground-sleep to the timeout.** The Bash tool has a **120s default
   > timeout** (a foreground `sleep 120` or longer returns exit 143 / SIGTERM, wasting the turn).
   > Any *foreground* wait you schedule must be **≤100s**, comfortably under the 120s ceiling.
   > Prefer the watcher (event-driven, background) over any foreground sleep at all. Never write a
   > snippet containing a foreground `sleep` of 120 or more.

   The literal string "120" and the ≤100s bound must both appear. The 60s watcher poll is INSIDE
   the background task and is explicitly exempt — call that out so a reader does not "fix" it.

3. **Batched-status rule.**
   > **Batched status.** Emit at most **one** narration per meaningful state change (dispatch
   > launched; watcher fired NEW_COMMIT; watcher fired STALLED; phase reviewed). "Still waiting" /
   > "checking again" turns are **prohibited** — if nothing changed, say nothing and let the
   > watcher wake you.

4. **Stall-response procedure (AC3.2).** State the three steps verbatim in intent:
   > **On a `STALLED` notification:** (1) **verify disk state** — inspect the worktree (git log /
   > git status / read the changed files) to establish what actually landed, per
   > `verification-before-completion` (never trust the absence of a commit as proof of no work);
   > (2) **instruct commit-and-report** — `SendMessage` the named agent to commit whatever is
   > done and report a resumable stopping point; (3) **if unrecoverable, resume from disk** — start
   > a fresh cold implementor dispatch seeded from the on-disk state (same posture as the existing
   > Fallback Conditions), never from the stalled agent's unverified claims.

5. **Cross-reference.** The stall-response step (1) and the batched-status rule must cite
   `verification-before-completion` (skill name in text) as the governing principle — this phase
   introduces the citation that Phase 3's AC2.3 relay rule builds on. Do not duplicate that skill's
   content; point to it.

**What to implement:**
Write the section as prose + a short bullet list, matching the skill's existing voice (imperative,
tables where useful). Keep it under ~40 lines. No code fences containing a foreground `sleep >=120`
anywhere in the file (that would trip AC1.2 Failure).

### director-loop/SKILL.md — director-side summary

**Files:**
- Modify: `plugins/jackal-director/skills/director-loop/SKILL.md`

**Where:** add a short subsection under `## Standing obligations during design/plan/execute work`
(e.g. a new numbered item or a `### Waiting for async work` block after item 4).

**What to implement:** a 4–6 line mirror stating that when the director waits on dispatched async
work it uses the event-driven watcher (`scripts/worktree-watcher.sh`), never scheduled foreground
polling; that foreground sleeps are ≤100s under the 120s Bash timeout; that status is batched (no
"still waiting" turns); and that a `STALLED` signal triggers the verify-disk → instruct
commit-and-report → resume-from-disk procedure documented in the `execute` skill. Reference
`execute` for the full procedure rather than restating all of it — director-loop carries the
summary, execute carries the canonical version (DRY).

**Tests:**
No pytest suite. Verification is the CI trio plus targeted text assertions (Grep):
- `execute/SKILL.md` contains the string `120` in the sleep-rule context, the `≤100` (or `<=100`)
  bound, the `worktree-watcher.sh` reference, `STALLED`, `NEW_COMMIT`, a "batched"/"still waiting"
  prohibition, and a citation of `verification-before-completion`.
- `execute/SKILL.md` contains **no** foreground `sleep 120`/`sleep 130`/etc. snippet (AC1.2
  Failure guard). The implementor greps for `sleep 1[2-9][0-9]` and `sleep [2-9][0-9][0-9]` and
  confirms zero matches in a foreground context.
- `director-loop/SKILL.md` references `worktree-watcher.sh` and `execute` and states the
  ≤100s/120s rule.
Map: AC1.2 → the sleep-rule + 120s text; AC3.2 → the stall-response procedure in `execute`.

---

## Verification

Run: `bash scripts/trace-deps.sh && python3 scripts/check-version-sync.py && python3 scripts/check-frontmatter.py`

Expected: `trace-deps` PASS (the new prose adds no plugin-qualified refs that dangle — the
`worktree-watcher.sh` path is a script reference, not a `plugin:name` ref, so it is not scanned as a
cross-reference; if the implementor writes any `jackal-*:` or `ed3d-*:` token it must resolve).
version-sync and frontmatter unchanged-pass (no version/frontmatter edits in this phase — the bump
is Phase 4). Text assertions above all hold.

## Commit

`feat(execute): document watcher, sleep<timeout rule, batched status, stall-response`

(A second commit for `director-loop` is fine if the implementor prefers one-commit-per-file:
`feat(director-loop): mirror event-driven wait + stall-response summary`.)
