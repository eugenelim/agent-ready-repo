# Spec: Legacy engine cutover

- **Status:** Implementing
- **Owner:** Platform Core
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0144, ADR-0157
- **Brief:** brief:acceptance-centered-work-loop
- **Discovery:** none
- **Depends on:** spec:delivery-knowledge-projection, spec:execution-supervisor-cutover
- **Contract:** `contracts/delivery/delivery-fact-feed.v1.schema.json` is replaced by `delivery-fact-feed.v2.schema.json`
- **Shape:** integration
- **Risk triggers:** security-boundary, structural-interface, destructive-operation

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Protected semantic-policy contract.** `Agent Rules`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads. `Outcome`,
> `What Changes`, `Durable Outputs`, `Follow-ons` and `Assumptions` are working
> material that may be corrected without changing accepted authority.

## Outcome

Core maintainers and adopters get a work loop in which only the acceptance, evidence and delivery-fact paths decide anything: the `spec-approved` and `plan-locked` knowledge capture gates, the v1 shadow member of the delivery fact feed, and the dead compatibility code are gone. Deleting every projection, journal and cache changes no accepted scope, evidence or verdict, and the loop runs the same with Pi absent.

## What Changes

- `work-loop` PLAN stops requesting a capture at spec approval and at `start`. The parked approval gates `spec-approved` and `plan-approved` are human approvals and stay as they are — `packs/core/.apm/skills/work-loop/SKILL.md`, `references/supervisor.md`, `references/session-resumption.md`.
- The `project-knowledge` `work-loop` producer profile loses its capture and distill modes, since the two gate names are the only inputs they accept; its enquiry modes stay. the close-time `work-item` capture and plain `--capture` stay — `packs/core/.apm/skills/project-knowledge/`, `new-spec/SKILL.md`.
- `delivery-fact-feed` moves to a v2 page: the `shadow_services` member and the four reason codes the feed no longer produces (`shadow-dir-unsafe`, `marker-missing`, `marker-invalid`, `marker-unsafe`) leave the contract — `contracts/delivery/`, `_delivery_feed.py`, `project_knowledge.py` candidate mode.
- `compatibility_snapshot` and `reverse_read` leave `_policy_import.py`; neither has a production caller. `_review_bridge.py` stays: the supervisor's readiness check calls it.
- The `CQ-CHANGE` and `CQ-VERIFY` enquiries stay as an explicit rail; only the capture requests go.
- The `.shadow-acceptance/` entry in `_containment.py` stays as a denied path.
- Architecture pages, guides, evals and tests state the current behavior; `test_retained_capture_paths.py` becomes a test that the gates are absent.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Current architecture | Gate removal and v2 feed change documented behavior | `docs/architecture/knowledge-capture.md`, `work-loop-knowledge-handoff.md`, `work-loop-authority-migration.md`, `acceptance-centered-work-loop.md` | Platform Core | No Slice 8 `STATUS: PLANNED` marker or "retained" gate wording remains; doc pins green | `close-work` finds each page whole and current |
| Interface compatibility | Published feed contract changes major | `contracts/delivery/delivery-fact-feed.v2.schema.json`, `contracts/README.md` | Platform Core | Roster bundle test green; v1 pages refused | Contract registered, v1 file deleted |
| Maintainer and adopter guidance | Gate removal changes what an agent is asked to do | `guides/`, `docs/guides/`, pack evals | Platform Core | Eval harness updated; guides cite no removed gate | No guide names a removed gate |
| Release history | Core behavior change | `packs/core/pack.toml`, `plugin.json`, changelog fragment | Platform Core | `check-core-release` green | One major above the merge base |
| Brief closeout | Last slice of the brief | `docs/product/briefs/acceptance-centered-work-loop.md` | Owner, via `close-work` | All eight slices `Cut-closed` with evidence | Brief in its closed state |

## Agent Rules

### Always do

- Edit pack sources under `packs/core/.apm/` and regenerate with `make build-self`; never edit the generated `.claude/` or `.agents/` copies.
- Keep the human approval gates `spec-approved` and `plan-approved` and the supervisor `start` binding unchanged.
- Leave frozen ADR bodies unchanged.

### Ask first

- Removing the close-time `work-item` capture or plain `--capture`.
- Removing the `.shadow-acceptance/` deny entry, or any other change to `_containment.py`.
- Adding a superseding ADR if the gate removal turns out to need one.

### Never do

- Add a compatibility adapter, reverse reader or dual-write path for the removed items.
- Add a new top-level directory or dependency.
- Edit `work-loop/scripts/` while a `WORK_SUPERVISOR_INTEGRATION=1` run is live in this worktree.

## Testing Strategy

- **TDD (AC-0002, AC-0003, AC-0004, AC-0005, AC-0012).** v2 feed page shape, v1 refusal in candidate mode, the producer profile's refusal of the removed gate names, and absence pins. These have compressible invariants and exact oracles.
- **Goal-based check (AC-0006, AC-0011, AC-0013, AC-0014).** No production reader of the removed names (`git grep` over `.apm/` sources, `contracts/` and seeds); generated copies match sources (`make build-self` leaves no diff); doc and lint gates pass.
- **Behavior pin (AC-0001, AC-0007, AC-0008).** The supervisor's parked-gate suites (`test_supervisor_parked_gates.py`, `test_parked_gates_guidance.py`) stay green and unchanged, the `_policy_import` suite stays green with the two helpers gone, and the review-failure fixture yields the same candidate entries as on the base commit.
- **Rehearsal (AC-0009, AC-0010).** The cache-deletion rehearsal runs as a test over a fixture spec. The removal rehearsal runs once in a clean clone and its observed output is recorded in the verification ledger, because a nested clone-and-build run inside a pack suite costs more than the assertion it carries.

