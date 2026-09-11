---
type: documentation-surface-spec
surface-type: product-or-reference
communication_mode: reference-documentation
persona: non-technical-practitioner — docs/design/journeys/claude-apps-practitioner-current-state.md
date: 2026-09-10
---

# Documentation surface: reaching a discipline method without a terminal

Structural specification for the documentation that answers
[the practitioner journey](../journeys/claude-apps-practitioner-current-state.md).
IA and placement only — this does not write the pages, and it makes no
per-pack first-value claim.

## Preconditions

- **Goal is reader enablement.** The reader is measured on completing the
  registration task, not on converting.
- **TTFV target:** the reader has the catalogue registered and an install
  submitted, in a single sitting, knowing what is and is not claimed about it. The journey's highest positive peak — a method running to
  an artifact — sits one step beyond this surface, with the first-value work
  that owns it.
- **Navigation strategy is settled, not proposed.** 209 guide pages, already
  hub-and-spoke: `guides/README.md` is the hub, per-pack sections are the
  spokes. This work places pages into that structure and changes no navigation
  architecture.

## Decision (a) — the Stage 1 fix is an entry *and* a page, with different jobs

The negative peak is at **discovery**, on the site home, where the only install
affordance is a terminal block. A new guide page cannot fix discovery; only a
route from the home page can. But that route needs a destination the reader can
act on, and the existing destination is the wrong content type:
`guides/_shared/explanation/install-routes.md` is an **explanation** — it
answers "why are there four routes", which is not the question a reader with no
terminal is asking.

So both, and neither substitutes for the other:

| Piece | Job | Type |
|---|---|---|
| Home-page door | One of **two equal doors** in the home's start zone, not a side entrance | link, not content |
| New destination page | Takes the reader from nothing to a submitted install, with the evidence boundary stated | **How-to** |

Superseded 2026-09-10 by the marketing-home brief's audience amendment: the
home's reader is now a first-time user whose goal is Execution, so starting is
the page's business rather than a station partway down it. The Claude-apps route
is half of the primary action, and this page is what that half opens onto —
which raises its bar. It is the destination of a promoted call to action, not a
page found by someone already looking.

**Corrected 2026-09-10 after shaping review: this is a how-to, not a tutorial.**
The repository picks by reader posture, and the reader arriving through the door
has a *named task* — get this catalogue into the app they already use. Tutorial
posture would be on-rails learning of a discipline method ending in a
recognisable artifact, and that is exactly what
[`claude-apps-first-value-entry`](../../product/intents/claude-apps-first-value-entry.md)
owns and cannot yet reach: `[pack.first-value]` cannot name this surface, and no
install has been observed. So the split is real rather than a relabelling — the
how-to carries the reader to a submitted install, a later tutorial teaches the
method to an artifact, and only the second needs the first-value contract.

## Decision (b) — split the Stage 3 cliffs by type, not by convenience

The three cliffs are not one kind of content, and putting them together would
mix types in a single page.

| Cliff | Reader's question | Type | Placement |
|---|---|---|---|
| Wrong-store registration | "Did I do this right?" | how-to **step** | Inline, at the registration step |
| Sub-agents inert in chat | "What works where?" | **Reference** | Separate capability reference |
| Artifact has nowhere to land | "Where does my output go?" | **Reference** | Same capability reference |

Cliff 1 belongs **in the how-to, at the moment of registration**. It is a
step-level correction, not a lookup: a reader who registered in Claude Code and
sees nothing in chat has already failed, and a reference page they have not
opened cannot save them. This is the one place where inline interruption is
correct.

Cliffs 2 and 3 are lookups — a surface × capability matrix consulted later and
returned to. Dropping a matrix into the middle of a procedure is the type-mixing
anti-pattern: the reader who came to get started loses the thread, and the
reader who came to check a capability will not find it inside a how-to.

## Decision (c) — content types and placement

| Piece | Type | Path | Status |
|---|---|---|---|
| Registering and installing in the Claude apps | How-to | `guides/_shared/how-to/<slug>.md` | **new** — joins an existing quadrant; no new quadrant is created |
| Claude surface capabilities | Reference | `guides/_shared/reference/<slug>.md` | **new** — joins 13 existing `_shared` reference pages |
| Install routes | Explanation | `guides/_shared/explanation/install-routes.md` | **exists, done** — gains two outbound links, no new prose |
| Home-page entry | link | `web/src/pages/index.astro` | **new link** |
| Guide hub + docs-site pointers | link | `guides/README.md`, `docs-site/.../getting-started/install.md` | **new links** |

`_shared` is correct for both new pages: the subject is the *surface*, which is
cross-pack. The how-to names `product-strategy` as its example because it is the only one
of the four carrying no sub-agents, so nothing in its skill listing degrades
silently while the reader is learning to trust the surface.

**Do not duplicate `install-routes.md`.** It owns the four-route comparison,
the per-surface registration mechanics, and the org path. The how-to links to it for "why"; the reference links to it for the org route.
Neither restates it.

## Machine-readability requirements

Design-time, not implementation notes:

- The capability reference uses one table with fixed columns — **Surface |
  Skills | Sub-agents | Hooks | Where artifacts land** — so it is parseable and
  so a new surface is a row, not a rewrite.
- UI paths render as literal breadcrumb text (`Customize › Plugins › Personal
  plugins`) consistently in both pages, because that string is what a reader
  scans for.
- Heading hierarchy: H2 = section, H3 = procedure step in the how-to.
- Both pages carry `title:` frontmatter, which is also what keeps them out of
  `guide-nav-baseline.toml` — that registry is frozen and shrinking, and none
  of the existing `_shared` explanation pages appear in it. **A new page needs
  no baseline entry.**

## Constraints carried

- `tools/lint-plugin-route-docs.py` pins literal substrings across 9 sites. Two
  of its sites are edited here (`install-routes.md`, and the docs-site install
  page if it gains a pointer); the gate must stay green, and its pinned strings
  are not to be reworded incidentally.
- New pages must pass `validate_guides.py`, `check-guide-index.py`, and
  `lint-guide-titles.py`, and keep `title:` identical to the leading H1.
- **Out of scope, mechanically:** no page may state that a pack *delivers first
  value* on the Claude apps. `[pack.first-value].surfaces` must be a subset of
  `[pack.install].allowed-adapters` and all four packs declare `["claude-code"]`
  — so the how-to teaches registration and install, and says nothing about
  certified first value or a completed method.

## What this does not decide

The how-to's copy, its example's exact steps, and the wording of the capability
matrix. Those are authoring decisions for `author-product-docs`.

---

**Delivery ownership:** `claude-apps-first-value-entry`. This brief specifies
composition and content constraints only; it does not own delivery of the
first-value doors or the route copy.
