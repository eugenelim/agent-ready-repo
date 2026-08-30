# Spec: spec-authoring-discipline

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none
- **Contract:** none — this feature changes authoring guidance, not an interface surface

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

An author using `new-spec` writes acceptance criteria that a reviewer can
converge on. Twelve authoring failures currently survive to review and consume
rounds there: an acceptance criterion holds several contracts at once, so no
reviewer can tick it honestly; a numeric limit is stated without the facts that
make it enforceable; two limits are stated over one quantity with no account of
which fires first, so one of them is unreachable; a limit is stated without the
origin it is measured from, so it changes verdict when the subject is
rearranged; a limit's value is delegated to whoever implements it; a refusal
contract is written from imagination and never run against a real input; a rule
is restated in several documents that then disagree; the review loop only ever
adds; a claim that merely explains survives while a claim that is the only
oracle gets cut; a criterion states the mechanism instead of the outcome; a plan
bullet restates a criterion instead of naming a mechanism; and a plan that draws
under-specification findings is extended rather than reduced. The skill now
names each failure at the point of authoring, and schedules the one pass that
removes work rather than adding it.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Maintainer authoring procedure | Applicable — the skill body *is* the procedure surface these rules live on | `packs/core/.apm/skills/new-spec/SKILL.md`, `packs/core/.apm/skills/new-spec/assets/spec.md` | new-spec skill owner | Contract tests in `packs/core/tests/skills/new-spec/` green; projections byte-identical to source by directory `diff -rq` | Each rule resolves to one owning file and its test reds under mutation |
| Release history | Applicable — a published core pack content change | `docs/product/changelog.md` | Maintainer | A `## [core][2.15.3]` section directly beneath `## [Unreleased]`, agreeing with `packs/core/pack.toml` and `packs/core/.claude-plugin/plugin.json` | Version agrees across all three files in one commit, and the entry's `Highlights` disposition is recorded — drafted bullets, or `none` with its reason in the PR's *what did you not change* answer |
| Reusable learning | Applicable — the rules are distilled review experience | `docs/knowledge/` via the `project-knowledge` public capture seam | `work-loop` semantic gates | Capture receipts returned at `spec-approved` and `plan-locked` | Receipts distilled at `plan-locked`; journal diff passes a verification barrier |
| User-facing promise | Not applicable beyond release history — the reader of these rules is the agent executing `new-spec`, and no separate guide owns AC-shape rules. `guides/core/explanation/why-the-plan-owns-the-lld.md` was read whole; it is genre-explanation that narrates the AC rules and cites rather than owns them, so it needs no refresh | — | — | — | — |
| Current architecture, decision rationale | Not applicable — no module boundary, dependency, or prior decision changes; AC8 extends the one-canonical-home doctrine `SKILL.md` step 8 already carries | — | — | — | — |
| Interface compatibility, operations | Not applicable — the change is additive authoring guidance with no runtime, schema, or engine surface | — | — | — | — |

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Edit `packs/core/.apm/skills/new-spec/**` as the only source, then regenerate
  the `.claude/` and `.agents/` copies with the full chain in `plan.md` T5.
- State each new rule in exactly one file and cite it elsewhere by file and step
  identifier — the change must satisfy AC11 about itself.
- Update this skill's eval harness alongside its content, per the scoped rule in
  [`packs/AGENTS.md`](../../../packs/AGENTS.md).
- Run `make ci`, not only `make build-check`, because this change bumps a pack
  version and edits a changelog.

### Ask first

- Adding any of these rules to a pack primitive other than the `new-spec` skill —
  another skill, or a subagent, command, or hook under `packs/*/.apm/`. The
  nearest such host is `packs/core/.apm/agents/adversarial-reviewer.md`, whose
  spec-stage checklist could carry a review-time pointer; that is a scope
  decision, not an implementation detail.
- Adding a mechanical checker for any of these rules, in any location.
- Reintroducing a numeric threshold for criterion size, in the shipped guidance
  or a checker.

### Never do

- Add an editorial rule from this change to `packages/agentbundle/**` — including
  `pack.schema.json` and `lint_packs` — which ships inside the published package
  and runs against third-party catalogues, so an editorial rule there exports
  this repository's taste as a hard failure in an adopter's build. That tree also
  refuses a changeset without an `Engine-Change-RFC:` trailer. *(structural)*
