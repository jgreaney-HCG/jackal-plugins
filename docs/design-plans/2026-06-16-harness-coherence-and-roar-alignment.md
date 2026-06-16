# Harness Coherence & ROAR Alignment — Design Plan

**Date:** 2026-06-16
**Status:** Draft — awaiting review
**Scope:** Two repos — `jackal-plugins` (the harness) and `~/code/monorepo` (ROAR, the consuming project)

---

## Summary

A critical-eye audit of the `jackal-plugins` suite, a comparison against its `ed3d-plugins`
predecessor, a survey of current Claude Code harness best practice, and a bounce against the
ROAR repo's own standards surfaced three classes of problem:

1. **Broken/dangling references** — the harness points at skills and agents that no longer
   exist in the marketplace (fallout from the ed3d → jackal rework).
2. **Undeclared external dependencies** — jackal skills dispatch to 4 agents shipped only by
   ed3d plugins the jackal marketplace doesn't include or declare.
3. **ROAR-side friction** — the harness's autonomous defaults (self-merge to `main`) and config
   contract (`gh_repo`) collide with ROAR's protected-main, PR-only invariant and its actual
   Jackal Config; ROAR's mandatory CLAUDE.md freshness re-verification has no working harness step.

This plan fixes all three, plus the staleness/branding cleanup, across coordinated changes in
both repos.

### Decisions locked at design time

- **External agents → declared as required deps**, not vendored. Matches the "minimal
  customization for painless upstream sync" strategy. ROAR already standardizes on
  `ed3d-extending-claude`, so declaring it is consistent with reality.
- **Plan covers both repos.** ROAR-side changes are real phases, not an appendix.
- **The 2 dropped skills are *ported into* `jackal-plan-and-execute`**, NOT declared as deps.
  Rationale (discovered during design): unlike the 4 agents — which live in standalone plugins —
  `test-driven-development` and `verification-before-completion` live *only inside
  `ed3d-plan-and-execute`*, the exact plugin `jackal-plan-and-execute` forked and replaced.
  Declaring a dependency on it would reintroduce colliding `design`/`plan`/`execute` skills and
  commands. Porting the two skills under their original names makes every existing dangling
  reference (`jackal-plan-and-execute:test-driven-development`, `:verification-before-completion`)
  resolve with no ref rewriting.

---

## Definition of Done

- No skill or agent in any jackal plugin references a skill/agent that the installed plugin set
  cannot resolve (either it ships it, or the marketplace/README declares it as a required dep).
- A clean install of the jackal marketplace + declared deps runs the full
  design → plan → execute → finish lifecycle end-to-end without a missing-agent failure.
- The top-level `README.md` describes the jackal marketplace as it actually is (4 plugins,
  current command/skill names, correct marketplace URL).
- Running `/execute` backlog mode against ROAR respects ROAR's protected-main / PR-only rule by
  default, and the GitHub backlog path has the config keys it requires.
- ROAR's mandatory CLAUDE.md freshness re-verification at branch closeout is actually performed by
  a working `finish`-path step.
- All ed3d-era branding/naming staleness in the jackal plugins is corrected.
- A committed test document + re-runnable trace script proves zero dangling references and a
  fully-resolving lifecycle, and confirms the harness fails *loudly* when a declared dep is absent.
- The harness generates and queries labels in a configurable scheme (default slash-style), verified
  against the consuming repo's real label set, so label edits don't silently miss.

### Out of scope

- Restructuring the orchestrator/worker model — it is sound and matches best practice.
- Re-tiering models (adding Haiku exploration agents) — noted as a future consideration, not done
  here.
