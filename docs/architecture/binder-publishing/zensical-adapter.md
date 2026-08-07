# Zensical adapter

> The v1 renderer adapter, and the whole of the dependency contract. The renderer
> decision and its evidence are
> **[ADR-0073](../../adr/0073-zensical-as-the-v1-binder-renderer.md)**; **every
> assertion in this file is gated by Z1–Z4 in
> [`verified-findings.md`](verified-findings.md)**.
>
> **Three claims in the first version of this file were wrong, and the Z-gates
> found them:** `zensical.__version__` does not exist (Z1c), the font-suppression
> form emitted a request for a typeface named `False` (Z4a), and Mermaid is **not**
> bundled — the theme fetches it from unpkg at read time (Z3b). All three are
> corrected below.

## What the adapter is given, and what it may do

Its only inputs are `binder-index.json` and the pack's own theme assets. It is
given **no recipe and no discovery function**, and although the index carries
`content-root`, every source read goes through a single `read_node_source(node)`
accessor that **rejects any path not enumerated in the index** (invariant 3). It
writes no field of the index (invariant 22); anything it must invent goes in
`renderer-plan.json`.

> Stated that way deliberately. "It is given no source root" would be the stronger
> claim and it would be false — staging must read caller-owned sources, and the
> index does carry the root. The mechanical guarantee is the accessor, not a
> withheld variable. See [`overview.md`](overview.md#proposed-component-architecture).

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

Four steps, down from eight. **Only steps 1–2 change line counts**, and they change
it by a fixed amount per file — so the `line-map` breakpoint array the Quarto
adapter needed collapses to a single integer offset.

| Step | Operation | Δ |
|---|---|---|
| 1 | **Discard source frontmatter entirely** — not filtered, discarded | Δ |
| 2 | **Emit a fresh frontmatter block** containing only `title`, written through the YAML-safe scalar emitter | Δ |
| 3 | **Heading normalization** — drop a duplicate H1, or shift headings down one so the chapter title is the only H1. Clamps at H6, warning on collision | Δ¹ |
| 4 | **Rewrite internal links and asset references** from the index's pre-resolved `links` and `assets`. In-binder targets become relative `.md` page links; out-of-binder relative targets become plain text with a footnote naming the original path. Assets are rewritten to `assets/<node-id>/<basename>`, hash-disambiguated on collision | — |

¹ Heading normalization changes line count only when it drops a duplicate H1 — a
fixed −1 or −2 per file, known before the write. Combined with steps 1–2 the total
is a single integer, recorded as `line-offset` in `renderer-plan.json`.

**Link rewriting targets `.md`, not a URL.** Z2b's fixture confirmed Zensical
rewrites a `[text](006-rfc-0091-payments-migration.md)` link to the pretty URL
`../006-rfc-0091-payments-migration/` itself. The adapter emits the staged
filename and lets the renderer do the URL shape — which is the same
told-not-asked relationship the `nav` has.

**Mermaid fences are untouched.** They pass through as authored (Z3a), which is
what makes the source-is-never-modified invariant cheap here rather than
elaborate.

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

**What is verified and what is not.** Z3c confirms the guard exists in the bundle's
source; Z3d confirms the script lands in `<head>` before it. That a real browser
then renders the diagram from the vendored copy with egress blocked is **Z6, not
yet run** — it needs a headless browser the design does not otherwise require. The
fallback if the guard misbehaves is benign: the reader sees the diagram's own
Mermaid source as preformatted text, not a blank space.

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
| `clamped-source-lines` | source line numbers where a heading shift hit the H6 ceiling and was clamped with a warning. **The accessibility check reads this** — the clamp is a transformation record, so invariant 22 keeps it out of the index |
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

The whole of it. **This file used to have a 211-line sibling** describing an
install ladder, consent tokens, digest verification, PEP 668 handling, a toolchain
cache with its own lock, and a platform gate — all of it machinery for managing a
236 MB external CLI. ADR-0073 deleted the CLI, so it deleted the machinery.

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

## What a future Quarto adapter would need

Retained deliberately: [`verified-findings.md`](verified-findings.md) carries
Q1–Q28, all of it hard-won by direct execution. A PDF or EPUB path would go
through Quarto, and Q5, Q10a, Q17, Q18, Q26, and Q28 are exactly what that adapter
would be built against. The findings are evidence, not history.
