# Plan: load-bearing-claim-grounding

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `packs/AGENTS.md` for the pack release surface and the
  portability rule that forbids an install path in a shipped body;
  `packages/agentbundle/agentbundle/catalogue_tooling/skill_spec_lint.py:516-547`
  for the body limits a skill edit is measured against. Analogous shipped
  implementations of "one normative rule in a skill step plus a structural
  control": `docs/specs/spec-authoring-discipline/` and
  `docs/specs/construction-time-razor/`, both Shipped, both pairing a
  `new-spec` step edit with a test under `packs/core/tests/skills/new-spec/`;
  that directory is the construction path. Named uncertainty: the obligation is
  prose, so no control reaches whether an author applied it — `spec.md` §
  Testing Strategy gates the structural properties only and says which property
  it leaves ungated.

## Approach

One normative rule lands in `new-spec`'s assumptions step, which already owns
"surface a claim, then get evidence for it". The rule is a **routing table**: a
claim the author cannot settle goes to one of three destinations chosen by what
its falsehood would cost. The table's key set is pinned by a fixture written in
the test rather than read from the table, which is what makes it checkable beyond
presence.

Nothing about evidence *selection* ships. Five candidate evidence-shape demands
were cut across four review rounds and an extended sample of seven deliveries,
each on measured evidence recorded in `notes/replay.md`, and AC-0008 keeps the
cut contractual rather than trusting it to stay cut. The pre-review probe step is
untouched; the parent brief assigns it to slice A4. Two consuming surfaces gain
the owning step's anchor identifier and no table row.

The one-per-candidate cardinality is removed from **both** places it appears,
because a claim routed to a pre-approval spike may need more than one check. The
step's separate bound against an unbounded sweep is retained: removing the
cardinality must not take the protection with it.

## Constraints

- The skill body may not cite an install path, and stays under the 1000-line
  body error.
- The pre-review disconfirming-evidence step's heading is pinned by
  `packs/core/tests/skills/new-spec/test_acceptance_criteria_discipline.py:120-122`
  and does not move.
- Projection parity and the version increment have shipped owners and get no new
  control.
- `notes/replay.md` is complete before scope approval. It is an approval
  precondition and non-normative rationale, so it owns no task and no criterion.

## Construction tests

Per-task, listed below. **Integration tests:** none beyond per-task tests.
**Manual verification:** the shipped rule exercised against two real claims,
recorded in the verification ledger — T3.

## Durable-output map

| Semantic role | Destination | Task |
| --- | --- | --- |
| Shipped agent guidance | `new-spec`'s assumptions step | T1 |
| Shipped agent guidance, pointer only | the `work-loop` plan-stage self-coverage step | T2 |
| Adopter-facing description | `guides/core/how-to/plan-and-execute-non-trivial-work.md` | T2 |
| Release history | `docs/product/changelog.md` | T4 |
| Reusable learning | `project-knowledge` topics | T4 |

## Design (LLD)

### Design decisions

**Why the assumptions step and not the pre-review probe step.** The claim becomes
an artifact at the assumptions step; the probe step fires later, once a plan
mechanism exists, and the parent brief assigns that surface to slice A4.
`construction-time-razor` measured the gap precisely: it complied with the
existing one-throwaway-check rule "and did — while leaving the
inadequate-candidate, refusal-status, schema-field, and required-construction
claims unresolved". One probe of the load-bearing mechanism is not a routing
decision for every unresolved consequence-bearing claim.

**Why three destinations and not a single "spike it" rule.** Both failure
directions are measured in the sample. `work-loop-in-process-guards` states the
under-firing cost as a design finding — "the tooling forbids exactly the
mid-execution amendment the contract invites, and the only sanctioned escape is a
destructive reset" — with eight amendments queued for a human gate and one
`Touches:` field still false in the shipped contract.
`construction-time-razor` supplies the over-firing counterexample by measurement:
its required-construction control was rebuilt two ways, "Both satisfied the
pre-existing consumer's `render` protocol and both passed", so "A pre-approval
spike intended to select the class, module, or helper shape would therefore have
been wasted design work."

