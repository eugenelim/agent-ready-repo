# History (non-normative)

> **Nothing here is a specification.** It records what was considered and
> rejected, so a future maintainer asking "was this thought about?" gets an answer
> without the normative files carrying the answer inline. Where this file
> disagrees with any other, **the other file governs.**
>
> Merged from three files — `open-decisions.md`, `renderer-choice.md`, and
> `review-history.md` — which together carried 868 lines of reasoning around
> decisions now recorded in [`decisions.md`](decisions.md).

---

## The two shape decisions

Ten cold-review rounds ran. Rounds 1–8 kept finding defects in two areas; rounds
9–10 removed both areas rather than fixing them again.

### D-A — collapse the trust surface instead of routing it

Five rounds each found a *different* unrouted input surface — `--profile`,
`$BINDER_POLICY_FILE`, `--quarto`, `--replace-foreign-dir`, `publication-dir`,
`--out`, `--root`, `--from-index`, `--force-unlock`. Each time the answer was one
more rule in the authority lattice.

**A router that must wrap nine surfaces is evidence the surface is too large.** So
the surfaces were cut: the `trusted` profile, `binder-policy.toml` at every tier,
every grant, and six flags. What survives is `--root`, guarded by refusal rules
rather than by a lattice.

**The cost is real and accepted.** A team whose repository legitimately contains
raw HTML in prose cannot publish those files without editing or excluding them.
Accepted for v1 because the corpus gate will say empirically how often it bites,
because the case that actually appeared (`<br/>` in Mermaid labels) is verified to
work under strict, and because **a profile added later on evidence is a better
profile than one designed against a hypothetical.**

Recorded as D39, extended by D41 (no verb takes a caller-named write destination).

### D-B — the renderer

**The decision and its full reasoning are
[ADR-0073](../../adr/0073-zensical-as-the-v1-binder-renderer.md).** Zensical at an
exact pin, chosen for foundation continuity rather than footprint — the ADR
carries the measurements, the shared-fixture comparison against Quarto and
mkdocs-material, the MkDocs 2.0 evidence and its independent corroboration, and
the revisit conditions.

What belongs here is only the path the design took to get there, because it went
wrong twice and both errors are instructive:

1. **Quarto was selected on documented behaviour and never spiked.** It drove most
   of the design's complexity — the fence transformation, the shortcode scanner,
   the install ladder, the toolchain cache — and every one of those was renderer
   management wearing the shape of architecture.
2. **The first reopening recommended owning a small renderer**, reasoning that
   `binder-index.json` already supplies the structure a static-site generator
   exists to derive. The spike reversed it: Zensical deletes two whole design
   areas that owning a renderer would not have.
3. **The second reopening kept the answer and replaced the argument.** The
   selection had been made on weight, and measurement did not support it —
   mkdocs-material's wheel is *smaller*, and the two are behaviourally
   interchangeable on every criterion that had decided the question. The real
   argument was foundation, not size. See the ADR.

Recorded as D40.

---

## The ten review rounds

| Round | Verdict | Blockers | Majors | Minors | Nits |
|---|---|---|---|---|---|
| 1 | MAJOR REWRITE | 5 | 11 | 15 | 0 |
| 2 | MAJOR REWRITE | 5 | 12 | 20 | 0 |
| 3 | MAJOR REWRITE | 3 | 10 | 17 | 2 |
| 4 | MAJOR REWRITE | 3 | 11 | 11 | 2 |
| 5 | MAJOR REWRITE | 3 | 10 | 14 | 4 |
| 6 | SHIP WITH CHANGES | 2 | 10 | 10 | 2 |
| 7–9 | MAJOR REWRITE → the tree split, then D-A and D-B | | | | |
| 10 | SHIP WITH CHANGES | 3 | 12 | 13 | 4 |

**No finding was ever declined** except round 1's finding 13, which was adopted in
a different form than offered (the digest-verified install was kept and reordered
rather than removed — moot now, since D-B deleted it).

### What each round changed that mattered

**Round 1.** Shortcode handling was specified two contradictory ways and the
escape mechanism was invented; `line-offset` as a scalar was disproved by the
document's own worked example; the trust lattice was bypassable by
`--profile trusted`; environment scrubbing was a denylist that passed
`AWS_SECRET_ACCESS_KEY` — the design's own exfiltration example. Three
load-bearing claims were marked UNVERIFIED and gated.

**Round 2.** The "renderer-neutral" index was not neutral — it carried `.qmd`
filenames, a line map, and pandoc anchors that `resolve` could not have produced.
**Split into `binder-index.json` and an adapter-owned `renderer-plan.json`, with
invariant 22.** This is the change that later made the renderer swap a one-file
edit. Also: a YAML injection surface via recipe `title`; two more open trust
channels; caption binding was ordinal binding with an extra step.

**Round 3.** All three blockers were writes — the read side had been scrutinised
and the write side had not. Publication replacement could `rmtree` an arbitrary
user directory; the published index disclosed exclusion reasons, gaps, and every
source path to review boards and vendors (replaced by a purpose-built
`binder-stamp.json`); the confinement root was specified two incompatible ways.

