# Plan: Lint traceability intent parity

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done
- **Constrained by:** RFC-0103 D2; RFC-0105 D1; ADR-0007; ADR-0074
- **Repository anchors:** the navigator's `_preamble_visible`, `_normalize_kind_level` and `_compute_node_id` in `packs/core/.apm/skills/navigate-intents/scripts/intent_graph.py`; the existing hand-mirror in `packs/core/.apm/skills/work-loop/scripts/lint-graph-pointers.py` (`_preamble`, `_registered_kind`); the cross-port parity precedent `packs/core/tests/skills/navigate-intents/test_related_intents_lint_parity.py`; the roster precedent `tests/roster/test_graph_pointer_authoring.py` and its CI wiring.
- **Retention:** repository-durable spec, plan and `notes/verification-ledger.md`. Implementers, reviewers, resuming agents and CI read them. After closeout, source docstrings, the suites, the architecture page and the release fragment own current truth.

## Constraints

- One slice PR targets `main`. No commit, push or merge without the owner's approval. No bare `git stash`.
- Skill scripts are standard-library only (ADR-0074) and import no other skill. The navigator's rule is mirrored by hand, and the tests pin the mirror.
- A pack test reads only inside `packs/core/`. The real-corpus check reads `docs/product/intents/`, so it lives in `tests/roster/`, anchored at `Path(__file__).resolve().parents[2]` (`tests/AGENTS.md`).
- Test modules load skill scripts by path under unique `core_<skill>_…` names (`packs/AGENTS.md`).
- Local gate: `make lint-ruff lint-mypy`, the touched suites, and one `make build-check` before the first push. `test-corpus.yml` and `test-roster.yml` are dispatched on the PR branch.
- Use the Python 3.13 interpreter at `$HOME/.pyenv/versions/3.13.13/bin/python3` locally; CI runs 3.11, so no 3.12+ syntax.
- Expected review shape: DEEP for T1 (a reader change in a gate script); WIDE for T3 and T4 wiring.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Lint docstrings (current product truth) | T1 | Fixture suite green | Docstrings name the preamble-only reading |
| Architecture § 8 ladder-marker sentence | T1 | Diff of that sentence | Sentence names the preamble |
| Release fragment, versions, eval case | T4 | Catalogue verify; eval JSON checks | Core is one patch above `main` |
| Verification ledger | T3, T4 | Corpus counts; CI run ids | Ledger names the verified head |

## Design (LLD)

### Behavior & rules

Owned by: T1

Traces to: AC-0001, AC-0002, AC-0003.

The lint gains one preamble field reader for intent files. It reuses the existing `_visible_intent_preamble`, which hides HTML comments and stops at the first visible `## ` line. It then matches the navigator's field-line grammar, `^- \*\*([^*:]+):\*\*\s*(.*)$`, on each visible line. The field name is exact-case, and every value of each field is kept in order. Each value first takes the navigator's value normalization, the resolver's `_normalize`: strip a trailing comment, then one wrapping pair of backticks.

- Kind and Level then take a hand copy of the navigator's `_normalize_kind_level`: strip a trailing comment, cut at ` (`, ` →` or `<!--`, strip one wrapping pair of backticks, then lowercase the first word. The kind is the first `Kind:` value when it is `outcome` or `opportunity`. Otherwise it is `capability` when the first `Level:` value is `capability`. Otherwise the file is not a ladder rung.
- Slug is the first `Slug:` value, passed through the lint's existing `_token` and `_is_placeholder`. For every slug the navigator admits (`^[a-z0-9]+(?:-[a-z0-9]+)*$`, optionally in backticks) other than `none`, this gives the navigator's value. `recognize_ladder` falls back to the filename stem. `recognize_intents` keeps its note and creates no node.
- A file is a tombstone when its preamble fields contain `Tombstone`, whatever the value. `_is_tombstone` takes this reading. `recognize_ladder` skips tombstones before classifying, so a retired ladder file no longer collides with its reissue.

