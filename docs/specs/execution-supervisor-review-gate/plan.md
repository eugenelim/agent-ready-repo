# Plan: Execution supervisor review gate

- **Spec:** [`spec.md`](spec.md)
- **Status:** Executing <!-- Drafting | Approved | Executing | Done -->
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
loop. The registry stage entries (T4) follow core's stage set. The four tasks
ship in one pull request with one Core patch bump and one
`docs/product/changelog.d/` fragment.

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
| Release history | T1–T4, one pull request | Version parity | One changelog fragment for the release |

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
- **Exchange schemas.** Core's request set and step kinds stay unchanged. The
  two v1 exchange schemas gain optional fields only, so every record valid
  today stays valid. Old producers never emit the new fields.
  - `execution-request.v1` gains `candidates` (an array of role names) and
    `selection_key` (a string). Its `review-role` branch then requires
    `review_subject_fingerprint`, `review_subject`, and exactly one of `role`
    or `candidates`.
  - `execution-result.v1` gains `selection` (`selected`, `omitted` with a
    `reason` each, `authority_ref`, and an optional `authorized_by` decision
    request id) and `decision` (`decision` in `reselect-review` or
    `accept-risk`, `authority_ref`, and `finding_ids` or `selection_key`). Its
    `review-role` branch requires exactly one of `report` or `selection`. A new
    `human-decision` branch requires `decision`.
  - `contracts/README.md` rows for both schemas name the selection exchange
    and `human-decision` results.
  - A schema-validation test checks each new request and result shape against
    the canonical schemas.
- **Selection and policy.**
  - **Request.** When criteria are supported and no selection record exists
    for the current key, `readiness_action` emits a `review-role` request with
    the conditional roles allowed in full mode as `candidates`, the
    `selection_key`, and id `select:<key-digest[:24]>:<n>`. It carries no
    `role`.
  - **Result.** The controller answers with `selection`: `selected` roles,
    `omitted` roles each with a `reason`, and an `authority_ref`. `report`
    routes it through `report_readiness` to `_supervisor_review.admit_selection`.
  - **Commit.** An admitted selection appends one line to
    `delivery/review-selections.jsonl` through `build_commit(operation="review",
    appends={"review-selections.jsonl": …})`, the path core's `review` step
    already uses for `evidence.jsonl`.
  - **Key.** The key is the delivery subject fingerprint plus a sha256 over the
    sorted changed paths that `review_subject` already gathers. A repair that
    changes the product therefore asks for a fresh selection.
  - **Policy.** `_supervisor_review.current_policy(ws, state)` loads
    `review-rules.json`, finds the record for the current key, and resolves the
    Slice 2 review-policy. It adds every `always` role, maps each role to
    `mandatory` or `optional` by the spec's role obligation, and sets the
    fingerprint to sha256 over `rules_version` plus the ordered `(role, kind)`
    list. `_supervisor_readiness.review_subject` and `readiness` call it in
    place of `ws.policy["review_policy"]`, and the static `review_policy`
    entry leaves `supervisor-policy.json`.
  - **Fail closed (AC-0021).** `current_policy` raises `Refusal` with
    `review-rules-invalid`, `review-selection-invalid`, or
    `review-selection-missing`. Readiness treats a missing record as "selection
    required" and emits the selection request. The other two codes surface as a
    supervisor refusal, so the stage never closes.
  - **Reselection (AC-0010).** A selection for a key that already has a record
    is refused as `review-selection-exists`. The exception is when the run holds
    an admitted `human-decision` result with decision `reselect-review` and an
    `owner` authority reference for that key. Readiness then re-emits the
    selection request with `n + 1`.
  - **Reselection request.** The owner's `reselect-review` result answers the
    existing `review-not-eligible` `human-decision` request. `readiness_action`
    already raises that request from durable evidence whenever review readiness
    is not eligible, keyed by the review subject fingerprint, so it survives a
    crash. Its question gains one sentence naming `reselect-review` as an
    answer. VI-6012 builds the request through that path: a supported finding
    left open makes readiness ineligible.
- **Human-decision results.** `report` admits a `human-decision` result for
  the current `human-decision` request. Only `review-not-eligible` requests
  take `accept-risk` or `reselect-review`, and any other reason refuses with
  `authority-refused`. Its `decision` object carries the
  decision and an `authority_ref`, which `check_authority_ref` checks against the role the
  decision needs: `owner` for `reselect-review` (a new `authority_roles` entry,
  `reselect_review`), and `risk-owner` for `accept-risk` (the existing
  `risk_decision` entry). A wrong role or an unknown decision refuses with
  `authority-refused`. The admitted result is committed as a `review` step.
  T2 ships the admission and `reselect-review`. T3 adds `accept-risk`.
- **Assessments and dispositions.**
  - The controller dispatches the finding-adjudication reviewer on
    `assess-finding` requests. Its result becomes `finding-assessment.v1`
    through `_review_bridge`.
  - The supervisor writes `repair-request` for supported material findings, and
    `fixed-by` after a fresh clean report.
  - `accept-risk` comes only from an admitted `risk-owner` `human-decision`
    result that answers the `review-not-eligible` request and names the finding.
    `_review_disposition.append_finding_disposition` records it with that
    reference as the decision maker.
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
  - **Confinement (AC-0022).** `--run-id` goes through `_parse_metadata`'s
    canonical-UUID check. Record reads, writes, and the highest-round scan go
    through `_open_with_descriptor_walk`, the no-follow, regular-file-only open
    that `validate` uses, extended with an exclusive-create write mode. A
    symlinked directory, a non-regular file, a malformed record body, or a gap
    in round numbers refuses with `unsafe-artifact` or `invalid-record`.
  - **Override (AC-0015).** In the no-cohort path, `--allow-retry-cap-override`
    requires `--authority-ref` to pass `check_authority_ref(ref, "owner")`. The
    `record` body stores `override: true` and the reference. The cohort-state
    path keeps the bare boolean.
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
- **Supervisor ingest.** `_review_compat.py` stays the shipped owner of
  Slice 2's four-value mapping until `execution-supervisor-cutover` removes the
  old engine. `_supervisor_review.py` calls that mapping and does not copy it.
  `test_review_compat.py` and the `loop-engine.py` callers stay unchanged.

