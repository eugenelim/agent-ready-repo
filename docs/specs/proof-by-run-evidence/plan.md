# Plan: proof-by-run evidence

- **Spec:** [`spec.md`](spec.md)
- **Status:** Executing <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `packs/AGENTS.md` (version bump, self-host, eval harness, no internal citations, UTF-8 streams); `tests/AGENTS.md` (roster placement and its three wiring edits); `_review_assessment.assess_finding_actual_failure` and `test_review_assessment.py` as the analogous pure predicate and its tests; `_supervisor_readiness.report_readiness` as the `assess-finding` admission seam; `_supervisor_git.HardenedGit` as the only Git launcher; `test_supervisor_review_gate.py` with `supervisor_harness` as the analogous integration test; `docs/specs/verify-entries/` as the analogous guidance-plus-roster delivery.

> **Plan contract:** this is the implementation strategy. After approval, a
> change needs an **amendment** only when it touches the spec's protected
> sections (contract, scope and non-goals, durable outputs, agent rules, testing
> strategy, acceptance criteria, accepted risk) or its `Terminal Intent`. A change
> to tasks, tests, stubs, design, or approach needs none: the controller makes it
> as an in-envelope working-plan change while no execution attempt is open, and
> the run continues with every finished task still finished. Execution
> observations belong in `docs/specs/<feature>/notes/verification-ledger.md` (or
> the adopter's equivalent). A genuine error in a protected section follows the
> controlled-amendment path.
>
> **Not every field is contract.** `Touches`, `Tests` and `Done when` are what a
> completion gate reads. `Design`, `Approach`, `Grounding` and `Risks` are working
> material the controller corrects in place, before or after approval, while no
> attempt is open.

## Approach

The pure predicate lands first (T1), because the supervisor check (T2), the `proof-run` CLI (T4), and the roster fit test (T6) all call it. The `git-history` module (T3) is independent of T1 and carries the security boundary, so its refusal tests are written red before any Git call exists. Guidance and evals (T5) follow the code they describe. The captured amendment request and its Follow-ons link are a controller commit made before `start`. The release (T8) is last. `HardenedGit.run` returns stdout and raises on a non-zero exit unless `check=False`; T3 and T4 confirm it serves every form the entry launches without a helper edit, and a needed helper change is a plan correction, not an amendment.

## Constraints

- ADR-0155 fixes the git-history entry's forms, value sources, and controls; D7 forbids widening them here.
- ADR-0154: the subject commit is the product ref's commit, which `HEAD` equals whenever a supervisor verb acts; `evidence-gate.py` reads `HEAD`, and the supervisor check reads `_supervisor_readiness.result_lineage(ws, state)[1]`.
- `finding-assessment.v1` and `evidence-receipt.v1` are consumed unchanged. `evidence_refs` are opaque strings the store does not resolve, so the proof-run reference carries its own commit and digest.
- `HardenedGit.run(..., check=False)` returns stdout only; ancestry is decided by `merge-base <base> <head>` equal to `<base>`, and presence by `cat-file -t <base>:<path>` printing `blob`.
- The supervisor pins every file under `scripts/` by digest at `start`; a run of this change starts from the installed copy (`.claude/skills/work-loop/scripts/work-supervisor.py`), and pack-source edits reach it through `regenerate`.
- The supervisor protects the spec directory during a worker attempt; ledger records and the captured item are controller commits between attempts.
- A pack test may not read `contracts/` or `guides/`; schema fit lives in `tests/roster/`.

## Construction tests

**Integration tests:** T2's supervisor admission tests, gated by `WORK_SUPERVISOR_INTEGRATION=1`.
**Manual verification:** none.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Maintainer procedure | T5 | content tests green | suites green at the delivery commit |
| Interface compatibility | T6, closeout | `test_proof_by_run_contract_fit.py` green | schema diff recorded empty in the ledger |
| Decision rationale | none — ADR-0155 committed before approval | ADR file | cited in `Constrained by:` |
| Product direction | none — controller commit before `start` | captured item present | linked from Follow-ons; ledger records AC-0023 at delivery |
| Release history | T8 | version-equality assertion; fragment | `check-core-release.py` result recorded |

## Design (LLD)

### Design decisions

Owned by: T1, T2, T3, T4.

**Run envelope.** Canonical JSON (sorted keys, no spaces, ASCII) of `{"command_sha256", "exit_status", "stderr_sha256", "stdout_sha256", "subject_commit"}`. Its SHA-256 is the reference digest. The envelope file stored at `.context/proof-runs/<sha256 of assessment id>-<envelope digest>.json` also holds the raw command, stdout, and stderr for audit; the digest covers only the five fields, so the raw bytes are checked against their own digests on read.

**When the run is made.** Between `next` issuing the finding's `assess-finding` request and `report`, no supervisor step commits, so `HEAD` is the result commit for the whole window. Only the `proof-run` invocation is bound to the commit: an invocation made before an earlier finding's assessment was admitted is refused by the supervisor, and is redone inside the open request, which writes a new envelope. When the command itself ran is the controller's attestation.

**Predicate.** `proof_by_run_assessment(*, assessment_id, report_id, finding_id, review_subject_fingerprint, observed, envelope, current_subject_commit, judgment_authority) -> dict`. Mapping: envelope commit differs from current → refuse `denied-proof-run-stale`; `observed == "fail"` → `supported`; `observed == "pass"` → `unsupported-opinion`. Built through the existing `_assessment_record` path so `validate_finding_assessment_dict` runs on every output. Refusals raise `ReviewAssessmentRefused` with `denied-invalid-proof-run-observation`, `denied-invalid-proof-run-commit`, or `denied-invalid-proof-run-envelope`.

**Consistency check.** `check_proof_by_run(assessment, subject_commit) -> str | None` returns a denial code or `None`; it inspects only records whose `lineage.predicate_version` is `proof-by-run.v1`. `report_readiness` calls it for `assess-finding` before `write_assessment` and raises `Refusal("review-record-refused", "controller", code)` on a code, so nothing is written and `HEAD` does not move.

**git-history module.** `_git_history.py` exposes `git_history(git, *, base, path) -> dict` and raises `GitHistoryRefused(code)`. Order, so that no caller value reaches a launch before it is replaced by a trusted one: refuse arguments outside one `--path` and an optional `--base` in the CLI parser (`denied-not-in-catalog`); refuse a supplied base unless `re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", base)` (`denied-ref-form`); refuse a path under `.context/` by its first segment (`denied-artifact-path`); refuse object sources from `git.pins` (`objects/info/alternates` under the common dir) and `git.config_entries()` (`extensions.partialclone`, `remote.*.promisor`) (`denied-object-source`); refuse a non-empty `_supervisor_git.code_running_keys(git.config_entries())` (`denied-git-config`); resolve `HEAD^{commit}`; resolve `symbolic-ref -q refs/remotes/origin/HEAD` (`denied-no-change-base` when empty) and compute the change base with `merge-base <head> <default-ref>`; refuse a supplied base that does not byte-equal it (`denied-ref-outside-subject-history`); compute the path set with `diff --name-only -z --no-renames <base> <head>`; select the member byte-equal to the caller's path or refuse (`denied-path-not-in-change`); only then run `cat-file -t <base>:<member>`, `cat-file -s`, `rev-parse --verify <base>:<member>` for the blob ID, `show` when the size is within the content cap, and `log --format=%H --max-count=51 <base>..<head> -- <member>` with literal pathspecs. Content cap 256 KiB; the envelope is checked against 1 MiB before it is printed. The helper's in-memory capture of `diff --name-only` for a very large change is an accepted limit (ADR-0155 D5).

**CLI.** `evidence-gate.py` with subcommands `proof-run` and `git-history`, argparse with `allow_abbrev=False`, UTF-8 stream reconfiguration, sibling modules loaded by path as `_review_assessment.py` does. Exit 0 prints JSON; a refusal prints `{"refused": "<code>", "detail": "<fixed remedy text for that code, naming the condition to fix>"}` to stdout and exits 2. `proof-run` refuses code-running config the way `git-history` does, then checks the tracked tree with `status --porcelain=v1 -z --untracked-files=no --ignore-submodules=dirty` through `HardenedGit` (a submodule whose checked-out commit differs from `HEAD`'s gitlink still shows; no status runs inside a submodule, so no filter it configures runs), reads its three inputs with `_file_safety.read_confined_regular_file(<checkout>/.context, path, max_bytes=1 MiB)` after refusing a path whose directories include `.context/reviews/` or `.context/proof-runs/` by device and inode identity (so a case variant on a case-folding file system is refused), refuses a symbolic-link `.context/proof-runs`, and creates the envelope with `_confined_mutation.confined_create`; when the path already exists it first reads it with `read_confined_regular_file` and exits 0 on identical bytes, refusing otherwise.

### Failure, edge cases & resilience

Owned by: T3.

- A path with a newline or a leading `-` that is a real changed path is still a set member; `-z` parsing and the `<oid>:<path>` single argument plus `--` before the log pathspec keep it inert.
- A deleted path is in the change set; `show` at base returns its base content and the log lists the deleting commit.
- A change base equal to `HEAD` gives an empty change set, so every path refuses.
- `refs/remotes/origin/HEAD` is absent in a clone made without it; `git remote set-head origin --auto` sets it, and that refusal's `detail` names that remedy.

## Tasks

### T1: Proof-by-run predicate

**Depends on:** none

**Touches:** `packs/core/.apm/skills/work-loop/scripts/_review_assessment.py`, `packs/core/tests/skills/work-loop/test_proof_by_run.py`

**Tests:** TDD — unit, at `_review_assessment`
- AC-0001, AC-0002, AC-0003, AC-0004: test functions named `test_t1_…`, with subject, report, and finding helpers created in `test_proof_by_run.py` on the shape of `test_review_assessment.py`'s private `_review_subject`, `_report`, and `_finding`.

**Done when:** `python3 -m pytest packs/core/tests/skills/work-loop/test_proof_by_run.py -q -k t1_` exits 0.

### T2: Supervisor refuses an inconsistent proof-by-run assessment

**Depends on:** T1

**Touches:** `packs/core/.apm/skills/work-loop/scripts/_review_assessment.py`, `packs/core/.apm/skills/work-loop/scripts/_supervisor_readiness.py`, `packs/core/tests/skills/work-loop/test_proof_by_run.py`

**Tests:** TDD — integration, through `supervisor_harness` to the first `assess-finding` request, as `test_supervisor_review_gate.py` does
- AC-0005: one parametrized case per refusal shape; each asserts the refusal code and `HEAD` unchanged.
- AC-0006: a consistent `supported` record is admitted and the next commit carries a `repair-request`; a record with the harness's default predicate version is admitted unchanged.

**Done when:** `WORK_SUPERVISOR_INTEGRATION=1 python3 -m pytest packs/core/tests/skills/work-loop/test_proof_by_run.py -q -k t2_` exits 0, and `WORK_SUPERVISOR_INTEGRATION=1 python3 -m pytest packs/core/tests/skills/work-loop/test_supervisor_review_gate.py packs/core/tests/skills/work-loop/test_supervisor_review_closure.py packs/core/tests/skills/work-loop/test_supervisor_results.py -q` exits 0.

### T3: git-history entry and its refusals

**Depends on:** none

**Touches:** `packs/core/.apm/skills/work-loop/scripts/_git_history.py`, `packs/core/.apm/skills/work-loop/scripts/evidence-gate.py`, `packs/core/tests/skills/work-loop/test_git_history_evidence.py`

**Tests:** TDD — integration, in temporary Git repositories with a bare `origin` remote and `refs/remotes/origin/HEAD` set, through `evidence-gate.py`'s `main`, with `_supervisor_git._launch` wrapped by a spy that records each argument vector
- AC-0009, AC-0015: a base commit on `origin`, an added path, a modified path, and a path touched by 51 commits for the log bound.
- AC-0010, AC-0011, AC-0012, AC-0013, AC-0027, AC-0028, AC-0031: one test per refusal family; each asserts the code and the spy's substring check.
- AC-0033: a function-scoped spy fixture used only by the covered tests asserts, at teardown, a launch list inside the allowed set that is empty for the refusal tests the criterion exempts and non-empty for every other covered test, so the check runs with every test whatever the order or `-k` filter.
- AC-0014, AC-0029: a blob over the content cap; a changed path named `-x` and one named `:(glob)*`.
- AC-0030: an `ast` walk over both files.

**Done when:** `python3 -m pytest packs/core/tests/skills/work-loop/test_git_history_evidence.py -q` exits 0.

### T4: proof-run CLI

**Depends on:** T1, T3

**Touches:** `packs/core/.apm/skills/work-loop/scripts/evidence-gate.py`, `packs/core/tests/skills/work-loop/test_proof_by_run.py`

**Tests:** TDD — integration, in a temporary Git repository through `main`
- AC-0007: the printed record's reference digest recomputes from the created envelope file, and the spy shows only Git launches.
- AC-0032: a redo after a test commit, and an identical rerun.
- AC-0008: a dirty tracked file, an existing envelope path holding different bytes, an envelope path that is a symbolic link, a symbolic-link `.context/proof-runs`, an input outside `.context/`, an input under `.context/reviews/`, a FIFO input, and a stdout file over 1 MiB each refuse with no envelope written.

**Done when:** `python3 -m pytest packs/core/tests/skills/work-loop/test_proof_by_run.py -q -k t4_` exits 0.

### T5: Guidance and eval cases

**Depends on:** T2, T3, T4

**Touches:** `packs/core/.apm/skills/work-loop/SKILL.md`, `packs/core/.apm/skills/work-loop/references/finding-adjudication.md`, `packs/core/.apm/skills/work-loop/references/supervisor.md`, `packs/core/.apm/skills/work-loop/evals/evals.json`, `packs/core/tests/skills/work-loop/test_proof_by_run.py`, `packs/core/tests/skills/work-loop/test_git_history_evidence.py`

**Tests:** no stub (goal-based — content check)
- AC-0016: reads the bounded section, and compares its sentences with the section read from `git show <merge-base>:<path>` only at delivery; the standing test asserts the new statements and the existing pinned phrase in `test_finding_adjudication_contract.py`.
- AC-0017, AC-0018, AC-0019: bounded-section reads in `test_proof_by_run.py`.
- AC-0021: the three case ids and their fields.

**Done when:** `python3 -m pytest packs/core/tests/skills/work-loop/test_proof_by_run.py packs/core/tests/skills/work-loop/test_git_history_evidence.py packs/core/tests/pack/test_finding_adjudication_contract.py packs/core/tests/skills/work-loop/test_evidence_modes_contract.py -q` exits 0.

### T6: Contract fit roster test

**Depends on:** T1

**Touches:** `tests/roster/test_proof_by_run_contract_fit.py`, `.github/workflows/build-check.yml`, `tools/lint-ci-parity.py`

**Tests:** no stub (goal-based — schema validation)
- AC-0020: loads `_review_assessment.py` by path under a unique module name and validates the two outputs with `Draft202012Validator`, resolving `review-subject.v1` through a local registry.
- Wiring: a named build-check step above the bulk `pytest tests/ -q` step, and a `LOCAL("test-after-build-check")` disposition in `lint-ci-parity.py`.

**Done when:** `python3 -m pytest tests/roster/test_proof_by_run_contract_fit.py -q` exits 0, and `python3 tools/lint-ci-parity.py` exits 0.

### T9: Identical proof-run rerun holds for every accepted input

**Depends on:** T4

**Touches:** `packs/core/.apm/skills/work-loop/scripts/evidence-gate.py`, `packs/core/tests/skills/work-loop/test_proof_by_run.py`

**Tests:** TDD — integration through `main`
- AC-0032: a 1 MiB stdout full of control and non-ASCII bytes is accepted, and an identical rerun at the same `HEAD` exits 0 without writing.

**Done when:** `python3 -m pytest packs/core/tests/skills/work-loop/test_proof_by_run.py -q -k t9_` exits 0.

### T10: proof-run tree check runs no configured program

**Depends on:** T4

**Touches:** `packs/core/.apm/skills/work-loop/scripts/evidence-gate.py`, `packs/core/tests/skills/work-loop/test_proof_by_run.py`

**Tests:** TDD — integration through `main`
- AC-0007: a submodule whose own config defines a clean filter that a committed `.gitattributes` selects, with a stat-dirty file, runs no filter program (a marker file stays absent).
- AC-0008: a submodule checked out at a commit other than the one `HEAD` records refuses with `denied-tree-dirty` and writes no envelope.
- AC-0008: local code-running config refuses with `denied-git-config` before any launch other than the helper's pinning and config reads.

**Done when:** `python3 -m pytest packs/core/tests/skills/work-loop/test_proof_by_run.py -q -k t10_` exits 0.

### T11: Input exclusion holds on case-insensitive file systems

**Depends on:** T4

**Touches:** `packs/core/.apm/skills/work-loop/scripts/evidence-gate.py`, `packs/core/tests/skills/work-loop/test_proof_by_run.py`

**Tests:** TDD — integration through `main`
- AC-0008: on a file system that folds case (probed at test time), an input named through a case variant of `.context/reviews/` or `.context/proof-runs/` refuses with `denied-input-path` and writes no envelope; elsewhere that test skips with the probe result as its reason.
- AC-0008: on any file system, a unit test drives the exclusion helper with injected directory identities and fails if it compares names instead of `(st_dev, st_ino)`.

**Done when:** `python3 -m pytest packs/core/tests/skills/work-loop/test_proof_by_run.py -q -k t11_` exits 0.

### T12: Proof-by-run check and refusal paths are pinned in the default lane

**Depends on:** T2, T4

**Touches:** `packs/core/.apm/skills/work-loop/scripts/evidence-gate.py`, `packs/core/tests/skills/work-loop/test_proof_by_run.py`

**Tests:** TDD — unit and integration
- AC-0005: a default-lane test pins each `check_proof_by_run` outcome by its exact return value (each denial code, a non-proof-by-run version, consistent `fail` and `pass`); each T2 refusal case asserts its specific denial code in the refusal detail.
- AC-0008: `denied-proof-run-invalid` (an empty `--report-id`), `denied-envelope-write` (an unwritable `.context/proof-runs`), and a helper Git refusal (run outside a repository) each exit 2 with valid JSON and leave no envelope.

**Done when:** `python3 -m pytest packs/core/tests/skills/work-loop/test_proof_by_run.py -q -k t12_` exits 0, and `WORK_SUPERVISOR_INTEGRATION=1 python3 -m pytest packs/core/tests/skills/work-loop/test_proof_by_run.py -q -k t2_` exits 0.

### T13: Guidance wording and the amended launch check

**Depends on:** T5, T12

**Touches:** `packs/core/.apm/skills/work-loop/references/finding-adjudication.md`, `packs/core/tests/skills/work-loop/test_git_history_evidence.py`, `packs/core/tests/skills/work-loop/test_proof_by_run.py`

**Tests:** TDD — integration and content
- AC-0016: the shipped `git-history` subsection says up to 50 commits are reported and a 51st marks the list truncated, and says to run the entry from the checkout root.
- AC-0033: the T3 fixture's empty-list branch applies to exactly the tests AC-0033 exempts, in both test files.

**Done when:** `python3 -m pytest packs/core/tests/skills/work-loop/test_proof_by_run.py packs/core/tests/skills/work-loop/test_git_history_evidence.py packs/core/tests/pack/test_finding_adjudication_contract.py packs/core/tests/skills/work-loop/test_evidence_modes_contract.py -q` exits 0.

### T14: proof-run refuses outside object sources, and the round-2 test gaps close

**Depends on:** T10, T11, T12

**Touches:** `packs/core/.apm/skills/work-loop/scripts/evidence-gate.py`, `packs/core/.apm/skills/work-loop/scripts/_git_history.py`, `packs/core/tests/skills/work-loop/test_proof_by_run.py`

**Tests:** TDD — integration through `main` and unit
- AC-0007: a repository with an alternates file, an `extensions.partialClone` setting, or a promisor remote makes `proof-run` refuse `denied-object-source` with no launch beyond the helper's pinning and config reads, so no lazy fetch can start; the check is the one `git-history` already uses.
- AC-0008: run from a temp directory outside any repository, `proof-run` refuses with the helper-Git refusal's exact code, under the launch spy.
- AC-0008: on any file system, a test stubs the directory-identity lookup in `evidence-gate.py` so a differently named directory under `.context/` reports the identity of `.context/reviews`, and `proof-run` refuses `denied-input-path`; it fails if `_input_file` stops calling the identity check.
- AC-0005: the `check_proof_by_run` outcome table gains a single non-string reference, expecting `denied-proof-run-reference-count`.

**Done when:** `python3 -m pytest packs/core/tests/skills/work-loop/test_proof_by_run.py packs/core/tests/skills/work-loop/test_git_history_evidence.py -q` exits 0.

### T8: Core release

**Depends on:** T1, T2, T3, T4, T5, T6, T9, T10, T11, T12, T13, T14

**Touches:** `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`, `docs/product/changelog.d/*.md`, adapter projections

**Tests:** no stub (goal-based — release check)
- AC-0024: the version-equality assertion the pack suite already carries, plus a ledger record of the merge-base version and the new one.
- AC-0026: the catalogue commands' exit status and a clean tree after self-host.

**Done when:** `PYTHONPATH=packages/agentbundle python3 -m agentbundle catalogue lint --root . --deep` and `... catalogue verify --root .` exit 0, and the ledger records AC-0022, AC-0023, AC-0024, AC-0025, AC-0026, and the merge-base halves of AC-0016 and AC-0019.

## Rollout

Ships in the next core patch. A run in flight picks up the supervisor check only through `regenerate`; an assessment without `proof-by-run.v1` is admitted exactly as before, so no run changes behavior until a controller records a proof-by-run assessment.

## Risks

- The reference is a controller attestation. A controller can record `observed: fail` for a run that showed nothing, or write a reference without running `proof-run` at all; the supervisor checks only consistency and the commit, the judgment authority is named, and a real run leaves an envelope an auditor can recompute.
- The after-fix run stays prose until the captured amendment lands.

## Changelog

- 2026-11-03: spec approved by eugenelim (scope).
- 2026-11-03: plan approved by eugenelim (build strategy).
- 2026-11-03: amendment drafted: AC-0033 excludes tests of refusals the entry makes before its first Git launch; repair tasks T9 to T13 added from implementation review.
- 2026-11-03: amendment approved by eugenelim (scope and build strategy).