- Changes to ROAR application code, CI workflow (E1/#19), or any module.
- Upstream-sync mechanics beyond what these fixes touch.

---

## Findings → Fix Traceability

| # | Finding | Severity | Repo | Phase |
|---|---------|----------|------|-------|
| F1 | `jackal-supervisor` *agent* (the orchestrating brain) isn't shipped by the plugin — lives only in `~/.claude/agents/` | Critical | jackal | P1 |
| F2 | Top-level `README.md` is the stale ed3d README (wrong title, 9-plugin layout, dead command names, ed3d marketplace URL) | Critical | jackal | P5 |
| F3 | `debug` skill hard-requires `test-driven-development` + `verification-before-completion` (dropped; dangling) | Critical | jackal | P2 |
| F4 | 4 external agents dispatched but not shipped/declared (`codebase-investigator`, `combined-researcher`, `project-claude-librarian`, `playwright-explorer`) | High | jackal | P3 |
| F5 | Autonomous `finish`/`execute` self-merge to `main` violates ROAR protected-main / PR-only | High | both | P4 (jackal default) + P6 (ROAR guidance) |
| F6 | ROAR Jackal Config lacks `backend:` + `gh_repo:` keys the GitHub path requires | High | ROAR | P6 |
| F7 | `jackal-house-style` plugin.json still branded "Ed" / ed3dai URLs | Medium | jackal | P5 |
| F8 | `jackal-design-plan` Step 6 hand-off prints legacy `feature/[module]/...` branch format | Medium | jackal | P5 |
| F9 | Stale ed3d prose: `jackal-pause-session:69` "ed3d skills create tasks"; `.ed3d/*-guidance.md` lookups in design/finish/review | Medium | jackal | P5 |
| F10 | `implementor` commit examples use bare `feat:`; ROAR uses module scopes `feat(institutions):` | Medium | both | P4 + P6 |
| F11 | `finish` `gh pr create` ignores ROAR's PR template (What changed / Closes / Risk / Docs / Gates) | Medium | jackal | P4 |
| F12 | CLAUDE.md freshness re-verification at closeout depends on `project-claude-librarian` "if available" — silently no-ops on clean install | High | jackal | P3 + P4 |
| F13 | `test-requirements.md` is written by planner but has no consumer (dropped `test-analyst`) | Low | jackal | P2 (reviewer cross-checks AC↔test) |
| F14 | `debug` skill frontmatter `name: systematic-debugging` ≠ dir `debug` (cosmetic but worth aligning) | Low | jackal | P2 (rename → `debug`) |
| F15 | Harness hard-codes **colon-style** labels (`status:ready`) in 5 skills; ROAR (the live consumer) uses **slash-style** (`status/ready`). Label edits/queries miss against ROAR. | High | jackal | P8 |
| F16 | `.jackal/` guidance is read from `$REPO_ROOT` only — no find-up. In a monorepo, a module-level `.jackal/` would silently never be read, so per-module harness-behavior overrides are impossible. | Medium | jackal | P8 |

---

## Architecture / Approach

The work splits cleanly into **dependency resolution** (make references resolve, either by
shipping or declaring) and **alignment** (make defaults and config respect the consuming repo's
invariants). Phases are ordered so the install-breaking items land first.

### Dependency model after this plan

```
jackal-plan-and-execute  ── ships ──▶ planner, implementor, reviewer agents
                         ── ships ──▶ design, plan, execute, review, finish, debug,
                                       test-driven-development, verification-before-completion skills
                         ── requires ─▶ ed3d-research-agents   (codebase-investigator, combined-researcher)
                                        ed3d-extending-claude  (project-claude-librarian)

jackal-supervisor        ── ships ──▶ jackal-supervisor agent  (NEW: moved into plugin)
                         ── ships ──▶ 5 wrapper skills
                         ── requires ─▶ ed3d-playwright         (playwright-explorer, via jackal-ui-verify)

jackal-house-style       ── ships ──▶ 11 skills  (self-contained; re-branded)
```

"requires" = declared in README prerequisites + a `dependencies`/`requires` note in
marketplace.json plugin entries (informational — Claude Code has no hard dep-resolution, so the
declaration is documentation + a pre-flight check, not enforcement).

---

## Implementation Phases

> Max 8 phases. Each is independently shippable (no "fixed in a later phase").

### Phase 1 — Ship the `jackal-supervisor` agent inside the plugin (F1)

**Goal:** The supervisor brain ships with the marketplace, not just on Jack's machine.

- Create `plugins/jackal-supervisor/agents/jackal-supervisor.md` from the installed
  `~/.claude/agents/jackal-supervisor.md` (262 lines), adjusting any references to use the
  `jackal-*` plugin-qualified skill names where it hands off.
- Verify it dispatches to skills/agents that exist (or are declared in P3).
- Bump `jackal-supervisor` version; update marketplace.json + CHANGELOG (per repo CLAUDE.md rule).

**Done when:** the agent file is in the plugin tree and a fresh install exposes the supervisor
agent without relying on `~/.claude/agents/`.

### Phase 2 — Port the two dropped skills + fix `debug` (F3, F13, F14)

**Goal:** `debug`'s required sub-skills resolve; no dangling refs in the plan-and-execute plugin.

- Port `test-driven-development/SKILL.md` and `verification-before-completion/SKILL.md` from
  `ed3d-upstream/main:plugins/ed3d-plan-and-execute/skills/...` into
  `plugins/jackal-plan-and-execute/skills/` under the **same names** (so existing
  `jackal-plan-and-execute:test-driven-development` refs resolve unchanged). Light-edit any ed3d
  branding inside.
- In `debug/SKILL.md`: confirm the two REQUIRED SUB-SKILL refs (lines ~176, ~278, ~282) now
  resolve; fix `coding-effectively` ref to point at `jackal-house-style:coding-effectively` if it
  doesn't already; align frontmatter `name: systematic-debugging` with the `debug` dir (rename
  one to match — recommend `name: debug` to match invocation, or document the divergence).
