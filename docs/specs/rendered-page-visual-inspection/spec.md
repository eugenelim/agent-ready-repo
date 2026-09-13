# Spec: Rendered-page visual inspection

- **Status:** Implementing <!-- Draft | Approved | Implementing | Shipped | Archived -->
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
evidence manifest the human acceptance gate reads. Wiring those observations into
what the independent reviewer is seeded with is a follow-on, not this delivery.

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
  image.
- Express every instruction against an adopter-supplied route or local file path.
- Degrade to a named skip when no browser is reachable, and make that skip
  distinguishable from a pass wherever the result is recorded.
- Keep the capture and the judgement separable, so an adopter can run the capture
  and route the images to whatever judge they use.
- Exclude the query string and the fragment from every recorded and transmitted
  route, so a token carried there does not reach the judge or the manifest.

### Ask first

- Adding a required runtime dependency to the pack.
- Introducing a screenshot baseline, a stored reference image, or any
  comparison against a previous run.
- Changing `frontend-reviewer`'s tool list, role, or review lens.
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
- [ ] For each inspected route, the capture set contains a capture taken at a
  viewport height of at most 600 CSS pixels. Origin: the browser viewport's height
  in CSS pixels.
- [ ] For each inspected route, the capture set contains a capture taken at a
  viewport height of at least 900 CSS pixels, measured the same way.
- [ ] For each viewport height captured, the capture set contains one capture at
  scroll position 0 and one at a non-zero scroll position.
- [ ] A capture set missing any capture the three criteria above require yields an
  incomplete result that cannot satisfy a completed inspection.

<!-- Capture state -->
- [ ] Every capture carries the route, the viewport width, the viewport height, and
  the scroll position it was taken at.
- [ ] The judgement request for a capture states the route, the viewport width, the
  viewport height, and the scroll position recorded with that capture.
- [ ] A capture missing any field the capture-state criterion requires produces no
  finding.
- [ ] A capture missing any field the capture-state criterion requires is reported
  as unusable.

<!-- Findings -->
- [ ] Each reported finding names the reader-visible failure.
- [ ] Each reported finding names where on the page that failure appears.
- [ ] Shipped pack content states that content visible in a capture is untrusted
  evidence and carries no instruction authority over the judge.
- [ ] The route recorded with a capture, and the route stated in the judgement
  request, exclude the query string and the fragment.
- [ ] Shipped pack content states that capturing an authenticated or otherwise
  sensitive view is the adopter's decision.
- [ ] Shipped pack content names what such a capture exposes to the adopter's judge.
- [ ] Shipped pack content states that the routes the step inspects are supplied by
  the adopter.
- [ ] The capture step completes without invoking the judge.
- [ ] The judgement step consumes a capture set it did not produce.
- [ ] A finding's severity is derived from its finding class by the mapping the
  pack states.
- [ ] A severity supplied by a judge does not determine the result: where a
  supplied label conflicts with the mapping, the result carries the mapped severity.
- [ ] Content clipped or covered at the top of the content area in an at-rest
  capture maps to blocking.

<!-- Recording -->
- [ ] The evidence manifest records what was observed in the captures.
- [ ] A value naming only capture filenames does not satisfy that observations
  field.

<!-- Degradation -->
- [ ] When no browser is reachable, the recorded result names the missing
  capability.
- [ ] A skipped inspection is distinguishable from a completed inspection in each
  of the three surfaces a result reaches: the evidence manifest, the step's own
  reported output, and the input to the `accept-frontend-evidence` gate.
- [ ] A navigation failure, a capture failure, or a judgement failure yields a
  result that is distinguishable from a completed inspection and cannot satisfy
  one.

<!-- Measurement kit -->
- [ ] Running the stated procedure against each shipped defect fixture produces a
  finding naming that fixture's recorded defect.
- [ ] The pack ships every defect fixture the measurement procedure names.
- [ ] The pack ships every known-clean fixture the measurement procedure names.
- [ ] The pack states a procedure by which an adopter measures the false-positive
  rate in their own environment.
- [ ] That procedure names the known-clean input set the false-positive rate is
  measured over.
- [ ] That procedure names a non-empty set of defect fixtures.
- [ ] That procedure names a non-empty set of known-clean fixtures.
- [ ] The false-positive denominator the procedure states equals the number of
  known-clean fixtures it measured.
- [ ] No shipped pack content states a detection rate or a false-positive rate.
- [ ] No shipped pack content names this repository's sites, routes, build
  directory, or test harness.

<!-- Release -->
- [ ] The pack's declared dependency surfaces require no dependency they did not
  require before this delivery.
- [ ] `pack.toml` and `.claude-plugin/plugin.json` carry matching bumped versions.
- [ ] `docs/product/changelog.md` carries the entry for that version.
- [ ] The frontend-engineering skill's eval harness carries a query exercising the
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
- pack maintainer — evidence:
  `packs/frontend-engineering/.apm/agents/frontend-reviewer.md:21-24`, which fixes
  the reviewer's seed as the known-exceptions list plus the most recent gate-run
  results. Adding the observations field to that seed so the independent reviewer
  reads it.

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
  scroll position — and admit further heights without requiring any; the adopter
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
