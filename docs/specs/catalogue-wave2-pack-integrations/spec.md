# Spec: catalogue-wave2-pack-integrations

- **Status:** Approved
- **Owner:** eugenelim
- **Constrained by:** [RFC-0076 D6](../../rfc/0076-catalogue-contracts-composition-semantics-discovery.md)
- **Contract:** `contracts/pack.schema.json` (adds `integrations` array — engine change), `packages/agentbundle/agentbundle/_data/pack.schema.json` (byte-parity sync)
- **Shape:** schema change + validation + CLI surface extension + first-party pilots + authoring guidance

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

Mode: full (structural: new public schema field in `contracts/pack.schema.json`; new
agentbundle CLI surface in `agentbundle show` and extended validation surface in
`agentbundle catalogue verify`; public contract change requiring
Engine-Change-RFC: RFC-0076; first-party pack.toml files changed)

## Objective

Wave 2 adds the optional `[[pack.integrations]]` convention to the pack contract,
implementing RFC-0076 D6. After this wave, any pack author can declare named, optional
behavior seams between their pack and another pack — describing what each integration
does, who consumes and provides it, and what the fallback is when the target is absent.

The schema change (10 fields, 4 kind values) ships alongside portable validation rules
in `agentbundle catalogue verify`, extended output in `agentbundle show <pack>`, five
first-party pilot entries across `core` and `governance-extras`, and a completed
authoring-standards hub section that was left as a placeholder in Wave 1. This
establishes the full integration authoring workflow — schema, validation, CLI, pilots,
and guidance — as a single cohesive surface rather than shipping the schema alone.

## Boundaries

### Always do

- Keep `contracts/pack.schema.json` and `agentbundle/_data/pack.schema.json` byte-identical
  after every schema change. Run `python3 tools/catalogue/check_contract_parity.py` before
  committing.
- Add `Engine-Change-RFC: RFC-0076` to every commit message that changes
  `contracts/pack.schema.json`, `agentbundle/_data/pack.schema.json`, or
  `agentbundle/commands/show.py`.
- Verify all first-party pilot consumer references exist in the declaring pack's
  `.apm/<type>s/` directory before authoring (e.g., `skill:x` → `.apm/skills/`,
  `agent:x` → `.apm/agents/`, `command:x` → `.apm/commands/`).
- Verify all first-party pilot provider references exist in the target pack's
  `.apm/<type>s/` directory before authoring (same mapping).
- When bumping a pack version in `pack.toml`, bump `.claude-plugin/plugin.json`
  in lockstep and run `make build-self` to reproject `dist/claude-plugins/<pack>/`.
  Both pilot packs (core, governance-extras) require this for AC17 and AC18.
- Keep the authoring hub section free of host CI workflow requirements, Make target
  requirements, and internal governance citations (RFC/ADR/spec paths).
- Keep packs/AGENTS.md ≤ 150 lines and root AGENTS.md ≤ 250 lines.

### Ask first

- Adding a fifth `kind` value beyond `input`, `augment`, `review`, `handoff`.
- Making any `integrations` field required (all fields except `id`, `pack`, `kind`,
  `role`, `consumers`, `providers`, `when`, `purpose`, `fallback` are optional per D6;
  the whole `[[pack.integrations]]` array is optional).
- Extending validation to cross-catalogue integrations (D6 explicitly defers these).
- Changing the validation behavior when a target pack is absent (verify must still pass
  for portable catalogues — this is a non-negotiable D6 semantic).
- Adding `integrations` output to `agentbundle list-packs` or any surface other than
  `agentbundle show`.

### Never do

- Make the `[[pack.integrations]]` array required; it is always optional.
- Implement automatic dispatch of an integration (no auto-install, no dependency
  closure, no source-resolution change).
- Treat `when` as an executable expression — it is explanatory text only; no runtime
  evaluates it.
- Allow a pack to declare an integration targeting itself (self-target prohibition).
- Edit projected outputs under `.claude-code/`, `.cursor/`, `.kiro/`, etc. directly —
  edit `.apm/` sources and run `catalogue self-host`.
- Cite RFC, ADR, or spec paths in the shipped guide content
  (`catalogue-authoring-standards.md`).
- Exceed the AGENTS.md line caps (packs/AGENTS.md ≤ 150, root AGENTS.md ≤ 250).

## Testing Strategy

- **Schema structure (AC1–AC4):** TDD — Python tests assert new `integrations` array
  is present in `contracts/pack.schema.json` and `agentbundle/_data/pack.schema.json`;
  valid integration objects pass schema validation; objects with missing required fields
  or invalid `kind` values fail validation.
