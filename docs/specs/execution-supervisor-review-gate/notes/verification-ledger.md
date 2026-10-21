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

## T2: Review rules carry the roster, and the resolver keeps today's obligations

### Roster classification

`mandatory_when` follows the spec's role obligation: mandatory once selected
unless `SKILL.md` allows a named skip.

| Role | `kind` | `mandatory_when` | Basis in `SKILL.md` |
| --- | --- | --- | --- |
| `adversarial-reviewer` | `always` | `always` | The default role. |
| `security-reviewer` | `conditional` | `selected` | "Missing `security-reviewer` on infra work = loud blocker"; the spec makes it mandatory on non-infra work too. |
| `experience-reviewer` | `conditional` | `never` | "Fallback absent: named skip." |
| `frontend-reviewer` | `conditional` | `never` | "Fallback absent: named skip." |
| `design-reviewer` | `conditional` | `selected` | No named-skip text. |
| `quality-engineer` | `conditional` | `selected` | No named-skip text. |

The last two rows apply the definition's default (no allowed skip means
mandatory when selected). VI-6011 names only the first four roles, so the owner
should confirm these two when reviewing; changing one is a one-word edit in
`review-rules.json` plus the matrix in `test_supervisor_review.py`.

### Design notes

- **Verbatim copies.** `boundary` holds the whole bullet after its `- `
  marker, including the bold role name and any continuation lines. `fallback`
  is the bullet's `Fallback absent: ...` or `Missing ...` sentence, and holds
  `""` where the bullet has none. `condition` holds the table cell as written
  (`*(always)*`, `**high-risk work**`). `SKILL.md` sits at the skill root, so
  the link-rewrite normalization changes nothing.
- **Selection key.** `sha256(acceptance_fingerprint + sha256(sorted changed paths))`
  where `acceptance_fingerprint` is the delivery subject's. The selection commit
  lives under `delivery/`, which the subject excludes, so recording a selection
  never changes its own key.
- **Decision record.** An admitted `human-decision` result is appended to
  `delivery/review-decisions.jsonl` through a `review` step (step id
  `decision:<request id>`). The file is separate from `evidence.jsonl` and from
  `review-selections.jsonl`; the resolver counts its owner `reselect-review`
  lines per key (record `n` of a key needs `n - 1` of them). T3 can append its
  `accept-risk` lines to the same file.
- **Selection pending a reselection.** While an owner decision exceeds the
  records for its key, readiness reports `selection.required` and issues
  `select:<key[:24]>:<n+1>`; the policy of the old record is not used.
- **Selection request subject.** The schema requires `review_subject` on
  every review-role request, so the selection request carries a subject whose
  policy fingerprint is the placeholder `review-selection-pending`. It lists
  the changed paths the controller selects from.
- **Refusal surfacing.** `decide` turns a rules or selection `Refusal` into a
  `refusal` action, so `next` writes `run.json` with the code and `status`
  shows it under `readiness.refusal`.
- **Request addition.** The `review-not-eligible` request now carries
  `selection_key` so the controller can name the key in a `reselect-review`
  answer.

### Anchor sweep

No test pins a digest, snapshot, or count of `supervisor-policy.json`, the two
schemas, `contracts/README.md`, or ADR-0144. No digest was updated. The static
policy fingerprint `work-supervisor-default-review-policy-v1` appears in no
test.

### Existing tests changed on purpose

- `supervisor_harness.py` (shared helper, not a test): `Controller.work` answers
  a `review-role` request carrying `candidates` with a selection that selects no
  conditional role (`select_none`), so every run resolves to the policy the
  static file held (`adversarial-reviewer`, mandatory). No test assertion
  changed. `select_none` is new.

### Gates

- `test_review_rules_roster.py` (new): written red first (`roles` missing from
  the rules), then green once the roster was generated.
- Integration-marked supervisor suites skip without
  `WORK_SUPERVISOR_INTEGRATION=1`: admission, commit, crash corpus, dark
  launch, effects, readiness, step loop, tdd, and the new
  `test_supervisor_review_gate.py`. The implementer ran only
  `test_supervisor_review_gate.py` (2 passed) and, as a smoke check on the
  readiness wiring, `test_supervisor_readiness.py -k "row_ready or
  review_not_eligible"` (2 passed). The CI lane owns the rest.

## T1 follow-up: the supervisor stays dark

