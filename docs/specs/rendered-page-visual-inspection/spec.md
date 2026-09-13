# Spec: Rendered-page visual inspection

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none
- **Brief:** none
- **Discovery:** [`docs/product/intents/rendered-page-visual-inspection.md`](../../product/intents/rendered-page-visual-inspection.md)
- **Contract:** none
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

A team using the `frontend-engineering` pack finishes a web surface and learns,
before a reader does, that something on the rendered page is covering something
else, running off its container, or unreadable. The pack already instructs the
agent to observe a screenshot, but that instruction names no required capture
states, no record of what was seen, and no consequence for skipping. This delivery
makes the step real: the agent drives the browser the pack already requires,
captures the surface in named states, and reports reader-visible failures into the
evidence manifest the human acceptance gate reads, and an unresolved blocking
finding stops the surface completing. Wiring those observations into what the
independent reviewer is seeded with was scoped out at authoring time and **taken
into scope on 2026-09-13 by owner decision**, together with the reviewer's lens
and its ability to capture a page itself.

Success for the adopter is a completion signal that cannot be green while the
page is visibly broken, plus the means to measure, in their own environment, how
often it reports a page that is fine. The pack does not promise a noise level it
cannot measure for them.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| User promise | Applicable — adopters gain a new step in a published journey | `packs/frontend-engineering/JOURNEY.md` step 4 and its `accept-frontend-evidence` gate | pack maintainer | Journey text names the step, its output, and its named skip | Journey describes what an adopter actually receives |
| Current product truth | Applicable — the skill is the executable contract | `packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md` visual-QA section and evidence-manifest table | pack maintainer | Self-host projection regenerated; catalogue lint and verify green | Skill and its projections agree |
| Adopter guidance | Applicable — a new step needs a how-to | **Unresolved — closeout blocker:** whether this extends an existing page under `guides/frontend-engineering/` or adds a new one is decided in T6 against the tree as it then stands | pack maintainer | Guide page walks the step against a non-repository surface | The destination decision is recorded and the guide is walkable without this repository |
| Decision rationale | Applicable — "do not ask the model for severity" is non-obvious and was measured | this spec's Acceptance Criteria plus the intent's de-risk record | spec owner | the severity-derivation and top-clipping criteria state the rule; the intent holds the measurement | A future reader can see why severity is derived, not asked |
| Measurement kit | Applicable — the false-positive rate does not transfer between environments | `packs/frontend-engineering/.apm/skills/frontend-engineering/references/` | pack maintainer | Fixtures plus a stated procedure an adopter runs locally | An adopter can measure their own rate without this repository |
| Reusable learning — eval harness | Applicable — `packs/AGENTS.md` § *Security and authoring rules* obliges a non-cosmetic pack update to update that pack's eval harness | `packs/frontend-engineering/.apm/skills/frontend-engineering/evals/` | pack maintainer | Harness carries a query exercising the inspection step | The harness exercises the shipped step |
| Release history | Applicable — pack content changes | `packs/frontend-engineering/pack.toml`, `.claude-plugin/plugin.json`, `docs/product/changelog.md` | release workflow | Matching version bump in both manifests; changelog entry | Versions and changelog agree with shipped content |

## Boundaries

### Always do

- Record, with every capture, the route, viewport width and height, and scroll
  position it was taken at, and state that same context to whatever judges the
  image. Record also whether the page was scrollable at that height, so a page
  with nothing below the fold is distinguishable from one nobody scrolled.
- Express every instruction against an adopter-supplied route or local file path.
- Degrade to a named skip when no browser is reachable, and make that skip
  distinguishable from a pass wherever the result is recorded.
- Keep the capture and the judgement separable, so an adopter can run the capture
  and route the images to whatever judge they use.
- Exclude the query string and the fragment from every recorded and transmitted
  route, so a token carried there does not reach the judge or the manifest.
- Carry the untrusted-evidence boundary in the request that reaches the judge,
  not only in the skill the agent reads: a separate adopter-chosen judge never
  reads the skill.