**Round 4.** Emitted strings bypassed the scanner — the scanner reads bodies, but
titles reach renderer metadata. Two controls were absolute in prose with a channel
left open.

**Round 5.** `check --published` had no input, making exit 9 unreachable and
collapsing the justification for recording source hashes at all. The execution
control was stated two incompatible ways. The provenance appendix republished what
the stamp had just removed.

**Round 6.** The finding that mattered told the author to stop writing about a
gate and run it. V1 confirmed Mermaid survives execution-off **and produced Q26** —
the reader-toggle the security model used as a second layer destroys every diagram
— **and Q27**, the stock theme fetching a typeface from Google at read time. Two
findings the gate was not looking for.

**Rounds 7–9.** Produced the two shape diagnoses above: the trust surface was too
large to route, and the renderer had been chosen on paper and never spiked. The
single-file draft was split into this tree at the same time, because patching one
section reliably broke another repeating the same fact.

**Round 10 — the first round against the propagated tree.** Blockers fell to
three, and **none was a trust-model or renderer finding** — those areas no longer
exist to be found wrong. What replaced them was ordinary contract drift: the
content-key hashed the renderer version though `resolve` runs renderer-free;
`--editorial=DIR` was a surviving caller-named write destination; and one file
still enforced `[policy] profile`. The majors were dominated by **the same
contract published in two files with different values** — which is the defect the
tree split exists to prevent, and which recurs because propagation touches many
files at once.

---

## The gate runs — 2026-08-06 and 2026-08-07

Not review rounds. The rounds above found what the tree said; these found what the
renderer and the harness *do*.

**2026-08-06 — Z1–Z4.** Ran against `zensical==0.0.53` and a transcription of the
config the adapter is specified to emit. Several specified controls were wrong, each
inferred from the shape of a configuration surface rather than executed: the
version probe named an attribute that does not exist, the font-suppression form
requested a typeface literally named `False`, and Mermaid turned out not to be
bundled at all.

**2026-08-07 — Z5, Z6, and V6.** The three that had been left as "needs a
network-isolated runner" or "needs a headless browser". Two came back confirming
the design and one falsified it.

- **Z5 confirmed more than it was asked.** The question was whether the build
  reaches the network; the answer is that it makes **no attempt at all**, measured
  with `SIGKILL` armed on any outbound operation. The instructive part was needing
  a kernel-level instrument rather than a Python-level one: `zensical` ships a
  compiled extension that links network symbols, so a source grep would have
  reported clean for the wrong reason.
- **Z6 is the round's real finding, and it is a new failure mode for this tree.**
  The three earlier corrections were about configuration; this one was about a
  *runtime*. The design reasoned about the HTML the compiler emits and never asked
  what the client-side bundle does to it — and the bundle replaces the element the
  accessibility attributes were on. Worse, Z6e found the mechanism fails
  **inverted**: the name is present exactly when the diagram is broken, so the
  static CI check the design had specified would have read green forever. D46
  replaces it with attributes on the fence delimiter that the theme lifts into the
  Mermaid source, verified in a browser — a `<figure>` wrapper was drafted first and
  rejected for inserting lines per diagram.
- **V6 removed a defensive requirement rather than confirming one.** The agent's
  working directory is the project root on both adapters measured, so `--root`
  stopped being effectively required. The guard was kept, because the remaining
  adapters could not be measured — the honest shape for a relaxation drawn from a
  partial sample.

**What the runs say about the review rounds.** Ten cold reviews did not catch any
of the corrected controls, and could not have: every one of them was a claim
about external behaviour that reads as entirely plausible on the page. That is the
argument for gates being executed before the RFC rather than after, and it is the
reason Z1–Z6 become CI assertions rather than retiring once green.

---

## Alternatives considered and rejected

Twelve were assessed. The four that were close are above and in
[`overview.md`](overview.md); the rest, briefly:

| Alternative | Rejected because |
|---|---|
| Quarto-specific schema, no neutral index | Fails the interop requirement — every producing pack's integration point becomes renderer configuration. The right answer if that requirement were dropped |
| Extend `site.toml` / `tools/build-site.py` | Repository-specific Astro sidebar recipe: no schema, no versioning, no portability, needs npm, cannot install into an unrelated directory |
| Ship Astro/Starlight inside the pack | Ships `node_modules` or hundreds of transitive npm dependencies; the pack becomes a frontend application |
| Custom Python static-site generator | Sidebar, search, prev/next, TOC, cross-references, and accessible theming are individually modest and collectively a product. Still the fallback if the renderer choice fails |
| Chief editor copies and orders files directly | Non-deterministic, unreviewable, and either mutates sources or produces copies that go stale. This is the status quo the design displaces |
| `binder.toml` as a repository-specific format | A format that lands in adopter repositories is public whether documented as one or not |
| Repository scope only / user scope only | Each forecloses a leading use case; supporting both is nearly free given one implementation |
| `binder-index.json` as an internal detail | A contract with two consumers and no stability guarantee is a contract that breaks |
| Author `_quarto.yml` (or `zensical.toml`) directly | Renderer configuration as the authored contract lets source-adjacent files set the surfaces the trust model must own — the failure invariant 12 exists to prevent |
