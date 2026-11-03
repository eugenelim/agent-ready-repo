# Plan: proof-by-run evidence

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
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

The pure predicate lands first (T1), because the supervisor check (T2), the `proof-run` CLI (T4), and the roster fit test (T6) all call it. The `git-history` module (T3) is independent of T1 and carries the security boundary, so its refusal tests are written red before any Git call exists. Guidance and evals (T5) follow the code they describe. The captured amendment (T7) is a controller commit outside the spec directory. The release (T8) is last. A spike before review ran every Git form the entry needs through `HardenedGit` in a scratch repository: `rev-parse --verify HEAD^{commit}`, `diff --name-only -z --no-renames`, `merge-base`, `cat-file -t` and `-s`, `show <oid>:<path>`, and `log --format=%H <base>..<head> -- <path>` with literal pathspecs all returned the expected bytes, so the helper needs no edit.

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
| Product direction | T7 | captured item present | linked from Follow-ons |
| Release history | T8 | version-equality assertion; fragment | `check-core-release.py` result recorded |

## Design (LLD)

### Design decisions

Owned by: T1, T2, T3, T4.

**Run envelope.** Canonical JSON (sorted keys, no spaces, ASCII) of `{"command_sha256", "exit_status", "stderr_sha256", "stdout_sha256", "subject_commit"}`. Its SHA-256 is the reference digest. The envelope file stored under `.context/proof-runs/<sha256 of assessment id>.json` also holds the raw command, stdout, and stderr for audit; the digest covers only the five fields, so the raw bytes are checked against their own digests on read.

**When the run is made.** Between `next` issuing the finding's `assess-finding` request and `report`, no supervisor step commits, so `HEAD` is the result commit for the whole window. A run made at FIX time, or before an earlier finding's assessment was admitted, is bound to a commit the next step moves past, and the predicate or the supervisor refuses it. A stale run is redone inside the open request.

**Predicate.** `proof_by_run_assessment(*, assessment_id, report_id, finding_id, review_subject_fingerprint, observed, envelope, current_subject_commit, judgment_authority) -> dict`. Mapping: envelope commit differs from current → refuse `denied-proof-run-stale`; `observed == "fail"` → `supported`; `observed == "pass"` → `unsupported-opinion`. Built through the existing `_assessment_record` path so `validate_finding_assessment_dict` runs on every output. Refusals raise `ReviewAssessmentRefused` with `denied-invalid-proof-run-observation`, `denied-invalid-proof-run-commit`, or `denied-invalid-proof-run-envelope`.

**Consistency check.** `check_proof_by_run(assessment, subject_commit) -> str | None` returns a denial code or `None`; it inspects only records whose `lineage.predicate_version` is `proof-by-run.v1`. `report_readiness` calls it for `assess-finding` before `write_assessment` and raises `Refusal("review-record-refused", "controller", code)` on a code, so nothing is written and `HEAD` does not move.

**git-history module.** `_git_history.py` exposes `git_history(git, *, base, path) -> dict` and raises `GitHistoryRefused(code)`. Order, so that no caller value reaches a launch before it is replaced by a trusted one: refuse arguments outside one `--path` and an optional `--base` in the CLI parser (`denied-not-in-catalog`); refuse a supplied base unless `re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", base)` (`denied-ref-form`); refuse a path under `.context/` by its first segment (`denied-artifact-path`); refuse object sources from `git.pins` (`objects/info/alternates` under the common dir) and `git.config_entries()` (`extensions.partialclone`, `remote.*.promisor`) (`denied-object-source`); resolve `HEAD^{commit}`; resolve `symbolic-ref -q refs/remotes/origin/HEAD` (`denied-no-change-base` when empty) and compute the change base with `merge-base <head> <default-ref>`; refuse a supplied base that does not byte-equal it (`denied-ref-outside-subject-history`); compute the path set with `diff --name-only -z --no-renames <base> <head>`; select the member byte-equal to the caller's path or refuse (`denied-path-not-in-change`); only then run `cat-file -t <base>:<member>`, `cat-file -s`, `show` when the size is within the content cap, and `log --format=%H --max-count=51 <base>..<head> -- <member>` with literal pathspecs. Content cap 256 KiB; the envelope is checked against 1 MiB before it is printed. The helper's in-memory capture of `diff --name-only` for a very large change is an accepted limit (ADR-0155 D5).