Owned by: T1, T2, T3, T4.

## Tasks

### T1: Finding-adjudication commands live in review-artifact.py

- **Depends on:** none
- **Spec behavior:** AC-0006 (cap clause), AC-0012, AC-0013, AC-0014, AC-0015, AC-0016, AC-0018, AC-0022; goal-based.
- **Touches:** `work-loop/scripts/review-artifact.py`; `loop-cohort.py` (`review` verbs delegate); new `work-loop/review-rules.json` (`rules_version`, `max_review_retries`); recorded golden fixtures; `evals/evals.json`; tests
- **Verification mode:** goal-based
- **Tests:**
  - **VI-6001 (AC-0012, AC-0013):** each comparison-corpus case runs through
    both command sets. Outputs are compared with the recorded golden outputs,
    and counters with the pre-change values. With cohort state seeded,
    `review-artifact.py record` leaves `state.json` byte-equal to what the
    pre-change verb left, and `.context/reviews/<run-id>/` holds no `record`
    artifact afterwards.
  - **VI-6002 (AC-0014, AC-0015, AC-0018, AC-0022):** with no cohort state and
    a fixture cap of 2, the third recorded round is refused. An override with an
    `owner` reference passes and is stored in the artifact. An override with no
    reference or a `risk-owner` reference is refused. A persisted but unrecorded
    round does not count. `validate` accepts a well-named `record` artifact and
    refuses a misnamed one. Run ids `../x`, an absolute path, an uppercase UUID,
    and a symlinked run directory are refused. A truncated record and a gap
    from round 1 to round 3 refuse the count.
  - **VI-6003 (AC-0016):** a replayed `record --operation-id` returns the first
    output and writes one artifact.
  - **VI-6004 (AC-0006):** changing `max_review_retries` in `assets/state.json`
    alone fails the parity check.
- **Done when:** VI-6001–VI-6004 pass, and the cohort review suites pass unchanged.

### T2: Review rules carry the roster, and the resolver keeps today's obligations

- **Depends on:** T1, spec:execution-supervisor-core/T4
- **Spec behavior:** AC-0005, AC-0006 (roster clause), AC-0007, AC-0008, AC-0009, AC-0010, AC-0011, AC-0021; TDD.
- **Touches:** `work-loop/review-rules.json` (roles and high-risk definition); new `_supervisor_review.py`; `contracts/delivery/execution-request.v1.schema.json` and `execution-result.v1.schema.json` (additive fields), `contracts/README.md` rows; `_supervisor_readiness.py` (selection request, `current_policy` in place of the static policy, selection admission); `_supervisor_loop.py` (`report` admits `human-decision` results); `supervisor-policy.json` (`reselect_review` authority role); `docs/adr/0144-work-loop-supervisor-owns-procedure.md` (D8 scope, Consequence, and Confirmation wording)
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
    carries the `review` operation and appends `review-selections.jsonl`. The
    selection request, the selection result, and both `human-decision` results
    validate against the amended canonical schemas, and every request and
    result fixture already in the supervisor suites still validates.
  - **VI-6013 (AC-0021):** a missing rules file, invalid JSON, `kind:
    "sometimes"`, `mandatory_when: "maybe"`, a truncated selection line, and an
    unauthorized repeated key each refuse with their named code. A missing
    record yields the selection request, and no case resolves a role as
    optional.
- **Done when:** VI-6010–VI-6013 pass, and the supervisor step-loop and
  readiness suites pass with the resolved policy.

### T3: The supervisor review stage closes from readiness

- **Depends on:** T2, spec:execution-supervisor-core/T6
- **Spec behavior:** AC-0001, AC-0002, AC-0003, AC-0004, AC-0017; goal-based.
- **Touches:** `_supervisor_review.py`; `_supervisor_readiness.py` and `_supervisor_loop.py` (review, assessment, repair requests, and the `accept-risk` decision)
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
- **Done when:** VI-6020–VI-6023 pass, and `test_review_compat.py` passes unchanged.

### T4: Policy families gain stage keys

- **Depends on:** spec:execution-supervisor-core/T4
- **Spec behavior:** AC-0019, AC-0020; TDD.
- **Touches:** `references/policy-families.md` (registry, and the "one reserved constant" sentence); `packs/core/tests/skills/work-loop/test_policy_family_registry.py` (key-set and map assertions extended); `guides/core/reference/phase-scoped-policy-delivery.md`
- **Verification mode:** TDD
- **Tests:**
  - **VI-6040 (AC-0019, AC-0020):** every core stage and `PRE-APPROVAL` has an
    entry. For each engine state, selection by the state equals selection by
    its mapped key. Every engine-state entry is unchanged.
- **Done when:** VI-6040 passes, and the extended registry tests pass.

## Rollout

- **Delivery:** one Core 3.x patch release. T1 keeps 3.x outputs byte-identical.
- **Infrastructure:** none.
- **External-system integration:** none.
- **Deployment sequencing:** T2–T4 follow the core tasks they name.

## Risks

- **Roster edits before the cutover:** VI-6010 fails until both sides match, so
  drift cannot merge.

## Changelog

<!-- Approvals only. -->

- 2026-10-20: spec approved by eugenelim
- 2026-10-20: plan approved by eugenelim
