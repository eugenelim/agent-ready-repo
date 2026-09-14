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


## T8 — the step performed end to end across two channels

**Ran 2026-09-13 against a real surface.** AC-0017's four values, and a finding.

- **Route:** `/agent-ready-repo/docs/contributing/`, the built docs site served
  from `build/docs` at its configured base path.
- **Channel basis:** `declared-breakpoints`. One breakpoint declared, `1152`,
  because that is where the vendored Starlight component switches the right-hand
  rail from an in-flow block to a fixed full-height column. Bands `<1152` and
  `>=1152`; capture widths `1151` and `1152` by the shipped rule.
- **Result state:** `completed`. Eight captures, two channels x two heights x two
  scroll positions, each carrying all five required fields.
- **Verdict:** `fail`. One unresolved finding of `Blocker` severity.

### Observations

| Capture | width | height | scroll | rail fixed | article top | rail empty tail |
| --- | --- | --- | --- | --- | --- | --- |
| below-1152-short-at-rest | 1151 | 600 | 0 | no | 648 | 20 |
| below-1152-short-scrolled | 1151 | 600 | 400 | no | 248 | -380 |
| below-1152-tall-at-rest | 1151 | 900 | 0 | no | **948** | **319** |
| below-1152-tall-scrolled | 1151 | 900 | 400 | no | 548 | -81 |
| from-1152-short-at-rest | 1152 | 600 | 0 | yes | 101 | -48 |
| from-1152-short-scrolled | 1152 | 600 | 400 | yes | -299 | -48 |
| from-1152-tall-at-rest | 1152 | 900 | 0 | yes | **101** | 252 |
| from-1152-tall-scrolled | 1152 | 900 | 400 | yes | -299 | 252 |

**Finding — `clipped-at-rest-top`, severity `Blocker`.** At 1151x900 at rest the
whole content column is blank: the article's first line sits 948px down a 900px
viewport, so a reader who never scrolls sees the navigation sidebar beside an
empty white column and no article at all. The rail holds 799px of height with
319px of empty space below its last in-flow child. One pixel wider, at 1152x900
at rest, the same page renders correctly with its first line 101px down.

The two captures differ only in viewport width, and `matchMedia('(min-width:
72rem)')` reports `false` at 1151 and `true` at 1152 — read from the page rather
than compared against a copy of the number, so a dependency moving its breakpoint
cannot leave a width silently unchecked.

This is the defect class the delivery exists for, found by the axis it adds. A
capture set taken only at 1280, 1440 and 1920 sits entirely in the `>=1152` band
and reports this page as sound. The finding is in `docs-site`, outside this
delivery's scope, and a fix for it already exists on another branch; it is
recorded here as the run's observation, not taken into this change.

### A false pass caught before it was recorded

The first run of this capture served `build/docs` as the server root. The site is
built for the base path `/agent-ready-repo/docs`, so every stylesheet 404'd and
every page rendered unstyled. The geometry probes still returned numbers —
`railEmptyTail: 0` everywhere, `articleTop` identical across both channels — and
the run would have been recorded as `completed` / `pass` on a page with no CSS
applied at all. Reading one capture rather than the numbers is what exposed it.
The rule the pack already states covers this: a value naming only filenames does
not satisfy the observations field, and neither does a table of measurements
nobody looked behind.
