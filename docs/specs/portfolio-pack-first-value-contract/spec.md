# Spec: portfolio-pack-first-value-contract

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md) <!-- authored at EXECUTE start -->
- **Constrained by:** RFC-0064 Amendment #4 (2026-07-21) — cross-pack first-value adoption overlay; RFC-0031 (pack.toml as source of truth + lossy projection model); RFC-0011 (optional `pack.toml` fields under a contract bump)
- **Brief:** none
- **Discovery:** none
- **Contract:** `docs/contracts/pack.schema.json`
- **Shape:** mixed <!-- schema extension + data migration (17 pack.toml files) + new validator tool -->

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

Pack audience, surface, install, verification, recovery, first-task, artifact,
tutorial, and next-action facts are currently scattered across `pack.toml`
descriptions, README prose, per-pack guides, journey maps, and generated
manifests. No single record owns them, so any one fact can silently drift
between documents and between packs.

This spec authors the **pack first-value contract**: a single `[pack.first-value]`
section added to every pack's `pack.toml` that becomes the one authoritative
record for all audience, surface, and first-run facts. Public consumers (pilot
tutorials, the agentbundle install handoff, future rollout artifacts) are either
generated from this record or parity-checked against it. Corrections happen in
one place; consumer drift is detected at build time.

Two internal-only obligation levels govern the required fields:

- **Level A** — baseline for every published pack. Declares audience posture,
  verified surfaces, prerequisites, install verification, and recovery. Internal
  working label; never becomes public copy.
- **Level B** — additive for packs with non-technical or mixed audiences.
  Level A plus: starter task, starter prompt, expected result, and next action.
  `tutorial` is a Level B field, but is omitted until the pilot spec that creates
  the tutorial file ships (see AC5). `safety-gate` is additionally required for
  packs that declare `writes-to-repo = true`. Internal label only.

The **proposed Level B set** (ratified in this spec's Acceptance Criteria):
`architect`, `atlassian`, `converters`, `desk-research`, `experience-design`,
`figma`, `governance-extras`, `product-engineering`, `product-strategy`,
`user-guide-diataxis`.

The **Level A-only set**: `catalogue-curation`, `contracts`, `core`,
`credential-brokers`, `iac-terraform`, `monorepo-extras`, `release-engineering`.

The implementing PR authors the contract schema, migrates all 17 current packs,
and adds a build-check validator. The three downstream pilot specs
(`portfolio-first-run-pilot-architect`, `portfolio-first-run-pilot-figma`,
`portfolio-first-run-pilot-governance-extras`) each author their pack's tutorial,
add the `tutorial` field pointing to it, and independently verify the contract
against live evidence — those are the real consumers and the independent parity
proof. This spec's job is to make all three pilot contracts complete enough to
be immediately unblocked.

## Boundaries

### Always do

- **Extend `pack.toml`, not a sidecar file.** The `[pack.first-value]` section
  lives in the same `pack.toml` as all other pack metadata — same source of
  truth, same projection pipeline. A companion TOML or YAML sidecar introduces
  a second file to maintain.
- **Keep every field optional in `pack.schema.json`.** A pack that omits
  `[pack.first-value]` entirely must still pass schema validation. The validator
  (`tools/lint-first-value-contract.py`) is the enforcement surface, not the
  JSON schema; the schema only types the fields that are present.
- **Enforce via the new validator, not the adapter-contract bump.** The
  `[pack.first-value]` section is catalogue-internal (not projected to adapter
  paths such as `plugin.json`). No adapter-contract version bump is needed.
  Wire `lint-first-value-contract.py` into `make build-check` as the enforcement
  gate.
- **Populate all 17 packs in the same PR.** A partial migration that leaves
  some packs un-contracted leaves the "inventory reconciles" AC open. All
  pack-version bumps and changelog entries land together.
- **Write only what is currently true.** Every field must reflect the pack's
  actual supported behaviour today. Do not write aspirational values — if the
  recovery procedure is not yet documented, write a brief honest description; do
  not copy from another pack's better-documented path.
- **Keep field values short and machine-readable.** `audience-posture` is a
  single vocabulary word; `surfaces` is a list of adapter names; `prerequisites`
  is a list of short strings. Long prose belongs in the tutorial doc.
- **Only declare `tutorial` when the file exists.** The validator resolves the
  path relative to the repo root and exits 1 if the file is absent. Leave
  `tutorial` absent until the pilot spec that creates the file ships.
- **Edit canonical pack sources only.** `packs/<pack>/.apm/` (or `packs/<pack>/`
  for seeds and pack.toml); run `make build-self FORCE=1` after to propagate
  pack.toml changes to the dist routes.
- **Bump each modified pack's version and add a changelog entry.** Adding
  `[pack.first-value]` is a non-cosmetic pack change. Each of the 17 packs
  gets a patch bump; `docs/product/changelog.md` gains one `[Unreleased]`
  entry covering the migration.

### Ask first

- **Level B membership change.** If inspection reveals a pack should be Level B
  but is not on the proposed list (or vice versa), surface the finding and wait
  for confirmation before changing membership. The proposed set is from
  Amendment #4; any delta is a governance call.
- **`writes-to-repo` and `safety-gate` ambiguity.** For Level B packs where it
  is unclear whether the canonical first task writes to the user's repo (e.g. a
  pack that can do either), ask whether to declare `writes-to-repo = true` or to
  scope the canonical first task to a read-only action.
