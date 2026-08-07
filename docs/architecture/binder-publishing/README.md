# Binder publishing — architecture

> Design for `binder-publishing`: a portable pack that compiles selected Markdown
> artifacts into a coherent, reader-oriented static HTML binder.
>
> **Status:** Draft — pre-RFC. Eight cold-review rounds ran against the previous
> single-file draft; this tree is the holistic re-shape that followed. See
> [`review-history.md`](review-history.md) for what changed and why.

## Why this is a tree and not a document

The previous draft was one 4,800-line file. Eight review rounds found real defects
every time, and a recurring class of them was **"X is specified two or three
incompatible ways"** — because patching one section reliably broke another that
repeated the same fact. The split is not cosmetic: each file below owns one
concern, so a change to the trust model touches one file and a reader checking a
contract reads one file.

The same review history produced two other shape-level diagnoses, and both are
fixed here rather than patched:

1. **The trust surface was too large to route.** Five separate rounds each found
   *a different* flag, environment variable, or file that had not been routed
   through the authority lattice. The first response was a better router; the right
   response is fewer inputs. D-A cuts the `trusted` profile, the policy file, and
   six flags — which deletes the lattice rather than perfecting it, leaving
   [`trust-model.md`](trust-model.md) at one sentence.
2. **The renderer was chosen on paper and never spiked.** D-B replaced Quarto's
   236 MB external CLI with a 12.2 MB pip package after a spike showed Zensical
   reads portable Mermaid fences directly and does not interpret `{{< … >}}` —
   deleting two entire control areas that existed only to work around Quarto.
3. **The strict profile was a denylist validated against no corpus.** It rejected
   `<br/>` in Mermaid labels (45 occurrences in the design doc itself), `<|--` in
   class diagrams, and `{{<` in any document about Quarto. Rules are now
   corpus-tested by construction — see the corpus gate in
   [`security-profile.md`](security-profile.md).

## Read in this order

> **⚠ The tree is mid-propagation.** Decisions D-A (collapse the trust surface)
> and D-B (Zensical replaces Quarto) reached the files marked ✓. Files marked
> ⚠ still describe the pre-decision shape — a Quarto adapter, a `trusted`
> profile, a policy file. **`open-decisions.md` is authoritative** wherever they
> disagree. Do not write a specification from a ⚠ file.

| File | Status | What it settles |
|---|---|---|
| [`open-decisions.md`](open-decisions.md) | **authority** | **Read first.** Two shape-level questions raised after the review rounds: collapsing the trust surface, and whether Quarto is the right renderer at all. The rest of the tree is written against the pre-reshape answers. |
| [`renderer-choice.md`](renderer-choice.md) | evidence | **Measured** applied survey resolving D-B: Quarto vs mkdocs-material vs Zensical vs owning it. |
| [`outline-and-templates.md`](outline-and-templates.md) | ✓ new | `binder outline` — drafting a recipe from a folder — and how packs ship reusable recipe templates. |
| [`overview.md`](overview.md) | ⚠ not propagated | Problem, goals and non-goals, product boundary, the alternatives and why this shape won |
| [`trust-model.md`](trust-model.md) | ✓ D-A | **One sentence, and why it got that small.** Everything outside the pack is untrusted, the profile is strict, and nothing can relax it |
| [`security-profile.md`](security-profile.md) | ✓ D-A/D-B | What the scanner rejects, how it detects it, and the corpus it is tested against |
| [`binder-recipe.md`](binder-recipe.md) | ⚠ not propagated | `binder.toml` — the authored contract, its complete surface, and how it evolves |
| [`resolved-index.md`](resolved-index.md) | ⚠ not propagated | `binder-index.json` and `renderer-plan.json` — the two output contracts and the invariant that separates them |
| [`resolution.md`](resolution.md) | ⚠ not propagated | Discovery, identity, ordering, conflicts, diagnostics, explainability |
| [`zensical-adapter.md`](zensical-adapter.md) | ✓ D-B | Staging, the per-file transformation, the generated `zensical.toml`, and the required offline hardening |
| [`dependency-contract.md`](dependency-contract.md) | ✓ D-B | One pinned pip package. Reduced from 211 lines to a manifest block and an install command. |
| [`runtime.md`](runtime.md) | ⚠ not propagated | Storage layout, locks, concurrency, publication replacement |
| [`invocation.md`](invocation.md) | ⚠ not propagated | The command contract, exit codes, and entry-point resolution |
| [`verified-findings.md`](verified-findings.md) | Quarto evidence | **Evidence.** Every Quarto claim with source and confidence; the gates, including which have been run |
| [`rollout.md`](rollout.md) | ⚠ not propagated | Phases, testing strategy, CI wiring, unresolved questions |
| [`decisions.md`](decisions.md) | ⚠ not propagated | The decision log |
| [`review-history.md`](review-history.md) | historical | Non-normative record of the eight review rounds |

## The one-paragraph version

Markdown artifacts are produced by many workflows, each writing where its own
convention puts it — and **the source hierarchy is not the reader hierarchy**. A
`binder.toml` recipe declares a reading order over artifacts that already exist; a
resolver turns it into a deterministic `binder-index.json`; a renderer adapter —
Zensical as of D-B — renders that index to a static HTML binder. **The resolved index, not the
renderer, is the interoperability contract** — which is what lets another pack
participate with `tomllib` and nothing else, and what makes a second renderer a
later addition rather than a later redesign.

## Load-bearing invariants

The full list is in [`overview.md`](overview.md#architectural-invariants). Three
carry most of the weight:

- **21 — `binder-index.json` is byte-reproducible for identical inputs.** No
  timestamps, run IDs, host names, or absolute paths. This makes ceremonial fields
  structurally impossible rather than merely discouraged.
- **22 — `binder build` writes no field of `binder-index.json`.** Anything an
  adapter must invent goes in that adapter's own plan file. Renderer neutrality
  becomes checkable rather than aspirational.
- **23 — every input is classified by origin before it is trusted.** New in this
  re-shape; it is what stops the authority model needing a new rule per flag.
