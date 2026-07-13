# Event-Driven Waits + Subagent Liveness Contract Design

**Issue:** #18 (R1+R2) · Part of Epic #17 (Director-Loop Hardening)
**Design ref:** `docs/design-plans/director-loop-hardening-design.md` (R1, R2)

## Summary

Give the director loop a deterministic, event-driven way to wait for async work and a liveness
contract that lets the loop — not the human — detect and recover from stalled subagents. R1 and R2
ship together because they share one mechanism: a background *watcher* that wakes on real state
change (a new commit) or fires a `STALLED` signal, producing a task-notification. All deliverables
are skill/agent **text** plus one committed helper script; there is no application code in this repo.

## Reframe established by codebase investigation

The audit's 93 sleep-poll turns were the director's **improvised** behavior in the external
mitch-GL session — they are **not** encoded in any current skill. The `execute` skill already waits
correctly via `SendMessage` continuation (execute/SKILL.md:95–154), and a strong verify-don't-trust
framework already exists in `verification-before-completion/SKILL.md`. Therefore:

- **R1 is preventive/additive**, not rip-and-replace: install the watcher pattern + a hard
  sleep<timeout guardrail so a director never *improvises* foreground polling again.
- **R2 extends** the existing verification framework from *local* work to *delegated* work; it must
  cite and strengthen `verification-before-completion`, never duplicate or contradict it.

## Definition of Done

Skill/agent text (and one helper script) that:
1. Documents the watcher pattern (wake-on-state-change; `STALLED` on missed heartbeat) in
   `execute` and, director-side, in `director-loop`.
2. Encodes the sleep<timeout hard rule (≤100s under the 120s Bash timeout) and documents the 120s
   timeout explicitly (absent today).
3. Adds a batched-status rule (≤1 narration per meaningful state change; "still waiting" turns
   prohibited).
4. Adds the honest-stopping-point clause verbatim to `jackal-supervisor.md` and `implementor.md`
   **and** to the dispatch templates that launch them (belt-and-braces per CLAUDE.md).
5. Sets a heartbeat/EXPECT expectation at dispatch and a director-side stall-response procedure.
6. Restates the reinforced non-goal (never accept a claim without a same-turn disk-verified
   observation).
7. Bumps versions + syncs marketplace.json + CHANGELOG for every plugin touched.
Success = the text/script land and CI (`trace-deps` + `check-version-sync` + `check-frontmatter`)
stays green. AC1.1 / AC1.3 / AC2.2 are **manual/observational** — proven only in a future live
director cycle, never gated in this repo's CI.

## Acceptance Criteria

### 18-event-driven-waits-liveness.AC1: Event-driven waits (R1)
- **AC1.1 Success (MANUAL/OBSERVATIONAL — not CI):** a full Complex-issue director cycle completes
  with zero foreground sleep-poll turns in the transcript.
- **AC1.2 Success:** the `execute` skill text states the sleep<timeout hard rule (≤100s / 120s) and
  documents the 120s Bash timeout; no scheduled sleep can produce an exit-143 timeout.
- **AC1.2 Failure:** a skill still permits (or a snippet contains) a foreground `sleep ≥ 120`.
- **AC1.3 Success (MANUAL/OBSERVATIONAL — not CI):** director wait-attributable turns per issue
  drop ≥50% vs the GL-488 baseline.

### 18-event-driven-waits-liveness.AC2: Liveness contract (R2)
- **AC2.1 Success:** the honest-stopping-point clause appears verbatim in both agent definitions
  **and** in the dispatch templates that launch them.
- **AC2.1 Failure:** the clause exists in only one location (frontmatter-only, given known
  enforcement gaps, is a defect per CLAUDE.md).
- **AC2.2 Success (MANUAL/OBSERVATIONAL — not CI):** a deliberately-stalled test agent produces a
  `STALLED` notification and director recovery without human prompting.
- **AC2.3 Success:** the `execute`/`director-loop` text codifies that no director message asserts
  subagent progress unbacked by a same-turn on-disk observation, cross-referencing
  `verification-before-completion`.
- **AC2.3 Failure:** any relay guidance lets the director restate an agent's success claim without a
  cited disk check.

### 18-event-driven-waits-liveness.AC3: Watcher mechanism + hygiene
- **AC3.1 Success:** `scripts/worktree-watcher.sh` exists, is `trace-deps`-clean, wakes on new
  commit, and emits `STALLED <agent> <window>` when no qualifying change occurs within EXPECT.
- **AC3.2 Success:** the stall-response procedure (verify disk → instruct commit-and-report →
  resume from disk if unrecoverable) is in the `execute` skill.
- **AC3.3 Success:** versions bumped + marketplace.json + CHANGELOG synced; `check-version-sync`
  and `check-frontmatter` pass. Worker agents keep `disallowedTools: Agent` (no-nesting intact).

## Architecture

**Chosen approach: Option C (hybrid) — committed helper script + concise inline summary.**

