# Spec: Agent Skill Engineering Composition Fixtures

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [`RFC-0097`](../../rfc/0097-agent-skill-engineering.md)
  § *Experiment / validation*, Gate 2's M2 expanded measure;
  [`Agent Skill Engineering Composition Floors`](../agent-skill-engineering-composition-floors/spec.md)
- **Brief:** docs/product/briefs/agent-skill-engineering.md
- **Discovery:** none
- **Contract:** none — the semantic provider request/response contract is
  untouched.
- **Shape:** mixed

> **Hard dependency.** This slice depends on the composition floors slice, whose
> portable floors are the corpus the two fixtures grade against. That dependency
> is recorded as satisfied in the Assumptions below. The `Status` field above,
> not this banner, carries the authorization to implement.

## Objective

The pack's graded behavior evidence covers every representative task fixture
RFC-0097's Gate 2 M2 expanded measure names. The two that measure composition —
subagent composition and hook/plugin design — are declared cases of the
authoring workflow, each posed as a read-only framing task over a payload the
case names, each seeding the defects the shipped composition floors govern, each
declaring the pattern identifiers it exercises alongside its checklist items,
and each graded from an observation taken apart from authoring.

The audience is the maintainer who has to decide whether the pack's composition
guidance survives contact with a real authoring request. Success is that the
answer is a recorded verdict per declared assertion, readable against a retained
transcript of the response it was read from, rather than an inference from the
corpus being present.

This slice adds no corpus topic, no runtime profile, and no authoring mode. It
records what the fixtures measured; asserting that the measure is met belongs to
the closeout slice.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Operations — retained observation | A verdict with no readable response behind it cannot be distinguished from a copied one, so the round's transcripts are retained rather than discarded. | `docs/specs/agent-skill-engineering-composition-fixtures/notes/` | This spec | One retained transcript per graded case, each matching the digest its record carries | Every graded record's digest recomputes against a retained transcript in the tree |
| Verification record | An observation produced by execution belongs in the sibling ledger, never in an approved artifact. | `docs/specs/agent-skill-engineering-composition-fixtures/notes/verification-ledger.md` | This spec | The base-freshness verdict and the base commit the comparison sets are read from; every inherited verdict that moved, with its prior and measured value; each exemption's authority fields; each enumeration's mutation proof; every advisory reading and operator attestation the Testing Strategy names; every observed gate failure | No required observation lives only in a commit message or an approved artifact |
| Interface compatibility | The pack's shipped `.apm/` tree gains two eval declarations and two payloads, which the version-bump rule treats as changed content. | `packs/agent-skill-engineering/pack.toml` and `.claude-plugin/plugin.json`, edited in lockstep; the aggregated marketplace manifest, which is a projection of them | This spec | Both authored manifests carry the same bumped version; publication and roster gates green | Both authored manifests agree, and regenerating the aggregate leaves it unchanged |
| Release history | The pack version bump is a released-artifact change. | `docs/product/changelog.md` — an `agent-skill-engineering` entry at the bumped version | This spec | Entry present in the same change that bumps the manifests, and topmost for this pack | Entry names the two fixtures and the re-measurement of the inherited results |
| Current architecture | RFC-0097 requires each delivery spec to update the planned architecture with its slice's implemented names, paths, dependency edges, and verification evidence. | `docs/architecture/agent-skill-engineering.md` | This spec | All four of those fields for this slice; the document stays `PLANNED` | The record claims no later-slice surface and no gate verdict |
| Spec index | The index row states this spec's shape and counts. | `docs/specs/README.md` | This spec | Row's criterion and task counts equal this document's | Row matches the shipped spec |
| Product provenance | The brief's Spec map is the derived status surface for this slice. | `docs/product/briefs/agent-skill-engineering.md` § *Spec map* | This spec | A row carrying this spec's bare slug | The row resolves under brief-coverage lint |
| Current product truth | The pack README states what the pack's evaluation evidence covers. | `packs/agent-skill-engineering/README.md` | This spec | Any sentence naming the behavior-fixture set agrees with what shipped, or the README states no such claim | No README sentence states a fixture inventory or absence the pack no longer has |
| Lifecycle record | The slice writes its own registration and status, so the Gate 2 prohibition must reach those artifacts too. | `workspace.toml` — the `["ini-009".work]` entry and the `["ini-009"]` milestone string — and the `Status` tokens in this spec and its plan | This spec | The registration resolves under canonical preflight; the projection emits no `impossible_transition` | Registration, milestone, and both status tokens agree at close |
| Reusable learning | Work-loop's `spec-approved` and `plan-locked` gates capture authoring residue. | `project-knowledge` public seam | work-loop | Capture receipts, or the named skip `project-knowledge unavailable` | Receipts distilled at `plan-locked`, or the skip recorded |

