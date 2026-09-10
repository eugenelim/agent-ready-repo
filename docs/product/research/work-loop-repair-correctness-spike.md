# Work-loop repair correctness — validation spike

Paired current-path/closure-packet repair measurement from identical pre-repair bytes, testing the
riskiest assumption of [work-loop repair correctness](../intents/work-loop-repair-correctness.md),
the third child of [work-loop delivery efficiency](../intents/work-loop-delivery-efficiency.md).

- **Run date:** 2026-09-09
- **Owner:** eugenelim, Platform Core maintainer
- **Verdict:** recorded in [Survive/kill: the immediate-stop rule fired](#survivekill-the-immediate-stop-rule-fired) below
- **Kill condition:** predeclared 2026-09-09 in the child intent, before any case ran; the exact
  clauses are quoted in the calculation section rather than restated loosely

This validation is independent of [focused re-review](work-loop-focused-re-review-spike.md), which
was killed on 2026-09-09. Both arms here use the repository's current broad post-repair review, so
nothing in this result depends on that sibling surviving. The corpora do not overlap: no repair
event used here was used there.

## What this spike tests

The riskiest assumption is that a compact, obligation-aware closure packet plus targeted
verification materially reduces repair-induced defects and total repair-to-verdict cost beyond the
**real current implementer path and its gates** — not beyond the predecessor spike's weakened
experimental conditions, where repairs were forbidden from running the gate suite and projections
were synchronised by hand.

Both arms start from the same frozen pre-repair tree with the same complete adjudicated finding set,
use the same model and permissions, run every applicable current gate, and receive the same broad
post-repair reviewer and adjudicator. Only the dispatch context differs.

## Frozen corpus

All four cases were preselected and recorded here before either arm ran on any case. No case was
replaced, split or reclassified after any result was seen.

A **repair event** is one natural repair commit answering one adjudicated review round. This
repository records that round durably in the repair commit's own message — sustained and refuted
counts, each finding's severity band, the adjudicated mechanism, and the remedy applied. That
message is the complete adjudicated finding set for the event. Both arms receive it in full; every
sustained finding answered by the natural repair revision stays in the case and none may be split
or selected after results are visible.

- **Pre-repair revision (P)** — the tree both arms start from and repair.
- **Historical repair revision (R)** — `P`'s child, the natural repair. It supplies the finding set
  and is the reference for what a competent repair had to close. Neither arm sees it.
- **Base (B)** — the branch point, `git merge-base M^1 M^2` for the merge commit `M` that landed the
  branch. Every case has zero merge commits in `B..R`.

| Case | Stratum | Obligation class | Pre-repair (P) | Historical repair (R) | Base (B) | Whole change | Repair diff |
| --- | --- | --- | --- | --- | --- | --- | --- |
| P1 | low-risk | register, approval, freeze | `2262670c4` | `13870d506` | `98df5599c` | 9 files, +879 | 4 files, +25/−20 |
| P2 | ordinary | projection, release | `02485d40d` | `7c14fbac4` | `236ae549c` | 23 files, +896/−68 | 21 files, +573/−175 |
| P3 | ordinary | logic, executable control | `b67499d02` | `e9898f7ba` | `7b6c5dd8e` | 12 files, +2366/−109 | 3 files, +198/−46 |
| P4 | high-risk | logic, executable control | `c073dd1f0` | `d58149eeb` | `4d2ef2b5a` | 6 files, +388/−10 | 2 files, +104/−27 |

The intent requires two events whose repairs trigger projection, release, register, approval or
verification obligations and two whose repairs change logic or an executable control. P1 and P2 are
the first pair; P3 and P4 are the second.

| Case | Whole-change digest | Repair-diff digest | Accepted contract | Contract digest at R |
| --- | --- | --- | --- | --- |
| P1 | `a0006fe45fe709d2` | `f947d437d6c9b34b` | `docs/specs/dependency-scoped-completion-receipts/spec.md` | `4c3f8f9e13543872` |
| P2 | `bbe4cd423516ec4f` | `ad20ce673416dbde` | `docs/CONVENTIONS.md` | `cc20369c65df0c08` |
| P3 | `bfc20da2cf447ac5` | `66494a7c820b9f23` | `docs/specs/cooling-untrusted-input-refusals/spec.md` | `ea4e74c64a49f766` |
| P4 | `2599a5212d8cffef` | `99d199689572e910` | `docs/CONVENTIONS.md` | `6faf0753654df33b` |

### Why each case sits in its stratum

The stratum rule is the same one used for the sibling spike and was fixed before selection.
**Low-risk**: the repair touches only prose or test files and no protected consequence class is
reachable from it. **Ordinary**: the repair changes user-visible behaviour, agent-facing
instructions or a released pack surface, with one owner and no destructive, migration,
security-boundary or breaking-public-contract trigger. **High-risk**: the repair reaches a protected
class.

**P1 — low-risk; register, approval and freeze obligations.**
`docs(specs): close the final pre-EXECUTE review's freeze-bound findings`. Four files: a spec body,
a plan body, an ADR and the `docs/specs/README.md` register row. The obligations are the ones a
docs repair must not miss — a register row that must stay consistent with the tree, an ADR index
ordering, and a spec whose criteria are freeze-bound at the pre-EXECUTE boundary. No executable
behaviour changes.

**P2 — ordinary; projection and release obligations.** `fix(core): settle five review findings on
the closeout residue blocker`. This is the richest obligation case in the corpus: one edit to
`packs/core/.apm/skills/workspace-status/scripts/workspace_status.py` must be regenerated into
**four** projection trees (`.agents/`, `.claude/`, `packages/agentbundle/_data/`, and the pack's own
tree), and the change carries a `pack.toml` and `plugin.json` version bump, a `docs/product/changelog.md`
entry and a regenerated `web/src/lib/now-highlights.generated.json`. The adjudicated round is five
findings — one MAJOR cooling-symmetry defect where two shaping arms disagreed about a retired entry,
one MAJOR untested-branch defect, and three MINOR fixture-validity defects where every fixture wrote
`**Status:** X` rather than the list-item form the parser reads, so no artifact status resolved and
a collection was vacuously true on empty state.

**P3 — ordinary; logic and an executable control.** `fix(core): refuse a completion date with no
review date, and close two unguarded sites`. `packs/core/.apm/skills/close-work/scripts/cooling.py`
plus its test module and a changelog entry. The defect is a schema-valid escape: the contract's
`calendarDate` pattern has no year ceiling, so `completed_on = 9999-12-02` makes the review date
overflow, `OverflowError` subclasses `ArithmeticError`, and it matched no handler across five entry
points. It also closes two `_matches` sites that had no criterion that could fail. There is a clean
executable oracle here.

**P4 — high-risk; logic, an executable control, and a privacy class.** `fix(tools): replace the
maintainer-email pattern rule with a reviewed host allowlist`. The pre-repair commit shipped a lint
that was supposed to keep published pack maintainer emails non-identifying, and the round-1 review
Blocker is that three addresses defeat it — including one that is not a valid address at all, where
`partition("@")` split on the first `@` and left the local part reading `noreply`. The protected
class is privacy: the control exists to stop an identifying maintainer address reaching a published
pack, and it did not. This case has the sharpest targeted verifier in the corpus — the three bypass
addresses must exit 1 after the repair and did exit 0 before it.

## Controls carried forward from the sibling spike

Both were directed by the owner on 2026-09-09 and are recorded here **before either arm ran**,
because the first changes how a kill-condition clause is counted.

### Control A — pre-existing defects are counted separately from repair-induced ones

The kill condition turns partly on repair-induced sustained clusters. A defect that was already
present at the frozen pre-repair revision `P` is not repair-induced, however the post-repair reviewer
words it. Such defects may legitimately raise an arm's terminal review and adjudication cost, and
that cost is reported, but they must not inflate either arm's repair-induced count.

The blind adjudicator is therefore given the pre-repair revision as well as the repaired one, and
must return a `provenance` ruling on every sustained finding:

- `pre-existing` — the defect is demonstrably present at `P`. Cite the evidence at `P`.
- `repair-induced` — the defect is demonstrably absent at `P` and present after the repair.
- `indeterminate` — provenance could not be established from the two revisions.

Only `repair-induced` clusters count toward the kill condition's repair-induced clause. Pre-existing
and indeterminate clusters are reported separately and never folded in.

This control is a direct consequence of the sibling spike, where all three deciding misses turned
out to be defects committed upstream on the branch rather than anything the repair did. Counting
those against a repair arm would have measured the corpus, not the mechanism.

### Control B — unresolved merge markers are a deterministic gate opportunity, not a review problem

Recorded as an observation routed to the parent intent's gate-economics evidence, not as a new
intent and not as a finding against either arm here. This repository has **no** gate that detects
committed conflict markers; the measured `git grep` over a tree object cost **0.35 s**, fired on the
sibling spike's pre-repair and repaired revisions and was clean at their base. The three sustained
public-contract clusters it would have caught cost a broad reviewer 529.9 s and 10,603,322 tokens to
find after eleven review rounds had missed them. A later history scan found three commits in 5,001,
all from the same self-corrected incident, with zero markers surviving on main. That base rate does
not justify a dedicated gate; it supports a generic mechanical-residue sweep if one already exists.

The economic response to a mechanically detectable defect is a cheap deterministic check before
review, not more broad-review sampling.

## Pinned configuration

| Pinned item | Value |
| --- | --- |
| Host | Claude Code 2.1.267, macOS (Darwin 25.5.0) |
| Controller model | `claude-opus-5` |
| Repair role | `implementer`, both arms, every case |
| Repair model | `sonnet`, from `.claude/agents/implementer.md` frontmatter, unmodified |
| Repair tools | `Read, Edit, Write, Grep, Glob, Bash`, agent-definition default, unmodified |
| Post-repair reviewer | `adversarial-reviewer`, model `opus`, tools `Read, Grep, Glob, Bash`, both arms |
| Adjudicator | `finding-adjudicator`, model `opus`, tools `Read, Grep`, both arms |
| Role revisions | `packs/core/.apm/agents/` at working-tree revision `d44484b29` |
| Policy revision | `packs/core/.apm/skills/work-loop/` at working-tree revision `d44484b29` |
| Contract revision | per case, digest-pinned above |
| Repository under repair | one disposable git worktree per arm per case, checked out at `P` |

## Arm definitions

**Baseline** is the repository's real current repair dispatch. The `implementer` subagent receives
the sustained finding set, the execution root, and references to the accepted contract, which is
what its own agent definition contracts for, and it runs the project's gates before returning —
again its own contract, not an experimental addition. Nothing is added and nothing is withheld.

**Candidate** is that identical baseline dispatch **plus** the compact closure packet the intent
defines: the complete adjudicated finding set and remedy predicates for the event, affected contract
and paths, touched-path repository obligations, unresolved owner-only decisions that must stop the
repair, and the smallest targeted verifiers required before return. The packet states explicitly
that it is additive evidence and not an exhaustive boundary — the repairer may inspect dependencies
outside it, and must stop on contradiction, missing authority, or an owner-only decision.

Packet preparation is **dispatched, not hand-written**, so its cost is provider-measured and counted
in the candidate arm from the moment preparation begins.

**Gates are not simulated.** The intent makes this an admissibility requirement: a case is
inadmissible if the experiment forbids, hand-simulates or silently skips a gate either arm's repair
warrants. Both arms run every applicable current gate in their own worktree. Any gate that cannot
run in a disposable worktree is recorded by name, with the reason, and its case is marked
inadmissible rather than quietly downgraded.

**Targeted verification.** Where an executable oracle exists, the targeted verifier must fail on the
frozen pre-repair revision `P` and pass on the arm's repair. Document and contract cases need a
deterministic before/after predicate instead. The verifier is recorded per case before the arms run.

**Both arms then receive the same broad post-repair review and adjudication**, and at most one
further repair-and-review cycle, stopping earlier on a terminal verdict.

**Arm order alternates across cases.** P1 and P3 run baseline first; P2 and P4 run candidate first.
Each arm runs in a separate clean agent context with no access to the other arm's work.

## Telemetry mechanism

Unchanged from the two prior spikes, whose instrument is reused: token counts are the inference
provider's own `usage` blocks summed across every API request in a call, read from the call's own
JSONL transcript; elapsed time is the span between the transcript's first and last record; long
inter-record gaps are split into human permission waits and model or queue stalls. The deciding
interval runs from arm preparation through terminal verdict or the two-cycle cap, with packet
construction, repair, gates, review, adjudication and further cycles recorded separately so
preparation cost cannot disappear.

Calls run strictly one at a time. The predecessor spike's wall-clock clause was destroyed by
self-inflicted concurrency, and the elapsed-time threshold cannot be measured any other way.

## Protocol corrections made during the run

Recorded because a protocol that changes mid-run must show what changed, when, and which way it
pushes.

**Nit handling, corrected after P1 and applied unchanged from P2 onward.** P1's cycle-2 briefs told
both arms the Nits "may be deferred, but if you defer one, record it with its citation". That
wording permitted repair, which the shipped policy does not: `work-loop/SKILL.md:551` defines the
clean state as one "carrying only deferred Nits recorded with their citations", so an unacted Nit is
*recorded as deferred*, not repaired. From P2 onward the brief states the policy exactly — Nits are
not to be repaired, and each is recorded as deferred with its citation in a durable location. P1's
looser wording is a defect in the experimental instrument, not in either arm, and both arms'
deviations from the shipped policy are scored as separate compliance defects rather than as credit
or blame for the mechanism.

**Gate equalisation, and what makes it admissible.** Where the closure packet instructed a narrower
gate set than the baseline ran, the omitted gates were run by the controller on the arm's own
revision. This restores gate completeness only under three conditions, all of which are checked and
recorded per case: every omitted gate ran on the **exact unchanged arm revision**, it ran **before
that cycle's terminal verdict**, and **its cost is included** in the arm's figures. A case where any
of the three fails is inadmissible under the intent's gate rule and is reported as such, not
silently downgraded.

**Contamination.** Elapsed time is reported per case with its stall share. A case whose arms exceed
the 10% stall ceiling cannot contribute to the elapsed-time median, and the intent's single
permitted quiet-host re-run is the only route back to admissibility.

**The packet is barred from selecting gates, from P2 onward.** In both P1 cycles the packet's
targeted-verifier section instructed the repairer to omit repository gates, which the intent's
guardrail forbids ("does not … replace applicable repository gates"). From P2 the packet-preparation
brief states the limit explicitly: naming the smallest verifiers that prove closure is the packet's
job, deciding which of the repository's required gates apply is not.

This correction is not neutral and is recorded as such. It removes a cost advantage the candidate
was buying by not running gates the baseline ran, so it is **adverse to the candidate**. It also
means P1's candidate arm and P2's do not run an identical mechanism: P1 measured the packet as it
first behaved, P2 onward measures the packet the intent actually proposes. Neither result is
discarded; both are reported with the mechanism they measured.

### Contamination: the P2 baseline arm was voided and re-run

The first P2 baseline arm **solved the case by copying the historical repair**, and said so in its
own report: "Applied the historical repair diff for case P2 to the execution root", and
"`python3 closure-predicate.py <root>` — 5/5 closure checks pass". Two distinct leaks, both defects
in this experiment's design rather than in the arm:

1. **Answer lookahead.** A disposable worktree shares the repository's object store, so the
   historical repair commit is reachable from inside it — `git cat-file -t 7c14fbac4` resolves. The
   packet-preparation brief forbade consulting it from the first case; the **arm repair briefs never
   did**.
2. **Instrument leakage.** The arm located and ran the closure predicate — this experiment's scorer —
   and optimised directly against it.

Confirmed mechanically rather than taken from the report: `git diff 7c14fbac4 HEAD` in that arm's
worktree is **empty**, i.e. byte-identical to the historical repair.

**The asymmetry favoured the baseline**, which is the direction that matters: the mechanism under
test was constrained against lookahead from the start while its control was not. It arose because
the anti-lookahead rule was written once, for the packet-preparation call, and never propagated.

**Disposition.** The arm is void. Its call is recorded as experiment overhead — 1,409,398 tokens,
392.9 s — and excluded from the baseline's figures. The worktree was destroyed and recreated at the
pre-repair revision, the scoring instruments were moved out of the directories the arms are pointed
at, and the brief now names the forbidden reads explicitly and requires an arm that finds itself
holding a ready-made answer to stop and report rather than apply it. Both arms carry the identical
constraint for every remaining case.

**Audit of the earlier arms.** Each arm's tree was diffed against its case's historical repair:

| Arm | Diff against the historical repair | Reading |
| --- | --- | --- |
| P2 baseline (first run) | empty — byte-identical | contaminated, voided |
| P2 candidate | 21 files, +494/−556 | independent |
| P1 baseline | 4 files, +28/−28 | independent |
| P1 candidate | 5 files, +45/−28 | independent |

P1's arms diverge from the historical repair, from each other, and produced different reviews, all
of which is consistent with independent work. That is **outcome evidence, not proof**: the leak path
existed for them too, and nothing outside their transcripts establishes what they read. P1 is
therefore recorded as *not shown to be contaminated* rather than *shown to be clean*.

### Instrument defect: I made the arms' cycle-2 briefs asymmetric, mid-case, after seeing a result

P2's candidate cycle-2 brief said to record deferred Nits "in a durable location". The candidate
then recorded them in `notes/verification-ledger.md` **at the repository root**, creating a new
top-level directory against `AGENTS.md:39`.

Having seen that, I wrote the baseline's cycle-2 brief differently: record them "in a location the
repository's own guidance sanctions for this kind of change; work out from that guidance where such
a record belongs and say in your report which rule you relied on." The baseline then chose
`workspace.toml [backlog].open` with a `docs/CONVENTIONS.md:484-488` citation, and created no
top-level directory.

**The difference in destination therefore measures my brief, not the mechanism**, and it is adverse
to the candidate: the control received a stronger prompt than the treatment on exactly the dimension
being compared, after the treatment had already failed on it. The destination outcome is excluded
from every arm-level comparison. What survives is the evidence about the **convention**, recorded
under [cross-cutting loop economics findings](#cross-cutting-loop-economics-findings), which is
where that finding belonged in the first place.

Recorded because it is the same class of error this spike spent the run catching in its arms, and
predeclaration exists to stop the controller committing it too.

### Instrument defects found and corrected during P2 preflight

All were caught by requiring each predicate to discriminate — fail at the pre-repair revision, pass
at the historical repair — rather than by reading it, and all were corrected before either arm ran.

- A check would have penalised an arm for **keeping a comment** that explains why a field is no
  longer read, because it grepped the whole function body rather than its code lines.
- A check was **scoped to the wrong function**: the reconciled legacy membership layer is assembled
  by the caller that supplies the residue predicate's record source, not inside the predicate.
- Two projection checks **hold at the pre-repair revision**, so they cannot evidence closure. They
  are reported as regression checks — they fail only if an arm edits the canonical pack copy without
  reprojecting it — and scored separately.
- One further check passes at the pre-repair revision and is marked non-discriminating and unscored,
  rather than deleted after the fact.

## Measures: resolve rate, reopened defects, escaped defects

Added during the run, at the owner's prompting, because the kill condition's repair-induced clause
is not the only thing the corpus can answer. All three were computed from the run evidence and are
reported here.

**Defect resolve rate** is the share of the dispatched finding set closed at terminal, measured with
the case's deterministic closure predicate. That instrument — not either adjudicator's grouping — is
the right denominator: the dispatched set is identical for both arms, while the adjudicators grouped
it differently (on P2, four items against five), so a rate taken from their groupings would measure
the grouping.

**Reopened defects** are dispatched findings closed in one cycle and open again at terminal. P1
shows this is not always zero, so it is tracked per case.

**Escaped defects cannot be attributed per arm on this corpus, and are not.** At P1 terminal, 10 of
12 sustained clusters were reached in one tree only — but most are *pre-existing*, which means they
are present in **both** trees and only one arm's reviewer found them. Counting those against an arm
would measure reviewer yield, not repair quality. The only per-arm-attributable escapes are the
repair-induced clusters, which is what the kill condition already counts.

| Measure | P1 baseline | P1 candidate |
| --- | --- | --- |
| Dispatched findings closed at terminal | **10/10** | **9/10** |
| Reopened at terminal | 0 | **1** |
| Repair-induced clusters (adjudicated) | 1 (Nit, human-approval) | 1 (Nit) |

The P1 reopening is instructive rather than sloppy. The dispatched finding asked that AC14 state
"the two fixtures it is read from". The candidate's first repair named the AC4 and AC7 fixtures,
satisfying that literally; a broad review then sustained a Blocker showing AC7's fixture requires the
citing entry to be `blocked` while AC14 asserts `ready`, so the two criteria could not both hold. Its
second repair narrowed AC14 to the AC4 fixture alone — resolving the contradiction and reopening the
dispatched finding as worded. The baseline resolved the same conflict without reopening, by keeping
two fixtures and scoping the second to AC8's terminal arm.

### Owner ruling, 2026-09-10 — the binding contract is the frozen adjudicated closure predicate

The owner settled which reading governs:

> The binding repair contract is the frozen, adjudicated closure predicate — not unstated reviewer
> intent, and not raw wording interpreted charitably afterward. If the wording omits a property,
> score against what was frozen and record an upstream finding-quality defect.

Applied here: **"the two fixtures it is read from" is present in the frozen finding text**, so the
candidate scores **9/10 with one reopened finding**, and the baseline 10/10.

**No upstream finding-quality defect is recorded**, because the frozen wording was satisfiable and
was in fact satisfied: the baseline kept two fixtures by scoping the second to AC8's *terminal* arm,
which avoids the contradiction the candidate hit with AC7. The candidate's cycle-1 error was
choosing an impossible pair; its cycle-2 error was narrowing rather than re-choosing. That is a
non-compliant simplification, not a defective contract, and the earlier framing of the two as
equally defensible was too generous to the candidate.

## Case P1 — result

### Cost over the deciding interval

The interval runs from arm preparation to terminal verdict at the two-cycle cap. The `blind` row is
the independent union adjudication and belongs to neither arm.

| Arm | Phase | Cycle | Tokens | Elapsed s | Stall s |
| --- | --- | --- | ---: | ---: | ---: |
| baseline | repair | 1 | 3,630,495 | 583.7 | 296.0 |
| baseline | broad review | 1 | 9,466,741 | 607.1 | 0.0 |
| baseline | adjudication | 1 | 3,926,099 | 388.6 | 173.0 |
| baseline | repair | 2 | 2,878,299 | 428.7 | 72.4 |
| baseline | broad review | 2 | 3,595,903 | 411.1 | 0.0 |
| candidate | packet preparation | 1 | 2,075,633 | 270.6 | 75.5 |
| candidate | repair | 1 | 3,119,287 | 409.6 | 67.4 |
| candidate | gate equalisation | 1 | 0 | 19.4 | 0.0 |
| candidate | broad review | 1 | 5,730,239 | 531.9 | 0.0 |
| candidate | adjudication | 1 | 2,383,081 | 311.7 | 76.8 |
| candidate | packet preparation | 2 | 1,902,051 | 255.5 | 90.4 |
| candidate | repair | 2 | 2,286,376 | 398.1 | 187.5 |
| candidate | gate equalisation | 2 | 0 | 27.1 | 0.0 |
| candidate | broad review | 2 | 6,558,341 | 560.9 | 0.0 |
| blind | union adjudication | — | 8,109,319 | 554.6 | 189.5 |

| Arm | Calls | Tokens | Elapsed s | Stall share |
| --- | ---: | ---: | ---: | ---: |
| baseline | 5 | 23,497,537 | 2,419.1 | 22.4% |
| candidate | 7 (+2 controller gate runs) | 24,055,008 | 2,784.8 | 17.9% |
| **Candidate change** | | **+2.37% (worse)** | **+15.12% (worse)** | |

The candidate led on tokens by 21.8% after cycle 1 and lost that lead in cycle 2, because its
terminal review cost 6,558,341 against the baseline's 3,595,903. It cost more because it found more,
including the case's only Blocker. Against the intent's 20% token bar, P1 misses in the wrong
direction.

**P1's elapsed time is contaminated and cannot enter the elapsed median.** Both arms exceed the 10%
stall ceiling — baseline 22.4%, candidate 17.9% — with only one agent running at a time, so this is
host or provider load rather than experiment design. Permission wait was 0 s throughout. Under the
intent's admissibility rule P1 contributes to the elapsed median only if its single permitted
quiet-host re-run is itself admissible. Tokens are unaffected by stall and stand as measured.

**Gate admissibility.** The packet instructed a narrower gate set than the baseline ran, in both
cycles. The omitted gates were run on the candidate's own revisions `583602fc6` and `9c0193ab5`,
before each cycle's terminal verdict, leaving zero tracked-file modifications and zero untracked
residue; all passed (`make lint-ruff` clean, `lint-spec-status.py` clean, 44 passed, 43 passed, then
70 passed with 12 subtests). Their 46.5 s is included above. P1 is therefore **admissible** under the
gate rule — but see the mechanism failure below, which is a separate matter from admissibility.

### Repair-induced defects, independently adjudicated

Fourteen findings across the two terminal reviews were blinded — reviewer identity, dispatch context
and the tree-to-dispatch mapping removed, identifiers renumbered, ordering hashed — and adjudicated
by a fresh `finding-adjudicator` that received both repaired trees **and the pre-repair tree**, and
ruled provenance itself rather than accepting either reviewer's attribution. A mechanical leak scan
returned one hit, verified a false positive ("AC3's engine arm").

Twelve defect clusters. **Repair-induced: one per arm.**

| Cluster | Severity | Class | Provenance | Trees |
| --- | --- | --- | --- | --- |
| `C2` queue membership never moves | Blocker | none | pre-existing | candidate only |
| `C1` T0's `canonical.ready` unreachable | Concern | none | pre-existing | both |
| `C3` receiptless need's target unpinned | Concern | none | pre-existing | both |
| `C4` Wave 7a-ii register undisposed | Concern | human-approval | pre-existing | candidate only |
| `C11` spec index row unowned | Concern | none | pre-existing | baseline only |
| `C10` deferred Nits unrecorded | Concern | none | indeterminate | baseline only |
| `C12` Ask-first record path ambiguous | Nit | human-approval | **repair-induced** | baseline only |
| `C6` cross-file symbol citation | Nit | none | **repair-induced** | candidate only |
| `C5`, `C7`, `C8`, `C9` | Nit | none | pre-existing | — |

**Control A is what makes this table honest.** Read from the reviewers' own attributions the arms
looked like 4 repair-induced defects against 1, a 75% reduction. The independent adjudicator, testing
each against the pre-repair tree, reclassified the baseline's AC14, index-row and T0 findings as
pre-existing defects the repair merely touched, and the candidate's Blocker as a pre-existing base
defect its reviewer happened to catch. The real figure is 1 against 1: **no reduction**.

The candidate's Blocker `C2` is retained as **reviewer-yield evidence, not repair-induced damage**:
no task moves this spec's `workspace.toml` membership out of `work.queue`, so the mandatory
`Status: Implementing` bump makes the engine emit `impossible_transition` against the real
`workspace.toml` and breaks a zero-ceiling roster ratchet that two tasks' own `Done-when` conditions
depend on. It is present at the base, and only one arm's reviewer found it.

The baseline produced **one** repair-induced cluster. The kill condition's repair clause fires when
"the baseline produces fewer than two and therefore demonstrates no material opportunity in the
corpus" — a corpus-level measure that cannot be decided on one case, but P1 contributes a case in
which the mechanism had almost nothing to improve.

### Compliance defects, scored separately from the mechanism

Both are deviations from shipped policy, and neither is evidence for or against the closure packet.

- **Candidate — scope expansion.** It repaired all three Nits. `work-loop/SKILL.md:551` admits a
  clean state carrying deferred Nits *recorded with their citations*; it does not authorise repairing
  them. The repair was neither explicitly authorised nor promoted to Concern. P1's brief wording
  permitted it, which is the instrument defect recorded above, but the deviation is still recorded
  against the arm.
- **Baseline — deferral not recorded.** It deferred two Nits with reasons in its status report and
  no durable record anywhere in the spec directory or the workspace. Because `plan.md` hash-pins at
  approve-plan, the deferral can no longer be recorded in the file that carries the defect. The
  independent adjudicator ruled this cluster `C10` INDETERMINATE, because the cycle-2 brief and prior
  adjudication record sit outside the three trees it was given.

### Mechanism failure: the packet narrowed the gate set, twice

In both cycles the closure packet's "smallest targeted verifiers" section instructed the repairer to
skip gates the baseline ran — cycle 1 "Deliberately excluded: `make test`, `make ci`,
`make build-self`, `tools/validate_guides.py`, `tools/test_build_site_routing.py`", cycle 2 "Not
worth running this cycle". Its stated reason is a real repository concept: a gate whose inputs did
not change would ratify intent rather than discharge a finding. The intent's guardrail is
nonetheless explicit that the packet "does not … replace applicable repository gates", and this is a
repeated behaviour of the mechanism rather than one repairer's judgement.

It hid no defect here — every omitted gate passed when run — but it means part of the candidate's
measured cost profile came from not running gates the baseline ran, and it is a reshape trigger
independent of the cost verdict.

### What the candidate did better, none of which the kill condition scores

It closed every dispatched finding by terminal, where the baseline left two open at cycle 1 and
introduced a repair that removed the index row's ownership rather than re-timing it. It handled the
one owner-only decision correctly, adding the missing `Done-when` completion clause for the
*Ask first* sign-off without granting the approval. And its cycle-2 packet independently re-measured
the Blocker's premise before writing a closure predicate for it, rather than taking the reviewer's
claim on trust.

## Case P2 — result

### Terminal state: both arms ship a red required gate

Verified by the controller through execution in both trees, before any adjudication:

| | baseline (W1) | candidate (W2) |
| --- | --- | --- |
| `catalogue self-host --root . --check` | **FAIL** — 2 drifts, both projected copies | ok |
| `tests/roster/test_cooling_scope_closure.py` | 46 passed | **1 failed, 45 passed** |
| brief-arm mutation (revert, re-run) | **15 passed — fix unprotected** | killing control present |

Each arm shipped a red gate, and **each arm's own chosen gate set missed its own failure**. The
baseline ran lint and pytest but not `self-host`; the candidate ran `build-self` and `self-host` but
not `tests/roster/`. On P2 the packet was explicitly barred from selecting gates and the repairer
still chose wrong, so gate selection by the repairer is unreliable in both arms.

### Blinded union and defect clusters

Fourteen terminal findings were blinded — reviewer identity, dispatch context and the
tree-to-dispatch mapping removed, identifiers renumbered, ordering hashed — with a mechanical scan
returning **zero identity leaks**. A fresh `finding-adjudicator` received both repaired trees and
the pre-repair tree, and ruled severity, protected class and provenance itself.

Thirteen clusters. Repair-induced, which is what the kill condition counts:

| Arm | Clusters | **Repair-induced** | Pre-existing | Indeterminate |
| --- | ---: | ---: | ---: | ---: |
| baseline | 5 | **4** | 1 | 0 |
| candidate | 8 | **6** | 1 | 1 |

### Survive/kill: the immediate-stop rule fired

The intent's Activity clause: *"Stop immediately on a candidate-only protected-class, Blocker, or
High defect."*

**Four candidate-only repair-induced clusters qualify on severity alone:**

| Cluster | Severity | Class | What it is |
| --- | --- | --- | --- |
| `C-W2-AC16-PROSE-BROKEN` | Blocker | public-contract | Rewrote prose a Shipped spec's AC16 roster test pins verbatim; gate red, criterion gone from the released pack |
| `C-W2-NOW-PAGE-OVERCLAIM` | High | public-contract | Published to `/now/` that an unreadable entry is "never silently eligible", which the code does not deliver |
| `C-W2-NEW-TOPLEVEL-DIR` | High | human-approval | Created `notes/` against `AGENTS.md:39` with no ADR or RFC |
| `C-W2-INVALID-VERDICT-RECORD` | High | human-approval | `review-verdict.v1` carries 2 of 12 required keys, so both Nit deferrals are refused — silent suppression |

Two further candidate-only repair-induced clusters — `C-W2-EVAL-HARNESS-NOT-UPDATED` and
`C-W2-EVAL-FIXTURE-REGRESSED` — are Concern severity but were **assigned `public-contract` by the
adjudicator**. Under the clause's protected-class limb they would also qualify; whether a
Concern-severity protected-class finding warrants an immediate stop is a reading left to the owner.
Reported as **4 qualifying / 6 total**, and the kill is decisive at 4.

**Repair-induced clause.** Baseline 4 → candidate 6: a **50% increase**, where the clause requires
at least a 50% reduction.

**Token clause: formally UNMEASURED.** It requires a median across the three non-high-risk cases and
only two cases executed. P1 and P2 are directional evidence only: candidate cost was worse in both,
by 2.37% on P1 and 43.7% on P2. This is not a second deciding clause and is not reported as one.

**Elapsed clause: UNMEASURED.** Both cases exceed the 10% stall ceiling on a host carrying
concurrent peer workloads at load average 13–14, with permission wait 0 s throughout and one agent
dispatched at a time. A sampled 1,312-second transcript gap occurred while unrelated tests and
agent work were active on the host, so elapsed time is not defensible as mechanism cost.

### Verdict: Killed on the immediate-stop safety clause

P3 and P4 were **not run**, and this is the frozen protocol rather than a truncation of it: the
Activity clause directs an immediate stop on a candidate-only protected-class, Blocker or High
defect, and four fired. The corpus therefore contains **no high-risk case**, which would matter for
a *survive* verdict and does not for a kill on an existence clause — the same logic that made V1's
one-case kill valid.

**What is killed: the closure packet as designed.** The mechanism failed in precisely the area it
was meant to improve. It supplied obligations and nonetheless induced public-contract and
human-approval violations, at higher cost, **across the two executed cases**. That is an
aggregate claim about P1 and P2 only; the unexecuted cases prevent a claim about the frozen corpus.

**What is not killed** is a much narrower future mechanism carrying only:

- the frozen adjudicated closure predicate;
- exact repair authority and non-goals;
- one killing control;
- no obligation bundle and no expanded repair surface.

Nothing measured here speaks against that shape. What the evidence indicts is the *bundle*: the
packet's breadth is what widened the repair surface, and the widened surface is where the
public-contract and approval violations occurred.

## Cross-cutting loop economics findings

These findings were collected during the validation but do not depend on either arm's verdict.
They are retained here because they identify cheaper follow-on work than another paired-agent
experiment.

- **Tool-result context dominates some calls.** Across four measured calls, re-read tool results
  accounted for 29.7–63.8% of total call tokens. An illustrative 2,000-character cap would have
  reduced 26.2M re-read tokens to 9.2M, a 64.9% reduction (17.0M tokens), while median tool-result
  size was only about 580–1,286 characters. The opportunity is in the long tail: default gates
  should return exit code, counts and duration, preserve warnings and errors, and expose full
  output on failure or explicit verbose mode. Whole-file reads need narrower selection rather than
  blind truncation. This four-call sample is directional, and much of the saving is cached input.
- **Workspace orientation emits unused bulk.** A measured `workspace_status.py status` response was
  about 54,752 tokens. `canonical.evaluations` contributed 51.5% even though its consuming skill did
  not name that field; `repo_backlog` contributed 28.5% while the skill consumed only three fields
  per entry. Any key-set narrowing remains Ask-first because output can be a public contract.
- **A clean spec-status run is noisy.** `lint-spec-status.py` exited 0 while emitting 184 lines and
  about 8,157 tokens: 183 warn-only warnings plus its success line. Those warnings represent real
  unresolved references, so the economic fix has two parts: make routine success concise, and
  separately register or resolve the debt rather than hide it. Static review also found scalable
  success narration in brief coverage, traceability, Mermaid rendering and publishing scripts;
  contractual result markers and failure diagnostics must remain.
- **The verification-ledger convention is root-ambiguous.** `docs/CONVENTIONS.md:129` routes
  execution evidence to `notes/verification-ledger.md` without naming the root. A spec-backed
  change naturally resolves that under `docs/specs/<feature>/`, while a light-mode change can read
  it as a forbidden repository-root directory. Two independent arms followed the ambiguous rule in
  separate cases. The owning convention should name the root and specify the no-spec destination.
- **Conflict markers are an example, not a dedicated gate.** The 0.35-second check would have found
  the sibling spike's three protected-class misses, but history showed one self-corrected incident
  across 5,001 commits and none on main. A generic mechanical-residue sweep may include the check;
  a standalone gate is not economically justified by this evidence.

### Method limitations

**The adjudicator was asked to do something its envelope forbids.** The terminal brief instructed
the blind adjudicator to run gates and mutations; `finding-adjudicator` holds only `Read` and
`Grep`. It reported the constraint plainly and settled 13 of 14 findings by reading, marking the
fourteenth INDETERMINATE for want of git ancestry it was also forbidden to consult. No result was
harmed — the controller had already executed both gate claims in both trees — but the brief was
wrong and the recovery was the agent's. **Future adjudicator briefs must supply already-executed
gate and ancestry evidence for evaluation, never instruct the read-only adjudicator to produce it.**

**Controller-introduced brief asymmetry**, recorded in full above: the cycle-2 deferral-destination
wording differed between arms, favouring the baseline, and that comparison is excluded.

**Contamination**: P2's first baseline arm copied the historical repair and was voided and re-run;
the audit of all four earlier arms is recorded above.

<!-- P3 and P4 were not run: the immediate-stop clause fired on P2. -->

## Evidence retention

Owner decision, 2026-09-10: retain this findings report only. Raw arm reports, repair packets,
closure predicates, blinded unions, adjudication records, measurements and helper scripts were
deliberately not retained in the repository. The report preserves the reported observations and
method corrections, but the arm-level calculations cannot be recomputed from repository artifacts
alone.
