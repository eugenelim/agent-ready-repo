---
name: content-design
description: "Use when a designer or product person needs to decide what a surface should say, for whom, in what form, and to what objective — before any wireframe or screen flow is opened. Routes across two surface types: acquisition surfaces (marketing pages, landing pages, web onboarding flows) and product/reference surfaces (help pages, feature reference, in-product wayfinding). Triggers on \"what should this landing page say\", \"write a content brief for our onboarding flow\", \"what's the narrative arc for this marketing page\", \"what does this feature page need to communicate\", \"help me decide the above-fold structure\". Do NOT use to write final copy (use `tone-of-voice` for copy voice, then `voice-and-microcopy` for UI strings), to produce an analytics or CRO measurement framework, or to generate SEO keyword plans."
---

# Skill: content-design

Produces a **content brief** — a text-first document answering "what does this surface need to say, for whom, in what form, to achieve what objective" — before any wireframe or screen flow is started. The brief is the durable artifact: it lets every later design and copy choice point back to a content decision, not a fresh opinion. This skill fills the first link in the design thread between `journey-mapping` and `user-flow`: it runs after a journey exists (or elicits one inline) and before screens are sequenced.

## When to invoke

Confirm all four before drafting; if any fails, push back and resolve it first.

1. **There is a real surface with a defined purpose** — a specific page, flow, or section with a business objective. A vague "we need content" is not yet a brief; identify the surface and its goal before proceeding.
2. **No content brief already exists for this surface** — if one exists, you are amending it, not starting fresh.
3. **You are deciding direction, not writing final copy** — the moment the ask is "write the headline," this skill has done its job and hands off to `tone-of-voice` for voice and `voice-and-microcopy` for UI strings.
4. **You know or can elicit the target audience** — either `journey-mapping` output is available, or you can elicit persona and outcome inline before routing to a sub-path.

## Procedure

1. **Confirm the surface type.** Ask: is this an **acquisition surface** (marketing page, landing page, web onboarding flow — the goal is to move a visitor from awareness or evaluation to action) or a **product/reference surface** (help page, feature reference, in-product wayfinding — the goal is to help a current user complete a task or find information)? Documentation surfaces route as product/reference. Name the confirmed type before proceeding; it determines the sub-path and the elicitation questions. Load `references/surface-routing.md`.

2. **Elicit or confirm persona and outcome.** If `journey-mapping` output is available, consume it — the journey's audience definition, awareness level, and key moments are direct inputs. If not, elicit inline:
   - Who is the primary reader? (role, context, what brought them here)
   - What is the one outcome they need to carry away from this surface?
   - For acquisition surfaces: what is their awareness level? (Have they never heard of the product, are they evaluating actively, or do they already know they want it?)
   Record the answers; they feed the sub-path elicitation and anchor every section job.