- Wire any of these rules into `lint-spec-status.py`, `pre-pr.py`, or any other
  lint projected into an adopter repository.
- Introduce a new top-level directory, module boundary, abstraction layer, or
  dependency. *(structural)*
- Hand-edit the `.claude/` or `.agents/` projections, or
  `web/src/lib/now-highlights.generated.json`.

**Non-goal.** A mechanical checker for criterion independence is not built here and is not registered as follow-on work. It would never belong in the published package. The *Ask first* entry above routes any future checker to human sign-off.

## Testing Strategy

- **Every rule's presence and single ownership (AC1, AC3–AC12, AC16–AC22) — goal-based check.** Each rule's normative phrasing is asserted against
  the whitespace-flattened body of its owning file by a contract test in
  `packs/core/tests/skills/new-spec/`, following the idiom at
  `packs/core/tests/skills/new-spec/test_repository_anchors.py:11`. The mode is
  goal-based rather than TDD deliberately: the subject is document text, and the
  assertion is a grep, not a compressible logic invariant — so there is no red
  stub to materialise at PLAN, and none is required.
- **The worked examples and the rule's smoke gate (AC2) — goal-based check.**
  Every example in AC2's set is present with its identifier, verdict and reason,
  and the shipped rule wording is run against the whole set before T3 pins any
  phrasing. A wording that misclassifies any example is rejected rather than
  pinned; this gate, not AC2's prose, is where the rejection happens.
- **Detectability (AC13, AC14) — goal-based check.** One mode only. For each rule,
  delete its sentence from the owning file, observe the named test fail, restore
  the text. A prose pin that survives deletion of the prose is the
  control-that-cannot-fail shape, so the recorded mutation is the evidence.
- **Eval harness (AC15) — goal-based check.** The added eval's presence, unique
  `id`, and field shape are asserted structurally by the same contract-test file.
  The harness is not executed here: a model-graded eval is not a deterministic
  gate, and `packs/AGENTS.md` obliges updating the harness, not proving it.
- **Portability of added pack prose — manual check, recorded.** `git diff` of
  `packs/**` grepped for `docs/`, `workspace.toml`, and `AC<n>` over *added*
  lines only, with the result recorded. This cannot be a contract test: `SKILL.md`
  already contains `docs/specs/<feature>/` and `docs/product/briefs/<slug>.md`,
  so a whole-file assertion is either vacuous or red.
- **The guidance's own usability — manual QA.** This spec was authored under its
  own rules. Record which rules fired while writing it and what each changed.

## Acceptance Criteria

<!-- One contract each. The cross-file "stated once" fact is owned by AC11 and is
not repeated in the criteria it governs. AC10 carries its own non-restatement
clause because a step-4 pointer restating a rule owned by a later step of the
same file is intra-file, which AC11's cross-file assertion cannot reach. -->

- [x] **AC1 — the template states the criterion-independence rule.**
  `packs/core/.apm/skills/new-spec/assets/spec.md`'s `## Acceptance Criteria`
  guidance states that a criterion is more than one when its parts have separate
  failure modes with separate remedies; that where the parts read as one
  constraint over a set, the author rewrites the criterion as a single predicate
  with a member substituted in, and it stays one criterion only if that predicate
  is checkable as written at every member rather than expanding into a different
  check per member; and that the worked examples fix where the boundary falls.
- [x] **AC2 — the template carries five worked examples that fix the rule's
  boundary.** Each carries a stable identifier, its verdict, and the reason it
  holds: E1 two contracts joined by "and" (splits); E2 one predicate applied
  across an enumerated set (stays one); E3 one comparison value expressed in
  parts (stays one); E4 two contracts framed as a single constraint over a domain
  (splits); E5 parts with different failure modes but one substitutable predicate
  and a shared remedy (stays one). The set is normative: it, not an adjective
  inside the rule, decides the boundary.
- [x] **AC3 — `SKILL.md` cites the independence rule by its owning file and
  section.**