- Keep the inspection's verdict separate from whether it executed, and let an
  unresolved reader-visible failure of blocking severity stop the surface
  completing.

### Ask first

- Adding a required runtime dependency to the pack.
- Introducing a screenshot baseline, a stored reference image, or any
  comparison against a previous run.
- Changing `frontend-reviewer`'s tool list, role, or review lens. **Authorised
  2026-09-13**: the owner took all four parts of the reviewer fix, so this
  delivery changes the tool list (adds Bash), the seed, and the lens. The
  boundary stands for any further change.
- Changing what a named skip costs at the `accept-frontend-evidence` gate.

### Never do

- Publish a false-positive or detection rate as a property of a model or of the
  feature. Those numbers were measured to differ between viewer configurations
  and do not transfer.
- Accept a filename, a truthy path, or an unexamined capture as evidence that the
  page was inspected.
- Take a model-supplied severity label as the finding's severity.
- Cite this repository's routes, sites, build, or test harness in shipped pack
  content.

## Testing Strategy

- **State recording, capture-set completeness, and severity derivation — TDD.**
  Each is a compressible invariant over data: a capture record either carries its
  four fields or it does not, a capture set either contains every required
  height-and-scroll combination or it does not, and a finding class either maps to
  a severity or the mapping is incomplete. Unit tests against the pack's stated
  capture table and severity mapping.
- **Skill, journey, and manifest text — goal-based check.** `agentbundle catalogue
  lint --deep`, `catalogue verify`, and the self-host projection are the one-liners
  that prove pack content is well-formed and its projections agree.
- **The two prohibition criteria — goal-based check, each with its reach stated.**
  Both are universal claims over authored prose, so each names the search that
  makes it checkable and thereby makes its own blind spot visible.
  - *No published rate:* a search of shipped pack content for a number adjacent to
    any term in the pack-stated rate vocabulary. Its reach is that vocabulary; a
    rate phrased outside it is not caught, and the vocabulary is the artifact a
    reviewer inspects to judge the claim.
  - *Adopter genericity:* a search of shipped pack content for a stated set of this
    repository's identifiers. Its reach is that identifier set.
- **No new dependency — goal-based check.** A comparison of the pack's declared
  dependency surfaces before and after the change, which fails on any newly
  required dependency. The surfaces compared are named in the plan.
- **The inspection end to end — visual / manual QA.** The step is an agent gesture,
  so it is verified by performing it: run the capture against a surface, route the
  images to a judge, and record what came back. A passing unit test for the record
  shape is not evidence that the inspection found anything.
- **The measurement kit — manual QA with a recorded outcome.** Run the shipped
  fixtures through a judge and record the result as a local measurement. The
  recorded number is evidence the kit works, never a published rate.

## Acceptance Criteria

<!-- Capture set -->
- [x] For each inspected route, the capture set contains a capture taken at a
  viewport height of at most 600 CSS pixels. Origin: the browser viewport's height
  in CSS pixels.
- [x] For each inspected route, the capture set contains a capture taken at a
  viewport height of at least 900 CSS pixels, measured the same way.
- [x] For each viewport height captured, the capture set contains one capture at
  scroll position 0 and one at a non-zero scroll position, or the page is recorded
  as not scrollable at that height. Amended 2026-09-13 under owner authority: the
  end-to-end run measured 17 of 32 captures unable to reach a non-zero scroll
  position because the page is shorter than the viewport, which made every such
  page permanently incomplete. A page with nothing below the fold has no scrolled
  view to inspect. The not-scrollable case is recorded on the capture, never
  inferred from a scroll position of 0.
- [x] A capture set missing any capture the three criteria above require yields an
  incomplete result that cannot satisfy a completed inspection.

<!-- Capture state -->
- [x] Every capture carries the route, the viewport width, the viewport height, and
  the scroll position it was taken at, plus whether the page was scrollable at that
  height.
- [x] The judgement request for a capture states the route, the viewport width, the
  viewport height, and the scroll position recorded with that capture.
