# Plan: A schema for the catalogue release archive manifest

- **Spec:** [`spec.md`](spec.md)
- **Status:** Approved <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** RFC-0109 D5; `catalogue_tooling/archive.py` `_check_manifest_schema`, `_check_manifest_shape`, `_check_unit_entry_fields` (the accepted shape); `catalogue_tooling/package.py` `_generate_manifest` (what is written); `build/validate.py` (the in-house validator's keyword set); `contracts/catalogue-index.schema.json` (an existing member schema's conventions); `packages/agentbundle/tests/unit/test_catalogue_archive_unit_digests.py` `_SHAPES` (the verifier's malformed-shape table)

## Approach

Write the schema from the verifier's checks, using only keywords the package
validator supports. Bundle it like the other members and register it in the
manifest. Prove agreement in both directions in a package test module that drives the real packager and the real manifest check, and in a roster test that uses a standard draft 2020-12 validator. Make the verifier
reject a boolean `schema`, and correct the guide. The riskiest part is
expressing string-or-object `profiles[]` items without `oneOf`.

## Constraints

- RFC-0109 D5 and its 2026-10-21 errata entry: the schema matches what the verifier accepts under standard draft 2020-12 semantics, after the verifier also rejects a boolean `schema`.
- The package validator supports `type`, `properties`, `required`, `additionalProperties`, `enum`, `pattern`, `items`, `minItems`, `maxItems`, `contains`, and `if`/`then`/`else`. It has no `oneOf`, `anyOf`, `const`, `null` type, `$ref` or `format`.
- Shipped package source and package tests cite no RFC, ADR or spec identifiers.
- `packages/AGENTS.md`: package tests read no repository paths; they load the schema through `_load_bundled_json`.

## Construction tests

The package-validator agreement tests live in one new package module (T2); the standard-validator agreement test lives in one roster module (T2b).

## Durable-output map

| Spec durable output | Task |
| --- | --- |
| `contracts/catalogue-manifest.schema.json`, `contracts/catalogue-spec.toml`, `contracts/README.md` | T1 |
| `docs/guides/reference/catalogue-archive.md` | T3 |
| the six release files | T4 |

## Design (LLD)

### Data & schema

Top level: `"x-spec": "docs/specs/catalogue-manifest-schema"`, `$schema` draft
2020-12, `"$id": "catalogue-manifest.schema.json"`, `title`, a `description` carrying
the shape-only statement spec AC 8 requires,
`type: object`, `required: [schema, bundle, release, generated_at, files, packs]`,
no `additionalProperties`.

- `schema`: `{type: integer, enum: [1, 2]}`. Its `description` says the package's validator rejects an integer-valued number such as `1.0` that standard validators and `catalogue verify` accept.
- `bundle`, `release`, `generated_at`: `{type: string}`.
- `files`: `{type: array, items: {type: object, required: [path, sha256], properties: {path: {type: string}, sha256: {type: string}}}}`.
- `packs`: `{type: array, items: {type: object, required: [name, version], properties: {name, version, path, digest: {type: string}}, if: {required: [digest]}, then: {required: [path]}}}`.
- `profiles`: `{type: array, items: {if: {type: string}, else: {type: object, required: [name], properties: {name, path, digest: {type: string}}, if: {required: [digest]}, then: {required: [path]}}}}`.
- The nullable keys `catalogue package` writes (`source_revision`, `minimum_agentbundle_version`, `catalogue_name`, `catalogue_display_name`, `marketplace_digest`) and the other unchecked keys (`adapter_contract_version`, `pack_schema_version`) are described in `description` text only. They are not typed, because the verifier does not check them.

`$id` stays a bare filename until S4 mints absolute identifiers.

### Behavior & rules

`_check_manifest_schema` changes `schema not in (1, 2)` to
`isinstance(schema, bool) or schema not in (1, 2)`, so `true` reports
CAT-V-ARC-011 and `1.0` stays accepted, as draft 2020-12 treats it as an
integer. No other verifier line changes.

## Tasks

### T1: Schema file, bundling and registration

**Depends on:** none

**Tests:** goal-based.

**Approach:**
- Write the schema per *Data & schema*.
- Copy it to `packages/agentbundle/agentbundle/_data/`.
- Add its `member` row to `contracts/catalogue-spec.toml`, and a row under `Specification members` in `contracts/README.md`.
- Run `tools/catalogue/sync_contract_inventory.py --write`.
- Update what S1's tests pin in `tools/test_contract_parity.py`: `catalogue-manifest.schema.json` joins the ordered member list (lines 129–133) at the position of its `catalogue-spec.toml` row, and `len(rows)` changes from 20 to 21.

**Done when:** `python tools/catalogue/check_contract_parity.py` and `sync_contract_inventory.py --check` exit 0, `python -m pytest tools/test_contract_parity.py tests/roster/test_contract_backward_registry.py -q` passes, and `public-contracts.txt` has 19 names.

### T2: Agreement tests and the verifier's boolean check

**Depends on:** T1

**Tests:** `packages/agentbundle/tests/unit/test_catalogue_manifest_schema.py` (new). It loads the schema with `_load_bundled_json("catalogue-manifest.schema.json")` and validates with `agentbundle.build.validate.validate`.
- AC 2: run `catalogue init` and then `catalogue package` in `tmp_path`, once on the starter catalogue and once after adding one pack and one profile. Extract `catalogue-manifest.json` and assert no schema errors.
- AC 3: the four legacy shapes each validate.
- AC 4: `from tests.unit.test_catalogue_archive_unit_digests import _SHAPES, _base_manifest`, as other package tests share helpers. Build each case as `_SHAPES[name](copy.deepcopy(_base_manifest()))`, add the CAT-V-ARC-011 cases, and assert each fails the schema.
- A module-level `AGREEMENT_CASES: dict[str, dict]` holds the one case definition T2 and T2b share: the AC 3 legacy shapes, the AC 4 cases (each `_SHAPES` mutation applied to a deep copy of `_base_manifest()`, plus the CAT-V-ARC-011 cases), and `schema: true`, `schema: 1.0` and `schema: 3`.
- AC 6 (package-validator equality): for every `AGREEMENT_CASES` entry except `schema: 1.0`, assert that `bool(schema errors)` equals `bool(ARC-011 or ARC-019 diagnostics from archive._check_manifest_schema(manifest))`. A separate case pins `schema: 1.0`: the package validator rejects it and the verifier accepts it.
- AC 7: write archives with the `_write` helper from the same module. `verify_archive` reports CAT-V-ARC-011 for `schema: true` and none for `schema: 1.0`.
- AC 9: extra keys at the top level and in items validate.
- AC 8: the schema's top-level `description` contains the shape-only, not-verification and not-origin statements, and the phrase "separately authenticated channel".

```python
# stub: true — red until the schema is bundled
def test_bundled_schema_loads() -> None:
    from agentbundle.build.main import _load_bundled_json
    schema = _load_bundled_json("catalogue-manifest.schema.json")
    assert schema["type"] == "object"
```

**Approach:** change `_check_manifest_schema` per *Behavior & rules*.

**Done when:** the new module passes, and the existing archive and unit-digest suites pass.

### T2b: Standard-validator agreement

**Depends on:** T2

**Tests:** `tests/roster/test_catalogue_manifest_schema_parity.py` (new), following the existing roster schema-parity tests such as `tests/roster/test_workspace_entry_contract.py`. Validate with `jsonschema.Draft202012Validator` against `contracts/catalogue-manifest.schema.json`. Import the shared case table with `from tests.unit.test_catalogue_manifest_schema import AGREEMENT_CASES`; the root `pyproject.toml` `pythonpath` already includes `packages/agentbundle`, so `tests.unit` resolves to the package's test package. Assert that validity equals the verifier's verdict for every case (AC 5).

**Approach:** add a named step for the file in `.github/workflows/build-check.yml`'s `gate-main` job above the bulk roster step, its `STEP_DISPOSITION` entry `LOCAL("test-after-build-check")` and its name in `_GATE_MAIN_CHECKS` in `tools/lint-ci-parity.py`. The test names no `docs/specs/<slug>` literal.

**Done when:** `python -m pytest tests/roster/test_catalogue_manifest_schema_parity.py -q` and `python3 tools/lint-ci-parity.py` pass.

### T3: Guide correction

**Depends on:** T1

**Tests:** add a test to `tools/test_catalogue_tooling_docs.py` that reads `docs/guides/reference/catalogue-archive.md` and asserts: the phrase "the provenance evidence" is absent; the guide says the sidecar and descriptor prove only that the bytes arrived intact; it says origin needs a sidecar or signature obtained through a separately authenticated channel; it says a schema-valid manifest is not evidence of origin; and it links `contracts/catalogue-manifest.schema.json` (AC 10).

**Approach:** rewrite `catalogue-archive.md` lines 90–92 to state the RFC-0109 D5 provenance limits. S3 repoints the link to the site.

**Done when:** `python -m pytest tools/test_catalogue_tooling_docs.py -q` passes, and `python3 tools/validate_guides.py` passes.

### T4: Release files

**Depends on:** T2

**Tests:** goal-based: `python -m agentbundle --version` prints `agentbundle 0.55.0 (spec 0.18)` (AC 12).

**Done when:** the six files in `docs/guides/how-to/cut-a-package-release.md` move from 0.54.0 to 0.55.0, with a `changelog.d` fragment. `tests/roster/test_okf_catalogue_discovery.py` and `tests/roster/test_agentbundle_governance_markers.py` pass.

## Rollout

One PR, stacked on S1's PR. Reversible: a new file, plus one verifier tightening
that no packaged manifest reaches, because `catalogue package` always writes the
integer 2. Nothing is published to the site until S3.

## Risks

- The roster agreement test imports package test helpers through the root `pythonpath`; a change to that setting would break the import loudly, not silently.

## Changelog

- 2026-10-21: spec approved by eugenelim
- 2026-10-21: plan approved by eugenelim
