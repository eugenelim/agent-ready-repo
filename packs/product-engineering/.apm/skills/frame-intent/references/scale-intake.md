# Scale intake — infer → confirm → ask

**Scale** is the one global axis of the pack. It is resolved once, at intake, and
stamped on the intent (and on the `docs/product/` root the first time). Where the
work lives and how it decomposes **follow from it**; the starting **altitude** it
merely *suggests* — `Level` is decoupled from Scale and overridable in one word.

| Scale | What it means | Suggested starting altitude | Leaf lands as |
| --- | --- | --- | --- |
| `app` | a solo dev / small team in **one repo** | `feature` (a known feature) or `product-vision` (a greenfield concept) | a `core` brief in this repo |
| `business-unit` | a product org whose work fans out to **many component repos** | `product-strategy` or `capability` | per-component briefs, coordinated from a value-stream meta-repo |

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

Scale **suggests a starting altitude** — it does not stamp one. The suggestion:
an `app` greenfield product concept → `product-vision`; an `app` effort with a
known feature in hand → `feature`; a `business-unit` effort → `product-strategy`
or `capability`. You override it in one word. Scale's **load-bearing** role is
unchanged: it tells `decompose-intent` whether the leaf is a same-repo brief
(`app`) or a per-component slice that crosses repos (`business-unit`). At
`business-unit` Scale
the cross-component artifacts — catalog, shared contracts, architecture, and the
delivery rollup — live in a coordinating **value-stream meta-repo** (the
`align-value-stream` skill); `decompose-intent` slices each feature intent into
one brief per component and seeds that rollup.

> Scale is the *only* global mode. **Maturity** (greenfield/brownfield) and, in
> `de-risk-intent`, **reversibility** + the **prototype-approach** are per-intent
> flags — not global ceremony.