`test_supervisor_dark_launch.py::test_nothing_in_the_skill_but_the_supervisor_invokes_it`
failed on the T1 commit. `review-artifact.py` loaded `_supervisor_admission.py`
to check the override's `owner` reference, and its comments and one eval named
`work-supervisor`. The fix gives `review-artifact.py` its own copy of the
authority-reference pattern. A new VI-6002 test pins that copy equal to
`_supervisor_admission._AUTHORITY_RE`, and the comment and eval wording no
longer name the supervisor. With the fix, the dark-launch suite passes: 2
passed under `WORK_SUPERVISOR_INTEGRATION=1`.

### Integration subset after T2

- Run under `WORK_SUPERVISOR_INTEGRATION=1` with `-n auto`: the readiness,
  step-loop, admission, and commit suites. 95 passed and 1 failed, in 837 s.
- The failure was `test_supervisor_readiness.py::test_no_stored_verdict_or_readiness_answer_exists`
  at `_started` (`h.start(repo)` returned non-zero under parallel load), before
  any review step ran.
- Re-run alone, the test passed: 1 passed, in 65 s.
- A direct drive of the same run found none of the test's forbidden markers in
  `delivery/`.
- CI's integration lane is the deciding run.

## T3: The supervisor review stage closes from readiness

### Design notes

- **Closure (AC-0001).** Nothing new closes the stage. `readiness().ready`
  already requires `review_readiness(...)["acceptance_eligible"]` for the
  resolved policy, and `decide` returns terminal only when `readiness_action`
  is `None`. VI-6020 asserts it end to end: ineligible with a finding open and
  again with a fresh subject awaiting its report, eligible and terminal on the
  step that admits the clean report.
- **Repair projection (AC-0003).** `_supervisor_review.record_dispositions`
  runs inside the same evidence write as every admitted report and assessment,
  so one `review` step carries both. A current supported material finding with
  no disposition gets `repair-request`, with the run id as the identity and
  `work-supervisor` as the role of its approval. Repair work reaches the
  controller through the existing `review-not-eligible` `human-decision`
  request; no request kind was added. Its question now lists the open finding
  ids and names `accept-risk`.
- **`fixed-by`.** Recorded for an earlier subject's open `repair-request` only
  when, on the current subject, the same role's report is the tip, shares the
  delivery subject id, carries no finding with the old finding's id or actual
  failure, and every one of its findings has a current non-indeterminate
  assessment. The store's own `disposition_closes` is checked after the write
  and a disagreement refuses the step. A reselection that changes only the
  policy fingerprint is also a replacement subject, so a clean report under it
  records `fixed-by` for the old subject's findings. Slice 2 scopes readiness
  per subject, so readiness does not change.
- **Grant.** Dispositions need the `review/disposition` write scope, which the
  receipts grant (`evidence`) lacks. `_review_grant` issues a `review`-scoped
  grant from the same issuer for the disposition write alone. No change to
  `_supervisor_admission.py`.
- **`accept-risk` (AC-0002).** `admit_decision` admits it for a `risk-owner`
  reference and a non-empty, duplicate-free `finding_ids` with no
  `selection_key`. `accept_risk_evidence` then requires each id to be exactly
  one open (supported, material, no closing disposition) finding of the current
  subject, and writes one disposition per id with the reference as decision
  maker and role `risk-owner`. The line goes to `delivery/review-decisions.jsonl`
  in the same `review` step as the evidence. A bad id refuses before the
  commit, so a mixed list records nothing.
- **Ingest (AC-0017).** `ingest_legacy_event` calls
  `_review_compat.reconcile_review_source_event` and holds no result value.
  The corpus is read from the `pytest.mark.parametrize` rows of
  `test_review_compat.py::test_vi1013_compatibility_corpus` by path, so the
  rows are not copied. `_review_compat.py` and `test_review_compat.py` are
  unchanged.
- **Synthetic role (AC-0004).** The fixture skill drops the roster table from
  `SKILL.md`, adds one role to `review-rules.json`, and loads it through
  `load_rules(path)`. The shipped code names no role from the rules.

### Existing tests changed on purpose

- `test_supervisor_review.py::test_vi6012_a_decision_outside_reselect_review_by_the_owner_is_refused`:
  removed the `risk-owner` `accept-risk` case. T3 admits it, so it no longer
  refuses. The `owner`-role `accept-risk`, unknown-decision, and wrong-key cases
  stay; docstring updated.
- `test_supervisor_review_gate.py::test_vi6012_vi6013_selection_then_reselection_through_a_run`:
  the refused `accept-risk` answer now uses the `owner` reference instead of
  `risk-owner`, for the same reason.

### Anchor sweep

No test pins a digest, size, or snapshot of `_supervisor_review.py`,
`_supervisor_readiness.py`, or `_supervisor_loop.py`. The `.claude/` and
`.agents/` copies are projections that `self-host --write --force` regenerated.
No digest was updated.

