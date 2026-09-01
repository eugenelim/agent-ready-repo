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
move together, AC4 repeats that for an alias-named entry, and AC5 pins that
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

Computed this session:

| Criterion | Target | SHA-256 |
| --- | --- | --- |
| AC28 | RFC-0096 §9 byte range (2 861 bytes) | `e49f49f12fc7dccff4cd962cecff7be003672283d8a750097a238001b222a45e` |
| AC23 | `close-work/scripts/cooling.py` | `d6bd7c6e47d5a23e45a9f5ee5a8d5506d3435b1da00facde96f1fbfba5bf061c` |
| AC23 | `delivery-lifecycle-record.schema.json` | `557e3d60b8fd5647a06fbc2225de51a52cfff1b8777fd3d917e91bcebbe27878` |
| AC23 | `status-projection-and-context-exclusion/spec.md` | `2cac21ca5f84e0f4e477a6bab432429a55034f6851dc152cfcd93611e9e3523d` |
| AC23 | `status-projection-and-context-exclusion/plan.md` | `93958585c454ab761a79f2e358e546f5d0cc7e7c8e722a8cf42114ab22a7c487` |
| AC23 | `thirty-day-cooling-and-retirement/spec.md` | `3255b1a8b12e2cfaeccc5e6c97a7047467e8ca8e001467fdefc6757318d4c95f` |
| AC23 | `thirty-day-cooling-and-retirement/plan.md` | `2c416277c607b9f7b2b617e06a79a58f6059f43bd2d6c2ebef35ea6af810e3e7` |

AC13 pins a seventh value that is not a file digest: the SHA-256 of the
`test_`-prefixed function names in Wave 6's roster file, sorted and newline
joined, is `660b7204a2fe32f5d75ab03f43828934ad42c8b06b572b99292585bf13bbf8e6`
over the 67 names present today. A name set rather than a count, because a count
survives deleting an assertion from an unrelated function.

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
