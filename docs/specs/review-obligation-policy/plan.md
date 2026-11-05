# Plan: Review obligation policy

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:**
  - **Readiness:** `scripts/_supervisor_readiness.py` (`readiness`, `readiness_action`, `_current_report`) and `scripts/_review_disposition.py` (`review_readiness`), which match reports, assessments, and dispositions by the current subject fingerprint.
  - **Selection:** `scripts/_supervisor_review.py` (`validate_rules`, `check_selection`, `resolve_policy`, `parse_selections`, `admit_selection`, `admit_decision`, `DECISIONS`).
  - **Git:** `GitPort` in `scripts/_supervisor_commit.py`, the only route to `HardenedGit.run`. No raw commit-to-commit diff or `patch-id` helper exists yet.
  - **Records:** `_SEMANTIC_RECORDS` in `scripts/_evidence_store.py`; `REVIEW_WRITER_BOUNDARIES` and `_REVIEW_RECORD_VALIDATORS` in `scripts/_review_contracts.py`.
  - **Tests:** `packs/core/tests/skills/work-loop/supervisor_harness.py` and `supervisor_support.py`, `test_supervisor_readiness.py`, `test_supervisor_review.py`, `test_supervisor_review_closure.py`, `test_review_relocation.py`, and `tests/roster/test_delivery_contract_bundle.py`.
  - All script paths are under `packs/core/.apm/skills/work-loop/`.

> **Plan contract:** this is the implementation strategy. After approval, a
> change needs an **amendment** only when it touches the spec's protected
> sections or its terminal intent. Execution observations belong in
> `docs/specs/review-obligation-policy/notes/verification-ledger.md`.

## Approach

The work runs inside out. Rules data and validation (T1) and selection protection (T2) come first, because every later task reads them. The tier classifier (T3) is a pure function over the recorded anchor facts, the current result, and the rules, tested against throwaway Git repositories. T4 records anchor facts, adds the closed carry schema, and teaches readiness to accept carries. T5 wires tiers, carries, delta passes, round counting, and `review-cap` into `readiness_action` and decision admission; it is the riskiest task, because it changes which requests a live run sees. T6 updates the procedure documents, evals, the two amended specs' pointers, and the release. Everything ships in one pull request with one Core patch.

## Constraints

- ADR-0158 D1-D8, as accepted on 2026-11-05.
- ADR-0144 D8 stands except as ADR-0158 D2 amends it; D11 keeps worker attempts untrusted, so only the supervisor writes `review-carry.v1`.
- ADR-0157: owner decisions read supervisor-owned text only.
- `execution-supervisor-review-gate`: the parity check over `max_review_retries` (`test_review_relocation.py`) is unchanged, and the new keys stay outside it.
- Installed copies under `.claude/skills/` and `.agents/skills/` are projections; rebuild them with `agentbundle catalogue self-host`, never by hand.

## Construction tests

<!-- Owned by: T1, T2, T3, T4, T5, T6. -->

Each task's `Tests:` names its suites; the integration flows all run in the supervisor harness (`supervisor_harness.make_repo`, `start`, `Controller`).

## Durable-output map

| Spec durable output | Task |
| --- | --- |
| Decision rationale | Done before this plan (ADR-0158 Accepted, commit `8542555d7`). |
| Interface compatibility | T4 (`review-carry.v1`, `review-anchors.jsonl`), T5 (request and result schema amendments). |
| Maintainer procedure | T6. |
| Current architecture (the amended rows and rules in the two Shipped specs) | T6. |
| Skill evaluation | T6. |
| Release history | T6. |

## Design (LLD)

### Design decisions

