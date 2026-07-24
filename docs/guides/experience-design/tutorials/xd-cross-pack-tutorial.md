# Walk the full XD chain: SaaS onboarding from research to reviewed screens

**What you'll build:** A complete set of committed design artifacts for a SaaS
onboarding flow — research brief, strategy artifacts, customer journey, screen
flow with per-screen briefs, token foundation, copy voice, and a reviewed
design ready for the build handoff.
**Prerequisites:** `desk-research`, `product-strategy`, and `experience-design`
packs installed. No prior artifact required — this tutorial starts from a blank
repo.
**Time:** Two to three hours end to end; each phase is independently stoppable.

> **Tutorial** — learning-oriented. Follow these steps in order to see how four
> discipline packs connect into one coherent product experience. The steps are
> cumulative: each step's output feeds the next skill's input. For *how* to use
> any individual skill on a live task, see that pack's how-to guides.

This tutorial uses a single surface throughout: **SaaS onboarding for Velodata
Analytics**, a fictional B2B analytics product. A new user has just signed up,
landed on an empty workspace, and needs to connect their first data source, see
a meaningful chart, and share it with a teammate before they churn. Every step
anchors to that surface — the fictional product is a prop; the methods travel to
yours.

The tutorial covers four handoff points where one discipline's output becomes
the next discipline's input:

1. Research brief → SWOT + PRFAQ (desk-research hands to product-strategy)
2. Strategy section of the Digital Experience Contract → journey map
   (product-strategy hands to experience-design)
3. Token taxonomy → design system foundation (design-token-taxonomy hands to
   design-system-foundations)
4. Screen brief with IA archetype → copy voice → quality floor (user-flow
   → copy-direction → design-review)

---

## Part 1: Research

### Step 1 — Start a research project on onboarding friction

**What to type:**

```
start a research project on SaaS onboarding friction — why do new analytics users churn in the first week
```

**Skill that fires:** `desk-research-project-start`

The phrase "start a research project" triggers project mode (not a one-off
lookup). The skill asks where to put the project folder if it cannot resolve a
location on its own, then scaffolds the folder.

**What you get:**

```
.context/desk-research/2026-MM-DD-saas-onboarding-friction/
  overview.md          ← question, working_hypothesis (empty), phase: capture
  sources/
```

Open `overview.md`. The `question` field records what you asked. The
`working_hypothesis` is empty — you'll form it as sources accumulate. The
project starts in the **capture** phase.

> The folder lands in scratch space (gitignored `.context/` or a user-level
> path) by default. Research corpus stays out of the repo; the brief it
> produces is what travels.

---

### Step 2 — Synthesize the research brief

After adding or collecting a few sources, tell the skill you're ready:

**What to type:**

```
synthesize the onboarding friction project
```

**Skill that fires:** `desk-research-project-synthesize`

The skill reads the source files and the digest, then writes the output brief.

**What you get:**

```
onboarding-friction-brief.md
```

Open the brief. Notice four things:

1. The **bottom line is the first content line** — the key finding about where
   users churn, before any supporting detail.
2. Every load-bearing claim carries a citation and a confidence tag
   (`[high]` / `[moderate]`).
3. It ends with a **Known unknowns** section — the questions a complete answer
   still needs.
4. The brief is self-contained: everything needed is inlined; you can hand this
   single file to the next step.

**What the brief should surface for Velodata Analytics:** time-to-value exceeds
the user's patience threshold at the empty state — no chart appears until after
the data source connection flow, which has four steps and a copy-paste token,
and most users abandon at step 3. The first meaningful output takes eleven
minutes on average.

---

> **Handoff 1: desk-research → product-strategy**
>
> The research brief is the input to the strategy skills. Specifically:
>
> - The "eleven-minute time-to-value" finding informs the SWOT's Weaknesses
>   quadrant.
> - The "abandonment at step 3 of the token flow" finding becomes the
>   evidence base for the PRFAQ's customer problem statement.
> - The Known unknowns section flags which claims the strategy layer needs
>   to test before committing to a direction.
>
> You do not need to reformat the brief. The `run-swot` and `write-prfaq`
> skills read narrative input and extract what they need.

