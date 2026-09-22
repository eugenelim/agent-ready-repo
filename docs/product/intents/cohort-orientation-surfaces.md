# Cohort orientation across the marketing and documentation surfaces

- **Slug:** `cohort-orientation-surfaces`
- **Level:** feature
- **Status:** Draft
- **Owner:** eugenelim
- **Parent intent:** none

**Refreshed 2026-09-21 by eugenelim.** Commit `49dac48c5` retrofitted the
marketing home to a paper-first editorial direction and deleted
`HumanGates.astro` and `ThreeLoops.astro`, which delivered three of this
intent's in-scope claims: the home's structure and copy, the eleven rendered
gate identifiers, and the broad marketing-palette contrast gap. The guides hub's
start-here promise and ordered paths shipped across `cc52c0698`, `2f3d9537f`,
`7bd051fa3` and `f2b1f5ab4`. Delivered scope is removed rather than carried, the
internal-case route leaves for contradicting the narrowed audience, and the
altitude is stated as `feature`. No governance parent exists: RFC-0089 excludes
routes, navigation, content and chrome; ADR-0050 owns build and deploy topology;
RFC-0061 owns the `web/` directory; and RFC-0076 D10 is page-level collision
authority for `/evaluate/`, catalogue and pack pages.

## Outcome

An adoption champion can use one published operating-model artifact and the
documentation hub's job-based routes to explain the AI-supervised operating
model to an engineer or platform teammate without reconstructing its structure
or translating internal gate codes.

The artifact makes five relationships recoverable: the adoption stations in
order; the work sequence nested inside proving the model on real work; the
human decisions in plain language; the repository as the source of truth with
one-way tracker projection; and no autonomous approval, merge, or production
ship.

The outcome serves influencers — engineers, tech leads and platform teams. It
does not claim to satisfy architecture, security, procurement, or budget
approval.

## Canvas carrier decision — owed before implementation

The repository does not ship the canvas through `<picture>` and does not ship
both light and dark variants. The only design asset is a single dark SVG with
literal fills, while the current marketing direction places the canvas on paper
and voids the earlier dark-carrier analysis
(`docs/design/direction/marketing-site.md:271-274`,
`docs/design/screens/team-orientation/operating-model-canvas.svg:1-35`).

Re-derive the canvas against the current paper-first tokens and decide the
minimum carrier variants before implementation. Generate every approved SVG and
raster rendering from one token-backed source. The README rendering survives
GitHub sanitisation and retains a complete text alternative, and the
implementation verifies the exact markup it ships — the sanitiser constraint at
`docs/design/screens/team-orientation/operating-model-canvas.md:61-67` still
binds.

## Boundary

**In.** The residue after the shipped work above:

- Reconcile the canvas with the paper-first direction: settle its carrier and
  variant set, then update the composition, focus and contrast decisions that
  still assume a dark carrier.
- Build the portable operating-model artifact and its dedicated marketing
  route, retaining the five relationships named in Outcome and a complete text
  alternative.
- Generate the chosen SVG variant or variants from the current tokens. The
  asset is checked in today and no canvas generator is registered
  (`web/package.json:9-21`).
- Embed the canvas in `README.md`, whose operating-model entry is a pair of
  text links today (`README.md:56-60`), with a regression check for the exact
  sanitised markup.
- Produce the raster and unfurl export from the same source.
- Verify canvas-specific contrast once its carrier is settled.
- Finish the guides hub's job-based navigation: name one authority for job
  membership, amend `guides-sidebar-generation` for a `job` field if that
  remains the model, and project the groups without a third taxonomy.
- Add prominent documentation search with a real example query
  (`docs/design/content/docs-guides-index.md:74-85`).
- Add the cross-surface route from the documentation hub back to the
  operating-model artifact, keeping the documentation surface technical.
- Add one intentional marketing-home route to the journeys index. `site.toml`
  omits `journeys` from the header (`site.toml:148-156`) and the home links only
  to the individual core journey.
- Remove persuasion language from the guide hub — "flagship" and "most
  rigorous" remain against the technical-editorial brief (`guides/README.md:188`).

**Out.** The shipped marketing-home structure and copy; the deleted
`HumanGates.astro` and `ThreeLoops.astro`; the terminal and Claude-app
first-value doors, owned by
[`claude-apps-first-value-entry`](claude-apps-first-value-entry.md); the
internal-case and budget-holder route; gatekeeper decision evidence — TCO, ROI,
exit path, SBOM and CVE posture, SOC 2, SSO and audit claims, data-flow
diagrams, legal terms, DORA deltas; correction of the Shipped sidebar spec's
unrelated directory-fallback premise; the guide-source and generated-content
gate-code programmes, 94 occurrences across 14 files and 12 across nine
generated files; README restructuring; the pack catalogue, journey pages and
`/now/`; tutorial coverage for the ten guide areas without one; and the
dedicated `agent-skill-engineering` guide slice, now owned by
[`agent-skill-engineering-guide-slice`](agent-skill-engineering-guide-slice.md).

