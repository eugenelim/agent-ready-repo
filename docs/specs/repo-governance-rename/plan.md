# Plan: Rename governance-extras to repo-governance with an installer rename hint

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** RFC-0110 § D3, § Trust model (D3 block) and its Errata; `commands/upgrade.py` `_unusable_stored_source_refusal` (the refuse-with-placeholder precedent the hint follows); `tools/lint-pack-dependency-declaration.py` with `tools/test-lint-pack-dependency-declaration.py` and its `tools/repo/build_gate_chain.py:725-729` wiring (the lint precedent); ADR-0038 commit `be5ba458c` (the prior pack rename's file set).

> **Plan contract:** this is the implementation strategy. It may change
> substantively only while its Status is `Drafting`, before approval records its
> baseline. After approval, `spec.md` and `plan.md` are pinned in substance;
> only lifecycle bookkeeping is permitted, and execution observations belong in
> `docs/specs/<feature>/notes/verification-ledger.md` (or the adopter's
> equivalent). A genuine artifact error follows the controlled-amendment path.
>
> **Not every field is contract.** `Touches`, `Tests` and `Done when` are what a
> completion gate reads, and they are pinned. `Design`, `Approach`, `Grounding`
> and `Risks` are working material that an implementer corrects in place only
> before approval: approval hashes the whole plan. After approval, grounding for
> a seam recorded as `no stub (implementation-discovered)` goes to the
> verification ledger; a settled design decision that execution falsified is a
> plan error that follows the controlled-amendment procedure. Treating them as
> contract is how a review spends a round on prose no gate consumes — the
> measured share is over half the plan's lines. `Grounding` stays *recorded*,
> because a per-task resolution that nobody wrote is not grounding; what it stops
> being is a claim a reviewer holds the plan to.

<!-- Existing plans without this field remain valid. Treat its absence as a
named assurance gap during structural review, not a universal lint failure. -->

<!-- **Durable-plan fill.** This template is the implementation and verification
strategy for a durable delivery slice. Fill Approach, Constraints, Risks,
Design, Tasks, and Changelog to the depth the durable work requires. Its sibling
spec is the durable behavior contract. Eligible direct-light work does not
create this artifact. -->

## Approach

Two independent strands meet at the end. The engine strand adds the rename map contract, then a pure hint builder, then wires it into `install` and `upgrade`. The rename strand moves the pack and every live surface, mechanically, under a completeness test. Releases and the end-to-end migration test need both strands. The riskiest part is the hint's source rendering, because it prints adopter sources that may carry credentials. It is a pure function with its own TDD task so every refusal and redaction is pinned before any command prints it.

## Constraints

- RFC-0110 D3 and its trust-model D3 block govern the map and the hint; its second erratum governs the completion check and the rename PR's allowed diff. That diff's exact allowed set is recorded under Design decisions.
- `packages/AGENTS.md` and `packages/agentbundle/AGENTS.md`: edit engine source, not packaged projections; normalise CRLF before byte comparisons; use `Path.as_uri()` for `file://` URLs.
- `packs/AGENTS.md:43-47`: `pack.toml` and `.claude-plugin/plugin.json` versions move together; a removal is a major bump. `packs/AGENTS.md:58`: a non-cosmetic pack change updates the pack's eval harness.
- `docs/guides/how-to/cut-a-package-release.md:85-111`: the six files an agentbundle release moves together.
- Root `AGENTS.md` § Security considerations: confined reads use `agentbundle.catalogue_tooling.file_safety`. `packages/AGENTS.local.md` § Engine-Change-RFC requirement: commits touching `packages/agentbundle/` carry `Engine-Change-RFC: RFC-0110`.
- `packages/AGENTS.md` § Test conventions: `packages/agentbundle/tests/` re-runs from the sdist with no `contracts/`, `packs/` or `catalogue.toml`, so a test that reads this repository's tree lives under `tests/roster/`.
- agentbundle's only runtime dependency is `credbroker`, so the CLI validates the map in code, not with a JSON Schema library.

## Construction tests

**Integration tests:** the per-shape CLI runs in T3 and the end-to-end migration run in T6 span tasks; they are listed under those tasks.

**Manual verification:** none.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| User promise: `packs/repo-governance/README.md` migration section, `guides/repo-governance/` | T4, T5 | README section; guides moved | AC-0026 test compares the README and CHANGELOG steps to the hint builder's steps and checks the replace-adapter sentence (T5) |
| Interface compatibility: `contracts/renames/pack-renames.toml`, its schema, `contracts/README.md` rows, `contracts/REGISTRY.md` row | T1 | schema validation test; contract registry test | both files listed in `contracts/README.md` § Repository only; `catalogue-spec.toml` unchanged |
| Maintainer procedure: `contracts/README.md` entry on adding a rename | T1 | entry text | entry present |
| Release history: agentbundle CHANGELOG, three `changelog.d` fragments | T5 | `tools/changelog.py` validation green | fragments and CHANGELOG entry present |
| Current architecture: `docs/architecture/pack-layout.md` | T4 | renamed text | AC-0025 search clean |

## Design (LLD)

### Design decisions

- **The map is a contract file, not a `pack.toml` field.** `contracts/` ships in the Git, local-path and archive shapes alike (`catalogue_tooling/package.py:52-58`, always walked), and the archive drops `catalogue.toml` (`:821-822`). A file there keeps the old name reserved even if the new pack is later removed. Traces to: AC-0005, AC-0006 · `contracts/renames/pack-renames.toml`.
- **The hint builder is pure and the commands only print it.** Selection, rendering and refusal live in one function of (requested name, reporting catalogue directory, reporting source string, installed state, target root, explicit adapter). `install` passes its `--adapter` value (`cli_adapter`, `install.py:425`, already limited by argparse to shipped adapter names) or none; `upgrade --pack` and `upgrade --all` always pass none, because AC-0014's explicit-adapter clause applies only to the reporting `install`. `install`, `upgrade --pack` and `upgrade --all` call it at their existing not-found points and print its result. This makes AC-0010's no-change property hold by construction, because the builder has no write path. Traces to: AC-0009, AC-0010, AC-0011, AC-0012, AC-0013, AC-0014, AC-0015, AC-0016, AC-0017, AC-0018, AC-0019, AC-0020, AC-0021, AC-0022, AC-0023.
- **Reuse the safety helpers, and split out the one that is not reusable as it stands.**
  - Shell quoting: `direct_source.recovery_command`.
  - Unsafe characters: a character is unsafe exactly when `catalogue_tooling.diagnostics.escape_rendered_value` changes it. One predicate drives both AC-0021's refusal and the escaping in AC-0016 and AC-0028. The `ord(c) < 32` check in `upgrade.py:369-375` is not used, because it misses DEL, C1 controls, bidi overrides and line separators.
  - Credential detection: `canonicalize_source` returns `None` for many reasons without saying which. So its rules 6-7 (`config.py:662-672`) move into a named predicate that `canonicalize_source` keeps calling, unchanged in behaviour. AC-0018's sentence uses that predicate. It does not decide what is printed: the printable-source rule below is the only gate for printing a source. `_redact_credentials` (`upgrade.py:725`) is not used: it misses token-only user-info and fragments.
  - Name grammar: `install._PACK_NAME_RE`.
  - Printable sources: a reporting source is printed only when it is printable in the spec's sense: no user-info, no query, and no fragment except an `archive+https` `sha256=` digest. A list of banned key names cannot cover signed-URL forms (`md5=`, `verify=`, `Policy=`), bare segments, or `;`-joined pairs, so the hint does not depend on one.
  - Traces to: AC-0014, AC-0016, AC-0019, AC-0020, AC-0021, AC-0028.
- **Dependents come from the reporting catalogue and installed state only.** Installed state records no dependencies. The builder takes the installed pack names from the installed state the hint reads (repo scope only, as the spec's term defines), checks each against the name grammar, and reads its `pack.toml` from the reporting catalogue through `file_safety`, with the same byte cap as the map. It counts a pack as a dependent when that `pack.toml` requires the rename target. Only a catalogue carrying the rename has a dependent requiring the new name, so no other catalogue is needed. Traces to: AC-0015, AC-0023.
- **The rename PR's allowed diff.** Outside tests, fixtures, eval updates and release notes, the diff holds only renamed names and paths, version bumps, the rename map and its schema, the hint and lint code, the `rename_hint` JSON key, the predicate split out of `canonicalize_source`, and the migration text. Review checks the diff against this list (RFC-0110 second erratum).
- **The completion check is a repository test, not a review step.** It runs `git grep -l governance-extras`, classifies each hit by AC-0025's categories, and fails on any unclassified path. It classifies files as T4's Tests bullet states, applying RFC-0110 D3's status rule and its path rule for dated changelog history. Traces to: AC-0025.


Owned by: T1, T2, T3, T4.
### Data & schema

`contracts/renames/pack-renames.toml`:

```toml
schema = 1

[[rename]]
from = "governance-extras"
to = "repo-governance"
```

Names only: no versions, sources or prose. `contracts/renames/pack-renames.schema.json` requires `schema = 1` and a `rename` array of tables with exactly `from` and `to`, both matching `^[a-z0-9][a-z0-9-]*$`. The CLI reads the file through `file_safety.read_confined_regular_file`, rooted at the reporting catalogue's root, with a 65,536-byte cap. A one-rename map is about 70 bytes, so the cap leaves room for hundreds of renames. It always reads the fixed path `contracts/renames/pack-renames.toml`, because packaging walks only a fixed `contracts/` tree (`package.py:52-58`) and the archive drops `catalogue.toml`. A probe on 2026-10-25 confirmed that subfolders of `contracts/` ship in the archive: it held 18 files from `contracts/jsonschema/`. An unreadable, oversized or invalid map produces no hint. A probe on 2026-10-25 built this repository's archive with `agentbundle catalogue package`. The archive held `contracts/pack.schema.json`, but no `catalogue.toml` and no `packs/governance-extras/`, because `[catalogue.package].include` lists only `packs/core`. So in this repository's own archive the map ships, but its target is absent and AC-0022 refuses the hint. The archive-shape runs in T3 therefore use a fixture catalogue whose package includes `repo-governance`. Traces to: AC-0005, AC-0022 · `contracts/renames/pack-renames.toml`.


Owned by: T1, T2.
### Interfaces & contracts

The hint is stderr text whose layout and per-step word order are the spec's "hint's layout" term, which is the single source for both. For example, with one adapter and no target root:

```
<command>: pack 'governance-extras' was renamed to 'repo-governance'.
Run these steps to move to it:
  1. agentbundle uninstall --pack governance-extras --scope repo
  2. agentbundle install --pack repo-governance --scope repo --adapter claude-code <source>
  3. agentbundle upgrade --pack iac-terraform --scope repo <source>
```

Step 1 appears only when the old pack is installed, and step 3 only once for each installed dependent. Sentence placement and order follow the spec's "hint's layout" term, which covers the AC-0018 sentence and AC-0030 notices that qualify no single step. Under `upgrade --all --format json`, the renamed row gains one additive key, `rename_hint`, an array of the same lines. Other rows and the document's `schema_version` are unchanged. How often each step repeats is set by AC-0013, AC-0014 and AC-0015. `<source>` is a printable source passed through `recovery_command`, or the placeholder `<catalogue-source>` printed unquoted. The source is always the last word, so a pasted placeholder step ends in a bare `>` and is a shell syntax error rather than a redirection (probe on 2026-10-25: `bash -n`, `zsh -n` and `sh -n` reject both `... --scope repo <catalogue-source>` and `... --scope repo --adapter claude-code <catalogue-source>`; they accept `... <catalogue-source> --adapter claude-code`). Test seam: the pure builder is unit-tested directly. The commands are tested through `agentbundle.cli` main with captured stderr. Traces to: AC-0009, AC-0013, AC-0014, AC-0015, AC-0016, AC-0017, AC-0018.


Owned by: T2, T3.
### Failure, edge cases & resilience

| Condition | Response | AC |
| --- | --- | --- |
| Map renames the pack, but the source is empty, unsafe or starts with `-`, the target root is unsafe or starts with `-`, or a `governance-extras` adapter row is not a shipped adapter name | Existing not-found message plus a refusal reason that omits those values; no hint; `--all` row `pack-not-found` | AC-0021 |
| A dependent has an adapter row that is not a shipped adapter name | No step for it; the AC-0030 adapter notice; the rest of the hint prints | AC-0030 |
| Map missing, unreadable, invalid, bad name or foreign target | Existing not-found message; no hint | AC-0022 |
| Map is a symlink, hard link, non-regular or over 65,536 bytes | `file_safety` raises; existing not-found message; no hint | AC-0027 |
| TOML nested deep enough to raise `RecursionError`, or wrong types | Caught with every other map failure; no traceback; `--all` row stays `pack-not-found` | AC-0022 |
| Old pack's recorded source differs or is absent | Move-between-catalogues or no-source sentence above step 2 | AC-0028 |
| Map present only in another catalogue | Not consulted; existing not-found message | AC-0023 |
| Reporting source non-empty, free of unsafe characters and not starting with `-`, but not printable | Placeholder in steps; the AC-0018 sentence too when it is credential-bearing | AC-0014, AC-0018 |
| Dependent's recorded source differs or is absent | Move-between-catalogues sentence or no-source sentence | AC-0016, AC-0017 |

Every refusal exits 1 and writes nothing.


Owned by: T2, T3.
## Tasks

### T1: The rename map contract exists, validates, ships, and is guarded by a lint

**Depends on:** none

**Touches:** contracts/renames/pack-renames.toml, contracts/renames/pack-renames.schema.json, contracts/README.md, contracts/REGISTRY.md, tools/lint-pack-renames.py, tools/test-lint-pack-renames.py, tools/repo/build_gate_chain.py

**Tests:**
- AC-0005: the map validates against its schema. This uses the same validation route the repository's existing `contracts/*.schema.json` tests use (discovery predicate: the test that validates `profile.schema.json` against `profiles/*.toml`).
- AC-0007, AC-0008: `tools/test-lint-pack-renames.py` builds two fixture catalogues under `tmp_path` and asserts the lint exits non-zero on each: one with a pack named after an old name, one with a map target that is no pack. A third, clean fixture exits 0.
- AC-0005: `contracts/catalogue-spec.toml` and the `_data/` inventories are unchanged, and `tools/catalogue/check_contract_parity.py`, `tools/test_contract_parity.py` and `tools/catalogue/check_spec_version.py` stay green without edits. Both files sit in the `contracts/renames/` subfolder, which rule 3 of `check_contract_parity.py` (top-level files need a manifest row) does not reach, and `contracts/README.md` lists them under § Repository only. Kill condition: if any repository check requires a manifest row for either file, stop and raise it with the owner rather than adding one.

**Approach:**
- Build the lint on `tools/lint_harness.py` and its self-test on `tools/selftest_harness.py`, as `tools/AGENTS.md` requires. Register both in `tools/repo/build_gate_chain.py` beside `lint-pack-dependency-declaration.py` (`:725-729`), so CI parity lints see a known shape.

**Done when:** `tools/test-lint-pack-renames.py`, the schema test and `tests/roster/test_contract_backward_registry.py` pass, with a `contracts/REGISTRY.md` row pairing `contracts/renames/pack-renames.toml` with `docs/specs/repo-governance-rename/`, the schema carrying `"x-spec": "docs/specs/repo-governance-rename"`, and `lint-spec-status.py` reporting no invariant (v) warning for either file, and `python3 tools/lint-pack-renames.py` exits 0 on this repository.

### T2: The hint builder returns the exact hint or refusal for every input class

**Depends on:** T1

**Touches:** packages/agentbundle/agentbundle/pack_renames.py, packages/agentbundle/agentbundle/config.py, packages/agentbundle/tests/unit/test_pack_renames.py

**Tests:**
- One parametrised table per input class, asserting the exact returned text:
  - old pack installed or not (AC-0013);
  - safe and credential-bearing reporting sources, and `archive+https` sources with a digest-only fragment (printed) and with an extra fragment key (placeholder) (AC-0014, AC-0018);
  - a recorded source of `agent-ready-repo`, treated as no recorded source (AC-0017, AC-0028);
  - an explicit `--root` and `--output`, carried into every step in the fixed word order (AC-0013, AC-0014, AC-0015);
  - target roots with a space and `$` (AC-0020), and with U+000A, U+202E and a leading `-`, each asserting no hint and that stderr after the not-found message is exactly AC-0021's pinned reason (AC-0021);
  - an unsafe source with a pack the map does not rename, asserting today's not-found output byte-identical (AC-0021);
  - `governance-extras` installed for one non-default adapter such as `cursor`, giving an install step with `--adapter cursor` (AC-0014); not installed, giving one install step with no `--adapter` (AC-0014); and not installed with the reporting `install` given `--adapter cursor`, giving one install step with `--adapter cursor` (AC-0014);
  - adapter keys `bogus`, `-x`, and keys carrying U+000A or U+202E, on the old pack's row (AC-0021: no hint, and stderr after the not-found message exactly the pinned reason) and on a dependent's row (AC-0030, adapter notice, no step); a dependent with one shipped row and one `bogus` row, which gets no step at all and exactly one adapter notice (AC-0030, AC-0015); and a Readable non-dependent with a bad adapter key, which gets no notice (AC-0030);
  - `install` with no `--scope`, reading repo-scope state only (AC-0013, AC-0015);
  - a dependent found at the catalogue root layout rather than under `packs/` (AC-0030);
  - an empty reporting source, a reporting source `-o/evil`, and reporting sources carrying U+202E, U+200B, U+2028 and U+007F, each asserting that stderr after the not-found message is exactly AC-0021's pinned reason (AC-0021);
  - zero, one and two dependents; zero, one and two adapter rows for the old pack, and one and two for a dependent (AC-0013, AC-0014, AC-0015);
  - Absent, with no step and no notice (AC-0030): no `packs` directory at the catalogue root; nothing at `packs/<name>` under a real `packs/`; a real `packs/<name>/` holding no `pack.toml`;
  - Unchecked, each producing the pinned notice while the rest of the hint still prints (AC-0030): an invalid name carrying U+202E, asserting its escaped rendering; a symlinked `packs/`; a regular file at `packs`; a symlinked `packs/<name>/`; a regular file at `packs/<name>`; at `pack.toml`, a dangling symlink, a symlink, a hard link, a directory, a FIFO where the platform supports one, a 65,537-byte file, non-UTF-8 bytes, invalid TOML, and 1,000 nested `[`;
  - `pack.toml` files that each parse without error and produce no notice (AC-0030): `required = "x"` and an integer `pack`, which are not dependents; and `pack = "repo-governance"` with no `catalogue`, or with another catalogue named, which are dependents;
  - the AC-0014 placeholder sentence, pinned verbatim;
  - each placeholder-bearing step, single- and multi-adapter (AC-0031). On every platform the test asserts the step's last word is the bare `<catalogue-source>`. It then runs `bash -n`, `zsh -n` and `sh -n` on each shell present. On Linux and macOS a missing `bash` or `sh` fails the test rather than skipping it. A missing `zsh` skips only that probe, and the `zsh -n` result from a macOS run is recorded in the verification ledger;
  - same, different and absent recorded sources for dependents (AC-0016, AC-0017) and for the old pack itself (AC-0028);
  - a missing map; invalid TOML; non-UTF-8 bytes; `a=` followed by 1,000 nested `[`; `rename = "x"`; `from = 1`; a missing `schema`; a bad name; a foreign target (AC-0022);
  - a symlinked map, a symlinked `contracts/` directory, a symlinked `contracts/renames/` directory, a regular file at `contracts/renames`, a hard-linked map, a FIFO and a 65,537-byte map (AC-0027).
- AC-0019: the fixture classes the criterion lists, each used as the reporting source and as a recorded source. The builder's whole output contains none of each source's user-info, password, or credential-keyed values.
- The predicate split out of `canonicalize_source` leaves `canonicalize_source`'s existing tests green unchanged.
- AC-0020: for sources with spaces, quotes, `$`, `;` and backticks, `shlex.split` of each step line returns the intended words.
- stub: true —
  ```python
  def test_hint_names_new_pack(tmp_path):
      cat = make_catalogue(tmp_path, renames=[("governance-extras", "repo-governance")], packs=["repo-governance"])
      hint = build_rename_hint("governance-extras", catalogue_dir=cat, source=str(cat), installed=Installed.empty(), command="install")
      assert hint.lines[0] == "install: pack 'governance-extras' was renamed to 'repo-governance'."
  ```

**Done when:** `python3 -m pytest packages/agentbundle/tests/unit/test_pack_renames.py -q` passes, and the verification ledger records a passing `zsh -n` result for each AC-0031 fixture from a macOS run.

### T3: install and upgrade print the hint on every catalogue shape and change nothing

**Depends on:** T2

**Touches:** packages/agentbundle/agentbundle/commands/install.py, packages/agentbundle/agentbundle/commands/upgrade.py, packages/agentbundle/tests/integration/test_rename_hint_cli.py, packages/agentbundle/tests/integration/_https_archive.py, packages/agentbundle/tests/unit/test_upgrade_bulk_all.py

**Tests:**
- AC-0009, AC-0010: `test_rename_hint_cli.py` runs `install --pack` and `upgrade --pack` through the CLI entry point for each of three shapes:
  - local path: unpatched;
  - release archive: built in the test with `agentbundle catalogue package`;
  - git: `resolve_catalogue`'s network download replaced by the same local tree.

  Each run asserts stderr's first line and exit 1. It also hashes the installed-state files and the target repository's tree before and after.
- AC-0033: two catalogue adapter rows for `governance-extras`, bare `upgrade --pack governance-extras`, asserting the hint replaces the "pass --adapter" refusal.
- AC-0034, AC-0035: bare multi-adapter `upgrade --pack` with one direct row, with the network fetch patched to fail the test if called. Then, with all-catalogue rows, the same command over: a pack present in the catalogue, no map entry, a failing catalogue fetch, and every AC-0021, AC-0022, AC-0023 and AC-0027 fixture T2 builds, reused as a parametrised table. Each run asserts today's refusal text byte-identical, exit 1, and an unchanged tree hash (AC-0010).
- AC-0010, AC-0021, AC-0022, AC-0027: one representative input per criterion (an unsafe source, an unsafe target root, an invalid map, a symlinked map) run through `install --pack`, `upgrade --pack` and `upgrade --all`. Each asserts exit 1, the existing not-found stderr with no traceback, `pack-not-found` on the `--all` row, and an unchanged tree hash.
- AC-0009, AC-0011: fixtures install both `governance-extras` and `iac-terraform`, and the assertions compare the full hint lines for each shape's source. AC-0011 runs `upgrade --all --scope repo` on each shape, once in table form and once with `--format json --dry-run`. `--format json` without `--yes` or `--dry-run` exits 2 before preflight (`upgrade.py:1432-1440`). It asserts the `rename_hint` key on the renamed row only, every row not `skipped-direct` as `blocked`, exit 1, and an unchanged tree. AC-0019's credential fixtures also run through the JSON form.
- AC-0012: `upgrade --all` with the row recorded from a pre-rename archive fixture upgrades that row and prints no hint.
- AC-0023: the reporting catalogue lacks the map while the packaged-default catalogue fixture has it; the command prints only not-found. Every run in this file patches the network fetch to fail the test if called after the reporting catalogue is resolved.
- The existing `pack-not-found` tests in `test_upgrade_bulk_all.py:207,335` and `test_list_installed_*` stay green unchanged.

**Approach:**
- Call the builder at the three existing not-found points (`install.py:560-567`, `upgrade.py:1778-1784`, and the `--all` per-row preflight at `upgrade.py:850-854`). For AC-0033, `upgrade --pack` also resolves the catalogue and checks the map before its multi-adapter refusal (`upgrade.py:1675-1686`), but only when every row of the requested pack came from a catalogue. Direct rows never enter catalogue resolution, as `upgrade.py:1733-1734` requires. Any result other than a rename hint, a resolution failure included, falls through to today's refusal unchanged. Every other path stays byte-identical.
- Archive-shape runs serve the built archive from a local HTTPS server signed by a throwaway certificate authority passed through `AGENTBUNDLE_CA_BUNDLE`, which the archive fetch honours (`catalogue_fetch/direct_http.py:159-167`). On Linux and macOS a missing `openssl` fails these tests rather than skipping them.
- `upgrade --pack` today skips the name-grammar check on its argument. The builder's own check covers the hint, and the command's behaviour is otherwise unchanged.

**Done when:** `python3 -m pytest packages/agentbundle/tests/integration/test_rename_hint_cli.py packages/agentbundle/tests/unit/test_upgrade_bulk_all.py -q` passes.

### T4: The pack and every live surface carry the new name

**Depends on:** none

**Touches:** packs/governance-extras/**, packs/repo-governance/**, guides/**, packages/agentbundle/** (except the build-pipeline fixture and the tests that load it), packs/iac-terraform/**, profiles/full-ceremony.toml, packs/core/**, packs/catalogue-curation/**, packs/desk-research/**, packs/product-documentation/**, packs/agent-skill-engineering/**, packages/agentbundle/agentbundle/build/**, site.toml, docs-site/astro.config.ts, Makefile, .github/workflows/**, tools/**, tests/roster/**, web/src/**, docs/** (live only), workspace.toml, .claude/skills/**, .agents/skills/**

**Tests:**
- AC-0025: a repository test, `tests/roster/test_repo_governance_rename_completeness.py`, runs `git grep -l governance-extras` and fails on any path outside AC-0025's categories. Frozen status comes from the file's own or its owning record's `Status:` line, and also from RFC-0110 D3's path rule for dated changelog history: `docs/product/changelog*` and `packages/*/CHANGELOG.md`.
- AC-0001, AC-0002: assertions on the parsed `pack.toml` and `plugin.json` files.
- AC-0003: `install --profile full-ceremony` into a `tmp_path` repository exits 0 and records `repo-governance` 2.0.0.
- AC-0004: `FORCE=1 make build-self` followed by `git status --porcelain` is empty. This is a goal-based check recorded in the verification ledger.
- Existing suites that named the old pack pass under the new name: `tests/roster/test_governance_extras_standalone_install.py` becomes `test_repo_governance_standalone_install.py`, and `tools/lint-ci-parity.py` stays green with the renamed `build-check.yml` step.
- The pack's eval harness under `packs/repo-governance/tests/` passes with the renamed pack, as `packs/AGENTS.md:58` requires.

**Approach:**
- Review shape: WIDE and mechanically uniform. The completeness test is its reproducibility proof, so it lands as one review unit.
- `git mv` the pack and guides first, then rewrite references. Then run `FORCE=1 make build-self` so generated copies under `.claude/skills/` and `.agents/skills/` follow from source rather than being hand-edited.

**Done when:** the completeness test, the AC-0001, AC-0002, AC-0003 assertions, the renamed roster suites and `make lint-ruff lint-mypy` pass, and the AC-0004 check is recorded green in the verification ledger.

### T5: agentbundle 0.57.0, repo-governance 2.0.0 and iac-terraform 0.2.0 are released with the migration steps

**Depends on:** T3, T4

**Touches:** tests/roster/test_repo_governance_migration_text.py, packages/agentbundle/agentbundle/version.py, packages/agentbundle/pyproject.toml, packages/agentbundle/CHANGELOG.md, packages/agentbundle/README-pypi.md, tests/roster/test_okf_catalogue_discovery.py, docs/product/changelog.d/*, packs/repo-governance/README.md

**Tests:**
- AC-0026: `tests/roster/test_repo_governance_migration_text.py` calls the hint builder for the criterion's named input. It asserts that the step commands in the `0.57.0` CHANGELOG entry and in the README's migration section both equal its steps, and that both carry the sentence telling readers to replace `claude-code` with their own adapter.
- `tools/changelog.py` validation passes for the three new fragments.
- The version pin in `tests/roster/test_okf_catalogue_discovery.py` matches `0.57.0`.

**Done when:** those tests pass and `make lint-ruff lint-mypy` is green.

### T6: The printed steps carry a real repository across the rename

**Depends on:** T3, T4

**Touches:** packages/agentbundle/tests/integration/test_rename_migration_e2e.py, packages/agentbundle/tests/integration/fixtures/**, packages/agentbundle/tests/integration/_https_archive.py (reused from T3), tests/roster/test_repo_governance_archive_map.py

**Tests:**
- AC-0032: the same run with the post-rename fixture served as an `archive+https` archive over local HTTPS, as T3 serves it; the printed steps carry the `#sha256=` source and complete.
- AC-0024, AC-0029: `test_rename_migration_e2e.py` uses pre-rename and post-rename catalogue fixtures under `packages/agentbundle/tests/integration/fixtures/`, so it reads nothing from this repository's tree. It installs `governance-extras` 1.0.3 and `iac-terraform` 0.1.12 from the pre-rename fixture. One run records `iac-terraform` from a pre-rename archive built in the test, and one leaves it with no recorded source. Each run calls `upgrade --pack governance-extras` against the post-rename fixture and parses the printed steps. It runs each step through the CLI with `--yes` appended to answer the confirmation prompt, and with no `--force`. It asserts the expected sentence, exit 0 per step, and the final installed state.
- AC-0006: `tests/roster/test_repo_governance_archive_map.py` builds this repository's archive with `agentbundle catalogue package` and compares `contracts/renames/pack-renames.toml` inside it to the source bytes.

**Done when:** `python3 -m pytest packages/agentbundle/tests/integration/test_rename_migration_e2e.py tests/roster/test_repo_governance_archive_map.py -q` passes.

## Rollout

- **Delivery:** big bang, in the release PR. The rename is a one-way door for adopters: rolling it back would need a second rename. The hint itself is reversible.
- **Deployment sequencing:** catalogue and CLI ship together. An adopter on a CLI older than 0.57.0 sees the plain not-found message and relies on the CHANGELOG and README steps (T5).
- **Infrastructure / external systems:** none beyond the existing PyPI publish of the `agentbundle-v0.57.0` tag.

## Risks

- `uninstall --pack governance-extras` may remove seeded files such as `docs/adr/README.md` that `install --pack repo-governance` then reseeds. T6's end-to-end run shows whether an adopter's edited seeds survive; if they do not, stop and raise it before release.
- T4's diff is large, about 124 files outside `docs/` plus about 32 live docs files, so a stray behaviour change can hide in it. The allowed-diff list in Design decisions is the review check.

## Changelog

- 2026-10-25: spec approved by eugenelim
- 2026-10-25: plan approved by eugenelim
- 2026-10-25: spec amendment (No recorded source covers a non-text value) approved by eugenelim
- 2026-10-25: amended plan approved by eugenelim