- Note F13 inline: add a short "test-requirements.md consumer" note to the planner or finish skill
  (either wire a lightweight AC-coverage check into the reviewer prompt, or explicitly state the
  file is a human reference artifact). **Decision needed at review** — see Open Questions.

**Done when:** grep for cross-refs in `jackal-plan-and-execute` shows every referenced skill
resolving to a shipped or house-style skill.

### Phase 3 — Declare external agent dependencies (F4, F12)

**Goal:** The 4 external agents are documented as required, and the freshness step is honest about
its dependency.

- README "Plugins" + a new "Required dependencies" section: list `ed3d-research-agents`,
  `ed3d-extending-claude`, `ed3d-playwright` as prerequisites, with install commands and which
  jackal flows need each.
- marketplace.json: add an informational `requires` note to the relevant plugin entries (or a
  top-level note) naming the ed3d plugins. (Schema permitting; otherwise a README-only declaration
  plus a comment.)
- `finish/SKILL.md` step 5: keep the `project-claude-librarian` dispatch but change the framing
  from silent "if available, else skip" to: dispatch it; if the plugin is genuinely absent, **emit
  a visible warning** that CLAUDE.md freshness re-verification was skipped (so ROAR's mandatory
  closeout rule failing is loud, not silent). This addresses F12.

**Done when:** README and marketplace name the 3 required ed3d plugins, and the finish skill no
longer silently swallows a missing librarian.

### Phase 4 — Make harness defaults respect protected-main + project conventions (F5, F10, F11)

**Goal:** Autonomous defaults are safe against a protected `main`, and generated commits/PRs match
the consuming repo's conventions.

- `finish/SKILL.md` + `jackal-finish-branch`: when the repo signals a protected main (detectable
  via `gh repo view --json` branch protection, or a `protected_main: true` Jackal Config key, or
  the presence of `.jackal/harness-guidance.md` merge-strategy), the **autonomous default becomes
  "push + open PR" (Option 2), not local merge (Option 1)**. Local-merge remains the default only
  when main is unprotected. Document the precedence: harness-guidance > config key > detection >
  built-in default.
- `execute/SKILL.md` Backlog mode "Merge result" step: same gating — open PR instead of self-merge
  when main is protected; the loop then continues to the next issue rather than blocking on human
  merge (records the open PR and moves on).
