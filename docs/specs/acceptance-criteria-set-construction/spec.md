# Spec: acceptance-criteria set construction

- **Status:** Shipped (2026-09-11) <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0108
- **Brief:** docs/product/briefs/agent-authoring-input-quality.md
- **Discovery:** none
- **Contract:** none
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

**The skill checks its own loop-contract artifacts.** `new-spec` ships three
checks in its own `scripts/`, each reading artifacts the skill itself emits, and
each named by a step of the procedure with the form that invokes it, so no
shipped control is one nobody runs:

- an **item-alignment check** over a spec directory, deciding that every
  criterion and verification item carries an identifier, that identifiers are
  unique, that none is reused against the artifact's retired list, that every
  criterion-class reference resolves, that a criterion is named by a task entry,
  and — reporting rather than blocking — that a reworded criterion's assertion
  followed it and that a task entry is not structurally broken;
- a **grounding explorer** answering what already governs a set of touched
  paths, its probe set selected by stage, its repository-shaped thresholds
  derived from the adopter repository's own distribution and reported with what
  produced them, every probe reporting and none deciding;
- a **finding-coverage check** reporting a rule whose message no test observes.

The identifier standard those checks enforce is ADR-0108's, and this spec holds
the ADR to a confirmation state that names the check rather than claiming none
exists.

**What this spec does not carry.** The selection procedure, the set-level
sweep, the plan-authoring rules, the review-response protocol and per-task
grounding are authoring guidance whose only check would be that a sentence
exists. They are routed to
`docs/product/intents/spec-authoring-protocol-measured-before-shipping.md`,
which gates promoting any of them to a criterion on a frozen-case score, and
each rule already shipped is pinned by name in the pack suite. The mechanical
half of grounding is not routed — it is the explorer above, which is how
grounding gets an answer a machine produces rather than an obligation a reader
grades.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| User-facing promise | Not applicable to this slice — the guide page publishing the procedure was cut with the procedure; see the plan's `## Cut from this slice` | routed to [the authoring protocol measured before shipping](../../product/intents/spec-authoring-protocol-measured-before-shipping.md) | that intent's owner | none owed here | The route is recorded and no task in this slice claims the page |
| Reusable learning | Applicable — the procedure's own first use, and the identity evidence the records cite | `notes/set-construction-self-application.md` for the procedure's own first use; [`docs/product/research/item-id-management-comparison-matrix.md`](../../product/research/item-id-management-comparison-matrix.md) for the identity evidence ADR-0108 and the architecture page both cite; [`docs/product/research/review-loop-nonconvergence-survey.md`](../../product/research/review-loop-nonconvergence-survey.md) for the round measurements the loop-contract page links | This spec's owner | The transcript's dated addenda; the matrix's alternatives and their rejection reasons | Each destination exists and nothing an architecture page or decision record cites is left without an owner |
| Release history | Applicable — a `.apm/**` content change is a released pack change | `docs/product/changelog.md` (a pack keeps no `CHANGELOG.md` of its own; that convention is for published packages) | Pack release pipeline | Free-standing topmost `core` entry at the bumped version | Entry present at the version `pack.toml` and `plugin.json` both carry |
| Current product truth | Applicable — the brief tracks slice delivery | `docs/product/briefs/agent-authoring-input-quality.md` § "Spec map" | `lint-brief-coverage` roll-up | Coverage roll-up resolves this spec through its `Brief:` back-link | Roll-up names this spec; no status hand-written into the brief |
| Decision rationale | Applicable — this slice amends a decision record, and owner decisions taken during delivery are recorded rather than left in commit messages | [`docs/adr/0108-opaque-append-only-loop-contract-identifiers.md`](../../adr/0108-opaque-append-only-loop-contract-identifiers.md) for the identifier decision; this plan's `## Changelog` for the delivery decisions | This spec's owner | ADR-0108's `Confirmation` names the shipped check and its `Revisit if` records the fired trigger, with the decision text unchanged; each delivery decision is dated in the plan's changelog | The ADR states no falsehood about current tooling, and no owner decision from this delivery is discoverable only from a commit message |
| Interface compatibility | Applicable — the slice ships command-line checkers that project into every installed adapter, each with its own flags, exit codes and output contract | each checker's own `--help` text, which is its docstring | This spec's owner | Each shipped script's header names its probe or rule set, its flags, and what its exit codes mean | An adopter reading `--help` learns every flag and every exit code the script can return, and no header describes a set the code does not have |
| Current architecture | Applicable — this slice adds a subsystem page for the loop contract, which `docs/CONVENTIONS.md` names as a durable role | [`docs/architecture/loop-contract.md`](../../architecture/loop-contract.md) | This spec's owner | The page states ownership, boundaries and navigation and cites each rule's owner by document and identifier | No rule is restated where an owner already states it, and the page is reachable from the architecture index |

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Edit pack sources under `packs/core/.apm/`, then regenerate the `.agents/` and
  `.claude/` projections and commit source and projection together.
