# Plan: Rendered-page visual inspection

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `packs/AGENTS.md` (pack export boundary, version-bump
  rule, portability rule) and `packs/frontend-engineering/AGENTS.md`; analogous
  implementations — `packs/core/tests/` and `packs/catalogue-curation/tests/` are
  the two nearest pack-test trees, and
  `packs/frontend-engineering/.apm/skills/frontend-engineering/references/digital-experience-contract.md`
  is the pack's one existing reference file and the shape a new reference follows;
  construction path — `agentbundle catalogue lint --deep`, `catalogue verify`, and
  `catalogue self-host --write`. Named uncertainty: this pack ships no `tests/`
  directory and no `scripts/`, so both the test location's registration in whatever
  runner executes pack suites, and the size headroom in `SKILL.md`, are discovery
  predicates below rather than assumptions.

## Approach

The pack already tells the agent to observe a screenshot and already requires a
headless browser for its accessibility step. The gap is that nothing captures in
named states, nothing carries the state into the judgement, nothing records what
was seen, and nothing fails when the step is skipped. So this is mostly a content
change to one skill and one journey, plus one new reference file holding the two
pieces of structured data the behaviour turns on.

Order of operations: land the structured data first, because everything else
cites it — the finding-class to severity mapping and the capture-record shape.
Then the skill section that performs the capture and consumes them, then the
manifest field that records the outcome, then the journey text that promises it.
The measurement kit and the guide follow the behaviour they describe. Version bump
and projection regeneration land last, once content has stopped moving.

The riskiest part is not the behaviour; it is the two places pack content is
pinned by mechanisms this plan cannot see from the outside. `SKILL.md` may sit near
a size ceiling, and the pack's test tree does not exist yet, so nothing here
asserts where a suite must be registered to actually run. Both are handled as
discovery predicates in T0 before any content is written, because discovering
either mid-execution would invalidate the task breakdown rather than just delay it.

## Constraints

- `packs/AGENTS.md` § *Shipped pack content carries no internal-governance
  citations* — shipped content states rules directly and cites no repository-only
  path. The adopter-genericity criterion is the checkable form of this, and the
  Testing Strategy names the identifier search that bounds its reach.
- `packs/AGENTS.md` § *Version bump rule* — a non-cosmetic `.apm/**` change bumps
  matching versions in `pack.toml` and `.claude-plugin/plugin.json`, which the spec
  carries as the matching-bumped-versions criterion.
- `packs/AGENTS.md` § *Self-hosting projection* — `.apm/` is the source of truth;
  run self-host after pack edits and never edit projections directly.
- `packs/AGENTS.md` § *Writing pack tests* — load modules under a pack-and-skill
  unique name; keep cost in assertions, not processes.
- RFC-0088 governs authenticated-browser access to sites an adopter does not own.
  Out of scope here by the spec's Assumptions; nothing in this plan may introduce a
  browser runtime, profile, or credential path.

## Construction tests

**Integration tests:** none beyond per-task tests. The pack ships no runtime to
integrate; the cross-cutting checks are the catalogue gates, which are goal-based.

**Manual verification:**
- Run the capture instruction against a surface that is not this repository's —
  a local HTML file is sufficient and is the pack's own documented target — and
  record the observed findings. This is the AC-level evidence that the step works,
  and it belongs in the verification ledger.
- Run the shipped fixtures through a judge and record the resulting local
  false-positive count as a measurement, never as a published rate.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| User promise — journey step 4 and its gate | T5 | Journey text names step, output, named skip | Journey matches what an adopter receives |
