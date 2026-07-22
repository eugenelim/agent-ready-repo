# Plan: m5-jira-align-brief-intake

## Constraints

- Pure choreography skill — no new scripts or executable logic. Gates are
  `lint-packs` + `agentbundle validate` + `make build` + package pytest.
- Version bump: atlassian pack 0.3.2 → 0.4.0 (minor — new skill = new
  published interface).
- All `jira-align` subcommand names verified against
  `packs/atlassian/.apm/skills/jira-align/SKILL.md` before use in the skill
  body — no assumed subcommands.

## Risks

- None identified. This is a read-only choreography skill over an existing
  primitive (`jira-align`). The only novel element is the config-guided field
  mapping reference; no runtime parsing, no new dependencies.

## Changelog

- atlassian pack 0.4.0: `jira-align-brief-intake` skill added.

## Tasks

### Task 1: Author `SKILL.md` and `manifest.json`

**Verification mode:** goal-based check
**Done when:** `lint-packs` passes against the new skill directory; the
`SKILL.md` frontmatter parses; the `manifest.json` is valid JSON with
required fields; `agentbundle validate` reports the pack as valid.

**Approach:** Create `packs/atlassian/.apm/skills/jira-align-brief-intake/`
with `SKILL.md` and `manifest.json`. The skill body follows
`jira-brief-intake`'s choreography pattern, adapted for the Jira Align
entity model (Feature instead of Epic; `jira-align` primitive instead of
`jira`; config-guided field mapping).

### Task 2: Author `references/field-mapping.md`

**Verification mode:** goal-based check
**Done when:** The reference table covers all five AC items: (a) standard
Jira Align Feature field → brief field mapping; (b) org-specific state
vocabulary section with placeholder rows; (c) PI/Program Increment mapping;
(d) child → `US-n` provenance format; (e) setup note for new instances.

**Approach:** Create `packs/atlassian/.apm/skills/jira-align-brief-intake/references/field-mapping.md`.
Adopt a tabular format the adopter can annotate in-place. Include "Customize
for your org" headings on sections that require instance-specific values.

### Task 3: Update pack metadata

**Verification mode:** goal-based check
**Done when:** `packs/atlassian/pack.toml` shows version `0.4.0`, updated
`description`, and `jira-align-brief-intake` in `[pack.evals].skills`.
`packs/atlassian/.claude-plugin/plugin.json` matches. `make build` produces
an updated `marketplace.json` that includes the new skill.

**Approach:** Edit `pack.toml` and `plugin.json` in place.

### Task 4: Update enumeration docs

**Verification mode:** goal-based check
**Done when:** `grep -r "jira-align-brief-intake"` returns hits in all five
target docs: `packs/atlassian/README.md`,
`docs/guides/atlassian/README.md`,
`docs/guides/atlassian/reference/atlassian-skills.md`,
`docs/guides/atlassian/explanation/atlassian-pack.md`,
`docs/architecture/overview.md`.

**Approach:** Add the new skill to each doc's enumeration prose. De-count
hardcoded skill counts where the edit already touches the line (no-brittle-
counts convention).

### Task 5: Changelog entry + spec Status

**Verification mode:** goal-based check
**Done when:** `docs/product/changelog.md` has a `[Unreleased]` entry naming
the new skill. `spec.md` Status field is updated to `Shipped`. `workspace.toml`
moves the spec path from `queue` to `shipped`.

**Approach:** Add one entry under `[Unreleased] → Added`. Update spec.md and
workspace.toml in the same commit.

## Manual verification

Trace the skill's documented procedure against a representative Jira Align
Feature (using real subcommand names from `jira-align` SKILL.md) and confirm:

1. `jira-align: check` — maps to the real `check` subcommand. Exit 0 = proceed.
2. `jira-align get features <ID> --expand ownerUser,milestones` — maps to
   real `get` subcommand with a real resource path.
3. `jira-align list stories --filter "featureID eq <ID>"` — maps to real
   `list` subcommand with real OData filter syntax (verified in SKILL.md
   Step 3).
4. `jira-align list tasks --filter "featureID eq <ID>"` — same.
5. `jira-align list defects --filter "featureID eq <ID>"` — same.
6. Brief produced at `docs/product/briefs/<slug>.md` conforms to the Shape B
   template: heading, `Epic:` pointer, Outcome, user stories each tagged
   `(stories/<id>)`.
7. Hand-off to `receive-brief` by name fires in the core-present path.
8. Core-absent path: inlined compact brief shape + decompose/execute
   instruction is clear and actionable without `receive-brief` installed.