**Why no evidence-shape obligation ships, and why that is a criterion.** Five
candidates were cut, and AC-0008's fixture is exactly those five.
`set-membership` went after two sharpenings, once the cited delivery proved it had
already reported residuals on both instruments and still missed the defect.
`sweep-completeness` went because `work-loop` DECIDE owns it with a real
comparator. `generated-measurement` went because every instance belonged to DECIDE
or to step 5's oracle rule. `reused-machinery` went because the plan's claim about
those helpers was true at approval and the misuse arrived in a post-gates repair.
`generated-output` went last, chased into a fourth delivery added specifically to
earn it: "Counting it would broaden the proposed obligation from claims about
generated artifacts to every authored source that will later be projected."
AC-0008 exists because a cut held only by a changelog entry is a cut that comes
back.

**Why the routing table's key set comes from a fixture in the test.** A criterion
reading "total over the inputs it names" takes its domain from the artifact under
test, so an omitted or renamed input redefines the property instead of failing
it. The control compares parsed keys against a literal set written in the test,
before building any mapping.

### Dependencies & integration

No new dependency. The construction path is the existing
`packs/core/tests/skills/new-spec/` suite.

## Tasks

### T1: The routing table lands, and the one-check cardinality goes

**Depends on:** none

**Touches:** packs/core/.apm/skills/new-spec/SKILL.md,
packs/core/tests/skills/new-spec/test_load_bearing_claim_grounding.py

**Tests:** a new suite at
`packs/core/tests/skills/new-spec/test_load_bearing_claim_grounding.py`, reading
the shipped `SKILL.md` from the pack tree. Only AC-0001's case is two-sided —
obligation present on the owning surface and absent from every excluded one; the
rest carry the criterion-specific falsifier `spec.md` § Testing Strategy names for
each:

- the category enumeration in the assumptions step resolves to exactly three, and
  the step states the rule applies across them (AC-0003);
- the consequence test enumerates exactly six consequences, with a case that
  reddens on a seventh and a case that reddens on an alternative test (AC-0004);
- the firing bound is located inside the same step as the obligation, asserted by
  section extraction rather than by a whole-file search, because a whole-file
  search is satisfied by a preamble (AC-0005);
- the routing table's parsed row keys are compared against a literal
  three-element fixture — `reaches-the-contract`, `unstarted-task-method`,
  `cheap-with-an-oracle` — as the first assertion, before any mapping is
  constructed; each maps to exactly one destination; and the
  `unstarted-task-method` destination enumerates five fields including a kill
  condition. The fixture is written in the test, never read from the table
  (AC-0006);
- the routing table appears in exactly one file, the scan enumerating every
  regular Markdown file reachable recursively from `packs/core/.apm/skills` and
  `guides` (AC-0001);
- the pre-review step's heading, firing condition, and probe bound are byte-equal
  to their pre-change text, pinned by a digest computed in this task from
  `git show HEAD:` rather than from the working tree (AC-0007);
- the step names none of the five cut shape identifiers — `reused-machinery`,
  `set-membership`, `generated-output`, `generated-measurement`,
  `sweep-completeness` — and carries none of their demand sentences, with each of
  the five injected in turn as a mutation that must redden. The closed set is the
  whole obligation; no arm claims to detect a paraphrase outside it (AC-0008);
- the one-per-candidate cardinality is absent from **both** homes, the step's
  heading and its load-bearing body sentence, **and** the step's bound against an
  unbounded sweep is still present (AC-0009).

**Approach:** **Replace** the one-per-candidate cardinality in both places it
appears — the step heading's "run one targeted verification check per candidate
first" and the body's "one targeted check per candidate assumption" — because
`reused-machinery` demands two, a contract read and a discriminating example, and
removing only the body sentence leaves the contradiction in the heading. Keep the
step's bound against an unbounded sweep: two targeted checks are not a sweep. Add no sibling step and no fourth category. Give
the step a stable anchor identifier so T2's pointers have something exact to
carry. Keep the body under the 1000-line error and cite no install path.

**Done when:** the new suite is green, and each arm reddens when its own
obligation is removed from `SKILL.md`.

### T2: The two consuming surfaces carry the anchor identifier and no table row

**Depends on:** T1

**Touches:** packs/core/.apm/skills/work-loop/SKILL.md,
guides/core/how-to/plan-and-execute-non-trivial-work.md,
packs/core/tests/skills/new-spec/test_load_bearing_claim_grounding.py

**Tests:** cases added to T1's suite, a presence-and-absence pair on the same two
surfaces: each carries the owning step's anchor identifier verbatim, and each
carries no row of **the routing table** — the only table this change ships — with
the row-absence arm driven from the single table T1 parses rather than from a
literal (AC-0002).

