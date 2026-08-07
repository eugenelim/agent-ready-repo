# Cross-component rollup: <one-line outcome>

> **This is a template, not a schema.** It shows the *shape* of a
> **cross-component delivery rollup** — the value-stream meta-repo's answer to
> "is this whole feature intent delivered **across all** the components it was
> sliced into?" Copy it to `docs/product/rollups/<slug>.md` and fill in one row
> per component slice. An empty heading is a prompt, not an error; the
> `align-value-stream` skill keeps it current and never rejects a half-formed
> rollup for non-conformance.

- **Parent intent:** `<slug>` <!-- the capability/feature intent this fans out from (docs/product/intents/<slug>.md) -->
- **Last reviewed:** YYYY-MM-DD <!-- when the snapshot below was last reconciled against each component repo -->

## Why this is a snapshot, not a live feed

This rollup is a **markdown snapshot**, not a running tracker. Each row points at
the component repo's **own** auto-derived brief coverage (the authoritative
source); the status here is a **cached snapshot** of that, reconciled by hand
when you review the rollup — mirroring how the shared contract is *referenced*,
never forked. There is **no runtime hub** reaching into the component repos, and
the polyrepo hard limits apply: **no atomic cross-repo commit, no shared release
train**. Currency is the discipline that keeps the snapshot honest — a stale row
is the failure mode, so review the rollup whenever a slice's status changes.

## Delivery rollup

<!-- One row per component the parent intent was sliced into. The whole feature
is delivered only when EVERY row is delivered (the AND across rows). A row whose
authoritative source is absent — a component repo with no `catalog-info.yaml`, or
no auto-derived coverage yet — carries the explicit status
`unknown / not-yet-catalogued`. NEVER count an absent-source row as delivered:
an unknown row makes the AND-across-rows answer "not yet", never falsely green. -->

| Component | Brief (repo + slug) | Contract@version | Status (snapshot) | Coverage pointer |
| --- | --- | --- | --- | --- |
| `<component>` | `<repo>` · `<slug>` | `<contract>@<version>` | `<delivered \| in-progress \| not-started \| unknown / not-yet-catalogued>` | `<link to that repo's own coverage>` |
| `<component>` | `<repo>` · `<slug>` | `<contract>@<version>` | `<status>` | `<link>` |

**Delivered across all components?** `<yes only when every row is delivered; otherwise no — and any unknown / not-yet-catalogued row keeps the answer no>`
