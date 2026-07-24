# Tutorial: First session with the digital-product profile

This tutorial walks a product manager, product designer, or product lead through
their first session using the `digital-product` profile — the portable toolkit for
owning strategy → shaping → experience → build hand-off for a digital product.

By the end, you will have:

- Installed the profile in one command
- Grounded your strategy in a committed market situation and adoption hypothesis
- Mapped the customer journey and derived the screen list
- Handed the Digital Experience Contract to the build repo's `core` pack

**Time:** 3–6 hours for a realistic product scope across all four packs.
**Pre-requisites:** `agentbundle` installed and a target catalogue available.

---

## Step 1. Install the profile

```bash
agentbundle install --profile digital-product <catalogue>
```

This installs four packs at user scope, in deps-first order:

| Pack | What it gives you |
|---|---|
| `desk-research` | Evidence-grounded research — scoping, source curation, synthesis, adversarial review |
| `product-strategy` | Market situation → adoption hypothesis → OKR cascade → strategy-to-experience handoff |
| `product-engineering` | Shaping queue, first-success operationalization, thin-slice learning contract |
| `experience-design` | Full XD chain: journey → screens → design intent → per-screen design → independent review |

Verify installation:

```bash
agentbundle list <catalogue>
```

All four packs should appear at `scope: user`.

---

## Step 2. Set the market context with desk-research

Before strategy work begins, ground the session in evidence.

1. Run the `desk-research` skill and scope the research question:

   > "Scope a research project on [your market/domain]. I want to understand the competitive
   > landscape, key user behaviors, and what's driving adoption in this space."

2. The agent will run `frame-research-question`, curate sources, and synthesize findings.
   Review the synthesis before moving to strategy. If the synthesis describes the market
   but doesn't surface adoption signal (how users actually behave, not just who they are),
   redirect and re-run.

3. Output: committed research synthesis in `docs/product/shaping/` ready to feed the
   situation analysis.

---

## Step 3. Run the product-strategy chain to produce strategy artifacts

### 3a. Build the market situation

Run the strategy situation analysis:

> "Run the full situation analysis for [product/initiative name]. Use the desk-research
> outputs in docs/product/shaping/ as inputs."

The agent runs:
- `run-pestle-analysis` — macro environment (six lenses)
- `run-porters-five-forces` — competitive landscape and structural position
- `run-bcg-matrix` — portfolio position
- `run-swot` — synthesizes all inputs into a SWOT with adoption hypothesis and differentiation mechanism

**Human gate:** review the SWOT. Approve only when:
- The adoption hypothesis is named (which SO pair produces a first-success event, and what is that event specifically)
- The differentiation mechanism is named (a structural advantage, not a generic moat claim)
- The most acute threat is named

If the SWOT has generic strengths like "talented team" and no adoption hypothesis, redirect before the PRFAQ stage.

### 3b. Commit the altitude-0 direction

> "Write a PRFAQ for [initiative name] based on the committed SWOT."

The agent runs `write-prfaq` to produce:
- A press release naming a specific person with a specific pain
- A named first-success event (a specific observable behavior — not "user signs up")
- An internal FAQ with a success metric traceable to the first-success event

**Human gate:** approve the PRFAQ. The first-success event named here is the measurement
contract that all downstream work — PE shaping, XD journey, instrumentation — must trace
back to. If the first-success event is "user completes onboarding", redirect.

### 3c. Cascade OKRs and complete the strategy-to-experience handoff

> "Run the OKR cascade for [initiative] and produce the strategy-to-experience handoff."

The agent runs:
- `run-okr-cascade` — cascades company OKRs, derives the causal metric tree, routes gaps to workspace.toml
- `define-ux-strategy` — experience vision, goals+measures with value loop and adoption hypothesis
- `define-content-strategy` — Halvorson quad organizational governance layer

Together these populate the seven Strategy fields of the Digital Experience Contract:
Target User and Context, Diagnosis and Strategic Choices, Adoption Hypothesis, Value Loop,
Metric Tree, Differentiation, Assumptions and Kill Criteria.

---

## Step 4. Run experience-design to design the screens

