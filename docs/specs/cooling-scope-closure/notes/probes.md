# Probes taken before the contract was written

Recorded during PLAN, 2026-09-01, against merge base `a06fb2e6c` (core 2.18.2).
Each probe is side-effect-free and was run from the repository root. Every
criterion that rests on a runtime fact cites one of these rather than asserting
it.

## Probe 1 — a pruned artifact whose workspace entry survives never reaches the absent-target refusal

The question a later wave depends on: when Wave 7c prunes an artifact, is
removing the file enough?

A dependant that is `Approved` with an `Approved` plan on disk — so its only
possible refusal is its dependency — points its `needs` at a `spec` path whose
file is absent. The only variable is whether the target keeps its `work.shipped`
entry:

```
membership KEPT (file pruned, entry left behind):
   [('unsatisfied_dependency', 'dependency has findings')]
membership REMOVED:
   [('missing_dependency', 'dependency target missing')]
```

A live membership with an absent artifact raises `missing_artifact` in
`_structural_findings`, which puts the path in `structurally_blocked_paths`, and
`_dependency_is_satisfied` refuses there **before** the absent-target refusal.

Two consequences this contract carries:

1. Nothing in this delivery depends on the distinction, because this delivery
   projects no receipt. It is recorded here because it is the reason the Wave 7c
   follow-on row states an obligation rather than a scope: pruning must remove
   the workspace entry as well as the file, or the dependants the receipt exists
   to protect are stranded with every criterion green.
2. It is also why the completion receipt is a separate contract. Its load-bearing
   precondition is a repository state — entry gone, file gone — that only
   closeout produces, and RFC-0096 §7 says so directly: "Closeout removes the
   live entry and keeps `{delivery_id, outcome, completion_event,
   evidence_ref}` only while a live dependency cites it."

## Probe 2 — `closeout` describes one initiative, and `initiatives[]` carries only active ones

`_closeout_projection` sorts the initiatives whose status is `active` or
`paused` by slug and projects the first. `initiatives[]` skips every non-`active`
initiative. A workspace holding one `paused` initiative and nothing else emits:

```
exit: 0
closeout present: True
closeout: {"all_specs_shipped": true, "closeout_blockers": [],
           "cooling_context_visible": false, "initiative_eligible": false,
           "next_action": "resume-or-keep-paused", "paused": true}
initiatives[] entries: []
```

So a paused projection has a `closeout` block and **no** `queue_empty` value
anywhere in the response. AC3's agreement criterion is therefore measurable only
where the projected initiative is `active`, and AC11 pins the paused case
separately. Writing one criterion over both would have been unsatisfiable for
the paused input — the residual round-1 review named and the first repair made
explicit without closing.

## Probe 3 — the two closeout derivations, and why AC3 compares direction and AC5 pins the shapes

```
all_specs_shipped = not (initiative.work.queue or initiative.work.active)
queue_empty       = len(ini.work.queue) == 0
```

Different predicates over different lists. An initiative with an empty queue and
one active entry reports `all_specs_shipped` `false` with `queue_empty` `true`,
legitimately and today. Wave 6's follow-on requires that "the two must agree"
about the **cooled set**, not that they hold the same value, so AC3 asserts they
move together between the cooled fixture and its uncooled control, and AC4
repeats that for an alias-named entry. AC5 is a separate single-run assertion
over a third fixture — empty queue, one uncooled active entry — pinning that
neither derivation's shape widened between the cooled fixture and the same fixture with
`docs/lifecycle/` removed. An equality assertion would fail on correct code, and
two separate assertions would both pass against the defect Wave 6 reverted.

## Probe 4 — the pinned digests, and why no frozen file is edited

An earlier draft annotated Wave 6's frozen `**Status:**` line and needed a
digest rule that excluded that region. The annotation was dropped: the
convention's non-supersession pointer is licensed for a deleted
`workspace.toml [backlog].open` anchor, and Wave 6 registered these follow-ons in
RFC-0096 §9, so no anchor disappears and no licence applies. The erratum is the
record of closure instead, and this delivery edits no frozen file — which makes
every pinned digest a plain whole-file comparison.

