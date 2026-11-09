# Plan: Legacy engine cutover

- **Spec:** [`spec.md`](spec.md)
- **Status:** Executing
- **Repository anchors:** `docs/architecture/work-loop-authority-migration.md` § 2, § 4 and § 6 (an authority moves with its record and a stated in-flight consequence); `docs/architecture/work-loop-knowledge-handoff.md` and `knowledge-capture.md` (gate boundary); `tests/roster/test_delivery_contract_bundle.py` and `packs/core/tests/skills/work-loop/test_delivery_fact_feed.py` (contract construction path); `docs/specs/pi-runtime-compatibility/plan.md` (Pi isolation). No prior `*.v2.schema.json` exists under `contracts/`, and `contracts/README.md` states no major-bump rule; T1 records the rule it follows.

> **Plan contract:** tasks, tests, design and approach are working material;
> only the spec's protected sections need an amendment.

## Approach

Cut the feed's v1 leftovers first, because two consumers read the page. Then remove the gates, delete dead compatibility code, bring the docs in line, and prove removal with the two rehearsals. Release and closeout come last.

## Constraints

- Edit `packs/core/.apm/` sources; run `make build-self` and `make bootstrap-sites` to regenerate.
- The parked approval gates `spec-approved` and `plan-approved` in `_supervisor_gates.py` and `work-supervisor.py` are out of scope. The capture request shares step 12 text in `work-loop/SKILL.md` (lines 331-370: steps 12.1 and 12.3, the "Project-knowledge integration" capture bullets and the journal-diff paragraph at line 370; renumber the remaining sub-steps without gaps) and `references/session-resumption.md`; cut only the capture lines.
- The supervisor pins `work-loop/scripts/`; edits in T1 and T4 need the three `tools/` pin suites rerun before pushing.
- Anchor-test sweep (suites that pin removed content): `test_retained_capture_paths.py`, `test_work_loop_producer_profile.py`, `test_work_loop_skill_capture_sequence.py`, `test_candidate_mode.py`, `test_contracts.py`, `test_quarantine_write_paths.py` (project-knowledge); `test_project_knowledge_handoff.py`, `test_delivery_knowledge_isolation.py`, `test_delivery_fact_feed.py`, `test_delivery_fact_feed_confinement.py`, `test_knowledge_projection.py`, `test_policy_import.py` (work-loop); `test_project_knowledge_boundary.py` (new-spec); `tests/roster/test_delivery_contract_bundle.py`.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Current architecture | T5 | Doc pins green | Pages read whole |
| Interface compatibility | T1, T2 | Roster bundle test | v1 file gone |
| Guidance and evals | T3, T5 | Eval harness run | No removed gate named |
| Release history | T7 | `check-core-release --kind major` | Version one major above base |
| Brief closeout | Closeout | `close-work` | Brief closed |

## Design (LLD)

### Design decisions

- The v2 feed schema is a new file `delivery-fact-feed.v2.schema.json` with `schema_version` enum `[2]`, no `shadow_services`, and the four `log-*` unread-source reason codes only. The v1 file is deleted in the same change (no adapter, no dual reader). The snapshot-id preimage drops `shadow_services`, so every snapshot id and `dff1.` continuation token changes; an old token is refused with `snapshot-changed`.
- Candidate mode refuses a v1 page whole through its existing schema-version check.
- The producer profile's capture and distill modes are removed with `_WORK_LOOP_CAPTURE_GATES`, `build_work_loop_capture_request`, `_validate_work_loop_artifact`, `validate_work_loop_terminal_distill_request` and the distill branch; `--capture` and `--distill` under `--producer-profile work-loop` fall to the CLI's usage refusal. The profile's enquiry modes stay. Pending captures a `plan-locked` gate stored earlier drain through a plain `--distill --pending`. Means: `implementation-discovered` — read `project_knowledge.py` and `test_work_loop_producer_profile.py` first to find which other entry points read the removed helpers.
- `compatibility_snapshot` and `reverse_read` (`_policy_import.py`) are the removal set; `import_policy` stays because `_supervisor_admission.py` calls it.

### Behavior & rules

