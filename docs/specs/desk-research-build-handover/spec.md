# Spec: desk-research-build-handover

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none
- **Brief:** docs/product/briefs/sdlc-guide-uplift-and-learning-paths.md
- **Discovery:** none
- **Contract:** none
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

Mode: full. The change adds one navigation entry and repairs the broken links
already shipping from the same pack.

## Objective

A reader who finishes a research route in the `desk-research` pack reaches the
shaping-to-build handover from the pack's own front door, in one click, without
falling back to browsing pack directories. The pack's navigation is also
truthful: every in-tree link it publishes points at something that exists, and a
guide that only *illustrates* link syntax shows that syntax as text rather than
offering the reader a link that goes nowhere.

The handover entry is the confirmed slice. The link repairs are defect
correction on the same pages, not new scope: they are already shipping as
external 404s.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| User-facing promise | Applicable — the handover entry is the outcome | `guides/desk-research/README.md` | `author-product-docs` workflow; docs maintainers | The handover entry, and corrected in-tree links | AC1, AC2 hold |
| Current product truth | Applicable — two pack pages publish links to files that do not exist | `guides/desk-research/how-to/run-a-research-project-into-an-rfc.md`, `guides/desk-research/tutorials/your-first-research-project.md` | `author-product-docs` workflow; docs maintainers | Corrected or de-linked references | AC2 holds |
| Reusable learning | **Not applicable to this slice** — the standing emitted-fallback detector was cut on 2026-09-09 and is registered under Follow-ons. The mechanism is recorded as a captured project-knowledge observation rather than left implicit. | — | — | — | — |
| Decision rationale | **Not applicable** — no decision is settled here; the pack's navigation is being corrected to what it already claims. | — | — | — | — |
| Release history | **Not applicable** — `docs/CONVENTIONS.md` § 5b owes an entry only in a PR that bumps a released artifact's version. This bumps none. | — | — | — | — |
| Architecture, operations, maintainer procedure | **Not applicable** — no component, runtime, or authoring procedure changes. | — | — | — | — |

## Boundaries

### Always do

- Point a corrected link at the file that already exists. Renaming a guide file
  to match a broken link would change a published URL.
- Keep an illustrative snippet illustrative: a guide showing a reader *how to
  write* a link states the syntax without offering it as a live link.
- Repair a broken link by pointing it at the file that exists. Never repoint an
  intentionally fictional example at a real unrelated file.

### Ask first

- Renaming or moving any file under `guides/desk-research/`.
- Repairing links in any pack other than `desk-research`.

### Never do

- Change any skill's behavior, trigger phrasing, or `SKILL.md`.
- Edit generated content under `docs-site/src/content/docs/`.
- Deliver brief slices S3, S4, or S5 — the affordance and worked-example passes
  are out of scope.
- Change `build-site.py`'s link-rewriting behavior. The laundering is real and
  recorded, but changing it is not this slice's outcome.
- Add the standing emitted-fallback detector. It was explicitly cut; it is a
  Follow-on, not silent scope.

## Testing Strategy

- **Handover entry (AC1) and its route (AC3):** goal-based check over emitted
  HTML, binding the anchor's text and target together and requiring the target
  to be a page the site emits.
- **In-tree link truth (AC2):** goal-based check over authored Markdown. This
  belongs at source altitude because the defect *is* a source link whose emitted
  form is a plausible-looking external locator — the emitted page cannot
  distinguish a deliberate external reference from a laundered mistake.

**What AC2 does not cover, and why.** It reads inline links only. Reference-style
definitions, angle-bracket destinations, destinations continued on a following
line, and raw HTML anchors are outside it, because a regex is not a CommonMark
parser and claiming otherwise would be a coverage claim this slice cannot keep.
A walk of the pack on 2026-09-09 found 56 inline links and none of those other
forms, so the check covers every link the pack publishes today. The general case
belongs to the emitted-fallback detector registered under Follow-ons: the
renderer already knows which links it could not resolve, because that is exactly
when it emits the external fallback.

