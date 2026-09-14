# Verification ledger — rendered-page inspection channel axis

Execution observations for this delivery. The spec states outcomes and the plan
states mechanism; what actually happened when a task ran is recorded here.

## T1 — the reference states the channel axis

**Ran 2026-09-13.** Content complete and verified.

- Every table in the new `## Channels` section parses under `table_rows`'s
  cell-count rule, and `unique_keyed` rejects a duplicate key in each of the
  three blocks — band rows, rule rows, and the forbidden-token column.
- `capture_set_rules()` returns
  `{'every-captured-width-and-height-needs-the-pair': 'required'}`; the reference
  holds no remaining instance of the old key.
- `make build-self` exited 0 and left no projection diff.
- `python3 -m pytest packs/frontend-engineering/tests/skills/frontend-engineering/ -q`
  reported **4 failed, 234 passed in 1.24s**. All four failures are the pins the
  adversarial review named, and all four are T2's to re-decide:
  `test_an_extra_captured_height_needs_its_scrolled_counterpart`,
  `test_the_every_captured_height_rule_is_shipped`,
  `test_no_check_enforces_a_capture_rule_the_pack_does_not_state`, and
  `test_a_duplicate_capture_set_rule_row_is_rejected`. The last fails exactly as
  predicted — its `md.replace` is a no-op under the rename, so `assert mutated
  != md` prints two identical strings and names no cause.

### Deviation: T1's `Done when` is mis-scoped, carried forward to T2

**Owner decision 2026-09-13: carry forward, no amendment.**

T1's `Done when` requires that a search for `every-captured-height-needs-the-pair`
across `packs/frontend-engineering/` "returns no remaining site". T1's `Touches`
is the reference alone, and the plan assigns the remaining sites to T2, so the
condition cannot be met by T1. The line was written while repairing an
adversarial finding about mis-stating this same sweep, over-correcting from
"names a count" to "demands zero"; the plan sealed before the line was tested
against the task boundary.

What T1 discharged is the sweep itself. Its output, which is the enumeration and
not a recollection:

| File | Sites |
| --- | --- |
| `tests/skills/frontend-engineering/test_rendered_page_verdict.py` | `:196`, `:220`, `:221`, `:447`, `:448` |
| `tests/skills/frontend-engineering/frontend_engineering_rendered_page_rules.py` | `:247` |

Six sites across two files, both already in T2's `Touches`. The zero-site
condition is verified at the end of T2. No acceptance criterion changes.
