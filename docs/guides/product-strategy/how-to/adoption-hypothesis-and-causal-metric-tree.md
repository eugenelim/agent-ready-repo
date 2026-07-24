# Author an adoption hypothesis and causal metric tree

**Use this when:** you have a product concept or OKR structure and need to name what behavior constitutes adoption and what metrics causally predict the outcome you are targeting.
**Prerequisites:** `product-strategy` pack installed; a product concept, PRFAQ draft, or OKR cascade in progress.
**Result:** a named first-success event, a repeat-value behavior, a north-star metric, and 2–4 leading indicators with explicit causal connections — ready to populate the Digital Experience Contract's Strategy section and the PE pack's first-success operationalization field.

This guide covers how to derive both from your existing strategy artifacts. The adoption hypothesis names what a user does to count as adopted (first-success event) and why they return (repeat-value behavior). The causal metric tree names the north-star metric and the 2–4 leading indicators that causally predict it, each connected to an OKR gap.

---

## Step 1: Name the first-success event from the PRFAQ solution

Start from the PRFAQ's solution description. Ask:

> "What is the first thing a user does that proves they received the value this solution describes?"

The first-success event must pass three tests:

- **Behavioral**: it is an action, not an attitude. "User feels confident" fails; "user completes their first contract review in under 5 minutes" passes.
- **Observable**: you can detect it without asking the user. If you need a survey to confirm it happened, it is not a first-success event — it is a satisfaction outcome.
- **Specific**: it names a time, a completion threshold, or a concrete output. "User uses the product" fails; "user publishes their first report with at least three data sources" passes.

If you cannot name a first-success event that passes all three tests, the PRFAQ's solution description is too vague. Return to write-prfaq and sharpen the solution before continuing.

---

## Step 2: Name the repeat-value behavior from the value loop

Ask:

> "What does the user need to do — and need to have — after first success that they did not have before?"

The repeat-value behavior names the mechanism that compounds value: what accumulates, what the user learns to do, what network grows, what workflow deepens. Common mechanisms:

- **Data accumulation**: the product gets smarter with each use (personalization, history, benchmarks)
- **Skill development**: the user becomes faster or more capable with practice
- **Network effect**: the value increases as more of the user's collaborators or contacts use the product
- **Workflow depth**: the user unlocks more sophisticated capabilities as they progress through a learning curve

Name the mechanism specifically. "Users come back because the product is useful" is not a value loop — it is a tautology.

---

## Step 3: Derive the north-star metric from the first-success event

The north-star metric is the measurable expression of the first-success event at scale. It answers:

> "If our adoption hypothesis is correct, what aggregate user-behavioral metric moves when users are successfully adopting?"

Derive it from the first-success event by asking:

- What is the count, rate, or depth of the first-success behavior at scale?
- Does this metric rise when adoption is happening and stay flat when adoption is not?
- Is it under the team's influence (not just market conditions)?

The north-star must be **user-behavioral and outcome-oriented**. Common anti-patterns:

| Looks like north-star | Why it fails |
|---|---|
| Monthly recurring revenue | Output metric — measures team success, not user success |
| Features shipped | Output metric — does not measure value delivery |
| Registered users | Measures acquisition, not adoption |
| NPS | Lagging and attitudinal — too slow to drive weekly decisions |
| Daily active users (unqualified) | Activity without value definition — a "user who logged in" is not an "adopter" |

A good north-star for the contract review example: "contracts reviewed to completion per legal team per month" — user-behavioral, outcome-oriented, and sensitive to adoption.

---

## Step 4: Derive leading indicators from the causal chain

For each OKR gap or Key Result in your cascade, ask:

> "What behavior, earlier in the user journey, causally predicts whether the user will reach the first-success event?"

A leading indicator is valid if:

- It moves before the north-star moves (it is upstream in the causal chain)
- It connects to a specific OKR gap — it is not floating
- Its causal connection to the north-star can be named (not just "we think these are related")

Aim for 2–4 leading indicators. More than four creates a dashboard, not a tree.

---

## Worked example: contract review tool

**Product**: AI-powered contract review tool for in-house legal teams.
**PRFAQ solution**: legal teams complete low-complexity contract reviews in under 5 minutes, freeing senior counsel time for complex work.

### First-success event

> User completes their first contract review using the AI assist and approves it for signature without manual re-review.

**Why**: behavioral (action taken), observable (detected in activity log), specific (first AI-assisted review approved without rework).

### Repeat-value behavior

> User initiates contract review directly in the tool rather than downloading to Word first — the workflow has become the user's default.

**Mechanism**: workflow depth. The user's first review requires learning the tool; each subsequent review requires less context-switching. The adoption threshold is the moment the tool becomes the default, not a fallback.

### North-star metric

> **Contracts reviewed to AI-approved completion per legal team per month**

Rises when teams adopt the workflow; stays flat when they revert to manual review. Measurable in the product's activity log. Under the team's influence (feature improvements that reduce friction drive it up).

### Causal metric tree

| Metric | Level | Causal connection | OKR link |
|---|---|---|---|
| Contracts reviewed to AI-approved completion per team per month | North-star | — | Company KR: close 5 enterprise contracts |
| % of first reviews completed without manual re-download to Word | Leading indicator | Predicts north-star: if users don't revert to Word, adoption is holding | OKR gap: workflow-default |
| Time from contract upload to AI review completion (median) | Leading indicator | Predicts north-star: if median time drops below 5 min, the speed benefit is real | OKR gap: review-speed |
| % of users who complete a second review within 7 days of first review | Leading indicator | Predicts north-star: second review is the repeat-value signal | OKR gap: retention-at-day-7 |

---

## Connecting to the Digital Experience Contract

The adoption hypothesis and causal metric tree map directly to the Digital Experience Contract's `## Strategy` section:

| Adoption doctrine artifact | Contract field |
|---|---|
| First-success event | `### Adoption Hypothesis` → First-success event |
| Repeat-value behavior | `### Adoption Hypothesis` → Repeat-value behavior |
| Value loop mechanism | `### Value Loop` |
| North-star + leading indicators + causal connections | `### Metric Tree` |

Populate these fields in the contract after `write-prfaq` and `run-okr-cascade` complete. The PE pack's `first-success operationalization` field reads from the contract's Adoption Hypothesis; the XD pack's `primary journey` reads from the Value Loop.

---

## Common mistakes

- **Naming "launch" or "onboarding completion" as first-success.** These are delivery milestones for the team, not adoption events for the user. The first-success event is something the *user* does that proves they received value.
- **Treating the north-star as a revenue metric.** Revenue is a consequence of adoption, not a measure of it. The north-star measures user behavior that causes revenue — not revenue itself.
- **Listing metrics without causal connections.** A list of five metrics without named causal connections is a dashboard. The tree requires naming why each leading indicator predicts the north-star — the mechanism, not just the correlation.
- **Skipping the repeat-value behavior.** A first-success event without a repeat-value behavior is an acquisition metric with extra steps. The value loop is what makes first success the start of adoption, not the end of a trial.