- A rehearsal spec is a committed fixture with `delivery/` records. The cache-deletion rehearsal removes `<spec>/.supervisor/` and every projection, journal and cache the fixture run wrote, then compares `status --check`, the acceptance verdict and `delivery/evidence.jsonl` byte for byte. Traces to AC-0010. Owned by: T6.

## Tasks

### T1: The feed prints a v2 page and the v1 schema is gone

**Depends on:** none
**Verification mode:** TDD

**Tests:**
- `test_delivery_fact_feed.py`, `delivery_feed_support.py` and `test_delivery_fact_feed_confinement.py` (line 181): page carries `schema_version` 2 and no `shadow_services`; the pinned page bounds still equal the schema's; a `dff1.` token issued by the base commit is refused with `snapshot-changed`. Covers AC-0004.
- `tests/roster/test_delivery_contract_bundle.py`: the v2 schema validates the fixture page; a page with `shadow_services` or a removed reason code fails; the v1 file is absent. Covers AC-0004 and AC-0006.
- Drop the two tests that set `WORK_LOOP_SHADOW_SERVICES`; update docstrings naming v1 in `_delivery_feed.py`, `delivery-fact-feed.py` and `contracts/README.md`; update the seed README line on the unset flag. Covers AC-0006.
- Record in the task the version rule followed: a major bump is a new file, and unknown majors are inadmissible (schema description).

**Done when:** the suites above are green and `git grep -n "WORK_LOOP_SHADOW_SERVICES\|shadow_services\|delivery-fact-feed.v1" -- packs/core/.apm packs/core/seeds contracts` finds nothing (AC-0006).

### T2: Candidate mode reads v2 and refuses v1

**Depends on:** T1
**Verification mode:** TDD

**Tests:**
- `test_candidate_mode.py` and `candidate_support.py`: a v2 page yields candidates; a v1 page is refused whole with nothing written; the validator no longer lists `shadow_services` or the four removed codes. Covers AC-0005.
- Behavior pin: record the review-failure fixture's candidate entries on the base commit first, then assert entries, fingerprints and order are equal after, with only `snapshot` and tokens differing. Covers AC-0008.
- Update `references/candidate-mode.md` (v1 wording at lines 4 and 46) and the `work-loop` eval text naming `delivery-fact-feed.v1`.

**Done when:** `test_candidate_mode.py` and `test_knowledge_projection.py` are green (AC-0005, AC-0008).

### T3: The capture gates are removed from the work loop and project-knowledge

**Depends on:** none
**Verification mode:** TDD

**Tests:**
- `test_work_loop_producer_profile.py`: `--capture` and `--distill` under the `work-loop` profile are refused with a non-zero exit and no write; a `close-time` `work-item` capture and a plain `--distill --pending` over a stored `plan-locked` capture are admitted. Covers AC-0002 and AC-0003.
- Delete `test_retained_capture_paths.py`; add an absence pin that fails when either gate name returns to the work-loop skill's capture steps. Covers AC-0012.
- Update `test_work_loop_skill_capture_sequence.py`, `test_project_knowledge_handoff.py`, `test_delivery_knowledge_isolation.py` and `test_project_knowledge_boundary.py` for the removed text and evals (`spec-approved-capture-only-boundary`, `plan-locked-receipt-scoped-terminal-gate`); update `evals.json` for `work-loop`, `project-knowledge` and `new-spec`.
- Behavior pin: `test_supervisor_parked_gates.py` and `test_parked_gates_guidance.py` pass unchanged. Covers AC-0001.

**Approach:** keep the `CQ-CHANGE` and `CQ-VERIFY` enquiry bullets; cut the capture requests, steps 12.1 and 12.3, the `At spec-approved`, `At plan-locked` and "At each capture gate" bullets, and the journal-diff paragraph at line 370 (the paragraph at line 368 stays, since the enquiries need its envelope and `project-knowledge unavailable` fallback; drop "capture" from its wording if needed); also update `project-knowledge/references/capture-mode.md`, `project-knowledge/SKILL.md` and `new-spec/SKILL.md` line 769 with its evals.

**Done when:** the suites in `Tests:` are green, the two parked-gate suites show no diff, and `git grep -n "plan-locked" -- packs/core/.apm packs/core/seeds` finds nothing while every `spec-approved` hit there names the parked approval gate (AC-0001, AC-0002, AC-0003, AC-0011, AC-0012).

