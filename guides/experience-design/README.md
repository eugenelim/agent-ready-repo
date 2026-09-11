---
title: "`experience-design` — guides"
summary: Move from an understood need through journeys, screens, service evidence, design decisions, and independent review.
pack: experience-design
kind: explanation
---

# `experience-design` — guides

Use this pack to move from an understood user need to design decisions a builder
can implement and an independent reviewer can assess. Start with the job in your
own words: “Map what a new customer goes through, turn the painful step into
screens, and tell me which design decision comes next.” You receive durable
design artifacts and an explicit next step; the pack does not write frontend
code or choose the product bet for you.

## Walk the guidebook

This guidebook is for a product designer, product engineer, or product team
turning an understood user outcome into reviewed screen designs. It assumes you
can name the user, their intended outcome, and the surface you are designing.
Existing research, brand constraints, and design artifacts help, but each step
says which inputs are required and which can be elicited.

Type the requests shown in each step into an AI agent session with the
`experience-design` pack installed. They are natural-language requests for the
agent, not terminal commands.

Artifact paths use two placeholders:

- `<output_dir>` is the configured root directory for design artifacts.
- `<slug>` is the short, project-specific name substituted into a file path,
  such as `account-setup`.

Every step has the same layout, so once you have read one you know where to
look on the rest. Above the first heading: where you are, what the step changes,
what you need first and the cost of skipping it, and any concept it depends on.
Then **What you will run** — a table of that step's skills, what each produces,
and which ones you actually have to run. Then one **Run** section per skill.
Then **Where this leads**.

Each run section shows what you type, what the agent returns, a turn where you
push back and the agent adjusts, the decision and judgement point, what to do
when it goes wrong, and where the artifact lands with the headings to expect
inside it.

Walk these in order:

1. [Map the customer journey](how-to/map-the-customer-journey.md)
2. [Derive the screen flow](how-to/derive-the-screen-flow.md)
3. [Establish design intent](how-to/establish-design-intent.md)
4. [Design each screen](how-to/design-each-screen.md)
5. [Review independently](how-to/review-independently.md)

## Choose by job

**Understand what happens.** Use `journey-mapping` for the customer's path,
`service-blueprint` for the people and systems behind it, `process-mapping` for
an internal operation, and `experience-status` to orient to existing design
artifacts.

**Turn intent into a screen experience.** Use `design-principles` for durable
arbitration rules, `user-flow` for screen sequence and edge paths,
`information-architecture` for hierarchy and wayfinding, and
`interaction-design` for behavior within a screen or component.

**Set direction and assess the result.** Use `creative-direction` for visual
goals, `design-system` for the token taxonomy, `content-design` for the surface's
message and narrative structure, and `design-review` for an authoring-time
critique. Copy has four distinct layers: `tone-of-voice` owns the brand register;
`content-design` owns what a surface must communicate; `copy-direction` owns
copy goals for one acquisition surface; `ux-writing` in product engineering
owns product UI strings.

**Match the surface genre.** Use `conversion-design` for marketing,
`documentation-design` for docs and help, `analytical-design` for dashboards,
`informational-design` for editorial reading, `marketplace-design` for
multi-party exchange, and `workspace-design` for sustained professional work.

That is the complete 20-skill inventory. Every skill ships a portable method,
not framework code, styling syntax, values tables, or pixel comps.

## Leave the pack at the discipline boundary

- Market, audience, positioning, adoption, and organization-level direction
  belong to product strategy.
- Framing, appetite, risks, scope, solution options, and bet commitment belong
  to product-engineering shaping.
- HTML, CSS, components, data bindings, and build evidence belong to frontend
  engineering after the design is approved.

Read [The experience thread](explanation/the-experience-thread.md) for the
mental model, or [Thread a feature from journey to screens](how-to/author-design-intent.md)
to run the connective path end to end.

## Explanation

- [The experience thread](explanation/the-experience-thread.md) — the connective
  + craft skills, why the discipline is framework-agnostic, the shared quality
  floor, the macro/micro carve, and how design intent feeds the build.

## How-to

- [Thread a feature from journey to screens](how-to/author-design-intent.md) —
  map the journey, derive the screen flow and per-screen briefs, blueprint the
  services, design and critique each screen, and get an independent review.
- [Route copy work across content-design, copy-direction, ux-writing, and tone-of-voice](how-to/copy-boundary.md) —
  which skill owns what across the four-way copy boundary.

## Reference

- [The skills, the reviewer, and the `quality-floor`](reference/experience-design.md) —
  what each skill and the `experience-reviewer` agent trigger on, what they
  produce, the `[design]` layout, and the shared floor they all clear.

---

Installing and upgrading live in [`../_shared/`](../_shared/).