- **Additional `audience-posture` vocabulary.** The spec defines three values
  (`"non-technical"`, `"mixed"`, `"technical"`); if a pack genuinely does not
  fit, surface the case rather than forcing a nearest-neighbour assignment.
- **New top-level section or field name changes.** The `[pack.first-value]`
  section name and all field names below are load-bearing (downstream specs
  reference them). Any rename is an RFC-level change.

### Never do

- **Project `[pack.first-value]` into `plugin.json` or `marketplace.json`.**
  These are internal obligation fields, not marketplace display metadata. They
  are not part of the lossy-projection surface.
- **Leave pack-version unchanged.** Every `pack.toml` that gains
  `[pack.first-value]` fields gets a patch-version bump.
- **Introduce adapter-contract version logic for this change.** No
  `[pack.adapter-contract].version` bump, no version-gated schema branch, no
  `test_contract.py` update scoped to this spec.
- **Make Level A/B labels visible to adopters.** They do not appear in READMEs,
  marketplace descriptions, or public guides. The labels exist for internal
  quality tracking only.
- **Create a `pack-first-value.toml` or any other sidecar file per pack.** One
  place, one file.
- **Declare a `tutorial` path that does not yet exist.** The build fails if the
  path is absent; an aspirational pointer breaks `make build-check`.
- **Author any pilot pack tutorial in this PR.** Tutorials ship in the pilot
  specs (`portfolio-first-run-pilot-architect`, etc.), not here. This PR
  populates the contract fields so those specs are immediately unblocked.
- **Duplicate first-value facts in README prose.** Pack README files may link
  to the guide home; they must not carry a separate inline table of
  audience/surface/prerequisite facts that would need to be kept in sync.

## Field reference

The `[pack.first-value]` section schema, expressed as TOML with types noted
inline. All fields are optional in `pack.schema.json`; the validator enforces
presence for Level A and Level B fields as described below.

```toml
[pack.first-value]
# ── Level A (required for all 17 packs) ─────────────────────────────────────

# One of: "non-technical" | "mixed" | "technical"
# Setup posture of the intended audience — not professional sophistication.
# "non-technical"  = user is comfortable in a desktop IDE or web app but does
#                    not maintain a terminal workflow.
# "mixed"          = pack is useful to both technical and non-technical users.
# "technical"      = primary audience has a terminal/CLI workflow.
audience-posture = "..."

# List of adapter names where the first-value path is verified/supported.
# Must be a subset (⊆) of this pack's [pack.install].allowed-adapters.
# List only adapters the first-value path has been tested/transcribed against.
# At least one entry required; ≥ 1 enforced by the validator.
surfaces = ["claude-code", ...]

# List of prerequisites the user must have in place before first use.
# Empty list if none. Each entry ≤ 80 chars (one noun phrase or command name).
prerequisites = []

# Short description of how to verify the pack is working after install.
# One sentence; ≤ 160 chars.
# For non-technical/mixed packs: describe a check that needs no terminal knowledge.
verification = "..."

# Short description of what to do when the first use fails.
# One to two sentences; ≤ 300 chars. Be specific about the most common failure.
recovery = "..."

# ── Level B flag ─────────────────────────────────────────────────────────────

# Absent = false. Set to true to declare Level B obligations.
# When true, all Level B required fields below must be populated.
level-b = true

# ── Level B fields (required when level-b = true) ────────────────────────────

# One plain-language sentence; ≤ 120 chars.
# Written from the user's outcome perspective, not the skill's action.
starter-task = "..."

# Copy-ready verbatim prompt the user can paste into the agent; ≤ 500 chars.
# No <placeholder> tokens — any <word> token causes the validator to exit 1.
# The complete prompt must be actionable without modification.
starter-prompt = "..."

# Brief description of the artifact or decision the user will see at the end
# of the starter task; one to two sentences; ≤ 200 chars.
expected-result = "..."

# Plain-language next step after the starter task; one sentence; ≤ 120 chars.
next-action = "..."

# ── Level B tutorial field (optional; enforced when present) ─────────────────

# Relative path from repo root to the step-by-step tutorial file.
# Omit until the pilot spec that creates the file ships.
# When present: must resolve to an existing .md file (validator exits 1 if absent).
tutorial = "docs/guides/<pack>/tutorials/<slug>.md"

# ── Level B write-operation fields (required when writes-to-repo = true) ─────

# Absent = false. Set to true when ALL of:
#   (1) the starter task writes a shared governance or structural record (an ADR,
#       a docs scaffold, a configuration file other team members depend on); AND
#   (2) the pack's skill shows a preview-confirm gate before the write runs.
# File creation that is personal workspace output (architecture notes, exports,
# research scaffolds) does not set this flag — only shared, committed records.
# When true, safety-gate is required by the validator.
writes-to-repo = true

# One to two sentences describing the preview-confirm gate before any write
# is made; ≤ 200 chars. Required when writes-to-repo = true.
safety-gate = "..."
```