### T4: Dead compatibility code is removed

**Depends on:** none
**Verification mode:** Behavior pin

**Tests:** pin the current output of `test_policy_import.py` and the acceptance suites; update `docs/architecture/work-loop-acceptance-evidence.md` (line 276) to current behavior; remove `compatibility_snapshot`, `reverse_read` and their tests; the remaining suites stay green. `import_policy`, `_review_bridge.py`, `SUPPORTED_ADAPTERS` and `.shadow-acceptance/` in `_containment.py` are untouched. Covers AC-0007.

**Done when:** `git grep -n "compatibility_snapshot\|reverse_read" -- packs tests tools docs/architecture` finds nothing and the work-loop suites are green (AC-0007).

### T5: Docs, guides and architecture state current behavior

**Depends on:** T1, T2, T3, T4
**Verification mode:** Goal-based check

**Tests:** update `knowledge-capture.md`, `work-loop-knowledge-handoff.md`, `work-loop-authority-migration.md` (the Decision line, the gate row and the Slice 8 row become removed), `acceptance-centered-work-loop.md`, `work-loop-acceptance-evidence.md`, `contracts/README.md`, `packs/core/JOURNEY.md`, the seed README and guides that name the gates. Read each page whole first. Covers AC-0011.

**Done when:** `git grep -n "delivery-fact-feed.v1\|reverse_read\|compatibility_snapshot" -- docs/architecture` finds nothing, the `STATUS: PLANNED` marker that names Slice 8 in `knowledge-capture.md` is gone, and the count of other `STATUS: PLANNED` markers under `docs/architecture` is unchanged, the named pages name the gates only in a removed row, and `make lint-ruff lint-mypy` passes (AC-0011).

### T6: The removal and cache-deletion rehearsals pass

**Depends on:** T1, T2, T3, T4
**Verification mode:** TDD

**Tests:** a new suite under `packs/core/tests/skills/work-loop/` runs the cache-deletion rehearsal on a fixture spec (AC-0010); its first step names the paths the run writes under `<spec>/.supervisor/` and the install projections, leaving `delivery/` and the git-directory attempt store in place; register it where parity checks require (build-check, parity, dedup, changelog fragment, boundary lint). The removal rehearsal runs once in a fresh clone with Pi absent (no `pi` on `PATH`, no `PI_*` variable): `make build-self` leaves no diff and the `work-loop`, `project-knowledge` and `new-spec` pack suites pass; the observed output goes in `notes/verification-ledger.md` (AC-0009).

**Done when:** the new suite is green and the ledger holds the removal rehearsal's output (AC-0009, AC-0010).

### T7: Release bump and regeneration

**Depends on:** T5, T6
**Verification mode:** Goal-based check

**Tests:** `make build-self && make bootstrap-sites` leave no uncommitted diff; `make precheck PRECHECK_ARGS="--with-tests --base origin/main"` passes except its core-release step, which reports the patch successor for a major bump (the recorded expected result); `python3 tools/check-core-release.py --base origin/main --kind major` and the three `tools/` pin suites pass. A changelog fragment states the removed gates, the v2 contract and the in-flight consequence. Covers AC-0013 and AC-0014.

**Done when:** `pack.toml` and `plugin.json` are one major above the merge base with freshly fetched `origin/main`, and `check-core-release.py --kind major` passes (AC-0013, AC-0014).

## Closeout

After merge, close the brief through `close-work`: set `Cut-closed` with evidence for all eight slices and move the brief to its closed state. Close this spec: every AC checked against cited evidence, `notes/verification-ledger.md`, spec Shipped, plan Done.

## Rollout

- **Delivery:** one PR; reversal is reinstalling the prior Core major. The feed is read-only and holds no state, so nothing migrates.

## Risks

- A grep for `spec-approved` removes a parked approval gate by mistake — T3's behavior pin runs the parked-gate suites unchanged.
- An unknown external reader of v1 pages breaks — none exists in this repository, and the contract says unknown majors are inadmissible.

## Changelog

- Drafted.
- 2026-11-09: spec approved by eugenelim (scope)
- 2026-11-09: plan approved by eugenelim (build strategy)