**What these checks do not establish.** They read the emitted document, so they
prove the handover anchor exists with the right text and target — not that it is
visible after CSS. The repository's browser gate does not visit this pack's
pages, and its marketing route set is another spec's ratified constant, so
CSS-level concealment is a gap this spec accepts rather than covers, exactly as
the sibling `install-to-ship-walkthrough` records it.

No behavior here has a compressible invariant, so no criterion is TDD-mode.

## Acceptance Criteria

- [x] **AC1 — the research route reaches the handover.** The rendered article
      body of the emitted `desk-research` pack page — the container holding the
      page's own authored Markdown, excluding the site-wide sidebar, breadcrumbs,
      pagination, edit controls, and footer — presents an anchor that is not
      inside a collapsed disclosure, whose text names handing an intent to the
      build loop, and whose target is the `hand-an-intent-to-build` guide page.
- [x] **AC2 — every inline in-tree link in the pack resolves.** Under
      `guides/desk-research/`, every **inline** Markdown link target outside
      fenced or indented code — with any `#fragment` removed — names a file that
      exists, or a directory containing a `README.md`.
- [x] **AC3 — the handover link resolves in the built site.** The AC1 anchor's
      target is a page the site emits.

## Follow-ons

- eugenelim: `docs/product/briefs/sdlc-guide-uplift-and-learning-paths.md`
  slices S3–S5 were confirmed on 2026-09-09 and exist as Draft spec packets
  owned by another session. They are not registered in the initiative's work
  queue, so the brief's child scope does not yet derive from them.
- eugenelim: the standing emitted-fallback detector — asserting that no page
  emitted from `guides/` carries an external blob locator pointing back under
  `guides/` — was cut from this slice on 2026-09-09 and needs its own
  confirmation. Without it, AC2 guards this pack's inline links only at source,
  and a future defect reaching the same fallback by another route is undetected.
  Stable reference:
  [`docs/product/intents/emitted-guide-link-fallback-detector.md`](../../product/intents/emitted-guide-link-fallback-detector.md),
  registered in `[backlog].open` in this change with the canonical
  `{path, kind, source, summary, needs}` shape, and carrying captured
  observation
  `kco-202609-43b240cb94a85bb57b6c908b7e4cdaf71a4845bdd3c591750d02d42c083ed0ba`.
- eugenelim: whether packs other than `desk-research` publish unresolvable
  in-tree links needs its own measurement and cut. The 2026-09-09 walk found
  none outside this pack, but no standing check holds that true.

## Assumptions

- Technical: `guides/desk-research/` publishes six unresolvable relative
  Markdown links and the rest of `guides/` publishes none (source: a walk of
  every `](...md)` link under `guides/` resolved against the filesystem, run
  2026-09-09).
- Technical: three are `README.md` entries naming `desk-research-pipelines.md`
  and `desk-research-methodology.md`, whose real files are `research-pipelines.md`
  and `research-methodology.md`; two are `your-first-research-project.md`
  entries naming `research-first-session.md`, whose real file is
  `desk-research-first-session.md` (source: `ls guides/desk-research/*/`).
- Technical: the sixth is an illustrative example in
  `run-a-research-project-into-an-rfc.md:93` showing a reader how to cite an RFC
  notes companion. `docs/rfc/0041-notes/` exists but contains `research.md`, not
  the example's `python-dep-manager-brief.md`, so the example names a
  deliberately fictional file (source: that line and `ls docs/rfc/0041-notes`).
- Technical: `tools/build-site.py` rewrites an unresolvable in-tree link to a
  GitHub blob URL, so it leaves the internal-link audit's scope. `make
  site-link-check` reported 73,075 links across 288 pages clean on 2026-09-09
  while all six defects were present (source: that run, and the emitted
  `build/docs/guides/desk-research/index.html`, which carries
  `https://github.com/eugenelim/agent-ready-repo/blob/main/guides/desk-research/how-to/desk-research-pipelines.md`).
- Technical: `guides/architect/README.md:43` already links to the handover, so
  this slice follows a shipped precedent rather than inventing an entry shape
  (source: that file).
- Process: the owner confirmed slice S2 on 2026-09-09 (source: user
  confirmation).
