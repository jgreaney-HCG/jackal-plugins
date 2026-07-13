# Phase 2: Model Tier Table in execute skill + jackal-supervisor (R4)

**Goal:** Add the canonical model tier table to both the `execute` skill and the `jackal-supervisor` agent, and reconcile the documented discrepancies between the table, the worker-agent frontmatter, and CLAUDE.md.
**AC Coverage:** R4 AC "Tier table added to the execute + jackal-supervisor skills: planner=Opus, implementor=Sonnet, reviewer=Sonnet, reviewer-deep=Opus, contract-sentinel=Sonnet, lexicon-warden=Sonnet, doc-render/research=Sonnet."; R4 AC4.2 (guidance to spot-check Sonnet sentinel/warden verdicts against an Opus baseline).

---

## Context

The issue spec pins the tier table exactly: **planner=Opus, implementor=Sonnet, reviewer=Sonnet, reviewer-deep=Opus, contract-sentinel=Sonnet, lexicon-warden=Sonnet, doc-render/research=Sonnet.**

**Discrepancies surfaced this session — the implementor MUST reconcile these deliberately, not silently:**

1. **contract-sentinel and lexicon-warden frontmatter is `model: haiku`**, but the tier table says **Sonnet** for both. Verified on disk:
   - `plugins/jackal-director/agents/contract-sentinel.md` → `model: haiku`
   - `plugins/jackal-director/agents/lexicon-warden.md` → `model: haiku`
   The dispatch-site `model` param overrides frontmatter, so a director dispatch that passes `model: sonnet` wins at runtime. But the mismatch must be **intentional and documented**, not left as a silent contradiction. This issue's in-scope files do NOT include the director agent frontmatter or the director dispatch sites (those live in `jackal-director` and are out of scope per the issue's Scope section), so **do not edit the director agent files in this issue.** Instead, add an explicit footnote to the tier table (see below) recording that sentinel/warden currently declare `model: haiku` in frontmatter, that the table promotes them to Sonnet, and that reconciling the director-side dispatch/frontmatter is tracked separately (a follow-up in the `jackal-director` plugin). This makes the intent visible without touching out-of-scope files.

