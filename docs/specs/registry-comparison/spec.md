# Spec: Registry comparison

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Approved:** 2026-10-27 by eugenelim, spec and plan, after spec-stage shaping and adversarial reviews over five rounds ending clean, with the FEAT-0034 amendment clean in intent review; review records under `.context/reviews/0a169cc7-b068-428f-aae2-8b3eb35b48dc/`.
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0106 (D1, a type's registration stops only when its replacements have shipped), RFC-0105 (D3, the behavioral-equivalence gate)
- **Brief:** brief:workspace-registry-retirement-delivery
- **Discovery:** none
- **Depends on:** spec:intent-navigation
- **Contract:** none — the output record is contracted by the criteria below.
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Outcome`, `What Changes`, `Durable Outputs`, `Follow-ons` and
> `Assumptions` are working material: they orient a reader and an author corrects them in place
> as the work teaches, without an amendment and without a review round. A review
> finding against working material is advisory — it cannot block, because nothing
> gates the text it cites. Marking the tiers is the spec's job; honouring them
> when a finding is adjudicated is the reviewing surface's.

## Outcome

A maintainer about to stop a type's registration runs one read-only command. It compares the outstanding work the artifacts show with `workspace.toml` and classes each difference as [FEAT-0034 § Registry comparison](../../product/intents/FEAT-0034-workspace-registry-retirement.md#registry-comparison-owned-here) defines. Success is that the command's summary and exit code alone tell them whether that type's registration may stop, under FEAT-0034 § Validation hook part (a), and the summary is what the stop's spec records.

## What Changes

- The comparison — a new repository tool, `tools/compare-registry.py`, with its tests in `tools/test_compare_registry.py`. It runs `navigate-intents`' `outstanding` operation, reads captured-item files through `workspace-status`'s reader, and parses `workspace.toml` itself.
- Its first run over this repository — recorded in `docs/specs/registry-comparison/notes/verification-ledger.md`.
- The consumer inventory — rows for the tool, its test, and this spec directory in `docs/specs/workspace-retirement/inventory.toml`, each with owner 5.
- Delivery membership — this spec's row in the brief's Spec map and its `workspace.toml` entry.
- The class definitions — [FEAT-0034 § Registry comparison](../../product/intents/FEAT-0034-workspace-registry-retirement.md#registry-comparison-owned-here), amended to add captured-item files to the outstanding side.
- The tool's test suite in `make test` — the `Makefile`'s `run-test-suite` define and its `tools/lint-ci-parity.py` roster entry.
- Unchanged: `navigate-intents`, `workspace-status`, `close-work`, and every pack. No registration writer stops here. The comparison has no CI job, schedule, or `make` gate.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Maintainer procedure: running the comparison before a stop | Applicable: slices 3, 7, and 8 run it before their stops | The tool's module docstring and `--help`. The brief's slice 5 already says when to run it | Platform Core maintainer | AC-0020 holds | `--help` names the classes, which fail, and the exit codes |
| Decision rationale: the class definitions | Applicable: the comparison applies them | [FEAT-0034 § Registry comparison](../../product/intents/FEAT-0034-workspace-registry-retirement.md#registry-comparison-owned-here), amended 2026-10-27 to add captured-item files | Platform Core maintainer | The intent's shaping-review line names the amended revision | The amendment is merged with this spec |
| Verification evidence: this repository's first run | Applicable: the owner asked for one run with its result recorded | `docs/specs/registry-comparison/notes/verification-ledger.md` | Platform Core maintainer | AC-0015 holds | The ledger holds the run's summary, exit code, and commit |
| Current product truth: the inventory | Applicable: the tool and this spec name `workspace.toml` | `docs/specs/workspace-retirement/inventory.toml` | Platform Core maintainer | `tests/roster/test_workspace_retirement_inventory.py` passes | The three rows are present |
| Delivery membership | Applicable: the brief's coverage map | The brief's Spec map and this spec's `workspace.toml` entry | `author-delivery-brief` | `lint-brief-coverage.py` lists this spec under the brief | The coverage lint passes |

Release history does not apply: nothing shipped to adopters changes, so no pack version or changelog fragment moves. The retirement record does not change either. FEAT-0034 § Validation hook records each run in the spec that stops that registration, and § Equivalence holds migration behaviors, not this check.

## Agent Rules

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Read `workspace.toml` and every corpus file through `agentbundle.catalogue_tooling.file_safety`'s confined readers, or through the navigator's or `workspace-status`'s own readers.
- Take each rule from the module that owns it, by import: terminality from `close-work`'s `closure_terminality.py`, artifact ids and paths from `navigate-intents`' `intent_graph.py`, the captured-item reading and the registry's collection and initiative-key rules from `workspace-status`'s engine.
- Run one implementation-stage `security-reviewer` pass on confinement and output escaping once the adversarial review is clean (owner decision, 2026-10-27).

### Ask first

- Any failing difference in this repository's run: report it to the owner with its rows. Do not change the registry or an artifact to clear it.
- Any class reading that FEAT-0034 § Registry comparison does not settle. The intent owns the classes, so it is amended first.

### Never do

- Write any file, `workspace.toml` and bytecode included. The comparison only reads.
- Add a CI job, a schedule, or a `make` target that runs the comparison over this repository (FEAT-0034 § Registry comparison; the brief's slice 5; owner decision, 2026-10-27). The tool's own fixture suite in `make test` is not such a target.
- Change `navigate-intents`, `workspace-status`, `close-work`, or any pack, or copy any of their rules into the tool.
- Add a dependency, a top-level directory, or a new module boundary.

## Testing Strategy

- **Class rules, output, exit codes, refusals, and help (AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0006, AC-0007, AC-0008, AC-0009, AC-0010, AC-0011, AC-0012, AC-0013, AC-0014, AC-0017, AC-0018, AC-0019, AC-0020):** TDD. The rules are a closed predicate over a small fixture tree, so one fixture per class and per refusal decides each.
- **This repository's run (AC-0015):** goal-based check. One run over this repository at a named commit, recorded in the ledger.
- **Inventory (AC-0016):** goal-based check. The inventory roster test passes.

## Acceptance Criteria

Terms used below:

- **Registry entry.** Each element of an array that `workspace-status`'s engine places as a collection: its `_TOP_LEVEL_ENTRY_COLLECTIONS` at the top level of `workspace.toml`, and its `_INITIATIVE_ENTRY_COLLECTIONS` under each top-level table whose key its `_CANONICAL_INITIATIVE_RE` matches. Its **collection** is the two-part name, such as `work.queue`, without the initiative key. **Non-terminal** and **terminal** collections are the sets FEAT-0034 § Registry comparison names.
- **Typed file** and its **status** are as the `workspace-retirement` spec's Terms define them. **Captured-item file** and its **slug** are as the `captured-item-files` spec's Terms define them.
- **Target.** For a table with a string `path`: that string, exactly as written. For a table with no `path` and a string `slug`: `docs/product/captured/<slug>.md` when that is a captured-item file. Every other entry has no target. A target is **canonical** when it is a relative POSIX path with no empty, `.`, or `..` segment and no backslash.
- **Outstanding item.** Each item in the `placed` and `no_parent` arrays of `navigate-intents query --operation outstanding` over the root, with the root-relative POSIX path the navigator's graph gives its id. Also each captured-item file whose own status is `Open`, with its root-relative path.
- **Own status.** For a navigator item: its `status` value, terminal when `closure_terminality`'s `is_intent_terminal`, `is_brief_terminal`, or `is_spec_terminal` for its `type` says so. For a typed file that is not an outstanding item: its status, judged the same way for its type, and non-terminal when it has no `- **Status:**` line. For a captured-item file: its `Status:` value as `workspace-status`'s captured-item reader returns it, where only `Closed` is terminal.
- **Registered.** An outstanding item is registered in each collection of an entry whose target equals its path, compared byte for byte.
- **Difference row.** A JSON object with the keys `class`, `failing` (a boolean), `target`, `location`, `id` (the navigator id, or `""`), `collections` (a sorted array), and `status` (the own status, or `""`). For a row from an outstanding item, `target` is the item's path. For a row from entries with a target, it is that target. For a row from one entry with no target, `target` is `""` and `location` is `<initiative>.<collection>[<index>]`, or `<collection>[<index>]` at the top level. Every other row's `location` is `""`. Rows sort by class in AC-0012's order, then by `target`, then by `location`.

Classification is per target. Every entry naming a target is judged together, over the union of their collections, and each entry with no target is judged alone.

- [x] **AC-0001.** `python3 tools/compare-registry.py --root DIR` reads its registry, `DIR/workspace.toml`, and its captured-item files from `DIR`.
- [x] **AC-0017.** The tool runs the navigator `packs/core/.apm/skills/navigate-intents/scripts/navigate_intents.py` found from the tool's own location, never from `DIR`, with `--root DIR`.
- [x] **AC-0002.** An outstanding item registered in at least one non-terminal collection, with a non-terminal own status, gives no difference row. Neither does a target or no-target entry whose collections are all terminal and that is not an outstanding item's path.
- [x] **AC-0003.** An outstanding item whose own status is terminal gives one failing `result_terminal` row, whatever its collections.
- [x] **AC-0004.** An outstanding item with a non-terminal own status, registered only in terminal collections, gives one `registry_closed_stale` row.
- [x] **AC-0005.** An outstanding item with a non-terminal own status, registered in no collection, gives one `registry_omission` row.
- [x] **AC-0006.** These are the rows for an entry in at least one non-terminal collection that is not an outstanding item's path. A string that the engine's `_is_legacy_spec_path` accepts gives `legacy_shape`. So does a table with a `slug`, no `path`, and no captured-item file for that slug.
- [x] **AC-0007.** Such an entry whose target is canonical and exists as a regular file that is neither a typed file nor a captured-item file gives `captured_item`.
- [x] **AC-0008.** Such an entry whose target is a canonical typed file or captured-item file with a terminal own status gives `registry_stale`.
- [x] **AC-0009.** Such an entry whose target is a canonical typed file or captured-item file with a non-terminal own status gives a failing `registry_live_only` row.
- [x] **AC-0010.** Every other such entry gives a failing `unclassified` row. That covers a target that is not canonical, is missing, is a link, is not a regular file, or resolves outside the root; a typed file that cannot be read or is not UTF-8; and an entry with no target that AC-0006 does not class.
- [x] **AC-0011.** Entries that share a target give one row for that target, holding the union of their collections. Each entry with no target in a non-terminal collection gives its own row.
- [x] **AC-0012.** By default the tool prints these stdout lines and nothing else:
  - `registry comparison: pass` when no row is failing, otherwise `registry comparison: fail`;
  - then one line `<class> <count>` for each of `captured_item`, `legacy_shape`, `registry_stale`, `registry_closed_stale`, `registry_omission`, `registry_live_only`, `result_terminal`, and `unclassified`, in that order, zeros included;
  - then one line `FAIL <class> <target> <location> <collections>` per failing row, in row order, with the row's `target`, `location`, and `collections` each written as `json.dumps` with `ensure_ascii=True` writes it;
  - then `commit <git rev-parse HEAD in DIR, or "unknown">`;
  - then `workspace.toml sha256 <hex digest of its bytes>`.
- [x] **AC-0018.** With `--format json`, it prints one JSON object instead of AC-0012's lines. The object has `schema` set to `registry-comparison.v1`, `result` set to `pass` or `fail`, `counts` with all eight classes, `differences` holding every row in row order, and `inputs` holding `commit`, `workspace_sha256`, and the navigator's `provenance.generated_at`.
- [x] **AC-0013.** It exits 0 when no row is failing and 1 when any row is failing.
- [x] **AC-0019.** In each case below it exits 2 and prints one stderr line `refused: <input>: <reason>`, with nothing on stdout. The inputs are checked in this order, and the first refusal wins:
  1. `workspace.toml` is missing, is a link, is not a regular file, is not UTF-8, or does not parse as TOML; or a section or initiative table the engine's tables place is present but is not a table; or a collection is present but is not an array.
  2. The navigator exits non-zero, or its output is not a JSON object with `schema` `intent-navigation.query.v1`, `status` `ok`, and `placed` and `no_parent` arrays whose items each carry string `id`, `type`, and `status`.
  3. The navigator's graph cannot be derived, or an outstanding item's id has no path in it.
  4. The captured-item directory exists but cannot be listed, or a captured-item file is unreadable or invalid by `workspace-status`'s captured-item reader, whether or not an entry names it.

  A command-line usage error exits 2 the same way, with `<input>` `arguments`. Any other error also exits 2, with `<input>` `internal`, never 1.
- [x] **AC-0020.** `--help` names the eight classes, which of them fail, and the three exit codes.
- [x] **AC-0014.** A run leaves every file under `DIR` byte-identical and creates no file there or anywhere else, bytecode included.
- [x] **AC-0015.** `docs/specs/registry-comparison/notes/verification-ledger.md` records one run of the tool over this repository. It holds the run's full default output and exit code, the commit it ran at on this spec's branch, and that commit's merge base with `origin/main`. When that run has a failing row, the ledger also names the owner's disposition of each failing row.
- [x] **AC-0016.** `docs/specs/workspace-retirement/inventory.toml` governs `tools/compare-registry.py`, `tools/test_compare_registry.py`, and `docs/specs/registry-comparison/*` by rows with owner 5, and `tests/roster/test_workspace_retirement_inventory.py` passes.

## Follow-ons

- The brief's slices 3 (its writer stop), 7, and 8 each run the comparison just before their stop and record its summary in their own spec.

## Assumptions

none