| Current product truth — skill + manifest | T2, T3, T4 | `catalogue lint --deep`, `catalogue verify`, self-host projection green | Skill and projections agree |
| Adopter guidance — guide page | T6 | Guide walks the step against a non-repository surface; destination decision recorded | Destination blocker closed and guide walkable without this repository |
| Decision rationale — severity is derived | T1 | Mapping reference plus its four assertions | A reader sees why severity is derived, not asked |
| Measurement kit — fixtures + procedure | T6 | Fixtures present; local measurement recorded in the ledger | Adopter can measure their own rate |
| Reusable learning — eval harness | T7 | Harness carries a query exercising the inspection step | The harness exercises the shipped step |
| Release history — versions + changelog | T7 | Matching bumps; changelog entry checked independently of the bump | Versions and changelog agree with content |

## Design (LLD)

### Design decisions

- **The severity mapping and the capture-record shape are structured data in a
  reference file, not prose in the skill.** Traces to: the severity, top-clipping and capture-state criteria. A test can
  assert a table's completeness without pinning the surrounding prose; a test that
  asserts prose fails on every wording change and teaches authors to route around
  it. The pack's one existing reference file is the precedent for where this lives.
- **No script is added to the pack.** Traces to: the no-new-dependency criterion. The pack ships no `scripts/`
  and expresses every other tool step as a command the agent runs — `npx pa11y`,
  `npx html-validate`. A capture script would be a new runtime boundary in a pack
  that has none, and the browser the step needs is already the adopter's.
- **Capture and judgement stay separable.** Traces to: the capture-set and judgement-request criteria. The capture
  produces images plus their state records; the judgement consumes both. An adopter
  who wants a different judge substitutes one without touching the capture.
- **Rejected: a screenshot baseline.** The spec's *Ask first* covers it; the
  discovery record measured that findings naming a failure, rather than a
  difference, are what keep the step quiet on a deliberate redesign.

### Behavior & rules

The finding-class to severity mapping is the whole of the rule layer. Traces to: the severity-derivation and
top-clipping criteria. Its one non-obvious row is the at-rest top-clipping rule, which the spec carries:
content clipped or covered at the top of the content area in an at-rest capture
maps to blocking. The scrolled case is deliberately not classified here — the
contract does not state it, and a plan that classifies what the spec does not is a
rule no gate reads. The distinction is exactly what a judge cannot make from an
image alone. That is why the contract requires the scroll position in the
judgement request and refuses a finding from a stateless capture.

### Failure, edge cases & resilience

Traces to: the degradation criteria. Five families, each of which must be
distinguishable from a completed inspection — the spec requires that distinction
and no other: no browser reachable (named skip, capability named), a capture whose
state was not recorded (unusable, no finding emitted), and navigation, capture and
judgement failures. A single "unverified" bucket would collapse them, and the
unrecorded-state case would then read as an environment problem rather than a
defect in the step.

### Dependencies & integration

Traces to: the no-new-dependency criterion. The step uses the headless Chromium the accessibility step
already requires. Nothing is added to any manifest.

## Tasks

Criteria are cited by their text, not by an index. The Acceptance Criteria list is
an unnumbered checklist, so an index would decay the moment a criterion is added.

### T0: The two pinning mechanisms are known before content is written

**Depends on:** none

**Tests:** no stub (goal-based).

**Approach:**
- Resolve where a new pack test suite must be registered for it to actually run:
  inspect how an existing pack test tree is discovered and executed, and name the
  registration surface. Discovery predicate — do not assume a path. `Makefile`
  records that adding a suite directory does not by itself add it to a run class.
- Measure whether `SKILL.md` has headroom for the new section under whatever size
  or hash mechanism governs pack skill content. Measure it; do not recall a limit.
- Name the pack's declared dependency surfaces — the files a new required
  dependency would have to appear in — so the no-new-dependency check in T7 has a
  defined comparison set rather than an intention.
- If any answer forces different content placement, amend this plan before T1
  rather than routing around the mechanism.

**Done when:** three things are in the verification ledger — the registration
surface for a new pack suite, named with its evidence; the dependency surfaces,
enumerated; and, for the size question, either the governing mechanism plus the
measured headroom figure or a decisive bounded result that no such mechanism
governs. The second branch is admissible because the Approach frames the mechanism
as unknown, and a condition satisfiable by only one of a predicate's two valid
outcomes is not a completion condition.