- [x] **AC4 — the template requires a bound ledger for each stated numeric
  limit.** For every limit a criterion states, it records which input makes the
  limit fire first and the enforcement mechanism that makes that ordering true;
  a limit missing either fact is not yet a criterion.
- [x] **AC5 — the template resolves two limits over one quantity.** Where one
  quantity carries two limits, the criterion either orders them so each is
  reachable for some input, or declares one non-binding on that route and names
  the limit that fires instead.
- [x] **AC6 — `SKILL.md` requires a corpus oracle before a refusal contract over
  externally authored input is finalised.** When the spec's subject is
  third-party, untrusted, or otherwise externally authored input, the author
  drafts into the plan's first tasks a corpus task that runs the specified rules
  against recorded real inputs and records the resulting accept and reject
  counts, before finalising any criterion that specifies a refusal.
- [x] **AC7 — `SKILL.md` requires an unreachable corpus to be recorded, not
  passed over.** When no corpus is reachable, that absence is recorded as an
  Unverified assumption under step 3.
- [x] **AC8 — `SKILL.md` step 8 requires a rule a criterion depends on to be
  cited by document and identifier rather than restated.**
- [x] **AC9 — `SKILL.md` step 8 requires a duplicated rule to be resolved.** On
  finding one rule stated in two places, the author records which statement is
  the owner and reduces the other to a cross-reference.
- [x] **AC10 — `SKILL.md` step 4 carries pointers to every rule that applies
  while criteria are being written**, including those owned by later steps and by
  the template, restating none of them.
- [x] **AC11 — nothing introduced by this change is stated in more than one of
  the three source files.** For each rule and for each worked example, a
  contract test asserts its text is present in its owning file and absent from
  the other two of `SKILL.md`, `assets/spec.md`, and `assets/plan.md`. Examples
  are included because a copied example drifts exactly as a copied rule does.
- [x] **AC12 — `SKILL.md` step 6 schedules one deletion pass.** After the review
  rounds converge and before human approval is requested, the author runs one
  explicit pass over every criterion and task added during review, asking of each
  whether the accepted contract requires it or a reviewer's remedy invented it,
  whether it contradicts a stated non-goal, and whether it traces to a criterion
  at all, then takes the cuts to the human with conformance fixes separated from
  scope calls.
- [x] **AC13 — a contract test pins every rule's normative phrasing** against the
  whitespace-flattened body of its owning file, in
  `packs/core/tests/skills/new-spec/`.
- [x] **AC14 — every rule's removal is caught, and the proof is recorded.** For
  each rule the phrase is deleted from its owner, the named test is observed
  failing, and the file is restored; a rule whose test still passes once the rule
  is deleted does not ship.
- [x] **AC15 — the skill's eval harness exercises the new rules.**
  `packs/core/.apm/skills/new-spec/evals/evals.json` gains at least one eval whose
  prompt presents a criterion bundling two contracts, a numeric limit with no
  stated firing order, and a rule already owned by another document, and whose
  assertions require the agent to split the criterion, demand the bound ledger's
  two facts, and cite the owning document rather than restate the rule.
- [x] **AC16 — the template requires a claim to earn its place by making a wrong
  implementation detectable.** It requires deleting a claim that does not help
  establish the outcome — rationale, history, reassurance, restated context, or a
  figure that merely explains where a threshold came from — while keeping any
  claim that is the only written form of a comparison value, such as a byte
  layout, an exact key order, a literal token, a collection floor, or a stated
  bar, and states the test as "could a wrong implementation now pass this?".

- [x] **AC17 — the template requires a stated limit to name its origin.** A
  criterion stating a limit names the reference point the limit is measured from,
  and that origin is chosen so the same input yields the same measurement however
  the subject is organised. A limit whose origin is unstated is not yet a
  criterion, because a limit measured from a movable point silently changes
  verdict when the subject is rearranged.
- [x] **AC18 — the template forbids delegating a limit's value.** A criterion
  that requires a limit states the limit's value; it never asks an implementer to
  supply one. A value invented to satisfy an unspecified requirement is worse
  than an absent limit, because it reads as a decision that was made.
