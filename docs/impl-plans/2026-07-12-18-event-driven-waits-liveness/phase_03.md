# Phase 3: R2 liveness — honest-stopping-point clause + heartbeat

**Goal:** Add the honest-stopping-point clause verbatim to `implementor.md` and `jackal-supervisor.md` **and** to the dispatch templates that launch them; add the EXPECT/heartbeat expectation at dispatch; add the AC2.3 relay rule citing `verification-before-completion`; restate the reinforced non-goal.
**AC Coverage:** 18-event-driven-waits-liveness.AC2.1, 18-event-driven-waits-liveness.AC2.3

---

## Context

**Before this phase:** `implementor.md` carries `disallowedTools: Agent` (frontmatter line 6) and a
no-nesting body rule (line 129). `jackal-supervisor.md` keeps the `Agent` tool (frontmatter line 4)
as the sole orchestrator, with its "Your workers never spawn workers" line at ~17–19. The two
long-running dispatch templates live in `execute/SKILL.md`: the implementor **cold dispatch**
(~105–121) and the **`SendMessage` continuation** (~125–143). Phase 2 added the watcher, sleep
rule, batched-status, and stall-response to `execute` + `director-loop`.

**What this phase adds (R2 extends verification-before-completion to delegated work — never
duplicates or contradicts it):**
- The **honest-stopping-point clause** (defined below), added verbatim to: `implementor.md`,
  `jackal-supervisor.md`, AND both dispatch templates in `execute/SKILL.md`. Belt-and-braces per
  CLAUDE.md: frontmatter/body restrictions have known enforcement gaps, so the clause must live at
  the prompt level too.
- An **EXPECT/heartbeat expectation** set at dispatch (the dispatch tells the agent the EXPECT
  window and that a resumable commit is expected within it).
- The **AC2.3 relay rule** in `execute`/`director-loop`: no director/orchestrator message may assert
  subagent progress unbacked by a same-turn on-disk observation, cross-referencing
  `verification-before-completion`.
- The **reinforced non-goal** restated.

**CRITICAL invariants (must hold at end of phase):**
- `implementor.md` frontmatter still contains `disallowedTools: Agent`, and the body no-nesting rule
  stays. The clause is **added alongside**, never in place of, the Agent denial.
- `jackal-supervisor.md` frontmatter still lists `Agent` in `tools:`. Do not remove it.
- Nothing in this phase weakens verify-don't-trust; it strengthens it for delegated work.

## Implementation

### The honest-stopping-point clause (author once, paste verbatim in all four locations)

Author this exact block once and use the **identical text** in every location (verbatim is an AC2.1
requirement — a diff between copies is a defect). Suggested canonical text:

> **Honest stopping point.** If you stop before the unit of work is fully done — context limit,
> ambiguity, a blocking dependency, or a genuine stall — commit whatever compiles and report a
> **resumable, disk-truthful** stopping point: what landed on disk (cite the commit SHA and changed
> files), what remains, and the exact next step. Never claim autonomous progress you cannot back
> with an on-disk observation, and never imply the work is further along than the committed state
> proves. A truthful "stopped here, N of M done, resume at X" is correct behavior, not a failure.

This is the design's "Honest-stopping-point clause" glossary term. Keep the wording identical
across all four insertions; only surrounding context lines differ.

### implementor.md

**Files:**
- Modify: `plugins/jackal-plan-and-execute/agents/implementor.md`