- `implementor.md`: add module-scoped Conventional Commit guidance — if the project's CLAUDE.md
  documents commit scopes (e.g. `feat(institutions):`), use them.
- `finish` PR creation: detect and honor a repo PR template
  (`.github/PULL_REQUEST_TEMPLATE.md`) — populate its sections (What changed / Closes #N / How to
  verify / Risk / Docs updated / Gates) rather than a freeform body. Fall back to the current body
  if no template exists.

**Done when:** against a repo with protected main, autonomous finish opens a PR (never attempts a
local merge to main), and generated PRs fill the repo template.

### Phase 5 — Staleness & branding cleanup (F2, F7, F8, F9)

**Goal:** No ed3d-era artifacts misrepresent the jackal suite.

- **Top-level `README.md`** (F2): rewrite for jackal — title, the actual 4-plugin table, current
  command/skill names (`/jackal-design-plan` → `/jackal-impl-plan` → `/execute` → `/finish`),
  correct marketplace URL (`jgreaney-HCG/jackal-plugins`), keep the obra/superpowers + Trail of
  Bits attribution. Add the "Required dependencies" section from P3.
- **`jackal-house-style/.claude-plugin/plugin.json`** (F7): author → Jack Greaney /
  jgreaney@hcg.com; description → jackal-framed; fix/remove the `homepage`/`repository` ed3dai URLs.
- **`jackal-design-plan` Step 6** (F8): hand-off template prints `<type>/<issue#>-slug` to match
  the convention the same skill's Step 2 actually creates.
- **Stale ed3d prose** (F9): `jackal-pause-session:69` reword "ed3d design/impl skills create
  tasks" → "the jackal design/impl skills"; in `design`/`finish`/`review`, drop or de-emphasize
  the `.ed3d/*-guidance.md` lookups (keep `.jackal/` as the canonical path; mention `.ed3d/` only
  as a legacy fallback if desired).
- Version bumps + CHANGELOG entries for every plugin touched (repo CLAUDE.md rule), and
  marketplace.json version sync.

**Done when:** README, plugin.json, and skill prose contain no inaccurate ed3d references; all
touched plugins have synced versions + changelog entries.

### Phase 6 — ROAR-side alignment (F5, F6, F10)

