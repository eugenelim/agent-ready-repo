---
slug: catalogue-spec-manifest
title: "Catalogue specification manifest and bundled-only contract loading (RFC-0109 S1)"
status: Implementing
---

# Spec: Catalogue specification manifest and bundled-only contract loading

- **Status:** Implementing <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [RFC-0109](../../rfc/0109-catalogue-specification-publication.md) D1, D7 check 1 and S1; [RFC-0076](../../rfc/0076-catalogue-contracts-composition-semantics-discovery.md) D1 (authority model, no catalogue-local override)
- **Contract:** `contracts/catalogue-spec.toml`
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Outcome`, `What Changes`, `Durable Outputs`, `Follow-ons` and
> `Assumptions` are working material.

**Mode:** full. It changes a guarding control: which contract files the CLI
enforces, and whether a file in or above a catalogue can replace one.

## Outcome

Maintainers get one file that says which contracts form the catalogue
specification, which other contracts the CLI bundles, and which are vendored
from upstream. Adopters get a CLI that enforces only its own bundled contract
copies and stops with a named error when one is missing, whatever `contracts/`
folder sits in or above their catalogue.

## What Changes

- New manifest naming every bundled contract with one role, `member`, `bundled`
  or `vendored`, plus an empty release table — `contracts/catalogue-spec.toml`
- `public-contracts.txt` is written from the manifest's `member` and `bundled`
  rows instead of from folder position — `tools/catalogue/sync_contract_inventory.py`,
  which also owns the manifest loader
- The parity gate reads the manifest. It also refuses an unlisted top-level
  contract and a README row filed under the wrong role — `tools/catalogue/check_contract_parity.py`
- `contracts/README.md` groups its file table into role sections
- Every contract load site in `agentbundle` reads the bundled `_data/` copy
  only, and no site falls back to a `contracts/` folder. The plan's
  *Load-site inventory* lists every site
- The two sites that read a catalogue-side file first change behaviour:
  `build/lint_packs.py` (`target-vocab.toml`) and `commands/pack_evals.py` (`adapter.toml`)
- A roster test runs the catalogue commands on a starter catalogue and checks
  every contract the CLI loads — `tests/roster/test_catalogue_spec_contract_loads.py`
- agentbundle 0.54.0

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Interface compatibility | The manifest is the membership record S2–S4 build on | `contracts/catalogue-spec.toml`, `contracts/README.md`, `contracts/REGISTRY.md` | eugenelim | Parity gate green; README role sections; registry row | Manifest committed with 20 rows and an empty release table |
| Current architecture | Two architecture pages describe the parity gate and the contract load path | `ARCHITECTURE.md` § 7, `docs/architecture/agentbundle.md` invariants list | eugenelim | Updated bullets | Both name the manifest and the bundled-only rule |
| Release history | Package behaviour changes | the six files `docs/guides/how-to/cut-a-package-release.md` § Files that move together names, including a `docs/product/changelog.d/` fragment | eugenelim | 0.53.2 → 0.54.0 in all six | `tests/roster/test_okf_catalogue_discovery.py` passes |
| Decision rationale | Owned by RFC-0109 | none — the RFC already records it | — | — | — |

## Agent Rules

### Always do

- Keep `public-contracts.txt` byte-identical to its current 18 names. S1 changes
  how it is derived, not what it lists.
- Load every contract the CLI applies from the bundled `_data/` copy. Never
  read a `contracts/` folder instead, whether it is found from the catalogue, the
  working directory, or the package's own location.
- When a bundled copy is missing, unreadable or unparsable, fail closed: raise,
  or emit an ERROR diagnostic, whose message names `_data/<name>`. Never try
  another source after such a failure.
- State rules in shipped package source and messages without citing RFC, ADR or
  spec identifiers; the roster governance-marker test enforces this.
- Add `Engine-Change-RFC: RFC-0109` to every commit touching `packages/agentbundle/`.
- Bump `version.py` and `pyproject.toml` together.

### Ask first

- Changing any contract file's bytes.
- Adding a role beyond `member`, `bundled` and `vendored`.
- Changing which contracts the CLI bundles.

### Never do

- Move a contract file on disk (RFC-0109 D4).
- Add a third-party dependency or a new top-level directory.
- Bundle `contracts/catalogue-spec.toml` into the package.
- Change `_data/workspace_status_engine.py`'s digest read of a workspace
  `contracts/adapter.toml`. It hashes the file for cache identity, applies no
  rule from it, and belongs to the core pack's workspace engine.

## Testing Strategy

- Manifest validation, inventory writing and the parity rules: **TDD** in
  `tools/test_contract_parity.py`, against tmp fixture trees. They are pure
  functions over a small tree.
- Bundled-only loading at the changed sites and failing closed: **TDD** in the
  package suite. Tests plant a hostile `contracts/` folder in a tmp catalogue, or
  run a relocated copy of the package with a `_data/` file removed.
- No remaining fallback path: **goal-based**, by a package test that scans the
  package source.
- End-to-end load inventory: **goal-based**, exercised by a roster
  **integration** test that drives the real CLI on a starter catalogue outside
  the repository, one fresh process per command.
- Real repository state: **goal-based**. The parity gate,
  `sync_contract_inventory.py --check` and the contract-registry roster test pass
  on the tree.

## Acceptance Criteria

- [ ] `contracts/catalogue-spec.toml` lists exactly these rows. Members: `pack.schema.json`, `catalogue.schema.json`, `profile.schema.json`, `skill.schema.json`, `skill-manifest.schema.json`, `target-vocab.toml`, `catalogue-index.schema.json`, `adapter.toml`, `adapter.schema.json`. Bundled: `marketplace-entry.schema.json`, `plugin-manifest.schema.json`, `plugin-manifest.derived.schema.json`, `distribution-routes.toml`, `distribution-routes.schema.json`, `agent-plugin-extension-namespaces.toml`, `agent-plugin-extension-namespaces.schema.json`, `guide.schema.json`, `jsonschema/knowledge-captured-observation.schema.json`. Vendored: `vendor/agent-plugins/1.0.0/plugin.schema.json`, `vendor/agent-plugins/1.0.0/mcp.schema.json`. Its top-level `release` array is empty.
- [ ] Manifest validation rejects each of these cases with a message naming the offending row or key:
  - a missing top-level `release` array, or one that is not an array;
  - an unknown role;
  - a duplicate path;
  - a path that is absolute, contains `..`, a backslash or a drive letter;
  - a path that does not resolve, after following links, to a regular file inside `contracts/`;
  - a `vendored` row without an `https://` upstream;
  - a `vendored` row whose upstream differs from its file's `$id`;
  - two `member` or `bundled` rows with the same file name.
