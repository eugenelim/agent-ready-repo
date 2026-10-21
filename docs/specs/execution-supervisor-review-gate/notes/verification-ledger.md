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
