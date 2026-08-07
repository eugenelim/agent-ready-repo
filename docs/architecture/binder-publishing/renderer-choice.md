# Renderer choice — applied survey

> Discipline: applied (practitioner-pattern survey)

Resolves [`open-decisions.md`](open-decisions.md) D-B: is Quarto the right
renderer for a portable pack, given that the resolver already supplies the
document structure?

**Measured 2026-08-06** by installing each candidate into a clean virtualenv on
macOS/arm64. Sizes are stated as *download* and *on-disk over an empty-venv
baseline*, because those differ enough to change a conclusion.

## The measurements

| Candidate | Download | On disk, over baseline | Nature | Status |
|---|---:|---:|---|---|
| **Quarto** | 236 MB (macOS) · ~140 MB (Linux/Win) | — | external CLI, no pip library | stable 1.10.18 |
| **mkdocs-material** | ~9 MB wheel | **129 MB** (30 packages) | pure Python | stable 9.7.7 |
| **Zensical** | **12.2 MB wheel** | ~94 MB (11 packages) | compiled `abi3` extension + Python | **alpha 0.0.53** |
| **markdown-it-py** | 0.09 MB wheel | **~1 MB** (3 packages) | pure Python | stable 4.2.0 |

`[high]` — direct measurement, reproducible; `pip install` into a fresh venv,
`du` against an empty-venv baseline of 12 MB.

**Two corrections to my own first reading**, both material:

- I initially reported Zensical as "94 MB installed" and nearly recommended
  against it on that basis. The on-disk figure is inflated by
  **16,654 individual icon SVGs** in `templates/.icons` — block-allocation
  overhead, not bytes. The honest number a user pays is the **12.2 MB wheel**,
  which is **19× smaller than Quarto**. `[high]`
- mkdocs-material's ~9 MB wheel expands to **129 MB installed across 30
  packages** — the heaviest Python option, and close enough to Quarto's order of
  magnitude that "MkDocs is the light alternative" is false. `[high]`

## Why every documentation generator is heavy

All three site generators bundle a **design system** — icon sets, fonts,
compiled CSS/JS, search machinery. That is what you are buying, and it is most of
the weight. `[synthesis]`

**We already have the expensive part.** `binder-index.json` holds the resolved
sections, parts, order, labels, and pre-resolved cross-document links. The hard
problem of a static site generator — working out structure — is what the resolver
does. So a generator is being paid to re-derive navigation we computed, and then
constrained so it re-derives nothing else. `[inference]`

## Pressure-testing Zensical

It is genuinely the most forward-looking option, and the instinct behind
preferring it is sound — but three things must be weighed honestly.

**In its favour** `[high]`:

- Built by the Material for MkDocs team; repo created 2025-05-18, last pushed
  2026-08-04 — **actively developed**, 5,400 stars, MIT.
- **12.2 MB download**, 19× lighter than Quarto and by far the lightest of the
  three full generators.
- Pure-Python dependency tree otherwise (`click`, `jinja2`, `markdown`,
  `pygments`, `pymdown-extensions`, `pyyaml`, `deepmerge`, `tomli`) — all small,
  all boring, all already common.
- **12 platform wheels** including Windows, musl, and armv7 — better platform
  coverage than most compiled-extension projects, and it sidesteps the PEP 668
  and sdist-build problems that made Quarto's pip route fragile.

**Against it** `[high]` unless noted:

- **`Development Status :: 3 - Alpha`, version `0.0.53`.** Fifty-three releases in
  fifteen months, none of which has claimed 0.1. Committing a *published,
  versioned contract* to an alpha renderer means our stability guarantee is
  downstream of something that does not offer one.
- **It ships a compiled `zensical.abi3.so`** (7.7 MB). That is not disqualifying —
  the wheel coverage is good — but it means no pure-Python fallback on an
  unlisted platform, where Quarto at least has a tarball and `markdown-it-py`
  needs nothing.