## Boundaries

### Always do

- Pose each new case as a read-only framing task over the payload its own
  declaration names, and declare for it the marker set its closest inherited
  sibling declares.
- Hold authoring, execution, and grading in three separate contexts. The
  executing context receives the prompt and the payload — the payload carries
  the seeded defects, and finding them unaided is the thing being measured.
  What is withheld from it is the authoring material *about* the payload: the
  assertion list, the pattern identifiers, and any statement of which defects
  were seeded or what a good answer names. Those go only to the grading
  context.
- Retain the transcript of every graded response, and bind each verdict to the
  transcript it was read from and to the digests of the skill body and payloads
  that produced it.
- Read every comparison set that describes the state before this slice from the
  base commit rather than from the working tree, so the change under test cannot
  supply its own baseline.
- Re-measure any recorded evidence whose covered content changed. A digest that
  moved is re-measured, never re-stamped onto the earlier observation.
- Widen a pinned enumeration in the same change that widens the set it pins.

### Ask first

- Adding a known-miss exemption to a graded case after seeing its verdict.
- Adding a corpus topic, retrieval case, authoring mode, or runtime claim in
  service of making a fixture pass.
- Changing a declared assertion, prompt, pattern identifier, or expected output
  after a measurement is in hand.
- Extending the pattern-identifier field to a case this slice did not author.

### Never do

- Reword an assertion, prompt, pattern identifier, or payload to match a
  measured result. A refuted predeclaration is corrected only on explicit owner
  authority recorded in the verification ledger with the prompt, the declared
  expectation, the measured result, and the ground the correction rests on.
  Never adjust a declaration until it agrees.
- Re-stamp a moved digest onto an earlier observation, discard a transcript a
  record still cites, or carry a verdict forward across a body or payload edit.
- Retain an exemption whose miss the current measurement repaired, or add one
  the current measurement did not produce. Each exemption change is recorded in
  the verification ledger with the case, the assertion text, the prior verdict,
  the measured verdict, the owner authority admitting it, and the date that
  authority was given; a basis that lives only in a commit message does not
  satisfy this.
- Edit an inherited declaration in order to widen what a new case may declare.
- Claim a runtime profile, `runtime-package`, or per-claim router reporting
  capability. The brief assigns per-claim reporting to slice 3c-r and
  `runtime-package` to slice 3d, and makes runtime profiles beyond Claude Code
  an open extension rather than a committed slice — so none of the three is this
  slice's to claim, and none may be routed to 3c or 3d as though it were
  already owned there.
- State that RFC-0097's Gate 2, its M2 expanded measure, or its M2 expanded
  success condition is met, in any artifact this slice writes. Slice 6 owns that
  verdict. Two sections together enumerate what this slice writes: the plan's
  durable-output map, which carries the lasting records, and the plan's
  Construction tests section, which names the guard files. The pair is needed
  because a durable-output map routes semantic owners of lasting truth, and a
  test file is not one — so a guard name or docstring is exactly where the
  forbidden claim would otherwise sit outside the ban.
- Commit personal or host-identifying data in any recorded evidence field,
  including a retained transcript.

## Testing Strategy

- Use observed behavior fixtures, graded blind, for both new cases and for every
  inherited authoring case whose pinned digest this slice moves. A construction
  test cannot substitute: the subject is what the workflow does with a supplied
  draft, not what the tree contains.
