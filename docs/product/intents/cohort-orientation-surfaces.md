# Cohort orientation across the marketing and documentation surfaces

- **Status:** Draft

## Outcome

An adoption champion can understand the whole AI-supervised operating model from
the published surfaces and re-explain it accurately to an engineer, a platform
team, and a budget holder — without improvising.

Concretely, the surfaces stop asking a reader to assemble the relationships
themselves. The marketing home leads with one artifact that carries the whole
model; the documentation surface leads with the ordered paths it already
publishes and groups its navigation by the reader's job; and the **marketing**
surface describes the human decision points in the words a person would use
rather than in internal gate identifiers.

**Scoped to marketing on the gate-identifier clause, deliberately.** The
documentation surface publishes 94 gate-code occurrences across 14 files in
`guides/`, one of which defines them as reader-facing vocabulary. Those are out
of this boundary, so a both-surfaces claim would be unachievable — see Boundary.

**Falsifier.** The outcome is achieved when a reader who has seen only these
surfaces can explain the model back. It is *not* achieved by shipping any
particular composition — the nesting of the work lifecycle inside one adoption
station is an inherited design decision with its own recorded kill condition,
not part of this outcome.

## Boundary

**In:** the marketing home page's structure and copy; two new marketing pages
(the operating-model canvas as a portable artifact, and an internal-case route);
the documentation guides index and its navigation model; and the removal of the
**eleven rendered gate identifiers in two marketing components** —
`HumanGates.astro` (six) and `ThreeLoops.astro` (five). Also in: the canvas's
`README.md` rendering and the probe that verifies it, because that rendering is
what defines the canvas's contract.

**Also in, each on its own recorded basis** — not on one universal claim:

| Item | Why it is in |
| --- | --- |
| Amend the Shipped `guides-sidebar-generation` spec — the `job` field **and** the correction to its stale directory-fallback premise | **The outcome is unreachable without the first.** Its data model pins `[[guide_groups]]` to `dir` + `label`, so job grouping cannot be expressed. The second is in because the packet's own conclusion is that both belong in one amendment; leaving a measured-false premise inside a Shipped contract while it is open is not defensible. |
| Generate the canvas SVG from the token source | **Decay control.** A hand-authored snapshot diverges from the palette silently and nothing fails. |
| Raster export for link previews | **Link-preview validity** — no platform accepts SVG. Note the packet corrected its own emphasis here: the text payload does more work than the image, so this is required but not the centre of the transfer surface. |
| Contrast check for the marketing palette | **An owner-approved accessibility control** closing a pre-existing gap, not a consequence of this outcome. The canvas is simply the first element to walk into it. |

**Out:**

- **Restructuring `README.md`.** Its highest-traffic status is why this is
  tempting; the canvas's rendering there is separately In, above.
- **The 94 gate-code occurrences across 14 files in `guides/`**, including one
  explanation page that defines them as reader-facing vocabulary. A content
  programme, not a redesign. This is why the outcome's gate-identifier clause is
  scoped to marketing.
- The pack catalogue, journey pages, and `/now/`.
- The nine generated content files carrying 12 gate-code occurrences, fixable
  only at their `packs/*/JOURNEY.md` sources. **One of them,
  `web/src/content/packs/iac-terraform.md`, is also in the adjacent intent's
  scope** — see unresolved question 2.
- Writing tutorials for the ten guide areas that have none.
- **Moving the job taxonomy into `site.toml`.** Not merely "separable": the
  taxonomy has two homes today — a marketing-only TypeScript module and a
  Markdown table — and their pack membership has **already drifted in three of
  seven rows**. The In-scope re-grouping consumes those same seven names, so
  which home governs membership must be answered even though the consolidation
  is out.
- **`agent-skill-engineering` is named in the job taxonomy with no guide
  directory**, which interacts with the spec rule requiring an entry per
  directory. The taxonomy's owner decides.

**Not a boundary change but worth stating:** no file under `web/`, `docs-site/`,
`guides/`, `site.toml`, or `packs/` was changed by the design session.
Everything upstream of this intent is specification.

## Owner

eugenelim.

**Decisions this owner cannot make alone**, each named in the source with a
different holder: the scope of ADR-0020 (its owner), whether the guide source
model gains a `hub` kind (the guide source model's owner), and which of the job
taxonomy's two homes governs pack membership (the taxonomy's owner).

## Unresolved questions