`_intent_preamble_field`, which serves `Outcome co-owner:`, keeps its `field_re` matching unchanged. So do brief recognition and spec pointer reads.

**Residual differences the hand copy does not cover.** The real-corpus check catches each of these if a corpus file ever reaches it:

- File admission: the lint reads every non-`_` `*.md` file, while the navigator admits `^[A-Za-z0-9][A-Za-z0-9._-]*\.md$`.
- Read limit: the lint's per-file cap is 8 MiB, while the navigator's is 1,000,000 bytes and fails the whole derivation past it.
- Slug `none`: the navigator registers `intent:none`, while the lint treats `none` as a placeholder under AC-0002.

### Interfaces & contracts

Owned by: T2, T3

Traces to: AC-0004, AC-0005.

The fixture suite (T2) builds a temporary root per case and observes three ports for each fixture file:

- **The lint:** `recognize_ladder`, then `recognize_intents` with `claimed=set(ladder.values())`, inverted to a map from path to the set of ids.
- **The navigator:** `intent_graph.derive(root)`, taking its `type == "intent"` nodes.
- **`lint-graph-pointers.py`:** `_registered_kind(_preamble(text))` and `any(_preamble(text).get("Tombstone", []))`.

The roster check (T3) uses the same lint and navigator calls on the repository root and `docs/product/intents/`. It loads both modules from `packs/core/.apm/` sources. It compares the two maps over the union of their paths, and reports every differing path in one failure message. A `DerivationError` from the navigator fails the test. Non-vacuity: the navigator ids must include all four kinds. The verification ledger records the corpus counts.

Some fixtures already pass against the current lint; the ledger records which ones T1 turns from red to green, run against the unchanged lint before T1's source edit.

### Dependencies & integration

Owned by: T2, T3

- The fixture suite is a new `_pytest_step("test-lint-traceability-intent-parity", …)` in `tools/repo/build_gate_chain.py`. It sits directly after `test-lint-traceability`, and `EXPECTED_SCRIPT_STEPS` in `tools/test_build_gate_chain.py` gains it.
- The roster check gets a named step in `.github/workflows/build-check.yml`, placed beside `pytest graph-pointer authoring sources (roster-owned)`, above the bulk roster step. It carries the same `if:` guard.
- In `tools/lint-ci-parity.py`, its `STEP_DISPOSITION` entry is `LOCAL("test-after-build-check")`, and `_GATE_MAIN_CHECKS` gains its name.
- The test names no `docs/specs/` literal, so `.workspace-prune-protected.toml` is unchanged.

## Tasks

### T1: The lint reads an intent's kind, slug and retirement from its visible preamble

**Depends on:** none

**Verification mode:** TDD

**Touches:** `packs/core/.apm/skills/work-loop/scripts/lint-traceability.py`, `packs/core/tests/skills/work-loop/test_lint_traceability_intent_parity.py`, `docs/architecture/work-intake-and-artifact-routing.md`

**Tests:**
- **VI-1001.** In the new `test_lint_traceability_intent_parity.py`, a parameterized case per AC-0001 fixture asserts the lint's id set for the file. The expected ids are written in the test, not computed (AC-0001).
- **VI-1002.** Slug cases: a body-only `Slug:`, a comment-only `Slug:`, a ladder file with no preamble `Slug:` (stem id), a non-ladder file with no preamble `Slug:` (no node, one note naming it), and a non-ladder file whose `Slug:` is `none` (no node, one note) (AC-0002).
- **VI-1003.** Tombstone cases: `Tombstone:` with `Kind: outcome`, an empty-valued preamble `Tombstone:`, a body-only `Tombstone:`, and a comment-only `Tombstone:` (AC-0003).
- **VI-1004.** The existing `test_lint_traceability.py`, `test_lint_traceability_delivery_checks.py` and `test_lint_traceability_delivery_checks_vi.py` pass unchanged.

