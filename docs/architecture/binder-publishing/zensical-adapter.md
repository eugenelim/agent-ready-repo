# Zensical adapter

> The v1 renderer adapter. Replaces the Quarto adapter per
> [`open-decisions.md`](open-decisions.md) D-B; the reasoning and the spike
> results are in [`renderer-choice.md`](renderer-choice.md).

## What the adapter is given, and what it may do

Its only inputs are `binder-index.json` and the pack's own theme assets. It is
given no source root, no recipe, and no discovery function, and every source read
goes through a single `read_node_source(node)` accessor that **rejects any path
not enumerated in the index** (invariant 3). It writes no field of the index
(invariant 22); anything it must invent goes in `renderer-plan.json`.

## Why this adapter is small

The Quarto adapter was large because Quarto needed working around. Three of its
areas do not exist here:

| Quarto needed | Zensical |
|---|---|
| ` ```mermaid ` → `` ```{mermaid} `` transformation, label injection, caption binding, `line-map` | **Reads the portable fence directly.** No transformation, so no line-count change, so no line map |
| Shortcode neutralization (Q11) | **Does not interpret `{{< … >}}`.** Passes it through as text |
| A reader-toggle layer that broke diagrams (Q26) | Not applicable |

What remains is genuinely a *staging* step: copy, rewrite links, write config.

## Staging

1. **Create the staging directory** fresh — `<workspace>/<binder-id>/<content-key>/stage/`. A pre-existing one is removed first, so nothing can survive into a build.
2. **Re-verify** each source against the `sha256` recorded at resolve time. A mismatch means the source changed between `resolve` and `build`: exit 6, naming the path. (The trust scan itself already ran, at the end of discovery — see [`security-profile.md`](security-profile.md).)
3. **Copy each selected source into `docs/`** as `NNN-<slug>.md`, applying the per-file transformation below.
4. **Generate the cover** as `docs/index.md` from the index's binder identity.
5. **Generate part pages and section introductions** where the recipe declares them.
6. **Generate appendices** — the source inventory, when opted in.
7. **Write `zensical.toml`** entirely from the index. Nothing from any source.
8. **Copy theme assets** from the pack's `assets/theme/`.
9. **Copy approved local assets**, re-confined at copy time, `follow_symlinks=False`, extension and magic-byte checked, size-capped.
10. **Write `binder-stamp.json`** into the output for `check --published`.
11. **Invoke** `zensical build` with a list-form argv and an allowlist-constructed environment.
12. **Map diagnostics** back to source paths.
13. **Publish** near-atomically.

## Per-file transformation

Four steps, down from eight. **Only steps 1–2 change line counts**, and they change
it by a fixed amount per file — so the `line-map` breakpoint array the Quarto
adapter needed collapses to a single integer offset.

| Step | Operation | Δ |
|---|---|---|
| 1 | **Discard source frontmatter entirely** — not filtered, discarded | Δ |
| 2 | **Emit a fresh frontmatter block** containing only `title`, written through the YAML-safe scalar emitter | Δ |
| 3 | **Heading normalization** — drop a duplicate H1, or shift headings down one so the chapter title is the only H1. Clamps at H6, warning on collision | Δ¹ |
| 4 | **Rewrite internal links and asset references** from the index's pre-resolved `links` and `assets`. In-binder targets become relative page links; out-of-binder relative targets become plain text with a footnote naming the original path. Assets are rewritten to `assets/<node-id>/<basename>`, hash-disambiguated on collision | — |

¹ Heading normalization changes line count only when it drops a duplicate H1 — a
fixed −1 or −2 per file, known before the write. Combined with steps 1–2 the total
is a single integer, recorded as `line-offset` in `renderer-plan.json`.

**Mermaid fences are untouched.** They pass through as authored, which is what
makes the source-is-never-modified invariant cheap here rather than elaborate.

## Generated `zensical.toml`

Written entirely from the index. The `nav` array is the resolved structure — the
generator is *told* the order, never asked to derive it, which is the relationship
invariant 3 wants.