### Vocabulary constraints

| Field | Type | Level | Required by validator | Vocabulary / constraints |
|---|---|---|---|---|
| `audience-posture` | string | A | always | one of: `"non-technical"` \| `"mixed"` \| `"technical"` |
| `surfaces` | array of strings | A | always | ⊆ `[pack.install].allowed-adapters`; ≥ 1 entry required |
| `prerequisites` | array of strings | A | always | may be empty; each entry ≤ 80 chars |
| `verification` | string | A | always | ≤ 160 chars |
| `recovery` | string | A | always | ≤ 300 chars |
| `level-b` | bool | — | — | absent = false |
| `starter-task` | string | B | when `level-b = true` | ≤ 120 chars |
| `starter-prompt` | string | B | when `level-b = true` | ≤ 500 chars; no `<word>` token |
| `expected-result` | string | B | when `level-b = true` | ≤ 200 chars |
| `next-action` | string | B | when `level-b = true` | ≤ 120 chars |
| `tutorial` | string | B | when present | resolves to an existing `.md` file |
| `writes-to-repo` | bool | B | — | absent = false |
| `safety-gate` | string | B | when `writes-to-repo = true` | ≤ 200 chars |

## Testing Strategy

`lint-first-value-contract.py` is the primary enforcement mechanism — a new
tool in `tools/`, wired into `make build-check`. It is **TDD-driven** with
a paired test file `tools/test-lint-first-value-contract.py`.

**TDD (unit, per validator rule):**

Positive:
- Level A fields present for all packs → exits 0.
- `level-b = true` with all required Level B fields present → exits 0.
- `tutorial` present and pointing to an existing file → exits 0.
- `writes-to-repo = true` with `safety-gate` present → exits 0.
- A `surfaces` entry that matches an entry in `[pack.install].allowed-adapters` → exits 0.
- A pack omitting `tutorial` (absent field) → exits 0 (field is optional).
- No `packs/` directory → exits 0 (nothing to lint).

Negative fixtures (at minimum):
- Pack with no `[pack.first-value]` section at all → exits 1 with pack name.
- Pack with `[pack.first-value]` present but `audience-posture` absent → exits 1 with field name + pack name.
- `audience-posture` outside the three-value vocabulary → exits 1.
- `surfaces` is an empty list → exits 1 (zero entries not allowed).
- A `prerequisites` entry > 80 chars → exits 1.
- `verification` > 160 chars → exits 1.
- `recovery` > 300 chars → exits 1.
- `level-b = true` with any required Level B field absent (e.g. `starter-task` missing) → exits 1.
- `starter-task` > 120 chars → exits 1.
- `starter-prompt` containing a `<placeholder>` token (pattern: `<[a-zA-Z][a-zA-Z0-9 _-]*>`) → exits 1.
- `starter-prompt` > 500 chars → exits 1.
- `expected-result` > 200 chars → exits 1.
- `next-action` > 120 chars → exits 1.
- `tutorial` declared but path absent on disk → exits 1 with pack name + path.
- `tutorial` declared but path is not a `.md` file (e.g. a `.txt` file) → exits 1.
- `tutorial` declared but path resolves to a directory, not a file → exits 1.
- `writes-to-repo = true` with `safety-gate` absent → exits 1.
- `safety-gate` > 200 chars → exits 1.
- `surfaces` entry not present in `[pack.install].allowed-adapters` → exits 1.

