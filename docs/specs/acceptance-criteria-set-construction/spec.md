# Spec: acceptance-criteria set construction

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
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

**Scope.** This spec ships the authoring moves below and states no count of
them. The moves share one defect: the skill tells an author
what a finished artifact
must look like and never what move to make, so an author selects by instinct,
places facts by habit, and answers every finding by repairing it.

**What carries a criterion here, and what does not.** The criteria below are the
obligations a machine decides: the governing set admission resolves against,
the set-level coverage read, per-task grounding, the count prohibition, the
frozen cases and their scoring, the identifier convention, and the checks the
skill ships over its own artifacts. The selection procedure's remaining stages,
the plan-authoring rules and the review-response protocol ship from this spec's
tasks and carry no criterion here: their only check would be that a sentence
exists, so they are routed to
`docs/product/intents/spec-authoring-protocol-measured-before-shipping.md`,
which gates promoting any of them back to a criterion on a frozen-case score.
Each is listed once in the plan's `## Shipped ahead of a criterion,
deliberately` with that route, and each is pinned by rule name in the pack
suite, so routing loses the obligation and keeps the check.

An author using `new-spec` — human or agent — decides *which* contract
obligations become acceptance criteria before wording any of them. The skill's
acceptance-criteria step carries an ordered selection procedure: name the
changed contract obligations, admit only candidates whose failure independently
blocks shipment *and* whose observing surface the author can name, attach one
positive and one disconfirming scenario per admitted obligation, route every
rejected candidate to a named owner — including, for an obligation whose
content only the build can settle, a discovery predicate in the plan rather than
an answer invented at approval time — then run the set-level pass the procedure defines.

The procedure is a **self-check the author runs while authoring**, not a gate
another party applies afterwards. Its load-bearing move is that a criterion is
admissible only once something is named that would show its failure: an
obligation whose observer cannot be named stays a candidate. The set-level pass, whose members the
procedure enumerates once and nothing else restates, reads coverage in both
directions — every obligation reaches a criterion or
a routed owner, and every criterion has exactly one observer. Necessity is
operational rather than a word in a list: each criterion names the input that
makes it red, and a criterion whose red input a sibling already covers is
merged or removed.

The author records the candidate count, the final count, and each candidate's
disposition. Success for that author is that a distinct obligation
and a non-waivable guardrail always survive selection, while a seeded
implementation detail, a duplicate claim and an example-only variant do not
become criteria. Criterion count is a descriptive outcome that orders how hard
the set-level pass looks; it never rejects a spec and never proves one is
well-shaped, so a genuinely large irreducible set survives.

Each criterion is then composed from the parts those steps already named — the
obligation, the surface that observes its failure, and its disconfirming and
positive cases — rather than written whole and tested afterwards. Composing
from singular parts is what keeps one criterion to one predicate.

Criterion *shape* — whether a given sentence is one criterion or two — stays
owned by the skill's `assets/spec.md`. This spec owns which obligations reach
that question at all, and where the hand-off to that owner sits: after routing,
before the set-level pass. Selection finishes first, and the pass then reads a
worded set together with the plan entries tracing to it — which is what its
uniqueness and necessity checks compare.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| User-facing promise | Applicable — adopters install the skill and need the procedure outside it | `guides/core/reference/acceptance-criteria-authoring.md` (new; the per-criterion section is a later slice's) | `author-product-docs` conventions | Page validates and publishes; `title` matches the leading H1 | Page exists, carries the set-construction section only, and passes the guide validators |
| Reusable learning | Applicable — the delivery gate is a recorded exercise, not a suite | `docs/specs/acceptance-criteria-set-construction/notes/verification-ledger.md` for the graded run; `notes/set-construction-self-application.md` for the procedure's own first use; [`docs/product/research/item-id-management-comparison-matrix.md`](../../product/research/item-id-management-comparison-matrix.md) for the identity evidence ADR-0108 and the architecture page both cite; [`docs/product/research/review-loop-nonconvergence-survey.md`](../../product/research/review-loop-nonconvergence-survey.md) for the round measurements the loop-contract page links | This spec's owner | The graded run's per-candidate dispositions; the transcript's dated addenda; the matrix's alternatives and their rejection reasons | Each destination exists, is dated where it records a run, and nothing an architecture page or decision record cites is left without an owner |
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
- Retiring, renaming or reordering an existing eval case.

### Never do

- Add a fixed absolute criterion count to any surface — a cap, a ceiling, a
  budget, a refusal, or a pass/fail bar on how many criteria a spec may carry. A
  percentile derived from the author's own corpus, used only to order scrutiny,
  is not one of these and is required elsewhere in this contract.
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
  general. This slice's evaluation covers three frozen cases and nothing wider.
- Build the identity or fingerprint mechanism beneath the single-homing check.
  The phrase-based oracle is how that check already works; leaving it is
  declining to repair a pre-existing gap, not shipping new debt, and everything
  this spec delivers works the same underneath it.

## Testing Strategy

- **The admission grounding and the set-level coverage read (AC-0006,
  AC-0011):** goal-based check over the authored skill file. The observation
  is the presence and scope of that prose; the verification surface is the
  pack-local suite.
- **The count prohibition (AC-0018) — split surface.** The span check that the
  procedure states no fixed absolute count is a goal-based check on the
  pack-local suite. The sweep across all three shipped surfaces is a goal-based
  check at repository level, because reading the guide page from
  `packs/core/tests/` breaches the pack-test boundary. Both are named here so the
  declared placement matches where each check lands.
- **The three frozen cases and their seeded integrity (AC-0019, AC-0020):** TDD. Each
  case is data whose required shape and seeded material are compressible into
  assertions.
- **The frozen scoring order (AC-0021):** goal-based check. The observation is that
  every frozen case's stated scoring contract carries the three grading ranks
  and the losing-an-obligation failure rule; the verification surface is the
  pack-local suite.
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
- **Every shipped check names its consuming step (AC-0038):** goal-based check
  over the authored skill file, on the pack-local suite. The surface is the
  skill's procedure, not a gate list, and the check reads the skill's own
  `scripts/` directory rather than a restated inventory, so a check added later
  without a named caller fails rather than passing unnoticed.
- **ADR-0108's confirmation state (AC-0032):** goal-based check over the ADR,
  at repository level. The ADR is not pack content, so the pack-local suite
  cannot read it.
- **The alignment checker (AC-0033):** TDD. The check is a pure function over a
  spec directory's two texts and its retired list, so its cases compress into
  assertions. Its scope is deliberately distinct from the repository's
  spec-status lint, which decides spec *state* — status vocabulary, criteria
  checked at a ship transition, deferral anchors, contract traceability. This
  one decides *item alignment* and owns no lifecycle question.
- **Per-task grounding (AC-0031):** goal-based check over the authored skill
  file, on the pack-local suite. The plan step is its surface, not the
  acceptance-criteria step.
- **The template carries the identifier convention (AC-0030):** goal-based check
  over `assets/spec.md`, on the pack-local suite. The asset sits inside
  `packs/core`, so no pack-test boundary is crossed.
- **The recorded run, both graded ranks (AC-0028, AC-0029):** visual / manual QA. A model-in-the-loop
  measurement runs in-agent through one fresh subagent per case, and its recall
  verdict is read by a human from the recorded dispositions. No mechanical proxy
  substitutes for that reading.

## Acceptance Criteria

- [ ] **AC-0006.** The procedure carries an admission step, and a candidate passes it only
      once it is grounded in what already
      governs the surface it demands content on. The procedure defines that
      **governing set** once, and names its members: the scoped `AGENTS.md`
      files, resolved by walking from the surface's own directory up to the
      repository root and reading each file found; the gates and linters that run
      against that surface; the documents that already own rules for it; and the
      repository conventions that apply to it. A candidate demanding what any
      member forbids is not admissible in that form. The `AGENTS.md` member is
      stated as a walk, not a single lookup, because a nested file does not
      replace the one above it and stopping at the first hit skips the rest
      silently. The remaining members are named because guidance files are the
      surfaces an author thinks to read, and a linter, an existing owner and a
      convention are the ones that actually fail the work.
- [ ] **AC-0011.** The procedure carries a pass over the set as a whole, after the
      per-criterion work, and that pass reads coverage from the criteria back to
      their observers: every admitted criterion has exactly one observing
      surface, and a criterion with none, or with two, fails the pass. Both
      halves are required of the prose: a procedure with no set-level pass
      satisfies a coverage rule that assumes one.
- [ ] **AC-0018.** No surface this slice ships — the procedure span, the guide page, or the
      frozen eval entries — states a fixed absolute criterion count, meaning a
      cap, ceiling, budget, refusal or pass/fail bar on how many criteria a spec
      may carry, and a set above the author's stated threshold passes on its
      obligations alone.
      The surface set is the surfaces this slice's count prose ships on,
      because that is what the check reads. The spec template is deliberately
      outside it: this slice authors identifier-convention prose there and no
      count prose, so no text the check would look for lands in it. Surfaces
      carrying older count prose are a recorded residual, not this criterion. The wider claim that count never proves quality is a
      non-waivable Boundary, not this criterion, because no check reaches it.
      The procedure also states the authoring rule this follows from: where a set
      is enumerated, name the set, never its cardinality, since a numeral beside
      an enumeration is checkable only against the list it duplicates and goes
      stale when a member is added. The same rule forbids a count of the
      delivery's own history — rounds run, defects a class produced, rules landed
      ahead of their criterion — which belongs to the changelog.
- [ ] **AC-0019.** The skill's eval register carries one frozen case per named
      shape: a small change, a large change, and an amendment to an existing
      contract. Whether the large case's obligation set is genuinely irreducible
      is a review obligation, not this criterion — no check reads it, and a
      criterion claiming it would reach past its own oracle.
- [ ] **AC-0020.** Each frozen case carries its full seeded set: at least one
      implementation detail, one duplicate claim and one example-only variant
      that must not become criteria, and every objective and non-waivable
      guardrail that must remain represented.
- [ ] **AC-0021.** The shipped scoring order grades obligation and protected-guardrail
      recall first, non-criterion rejection second, and count as a descriptive
      outcome only, and records that a smaller set obtained by losing a
      distinct obligation or guardrail is a failure.
- [ ] **AC-0028.** The recorded three-case run retains every seeded objective and
      non-waivable guardrail.
- [ ] **AC-0029.** That run admits no seeded implementation detail, duplicate claim or
      example-only variant as a criterion.
- [ ] **AC-0030.** The skill's bundled `assets/spec.md` carries the loop-contract
      identifier convention, stated directly rather than cited because shipped
      pack content carries no internal-record citation: every acceptance
      criterion and every verification item takes an opaque, append-only
      identifier scoped to its own spec directory, drawn from a class-marked
      form — `AC-` for an acceptance criterion, `VI-` for a verification item —
      so a reference names which class it resolves against and a derived
      identifier is detectable rather than a matter of opinion. Each is assigned
      once, never
      renumbered on insertion or reorder, never reused after removal, and each
      removal recorded under a `## Retired identifiers` heading in the same
      artifact, one bare identifier per list item, the heading omitted while
      nothing has been retired — and the template's own
      criteria list shows the labelled form, so a criterion is cited without
      being counted. The template also fixes the verification group's shape: a
      Testing Strategy group is a list item whose leading bold segment names, in
      parentheses, every criterion it covers. Without a stated shape the
      one-group-per-criterion rule has nothing to read.