Every digest this contract pins is stated once, in the spec: the six file
digests in AC23, the `test_`-prefixed name-set digest in AC13, and the §9
byte-range digest in AC28. They are not restated here — an earlier draft carried
a second copy and the two disagreed about what the name-set value covered.

Two facts about those values that belong with the evidence rather than the
criteria:

- AC13's digest is computed over the **post-rename** name set: the 67 names at
  this branch's base with AC12's retirement replaced by
  `test_a_fully_cooled_initiative_reports_all_specs_shipped`. An earlier draft
  pinned the pre-rename value, which AC12 then made unreachable.
- AC28's range is the 2 861 bytes from the `## 9. Initiative waves` heading up to
  but excluding the `## 10. Risks and revisit conditions` heading.

Wave 5's directory meets the convention's freeze predicate — its `plan.md` is
`Status: Done`. Wave 6's `plan.md` is still `Status: Approved`, so that
directory does not literally meet it; AC23 pins both plans regardless.

## Probe 5 — the cardinality and identifier bounds this delivery does not need

Recorded because a round-2 security finding turned on them and the facts belong
with the evidence rather than in a review artifact that is not committed:

- `contracts/jsonschema/workspace-entry.schema.json` caps `needs` at
  `maxItems: 50`; `delivery-lifecycle-record.schema.json` caps `aliases` at 16.
  So a repository precedent exists for **deriving** a collection bound from a
  published sibling cap rather than inventing one.
- `workspace_status_engine._MAX_FINDING_IDENTIFIER = 200` — the bound this
  module applies to every untrusted `workspace.toml` value that becomes a
  finding path rendered into agent context.

Neither constrains this delivery, which adds no collection and no finding code.
Both are load-bearing for Wave 7a-ii and are carried on its follow-on row.

## Probe 6 — AC17's mutation is a killing one, and the fixture shape is why

AC17-AC22 pin a decision rather than a change, so the question is whether their
control pairs *could* differ under a wrong implementation. `repair-plan` calls
`analyze(..., cooling_enabled=False)`, and the mutation row is exactly the flip
of that flag. Measured over AC17's fixture — one `work.queue` entry whose spec is
`Status: Shipped`, so a Type-2 repair operation exists:

```
cooling_enabled=False  (today)   type2 findings=[docs/specs/cooled-one/spec.md]  files_read=4
cooling_enabled=True             type2 findings=[]                              files_read=2
```

The repair operation for the cooled spec disappears. So the mutation reddens
AC17, the criterion is a real regression guard, and the guard has a killing edit.

The fixture shape is load-bearing, not incidental. The difference appears only
because the queued spec is `Shipped` and therefore produces a Type-2 finding. An
ordinary `Approved` spec yields no operation in either run, both sides are empty,
and the mutation is silent — which is the vacuity AC18's fixture requirement and
T1's Done-when exist to prevent.

## Probe 7 — a legacy entry never reaches `canonical.ready`

The realness guard for the migration criteria was first written against
`canonical.ready`. That field cannot express it. A legacy queue entry is a bare
string, not a table, and `_parse_membership_entry` returns no membership for that
shape — so it lands only in `legacy_memberships`, and `evaluations`, which is the
sole source of `ready`, is built from memberships. Measured on the
migration-effects fixture's `"spec/legacy"` shape with
`docs/specs/legacy/spec.md` cooled:

| Run | `canonical.ready` | `canonical.legacy_memberships` |
| --- | --- | --- |
| `docs/lifecycle/` removed | `[]` | `['spec/legacy']` |
| record present | `[]` | `[]` |

`ready` is empty in both runs, so a guard on it passes whatever the cooled set
does. `legacy_memberships` is the discriminating field, and T1's guard asserts
that pair.

One shape correction this probe forced: the first attempt used
`{path = "spec/legacy", needs = []}`, a table, which the parser accepts as a
canonical entry and never treats as legacy — both fields came back empty and the
guard looked broken when the fixture was. The legacy form is the bare string, as
`packs/core/tests/skills/workspace-status/test_work_intake_migration_effects.py`
writes it.