- [ ] `sync_contract_inventory.py --write`, pointed at a fixture `contracts/` folder and inventory path, writes exactly the sorted file names of the fixture's `member` and `bundled` rows, one per line, and omits `vendored` rows.
- [ ] On the repository tree, `sync_contract_inventory.py --check` exits 0, and this PR leaves `public-contracts.txt` byte-identical to `origin/main` (checked once, for this PR).
- [ ] The parity gate fails when a `member` or `bundled` row has no `_data/` copy.
- [ ] The parity gate fails when a `member` or `bundled` row's `_data/` copy differs by one byte.
- [ ] The parity gate fails when `public-contracts.txt` differs from the manifest's `member` and `bundled` names.
- [ ] The parity gate fails when a top-level `contracts/*.json` or `contracts/*.toml` file other than `catalogue-spec.toml` has no manifest row.
- [ ] The parity gate fails when a `contracts/README.md` role section does not list exactly the manifest rows of that role.
- [ ] Given a catalogue tree whose own folder and parent folder each hold a valid `contracts/target-vocab.toml` that differs from the bundled one only by `name-max-length = 4`, `agentbundle.build.cmd_lint_packs` on a pack whose skill name has 10 characters exits 0 with no finding.
- [ ] Given a catalogue root holding a `contracts/adapter.toml` that is not valid TOML, the pack-evals Claude Code projection succeeds using the bundled adapter contract.
- [ ] A copy of the package is placed so that four parent folders above its `build/` folder is a tmp catalogue. That catalogue holds invalid `contracts/adapter.toml`, `contracts/target-vocab.toml` and `contracts/pack.schema.json`. With one of those three removed from the copy's `_data/`, the matching entry point exits non-zero with an error naming that `_data/` file: `agentbundle --version` for `adapter.toml`, `cmd_lint_packs` for `target-vocab.toml`, and `agentbundle validate <pack>` for `pack.schema.json`.
- [ ] When the bundled `pack.schema.json` is missing or unparsable, `agentbundle catalogue lint` reports CAT-L006 at ERROR severity with a message naming `_data/pack.schema.json`, and exits non-zero.
- [ ] When the bundled `adapter.schema.json` is missing, `python -m agentbundle.build validate` exits 1 with a message naming `_data/adapter.schema.json` that does not mention repository contracts.
- [ ] No Python module in `agentbundle/` outside `_data/` contains a string constant, including an f-string part, that equals `contracts`, starts with `contracts/` or contains `/contracts/`, beyond the test's fixed allow-list. Each allow-list entry names a file, the string, its exact occurrence count in that file, and why it builds no load path; an extra occurrence fails. The reasons are: archive inclusion in `catalogue_tooling/package.py`, configuration key names, a CLI subcommand name, or a self-host input glob.
- [ ] A roster test runs `agentbundle catalogue lint`, `verify`, `package` and `index`, each in a fresh process, on a catalogue written by `agentbundle catalogue init` in a directory outside the repository. A parent folder of the catalogue holds an invalid `contracts/` copy of every manifest contract name, and so does the catalogue root for every command except `package`, which archives that folder. The recorder sees every file the process opens, including through `os.open`. Every manifest contract file opened resolves inside the package's `_data/` folder.
- [ ] In that roster test, every manifest contract file read is a `member` row, or a `bundled` or `vendored` row listed in the test's fixed exclusion table with one of RFC-0109 D1's three exclusion classes: host projection, engine setting, or other record.
- [ ] `agentbundle --version` reports `0.54.0`.

## Follow-ons

- eugenelim: RFC-0109 S2 — `catalogue-manifest.schema.json` and its contract tests.
- eugenelim: RFC-0109 S3 — the docs-site specification section at `draft/`.
- eugenelim: RFC-0109 S4 — release 0.1 and drift checks 2–4.

## Assumptions

none
