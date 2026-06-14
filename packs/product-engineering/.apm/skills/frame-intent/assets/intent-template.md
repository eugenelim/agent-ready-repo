# Intent: <one-line outcome>

> **This is a template, not a schema.** It shows the *shape* of a product
> `intent` — a level-tagged statement of an outcome and the opportunity behind
> it. Copy it to `docs/product/intents/<slug>.md` and fill in what you have; an
> empty heading is a prompt, not an error. A capability intent and a feature
> intent are the same shape at different levels — the `Level:` field is the only
> difference. Keep only the sections that earn their place.

- **Slug:** `<slug>` <!-- kebab-case; matches the filename -->
- **Level:** `<capability | feature>` <!-- the altitude this intent sits at -->
- **Scale:** `<app | business-unit>` <!-- resolved at intake by frame-intent -->
- **Maturity:** `<greenfield | brownfield>` <!-- brownfield unlocks current-state inputs -->
- **Parent intent:** <!-- optional: the higher-level intent this was decomposed from; omit at the top of the tree -->

## Outcome

<!-- LOAD-BEARING. What changes, and how you'll know. Name a *steerable input
metric* you can directly move, the *lagging outcome* it should drive, and a
*guardrail* that must not get worse. A qualitative-but-falsifiable outcome is
fine in 0-to-1 — name the signal you'd accept as proof. -->

- **Input (steerable):** <the metric you can move directly>
- **Outcome (lagging):** <the result it should drive>
- **Guardrail:** <what must not get worse>

## Opportunity

<!-- LOAD-BEARING. The solution-independent need behind the outcome — what the
user is trying to get done (a job / opportunity), framed without baking in a
solution. -->

<the opportunity>

## Assumptions

<!-- What must be true for this bet to pay off. de-risk-intent picks the
riskiest one, predeclares a kill condition in the test's own currency, and tests
it under the chosen prototype-approach. -->

- <assumption>
- **Knowledge surface:** <name of the retrieval surface frame-intent consulted, or "none detected"> <!-- the audit home for frame-intent's knowledge-surface consult (see references/knowledge-surfaces.md); "none detected" is the trigger for the ask-and-lower-confidence path. Drop this line if no surface was relevant. -->

## Decomposition

<!-- The next level down: child intents (a lower `Level:`) or, at the leaf, the
spec/slice this becomes. At app scale the leaf feature intent *is* a `core`
brief — `receive-brief` takes it from there. Leave empty until decompose-intent
runs. -->

-

### Decomposition decisions

<!-- Optional log: why the cut went this way, plus any branch you considered and
dropped or replaced — with a pointer to the killed child's de-risk verdict when
an upward kill forced the re-cut. A line or two per decision; omit if the cut was
obvious. Keeps the parent from reading as if the tree were always this shape. See
decompose-intent step 2. -->

-
