# Plan: Registry comparison

- **Spec:** [`spec.md`](spec.md)
- **Status:** Executing <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `tools/AGENTS.md` (pure-stdlib tools; the `lint-ci-parity.py` suite roster); `tools/check_closure_terminality_parity.py`, a repository tool that imports sibling skills by path, and `tools/check_view_base_parity.py`, which imports `agentbundle.catalogue_tooling.file_safety`; their tests `tools/test_check_closure_terminality_parity.py` (the `_load` helper over `importlib.util.spec_from_file_location`).

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

## Approach

One new tool, built test-first around a pure classifier, then wired into the repository's records, then run once. The riskiest part is the join between a registry `path` and a navigator id. A throwaway prototype run before this plan rebuilt ids from `Slug:` lines by hand and reported 6 false failing differences, because it kept the `<!-- -->` comment that trails some `Slug:` values. The tool therefore takes paths from the navigator's own graph and never derives an id. A second read-only probe on origin/main `1ecd9b5db` loaded `intent_graph` and the engine by path. `derive(root)` gave a path for all 190 outstanding ids. `list_captured_items` read 77 files with no finding. The engine's two collection tables named exactly the thirteen FEAT-0034 collections.

## Constraints

- The comparison never runs inside `navigate-intents`, which must not read `workspace.toml` (FEAT-0002; RFC-0105 D3).
- `tools/` additions are pure standard library (`tools/AGENTS.md`). The in-repository `agentbundle` package and sibling skill modules load by path, as the anchors do.
- No CI job, schedule, or `make` gate runs the comparison (FEAT-0034 § Registry comparison).
- No registration writer stops here (RFC-0106 D1).

## Construction tests

**Integration tests:** `tools/test_compare_registry.py` runs the CLI end to end over `tmp_path` fixture roots, which drives the real navigator subprocess.
**Manual verification:** none beyond T3's recorded run.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Maintainer procedure: `tools/compare-registry.py` docstring and `--help` | T1 | the `--help` test | `--help` names the classes and exit codes |
| Decision rationale: FEAT-0034 § Registry comparison | T2 | the intent's shaping-review line names the reviewed blob | merged with this spec |
| Verification evidence: `notes/verification-ledger.md` | T3 | the recorded run | AC-0015 holds |
| Current product truth: `inventory.toml` rows | T2 | `tests/roster/test_workspace_retirement_inventory.py` | rows present, suite green |
| Delivery membership: Spec map and `workspace.toml` entry | T2 | `lint-brief-coverage.py` | lint passes |

## Design (LLD)

### Interfaces & contracts

`tools/compare-registry.py`:

