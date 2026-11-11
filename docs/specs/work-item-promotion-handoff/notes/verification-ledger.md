# Verification ledger — work-item promotion handoff

Execution observations for `docs/specs/work-item-promotion-handoff/spec.md`.
Evidence recorded as it was produced; nothing here changes the spec.

## Construction tests

- **2026-11-04 — module suites.** `tests/roster/test_promotion_drain_reader.py`
  (3), `test_promotion_drain_prose_rerun.py` (4), `test_promotion_drain_envelope.py`
  (8), `test_promotion_drain_recheck.py` (3), `test_promotion_drain_decide.py`
  (10), `test_promotion_drain_run.py` (6), `test_promotion_drain_procedure.py`
  (3) — all green over fixture stores, `ruff` and `mypy` clean.
- **2026-11-04 — store replay after the fixture drain (`AC-0003`,
  `AC-0004`).** `test_store_derived_counts_agree_with_the_run_report` drives
  one fixture drain producing a routed, a held, and a closed item, then
  derives the counts from the store alone: the routed disposition and the
  pruned-side closure are read back from the journal, the held item is the
  one capture still open, and the report agrees member for member.
- **2026-11-04 — crash recovery (`AC-0005`, `AC-0012`).**
  `test_crash_at_each_effect_boundary_then_re_drive_completes_once` drives a
  crash at each effect boundary (before the transaction, inside it — the
  transaction's own rollback, after it before the disposition, after the
  disposition) and re-drives: every pre-disposition crash leaves the capture
  open; the re-drive completes without a second artifact or a second
  terminal event. `test_closure_path_crash_and_identical_disposition_no_op`
  covers the closure path and the store's identical-disposition no-op.
- **2026-11-04 — the § D6 case table (`AC-0016`, `AC-0017`).**
  `test_every_d6_case_row_drives_the_recheck` parses the 46 rows live from
  `docs/specs/work-item-capture/spec.md` § D6 cases and drives each through
  the re-check, which calls the write path's own validator (asserted by
  identity in `test_recheck_calls_the_write_path_validator_itself`). A row
  added upstream drives the re-check with no edit here.

## Real-store drain (smoke)

- **2026-11-04 — unattended drain over this repository's observation
  store.** `promotion_drain.drain(".")` with no confirmer: completed and
  reported `{"attended": false, "counts": {"routed": 0, "held": 0,
  "closed": 0}, "items": []}` — the store holds no `work-item` captures
  today (its observations are `gotcha`-kind), so the drain read every
  partition, offered nothing, held nothing, and wrote nothing. The run
  satisfies the "whatever it holds" clause on an empty well; the first
  captured work item exercises it against real content.

## Deferred by design

- **The § D12 adjudicated sample.** The spec's Follow-ons gate it on the
  real store offering ten items to one drain; capture traffic does not yet
  exist. The fixture-driven suites above verify the mechanics the sample
  would exercise.
