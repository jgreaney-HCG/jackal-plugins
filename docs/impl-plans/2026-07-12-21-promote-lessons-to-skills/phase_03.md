# Phase 3: ruff-format line in the implementor prompt

**Goal:** Add a project-verification note to the implementor prompt so that when a repo uses `ruff format`, the implementor runs it before committing — closing the gap where lessons about formatting live only in director memory.

**AC Coverage:**
- Contributes to "AC6.1: the three lessons appear in the corresponding plugin skill/agent files, versioned." (This is the third promoted lesson from R6/#17: the operational habits that must reach spawned agents.)

---

## Context

The task brief lists five deliverables; item 4 is "ruff-format line into the implementor prompt." Per Phase 1's finding, spawned implementors do not receive `MEMORY.md`, so any expectation that the implementor auto-formats Python must live in the implementor agent definition text — the only substrate that reaches the spawned agent.

The implementor's **Step 4: Verify** currently says "Whatever linter is configured" as a comment placeholder. This phase makes the formatting expectation explicit and conditional (only when the project actually uses ruff), without prescribing ruff for repos that don't use it. This is a light, additive prompt change — it must not weaken any existing rule.

`plugins/jackal-plan-and-execute/agents/implementor.md` is the file. Its **Step 4: Verify** block is:

```
### 4. Verify

Run and report results:
​```bash
# Whatever test command the project uses
# Whatever build/compile command exists
# Whatever linter is configured
​```

If anything fails, fix it before proceeding. Iterate until green.
```

## Implementation

### ruff-format expectation in the implementor's Verify step

**Files:**
- Modify: `plugins/jackal-plan-and-execute/agents/implementor.md`

**What to implement:**

Extend **Step 4: Verify** with an explicit formatter line, conditioned on the project actually using ruff (detect via `pyproject.toml`/`ruff.toml`/`.ruff.toml`, or a documented ruff command in the project's CLAUDE.md / test command). Add text equivalent to:

```markdown
**Formatting.** If the project uses Ruff (a `pyproject.toml`/`ruff.toml`/`.ruff.toml`
is present, or its CLAUDE.md names ruff), run `ruff format .` and `ruff check --fix .`
before committing, and re-run the test command afterward. Formatting is part of
"green" — never commit code that the project's formatter would rewrite. For
non-Python projects, run the project's configured formatter/linter (Prettier,
gofmt, etc.) under the same rule. If no formatter is configured, skip this — do
not introduce one.
```

Keep it additive and conditional. Do not remove the existing "Whatever linter is configured" comment or the "Iterate until green" line — this text sits alongside them, making the formatting expectation concrete for Python/ruff projects while staying no-op for repos that don't use ruff (this plugins repo itself has no ruff config — the change is correct here precisely because it is conditional).

**Invariant check:** this phase touches only the body of `implementor.md`. Do NOT touch its frontmatter — `disallowedTools: Agent` and `model: sonnet` stay exactly as they are. The "never dispatch or invoke other subagents" rule stays.

**Tests:**
No unit tests (repo has none). `check-frontmatter.py` validates the frontmatter is intact — since we don't touch frontmatter, it passes. Verification is that the Verify step now contains the conditional ruff-format instruction and the no-subagents rule + frontmatter are unchanged.

---

## Verification

Run: `bash scripts/trace-deps.sh && python3 scripts/check-version-sync.py && python3 scripts/check-frontmatter.py`
Expected: all pass. `check-frontmatter.py` confirms `implementor.md` frontmatter still valid (name/description present; `disallowedTools: Agent` untouched).

Confirm: `implementor.md` Step 4 now names `ruff format` conditionally; frontmatter unchanged.

## Commit

`feat(plan-and-execute): implementor runs ruff format before commit when project uses ruff`