- [x] **AC19 — the template states the criterion-level mechanism give-away.** The
  `## Acceptance Criteria` guidance states that a criterion names an observable
  outcome, and that naming a function's parameters, a helper, or a call sequence
  is the give-away that the content belongs in the plan.
- [x] **AC20 — `SKILL.md` step 5 states that the plan carries mechanism, never a
  restatement of the spec's obligations.** A `Tests:` bullet names what the
  implementer cannot infer — which suite proves a property and where it lives,
  which fixture carries which join key, which shipped assertion this change
  moves — and never repeats a criterion, because the criteria are the checklist
  and a repeat creates a second home with nothing keeping the two in sync. The
  author's cue is a paste test over the whole plan except `## Constraints` and the
  durable-output map, which cite the spec by design: if a passage could be moved
  into the spec without looking out of place, it is either already there or
  belongs there, and either way it does not belong in the plan.
- [x] **AC21 — `SKILL.md` step 6's convergence rule names the plan as well as the
  spec.** When a reviewer keeps finding under-specification in the plan rather
  than defects in the spec, the plan is over-specified: the author reduces it
  rather than extending it, and does so before the existing three-pass
  escalation, which remains the route when reduction does not converge.
- [x] **AC22 — the template gives the conjunction cue as the author's first
  check.** It states that a criterion needing "and" to join two *different
  predicates* is two criteria, because a conjunction is where a coverage check
  silently passes while half the criterion is unimplemented. The cue is scoped to
  predicates, not to checkable properties, so it stays silent on one predicate
  applied across an enumerated set; where cue and examples conflict, the examples
  govern.

## Assumptions

- Technical: the single source for this skill is
  `packs/core/.apm/skills/new-spec/`, and the `.claude/` and `.agents/` copies are
  byte-identical projections of the whole directory (source: `diff -rq` over
  `packs/core/.apm/skills/new-spec` against `.claude/skills/new-spec` reported no
  differences). The directory carries six files, so any parity check is
  directory-level rather than a hand-listed file set.
- Technical: the spec template exists in exactly three files, all projections of
  one source (source: `grep -rln 'One paragraph. What are we building'` returned
  the source plus the two projections and nothing else).
- Technical: no numeric threshold for criterion size ships, because no numeric
  detector is portable across spec shapes. Measured over 6,062 criteria in 409
  specs: a 150-word trigger fires on 0.0% of `ui` criteria and 13.8% of `data`
  criteria, and 35% of over-150 criteria are structural enumerations that are one
  contract with many parts. Word count, sentence count, and identifier count
  spread 2.9x, 3.2x, and 2.3x across shapes respectively; excluding enumeration
  items and counting prose sentences spreads 2.7x while still firing on `ui`
  (source: probe over `docs/specs/*/spec.md`, recorded in `plan.md` T1).
- Technical: the bound-ledger rule has a small blast radius — 111 criteria (1.8%)
  state at least one numeric limit and 29 (0.5%) state two or more — so AC4 is
  written as a conditional obligation rather than a field every criterion carries
  (source: same probe).
- Technical: AC8 codifies majority practice rather than inventing one — 4,013 of
  6,062 criteria (66.2%) already cite an owning identifier (source: same probe).
- Technical: contract tests for this skill's prose pin whitespace-flattened
  substrings of the owning file (source:
  `packs/core/tests/skills/new-spec/test_repository_anchors.py:11`).
- Technical: the eval harness is two files, and only `evals/evals.json` needs an
  entry. These rules change no routing or trigger surface, and
  `evals/eval_queries.json` holds `{"query", "should_trigger"}` routing records
  only (source: read of both files).
- Process: this change is a **patch** — `2.15.3`, applied on top of `2.15.2`
  after a mid-flight rebase onto a main that had released two further minors.
  The owning rule is
  `packs/AGENTS.md` § *Version bump rule*: patch for changed content, minor for
  new primitives, major for removals. This change adds rules to an existing skill
  and introduces no new skill, subagent, command, or hook. The two most recent
  minors are consistent: 2.13.0 added the `close-work` skill and 2.12.0 added
  agent primitives under `.apm/agents/` (source: `packs/AGENTS.md:44-47`;
  `git show --stat be51a9847` and `eebd162f7`). An earlier reading of this spec
  inferred a minor from changelog section headings alone; the scoped rule is the
  owning source and governs.
