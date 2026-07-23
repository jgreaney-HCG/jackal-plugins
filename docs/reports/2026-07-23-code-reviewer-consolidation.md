# Report: Code-reviewer consolidation and reconciliation against jackal-plan-and-execute 3.10.0

_Date: 2026-07-23. Sources: the code-reviewer agent inventory collected from `~/.claude` (6 distinct definitions across 13 files), the org-chart Epic #499 session transcript (2026-07-22), and the current repo snapshot (jackal-plan-and-execute 3.10.0)._

_An earlier version of this report was written against a stale March snapshot (ed3d 1.10.3) and proposed changes the current repo had already implemented in evolved form; this version is reconciled against 3.10.0. The superseded ed3d-based rewrites are preserved in this branch's history (commit `6060660`) for reference._

## 1. Inventory verdicts (workstation `~/.claude`)

| Definition | Where | Verdict |
|---|---|---|
| ECC reviewer (sonnet, 8.7KB) | `~/.claude/agents/code-reviewer.md` + `everything-claude-code` marketplace | **Delete.** A user-level agent whose description ("Proactively reviews… **MUST BE USED for all code changes**") is engineered to win ambient agent selection — this is why it triggers most of the time. Generic checklists, arbitrary numeric thresholds, ~40% of its tokens are embedded code examples, and its CRITICAL/HIGH/MEDIUM/LOW + pass/warn taxonomy is incompatible with the jackal review loop's PASS/ISSUES_FOUND/BLOCKED verdicts. Its concrete security checklist was its one strong section — now folded into `reviewer` (3.11.0). |
| ECC `.kiro` copy + 6 translation variants | ECC marketplace | **Delete with the marketplace.** Never loaded as Claude Code agents; disk clutter. |
| ed3d plan-and-execute reviewer (opus) + review template | ed3d-plugins marketplace | **Superseded.** The jackal `reviewer`/`reviewer-deep` pair (this repo) is its successor and is better on every axis that matters (tiering, scoped verification, report caps, Minor-doesn't-block). If the ed3d marketplace copy is still installed alongside the jackal one, remove it to eliminate a second `code-reviewer`-shaped agent from selection. |
| pr-review-toolkit reviewer (opus) | claude-plugins-official | **Drop** — near-duplicate of the feature-dev reviewer. |
| feature-dev reviewer (sonnet, read-only) | claude-plugins-official | **Optionally keep one** as an ad-hoc, outside-the-pipeline reviewer; it had the best confidence rubric of the catalog (now ported into `reviewer`). If kept, rename it (e.g. `quick-reviewer`) — every definition in the catalog shares `name: code-reviewer`, which worsens ambiguous selection. |

**The single highest-impact action is deleting `~/.claude/agents/code-reviewer.md`.** User-level agents win ambient triggering; nothing in any repo can fix that.

## 2. What 3.10.0 already covers (no action needed)

The current `reviewer`/`reviewer-deep` pair and surrounding skills already implement, in evolved form, most of what the Epic #499 analysis called for:

- **Tiered review:** Sonnet `reviewer` for per-phase/Standard, Opus `reviewer-deep` reserved for Complex/security-sensitive final reviews, with the single full-suite run reserved for the deep tier.
- **Scoped verification + work budget:** per-phase reviews run touched-area tests once, verify the implementor's test-report artifact, and are explicitly bounded ("one verification pass plus focused reading of the diff is the whole job").
- **Loop economics:** Minor issues alone are PASS (report, don't block) — stronger than the old ed3d zero-issues loop; re-reviews re-dispatch the Sonnet reviewer with PRIOR_ISSUES; three-cycle escalation to the human.
- **Design fidelity at build time:** the implementor's per-slice visual gate (render → screenshot → compare against the phase's reference image), the `design` skill's reference-screenshot capture (5a) and canonical-fixture-first scheduling, and `jackal-ui-verify` for live end-of-issue verification against ACs.
- **Model/thinking discipline:** per-dispatch model params with the Model Tier Table (Haiku for mechanical slices), and the runaway-thinking lesson (~97% hidden thinking tokens on the marathon Sonnet implementor) baked into `execute`.

## 3. What 3.11.0 adds (this change)

Three gaps remained; all are reviewer-side:

1. **False-positive bar** (`reviewer` step 3, mirrored in `reviewer-deep`): findings must be verified against the actual code, every Critical/Important finding needs a one-line failure scenario (concrete input/state → wrong behavior), repeats consolidate. In a loop where any Critical/Important finding triggers a fix dispatch plus a re-review, a false positive costs two agent runs — the bar is an economic control, not politeness.
2. **Security breadth in the standard tier:** the per-phase reviewer's Critical list covered injection/auth-bypass/exposed-secrets; added path traversal, XSS, secrets/PII in logs, unvalidated trust-boundary input, and missing external-call timeouts (Important). `reviewer-deep` already had the deeper trace-to-sinks list.
3. **Independent check on the visual gate:** the implementor's per-slice visual gate was self-reported with no reviewer verification — a verify-don't-trust gap, the same one the test-report artifact rules exist to close. The reviewer now treats a UI phase report that is silent on its visual-gate outcome as an Important issue; the `review` skill's dispatch template gains an optional `UI_PHASES` line. The reviewer checks the *claim*; live re-rendering stays with `jackal-ui-verify` to respect the work budget.

## 4. Remaining machine-side actions (not in any repo)

1. Delete `~/.claude/agents/code-reviewer.md` (fixes ECC over-triggering outright).
2. Uninstall the `everything-claude-code` marketplace; remove the stale ed3d-plugins marketplace if still installed alongside jackal-plugins.
3. Decide on one renamed ad-hoc reviewer (feature-dev's) or none.
4. If not already set: cap implementor thinking (e.g. `MAX_THINKING_TOKENS` in the monorepo's `.claude/settings.json`) — the Model Tier Table controls which model runs, but not how much hidden thinking Sonnet burns per step.
