---
name: marketplace-design
description: "Use when designing a marketplace surface — a catalogue, a listing grid, a product detail page, or a buying/transaction flow that connects buyers and sellers or producers and consumers. Triggers on 'design the marketplace', 'structure the listing page', 'how should the catalogue work', 'design the search and filter', 'buyer journey on the marketplace', 'product card design'. Produces IA specifications for catalogue, filter, comparison, and transaction bridge surfaces. Do NOT use for single-product marketing surfaces (use conversion-design) or workspace tool surfaces (use workspace-design). Surface genre: marketplace. Do NOT use to name copy voice goals — use `copy-direction` for a specific surface or `tone-of-voice` for brand-level register."
---

# Skill: marketplace-design

Converts the buyer journey and the listing object model into a **structural specification for a marketplace surface** — the listing card IA, the filter and facet architecture, the comparison affordances, and the transaction bridge that carries a buyer from discovery to commitment. This skill is IA and structure; it does not design individual card components (that is `interaction-design`'s component state machine) and does not derive the token/scale taxonomy (that is `design-token-taxonomy` and `creative-direction`).

## Output rendering

Table — When presenting several items that share the same fields, render a Markdown table. Cap at ~5 columns; beyond that, switch to a per-item detail list. Right-align numeric columns.

## When to invoke

Confirm all three before specifying:

1. **The surface mediates a match between two parties** — a buyer choosing a seller, a user selecting from a catalogue, a customer finding a service. If the surface sells a single product directly, use `conversion-design`.
2. **The listing object model is defined** — what attributes does each listing carry? Which attributes drive filtering? Which drive comparison? The card IA and filter architecture are downstream of this model.
3. **The dominant buyer behavior is named** — browse-first (I don't know exactly what I want, show me options) vs. search-first (I know what I want, help me find it quickly). These produce fundamentally different surface structures.

## Listing card IA

The card is the atomic unit of a marketplace. Its hierarchy determines which attribute drives the match. Structure the hierarchy in order of decision weight:

1. **Primary identifier** — the name or title that lets the buyer know they're looking at the right category of thing (product name, service title, pack name)
2. **Key attribute** — the attribute that most immediately qualifies or disqualifies the listing for this buyer (price, rating, availability, compatibility, experience level)
3. **Social proof signal** — one trust signal visible on the card (rating score + count, badge, review count, notable customer name)
4. **Secondary attributes** — supporting details that inform, not decide (category tags, secondary specs, provider name)
5. **Primary CTA** — the action that advances commitment (View, Get, Install, Book, Select)

**Card density vs. detail page:** the card carries enough to qualify; the detail page carries enough to commit. Do not put commitment-level information on the card; do not put qualification-level information only on the detail page. A buyer who must open every card to qualify listings has a card that is doing the detail page's job.

## Filter and facet architecture

Filters reduce the consideration set; they do not select. The architecture decision — chip vs. sidebar, instant vs. apply-button, single-select vs. multi-select — follows from the filter purpose:

**Taxonomy design (before filter UI):**
- Name the dimensions a buyer filters on (category, price range, rating, compatibility, availability)
- For each dimension, name the options: are they enumerable (6 categories) or continuous (price range)? Enumerable dimensions suit chips or multi-select lists; continuous dimensions suit range sliders
- Name which dimensions are mutually exclusive (a listing is in exactly one category) vs. multi-valued (a listing can have multiple tags)

**Chip vs. sidebar:**
- **Chips** (horizontal filter row above the grid): best for ≤6 high-frequency filter dimensions; all visible at once; favors mobile and browse-first behavior
- **Sidebar** (vertical filter panel left of the grid): best for >6 filter dimensions or complex taxonomies; allows nested facets and filter groups; favors search-first and high-intent behavior

**Instant vs. apply-button:**
- **Instant** (grid updates as user selects): best when the consideration set is small or filter combinations are simple; provides immediate feedback on result count
- **Apply-button** (grid updates on explicit confirmation): best when filter combinations are complex or network latency makes instant updates jarring; required when filter selections are expensive to compute

**Empty-filter vs. zero-results distinction:**
- **Empty filter** (no filter applied, all listings visible): the starting state; the grid is full
- **Zero results** (filters applied, no matching listings): a design failure if it appears without explanation and recovery. Always show: which filters produced zero results, and the closest partial-match suggestions or the "clear filters" affordance

## Comparison affordances

When buyers need to compare listings before committing, design a comparison affordance that is available before the decision to compare is made:

- A **compare checkbox** (or toggle) on the card, visible before the card is opened — comparison intent surfaces at the browse stage, not after the buyer has already invested in individual detail pages
- A **comparison panel** or **comparison page** that aligns attributes in parallel columns — each column is one listing; each row is one attribute. Attributes that differ between listings are the decision levers; attributes that are identical are de-emphasized
- A **maximum comparison set** — comparing more than 4 listings simultaneously exceeds working memory. Limit to 4; prompt to remove before adding more

## Browse-first vs. search-first routing

**Browse-first surfaces** (buyer is exploring, not searching):
- The grid IS the primary experience; search is secondary
- Filter architecture is chip-based, immediately visible
- Card density is lower (more white space, larger images, fewer attributes) to invite exploration
- Sort order defaults to "recommended" or "popular"; the buyer is not yet ready to optimize on a specific attribute

**Search-first surfaces** (buyer knows what they want):
- Search is the primary experience; the grid is the result set
- Filter architecture is sidebar-based, complex, available immediately on search
- Card density is higher (more attributes visible, smaller images) to enable rapid qualification
- Sort order defaults to "relevance" to the search query; the buyer is optimizing, not exploring

## Transaction bridge to interaction-design

The point where a buyer commits — cart, checkout, booking confirmation — transitions from marketplace IA to wizard/stepper interaction design. This transition is a design seam:

- Name the handoff point explicitly (what action triggers the transition from marketplace to transaction)
- The transaction flow is a wizard pattern (see `interaction-design`'s wizard-and-stepper family): linear steps, save-and-resume, form validation
- The marketplace context (what listing the buyer selected) must be visible throughout the transaction flow — buyers abandon when they lose sight of what they are committing to

## Canonical aesthetic reference tier (study subjects, not prescriptive tools)

For grounding creative-direction on a marketplace surface, study how these products handle listing clarity and filter architecture: Airbnb (browse-first, map-integrated, social-proof hierarchy), GitHub Marketplace (developer tool catalogue, badge-first trust signals), npm (search-first, high-density reference information). Internalize the structural philosophy — card hierarchy, filter legibility, comparison design — not the surface treatment.

## Anti-patterns to refuse

- **Card that does the detail page's job.** A card that requires the buyer to open it to qualify basic attributes has a card that is too sparse, or a detail page that is too deep. Restructure the card hierarchy.
- **Zero-results with no recovery.** An empty results page with no explanation of which filter produced no results, and no "clear filters" path, is a dead end.
- **Comparison without a maximum.** Comparison with no upper limit produces a broken layout at 6+ columns. Set the limit; enforce it in the affordance design.
- **Browse-first grid with search-first density.** A browse grid filled with small, high-density cards signals "I know what you want." If the user is exploring, lower density and more visual space reduce cognitive load.
- **Transaction flow that loses marketplace context.** A checkout that shows only the cart, not what the buyer selected or why it matched their need, increases abandonment. Keep the listing context visible.