**What to implement:** insert the clause verbatim as a new subsection near the `## Process` header
(the design's named insertion point) — e.g. a `### Honest Stopping Point` block right after the
"Follow-Up Phases (Same-Session Continuation)" section and before `## Process`, or as the first item
under Process. Do **not** touch frontmatter line 6 (`disallowedTools: Agent`) or the body
no-nesting rule at line 129 — verify both are still present after the edit.

### jackal-supervisor.md

**Files:**
- Modify: `plugins/jackal-supervisor/agents/jackal-supervisor.md`

**What to implement:** insert the same clause verbatim near the "Your workers never spawn workers"
paragraph (~lines 16–19), as an adjacent paragraph or a short `**Honest stopping point.**` block.
Do **not** remove `Agent` from the `tools:` list on frontmatter line 4 — the supervisor is the sole
orchestrator and keeps it.

### execute/SKILL.md — dispatch templates + relay rule + non-goal

**Files:**
- Modify: `plugins/jackal-plan-and-execute/skills/execute/SKILL.md`

**What to implement:**

1. **Clause in the cold-dispatch template (~105–121):** add the verbatim clause to the `<prompt>`
   body of the `Agent` cold dispatch, alongside the existing "Do not dispatch or invoke any
   subagents…" line. Same verbatim text as the agent files.

2. **Clause in the `SendMessage` continuation template (~125–143):** add the verbatim clause to the
   `<message>` body, alongside its existing no-subagents line.

3. **EXPECT/heartbeat expectation at dispatch:** in both templates, add a line telling the agent the
   EXPECT window and the heartbeat expectation — e.g.:
   > EXPECT: commit a resumable checkpoint within `<expect-seconds>` (a watcher is monitoring this
   > worktree's HEAD; going silent past EXPECT triggers a STALLED recovery). If you cannot finish
   > within EXPECT, commit what compiles and report your honest stopping point.

   Tie the value to the `worktree-watcher.sh <expect-seconds>` arg from Phase 1/2 so the dispatch
   and the watcher agree on the same window.

4. **AC2.3 relay rule:** add (or extend the existing step 3c "Relay a 3-line summary" in Mode 1's
   Process) an explicit rule:
   > **Relay rule (verify-don't-trust for delegated work).** Never restate a subagent's success or
   > progress claim in your own status unless you have made a **same-turn on-disk observation** that
   > backs it (`git log`/`git diff`/reading the changed file this turn) and you cite that evidence.
   > An agent reporting "done" is a claim, not a fact — this is
   > `verification-before-completion` applied to delegated work (its "Agent completed → VCS diff
   > shows changes" / "Agent delegation: Agent reports success → Check VCS diff" rows). Cite it;
   > do not duplicate it.

5. **Reinforced non-goal (restate):** add a short standing line (near the relay rule or in the
   Stop Conditions area):
   > **Reinforced non-goal.** No director message asserts progress unbacked by a same-turn
   > disk-verified observation — even when skipping the check would be faster.

### director-loop/SKILL.md — director-side relay + non-goal mirror

**Files:**
- Modify: `plugins/jackal-director/skills/director-loop/SKILL.md`

**What to implement:** a 3–4 line mirror of the AC2.3 relay rule and the reinforced non-goal, in the
`## Standing obligations` area (adjacent to the Phase 2 wait summary). State that the director never
relays a subagent progress/success claim without a cited same-turn disk observation, cross-referencing
`verification-before-completion`, and pointing to `execute` for the full relay rule. DRY: summary
here, canonical version in `execute`.

**Tests:**
No pytest suite. Verification is the CI trio plus text assertions (Grep):
- The honest-stopping-point clause's distinctive sentence (e.g. "Never claim autonomous progress
  you cannot back with an on-disk observation") appears in **all four** files:
  `implementor.md`, `jackal-supervisor.md`, and **twice** in `execute/SKILL.md` (cold + continuation
  templates). The implementor greps each file and confirms the counts (AC2.1; single-location =
  AC2.1 Failure).
- The four copies are byte-identical for the clause block (verbatim requirement) — implementor
  diffs them.
- `implementor.md` frontmatter still has `disallowedTools: Agent`; `jackal-supervisor.md` frontmatter
  `tools:` still contains `"Agent"` (invariant guard — grep both).
- `execute/SKILL.md` and `director-loop/SKILL.md` contain the relay rule citing
  `verification-before-completion` and the reinforced non-goal (AC2.3; missing/unbacked relay =
  AC2.3 Failure).
Map: AC2.1 → clause in all four locations, verbatim; AC2.3 → relay rule + non-goal citing
verification-before-completion.

---

## Verification

Run: `bash scripts/trace-deps.sh && python3 scripts/check-version-sync.py && python3 scripts/check-frontmatter.py`

Expected: `trace-deps` PASS (edits add prose + `verification-before-completion` skill-name mentions;
if written as the bare skill name it is not a `plugin:name` cross-ref and is not scanned — if the
implementor writes a plugin-qualified ref like `jackal-plan-and-execute:verification-before-completion`
it must resolve, and it does, since that skill ships). `check-frontmatter` PASS — confirms the
`disallowedTools: Agent` and `tools: [... "Agent" ...]` frontmatter still parse as valid YAML with
required keys. version-sync unchanged-pass (bump is Phase 4). All text assertions above hold.

## Commit

`feat(liveness): add honest-stopping-point clause, EXPECT heartbeat, and relay rule`

(May be split per-file: `feat(implementor)`, `feat(jackal-supervisor)`, `feat(execute)`,
`feat(director-loop)` — one logical unit each is fine.)