- **Protected requests are whole-change.** A protected role gets a whole-change request, with no `delta_base`, on every subject. A spike recorded in `docs/product/research/work-loop-focused-re-review-spike.md` killed a focused re-review policy after it missed three protected-class defects that lay outside the repair diff. ADR-0158 D5 allows "at least a delta pass", so this choice stays within the decision.
- **Anchor facts are recorded, never re-derived.** `state.commits` is read from `HEAD`'s history, which an adopted rebase rewrites. So the facts a later classification compares against are written once, when the anchor round closes, to `delivery/review-anchors.jsonl`. That file is worker-protected under ADR-0144 D11, like the selections file. A missing line, or an anchor commit missing from the object store, classifies `full`.
- **`patch-id --verbatim`, not `--stable`.** A probe on 2026-11-05 (Git 2.56) confirmed that `--stable` gives one id for a re-indented line, while `--verbatim` gives two. Another probe showed that an upstream edit inside a hunk's three context lines changes the id, which fails safe. `--verbatim` needs Git 2.39 or later, and the supervisor's minimum is 2.32, so older Git classifies a rebase `full`.
- **Binary and mode checks ignore Git attributes.** A probe on 2026-11-05 showed that a work-tree `.gitattributes` `diff` entry makes `--numstat` count a NUL-bearing blob as text, and that a retargeted symlink reports `M` with mode `120000`. The classifier therefore reads both blobs itself, through `cat-file`, and accepts only modes `100644` and `100755`.
- **Cap findings are shown by supervisor references.** Finding and report ids are reviewer-supplied free strings, so `review-cap` shows `cap-finding:<sha256 hex>` references over the canonical JSON `[report_id, finding_id]`, which is injective. Each reference comes with its report's evidence-log sequence number, so the owner can read the report through the supervisor's own store before answering. `accept-risk` answers name the references, and the supervisor maps them back.
- **Open findings stay on the latest subject.** A role with an open finding is never carried or left unrequested: `rebase` and `wording-only` require no open finding, and `minor-fix` requests every raising role. So readiness keeps its current-subject `open_findings` and `disposition_closes` checks unchanged, and today's `accept-risk` writer serves `review-cap`.
- **Legacy selection lines.** A stored line without `protected_classes` parses, and it marks the unit protection-unknown. A controller answer without the field is refused. This keeps a run started before the release on today's behaviour (owner decision, 2026-11-05).
- **One new module.** The classifier and the Markdown line scan live in a new `scripts/_review_tiers.py`. It holds no state and does no writes.

### Data & schema

- **`review-rules.json` gains four keys:**
  - `code_review_round_cap` (2)
  - `minor_fix_max_lines` (40)
  - `prose_allowlist`: `{"globs": [...], "instruction_names": [...]}`. Matching is literal, by `fnmatch` on POSIX paths, and names match without regard to case.
  - `protected_class_reviewers`: the class-to-role map.
- **Selection record and answer:** gain `protected_classes` (a sorted list) and an optional `review_tier` (`"full"`). Both join `_SELECTION_FIELDS`. The parser does not require `protected_classes`. `admit_selection` and `check_selection` do. The mapped-reviewer check runs against the resolved policy roles.
- **Policy identity:** `resolve_policy` adds the sorted classes, and the protected roles they resolve to, to the fingerprinted identity.
- **`delivery/review-anchors.jsonl`:** one line per anchor round. Fields: `run_id`, `round`, `review_subject_fingerprint`, `review_policy_fingerprint`, `anchor_result`, `run_base` (or `null`), `changed_paths`, and `patch_ids` (`{path: id}`, or `null` below Git 2.39).
- **`review-carry.v1`:** a closed schema with these fields:
  - `schema_version`
  - `carry_id`, the canonical digest of the other fields
  - `role`
  - `from_report_id`, or `from_carry_id` when it carries a carry
  - `review_subject_fingerprint`
  - `review_policy_fingerprint`
  - `tier`
  - `anchor_round`
  - `classifier_digest`, the sha256 of the anchor facts line, the current result, and the rules version
  `carry_id` is the discriminating key for `_SEMANTIC_RECORDS`. Its writer boundary is `structured-control`, written through the supervisor's review grant.

### Interfaces & contracts

- **`execution-request.v1`:**
  - `review-role` gains optional `delta_base` and `repair_finding_ids`.
  - A `review-cap` request carries `round_count`, `selection_key`, and `open_findings` (`[{cap_ref, role, evidence_sequence}]`, closed items).
- **`execution-result.v1`:**
  - `$defs.selection` gains `protected_classes` (an enum of the five tokens) and `review_tier` (`const: "full"`).
  - The decision enum gains `extend-review`, paired with `authority_ref`.
  - `accept-risk` on a `review-cap` request takes cap references in `finding_ids`.