**Goal:** ROAR is configured so the harness's GitHub path works and its protected-main rule is
honored by default. (Changes in `~/code/monorepo`, on a ROAR feature branch, PR'd per ROAR rules.)

- **Jackal Config** (`~/code/monorepo/CLAUDE.md`, F6): add `backend: github` and
  `gh_repo: HCG-EDR-C-ROAR/roar`. Optionally add `protected_main: true` and `pr_method: github` to
  make the P4 detection explicit rather than inferred.
- **`.jackal/harness-guidance.md`** (NEW, F5): pin merge strategy = "never merge locally; always
  open a PR" and stop-after-each-issue if desired, so even without the P4 detection the harness
  cannot self-merge to ROAR's protected main.
- **Commit-scope note** (F10): confirm ROAR CLAUDE.md already documents `feat(institutions):`
  scopes (it does, line 60) — no change needed; this is the source the P4 implementor change reads.
- Bump ROAR root CLAUDE.md `Last verified` date (its own rule).

**Done when:** `/execute` backlog mode against ROAR reads `backend: github` + `gh_repo`, and the
default completion path opens a PR rather than attempting a forbidden local merge.

### Phase 8 — Configurable label scheme + hierarchical `.jackal/` resolution (F15, F16)

**Goal:** The harness matches the consuming repo's label convention, and `.jackal/` overrides can
(optionally) be scoped per module in a monorepo.

**F15 — label scheme (High).** The harness hard-codes colon-style labels (`status:ready`,
`status:in-progress`, `status:paused`, `status:blocked`) in 5 skills:
`jackal-design-plan`, `jackal-impl-plan`, `jackal-pause-session` (supervisor) and
`execute`, `finish` (plan-and-execute). ROAR — the first and only live GitHub-backlog consumer —
uses **slash-style** (`status/ready`, `complexity/simple`, `type/chore`, `module/api`), which is the
better/standard convention (GitHub renders `area/value` hierarchically). The harness is the outlier.

- Add a `label_style:` key to the Jackal Config contract — values `slash` | `colon`, **default
  `slash`** (matches ROAR and GitHub norm).
- Update the 5 skills to derive the separator from config and build labels as
  `status${SEP}ready` etc., rather than literal `status:ready`. Touch every label read *and* write
  (`--add-label`, `--remove-label`, `gh issue list --label`, and the prose label legends in
  `execute`).
- Document the standard label set in the supervisor agent / README so projects can create matching
  labels (`status/ready`, `status/in-progress`, `status/paused`, `status/blocked`, plus the
  `complexity/*`, `type/*`, `priority/*`, `module/*` families ROAR already uses).
- The Phase 7 trace script gains a check: every label a skill references resolves against the target
  repo's actual label set (`gh label list`), flagging missing labels before a run.

**F16 — hierarchical `.jackal/` resolution (Medium).** Today every skill reads
`$REPO_ROOT/.jackal/harness-guidance.md` — **root only, no find-up.** In a monorepo a module-level
`.jackal/` (e.g. `packages/modules/atlas/.jackal/`) would silently never be read, so per-module
harness-*behavior* overrides are impossible. (Per-module *context* already flows correctly via domain
`CLAUDE.md` and cwd→root loading — that is the right home for most module differences, and F16 does
not change it.)

- Teach the guidance-reading step in `design`, `plan`, `execute`, `review`, `jackal-ui-verify` to
  resolve `.jackal/harness-guidance.md` **find-up from the worktree's working directory to repo
  root**, merging nearest-wins (module-level overrides root-level keys; root provides the base).
- Keep root-only as the effective behavior when no nested `.jackal/` exists (zero change for
  single-package repos like the harness's other consumers).
- Document the precedence chain explicitly:
  `module .jackal/ > root .jackal/ > Jackal Config keys > built-in defaults`.
- **Scope guard:** this is a real feature with edge cases (merge semantics, which dir is "the
  module"). If it proves larger than Simple at impl-plan time, split F16 into its own issue and ship
  F15 alone — F15 is the one blocking real ROAR runs; F16 is a latent monorepo limitation with no
  current broken behavior.

**Done when:** labels generated/queried by the harness match a configurable scheme (default slash,
verified against ROAR's real labels), and `.jackal/harness-guidance.md` resolves find-up with
documented nearest-wins precedence.

---

## Phase Dependency / Sequencing

```
P1 (supervisor agent) ─┐
P2 (skills + debug)    ─┤
P3 (declare deps)      ─┼─▶ independent; can land in any order or parallel
P5 (staleness)         ─┤
P8 (labels + .jackal)  ─┘   (F15 label fix is independent; F16 may split out if large)
P4 (defaults)  ─────────────▶ should land before P6 (P6 leans on P4's detection)
P6 (ROAR)      ─────────────▶ last; depends on P4 semantics existing
P7 (trace/test) ────────────▶ runs LAST, gates the release (depends on all above)
```

P1, P2, P3, P5, P8 are independent and parallelizable. P4 then P6 are sequential. P7 gates release.
**F15 (label scheme) is a prerequisite for any real ROAR backlog run** — prioritize it alongside P6.

---

## Risks & Mitigations

- **marketplace.json `requires` may not be a supported schema field.** Mitigation: if the schema
  rejects it, declare deps in README only + a pre-flight check in the supervisor agent; don't block
  on schema support.
- **Protected-main detection via `gh` adds a network call / auth dependency in the hot loop.**
  Mitigation: prefer the explicit `protected_main`/harness-guidance signal; treat `gh` detection as
  a best-effort fallback, cached per session.
- **Porting ed3d skills drags ed3d voice/branding.** Mitigation: light edit pass for naming; keep
  the substance (the discipline is the value).
- **Two-repo plan = two PRs in two repos.** Mitigation: land jackal phases (P1–P5) first, release,
  then do the ROAR PR (P6) against the released harness behavior.

---

## Resolved Decisions (review round 1)

1. **F13 / test-requirements.md → wire a real consumer.** The reviewer agent will cross-check that
   each acceptance criterion maps to a test (reading `test-requirements.md`), turning the orphaned
   artifact into an actual gate. Folded into **Phase 2**. (Full `test-analyst` agent stays out of
   scope; this is the lighter coverage check.)
2. **F14 / debug frontmatter → rename to `debug`.** Rename `name: systematic-debugging` →
   `name: debug` to match the directory and invocation, *unless* a reference inventory finds the old
   name is depended on elsewhere — in which case update those refs too. Folded into **Phase 2**.
3. **F9 / `.ed3d/` fallback → KEEP as documented legacy fallback.** Investigation found **ATLAS
   actively uses `.ed3d/design-plan-guidance.md` + `.ed3d/implementation-plan-guidance.md`** (and was
   modified 2026-06-15). Dropping the lookups would break ATLAS planning. Resolution: `.jackal/` stays
   canonical; `.ed3d/` remains a documented legacy fallback in `design`/`finish`/`review`. Only the
   stale *prose* is fixed (e.g. `jackal-pause-session:69` "ed3d skills create tasks"). **Phase 5
   adjusted accordingly** — do NOT remove `.ed3d/` reads. (Migrating ATLAS to `.jackal/` is a
   separate, out-of-scope task.)
4. **F4 / marketplace `requires` → add it.** `marketplace.json` is JSON, not YAML — an extra
   informational `requires` array won't break parsing. Add it to the relevant plugin entries even if
   the published schema ignores it; pair with the README declaration. Folded into **Phase 3**.
5. **Versioning → one batched marketplace bump.** Single marketplace version bump covering all
   touched plugins, with a consolidated CHANGELOG entry. (Repo CLAUDE.md's per-plugin + marketplace +
   changelog sync rule is satisfied by one coordinated changeset.) Applies across all phases.

---

## Phase 7 — Test & dependency-trace verification (Q1)

**Goal:** A repeatable test document that simulates invoking the plugins and traces every
cross-reference, so "everything resolves" is a checked fact, not a claim.

- Write `docs/test-plans/2026-06-16-harness-coherence.md` containing:
  - **Static dependency trace:** a table of every `subagent_type`, `Skill(...)`, and
    REQUIRED-SUB-SKILL reference across all jackal plugins → resolves to (shipped | declared dep |
    house-style | BROKEN). The DoD is zero BROKEN rows.
  - **A shippable trace script** (`scripts/trace-deps.sh` or inline) that greps every
    `subagent_type:`/`Skill(`/`jackal-*:`/`ed3d-*:` reference and classifies each as shipped,
    declared, or dangling — runnable as a pre-release check and re-runnable after future upstream
    syncs.
  - **Lifecycle simulation (dry trace):** walk a sample Standard and Complex issue through
    `jackal-design-plan → jackal-impl-plan → execute → finish`, listing at each step which
    skill/agent is invoked and confirming it exists. Where live invocation is feasible (e.g. a
    throwaway issue in a scratch repo), capture the actual dispatch; otherwise document the trace.
  - **Declared-dep absence test:** confirm that with the 3 ed3d plugins *uninstalled*, the harness
    fails *loudly* (per Phase 3's visible warning), not silently.
  - **Label-resolution check (F15):** every label a skill references resolves against the target
    repo's actual label set (`gh label list`), so a label-scheme mismatch is caught before a run.
- Run the trace script as the final gate before the batched version bump.

**Done when:** the trace script reports zero dangling references, the lifecycle simulation shows
every step resolving, the label-resolution check passes against ROAR's labels, and the test doc is
committed.

> Sequencing is canonical in the **Phase Dependency / Sequencing** section above (P7 runs last and
> gates the release; it depends on P1–P6 and P8 having landed).