**Approach:** The how-to currently restates the superseded sentence at line 80,
so it is a companion statement that goes stale on T1's edit rather than an
optional addition. It carries the pointer, never a copy — which is why AC-0002
asserts identifier equality and not that two prose passages agree.

**Done when:** those cases are green and each arm reddens when its pointer is
removed.

### T3: The shipped rule is exercised against two real claims, and registered

**Depends on:** T2

**Touches:** docs/specs/load-bearing-claim-grounding/notes/verification-ledger.md,
packs/core/.apm/skills/new-spec/evals/evals.json

**Tests:** no stub (visual / manual QA). Run the assumptions step of the shipped
`new-spec` against two claims from this delivery's own authoring — one
contract-reaching and one task-local — and record the observed routing, the
evidence each shape demanded, and whether the ordinary facts were left alone.

**Approach:** The artifact is guidance an agent reads, so the documented happy
path is a real authoring pass; a green suite is not a substitute. Add one output eval to the skill's register in the
same task, and record in the ledger that no workflow executes it — `pack evals
run`'s `--check` carries `choices=("activation", "behavior")` defaulting to
`activation`, `pack-evals.yml` passes neither `--mode` nor `--check`, and the
defaults select headless activation over `eval_queries.json` — so the entry is
documentation, not coverage. Neither observation closes a criterion.

**Done when:** the ledger records both routings with the evidence actually
obtained, records any case where the rule over-fired, and states that the eval
register entry is executed by nothing rather than implying coverage.

### T4: The release surface and the learning capture carry the change

**Depends on:** T3

**Touches:** packs/core/pack.toml, packs/core/.claude-plugin/plugin.json,
docs/product/changelog.md

**Tests:** no stub (goal-based check). `make build-check` passes, which runs both
`agentbundle catalogue self-host --check` for projection parity and the pack
delivery-contract suite for the version increment.

**Approach:** Patch bump 2.26.11 to 2.26.12 across `pack.toml` and
`plugin.json`, with a changelog entry in the same change. Core carries no root
marketplace entry, so the surface is three files. Regenerate the `.claude/` and
`.agents/` projections through the supported self-host path; do not hand-edit a
projection.

**Done when:** `make build-check` is green and the three version surfaces agree.

## Rollout

- **Delivery:** big bang, no flag. The change is guidance an agent reads on
  invocation; reverting the commit reverts it entirely.
- **Infrastructure:** none.
- **External-system integration:** none.
- **Deployment sequencing:** the projection regeneration and the version bump
  travel in the same change as the authored edit, because the self-host check
  compares them.

## Risks

- **The rule ships and never fires.** The parent brief names this as the most
  likely failure for an authoring rule, and this delivery does not measure
  activation. Mitigated only by routing that question to its owning brief and
  claiming no behaviour change; the risk is accepted, not closed.
- **A structural control passes a wrong sentence on the right surface.** This is
  not fully mitigable and is not claimed to be. The routing table's totality and
  disjointness reach further than presence, and the ungated property is named in
  the spec's Testing Strategy rather than left to a reader to infer.
- **The rule over-fires on ordinary facts.** Mitigated by stating the firing
  bound in the same step as the obligation, and probed in T3 by recording any
  over-fire against a real claim.

## Changelog

- 2026-09-17: Owner approved the recut contract and directed implementation.
  Rounds 5 and 6 ran before the gate, returning 6 then 8 findings, all
  sustained. Round 6's findings were entirely defects in round 5's own repairs,
  and six of the eight were one class: a count or a scope word corrected at the
  instance and left standing elsewhere. The baseline count was the worst of them
  — **three** sampled deliveries ran with all four catchers, not one, so this
  record had been understating its own evidence in three separate places. Fixed
  by class sweep rather than instance: AC-0008 is now a five-entry
  identifier-and-sentence fixture rather than a prose prohibition; AC-0007 gains
  a named falsifying mutation; T1's two-sided differential claim is scoped to
  AC-0001; every plural-table reference outside this changelog is singular; the
  `--check` flag is named correctly, `--mode` having been wrong while the
  no-coverage conclusion it supported stayed right; and `generated-output` is
  counted among the five cut shapes rather than as a sixth.

