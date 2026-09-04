# Cohort orientation across the marketing and documentation surfaces

- **Status:** Draft

## Outcome

An adoption champion can understand the whole AI-supervised operating model from
the published surfaces and re-explain it accurately to an engineer, a platform
team, and a budget holder — without improvising.

Concretely, the surfaces stop asking a reader to assemble the relationships
themselves. The marketing home leads with one artifact that shows the team's
adoption arc with the work lifecycle nested inside one of its stations; the
documentation surface leads with the ordered paths it already publishes and
groups its navigation by the reader's job; and both surfaces describe the human
decision points in the words a person would use rather than in internal gate
identifiers.

## Boundary

**In:** the marketing home page's structure and copy; two new marketing pages
(the operating-model canvas as a portable artifact, and an internal-case route);
the documentation guides index and its navigation model; the removal of all
eleven rendered internal gate identifiers from adopter copy on both surfaces.

**Also in, because the outcome cannot be reached without them:** an amendment to
the Shipped `guides-sidebar-generation` spec, whose data model has no way to nest
pack directories inside a job group; and three pipeline capabilities that do not
exist — generating the canvas SVG from the token source, exporting a raster for
link previews, and a contrast check for the marketing palette.

**Out:** `README.md`, despite being the highest-traffic surface. The pack
catalogue, journey pages, and `/now/`. The nine generated content files that
carry gate identifiers, which are fixable only at their pack sources. Writing
tutorials for the ten guide areas that have none. Moving the job taxonomy into
`site.toml`, which is recommended and separable.

**Not a boundary change but worth stating:** no file outside `docs/` has been
touched. Everything upstream of this intent is specification.

## Owner

eugenelim

## Unresolved questions

1. **Which solution artifact this becomes.** The scope spans two surfaces, a
   Shipped-spec amendment, and three new pipeline capabilities. That is larger
   than one spec and may warrant a delivery brief coordinating several, or an RFC
   for the spec amendment with specs beneath it. This intent deliberately does
   not choose.
2. **An adjacent intent touches the same surface.**
   `docs/product/intents/catalogue-wave7-marketing-evaluator.md` adds a marketing
   `/evaluate/` page and updates catalogue and pack pages under RFC-0076 D10. It
   is a different reader and a different outcome, but the same renderer and
   navigation. Sequencing or merging is a routing decision.
3. **Who writes the marketing headline.** The design packet specifies its
   contract in full — at most ten words, the team's situation before any
   mechanism — and no installed skill produces positioned marketing copy. Three
   candidates exist as input, not as a decision.
4. **Whether one canvas serves four audiences.** Practitioner literature holds
   that per-stakeholder collateral is required. The owner chose to ship one shared
   model and let a role-stratified comprehension check falsify it; the kill
   condition is written.
5. **Five verifications are owed before this can ship**, and one cannot be closed
   by writing: whether the canvas survives GitHub's Markdown sanitiser needs a
   probe in a real README.
6. **The primary success metric has no baseline.** The explain-it-back instrument
   exists as a guide; the champion interview that would establish its baseline has
   not run. Until it does, every stage emotion and pain in the source journeys is
   assumption-based.

## Projection

None. No tracker projection was requested, and none is implied — the repository
holds the truth for this work.

## Source

- Mode: repo-origin
- Locator: docs/design/discovery/team-orientation-build-handoff.md
- Revision: sha256-bytes-v1:065288980bfb77ab13289ce3b60aa83f68fe4fa3fa36edbdb64ea78e42606c10
- Authority: the design packet under `docs/design/`, produced through the
  experience-design thread with three owner gates passed — `approve-journey` and
  `approve-aesthetic-direction` on 2026-09-04, and `review-experience-designs`
  requested after both cold reviews were adjudicated. Rationale and every
  decision's basis are in `docs/design/discovery/team-orientation-decision-log.md`;
  the six screens and their transitions are in
  `docs/design/screens/team-orientation-flow.md`.
