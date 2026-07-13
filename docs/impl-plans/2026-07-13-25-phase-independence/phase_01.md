# Phase 1: `depends_on:` schema in the planner

**Goal:** Add the optional `depends_on:` field plus absent-⇒-sequential prose to planner.md's phase template, and define a malformed `depends_on:` as a planner defect the execute skill must surface.
**AC Coverage:** 25-phase-independence.AC1.1, 25-phase-independence.AC1.2

---

## Context

**Before this phase:** `plugins/jackal-plan-and-execute/agents/planner.md` contains a "Phase file structure" markdown template (currently lines ~58–99). The template has a header block:

```markdown
# Phase N: [Title]

**Goal:** [One sentence]
**AC Coverage:** [which ACs this phase implements — use full identifiers]
```

There is no way for a plan to declare that phases may run out of order. Execute (Phase 2) will read these headers to schedule work; today it always runs phases strictly sequentially.

**What this phase adds:** an optional `depends_on:` field in the phase-file header template, prose describing its semantics (absent ⇒ depends on all prior phases ⇒ sequential default), and a schema note declaring a malformed `depends_on:` a planner defect. This phase is text-only in one file (`planner.md`). It does NOT touch execute — the scheduler that consumes this field is Phase 2.

This is documentation of a contract between planner output and execute input. No `docs/canon/` contract-model change is involved (this repo has no `docs/canon/` — confirmed absent), so no impact statement is required.

## Implementation

### `depends_on:` field in the phase template

**Files:**
- Modify: `plugins/jackal-plan-and-execute/agents/planner.md` — add the field to the phase-file template header and add a schema note directly after the template's closing fence.

**What to implement:**

1. **Add the field to the template header.** In the "Phase file structure" fenced code block, insert a `depends_on:` line immediately **after** the `**AC Coverage:**` line and before the `---` separator, so the header becomes:

   ```markdown
   # Phase N: [Title]

   **Goal:** [One sentence]
   **AC Coverage:** [which ACs this phase implements — use full identifiers]
   **Depends on:** [optional — list of prior phase ids, e.g. `phase_01, phase_02`, that must
   complete before this phase may start. OMIT this line entirely for the sequential default
   (see schema note below).]
   ```

   Keep the exact byte content of every other line in the template unchanged. The field name in the rendered phase file is `**Depends on:**` (matching the existing bold-label header style `**Goal:**` / `**AC Coverage:**`). Where prose refers to the field generically, call it `depends_on:` (the schema/design name).

2. **Add a schema note after the template.** Immediately after the closing ``` fence of the "Phase file structure" block (before the `**Principles:**` list), add a subsection:

   ```markdown
   **`depends_on:` schema (phase-independence).** The optional `**Depends on:**` header lets a plan
   mark phases that are safe to run out of strict order:

   - **Value:** a list of prior phase ids (`phase_01`, `phase_02`, …) that must complete before this
     phase may start. Only ids of phases defined in this same plan are valid.
   - **Absent (the default):** a phase with no `**Depends on:**` line depends on **all prior phases** —
     i.e. it runs strictly after every lower-numbered phase, exactly as phases behave today. Emitting
     no `**Depends on:**` line is the correct, backward-compatible choice for any phase whose work
     consumes an earlier phase's output. When in doubt, omit it — the safe default is sequential.
   - **Present:** the phase is dispatchable as soon as **every** id it lists is complete, regardless of
     other phases' state. Two phases that (transitively) depend only on already-complete phases may run
     in parallel. Only add `**Depends on:**` to a phase whose work is genuinely independent of the
     phases it does NOT list — typically leaf work (tests, docs, lint, plumbing) that does not read a
     sibling phase's in-context output.
   - **Malformed is a defect, not a silent no-op.** A `**Depends on:**` that names a non-existent phase
     id, names the phase itself, or forms a dependency cycle is a **planner defect**. The execute skill
     is required to **surface** it (halt scheduling and report), not silently ignore it or fall back to
     sequential. Write `**Depends on:**` lists carefully: every id must name a real, lower-defined phase
     in this plan.
   ```

**Tests:**
There are no unit tests for skill/agent prose (this repo has no pytest; the suite is `trace-deps` + `check-version-sync` + `check-frontmatter`). Verification for this phase is:
- `check-frontmatter.py` must still pass — the edit is body-only and must not disturb `planner.md`'s YAML frontmatter (name/description/model/color/disallowedTools).
- Manual/reviewer read confirms AC1.1 (template documents the optional field + absent-⇒-sequential prose) and AC1.2 (malformed `depends_on:` is defined as a planner defect the execute skill must surface).
- Map to `test-requirements.md`: AC1.1 and AC1.2 are prose-verified in this file.

**Invariants to preserve:**
- Do NOT change `planner.md`'s frontmatter. `disallowedTools: Agent` stays; `model: opus` stays.
- Do NOT add any instruction that lets the planner or any worker dispatch subagents.

---

## Verification

Run: `python3 scripts/check-frontmatter.py`
Also run the full suite to be safe: `bash scripts/trace-deps.sh && python3 scripts/check-version-sync.py && python3 scripts/check-frontmatter.py`
Expected: all three checks pass (version-sync is unaffected here since no version changed yet; it should still report OK for the current on-disk versions).

Additionally confirm by reading `planner.md`: the phase template now shows the optional `**Depends on:**` line after `**AC Coverage:**`, and the schema note defines absent ⇒ sequential and malformed ⇒ surfaced planner defect.

## Commit

`docs: add depends_on phase-file schema to planner (#25 R9)`