A single committed script `scripts/worktree-watcher.sh` is the reference implementation; both skills
reference it and carry a short "what it does / when to use" summary rather than duplicating the bash.
This is DRY, testable, and matches the repo's existing `scripts/` convention
(`trace-deps.sh`, `check-*.py`).

```
Director dispatches async agent ──► launches scripts/worktree-watcher.sh <wt> <signal> <expect>
        │                                        │ (background task; foreground turn ENDS)
        │                                        ▼
        │                            wakes every 60s, compares HEAD
        │                            ├─ new commit ──► writes "NEW_COMMIT <sha>" ─► task-notification
        │                            └─ no change within EXPECT ─► "STALLED <agent> <window>" ─► notify
        ▼
Director context is touched ONLY on a real notification — never on a schedule.
On STALLED: verify disk state → instruct commit-and-report → resume from disk if unrecoverable.
```

Rejected: **Option A (inline-only)** duplicates bash across two skills and is untestable;
**Option B (script-only)** loses the self-explanatory skill text. C keeps both.

Watcher contract (the script):
- Args: `<worktree-path> <signal-file> <expect-seconds>`. Polls HEAD every 60s **inside the
  background task** — this is not a director foreground sleep, so the sleep<timeout rule doesn't
  bind it; the rule binds only foreground director sleeps.
- Exits 0 writing `NEW_COMMIT <sha>` on change; writes `STALLED <agent> <window>` and exits if
  EXPECT elapses with no qualifying change. Completion generates the task-notification.

## Existing Patterns (from investigation — extend, don't duplicate)

- **Wait today:** `execute/SKILL.md:95–154` — cold dispatch → `SendMessage` continuation → fallback
  on empty/truncated response. The watcher augments this for genuinely long/async phases; it does
  not replace `SendMessage`.
- **Verify-don't-trust:** `verification-before-completion/SKILL.md` ("Evidence before claims,
  always") — AC2.3 text cites this as the model and extends it to delegated work.
- **Dispatch templates (4):** execute (implementor cold + SendMessage), review (reviewer/-deep),
  director-packet, contract-check — each already carries a no-nesting line; the honest-stopping-point
  clause is added alongside it in the two long-running templates (implementor, supervisor).
- **No existing watcher/signal-file pattern and no documented 120s timeout** — both are net-new.
- **Frontmatter:** `implementor.md` has `disallowedTools: Agent` (body line 129); `jackal-supervisor.md`
  keeps `Agent` (sole orchestrator). Clause insertion points: implementor near the Process header;
  supervisor near its "workers never spawn workers" line.

## Implementation Phases

### Phase 1: Watcher helper script
**Goal:** land `scripts/worktree-watcher.sh` with the wake-on-change + STALLED contract.
**Components:** `scripts/worktree-watcher.sh` (+ trace-deps registration if required).
**Done when:** AC3.1; `bash scripts/trace-deps.sh` green.

### Phase 2: R1 skill text — waits, sleep rule, batched status
**Goal:** document the watcher, the sleep<timeout hard rule + 120s timeout, and the batched-status
rule in `execute/SKILL.md`, with the director-side summary in `director-loop/SKILL.md`.
**Components:** execute/SKILL.md, director-loop/SKILL.md.
**Done when:** AC1.2, AC3.2.

### Phase 3: R2 liveness — honest-stopping-point clause + heartbeat
**Goal:** add the clause verbatim to `implementor.md` + `jackal-supervisor.md` **and** their dispatch
templates; add the EXPECT/heartbeat expectation and stall-response procedure; add the AC2.3 relay
rule citing verification-before-completion; restate the reinforced non-goal.
**Components:** implementor.md, jackal-supervisor.md, execute/SKILL.md, director-loop/SKILL.md.
**Done when:** AC2.1, AC2.3; workers retain `disallowedTools: Agent`.

### Phase 4: Version + changelog sync
**Goal:** bump plan-and-execute (3.1.1→), director (1.3.0→), supervisor (3.0.3→) as touched; mirror
marketplace.json; add CHANGELOG entries.
**Components:** the three plugin.json, marketplace.json, CHANGELOG.md.
**Done when:** AC3.3; `check-version-sync` + `check-frontmatter` green.

## Glossary

- **Watcher:** a background bash task (`scripts/worktree-watcher.sh`) that wakes the director only on
  real state change or a missed heartbeat, replacing scheduled polling.
- **Signal file:** the file the watcher writes (`NEW_COMMIT <sha>` / `STALLED <agent> <window>`);
  its completion triggers a task-notification.
- **EXPECT window:** the max interval a dispatch may go without a qualifying state change before the
  watcher declares `STALLED`.
- **Honest-stopping-point clause:** standing agent-prompt text requiring a resumable, disk-truthful
  stopping report; "autonomous" progress claims prohibited.
- **Reinforced non-goal:** no director message may assert progress unbacked by a same-turn
  disk-verified observation, even when skipping the check would be faster.
