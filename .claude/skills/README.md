# Claude Skills

Skills are workflows that Claude (and other agents) invoke for repeating
multi-step tasks. Each lives in `.claude/skills/<name>/SKILL.md` and is
auto-discovered by Claude Code.

## When to add a skill

Add a skill when you've performed the same multi-step workflow **three times**.
Don't add one speculatively — speculative skills bloat context and degrade
adherence. The full four principles for what we keep — universal across
tech stacks, substantive rather than duplicative, a habit rather than a
tool, used often enough to stick — live in
[`docs/APPROACH.md`](../../docs/APPROACH.md).

## Skills in this repo

| Skill | What it does |
| ----- | ------------ |
| [`work-loop`](work-loop/SKILL.md) | The standard plan → execute → verify → review loop for non-trivial work. Start here for any feature, fix, or refactor. |
| [`new-adr`](new-adr/SKILL.md) | Create a new ADR with the next available number, from the template |
| [`new-rfc`](new-rfc/SKILL.md) | Open a new RFC with a research-phase gate (repo + external sweep, recommendations on unresolved questions) before drafting |
| [`new-spec`](new-spec/SKILL.md) | Scaffold a new spec directory, surface assumptions, then fill `spec.md` and `plan.md` |
| [`bug-fix`](bug-fix/SKILL.md) | Fix a defect — reproduce → failing test → root cause → minimum fix → root-vs-symptom verify → commit body documents *why* |
| [`new-package`](new-package/SKILL.md) | Scaffold a new package in `packages/` |
| [`update-conventions`](update-conventions/SKILL.md) | Open an RFC to change `docs/CONVENTIONS.md` |
| [`adapt-to-project`](adapt-to-project/SKILL.md) | Walk the adopter through the four classes of post-install change (substitution, `.upstream` companion merges, discovery + restructuring, within-layout consolidation). Per-scope; class-1 shells out to `agentbundle adapt` |
| [`new-guide`](new-guide/SKILL.md) | *(stub — full body in a follow-on PR)* Draft a new user-facing guide under `docs/guides/<quadrant>/` following the Diátaxis framework |

## Authoring skills

Each `SKILL.md` should:

1. Have a tight YAML frontmatter `description` — the *trigger surface*
   that decides invocation. The body answers the disjoint question of
   what to do once invoked (preconditions, judgment, procedure); it must
   not restate the trigger.
2. Be small. Skills are loaded into context when triggered; bloated skills
   crowd out the user's actual task.
3. Link out to scripts in the same directory rather than embedding shell.
   Code in scripts can be tested; code in markdown can't.
4. Refer to other skills, subagents, and conventions sections by name
   in the body — the same way `work-loop` cites `new-spec`,
   `adversarial-reviewer`, and `docs/CONVENTIONS.md`. The body is the
   contract; resolution happens at runtime against whatever the
   adopter has installed. Don't try to pin those references in
   frontmatter — there's no machinery that consumes a manifest, and
   skills installed elsewhere land on top of the adopter's own
   `AGENTS.md` / `docs/CONVENTIONS.md` / `docs/CHARTER.md` rather than
   our copy. The contract is that an `AGENTS.md` exists, not that
   ours does.
