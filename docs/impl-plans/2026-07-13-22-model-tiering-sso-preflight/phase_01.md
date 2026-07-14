# Phase 1: Explicit model on every Agent dispatch + defect declaration (R4)

**Goal:** Add an explicit `<parameter name="model">` to every one of the five `<invoke name="Agent">` dispatch blocks across the plan-and-execute skills, and declare a model-unspecified dispatch a defect in skill text.
**AC Coverage:** R4 AC "Every `<invoke name="Agent">` dispatch block in the execute, plan, review, design, and finish skills carries an explicit `<parameter name="model">`. A model-unspecified dispatch is declared a defect in the skill text." (partial — the tier table itself lands in Phase 2); supports AC4.1 (observational).

---

## Context

The audited director session showed 24 of 28 Agent dispatches ran with `model=null` (harness default), meaning tier discipline was never actually enforced at dispatch time. The dispatch-site `model` param is authoritative — it overrides the agent's frontmatter `model:` for that invocation.

Enumeration verified this session — there are **exactly five** `<invoke name="Agent">` blocks in the in-scope skills, one per skill, **none currently carrying a `model` param**:

| Skill | File | Line (current) | subagent_type dispatched | Tier per table (Phase 2) | Model param to add |
|---|---|---|---|---|---|
| execute | `plugins/jackal-plan-and-execute/skills/execute/SKILL.md` | 113 | `jackal-plan-and-execute:implementor` | implementor = Sonnet | `sonnet` |
| plan | `plugins/jackal-plan-and-execute/skills/plan/SKILL.md` | 127 | `jackal-plan-and-execute:planner` | planner = Opus | `opus` |
| review | `plugins/jackal-plan-and-execute/skills/review/SKILL.md` | 22 | `jackal-plan-and-execute:reviewer` | reviewer = Sonnet | `sonnet` |
| design | `plugins/jackal-plan-and-execute/skills/design/SKILL.md` | 77 | `ed3d-research-agents:codebase-investigator` | research = Sonnet | `sonnet` |
| finish | `plugins/jackal-plan-and-execute/skills/finish/SKILL.md` | 113 | `ed3d-extending-claude:project-claude-librarian` | doc-render = Sonnet | `sonnet` |

The execute skill also has a `SendMessage` continuation block (execute line 144) that resumes the named implementor for phases 2..N. `SendMessage` resumes an already-dispatched agent and does **not** take a `model` param — the model is fixed at the cold dispatch. Do **not** add a model param to the `SendMessage` block; only to the five `Agent` blocks. (The named-continuation cold dispatch is the execute-line-113 block, which does get `sonnet`.)

Note the `model` value convention in this repo: agent frontmatter uses the bare tier alias (`model: sonnet`, `model: opus`, `model: haiku`). Use the **same bare-alias form** in the dispatch `model` param for consistency — `sonnet` / `opus`, not a full `us.anthropic.*` model id.

## Implementation

### Add `<parameter name="model">` to each of the five dispatch blocks

**Files:**
- Modify: `plugins/jackal-plan-and-execute/skills/execute/SKILL.md`
- Modify: `plugins/jackal-plan-and-execute/skills/plan/SKILL.md`
- Modify: `plugins/jackal-plan-and-execute/skills/review/SKILL.md`
- Modify: `plugins/jackal-plan-and-execute/skills/design/SKILL.md`
- Modify: `plugins/jackal-plan-and-execute/skills/finish/SKILL.md`

**What to implement:**

In each of the five `<invoke name="Agent">` blocks, add a `<parameter name="model">` line immediately after the `<parameter name="subagent_type">` line, with the value from the table above. Keep the existing `subagent_type`, `name` (execute only), `description`, and `prompt` params in place and in order.

Example — execute skill, the phase-1 cold dispatch (currently lines 113-118):

```xml
<invoke name="Agent">
<parameter name="subagent_type">jackal-plan-and-execute:implementor</parameter>
<parameter name="model">sonnet</parameter>
<parameter name="name">implementor-<ISSUE_NUMBER></parameter>
<parameter name="description">Implementing phase 1 of #<ISSUE_NUMBER></parameter>
<parameter name="prompt">
...
```

Apply the same insertion (subagent_type line, then a new `model` line) to plan (`opus`), review (`sonnet`), design (`sonnet`), and finish (`sonnet`).

**Review skill special case:** the review skill dispatches `reviewer` (Sonnet) by default but escalates to `reviewer-deep` (Opus) for Complex/security-sensitive diffs — there is a note at line 43: "(Substitute `jackal-plan-and-execute:reviewer-deep` when the tier calls for it.)". After adding `<parameter name="model">sonnet</parameter>` to the default block, extend that substitution note so the model param is swapped **together with** the subagent_type. Reword line 43 to something like:

> (When the tier calls for the deep reviewer, substitute **both** `subagent_type` → `jackal-plan-and-execute:reviewer-deep` **and** `model` → `opus`. The two must always move together — a `reviewer-deep` dispatch left on `model: sonnet` is a model-tier defect.)

### Declare a model-unspecified dispatch a defect (skill text)

**File:**
- Modify: `plugins/jackal-plan-and-execute/skills/execute/SKILL.md` (the "Subagent discipline" callout at lines 14-16)

**What to implement:**

The execute skill already has a "Subagent discipline" callout (lines 14-16) declaring the no-nesting prompt line mandatory. Extend that callout with a parallel sentence declaring the model param mandatory. Add after the existing lines:

> **Model discipline:** every `<invoke name="Agent">` dispatch in this skill must
> carry an explicit `<parameter name="model">` chosen from the tier table below
> (see "Model Tier Table"). A dispatch that omits `model` — leaving the harness
> default / `model=null` — is a **defect**, not a stylistic lapse: it silently
> abandons tier discipline (24 of 28 dispatches in the audited session ran
> `model=null`). `SendMessage` continuations inherit the model of their cold
> dispatch and do not take a `model` param.

(The "Model Tier Table" it references is added in Phase 2, in the same skill — Phase 2 depends on this phase but both land before finish, so the forward reference is resolved within this issue's delivery.)

Add a shorter equivalent one-liner to the other four skills near their dispatch block, so the defect rule is discoverable from each skill, e.g. for plan/review/design/finish:

> Every Agent dispatch above carries an explicit `<parameter name="model">`; a
> model-unspecified dispatch is a defect (see the Model Tier Table in the
> `execute` skill and the `jackal-supervisor` agent).

Place this line directly below each skill's dispatch block.

## Verification

Run: `bash scripts/trace-deps.sh && python3 scripts/check-version-sync.py && python3 scripts/check-frontmatter.py`
Expected: all three pass (no version bump yet in this phase — that is Phase 4; check-version-sync stays green because plugin.json and marketplace.json are both still at their current values).

Manual grep check (operational, not CI):
```
grep -rn 'name="Agent"' plugins/jackal-plan-and-execute/skills   # 5 blocks
grep -rn 'name="model"' plugins/jackal-plan-and-execute/skills    # must be 5
```
Expected: exactly 5 `name="Agent"` blocks and exactly 5 `name="model"` params (one per block). If the counts differ, a dispatch was missed.

## Commit

`feat(plan-and-execute): add explicit model param to all 5 Agent dispatch blocks`
