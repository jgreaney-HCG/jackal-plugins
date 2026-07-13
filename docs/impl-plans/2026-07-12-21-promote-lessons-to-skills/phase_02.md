# Phase 2: Merged-PR ranking gate (cross-check candidate OPEN issues before ranking)

**Goal:** Add a merged-PR cross-check that runs on every candidate OPEN issue *before* it is ranked/selected, producing a separate "stale-open — close these" list, so a delivered-but-still-open issue is never top-ranked again (the GL-347 failure).

**AC Coverage:**
- "Merged-PR gate migrated into the jackal-supervisor sweep procedure: for every candidate OPEN issue, run a merged-PR cross-check (e.g. `gh pr list --state merged --search '<#>'`) before ranking, and produce a separate stale-open-close-these list."
- "AC6.2 (MANUAL/OBSERVATIONAL — not CI): a fresh sweep on a repo with a known stale-open merged issue does not rank it, with no director-side correction." (behavior enabled here; verified manually — see test-requirements.md)
- Contributes to "AC6.1: the three lessons appear in the corresponding plugin skill/agent files."

---

## Context

**Where ranking actually happens — target differs from the issue-doc's literal assumption.**

The issue doc and design R6 say the gate goes into "the jackal-supervisor sweep procedure." But `plugins/jackal-supervisor/skills/jackal-sweep/SKILL.md` does **not** rank candidate OPEN issues — it reclaims worktrees/branches whose PRs have merged and fast-forwards main. It has no issue-backlog ranking step at all (grep for `rank|select|candidate` in that file returns nothing).

The GL-347 mis-ranking happened during a **backlog sweep** that produced an issue ranking. In this codebase, candidate-OPEN-issue ranking/selection lives in two places:

1. **`plugins/jackal-supervisor/agents/jackal-supervisor.md`** — "Reading the backlog" (surfaces the ready queue) and "Backlog Groom" (hygiene audit that surfaces stale/mis-labeled issues). This is the supervisor's backlog-sweep home.
2. **`plugins/jackal-plan-and-execute/skills/execute/SKILL.md`** — Mode 2, "Step 4: Select Work" (ranks ready issues by priority before dispatching).

So the gate belongs where ranking happens (supervisor agent + execute Step 4), and the `jackal-sweep` skill's report step gets a cross-reference + a place to surface the stale-open list when a sweep is run there. **This differs from the issue-doc's file assumption — the implementor should note the divergence in the PR body**, per the planner's finding.

Both `jackal-supervisor` (agent) and the `execute` skill (used by supervisor for backlog mode) are in scope because the issue's Module is "supervisor + plan-and-execute" and both are cross-agent-shared skill/agent text (the only substrate that reaches spawned agents, per Phase 1's finding).

## Implementation

### A. Merged-PR ranking gate in the jackal-supervisor agent

**Files:**
- Modify: `plugins/jackal-supervisor/agents/jackal-supervisor.md`

**What to implement:**

Add a **"Merged-PR gate"** subsection to the **"Reading the backlog"** section (immediately after the ready/in-progress/blocked grouping, before any prioritization). It must instruct: for every candidate OPEN issue about to be ranked or selected, cross-check whether a merged PR already delivered it, and route stale-open issues to a separate close-these list instead of ranking them.

Add text equivalent to:

```markdown
### Merged-PR gate (run before ranking — never rank a delivered issue)

Before ranking or selecting any candidate OPEN issue, cross-check it against
merged PRs. Squash-merges that reference an issue with `Refs`/`#NN` (not
`Closes #NN`) leave the delivered issue OPEN with a stale `status/in-progress`
label — ranking it wastes a whole assignment cycle (this is the GL-347 failure).

For each candidate OPEN issue `#N`:

​```bash
gh pr list --repo "$GH_REPO" --state merged --search "$N" \
  --json number,title,url,mergedAt
# Also catch body/branch references the search may miss:
gh pr list --repo "$GH_REPO" --state merged \
  --search "in:body $N" --json number,url
​```

- **A merged PR delivers `#N`** (its title/body/branch names the issue, or the
  work is clearly shipped) → **do not rank it.** Move it to a separate
  **stale-open — close these** list.
