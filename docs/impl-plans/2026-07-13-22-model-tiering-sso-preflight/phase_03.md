# Phase 3: Credential pre-flight snippet + commit-early clause (R5)

**Goal:** Add a credential-lifetime pre-flight snippet (required before any >10-min dispatch) to the execute skill and jackal-supervisor, and add a commit-early clause to the implementor prompt.
**AC Coverage:** R5 AC "Credential pre-flight snippet ... required before any dispatch expected to run >10 min; if remaining lifetime < task duration + margin, tell the human to re-auth BEFORE dispatching."; R5 AC "Commit-early clause added to the implementor agent prompt."; supports AC5.1 and AC5.2 (observational).

---

## Context

Long dispatches can outlive the operator's AWS SSO session; when creds expire mid-dispatch, uncommitted work in the worktree is at risk. R5 adds two complementary defenses: a **pre-dispatch credential check** (orchestrator side) and a **commit-early clause** (implementor side, so credential expiry can't destroy in-flight work).

**Critical framing (must be explicit in the text):** this pre-flight is **generic operational guidance for the downstream projects the loop operates on** — this `jackal-plugins` repo has no AWS creds of its own and is not gated by it. The snippet must say so plainly so no one reads it as a gate on this repo's own CI/dispatches. (Issue Technical Notes: "this plugins repo has no AWS creds of its own — the snippet is for the downstream projects the loop operates on.")

The commit-early clause **complements** the honest-stopping-point clause already present in `implementor.md` (added in #18, verified on disk at implementor.md lines 41-47). Do not remove or duplicate the honest-stopping-point clause — add commit-early as a distinct, adjacent instruction.

## Implementation

### Credential pre-flight snippet — execute skill

**File:**
- Modify: `plugins/jackal-plan-and-execute/skills/execute/SKILL.md`

**What to implement:**

Add a `## Credential pre-flight (before long dispatches)` section. Place it near "Waiting for async work" (which already governs long/async dispatches) since both concern dispatches expected to run a while. Content:

```markdown
## Credential pre-flight (before long dispatches)

**Applies to the downstream project the loop is operating on, not this repo.**
If the project the loop drives deploys to or reads from AWS with SSO/STS
credentials, a dispatch expected to run **>10 min** can outlive the operator's
session and lose uncommitted work. This plugins repo itself has no AWS creds and
is never gated by this check — the snippet is guidance to emit into projects that
do use AWS.

Before any dispatch you expect to run >10 min, in a project that uses AWS creds:

```bash
# Who am I / are creds live at all?
aws sts get-caller-identity || { echo "No valid AWS credentials — tell the human to re-auth (aws sso login) BEFORE dispatching."; }

# Remaining lifetime, where obtainable. SSO sessions expose an expiry in the
# cached token; STS assumed-role creds expose Expiration. Not every credential
# type reports a machine-readable expiry — if none is available, fall back to
# asking the operator when they last authenticated.
aws configure export-credentials --format process 2>/dev/null | \
  python3 -c 'import sys,json; d=json.load(sys.stdin); print("Expiration:", d.get("Expiration","<not reported>"))' 2>/dev/null \
  || echo "Expiration not machine-readable for this credential type — confirm remaining session time with the operator."
```

**Decision rule:** if remaining lifetime `< (expected task duration + margin)`
(use a margin of at least the dispatch's `EXPECT` window), **do not dispatch** —
tell the human to re-authenticate (`aws sso login` or the project's documented
re-auth) BEFORE the dispatch starts. A dispatch launched into a soon-to-expire
session is the failure this check exists to prevent. Record the check in the
transcript (AC5.1: every >=10-min dispatch is preceded by a credential check).
```

### Credential pre-flight snippet — jackal-supervisor

**File:**
- Modify: `plugins/jackal-supervisor/agents/jackal-supervisor.md`

**What to implement:**

Add the **same** `## Credential pre-flight (before long dispatches)` section (identical text, including the "not this repo / downstream project only" framing and the same bash snippet and decision rule). Place it near the supervisor's dispatch machinery (after "Route to Execution" / "Continuous Execution"). Keep it textually identical to the execute-skill copy to avoid drift.

### Commit-early clause — implementor.md

**File:**
- Modify: `plugins/jackal-plan-and-execute/agents/implementor.md`

**What to implement:**

Add a commit-early clause. The natural homes are the "### 5. Commit" step (lines 101-111) and/or the "Honest Stopping Point" callout (lines 41-47). Add it as a distinct instruction — recommended placement is a new paragraph at the end of the "### 5. Commit" section, and a one-line pointer in the Honest Stopping Point callout tying them together. Text:

Add to "### 5. Commit":

```markdown
**Commit early, commit at every green.** Don't save all your commits for the end
of a phase. Every time the work reaches a green intermediate state — a file
compiles, a test starts passing, a sub-step is done — commit it. WIP commits are
fine and expected; a squash-merge collapses them into one clean commit on merge,
so intermediate WIP commits cost nothing and never reach main's history. This is
insurance: if your session or the operator's credentials expire mid-phase, the
committed checkpoints survive and the work is resumable from disk. An implementor
phase that touches several files should show intermediate commits, not one
end-of-phase commit.
```

Add to the "Honest Stopping Point" callout (append one sentence):

```markdown
Commit-early (see step 5) is the other half of this: frequent green-state commits
mean your honest stopping point is always a real, resumable commit on disk, not an
uncommitted working tree.
```

## Verification

Run: `bash scripts/trace-deps.sh && python3 scripts/check-version-sync.py && python3 scripts/check-frontmatter.py`
Expected: all three pass. `check-frontmatter.py` must still pass — the implementor frontmatter (`disallowedTools: Agent`, `model: sonnet`) is unchanged; only body prose is added.

Manual (operational): confirm the pre-flight framing is unambiguous:
```
grep -n 'downstream\|no AWS creds\|not this repo' plugins/jackal-plan-and-execute/skills/execute/SKILL.md plugins/jackal-supervisor/agents/jackal-supervisor.md
grep -n 'Commit early' plugins/jackal-plan-and-execute/agents/implementor.md
```
Expected: framing lines present in both dispatch-side files; commit-early clause present in implementor.md.

## Commit

`feat(plan-and-execute): add credential pre-flight and implementor commit-early clause`
