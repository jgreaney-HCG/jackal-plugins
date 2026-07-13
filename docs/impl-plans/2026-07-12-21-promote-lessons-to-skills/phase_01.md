# Phase 1: VERIFY memory propagation + verify/cross-reference the #18 outputs

**Goal:** Empirically establish whether spawned agents receive the project memory index, and confirm the two #18 text outputs (honest-stopping-point clause, sleep<timeout rule) are already present on disk — recording both findings so later phases build on fact, not assumption.

**AC Coverage:**
- "VERIFY step first: empirically confirm whether spawned agents receive the memory index; record the finding in the PR."
- "Honest-stopping-point clause present in supervisor + implementor agent definitions (this is the R2.1 output from #18 — reference, don't duplicate divergently)."
- "Sleep<timeout rule present in the execute skill (R1.3 output from #18)."

---

## Context

This worktree is branched off a `main` that already contains the merged #18 work. That means the honest-stopping-point clause and the sleep<timeout rule are **already on disk** — this phase does not re-author them. Its job is to (a) run the empirical VERIFY step and record the finding, and (b) confirm the #18 outputs are present and note their exact locations so Phase 4 can add rule-of-thumb text that cross-references them.

The VERIFY finding is the framing decision for the whole issue: if spawned agents do **not** receive `MEMORY.md`, then memory is director-private and skills are the sole cross-agent channel — which is exactly why the three lessons must move into skill text (Phases 2-4).

### Investigation already performed by the planner (build on this — re-confirm, don't re-derive)

1. **No plugin file references memory.** `grep -rniE "MEMORY\.md|memory index|auto-memory|memory/" plugins/` returns **zero matches**. No skill or agent definition injects, reads, or forwards `MEMORY.md`.
2. **The memory lives at the Claude Code host level**, not in the repo: `~/.claude/projects/-Users-jgreaney-Documents-code-jackal-plugins/memory/MEMORY.md`. It is surfaced into the **main conversation's** system context by the host auto-memory feature (it appears in the top-level session's `# claudeMd` / auto-memory reminder block).
3. **Subagents dispatched via the `Agent` tool get a fresh context** assembled from: the agent definition file's frontmatter + body, plus the dispatch prompt. The host does not inject the project auto-memory into that subagent system prompt. Therefore a dispatched `implementor`/`planner`/`reviewer`/`jackal-supervisor` subagent does **not** receive `MEMORY.md` unless the dispatcher pastes it into the prompt (no skill does this).
4. **Conclusion (to be re-confirmed and recorded):** memory is director-private; skills/agent-definition text are the only substrate reliably shared with spawned agents. This matches the design's R6 hypothesis and the GL-347 failure mode.

## Implementation

This phase produces a **finding document**, not code. No plugin behavior changes here.

### VERIFY: memory propagation to spawned agents

**Files:**
- Create: `docs/impl-plans/2026-07-12-21-promote-lessons-to-skills/VERIFY-memory-propagation.md`

**What to implement:**

Re-run the confirmation commands and record results in the finding doc. Use Grep/Glob/Bash (read-only):

- `grep -rniE "MEMORY\.md|memory index|auto-memory|memory/" plugins/` — expect zero matches (no plugin forwards memory).
- Confirm the memory file location on the host: check that `~/.claude/projects/-Users-jgreaney-Documents-code-jackal-plugins/memory/MEMORY.md` exists and is a host-level file outside the repo (it is not tracked in git — confirm with `git -C "$(git rev-parse --show-toplevel)" ls-files | grep -i memory` returning nothing under the repo).
- Inspect how agents are dispatched: the `execute` skill's dispatch templates (`plugins/jackal-plan-and-execute/skills/execute/SKILL.md`, the `<invoke name="Agent">` and `<invoke name="SendMessage">` blocks) pass only `PHASE_FILE`, working directory, and prompt text — never the memory index. Cite these as evidence that nothing forwards memory into the subagent prompt.

Write the finding doc with this structure:

