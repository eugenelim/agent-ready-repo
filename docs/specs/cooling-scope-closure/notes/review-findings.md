# Review findings not fixed by this delivery

Ten findings survived adjudication across three review rounds on the withdrawn
contract amendment and are recorded here rather than in `[backlog].open`.

**Why not `[backlog].open`.** That collection cannot accept a new entry without
failing a gate. `workspace.toml`'s header states that a `{slug = ...}` table is
"still required" there, because `lint-spec-status.py` invariant (iv) resolves a
spec's `(deferred: <slug>)` anchor from the `slug` key only and "that is a hard
CI gate"; the canonical `{path, kind, source, summary, needs}` shape needs a
`path` to an artifact, and these findings have none, so a canonical entry raises
`missing_artifact` — which
`test_workspace_status_projection.py::RepositoryLifecycleRatchetTests` also
fails on. Meanwhile the write-side ratchet caps `backlog.open` at 160
legacy-shaped entries, `origin/main` sits at 156, and the guard says "Do not
raise this ceiling to make the check pass." Four slots for ten findings is an
allocation decision, and the header says reconciling this contradiction "needs a
governance decision, not a reshape of individual entries". That decision is
itself finding 1 below.

Each entry names what was measured, so none needs re-deriving.

## Repository-wide

**1. Mutation-row discharge is impossible under the plan freeze.** Plans
instruct that each mutation row's observed red is recorded in the plan's
mutation table, but `plan.md` is hash-frozen once `schedule` persists it:
`_loop_guards.check_schedule_current` compares the canonical hash and
`loop-engine` runs `schedule check-current` on every CODE-state transition, so
the recording edit fails. Measured on this delivery: **0 of 20 mutation rows
record an observed red**, and T6 — pinned completed and merged — records none in
its commit either, so its Done-when was never satisfiable. Decide whether a
frozen plan can carry discharge records, or move the recording location to the
discharging commit and update the plan template and every Done-when naming the
table. Owner: `work-loop`.

**2. `[backlog].open` cannot accept a new entry in any shape.** The contradiction
described above, between `workspace.toml`'s stated requirement, the
`missing_artifact` check, and the write-side ratchet. Owner: repository
governance.

**3. `cooling.load_record` reports a missing confinement helper as an invalid
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

**4. No criterion names a `work.*` entry class.** All 33 criteria use a canonical
`docs/specs/<slug>/spec.md` entry. Two defects passed all 33 green in that blind
spot; the second reached `origin/main` in PR #1210. The repair ships here and is
guarded by no test. What the withdrawn amendment would have added: a cooled
legacy `spec/<slug>` entry excluded from both closeout consumers, and a bare-slug
entry reported `unsupported_legacy` *not* excluded — each with an uncooled
control, and the refusal case with a positive control proving the record cools
the artifact (`_cooled_locators` admits a locator only when the member exists, so
without it the criterion passes over an empty cooled set).

**5. The closeout seam keys cooled exclusion on a raw path string.**
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

**6. AC31 cannot fail when the release surfaces agree at a version whose
published code differs from what ships.** Measured 2026-09-02: this branch
changed `packs/core` behaviour while `pack.toml`, `plugin.json` and the topmost
dated `[core]` heading all read `2.21.0`, matching `origin/main` — every AC31
clause passed. That is the hazard
`tests/roster/test_security_checklists_okf_projection.py` documents, and it is
the defect this delivery repairs by hand with the 2.22.0 bump. AC31's floor
literal is also cleared by three releases and cannot fail.

**7. The cooled-membership alias axis is unpinned for legacy entries.** AC4 pins
alias-named cooling for a canonical entry only. The Testing Strategy's own
rationale — two independently written filters can agree on a locator and
disagree on an alias — makes the axis independent. Exposure is nil because
`_cooled_locators` flattens `locator` and `aliases` into one resolved-path set
and `_legacy_membership_is_cooled` reads that single set, so an implementation
splitting that resolution later would satisfy the contract while breaking the
`Always do`. Raised in three consecutive rounds.

**8. A withheld closeout cannot name the record that caused it.** When the cooled
reading is incomplete because a record's review date could not be judged, the run
withholds `invoke-close-work` and emits no finding identifying the record, so a
maintainer sees a blocker with no actionable cause. The Objective accepts this
residual. The comment at `workspace_status.py:700` half-describes it and is
itself wrong: that arm emits no finding, though it does reach `dueness_failed`
and flip `cooling_context_visible`. Adding a finding code was a `Never do` for
this delivery, so closing it needs an owner decision on the surface.

**9. `notes/closeout-records.md` is reachable from no other artifact.** The
spec's Durable Outputs `project-knowledge` row carries an em-dash Destination.
Give the record an inbound pointer, or state in that row that it is
delivery-local and takes no durable destination.

**10. AC28's discharge records its method but not its observed result.**
`notes/closeout-records.md` describes the scratch-copy byte mutation of RFC-0096
§9 without the observed digest comparison, so a later reader cannot distinguish a
discharged obligation from a described one.