- **A commercial tier exists** ("Zensical Spark", with pricing and billing on the
  project's own site). Open-core is a legitimate model and MIT is MIT, but a
  design that hard-depends on it should say the words "open-core risk" out loud
  rather than discover them later. `[moderate]` — the commercial surface is
  documented; how the OSS/commercial line will move is not.
- **1 open issue against 5,400 stars** is anomalous for a project of that
  visibility, and I could not establish why. `[uncertain]`

**The decisive point is not any of those.** Zensical is a *site generator* — it
wants to own navigation, and its configuration surface is the MkDocs lineage's
`nav`. We would be generating that config from our index, then constraining the
generator so it does not do anything else. Adopting it buys a theme and a search
index for 12 MB and an alpha dependency; it does not remove the adapter layer,
the staging layer, or the trust scanner, because those exist to control what
reaches *any* renderer.

## What we actually need

Given the index, the renderer's remaining job is small `[inference]`:

| Job | Cost |
|---|---|
| Markdown → HTML | The one real gap. `markdown-it-py`, ~1 MB installed, CommonMark-compliant, plugin-based |
| Sidebar, prev/next, per-page TOC | Generated from the index — templating, not derivation |
| Cross-document links | Already resolved (`links[].target-node`) |
| Figure numbering | Already derivable — the index knows every figure and its order |
| Client-side search | A JSON inverted index over headings and text, plus a small JS reader |
| Mermaid | One vendored `mermaid.min.js`. Q27 already forbids a CDN |
| Theme | One CSS file we own — needed regardless, since Q27 showed the stock Bootstrap theme fetches a typeface from Google |

**~1 MB of dependency, plus a vendored Mermaid bundle and roughly 600–900 lines we
maintain.**

## The spike — and why it reversed the recommendation

Run 2026-08-06 against `zensical==0.0.53`: scaffold a project, add a third page,
a portable ` ```mermaid ` fence with a `<br/>` label, a literal shortcode, and a
cross-document link; build; inspect the output. `[high]` — direct execution.

| Check | Result |
|---|---|
| Build | **0.82 s**, "No issues found" |
| Config format | **TOML**, with `nav = [...]` **fully explicit** |
| Mermaid | **Renders from the portable ` ```mermaid ` fence** — `pymdownx.superfences` with a `mermaid` custom fence is in the *default scaffold* |
| `<br/>` in a node label | Preserved |
| `{{< env HOME >}}` | **Passed through as literal text** — not interpreted |
| Sidebar nav · prev/next · per-page TOC | All present |
| Client-side search | `search.json`, 7 KB, offline |
| CDN references | Google Fonts, `unpkg` MathJax, `jsdelivr` twemoji — **all present by default** |

**Three of those change the design, not just the decision.**

1. **Mermaid needs no staging transformation.** Q5 — Quarto requiring
   `` ```{mermaid} `` executable-cell syntax — is what made staging mandatory and
   forced the fence transform, the label injection, the caption-binding protocol,
   and the `line-map`. Zensical reads the portable fence directly. That entire
   area of the design exists *because of Quarto*.
2. **The shortcode attack surface does not exist.** Q11 — `{{< env >}}`
   exfiltrating a secret with execution disabled — is a *Quarto* behaviour.
   Zensical passes the sequence through as text. The single most load-bearing
   security control in the design, and the `[policy] shortcodes` key, are both
   Quarto-specific.
3. **`nav` is fully explicit TOML.** This is precisely what we would generate from
   `binder-index.json` — the generator is *told* the structure rather than
   deriving it, which is the relationship invariant 3 wants.

**The CDN finding is symmetric, not disqualifying.** Zensical's defaults fetch
Google Fonts, MathJax, and twemoji at read time — the same class of problem as
Q27 found in Quarto's Bootstrap theme. Both need offline hardening; neither is
offline by default. This neutralises one of the arguments I had made *for* owning
the renderer ("we need our own CSS anyway"), because that is true either way.

## Recommendation — revised by the spike

**Adopt Zensical as the v1 renderer.** Keep the adapter seam.

I previously recommended owning the renderer, on the reasoning that a generator
would re-derive structure we already have. The spike showed the trade is better
than that argument allowed: for **12.2 MB** we get search, navigation, prev/next,
per-page TOC, and a maintained theme — and, more importantly, we **delete two of
the design's hardest areas**, because both existed only to work around Quarto.

Owning it remains viable (~1 MB, total control) but now costs 600–900 lines to
replace things Zensical does well, for a saving of 11 MB.

### The alpha risk, and why it is bounded

`Development Status :: 3 - Alpha` at `0.0.53` is real and I am not discounting
it. Two things bound it:

- **We depend on a narrow slice** — `nav`, the theme, `superfences`, and search.
  Not the plugin API, not the extension surface, not anything exotic.
- **Invariant 22 means swapping is one file.** The index is renderer-neutral by
  construction; a Zensical adapter and a Quarto adapter differ only in the staging
  module. This is exactly the reopening the Axis A / Axis B split was drawn for,
  and it worked.

**Mitigation:** pin the version, and add a gate that renders the fixture and
asserts the output contract — the same discipline that caught Q26 and Q27.

## Open-core and enterprise use

**Legally, MIT — and that is the whole answer for adoption.** `[high]`

- The `zensical` PyPI package carries `License :: OSI Approved :: MIT License`;
  the GitHub repository is MIT.
- MIT is permissive: no copyleft, no per-seat terms, no redistribution
  restriction, no obligation beyond preserving the licence text. An enterprise can
  vendor it, run it in CI, and ship its output commercially without a licence
  conversation.
- **We depend only on the MIT pip package.** "Zensical Spark" is a paid *service*
  tier (pricing, access management, billing) — a hosted product, orthogonal to
  building a static site locally.

**The real risk is feature availability, not licensing.** `[moderate]` The same
team runs Material for MkDocs on an MIT core plus an "Insiders" sponsorware
edition, where features ship to sponsors first and graduate to the OSS release
once funding goals are met. If Zensical follows that model — and the precedent
says it likely will — then a feature we want could land behind sponsorship for a
period. That is a *waiting* problem, not a *blocking* one: the MIT core keeps
working, and nothing we need today (nav, search, Mermaid, theme) is plausibly
retracted from it.

**What an enterprise should actually check:** that the pinned version is MIT (it
is), that the build runs offline once hardened (it can), and that no telemetry is
emitted — which I have **not** verified. Recorded as a known-unknown.

The reasoning is not that Zensical is bad — it is the best of the three
generators and the instinct to prefer it over dated alternatives is right. It is
that **all three solve a problem we already solved.** We would be adding a
19-MB-download alpha dependency, with a compiled extension and an open-core
question, to obtain navigation we compute ourselves and a theme we must override
anyway for Q27.

What we give up by owning it: pandoc-grade Markdown fidelity, and a free path to
PDF/EPUB. The first is the real loss; the second is a v1 non-goal.

What we gain: the entire dependency contract disappears — the install ladder,
consent tokens, digest verification, PEP 668 handling, the toolchain cache and its
lock, gate V4, and the 236 MB-per-CI-job cost. That is not a small simplification;
it is most of the machinery the last eight review rounds kept finding defects in.

**The seam stays open.** Because the index is renderer-neutral by construction
(invariant 22), a Zensical adapter — or a Quarto one for PDF — remains a later
addition rather than a later redesign. If Zensical reaches 1.0 and its theme is
worth more than our CSS file, adopting it touches one file.

## Known unknowns

- **Closed by the spike:** Mermaid, offline search, and `nav`-from-config all
  verified working. See *The spike* above.
- **Known-unknown:** whether Zensical emits telemetry, and whether a fully
  offline build (no CDN references at all) is reachable by configuration alone.
  Would be closed by: a hardened-config build with network egress blocked.
- **Known-unknown:** whether Zensical will adopt Material's Insiders model, and
  which features would sit behind it. Would be closed by: a published governance
  or funding statement.
- **Known-unknown:** how good a `markdown-it-py`-based renderer's output actually
  is against the multi-pack fixture. Would be closed by: a spike rendering the
  fixture and diffing against the Quarto output that already exists.
- **Known-unknown:** the anomalous 1-open-issue count. Would be closed by: the
  project's stated triage policy.
- **Unknowable:** where Zensical's OSS/commercial line will settle. The decision
  has not been made publicly, so no evidence can answer it today — which is
  itself the argument for not hard-depending on it at alpha.
