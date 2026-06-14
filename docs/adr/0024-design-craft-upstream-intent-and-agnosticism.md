# ADR-0024: `design-craft` serves designers as upstream design-intent authors, under strict framework-agnosticism

- **Status:** Accepted
- **Date:** 2026-06-14
- **Deciders:** eugenelim
- **Supersedes:** none
- **Related:** RFC-0033 (the proposal), RFC-0007 (user-scope refusal rails + grep-enforcement pattern), RFC-0004 (install-scope-per-pack, Rail A), RFC-0032 (the three-reviewer ceiling reading), `docs/specs/design-craft-pack/`

## Context

The catalogue had skills for product intent (`product-engineering`),
architecture (`architect`), and research (`research`), but nothing for the
**interaction/visual design** craft that sits between product intent and the
UI build. Designers — solo, design-eng hybrids, or part of a design team —
author the upstream **design intent** (an aesthetic direction, a token
taxonomy rationale, an information architecture, a heuristic critique) that
the build consumes, the way `product-engineering`'s briefs and specs feed the
delivery loop.

Two forces shaped how such a pack could exist here:

- **The charter's "not a framework that picks your tech stack."** A design
  pack is the single most tempting place to violate this: design content
  naturally reaches for React/Vue, CSS, ARIA, animation libraries, and
  values cheat-sheets (palettes, spacing scales, contrast ratios). Ship those
  and the pack stops being portable method and becomes one stack's manual.
- **The "habits, not infrastructure" principle and the three-reviewer
  ceiling.** RFC-0032 read the charter's reviewer ceiling as scoping the
  *core code-review lenses*, not opt-in design-side review. A design pack must
  not smuggle in a hook, an engine, an in-pack validator, or a fourth
  `work-loop` reviewer subagent.

The open question (RFC-0033 OQ#2) of whether design-craft should also ship a
forked-context `design-reviewer` subagent (the RFC-0032 twin) was deferred —
v1 is skills only.

## Decision

> **`design-craft` is an opt-in, user-scope pack of pure-markdown skills that
> serve designers as authors of upstream design intent, and every skill is
> stripped to portable method under two hard agnosticism guardrails.**

Specifically:

- **Audience and seam.** The pack serves interaction/visual designers and
  design-eng hybrids authoring design intent the build consumes — the
  design-side twin of `product-engineering`'s product-intent seam. v1 ships
  **four skills** (`aesthetic-direction`, `design-system-foundations`,
  `layout-and-information-architecture`, `design-critique`) plus a shared
  **`quality-floor` checklist** (handle-all-states, accessibility floor,
  reduced-motion principle).

- **Guardrail A — point to standards, never reprint values.** Skills name the
  recognized standards (WCAG for the accessibility/contrast floor, the W3C
  Design Tokens interchange shape for serialization) and ship the method to
  *derive* values. They never reprint a palette, spacing/type scale, contrast
  ratio, or any px/ms/hex/easing table.

- **Guardrail B — concepts, not platform primitives.** Wayfinding is described
  as orientation, never as ARIA roles; layout as hierarchy and reading flow,
  never as CSS grid; motion as the reduced-motion *principle*, never as a
  media query or an animation library.

- **Habits, not infrastructure.** No hook, no engine, no in-pack
  validator/linter, no `work-loop` reviewer subagent, no new top-level
  directory. `design-critique` is an interactive authoring-time **skill**, not
  a forked-context reviewer. The `design-reviewer` subagent twin (RFC-0033
  OQ#2) is explicitly out of v1 — a later RFC if ever.

- **Enforcement is catalogue governance, not a pack primitive.** The
  agnosticism guarantee is held by a **pack-scoped lint**
  (`tools/lint-design-craft-agnostic.py`) wired into CI — the RFC-0007
  grep-enforcement pattern. It is **not** promoted to a repo-wide
  `CONVENTIONS` lint; doing so would be a separate RFC decided on its own
  merits.

- **Install shape.** User-scope-default (`default-scope = "user"`,
  `allowed-scopes = ["user","repo"]`), all seven shipped adapters, contract
  v0.12 (matching `research`). No `seeds/` (RFC-0004 Rail A); the one template
  (the aesthetic-direction doc) rides as a skill `assets/` file copied into the
  repo at runtime.

## Consequences

**Positive:**

- The pack travels to any repo and any stack — its method survives a
  framework change because it never depended on one.
- The agnosticism promise is mechanically enforced, so a well-meaning future
  edit that pastes in a values table or a CSS snippet fails CI rather than
  rotting the pack's portability.
- The catalogue gains a coherent design-intent seam that mirrors the
  product-intent one, without expanding the reviewer ceiling or adding infra.

**Negative / accepted trade-offs:**

- Designers used to copy-paste starter values (a default palette, a spacing
  scale) get method instead of a cheat-sheet. That is the deliberate cost of
  portability; the skills compensate by teaching the derivation.
- The pack-scoped lint is bespoke to one pack. If a second pack ever needs the
  same enforcement, the lint should be generalized — but that is a future
  decision, not a reason to over-build now.

**Neutral / to revisit:**

- Whether design-craft eventually ships a `design-reviewer` subagent (OQ#2)
  remains open and would reopen the reviewer-ceiling reading RFC-0032 settled.

## Alternatives considered

- **Fold design skills into `architect` or `product-engineering`.** Rejected:
  the audience and the craft differ, and overloading those packs blurs both.
  A standalone, opt-in pack keeps each pack's identity sharp.
- **Ship concrete starter values (a default design system).** Rejected: it
  would directly violate the charter's "not a framework that picks your tech
  stack" and make the pack stale the moment a team's stack or brand differs.
- **Enforce agnosticism by a repo-wide `CONVENTIONS` lint.** Rejected for v1:
  the rule is specific to this pack today; a repo-wide rule is a separate RFC
  with its own blast radius.
- **Make agnosticism a review-only (judgment) check.** Rejected: design
  content is the highest-temptation surface for stack leaks, so it earns a
  mechanical floor under the judgment, the way RFC-0007 treats the converters
  rails.

## References

- RFC-0033 — `docs/rfc/0033-design-craft-pack.md`
- `docs/specs/design-craft-pack/spec.md` and `plan.md`
- RFC-0007, RFC-0004, RFC-0032; the converters CI scrubs in
  `.github/workflows/build-check.yml`