- [x] A capture missing any field the capture-state criterion requires produces no
  finding.
- [x] A capture missing any field the capture-state criterion requires is reported
  as unusable.

<!-- Findings -->
- [x] Each reported finding names the reader-visible failure.
- [x] Each reported finding names where on the page that failure appears.
- [x] Shipped pack content states that content visible in a capture is untrusted
  evidence and carries no instruction authority over the judge.
- [x] The route recorded with a capture, and the route stated in the judgement
  request, exclude the query string and the fragment.
- [x] Shipped pack content states that capturing an authenticated or otherwise
  sensitive view is the adopter's decision.
- [x] Shipped pack content names what such a capture exposes to the adopter's judge.
- [x] Shipped pack content states that the routes the step inspects are supplied by
  the adopter.
- [x] The capture step completes without invoking the judge.
- [x] The judgement step consumes a capture set it did not produce.
- [x] A finding's severity is derived from its finding class by the mapping the
  pack states.
- [x] A severity supplied by a judge does not determine the result: where a
  supplied label conflicts with the mapping, the result carries the mapped severity.
- [x] Content clipped or covered at the top of the content area in an at-rest
  capture maps to blocking.

<!-- Recording -->
- [x] The evidence manifest records what was observed in the captures.
- [x] A value naming only capture filenames does not satisfy that observations
  field.

<!-- Degradation -->
- [x] When no browser is reachable, the recorded result names the missing
  capability.
- [x] A skipped inspection is distinguishable from a completed inspection in each
  of the three surfaces a result reaches: the evidence manifest, the step's own
  reported output, and the input to the `accept-frontend-evidence` gate.
- [x] A navigation failure, a capture failure, or a judgement failure yields a
  result that is distinguishable from a completed inspection and cannot satisfy
  one.

<!-- Measurement kit -->
- [x] Running the stated procedure against each shipped defect fixture produces a
  finding naming that fixture's recorded defect.
- [x] The pack ships every defect fixture the measurement procedure names.
- [x] The pack ships every known-clean fixture the measurement procedure names.
- [x] The pack states a procedure by which an adopter measures the false-positive
  rate in their own environment.
- [x] That procedure names the known-clean input set the false-positive rate is
  measured over.
- [x] That procedure names a non-empty set of defect fixtures.
- [x] That procedure names a non-empty set of known-clean fixtures.
- [x] The false-positive denominator the procedure states equals the number of
  known-clean fixtures it measured.
- [x] No shipped pack content states a detection rate or a false-positive rate.
- [x] No shipped pack content names this repository's sites, routes, build
  directory, or test harness.

<!-- Consequence: the Objective's promise, which the original criteria never carried -->
- [x] A run whose findings include an unresolved finding of blocking severity
  does not yield a completed inspection, even when every required capture was
  taken, judged, and recorded.
- [x] The result a run reports distinguishes whether the inspection executed
  from whether it passed, so an execution failure and a blocking finding are not
  the same state.
- [x] The `accept-frontend-evidence` gate is told to check the inspection
  verdict, not only that observations are present.
- [x] A failure that fits more than one finding class takes the most severe of
  the classes it fits, so which class a judge happens to name cannot lower the
  result.

<!-- The judge-side trust boundary -->
- [x] The request that reaches the judge declares the capture untrusted evidence
  carrying no instruction authority.

<!-- Every captured height, shipped rather than assumed -->
- [x] Shipped pack content states that a viewport height the run captured beyond
  the required bands carries the same at-rest and scrolled requirement, with the
  recorded not-scrollable branch.
- [x] No check enforces a capture-set rule that shipped pack content does not
  state.

<!-- The independent reviewer can see the page -->
- [x] `frontend-reviewer` is seeded with the capture set and the recorded
  observations for the surface under review.
- [x] `frontend-reviewer` carries a lens for reader-visible layout failure whose
  severity comes from the pack's finding-class mapping.