- Add a pointer when a rule already has an owner, and cite that owner by
  document and identifier.
- Bump `packs/core/pack.toml` and `packs/core/.claude-plugin/plugin.json` to the
  same version, with core leading its own free-standing changelog entry. While
  the delivery is unreleased its entry is amended in place as further content
  lands, so one version string never describes two code states. The task that
  closes the release surface owns the entry's final state **and re-resolves the
  version number against `origin/main` at that moment**: a number taken from
  what was free when the branch started is a claim, not a reservation, and a peer
  that merges first takes it. Re-resolving at close is not a second bump — it is
  the only point at which the number can be correct.

### Ask first

- Any change to `assets/spec.md` beyond adding a cross-reference, because that
  file owns criterion shape.
- Any edit to `docs/product/briefs/agent-authoring-input-quality.md`.

### Never do

- Add a fixed absolute criterion count to any surface — a cap, a ceiling, a
  budget, a refusal, or a pass/fail bar on how many criteria a spec may carry. A
  percentile derived from the author's own corpus, used only to order scrutiny,
  is not one of these and stays permitted.
- Restate a rule owned by `assets/spec.md`, `assets/plan.md` or
  `references/spec-authoring-rubric.md` into a second file.
- Silence a pre-existing warn-only lint warning to make a gate read clean.
- Introduce a new top-level directory or a new dependency. The selection
  procedure, the plan rules and the response protocol are prose in files that
  already exist. The one admitted addition is the alignment checker in
  AC-0033, owner-approved 2026-09-10: it takes a `scripts/` directory inside
  this skill, which is the catalogue's standard skill layout and is already how
  sibling skills already ship their own tooling. The checkers that ship there are
  AC-0033's alignment check, the grounding explorer AC-0041 admits, and AC-0037's
  finding-coverage check, each admitted by its own criterion rather than by
  sitting beside one that was.
- Claim, on any surface, that a criterion count proves a set well-shaped. The
  count orders how hard the set-level pass looks and settles nothing on its own;
  no check reaches this claim, so it is held here and read at review.
- Claim, in shipped text, that written guidance changes author behaviour in
  general. This slice ships no measurement of that, and the one measurement
  taken found the guidance made selection worse.
- Build the identity or fingerprint mechanism beneath the single-homing check.
  The phrase-based oracle is how that check already works; leaving it is
  declining to repair a pre-existing gap, not shipping new debt, and everything
  this spec delivers works the same underneath it.

## Testing Strategy

- **The finding-coverage check (AC-0037):** TDD. Its rules are functions over
  fixture skill trees, and its cases compress into assertions.
- **The grounding explorer, five criteria over one script (AC-0041, AC-0042,
  AC-0043, AC-0044, AC-0045):** TDD. Each probe is a function over a fixture
  tree, and its cases compress into assertions. Each criterion takes its own
  cases rather than sharing one group, because they fail on different inputs:
  the explorer can exist and answer every probe while stage selection filters
  instead of gating (AC-0041 green, AC-0042 red), and every probe can be
  stage-selected and bounded while a threshold reports no basis (AC-0042 green,
  AC-0043 red).
- **A reworded criterion whose assertion did not follow (AC-0040):** TDD, on the
  pack-local suite, over fixture repositories with real history rather than this
  repository's own. It reports rather than blocks, and it under-reports by
  design; both are stated in the criterion.
- **A structurally broken task entry (AC-0039):** TDD, on the pack-local suite.
  The predicate is a function over entry text, so its cases are assertions. Its
  cases record which backtick shapes break a naive count, so the predicate is
  distinguished from the one it replaced by the fixtures rather than by a quoted
  rate.
- **Every shipped check is named by a step, with the form that invokes it
  (AC-0038):** goal-based check over the authored skill file, on the pack-local
  suite. The surface is the skill's procedure, not a gate list, and the check
  reads the skill's own `scripts/` directory rather than a restated inventory,
  so a check added later without a named caller fails rather than passing
  unnoticed. Both halves are observed: a script named nowhere fails, and a
  procedure naming every script without the runnable form fails too.
- **ADR-0108's confirmation state (AC-0032):** goal-based check over the ADR,
  at repository level. The ADR is not pack content, so the pack-local suite
  cannot read it.
