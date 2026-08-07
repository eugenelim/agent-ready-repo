# Binder publishing — architecture

> Design for `binder-publishing`: a portable pack that compiles selected Markdown
> artifacts into a coherent, reader-oriented static HTML binder.
>
> **Status:** Draft — pre-RFC. Ten cold-review rounds ran; the tree is internally
> consistent and a specification can be written from any file in it.
> [`history.md`](history.md) records what changed and why.

## The one-paragraph version

Markdown artifacts are produced by many workflows, each writing where its own
convention puts it — and **the source hierarchy is not the reader hierarchy**. A
`binder.toml` recipe declares a reading order over artifacts that already exist; a
resolver turns it into a deterministic `binder-index.json`; a Zensical adapter
renders that index to a static HTML binder. **The resolved index, not the
renderer, is the interoperability contract** — which is what lets another pack
participate with `tomllib` and nothing else, and what makes a second renderer a
later addition rather than a later redesign.

## Read in this order

| File | What it settles |
|---|---|
| [`overview.md`](overview.md) | **Start here.** Problem, goals and non-goals, product boundary, charter fit, the architecture alternatives, and the component view |
| [`binder-recipe.md`](binder-recipe.md) | `binder.toml` — the authored contract, its complete surface, and how it evolves |
| [`resolved-index.md`](resolved-index.md) | `binder-index.json`, `renderer-plan.json`, and `binder-stamp.json` — what each holds and why they are three files |
| [`resolution.md`](resolution.md) | Discovery, identity, ordering, conflicts, diagnostics, explainability |
| [`security-profile.md`](security-profile.md) | **The trust model in one sentence**, what the scanner rejects, how it detects it, and the corpus that proves the rules right |
| [`zensical-adapter.md`](zensical-adapter.md) | Staging, the per-file transformation, the generated `zensical.toml`, the invocation, the offline hardening, and the dependency contract |
| [`invocation.md`](invocation.md) | The complete verb table, the closed flag surface, the six cut flags, exit codes, entry-point resolution |
| [`runtime.md`](runtime.md) | Storage layout, two locks, concurrency, publication replacement |
| [`outline-and-templates.md`](outline-and-templates.md) | `outline`, the producer-copies template seam, and `recipe write` |
| [`editorial-model.md`](editorial-model.md) | Pack and skill shape, `pack.toml`, the chief-editor procedure, the three content classes |
| [`examples.md`](examples.md) | Worked recipes, the staged tree, and an end-to-end scenario |
| [`rollout.md`](rollout.md) | Phases, testing strategy, CI wiring, unresolved questions |
| [`verified-findings.md`](verified-findings.md) | **Evidence.** Z1–Z4 (Zensical, executed) are the live gates; Q1–Q28 (Quarto) are retained for a future PDF adapter |
| [`decisions.md`](decisions.md) | The decision log. **D39–D45 are the post-review authority** |
| [`history.md`](history.md) | Non-normative: the ten review rounds, the two shape decisions, and the alternatives that lost |

**Decided elsewhere:**
[**ADR-0073**](../../adr/0073-zensical-as-the-v1-binder-renderer.md) — why
Zensical is the v1 renderer, with the measurements, the shared-fixture comparison,
and the revisit conditions.

## Why this is a tree and not a document

The previous draft was one 4,800-line file. Every review round found real defects,
and a recurring class was **"X is specified two or three incompatible ways"** —
because patching one section reliably broke another repeating the same fact. The
split is not cosmetic: each file owns one concern.

The same review history produced three shape-level diagnoses, and all three were
fixed rather than patched:

1. **The trust surface was too large to route.** Five rounds each found *a
   different* flag, environment variable, or file that had not been routed through
   the authority lattice. The first response was a better router; the right one was
   fewer inputs. D39 cut the `trusted` profile, the policy file, and six flags —
   deleting the lattice rather than perfecting it.
2. **The renderer was chosen on paper and never spiked.** Running it deleted two
   entire control areas that existed only to work around Quarto, and later
   measurement showed the *stated* reason for the replacement was wrong too. See
   ADR-0073.
3. **The strict profile was a denylist validated against no corpus.** It rejected
   `<br/>` in Mermaid labels — 45 occurrences in the design document itself. Rules
   are now corpus-tested by construction.

## Load-bearing invariants

The invariants this tree restates and amends are #3, #8, #10, #12, #13, #18, #21
and #22, in [`overview.md`](overview.md#architectural-invariants); the original
twenty come from the brief. Three carry most of the weight:

- **3 — the adapter cannot re-select.** Every source read goes through a single
  `read_node_source(node)` accessor that rejects any path not enumerated in the
  index. Renderer neutrality is mechanical rather than declared.
- **21 — `binder-index.json` is byte-reproducible for identical inputs.** No
  timestamps, run IDs, host names, or absolute paths. This makes ceremonial fields
  structurally impossible rather than merely discouraged.
- **22 — `binder build` writes no field of `binder-index.json`.** Anything an
  adapter must invent goes in that adapter's own plan file — and this was checked
  rather than asserted: the renderer changed and the index did not.

> There is no invariant 23. An earlier draft added *"every input is classified by
> origin before it is trusted"* to serve the authority lattice; D39 deleted the
> lattice, and origin classification with it.