### T1: Severity is derived from the class mapping and no judge label reaches the result

**Depends on:** T0

**Tests:**
- Every finding class named in the reference has exactly one severity. Verifies
  *severity is derived from its finding class by the mapping the pack states*.
- The at-rest top-clipping class maps to blocking. Verifies *content clipped or
  covered at the top of the content area in an at-rest capture maps to blocking*.
- A judgement carrying a severity label that conflicts with the mapping yields a
  result carrying the mapped severity and not the supplied one. Verifies *no
  severity supplied by a judge appears in the result*.
- The mutation: a row whose class field holds a recognized class name and whose
  severity field is empty must fail the suite. Stated as an exact malformed row,
  because if the class set were the mapping's own key set then "a class added
  without a severity" is unrepresentable and the assertion could never fail.
- `no stub (implementation-discovered)` — the reference file's path and the test
  module's location follow T0's answer. Discovery predicate: T0's named
  registration surface. Constraint: pack-and-skill-unique module name per
  `packs/AGENTS.md`. Required outcome: the four assertions above. Verification
  mode: TDD.

**Approach:**
- Write the reference file holding the finding classes and their severities.
- Write the suite that reads it.

**Done when:** the four assertions are green and the completeness assertion fails
under the stated mutation.

### T2: The capture set is complete and every capture carries its state

**Depends on:** T1

**Tests:**
- A capture set lacking a capture at a viewport height of at most 600 CSS pixels
  is rejected. Verifies the at-most-600 criterion and, with the next two, the
  incomplete-set criterion.
- A capture set lacking a capture at a viewport height of at least 900 CSS pixels
  is rejected.
- A capture set lacking either the zero or the non-zero scroll position at any
  captured height is rejected.
- The capture-record shape names route, viewport width, viewport height, and
  scroll position. Verifies *every capture carries the route, the viewport width,
  the viewport height, and the scroll position*.
- The stated judgement request includes the route, viewport width, viewport height
  and scroll position recorded with the capture. Verifies the judgement-request
  criterion at every one of its four members — the Always-do boundary requires that
  same context be stated to whatever judges the image, and a scroll-position-only
  check left three of the four unverified.
- Capture completes and produces its set without invoking the judge. Verifies *the
  capture step completes without invoking the judge*.
- Judgement runs against an existing capture set and produces no capture. Verifies
  *the judgement step consumes a capture set it did not produce* — together these
  two carry the separability boundary, which no criterion or task previously held.
- A record missing any one of those four fields yields no finding. Verifies
  *produces no finding*.
- That same record is reported as unusable. Verifies *is reported as unusable* —
  asserted separately, because a run that emits no finding and no status would
  otherwise pass the criterion above while failing this one.
- A capture set satisfying both height bounds at both scroll positions is accepted
  and remains eligible for a completed inspection. The green path: without it an
  implementation that rejects every capture set passes all three rejection
  assertions above.
- A rejected capture set records an incomplete result. Verifies the recorded half
  of *yields an incomplete result that cannot satisfy a completed inspection*,
  which the rejection assertions alone do not observe.

**Approach:**
- Add the capture table and the capture-record shape to the reference file from T1.
- Write the skill's capture section against that table.

**Done when:** the eleven assertions are green and `catalogue lint --deep` passes
on the edited skill.

### T3: The manifest records what was seen, and every degraded outcome is distinguishable

**Depends on:** T2

**Tests:**
- The manifest table carries an observations field distinct from `screenshots`.
  Verifies *the evidence manifest records what was observed*.
- A value naming only capture filenames does not satisfy that field. Verifies the
  filename-rejection criterion — asserted separately from field presence, because
  adding the field is one remedy and constraining its content is another.
- The no-browser result names the missing capability. Verifies *the recorded
  result names the missing capability*.