---

## Part 2: Strategy

### Step 3 — Run a SWOT on the onboarding opportunity

**What to type:**

```
run a SWOT for Velodata Analytics, focused on onboarding — use the friction research brief as the evidence base
```

**Skill that fires:** `run-swot`

The skill works one quadrant at a time — Strengths, Weaknesses, Opportunities,
Threats. It will ask for internal claims (present-tense) and then external
claims (forward-looking). Give concrete claims, not adjectives: "the token
copy-paste step causes 34% of users to abandon at step 3 [moderate confidence]"
is a Weakness; "complex setup" is not.

**What you get:**

```
docs/product/shaping/swot-analysis.md
```

The four quadrants, committed. The Weaknesses quadrant should name the
eleven-minute time-to-value and the token flow abandonment. The Opportunities
quadrant should name competitors' shorter time-to-value benchmarks (if your
research surfaced them) and the activation rate uplift achievable by surfacing a
sample chart before the connection flow.

---

### Step 4 — Write a PRFAQ and fill the Digital Experience Contract

**What to type:**

```
write a PRFAQ for the Velodata onboarding redesign — the bet is: users who see a meaningful chart in under three minutes activate at 2x the baseline rate
```

**Skill that fires:** `write-prfaq`

The PRFAQ follows Amazon's format: a press release (what ships and why it
matters) and an FAQ (what breaks, what it costs, what success looks like). The
skill will ask you to confirm or refine the customer problem statement and the
key claims before it writes.

**What you get:**

```
docs/product/shaping/prfaq-onboarding-redesign.md
```

**What to look for in the PRFAQ:**

