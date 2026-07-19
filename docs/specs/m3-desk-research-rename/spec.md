# Spec: m3-desk-research-rename

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0064
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** integration

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

The `research` pack is renamed to `desk-research` and bumped to version 1.0.0.
The pack's primary entry skill `research` is renamed to `desk-research`. Four
project-lifecycle skills (`research-project-start`, `research-project-digest`,
`research-project-check`, `research-project-synthesize`) are renamed to their
`desk-research-project-*` equivalents. The six function-named skills that are
not pack-eponymous (`build-outline`, `compare-hypotheses`, `decision-archaeology`,
`devils-advocate`, `identify-perspectives`, `source-map`) are unchanged.

Operative cross-pack references are updated across all files that invoke the
pack or skill by old slug — including `frame-domain` (PE pack), `check-workspace`
(core pack), `init-project` (core pack), `contract-acquisition` (core pack),
`discovery-loop` (PE pack), `frame-intent` references, `frame-domain` examples,
and the `evidence-retriever` agent in the renamed pack. An `AGENTS.md` migration
guide is created in the renamed pack. RFC-0064 is edited (it is still Draft) to
record that no pack-level alias mechanism exists and that the migration is
documentation-only. `build-self` is run to propagate the rename into projected
outputs.

**Two namespaces that do not change:** the `workspace.toml` `type = "research"`
activity-type field and the `agentbundle-layout.toml` `[research]` section key are
both activity-type identifiers, not pack identifiers — they stay as `research`.

## Boundaries

### Always do

- Rename only operative references — files that execute, build, or run tests against
  the actual pack or skill names. Leave historical references in frozen RFC/ADR/spec
  bodies intact.
- Bump version to `1.0.0` in both `pack.toml` and `plugin.json` (breaking change —
  major bump).
- Update `display_name`, `description`, and `documentation` link in `pack.toml` and
  `plugin.json` to reflect the new name.
- Update the two renamed skill slugs present in `[pack.evals] skills` in `pack.toml`
  (`"research"` → `"desk-research"` and `"research-project-start"` →
  `"desk-research-project-start"`; the other three project skills are not in the
  evals list and are not added).
- Sweep the entire `packs/` tree for operative `research` pack/skill slug references
  beyond the three named cross-pack files — at minimum check `init-project`,
  `contract-acquisition`, `discovery-loop`, `frame-intent` references, and
  `frame-domain` examples.
- Update guide prose and slug-named guide files within `docs/guides/desk-research/`
  to reflect new skill slugs.
- Create `packs/desk-research/AGENTS.md` with a migration table covering: pack name,
  all five renamed skill slugs, and the adopter install-state impact.
- Edit RFC-0064 body directly (it is still Draft — formal errata apply only after
  acceptance per RFC-0055) to record the deprecation-alias assessment outcome in the
  M3 ACs section.
- Run `make lint-packs`, `make build-self`, and the agentbundle test suite as the
  final gate.

### Ask first

- If the `research-project-start` bug-fix spec (also in M3) has already landed and
  created new agentbundle-layout reference content that references the old skill name —
  coordinate rather than double-editing.
- If any skill `SKILL.md` body within the pack references other pack skills by the
  old slug in a way that is ambiguous between operative and historical — surface before
  editing.

### Never do

- Change `workspace.toml` `type = "research"` entries or the `agentbundle-layout.toml`
  `[research]` section key — these are activity-type identifiers, not pack names.
- Edit the `[pack.layout.repo] parent = ".context/research"` line in `pack.toml` or
  the `agentbundle-layout.toml` schema reference — both are owned by the bug-fix spec.
- Rename references in frozen RFC/ADR bodies or shipped spec bodies (historical record).
- Rename generic test-fixture strings that use `"research"` as an arbitrary placeholder
  unconnected to the actual pack (e.g. schema-shape unit tests).
- Add a new top-level directory without running `make build-self`.
- Introduce a compatibility shim or dual-name projection — the assessment outcome is
  documentation-only migration; no alias code.

## Testing Strategy

**Goal-based check** for all structural ACs: `make lint-packs` exits 0; `make build-self`
exits 0; `pytest packages/agentbundle/` green. These are the single commands a reviewer
can run to confirm the rename is structurally complete.

**Goal-based check** for each name-change AC: targeted `grep` / `find` one-liners
confirming old names are absent and new names are present in the operative file set.
Each task's `Done when:` states the exact check.

No TDD stubs required — this spec has no logic invariants, only renaming invariants.
No manual QA — no user-facing UI surface.

## Acceptance Criteria

- [x] `packs/desk-research/` directory exists; `packs/research/` does not exist.
- [x] `packs/desk-research/pack.toml` has `name = "desk-research"`, `version = "1.0.0"`,
  `display_name = "Desk Research"`, and `documentation` link updated to `.../docs/guides/desk-research/`.
