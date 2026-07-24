# `experience-design` — guides

The design/UX seat that carries the **whole design thread** — from a customer
journey, through the screens it implies and the services behind them, to how
each screen looks and behaves, to an independent review and a hand-off to
realization. 21 skills covering: journey mapping and screen flow derivation
(connective thread), design principles (Define phase), genre-specific surface
design (marketing, documentation, analytical, marketplace, informational,
workspace), craft design (creative direction, design-token-taxonomy,
design-system-foundations, information architecture, interaction design), content
design and tone of voice, continuous review, and a forked-context reviewer.

Every skill ships portable **method**, never your stack: no UI-framework code,
no styling-language syntax, no values tables, no pixel comps. The skills point
to the recognized standards — WCAG, the Design Tokens Community Group (DTCG),
Apple HIG, Material 3, APQC, BPMN — and ship the method to *derive* your design,
so the discipline travels to any repo and any toolchain.

## Start here

New here? The XD chain runs in this order:

1. **Discover** — map the customer journey, content intent, and copy voice goals
   → [Thread a feature from journey to screens](how-to/author-design-intent.md)
2. **Define** — derive the screen flow and design principles
   → [Thread a feature from journey to screens](how-to/author-design-intent.md)
3. **Design intent** — establish aesthetic direction and apply the token foundation
   → [Derive a token taxonomy and apply the design token foundation](how-to/design-system-chain.md)
4. **Design each screen** — identify the page archetype, then apply IA, genre-specific structure, and interaction patterns
   → [Page archetypes: when to use which](how-to/page-archetypes.md)
5. **Self-review** — run the three-pass design-review before the independent reviewer
   → [Run a design review before the independent pass](how-to/design-review.md)
6. **Independent review** — `experience-reviewer` reviews the full screen set in forked context
7. **Quality floor** — all 18 states required across every screen
   → [State coverage reference — the 18-state set](reference/state-coverage.md)

## Tutorials

- [Walk the full XD chain: SaaS onboarding from research to reviewed screens](tutorials/xd-cross-pack-tutorial.md) —
  follow the complete chain end to end across four packs (`desk-research` →
  `product-strategy` → `experience-design`) on a realistic SaaS onboarding
  surface, with all four handoff points shown explicitly.

## Explanation

- [The experience thread](explanation/the-experience-thread.md) — the connective
  + craft skills, why the discipline is framework-agnostic, the shared quality
  floor, the macro/micro carve, and how design intent feeds the build.

## How-to

Organized by XD chain phase:

**Connective thread (discover → define)**

- [Thread a feature from journey to screens](how-to/author-design-intent.md) —
  map the journey, derive the screen flow and per-screen briefs, blueprint the
  services, design and critique each screen, and get an independent review.

**Design intent**

- [Derive a token taxonomy and apply the design token foundation](how-to/design-system-chain.md) —
  the two-step chain from aesthetic direction to working token foundation: derive the
  token/scale taxonomy with `design-token-taxonomy`, then apply it as a working
  foundation with `design-system-foundations`.

**Surface design**

- [Page archetypes: when to use which](how-to/page-archetypes.md) —
  identify the right page archetype before designing hierarchy, apply the
  first-screen contract, attention contract, and read/write permission contract.

**Review**

- [Run a design review before the independent pass](how-to/design-review.md) —
  run the three-pass self-check (cold-read → primary task + unhappy path → full
  quality-floor contract review) before the forked-context `experience-reviewer`.

**Copy and content**

- [The three-way copy boundary: copy-direction, ux-writing, and content-design](how-to/copy-layer-boundary.md) —
  decide which copy skill to run on a new task and hand copy work to the right layer.

**Cross-pack**

- [How to run the cross-pack experience eval](how-to/run-cross-pack-eval.md) —
  run the deterministic `check-xd-chain.py` checker, read its output, and promote
  a check to a fail-closed gate.

## Reference

- [The skills, the reviewer, and the `quality-floor`](reference/experience-design.md) —
  what each skill and the `experience-reviewer` agent trigger on, what they
  produce, the `[experience]` layout, and the shared floor they all clear.
- [State coverage reference — the 18-state set](reference/state-coverage.md) —
  the canonical 18-state set shared by `design-review` (at design time) and
  `frontend-engineering` (at build time), aligned so design and build vocabulary match.
- [I want to… intent index](reference/intent-index.md) —
  cross-pack lookup: map a starting job to the right pack, skill, and guide.
  Covers single-skill jobs, multi-skill chains, and out-of-scope redirects.

---

Installing and upgrading live in [`../_shared/`](../_shared/).
