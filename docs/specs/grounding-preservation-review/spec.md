# Spec: Preservation through typed review

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** Platform Core
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none
- **Brief:** brief:repository-grounding-preservation
- **Discovery:** none
- **Depends on:** spec:grounding-preservation-evidence, spec:structured-review-boundary
- **Contract:** `contracts/delivery/review-report.v1.schema.json` and `contracts/delivery/finding.v1.schema.json`, consumed unchanged as merged by `structured-review-boundary` at `bfe30052cc760cc0e3c79e95582c3bfc6c87cd0e`
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Outcome`, `What Changes`, `Durable Outputs`, `Follow-ons` and
> `Assumptions` are working material.

## Outcome

When a change touches a shared substrate, `adversarial-reviewer` asks whether
every reachable consumer class has a preservation criterion in the spec under review, and
`quality-engineer` asks whether each preservation criterion has current,
independent evidence. Each reviewer can return its findings as a typed report
in which every finding names the criterion it affects in the spec the caller names. Success is a
fixture suite in which such a finding, sent through the shipped generic review
path without any reviewer-specific code, makes exactly its affected
preservation property `contradicted`, and graded runs in which both reviewers
emit that shape on the frozen PR-207-shaped cases.

## What Changes

- One typed-report section in each of `packs/core/.apm/agents/adversarial-reviewer.md`
  and `packs/core/.apm/agents/quality-engineer.md`: the report's terminal
  statuses, the fields every finding carries, which fields the caller fills in,
  which findings the typed report carries, and how a finding names the
  criteria it affects in the caller-named spec. The section serves every finding, not only
  preservation findings. Without a request for it, the reviewer returns its
  Markdown findings block or clean line exactly as before.
- One lens question in each reviewer: shared-substrate reachability in
  `adversarial-reviewer`, oracle independence and evidence sufficiency in
  `quality-engineer`.
- Two reviewer eval cases in `work-loop`'s `evals/evals.json` with fixture
  files under `evals/files/preservation-review/`.
- Pack test modules under `packs/core/tests/` that pin the reviewer guidance,
  pin the eval cases, and drive typed reports through the shipped review and
  evidence modules.
- One sentence in `guides/core/how-to/plan-and-execute-non-trivial-work.md`
  § REVIEW naming the typed report and the two preservation questions.
- A Core patch release and its changelog fragment, at the version AC-0023
  states.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| User-facing promise | Adopters running review on a shared-substrate change meet the new questions | `guides/core/how-to/plan-and-execute-non-trivial-work.md` § REVIEW | Platform Core | The sentence names the typed report and both questions without restating the reviewer rules | The guide sentence is present |
| Current product truth | The brief tracks slice delivery | The brief's Spec map row | Platform Core | The coverage roll-up resolves this spec through its `Brief:` line | The row derives `Shipped` |
| Release history | Any `packs/core/` change ships under a new Core version | `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`, a fragment in `docs/product/changelog.d/` | Core pack release maintainers | The version AC-0023 states | AC-0023 and AC-0024 hold |
| Reusable learning | The graded runs measure reviewer behavior | `notes/verification-ledger.md` in this spec directory | Platform Core | Each graded and baseline run's output and grade, with the pack version it ran against | The ledger records the AC-0022 runs and their baselines |

## Agent Rules

### Always do

- Edit `packs/core/.apm/` sources, then regenerate the projections with
  self-host.
- Keep the text this spec adds to the reviewer files portable: no
  catalogue-internal records, no path under `docs/` or `contracts/`, and no
  requirement for an optional pack, a code-intelligence capability, or Pi.
- Express every preservation finding through the typed report's generic fields;
  bind it to a criterion only through the affected-criteria field.
- Drive every verdict in the suite through the shipped review modules,
  `EvidenceStore`, and the acceptance evaluator, with no stand-in for them.

### Ask first

- Changing a reviewer's severity rules, clean sentinel, or Markdown findings
  grammar.
- Any reviewer-file edit outside the typed-report section and the two lens
  checks.

### Never do

- Add a reviewer role, a reviewer-role condition in `work-loop`, a finding
  category or field specific to preservation or grounding, or an orchestration
  branch for either.
- Add a schema, a schema field, an evaluator or evidence-store change, a new
  persistent state record, or a change to who may approve, waive, or dispose a
  finding.
- Make a reviewer invent a criterion identifier the caller-named spec does not
  contain.
- Move review authority from the current review path, or touch the supervisor
  cutover's files.
- Edit `work-loop` `SKILL.md`, its `references/` or `scripts/`, or anything
  under `contracts/`.
- Add a dependency, or let the absence of an optional pack lower either
  question.
- Edit a generated projection under `.agents/` or `.claude/` by hand.

## Testing Strategy

- **Reviewer guidance (AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0006, AC-0007, AC-0008):**
  TDD. Content pins are written first and fail while the sections are absent.
- **The generic path (AC-0009, AC-0010, AC-0011, AC-0012, AC-0013, AC-0014, AC-0015):**
  goal-based. The review modules and evaluator already exist, so a TDD red is
  not available; the negative controls and the refused report are the failing
  cases.
- **Disposable projections (AC-0016):** goal-based, extending the plan-resident
  consumer-map fixture shape C1 ships.
- **Eval cases (AC-0017):** TDD construction pins, written first.
- **Scope and optional packs (AC-0018, AC-0019, AC-0020, AC-0021):**
  goal-based; one command each.
- **Reviewer behavior (AC-0022):** visual / manual QA of the rebuilt agent
  artifacts. No CI gate grades eval output, so each case runs as a graded run
  beside one baseline graded run against the base revision's projection, and a
  rerun replaces a head run when the guidance changes. The positive authoring
  case is recorded, not graded for a pass.
  If a case's baseline also holds every assertion, AC-0022 shows only
  that the guidance does not regress that case, and the content pins carry the
  proof that the guidance ships.
- **Release (AC-0023, AC-0024):** goal-based; one command each.

## Acceptance Criteria

Terms:

- **The two reviewer files** are `packs/core/.apm/agents/adversarial-reviewer.md`
  and `packs/core/.apm/agents/quality-engineer.md`.
- **The typed-report section** is the one `## Typed report` section in a
  reviewer file.
