# Zensical adapter

> The v1 renderer adapter, and the whole of the dependency contract. The renderer
> decision and its evidence are
> **[ADR-0073](../../adr/0073-zensical-as-the-v1-binder-renderer.md)**; **every
> assertion in this file is gated by Z1–Z6 in
> [`verified-findings.md`](verified-findings.md)**.
>
> **Claims in earlier versions of this file were wrong, and the Z-gates found
> them:** `zensical.__version__` does not exist (Z1c), the font-suppression form
> emitted a request for a typeface named `False` (Z4a), Mermaid is **not** bundled —
> the theme fetches it from unpkg at read time (Z3b) — and the diagram accessible
> name was emitted onto an element the theme bundle throws away (Z6d). All are
> corrected below.

## What the adapter is given, and what it may do

Its only inputs are `binder-index.json` and the pack's own theme assets. It is
given **no recipe and no discovery function**, and although the index carries
`content-root`, every source read goes through a single `read_node_source(node)`
accessor that **rejects any path not enumerated in the index** (invariant 8). It
writes no field of the index (invariant 16); anything it must invent goes in
`renderer-plan.json`.

> Stated that way deliberately. "It is given no source root" would be the stronger
> claim and it would be false — staging must read caller-owned sources, and the
> index does carry the root. The mechanical guarantee is the accessor, not a
> withheld variable. See [`overview.md`](overview.md#component-architecture).

## Adapter staging boundary

The adapter stages sources, rewrites links, emits configuration, reads portable
Mermaid fences without rewriting their bodies, and treats `{{< … >}}` as text.

## Staging

1. **Create the staging directory** fresh — `<workspace>/<binder-id>/<content-key>/stage/`. A pre-existing one is removed first, so nothing can survive into a build.
2. **Re-verify** each source against the `sha256` recorded at resolve time. A mismatch means the source changed between `resolve` and `build`: exit 6, naming the path. (The trust scan itself already ran, at the end of discovery — see [`security-profile.md`](security-profile.md).)
3. **Copy each selected source into `stage/docs/`** as `NNN-<slug>.md`, applying the per-file transformation below.
4. **Generate the cover** as `stage/docs/index.md` from the index's binder identity.
5. **Generate part pages and section introductions** where the recipe declares them.
6. **Generate appendices** — the source inventory, when opted in.
7. **Write `stage/zensical.toml`** entirely from the index. Nothing from any source.
8. **Copy theme assets** from the pack's `assets/theme/` into `stage/theme/` — including `main.html` and the vendored `mermaid.min.js`. See *Vendoring Mermaid*.
9. **Copy approved local assets**, re-confined at copy time, `follow_symlinks=False`, extension and magic-byte checked, size-capped.
10. **Assert every `nav` target exists on disk.** A missing target is an adapter error (exit 7) naming the node and the expected staged path. **Zensical will not catch this** — Z2g found that a `nav` entry naming a non-existent file produces no warning even under `--strict`, and renders a working-looking dead sidebar link.
11. **Invoke** `zensical build` (below).
12. **Map diagnostics** back to source paths.
13. **Write `binder-stamp.json`** into `stage/site/` for `check --published`.
14. **Publish** near-atomically from `stage/site/`.

The stamp is written **after** the render, not before: `site/` is Zensical's
output directory and it is rebuilt by the build, so a stamp written earlier would
not survive.

## Per-file transformation

Five steps, down from eight. **Only steps 1–3 change line counts**, and they change
it by a fixed amount per file — so the `line-map` breakpoint array the Quarto
adapter needed collapses to a single integer offset. Steps 4 and 5 rewrite *within*
a line and never add or remove one, which is the property that keeps the offset a
scalar.

| Step | Operation | Δ |
|---|---|---|
| 1 | **Discard source frontmatter entirely** — not filtered, discarded | Δ |
| 2 | **Emit a fresh frontmatter block** containing only `title`, written through the YAML-safe scalar emitter | Δ |
| 3 | **Heading normalization** — drop a duplicate H1, or shift headings down one so the chapter title is the only H1. Clamps at H6, warning on collision | Δ¹ |
| 4 | **Rewrite internal links and asset references** from the index's pre-resolved `links` and `assets`. In-binder targets become relative `.md` page links; out-of-binder relative targets become plain text with a footnote naming the original path. Assets are rewritten to `assets/<node-id>/<basename>`, hash-disambiguated on collision | — |
| 5 | **Annotate each Mermaid fence's opening delimiter** with `data-a11y-name` (and `data-a11y-desc` once there is a source for one), allowlist-reduced, derived from values the compiler owns — in v1 that is `Diagram <chapter-ordinal>.<n>` (D46). A same-line rewrite of ` ```mermaid ` to ` ```{.mermaid …} ` — **the fence body is not read and not touched** | — |

¹ Heading normalization changes line count only when it drops a duplicate H1 — a
fixed −1 or −2 per file, known before the write. Combined with steps 1–2 the total
is a single integer, recorded as `line-offset` in `renderer-plan.json`.

**Link rewriting targets `.md`, not a URL.** Z2b's fixture confirmed Zensical
rewrites a `[text](006-rfc-0091-payments-migration.md)` link to the pretty URL
`../006-rfc-0091-payments-migration/` itself. The adapter emits the staged
filename and lets the renderer do the URL shape — which is the same
told-not-asked relationship the `nav` has.

**Mermaid fence *bodies* are untouched.** Every line between the delimiters passes
through as authored (Z3a) — the adapter neither parses nor rewrites diagram source
— which is what makes the source-is-never-modified invariant cheap here rather than
elaborate. **The opening delimiter is rewritten**, to carry the accessibility
attributes D46 needs (step 5), and that is a same-line edit: no line is added, so
the scalar `line-offset` is unaffected and the scanner still sees the author's own
bytes in the body.

**Numbering is compiler-emitted, and presentational** (D44). Zensical numbers
nothing — no chapter numbers, no appendix lettering, no `.unnumbered` equivalent
(Z2h) — so the compiler supplies the ordinal. **It never enters a title string.**

```markdown
# Payments landscape survey {: data-ordinal="3" }
```
```css
[data-ordinal]::before { content: attr(data-ordinal) ". "; }
```

`attr_list` is already in the extension allowlist, so the heading side costs
nothing new.

**The sidebar uses the same attribute, not a CSS counter.** An earlier draft
numbered the nav with `counter-increment` — which is wrong, and the failure is
silent: a lettered appendix emits `data-ordinal="A"` on its heading while a
counter renders a number, so the page says "Appendix A" and the sidebar says "17".
Any compiler-side skip diverges the same way. **Two ordinals from two sources
cannot be kept in step by construction, and the design claimed they could.**

So the adapter overrides `partials/nav-item.html` in its `custom_dir` and emits
the ordinal onto the nav item from `renderer-plan.json`'s `emitted-ordinal` — the
one value both surfaces read:

```jinja
{% set ordinal = binder_ordinals.get(nav_item.file.src_uri) %}
<a class="md-nav__link"{% if ordinal %} data-ordinal="{{ ordinal }}"{% endif %} …>
```

One source, one rendering rule, and the cover and part pages carry no attribute so
they are skipped without a selector that has to know about them.

**Baking the number into the title was the obvious route and is wrong.** It would
put "3." in the browser tab, in `search.json` as part of the indexed title, and in
anything a reader copy-pastes — and inserting one chapter would rewrite every
later chapter's published title. Keeping it in an attribute means the number is
style, the text stays clean, and the sidebar and the page heading cannot disagree.

`emitted-ordinal` in `renderer-plan.json` records what was emitted, so a
diagnostic can name "chapter 3" without re-deriving it.

## Generated `zensical.toml`

Written entirely from the index. The `nav` array is the resolved structure — the
generator is *told* the order, never asked to derive it, which is the relationship
invariant 8 wants.

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

# Offline hardening — a SCALAR false on the whole `font` key. See below; the
# per-face form specified in an earlier draft is verified wrong (Z4a).
font = false

features = [
  "navigation.sections",
  "navigation.footer",     # prev/next
  "navigation.top",
  "search.highlight",
  "content.code.copy",
]

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

**The extension set is a closed allowlist, and Z2b established that it genuinely
replaces the scaffold set rather than merging with it** — the open question this
file previously left unanswered. With the block above emitted, `pymdownx.tilde`,
`caret`, `details`, `emoji`, `keys`, and `arithmatex` are all inert and their
syntax renders as literal text.

That is what makes the exclusions real rather than shadowed:

| Excluded | Why | Status |
|---|---|---|
| `pymdownx.arithmatex` | pulls MathJax from `unpkg` | scaffold default; **removed** |
| `pymdownx.emoji` | pulls twemoji SVGs from `jsdelivr` | scaffold default; **removed** |
| `pymdownx.snippets` | reads arbitrary files from disk — a path-confinement bypass by design | **commented out in the scaffold already** (Z2f), so excluding it is a precaution, not a removal |

Quoted dotted keys (`"pymdownx.superfences"`) are what the adapter emits, because
the scaffold's unquoted `pymdownx.superfences = { … }` is a TOML *dotted key*
building a nested table. Both reach the same extension (Z2c); one of them says so.
An adapter option outside the allowlist is a validation error.

**Where the two allowlisted `[renderers.zensical]` options land**, because a
recipe key with no emission point is the silently-ignored key D15 forbids:

| Option | Emitted as |
|---|---|
| `toc-depth` | `toc = { permalink = true, toc_depth = <n> }` in the extension block |
| `mermaid-theme` | a `mermaid.initialize({ theme: … })` call in the theme's `main.html`, beside the vendored bundle — the renderer has no config key for it |

Two options is the whole surface. If a third is proposed, it needs an emission
point named here before it reaches the allowlist.

## Offline hardening — required, not optional

Zensical's defaults fetch **Google Fonts, unpkg MathJax, jsdelivr twemoji, and
unpkg Mermaid** at read time. That is the same class of finding as Q27 was for
Quarto's Bootstrap theme: a binder sent to an air-gapped review board or a
privacy-sensitive client cannot phone out.

Three mechanical measures, all now verified:

- **`[project.theme] font = false`** — a scalar `false` on the whole `font` key,
  which is what `base.html` guards on (`{% if config.theme.font != false %}`).
  Verified to remove both the `fonts.googleapis.com` stylesheet and the
  `fonts.gstatic.com` preconnect (Z4b). The theme's CSS supplies a system-font
  stack instead.

  > **The form specified in the first draft of this file was wrong.**
  > `[project.theme.font] text = false, code = false` does not suppress anything —
  > it emits a request for a typeface literally named `False`
  > (`family=False:300,300i,…`). Z4a caught it. It is the Q26 failure mode
  > repeated: a control inferred from the shape of a configuration surface rather
  > than from running it.

- `arithmatex` and `emoji` excluded from the extension allowlist (Z2b), which
  removes the MathJax and twemoji references outright.

- **Mermaid is vendored** — see below. This is not optional and it does not
  disappear under Zensical.

### Vendoring Mermaid — the mechanism, because it is the only control

**Zensical does not bundle Mermaid.** Z3b found `https://unpkg.com/mermaid@11/dist/mermaid.min.js`
inside the theme bundle, fetched from the reader's browser the moment a `.mermaid`
element mounts. A binder with one diagram phones out to a third-party CDN. The
vendored `mermaid.min.js` the design had hoped to delete stays.

Z3c found the mechanism that makes vendoring work, in the bundle's own source:

```js
typeof mermaid == "undefined" || mermaid instanceof Element
  ? fetch("https://unpkg.com/mermaid@11/dist/mermaid.min.js")
  : /* already present — no request */
```

So defining a global `mermaid` before the bundle runs suppresses the fetch
entirely. **The delivery route is `custom_dir`, not `extra_javascript`**, because
Z3d found `extra_javascript` is emitted *after* the bundle — an execution-order
race. The pack's theme ships:

```
assets/theme/
├── main.html                # {% extends "base.html" %}
└── assets/javascripts/mermaid.min.js
```

```jinja
{% extends "base.html" %}
{% block extrahead %}
  <script src="{{ 'assets/javascripts/mermaid.min.js' | url }}"></script>
{% endblock %}
```

`extrahead` renders inside `<head>`, ahead of the bundle — verified (Z2d, Z3d).

**Z6 ran this in a browser, and the mechanism works.** Two diagrams rendered from
the vendored copy with egress blocked and **zero remote requests of any kind**
(Z6a). One detail worth stating, because a reader checking the vendored file would
otherwise conclude the opposite: mermaid's distribution *opens* by assigning into
an esbuild namespace, but its **last line is
`globalThis["mermaid"] = globalThis.__esbuild_esm_mermaid_nm["mermaid"].default`**
— so a plain `<script src>` does define the global the guard tests (Z6b), and
`extrahead` puts it in `<head>` while the theme bundle loads from `<body>` (Z6c).
The benign fallback is confirmed rather than hoped: with the bundle unreachable the
reader sees the diagram's own Mermaid source as preformatted text (Z6k).

**A cost the run measured.** The vendored file is copied verbatim into
`site/assets/javascripts/`, merging with Zensical's own asset directory, and adds
**3.5 MB to every published binder** (Z6l) — the price of offline diagrams, stated
here rather than discovered by an adopter.

**And a risk it exposed.** The bundle asks for the floating `mermaid@11` tag, so
what gets vendored is whatever that resolved to at vendoring time — 11.16.1 during
this run (Z6m). The suppression mechanism is a property of the esbuild distribution
rather than of a patch version, so this is not fragile, but **the pack vendors a
pinned version with a recorded digest**, for the same reason `zensical` itself is
pinned exactly.

### Accessible diagram naming

The theme replaces the staged `<pre>`. Accessibility metadata must therefore reach
Mermaid before mounting and be asserted on the rendered SVG, not on the `<pre>`.

**The mechanism is two halves that meet in the browser, and it is verified (D46).**
The compiler emits the name and description as `attr_list` attributes on the
fence's **opening delimiter**, and the theme lifts them into the Mermaid source
before the bundle mounts the diagram — so Mermaid itself generates the
`<title>`/`<desc>`, inside the shadow SVG, where nothing can strip them.

Compiler side — note this changes the fence's opening line and **not a single line
count**. This is the v1 emission; `data-a11y-desc` joins it when `figures[]` gives it
a source (below):

````markdown
```{.mermaid data-a11y-name="Diagram 3.1"}
flowchart TD
    A[Client] --> B[API gateway]
```
````

Theme side, in `main.html` beside the vendored bundle — **stated as a contract, not
as code**, because the implementation is theme-internal:

> The theme prepends `accTitle:` and `accDescr:` lines, derived from the fence's
> allowlisted `data-a11y-*` attributes, into the fence's Mermaid source **before the
> bundle mounts it**. The step is idempotent, and its failure mode is a missing name,
> never a missing diagram.

Verified with a `MutationObserver` registered in `<head>`, which sees each
`pre.mermaid` as the parser inserts it and therefore always precedes the mount —
measured with **no `DOMContentLoaded` fallback present**, so the result is
attributable to the observer alone, and on a sixty-edge fence as well as a two-line
one (Z6j). The spec carries the implementation.

Measured with the diagram rendered and egress blocked: `role='graphics-document'`
carrying **both** `name='Diagram 3.1 — ledger write path (RFC-0091)'` and
`description='Client calls the API gateway, …'`, with real `<title>` and `<desc>`
elements inside the closed shadow root, and zero remote requests (Z6f, Z6i). Four
properties earn it the decision:

- **It names the graphic, not a box around it.** The accessible name lands on the
  `<svg>` itself — and the long description will, once Phase 2 gives `accDescr` a
  source — which is what a text alternative for non-text content has to do.
- **It adds no lines.** The attributes ride on the fence's existing opening
  delimiter, so *only steps 1–3 change line counts* stays true and the single
  integer `line-offset` survives.
- **The fence body is untouched in the staged file.** The `accTitle:`/`accDescr:`
  lines exist only in the reader's DOM, so *the body passes through as authored*
  (Z3a) holds, and the trust scanner still sees exactly the bytes the author wrote.
- **It needs no new extension.** `attr_list` is already allowlisted for
  `data-ordinal` (D44).

**What the name actually is in v1, because the index has no field for one.**
`resolved-index.md` is explicit that **v1 emits no `figures` key at all** — ordinal,
caption and `fence-sha256` arrive with captions in Phase 2. So the only name the
compiler can derive in v1 is one it owns outright: **`Diagram <chapter-ordinal>.<n>`**,
where the chapter ordinal is `emitted-ordinal` from `renderer-plan.json` (D44) and
`n` counts fences in document order as step 5 walks them. No new index field, so
invariant 16 is untouched.

That is a real accessible name and a weak one: it identifies and distinguishes a
diagram, and it describes nothing. **`accDescr` has no v1 source at all** and is
therefore not emitted in v1. Both improve when `figures[]` lands — a caption becomes
the name, and a description becomes `accDescr` — and D46's mechanism does not change
when they do, which is the point of specifying the mechanism separately from the
copy.

> **Stated because the alternative was a decision that ships as a no-op.** An
> earlier draft of D46 said the name comes "from index metadata", which in v1 means
> from nothing — so every diagram would have taken the no-name branch and the Phase 1
> static check would have asserted a property no build could produce. A mechanism
> whose input does not exist yet is not a mechanism.

**Emitted values are escaped for HTML and rejected for two Mermaid constructs, and
both halves are measured.** Z6h found an unescaped `attr_list` value containing `"`
**terminates the attribute**, turning the remainder into markup — a label of
`Diagram & "3.1" <script>x</script>` put a live `<script>` in the published page.
HTML-escaping closes that completely and preserves the value exactly, accents and
CJK included.

What escaping cannot cover is that **the value's sink is Mermaid source, not HTML**:
the theme lifts it into an `accTitle:` line, so Mermaid evaluates it. Z6i measured
`%%{init:{"theme":"dark"}}%%` being **consumed as a directive** — the construct the
rule table rejects in authored fence bodies, reaching Mermaid through a channel the
scanner never inspects — and an embedded newline destroying the diagram outright. So
emission **rejects** a value containing `%%{` or a newline rather than stripping it:
in a compiler-owned string either is a bug, not input.

> **An allowlist was specified here first, and it was the wrong control.** Reducing
> to `[A-Za-z0-9 …]` would mangle `Réseau : l'architecture 漢字` — which escaping
> round-trips character for character — silently, in the one kind of string whose
> whole purpose is to be read aloud. See [`security-profile.md`](security-profile.md)
> control 3.

The same rule binds every `attr_list` value this adapter emits, `data-ordinal`
included.

**When no name is derivable, the attributes are omitted and the diagram is
unnamed** — the same reasoning as the `<img alt>` rule in
[`rollout.md`](rollout.md#accessibility-smoke-checks): a fabricated description is
worse than an honest absence. An omitted attribute is recorded in diagnostics; it
is not a build failure, because a diagram whose only available label is its own
node text has nothing for the compiler to add.

**Two rejected routes, both of which work.** *Injecting `accTitle:` into the staged
fence body* produces an identical result and is simpler — one place instead of two —
but writes into the body, which forfeits the property that makes the scanner's job
and the `line-offset` cheap. *A `<figure role="group" aria-label>` wrapper with a
`<figcaption>`* was measured naming a region correctly, and was the first
replacement drafted — but it names a container rather than the graphic, has no
`accDescr` equivalent, needs the same string in two places where they can drift, and
**inserts lines around every diagram**, which is what disqualified it: the
single-integer `line-offset` is the reason this adapter has no `line-map` at all.
If a future requirement wants a *visible* caption, the wrapper returns as an
addition to D46 rather than a replacement for it, and the offset cost has to be paid
then.

**The theme directory is a publication surface.** Non-template files in
`custom_dir` are copied verbatim into the output root (Z2d), so only pack-owned
assets may go there. Nothing caller-owned is ever staged into `stage/theme/`.

**Gate Z4 asserts zero remote *subresource* references in the built output** — no
`src=`, no stylesheet or preconnect `href=`, no `@import`, no `url()` resolving
off-host. It does **not** assert zero `https://` strings: Z4d found that form
unsatisfiable, because the output legitimately carries a `zensical.org`
attribution anchor and two Font Awesome licence-comment URLs in the CSS, none of
which issues a request. Asserting the unsatisfiable version would have produced a
gate that fails forever and is therefore disabled — which is worse than no gate.
It runs against the real emitted `zensical.toml`, because testing a hand-written
config verifies something the pack never emits — the lesson V1 taught when it
produced Q26, and the lesson Z4a taught again.

## The invocation

```python
[sys.executable, "-m", "zensical", "build",
 "-f", str(stage / "zensical.toml"),
 "--strict"]
```

A constructed list, never a shell string, with an allowlist-built environment
(see [`security-profile.md`](security-profile.md)). Four things are load-bearing
and all four are gated:

- **`-f/--config-file` is the only path input.** `zensical build` takes no
  positional directory (Z1a), so there is exactly one place a path enters and it
  is one the adapter wrote.
- **`--strict` is required.** Without it a build that emits warnings — including
  dead links — still exits 0 (Z1b). Verified: `--strict` with issues exits **1**,
  clean exits **0**, no `--strict` with issues exits **0**. A compiler that
  reported success on a warned build would publish a binder with broken
  navigation.
- **Output and cache are config-file-relative, not CWD-relative** (Z1e). So
  `stage/zensical.toml` produces `stage/site/` and `stage/.cache/`, both inside
  the workspace and inside the write set. `.cache/` is Zensical's, not ours; it is
  removed with the staging directory.
- **`site_dir` and `docs_dir` default to `site` and `docs`**, are configurable,
  and Zensical itself refuses either resolving outside the project root or the two
  being equal (Z1d). The adapter emits neither key and takes the defaults.

## Renderer plan

`renderer-plan.json` — adapter-owned, no stability guarantee, never published.
**This is the canonical specification**; [`resolved-index.md`](resolved-index.md)
describes the boundary and points here.

```json
{
  "plan-version": "1",
  "renderer": "zensical",
  "index-sha256": "e91b…",
  "nodes": {
    "n008": {
      "staged-path": "docs/008-docs-rfc-0091-payments-migration.md",
      "line-offset": -4,
      "heading-rule": "dropped-duplicate-h1",
      "clamped-source-lines": [],
      "emitted-ordinal": "8",
      "a11y": [
        { "fence": 1, "name": "Diagram 8.1", "desc": null, "omitted": false },
        { "fence": 2, "name": null,          "desc": null, "omitted": true  }
      ],
      "assets": { "img/ledger-topology.png": "assets/n008/ledger-topology.png" },
      "links": { "../adr/0044-ledger-boundary.md": "011-docs-adr-0044-ledger-boundary.md" }
    }
  }
}
```

| Field | Meaning |
|---|---|
| `staged-path` | workspace-relative path of the staged file, under `stage/` |
| `line-offset` | single integer; add it to a source line to get the staged line |
| `heading-rule` | which normalization ran: `none`, `dropped-duplicate-h1`, or `shifted-down` |
| `clamped-source-lines` | source line numbers where a heading shift hit the H6 ceiling and was clamped with a warning. **The accessibility check reads this** — the clamp is a transformation record, so invariant 16 keeps it out of the index |
| `a11y` | one entry per Mermaid fence in document order: the `data-a11y-name` and `data-a11y-desc` values emitted (D46), or `omitted: true` where no name was derivable. **The accessibility smoke check reads this** rather than asserting bare presence, so an honestly-unnamed diagram is not a build failure and a *silently* unnamed one still is. `desc` is `null` throughout v1 — there is no source for it until `figures[]` ships |
| `emitted-ordinal` | the chapter number or appendix letter the adapter emitted **as the `data-ordinal` attribute** (D44), because Z2h established the renderer numbers nothing. **Never written into the title text or the nav label.** `null` for an unnumbered chapter |
| `assets` | source-relative asset reference → staged asset path |
| `links` | source-relative link target → staged filename |

`index-sha256` pins the plan to the index it came from, so a stale plan is detected
rather than silently misapplied. `renderer` names the adapter that wrote it, so a
plan left by a different adapter is recognised rather than misread.

## Diagnostics

Zensical reports against staged files in `<staged-file>.md:LINE:COL` form (Z1f) —
exactly the anchor the offset mapping needs. The adapter **strips ANSI SGR
sequences first**: Z1f found `NO_COLOR=1` is not honoured, so the output arrives
coloured whether or not a terminal is attached. It then rewrites each
`<staged>:<line>` to `<source-path>:<line - line-offset>`, annotated with the
binder section and node label:

```
ERROR  Mermaid diagram failed to parse
  source   docs/design/payments/design.md:118  (section "architecture", node n009)
  staged   docs/012-docs-design-payments-design.md:114
  detail   Parse error on line 3: expected 'graph', 'flowchart', …
```

## The dependency contract

The runtime dependency contract is:

```toml
[[pack.runtime-dependencies]]
ecosystem = "pypi"
package   = "zensical"
version   = "==0.0.53"           # exact pin; alpha upstream
optional  = false                # required to render; see note
skills    = ["publish-binder"]
install   = "python -m pip install zensical==0.0.53"
note      = "12.2 MB wheel. Required only by `build`. `outline`, `templates`, `resolve`, `explain`, `inventory` and `check --published` all work without it. Never installed silently."
```

**This block is the single source for the manifest entry**; `editorial-model.md`'s
`pack.toml` quotes it. Note the qualifier on `check`: plain `check` *is* the
renderer doctor, so it needs the renderer to say anything useful. It is
`check --published`, the CI staleness gate, that is renderer-free.

**Install is Tier 2 with no deviation** — `author-a-skill.md` § *What counts as a
dependency* settles it directly: *"`pip`/`uv` ship with a Python install, so a
pip-based Tier-2 install is low-risk."* The skill detects, asks, installs on
consent, and re-verifies. It declines to install when `CI` is set — a guard
against an accidental install, **not** a control against a hostile pipeline, which
could unset the variable.

**Python floor: 3.11** (`tomllib`), checked as `binder.py`'s first action, exiting
**11** — not 2, which means *renderer not installed* and would send a Python-3.10
user to `pip install zensical`.

**No Python dependencies of our own.** `binder.py` is standard library only.
Zensical brings `click`, `jinja2`, `markdown`, `pygments`, `pymdown-extensions`,
`pyyaml`, `deepmerge`, and `tomli` — all small, all common — and ships platform
wheels across 12 targets including Windows, musl, and armv7, so there is no source
build on any supported platform.

| Situation | Behaviour |
|---|---|
| Offline, present | Full function — **subject to the offline hardening above**, without which the *output* fetches fonts and scripts at read time |
| Offline, absent | `outline`, `templates`, `resolve`, `explain`, `inventory`, `check --published` all work. `build` exits 2 with the install command and attempts nothing |
| Restricted network | The install fails cleanly naming the unreachable index; `pip`'s own error surfaces verbatim, and no `--trusted-host` or certificate relaxation is ever offered |
| CI | `pip install zensical==0.0.53` as an ordinary pipeline step |

## Version pinning and the version probe

`zensical` is pinned to an exact version, and the running version is recorded in
`run.json` so `clean --stale` can report a tree staged by a different renderer
build.

**The version is deliberately *not* part of the content-key.** An earlier draft
put it there, to stop an upgrade reusing a workspace staged by a different
renderer. But `stage/` is deleted and rebuilt on every run, so there was nothing
to reuse — and `resolve` runs with no renderer installed and must be able to
compute its own output path. See [`runtime.md`](runtime.md).

**The probe is `importlib.metadata.version("zensical")`.** Z1c found that
`zensical.__version__` — which an earlier version of this file specified — **does
not exist**, and that the module *does* expose `zensical.version`, a built-in
*function*. A probe reaching for the attribute that is there would compare a pin
against `<built-in function version>` and never match; one reaching for
`__version__` raises `AttributeError`. Both are avoided by asking the package
metadata, which is what `pip` actually recorded.

Detection is `importlib.util.find_spec("zensical")` for presence, then the
metadata call for the version — neither imports the compiled extension, so a
missing renderer is exit 2 rather than an import traceback.

The pin matters more than it would for a stable dependency: Zensical is
`Development Status :: 3 - Alpha` at `0.0.53`. The mitigation is the pin plus the
Z-gates — the same discipline that caught Q26 and Q27, and that caught three
errors in this file — and the fact that swapping renderers touches this file and
nothing else.

## Future Quarto adapter (not v1)

Not v1 work. A PDF or EPUB adapter using Quarto must implement the constraints in
[`verified-findings.md`](verified-findings.md), including fence transformation,
shortcode neutralization, reader-toggle behavior, numbering, and label handling.
