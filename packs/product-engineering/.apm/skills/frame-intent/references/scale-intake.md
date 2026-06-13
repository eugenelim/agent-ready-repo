# Scale intake — infer → confirm → ask

**Scale** is the one global axis of the pack. It is resolved once, at intake, and
stamped on the intent (and on the `docs/product/` root the first time). Everything
else — altitude, where the work lives, how it decomposes — follows from it.

| Scale | What it means | Typical top level | Leaf lands as |
| --- | --- | --- | --- |
| `app` | a solo dev / small team in **one repo** | `feature` | a `core` brief in this repo |
| `business-unit` | a product org whose work fans out to **many component repos** | `capability` | per-component briefs (phase 2) |

## The routine

1. **Infer.** Read the workspace:
   - app code present (a lockfile, a source tree) **and** a single deployable
     component → infer `app`.
   - no app code (a docs/product-only repo), or pointers to many component repos
     → infer `business-unit`.
2. **Confirm.** State the inference and why ("this looks like `app` — one repo
   with a Node service; correct me"). A one-word confirm is enough.
3. **Ask** only when inference is genuinely ambiguous (mixed signals, a fresh
   repo). Never guess silently — an unasked-for Scale mis-routes the whole tree.

Stamp the resolved value as `Scale:` on the intent. There is **no config file** —
the artifact records the mode.

## Why it matters here

Scale sets the **default level** (`app` → feature; `business-unit` → capability)
and tells `decompose-intent` whether the leaf is a same-repo brief (`app`) or a
per-component slice that crosses repos (`business-unit`, phase 2). v1 of the pack
serves the **`app` + single-component** path end to end; the `business-unit`
cross-component layer is specified but deferred.

> Scale is the *only* global mode. **Maturity** (greenfield/brownfield) and, in
> `de-risk-intent`, **reversibility** + the **prototype-approach** are per-intent
> flags — not global ceremony.