- **The added text** is the typed-report section plus the lens checks AC-0006
  or AC-0007 names in that file.
- **The finding fields** are `schema_version`, `finding_id`, `rule_ref`,
  `observation`, `reachable_path`, `actual_failure`,
  `affected_acceptance_criteria`, `evidence_refs`, and `material`.
- **The caller fields** are the report's `schema_version`, `report_id`,
  `role`, `subject`, and `lineage`.
- **A material finding** is a Blocker or Concern whose defect something
  outside the finding establishes: code, a test, a lint, a schema, a
  resolvable reference, or a stated constraint disagrees with the target.
  Every other finding is not material.
- **The fixture properties** are three `acceptance-property.v1` records: the
  ordinary-calls property, the default-search property, and the lifecycle
  property. Each names `supported-review-failure` in its contradiction rule
  and has a current passing receipt for each required term.
- **A typed report** is a `review-report.v1` record whose findings are
  `finding.v1` records.
- **Sent through the generic path** means: validated with the shipped report
  contract, persisted as the current report, each finding assessed with the
  shipped assessment function, each supported assessment recorded through the
  shipped assessment bridge, and each fixture property decided by
  `EvidenceStore.evaluate_verdicts`.
- **The base revision** is `git merge-base origin/main HEAD` after a fresh
  fetch, with every change committed.

### Reviewer guidance

- [ ] **AC-0001.** Each of the two reviewer files has exactly one typed-report
  section, and the two sections are identical.