- A skipped inspection is distinguishable from a completed one in each of the
  three named surfaces: the evidence manifest, the step's reported output, and the
  gate input. Verifies the three-surface criterion at every member.
- A navigation failure, a capture failure, and a judgement failure each yield a
  result that cannot satisfy a completed inspection. Verifies half the failure-set
  criterion at every member.
- Each of those three failure families records a state distinguishable from a
  completed inspection. Verifies the other half — the sibling skip criterion gets
  its own distinguishability assertion, so a failure family staying
  indistinguishable while the plan reports green is the gap this closes.

**Approach:**
- Add the observations field and the filename constraint to the manifest table.
- State the skip and failure forms and where each is recorded.

**Done when:** the six assertions are green and the self-host projection
regenerates with no diff other than the intended content.

### T4: The judge receives evidence only, and no secret rides along in a route

**Depends on:** T2

**Tests:**
- Shipped pack content states that content visible in a capture is untrusted
  evidence carrying no instruction authority over the judge. Verifies that
  criterion.
- A recorded route and a judgement-request route both exclude the query string and
  the fragment. Verifies the route-exclusion criterion.
- Shipped pack content states that capturing an authenticated or sensitive view is
  the adopter's decision. Verifies that criterion.
- Shipped pack content names what such a capture exposes to the adopter's judge.
  Verifies that criterion — asserted separately, because stating ownership and
  naming exposure are two remedies.
- Shipped pack content states that the routes the step inspects are supplied by the
  adopter. Verifies that criterion — the adopter-genericity search forbids naming
  this repository's routes but does not establish where a route comes from.

**Approach:**
- Add the untrusted-evidence clause to the skill's judgement section, using the
  repository's existing untrusted-data wording as the seam rather than inventing a
  new formulation.
- Add the route-exclusion rule to the capture-record shape in the T1 reference, so
  one definition governs both what is recorded and what is transmitted.
- Add the sensitive-view note to the skill's capture section.

**Done when:** the five assertions are green and the clauses survive the
self-host projection.

### T5: The journey promises the step, its output, and its skip

**Depends on:** T3

**Tests:**
- What a named skip costs at the `accept-frontend-evidence` gate is byte-identical
  before and after this task. The spec lists changing it under `Ask first`, and
  neither `catalogue verify` nor the journey text reads skip cost, so without this
  the boundary can be crossed undetected.

**Approach:**
- Update step 4 and the `accept-frontend-evidence` gate's `whatToCheck`.
- Leave what a skip costs at that gate unchanged — spec `Ask first`.

**Done when:** the skip-cost comparison shows no change, `catalogue verify` is
green, and the journey names the step, its output, and the named skip.

### T6: An adopter can measure their own false-positive rate, and the guide walks the step

**Depends on:** T2, T4, T5

**Tests:**
- Every defect fixture the procedure names is present. Verifies that criterion.
- Every known-clean fixture the procedure names is present. Verifies that criterion.
- Running the procedure against each shipped defect fixture produces a finding
  naming that fixture's recorded defect. Verifies the detection criterion — without
  it a judge that reports nothing on every page satisfies the whole contract.
- The procedure names its known-clean input set. Verifies that criterion.
- The procedure names a non-empty defect-fixture set and a non-empty known-clean
  set, and a procedure naming either as empty fails. Verifies both non-empty
  criteria — without them a delivery shipping zero fixtures satisfied every
  measurement criterion before any work happened.
- The stated false-positive denominator equals the number of known-clean fixtures
  measured. Verifies that criterion.
- The procedure names the denominator the rate is computed from. Verifies that
  criterion — a rate measured over defect-only fixtures answers a different
  question than the criterion asks.
- The complete procedure is present in shipped pack content, not only in the guide
  or the ledger. Verifies *the pack states a procedure*.
- A search for a number adjacent to any term in the pack-stated rate vocabulary
  returns nothing in shipped pack content. Verifies *no shipped pack content
  states a detection rate or a false-positive rate*.