- [ ] **AC-0031.** The plan step requires each task to be grounded against the same
      governing set AC-0006 defines, resolved for the surfaces that task's own
      work touches rather than for the plan as a whole, and to record what it
      resolved. A plan-level anchor list is not sufficient and the procedure says
      so: it is written once, against the surfaces the author expected to touch,
      and a task added later inherits it without ever testing it. The procedure
      names no tool for the resolving. It requires the recorded result and
      instructs the author to pick the most token-efficient bounded exploration
      the session actually offers — a subagent, a worker, or a direct search —
      because a named tool makes the rule unrunnable wherever that tool is
      absent, and the obligation is the grounding, never the mechanism. The
      resolving runs mechanically first and semantically second: every file that
      names a touched path is enumerated by search before any model is asked
      which rules apply, because the search is exhaustive over
      references-by-path while the question is not. What the search cannot reach
      — a gate matching by glob or directory walk, and a rule that applies by
      content rather than by path — is the stated residue that review still
      owns.
- [ ] **AC-0032.** ADR-0108's `Revisit if` names a tool that enforces no-reuse for
      inline-Markdown items, and the checker below is that tool, so the trigger
      fires on delivery. The ADR's `Confirmation` moves from reviewer-checked to
      the shipped check and its `Revisit if` records that the trigger fired and
      the decision stands unchanged. A shipped decision record stating that no
      lint enforces it, on the commit that ships the lint, is the conflict the
      repository's own guidance forbids resolving silently.
