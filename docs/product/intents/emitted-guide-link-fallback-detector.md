# Emitted guide-link fallback detector

- **Status:** Draft
- **Level:** feature

## Outcome

A broken in-repository guide link fails a gate instead of shipping as an
external 404. Today it does the opposite: it is rewritten into an external
locator and disappears from the only check that would have caught it.

## The opportunity

`tools/build-site.py` resolves each relative Markdown link in `guides/` against
the tree. When a target does not exist, it rewrites the link to an external
GitHub blob locator rather than failing. `tools/check-rendered-site-links.py`
audits **internal** links only, so the rewritten link leaves its scope entirely.
The two behaviours are individually reasonable and jointly blind.

Measured on 2026-09-09: `guides/desk-research/` published six unresolvable
relative links — three in its `README.md`, two in a tutorial, one inside an
illustrative snippet — while `make site-link-check` reported **73,075 links
across 288 pages, clean**. A reader following any of the five real ones reached
a GitHub 404. The defect was found by reading the pack, not by any gate.

## What would have to be true

A detector asserts that no page emitted from `guides/` carries an anchor whose
target is an external blob locator pointing back under `guides/`.

That signature is **necessary but not by itself sufficient**. `build-site.py`
leaves an authored `https://` link untouched, and emits the same blob shape for
an unresolved repository-relative link — so an author who deliberately writes an
absolute link into this repository's own guide tree produces output the detector
cannot distinguish from a rewrite. Making the signature decisive therefore needs
one of: a stated convention forbidding authored self-repository blob links in
`guides/` (making every occurrence a defect by definition), a rewrite that marks
what it generated, or a check that resolves the target back against the tree and
reports only the ones that do not exist. Choosing between those is part of this
intent, not a detail of it.

The renderer is the right place to judge this, because the renderer already
knows which links it could not resolve — that knowledge is exactly what triggers
the rewrite. A source-side regex cannot match it: the publishing pipeline parses
CommonMark, and reference-style, angle-bracket, multiline, and raw-HTML anchors
all escape a regex built for inline links.

## Boundary

This is detection, not a change to the rewrite. Whether `build-site.py` should
fail, warn, or keep rewriting is a separate decision this intent does not make.

## Provenance

Cut from [`desk-research-build-handover`](../../specs/desk-research-build-handover/spec.md#follow-ons)
on 2026-09-09 by owner scope decision, so that slice stayed at its confirmed
boundary. That spec's AC2 guards one pack's inline links at source; this is the
general, emitted-side control.

Mechanism and measurement are recorded as captured observation
`kco-202609-43b240cb94a85bb57b6c908b7e4cdaf71a4845bdd3c591750d02d42c083ed0ba`
in `docs/knowledge/observations/gotcha/2026-09.jsonl`.

## Open questions

- Does any pack other than `desk-research` publish unresolvable in-tree links?
  The 2026-09-09 walk found none, but no standing check holds that true.
- Should the detector cover `packs/**` README material as well as `guides/**`?
  Both trees are mirrored by the same build step.
- Which of the three disambiguation routes above should make the signature
  decisive? The convention route is cheapest and needs no build change; the
  resolve-back route is the most precise and duplicates work the rewrite already
  did.