- [x] `frontend-reviewer` can capture a rendered page itself rather than relying
  only on captures the author supplied.
- [x] Shipped reviewer content states that the reviewer does not write to the
  repository under review.

<!-- Rule-table integrity -->
- [x] A duplicate row key in a rule table is rejected rather than silently
  collapsed, so the one-severity-per-class rule can fail.

<!-- Release -->
- [x] The pack's declared dependency surfaces require no dependency they did not
  require before this delivery.
- [x] `pack.toml` and `.claude-plugin/plugin.json` carry matching bumped versions.
- [x] `docs/product/changelog.md` carries the entry for that version.
- [x] The frontend-engineering skill's eval harness carries a query exercising the
  inspection step this delivery adds.

## Follow-ons

- pack maintainer — evidence: this spec's `Ask first` boundary "Changing what a
  named skip costs at the `accept-frontend-evidence` gate". Making a named skip
  cost something at that gate. Today a recorded "no Chromium" reason completes the
  surface (`packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md:623`);
  changing it is a decision about a human gate and is excluded here.
- pack maintainer — evidence:
  [`docs/product/intents/rendered-page-visual-inspection.md`](../../product/intents/rendered-page-visual-inspection.md)
  § *Scope — one shippable behaviour*, which lists this as out of scope. Turning a
  finding into a durable regression assertion.
- ~~Adding the observations field to `frontend-reviewer`'s seed.~~ **Taken into
  scope 2026-09-13** by owner decision, together with the reviewer's lens and its
  ability to capture a page itself. Carried by the reviewer criteria above.

## Assumptions

- Technical: the pack already requires headless Chromium for its accessibility
  step, so a browser is in the adopter's hands before this feature asks for one
  (source: `packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md:531`).
- Technical: the pack's evidence-manifest table records capture filenames under
  `screenshots` and carries no field for what was seen in them (source:
  `packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md:613-623`).
- Technical: `frontend-reviewer` is read-only by declared tools and is seeded with
  the manifest's known-exceptions list and most recent gate-run results — a specific
  pair that does not today include an observations field. Widening that seed is a
  follow-on (source: `packs/frontend-engineering/.apm/agents/frontend-reviewer.md:4`, `:21-24`).
- Technical: RFC-0088's `web-pilot` would own a local authenticated-browser
  runtime. This feature introduces no browser runtime, profile, or credential path,
  so it neither extends nor depends on it (source:
  `docs/rfc/0088-web-pilot-foundation.md:3`, `:35-39`).
- Product: severity supplied by a judge is not trustworthy. Measured wrong in both
  directions across two viewer configurations — a non-defect ranked blocking, and
  the defect every reader meets ranked cosmetic (source: the intent's de-risk
  record, rounds 1 and 3).
- Product: the false-positive rate varies by viewer configuration and its cause was
  not isolated between model and environment, so no rate is publishable (source:
  the intent's de-risk record, rounds 4 and 5).
- Technical: consumption is bounded by construction, so no upper bound is
  specified. The capture criteria put a floor of four captures per route — one
  height at most 600 CSS pixels and one at least 900, each at a zero and a non-zero
  scroll position, the latter satisfied by a recorded not-scrollable page — and
  admit further heights without requiring any; the adopter
  names the routes, and the
  delivery ships no script, so no input scales captures, image size, or judgement
  calls (source: this spec's capture criteria; `plan.md` § Design decisions,
  "No script is added to the pack").
- Process: this delivery adds no `metadata.boundaries` declaration to the skill.
  The field is schema-valid and other packs use it, but no rule obliges it for a
  non-credentialed skill: `docs/CONVENTIONS.md:1443-1478` documents only the
  credentialed-skill keys, lint scopes its checks to `metadata.credentialed: true`,
  and `catalogue verify` pins the permitted top-level frontmatter set (source: user
  confirmation 2026-09-13).
- Process: the intent's bet survived de-risking only once the judgement request
  carried the capture's state; two earlier rounds were killed without it (source:
  the intent's de-risk record, rounds 1-3).