- [ ] **AC-0033.** The skill ships its own alignment checker, invoked from its own
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
- [ ] **AC-0041.** The skill ships a grounding explorer in its own `scripts/`,
      depending on no other skill, answering the mechanical half of AC-0031 from
      a seed set of touched paths: which files name a seed, which historically
      change with one, which gates would run one, which quote a distinctive line
      from one, and which scoped guidance governs each, plus which paths a seed
      names that no longer resolve. It reads no configuration file of its own,
      and its own top-level expectations are the adopter repository's rather than
      this one's.
- [ ] **AC-0042.** The probe set is selected by stage rather than run whole: a probe
      outside a stage's set does not execute, and each stage's report names the
      probes it ran. Selection is executional rather than a filter on the output,
      because a discarded result is work an adopter paid for, and an oracle that
      reads only the report cannot tell a probe that was skipped from one whose
      output was suppressed.
- [ ] **AC-0043.** The thresholds whose right value is repository-shaped — the
      sweep-commit size and the phrase cutoff — derive from the adopter
      repository's own distribution, and the report names each value with what
      produced it, on every stage, whether or not that stage's probe set consumes
      the value, so a defaulted value is not labelled as measured and an absent
      line is not read as an absent derivation. The minimum co-occurrences before
      a partner is reported filters results rather than presenting them, so it is
      reported on every run though it is not derived; the remaining bounds are
      presentation limits with documented defaults and flags.