### 4a. Map the customer journey and derive the screen list

> "Map the customer journey for [the feature or product]. Derive the screen list from the journey."

The agent runs `journey-mapping` then `user-flow`. Review the journey map before the
screen list is derived — if the map describes what the current product does rather than
what the user is trying to achieve, redirect. A screen list derived from the wrong model
designs the wrong product, faithfully.

**Human gate:** approve the journey and screen list. Remove any screen not traceable to a
moment in the journey.

### 4b. Establish design intent

> "Establish the aesthetic direction and token foundation for [product name]."

The agent runs:
- `design-principles` — 3–5 named decision rules grounded in journey moments
- `creative-direction` — named visual character, emotional and brand goals
- `design-token-taxonomy` — token/scale taxonomy derived from the aesthetic direction
- `design-system-foundations` — semantic color roles, typography, spacing, radius, focus, status tokens

**Human gate:** approve the aesthetic direction and token set. Reject tokens that introduce
hardcoded values outside the semantic token system. An aesthetic direction that says
"clean and professional" is not specific enough — redirect.

### 4c. Design each screen

For each screen in the inventory:

> "Design [screen name] from the screen inventory."

The agent runs:
- `information-architecture` — identifies the page archetype, names the product object, applies the attention and permission contracts
- The appropriate genre-specific skill (`conversion-design`, `workspace-design`, `analytical-design`, etc.)
- `interaction-design` — states, transitions, feedback patterns against WCAG 2.2 AA
- `design-review` — three-pass self-check (cold-read → primary task + unhappy path → full 18-state quality-floor review)

Watch for missing states: if a screen has no empty state, loading state, or error recovery,
name it before the independent review — catching it here is cheaper.

### 4d. Run the independent experience-reviewer

> "Run the experience-reviewer on the completed screen set."

The agent dispatches the forked-context `experience-reviewer` — no access to the authoring
session — returning findings across the full screen set:
- Handle-all-states violations (missing empty, loading, error, success states)
- WCAG 2.2 AA failures (color contrast, label associations, focus order)
- Aesthetic inconsistencies with the approved direction

**Human gate:** review the findings. Apply all Blockers before design intent feeds the build.
Handle-all-states violations are the most common finding — a screen that looks good in the
happy-path state but has no designed error recovery is the canonical blocker.

---

## Step 5. Hand off to the build repo's core pack

The Digital Experience Contract — now populated with strategy, shaping, and experience
fields — is the hand-off artifact.

In the build repo:

```bash
agentbundle install --pack core <catalogue>
```

Point the build loop to the contract:

> "The Digital Experience Contract is at docs/design/digital-experience-contract.md.
> Use it to ground the build — confirm the first-success event matches what we'll instrument."

The `core` pack's `work-loop` and `frontend-engineering` skill read the contract fields to
ground build decisions in the strategy and design intent. The first-success event named in
Step 3b is the instrumentation anchor — if the build loop doesn't instrument it, the
measurement contract is broken.

---

## What you've built

After this tutorial, you have a connected chain:

```
desk-research synthesis
  → market situation (SWOT with adoption hypothesis + differentiation mechanism)
    → PRFAQ (first-success event as measurement contract)
      → OKR cascade + causal metric tree
        → strategy-to-experience handoff (7 Digital Experience Contract strategy fields)
          → shaping brief (first-success operationalization)
            → journey map + screen list
              → aesthetic direction + token foundation
                → per-screen designs (independently reviewed)
                  → Digital Experience Contract (complete)
                    → build loop (core pack, anchored to first-success event)
```

Each step is traceable to the one before. The first-success event named in the PRFAQ is
the same event the OKR cascade builds a metric tree around, the journey map centers, the
instrumentation plan targets, and the build loop measures. That traceability is the contract.

---

## Next steps

- Run the cross-pack experience eval to validate the full chain:
  [How to run the cross-pack experience eval](../how-to/run-cross-pack-eval.md)
- Explore the full experience-design how-to guides:
  [Thread a feature from journey to screens](../how-to/author-design-intent.md)
- Understand the 18-state quality floor all screens must clear:
  [State coverage reference](../reference/state-coverage.md)