- Use TDD for the declaration contract — field completeness, payload binding,
  pattern-identifier mapping, marker provenance, transcript-to-verdict binding,
  and exemption bookkeeping — because each is a compressible invariant over
  files in the tree.
- Read every "before this slice" comparison set from the base commit with
  `git show <base>:<path>`, recording the base commit in the verification
  ledger. A set read from the working tree is one the change under test can
  edit.
- Use goal-based checks for the manifest bump, changelog placement, index row,
  and the registration invariant the workspace projection reads, each verified
  by an owning gate rather than by a new assertion.
- Three surfaces have no owning gate and are confirmed by reading at close, each
  saying so in its own criterion: the architecture record's four RFC-required
  fields, because no repository gate asserts them; the brief's Spec-map row,
  because brief-coverage lint reports an unresolved back-link informationally
  and exits zero; and this spec's registration digest, because nothing reads
  `source.revision`. Listing them as gate-verified would invite an executor to
  accept a green run for three things no gate looked at.
- Prove every widened enumeration by mutation: state the invariant, the test
  that must catch its removal, the exact mutation, and the observed failure.
  Narrowing a pinned set is the mutation that matters, because a narrowed set
  drops a record from coverage while every other assertion still passes. Restore
  by editing, never by checkout.
- Five judgements are advisory rather than gated, because no predicate over
  authored prose decides them: whether each assertion tests a requirement its
  declared floor actually states, rather than one a generic response satisfies;
  whether each recorded verdict is the one its transcript supports; whether the
  three-context separation actually held, which the transcript evidences but
  cannot prove; whether a payload's prose carries a defect a human would
  recognize as the one its declaration names; and whether a bare personal
  identity has leaked past the structural host scanner, whose pattern set does
  not recognize one. Each is read at review and recorded in the verification
  ledger. The guard owns form; review owns meaning.

## Acceptance Criteria

- [x] **AC1 — Both named cases are declared with a complete field set.** The
  authoring workflow's `evals/evals.json` declares `subagent-composition` and
  `hook-plugin-design`, and for each the `id`, `prompt`, `expected_output`,
  `assertions`, `expect.output_contains`, and `files` values are non-empty.
- [x] **AC2 — Each new case names its own payload.** Every path in each new
  case's `files` resolves to a file under the skill root, and the payload set
  each new case names is disjoint from the payload set every other declared case
  names, so a case is graded against the draft its own declaration supplies.
- [x] **AC3 — The declared-case set gains exactly these two.** The set of ids
  the authoring workflow declares equals the set read from the declarations file
  at the base commit, plus `subagent-composition` and `hook-plugin-design`, with
  no other id added, removed, or renamed. Reading the base set from the base
  commit rather than the working tree is what stops the change under test from
  defining its own baseline.
- [x] **AC4 — Each new case declares the pattern identifiers it exercises.**
  `subagent-composition` declares exactly
  `["skills-and-subagents-common-floor"]` and `hook-plugin-design` declares
  exactly `["hooks-common-floor", "plugin-package-common-floor"]`, and every one
  of those identifiers resolves to an admitted topic in
  `packs/agent-skill-engineering/tests/fixtures/topic-admission.json`. Equality
  per case, not membership in the admitted set: an unrelated admitted topic
  would otherwise satisfy the criterion.
- [x] **AC5 — Each new case declares the marker set its closest sibling
  declares.** Each new case's `expect.output_contains`, as a set, equals the set
  `pytest-suite` declares at the base commit, and `pytest-suite`'s declared set
  on the shipping tree equals the set it declared at the base commit. Equality
  against one named sibling, not containment in the union of all base
  declarations: the union spans modes and authorization states, so containment
  admits a marker whose behavior a read-only framing case never produces.
  `pytest-suite` is the sibling because it is the inherited case with this same
  shape — read-only framing over a payload the case supplies. Reading it from
  the base commit, and asserting it unmoved, is what stops this slice widening
  its own allowed set.
