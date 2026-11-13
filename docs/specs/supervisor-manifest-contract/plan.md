# Plan: Supervisor manifest contract

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting
- **Repository anchors:** `contracts/delivery/execution-request.v1.schema.json` (the JSON Schema 2020-12 style; its required keys include `spec`, which the five-key envelope drops because a sibling's subject is not always a spec directory, per page 05 line 220); `tests/roster/test_delivery_contract_bundle.py` (the schema-set completeness test and the validator setup); `packs/core/tests/skills/new-spec/` (where a core-pack schema test lives); page 05 and page 01 of `docs/architecture/unattended-delivery-runner/` (the manifest fields and the schema path). Named uncertainty: the stdlib schema checker that page 01 section 8 describes does not exist yet, so keyword support is checked only against the full validator here.

> **Plan contract:** this is the implementation strategy. After approval, a
> change needs an **amendment** only when it touches the spec's protected
> sections or its `Terminal Intent`. A change to tasks, tests, design, or
> approach is an in-envelope working-plan change while no attempt is open.

## Approach

Add two JSON Schemas to the core pack's `new-spec` assets and copies under `contracts/ferryman/` that add an `x-spec` back-pointer, a pack test that exercises the pack originals, a roster test that compares the copies, and the registrations, self-host projections and core release records. The manifest schema is closed at `manifest_version` 1, so a later field is a version bump. The envelope schema carries the five shared keys and leaves `kind` and `stage` open strings, since each supervisor owns its own enums. The riskiest part is the manifest field set, which pages 01, 02, 03 and 05 and RFC-0115 describe only in part, so each field is grounded below.

## Constraints

- ADR-0162 D1 (six commands), D2 (the manifest lists request kinds and a controller refuses an unknown manifest or version), D3 (delegation is another supervisor's `park` or `start`) and D7 (the core pack owns the manifest and envelope).
- Page 05 line 271: the core pack owns the schema and a copy sits at `contracts/ferryman/supervisor-manifest.v1.schema.json`.
- ADR-0144 (pinned supervisor files) and ADR-0163 D3: nothing under `packs/core/.apm/skills/work-loop/` changes.
- RFC-0115 D3: argv comes only from a controller's built-in descriptors, so the manifest carries no command line.
- `packs/AGENTS.md`: shipped pack content carries no internal-governance citation, a non-cosmetic pack update bumps `pack.toml` and `plugin.json` together, and `tools/lint-pack-test-boundary.py` keeps a pack test inside its pack.

## Construction tests

**Integration tests:** none beyond per-task tests.
**Manual verification:** none.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Interface compatibility: the schemas, the copies, README row, pack and roster tests | T1, T2, T3 | the pack test and the roster test run by name | both runs green, copies equal apart from `x-spec` |
| Current architecture: pages 01, 02 and 05 name the envelope file, the paths, the count and the manifest location | T3 | the pages name `supervisor-request-envelope.v1` and the shipped paths | no page names another path, count or location |
| Release history: the core version, its changelog fragment and the self-host projections | T4 | `python3 tools/changelog.py validate` and the self-host drift check | the changelog validates and `make build-self` is clean |

## Design (LLD)

### Interfaces & contracts

The manifest is TOML on disk and is parsed to a mapping before validation, so the schema describes that mapping. Traces to: AC-0001 to AC-0020 · `contracts/ferryman/supervisor-manifest.v1.schema.json`.

- Required: `manifest_version` (the integer 1), `id` and `subject_kind` (lowercase identifiers), `commands` (exactly the six names, each once, in any order; ADR-0162 D1), `request_kinds` (page 01 line 59) and `pinned_files` (page 05b line 168).
- A lowercase identifier is ASCII `a` to `z`, digits and hyphens, starting with a letter. The Python validator's `pattern` keyword uses `re.search`, where `$` also matches before a final newline, so each pattern also refuses a value that ends in a newline, and a test case covers it. `implementation-discovered`: the exact way to refuse the trailing newline (a second `not` pattern or a character class that excludes control characters), settled by the case failing red.
- `id` is also refused when it is `work-supervisor`, the id whose descriptor the controller holds (page 02), with or without a trailing newline.
- `request_kinds` is a non-empty object keyed by a lowercase-identifier kind name, so a duplicate name cannot occur (TOML refuses a repeated table key). Each entry is closed and requires `modes`, a non-empty array of unique values from `headless`, `attach`, `session`, `supervisor-run`, `ferryman-run` and `human`. The values come from the request-kind tables on page 05 (lines 99 to 105 and 132 to 139) and the `session` mode on page 05 line 161. `consent` and `human-decision` may list only `human` (page 05 lines 105, 173 and 211; page 03 line 78), `delegate-verb` only `ferryman-run`, and no other kind may list `human` or `ferryman-run`.
- `pinned_files` is a non-empty array of unique strings, each in the portable relative form: non-empty `/`-separated segments of ASCII letters, digits, `_`, `.` and `-`, no segment starting with `.`, no trailing newline. The form rules out an empty entry, an empty middle or trailing segment, a leading `/` or `\`, a backslash, a drive letter, `~`, a non-ASCII letter, and `.` or `..` segments in one pattern. Paths resolve from the directory that holds the manifest, which is the skill root (page 02 line 225 says "beside the script", and T3 corrects it).
- Optional: `delegates_to` (a non-empty array of unique closed entries with a `supervisor` identifier and a `command` of `park` or `start`; ADR-0162 D3, page 05 line 221) and `max_width` (an integer of at least 1, the widest `next --width N` the supervisor accepts, with absent meaning 1; page 05 line 223). `delegates_to` is present exactly when a `delegate-verb` request kind is listed.
- `additionalProperties` is false at the top level and inside a request kind and a delegation, and the allowed keys are the sets AC-0014 lists.
- A TOML float such as `1.0` reads as an integer under JSON Schema 2020-12, so the schema cannot refuse it; the criteria refuse non-integral values and a Follow-on assigns the float rule to the controller's loader.
- Assumption this rests on: no consumer needs a field the pages did not name; if the build shows one does, it is a new `manifest_version`.

The envelope schema holds `schema_version` (the integer 1), `request_id` (a non-empty string of at most 512 characters), `run_id` (a non-empty string of at most 128 characters), `kind` and `stage` (non-empty strings), all required, with `additionalProperties` open so a supervisor adds its own keys. The two bounds are those of `contracts/delivery/execution-request.v1.schema.json`. Page 05 line 220 describes it as the existing envelope with each sibling defining its own `stage` enum and per-kind schemas; the five keys drop `spec`, which the work supervisor's `execution-request.v1` requires because its subject is a spec directory. Traces to: AC-0021 to AC-0025 · `contracts/ferryman/supervisor-request-envelope.v1.schema.json`.

Both schemas use `$schema` draft 2020-12. The pack originals carry a `description` that cites no record. The `contracts/ferryman/` copies add one `x-spec` entry naming this spec directory, as `contracts/delivery/` schemas do. The refresh step is to edit the pack original and copy it to `contracts/ferryman/`, then add `x-spec`; AC-0026 catches drift.

Owned by: T1, T2

### Failure, edge cases & resilience

The pack test builds each invalid case from a valid base by changing one field, so each rule fails alone. Each path rule has one case per escape form: a leading `/`, a backslash, a drive letter, `~`, an empty entry, an empty middle segment, a trailing `/`, a non-ASCII letter, a trailing newline, and a `..` segment at the start, in the middle and at the end. Each identifier rule has an uppercase, an underscore, a leading-digit, a slash, a non-ASCII and a trailing-newline case. Each integer rule has a non-integral case. Traces to: AC-0005 to AC-0020, AC-0022 to AC-0025.

Owned by: T1, T2

### Dependencies & integration

The roster test reads the pack copies and the `contracts/ferryman/` copies and compares them with the `x-spec` entry removed from the second; the pack test also scans each pack original for an ADR, RFC, spec or `docs/` reference. Traces to: AC-0026, AC-0027, AC-0028.

Owned by: T3

## Tasks

### T1: Manifest schema

**Depends on:** none

**Touches:** `packs/core/.apm/skills/new-spec/assets/supervisor-manifest.v1.schema.json`, `packs/core/tests/skills/new-spec/test_supervisor_manifest_schema.py`

**Tests:**
- A representative manifest passes (AC-0001), a manifest with only the required keys passes (AC-0002), each permitted delegation command passes (AC-0003), a request kind with several modes passes (AC-0004). One invalid variant per rule fails: versions 0, 2 and 1.5 (AC-0005), each required key missing in turn (AC-0006), a missing, a repeated and a seventh command (AC-0007), an empty, a repeated and an unknown mode (AC-0008), `consent` as `headless`, `consent` as `session`, `human-decision` as `attach`, `delegate-verb` as `headless`, `review-round` as `human` (AC-0009), a delegation with command `report` and one with no `supervisor` (AC-0010), `delegates_to` without a `delegate-verb` kind and the reverse (AC-0011), an empty `delegates_to` (AC-0012), a repeated delegation (AC-0013), an extra key at each of the three levels, including `argv` at the top (AC-0014), `max_width` 0 and 1.5 (AC-0015), one case per path escape form (AC-0016), an empty and a repeated `pinned_files` (AC-0017), the identifier cases (AC-0018), `id` `work-supervisor` and `work-supervisor` plus a newline (AC-0019), an empty `request_kinds` table (AC-0020). Mode: TDD, drive the repository's JSON Schema validator over the schema file.

**Done when:** the T1 tests for AC-0001 to AC-0020 pass.

### T2: Request envelope schema

**Depends on:** none

**Touches:** `packs/core/.apm/skills/new-spec/assets/supervisor-request-envelope.v1.schema.json`, `packs/core/tests/skills/new-spec/test_supervisor_manifest_schema.py`

**Tests:**
- A request with the five keys and extra keys passes (AC-0021); a request missing each key fails in turn (AC-0022); `schema_version` 2 and 1.5 fail (AC-0023); a `request_id` or `run_id` that is null, an integer, empty, or over its bound fails (AC-0024); an empty `kind` and an empty `stage` each fail (AC-0025). Mode: TDD.

**Done when:** the T2 tests for AC-0021 to AC-0025 pass.

### T3: Copies, citations and registration

**Depends on:** T1, T2

**Touches:** `contracts/ferryman/supervisor-manifest.v1.schema.json`, `contracts/ferryman/supervisor-request-envelope.v1.schema.json`, `tests/roster/test_ferryman_contract_copies.py`, `packs/core/tests/skills/new-spec/test_supervisor_manifest_schema.py`, `contracts/README.md`, `docs/architecture/unattended-delivery-runner/01-contracts-and-data.md`, `docs/architecture/unattended-delivery-runner/02-install-trust-and-detection.md`, `docs/architecture/unattended-delivery-runner/05-supervisors-and-gates.md`

**Tests:**
- Each pack schema equals its `contracts/ferryman/` copy once `x-spec` is removed (AC-0026); every pack supervisor schema has a copy and no `supervisor-*` file in the folder lacks a pack original (AC-0027); each pack schema carries no ADR, RFC, spec or `docs/` reference (AC-0028). Mode: goal-based.
- Each `contracts/ferryman/` copy carries an inline `x-spec` entry, the README row marks both as copies of the pack originals, page 01 lists the envelope and updates the contract count, page 02 places the manifest at the skill root, page 05 names the envelope file and its path, and `make precheck` stays green with the new folder.

**Done when:** the T3 tests for AC-0026 to AC-0028 pass, the README, `x-spec` and page edits are in, and `make precheck` is clean.

### T4: Core release records and projections

**Depends on:** T1, T2

**Touches:** `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`, `docs/product/changelog.d/`, `.claude/skills/new-spec/assets/`, `.agents/skills/new-spec/assets/`

**Tests:**
- `python3 tools/changelog.py validate` passes, the core release check in `make precheck` accepts the version with `pack.toml` and `plugin.json` matching, and the self-host projections of the two new assets are committed so the self-host drift check is clean. Mode: goal-based.

**Done when:** the T4 changelog validation, the core release check and the self-host drift check pass, with the core version one patch above the version on `main` at merge.

## Rollout

Delivery is one change with no flag. Rollback is deleting the assets, the copies, the tests, the projections and the registrations, since no consumer exists until the supervisors ship. A core pack release carries the assets to adopters, and no consumer reads them before E1. The `new-spec/evals/` harness is unchanged because the assets are inert data that change no skill behavior (the Assumptions record this). No infrastructure, external system or deployment ordering applies.

## Risks

- The field set may miss something a supervisor needs. Mitigation: the first two manifests are built against these schemas, and a missing field becomes a new `manifest_version`.
- A hostile manifest may try to widen authority within the schema. Mitigation: the reserved-kind, delegation, key-closure and path rules here, and the controller-side controls the Follow-ons name.
- The pack test and the roster test are in no pull-request check. Mitigation: the Assumptions name a targeted run, `make precheck --with-tests` and one corpus dispatch as closeout evidence.
- The controller's stdlib checker may skip a keyword the schemas use, and the full validator reads a TOML float as an integer. Mitigation: Follow-ons require the checker to refuse unsupported keywords, add a differential test, and give the loader the float rule.
- The sources do not say which of a kind's listed modes a request uses. Mitigation: a Follow-on assigns the choice to the controller's configuration in phase P0.

## Changelog
