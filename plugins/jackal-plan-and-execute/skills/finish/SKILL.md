---
name: finish
description: Completes a development branch — verifies tests, rebases onto origin/main when behind, pushes, and opens a Pull Request. PR is the only completion path; keep/discard only on explicit request.
user-invocable: true
---

# Finish

Complete a development branch after implementation passes review. The output of
finish is **always a Pull Request** — `main` is protected and the harness never
merges locally. There is no options menu.

Two exceptions, only when the user explicitly asks:
- **Keep** ("keep the branch, I'll handle it") — report branch + worktree location, stop.
- **Discard** ("throw this away") — require a typed "discard" confirmation, then
  delete the branch and worktree and restore the issue to `status/ready`.

---

## Process

### 1. UI Verification (if applicable)

Read `ui_path` from the Jackal Config in CLAUDE.md. Check whether this branch touched any files under that path:

```bash
UI_PATH=$(grep 'ui_path' CLAUDE.md | awk '{print $2}')
git diff --name-only main...[feature-branch] | grep "^${UI_PATH}"
```

If any UI files changed: invoke `jackal-ui-verify` with the issue ID. **Do not proceed until it reports ✅ PASS.**

### 2. Verify Tests Pass

```bash
$TEST_CMD
```

If tests fail → stop. Report failures. Don't proceed.

### 3. Rebase If Behind

PRs that sit behind `main` accumulate conflicts and fail CI on stale code. Check
**before** pushing, every time:

```bash
git fetch origin
BEHIND=$(git rev-list --count HEAD..origin/main)
```

If `BEHIND` > 0:

```bash
git rebase origin/main
```

- Rebase clean → re-run `$TEST_CMD` (fast fail: the rebase may have changed
  behavior under you). Green → proceed.
- Rebase conflicts → resolve them if the resolution is mechanical (imports,
  lockfiles, adjacent edits). If the conflict is semantic — both sides changed
  the same behavior — stop and report: this needs a human or a fresh look at
  both branches. Never resolve a semantic conflict by guessing.

### 4. Contract Check (if canon exists)

If `docs/canon/` exists and `/jackal-director:contract-check` was not already run by `execute`'s
final review, run it now. The bar is **CLEAN, or FLAGGED with every flag
explained** in your report. An unexplained FLAG blocks the PR. ESCALATE always
blocks — fix the canon gap first.

### 5. Push and Create PR

```bash
git push -u origin [feature-branch]
```

Build the PR body from the repo's template if one exists, so required sections
are filled rather than left blank:

```bash
TEMPLATE=$(ls .github/PULL_REQUEST_TEMPLATE.md .github/pull_request_template.md 2>/dev/null | head -1)
```

- If a template exists: fill every section it defines from the issue ACs and
  the diff — the section names are project-specific (e.g. "Linked issue",
  "Related issue"), so read the template rather than assuming a section is
  literally titled "Closes #N".
- **Regardless of the template's section names**, if this PR fully completes
  the issue, that section's body text must contain one of GitHub's literal
  auto-close keywords immediately before the bare issue number: `Closes #N` /
  `Fixes #N` / `Resolves #N`. Writing the issue's tracker ID alone (e.g.
  `GL-42`) does **not** trigger auto-close — GitHub only recognizes those
  keywords followed by `#<number>`. If the PR only partially completes the
  issue (follow-up work remains), use `Related to #N` instead and leave the
  issue open on purpose.
- If no template: use a concise default body (summary + `Closes #N` + test
  results + review verdict + contract-check status).

```bash
gh pr create --title "[#issue]: [title]" --body "$PR_BODY"
```

If the project uses CodeCommit (check `pr_method` in Jackal Config), push and
print the `aws codecommit create-pull-request` command instead.

### 6. Update Project Context

Dispatch the project-claude-librarian to update CLAUDE.md files if contracts
changed. This agent ships in the `ed3d-extending-claude` plugin — a **declared
dependency** of the jackal harness.

```xml
<invoke name="Agent">
<parameter name="subagent_type">ed3d-extending-claude:project-claude-librarian</parameter>
<parameter name="model">sonnet</parameter>
<parameter name="description">Updating project context</parameter>
<parameter name="prompt">
Review changes on [feature-branch] vs main.
Update CLAUDE.md files if API contracts or project structure changed.
Working directory: [path]

Do not dispatch or invoke any subagents — do the work directly with your own tools.
</parameter>
</invoke>
```

Every Agent dispatch above carries an explicit `<parameter name="model">`; a
model-unspecified dispatch is a defect (see the Model Tier Table in the
`execute` skill and the `jackal-supervisor` agent).

**If `ed3d-extending-claude` is not installed, do NOT silently skip.** Emit a
visible warning so the human knows the closeout was incomplete:

```
⚠️  CLAUDE.md freshness re-verification SKIPPED — ed3d-extending-claude (project-claude-librarian)
    is not installed. If this project requires doc closeout, update the touched CLAUDE.md files
    and their `Last verified:` dates manually before the PR merges.
```

### 7. Update Issue State

- Post the final review's **AC coverage table** as an issue comment and tick the
  satisfied `- [ ] AC` checkboxes in the issue body — the issue should reflect
  verified reality, not intentions.
- Remove `status/in-progress`. Leave the issue **open** — `Closes #N` in the PR
  body closes it when the PR merges.
- Issue doc (if the project keeps them): Status → In Review, add the PR URL.

(The `jackal-finish-branch` wrapper handles the label/comment mechanics when the
supervisor is in use.)

### 8. Worktree

**Keep the worktree while the PR is open** — review feedback may need fixup
pushes. `/jackal-supervisor:jackal-sweep` removes it (and the local branch) after the PR merges.

For an explicit discard: `git worktree remove --force [path]` and
`git branch -D [branch]` after the typed confirmation.

### 9. Test Plan Reminder

If `docs/test-plans/` has a file matching this issue, remind the user it exists.

---

## Autonomous Mode

Identical flow — there is nothing to ask the user. Rebase if behind, push, open
the PR, update the issue, report the PR URL in one line, and return control to
the loop. Never block waiting for the PR to merge.
