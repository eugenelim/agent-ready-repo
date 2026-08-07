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
required exact reference into a selector, and may not set `[policy] profile` less
strictly than its base.

### Mermaid normalization, worked — with the line map

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
13    A[Gateway] --> B[Ledger service]
14    B --> C[(Postgres)]
15  ```
````

Staged (`011-docs-design-payments-design.qmd`):

````markdown
 1  ---
 2  title: "Payments migration design"
 3  ---
 4
 5  The ledger boundary is shown below.
 6
 7  ```{mermaid}
 8  %%| label: fig-docs-design-payments-design-1
 9  flowchart LR
10    A[Gateway] --> B[Ledger service]
11    B --> C[(Postgres)]
12  ```
````

**This is the v1 output**: one injected `%%|` line, the deterministic label. Phase
2's caption adds a `%%| fig-cap:` line and one more breakpoint.

Emitted into `renderer-plan.json` (**not** the index — invariant 22):

```json
"line-map": [[1, 1], [9, 5], [11, 7], [12, 9]]
```

Reading it: the frontmatter rebuild (steps 1–2) shortens by 2; the duplicate-H1
drop (step 3) shortens by a further 2, so source 9 → staged 5; the fence
transform (step 4) is neutral at the fence line itself but the two injected
`%%|` line pushes the diagram body down by 1, so source 12 → staged 9. A single
scalar offset cannot express this — the deltas are 0, −4, −4, −3 across one file —
which is why `line-map` is an array.

Three security-relevant things happened. The `css:` key — a source-controlled
renderer-configuration channel — was **discarded with the rest of the
frontmatter**, not filtered out. The H1 was dropped because it duplicated the
chapter title. The fence became an executable diagram cell with a deterministic
label and the caption the recipe bound to ordinal 1 and verified against that
fence's content hash. **The source file on disk is byte-identical to before.**

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

Resolution: 11 nodes — the nine source artifacts named by path, one editorial
executive summary, one generated source inventory. `0088` excluded by the explicit
`[[exclude]]` rule with its reason recorded. `notes/security-assessment-payments.md`
is listed by path and resolves, because an explicit path needs no `source-roots`
entry (D33). No gaps, no ambiguity, nothing deferred — this is the whole v1
feature set exercised end to end.

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
├── _quarto.yml
├── binder.scss
├── index.qmd                                       # generated cover
├── 001-executive-summary.qmd                        # editorial
├── 002-part-evidence.qmd                            # generated part page
├── 003-docs-product-research-payments-landscape-survey.qmd
├── 004-docs-product-intents-payments-migration.qmd
├── 005-notes-vendor-comparison.qmd
├── 006-part-proposals.qmd
├── 007-context-intro.qmd                            # editorial section intro
├── 008-docs-rfc-0091-payments-migration.qmd
├── 009-docs-rfc-0093-payments-strangler.qmd
├── 010-docs-adr-0044-ledger-boundary.qmd
├── 011-docs-adr-0045-dual-write-window.qmd
├── 012-docs-design-payments-migration-design.qmd    # 3 mermaid diagrams
├── 013-docs-specs-payments-migration-spec.qmd
├── 014-notes-security-assessment-payments.qmd
├── 900-source-inventory.qmd                        # generated appendix
├── assets/n008/ledger-topology.png                 # copied, confined, rewritten (step 7b)
└── _output/
```

### Final HTML information architecture

Cover (title, purpose, audience, subject, binder status, build summary) →
Executive summary *(marked editorial, unreviewed)* → **Part I Evidence** (survey,
intent, vendor comparison) → **Part II Proposals and decisions** (section intro,
Proposal A, Proposal B, ADR-0044, ADR-0045) → **Part III Architecture and
delivery** (design with three rendered diagrams, spec, security assessment) →
Appendix: source inventory and provenance. Sidebar, search, previous/next, and
per-page TOC throughout.

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
