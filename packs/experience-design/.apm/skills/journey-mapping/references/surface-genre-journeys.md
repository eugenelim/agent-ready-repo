# Surface-genre journey stage scaffolds

Canonical stage vocabularies for each of the 7 surface genres. Use these as the starting scaffold when a journey map's genre is known. Stages are coarse phases — 3–6 per journey — representing the customer's goal progression, not screens or steps. Adjust stage names to fit the specific product and customer; these are anchors, not mandates.

---

## Marketing genre

Customers arrive without commitment; the journey ends at a conversion decision.

| Stage | Customer goal |
|-------|--------------|
| **Aware** | Discovers that a product exists; forms an initial impression |
| **Interested** | Investigates further; compares against alternatives |
| **Evaluating** | Assesses fit for their specific need; weighs risk |
| **Intending** | Has decided in principle; looking for final confidence |
| **Converting** | Takes the commitment action (signup, purchase, trial start) |
| **Advocating** | Shares the experience; drives referral or social proof |

**Design priority:** negative peaks cluster at the Evaluating stage (trust gaps, unclear pricing, unaddressed objections). The most-positive peak is typically at Conversion or the first moment of product value. `conversion-design` owns the surface design for this journey.

---

## Documentation genre

Customers arrive with a task or a concept to understand; success is defined by task completion or understanding achieved.

| Stage | Customer goal |
|-------|--------------|
| **Discovering** | Finds the right documentation entry point from search, referral, or in-product link |
| **Orienting** | Understands what type of content is present and where to go |
| **First value (TTFV)** | Completes the first successful task or grasps the key concept |
| **Recurring reference** | Returns to look up specific details, parameters, or edge cases |
| **Mastery** | Navigates with confidence; rarely needs the entry-level content |

**Design priority:** negative peaks cluster at Discovering (wrong entry point, outdated content, broken search) and First value (tutorial fails mid-way, prerequisite unstated). `documentation-design` owns the surface design for this journey.

---

## Informational genre

Customers arrive to understand a topic; success is knowledge gained or perspective shifted.

| Stage | Customer goal |
|-------|--------------|
| **Discovering** | Finds the piece via search, social, or newsletter |
| **Committing** | Reads the headline and deck; decides whether to invest time |
| **Reading** | Moves through the body; absorbs the argument or information |
| **Integrating** | Connects what they read to their existing knowledge or situation |
| **Acting or sharing** | Takes a next step (action, share, deeper reading) |

**Design priority:** negative peaks cluster at Committing (unclear value proposition in headline/deck) and Integrating (no "what's next" path after the content ends). `informational-design` owns the surface design for this journey.

---

## Analytical genre

Customers arrive to answer a business question and take action; success is a decision made or an action initiated.

| Stage | Customer goal |
|-------|--------------|
| **Arriving** | Opens the surface; re-establishes context from the last session |
| **Signal-checking** | Scans Tier 1 KPIs for anything requiring attention |
| **Diagnosing** | Drills into a signal to understand the cause |
| **Deciding** | Forms a conclusion from the diagnostic evidence |
| **Acting** | Takes an action (assigns, escalates, exports, adjusts) |
| **Verifying** | Confirms the action had the intended effect |

**Design priority:** negative peaks cluster at Diagnosing (can't find the cause from the signal) and Acting (action affordance not visible from the diagnostic). `analytical-design` owns the surface design for this journey.

---

## Transactional-journey genre

Customers arrive with intent to complete a specific transaction; success is a confirmed, recoverable commitment.

| Stage | Customer goal |
|-------|--------------|
| **Initiating** | Starts the transaction (selects item, begins checkout, starts a form) |
| **Configuring** | Fills in required details and makes choices |
| **Reviewing** | Checks what they are about to commit to before confirming |
| **Confirming** | Submits the transaction |
| **Receiving confirmation** | Gets evidence that the transaction was accepted |
| **Post-transaction** | Follows up (tracks delivery, manages the result, seeks support) |

**Design priority:** negative peaks cluster at Configuring (unexpected required fields, confusing options) and Receiving confirmation (ambiguous success state — did it work?). `interaction-design` wizard-and-stepper pattern owns the surface design for this journey.

---

## Marketplace genre

Customers arrive to find and select from a set of offerings; success is a confident match between buyer need and listing.

| Stage | Customer goal |
|-------|--------------|
| **Exploring** | Enters the catalogue without a specific target; forms a sense of what's available |
| **Searching or filtering** | Narrows the consideration set to likely matches |
| **Evaluating listings** | Compares candidates against their need; reads detail pages |
| **Comparing** | Places two or more candidates in direct comparison |
| **Committing** | Selects a listing and initiates the transaction |
| **Post-purchase** | Uses, reviews, or manages the purchased item |

**Design priority:** negative peaks cluster at Evaluating listings (not enough qualification information on the card, or too much cognitive load in the detail page) and the transition to Committing (transaction flow loses marketplace context). `marketplace-design` owns the surface design for this journey.

---

## Workspace genre

Customers arrive to do complex, sustained professional work; success is meaningful progress on a task that spans sessions.

| Stage | Customer goal |
|-------|--------------|
| **Arriving** | Returns to the workspace; re-establishes context from last session |
| **Orienting** | Understands what has changed, what requires attention, and where to start |
| **Working** | Focuses on the primary task without interruption |
| **Persisting** | Saves progress and exits gracefully; confirms work is safe |
| **Collaborating** | Shares, hands off, or reviews with another person |

**Design priority:** negative peaks cluster at Arriving (context loss — "where was I?") and Persisting (uncertainty about whether work was saved). `workspace-design` owns the surface design for this journey.