- [x] `packs/desk-research/.claude-plugin/plugin.json` has `"name": "desk-research"` and
  `"version": "1.0.0"`.
- [x] `[pack.evals] skills` list in `pack.toml` contains `"desk-research"` and
  `"desk-research-project-start"` and does not contain the old names `"research"` or
  `"research-project-start"` (only two of the five renamed skills are in the evals list).
- [x] Skill directory `packs/desk-research/.apm/skills/desk-research/` exists;
  `packs/desk-research/.apm/skills/research/` does not.
- [x] Skill directories `desk-research-project-start`, `desk-research-project-digest`,
  `desk-research-project-check`, `desk-research-project-synthesize` exist under
  `packs/desk-research/.apm/skills/`; the four old `research-project-*` directories
  do not.
- [x] `packs/core/.apm/skills/check-workspace/SKILL.md` references `desk-research-project-start`,
  not `research-project-start`.
- [x] `packs/product-engineering/.apm/skills/frame-domain/SKILL.md` references
  `desk-research` (not `research`) for all operative skill-invocation lines.
- [x] `packs/core/.apm/skills/init-project/SKILL.md`, `contract-acquisition/SKILL.md`,
  `packs/product-engineering/.apm/skills/discovery-loop/SKILL.md`, and
  `frame-domain/examples/` contain no stale operative `research` pack/skill slug
  references; same for all other files found by the repo-wide operative sweep.
- [x] `packs/desk-research/.apm/agents/evidence-retriever.md` description references
  `/desk-research`, not `/research`.
- [x] `packs/desk-research/AGENTS.md` exists and contains a migration table with: old pack
  name → new pack name; all five old skill slugs → new skill slugs; a note on adopter
  install-state impact (state key `research` → `desk-research`; reinstall required).
- [x] RFC-0064 body (M3 ACs section) records the assessment outcome: pack-level alias
  unsupported in agentbundle (adapter-level only); migration is documentation-only;
  assessed 2026-07-18.
- [x] Guide files under `docs/guides/desk-research/` contain no `/research` or
  `research-project-*` invocation prose; pack-named slug files renamed
  (`reference/research-pack.md` → `reference/desk-research-pack.md`,
  `tutorials/research-first-session.md` → `tutorials/desk-research-first-session.md`).
- [x] `docs/guides/desk-research/` directory exists; `docs/guides/research/` does not.
- [x] `packages/agentbundle/tests/integration/test_install_research_user_scope.py` and
  other integration tests that reference the actual pack by name pass with the new name.
- [x] `make lint-packs` exits 0; `make build-self` exits 0; `pytest packages/agentbundle/`
  green.

## Assumptions

- Technical: Pack manifest at `packs/research/pack.toml` — `name = "research"`, `version = "0.6.1"`,
  `display_name = "Research"` (source: `packs/research/pack.toml:2-6`)
- Technical: Plugin JSON — `"name": "research"` (source: `packs/research/.claude-plugin/plugin.json`)
- Technical: 11 skill directories in `packs/research/.apm/skills/`; 5 are rename targets,
  6 are unchanged (source: `ls packs/research/.apm/skills/`)
- Technical: No pack-level deprecation alias mechanism exists in agentbundle — alias support
  is adapter-scoped only; `deprecated_names` field not in pack.toml schema (source: grep on
  `packages/agentbundle/` — no match; `test_adapter_kiro_alias.py` confirms alias is
  adapter-level only)
- Technical: `agentbundle-layout.toml [research]` section key is an activity-type identifier,
  not a pack name — confirmed by `check-workspace/SKILL.md:89` which already uses
  "desk-research pack" alongside `type = "research"` (source:
  `packs/core/.apm/skills/check-workspace/SKILL.md:89`)
- Technical: No `AGENTS.md` exists in the research pack root today (source: `ls packs/research/`)
- Technical: Integration tests that reference the actual pack by operative name:
  `test_install_research_user_scope.py`, `test_install_copilot_full_parity.py:152`,
  `test_install_profile_live.py:83`, `test_install_default_source.py:124-146`,
  `test_enriched_pack_metadata.py:40` (source: grep on `packages/agentbundle/tests/`)
- Technical: `docs/guides/research/` exists; pack.toml `documentation` link points to it
  (source: `packs/research/pack.toml:85`; `ls docs/guides/`)
- Process: RFC-0064 M3 governs this rename; no sub-RFC needed; rename and bug-fix are
  independent and can ship in parallel PRs (source: `docs/rfc/0064-ini-001-ai-native-ecosystem.md:122`)
- Process: Operative references renamed; historical references in frozen RFC/ADR bodies
  left intact (source: memory `reference_renaming_catalogue_tool_operative_vs_historical`)
- Product: Major version bump (1.0.0) for a breaking rename — confirmed by user 2026-07-18
- Product: No pack-level alias — documentation-only migration; erratum added to RFC-0064 —
  confirmed by user 2026-07-18