- [x] **AC6 — Each new case names the assertion that reports its seeded
  defect.** Each of the two cases declares, alongside its pattern identifiers,
  the exact text of the one assertion in its own list that reports the defect
  the payload seeds; that text is a member of the case's `assertions`; and the
  two cases name different assertions, since one text satisfying both would mean
  the two payloads seed the same defect.
  Without this the seeded-defect subject is whichever assertion the implementer
  has in mind, and dropping it while keeping other true assertions leaves every
  check green.
- [x] **AC7 — Each new assertion cites the floor requirement it tests.** For
  each assertion either new case declares, the verification ledger records the
  requirement in the declared floor's shipped text that the assertion tests, and
  a reviewer's judgement that a response could satisfy the assertion only by
  meeting that requirement. An assertion a generic response satisfies is the
  failure this addresses, and no predicate over authored prose decides it, so it
  is read at review and recorded rather than gated.
- [x] **AC8 — Each payload is a distinct, non-empty draft.** Neither payload is
  empty, and neither is byte-equal to the other or to any payload the base
  commit carried. Whether a payload's prose carries the defect its declaration
  names is the advisory judgement the Testing Strategy names, recorded in the
  verification ledger rather than gated here.
- [x] **AC9 — Every graded verdict is readable against its own retained
  transcript.** Every authoring record names a transcript path under this spec's
  `notes/` directory; no two records' paths resolve to the same transcript,
  compared on canonical resolved targets rather than on the path strings, since
  a symlink defeats a string comparison; the record's captured-response digest
  recomputes from that transcript's bytes; and every
  string in the case's `expect.output_contains` appears in it. One transcript
  witnessing several records is the mutation the per-record path and the
  distinctness check exist to stop.
- [x] **AC10 — Every recorded verdict is the one the transcript supports.** For
  every recorded assertion verdict, the verification ledger records the grading
  context's reading of the transcript passage the verdict rests on. A transcript
  can hash correctly, carry every declared marker, and still contradict a
  recorded `true`; nothing mechanical decides that, so the reading is recorded
  and read at review.
- [x] **AC11 — Every authoring record belongs to one declared round.** Every
  authoring result carries the same observation identifier, a verdict per
  declared assertion in declaration order, and its own transcript. Two claims
  are deliberately *not* gated here, because no artifact in the tree
  distinguishes them from their negation: that the responses were generated
  fresh rather than copied under a new identifier, and that the executing
  context was withheld from the assertion list, the pattern identifiers, and any
  statement of which defects the payload seeds. Both are attested in the
  verification ledger by the operator who ran the round, alongside the other
  advisory readings the Testing Strategy names.
- [x] **AC12 — Every inherited result is re-measured, not re-stamped.** Adding
  the two cases moves `evals/evals.json`'s digest, which every authoring record
  pins. Every authoring record the base commit carried holds this round's
  observation identifier and transcript digest, and every digest in its
  `source_files` equals the shipping tree's value for that path.
- [x] **AC13 — Each new case's graded response reports its declared defect.**
  For each of the two cases, the assertion AC6 names is recorded true, or its
  miss is recorded under AC14 and AC15. A payload whose defect the
  workflow does not surface is a measurement this slice reports, not a payload
  it rewrites.
- [x] **AC14 — The exemption set equals the misses this slice measured.** The
  known-miss exemption set names exactly the `(case, assertion text)` pairs
  whose verdict is false in the recorded round; an exemption whose miss the
  measurement repaired is removed; and each exemption still names an assertion
  the case declares.
- [x] **AC15 — Every exemption carries a recorded authority.** For each entry in
  the exemption set, the verification ledger carries the fields the *Never do*
  rule enumerates. Verified by reading the ledger at close: a set-equality guard
  compares two machine-readable sets and cannot see whether an authority exists.
- [x] **AC16 — Every enumeration the plan names equals the set it pins.** Each
  enumeration the plan identifies as scoping which declarations or results a
  pack guard reads equals that set on the shipping tree. The claim is bounded to
  the named enumerations: a consumer that selects records by a computed
  predicate rather than by a literal id set is outside what any search over ids
  finds, and the plan states that limit rather than this criterion asserting a
  coverage it cannot establish.