3. **Route to the sub-path and run elicitation.** Run the elicitation sequence for the confirmed surface type:

   **Acquisition sub-path:** Load `references/surface-routing.md` (acquisition questions) and `references/narrative-arc.md`. Elicit:
   - Audience action goal — what is the primary outcome the reader must carry away? (Decision / Understanding / Execution / Belief shift). The action goal shapes the evidence type and emphasis; awareness level drives arc selection. See `references/surface-routing.md` step 0 for the full four-goal definitions.
   - Business objective — what is the one action this surface needs to drive?
   - Primary reader awareness level using the Schwartz five-stage awareness ladder (Unaware → Problem-Aware → Solution-Aware → Product-Aware → Most Aware). Awareness level is the primary arc selection driver.
   - Narrative arc: StoryBrand (seven-element arc) is the right choice for cold and warm audiences (awareness levels 1–3); Conversion-Centered Design (seven principles) is the right choice for bottom-of-funnel audiences (levels 4–5). State the applicability rationale before selecting.
   - Scroll section assignment — each scroll section gets one job: problem, guide proof, plan, stakes, or CTA.
   - Above-fold structure — what is the headline contract (what/who/why in the first sentence), and what does the subheadline add?
   - Primary CTA and transitional CTA — what action, what label, what happens next?
   - Success metric — how do we know this surface worked?

   **Product/reference sub-path:** Load `references/surface-routing.md` (product questions), `references/content-hierarchy.md`, and `references/narrative-arc.md` (for the Pyramid Principle, applicable when the reader's action goal is Decision or Understanding at high prior knowledge). Elicit:
   - Reader action goal — is the reader arriving to make a Decision, gain Understanding, complete an Execution task, or shift a Belief? This determines whether the Pyramid Principle applies.
   - Prior knowledge level — does the reader arrive already knowing why the topic matters (high), or do they need context before the conclusion can land (low)?
   - Content structure arc: if the action goal is Decision or Understanding at high prior knowledge, apply the Pyramid Principle (conclusion first, top-down hierarchy). Otherwise use the default task-completion structure (context before answer). State the applicability rationale.
   - User task — what is the user trying to accomplish? State it as a verb phrase.
   - Completion definition — what does "done" look like for the user on this surface?
   - Content format: which format matches the task type? (prose for conceptual explanation; numbered steps for procedural tasks; table for comparison or reference; diagram for relationships or flows)
   - Content hierarchy using the Nava PBC must-say → probably-say → might-say model: what is non-negotiable (must-say), what helps most readers (probably-say), and what serves edge cases (might-say)?
   - Completion metric — task completion rate or search resolution rate.

4. **Resolve and write the content brief.** Copy `assets/content-brief-template.md` to `docs/design/content/<slug>.md`. Fill the relevant sections for the surface type. Resolve any conflicts in the elicitation (competing section jobs, unclear audience priority) before writing — the brief should have no open decisions, only open questions. Record open questions at the end. The artifact path follows the three-tier layout contract (config → default → discover-by-marker) per RFC-0050 D6; the default is `docs/design/content/<slug>.md` with frontmatter `type: content-brief`. Load `references/agentbundle-layout.md` for the full path resolution.

5. **Hand off.** Once the content brief is written:
   - Name `tone-of-voice` as the next step for copy voice and register grounding — the brief names what to say; tone-of-voice names how to say it.
   - Name `user-flow` as the next step for screen sequencing — the scroll sections and content hierarchy in the brief feed the screen-flow's copy slots directly.
   - Note: experience-reviewer scope extension to include content briefs as a reviewable artifact type is deferred to a follow-on RFC (RFC-0062 OQ1). Until that RFC ships, experience-reviewer does not review content briefs; this step is the hand-off point.

## Anti-patterns to refuse

- **Reprinting framework text verbatim.** Name the Schwartz awareness ladder, StoryBrand arc, CCD principles, Nava PBC model, or Pyramid Principle as named references; never quote their framework text or list their elements as though they are the answer.
- **Producing copy templates or pre-written strings.** This skill produces content direction — what to say, in what order, to whom — not finished copy. If the output contains a written headline or label, it has overstepped.
- **Producing an analytics or measurement framework.** Naming a success metric (task completion rate, sign-up rate) is in scope. Specifying tracking instrumentation, funnel metrics, or A/B test design is not.
- **Running user research or VoC production.** This skill takes audience information as input; it does not produce it. If no persona exists, elicit inline at the level of a sketch — do not run a research project.
- **Producing an SEO keyword plan or meta-tag specification.** SEO is explicitly deferred per RFC-0062 D5; naming a headline's clarity is in scope, targeting a keyword is not.
- **Writing a single "global" brief for multiple distinct surfaces.** Each surface gets its own brief — a global brief produces direction that serves none of them precisely. If the ask is multi-surface, produce one brief per surface or push back on scope.
- **Substituting a content brief for a screen flow.** The brief names what each section must accomplish; it does not sequence screens or define interaction states — that is `user-flow`'s job.