- **Validation rules (AC5–AC12):** TDD — pytest parametrized tests exercise each
  validation rule: unique IDs, kind enum, consumer ref existence, non-empty text fields,
  self-target prohibition, version-range grammar, target-absent portability, and
  target-present provider ref check.
- **agentbundle show output (AC13–AC16):** TDD — integration tests call `show.run()`
  with a fixture pack containing `[[pack.integrations]]` entries; assert table row and
  JSON key present and correctly populated.
- **First-party pilots (AC17–AC21):** goal-based — `agentbundle catalogue verify`
  exits 0 on the working-tree catalogue; `agentbundle show core --format json` and
  `agentbundle show governance-extras --format json` return the expected integration
  entries; each declared consumer/provider ref resolves.
- **Authoring hub (AC22–AC25):** visual/manual QA — placeholder replaced with
  substantive content; section numbered 11; contract citation present; scaffold sync
  passes.
- **Engine change and version (AC26–AC27):** grep confirms version strings; git log
  confirms Engine-Change-RFC footer.
- **Regression (AC28–AC31):** `SKIP_SAST=1 make build-check` and pytest exit 0; line
  count gates pass.

## Acceptance Criteria

### Phase A — pack.schema.json update (D6 schema; engine change)

**Schema structure**

- [ ] AC1: `contracts/pack.schema.json` gains an `integrations` property on the `pack`
  object — an array of integration objects, optional (not in `required`). Each
  integration object has `additionalProperties: false` and declares the following
  properties:
  - `id` (string, required): `^[a-z0-9][a-z0-9-]*$`
  - `pack` (string, required): target pack name
  - `kind` (enum, required): `["input", "augment", "review", "handoff"]`
  - `role` (string, required): user-facing label
  - `consumers` (array of strings, required, minItems 1): type-qualified primitive
    references matching `^(skill|agent|command|hook):[a-z0-9][a-z0-9-]*$`; each ref
    resolves within the declaring pack's `.apm/<type>s/` directory
  - `providers` (array of strings, required, minItems 1): same pattern; each ref
    resolves within the integration's target `pack` field's `.apm/<type>s/` directory
  - `when` (string, required, minLength 1)
  - `purpose` (string, required, minLength 1)
  - `fallback` (string, required, minLength 1)
  - `version` (string, optional): semver range

- [ ] AC2: A `pack.toml` with no `[[pack.integrations]]` section validates against the
  updated `contracts/pack.schema.json` without error (the array is optional).

- [ ] AC3: A `pack.toml` with a valid `[[pack.integrations]]` entry validates without
  error. A `pack.toml` with an integration entry missing a required field fails schema
  validation with a clear error. A `pack.toml` with `kind = "unknown"` fails schema
  validation.

- [ ] AC4: `agentbundle/_data/pack.schema.json` is byte-identical to
  `contracts/pack.schema.json` after the update. `python3 tools/catalogue/check_contract_parity.py`
  exits 0 on the updated repo.

### Phase B — agentbundle validation (new lint/verify rules)

**Validation rules**

- [ ] AC5: `agentbundle catalogue verify` reports an error when two integration entries
  in the same pack share the same `id`.

- [ ] AC6: `agentbundle catalogue verify` reports an error when an integration
  `kind` value is not one of `input`, `augment`, `review`, `handoff`.

- [ ] AC7: `agentbundle catalogue verify` reports an error when a `consumers` entry
  references a primitive type/name combination that does not exist in the declaring
  pack's `.apm/` directory (e.g., `skill:nonexistent` when no such skill file exists).

- [ ] AC8: `agentbundle catalogue verify` reports an error when `when`, `purpose`, or
  `fallback` is an empty string.

- [ ] AC9: `agentbundle catalogue verify` reports an error when an integration's
  `pack` field names the same pack as the declaring pack (self-target prohibition).

- [ ] AC10: `agentbundle catalogue verify` reports an error when the `version` field
  is present but its value is not a valid semver range string. Grammar: npm-compatible
  range syntax — caret (`^`), tilde (`~`), comparison operators (`>=`/`<=`/`>`/`<`),
  hyphen ranges, and `||` unions are all valid; exact `X.Y.Z` is always valid.
  Accept examples: `^1.0.0`, `>=2.0.0 <3.0.0`, `1.2.3`. Reject examples: `latest`,
  `@1`, `not-a-version`.

- [ ] AC11: `agentbundle catalogue verify` exits 0 when an integration's target
  `pack` is not present in the catalogue (portable validation: absent target is not
  an error).

- [ ] AC12: `agentbundle catalogue verify` reports an error when the integration's
  target pack is present in the catalogue and a `providers` entry names a primitive
  that does not exist in that target pack's `.apm/` directory. Absent-target catalogues
  skip this check (AC11).

