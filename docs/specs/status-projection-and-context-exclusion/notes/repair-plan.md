# Post-GATES repair plan

Written after the post-GATES review returned 35 sustained findings across three
adjudicated reports. `plan.md` is hash-pinned by `approve-plan`, so the repair
design lives here; `spec.md` is `Status: Implementing` and therefore Living, so
its amendments are made in place.

## Owner decisions taken

| # | Decision | Consequence |
| --- | --- | --- |
| 1 | A cooled dependency is satisfied **from its lifecycle record**, not from a coordination receipt | AC14 and AC56 stand as written; the receipt follow-on stays deferred to Wave 7 |
| 2 | A cooled `containing_brief` on the cross-repo path is **refused without reading** | RFC-0096 §7 held with no exception |
| 3 | The `surface_resolver()` execution path is **closed**, not documented | Touches `close_work.py` (Wave 5, not frozen) and re-projects `_data/` |
| 4 | With no active or paused initiative, the `closeout` block is **omitted** | AC29's closed key set is untouched; a new AC pins the absence |
| 5 | Record count stays **uncapped** | Wave 7 owns pruning; a cap needs a third finding code where AC46 pins two |
| 6 | A transient tz-database fault is **outside the threat model** | Recorded; `naive-clock` is unreachable and the remedy contradicts AC46 |

## The root cause, and the one change that fixes most of it

Exclusion was applied by deleting cooled entries from the membership set at
`run_canonical_reconciliation:2996-3005` — *before* `by_path` (`:3010`),
`duplicate_paths` (`:3019`), `cycle_paths` (`:3047`) and
`structurally_blocked_paths` (`:3059-3073`) are derived from it. A cooled
artifact therefore never becomes *cooled* in the engine's model; it becomes
**absent**, and every fact derived about it silently defaults.

The two adjudicators disagreed on the repair. Security: computing those facts
unfiltered would run `_artifact_metadata` inside the structural loop and open
cooled bodies, which AC13/AC16/AC18/AC20 and the `Never do` rail forbid.
Adversarial: the facts must be derived unfiltered or the bypass remains. Both
hold, because **`_metadata_from_membership` (`:2128-2137`) is read-free** — it
takes status from `_membership_status`, i.e. from `workspace.toml` — and the
structural loop already lists it as a fallback at `:3062`.

> **R1.** Iterate memberships **unfiltered**. For a cooled membership use the
> read-free metadata path only, never `_artifact_metadata`. Apply the cooled
> selection at **evaluation and emission**.

A fact derived from a body we may not read is *taken from the membership*, not
computed from the artifact. This repairs S1 and A3 together.

## Repairs, in dependency order

**R1 — unfiltered structural derivation, read-free metadata for cooled members.**
Fixes S1 (dependency-gate bypass) and A3 (cooled closed defect blocking its
dependants). Must land with R7's AC55 rewrite, or AC55 reds at the projection
level.

**R2 — decide every dependency before any probe is built.**
`_dependency_is_satisfied` must compute `cooled_dependency` and decide ahead of
both probe constructions (`:2520-2527` defect, `:2541-2548` general) and ahead of
the `matches[0]` metadata read at `:2539`. Outcome per decision 1:

- `defect` → existing `backlog.closed` membership test (membership data only)
- every other kind → satisfied from the lifecycle record

Fixes A1. Note R1 restores the `backlog.closed` membership, so the defect arm
behaves correctly for the first time.

**R3 — cross-repo cooled brief refused without reading.** Move the cooled check
above the `_cross_repo_receipt_satisfied` return at `:2503` and drop
`cooled_dependency`'s `dep.type == "local"` clause. Fixes A6.

**R4 — emit the cooling findings.** Carry `result.cooling_findings` into the
findings list built in `_canonical_projection` and into the MCP projection, then
re-point AC5, AC8, AC9, AC10, AC11 and AC38 at `canonical.findings`. Fixes
S6/A2/Q1 — six unmet criteria — and makes AC6/AC7's absence assertions
non-vacuous.

**R5 — legacy filter through `_legacy_canonical_alias`.** `:3004` currently
resolves the legacy `spec/alpha` form, giving `root/spec/alpha`, which can never
equal the cooled canonical path. Extend AC20 to assert absence from
`canonical.blocked`. Fixes A7.

**R6 — contain `surface_resolver()`.** Refuse when the module is not running from
a skills tree, keeping the co-located `file_safety()` load working in both
layouts; re-project into `_data/close_work.py`; restore AC41's test to plant a
loadable resolver outside `_data/` and assert both the refusal and a
non-execution marker. Fixes S2/A5/Q6.

**R7 — raise the tests to their criteria's level.** AC12 and AC55 currently
assert one layer below the observable they name; AC12's second assertion compares
an unresolved literal against resolved paths and can never hold. Fixes A16.

**R8 — the remaining sustained set.** MCP degradation path reusing
`_resolve_cooled_state` (A8/Q4); module contract guard extended to `is_due` and
the attributes the projection reads (A9); `ExternalAdvisory` exceptions gated on
`post_closeout_result in {"Retained", "ExternalAdvisory"}` (A11/Q11 — *not* on
`exception is not None`, which would wrongly admit `Retired`); AC39 given its real
control/failed pair (A4/Q2); `cooling_enabled` given a CLI-level test (Q3);
`SKILL.md` visibility prose split so one bad record does not claim nothing was
excluded (Q5); `closeout` omitted with no active initiative (Q12, decision 4);
`type(exc).__name__` logged before the generic failure payload — **not**
`str(exc)`, which can emit a host path into agent context (Q14); the two engine
copies collapsed in the harness (Q7); plus the nits Q15–Q18, A14, A15.

**R9 — correct the record.** `notes/gate-evidence.md:76-82` is wrong on both
counts: `brief` is the one kind constrained by `_is_canonical_local_brief_path`,
so it is the only kind that could not reproduce A1, and the measurement observed
dispatch outcome, which says nothing about whether the body was read. Re-derive
the killability claim after R2.

## Spec amendments

`spec.md` is Living while `Status: Implementing`. Amend: the Assumption that
`project_closeout_status` has no production caller (now false — `:100`, `:129`,
`:704`) and its drifted definition citation; the `Never do` probe citation at
`:125`, resolved by symbol rather than line range; AC20, AC27, AC39, AC41 and the
six finding-code criteria per the repairs above; and a new criterion for the
omitted `closeout` block.

## Verification discipline for this pass

The mutation table was green while six criteria were unmet, because those tests
asserted `_resolve_cooled_state()`'s internal tuple rather than the JSON their
criterion names. **A mutation proof inherits its test's blind spot.** Every
repaired criterion is therefore verified at the level its own text states, and
each mutation is re-derived against the emitted surface — not against the
internal call that produced it.

## Engine route

From `CODE-REVIEW`: fire `findings-remain`, record the sustained fingerprints,
apply the repairs, fire `wave-complete` to reach `CODE-VERIFICATION`, re-run the
full gate set, then re-enter `REVIEW`. `plan.md` is not edited at any point.