- A search for the stated set of this repository's identifiers returns nothing in
  shipped pack content. Verifies *no shipped pack content names this repository's
  sites, routes, build directory, or test harness*. Reach is shipped pack content,
  matching both the criterion and the guard boundary the constraint below accepts;
  the guide page is covered by its own walkability check, not by this search.
- `no stub (implementation-discovered)` — reuse an existing portability guard over
  `packs/**` if one exists; author one only on a decisive empty result. Discovery
  predicate: one bounded search for an existing shipped-content portability guard.
  Constraint: the guard's source boundary must cover every path this delivery ships
  under `packs/frontend-engineering/` including the fixtures, or it is not a reuse.
  Required outcome: an empty result for the stated identifier set over that
  boundary. Verification mode: goal-based if an existing guard covers it, otherwise
  TDD.

**Approach:**
- Ship the defect fixtures as reproducible page sources with the defect each carries.
- Ship the known-clean fixtures the rate is measured over.
- State the procedure in shipped pack content, including its clean input set, its
  denominator, and the rate vocabulary the first search uses.
- Decide the guide destination against the tree as it then stands, record that
  decision, and write the page against a local file surface.

**Done when:** every assertion above is green; the procedure as it appears in
shipped pack content runs end to end over both fixture sets, naming each recorded
defect and producing a false-positive count over the clean set, with that outcome
recorded in the verification ledger; the guide destination decision is recorded;
and the selected guide page exists and walks the inspection step end to end against
a non-repository surface, which is the closeout condition the durable-output map
already carries for it.

### T6a: A page that cannot scroll is recorded, not marked incomplete

**Depends on:** T6

Added 2026-09-13 by controlled contract amendment under owner authority. T6's
end-to-end run measured 17 of 32 captures unable to reach a non-zero scroll
position because the page is shorter than the viewport, which made every such
page permanently `incomplete`. T2's completed sections are preserved; this is
the dependency-ordered correction rather than an edit to them.

**Tests:**
- A capture set whose scrolled capture is absent but whose record carries
  `page-scrollable: no` at that height is complete. Verifies the amended
  scroll criterion's new branch.
- A capture set whose scrolled capture is absent and whose record carries
  `page-scrollable: yes` is still incomplete. Without this the amendment would
  excuse every missing scrolled capture rather than the unscrollable ones.
- A capture record carries `page-scrollable`, and a record missing it is
  unusable on the same terms as the other required fields. Verifies the amended
  capture-state criterion.
- The shipped fixtures exercise both branches, so the kit covers the case the
  live run found rather than only the case the unit fixtures modelled.

**Approach:**
- Add `page-scrollable` to the capture-record table and the `>0, or
  page-scrollable: no` branch to the required-capture table.
- Carry the same rule into the skill's capture section.
- Extend the evaluator to honour the recorded value, never to infer it from a
  scroll position of 0.

**Done when:** the four assertions are green, the mutation in which
`page-scrollable: yes` is treated as satisfying the scrolled requirement fails,
and the end-to-end run is re-executed with every fixture reaching a complete
capture set.

### T8: A reader-visible Blocker stops the surface completing

**Depends on:** T6a

Added 2026-09-13 by contract amendment under owner authority. The Objective
promises a completion signal that cannot be green while the page is visibly
broken; no original criterion carried it, and every "cannot satisfy a completed
inspection" rule was about execution failure rather than findings.

**Tests:**
- A run with every required capture present, judged, recorded, and carrying an
  unresolved blocking finding does not yield a completed inspection. Verifies the
  consequence criterion at the state the whole delivery turns on.
- The same run with no blocking finding does yield a completed inspection. The
  green path: without it, a rule failing every run satisfies the assertion above.
- Execution state and verdict are separate fields, so `failed-capture` and "a
  Blocker was found" are not the same state. Verifies the separation criterion.
