# Plan: Execution supervisor review gate

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:**
  - **Roster:** `packs/core/.apm/skills/work-loop/SKILL.md` holds the reviewer
    roster table, each role's bullet, and the high-risk paragraph.
    `references/reviewer-roster.md` and `references/finding-adjudication.md`
    describe the adjudication protocol.
  - **Legacy review verbs:** `loop-cohort.py` has `review classify`,
    `raw-classify`, `inspect`, and `record` (`:3314-3420`, `:1541-1574`,
    `:4120-4126`). The cap comes from `assets/state.json`.
  - **Artifact kinds:** `review-artifact.py` validates `raw`, `adjudication`,
    and `evidence` artifacts.
  - **Slice 2:** `_review_selection.py` (closed policy shape, kinds
    `mandatory|optional`), `_review_assessment.py`, `_review_disposition.py`,
    and `_review_compat.py`.
  - **Policy families:** `select-policy-families.py` takes the selection key as
    an argument.

> **Plan contract:** this is the implementation strategy. It may change
> substantively only while its Status is `Drafting`. After approval, execution
> observations belong in
> `docs/specs/execution-supervisor-review-gate/notes/verification-ledger.md`.

## Approach

The command relocation (T1) comes first. It moves live 3.x commands behind
byte-identical outputs and creates `review-rules.json` with the review budget.
The roster data and resolver (T2) and the review stage (T3) build on core's step
loop. The registry stage entries (T4) follow core's stage set. Every task bumps
the Core patch version and adds a changelog line.

## Constraints

- ADR-0144 D8 and D11; ADR-0042 and ADR-0047 selection meaning is carried
  verbatim.
- ADR-0061 D6: the shared review budget keeps today's counting.
- Slice 2's closed policy shape is unchanged. The resolver maps each role to
  `mandatory` or `optional` by the spec's role obligation.

## Construction tests

**Integration tests:** none beyond the per-task tests.

**Manual verification:** none.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Decision rationale — ADR-0144 wording | T2 | ADR shape lint | Consequence and Confirmation updated |
| Maintainer procedure — registry | T4 | VI-6040 | Stage keys listed |
| Skill evaluation | T1 | Skill evals | Relocated commands covered |
| Release history | every task | Version parity | One changelog line per release |

## Design (LLD)

### Design decisions

- **Rules shape.**

  ```json
  {
    "rules_version": "…",
    "max_review_retries": 5,
    "high_risk_definition": "…",
    "roles": [
      {
        "role": "…",
        "kind": "always|conditional",
        "condition": "…",
        "mode_limit": ["light", "full"],
        "boundary": "…",
        "fallback": "…",
        "mandatory_when": "…"
      }
    ]
  }
  ```

  - `condition`, `boundary`, and `fallback` are copied verbatim.
  - `mandatory_when` is `"selected"` when the role is mandatory once selected,
    `"never"` when `SKILL.md` allows a named skip, and `"always"` for
    `adversarial-reviewer`.
- **Selection and policy.**
  - The `review-role` selection result names each conditional role as selected
    or omitted, with a reason for omissions.
  - The resolver adds every `always` role allowed in the run's mode.
  - It maps each role to Slice 2 `mandatory` or `optional` by the spec's role
    obligation.
  - The fingerprint is sha256 over `rules_version` plus the ordered
    `(role, kind)` list.
  - The record is keyed by delivery subject and changed-path digest, and is
    committed through core's `review` step kind before the review subject is
    projected.
- **Assessments and dispositions.**
  - The controller dispatches the finding-adjudication reviewer on
    `assess-finding` requests. Its result becomes `finding-assessment.v1`
    through `_review_bridge`.
  - The supervisor writes `repair-request` for supported material findings, and
    `fixed-by` after a fresh clean report.
  - `accept-risk` comes only from a `risk-owner` `human-decision`.
- **Command relocation.**
  - **Shared logic:** classification and fingerprint logic move into
    `review-artifact.py`, which the `loop-cohort.py review` verbs then call.
  - **With cohort state:** the legacy verbs keep reading the per-spec cap and
    updating counters.
  - **Without cohort state:** `record --run-id <id>` writes
    `.context/reviews/<run-id>/<round>-record.md`, a JSON body in the validated
    artifact tree. The round is one more than the highest existing `record`
    artifact. `inspect --run-id` and the budget read `record` artifacts only.
    `--run-id` is a new optional argument, and corpus output is unchanged
    without it.
  - **Golden outputs:** recorded once from the pre-change verbs before
    delegation lands, and committed as test fixtures.
- **Stage keys.**

  | Pre-change engine state | Key |
  | --- | --- |
  | `SPEC-PLAN-DRAFTING`, `SPEC-PLAN-REVIEW` | `PRE-APPROVAL` (declared constant, like `DIRECT-LIGHT`) |
  | `SPEC-PLAN-APPROVED` | `admitted` |
  | `CODE-IMPLEMENTATION` | `implementing` |
  | `CODE-VERIFICATION` | `gating` |
  | `CODE-REVIEW` | `reviewing` |
  | `SPEC-HUMAN-GATE`, `PLAN-HUMAN-GATE`, `CODE-HUMAN-GATE` | `awaiting-human` |
  | `DONE` | `terminal` |

  `select-policy-families.py` keeps taking the key as an argument. The
  controller passes `status --json`'s `stage`.
