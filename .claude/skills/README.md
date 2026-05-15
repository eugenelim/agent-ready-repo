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
| [`new-rfc`](new-rfc/SKILL.md) | Create a new RFC with the next available number, from the template |
| [`new-spec`](new-spec/SKILL.md) | Create a new spec directory with `spec.md` and `plan.md` |
| [`bug-fix`](bug-fix/SKILL.md) | Fix a defect — reproduce → failing test → root cause → minimum fix → root-vs-symptom verify → commit body documents *why* |
| [`new-package`](new-package/SKILL.md) | Scaffold a new package in `packages/` |
| [`update-conventions`](update-conventions/SKILL.md) | Open an RFC to change `docs/CONVENTIONS.md` |

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
4. Declare a `dependencies:` list in the frontmatter — every file
   *outside this skill's folder* the body relies on. Sibling agents the
   skill invokes (`.claude/agents/<name>.md`), templates it generates
   from (`docs/_templates/<name>.md`), tools it runs (`tools/<name>.sh`),
   sections of `docs/CONVENTIONS.md` it cites by anchor
   (`docs/CONVENTIONS.md#anchor`). Empty list (`dependencies: []`) is
   valid and honest. The manifest powers `tools/install-skill.py` (Path
   B in [`USING_THIS_TEMPLATE.md`](../../USING_THIS_TEMPLATE.md)) and is
   validated by `tools/lint-skill-deps.sh`. Keep it accurate as the body
   changes — drift is what the linter exists to catch.