- **No merged PR** → the issue is genuinely open; proceed to ranking.

Emit the stale-open list as its own block, distinct from the ranked ready queue:

​```
Stale-open (delivered by a merged PR — close, don't rank):
  #347  (delivered by merged PR #351)  → gh issue close 347 --reason completed
Ready (ranked):
  #360 (priority/high), #362 (priority/medium), ...
​```

Closing is a hygiene action — surface it; apply with the user's confirmation
(same posture as Backlog Groom). Never rank an issue this gate flagged as
delivered.
```

Also add a matching item to the **"Backlog Groom (hygiene audit)"** numbered list so grooms catch stale-open issues too:

```markdown
7. **Stale-open (delivered, still open):** OPEN issue whose work shipped in a
   merged PR (see the Merged-PR gate under "Reading the backlog") → list under
   **stale-open — close these**; never rank. Close with confirmation.
```

### B. Merged-PR gate in the execute skill's Step 4

**Files:**
- Modify: `plugins/jackal-plan-and-execute/skills/execute/SKILL.md`

**What to implement:**

In **"Step 4: Select Work"** (Mode 2), add a gate that runs before the priority-ordering paragraph. It must instruct the orchestrator to drop any candidate whose work already shipped in a merged PR, rather than selecting it:

```markdown
**Merged-PR gate (before ranking).** For every candidate OPEN issue, cross-check
merged PRs before it enters priority ordering — a squash-merge that referenced
the issue with `Refs`/`#NN` (not `Closes`) leaves it OPEN with a stale
`status/in-progress` label. Ranking a delivered issue burns a full assignment
cycle (the GL-347 failure).

​```bash
gh pr list --repo "$GH_REPO" --state merged --search "$N" \
  --json number,url,mergedAt   # per candidate issue #N
​```

If a merged PR delivered the candidate, drop it from selection and surface it in
a **stale-open — close these** list (do not auto-close during the loop —
report it; closing is a supervisor hygiene action). Only issues with no
delivering merged PR proceed to priority ordering below.
```

### C. Cross-reference from the jackal-sweep skill

**Files:**
- Modify: `plugins/jackal-supervisor/skills/jackal-sweep/SKILL.md`

**What to implement:**

The sweep skill reclaims worktrees; it is NOT the ranking site. But a person running `/jackal-supervisor:jackal-sweep` is doing backlog hygiene, so surface the stale-open list here and point to the ranking gate. In **"Step 5: Report"**, add a `Stale-open` line to the report block and a note pointing to the gate:

```markdown
Stale-open (delivered by a merged PR, still OPEN — close, don't rank): #NN (PR #MM)
```

And add a short note after the report block:

```markdown
> **Stale-open issues.** This sweep reclaims *worktrees/branches*. Ranking a
> candidate OPEN issue that a merged PR already delivered is prevented by the
> **Merged-PR gate** in the jackal-supervisor agent ("Reading the backlog") and
> the `execute` skill (Step 4). If you spot a delivered-but-open issue here,
> list it under Stale-open and close it with `gh issue close <#> --reason completed`.
```

**Tests:**
No unit tests (repo has none). Verification is: (a) `TEST_CMD` still passes (frontmatter unchanged, no version drift *yet* — the version bump is Phase 5), and (b) the AC6.2 manual/observational check documented in test-requirements.md — a fresh backlog read on a repo with a known stale-open merged issue lists it under "stale-open" and does not rank it. This is behavioral text in prompts; it cannot be unit-tested and is verified by observation, recorded in the PR.

---

## Verification

Run: `bash scripts/trace-deps.sh && python3 scripts/check-version-sync.py && python3 scripts/check-frontmatter.py`
Expected: all pass. (No frontmatter changed; versions are bumped in Phase 5, so sync still holds at the pre-bump baseline.)

Manual (record in PR, per AC6.2): reason through a candidate list containing a known delivered-but-open issue and confirm the new gate text routes it to "stale-open" and out of ranking.

## Commit

`feat(supervisor): merged-PR gate — cross-check candidate open issues before ranking`
