# VERIFY: Do spawned agents receive the memory index?

**Finding:** NO. Spawned agents do not receive `MEMORY.md`.

**Evidence:**

1. `grep -rniE "MEMORY\.md|memory index|auto-memory|memory/" plugins/` returns
   **zero matches**. No plugin skill or agent definition references, injects, reads,
   or forwards `MEMORY.md`.
2. The memory index is a Claude Code **host-level** file:
   `~/.claude/projects/-Users-jgreaney-Documents-code-jackal-plugins/memory/MEMORY.md`
   (confirmed present on disk at that path, 1117 bytes, last modified Jul 7 08:31).
   It is not tracked in the repo — `git -C "$(git rev-parse --show-toplevel)" ls-files
   | grep -i memory` returns nothing. It is surfaced only into the **main
   conversation's** system context via the host's auto-memory feature (the
   `# claudeMd` / auto-memory reminder block seen at the top of this session).
3. Agent-tool dispatches pass only the phase file, working directory, and prompt
   text — no memory content is injected into the subagent context. Confirmed by
   inspecting `plugins/jackal-plan-and-execute/skills/execute/SKILL.md`:
   - The cold `<invoke name="Agent">` dispatch template (SKILL.md:112-139) passes
     `PHASE_FILE`, `Working directory`, an implementation instruction, the
     `EXPECT`/honest-stopping-point text, and the no-nesting guard — no memory
     reference anywhere in the template.
   - The `<invoke name="SendMessage">` continuation template (SKILL.md:143-169) is
     the same: `PHASE_FILE`, an instruction to trust warm context from prior
     phases, `EXPECT`/honest-stopping-point text, and the no-nesting guard — again
     no memory reference.

**Consequence:** Memory is director-private. Skill text and agent-definition text
are the ONLY substrate reliably shared with spawned agents. Operational lessons
that must reach subagents (merged-PR gate, honest-stopping-point, sleep<timeout)
therefore belong in skills/agent definitions, not memory. This is exactly the
GL-347 failure mode: the nested supervisor subagent lacked a lesson the director's
private memory implied.

**If a later Claude Code version DOES inject project memory into subagents:** the
migration is still correct — skill text is the authoritative, version-controlled
home for procedure; memory then merely echoes it. The rule-of-thumb (Phase 4)
codifies this.

## #18 outputs present (verified, referenced not re-authored)

- Honest-stopping-point clause:
  - `plugins/jackal-plan-and-execute/agents/implementor.md:40-47` — under the
    `### Honest Stopping Point` heading (present).
  - `plugins/jackal-supervisor/agents/jackal-supervisor.md:21-26` — in the header
    block, immediately after "**Your workers never spawn workers.**" (present).
  - `plugins/jackal-plan-and-execute/skills/execute/SKILL.md:129-134` (cold Agent
    dispatch template) and `SKILL.md:162-167` (SendMessage continuation template)
    — present in both dispatch templates.
- Sleep<timeout rule:
  - `plugins/jackal-plan-and-execute/skills/execute/SKILL.md:429-433` — "Waiting
    for async work" section, item 2, "**Hard rule — never foreground-sleep to the
    timeout.**" The Bash tool's 120s default timeout is cited, with the rule that
    any foreground wait must be ≤100s (present).

**Conclusion:** ACs "honest-stopping-point present" and "sleep<timeout present"
are satisfied by the merged #18 work. This issue REFERENCES them (Phase 4
cross-references from the rule-of-thumb text); it does not duplicate or diverge
from them.