- **Supervisor ingest.** The Slice 2 four-value mapping moves from
  `_review_compat.py` into `_supervisor_review.py`.

Owned by: T1, T2, T3, T4.

## Tasks

### T1: Finding-adjudication commands live in review-artifact.py

- **Depends on:** none
- **Spec behavior:** AC-0006, AC-0012, AC-0013, AC-0014, AC-0015, AC-0016, AC-0018; goal-based.
- **Touches:** `work-loop/scripts/review-artifact.py`; `loop-cohort.py` (`review` verbs delegate); new `work-loop/review-rules.json` (`rules_version`, `max_review_retries`); recorded golden fixtures; `evals/evals.json`; tests; Core manifests and changelog
- **Verification mode:** goal-based
- **Tests:**
  - **VI-6001 (AC-0012, AC-0013):** each comparison-corpus case runs through
    both command sets. Outputs are compared with the recorded golden outputs,
    and counters with the pre-change values.
  - **VI-6002 (AC-0014, AC-0015, AC-0018):** with no cohort state and a fixture
    cap of 2, the third recorded round is refused. An override with an
    authority reference passes. A persisted but unrecorded round does not
    count. `validate` accepts a well-named `record` artifact and refuses a
    misnamed one.
  - **VI-6003 (AC-0016):** a replayed `record --operation-id` returns the first
    output and writes one artifact.
  - **VI-6004 (AC-0006):** changing `max_review_retries` in `assets/state.json`
    alone fails the parity check.
- **Done when:** VI-6001–VI-6004 pass, and the cohort review suites pass unchanged.

### T2: Review rules carry the roster, and the resolver keeps today's obligations

- **Depends on:** T1, spec:execution-supervisor-core/T4
- **Spec behavior:** AC-0005, AC-0006, AC-0007, AC-0008, AC-0009, AC-0010, AC-0011; TDD.
- **Touches:** `work-loop/review-rules.json` (roles and high-risk definition); new `_supervisor_review.py`; `docs/adr/0144-work-loop-supervisor-owns-procedure.md` (D8 scope, Consequence, and Confirmation wording); Core manifests and changelog
- **Verification mode:** TDD
- **Tests:**
  - **VI-6010 (AC-0005, AC-0006):** the live roster, role bullets, fallback
    text, and high-risk paragraph equal the rules under the named
    normalizations. A one-word edit to either side fails.
  - **VI-6011 (AC-0007, AC-0008):** an obligation matrix covers every role and
    every combination of selected, omitted, and mandatory condition. Its
    expected kinds come from the role obligation:
    - `experience-reviewer` is optional;
    - `security-reviewer` is mandatory, on infra and on non-infra work;
    - `adversarial-reviewer` is always mandatory.

    Bad records are refused.
  - **VI-6012 (AC-0009, AC-0010, AC-0011):** two different selections give
    different fingerprints. A second record for the same subject and path
    digest is refused, refused again with a non-`owner` `human-decision`, then
    admitted with an `owner` one. The record commit
    carries the `review` operation.
- **Done when:** VI-6010–VI-6012 pass.

### T3: The supervisor review stage closes from readiness

- **Depends on:** T2, spec:execution-supervisor-core/T6
- **Spec behavior:** AC-0001, AC-0002, AC-0003, AC-0004, AC-0017; goal-based.
- **Touches:** `_supervisor_review.py`; `_supervisor_loop.py` (review, assessment, and repair requests); Core manifests and changelog
- **Verification mode:** goal-based
- **Tests:**
  - **VI-6020 (AC-0001, AC-0003):** a synthetic run with one supported finding
    gets a repair task. `fixed-by` follows a fresh clean report, and the run
    passes on the step where readiness turns eligible.
  - **VI-6021 (AC-0002):** a `risk-owner` `human-decision` records
    `accept-risk`, and readiness counts the finding disposed. Any other result
    is refused.
  - **VI-6022 (AC-0004):** in a fixture skill copy without a roster table, a
    synthetic role added only to the rules closes its obligation.
  - **VI-6023 (AC-0017):** every Slice 2 compatibility row maps to its required
    result.
- **Done when:** VI-6020–VI-6023 pass.

### T4: Policy families gain stage keys

- **Depends on:** spec:execution-supervisor-core/T4
- **Spec behavior:** AC-0019, AC-0020; TDD.
- **Touches:** `references/policy-families.md` (registry, and the "one reserved constant" sentence); `packs/core/tests/skills/work-loop/test_policy_family_registry.py` (key-set and map assertions extended); `guides/core/reference/phase-scoped-policy-delivery.md`; Core manifests and changelog
- **Verification mode:** TDD
- **Tests:**
  - **VI-6040 (AC-0019, AC-0020):** every core stage and `PRE-APPROVAL` has an
    entry. For each engine state, selection by the state equals selection by
    its mapped key. Every engine-state entry is unchanged.
- **Done when:** VI-6040 passes, and the extended registry tests pass.

## Rollout

- **Delivery:** Core 3.x patch releases. T1 keeps 3.x outputs byte-identical.
- **Infrastructure:** none.
- **External-system integration:** none.
- **Deployment sequencing:** T2–T4 follow the core tasks they name.

## Risks

- **Roster edits before the cutover:** VI-6010 fails until both sides match, so
  drift cannot merge.

## Changelog

<!-- Approvals only. -->
