# Phase 2: dependency-aware fan-out in execute Mode 1

**Goal:** Generalize Mode 1's "For each phase sequentially" loop into a dependency-aware scheduler that dispatches every currently-dispatchable phase in parallel (Option A), while preserving the sequential default byte-for-byte when no `depends_on:` is present.
**AC Coverage:** 25-phase-independence.AC2.1, 25-phase-independence.AC2.2, 25-phase-independence.AC2.3, 25-phase-independence.AC3.1, 25-phase-independence.AC3.2

---

## Context

**Before this phase:** `plugins/jackal-plan-and-execute/skills/execute/SKILL.md` runs plan phases strictly in order. The relevant existing structure (verified on disk in this stacked worktree, which already contains #18 watcher, #21 merged-PR gate, #22 model tiers, and #19 topology):

- **Mode 1 → Process → step 3: "For each phase sequentially:"** (currently ~line 176) — the loop that reads each phase, dispatches the implementor, relays a verified 3-line summary, and decides on review.
- **"Implementor Dispatch: Named Continuation"** (~line 194) — the warm-trunk pattern: one named agent `implementor-<ISSUE_NUMBER>`, cold cold-dispatched on phase 1, resumed via `SendMessage` for phases 2..N. Includes the `<invoke name="Agent">` (cold) and `<invoke name="SendMessage">` (resume) templates, plus the EXPECT / honest-stopping-point clauses and the "Do not dispatch or invoke any subagents" line.
- **"Fallback Conditions"** (~line 267) and **"Scope of continuation"** (~line 278) — note the existing line: "Parallel issues keep separate named agents (`implementor-<issueA>`, `implementor-<issueB>`); their contexts and transcripts never merge. See 'Parallel Dispatch' below."
- **"Parallel Dispatch"** (~line 509) — the issue-level fan-out model: separate named agents, separate worktrees, non-merging transcripts. R9 layers phase-level fan-out on THIS exact model.
- **"Waiting for async work"** (~line 565) — the #18 watcher (`scripts/worktree-watcher.sh <worktree> <signal-file> <expect-seconds>`), `NEW_COMMIT` / `STALLED` events, and the STALLED recovery procedure.
- **"Orchestration Topology"** (~line 82, from #19) — flat is the default: orchestrator → workers, no middle tier. The GL-488 named-continuation pattern is the reference flat implementation.
- **"Delegation Rules" / "Model Tier Table"** — the orchestrator makes all routing decisions; every Agent dispatch carries an explicit `<parameter name="model">` (implementor = `sonnet`).

**What this phase adds:** dependency-aware scheduling of phases within a single issue. Instead of "for each phase in order," the orchestrator maintains a completed-phase set and, each round, dispatches **every** phase whose `depends_on:` set (Phase 1's schema) is fully satisfied. One dispatchable phase continues on the warm trunk (`implementor-<N>`); additional simultaneously-dispatchable phases run as cold named leaf agents `implementor-<N>-pX` on the **same branch**, non-merging transcripts — reusing the existing Parallel Dispatch model rather than inventing a new concurrency mechanism. When no phase carries `depends_on:`, the scheduler reduces to exactly today's sequential named-continuation loop.

## Implementation

All edits are in `plugins/jackal-plan-and-execute/skills/execute/SKILL.md`. No other file changes in this phase.

### A. Generalize the Mode 1 Process loop into a scheduler

**Files:**
- Modify: `plugins/jackal-plan-and-execute/skills/execute/SKILL.md` — Mode 1 → Process, step 3.

**What to implement:**

Replace the current step 3 opener "3. For each phase sequentially:" (keeping sub-steps a–d as the per-phase body) with a dependency-aware scheduler that wraps those same sub-steps. The scheduler must:

1. **Parse `depends_on:` from phase headers.** Step 1 of Process already reads the first ~10 lines of each phase file; that header window now also carries the optional `**Depends on:**` line (Phase 1 schema). Parse each phase's dependency set from it. **Absent line ⇒ the phase depends on all lower-numbered phases** (the backward-compatible default from Phase 1's schema note).

2. **Validate before scheduling (AC1.2 surfacing).** Before the loop, validate every `depends_on:` entry: each id must name a real, lower-defined phase in this plan; no phase may name itself; there must be no cycle. If validation fails, **halt and report the malformed `depends_on:` as a planner defect** — do not silently ignore it and do not fall back to sequential. (This is the execute-side obligation the Phase 1 schema note references.)

3. **Run the scheduler.** Express it as the design's pseudocode, adapted to this skill's voice:

   ```
   completed = {}                      # phase ids that have finished and been disk-verified
   loop until every phase is in completed:
     ready = { p : p not in completed AND p's depends_on ⊆ completed }
     if ready is empty and phases remain → deadlock: report (should not happen after validation)
     - Dispatch the whole `ready` set this round:
         • one ready phase continues on the warm trunk agent implementor-<ISSUE_NUMBER>
           (SendMessage if continuation active, else the cold Phase-1 dispatch) — prefer the
           lowest-numbered ready phase for the trunk so the common single-ready case is identical
           to today.
         • each additional ready phase is dispatched as a cold leaf agent implementor-<ISSUE_NUMBER>-pX
           (see section B) — same branch, non-merging transcript.
     - Await completions (use the watcher from "Waiting for async work" for any long-running phase;
       short leaf phases need no watcher — see section D).
     - For each returned phase: run sub-steps c (verified 3-line relay) and d (review routing) exactly
       as today, then move that phase id into completed.
   ```

4. **Keep sub-steps a–d intact.** The per-phase body (a: read phase file; b: dispatch implementor per continuation rules; c: verified 3-line relay under the verify-don't-trust relay rule; d: review decision, resetting continuation on Critical) is unchanged — the scheduler decides *which* phases enter that body and *when*, not what the body does. The verify-don't-trust relay rule and the `verification-before-completion` posture are untouched.

**Sequential-default guard (AC2.3) — state it explicitly in the text:**

Add a sentence right after the scheduler pseudocode:

> **Sequential default is byte-for-byte preserved.** When no phase in the plan carries a `**Depends on:**` line, every phase depends on all prior phases, so `ready` is always exactly the single lowest-numbered incomplete phase. The scheduler then reduces to the current named-continuation loop — cold dispatch on phase 1, `SendMessage` resume for phases 2..N — with no cold-start regression and no parallel dispatch. Fan-out engages **only** when a plan explicitly declares independence via `depends_on:`.

### B. Phase-level Option A leaf dispatch (build on Parallel Dispatch)

**Files:**
- Modify: `plugins/jackal-plan-and-execute/skills/execute/SKILL.md` — add a subsection under "Implementor Dispatch: Named Continuation" (after the Fallback Conditions / Scope-of-continuation block), and cross-reference it from "Parallel Dispatch".

**What to implement:**

Add a subsection titled **"Phase-level fan-out (Option A: warm trunk + cold leaves)"** documenting the parallel leaf dispatch. It must state:

- **This is the existing Parallel Dispatch model applied within one issue.** Where "Parallel Dispatch" runs `implementor-<issueA>` and `implementor-<issueB>` on **different branches / worktrees**, phase-level fan-out runs `implementor-<N>` (trunk) plus `implementor-<N>-pX` (leaves) on the **same branch / same worktree**. Both are: separate named agents, concurrent, non-merging transcripts. No new concurrency mechanism is introduced — cross-reference "Parallel Dispatch" explicitly.
- **Trunk vs leaf:**
  - The **trunk** `implementor-<ISSUE_NUMBER>` carries warm context from phase 1 and is resumed via `SendMessage` (per "Named Continuation" above). It takes the lowest-numbered ready phase each round.
  - A **leaf** `implementor-<ISSUE_NUMBER>-pX` (where `X` is the phase number, e.g. `implementor-25-p3`) is a **cold** named dispatch — it does not share the trunk's transcript. Cold-start is acceptable precisely because a leaf phase is independent by construction (its `depends_on:` excludes the trunk's current work), so it does not need the trunk's in-context output; its phase file is the complete spec. State this rationale inline (it is the design's "accepted tradeoff").
- **Leaf dispatch template.** Provide an `<invoke name="Agent">` block modeled exactly on the existing cold Phase-1 dispatch, changed only in `name` (→ `implementor-<ISSUE_NUMBER>-p<PHASE>`), `description`, and `PHASE_FILE`. It MUST carry:
  - `<parameter name="model">sonnet</parameter>` (Model Tier Table — implementor = Sonnet; a missing model param is a defect).
  - The same `EXPECT` / honest-stopping-point clauses as the trunk cold dispatch.
  - The line **"Do not dispatch or invoke any subagents — do the work directly with your own tools."** verbatim (subagent discipline — the leaf is a worker and never fans out).
  - The same worktree path as the trunk (same branch).
- **Leaves are never continued across phases.** Each leaf is single-phase: it is dispatched cold for its one independent phase and returns. If a later phase depends on a leaf's phase, that later phase is scheduled by the orchestrator in a subsequent round (on the trunk or a new leaf) — never by the leaf resuming itself. This keeps every fan-out decision with the orchestrator.

Then add a one-line cross-reference at the end of the "Parallel Dispatch" section:

> **Phase-level fan-out reuses this model within a single issue** — see "Phase-level fan-out (Option A: warm trunk + cold leaves)" under Mode 1. Same-branch leaves (`implementor-<N>-pX`) are the intra-issue analogue of these cross-issue named agents.

### C. Same-branch write safety + unchanged verify posture (AC3.1)

**Files:**
- Modify: `plugins/jackal-plan-and-execute/skills/execute/SKILL.md` — inside the section B subsection, add a short "Same-branch write safety" note.

**What to implement:**

Add a note stating:

- **Parallel leaf phases commit to one branch HEAD.** This is safe because independent phases are disjoint by construction — a phase only carries `depends_on:` (and thus becomes a parallel leaf) when its files do not overlap the phases running concurrently. Commits are additive; each phase's diff touches different files.
- **Commit / merge ordering.** Concurrent leaves committing to the same HEAD interleave commits; that is fine (no rebase between them — same branch). If two dispatchable phases are *not* genuinely file-disjoint, they must NOT both carry independence-granting `depends_on:` — that is a planner defect, caught by the same AC1.2 surfacing rule. Per-phase timeout attribution across interleaved commits is explicitly **out of scope** (leaf phases are short; noted, not solved) — reference the same out-of-scope note the design carries.
- **Review + verify posture is unchanged.** Each phase's work is still disk-verified via the verify-don't-trust relay rule and routed through Review Routing exactly as in the sequential path. Fan-out changes *when* phases run, never *whether* their output is verified. Do not weaken `verification-before-completion`.

### D. Watcher cross-reference for long parallel phases (design DoD item 5)

**Files:**
- Modify: `plugins/jackal-plan-and-execute/skills/execute/SKILL.md` — one sentence in the scheduler text and/or the section B subsection.

**What to implement:**

State (cross-reference, do not duplicate the watcher mechanism): a long-running parallel phase stream gets its own watcher via "Waiting for async work" — launch `scripts/worktree-watcher.sh` per long leaf/trunk stream as needed; short leaf phases (the common case for independent tests/docs/plumbing) need no watcher and are simply awaited. The watcher fires on any commit to the shared HEAD (per-phase attribution out of scope, per section C).

### E. Topology consistency cross-reference (design DoD, #19 stack)

**Files:**
- Modify: `plugins/jackal-plan-and-execute/skills/execute/SKILL.md` — one sentence in the section B subsection.

**What to implement:**

State that phase-level fan-out **stays flat**: the orchestrator dispatches trunk and leaf workers directly; there is no middle tier and no worker gains the `Agent` tool. Cross-reference the "Orchestration Topology" section — this is flat topology (orchestrator → parallel workers), consistent with #19, and is NOT the justification-gated nested-supervisor exception.

### F. No-nesting / sole-Agent-holder invariant (AC3.2) — make it explicit

**Files:**
- Modify: `plugins/jackal-plan-and-execute/skills/execute/SKILL.md` — a sentence in the section B subsection.

**What to implement:**

State plainly, in the fan-out subsection: **the orchestrator — not the implementor — makes every fan-out decision.** Workers (`implementor-<N>`, `implementor-<N>-pX`) keep `disallowedTools: Agent`; no worker gains the `Agent` tool; the implementor never self-dispatches parallel sub-tasks. `jackal-supervisor` remains the sole `Agent`-holder (CLAUDE.md). The parallelism comes from the orchestrator dispatching multiple named workers in one message, exactly as issue-level Parallel Dispatch already does — never from a worker spawning workers.

**Tests:**
No unit tests (skill prose; repo has no pytest). Verification is:
- `check-frontmatter.py` passes (no frontmatter touched in SKILL.md — this skill's frontmatter is `name`/`description`/`user-invocable`/`argument-hint`).
- `trace-deps.sh` passes (no dependency graph change — no new file references introduced beyond `scripts/worktree-watcher.sh`, which already exists and is already referenced).
- Manual/reviewer read confirms AC2.1 (scheduler described), AC2.2 (Option A on Parallel Dispatch), AC2.3 (byte-for-byte sequential default stated), AC3.1 (same-branch safety + unchanged verify), AC3.2 (no worker gains Agent; orchestrator dispatches).
- Map to `test-requirements.md`.

**Invariants to preserve (do NOT violate):**
- No worker frontmatter gains `Agent`. Leaf agents are still `jackal-plan-and-execute:implementor` (which has `disallowedTools: Agent`).
- Every new dispatch template carries `<parameter name="model">sonnet</parameter>` and the "Do not dispatch or invoke any subagents" line.
- The verify-don't-trust relay rule and `verification-before-completion` posture are unchanged.
- The sequential (no-`depends_on:`) path must remain byte-for-byte the current named-continuation behavior.

---

## Verification

Run: `bash scripts/trace-deps.sh && python3 scripts/check-version-sync.py && python3 scripts/check-frontmatter.py`
Expected: all three pass. (No version change in this phase; version-sync still reports the current on-disk versions as in sync.)

Reviewer read of `execute/SKILL.md` confirms:
- Mode 1 step 3 is now a dependency-aware scheduler (completed set; `ready` = phases whose `depends_on:` ⊆ completed; dispatch all ready in parallel), with sub-steps a–d preserved.
- Malformed `depends_on:` is validated and surfaced (halt + report), not silently ignored (AC1.2 execute side).
- A "Phase-level fan-out (Option A)" subsection exists, explicitly building on Parallel Dispatch, with a cold leaf `implementor-<N>-pX` dispatch template on the same branch, non-merging transcripts.
- The byte-for-byte sequential-default guard sentence is present (AC2.3).
- Same-branch write safety + unchanged verify note is present (AC3.1).
- Watcher and #19 topology cross-references are present (no duplication).
- The orchestrator-dispatches / no-worker-Agent / sole-supervisor-holder statement is present (AC3.2).

## Commit

`docs: dependency-aware phase fan-out (Option A) in execute (#25 R9)`