**Pack enumeration:** the validator globs `packs/*/pack.toml` and asserts every
found pack has `[pack.first-value]`. It does NOT maintain a hardcoded name list.
The Level B membership check uses the names declared in each pack's `level-b`
field, not a hardcoded set in the tool.

**Goal-based checks (build-pipeline):**

- `make build-check` green with all 17 packs migrated.
- `python3 tools/lint-first-value-contract.py --root .` exits 0.
- `python3 tools/test-lint-first-value-contract.py` exits 0 with all negative
  fixtures rejected.
- `make build-self FORCE=1` exits 0 after all 17 `pack.toml` files are edited.
- Each of the 17 packs passes `agentbundle validate <pack>` (schema-valid
  against `docs/contracts/pack.schema.json`).

## Acceptance Criteria

### AC1 — Schema extended (both copies)

- [x] Both `docs/contracts/pack.schema.json` and `packages/agentbundle/agentbundle/_data/pack.schema.json` accept an optional `[pack.first-value]`
  section under `[pack]`. All fields listed in the Field Reference are typed
  correctly (`audience-posture`, `surfaces`, `prerequisites`, `verification`,
  `recovery`, `level-b`, `starter-task`, `starter-prompt`, `expected-result`,
  `next-action`, `tutorial`, `writes-to-repo`, `safety-gate`). A pack omitting
  `[pack.first-value]` entirely still validates.
- [x] Neither schema copy marks any `[pack.first-value]` fields as
  required — enforcement is the validator's job, not the schema's.
- [x] Both copies carry `"additionalProperties": false` on the `first-value`
  object as a typo-guard (the `pack` object itself remains open).
- [x] `diff docs/contracts/pack.schema.json packages/agentbundle/agentbundle/_data/pack.schema.json` exits 0 (copies remain byte-identical, satisfying `test_pack_schema_copies_match`).

### AC2 — Validator authored and wired

- [x] `tools/lint-first-value-contract.py` exists; takes an optional `--root`
  argument (defaults to `.`; packs directory is `<root>/packs/`).
- [x] The validator:
  - Globs `<root>/packs/*/pack.toml` and enforces Level A fields present on every
    found pack.
  - Enforces Level B fields on every pack with `level-b = true`.
  - Enforces `safety-gate` on every pack with `writes-to-repo = true`.
  - Rejects any `surfaces` entry not in that pack's `[pack.install].allowed-adapters`
    (skips the subset check when the pack has no `allowed-adapters` in `[pack.install]`).
  - Rejects `audience-posture` outside the three-value vocabulary.
  - Enforces `surfaces` ≥ 1 entry.
  - Enforces per-entry `prerequisites` ≤ 80 chars.
  - Enforces all field length constraints from the Vocabulary table.
  - Rejects `starter-prompt` values containing `<word>` placeholder tokens
    (pattern: `<[a-zA-Z][a-zA-Z0-9 _-]*>`).
  - Enforces `tutorial` file existence when `tutorial` is declared (relative to
    `--root`).
  - Does **not** require `tutorial` to be present (optional Level B field).
- [x] `tools/test-lint-first-value-contract.py` exists; all positive and
  negative fixture cases from the Testing Strategy pass.
- [x] `make build-check` runs `lint-first-value-contract.py` and fails the
  build on exit non-zero.

### AC3 — Level A/B membership ratified

- [x] The following 10 packs declare `level-b = true` in `[pack.first-value]`:
  `architect`, `atlassian`, `converters`, `desk-research`, `experience-design`,
  `figma`, `governance-extras`, `product-engineering`, `product-strategy`,
  `user-guide-diataxis`.
- [x] The following 7 packs declare Level A only (`level-b` absent or `false`):
  `catalogue-curation`, `contracts`, `core`, `credential-brokers`,
  `iac-terraform`, `monorepo-extras`, `release-engineering`.
- [x] A comment above each pack's `[pack.first-value]` block states the
  membership rationale in one cold-start-sufficient sentence.

### AC4 — All 17 packs migrated

- [x] Every pack found by `packs/*/pack.toml` glob has a `[pack.first-value]`
  section with all Level A fields populated.
- [x] Every Level B pack has all required Level B fields populated.
- [x] Every pack with `writes-to-repo = true` declares `safety-gate`.
- [x] No pack declares `tutorial` pointing to a path that does not exist on disk.
- [x] Each modified pack has a patch-version bump in `pack.toml`.
- [x] `docs/product/changelog.md` `[Unreleased]` has one entry covering the
  17-pack migration.
- [x] `lint-first-value-contract.py` exits 0 against the migrated `packs/`.
- [x] Each pack still passes `agentbundle validate <pack>`.