- [x] **AC17 — Structural host-identity scanning is clean over what this slice
  writes.** The pack's shared host-identity patterns match nothing in the two
  payloads, the two declarations, any behavior result this slice writes, or any
  retained transcript. The patterns are structural rather than derived from the
  running environment, so the control fires where it is gated rather than only
  where it was authored.
- [x] **AC18 — Both payloads are clean under both portability controls.** The
  export-boundary scan's repository-only pattern set matches nothing in either
  payload, and neither payload matches the committed portability grep the pack's
  maintainer procedure requires before commit, which additionally catches a bare
  `RFC-NNNN` or `ADR-NNNN` identifier the pytest scan does not. Each payload
  therefore reads as a portable draft to an installed consumer.
- [x] **AC19 — Every fixture the M2 expanded measure names is recorded.**
  `packs/agent-skill-engineering/tests/fixtures/behavior-results.json` carries a
  result for each representative task fixture RFC-0097's M2 expanded measure
  names, compared against that measure's own list rather than against a set
  restated here.
- [x] **AC20 — The architecture record carries all four fields the RFC
  requires.** `docs/architecture/agent-skill-engineering.md` records this
  slice's implemented names, their paths, its dependency edge on the composition
  floors slice, and the verification evidence for the two fixtures, and remains
  `PLANNED`. No repository gate asserts these fields, so this is verified by
  reading the record at close, in the same review pass as AC15.
- [x] **AC21 — The status and registration pair is consistent at every point
  the projection reads it.** The workspace projection emits no
  `impossible_transition` for this spec at either lifecycle point: not when the
  spec reads `Implementing` in `["ini-009".work].active`, and not when it reads
  `Shipped` in `.shipped`. The plan's Constraints require both moves in one
  commit, which is how the invariant is kept; the criterion is the invariant,
  not the commit shape, because a workspace projection reads a tree and five
  attempts at a Git-history predicate for the pairing each admitted a
  reconciling second commit.
- [x] **AC22 — The milestone stops advertising this slice as startable and says
  it is in flight.** While this spec's entry sits in `["ini-009".work].active`,
  the `["ini-009"]` milestone string differs from the one the base commit
  carries — read with `git show <base>:workspace.toml`, the same base-commit
  discipline AC3, AC5, AC8 and AC12 use — and describes slice 3e as in flight
  rather than as unblocked, parallel, or otherwise available to start.
  Red case: T1 moves the registration to `.active` and leaves the string
  untouched. Green case: the string names 3e as the slice being delivered and no
  longer offers it as startable work.
  Requiring the string to have moved is what makes this checkable at all. The
  base milestone already contains the substring `3e`, so a criterion asking only
  that the milestone name the slice is satisfied before any work happens.
- [x] **AC23 — This spec's own registration pins the brief's current digest.**
  The `["ini-009".work]` entry this slice creates carries, as its
  `source.revision`, the `sha256-bytes-v1` digest of
  `docs/product/briefs/agent-skill-engineering.md` as it stands when the entry
  is written, re-pinned at close if the brief moved in between. Scoped to the
  one registration this slice creates: measurement on the base tree found that
  no registration in `workspace.toml` carries the brief's current digest, that
  the four entries referencing the brief carry three different older ones, and
  that the `brief_queue.executing` entry pins RFC-0097 rather than the brief at
  all. That drift predates this slice and is recorded as a Follow-on; absorbing
  it here would make a fixtures slice the owner of workspace hygiene.
- [x] **AC24 — The brief's Spec map carries this spec.** The Spec map has a row
  for this spec's bare slug. A path-shaped entry does not resolve under
  brief-coverage lint, and that lint reports an unresolved back-link
  informationally and exits zero, so the row is confirmed by reading the brief.
