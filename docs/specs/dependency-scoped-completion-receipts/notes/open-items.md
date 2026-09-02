# Open items for the human editing pass

Review round 3 reported 5 of 5 blockers as introduced by round 2's patch and
recommended a human pass over § Testing Strategy, § Tasks and § Mutation proofs
**as a unit** rather than another patch round. This file records what was
measured, so none of it needs re-deriving.

Two items are substantive. The rest are cross-reference staleness.

## Substantive 1 — adding an optional `Dependency` field changes a persisted identity

Measured 2026-09-02. `canonical_repository_identity` serializes every need with
`dataclasses.asdict` (`workspace_status_engine.py:1598-1601`), so adding an
optional `receipt` field makes **every** need in **every** workspace gain a
`"receipt": null` key:

```
before: {"kind": "spec", "path": "a", "type": "local"}
after : {"kind": "spec", "path": "a", "receipt": null, "type": "local"}
```

That value is persisted as `repository_identity` in a
`work-intake-migration-ledger.v1` (`workspace_status.py:1909`) and re-checked at
apply time (`:1917`, `workspace_status_engine.py:5271-5275`). An in-flight
migration ledger would therefore fail its identity check after this change.

`plan.md` § Rollout currently asserts "No migration and no deployed data",
which is true of the receipt payload and false of the identity. Either narrow
the claim to the payload and state the ledger consequence, or exclude a `None`
receipt from the serialized form so the identity is unchanged for every need
that carries no receipt. The second option is available and is probably right —
it makes the change genuinely additive — but it is a design decision, not an
edit.

## Substantive 2 — `_LOCAL_NEED_FIELDS` needs a required/optional split

`workspace_status_engine.py:79` is `frozenset({"type", "kind", "path"})` and
`:761` compares with `set(raw) != _LOCAL_NEED_FIELDS` — exact equality. Adding
`"receipt"` to that frozenset makes the receipt **mandatory on every local
need**, which would reject every entry in the current `workspace.toml`. The
check has to become required-plus-optional. Probe B fact 3 records the
consequence of the current behaviour; the plan does not name the constant or
the split, and it is load-bearing for T2.

## Cross-reference staleness, by location

Each is a statement that a previous round's repair left behind. None changes a
decision; all of them make a frozen `plan.md` internally inconsistent.

| Where | What is stale |
| --- | --- |
| `spec.md` § Testing Strategy | Uses pre-renumber AC numbers. AC10 is declared a producer return-code check and AC11 a documentation check; AC13 and AC14 have no declared mode; the engine block says AC4–AC9 and now runs to AC11. |
| `spec.md` § Testing Strategy | Claims AC5 holds against the unmodified repository. Probe B fact 3 shows a receipt-bearing need is rejected today, so AC5's fixture does not parse. |
| `spec.md` Durable Outputs, user-documentation row | Cites AC12 and AC13 as evidence; AC13 is the producer criterion. Should be AC12 and AC14. |
| `spec.md:138` | `plan_completion_receipt` is defined at `close_work.py:690`; `:688-689` are blank. |
| `plan.md` T2 Approach | Two contradictory parser instructions. The first is the pre-patch "carry through as opaque bounded text, validate at the call site after `:2690`" — the placement § *Behavior & rules* proves unreachable. Delete it. |
| `plan.md` T1 | Edits `workspace_status_engine.py` for the digest constant but carries no `FORCE=1 make build-self`, no projection paths in Touches, and no drift gate in Done-when. The constant lives in four homes. |
| `plan.md` T4 Touches | Omits `guides/core/how-to/close-and-disposition-work.md`, which AC14 requires and T4's Approach edits. |
| `plan.md` T4 Done-when | Still claims the projection suite proves the finding-code documentation, which moved to T2. |
| `plan.md` § Mutation proofs, AC10 | The mutation cannot redden AC10. With the branch inside the `safety_finding is not None` guard, a present artifact never enters the body, so removing the `missing_dependency` condition changes nothing. The mutation must move the check outside that guard. |
| `plan.md` § Mutation proofs, AC7a/b/c | Observations are wrong for the parser/satisfaction split. AC7's fixture carries `outcome = "completed"`, so under AC7b and AC7c the receipt validates and the dependency is *satisfied* — no finding, not `unsatisfied_dependency`. AC7a names a satisfaction-time site that no longer exists. |
| `plan.md` § Mutation proofs, AC7e | "Move validation into the need parser" is no longer well defined, since the parser legitimately validates shape. The property guarded is that the parser emits a *sentinel* rather than a finding; state the mutation as making it emit a finding. |
| `plan.md` § Mutation proofs, AC8 | `_canonical_failure_payload` (`workspace_status.py:396-406`) returns `blocked` holding a synthetic `workspace.toml` entry, not empty. AC8 still kills on the exit-code clause. |
| `plan.md` § Mutation proofs, AC9 exemption | The stated reason — "a regression pin that holds against the unmodified repository" — is false for the same reason as AC5. |

## What held up

Round 3 re-verified and found accurate: every line citation in the spec's
Assumptions and the plan's Constraints and Design; that all `invalid_receipt`
emitters are confined to `_cross_repo_receipt_satisfied`; the finding-code
documentation gate being a superset comparison; the `x-spec` assertion being
exact equality; `self_host.py`'s runtime pairs and dirty-tree refusal; the
curation guard's prefixes and carve-outs; all three lifecycle-record JSON paths
and their values; every `plan_completion_receipt` call site and `_authority`
count; and the `[backlog].open` summary being under its 500-character cap.

The decisions in ADR-0103 are unaffected by everything above.