- **Python:**
  - `DECISIONS` gains `extend-review`.
  - `admit_decision` accepts the reason `review-cap`, and admits `extend-review` only for it.
  - The `review-cap` request id comes from `run_id`, `round_count`, `selection_key`, the count of admitted `review-cap` answers, and the sorted cap references, with no `state.head` salt. It is built by a sibling of `human_decision` in `_supervisor_loop.py`.

### Component / module decomposition

- `_review_tiers.classify(git, rules, anchor_facts, current, open_findings, selection_changed, review_tier) -> Tier`. The checks run in a fixed order: the `full` predicates and `review_tier` first, then `rebase`, `wording-only`, and `minor-fix`.
- `_review_tiers.scan_markdown(text) -> list[BlockKind]` assigns one block kind to each line. A construct it does not recognise yields `unknown`, which classifies `full`.
- **New `GitPort` methods:**
  - `raw_diff(older, newer, paths)` runs `diff --raw --no-renames -z --no-abbrev` with literal pathspecs.
  - `numstat(older, newer, paths)`.
  - `blob(rev, path)`, a bounded `cat-file`.
  - `patch_id(base, result, path)` pipes `diff` into `patch-id --verbatim`.
  - Each read goes through a new bounded launch in `_supervisor_git.py`. It streams the process output, stops at 1 MiB, kills the process, and reports overflow, instead of `_launch`'s unbounded `capture_output`.
- `_review_tiers.instruction_reached(git, result, rules)` collects `@` references from instruction-named files and follows them up to five hops. It resolves each reference relative to the referring file, and refuses an absolute, `~`, or escaping reference.
- `review_readiness` and `decide_review_obligation` take the carries for the current subject. A valid carry stands in for the role's report, and the carried report's assessments and dispositions join the filters.

### State & control flow

1. `readiness` resolves the selection, then reads the anchor facts, the latest reviewed subject's open findings, the round count, and the tier.
2. `readiness_action` issues `review-role` requests only for the roles the tier names, plus every protected role.
3. For each excused role, the supervisor writes one carry inside the same `review` step kind that records selections.
4. When an anchor round's last report is admitted, the supervisor appends the anchor-facts line in that same `review` step.
5. **Round count:** computed from the spec's Round definition over the review subjects recorded in the evidence store. `extend-review` raises the cap by one per admitted decision.
6. At the cap, with an open non-protected finding in an unprotected unit, the next action is `review-cap`, and no repair request is issued.
7. `accept-risk` on `review-cap` maps each reference back to its `(report_id, finding_id)` pair, checks it against the request, and disposes that pair on the current subject. Today's writer matches by `finding_id` alone (`_supervisor_review.py` `accept_risk_writer`), so T5 changes it to match the pair, keeping the bare-id path for `review-not-eligible` answers.

### Failure, edge cases & resilience

- Every classifier exception, Git refusal, output overflow, and unrecognised Markdown construct returns `full`, and `status` shows the reason.
- Invalid rules keys refuse in `validate_rules`, through the existing `_invalid_rules` named error.
- A carry or anchor write that fails leaves the role's obligation unsatisfied, so the run asks for that report instead.

## Tasks

### T1: Rules data and validation tests pass

**Depends on:** none

**Touches:** packs/core/.apm/skills/work-loop/review-rules.json, packs/core/.apm/skills/work-loop/scripts/_supervisor_review.py, packs/core/tests/skills/work-loop/test_supervisor_review.py

**Tests:**
- AC-0030: TDD over `validate_rules`, with one refusal case per missing or malformed new key.
- AC-0031: the shipped file loads with 2 and 40, and `test_review_relocation.py`'s parity tests stay green unchanged.
- AC-0035: no shipped allowlist glob matches a probe path under `docs/specs/`, `docs/adr/`, or `docs/rfc/`.

**Done when:** the T1 tests and the existing review suites pass.

### T2: Selection protection tests pass

**Depends on:** T1

**Touches:** packs/core/.apm/skills/work-loop/scripts/_supervisor_review.py, packs/core/tests/skills/work-loop/test_supervisor_review.py