### AC5 — Three pilot contracts ready to unblock downstream specs

- [x] Architect's `[pack.first-value]` is fully populated: Level A + Level B
  required fields (no `tutorial` — the architect pilot spec adds it).
  `audience-posture = "non-technical"`, `surfaces` contains at least
  `"claude-code"`, `prerequisites` is empty or documents any real prerequisite,
  `starter-task` names a no-terminal architecture outcome, `starter-prompt`
  is verbatim-pasteable.
- [x] Figma's `[pack.first-value]` is fully populated: Level A + Level B
  required fields. `prerequisites` declares the Figma token requirement.
  No `tutorial` (the figma pilot spec adds it). `starter-task` describes a
  safe read-only task against the user's own authorized file.
- [x] Governance-extras's `[pack.first-value]` is fully populated: Level A +
  Level B required fields + `writes-to-repo = true` + `safety-gate` describing
  the preview-confirm gate. No `tutorial` (the governance-extras pilot spec
  adds it).
- [x] `portfolio-first-run-pilot-architect`, `portfolio-first-run-pilot-figma`,
  and `portfolio-first-run-pilot-governance-extras` are each unblocked by this
  PR (their `needs = "work:spec/portfolio-pack-first-value-contract"` dependency
  is satisfied by this PR shipping). The pilot specs independently verify the
  contracts against live evidence and add the `tutorial` fields — that is the
  independent parity proof.

### AC6 — No consumer drift

- [x] One source change fails the build: removing a required Level A field from
  any `pack.toml` causes `make build-check` to exit non-zero (AC2 validator
  wiring).
- [x] One source-of-truth check: the three pilot packs' `starter-prompt` values
  are the sole copy of those prompts. Grep confirms no README or guide file
  carries the same verbatim prompt text outside of the tutorial itself (no
  duplicate that could drift separately).
- [x] No second hand-maintained inventory of first-value facts: grep confirms no
  `docs/guides/<pack>/README.md` or `packs/<pack>/README.md` carries a separate
  inline table of audience/surface/prerequisite facts that duplicates
  `[pack.first-value]` content.

## Assumptions

1. `pack.schema.json` does not set `additionalProperties: false` on the `[pack]`
   object — confirmed 2026-07-21; new optional fields are accepted without a
   schema rewrite.
2. No adapter-contract version bump is required. `[pack.first-value]` is
   catalogue-internal and is not projected to `plugin.json`, `marketplace.json`,
   or any per-adapter path. The enriched-pack-manifest spec (RFC-0031) bumped
   the contract only when adding *projected* fields; this spec adds none.
3. The current pack count is 17 — confirmed 2026-07-21 by `ls packs/`:
   `architect`, `atlassian`, `catalogue-curation`, `contracts`, `converters`,
   `core`, `credential-brokers`, `desk-research`, `experience-design`, `figma`,
   `governance-extras`, `iac-terraform`, `monorepo-extras`, `product-engineering`,
   `product-strategy`, `release-engineering`, `user-guide-diataxis`.
4. The architect pack already has a `docs/guides/architect/tutorials/` directory —
   confirmed 2026-07-21. The first-session tutorial is a new file; it ships in
   the `portfolio-first-run-pilot-architect` spec, not here.
5. `make build-check` is the correct integration point. It is the documented
   local preflight (AGENTS.local.md § Commands).
6. No tutorial files exist yet for figma or governance-extras. The `tutorial`
   field for both packs is left absent in this PR; the pilot specs populate it
   alongside the tutorial file they create. The validator tolerates an absent
   `tutorial` field (it only fails on a *declared* path that does not resolve).
8. `pack.schema.json` has two byte-identical copies (confirmed 2026-07-22):
   `docs/contracts/pack.schema.json` (source) and
   `packages/agentbundle/agentbundle/_data/pack.schema.json` (the copy
   `agentbundle validate` actually reads). Both must be edited identically.
   `test_pack_schema_copies_match` asserts equality; editing one breaks the test.
7. `writes-to-repo = true` criterion (resolved 2026-07-21): the flag applies when
   (1) the starter task writes a shared governance or structural record AND (2) the
   pack's skill provides a preview-confirm gate. Packs that create personal workspace
   outputs (architecture notes, generated exports, research scaffolds) do not set this
   flag. Under this definition only `governance-extras` and `user-guide-diataxis`
   declare `writes-to-repo = true` in this migration — matching RFC-0064 Amendment #4's
   explicit designation of governance-extras as the "preview-confirm write" archetype.

## Changelog

<!-- Add an entry under [Unreleased] in docs/product/changelog.md when this
     spec is implemented. Format: feature bullet, one line. -->
