# The cross-component rollup — snapshot and pointer

`receive-brief` already answers "is **this** repo's slice delivered?" — its
per-repo coverage reads each spec's `Status:`, follows the `Brief:` back-links,
and rolls a brief's Spec map up automatically. No single repo can answer the
level above: "is the **whole feature** delivered **across all** the components it
was sliced into?" That whole-feature answer is the meta-repo's rollup, and it
**aggregates** each repo's own coverage rather than re-deriving it.

## Shape: a markdown table, one row per slice

Copy the `docs/product/rollups/_template.md` seed. One row per component slice
`decompose-intent` produced, with a pointer back to the slice's brief and to the
component repo's **own** auto-derived coverage:

| Component | Brief (repo + slug) | Contract@version | Status (snapshot) | Coverage pointer |
| --- | --- | --- | --- | --- |

It is **markdown, not YAML**: nothing machine-consumes it in scope, it matches
the markdown coverage map it aggregates, and a schema'd YAML file would invite a
validator script — infrastructure this pack does not ship. (The catalog stays
YAML only because Backstage, a real external tool, mandates `catalog-info.yaml`.)

## The answer is the AND across rows

The whole feature is delivered **only when every row is delivered**. The status
in each row is a **snapshot** of the component repo's authoritative coverage,
plus a **pointer** to it — reference the authority, cache a snapshot, never fork
it (the same pattern as the shared contract).

**Absent-source rows are never silently green.** A row whose component repo has
no `catalog-info.yaml` yet, or no auto-derived coverage yet, carries the explicit
status **`unknown / not-yet-catalogued`**. An unknown row keeps the
AND-across-rows answer at "not yet" — it is *never* counted as delivered. This is
what stops a half-catalogued value stream from reporting a false green.

## Snapshot, not a live feed — and why

The rollup is a **snapshot you reconcile by hand**, not a running tracker. A live
rollup would require the meta-repo to reach into N component repos — auth,
polling, rate limits, idempotency, conflict rules. That is a **running service**,
which is infrastructure deferred to a later live-integration pack and out of this
pack's charter. The trade is honest: the snapshot can go stale between
reconciliations, which is exactly why **currency is the discipline**
(`catalog-currency.md`) — and why each row points at the repo's *auto-derived*
coverage, so only the cached snapshot can drift, never the underlying truth.

## The hard limits this implies

Because there is no hub and no shared tree, the polyrepo costs stand and are
stated, not engineered away: **no atomic cross-repo commit** (a contract change
and its consumers can't land in one PR) and **no shared release train** (each
component releases on its own cadence). An adopter accepts these as the cost of
coordinating without a runtime hub.