```toml
[project]
site_name = "Payments Migration Review"
site_url  = "/"

nav = [
  { "Cover" = "index.md" },
  { "Executive summary" = "001-executive-summary.md" },
  { "Part I — Evidence" = [
      { "Payments landscape survey" = "003-docs-product-research-payments-landscape-survey.md" },
      { "Vendor comparison" = "004-notes-vendor-comparison.md" },
  ]},
  { "Part II — Proposal and decisions" = [
      { "RFC-0091: Payments migration" = "006-docs-rfc-0091-payments-migration.md" },
      { "ADR-0044: Ledger boundary" = "007-docs-adr-0044-ledger-boundary.md" },
  ]},
  { "Source inventory and provenance" = "900-source-inventory.md" },
]

[project.theme]
custom_dir = "theme"
features = [
  "navigation.sections",
  "navigation.footer",     # prev/next
  "navigation.top",
  "search.highlight",
  "content.code.copy",
]

# Offline hardening — see below. Not defaults.
[project.theme.font]
text = false
code = false

[project.markdown_extensions]
admonition = {}
attr_list = {}
def_list = {}
footnotes = {}
toc = { permalink = true }
"pymdownx.highlight" = { anchor_linenums = true }
"pymdownx.superfences" = { custom_fences = [
  { name = "mermaid", class = "mermaid", format = "pymdownx.superfences.fence_code_format" },
]}
```

**The extension set is a closed allowlist**, not the scaffold default. Three of the
scaffold's extensions are deliberately absent: `pymdownx.arithmatex` (pulls MathJax
from `unpkg`), `pymdownx.emoji` (pulls twemoji SVGs from `jsdelivr`), and
`pymdownx.snippets` (reads arbitrary files from disk — a path-confinement bypass by
design). An adapter option outside the allowlist is a validation error.

## Offline hardening — required, not optional

The spike found Zensical's defaults fetch **Google Fonts, unpkg MathJax, and
jsdelivr twemoji** at read time. That is the same class of finding as Q27 was for
Quarto's Bootstrap theme: a binder sent to an air-gapped review board or a
privacy-sensitive client cannot phone out.

Three mechanical measures:

- `[project.theme.font] text = false, code = false` — suppresses the Google Fonts
  request; the theme's CSS supplies a system-font stack instead.
- `arithmatex` and `emoji` excluded from the extension allowlist, removing the
  MathJax and twemoji CDN references.
- **Mermaid is vendored**, not fetched — `mermaid.min.js` ships in the pack's theme
  assets and is copied into the staged theme.

**Gate V2b asserts zero `https://` references anywhere in the built output, CSS
included.** It runs against the real emitted `zensical.toml`, because testing a
hand-written config would verify something the pack never emits — the lesson V1
taught when it produced Q26.

## Renderer plan

`renderer-plan.json` — adapter-owned, no stability guarantee, never published:

```json
{
  "plan-version": "1",
  "renderer": "zensical",
  "index-sha256": "e91b…",
  "nodes": {
    "n008": {
      "staged-path": "docs/006-docs-rfc-0091-payments-migration.md",
      "line-offset": -4,
      "heading-rule": "dropped-duplicate-h1",
      "assets": { "img/ledger-topology.png": "assets/n008/ledger-topology.png" },
      "links": { "../adr/0044-ledger-boundary.md": "007-docs-adr-0044-ledger-boundary.md" }
    }
  }
}
```

`index-sha256` pins the plan to the index it came from, so a stale plan is detected
rather than silently misapplied.

## Diagnostics

Zensical reports against staged files. The adapter rewrites each
`<staged>:<line>` to `<source-path>:<line - line-offset>`, annotated with the
binder section and node label:

```
ERROR  Mermaid diagram failed to parse
  source   docs/design/payments/design.md:118  (section "architecture", node n009)
  staged   docs/012-docs-design-payments-design.md:114
  detail   Parse error on line 3: expected 'graph', 'flowchart', …
```

## Version pinning

`zensical` is pinned to an exact version in the pack's runtime dependency
declaration, and **the version is part of the content-key**, so an upgrade does not
silently reuse a workspace staged by a different renderer build.

The pin matters more than it would for a stable dependency: Zensical is
`Development Status :: 3 - Alpha` at `0.0.53`. The mitigation is the pin plus the
gate — the same discipline that caught Q26 and Q27 — and the fact that swapping
renderers touches this file and nothing else.

## What a future Quarto adapter would need

Retained deliberately: [`verified-findings.md`](verified-findings.md) carries
Q1–Q28, all of it hard-won by direct execution. A PDF or EPUB path would go
through Quarto, and Q5, Q10a, Q17, Q18, Q26, and Q28 are exactly what that adapter
would be built against. The findings are evidence, not history.