2. **delta-scribe and registry-drift-checker are also `model: haiku`** in frontmatter and are NOT named in the tier table. Leave them out of the table (the spec doesn't list them) but mention in the footnote that other director workers remain on haiku by design.

3. **`doc-render`/`research` are dispatched by name, not by those labels.** The `design` skill dispatches `ed3d-research-agents:codebase-investigator` (this is the "research" tier row) and `finish` dispatches `ed3d-extending-claude:project-claude-librarian` (the "doc-render" tier row). Map both to Sonnet in the table and annotate which concrete agent each label refers to, so the row is actionable.

4. **CLAUDE.md** currently contains no tier table and no per-agent model statement — its only model-related text is the "sole exception ... orchestrating tier keeps the `Agent` tool" line (verified: `grep -i 'opus\|sonnet\|haiku'` on CLAUDE.md returns only that line). So there is **no CLAUDE.md-vs-table conflict to resolve** — but the table's footnote should note that CLAUDE.md's worker/orchestrator split (supervisor = only Agent-holder) is consistent with the table (supervisor is the orchestrator; it is not a dispatched worker tier and so is not a row in the table).

Frontmatter cross-check (verified on disk, for the implementor's reference — table value vs frontmatter):

| Agent | Frontmatter `model:` | Tier table says | Match? |
|---|---|---|---|
| planner | opus | Opus | ✓ |
| implementor | sonnet | Sonnet | ✓ |
| reviewer | sonnet | Sonnet | ✓ |
| reviewer-deep | opus | Opus | ✓ |
| contract-sentinel | **haiku** | **Sonnet** | ✗ (footnote) |
| lexicon-warden | **haiku** | **Sonnet** | ✗ (footnote) |
| codebase-investigator (research) | (external plugin, not checked here) | Sonnet | dispatch-set |
| project-claude-librarian (doc-render) | (external plugin) | Sonnet | dispatch-set |

## Implementation

### Add the Model Tier Table to the execute skill

**File:**
- Modify: `plugins/jackal-plan-and-execute/skills/execute/SKILL.md`

**What to implement:**

Add a new top-level section titled `## Model Tier Table` (place it after the "Delegation Rules" section and before "Mode 1", so it is near the dispatch machinery it governs). The section contains:

```markdown
## Model Tier Table

Every Agent dispatch picks its model from this table. The dispatch-site
`<parameter name="model">` is authoritative — it overrides the target agent's
frontmatter `model:` for that invocation. A dispatch that omits `model` is a
defect (see "Subagent discipline" above).

| Dispatched agent | Tier | `model` param |
|---|---|---|
| `planner` | Opus | `opus` |
| `implementor` | Sonnet | `sonnet` |
| `reviewer` | Sonnet | `sonnet` |
| `reviewer-deep` | Opus | `opus` |
| `contract-sentinel` | Sonnet | `sonnet` |
| `lexicon-warden` | Sonnet | `sonnet` |
| research (`ed3d-research-agents:codebase-investigator`) | Sonnet | `sonnet` |
| doc-render (`ed3d-extending-claude:project-claude-librarian`) | Sonnet | `sonnet` |

The supervisor/orchestrator tier is not a row here — it is the dispatching
context, not a dispatched worker (CLAUDE.md: supervisor is the sole `Agent`
holder).

> **Frontmatter reconciliation (known, intentional):** `contract-sentinel` and
> `lexicon-warden` currently declare `model: haiku` in their `jackal-director`
> agent frontmatter; this table promotes both to Sonnet, and the dispatch-site
> `model` param wins at runtime. The director-side dispatch sites and frontmatter
> live in the `jackal-director` plugin (out of scope for this issue) — reconcile
> them there in a follow-up so frontmatter and table agree. Other director
> workers (`delta-scribe`, `registry-drift-checker`) intentionally remain on
> haiku and are not tiered up here.
```

### Add AC4.2 verdict-spot-check guidance

**File:**
- Modify: `plugins/jackal-plan-and-execute/skills/execute/SKILL.md` (immediately below the tier table)

**What to implement:**

Add a short subsection giving the reviewer/warden downgrade-safety guidance required by AC4.2:

```markdown
### Verifying a downgraded tier (Sonnet where Opus once ran)

Sentinel and warden run on Sonnet here where earlier cycles used Opus. To keep
the downgrade honest:
- **Spot-check a Sonnet sentinel/warden verdict against a prior Opus baseline**
  when one exists (e.g. GL-488's warden run flagged 12 glossary terms — a
  materially lighter Sonnet result on comparable input is a signal, not noise).
- **Log any case where a Sonnet `reviewer` verdict is later contradicted** (a
  bug it passed that a human or deep review then caught). Accumulated
  contradictions are the evidence to re-promote that tier to Opus. Record them
  where the project tracks review lessons (issue comment or the owning skill),
  not just in the transcript.
```

### Mirror the tier table into jackal-supervisor

**File:**
- Modify: `plugins/jackal-supervisor/agents/jackal-supervisor.md`

**What to implement:**

The supervisor already has a "Route to Execution" table and a "workers never spawn workers" rule. Add a `## Model Tiers` section (place it after the "Recording lessons" section and before "Step 0", or adjacent to "Route to Execution" — pick the location that reads cleanest) containing the **same table and the same reconciliation footnote** as the execute skill. Keep the two copies textually identical so they don't drift; a divergence between them is itself a defect.

Also add, right after the supervisor's existing "Your workers never spawn workers" callout (lines 16-19), a companion sentence:

> **Every dispatch you make specifies `model` explicitly** per the Model Tiers
> table below — a dispatch left on the harness default (`model=null`) silently
> abandons tier discipline and is a defect.

The supervisor's "Route to Execution" table dispatches `implementor` directly for Simple issues (line 289) — this is prose describing which skill/agent to route to, not a literal `<invoke name="Agent">` block, so it needs no `model` param itself; but add a parenthetical there pointing at the Model Tiers table so the reader knows the Simple-issue implementor dispatch is Sonnet.

## Verification

Run: `bash scripts/trace-deps.sh && python3 scripts/check-version-sync.py && python3 scripts/check-frontmatter.py`
Expected: all three pass.

Manual (operational): confirm the tier table appears in both files and the two tables are identical:
```
grep -n 'Model Tier\|Model Tiers' plugins/jackal-plan-and-execute/skills/execute/SKILL.md plugins/jackal-supervisor/agents/jackal-supervisor.md
```
Expected: a table heading in each file. Diff the two table bodies by eye — they must match.

## Commit

`feat(plan-and-execute): add model tier table to execute skill and supervisor`
