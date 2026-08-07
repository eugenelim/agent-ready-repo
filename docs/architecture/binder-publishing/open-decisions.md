# Open decisions — read before implementing

> Two shape-level questions are open, both raised after the eight review rounds.
> **The rest of this tree is written against the pre-reshape answers**, so where it
> disagrees with this file, this file is where the thinking currently is.

---

## D-A — Collapse the trust surface instead of routing it

**Status: decided; propagation in progress.** D-B strengthens it further — with
Zensical there is no shortcode surface, so `[policy] shortcodes` goes too.

Five review rounds each found a *different* unrouted input surface — `--profile`,
`$BINDER_POLICY_FILE`, `--quarto`, `--replace-foreign-dir`, `publication-dir`,
`--out`, `--root`, `--from-index`, `--force-unlock`. The response each time was to
route one more surface through the authority model.

**That was the wrong response.** A router that must wrap nine surfaces is evidence
the surface is too large, not that the router is incomplete. The design should not
support every combination; a caller who wants an arbitrary renderer configuration
is outside scope and should drive the renderer directly.

### What v1 offers

| Surface | Verdict |
|---|---|
| `--root` | **Keep.** It is what decouples "where the script lives" from "what it operates on", and it is the reason the contract survives seven adapter layouts. |
| `[policy] shortcodes` | **Keep.** Both values are safe; it exists because documents *about* Quarto are a real corpus. |
| `--keep-stage`, `--no-wait`, `--yes`, `--allow-unknown-fields` | **Keep.** None can reach trust or a path. |
| `--profile` / `trusted` profile | **Cut from v1.** Strict-only. |
| `binder-policy.toml` (all tiers) | **Cut from v1** — with no relaxation to grant, there is nothing for a policy file to say. |
| `--quarto=PATH`, `$BINDER_QUARTO` | **Cut.** Detection uses `PATH` and the managed cache. |
| `--out=PATH` | **Cut.** `resolve` writes to the workspace; CI reads it there. |
| `--replace-foreign-dir` | **Cut.** Refuse to replace a directory that is not ours; the caller can empty it themselves. |
| `--force-unlock` | **Cut.** `clean` handles stale state. |
| `--from-index` | **Cut.** `build` always resolves. Invariant 21 means identical inputs give an identical index, so "the thing I approved" is still what gets built. |
| Absolute `publication-dir` | **Cut.** Confined beneath the content root, no exception. |

### What this deletes

The entire authority lattice — origin classes, the four policy tiers, grants,
`trusted-paths`, the trusted-profile `_quarto.yml` variant, the
mtime-newer-than-process-start mitigation, and roughly half of
[`security-profile.md`](security-profile.md)'s conditional rows. The trust model
becomes one sentence: **everything outside the installed pack is untrusted, the
profile is strict, and there is no way to relax it.**

### What it costs

A team whose repository legitimately contains raw HTML in prose cannot publish
those files without editing or excluding them. That is a real cost and it is the
reason `trusted` was designed in the first place. It is accepted for v1 because:
the corpus gate will tell us empirically how often it bites; `<br/>` in Mermaid
labels — the case that actually appeared — is verified to work under strict
(Q28); and a profile added later on evidence is a better profile than one designed
against a hypothetical.

**`trust-model.md` is currently written against the four-tier model and must be
cut down to match this decision.**

---

## D-B — Is Quarto the right renderer at all?

**Status: RESOLVED 2026-08-06 — Zensical, by spike.** See
[`renderer-choice.md`](renderer-choice.md). The spike reversed the paper
recommendation: Zensical reads portable ` ```mermaid ` fences directly and does
not interpret `{{< … >}}`, which deletes the Mermaid staging transformation *and*
the shortcode attack surface — both of which existed only to work around Quarto.
The analysis below is retained as the reasoning that led there.

Quarto is a **236 MB external CLI** (140 MB on Linux/Windows). For a pack whose
selling point is portability, that is the single heaviest thing in the design, and
essentially all of the remaining machinery exists to manage it:
[`dependency-contract.md`](dependency-contract.md) in full, the install ladder and
its consent tokens, digest verification, PEP 668 handling, the toolchain cache and
its lock, gate V4, and the 236 MB-per-job CI cost.

### The argument that has changed

When Quarto was selected, the reasoning was that sidebar navigation, search,
prev/next, per-page TOC, cross-references, figure numbering, and a responsive
accessible theme are individually modest and collectively a product — so buying
them was better than building them.

**The two-artifact split undermines that argument.** The hard part of a static site
generator is working out structure; `binder-index.json` *already contains* the
resolved sections, parts, order, labels, and pre-resolved cross-document links. We
are paying 236 MB for a renderer to re-derive navigation we computed ourselves,
and then constraining it heavily so it does not re-derive anything else.

What a renderer must actually do, given the index:

| Job | Cost without Quarto |
|---|---|
| Markdown → HTML | A Markdown parser. The one genuine gap — stdlib has none. `markdown-it-py` or `markdown` is a small pip dependency (~1–2 MB). |
| Sidebar, prev/next, per-page TOC | Generated from the index. Roughly 100 lines of templating. |
| Cross-document links | Already resolved — `links[].target-node`. |
| Figure numbering | Already derivable — the index knows every figure and its order. |
| Client-side search | A JSON inverted index over headings and text, plus ~50 lines of JS. |
| Mermaid | One vendored `mermaid.min.js` (~1–3 MB). Q27 already forbids CDN. |
| Theme | One CSS file we own — which we need regardless, since Q27 showed the stock Bootstrap theme fetches a typeface from Google. |

Estimated footprint: **~5 MB against 236 MB**, with no external CLI, no install
ladder, no toolchain cache, no PEP 668 problem, and no 236 MB CI download.

What is genuinely lost: pandoc-grade Markdown fidelity, Quarto's citation
handling, and a free path to PDF/EPUB later. The first is the one that matters;
the others are v1 non-goals already.

### The three options

1. **Keep Quarto as the only renderer.** Verified working (V1, V1b, V1c, V3 all
   passed). Highest fidelity. Heaviest by two orders of magnitude, and the
   dependency machinery is most of the remaining design.
2. **Own a small renderer; drop Quarto from v1.** Deletes the dependency contract,
   the install ladder, the toolchain cache and lock, V4, and the CI cost. Adds one
   small pip dependency and roughly 600–900 lines we maintain. The adapter seam
   stays, so Quarto can return as an optional adapter for anyone who wants PDF.
3. **Own a small renderer as the default; ship the Quarto adapter as opt-in.**
   Both, with the light one as the default path. Most capability, most code.

**Recommendation: option 2 for v1, with the adapter seam kept open.** The
architecture already isolated this as Axis B precisely so it could be reopened
without touching the index, the schema, the resolver, or the scanner — and the
reason to buy Quarto weakened once the resolver started supplying the structure.
Option 3 is where this probably lands eventually, but shipping both in v1
contradicts "the smallest coherent portable capability."

**If option 2 or 3 is chosen,** [`zensical-adapter.md`](zensical-adapter.md) and
[`dependency-contract.md`](dependency-contract.md) are rewritten or removed, and
the verified Quarto findings in [`verified-findings.md`](verified-findings.md)
remain valuable — they are what a future Quarto adapter would be built against,
and Q26/Q27 in particular are hard-won.

**Nothing else in the tree changes**, which is the strongest available evidence
that the Axis A / Axis B split was drawn in the right place.