**Tests:**
- AC-0017: one refusal per case through `admit_selection`.
- AC-0018: the three admitted answers.
- AC-0019: fingerprint inequality.
- AC-0021: one superset refusal, plus admission with an authorizing `reselect-review`.
- AC-0012 (value half): `review_tier` values.
- AC-0022 (parse half): a stored line without the field parses and marks the unit protection-unknown.

**Done when:** the T2 tests pass.

### T3: Tier classifier tests pass

**Depends on:** T1

**Touches:** packs/core/.apm/skills/work-loop/scripts/_review_tiers.py, packs/core/.apm/skills/work-loop/scripts/_supervisor_commit.py, packs/core/.apm/skills/work-loop/scripts/_supervisor_git.py, packs/core/tests/skills/work-loop/test_review_tiers.py

**Tests:**
- AC-0002, AC-0003, AC-0004, AC-0006, AC-0008, AC-0011, and AC-0012 (forcing half): TDD over `classify`, using real Git repositories built in `tmp_path`:
  - one fixture per tier
  - one per `full` predicate, including a symlink retarget, a submodule bump, a `.gitattributes` `diff` override on a NUL-bearing blob, a deleted run-added file, and a 1 MiB overflow
  - a path reverted to base after the anchor: it is a delta path, and its reverted lines count toward `minor_fix_max_lines`
  - one per wording-only exclusion, including a fence opened outside the hunk, an indented code block, a reference link definition, a lower-case `agents.md`, `AGENTS.local.md`, an inline `@` reference, a two-hop `@` reference, an escaping `@` reference, a reference through a symlinked directory, a six-hop chain, and an instruction-named symlink
  - a 40-line and a 41-line minor fix, the 41 lines reached over two repairs
  - a rebase with an equal patch id, one with a re-indented line, and one on Git older than 2.39 (by injected version)
  - `review_tier: "full"` over a diff that earns `minor-fix`
- An injected `GitPort` error returns `full`.

**Done when:** `test_review_tiers.py` passes.

### T4: Anchor facts and carry record tests pass

**Depends on:** T2, T3

**Touches:** contracts/delivery/review-carry.v1.schema.json, contracts/README.md, contracts/REGISTRY.md, tests/roster/test_delivery_contract_bundle.py, packs/core/.apm/skills/work-loop/scripts/_evidence_store.py, packs/core/.apm/skills/work-loop/scripts/_review_contracts.py, packs/core/.apm/skills/work-loop/scripts/_review_disposition.py, packs/core/.apm/skills/work-loop/scripts/_review_selection.py, packs/core/.apm/skills/work-loop/scripts/_supervisor_review.py, packs/core/tests/skills/work-loop/test_supervisor_review_closure.py

**Tests:**
- AC-0013: TDD in which an anchor line is written once, and the classifier reads the recorded facts after a fixture rebase rewrites the run's commits with an upstream edit to a run path.
- AC-0014: a carried clean report, and a carried report with a disposed finding, each satisfy the obligation on a new subject.
- AC-0015: one non-counting case per refusal clause, including a mismatched classifier-input digest.
- AC-0016: the delivery bundle lists the new schema, and its closed-properties test covers it.

**Done when:** the T4 tests and `tests/roster/test_delivery_contract_bundle.py` pass.

### T5: Supervisor tier, carry, and cap flow passes in the harness

**Depends on:** T2, T3, T4

**Touches:** packs/core/.apm/skills/work-loop/scripts/_supervisor_readiness.py, packs/core/.apm/skills/work-loop/scripts/_supervisor_loop.py, packs/core/.apm/skills/work-loop/scripts/_supervisor_review.py, contracts/delivery/execution-request.v1.schema.json, contracts/delivery/execution-result.v1.schema.json, packs/core/tests/skills/work-loop/test_review_obligation_policy.py, tests/roster/test_execution_supervisor_records.py

**Tests:**
- Goal-based harness runs over one unit:
  - AC-0001: the first subject requests the full set.
  - AC-0005: a wording-only repair requests no non-protected role, and its carries are written.
  - AC-0007: a rebase requests only the `adversarial-reviewer` delta pass among non-protected roles.
  - AC-0009: a minor fix requests only the raising roles, with `delta_base` and `repair_finding_ids`.
  - AC-0010: a rebase-pass finding survives a later minor-fix subject.
  - AC-0012: `review_tier: "full"` requests the full set.