### Phase C — agentbundle show output (table + JSON)

**show command extension**

- [ ] AC13: `agentbundle show <pack>` (table output) includes an "integrations" row
  when the pack declares at least one `[[pack.integrations]]` entry. The row value
  lists integration IDs, their `kind`, and target `pack` in a readable summary form
  (e.g., `frontend-preflight-augment (augment → frontend-engineering)`). When no
  integrations are declared, the row shows "-".

- [ ] AC14: `agentbundle show <pack> --format json` includes an `"integrations"` key
  in the output object. When integrations are present, the value is an array of
  objects, each containing at minimum `id`, `pack`, `kind`, `role`, `consumers`,
  `providers`, `when`, `purpose`, `fallback`, and `version` (null if absent). When no
  integrations are declared, the value is an empty array `[]`.

- [ ] AC15: A pytest integration test calls `show.run()` with a fixture pack containing
  one `[[pack.integrations]]` entry (any valid entry). The test asserts the `integrations`
  key is present and non-empty in JSON output, and that the table output contains the
  integration ID string.

- [ ] AC16: A pytest integration test calls `show.run()` with a fixture pack containing
  no `[[pack.integrations]]` section. The test asserts the JSON output has
  `"integrations": []` and the table output does not error.

### Phase D — First-party pilot entries

**core pack.toml (core version must be bumped; governance-extras version must be bumped)**

- [ ] AC17: `packs/core/pack.toml` gains exactly two `[[pack.integrations]]` entries:

  1. `id = "frontend-preflight-augment"`, `pack = "frontend-engineering"`,
     `kind = "augment"`, `role = "Frontend pre-flight augmentation"`,
     `consumers = ["skill:work-loop"]`, `providers = ["skill:frontend-engineering"]`

  2. `id = "frontend-cold-reviewer"`, `pack = "frontend-engineering"`,
     `kind = "review"`, `role = "Frontend cold reviewer"`,
     `consumers = ["skill:work-loop"]`, `providers = ["agent:frontend-reviewer"]`

  Both entries include non-empty `when`, `purpose`, and `fallback` fields. The `core`
  pack version is bumped (patch) to reflect the pack.toml change.
  `packs/core/.claude-plugin/plugin.json` version is bumped in lockstep; `make build-self`
  is run to reproject `dist/claude-plugins/core/`.

- [ ] AC18: `packs/governance-extras/pack.toml` gains exactly three `[[pack.integrations]]`
  entries:

  1. `id = "promoted-research-evidence"`, `pack = "desk-research"`, `kind = "input"`,
     `role = "Promoted research evidence"`, `consumers = ["skill:new-rfc"]`,
     `providers = ["skill:desk-research", "skill:desk-research-project-synthesize"]`

  2. `id = "design-proposal-product-engineering"`, `pack = "product-engineering"`,
     `kind = "input"`, `role = "Design proposal"`, `consumers = ["skill:new-rfc"]`,
     `providers = ["skill:frame-intent", "skill:de-risk-intent"]`

  3. `id = "design-proposal-architect"`, `pack = "architect"`, `kind = "input"`,
     `role = "Design proposal"`, `consumers = ["skill:new-rfc"]`,
     `providers = ["skill:architect-design", "skill:architect-review"]`

  All entries include non-empty `when`, `purpose`, and `fallback` fields. The
  `governance-extras` pack version is bumped (patch) to reflect the pack.toml change.
  `packs/governance-extras/.claude-plugin/plugin.json` version is bumped in lockstep;
  `make build-self` is run to reproject `dist/claude-plugins/governance-extras/`.

- [ ] AC19: `agentbundle catalogue verify --root .` exits 0 on the working-tree
  catalogue after the pilot entries are added. All five consumer refs resolve to
  existing files in the declaring packs' `.apm/<type>s/` directories. All five provider
  ref groups resolve to existing files in the target packs' `.apm/<type>s/` directories.

- [ ] AC20: `agentbundle show core --format json` returns an object where
  `"integrations"` is a non-empty array containing entries with `"id":
  "frontend-preflight-augment"` and `"id": "frontend-cold-reviewer"`.

- [ ] AC21: `agentbundle show governance-extras --format json` returns an object where
  `"integrations"` is a non-empty array containing entries with `"id":
  "promoted-research-evidence"`, `"id": "design-proposal-product-engineering"`, and
  `"id": "design-proposal-architect"`.

### Phase E — Authoring guidance

**catalogue-authoring-standards.md section 11 (Wave 1 placeholder → full content)**