- The module sets `sys.dont_write_bytecode = True` before any import by path, so the in-process imports of `intent_graph`, the engine, `closure_terminality`, and `file_safety` write no `__pycache__` under the repository, which is `DIR` on the recorded run (AC-0014).
- `main(argv) -> int` parses `--root` and `--format {text,json}` and gathers the inputs in AC-0019's order: the registry, the navigator envelope, the graph, then the captured listing. The parser's `error` method is overridden to raise `Refusal("arguments", message)`, so a usage error prints the same one line. A `Refusal` is caught once and printed as `refused: <input>: <reason>`. Any other exception is caught at the same point as input `internal`. Both exit 2, so an exception can never read as exit 1.
- The gatherers are `load_registry(root)` (confined read, then `tomllib`), `run_outstanding(root)` (a subprocess `sys.executable -B <navigate_intents.py> query --root <root> --operation outstanding`, with a timeout, then envelope checks), `graph_paths(root)` (`intent_graph.derive(root)` nodes, id to path), and `captured_listing(root)` (the engine's `list_captured_items(root, frozenset())`, refusing on any directory finding or on any item marked `unreadable` or `invalid`). Each raises one `Refusal(input, reason)`. `intent_graph.DerivationError` becomes a `graph` refusal.
- `classify(registry, outstanding, paths, captured, root) -> list[Row]` is pure apart from typed-file status reads, which go through the confined reader. It holds every class rule and is the seam the unit tests drive. A synthesized envelope reaches `result_terminal`, which no real navigator run produces while the navigator's terminality agrees with `close-work`'s.
- `render_text(rows, inputs)` and `render_json(rows, inputs)`. The text form writes each `FAIL` line's target, location, and collections through `json.dumps(..., ensure_ascii=True)`, so a registry string holding a space, a newline, or a control character stays on one line, quoted, and can never forge another summary line (AC-0012).

Owned by: T1

### Data & schema

- Collection names and the initiative-key pattern come from the engine's `_TOP_LEVEL_ENTRY_COLLECTIONS`, `_INITIATIVE_ENTRY_COLLECTIONS`, and `_CANONICAL_INITIATIVE_RE`. The non-terminal and terminal split is written in the tool, cited to FEAT-0034. The two engine tables together name exactly those thirteen collections, and a test pins that equality so an engine change fails loudly.
- An empty `cooled` set is passed to the captured reader on purpose. Cooling governs dispatch, not a file's own `Status:`, and the comparison reads own status.
- A target is checked for canonical form before any filesystem call, then resolved through `file_safety`'s confined reader, which rejects a link, a non-regular file, and an escape from the root.
- The typed-file classification of a target path uses the `workspace-retirement` Terms' globs. Its status is the first `- **Status:**` line's leading word, through `closure_terminality`'s extraction.

Owned by: T1

### Resilience

The navigator subprocess has a timeout of 120 s. Hitting it is a refusal, never a partial result.

Owned by: T1

## Tasks

### T1: The comparison tool

**Depends on:** none

**Touches:** `tools/compare-registry.py`, `tools/test_compare_registry.py`

**Tests:**
- `tools/test_compare_registry.py` builds each fixture root in `tmp_path`. It has `docs/product/intents/`, `docs/product/briefs/`, `docs/specs/<dir>/spec.md`, `docs/product/captured/`, and a `workspace.toml` with an `ini-001` table. It runs the CLI by subprocess for AC-0001, AC-0012, AC-0013, and AC-0014, and calls `classify` for the class cases.
- One case per class and per no-difference rule: AC-0002, AC-0003, AC-0004, AC-0005, AC-0006, AC-0007, AC-0008, AC-0009, and AC-0010. One shared-target case, for AC-0011. `result_terminal` goes through `classify` with a synthesized envelope.
- One case per refusal in AC-0019, each asserting exit 2, the one stderr line, and an empty stdout: each `workspace.toml` defect, a non-table `backlog` and `ini-001.work`, a non-array collection, a navigator failure, an `ok` envelope missing `placed`, the graph failure, and an unreadable and an invalid captured-item file with no entry naming them. The navigator-failure case points `--root` at a tree whose intent lacks `Slug:`, which fails both the navigator and `derive`, so it also proves the navigator refusal wins. The envelope-shape and graph cases replace `run_outstanding` and `graph_paths` through `monkeypatch` and call `main` in-process. One case makes `classify` raise and asserts `refused: internal:` with exit 2.
- AC-0014 hashes every file under the fixture root before and after a CLI run. A second CLI run sets `PYTHONPYCACHEPREFIX` to an empty `tmp_path` directory and asserts that no cache file under the prefix mirrors a source under the repository root, matched on the root's resolved path and on its as-invoked path. As a control, the same check must flag a subprocess that loads the existing `closure_terminality.py` by path, without the flag, under its own fresh prefix. That control writes only into its prefix.
- AC-0006: `spec/a.b` gives `unclassified`, because the engine's rule accepts no `.`.
- AC-0013: a CLI run over a fixture with one `registry_live_only` entry exits 1.
- AC-0018: a `--format json` run returns `schema`, `result`, `counts` with all eight classes, `differences`, and `inputs`, with each row carrying exactly the seven Difference row keys.
- AC-0019: a missing `--root` and a bad `--format` value each give one `refused: arguments:` line with exit 2.
- AC-0020: `--help` output names each class, marks the three failing ones, and names exit codes 0, 1, and 2.
- AC-0017: a decoy `packs/core/.apm/skills/navigate-intents/scripts/navigate_intents.py` under the fixture root exits non-zero, and the run still answers with the real navigator's result.
- AC-0012: a captured `registry_omission` row and a `result_terminal` row carry the item's path as `target`. A missing `path` equal to `ini-001.work.queue[0]` and a no-target entry at that location give two distinct, ordered rows.
- AC-0010 and AC-0012: one fixture whose `path` is `./docs/product/intents/a.md` gives `unclassified` plus a `registry_omission` for `a`. One fixture whose `path` holds a space and a newline gives exactly one `FAIL` line, with the target JSON-quoted.
- The collection-table pin from the design's Data & schema.
- A stub, red before T1:

```python
def test_registry_omission_for_unregistered_intent(tmp_path):
    _intent(tmp_path, "a", status="Draft")
    _registry(tmp_path, "")
    out = _run(tmp_path)
    assert out.returncode == 0
    assert "registry_omission 1" in out.stdout.splitlines()
```

**Done when:** `tools/test_compare_registry.py` passes and `make lint-ruff lint-mypy` is clean.

### T2: Records and wiring

**Depends on:** T1

**Touches:** `docs/specs/workspace-retirement/inventory.toml`, `Makefile`, `tools/lint-ci-parity.py`, `docs/product/briefs/workspace-registry-retirement-delivery.md`, `docs/product/intents/FEAT-0034-workspace-registry-retirement.md`, `workspace.toml`

**Tests:**
- `tests/roster/test_workspace_retirement_inventory.py` passes with three new rows: `tools/compare-registry.py` as `reader`, `tools/test_compare_registry.py` as `fixture`, and `docs/specs/registry-comparison/*` as `contract`, each with owner 5. This covers AC-0016.
- `tools/test_compare_registry.py` is added to the `Makefile`'s `run-test-suite` define with a `NO_PR_GATE` entry in `lint-ci-parity.py`'s `SUITE_DISPOSITION`. `tools/test-lint-ci-parity.py` and `python3 tools/lint-ci-parity.py` pass.
- `lint-brief-coverage.py` passes with this spec in the brief's Spec map and in `ini-002`'s `work` collection matching its `Status:`.
- FEAT-0034's `Shaping-reviewed` header carries the date of the isolated intent-mode review of the amendment, which runs during spec shaping. Its § Shaping review names that review's blob.

**Done when:** the four checks in Tests pass.

### T3: Run over this repository

**Depends on:** T2

**Touches:** `docs/specs/registry-comparison/notes/verification-ledger.md`

**Tests:**
- One run of `python3 tools/compare-registry.py --root .` at a commit on this branch, recorded as AC-0015 states. A failing row stops the task for the owner, under the spec's Ask-first rule.

**Done when:** the ledger holds the run, and the owner has disposed any failing row.

## Rollout

- **Delivery:** a repository tool, used by maintainers only, with no flag. Reverting the PR removes it, and nothing else reads it.
- **Infrastructure / External-system integration / Deployment sequencing:** none.

## Risks

- The navigator and the engine are imported by path, so a later rename in either breaks the tool at import time. That is a loud failure, caught by T1's suite.
- Slice 6 edits `inventory.toml` concurrently. Keep this change's rows contiguous and rebase when slice 6 lands.

## Changelog

- 2026-10-27: spec approved by eugenelim
- 2026-10-27: plan approved by eugenelim