- 2026-09-17: Sample extended to seven deliveries on owner instruction, using two
  Codex investigators and three subagents. **Every evidence-shape demand is now
  cut and the delivery ships the consequence routing alone.** `generated-output`
  was chased into `agent-skill-engineering-subagent-and-plugin-concepts`, the
  delivery that carries its only two-amendment evidence, and is not earned there:
  the frozen text made no claim about the generated tree, and counting it would
  broaden the obligation to every authored source that will later be projected.
  The round-3 discriminator — frozen-at-approval — is **withdrawn as untestable**:
  no `plan.md` in the sample records an owner-approval line, which one Codex
  investigator returned as an explicit indeterminate verdict. Dating established
  that three deliveries ran with all four catchers in force — this entry first
  said one, which was wrong when written and is corrected here rather than
  preserved — and that `construction-time-razor`, the one of those three replayed
  against the routing rule,
  both corroborates the routing rule and names the exact delta over shipped
  guidance. AC-0008 was added so the cut is contractual rather than held by a
  changelog entry. AC-0009 now covers both homes of the cardinality. Nine
  criteria. A well-evidenced post-gate replanning finding was routed to S2 rather
  than absorbed.

- 2026-09-17: Round 3 returned seven findings; five sustained, two refuted. The
  `generated-measurement` demand is cut: every instance in the sample is owned by
  DECIDE's companion sweep or by step 5's oracle rule, and none cost a contract
  amendment. `paths-ignore` was recorded as "caught twice over" and only half of
  it was caught, so that row is a pointer. AC-0009 narrowed to exclusion of three
  literal row keys, because an exact key set cannot see an obligation smuggled
  into a surviving cell. The cardinality criterion — a tenth at the time, and
  AC-0009 after the round-4 cuts renumbered the set — now removes only the
  one-per-candidate
  cardinality, from both its homes, and explicitly retains the step's no-sweep
  bound — two targeted checks are not a sweep. **Refuted:** that the earlier
  aggregate of 16 findings was stale; round 1 was two reports, 10 and 6, and the
  round-3 brief undercounted by omitting the shaping report. Across three rounds:
  23 findings, 21 sustained, 2 refuted. **What ships is now two evidence demands,
  one pointer, and the consequence routing** — the routing half carrying the
  strongest evidence in the sample.

- 2026-09-17: Drafted. The replay against `pr-gate-suite-disposition` plus
  `telemetry-sender-owns-its-configuration` and `loop-telemetry-export` returned
  narrow-not-kill: four evidence shapes are new obligations, two already have
  owners and ship as pointers, and the unstarted-task route gains exactly one
  field. The typed-literal and trigger-filter probe targets are recorded as not
  new catches and are not claimed. Owner confirmed the narrowing.
- 2026-09-17: The pre-review probe step was excluded from scope on the parent
  brief's record that slice A4 keeps that surface, its firing predicate and its
  eval. `grounding-probe-extensions.md` was read and is adjacent, not the same
  work: it adds executable probes, and its held experiment independently records
  that the claim-versus-check halves already have owners.
- 2026-09-17: Round 2 returned seven findings, five of them Blockers, all
  sustained. Two cut shipped content rather than sharpening it: the
  set-or-roster shape is deleted after two sharpenings, because the cited
  delivery had already reported residuals on both instruments and still missed
  the defect, and the sweep shape is deleted because DECIDE owns it with a real
  comparator and the assumptions step is the wrong home. The tables' key sets
  moved to fixtures written in the test, because "total over the shapes it
  names" sourced its domain from the artifact under test. AC-0001's roots are
  now exact paths. A tenth criterion was added, carried today as AC-0009: the
  superseded one-check sentence is
  replaced, not supplemented, because it forbids a sweep while the
  `reused-machinery` demand requires two checks. Ten criteria; three evidence
  demands and one pointer.
- 2026-09-17: Two pre-approval review rounds, 16 findings, four of them
  Blockers, all sustained. Three landed on the replay itself and two of those
  obliged a sharpening of what ships: residuals bound per producing instrument,
  and a measurement naming its counted unit. The blanket baseline claim was
  refuted and corrected per delivery. The four Blockers shared one premise —
  prose obligations authored as acceptance criteria — so the criteria were
  recut onto mechanical properties: single home, anchor-identifier pointers,
  taxonomy, predicate, predicate placement, two total-and-disjoint tables, a
  digest pin, and the narrowing negative. The behavioural property is now
  explicitly ungated per the shipped rubric's class 6, observed in T3 and in a
  register entry that states its own non-detection. Nine criteria; the replay
  lost its task and became an approval precondition.
