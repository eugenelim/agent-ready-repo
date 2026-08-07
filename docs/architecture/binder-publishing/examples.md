# Worked examples

> Concrete recipes, errors, and an end-to-end scenario.
> Part of [binder publishing architecture](README.md).

## Concrete examples

### Portable repository layout

```
project/
├── binder.toml
├── binders/
│   ├── architecture-review.binder.toml
│   ├── release-readiness.binder.toml
│   └── editorial/
│       └── payments-exec-summary.md
├── docs/ · notes/
└── .binder-work/            # gitignored
```

### User-scoped use in an unrelated directory

```bash
# ~/clients/acme/discovery — no Git, no pack.toml, no site.toml
cat > ~/clients/acme/discovery/binder.toml <<'TOML'
schema-version = "1"
id    = "acme-discovery"
title = "Acme Discovery Pack"

[[sections]]
id = "findings"
title = "Findings"

[[sections.items]]
path = "interviews/summary.md"

[[sections.items]]
path = "analysis/opportunities.md"
TOML

python scripts/binder.py build binder.toml --root=$HOME/clients/acme/discovery
# → ~/clients/acme/discovery/build/binders/acme-discovery/index.html
```

### `binder.toml` with semantic selectors (Phase 2)

```toml
schema-version = "1"
id      = "architecture-review"
title   = "Architecture Review — ${subject}"
purpose = "Everything the review board needs to decide on ${subject}."

source-roots = ["docs"]

required-params = ["subject"]

[params]
# no default for `subject` — it is in required-params, so the caller must supply it

[[sections]]
id    = "evidence"
title = "Context and evidence"

[[sections.items]]
select = { kind = "research", subject = "${subject}" }
pick   = "all"
order  = "date"

[[sections]]
id    = "decisions"
title = "Decisions"

[[sections.items]]
select = { kind = "adr", subject = "${subject}", status = "current" }
pick   = "all"

[[exclude]]
select = { status = "retired" }
```

Run against a Phase-0/1 build, this produces the *not-yet-implemented key* error
shown earlier — never a silent partial resolution.

### A dynamic overlay (Phase 3)

```toml
schema-version = "1"
id      = "payments-board-2026-08"
extends = "binders/architecture-review.binder.toml"
title   = "Payments Migration — Review Board Packet"
audience = ["architecture review board", "security reviewer"]

[params]
subject = "payments-migration"

[[sections]]
id       = "summary"
title    = "Executive summary"
kind     = "editorial"
position = "first"

[[sections.items]]
path = "binders/editorial/payments-exec-summary.md"
role = "executive-summary"

# Both competing proposals, explicitly — a required item may not be a query
[[sections.overrides]]
section = "proposal"

[[sections.overrides.items]]
path     = "docs/rfc/0091-payments-migration.md"
required = true
label    = "Proposal A — ledger service"

[[sections.overrides.items]]
path     = "docs/rfc/0093-payments-strangler.md"
required = true
label    = "Proposal B — strangler migration"

[[exclude]]
path   = "docs/rfc/0088-payments-migration-draft.md"
reason = "superseded by RFC-0091"
```

Overlay semantics: `extends` deep-merges; `[[sections]]` with a new `id` are added
at `position`; `[[sections.overrides]]` replaces a named section's items;
`[[exclude]]` entries accumulate and always win. An overlay may **not** convert a
required exact reference into a selector, and may not introduce a key the schema
does not define — which the unknown-field rule already covers.

> An earlier version added "and may not set `[policy] profile` less strictly than
> its base". D-A removed the key: it is now an unknown field, exit 4, at every
> level. [`binder-recipe.md`](binder-recipe.md) is the authority on the surface.

### The per-file transformation, worked — and the diagram that is not transformed

Source (`docs/design/payments/design.md`, unchanged on disk):

````markdown
 1  ---
 2  title: Payments migration design
 3  status: Draft
 4  css: /tmp/evil.css
 5  ---
 6
 7  # Payments migration design
 8
 9  The ledger boundary is shown below.
10
11  ```mermaid
12  flowchart LR
13    A[Gateway] --> B["Ledger<br/>service"]
14    B --> C[(Postgres)]
15  ```
````

Staged (`docs/011-docs-design-payments-design.md`):

````markdown
 1  ---
 2  title: "Payments migration design"
 3  ---
 4
 5  The ledger boundary is shown below.
 6
 7  ```{.mermaid data-a11y-name="Diagram 11.1"}
 8  flowchart LR
 9    A[Gateway] --> B["Ledger<br/>service"]
10    B --> C[(Postgres)]
11  ```
````