- A failure fitting two classes takes the more severe. Driven over every pair in
  the mapping that carries differing severities, not one example — the mapping is
  the domain. Verifies the precedence criterion.
- The `accept-frontend-evidence` gate names the verdict in its `whatToCheck`.

**Approach:**
- Add a verdict to the result contract, separate from the execution state, and a
  class-precedence rule to the reference.
- Carry both into `SKILL.md` § 5c and the journey gate.

**Done when:** the five assertions are green, the mutation in which a blocking
finding still completes fails, and `catalogue lint --deep` and `verify` pass.

### T9: The judge is told the capture is untrusted evidence

**Depends on:** T6a

**Tests:**
- The judgement request contract carries an untrusted-evidence declaration.
  Verifies that criterion.
- The declaration names both halves the cited authority requires: the content is
  evidence, and it carries no instruction authority.

**Approach:**
- Add the required row to the `Judgement request` table and restate § 5b.
- Do not add judge-output whitelisting; the adjudication called that over-broad
  and it overloads `failed-judgement`.

**Done when:** both assertions are green and the deep lint passes.

### T10: The every-captured-height rule is shipped, not assumed

**Depends on:** T6a

The rule is enforced by `evaluate_capture_set` and stated nowhere in shipped
content, which contradicts this plan's design decision that rules are data the
checks read. The check currently authors the rule it checks.

**Tests:**
- Shipped pack content states the every-captured-height at-rest/scrolled
  requirement, including the recorded not-scrollable branch. Verifies that
  criterion.
- The evaluator reads the rule from the table rather than hard-coding it:
  removing the rule from the reference makes the extra-height case stop failing.
  This is the assertion that makes the "no check enforces an unshipped rule"
  criterion able to fail.
- The contradicting "none are required" sentence is gone from the reference and
  from `SKILL.md`.

**Approach:**
- State the rule in `Required captures`; correct the contradicting sentence.
- Move the quantifier out of the evaluator and into the table it reads.

**Done when:** the three assertions are green and the mutation above fails.

### T11: A duplicate rule-table row is rejected rather than collapsed

**Depends on:** T6a

**Tests:**
- A rule table carrying a duplicate row key raises rather than silently keeping
  the last row. Verifies that criterion.
- With the duplicate rejected, the existing one-severity-per-class assertion
  fails on a conflicting duplicate class row — which it cannot do today.
- The pipe policy is stated explicitly rather than left to `split`.

**Approach:**
- Reject duplicate keys in the shared table reader; state the pipe policy.
- Take only the minimum the adjudication named; the wider validation set is a
  defensible owner choice and is not in scope.

**Done when:** the three assertions are green.

### T12: The independent reviewer can see the page

**Depends on:** T8, T9, T10

This is the part the intent named and the original spec scoped out: the reviewer
reads a diff, and nothing in a diff shows one element covering another.

**Tests:**
- `frontend-reviewer`'s seed contract names the capture set and the observations.
  Verifies that criterion.
- Its lens set includes reader-visible layout failure, taking severity from the
  pack's finding-class mapping. Verifies that criterion.
- Its declared tools let it capture a page itself. Verifies that criterion.
- Shipped reviewer content states it does not write to the repository under
  review. Verifies that criterion, and is the mitigation for the residual risk
  the ledger records.
- The work-loop's dispatch line for this reviewer passes the capture set, not
  only the diff and the manifest state. Without this the seed contract is
  aspirational.

**Approach:**
- Widen the seed section and the lens list in
  `packs/frontend-engineering/.apm/agents/frontend-reviewer.md`; add Bash to its
  tools with a stated capture-only, no-write constraint.
- Update the dispatch line in `packs/core/.apm/skills/work-loop/SKILL.md` — the
  source, not the `.claude/` projection — and regenerate self-host.

**Done when:** the five assertions are green, `catalogue lint --deep` and
`verify` pass for both packs, and the self-host projection regenerates.