- [x] **AC25 — Both authored manifests carry the same bumped version, and the
  aggregate matches its projection.** `pack.toml` and `.claude-plugin/plugin.json`
  carry one patch above the version they carried at the base commit, and
  running the projection generator against the committed tree leaves
  `.claude-plugin/marketplace.json` unchanged. Regeneration-is-a-no-op is the
  check, because the generator writes its target in place and so leaves no
  separate artifact to compare against; a hand-edit that diverges from the
  projection reddens it. Whether identical bytes were generated or typed is not
  decidable from a tree and is not claimed.
- [x] **AC26 — The changelog entry is topmost for this pack and carries a
  `Highlights` disposition.** `docs/product/changelog.md` carries a
  free-standing `##` entry for this pack at the bumped version, above every
  other entry for it, and the entry either carries a `### Highlights`
  subsection or the release's PR records the verdict that this change alters
  nothing a pack consumer can do, with the reason. Nothing downstream makes that
  call: the public projection is a parser over the file's bytes.
- [x] **AC27 — The spec index row matches this spec.** `docs/specs/README.md`
  carries a row for this spec stating its shape and its final criterion and task
  counts.

## Follow-ons

- Slice 6 owner, via the slice 6 row in
  `docs/product/briefs/agent-skill-engineering.md`: the verdict that RFC-0097's
  Gate 2 M2 expanded measure and its success condition are met, and the
  promotion of `docs/architecture/agent-skill-engineering.md` to `CURRENT`. This
  slice supplies the fixtures that verdict reads; it does not pronounce it.
- Slice 6 owner, same row: the fixtures that shipped before this slice declare
  their checklist items as an assertion list and declare no pattern identifier.
  Bringing them into the shape AC4 establishes — or recording the assertion list
  as the shipped reading of RFC-0097's requirement for them — is part of
  asserting the measure met.
- Workspace-hygiene owner: no `workspace.toml` registration carries the current
  `sha256-bytes-v1` digest of `docs/product/briefs/agent-skill-engineering.md`.
  The four entries referencing the brief carry three different older digests,
  and the `brief_queue.executing` entry pins RFC-0097 rather than the brief.
  Measured on this slice's base tree; no gate reads `source.revision`, which is
  why the drift accumulated unnoticed. This slice pins its own entry correctly
  and touches no other.
- Slice 3c owner: the composition and subagent concepts in the authored
  vocabulary. These fixtures grade against the portable floors slice 3a shipped;
  a fixture that would need 3c's vocabulary is not declared here.

## Assumptions

- The hard dependency on the composition floors slice is satisfied, and the
  corpus these fixtures grade against already ships. (source:
  `packs/agent-skill-engineering/tests/fixtures/topic-admission.json` admits the
  skills-and-subagents, hooks, and plugin-package floors and the Claude Code
  composition topic; the composition-floors spec is in `["ini-009".work].shipped`
  and reads `Status: Shipped`.)
- The two fixtures this slice adds are the ones RFC-0097's M2 expanded measure
  names that `behavior-results.json` does not yet record, compared list against
  list rather than by counting either. (source:
  `docs/rfc/0097-agent-skill-engineering.md` § *Experiment / validation*, Gate 2
  M2 expanded measure; `packs/agent-skill-engineering/tests/fixtures/behavior-results.json`.)
- Both cases belong to the authoring workflow rather than the review workflow,
  because each is a framing task over a supplied draft — the shape the inherited
  language-suite cases already use. (source: user confirmation 2026-09-09.)
- Adding two cases moves the `evals/evals.json` digest that every inherited
  authoring record pins, and the pack's digest guard requires exact equality, so
  the inherited verdicts are re-taken rather than re-stamped. (source:
  `packs/agent-skill-engineering/tests/skills/author_or_update/test_contract.py`
  `test_authoring_behavior_evidence_matches_its_source_digest`, whose
  `recorded == {digest}` admits no stale value; user confirmation 2026-09-09
  that every inherited case is re-measured blind.)
