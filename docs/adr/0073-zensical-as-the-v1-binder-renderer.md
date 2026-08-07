# ADR-0073: Zensical is the v1 binder renderer — chosen for foundation continuity, not footprint

- **Status:** Accepted
- **Date:** 2026-08-06
- **Decision-makers:** eugenelim
- **Consulted:** design-reviewer (rounds 1–10)
- **Supersedes:** none
- **Related:** `docs/architecture/binder-publishing/` (the design tree this decision serves)

## Decision summary

- **Decision:** the `binder-publishing` pack renders through **Zensical, pinned
  exactly at `0.0.53`**, as an ordinary Tier-2 pip dependency. The renderer sits
  behind an adapter seam; `binder-index.json` stays renderer-neutral, so a second
  adapter is an addition rather than a redesign.
- **Because:** on capability and footprint Zensical and mkdocs-material are
  interchangeable — measurement and a shared fixture both say so. What separates
  them is that **mkdocs-material's foundation is being withdrawn.** MkDocs 2.0
  removes the plugin system, passes navigation to themes as pre-rendered HTML
  rather than structured data, ships no migration path, and specifies no license.
  Zensical is the same team's rewrite that removes MkDocs from the picture. The
  choice is a trajectory, not a version.
- **Applies to:** the `binder-publishing` pack only. No other pack takes a
  renderer dependency, and nothing in the catalogue's core depends on this.

## Context

The pack compiles a `binder.toml` recipe into a deterministic
`binder-index.json`, then renders that index to a static HTML binder. Because the
resolver already produces the sections, parts, order, labels, and pre-resolved
cross-document links, the renderer's remaining job is narrow: Markdown → HTML, a
sidebar and prev/next from a *given* navigation tree, a client-side search index,
a theme, and Mermaid.

An earlier iteration selected **Quarto** on documented behaviour. That decision
was ratified on paper and never spiked, and it drove most of the design's
complexity: a 236 MB external CLI, an install ladder with consent tokens and
digest verification, PEP 668 handling, a toolchain cache with its own lock, a
mandatory Mermaid fence transformation with a line-map, and a shortcode scanner.

Two facts, both established by running things rather than reading documentation,
made that untenable and reopened the choice.

## Evidence

**Footprint, measured 2026-08-06** into clean virtualenvs on macOS/arm64:

| Candidate | Wheel | Packages | Bytes on disk | Nature | Status |
|---|---:|---:|---:|---|---|
| Quarto 1.10.18 | 236 MB (macOS) | — | — | external CLI, no pip library | stable |
| mkdocs-material 9.7.7 | **8.9 MB** | 30 | 84.2 MB | pure-Python wheel | stable |
| Zensical 0.0.53 | 12.2 MB | 11 | 46.6 MB | compiled `abi3` + Python | **alpha** |
| markdown-it-py 4.2.0 | 0.09 MB | 3 | ~1 MB | pure Python | stable |

An earlier reading of these numbers reported Zensical at "94 MB installed" and
mkdocs-material at "129 MB", then corrected only the first for icon-SVG
block-allocation overhead. mkdocs-material ships 14,344 icon SVGs totalling
9.3 MB of real bytes and needed the same correction. **Corrected, its wheel is
smaller than Zensical's.** The footprint argument does not select between them.