1. **Which solution artifact this becomes.** The scope spans two surfaces, a
   Shipped-spec amendment, and three new pipeline capabilities. That is larger
   than one spec and may warrant a delivery brief coordinating several, or an RFC
   for the spec amendment with specs beneath it. This intent deliberately does
   not choose.
2. **Who owns the marketing navigation model and the zero-gate-code count across
   two intents?** `docs/product/intents/catalogue-wave7-marketing-evaluator.md`
   adds a marketing `/evaluate/` page and updates catalogue and pack pages under
   RFC-0076 D10, and **RFC-0076 is Accepted** — so on a collision its page-level
   scope outranks a design packet whose third gate is not yet granted. Different
   reader, different outcome, but two shared surfaces remain after this intent
   cedes the catalogue and pack pages: **the marketing navigation model**, and
   **`web/src/content/packs/`** — where `iac-terraform.md` carries a gate
   identifier this intent declares Out while wave7 edits that file. So wave7
   could either break or discharge the zero-count check.

   **Trigger:** whichever intent reaches implementation first. **Needed:** one
   owner for the marketing navigation model, and one owner for the gate-code
   count across both. Recording the adjacency is sufficient for admission;
   neither intent has to move first.
3. **Who writes the marketing headline.** The design packet specifies its
   contract in full — at most ten words, the team's situation before any
   mechanism — and no installed skill produces positioned marketing copy. Three
   candidates exist as input, not as a decision.
4. **Not open — an accepted risk, recorded here so routing sees it.** Whether one
   canvas serves four audiences was **decided** by the owner at
   `approve-aesthetic-direction`. Practitioner sales-enablement writing holds that
   per-stakeholder collateral is required and generic collateral fails — and every
   source arguing it has a client-acquisition incentive and none is independent,
   which is why it did not carry. The falsifier is the role-stratified
   comprehension check in
   `docs/design/discovery/team-orientation-measurement-plan.md` § Kill conditions,
   under "Use one canvas for four audiences".
5. **Which of the five owed verifications gates delivery, and who runs each?**
   Three need execution rather than writing — diffing generated slugs, querying
   the live index, and measuring a read time — and one cannot be closed inside
   this repository at all: whether the canvas survives GitHub's Markdown
   sanitiser needs a probe in a real README. The verifications themselves are
   listed in the source; what is unresolved is their ownership.
6. **The primary success metric has no baseline.** The explain-it-back instrument
   exists as a guide; the champion interview that would establish its baseline has
   not run. Until it does, every stage emotion and pain in the source journeys is
   assumption-based.

7. **Who defines "pack" in plain words, and where?** It is unfamiliar
   product-specific vocabulary sitting in navigation on both surfaces, and the
   plain-language floor bars it until defined. Nobody owns the sentence.
8. **Does ADR-0020's per-pack Diátaxis hierarchy engage the job grouping?** It
   governs structure *within* an area, and grouping areas above themselves
   appears not to touch it — but that reading needs the ADR's owner, and if it
   does engage, the sidebar work needs a different shape.
9. **Does the guide source model gain a `hub` kind?** All 21 area index pages
   function as navigation hubs; 18 declare `explanation` and 3 declare
   `reference`, for no structural reason. Either they retype or the type set
   grows. The guide source model's owner decides.

## Projection

**Tracker:** none. No tracker projection was requested and none is implied — the
repository holds the truth for this work.

**Artifact:** deferred to unresolved question 1. This intent does not choose
between an RFC, a delivery brief, or a set of specs, and the field should not be
read as "no downstream artifact".

## Source

- Mode: repo-origin
- Locator: docs/design/discovery/team-orientation-build-handoff.md
- Revision: sha256-bytes-v1:fb74c0f2034dd6a0422b958b56f89a8abec66b48ec15becdf46509b92c70eadc
- Revision note: repinned after the source was corrected. The original pin went
  stale within the session when the gate-code scope was narrowed to marketing.
- Authority: the design packet under `docs/design/`, produced through the
  experience-design thread with **two owner gates passed** — `approve-journey`
  and `approve-aesthetic-direction`, both 2026-09-04. The third,
  `review-experience-designs`, is **requested and not yet granted**: all six
  cold-review blockers are fixed and ten of sixteen majors, with six owed.
  Admission does not depend on it, but **delivery does** — if that gate returns
  findings, this intent returns to the routing question rather than to build.
  Rationale and every decision's basis are in
  `docs/design/discovery/team-orientation-decision-log.md`; the six screens and
  their transitions are in `docs/design/screens/team-orientation-flow.md`.