### Gates

- `make lint-ruff lint-mypy`: pass.
- `test_supervisor_review_closure.py` (new, 14 tests, 12 function-level and 2
  integration-marked): 14 passed. Run with `WORK_SUPERVISOR_INTEGRATION=1`
  serially, 452 s.
- `test_supervisor_review.py`, `test_review_rules_roster.py`,
  `test_review_compat.py`, `test_review_disposition.py`, `test_review_bridge.py`,
  `test_supervisor_dark_launch.py`, and the new file without the marker:
  318 passed, 3 skipped, 12 s.
- `tests/roster/test_review_gate_schemas.py`: 22 passed.
- `test_supervisor_review_gate.py` and `test_supervisor_readiness.py` with
  `WORK_SUPERVISOR_INTEGRATION=1`, serially: 16 passed, 826 s.
- `agentbundle catalogue lint --root . --deep`: ok, 79 findings, none new.
- The CI `supervisor-integration` lane lists its suites by file name, and
  neither `test_supervisor_review_gate.py` (T2) nor
  `test_supervisor_review_closure.py` is in that list, so both skip in CI. Not
  changed here.

### CI lane

`.github/workflows/catalogue-tooling-ci-gates.yml`'s `supervisor-integration`
job lists its suites by file name. It now also runs
`test_supervisor_review_gate.py` (T2) and `test_supervisor_review_closure.py`
(T3), which otherwise skip everywhere. Its timeout rose from 30 to 40 minutes,
because the two suites took about 9 minutes when run serially on a local
machine.

### Reselection and `fixed-by`

A reselection that changes only the policy fingerprint makes a new review
subject. A clean report under that subject records `fixed-by` for the earlier
subject's open findings, even though the product did not change. This matches
AC-0003's wording: a fresh report for the replacement subject closes the
finding. Slice 2 scopes readiness to one subject, so readiness is not affected.

## T4

- Mapping check: `SPEC-PLAN-DRAFTING` and `SPEC-PLAN-REVIEW` both select the five authoring families, and the three human-gate states all select nothing, so the plan's stage mapping loses nothing.
- Registry gained `PRE-APPROVAL`, `admitted`, `implementing`, `gating`, `reviewing`, `awaiting-human`, `terminal`. Engine-state and `DIRECT-LIGHT` entries are untouched.
- Existing tests changed in `packs/core/tests/skills/work-loop/test_policy_family_registry.py`: `test_selection_map_is_the_declared_mapping` pinned exactly eleven keys, and `test_selection_covers_every_legal_state_plus_the_reserved_token` expected states plus `DIRECT-LIGHT`. Both now include the seven new keys (renamed the second to `..._declared_constants_and_stage_keys`). Added three VI-6040 tests: engine entries unchanged (pinned literals), stage key equals each mapped state, and the full map.
- Red first: 3 failed before the registry edit.

## Post-gates review round 1

- **Security:** clean after adjudication. All five findings were refuted
  against the settled spec-stage decisions.
- **Adversarial and quality-engineer:** three findings were sustained.
  - Shipped docstrings in `_supervisor_review.py` named an internal delivery
    slice. They now name the contract or module.
  - `Selection.latest` had no docstring. It now has one.
  - The owner's confirmation of two roster roles was not recorded. See below.
- **Repair receipts:** the controller made the six-line docstring repair
  itself, as the FIX step allows for a small diagnosis-sized fix. On
  2026-10-21, eugenelim directed that it stands, so T1–T4 carry
  `--decline human-directed` dispatch records for this round.
- **Owner decision, 2026-10-21:** eugenelim confirmed that `design-reviewer`
  and `quality-engineer` stay `mandatory_when: "selected"` in
  `review-rules.json`. That is the spec's role obligation: `SKILL.md` allows
  neither a named skip.

## PR CI round 1

Two existing tests failed in PR CI because behaviour changed on purpose. Each
keeps what it asserts.

- `tests/roster/test_work_loop_root_validation.py::test_report_sites_route_through_resolver`
  counts the `--report` call sites that pass through `_resolved_report`. T1 moved
  those sites from `loop-cohort.py` into `review-artifact.py`. The test now reads
  `review-artifact.py` and still expects three assignment-form sites and no bare
  `Path(args.report)`.
- `test_supervisor_crash_corpus.py` pins the uninterrupted run's kill points.
  T2's reviewer-selection exchange adds one supervisor step (four kill points)
  and one journal append, so `BOUNDARIES` rises from 59 to 64. Every kill and
  delete variant at those points must still converge, which now covers the
  selection step.