- Process: a non-cosmetic pack content change must also update that pack's eval
  harness (source: `packs/AGENTS.md` § *Security and authoring rules*), which is
  why AC15 exists.
- Process: shipped pack content carries no citation of this catalogue's records,
  criteria, or repository-only paths (source: `packs/AGENTS.md` § *Shipped pack
  content carries no internal-governance citations*). This is why the corpus
  measurement lives in this spec and in `plan.md` T1, and why no measured figure
  appears in any sentence added under `packs/`.
- Process: a version or changelog change requires `make ci`, because the CI job
  named `make build-check` runs steps the local target does not (source:
  `docs/knowledge/topics/` topic
  `local-make-build-check-does-not-run-what-ci-build-check-runs`).
- Process: `plan.md` is byte-pinned from `approve-plan` until the run's final
  cohort verb, so its tasks are already `### T<n>` headings and it must not be
  edited between the approval pair (source: `docs/knowledge/topics/` topic
  `plan-md-is-byte-pinned-from-approve-plan-until-the-run-s-final-cohort-verb`).
- Process: the `project-knowledge` store holds no pending observations — all 18
  captured observations carry a disposition — so the rules are a distillation
  already made, not one this change must perform (source: probe over
  `docs/knowledge/observations/*/*.jsonl` reconciling `observation.captured`
  against `observation.dispositioned`).
- Process: parallel sessions are carrying YAGNI work that will also touch
  acceptance-criterion claim handling. Those sessions reconcile against AC16's
  owning location, the template's `## Acceptance Criteria` guidance block; this
  spec does not wait on them (source: user confirmation 2026-08-28).
- Product: the rules are the user's distillation of a spec review that ran
  roughly 15 rounds and produced about 60 findings, in which the longest criteria
  absorbed most findings, five consecutive rounds produced dominated bounds, 24
  criteria specified refusals with none specifying real-input success, one rule
  reached seven disagreeing copies, and nine rounds proposed zero deletions until
  asked (source: user confirmation 2026-08-28).
- Process: a concurrent session also proposed two numeric size smells — plan/spec
  line ratio and Tests/Approach line ratio, both flagged at 2.3x. Measured over
  358 spec-and-plan pairs here, 2.3x is the 88th percentile, so the signal is
  real but the constant is tuned to one document. It ships in parameter-free
  form instead: AC20's paste test detects the same defect (the plan carrying
  facts the spec owns) with nothing to calibrate, and AC21 catches the review
  symptom. No ratio is shipped (source: probe over `docs/specs/*/{spec,plan}.md`;
  user confirmation 2026-08-28).
- Process: a concurrent session's distilled learnings propose a ~150-word
  criterion cap. It is deliberately not adopted: measured across this
  repository's corpus the threshold is not portable, and that session's own
  criteria ran 267-365 words against a local median of 86 where the repository
  median is 33, so the figure is calibrated to one document's house style. The
  causal mechanism that session identified — a fix inside a long criterion lands
  in one clause and silently contradicts another — is adopted, as the rationale
  behind AC1's split-on-separate-remedies rule (source: user confirmation
  2026-08-28; peer-session learnings relayed by the owner).
- Product: AC17, AC18, AC19 and AC20 come from concurrent sessions' distilled
  learnings, relayed and approved by the owner. A proposed freeze-time licence
  for incomplete task file lists was cut: `SKILL.md`'s existing specificity rule
  already says "where they're known", which licenses omitting paths and symbols
  that are unknown while a task is drafted. That rule does not reach a file list
  still incomplete when `plan.md` becomes byte-pinned at `approve-plan`; that
  case is knowingly unaddressed here (source: user confirmation 2026-08-28).
- Product: criterion independence ships as a structural test rather than a word
  count, because length is a stack-dependent proxy for the real defect — several
  contracts in one checkbox — and the measured evidence above shows no threshold
  generalises (source: user confirmation 2026-08-28).
- Product: the AC16 minimality rule is codified in the `new-spec` template only.
  A `docs/CONVENTIONS.md` § 4 change is a repository-wide convention change and
  is out of scope here (source: user confirmation 2026-08-28).