- [ ] **AC-0044.** Every probe reports and none decides, and every probe carries a
      bounded result. A probe whose input can be missing distinguishes found,
      none found, and input unavailable, since empty and unavailable are
      otherwise indistinguishable: those are the probes reading a seed's text, a
      runner set, or history — phrase pins, dead references, gate reachability
      and co-change. The probes reading the tree itself — scoped guidance, path
      references and the surface inventory — cannot have a missing input and
      distinguish found from none found. Both memberships are stated here so no
      probe is left without a declared case shape, and so no outcome is claimed
      that the code cannot reach.
- [ ] **AC-0045.** What the explorer cannot settle mechanically it emits as a named
      ambiguity with its candidate resolutions, for the author to decide once and
      record. An absent or thin grounding surface lowers the starting information
      and never fails the run, and in the stages whose probe set includes it, the
      report inventories which known grounding surfaces are present and which
      carry content, so a degraded grounding is legible rather than silent.
      Consuming those surfaces as probe input — a recorded value seeding a
      derivation, and a record the repository contradicts reported as drift — is
      named in the follow-on that owns it, not claimed here.
- [ ] **AC-0039.** The alignment checker reports a task entry whose text is
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
- [ ] **AC-0040.** Given a base revision, the alignment checker reports each criterion
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
- [ ] **AC-0038.** Every check the skill ships in its own `scripts/` is named by the
      step of the procedure that consumes it, so no shipped control is one
      nobody runs: the grounding explorer at the discovery pass,
      and the alignment and finding-coverage checks at the steps whose artifacts
      they read. This does not reach AC-0031's prohibition on naming a tool for
      the per-task resolving. That prohibition exists because a mechanism a
      session may not offer makes a rule unrunnable wherever it is absent; a
      check shipped inside the skill is present wherever the skill is, and the
      obligation it carries is the invocation, not a choice of mechanism.
- [ ] **AC-0037.** The skill ships a finding-coverage check in its own `scripts/`,
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
- AC-0007
- AC-0008
- AC-0009
- AC-0010
- AC-0012
- AC-0013
- AC-0014
- AC-0015
- AC-0016
- AC-0017
- AC-0022
- AC-0023
- AC-0024
- AC-0025
- AC-0026
- AC-0027
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
- Technical: an eval entry carries exactly `id`, `prompt`, `expected_output`
  and `assertions`, with unique ids across the register (source:
  `packs/core/tests/skills/new-spec/test_acceptance_criteria_discipline.py`)
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
  section and the Spec map cell)
- Product: this serves spec authors invoking `new-spec`, and the slice ends
  when the procedure, the guide's set-construction section, the three frozen
  cases, their seed pinning and the recorded run exist (source: user
  confirmation 2026-09-10)
- Product: the recorded three-case run happens inside this delivery rather
  than as a later exercise (source: user confirmation 2026-09-10)
