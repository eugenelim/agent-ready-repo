# Review findings not fixed by this delivery

Nine findings survived adjudication across three review rounds on the withdrawn
contract amendment. Each names what was measured, so none needs re-deriving.

This document is the artifact of the canonical `[backlog].open` entry
`docs/specs/cooling-scope-closure/notes/review-findings.md` (`kind = "defect"`).

**A tenth finding is resolved rather than recorded.** It claimed `[backlog].open`
could accept no new entry in any shape: the legacy `{slug = ...}` form was
required by `lint-spec-status.py` invariant (iv) and forbidden by the write-side
ratchet, while the canonical form raised `missing_artifact`. Only the last third
was true. `lint-spec-status.canonical_entry_anchor` resolves a deferral anchor
from a canonical record's `path`, and `backlog_open_slugs` documents that
accepting both shapes is "what stops invariant (iv) from obliging a deferring
spec to write a legacy" record. The `workspace.toml` header claiming otherwise
was stale, and is corrected in the same commit as this file. The real constraint
is only that a canonical `path` must name an artifact that exists — which is why
this document is the entry's artifact.

## Repository-wide

**1. A plan required a record that its own approved state forbids, and shipped
that way.** The delivery's mutation table instructs that each row's observed red
is recorded in the plan's own table. `plan.md` is hash-frozen once `schedule`
persists it: `_loop_guards.check_schedule_current` compares the canonical hash
and `loop-engine` runs `schedule check-current` on every `CODE-*` transition,
with only the status token and progress checkboxes normalised out. So that edit
is refused, and the obligation was never dischargeable.

**This is an authoring defect, not a missing work-loop capability.**
`references/pre-execute-review.md` already states that approved plans are
"immutable in substance", names the narrow bookkeeping exemption, and says in
terms: "If EXECUTE discovers a plan error, surface to the human and stop — do not
edit `plan.md` in-flight." The plan asked for an edit the skill already forbids.
An earlier draft of this note attributed it to a work-loop design hole; that was
wrong, and the correction matters because the fix is authoring discipline plus,
at most, a lint — not a state-machine change.

The measured consequence stands and is already merged: **0 of 20 mutation rows
record an observed red**, and T6 is pinned completed with a Done-when requiring
exactly that recording. Any plan whose Done-when requires writing to `plan.md`
after `approve-plan` is unsatisfiable by construction, and nothing currently
detects one at approval time. That detector is the only part worth building.

**2. `cooling.load_record` reports a missing confinement helper as an invalid
record.** `packs/core/.apm/skills/close-work/scripts/cooling.py` catches
`ImportError` alongside `OSError` and `ValueError` and returns `record-invalid`,
which `workspace_status_engine` surfaces as `invalid_lifecycle_record` naming the
file. Measured: running `workspace_status.py` from outside the checkout reports
`invalid_lifecycle_record` for a record the in-checkout run accepts, on both
`status` and `reconcile`. The direction is fail-closed and correct, but the
diagnosis sends a maintainer to repair a valid record when the cause is an
unimportable helper, and it means every closeout-derivation observable is
unobtainable in a packaged or user-scope layout — which bears on any manual QA
claiming to exercise the real invocation. Two probe attempts in this delivery
were voided by exactly this before the cause was understood.

## Cooling-scope-closure

**3. No criterion names a `work.*` entry class.** All 33 criteria use a canonical
`docs/specs/<slug>/spec.md` entry. Two defects passed all 33 green in that blind
spot; the second reached `origin/main` in PR #1210. The repair ships here and is
guarded by no test. What the withdrawn amendment would have added: a cooled
legacy `spec/<slug>` entry excluded from both closeout consumers, and a bare-slug
entry reported `unsupported_legacy` *not* excluded — each with an uncooled
control, and the refusal case with a positive control proving the record cools
the artifact (`_cooled_locators` admits a locator only when the member exists, so
without it the criterion passes over an empty cooled set).

**4. The closeout seam keys cooled exclusion on a raw path string.**
`cooled_work_entry_paths` transports its verdict as `entry.path` strings and
`_surviving_work` filters on them, but that string is not entry identity:
`parse_workspace_entry` shape-constrains `path` only for `kind = "spec"` and
`kind = "brief"`, so `{path = "spec/x", kind = "defect"}` is a valid canonical
membership whose raw path equals a legacy `"spec/x"` entry's stored form. Measured
by both reviewers with both controls: an initiative holding the cooled legacy
string and the uncooled `defect` entry reports `all_specs_shipped true` and
`invoke-close-work` on both invocations, while `canonical.findings` carries
`missing_artifact` and `impossible_transition` against the entry that silently
vanished. Reachability is nil today (0 string-form `work.*` entries of 125, 0
lifecycle records, 0 intra-initiative duplicate raw paths) and it grants no
privilege. The fix is a change to what the seam carries, plus a two-entry
criterion. The seam's own docstrings assert the opposite ("the two agree by
construction"); the fix must retract them.

**5. AC31 cannot fail when the release surfaces agree at a version whose
published code differs from what ships.** Measured 2026-09-02: this branch
changed `packs/core` behaviour while `pack.toml`, `plugin.json` and the topmost
dated `[core]` heading all read `2.21.0`, matching `origin/main` — every AC31
clause passed. That is the hazard
`tests/roster/test_security_checklists_okf_projection.py` documents, and it is
the defect this delivery repairs by hand with the 2.22.0 bump. AC31's floor
literal is also cleared by three releases and cannot fail.

**6. The cooled-membership alias axis is unpinned for legacy entries.** AC4 pins
alias-named cooling for a canonical entry only. The Testing Strategy's own
rationale — two independently written filters can agree on a locator and
disagree on an alias — makes the axis independent. Exposure is nil because
`_cooled_locators` flattens `locator` and `aliases` into one resolved-path set
and `_legacy_membership_is_cooled` reads that single set, so an implementation
splitting that resolution later would satisfy the contract while breaking the
`Always do`. Raised in three consecutive rounds.

**7. A withheld closeout cannot name the record that caused it.** When the cooled
reading is incomplete because a record's review date could not be judged, the run
withholds `invoke-close-work` and emits no finding identifying the record, so a
maintainer sees a blocker with no actionable cause. The Objective accepts this
residual. The comment at `workspace_status.py:700` half-describes it and is
itself wrong: that arm emits no finding, though it does reach `dueness_failed`
and flip `cooling_context_visible`. Adding a finding code was a `Never do` for
this delivery, so closing it needs an owner decision on the surface.

**8. `notes/closeout-records.md` is reachable from no other artifact.** The
spec's Durable Outputs `project-knowledge` row carries an em-dash Destination.
Give the record an inbound pointer, or state in that row that it is
delivery-local and takes no durable destination.

**9. AC28's discharge records its method but not its observed result.**
`notes/closeout-records.md` describes the scratch-copy byte mutation of RFC-0096
§9 without the observed digest comparison, so a later reader cannot distinguish a
discharged obligation from a described one.
