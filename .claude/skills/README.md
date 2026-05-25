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
[`docs/CHARTER.md`](../../docs/CHARTER.md) § Principles.

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

## Spec compliance

Every skill in this repo — and every skill an adopter scaffolds from
this template — is held to the [agentskills.io
specification](https://agentskills.io/specification). The contract is
mechanical, enforced by `tools/lint-skill-spec.py`; the linter runs in
CI, in the pre-PR hook, and on demand.

### Blessed layout

A skill directory may contain four canonical subdirectories. Anything
else at the skill root warns (allowed but flagged):

| Subdirectory | Purpose |
| ------------ | ------- |
| `scripts/`   | Executable helpers the skill invokes |
| `references/`| Long-form docs the skill links into on demand |
| `assets/`    | Templates and other static files |
| `evals/`     | Optional — see below |

### Evals add-on

A skill that ships `evals/` must include `evals/evals.json`. Schema:

```json
{
  "skill_name": "<must match the skill's frontmatter name>",
  "evals": [
    {
      "id": 1,
      "prompt": "...",
      "expected_output": "...",
      "files": ["evals/files/sample.txt"],
      "assertions": ["..."]
    }
  ]
}
```

`id` may be int or string but must be unique within the file. `files`
entries (when present) must resolve to existing files under the skill
root. Reference:
[evaluating skills](https://agentskills.io/skill-creation/evaluating-skills).

### Path rules in SKILL.md bodies

- **Self-references use skill-relative paths.** Write `scripts/foo.py`,
  not `.claude/skills/<self>/scripts/foo.py`; write `references/REF.md`,
  not `.claude/skills/<self>/references/REF.md`. The skill root is the
  implicit base. The linter rejects any install-path prefix
  (`.claude/skills/...` or `packs/<pack>/.apm/skills/...`) in a body,
  whether or not a skill name follows the slash — bare mentions of the
  install root are out too, because they're environment-specific.
- **Cross-skill references use the skill name only.** Say "use the
  `work-loop` skill", not `.claude/skills/work-loop/SKILL.md`. The body
  must stay portable across installations that put skills somewhere
  else.
- **`.claude/agents/<name>` references are allowed.** Subagents are
  not skills and the spec doesn't constrain them.
- **`~/.claude/...` references are allowed.** User-scope prose;
  documenting an install location is fine in narrative form.

### Project metadata extensions

The spec lets each project add its own keys under `metadata:`. This
repo uses two:

- `metadata.credentialed` — boolean, marks a skill as a credentialed
  primitive (needs an external API token).
- `metadata.primitive-class` — one of `credentialed-cli` or
  `mcp-server` when `credentialed: true`.

Value-shape checks for those two keys live in
`tools/lint-agent-artifacts.py`; companion lints in
`tools/lint-credentialed-skills.sh` enforce the safety rules
credentialed skills must carry in their bodies. The spec-compliance
linter only checks the structural shape (`metadata` is a mapping;
values are scalars or lists of scalars) — per-key value validation
is delegated.

### Enforcement floor

`tools/lint-skill-spec.py` walks both the projection
(`.claude/skills/*/SKILL.md`) and the seeds
(`packs/*/.apm/skills/*/SKILL.md`) so drift between source-of-truth
and rendered output can't sneak past `make build-check`. Run it
manually with `python3 tools/lint-skill-spec.py`. The companion
self-test is `python3 tools/test-lint-skill-spec.py`.
