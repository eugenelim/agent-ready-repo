# Spec: Engagement-shaping guides (product vision → strategy → architecture concept)

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim

Mode: full (multi-feature risk trigger — four new guides). Scoped to docs:
the operative gates are `new-guide`'s per-guide audience-contract checkpoint,
the per-quadrant Diátaxis rules, the `clear-prose` pass, and an
`adversarial-reviewer` pass. No security/infra machinery applies (repo-owned
Markdown under `docs/guides/`, which is not projected, so `build-self` drift
does not gate it).

## Objective

Give the practitioner who shapes a **new engagement / project** the recipes for
the three upstream shaping artifacts the catalogue's skills already produce but
that no guide yet documents — a **product vision**, a **product strategy**, and
an **architecture concept** — plus one explanation that ties them into a single
co-shaping arc. Frame every piece for that reader (delivery lead, product owner,
or solution architect starting an engagement), org-neutral.

## Why these four (and not more)

The two product altitudes and the architect-design Stage-0 concept have **no
how-to today** (`product-engineering` ships only `shape-a-feature-intent` at the
feature altitude; `architect` ships diagram/review/reference-architecture but no
`architect-design` how-to). Those are the real gaps.

The relations the user asked for are **already partly covered**, so this spec
does not duplicate them:

- vision ↔ strategy relation → `product-engineering/explanation/the-intent-tree.md`
  (+ `frame-intent/references/intent-model.md`).
- product → architecture **sequence** for a new project →
  `_shared/how-to/run-a-full-inception.md`.

What is *not* yet written is the **why product and architecture co-shape each
other** at engagement start — an explanation, which a how-to cannot carry. One
new explanation covers both the vision↔strategy and product↔architecture
relations as a connected arc, and cross-links (not restates) the two existing
pieces above.

## Deliverables

New files:

1. `docs/guides/product-engineering/how-to/frame-a-product-vision.md` — how-to.
2. `docs/guides/product-engineering/how-to/shape-a-product-strategy.md` — how-to.
3. `docs/guides/architect/how-to/shape-an-architecture-concept.md` — how-to.
4. `docs/guides/_shared/explanation/shaping-a-new-engagement.md` — explanation
   (cross-pack; the co-shaping arc and the relations).

README updates (per-pack indexes — the only index files; `new-guide` forbids
touching the per-quadrant framework READMEs):

5. `docs/guides/product-engineering/README.md` — add the two new how-to lines.
6. `docs/guides/architect/README.md` — add the new how-to line.
7. `docs/guides/README.md` — add the new `_shared` explanation under the
   "Not tied to one pack" section.

## Acceptance criteria

- [x] AC1 — Each of guides 1–3 is a true **how-to**: titled by the reader's
  problem, no reteaching of basics, names the real variations/pitfalls,
  documents a skill that **ships** (`frame-intent`, `architect-design`).
- [x] AC2 — Guide 1 documents `frame-intent` at the **`product-vision`** altitude
  (the existence bet; market-existence de-risk), not the feature altitude;
  it cross-links `shape-a-feature-intent` and `the-intent-tree`.
- [x] AC3 — Guide 2 documents `frame-intent` at the **`product-strategy`**
  altitude (central challenge, guiding policy, coherent actions, problem/segment
  sequence) and how it decomposes from a vision.
- [x] AC4 — Guide 3 documents the **Stage-0 architecture concept** from
  `architect-design` (≤½-page: problem/constraints, candidate shapes, provider,
  top quality attributes, key tradeoff) and the offer to converge into a full
  design doc — it does **not** re-document the full design-doc flow.
- [x] AC5 — Guide 4 is a true **explanation** (an *About <X>* frame, no
  step-by-step), explaining vision↔strategy and product↔architecture-concept
  co-shaping for a new engagement; it **cross-links** `the-intent-tree`,
  `run-a-full-inception`, and the three new how-tos rather than restating them.
- [x] AC6 — Every new guide opens matching its pack's existing convention: the
  `> **Diátaxis: <quadrant>.**` banner where the pack already uses one
  (product-engineering how-tos and explanations do), a plain `>` lead in the
  architect pack, and a plain prose lead (with an italic *About …* frame for the
  explanation) in `_shared`, where the sibling pages carry no banner. Each guide
  carries a `See also` section that links **only files that exist** (no broken
  links; placeholders surfaced, not invented).
- [x] AC7 — The three README indexes list the new guides with one-line
  descriptions matching the house style; existing reverse-links added from the
  cross-linked existing guides where the house style already does so.
- [x] AC8 — Prose passes the `clear-prose` checklist (no *simply/just*, no
  throat-clearing, no AI-tells, retcon discipline) and an `adversarial-reviewer`
  pass returns clean.

## Boundaries

- **Never do:** duplicate `the-intent-tree.md` or `run-a-full-inception.md`;
  re-document the full `architect-design` design-doc flow inside the concept
  how-to; bake a specific org name into the prose (keep it engagement-neutral);
  edit the per-quadrant framework READMEs under `_shared/<quadrant>/`.
- **Ask first:** splitting guide 4 into two separate explanations; placing the
  cross-pack explanation somewhere other than `_shared/explanation/`.
- **Always do:** match the surrounding per-pack guide structure and voice;
  honour `new-guide`'s audience-contract checkpoint per guide.

## Tasks

- T1 — Confirm the four audience contracts (gated; this surface). Depends on: none.
- T2 — Draft guide 1 (frame-a-product-vision). Depends on: T1.
- T3 — Draft guide 2 (shape-a-product-strategy). Depends on: T1.
- T4 — Draft guide 3 (shape-an-architecture-concept). Depends on: T1.
- T5 — Draft guide 4 (shaping-a-new-engagement explanation). Depends on: T2,T3,T4
  (it cross-links them). 
- T6 — Update the three README indexes + reverse cross-links. Depends on: T2–T5.
- T7 — clear-prose pass + adversarial-reviewer; fix; finish checklist. Depends on: T6.

## Declined temptations

- Tempted to add a standalone vision↔strategy explanation; declining —
  `the-intent-tree.md` already owns it; cross-link instead.
- Tempted to add a fifth "engagement inception" how-to; declining —
  `run-a-full-inception.md` already is that how-to; guide 4 is the missing
  *explanation*, not another recipe.
- Tempted to add a tutorial for the vision→strategy→concept arc; declining —
  no one asked for a guaranteed-result lesson, and the arc is reader-driven, not
  a single deterministic path.