The guide taxonomy may stay outside `site.toml`, but delivery names one existing
source as membership authority and projects from it. It does not add a third
hand-maintained taxonomy.

## Evidence and validation

Documentation is relied on during influencer-tier evaluation at moderate
confidence, but no current evidence shows that this canvas or this navigation
change improves comprehension. The portable artifact is a testable feature, not
a proven intervention.

Validate the release candidate with influencer-tier readers. A reader passes
only by recovering every relationship named in Outcome without seeing internal
gate identifiers and without explanation from the champion. Any missing
relationship is a failure to revise before acceptance.

No pre-redesign baseline is claimed, and none will be established — the champion
interview that would have set one was retired as theatre. Every stage emotion
and pain in the source journeys is assumption-based. That is a permanent
property of this packet, not an outstanding action, and it is not a gate.

Gatekeeper approval is a separate outcome requiring separately owned evidence.
No owner for that evidence set exists in the current corpus.

## Owner


**Decisions this owner cannot make alone:** the scope of ADR-0020 (its owner),
whether the guide source model gains a `hub` kind (that model's owner), and
which of the job taxonomy's two homes governs pack membership (the taxonomy's
owner).

## Unresolved questions

1. **Which source owns job membership?** The marketing TypeScript taxonomy
   calls itself canonical (`web/src/lib/catalogue-navigation.ts:1-17`) while the
   guide hub maintains a second table (`guides/README.md:176-197`), and they
   disagree: `architect` and `contracts` sit in "Provision and release safely"
   in one and "Design the product and system" in the other, and
   `agent-skill-engineering` appears in only one. Choose one and project the
   other from it. Moving the taxonomy into `site.toml` is not required.
2. **Will Wave 7 touch shared chrome or authored pack and journey sources?**
   RFC-0076 D10 owns `/evaluate/`, catalogue pages and pack pages. If
   `catalogue-wave7-marketing-evaluator`'s delivery spec also changes
   `site.toml` shared chrome or the authored sources behind
   `web/src/content/packs/`, name one owner for that shared file before
   implementation. Otherwise there is no collision.
3. **Who writes the marketing headline?** The design packet fixes its contract —
   at most ten words, the team's situation before any mechanism — and no
   installed skill produces positioned marketing copy. Three candidates exist as
   input, not as a decision.
4. **Which of the owed verifications gates delivery, and who runs each?** Three
   need execution rather than writing: diffing generated slugs, querying the
   live index, and measuring a read time. The sanitiser question was resolved
   2026-09-10 by probing GitHub's own renderer — the `<img>` binding works and
   inline is removed outright.
5. **Who defines "pack" in plain words, and where?** It is product-specific
   vocabulary sitting in navigation on both surfaces, and the plain-language
   floor bars it until defined. Nobody owns the sentence.
6. **Does ADR-0020's per-pack Diátaxis hierarchy engage the job grouping?** It
   governs structure *within* an area, and grouping areas above themselves
   appears not to touch it — but that reading needs the ADR's owner, and if it
   does engage, the sidebar work takes a different shape.
7. **Does the guide source model gain a `hub` kind?** All 21 area index pages
   function as navigation hubs; 18 declare `explanation` and 3 declare
   `reference`, for no structural reason. Either they retype or the type set
   grows.

## Projection

**Tracker:** none. The repository remains the source of truth.

**Artifact:** one delivery brief with two independently shippable slices — the
portable operating-model artifact with its README, marketing and link-preview
renderings; and the documentation navigation and search bridge. The `job` field,
if it remains the chosen model, lands as an amendment to
`guides-sidebar-generation` rather than a new spec. No RFC unless delivery
changes a durable cross-cutting decision that the amendment cannot own.

## Source

- Mode: repo-origin
- Locator: docs/design/discovery/team-orientation-build-handoff.md
- Revision: sha256-bytes-v1:fb74c0f2034dd6a0422b958b56f89a8abec66b48ec15becdf46509b92c70eadc
- Revision note: repinned after the source was corrected. The original pin went
  stale within the session when the gate-code scope was narrowed to marketing.
- Authority: the design packet under `docs/design/`, produced through the
  experience-design thread with **all three owner gates passed** —
  `approve-journey` (2026-09-04, re-gated 2026-09-10 for the Stage 2
  surface-plural install), `approve-aesthetic-direction` (2026-09-04), and
  `review-experience-designs` (**granted 2026-09-10**: six blockers and
  fourteen of sixteen majors fixed; Major 1/V1 closed by a live GitHub render
  probe; Minor 5 retired with the champion interview). Delivery depended on
  that third gate and is now unblocked.
  Rationale and every decision's basis are in
  `docs/design/discovery/team-orientation-decision-log.md`; the six screens and
  their transitions are in `docs/design/screens/team-orientation-flow.md`.