**Capability, from one shared fixture** — a multi-chapter binder with a nested
navigation tree, a `custom_dir` theme, generated frontmatter, a portable
` ```mermaid ` fence with a `<br/>` node label, a class diagram using `<|--`, a
literal `{{< env … >}}`, an admonition, and a cross-document link:

| Behaviour the design depends on | Quarto | mkdocs-material | Zensical |
|---|---|---|---|
| Portable ` ```mermaid ` fence read directly | ✗ requires `` ```{mermaid} `` | ✓ | ✓ |
| `{{< env … >}}` inert (no shortcode surface) | ✗ interprets it | ✓ | ✓ |
| `<br/>` and `<|--` preserved in labels | ✓ | ✓ | ✓ |
| Extension allowlist *replaces* defaults | n/a | ✓ | ✓ |
| Nested nav renders as a titled group | ✓ | ✓ | ✓ |
| Local offline search index | ✓ | ✓ | ✓ |
| Remote fonts suppressible by config | ✓ | ✓ | ✓ |
| Mermaid bundled (not CDN-fetched) | ✓ | ✗ unpkg | ✗ unpkg |

**Quarto is eliminated on the top two rows.** They are what forced the staging
transformation and the shortcode scanner — two of the design's hardest areas,
both of which existed only to work around it.

**mkdocs-material and Zensical are indistinguishable.** Every row matches,
including the Mermaid CDN fetch, which is inherited theme behaviour rather than a
Zensical gap.

**Foundation.** `mkdocs build` prints a warning from its own maintainers: MkDocs
2.0 will remove the plugin system, rewrite the theming system so navigation
reaches themes as pre-rendered HTML rather than structured data, provide no
migration path, adopt a closed contribution model, and ship **currently
unlicensed**. The design's offline hardening depends on `custom_dir` theme
overrides — exactly the surface named.

That warning comes from an interested party — the Material team also build
Zensical — so it was checked against disinterested ones. It holds:
[DDEV](https://github.com/ddev/ddev/issues/8216) filed *"Upcoming mkdocs 2.0 will
break everything"*; [Argo CD](https://github.com/argoproj/argo-cd/issues/27039)
opened *"Migrate from mkdocs to a migrated alternative"*; and two independent
continuation forks exist —
[ProperDocs](https://github.com/orgs/ProperDocs/discussions/33) and
[mkdocs-ng](https://github.com/mkdocs-ng/mkdocs-material). Large projects with no
stake in Zensical are migrating off.

## Options considered

**A — keep Quarto.** Highest fidelity, stable, and a free path to PDF/EPUB later.
Rejected: 236 MB external CLI, and it is the direct cause of the fence
transformation, the shortcode attack surface, the install ladder, the toolchain
cache and its lock, and a 236 MB-per-CI-job cost. Retained as the adapter a future
PDF path would use; its verified findings are kept for that purpose.

**B — mkdocs-material 9.7.7.** Stable today, capability-identical, smaller wheel.
Rejected on foundation: its substrate breaks at MkDocs 2.0 in exactly the surface
this design depends on, its maintainers say so, and unrelated projects are acting
on it. Choosing it means choosing a migration we already know is coming.

**C — Zensical 0.0.53. SELECTED.** Same theme lineage, same behaviours, half the
disk footprint, a third of the dependencies, and it is where the Material team is
going. Costs an alpha version number.

**D — own a small renderer on `markdown-it-py`.** ~1 MB and total control of the
security surface. Rejected for v1: 600–900 lines to replace things Zensical does
well, and it does not avoid the two costs people assume it does — a vendored
Mermaid bundle and a hand-written theme are needed either way. Remains the
fallback if C fails.

## Why an alpha dependency is acceptable here

Stated so it can be re-checked rather than taken on faith:

- **The mature half is inherited.** Theme, templates, search, icon sets, and
  accessibility work are Material's, proven over years. What is new is the build
  engine and the config layer — and that is precisely where verification found
  problems. A missing navigation target being silent is an engine gap; the
  mis-emitted font key is inherited behaviour mkdocs-material shares.
- **The exposure is four features:** the navigation tree, the theme,
  `pymdownx.superfences`, and search. Not the plugin API, not the extension
  surface, nothing exotic.
- **The exit is one file, demonstrated rather than asserted.** The Quarto →
  Zensical swap moved the adapter, its plan file, the dependency contract, and the
  staged layout. The index, the schema, the resolver, and the trust scanner did
  not change.
- **Being wrong is cheap.** mkdocs-material 9.x keeps working; option D remains
  open.

**Licensing is MIT** on both the package and the repository. "Zensical Spark" is a
paid hosted *service* tier, orthogonal to building a site locally. The residual is
feature availability if the team adopts Material's Insiders model — a waiting
problem, not a blocking one, since nothing v1 needs is plausibly retracted from
the MIT core.

## Consequences

**Deleted outright:** the Mermaid fence transformation and its line-map, the
shortcode attack surface and the control that governed it, the install ladder,
consent tokens, digest verification, PEP 668 handling, the toolchain cache and its
lock, and the 236 MB-per-CI-job provisioning cost. **One of three locks goes with
it** — the toolchain-cache lock — leaving the workspace and publication locks and
**no globally mutable resource** in the design at all.

**Newly required:** the renderer must be pinned exactly and verified by
`importlib.metadata.version` — `zensical.__version__` does not exist, and the
attribute that does exist is a function. Mermaid must be **vendored**, delivered
through a `custom_dir` template override rather than `extra_javascript`, because
the theme otherwise fetches it from unpkg at read time. Chapter numbering and
appendix lettering become the compiler's job, since Zensical numbers nothing.
Offline hardening is mandatory, not optional.

**Verification is a standing obligation, not a one-off.** Direct execution
falsified three specified controls in a single session — the version probe, the
font-suppression key, and the assumption that Mermaid ships bundled. All three had
been inferred from the shape of a configuration surface rather than run. The
renderer gates are therefore CI-required on every PR, which a 12.2 MB wheel makes
affordable in a way a 236 MB toolchain did not.

## Revisit as Zensical evolves

**This decision is explicitly provisional on an alpha dependency, and the revisit
is scheduled rather than event-driven.** A pin at `0.0.53` is a snapshot of a
project shipping roughly three releases a month; treating the choice as settled
until something breaks would mean discovering upstream changes through failures
rather than through review.

**Standing cadence — re-run Z1–Z4 against every version bump before it lands.**
They are CI-required, so a bump that changes the invocation contract, the config
surface, Mermaid handling, or the offline hardening fails loudly. That is the
mechanism; the pin is what makes it a decision rather than a drift.

**Review the decision itself at each of these**, not just the gates:

| Trigger | What to reconsider |
|---|---|
| **Zensical reaches 1.0** | Whether the alpha caveat, the exact pin, and this ADR's provisional framing still apply. A stable release is the moment to relax the pin to a compatible range if the gates have been quiet |
| **A minor release changes any of the four surfaces we depend on** — `nav`, the theme/`custom_dir` contract, `superfences`, search | Whether the adapter absorbs it or whether the seam is being stretched |
| **Zensical bundles Mermaid**, or offers a first-class offline mode | Drop the vendored `mermaid.min.js` and the `custom_dir` injection — that is the single largest piece of adapter code the renderer choice costs us |
| **It gains chapter numbering or cross-reference syntax** | D44's compiler-emitted ordinals and the Phase-2 caption plan both become cheaper, and possibly unnecessary |
| **MkDocs 2.0 ships and its reception is known** | The core premise of this ADR. If the ecosystem absorbs it without the breakage its critics predict, mkdocs-material becomes viable again and this decision was insurance rather than necessity — worth recording either way |

**Reverse the decision if:**

- A build makes outbound requests that configuration cannot suppress.
- No release lands for six months, or the project is archived.
- Navigation, search, or the theme move behind a sponsorship tier.
- The gates start failing on routine bumps often enough that tracking upstream
  costs more than owning a renderer would.

**Not a revisit trigger:** a PDF or EPUB goal. That path goes through Quarto as a
*second* adapter, and the retained Quarto findings exist for it. It does not
replace this one.