```markdown
# VERIFY: Do spawned agents receive the memory index?

**Finding:** NO. Spawned agents do not receive `MEMORY.md`.

**Evidence:**
1. No plugin skill or agent definition references MEMORY.md (grep result: 0 matches across plugins/).
2. The memory index is a Claude Code host-level file (~/.claude/projects/.../memory/MEMORY.md), loaded only into the MAIN conversation's system context — not tracked in the repo, not part of any agent definition.
3. Agent-tool dispatches (execute skill's Agent/SendMessage templates) pass only the phase file, working dir, and prompt — no memory content is injected into the subagent context.

**Consequence:** Memory is director-private. Skill text and agent-definition text are the ONLY substrate reliably shared with spawned agents. Operational lessons that must reach subagents (merged-PR gate, honest-stopping-point, sleep<timeout) therefore belong in skills/agent definitions, not memory. This is exactly the GL-347 failure mode: the nested supervisor subagent lacked a lesson the director's private memory implied.

**If a later Claude Code version DOES inject project memory into subagents:** the migration is still correct — skill text is the authoritative, version-controlled home for procedure; memory then merely echoes it. The rule-of-thumb (Phase 4) codifies this.
```

If, on re-running, the evidence somehow contradicts the planner's finding (e.g., a plugin is found to forward memory, or the harness is observed injecting it), record the **actual** observed result instead and note the divergence — the finding must be disk-truthful, not a copy of this template. If it cannot be determined definitively, say so explicitly and note that the implementor should record the empirical result in the PR body.

### VERIFY: #18 outputs already present (reference, don't re-author)

**Files:**
- Modify: `docs/impl-plans/2026-07-12-21-promote-lessons-to-skills/VERIFY-memory-propagation.md` (append a "#18 outputs present" section)

**What to implement:**

Confirm and record the exact on-disk locations of the two #18 text outputs. These already exist — do NOT rewrite them, do NOT create divergent copies:

- **Honest-stopping-point clause** — confirm it is present in:
  - `plugins/jackal-plan-and-execute/agents/implementor.md` (under a `### Honest Stopping Point` heading).
  - `plugins/jackal-supervisor/agents/jackal-supervisor.md` (in the header block, alongside "workers never spawn workers").
  - Also present in `plugins/jackal-plan-and-execute/skills/execute/SKILL.md` (both the Agent and SendMessage dispatch templates).
- **Sleep<timeout rule** — confirm it is present in `plugins/jackal-plan-and-execute/skills/execute/SKILL.md` under "Waiting for async work" ("Hard rule — never foreground-sleep to the timeout", the 120s ceiling / ≤100s foreground wait).

Grep to locate exact line ranges and record them in the finding doc, e.g.:

```markdown
## #18 outputs present (verified, referenced not re-authored)

- Honest-stopping-point clause:
  - plugins/jackal-plan-and-execute/agents/implementor.md — "### Honest Stopping Point" (present).
  - plugins/jackal-supervisor/agents/jackal-supervisor.md — "**Honest stopping point.**" header block (present).
  - plugins/jackal-plan-and-execute/skills/execute/SKILL.md — in both dispatch templates (present).
- Sleep<timeout rule:
  - plugins/jackal-plan-and-execute/skills/execute/SKILL.md — "Waiting for async work" > "Hard rule — never foreground-sleep to the timeout" (present, ≤100s under 120s Bash timeout).

Conclusion: ACs "honest-stopping-point present" and "sleep<timeout present" are satisfied by the merged #18 work. This issue REFERENCES them (Phase 4 cross-references from the rule-of-thumb text); it does not duplicate or diverge from them.
```

Use Grep with the literal strings above to confirm. If any is genuinely absent (it should not be — #18 is merged), STOP and report — that would mean the branch base is wrong, and re-authoring would risk divergence from the canonical #18 text.

**Tests:**
This is an investigation/documentation phase. No unit tests (this repo has none — the suite is `TEST_CMD`). Verification is operational: the finding doc exists and its claims are backed by the grep/read evidence cited in it. `TEST_CMD` must still pass (it will — no plugin files changed yet).

---

## Verification

Run: `bash scripts/trace-deps.sh && python3 scripts/check-version-sync.py && python3 scripts/check-frontmatter.py`
Expected: all pass (no plugin files changed in this phase, so version-sync and frontmatter are unaffected).

Confirm: `docs/impl-plans/2026-07-12-21-promote-lessons-to-skills/VERIFY-memory-propagation.md` exists and states the memory-propagation finding plus the #18-outputs-present confirmation, each backed by cited evidence.

## Commit

`docs: record VERIFY finding (spawned agents do not receive memory index) for #21`