**The fence *body* is byte-identical to the source's, and the fence is still one
line.** No `` ```{mermaid} `` rewrite, no injected `%%| label:` line, no
caption-binding protocol, no fence content-hash — because Z3a verified Zensical
reads the portable fence directly and emits `<pre class="mermaid"><code>…`. Z3e
verified the `<br/>` inside the node label survives, entity-escaped in the HTML and
decoded by the browser as the `<pre>`'s text content, exactly as Q28 recorded under
Quarto.

**The opening delimiter carries the accessibility attribute (D46), and that is why
it is on line 7 in both columns.** The annotation is a same-line rewrite: the theme
lifts `data-a11y-name` into the Mermaid source as an `accTitle:` in the reader's
browser, so nothing is inserted into the staged file and the offset below stays
constant. The value is `Diagram <chapter-ordinal>.<n>` — all of it compiler-owned,
none of it from the diagram body — and allowlist-reduced, because Z6h found an
`attr_list` value containing a quote terminates the attribute and admits raw markup.
A descriptive name and a `data-a11y-desc` arrive with `figures[]` in Phase 2.

Emitted into `renderer-plan.json` (**not** the index — invariant 22):

```json
"line-offset": -4
```

Reading it: the frontmatter rebuild (steps 1–2) shortens by 2, the duplicate-H1
drop (step 3) shortens by a further 2, and **nothing below that changes** — the
link/asset rewrite (step 4) and the fence annotation (step 5) both edit within a
line. Source 9 → staged 5, source 12 → staged 8, source 15 → staged 11 — one delta,
every line.

**This is the property that decided D46.** The first replacement drafted for the
falsified accessible-name mechanism wrapped each fence in a `<figure>` with a
`<figcaption>`, which would have inserted lines *here*, between the head and the
tail of this very file — reintroducing exactly the per-diagram divergence the
paragraph below describes. The offset staying scalar is not a happy accident of the
chosen mechanism; it is the constraint the mechanism was chosen to satisfy.

**This example used to be the proof that a scalar offset was impossible.** Under
Quarto the deltas were 0, −4, −4, −3 across this one file, because the fence
transform and its injected cell option shifted the body relative to the head; that
is why round 1 replaced `line-offset` with a `line-map` breakpoint array, and why
this example existed. D-B removed the transformation that made the array
necessary, and the same example now demonstrates the opposite. That is worth
noticing rather than quietly editing: the array was correct for the renderer it
was designed against.

Two security-relevant things still happen, and one no longer needs to. The `css:`
key — a source-controlled renderer-configuration channel — is **discarded with the
rest of the frontmatter**, not filtered out; a source cannot reach renderer
configuration whatever the renderer is. The H1 is dropped because it duplicated
the chapter title. What is *not* needed any more is a shortcode pass: Z3f verified
`{{< env … >}}` and `${…}` pass through as literal escaped text. **The source file
on disk is byte-identical to before.**

### Minimal `binder.toml` — Level 0

```toml
schema-version = "1"
id    = "payments-review"
title = "Payments Migration Review"

[[sections]]
id = "context"
title = "Context"

[[sections.items]]
path = "docs/research/payments-landscape.md"

[[sections]]
id = "proposal"
title = "Proposal"

[[sections.items]]
path = "docs/design/payments-migration.md"
```

---

## Worked scenario: payments migration review

Using this repository's actual pack, skill, and artifact shapes.

### Candidate artifacts

| Artifact | Producer | Metadata level |
|---|---|---|
| `docs/product/research/payments-landscape-survey.md` | `desk-research` (standard mode) | Level 1 — YAML frontmatter |
| `docs/product/intents/payments-migration.md` | `product-engineering` `frame-intent` | Level 1 |
| `docs/rfc/0091-payments-migration.md` | `governance-extras` `new-rfc` | **Level 0** — bold `**Status:** Accepted`, no frontmatter → sidecar |
| `docs/rfc/0093-payments-strangler.md` | `governance-extras` `new-rfc` | Level 0 → sidecar |
| `docs/rfc/0088-payments-migration-draft.md` | `governance-extras` `new-rfc` | Level 0, superseded |
| `docs/design/payments-migration/design.md` | `architect` `architect-design` | Level 0, contains Mermaid |
| `docs/adr/0044-ledger-boundary.md` | `governance-extras` `new-adr` | Level 0 → sidecar |
| `docs/adr/0045-dual-write-window.md` | `governance-extras` `new-adr` | Level 0 → sidecar |
| `docs/specs/payments-migration/spec.md` + `plan.md` | `core` `new-spec` | Level 0 |
| `notes/security-assessment-payments.md` | hand-written | none |
| `notes/vendor-comparison.md` | external workflow | none |

**Eight of eleven carry no YAML frontmatter.** That is not a contrived fixture — it
is what this repository actually looks like, and it is why Level 0 is the primary
path.

> **Phase labels.** Path A below uses selectors (**Phase 2**) and Path B an
> `extends` overlay (**Phase 3**). Under v1 they produce the *not-yet-implemented
> key* error, by design. The **v1 walkthrough is Path A0**, immediately below;
> the later paths show where the same recipe goes once the metadata and
> composition layers land.

### Path A0 — the v1 walkthrough, explicit paths only

`binders/payments-review.binder.toml` as printed in *Worked recipe*: every item an
explicit `path`, one `[[exclude]] path`, no `source-roots` needed for the explicit
references. Run:

```bash
python scripts/binder.py build binders/payments-review.binder.toml \\
  --root=/Users/dev/proj