- AC-0020: a `security-boundary` unit driven through every tier and one subject past round 2. Every subject issues a whole-change `security-reviewer` request, and no carry names it. The run repeats for `migration` with `quality-engineer`.
- AC-0023, AC-0024, AC-0025, AC-0026, AC-0027, AC-0028, AC-0029:
  - A two-task repair counts one round.
  - The cap fires on round 2 with cap references only. A finding id holding prose, control characters, or a NUL never appears in the request.
  - Two findings whose ids differ only by where a NUL falls get different references.
  - Two open findings with the same report id and finding id issue `review-not-eligible`, not `review-cap`.
  - The request id is stable across an unrelated commit, and a `reselect-review` followed by a second cap yields a new id.
  - `accept-risk` disposes the named findings, and an answer naming an unknown reference is refused whole.
  - Two roles' open findings on the cap subject share a finding id; accepting one reference disposes only that finding.
  - `extend-review` permits one round.
  - `reselect-review`, another answer, and no answer each behave as specified.
  - AC-0029: a protected unit and a protection-unknown unit never issue `review-cap`.
  - AC-0022 (flow half): a protection-unknown unit classifies every subject `full`.
- AC-0032 and AC-0033: TDD over schema validation for both amended schemas.

**Done when:** `test_review_obligation_policy.py`, the existing supervisor suites, and the roster contract tests pass.

### T6: Procedure, evals, spec amendments, and release are consistent

**Depends on:** T5

**Touches:** packs/core/.apm/skills/work-loop/SKILL.md, packs/core/.apm/skills/work-loop/references/supervisor.md, packs/core/.apm/skills/work-loop/evals/evals.json, docs/specs/structured-review-boundary/spec.md, docs/specs/execution-supervisor-review-gate/spec.md, packs/core/pack.toml, packs/core/.claude-plugin/plugin.json, docs/product/changelog.d/*.md, tests/roster/test_registry_upgrade_notes.py

**Tests:**
- AC-0034: goal-based version parity check after `git fetch origin`.
- The supervisor reference content pins and the skill evals pass.
- `agentbundle catalogue lint --root . --deep` passes on the pack source. The installed projections under `.claude/` and `.agents/` are rebuilt by the supervisor's own `regenerate` step, or by a controller commit after `terminal`, never inside an attempt.
- `tests/roster/test_registry_upgrade_notes.py`'s `_RELEASED["core"]` names the new version and fragment.
- The two Shipped specs change only in the rows and rules the spec's Durable Outputs name.

**Done when:** `make lint-ruff lint-mypy`, the touched suites, and the catalogue lint pass.

## Rollout

- **Delivery:** one Core patch. A run started before the upgrade stops with `supervisor-changed` (existing behaviour) or keeps today's review through its protection-unknown selection lines.
- **Infrastructure:** none.
- **Deployment sequencing:** start the run only after any upstream dependency merges, because a mid-run merge from `main` voids the pinned run. After `terminal`, rebase on `origin/main`, rebuild the projections with `make build-self && make bootstrap-sites`, commit them, and re-check AC-0034's version.
- **Closeout (controller, after `terminal`):** write `notes/verification-ledger.md` with every criterion's evidence, set the spec Shipped and the plan Done, and capture the `review-not-eligible` follow-on as a work-intake item. The spec directory is worker-protected, so none of this runs inside an attempt.

## Risks

- **Lost resampling:** a non-protected reviewer no longer resamples unchanged code after a repair, so a defect the first full pass missed can survive into the cap decision. Protected roles keep resampling, and the spike's misses were all in a protected class.
- **Markdown scan scope:** a construct the scan does not recognise classifies `full`, so an unusual document saves nothing. It is never under-reviewed.
- **Dropped role (existing behaviour):** a reselection that drops a role also drops that role's open findings from readiness, as it does today. The tier is `full` for that subject (AC-0011), but nothing here forces the dropped role back.
- **Anchor recovery:** a pruned anchor commit classifies `full`, so the savings shrink while the cap still applies.

## Changelog

<!-- Approvals only. -->

- 2026-11-05: spec approved by eugenelim (scope)