- **The alignment checker (AC-0033):** TDD. The check is a pure function over a
  spec directory's two texts and its retired list, so its cases compress into
  assertions. Its scope is deliberately distinct from the repository's
  spec-status lint, which decides spec *state* — status vocabulary, criteria
  checked at a ship transition, deferral anchors, contract traceability. This
  one decides *item alignment* and owns no lifecycle question.

## Acceptance Criteria

- [x] **AC-0032.** ADR-0108's `Revisit if` names a tool that enforces no-reuse for
      inline-Markdown items, and the checker below is that tool, so the trigger
      fires on delivery. The ADR's `Confirmation` moves from reviewer-checked to
      the shipped check and its `Revisit if` records that the trigger fired and
      the decision stands unchanged. A shipped decision record stating that no
      lint enforces it, on the commit that ships the lint, is the conflict the
      repository's own guidance forbids resolving silently.
- [x] **AC-0033.** The skill ships its own alignment checker, invoked from its own
      `scripts/` directory and depending on no other skill. It decides the
      mechanical alignment of a loop contract's items: every acceptance criterion
      carries a well-formed identifier, identifiers are unique within the spec
      directory, none appears in the retired list, every identifier reference in
      `spec.md` and `plan.md` carrying the criterion class marker resolves to a
      live criterion or to one the retired list records, a retired identifier
      being resolvable by design; every criterion is named by at least one plan
      entry and appears in exactly one verification group; and a verification
      item's identifier does not mirror the criterion it serves. An item-class
      identifier is not resolved against the criteria, and derivation from a
      *task* is not checked: no item registry exists, and nothing relates an item
      to a task number. Both are review obligations, named so the criterion
      claims exactly what its oracle decides. A spec whose criteria carry no
      identifiers is skipped rather than failed, so the checker is adoptable
      against the existing corpus on the commit that introduces it. A rule whose
      input is absent is named as having no input rather than counted as checked,
      and the report distinguishes that state from a clean one — a partial check
      read as complete is the defect this checker exists to find elsewhere. A
      rule that still decides part of its subject is applied, not unapplied.
- [x] **AC-0041.** The skill ships a grounding explorer in its own `scripts/`,
      depending on no other skill, answering from a seed set of touched paths
      what already governs the surfaces that seed names: which files name a seed, which historically
      change with one, which gates would run one, which quote a distinctive line
      from one, and which scoped guidance governs each, plus which paths a seed
      names that no longer resolve. It reads no configuration file of its own,
      and its own top-level expectations are the adopter repository's rather than
      this one's.
- [x] **AC-0042.** The probe set is selected by stage rather than run whole: a probe
      outside a stage's set does not execute, and each stage's report names the
      probes it ran. Selection is executional rather than a filter on the output,
      because a discarded result is work an adopter paid for, and an oracle that
      reads only the report cannot tell a probe that was skipped from one whose
      output was suppressed.
- [x] **AC-0043.** The thresholds whose right value is repository-shaped — the
      sweep-commit size and the phrase cutoff — derive from the adopter
      repository's own distribution, and the report names each value with what
      produced it, on every stage, whether or not that stage's probe set consumes
      the value, so a defaulted value is not labelled as measured and an absent
      line is not read as an absent derivation. The minimum co-occurrences before
      a partner is reported filters results rather than presenting them, so it is
      reported on every run though it is not derived; the remaining bounds are
      presentation limits with documented defaults and flags.
- [x] **AC-0044.** Every probe reports and none decides, and every probe carries a
      bounded result. A probe whose input can be missing distinguishes found,
      none found, and input unavailable, since empty and unavailable are
      otherwise indistinguishable: those are the probes reading a seed's text, a
      runner set, or history — phrase pins, dead references, gate reachability
      and co-change. The probes reading the tree itself — scoped guidance, path
      references and the surface inventory — cannot have a missing input and
      distinguish found from none found. Both memberships are stated here so no
      probe is left without a declared case shape, and so no outcome is claimed
      that the code cannot reach.
- [x] **AC-0045.** What the explorer cannot settle mechanically it emits as a named
      ambiguity with its candidate resolutions, for the author to decide once and
      record. An absent or thin grounding surface lowers the starting information
      and never fails the run, and in the stages whose probe set includes it, the
      report inventories which known grounding surfaces are present and which
      carry content, so a degraded grounding is legible rather than silent.
      Consuming those surfaces as probe input — a recorded value seeding a
      derivation, and a record the repository contradicts reported as drift — is
      named in the follow-on that owns it, not claimed here.