- [ ] **AC-0002.** The typed-report section names every finding field, the
  four terminal statuses `clean`, `findings`, `unable`, and `indeterminate`,
  and every caller field as filled by the caller.
- [ ] **AC-0003.** The typed-report section says that when the caller asks for
  a typed report, the reviewer returns only one fenced `json` block holding
  `terminal_status` and `findings`, instead of the findings block or clean
  line, and that this overrides the file's findings-only return for that
  request; otherwise the findings block or clean line is returned unchanged.
  It says the section governs only the modes in that file that return a
  findings block. It says the reviewer checks whether a typed-report
  request names a spec for the findings to bind to before any review work,
  and that a request naming none returns `indeterminate` with no findings,
  and that a named spec's status never changes the outcome. It says a typed-report return does not satisfy the file's
  review-complete gate, and the typed review path's obligation decision
  governs it instead. The sentence beginning `Return **only** the findings
  block above` stays in both reviewer files.
- [ ] **AC-0004.** The typed-report section defines a material finding as the
  Terms above do and says the typed report carries only material findings. It
  says a review against the caller-named spec that completes with no material
  finding returns `clean`, and that a caller
  who needs the non-material findings asks for the findings block instead.
- [ ] **AC-0005.** The typed-report section says an affected criterion is an
  identifier the caller-named spec contains, that under a typed-report
  request the spec under review is the caller-named spec, and that when a
  material finding has
  no such identifier to name, the typed report's status is `indeterminate`
  with no findings.
- [ ] **AC-0006.** `adversarial-reviewer.md` has check 6 under
  `### Spec-stage checks`, and check 10 under `### Implementation-stage checks`
  applies check 6 to the consumers the diff reaches. Check 6 asks,
  for a change that adds or alters a member of a model, registry, graph,
  index, schema, namespace, or collection that generic operations observe
  without opt-in, whether each reachable consumer class has a
  preservation criterion in the spec under review. It says a missed class is a finding whose affected
  criteria name the criterion that covers the class. When no criterion covers
  it, they name the criterion whose change reaches the consumer, and the fix
  is an amendment. It says a consumer that reaches the member only through an
  explicit filter raises no finding.
- [ ] **AC-0007.** `quality-engineer.md` has check 35 in a
  `### Preservation evidence` subsection of review mode. It asks, for
  each preservation criterion in the spec under review, whether its evidence is current, has
  an expected side independent of the code under test, and fails on a named
  mutation. It says missing, stale, tautological, or feature-only evidence is
  a finding whose affected criteria name that criterion.
- [ ] **AC-0008.** The added text names no path under `docs/` or `contracts/`
  and does not contain the words `preservation finding`, `adapt-to-project`,
  `code intelligence`, or `Pi`. The typed-report section does not contain the
  word `preservation`.

### The generic path

- [ ] **AC-0009.** Missed consumer: an `adversarial-reviewer` typed report with
  one material finding whose affected criteria name the default-search
  property, sent through the generic path, records one review-failure receipt
  for that property. Its verdict is `contradicted` and the other two fixture
  properties stay `supported`. With a mandatory obligation for its role, the
  obligation decision is satisfied and blocks acceptance on the open finding.
- [ ] **AC-0010.** Weak evidence: a `quality-engineer` typed report with one
  material finding whose affected criteria name the ordinary-calls property,
  sent through the generic path, makes that property `contradicted` and leaves
  the other two `supported`.
- [ ] **AC-0011.** Negative control: a `clean` typed report with no findings,
  sent through the generic path, records no review-failure receipt and leaves
  all three fixture properties `supported`. With a mandatory obligation for its
  role, the obligation decision is satisfied with no review or acceptance
  block.
- [ ] **AC-0012.** A typed report whose finding has an empty affected-criteria
  list, or omits one finding field, is refused by the shipped report contract,
  and no record is persisted.
