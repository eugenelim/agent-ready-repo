# Intent: <one-line outcome>

> **This is a template, not a schema.** It shows the *shape* of a product
> `intent` — a level-tagged statement of an outcome and the opportunity behind
> it. Copy it to `docs/product/intents/<slug>.md` and fill in what you have; an
> empty heading is a prompt, not an error. A `product-vision`, a
> `product-strategy`, a capability, and a feature intent are the same shape at
> different levels — the `Level:` field is the only difference. Keep only the
> sections that earn their place.

- **Slug:** `<slug>` <!-- kebab-case; matches the filename -->
- **Level:** `<product-vision | product-strategy | capability | feature>` <!-- the altitude this intent sits at; an open recognized set, not a closed enum — name an intervening altitude if your org has one -->
- **Kind:** `<outcome | opportunity>` <!-- optional, additive: the discovery-traceability chain rung this intent occupies on the opportunity-solution tree (outcome = the North Star / chain root; opportunity = a need in the OST). The structural-orphan lint reads this bold-body field to place the intent on the chain. Distinct from Level: (the altitude) — a `Level: capability` intent is placed by Level instead, and a feature intent maps downstream to a brief/spec. Omit it when not running the discovery-traceability chain; an intent still carries both an Outcome and an Opportunity section regardless. -->
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
solution.

Optional JTBD sub-fields — include when framing a job-shaped opportunity so all
three job dimensions are surfaced alongside the struggling moment; free-form
prose above is still valid for quick framing. See
`references/jtbd-job-categories.md` for definitions and examples. -->

<the opportunity — one sentence summary, or use the sub-fields below>

<!-- optional structured JTBD fields (omit for free-form prose) -->
- **Functional job:** <what the user is trying to accomplish>
- **Emotional job:** <how they want to feel during or after the job>
- **Social job:** <how they want to be perceived by others>
- **Struggling moment:** <where the current situation fails them>

## Product-vision fields

<!-- LEVEL-CONDITIONAL — fill only when `Level: product-vision`. The existence
bet: why this product should exist, for whom, through what wedge. This is a
prompt sheet, not a schema — an empty heading is a prompt, not an error; fill
what you have. Drop this whole section at any other Level. -->

- **Customer-shaped pitch:** <the one-liner in the customer's words — what they get>
- **The change:** <what is different for the customer once this exists>
- **The job + struggling moment:** <the job to be done, and the moment it bites>
- **Who, by circumstance:** <the early adopter by situation, not demographic>
- **Existing alternatives:** <what they do today instead, and why it serves them badly>
- **Narrowest wedge:** <the smallest version someone would pay for or adopt now>
- **Demand evidence:** <behaviour or payment that shows pull — not stated interest>
- **Open assumptions (tiered):**
  - *must-test-before-shipping:* <the bet that has to hold before you build>
  - *accept-as-bet:* <a bet you will take without testing>
  - *will-monitor-post-ship:* <something you will watch once it is live>
- **Counter-metrics:** <what you would watch to catch this going wrong>

## Product-strategy fields

<!-- LEVEL-CONDITIONAL — fill only when `Level: product-strategy`. The path:
diagnosis → guiding policy → coherent action. Same prompt-not-schema posture —
an empty heading is a prompt. Drop this whole section at any other Level. -->

- **Central challenge (diagnosis):** <the crux — the one obstacle the strategy must overcome>
- **Guiding policy:** <the overall approach chosen to meet the challenge>
- **Coherent actions (3–5):** <the handful of mutually-reinforcing moves that enact the policy>
- **Problem / segment sequence:** <which problem for which segment, in what order, and why now>
- **Horizon:** <the time / scope window this strategy covers>

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