- [x] **AC-0039.** The alignment checker reports a task entry whose text is
      structurally broken — a code span opened and never closed inside a `Tests`
      or `Done when` block. A multi-site edit that reshapes every entry at once
      can eat the head of a surviving clause, leaving a sentence that still reads
      as prose while the artifact or command it closed on is gone, which a
      reviewer reading for meaning does not see. The check matches backtick runs
      the way the markup
      delimits a span rather than counting backticks, and it discards a fence
      token written inline before matching: prose that mentions a fence, and a
      fence quoted inside a search pattern, both break a count and neither is a
      broken span — with no matching run of the same length the markup leaves
      the run literal, so it renders as written. It reports, and it is scoped to task
      entries rather than the whole document, so prose elsewhere is not its
      business.
- [x] **AC-0040.** Given a base revision, the alignment checker reports each criterion
      whose text changed since that revision while no line naming it in the plan
      changed with it — a criterion reworded without its implementing assertion
      following. This is a defect class that recurred while the propagation
      obligation, stated in prose alone, did not prevent it. The check reports and never blocks. The base
      revision is supplied by the caller and the rule is skipped, not failed,
      when it is absent or the repository has no history, so the check stays
      usable where neither exists. It adds no obligation: the propagation
      obligation is the set-level pass's and stays there, and this criterion states only
      that the checker reports the subset a machine can see. Its residue is
      stated for the same reason — an assertion that changed for an unrelated
      reason reads as covered, so the rule under-reports, and the re-read the
      set-level pass requires is what closes the gap the rule cannot. It over-reports in one
      direction too: a criterion trimmed of rationale without its obligation
      changing needs no new assertion, and the rule reports it anyway, because a
      reworded criterion and a re-obligated one are the same edit to a diff. That
      is why it reports and never blocks — a round spent confirming a trim is
      cheap, and a round that would have to be spent finding an unpropagated
      obligation is not. Its scope is the task
      entries that carry assertions, not the whole plan: a criterion named in a
      changelog entry or a rationale is not a criterion whose assertion
      followed, and reading the document as a whole silenced the rule wherever a
      changelog entry happened to name a criterion.
- [x] **AC-0038.** Every check the skill ships in its own `scripts/` is named by a
      step of the procedure, together with the runnable form that resolves in an
      installed tree, so no shipped control is one nobody runs and no named
      control is one a reader cannot invoke. The obligation is read from the
      `scripts/` directory rather than from a restated inventory, so a check
      added later with no named caller fails rather than passing unnoticed.
      Naming a check is not naming a required mechanism: a tool a session may
      not offer makes a rule unrunnable wherever it is absent, while a check
      shipped inside the skill is present wherever the skill is.
- [x] **AC-0037.** The skill ships a finding-coverage check in its own `scripts/`,
      depending on no other skill, which reads a subject's declared catalogue of
      the findings it can emit and reports any whose message no test in that
      subject's suite observes. A rule whose message no test observes has no red
      case, so its suite is green for a reason unrelated to whether the rule
      works. Participation is by declaration, so introducing the check fails
      nothing that has not opted in; a discovery scan finding no participant is
      reported as a failure rather than a pass, since a check reporting success
      over a tree it never examined is the defect it exists to detect; the
      directories it searched are named on every report; and a subject it cannot
      parse is reported rather than counted as a deliberate non-participant. It
      is a floor and says so: a test source containing a message is not proof an
      assertion fires, and only executing the case proves the branch is
      reachable.

## Retired identifiers

- AC-0001
- AC-0002
- AC-0003
- AC-0004
- AC-0005
- AC-0006
- AC-0007
- AC-0008
- AC-0009
- AC-0010
- AC-0011
- AC-0012
- AC-0013
- AC-0014
- AC-0015
- AC-0016
- AC-0017
- AC-0018
- AC-0019
- AC-0020
- AC-0021
- AC-0022
- AC-0023
- AC-0024
- AC-0025
- AC-0026
- AC-0027
- AC-0028
- AC-0029
- AC-0030
- AC-0031
- AC-0034
- AC-0035
- AC-0036

## Follow-ons

- eugenelim: [`docs/product/intents/loop-contract-item-identity-mechanism.md`](../../product/intents/loop-contract-item-identity-mechanism.md)
  — derive the pinned set from rule identifiers, fingerprint each item, and route
  a changed item's dependants into the next re-review's scope. Closes two of the
  single-homing oracle's three blind spots and gives the propagation sweep a
  mechanical backing; paraphrase detection stays out of scope there too.