- Retaining the graded transcripts under this spec's `notes/` is what makes AC9
  falsifiable. Without a retained response, a fabricated record and a measured
  one are structurally identical, which two independent reviews called the
  slice's dominant failure mode on 2026-09-09. The transcripts are repository
  records, not published corpus, so RFC-0097's exclusion of raw session logs
  from promoted evidence does not reach them; they are still scrubbed under the
  privacy convention before commit. (source:
  `docs/rfc/0097-agent-skill-engineering.md` § *Evidence promotion*;
  `docs/CONVENTIONS.md` § *Privacy*.)
- Observations produced by execution belong in `notes/verification-ledger.md`
  rather than in an approved artifact or a `qa.md`. Several older slices in this
  initiative used `qa.md`; the convention is the owner. (source:
  `docs/CONVENTIONS.md`, the sentence assigning an execution-produced
  observation to the sibling `notes/verification-ledger.md`.)
- The two new cases declare pattern identifiers although the shipped cases do
  not, because RFC-0097's M2 expanded measure makes that declaration part of
  each fixture while the brief gives slice 6 only the closeout verdict. The
  accepted cost is that the set is not uniform, so no guard can require the
  field on every case. (source: user confirmation 2026-09-09;
  `docs/rfc/0097-agent-skill-engineering.md` § *Experiment / validation*, Gate 2
  M2 expanded measure; the slice 6 row in
  `docs/product/briefs/agent-skill-engineering.md`.)
- Neither the export-boundary scan nor the host-identity scan needs a floor
  change, because each asserts its population is at or above a lower bound over
  a recursive walk, so adding a file under a covered suffix can only raise the
  population. No criterion reads a count. (source:
  `test_pack_boundary.py::test_shipped_content_names_no_repository_only_reference`
  and `test_corpus_admission.py::test_recorded_evidence_fields_carry_no_host_identifying_data`.)
- Portability has two controls, not one, and together they leave a smaller
  residual than either alone. The export-boundary pytest scan matches repository
  document paths, criterion references, and the workspace file; the committed
  grep in the pack's maintainer procedure additionally matches a bare
  `RFC-NNNN` or `ADR-NNNN`. AC18 requires both, and the plan schedules both, so
  a bare document identifier is gated rather than advisory. Host identity is
  different: the structural patterns match absolute paths, `user@host`, and
  `*.local` forms and cannot recognize a bare personal identity in an arbitrary
  field, so that one residual stays advisory under the Testing Strategy.
  (source: the pattern tuples in `test_corpus_admission.py` and
  `test_pack_boundary.py`; the committed grep in `packs/AGENTS.local.md`.)
- The pack version bump is a patch: two eval declarations and two inert payload
  files are changed content under the pack version-bump rule, not new
  primitives. The target is one patch above the version both authored manifests
  carry when the bump lands, which the plan's task reads rather than this
  document storing. (source: `packs/AGENTS.md` version-bump rule.)
- The base is current against the remote: this branch's tip and `origin/main`
  are the same commit, so nothing has landed upstream that this slice is
  authored against a stale view of. The base commit AC3, AC5, AC8, and AC12 read
  from is that commit, recorded in the verification ledger. Re-run the check
  before implementation begins rather than reading this line: a base that is
  fresh at authoring goes stale the next time a peer merges. (source:
  `python3 .agents/skills/work-loop/scripts/check-base-freshness.py`, which
  returned `{"status": "ok", "message": "head is current", "target":
  "origin/main"}` on 2026-09-09.)
- At intake, slice 3e had no spec, plan, or workspace entry, and
  `["ini-009".work].queue` was empty by the brief's *Derived work* rule — a
  confirmed slice is a decomposition target, not permission to dispatch. This
  spec and its plan are the first artifacts; the workspace entry is created by
  the plan's first task. (source:
  `docs/product/briefs/agent-skill-engineering.md` slice table and its *Not yet
  started* paragraph; `workspace.toml` `["ini-009".work]` as read before
  authoring on 2026-09-09.)
- A graded run the harness reports as unreliable is discarded and re-taken
  rather than recorded, so a fixture verdict never rests on a run the harness
  does not stand behind. (source: the practice recorded in
  `docs/specs/agent-skill-engineering-languages-and-execution/plan.md` T8 and
  its risk table.)