### T7: Eval harness, versions, changelog, and dependency surfaces agree with the shipped content

**Depends on:** T1-T6a, T8-T12

**Tests:** no stub (goal-based).

**Approach:**
- Update the skill's eval harness so it exercises the inspection step, per
  `packs/AGENTS.md` § *Security and authoring rules*.
- Bump `pack.toml` and `.claude-plugin/plugin.json` to matching versions.
- Add the changelog entry.
- Compare the dependency surfaces T0 enumerated against their pre-change state.
- Run self-host and the catalogue gates a final time.

**Done when:** all five hold, each checked independently — `catalogue lint --deep`,
`catalogue verify`, and self-host are green; the two manifests carry the same
bumped version; `docs/product/changelog.md` carries an entry naming that version;
the eval harness carries a query exercising the inspection step; and the
dependency-surface comparison shows no newly required dependency.

## Rollout

- **Delivery:** pack content only. An adopter receives it on their next install or
  update; nothing is flagged, staged, or migrated.
- **Infrastructure:** none. No runtime, no dependency, no credential path.
- **External-system integration:** none.
- **Deployment sequencing:** the version bump lands after content, in T7, so the
  published version never names content that did not ship with it.
- **Reversibility:** fully reversible. Rollback is reverting the whole pack-content
  change — skill sections, reference file, manifest field, journey text, fixtures,
  guide page, eval-harness query, version bumps and changelog entry — and
  regenerating the self-host projection. Nothing persists and nothing is migrated.

## Risks

- **A pinning mechanism forces a different content shape.** `SKILL.md` size or a
  content hash could make the new section land elsewhere. T0 exists to find this
  before the breakdown depends on it.
- **The new pack suite does not actually run.** The pack has no test tree, so a
  suite could be added, pass locally, and never execute in any gate. T0 names the
  registration surface; without that evidence T1's tests are decoration.
- **The portability assertion is weaker than its claim.** The adopter-genericity
  criterion is universal, and a
  search-based guard only covers the identifiers it searches for. T6 states the
  identifier set as the mechanism, so the claim's reach is visible rather than
  implied.
- **Prose-pinning brittleness.** Asserting against skill prose rather than the
  structured reference would make every wording change a test failure. The design
  decision to hold the rules as data is what keeps this risk closed.

## Changelog

- 2026-09-13: amended under owner authority after T6's end-to-end run — added
  T6a for pages that cannot scroll, which the shipped capture rule marked
  permanently incomplete.
- 2026-09-13: amended under owner authority after the specialist reviews — the
  Objective's promise had no acceptance criterion, and the owner took all four
  parts of the reviewer fix. Added T8-T12.
- 2026-09-13: initial plan.
- 2026-09-13: revised from the round-4 adjudications — shrank the judge-severity
  criterion to the provenance claim its check verifies, admitted both valid outcomes
  of T0's size-mechanism predicate, and put the guide walk in T6's completion
  condition rather than only in its durable-output row.
- 2026-09-13: revised from the round-3 adjudications — required non-empty fixture
  populations so the measurement criteria stop holding on empty state, widened the
  judgement-request criterion from scroll position to all four recorded fields,
  gave the separability and adopter-route boundaries criteria and checks, pinned
  T1's mutation to a representable malformed row, and narrowed the reviewer-seam
  claim to a follow-on.
- 2026-09-13: revised from the round-2 adjudications — added the detection criterion and
  the clean-fixture set and denominator the false-positive rate is measured over, gave
  T2 a green path, gave each failure family a distinguishability assertion, assigned the
  eval-harness rule to T7, and made T6 depend on T4.
- 2026-09-13: revised from the pre-EXECUTE adversarial and security adjudications —
  split every conjunctive criterion, added the verifications three contract-tier
  criteria lacked, added T4 for the untrusted-evidence clause, extended T3 to the
  full failure set, and replaced AC index references with criterion text.