## Acceptance Criteria

Pi is absent when no `pi` executable is on `PATH` and no `PI_*` variable is set, the isolation `docs/specs/pi-runtime-compatibility/plan.md` already defines.

- [ ] **AC-0001.** The `work-loop` skill text and references contain no request for a project-knowledge capture at spec approval or at `start`, and the existing supervisor parked-gate suites pass unchanged.
- [ ] **AC-0002.** `--capture` and `--distill` under `--producer-profile work-loop` are refused with a non-zero exit and no write, and `capture_gate` and distill handling for `spec-approved` and `plan-locked` no longer exist in `project_knowledge.py`.
- [ ] **AC-0003.** A close-time `work-item` capture and a plain `--distill --pending` are admitted, including over a pending capture a `plan-locked` gate stored earlier.
- [ ] **AC-0004.** `delivery-fact-feed.py` prints a page with `schema_version` 2 and no `shadow_services` member, `delivery-fact-feed.v2.schema.json` lists no `shadow-dir-unsafe` or `marker-*` reason code, and the feed refuses a continuation token issued before the change with `snapshot-changed`.
- [ ] **AC-0005.** Candidate mode refuses a `schema_version` 1 page whole and writes nothing.
- [ ] **AC-0006.** `delivery-fact-feed.v1.schema.json` is deleted, and no `.apm/` source, seed, contract or pack doc reads, sets or names `WORK_LOOP_SHADOW_SERVICES`, `shadow_services` or `delivery-fact-feed.v1`; a negative-test fixture may name the removed member.
- [ ] **AC-0007.** `compatibility_snapshot` and `reverse_read` are removed from `_policy_import.py`, its tests and `docs/architecture/`; `import_policy`, `_review_bridge.py`, the `core-compatibility` adapter name and the `.shadow-acceptance/` containment entry are kept.
- [ ] **AC-0008.** For the review-failure fixture the candidate entries, their fingerprints and their order equal the base commit's output; only the `snapshot` identifier and continuation tokens differ.
- [ ] **AC-0009.** In a clean clone with Pi absent, `make build-self` leaves no diff and the `work-loop`, `project-knowledge` and `new-spec` pack suites pass.
- [ ] **AC-0010.** After deleting `<spec>/.supervisor/` and the regenerable install projections of a fixture spec's run, leaving `delivery/` and the git-directory attempt store (run state, not a cache) in place, `work-supervisor.py status --check`, the acceptance verdict and `delivery/evidence.jsonl` are byte-identical to their values before the deletion.
- [ ] **AC-0011.** No `.apm/` source or seed contains `plan-locked`, and every `spec-approved` there refers to the parked approval gate; `docs/architecture/knowledge-capture.md`, `work-loop-knowledge-handoff.md`, `work-loop-authority-migration.md`, `acceptance-centered-work-loop.md` and `work-loop-acceptance-evidence.md` contain no `STATUS: PLANNED` marker that names Slice 8 or a capture gate, no `delivery-fact-feed.v1`, no `reverse_read` and no `compatibility_snapshot`, and name the removed gates only in a row marked removed; `STATUS: PLANNED` markers about other work are unchanged.
- [ ] **AC-0012.** `test_retained_capture_paths.py` is deleted and an absence test fails if either gate name returns to the work-loop skill's capture steps.
- [ ] **AC-0013.** `packs/core/pack.toml` and `plugin.json` are one major above the merge base with freshly fetched `origin/main`, and `tools/check-core-release.py --base origin/main --kind major` passes; `make precheck` reports the patch successor for a major bump, which is the recorded expected result.
- [ ] **AC-0014.** A changelog fragment records the removed gates, the v2 contract, and the consequence for in-flight work: specs approved before the release run unchanged, pending `plan-locked` captures drain through a plain `--distill --pending`, and v1 continuation tokens are refused.

## Terminal Intent

`code` — after approval, implement the removals and the v2 feed contract in What Changes through tasks T1-T7 until every Acceptance Criterion is satisfied.

## Accepted Risk

none

## Follow-ons

- Platform Core: the brief's closeout through `close-work` (all eight slices `Cut-closed`) — a post-delivery duty, tracked in `plan.md` § Closeout.

## Assumptions

- Defaulted: Governance: no superseding record — no accepted ADR names the capture gates; the accepted brief, `work-loop-authority-migration.md` § 6 and ADR-0144 ("Slice 8 shrinks") authorise the removal — default: no new ADR; if wrong: add an ADR task before approval (settled by: owner).
- Defaulted: Product: the gates admitted reusable spec- and plan-authoring practice; the feed derives only `review-failure` candidates, so that capture channel ends — default: accept, since plain `--capture` stays for any session; if wrong: add a feed producer or keep the gates (settled by: owner).
- Defaulted: Technical: `reverse_read` and `compatibility_snapshot` go together, since both are unused dual-read helpers — default: remove; if wrong: keep with a stated caller (settled by: owner).
- Defaulted: Technical: `core-compatibility` in `SUPPORTED_ADAPTERS` stays as the conformance floor — default: keep; if wrong: remove it with its conformance tests (settled by: owner).
- Defaulted: Technical: the `.shadow-acceptance/` containment deny entry stays, since removing it loosens a control — default: keep; if wrong: remove it under security review (settled by: owner).
- Defaulted: Process: the release is one major, because `packs/AGENTS.md` § Version bump rule says major for removals and this change deletes a published contract major and two accepted gate names — default: major; if wrong: minor or patch, with the grounds recorded (settled by: owner).
