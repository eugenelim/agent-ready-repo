# Verification ledger: Execution supervisor review gate

Execution observations for the approved plan. Obligations stay in `spec.md` and
`plan.md`.

## T1: Finding-adjudication commands live in review-artifact.py

### Golden outputs

- The comparison corpus has 41 cases in
  `packs/core/tests/skills/work-loop/review_relocation_support.py`.
- `fixtures/review-relocation/golden.json` was recorded from the pre-change
  `loop-cohort.py review` verbs. It was regenerated from `git show HEAD:`
  copies of `loop-cohort.py` and `review-artifact.py`, and the result was
  byte-identical.

### Existing tests changed on purpose

Each change keeps what the test asserts.

- `test_loop_cohort.py::test_record_path_never_rereads_for_its_digest` now
  reads the structural-clean recorder branch from `review-artifact.py`, where
  that branch moved. Its assertions are unchanged.
- `test_loop_guards.py::test_a_newly_bounded_read_refuses_and_says_why` now
  copies `review-artifact.py` into its sandbox and lists it in `_SCRIPT_PATHS`.
  `loop-cohort.py` loads that sibling to classify reports, and the sandbox had
  copied `loop-cohort.py` alone.

The plan's Done-when says the cohort review suites pass unchanged. These two
edits move a file reference only. Neither changes an assertion.

### Method notes

- **Delegation shape.** `loop-cohort.py` keeps thin `cmd_review_*` wrappers and
  its legacy helper names as aliases of the moved logic. Cohort state I/O and
  locking stay in `loop-cohort.py`, which hands `review-artifact.py` a host
  object, so `loop-engine.py` is unchanged.
- **Mode selection.**
  - No spec directory with `--run-id` uses the no-cohort path.
  - A spec directory without `state.json`, given `--run-id`, also uses the
    no-cohort path.
  - A spec directory with `state.json` uses cohort mode, and there `--run-id`
    and `--authority-ref` are ignored.
- **Refusal output.** No-cohort refusals print `INVALID <code>` on stdout and
  exit 3. The codes are `retry-cap-reached`, `authority-refused`,
  `operation-refused`, `invalid-form`, `record-refused`, `record-conflict`,
  `rules-unavailable`, `guards-unavailable`, `cohort-unavailable`,
  `unsafe-artifact`, and `invalid-record`.
- **Cap fixture.** VI-6002 points `review-artifact.REVIEW_RULES_PATH` at a
  temporary rules file with a cap of 2. No CLI flag accepts a rules path.
- **Platform limit.** The no-cohort record path needs descriptor-relative
  no-follow opens. Where those are unavailable (Windows), it refuses with
  `unsafe-artifact`.

### Gates

- `make lint-ruff lint-mypy`: pass.
- Targeted work-loop and pack suites run by the implementer: 1958 passed and
  5 skipped, in 363 s.
- Controller re-run of `test_review_relocation.py` and `test_loop_cohort.py`:
  344 passed, in 245 s.
- `agentbundle catalogue lint --root . --deep`: ok. `self-host --check`: ok.