- eugenelim: [`docs/product/intents/review-response-protocol-across-reviewer-surfaces.md`](../../product/intents/review-response-protocol-across-reviewer-surfaces.md)
  — carry the eight-response protocol this spec ships into `new-spec` out to
  `shaping-reviewer` and the pack reviewer surfaces, and rule out relitigating a
  decision a brief records as settled. This spec owns the authoring side only;
  the receiving side names no legitimate answer to a finding, which is why a
  sustained finding there reads as an instruction to edit. That intent also
  carries the boundary with
  [`spec-review-validation-guidance`](../../product/intents/spec-review-validation-guidance.md),
  a Draft intent on marking a finding's origin and testing its facts before
  repair: it shares this contract's guardrail of adding no lint and no
  review-count limit, and the two must not both come to own how a finding is
  answered.
- eugenelim: [`docs/product/intents/grounding-probe-extensions.md`](../../product/intents/grounding-probe-extensions.md)
  — the two probes this slice's survey ranks second and third: authority and
  projection closure, and the executable document-contract check. Held back
  because neither is cheap the way live-references was, and the second would
  execute a consumer's parse mode, which is a security surface the shipped probes
  do not have.

## Assumptions

- Technical: the acceptance-criteria procedure's surface is the `new-spec`
  skill's `SKILL.md` step 4 "No Acceptance Criteria" bullet, with the
  criterion-shape deferral restated at the shaping-review step (source: file
  read, 2026-09-10)
- Technical: a new guide needs `title`, `summary`, `pack` and `kind`
  frontmatter with `title` equal to the leading H1, and no navigation-baseline
  row (source: `contracts/guide.schema.json`; `guides/AGENTS.md`)
- Technical: `Shape: mixed` fits a skill-prose, guide and test change (source:
  `docs/specs/desk-research-build-handover/spec.md`)
- Process: a `.apm/**` content change bumps `pack.toml` and
  `.claude-plugin/plugin.json` together, and core leads its own free-standing
  changelog entry (source: `packs/AGENTS.md` § Version bump rule;
  `docs/product/changelog.md` header). The version is resolved against
  `origin/main` at release time, not reserved here: a peer change to the same
  pack already claims the next patch, so this slice takes the one after
  whichever version has landed when its release task runs (source: peer session
  notice, 2026-09-10 — corrects an earlier assumption that named a specific
  version from a local read)
- Process: a brief-derived spec registers in the workspace lifecycle index with
  the brief as its parent at spec-authoring time (source: `workspace.toml`
  precedent comment on the `sdlc-guide-uplift-and-learning-paths` S1 entry)
- Process: a model-in-the-loop evaluation runs in-agent through fresh
  subagents, never through an API key or SDK call (source: owner decision
  2026-08-18)
- Process: the evaluation adds no durable run schema, so no scorer script and
  no results file format (source:
  `docs/product/briefs/agent-authoring-input-quality.md` § "Author criteria
  from obligations, not from every check")
- Process: this slice edits the brief in four places — the A6 row's widened
  scope, the review-loop disposition section, a section recording that a
  criterion syntax was tested by rewriting and rejected, and the Spec map cell.
  All four carry owner authority: the first two on their own face, and the third
  and fourth by sign-off recorded here. The fourth writes the `<auto>`
  placeholder the roll-up resolves and hand-writes no status, which is what the
  lint's own contract asks for; reverting it would leave the roll-up naming this
  spec as `untracked` rather than `Draft`, measured on both states, and would
  not change the lint's exit status either way. The § "Corpus" exclusion rule
  already covers this spec generically (source: owner decision 2026-09-10 in the
  brief's A6 row for the first two; owner sign-off 2026-09-11 for the criterion-syntax
  section and the Spec map cell; and a fifth edit at close, advancing the brief's
  lifecycle from `Draft` to `Executing` because `lint-brief-coverage` refuses a
  `Draft` brief with a `Shipped` child — made under the owner's instruction to
  ship and clear CI, and reversible by one token)
- Process: this slice adds a tier blockquote to `assets/spec.md`, marking which
  sections a completion gate reads and which are working material an author
  corrects in place. That file is behind `Ask first` and the prose is not a
  cross-reference, so it carries owner sign-off rather than a residual, and the
  plan registers it as shipped without a criterion with its route (source: owner
  sign-off 2026-09-11)
- Product: this serves spec authors invoking `new-spec`, and the slice ends
  when the three checks over the skill's own artifacts exist, each named by a
  step with the form that invokes it, under ADR-0108's identifier standard (source: user
  confirmation 2026-09-10 for the audience; owner decision 2026-09-11 narrowing
  the end state, which supersedes the procedure-and-graded-run wording)