- **Strategy → Experience section:** the skill produces a block that names the
  first-success event ("user sees a chart with their own data"), the repeat-value
  behavior ("user shares chart with teammate within the same session"), and the
  value loop ("more connections → richer dashboard → team invites → wider org
  adoption").

After the PRFAQ is committed, fill the Digital Experience Contract's Strategy
section from it:

**What to type:**

```
fill the Strategy section of the Digital Experience Contract for the Velodata onboarding redesign
```

The `write-prfaq` skill (or any product-strategy skill reading the PRFAQ) fills
the contract. The fields it writes:

- **Target User and Context:** data analyst, newly onboarded, empty workspace
- **Adoption Hypothesis:** first-success event = user sees a chart with own
  data within three minutes of first login
- **Value Loop:** connections → richer dashboard → sharing → org adoption
- **Assumptions and Kill Criteria:** bet is falsified if median time-to-first-
  chart stays above five minutes after the redesign, or if chart-share rate
  does not increase within thirty days

**What you get:**

```
docs/product/digital-experience-contract.md  (Strategy section filled)
```

---

> **Handoff 2: product-strategy → experience-design**
>
> The Digital Experience Contract's Strategy section is the direct input to
> `journey-mapping`. Specifically:
>
> - **Target User and Context** → the persona the journey is mapped from
> - **Adoption Hypothesis / first-success event** → the "done" state the
>   journey must reach ("user sees a chart with own data")
> - **Value Loop** → the repeat behaviors the journey should enable after
>   first success
>
> The `journey-mapping` skill reads the contract directly. If the Strategy
> section is absent, it labels its output
> `[provisional — product-strategy not installed]` and infers what it can
> from your prompt.

---

## Part 3: Experience design

### Step 5 — Map the customer journey

**What to type:**

```
map the customer journey for onboarding a new Velodata Analytics user — surface: responsive web, starting from email confirmation, ending at first chart shared with a teammate
```

**Skill that fires:** `journey-mapping`

The skill divides the journey into named stages and, for each, captures actions,
emotions, pains, and opportunities — outside-in, in the customer's words. It
reads the Digital Experience Contract's Strategy section to anchor the
first-success event.

**What you get:**

A journey map with stages:

| Stage | Actions | Pains | Opportunities |
|-------|---------|-------|---------------|
| Arrive | Land on empty workspace | "Where do I start?" | Surface a sample chart immediately |
| Connect | Enter source URL, copy token | Four-step flow, token confusion | Reduce to two steps; auto-detect source type |
| First look | Wait for data sync | Spinner with no progress | Progressive loading; preview on partial data |
| First chart | Configure chart type, pick dimensions | Too many options | Smart defaults from data shape |
| Share | Find team invite | Buried in settings | Inline share prompt after chart creation |

**What the journey map hands forward:** the pains-to-opportunities column. Every
downstream skill points back to it. A screen that solves no pain from this
column is off-brief.

---

### Step 6 — Derive the screen flow and per-screen briefs

**What to type:**

```
turn that journey into a screen flow — sequence the screens, route the error cases, and give me a brief per screen
```

**Skill that fires:** `user-flow`

The skill sequences the screens the journey implies, draws the transitions and
error/edge flows, records which quality-floor states each screen must handle,
and emits one self-contained brief per screen. Each action names its backing
service; each screen names its journey stage.

**What you get:**

A screen inventory with per-screen briefs:

| Screen | Journey stage | IA archetype | Primary action |
|--------|--------------|--------------|----------------|
| Welcome + sample chart | Arrive | Marketing landing | "Connect your data" |
| Connect data source | Connect | Transactional flow | Submit source URL |
| Sync progress | First look | Transactional flow | (wait) |
| First chart builder | First chart | Product workspace | Configure and save chart |
| Share prompt | Share | Transactional flow | Invite teammate |

The `user-flow` brief names the **IA archetype** for each screen (from the
`page-archetypes` reference). The archetype governs layout priorities: a
transactional flow screen demands a single primary action above the fold with no
competing navigation; a product workspace screen permits a persistent side nav
with tool panels.

The skill finishes by walking the whole journey as a steel thread: every
transition resolves, every action has a backing service.

---

> **Handoff 4 (first half): screen brief with IA archetype → copy-direction**
>
> The per-screen brief is the input to `copy-direction`. Specifically:
>
> - The **IA archetype** tells `copy-direction` what hierarchy the screen
>   demands (a transactional flow screen needs a single, directive headline).
> - The **primary action** names what copy must make unmistakably clear.
> - The **pains** column from the journey anchors copy tone — the "token
>   confusion" pain signals to write the copy-paste instruction in the user's
>   terms, not the API's.

---

### Step 7 — Derive the token taxonomy

**What to type:**

```
name the aesthetic direction for Velodata Analytics — data-forward, precise, trustworthy; responsive web; persona: data analyst
```

**Skill that fires:** `creative-direction`

The skill names emotional and brand goals grounded in the persona and platform.
It does not produce values — it names the direction (for example: "Calibrated
precision — the UI recedes so the data stands forward; no decorative elements
compete with chart ink; trust signals are structural, not ornamental").

Then:

**What to type:**

```
derive a token taxonomy from those aesthetic goals
```

**Skill that fires:** `design-token-taxonomy`

The skill names the tokens by semantic role and chooses a single ratio as the
organizing concept — minor-third, golden ratio, or a custom scale. It produces
the token architecture: what tokens exist, what roles they serve, and what scale
they inhabit. It does not produce values.

**What you get:**

```
Token taxonomy for Velodata Analytics:
  Color roles: primary, surface, on-surface, data-positive, data-negative,
               data-neutral, error, warning, success, disabled, overlay
  Scale: 4px base unit, minor-third typographic scale (1.2)
  Spacing: 8-step linear progression (4px to 64px)
  Radius: none (data tables), sm (2px, badges), md (4px, cards), full (chips)
  Typography: heading family (geometric sans), body family (system stack),
              mono family (chart labels, code)
```

---

> **Handoff 3: design-token-taxonomy → design-system-foundations**
>
> The taxonomy is the contract `design-system-foundations` reads. It does not
> accept free-form direction — it reads the taxonomy's named roles and chosen
> scale. Without a taxonomy, `design-system-foundations` must either elicit the
> taxonomy inline (slower, less coherent) or label its output provisional.

---

### Step 8 — Apply the design system foundations

**What to type:**

```
apply the Velodata token taxonomy as a working design system foundation — lightweight mode
```

**Skill that fires:** `design-system-foundations`

Lightweight mode is appropriate here: the team needs to unblock component work
before committing to a full DTCG-compatible token pipeline. If the project needs
multi-theme switching or a generated token source later, re-run in full mode.

**What you get:**

A working foundation naming semantic token assignments, typography, spacing,
core component tokens, and the focus style meeting WCAG 2.4.11:

```
--ds-color-primary         → [value from taxonomy / team maps]
--ds-color-surface         → [value from taxonomy]
--ds-color-data-positive   → [chart uptrend]
--ds-color-data-negative   → [chart downtrend]
--ds-text-sm through --ds-text-2xl  (minor-third scale)
--ds-space-1 through --ds-space-8   (4px to 64px)
--ds-btn-*                 (button component tokens)
--ds-input-*               (input component tokens)
```

The foundation is framework-agnostic: the team maps these names to CSS custom
properties, a design tool variable set, or a platform token pipeline. The skill
ships the architecture, not the tooling.

---

### Step 9 — Set the copy voice and direction

**What to type:**

```
set copy direction for the Velodata onboarding screens — use the per-screen briefs from the screen flow; persona is a data analyst, surface is responsive web
```

**Skill that fires:** `copy-direction`

The skill reads the per-screen briefs (which name the IA archetype and the
primary action for each screen) and sets the copy voice governing the onboarding
flow. It does not write final copy; it sets the voice, tone constraints, and
per-screen copy priority.

**What you get:**

```
Copy direction for Velodata onboarding:
  Voice: Direct, minimal, precise — every word earns its place.
  Tone: Encouraging without cheerleading; technical without jargon.

  Transactional flow screens (Connect, Sync, Share):
    - Primary headline: action-first ("Connect your data source")
    - No secondary marketing copy above the fold
    - Error states: name the cause, not the symptom
      ("Token not found — paste the full token from your Velodata API
      settings page")

  Welcome screen:
    - Headline: outcome-first ("Your data, in seconds")
    - Sub-copy: "Connect a source below or explore with sample data"
```

---

> **Handoff 4 (complete): IA archetype → copy-direction → design-review**
>
> The copy direction output joins the screen briefs as input to the two
> remaining design skills:
>
> - `conversion-design` reads the brief (IA archetype + primary action) and
>   the copy direction (voice constraints) when it structures each screen's
>   hierarchy.
> - `design-review` checks that the final hierarchy and copy are consistent:
>   a transactional flow screen has a single primary action above the fold,
>   the copy voice matches the direction, and all 18 quality-floor states
>   are handled.

---

### Step 10 — Design the onboarding screens

**What to type:**

```
design the onboarding flow screens for Velodata Analytics — treat this as a conversion surface; use the screen briefs and copy direction
```

**Skill that fires:** `conversion-design`

`conversion-design` is the appropriate genre skill for an onboarding flow: the
user's goal is activation and the design's goal is to make that first success
easy and obvious. It applies a conversion hierarchy (single path, minimal
friction, progress reinforcement) to each screen's brief.

Work through each screen in the inventory:

**Welcome + sample chart.** Structure this screen with a visible sample chart
above the fold (the research showed most users don't scroll past the empty
state) and a primary CTA: "Connect your data source." The secondary option
("Explore sample data") appears below the fold so it does not dilute the
primary path.

**Connect data source.** Collapse the four-step flow to two: (1) paste the
source URL, (2) paste the token — with an inline link to where the token lives,
not a separate setup guide. Progress reinforcement: a step indicator at the top
of the screen shows "Step 1 of 2."

**Sync progress.** Design around progressive loading: a partial chart renders
as data streams in, reducing the blank-screen wait. The user sees their data
shape before sync completes, which reduces abandonment at this stage.

**First chart builder.** Smart defaults derived from the data shape (bar chart
for categorical dimensions, line chart for time series) appear pre-selected.
"Save chart" is the primary CTA, always above the fold.

**Share prompt.** Triggered immediately after the chart saves. A modal with a
text field for the teammate's email and a single "Send invite" action. No
navigation to settings required.

**What you get:** Screen structures — hierarchy, primary action placement, state
handling for all critical states — for each screen in the onboarding flow.

---

### Step 11 — Run the three-pass design review

**What to type:**

```
run a design review on the Velodata onboarding screens
```

**Skill that fires:** `design-review`

The skill runs three passes in sequence, not one combined check:

**Pass 1 — cold read.** The skill reads the screen set as a first-time user
would encounter it, with only the persona and job in context. It checks: Is the
primary action obvious? Does the hierarchy match the IA archetype? Is the copy
voice consistent with the direction?

**Pass 2 — primary task + one unhappy path.** The skill walks the activation
path (connect source → sync → first chart → share) and then one failure path
(token not found). It checks: Does every error state name the cause and the
recovery? Is the "token not found" error copy specific to the field, or generic?
Does the sync progress screen handle a partial failure (one of three tables
failed to sync)?

**Pass 3 — full quality-floor contract.** The skill checks all 18 required
states across every screen. For the onboarding flow, states most likely to be
missing: `empty` (the Welcome screen if no sample data loads), `error` (the
Connect screen if the URL is malformed), `offline` (the Sync screen if the
connection drops mid-sync), `loading-progressive` (the Sync screen itself),
`destructive-confirmation` (not applicable here — note it as
handled-not-applicable in the review).

**What you get:**

A findings report grouped by severity (Blocker / Concern / Suggestion), with
each finding mapped to the screen, the state or heuristic violated, and a
one-sentence fix. Expected findings for this flow:

- **Blocker:** `offline` state not handled on the Sync progress screen — user
  sees a frozen progress bar with no recovery action.
- **Concern:** "Token not found" error copy is generic — it should name the
  specific token field and link to the API settings page.
- **Suggestion:** the sample chart on the Welcome screen has no caption —
  adding the data source name sets user expectations before they connect.

Address Blockers before moving to the independent review.

---

### Step 12 — Get the independent review

**What to type:**

```
have the experience-reviewer review the Velodata onboarding screen set — provide the journey map, per-screen briefs, and the design-review findings
```

**Agent that fires:** `experience-reviewer`

The `experience-reviewer` is a forked-context reviewer — it has not seen the
authoring chain. It reviews the screen set against:

1. **Grounded aesthetic fit:** does the visual hierarchy match the "calibrated
   precision" direction? Do any decorative elements compete with the data?
2. **Platform fit (responsive web):** does each screen degrade gracefully at
   320px? Is the token paste input large enough for thumb input on mobile?
3. **Cross-brief coherence:** does the copy voice hold across all five screens,
   or does the Welcome screen shift to a warmer register that the transactional
   screens don't match?
4. **Quality floor:** are all 18 states handled? (It checks independently — it
   does not trust the design-review pass.)
5. **Marketing clarity (above-fold conversion copy on the Welcome screen):**
   tweet test (can the value proposition fit in one sentence?), five-second scan
   (what does a user see first?), painkiller-first (does the headline name the
   pain before the solution?).

**What you get:** A verdict (SHIP IT / SHIP WITH CHANGES / MAJOR REWRITE) with
severity-tagged findings. The `experience-reviewer` marks no homework of its
own: it never saw the design session, so its findings are an independent signal
about what the screen set actually communicates.

Expected verdict: **SHIP WITH CHANGES** — the offline state gap from the
design-review surfaces again (a Blocker), and the five-second scan test on the
welcome screen may surface that "Your data, in seconds" is abstract enough to
need a sub-head that names the supported data source types.

Address the Blockers. Commit the reviewed screen set.

---

## What you built

After Step 12 you have a committed chain of artifacts:

| Artifact | Lives in | Fed by | Feeds |
|----------|----------|--------|-------|
| Research brief | `.context/` (scratch) | `desk-research-project-synthesize` | SWOT, PRFAQ |
| SWOT analysis | `docs/product/shaping/swot-analysis.md` | `run-swot` | Strategy context |
| PRFAQ | `docs/product/shaping/prfaq-onboarding-redesign.md` | `write-prfaq` | Digital Experience Contract |
| Digital Experience Contract | `docs/product/digital-experience-contract.md` | product-strategy skills | `journey-mapping` |
| Journey map | In session (or committed artifact) | `journey-mapping` | `user-flow` |
| Screen flow + briefs | In session (or committed artifact) | `user-flow` | `copy-direction`, `conversion-design` |
| Token taxonomy | In session | `design-token-taxonomy` | `design-system-foundations` |
| Design system foundation | In session | `design-system-foundations` | Component build |
| Copy direction | In session | `copy-direction` | `conversion-design`, `design-review` |
| Screen structures | In session | `conversion-design` | `design-review` |
| Design review findings | In session | `design-review` | Remediation + `experience-reviewer` |
| Independent review | In session | `experience-reviewer` | Final sign-off |

The committed artifacts (SWOT, PRFAQ, Digital Experience Contract) travel to the
build packs. The in-session artifacts (screen structures, foundations, review
findings) are the design-intent signal the `frontend-engineering` skill reads
when it opens the build.

---

## The four handoffs in review

**Handoff 1 — research → strategy.** The `desk-research-project-synthesize`
brief names the friction findings. `run-swot` reads it to populate the
Weaknesses quadrant; `write-prfaq` reads it to populate the customer problem
statement. You do not reformat the brief — the skills extract what they need
from narrative input.

**Handoff 2 — strategy → experience-design.** The Digital Experience Contract's
Strategy section anchors `journey-mapping`. The first-success event ("user sees
a chart with own data in under three minutes") is the "done" state the journey
must reach. Without this anchor, the journey map is a generic user-flow that any
analytics product could claim.

**Handoff 3 — token taxonomy → design system foundation.** The
`design-token-taxonomy` output is the contract `design-system-foundations` reads.
Token names, scale ratios, color role names — all must be consistent between the
two steps. If you change a color role name in the taxonomy after applying the
foundation, you break the alias chain.

**Handoff 4 — screen brief → copy-direction → design-review.** The IA archetype
in each screen brief tells `copy-direction` what the screen's hierarchy demands.
The copy direction output tells `design-review` what to check. A transactional
flow screen with a conversational sub-head is a `design-review` Blocker because
the copy voice contradicts the archetype's hierarchy requirement.

---

## Where to go next

- Ran the chain and want to run it on a different surface? The same twelve
  steps apply — swap in your surface, persona, and first-success event at
  Steps 1, 5, and 10.
- Want to understand why the four packs are structured this way? Read
  [The Digital Experience Contract](../../core/explanation/digital-experience-contract.md) —
  the contract is the connective artifact that makes the handoffs explicit.
- Ready to build? The `frontend-engineering` skill reads the screen briefs,
  design system foundation, and the 18-state quality floor directly. Open it
  with the committed design artifacts in context.
- Want to run the deterministic cross-pack checker on your artifacts?
  [How to run the cross-pack experience eval](../how-to/run-cross-pack-eval.md).