- [ ] AC22: The unnumbered placeholder section "Optional pack integrations" in
  `guides/_shared/reference/catalogue-authoring-standards.md` is replaced by a
  numbered section "11. Optional pack integrations". The placeholder warning block is
  removed. The section includes:
  - A statement that `[[pack.integrations]]` is an optional array table in `pack.toml`,
    governed by `contracts/pack.schema.json`.
  - A reference to the ten fields with their required/optional status.
  - The four `kind` values with their D6 definitions.
  - A one-paragraph note on what integrations are not: no auto-install, no dependency
    closure, no executable `when` expressions.
  - The `fallback` requirement: every integration must declare what the consuming skill
    does when the target is absent.
  - A lint/verify command snippet.
  - No RFC, ADR, or spec path citations.

- [ ] AC23: The scaffold copy at
  `packages/agentbundle/agentbundle/_data/catalogue-scaffold/guides/_shared/reference/catalogue-authoring-standards.md`
  matches the updated live file after `python3 tools/catalogue/sync_authoring_scaffold.py --check`
  exits 0.

- [ ] AC24: `python3 tools/catalogue/sync_authoring_scaffold.py --check` exits 0 after
  the authoring hub update.

- [ ] AC25: The updated hub section contains no host CI workflow requirements, Make
  target requirements, or internal governance citations.

### Phase F — Engine change + version bump + changelog

- [ ] AC26: `packages/agentbundle/pyproject.toml` version is bumped to `0.27.0`.
  `packages/agentbundle/agentbundle/version.py` `CLI_VERSION` is set to `"0.27.0"` in
  lockstep. At least one commit in the PR contains `Engine-Change-RFC: RFC-0076` in
  its message (for the pack.schema.json + _data/ sync commit).

- [ ] AC27: `docs/product/changelog.md` has an `[Unreleased]` or `0.27.0` entry
  describing: (a) the new `[[pack.integrations]]` schema field in `pack.schema.json`,
  (b) the new validation rules in `agentbundle catalogue verify`, (c) the extended
  `agentbundle show` output, and (d) the five first-party pilot integration entries.
  This matches the 0.26.1 precedent where the agentbundle entry landed in
  `docs/product/changelog.md`.

### Regression

- [ ] AC28: `SKIP_SAST=1 make build-check` exits 0 after all changes.
- [ ] AC29: `python3 -m pytest packages/agentbundle/tests/ -q` exits 0 after all
  changes.
- [ ] AC30: `wc -l packs/AGENTS.md` ≤ 150 (CI enforces; verify after any edit).
- [ ] AC31: `wc -l AGENTS.md` ≤ 250 (CI enforces; verify after any edit).

## Assumptions

- **Technical:** `packs/core/.apm/skills/work-loop` exists at HEAD (verified: present).
- **Technical:** `packs/frontend-engineering/.apm/skills/frontend-engineering` exists
  at HEAD (verified: present). `packs/frontend-engineering/.apm/agents/frontend-reviewer.md`
  exists at HEAD (verified: present).
- **Technical:** `packs/governance-extras/.apm/skills/new-rfc` exists at HEAD
  (verified: present).
- **Technical:** `packs/desk-research/.apm/skills/desk-research` and
  `desk-research-project-synthesize` exist at HEAD (verified: present).
- **Technical:** `packs/product-engineering/.apm/skills/frame-intent` and
  `de-risk-intent` exist at HEAD (verified: present).
- **Technical:** `packs/architect/.apm/skills/architect-design` and `architect-review`
  exist at HEAD (verified: present).
- **Technical:** `contracts/pack.schema.json` and `agentbundle/_data/pack.schema.json`
  are byte-identical at HEAD (the D1 parity gate is active). The Wave 2 schema change
  must update both files in the same commit.
- **Technical:** The `agentbundle show` command reads `pack.toml` directly from the
  catalogue path via `load_pack_toml`; no migration of install-state files is needed
  to surface integrations in the primary path. The degrade path (installed-state
  fallback) does not surface integrations and is not extended in this wave.
- **Technical:** Version 0.27.0 is the next minor bump from 0.26.1; no other PR is
  racing to bump the same version number (verify before opening the PR).
- **Deferred:** The neutral `catalogue-index.json` integration view (D7) is Wave 4;
  this wave does not generate or update the index.
- **Deferred:** Marketing pack page rendering of integration relationships (D10) is
  Wave 7.
- **Deferred:** Cross-catalogue integrations are out of scope until registry-qualified
  identities exist (RFC-0076 D6 explicit deferral).
- **Deferred:** The "Journey format" placeholder section (section after 11) in
  `catalogue-authoring-standards.md` remains a placeholder; filled in Wave 4.
