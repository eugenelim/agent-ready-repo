# Surface routing

The two sub-paths differ in what the reader needs to accomplish and what success looks like. Choosing the wrong sub-path produces a brief that answers the wrong questions.

## The two sub-paths

**Acquisition surface** — the reader is evaluating whether to act. The surface must move them from their current awareness level to a decision. The primary content job is persuasion in the correct sequence: the reader's problem before the product's features, the guide's credentials before the ask, the plan before the stakes.

**Product/reference surface** — the reader is a current user trying to accomplish something. The surface must help them complete a task or find information. The primary content job is utility: the right information in the right format, prioritised so the most-needed content is always easiest to reach.

## Acquisition elicitation questions

Run these in order; each answer shapes the next question.

0. **Audience action goal:** What is the primary outcome the reader must carry away? On acquisition surfaces, **awareness level drives arc selection** (see step 3 and `references/narrative-arc.md`); the action goal shapes which evidence type and emphasis the selected arc must carry, not the arc choice itself. Name the action goal before writing section assignments — it prevents the common failure mode of selecting the right arc for the wrong emphasis.
   - *Decision* — the reader needs to evaluate options and commit (approve, purchase, select a plan). Distinguish from Execution: Decision carries evaluation stakes and commitment weight. Evidence emphasis: credible social proof, comparison support, and a clear what-happens-next at the conversion point.
   - *Understanding* — the reader needs a concept established before they can act. Evidence emphasis: the surface must earn context before the ask; prioritise explanation and meaning over social proof; the CTA should follow comprehension, not lead it.
   - *Execution* — the reader needs to perform a specific action right now (start a trial, click a button, complete a form step). Distinguish from Decision: Execution assumes the commitment is already made; the job is to make the next step obvious and the path frictionless. Evidence emphasis: the CTA is the single most prominent element; concrete, low-risk next-step language outweighs social proof at this moment.
   - *Belief shift* — the reader holds an incumbent belief that must be displaced before the offer lands. Evidence emphasis: the surface must name and directly address the existing belief before introducing the alternative; contrast and stakes language carry the weight.
   Name the action goal before writing section assignments. On acquisition, awareness level remains the authoritative arc selector (step 3); if the action goal's evidence emphasis and the arc's structure seem mismatched, the arc is correct and the section copy should adjust, not the arc.

1. **Business objective:** What is the single action this surface must drive? (sign up, start trial, request demo, download, contact) Name the action verb and the conversion point.

2. **Primary reader:** Who arrives at this surface? Name their role and the context that brought them here — a search result, a referral, a product-led prompt, an ad click. Context shapes awareness level.

3. **Audience awareness level (Schwartz five-stage ladder):**
   - *Unaware* — does not yet know they have the problem
   - *Problem-Aware* — recognises the problem but not the category of solution
   - *Solution-Aware* — knows solutions exist but hasn't evaluated this product
   - *Product-Aware* — knows this product but hasn't committed
   - *Most Aware* — ready to act; needs only the right offer and the next step
   The awareness level drives narrative arc selection (see `references/narrative-arc.md`).

4. **Scroll section assignment:** List the sections planned for this surface. Assign each section one job from: *problem* (name the tension the reader recognises), *guide proof* (establish why this product/team can solve it), *plan* (make the path to value concrete and low-risk), *stakes* (name what happens if nothing changes), *CTA* (the moment of decision). A section with two jobs is doing neither precisely.

5. **Above-fold structure:** What does the headline answer? It must cover what this product does, for whom, and why now — the reader should know whether this is for them within the first sentence. What does the subheadline add that the headline cannot carry? Subheadlines that restate the headline are wasted space.

6. **CTAs:** Name the primary CTA (the main conversion action) and the transitional CTA (the lower-commitment action for readers not yet ready to convert). Both need a label (the exact words on the button or link) and a next state (what happens immediately after clicking).

7. **Success metric:** How does the team know this surface is working? Name one rate — sign-up rate, trial start rate, demo request rate — as the primary signal. Naming more than one makes the brief harder to optimise against.

## Product/reference elicitation questions

0. **Reader action goal:** What is the primary outcome the reader needs from this surface?
   - *Decision* — they need to evaluate options and commit (choose a configuration, select an integration path, approve an approach).
   - *Understanding* — they need a concept explained before they can act (what a term means in context, why the system works a particular way).
   - *Execution* — they need to complete a specific task right now (run a command, fill a form, follow a sequence of steps).
   - *Belief shift* — they hold a prior assumption that conflicts with correct usage and need it corrected before the task will succeed.
   Name the action goal. If the goal is Decision or Understanding, also elicit prior knowledge level (step 0b below) — the Pyramid Principle applies only at high prior knowledge.

0b. **Prior knowledge level** (elicit only when action goal is Decision or Understanding): Does the reader arrive already knowing why the topic matters and what the key terms mean (high prior knowledge), or do they need context and framing before the conclusion makes sense (low prior knowledge)? If high: the Pyramid Principle (conclusion-first, top-down) is the right structure. If low: default to context-before-answer structure.

1. **User task:** What is the user trying to accomplish? State it as a verb phrase: "integrate the API with their existing auth system," "find the keyboard shortcut for X," "troubleshoot the Y error." A task stated as a noun phrase ("API integration") is not yet a task.

2. **Completion definition:** What does "done" look like for the user on this surface? Can they tell without leaving the page that they have what they came for? If not, the surface has a completion problem, not a content problem.

3. **Content format selection:** Match the format to the task type:
   - *Prose* — for conceptual explanation: why something works the way it does, what a term means in context
   - *Numbered steps* — for procedural tasks: do A, then B, then C; order matters; each step has a visible outcome
   - *Table* — for comparison or reference: comparing options, listing properties, referencing values by name
   - *Diagram* — for relationships or flows: how components connect, how data moves, what sequence looks like visually

   Mixed formats are fine when the task has mixed sub-tasks — a concept introduction (prose) followed by a setup procedure (steps) followed by a reference table is a legitimate structure. Name the format per sub-task, not per page.

4. **Content hierarchy:** Using the Nava PBC must-say → probably-say → might-say model, list the content items for this surface and assign each to a tier (see `references/content-hierarchy.md`). Must-say items belong above the fold and in the main content path. Probably-say items belong in the body, reachable within one scroll or one section. Might-say items belong in expandable sections, footnotes, or a linked reference page.

5. **Completion metric:** How does the team know a user successfully completed their task on this surface? Task completion rate (tracked via explicit feedback or session behaviour) or search resolution rate (the user did not immediately run another search after reading) are the two primary signals for product/reference content.
