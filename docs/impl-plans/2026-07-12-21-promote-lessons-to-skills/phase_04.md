# Phase 4: Rule-of-thumb text (memory vs. skills) + cross-reference the promoted lessons

**Goal:** Add the standing rule that separates memory (project facts/preferences) from skill text (agent procedure), and cross-reference the three now-promoted lessons — so future lessons that change agent procedure are written into the owning skill the same session, memory cross-references the skill, and stale memory entries are superseded.

**AC Coverage:**
- "Rule-of-thumb text added: memory is for project facts/preferences; any lesson that changes AGENT PROCEDURE gets written into the owning skill in the same session, with the memory entry cross-referencing the skill change and stale entries superseded."
- Completes "AC6.1: the three lessons appear in the corresponding plugin skill/agent files" by tying them together with the governing rule.

---

## Context

Phases 1-3 establish the finding (memory is director-private) and promote the three lessons into skill/agent text. This phase adds the **governing rule of thumb** so the pattern is self-sustaining: the next time a director learns a procedure-changing lesson, it goes into the skill, not just memory.

**Home decision (planner):** the rule of thumb governs the *supervisor/director's* operating discipline (it decides where lessons are recorded). The best home is the **`jackal-supervisor` agent body** — it is the orchestrating tier that manages backlog, dispatches workers, and already carries operating-discipline text (honest-stopping-point, no-nesting). Placing it there keeps it visible to the tier that makes the record-a-lesson decision. Do NOT put it in a worker agent (implementor/planner/reviewer) — workers don't manage memory.

Per Phase 1's finding, this rule is itself an example of the principle: it is procedure, so it lives in agent/skill text (shared substrate), not memory.

## Implementation

### A. Rule-of-thumb block in the jackal-supervisor agent

**Files:**
- Modify: `plugins/jackal-supervisor/agents/jackal-supervisor.md`

**What to implement:**

Add a **"Recording lessons: memory vs. skills"** section (place it near the other standing-discipline text — e.g., after the "Honest stopping point" header block, or as a new top-level `##` section before "Labels"). Text equivalent to:

```markdown
## Recording lessons: memory vs. skills

Two substrates, two purposes — do not conflate them:

- **Memory** (`~/.claude/projects/.../memory/`) is for **project facts and
  preferences**: which gh account to use, remote names, repo conventions,
  environment quirks. It is loaded only into *this* orchestrating context —
  **spawned agents do not receive it** (verified: no plugin forwards the memory
  index; the Agent-tool dispatch prompt carries none of it).
- **Skill / agent-definition text** is for **agent procedure** — anything that
  changes how a worker or the loop *behaves*. This is the only substrate
  reliably shared with spawned agents.

**Rule of thumb.** Any lesson that changes agent procedure gets written into the
**owning skill (or agent definition) in the same session it is learned** — not
parked in memory for later. When you do this:
1. Edit the owning skill/agent file with the procedure change.
2. Make the memory entry (if any) **cross-reference** the skill change rather
   than restating the procedure ("see jackal-sweep merged-PR gate" — not a
   duplicate copy of the rule).
3. **Supersede stale memory entries** as part of the same correction — delete or
   mark-superseded any memory note the skill change now obsoletes. Do this
   without waiting for the human to ask; stale procedure in memory that never
   reaches subagents is exactly the GL-347 failure mode.

The lessons already promoted under this rule (reference, don't re-park in memory):
- **Merged-PR gate** → "Reading the backlog" (this file) + `execute` skill Step 4.
- **Honest-stopping-point** → this file + `implementor.md` + `execute` dispatch templates (from #18).
- **Sleep<timeout** → `execute` skill "Waiting for async work" (from #18).
- **ruff-format before commit** → `implementor.md` Verify step.
```

The exact per-lesson file locations must match what Phase 1's VERIFY doc recorded and what Phases 2-3 wrote — keep the cross-references disk-truthful.

### B. (Optional, if present) update the memory entry to cross-reference

**Files:**
- Modify (host-level, only if the director's memory contains a now-superseded procedure note): `~/.claude/projects/-Users-jgreaney-Documents-code-jackal-plugins/memory/MEMORY.md`

**What to implement:**

The current repo memory (`MEMORY.md`) holds only project facts (gh account, remotes, upstream sync, branding) — **no procedure lessons** — so there is likely nothing to supersede here. Confirm by reading it. If (and only if) it contains a `feedback_sweep_cross_check_merged_prs`-style procedure note, replace that note's body with a one-line cross-reference to the skill change ("Superseded → see jackal-supervisor 'Merged-PR gate' + execute Step 4"). If it holds only project facts, leave it untouched and note in the PR that there was no stale procedure entry to supersede.

Do not add new procedure content to memory — that would violate the very rule this phase encodes.

**Tests:**
No unit tests (repo has none). Verification is textual: the rule-of-thumb section exists in `jackal-supervisor.md`, names the three-plus-one promoted lessons with correct file locations, and states the same-session / cross-reference / supersede-stale discipline. Frontmatter untouched → `check-frontmatter.py` passes.

---

## Verification

Run: `bash scripts/trace-deps.sh && python3 scripts/check-version-sync.py && python3 scripts/check-frontmatter.py`
Expected: all pass.

Confirm: `jackal-supervisor.md` contains the "Recording lessons: memory vs. skills" rule of thumb, and its cross-references point to the actual locations edited in Phases 2-3 (and #18's locations for the two pre-existing lessons).

## Commit

`docs(supervisor): rule of thumb — procedure lessons go in skills (same session), memory cross-references`
