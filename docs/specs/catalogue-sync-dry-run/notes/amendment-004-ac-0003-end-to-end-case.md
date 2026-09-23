# Amendment 004 — T5's `Tests` gains AC-0003's end-to-end case

- **Date:** 2026-09-17
- **Run:** `b9900572-04c5-40b5-ac46-a02ea5b54bd5`
- **Raised at:** `CODE-IMPLEMENTATION`, after wave 2 (T3) closed. **T5 is
  unstarted.**
- **Owner authority:** the repository owner, in session, chose "add the
  end-to-end case to T5" over a structural guard in T3 and over accepting the
  limit with a ledger note. This file is that decision's repository record.

## The defect

AC-0003 reads:

> Given a schema-3 state whose recipe records `attribution = "attributed"`,
> `tooling = "vendored"`, and `guides = "none"`, a `--dry-run` invoked without
> `--attribution`, `--tooling`, or `--guides-mode` replays `white-label`,
> `external`, and `selected` respectively.

The criterion is about **a `--dry-run` invocation**. A search of the plan found
AC-0003 named in exactly two places, both inside T3, and T3's case sits at the
`collect_fields` seam. No task drove the invocation the criterion describes.

At that seam the violation is **structurally inexpressible in one step**.
Mutating `collect_fields` to prefer a recorded attribution left T3's case
passing, because `_SelfHostRecipeInput` carries nine fields and no mode, so the
attribute does not exist and the read falls through. `_load_self_host_recipe`
drops the recorded modes before `collect_fields` is reached. That dataclass —
not `collect_fields` — is what currently enforces the property, and nothing
asserts its shape.

This matters because it is the repository owner's stated constraint on this
phase: the attribution, tooling and guides modes must never be read from the
recorded state, since reading them from state reintroduces the hole phase 1
closed. Today that line is held by a structure no test pins.

The contract-alignment lint passes throughout, because it checks only that some
task entry names each criterion — not that the naming task's seam can express
the criterion's violation. A criterion can therefore be fully "covered" by the
lint and untested in substance.

## Scope

Only `docs/specs/catalogue-sync-dry-run/plan.md`, and only T5's `Tests` field,
which gains one entry:

```
+ - A `--dry-run` over a state whose recipe records `attribution =
+   "attributed"`, `tooling = "vendored"` and `guides = "none"`, invoked with
+   none of the three mode flags, reports the replayed modes as `white-label`,
+   `external` and `selected` (spec AC-0003).
```

No acceptance criterion changes — AC-0003's text already demands this, and the
amendment brings a task entry into line with it rather than altering the
contract. No task outcome, `Touches`, `Done when`, or dependency edge changes.
No other task's section changes. `spec.md` is untouched; its canonical
`approved_spec_hash` has been `4d14dd64a131…` across every approval in this run.

T5 is unstarted, so no started-task section is edited. The controlled amendment
path is still used because `Tests` is a pinned field read by a completion gate,
and a verification obligation.

## Why T5 and not T3

T5 is where the verb first exists, and it is the first point at which a state
file's recorded modes can travel the whole path to rendered output. At that
level the case fails in one step: if any future change plumbs a recorded mode
through, the printed plan reports the recorded value instead of the default.

T3's case stays as it is. It locks the outcome at its own seam and is not
wrong — it is simply not sufficient on its own, which the ledger now records.

## Scoped review

The changed task is T5. Its declared dependants are T6, T9 and T10, each of
which names T5 in its `Depends on`.