**CLI.** `evidence-gate.py` with subcommands `proof-run` and `git-history`, argparse with `allow_abbrev=False`, UTF-8 stream reconfiguration, sibling modules loaded by path as `_review_assessment.py` does. Exit 0 prints JSON; a refusal prints `{"refused": "<code>"}` to stdout and exits 2. `proof-run` checks the tracked tree with `status --porcelain=v1 -z --untracked-files=no` through `HardenedGit`, reads its three inputs with `_file_safety.read_confined_regular_file(<checkout>/.context, path, max_bytes=1 MiB)` after refusing a path under `.context/reviews/` or `.context/proof-runs/`, refuses a symbolic-link `.context/proof-runs`, and creates the envelope with `_confined_mutation.confined_create`.

### Failure, edge cases & resilience

Owned by: T3.

- A path with a newline or a leading `-` that is a real changed path is still a set member; `-z` parsing and the `<oid>:<path>` single argument plus `--` before the log pathspec keep it inert.
- A deleted path is in the change set; `show` at base returns its base content and the log lists the deleting commit.
- A change base equal to `HEAD` gives an empty change set, so every path refuses.
- `refs/remotes/origin/HEAD` is absent in a clone made without it; `git remote set-head origin --auto` sets it, and the refusal names that remedy.

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
- AC-0010, AC-0011, AC-0012, AC-0013, AC-0027, AC-0028: one test per refusal family; each asserts the code and the spy's substring check.
- AC-0014, AC-0029: a blob over the content cap; a changed path named `-x` and one named `:(glob)*`.
- AC-0030: an `ast` walk over both files.

**Done when:** `python3 -m pytest packs/core/tests/skills/work-loop/test_git_history_evidence.py -q` exits 0.

### T4: proof-run CLI

**Depends on:** T1, T3

**Touches:** `packs/core/.apm/skills/work-loop/scripts/evidence-gate.py`, `packs/core/tests/skills/work-loop/test_proof_by_run.py`

**Tests:** TDD — integration, in a temporary Git repository through `main`
- AC-0007: the printed record's reference digest recomputes from the created envelope file, and the spy shows only Git launches.
- AC-0008: a dirty tracked file, an existing envelope path, a symbolic-link `.context/proof-runs`, an input outside `.context/`, an input under `.context/reviews/`, a FIFO input, and a stdout file over 1 MiB each refuse with no envelope written.

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

### T7: Captured amendment request

**Depends on:** none

**Touches:** `docs/product/captured/proof-by-run-after-fix-run-binding.md`

**Tests:** no stub (goal-based — delivery-time check)
- AC-0023: the file exists with `Kind: design`, names `finding-assessment.v1`, `finding-disposition.v1`, and `evidence-receipt.v1`, and proposes an optional `evidence_refs` on a `fixed-by` disposition; the spec's Follow-ons links it.

**Done when:** the ledger records the file's presence and the Follow-ons link.

### T8: Core release

**Depends on:** T1, T2, T3, T4, T5, T6

**Touches:** `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`, `docs/product/changelog.d/*.md`, adapter projections

**Tests:** no stub (goal-based — release check)
- AC-0024: the version-equality assertion the pack suite already carries, plus a ledger record of the merge-base version and the new one.
- AC-0026: the catalogue commands' exit status and a clean tree after self-host.

**Done when:** `PYTHONPATH=packages/agentbundle python3 -m agentbundle catalogue lint --root . --deep` and `... catalogue verify --root .` exit 0, and the ledger records AC-0022, AC-0024, AC-0025, AC-0026, and the merge-base halves of AC-0016 and AC-0019.

## Rollout

Ships in the next core patch. A run in flight picks up the supervisor check only through `regenerate`; an assessment without `proof-by-run.v1` is admitted exactly as before, so no run changes behavior until a controller records a proof-by-run assessment.

## Risks

- The reference is a controller attestation. A controller can record `observed: fail` for a run that showed nothing, or write a reference without running `proof-run` at all; the supervisor checks only consistency and the commit, the judgment authority is named, and a real run leaves an envelope an auditor can recompute.
- The after-fix run stays prose until the captured amendment lands.

## Changelog

- 2026-11-03: drafted.
