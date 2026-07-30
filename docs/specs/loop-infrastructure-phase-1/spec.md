# Spec: loop-infrastructure-phase-1

- **Status:** Approved <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0061
- **Brief:** none
- **Contract:** none
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

Ship Phase 1 of the loop infrastructure split: `loop-engine.py` as a pure FSM phase tracker with read-only guard enforcement; `loop-cohort.py` as the authoritative execution-state owner. The detailed command surface, guard contracts, FSM tables, crash-window analysis, session-resumption protocol, and test matrix live in `plan.md`.

## Acceptance criteria

- [ ] `loop-engine transition` enforces legal phase ordering (FSM table in `plan.md`) and refuses illegal events with exit non-zero.
- [ ] `loop-engine status` returns current phase, `last_event`, `run_id`, and `pending_human_wait` as JSON.
- [ ] `loop-cohort schedule check-current` runs as a mandatory pre-guard for every transition whose source state is `CODE-*`, except `done`; any change that alters `canonical(plan.md)` from the scheduled baseline causes refusal.
- [ ] Every post-initialization run-local cohort mutation (`approve-plan`, `schedule`, `wave advance`, `record-attempt`, `review record`) requires and enforces `--expect-run-id`.
- [ ] `review inspect` uses `parse_findings()` as the canonical findings extractor and combines its output with report readability and the canonical clean-substring check to classify reports; report-content outcomes exit 0; operational failures exit non-zero.
- [ ] Session resumption works without chat history for `wave-passed` and `gates-failed` windows (idempotent) and surfaces the documented limitation for `findings-remain` and `reviewers-clean` windows; `loop-cohort status <spec-dir> [--json]` reads cohort state without mutation as the read-only step of the resumption protocol.
- [ ] `loop-engine` refuses `gates-failed` when `implementation_retry_count` equals `max_implementation_retries`; refuses `findings-remain` when `review_retry_count` equals `max_review_retries`; stale-fingerprint stasis at `findings-remain` surfaces to human per the session-resumption protocol.
- [ ] Disabled Phase-1 verbs (`worktree`, `dispatch-decision`, `auto-parallel`) exit non-zero with no `state.json` mutation.
- [ ] `state-schema.md` is updated to reflect the Phase-1 field set; `.claude/` and `.agents/` projections are regenerated.
- [ ] `SKILL.md` removes the mid-execution replan path and wires the Phase-1 `approve-plan` + G-plan sequence in place of the old `check --phase plan` gate.

## Testing strategy

All acceptance criteria verified through the test layers in `plan.md § Testing`:

- FSM table tests (all legal transitions; all illegal event/state pairs)
- Guard-refusal tests (stub each guard; verify no file mutation on refusal)
- Init/reset and `run_id` coupling tests (including positive-path init pair)
- High-risk behavioural tests (crash windows, retry caps, stasis, plan mutation per state)
- SKILL.md content assertions (T4): the `findings-remain` and `reviewers-clean` session-resumption
  limitations (AC6 "surfaces the documented limitation") are verified as documented prose obligations
  in `SKILL.md` — script tests assert the resulting cohort state; the skill's human-surfacing
  behavior is a prose obligation, not a script-testable property.