**Done when:** VI-1001 to VI-1004 pass, and the docstrings and the architecture sentence state the preamble reading.

### T2: Three ports agree on every fixture, as a gate-chain step

**Depends on:** T1

**Verification mode:** TDD

**Touches:** `packs/core/tests/skills/work-loop/test_lint_traceability_intent_parity.py`, `tools/repo/build_gate_chain.py`, `tools/test_build_gate_chain.py`

**Tests:**
- **VI-2001.** Over the VI-1001 and VI-1003 fixtures, a parameterized case per fixture observes the three ports as AC-0004 states. The VI-1002 slug fixtures and the empty-valued `Tombstone:` fixture are not in this set (AC-0004).
- **VI-2002.** `tools/test_build_gate_chain.py` passes with the new step in `EXPECTED_SCRIPT_STEPS` (AC-0006).

**Done when:** VI-2001 and VI-2002 pass.

### T3: The real corpus is compared on every pull request

**Depends on:** T1

**Verification mode:** goal-based check

**Touches:** `tests/roster/test_lint_traceability_intent_parity.py`, `.github/workflows/build-check.yml`, `tools/lint-ci-parity.py`

**Tests:**
- **VI-3001.** The roster test passes on the real corpus. The same module's comparison runs on three temporary roots, never the real one, and each run must fail:
  - a file named `a b.md` that the lint reads and the navigator does not admit, with the failure naming that path;
  - a live intent with no `Slug:`, which raises the navigator's `DerivationError`;
  - a corpus with no `outcome` intent, which fails as vacuous.

  (AC-0005)
- **VI-3002.** `python3 tools/lint-ci-parity.py` and `python3 tools/test-lint-ci-parity.py` pass, with the new step registered (AC-0006).

**Done when:** VI-3001 and VI-3002 pass, and the ledger records the corpus counts.

### T4: The Core patch release is projected and verified

**Depends on:** T1, T2, T3

**Verification mode:** goal-based check

**Touches:** `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`, `packs/core/.apm/skills/work-loop/evals/evals.json`, `docs/product/changelog.d/`, generated projections

**Tests:**
- **VI-4001.** Bump Core to the next patch above `main`, add one changelog fragment with Highlights, and add one work-loop eval on a body-only `Kind:`. Then commit, run `make build-self`, and run `agentbundle catalogue verify --root .` with no drift (AC-0007).
- **VI-4002.** `make build-check` passes locally once before the first push. `test-corpus.yml` and `test-roster.yml` are dispatched on the PR branch and their run ids recorded in the ledger.

**Approach:** Grep for hash and content pins on every edited file before committing. `make build-self` refuses a dirty tree, so commit first, then regenerate.

**Done when:** VI-4001 and VI-4002 pass and the PR's checks are green.

## Rollout

Core's next patch release ships the reader change. It changes no node id in the current corpus. Rollback reverts the slice commit.

## Risks

- An adopter intent with `Kind:` below its preamble, inside a comment, or on a lowercase label loses its ladder node. That node now matches what the navigator shows. The release fragment says so.
- `main` may move before landing. Re-check the Core version and re-run the corpus check after any merge from `main`.

## Changelog

- 2026-10-21: spec and plan approved together by the repository owner. Shaping review: round 1 four findings, round 2 one, round 3 clean. Adversarial review: round 1 three sustained, round 2 two refuted (clean), round 3 clean. Reports are under `.context/reviews/631a259c-68f2-484a-8273-5da4e904e54a/`. The owner accepted the empty-`Tombstone:` gap in `lint-graph-pointers.py`.
- Approved reviewed revisions, before lifecycle-only approval annotations: spec SHA-256 `b071ed0c9ec8b857f02b7de8f07b7b9b5548f6e8d9a9f8561b2bb8e8b885330a`; plan SHA-256 `402062ba6bc9f29f06f902300cd1ddc7683ef07b18ca7ac4b3a4af94ad269b09`.