- [ ] **AC-0013.** Repeating AC-0009 and AC-0010 with each report's `role`
  replaced by a role name no shipped reviewer uses gives the same assessments,
  receipts, and verdicts.
- [ ] **AC-0014.** A finding whose assessment is unsupported, sent through the
  generic path, records no review-failure receipt and leaves its named property
  `supported`.
- [ ] **AC-0015.** An `indeterminate` typed report with no findings, sent
  through the generic path with a mandatory obligation for its role, is
  selected as that role's current report. The obligation decision for it is
  unsatisfied with a reason different from the decision with no report
  persisted. No review-failure receipt is recorded and all three fixture
  properties stay `supported`.
- [ ] **AC-0016.** Deleting the plan's consumer map, rebuilding it in another
  order, and replacing the plan's task list each leave unchanged the acceptance
  fingerprint, the ordered review obligations selected for the subject, the
  current report, and all three verdicts after AC-0009's report.

### Eval cases, scope, and optional packs

- [ ] **AC-0017.** `work-loop`'s `evals/evals.json` carries two cases, each
  with its files under `evals/files/preservation-review/`. The fixture spec
  reads `Status: Approved`, each prompt names it as the spec the findings bind
  to, and its criteria include `CRIT-2`, ordinary calls resolve to no value node, and
  `CRIT-3`, default search and listing exclude value nodes. The
  `adversarial-reviewer` case's expected output names `CRIT-3` for the
  unfiltered listing consumer, its prompt does not name that consumer, and one
  of its assertions requires no finding against the filtered search path. The
  `quality-engineer` case's expected output names `CRIT-2` for the
  tautological ordinary-calls test.
- [ ] **AC-0018.** `git diff --name-only <base revision> HEAD` lists no path
  under `contracts/`, `packs/core/.apm/skills/work-loop/scripts/`, or
  `packs/core/.apm/skills/work-loop/references/`, and does not list
  `packs/core/.apm/skills/work-loop/SKILL.md`.
- [ ] **AC-0019.** `packs/core/pack.toml` has no `[dependencies]` table.
- [ ] **AC-0020.** `agentbundle catalogue verify --root .` exits 0.
- [ ] **AC-0021.** The new test modules import only the standard library,
  `pytest`, and `work-loop` scripts loaded by path.

### Agent behavior and release

- [ ] **AC-0022.** Graded runs against the rebuilt projections hold every
  assertion of four cases: `new-spec`'s
  `isolated-private-change-does-not-expand-preservation-proof`, `work-loop`'s
  `shared-substrate-feature-tests-do-not-prove-preservation`, and AC-0017's two
  cases. `new-spec`'s `shared-substrate-change-expands-preservation-proof` also
  runs on the rebuilt and base projections, and the ledger records its scores
  without a pass requirement. A graded run is one fresh agent following a copy
  of the projection with its `evals/` directory removed, given only the case's
  `prompt` and files, and scored by a separate grader that receives the output
  and the case's `assertions`. A reviewer case's agent follows the projected
  reviewer definition. Each run's copy holds only Core's projected skills and
  agents and has no `adapt-to-project`, and each run's agent has no
  code-intelligence capability and no Pi; the ledger records that each condition
  held for every listed run.
- [ ] **AC-0023.** `packs/core/pack.toml` and `packs/core/.claude-plugin/plugin.json`
  both read the patch version one above `packs/core/pack.toml` at the base
  revision.
- [ ] **AC-0024.** A `docs/product/changelog.d/` fragment names `core` at the
  version AC-0023 states.

## Follow-ons

- The brief's C3 "integrated positive fixture" proof is not met by this slice:
  `new-spec`'s `shared-substrate-change-expands-preservation-proof` does not
  reproduce on unchanged `new-spec` guidance. Owner: Platform Core. Tracked in
  `docs/product/captured/new-spec-positive-case-reproducibility.md`, registered
  in the backlog. At closeout the brief's § C3 proof bullet points to it.

## Assumptions

none