```

Resolution: **12 nodes — 9 source, 2 editorial, 1 generated.** The nine source
artifacts are named by path; the two editorial nodes are the executive summary and
the `context` section's introduction; the generated node is the source inventory.
`0088` excluded by the explicit `[[exclude]]` rule with its reason recorded.
`notes/security-assessment-payments.md` is listed by path and resolves, because an
explicit path needs no `source-roots` entry (D33). No gaps, no ambiguity, nothing
deferred — this is the whole v1 feature set exercised end to end.

This is the same 12-node count the build summary in
[`resolution.md`](resolution.md), the sequence diagram in
[`editorial-model.md`](editorial-model.md), and the missing-dependency error in
[`zensical-adapter.md`](zensical-adapter.md) all print. The *Worked recipe*
in [`binder-recipe.md`](binder-recipe.md) is an abridged excerpt of this fixture
and says so.

### Path A — committed recipe with selectors (Phase 2)

`binders/architecture-review.binder.toml`, parameterized by `subject`. Run:

```bash
python scripts/binder.py build binders/architecture-review.binder.toml \
  --root=/Users/dev/proj --param=subject=payments-migration
```

Resolution: 9 nodes selected; `0088` excluded by `[[exclude]]`; `0093` not
selected (the committed recipe's `proposal` section takes the one `current` RFC);
`notes/*` absent because this recipe declares `source-roots = ["docs"]` and its
items are **selectors**, which scan only declared roots — an explicit `path` to a
`notes/` file would have resolved fine. The security-assessment gap is reported.

### Path B — dynamic overlay for a specific audience (Phase 3)

The overlay above adds the executive summary, forces **both** competing proposals
as required exact references, adds `notes` as a source root so the security
assessment resolves, and keeps the exclusion of `0088`.

Resolution: 13 nodes. Both proposals present and labelled. Superseded draft
excluded with a recorded reason. Security assessment now resolves. Rollback risk
emphasized by an editorial section introduction. One unreviewed editorial node
flagged in the summary.

### Staged project

```
.binder-work/payments-board-2026-08/c41d7e0a/stage/
├── zensical.toml                                   # generated entirely from the index
├── theme/
│   ├── main.html                                   # injects the vendored mermaid.min.js
│   └── assets/javascripts/mermaid.min.js           # vendored — Zensical does not bundle it
├── docs/
│   ├── index.md                                    # generated cover
│   ├── 001-executive-summary.md                    # editorial
│   ├── 002-part-evidence.md                        # generated part page
│   ├── 003-docs-product-research-payments-landscape-survey.md
│   ├── 004-docs-product-intents-payments-migration.md
│   ├── 005-notes-vendor-comparison.md
│   ├── 006-part-proposals.md
│   ├── 007-context-intro.md                        # editorial section intro
│   ├── 008-docs-rfc-0091-payments-migration.md
│   ├── 009-docs-rfc-0093-payments-strangler.md
│   ├── 010-docs-adr-0044-ledger-boundary.md
│   ├── 011-docs-adr-0045-dual-write-window.md
│   ├── 012-docs-design-payments-migration-design.md   # 3 mermaid diagrams
│   ├── 013-docs-specs-payments-migration-spec.md
│   ├── 014-notes-security-assessment-payments.md
│   ├── 900-source-inventory.md                     # generated appendix
│   └── assets/n008/ledger-topology.png             # copied, confined, rewritten
├── .cache/                                         # Zensical's
└── site/                                           # render output; published from here
```

`docs/` and `site/` are Zensical's default `docs_dir` and `site_dir`, and both are
resolved relative to `zensical.toml` (Z1d, Z1e) — which is why placing the config
in `stage/` keeps every byte the renderer writes inside the workspace.

### Final HTML information architecture

Cover (title, purpose, audience, subject, binder status) →
Executive summary *(marked editorial, unreviewed)* → **Part I Evidence** (survey,
intent, vendor comparison) → **Part II Proposals and decisions** (section intro,
Proposal A, Proposal B, ADR-0044, ADR-0045, the design with three diagrams, the
spec, the security assessment) → Appendix: source inventory and provenance.
Sidebar, search, previous/next, and per-page TOC throughout.

**Two parts, matching the two part pages in the staged tree above** —
`002-part-evidence.md` and `006-part-proposals.md`. An earlier version described a
third, *Architecture and delivery*, which no part page in the tree corresponded
to; the architecture and delivery chapters sit in Part II.

### The same mechanism in a clean directory

```
~/scratch/vendor-eval/
├── binder.toml
├── overview.md
├── option-a.md
├── option-b.md
└── recommendation.md
```

`binder.toml` lists four explicit paths in four sections. No Git, no `pack.toml`,
no `site.toml`, no frontmatter, no installed source packs. One command produces
`build/binders/vendor-eval/index.html` with the same navigation, search, and
theme. **This is the same code path** — the difference between it and the
thirteen-node board packet is entirely in the recipe.

---
