# QA record — agent-skill-engineering languages and execution (INI-009 slice 2b)

Base for every measurement below: `74f9a4ac9`, taken against `origin/main` at
`74f9a4ac9`. Every figure here was produced by the invocation named beside it.

The blind retrieval measurement and the graded authoring run were taken before
the final rebase. They are carried forward rather than re-taken, because they
are bound by content digest and not by base commit: a `git diff` over
`packs/agent-skill-engineering/` across that pair of bases is empty, so the
artifacts they measured are byte-identical. The graded *review* results were not
carried forward and were re-taken; the reason is recorded under **Review
evidence re-taken** below.

Two Boundaries in this slice's spec require a basis to be recorded, and both
name this file. Where a row below says *authority*, that authority is the record
the Boundary demands — not a summary of one kept elsewhere.

## Foundation pin re-take — the record the amended Never-do requires

Two of the 24 inherited foundation retrieval pins moved when T3 admitted the
language topics. The spec's *Never do* originally forbade re-recording a pin at
all; it now admits a re-take on explicit owner authority recorded here with the
prior value, the measurement that moved it, which topic the movement added, and
why the new routing is more correct.

| Field | Value |
| --- | --- |
| Authorised by | the repository owner, in session, 2026-08-31 |
| Pins re-taken | 2 of 24 |
| Measurement that moved them | T7 blind retrieval, measured 2026-08-30 in a read-only subcontext given the compiled corpus and the prompts, with the six answer-bearing fixtures withheld |
| Detected by | the measurement itself, surfaced before any fixture was written |

**`python-extension`** — was `[resources-scripts-and-exit-contracts]`, now
`[resources-scripts-and-exit-contracts, python-and-pytest]`. The movement adds
the topic this slice admitted, and the case is literally about a Python
extension, so the pin as it stood named a routing the corpus now tells readers
is incomplete.

**`node-extension`** — was `[resources-scripts-and-exit-contracts]`, now
`[resources-scripts-and-exit-contracts,
typescript-node-and-javascript-test-runners]`. Same mechanism, same reason.

Neither pin lost a topic. Both gained exactly the leaf whose admission is this
slice's subject, which is what distinguishes a corpus becoming more correct from
a regression: a regression would have removed or redirected an existing routing.
The remaining 22 pins are unchanged and hold against the current measurement.

## Retrieval case disagreements — and why this record is one case's only home

Three of the 61 declared retrieval cases disagreed with the measurement. Those
three are exactly the arithmetic behind the recorded 0.951 precision: 3
unexpected topics returned, 0 missing, hence recall 1.000. Two are the moved
foundation pins recorded above; the third, `nm-ci-vs-lock`, is recorded in its
own subsection below and is **not** corrected.

A fourth declaration, `nm-python-vs-node`, also disagreed — before it was
corrected under the authority recorded immediately below. It is not among the
three because the corrected declaration now agrees with the measurement, which is
exactly why its prior value has to live in this record: nothing in the tree
carries it.

| Field | Value |
| --- | --- |
| Case | `nm-python-vs-node` |
| Prompt | "Both language suites configure parallelism differently; which rule is portable?" |
| Declared expectation | answers nothing — no topic returned |
| Measured result | `[python-and-pytest, typescript-node-and-javascript-test-runners]` |
| Ground | the measurement is judged the better reading |
| Authorised by | the repository owner, in session, 2026-08-31 |

The prompt names both ecosystems and both topics carry a parallelism clause, so
returning both is the defensible reading and the predeclaration was wrong.

**This record is the only place the original declaration exists.** The case was
authored and corrected inside one commit (`275d3a6f8`); it is absent at that
commit's parent, where the fixture held 40 cases against 61 now. A reader
checking whether the declaration was tuned cannot recover the prior value from
history, which is precisely the failure mode the amended Boundary names when it
says a basis living only in a commit message does not satisfy it. An adversarial
review raised this; the adjudication set it aside for want of a prior revision
to cite, which is the same fact seen from the other side.

### The third disagreement, recorded and left uncorrected

| Field | Value |
| --- | --- |
| Case | `nm-ci-vs-lock` |
| Prompt | "Jobs on one runner interfere with each other's temporary directories" |
| Declared expectation | `[worktrees-state-locks-and-shared-host-admission]` |
| Measured result | `[worktrees-state-locks-and-shared-host-admission, pack-and-ci-critical-paths]` |
| Disposition | **not corrected.** Recorded as measured. |

No owner authority was sought for this one, so the declaration stands as written
and the disagreement is carried instead. Whether the second topic belongs is
arguable — temporary-directory interference between jobs on one runner is
genuinely a shared-host admission subject, and the CI-critical-paths topic
reaches it through the runner — and that is the point: an arguable disagreement
is exactly the kind a session under time pressure would rather tune away.

An earlier version of this record said "one predeclared retrieval case
disagreed" and named only the corrected one. That sentence was false, and the
figure it sat beside — 0.951 precision, which is *three* unexpected topics over
61 cases — contradicted it in the same document. A reviewer recomputed the
arithmetic and found the missing case.

## Declaration corrections from a clarified contract

Two authoring-case declarations were corrected on the second, narrower ground
the amended Boundary admits: the predeclaration was falsified by a *corrected
shipped contract* rather than by the measurement.

| Field | Value |
| --- | --- |
| Authorised by | the repository owner, in session, 2026-08-31 — the same direction that authorised the two contract fixes below, since these corrections follow from them |
| Ground | the predeclaration was falsified by a corrected shipped contract, not by the measurement |

Required markers. Both cases declared `Write status: awaiting explicit
authorization`; only `update-existing-skill`'s changed, so the other's row shows
it unchanged rather than omitting it:

| Case | Prompt | Declared | Corrected to | Measured |
| --- | --- | --- | --- | --- |
| `update-existing-skill` | "Update the supplied migration review skill without widening its activation boundary. First inventory the current contract, then describe the exact patch and verification; do not write until explicitly authorized." | `Mode: update`, `Write status: awaiting explicit authorization` | `Mode: frame`, `Write status: not authorized` | `Mode: frame`, `Write status: not authorized` |
| `cross-session-resumption` | "Update this skill so a second session can resume its work without re-reading everything. The skill root is evals/files/update-existing-SKILL.md." | `Mode: update`, `Write status: awaiting explicit authorization` | `Mode: frame`, `Write status: awaiting explicit authorization` (unchanged) | `Mode: frame`, `Write status: awaiting explicit authorization` |

Assertion texts. The Boundary names "assertion" as well as "criterion" and
"retrieval case", so these belong in this table and not in prose:

| Case, index | Declared | Corrected to | Measured |
| --- | --- | --- | --- |
| `update-existing-skill`, 2 | "Proposes an exact minimal diff rather than replacing the skill" | "Names the candidate changes and the authority each would need rather than inferring one, since the request leaves the change unspecified" | `true` |
| `cross-session-resumption`, 0 | "Enters update mode against the named existing skill root" | "Names update as the mode the work will need, against the named existing skill root, without entering it before authorization" | `true` |

**The contract change all four follow from** is the clause Fix 1 *added*, at
`SKILL.md` lines 18-24: "Identifying which mode the work will need is not
entering it … Until that transition the receipt reports `Mode: frame`, however
far the plan has progressed."

Naming the unchanged Modes preamble here would not discharge this burden, and an
adversarial review caught an earlier version of this record doing exactly that.
The preamble — enter `create` or `update` "immediately before the first write" —
is byte-identical on `origin/main`, and it is one of the *two* readings the
pre-fix contract supported: it is the reading that produced `Mode: frame`, while
the description's "identify the target and mode first" produced `Mode: update`.
An unchanged sentence that supports both readings cannot be what falsified a
declaration. The added clause is what removes the second reading, and removing it
is what makes `Mode: frame` the only correct receipt for a case that forbids
writing.

The reasoning then runs contract → declaration and reaches the same answer with
no measurement in hand, which is the burden that ground carries. That the
correction agrees with what was observed is evidence the contract fix was the
right repair, not the reason for the correction.

**The same session caught itself failing this test once.** Alongside one
assertion it also softened the case *prompt* to admit the path the response had
taken. That is rewording a case to match a measured result — the act the
Boundary forbids outright, with no authorised ground. The prompt was restored.
Its demand for an exact patch is a good adversarial input precisely because the
corrected contract now requires refusing it.

## Known-miss exemption — authority recorded

| Field | Value |
| --- | --- |
| Exemption | `("progressive-result-presentation", 2)` |
| Authorised by | the repository owner, in session, 2026-08-31 |
| Measured | 2026-08-31, graded authoring run, iteration 3 |
| What was measured | the response stated the universal rule — exactly one next action — then paired it with two of the four states it had named, giving the other two a reporting rule rather than a next action |
| Why exempted rather than fixed | nothing in the skill's contract governs how exhaustively a framing response enumerates states, so unlike the two contract gaps this slice fixed there is no wording defect behind it. Inventing a rule about enumeration exhaustiveness to turn one assertion green would widen the shipped contract to serve the fixture |
| Why not reworded | the assertion is well posed and the response did not meet it |

The exemption was added in T8 *before* this authority was obtained, contrary to
the spec's *Ask first* routing and the plan's explicit prohibition. That gap was
found at the ship gate by re-reading the plan against what had been committed,
and the authority above was then sought rather than assumed. The exemption names
an exact `(case, index)`, so a different miss in the same case still reddens the
suite.

## The scope change, and what verifies it

Two defects in a *shipped* skill's contract were fixed during this slice,
outside the spec's original boundary. Both were found by measurement rather than
by reading, and neither is a corpus defect.

| Field | Value |
| --- | --- |
| Authorised by | the repository owner, in session, 2026-08-31 — the second on the owner's direct question, "isn't this an activation bug in the skill to be fixed?" |
| File changed | `packs/agent-skill-engineering/.apm/skills/author-or-update-agent-skill/SKILL.md` |
| Where | the body only, never the activation-bearing `description`, so trigger discrimination is not perturbed |
| Re-measured after | activation re-observed headless at 18/18 with zero exclusivity violations, iteration 3; the graded authoring run re-taken blind, iteration 3 |

**Fix 1 — identifying a mode is not entering it.** The Modes section now states
that the receipt reports `Mode: frame` until the write transition, "however far
the plan has progressed — a fully specified patch that has not been authorized
is still framing."

The evidence was two independent executions against the *same* pre-fix wording
returning opposite receipt modes for the same two read-only cases:

| Case | First pre-fix run | Second pre-fix run |
| --- | --- | --- |
| `update-existing-skill` | `Mode: frame` | `Mode: update` |
| `cross-session-resumption` | `Mode: frame` | `Mode: update` |

Neither reading was careless. The first stayed in `frame` because the preamble
enters `update` immediately before the first write and both cases forbid
writing; the second entered `update` because the description makes identifying
the target and mode the workflow's first step. The contract supported both,
which is what an ambiguity is — and two runs disagreeing is stronger evidence
for it than any amount of re-reading the text. Neither run survives in the
committed record, so the values are recorded here.

**Fix 2 — a resolved target is not a resolved request.** The skill dispositioned
a missing mode and a missing target and said nothing about a *resolved target
whose requested change is unspecified*. A response extended the stated rule to
the unstated case faithfully, which is why it graded as a miss: the behavior was
right and the contract was silent. The skill now says to remain in `frame`, name
the candidate changes and the authority each would need, and not to infer a
change from the target's current shape.

An exemption request for that assertion was withdrawn rather than granted, since
the assertion follows from the corrected contract.

**What would fail if either fix were reverted.** Nothing did, when this was
first written. The two fixes were held only by eval assertions authored in the
same change as the behavior they assert — a mirror, not a contract — and an
adversarial review sustained exactly that. A guard was added at the ship gate:
`test_shipped_body_keeps_the_two_clauses_measurement_forced` in
`packs/agent-skill-engineering/tests/skills/author_or_update/test_contract.py`,
matching on collapsed whitespace so a re-wrap of hard-wrapped prose does not read
as a reverted clause.

Seven review rounds each defeated this guard a different way, and five of them
produced a change to the predicate over the body; the seventh defeat was in the
guard's own subject set rather than in the clauses it reads. Round 3's fix changed the predicate's **category**
rather than its pattern. Round 6's fix changed nothing about the predicate: it
wrote the boundary down instead, because the proposed closure turned out to be
another incomplete enumeration.

Rounds are numbered throughout; there is no separate change numbering, because
using both is how an earlier version of this paragraph made two ordinals
disagree.

| Round | Guard | How it was defeated |
| --- | --- | --- |
| 1 | eval assertions only | authored in the same change as the behavior they assert — a mirror, not a contract |
| 2 | five `substring in body` checks | one asserted a truncated prefix, `"…resolved but the"`, stopping before `*requested change* is not`; swapping that subject removed the disposition and stayed green |
| 3 | six `substring in body` checks | `Remain in \`frame\`` was pinned by nothing; flipping it to `Enter \`update\`` inverted the contract and stayed green |
| 4 | one digest per clause paragraph | the digest answered "some paragraph somewhere collapses to this hash", not "this clause is in force" — so the normative paragraph could be replaced with an advisory sentence and the original re-appended verbatim under a `## Superseded guidance (not normative)` heading, or a reversed duplicate added below the original where first-match never reached it |
| 5 | three conjuncts: match count, heading text, digest | the heading conjunct pinned the heading's *text* and never how many headings carried it, so gutting the clause in place and re-appending it verbatim under a **second `## Modes`** satisfied all three |
| 6 | four conjuncts: heading uniqueness, match count, heading text, digest | `- ## Superseded guidance` as a container-block heading, with the clause as indented list continuation — no line pattern matches it, a renderer shows the clause under the new h2, and the collapsed digest is unchanged. **Documented as uncovered rather than closed**, since closing it needs a CommonMark parse |
| 7 | the guard itself | the subject set `MEASUREMENT_FORCED_CLAUSES` was unpinned, so deleting an entry — or emptying the dict — left both guards green while asserting nothing. Closed by pinning the set. The first fix put that pin *inside* one consumer, which left the sibling still vacuous on an emptied dict; found by checking my own fix rather than by review, and the pin is now its own test |

Rounds 2 and 3 were the same mistake twice. The adjudication named why adding a
seventh assertion could not work: positive substring containment is **monotone
under insertion**, so no finite set of `substring in body` checks catches a
paragraph that keeps every pinned sentence and appends one reversing them. That
is a property of the predicate class, not a gap in the enumeration.

Round 4 was a different mistake — the new predicate was too *local*. A digest
identifies text; it says nothing about whether that text is the operative clause.

The guard now asserts **four conjuncts per clause**: the pinned heading occurs
exactly once in the body, exactly one paragraph carries the anchor, that
paragraph sits under the pinned heading, and its whitespace-collapsed text hashes
to the recorded digest. Re-wrapping the same words changes none of them.

The uniqueness conjunct exists because round 4's relocation probe varied the
heading's *text* and never varied how many headings carried it. Gutting the
clause where it is normative and re-appending it verbatim under a second
`## Modes` satisfies a heading-text pin exactly.

Twelve probes, each restored by rewriting the file rather than by checkout,
body verified byte-identical afterwards — eleven redden, and the twelfth is the
legitimate re-wrap that must not:

| Probe | Guard | Closed by |
| --- | --- | --- |
| `Remain in \`frame\`` → `Enter \`update\`` | red | digest |
| advisory sentence appended after the prohibition | red | digest |
| Fix 1 demoted to "an earlier draft said this. It is withdrawn." | red | digest |
| `*requested change*` → `*platform*` | red | digest |
| `however far the plan has progressed` → `as appropriate` | red | digest |
| `Do not infer a change` → `You may infer a change` | red | digest |
| authority-cost clause reworded | red | digest — unpinned until the paragraph became the unit |
| clause gutted in place, original re-appended under `## Superseded guidance (not normative)` | red | heading text |
| clause gutted in place, original re-appended under a second `## Modes` | red | **heading uniqueness** |
| reversed duplicate added below the original | red | match count |
| clause demoted to a blockquote | red | digest — markup counts |
| the same words re-wrapped across lines | **green** | a legitimate reflow must not fire |

### Which subject sets need pinning, and why only one did

Round 7's defeat was a *subject set*, not a predicate, so the lesson generalizes
past this guard. Every subject set the slice's guards use was emptied and its
suite re-run:

| Subject set | Emptied | Used as |
| --- | --- | --- |
| `MEASUREMENT_FORCED_CLAUSES` | **was vacuous**, now pinned | drives iteration |
| `AUTHORING_EVAL_IDS` | fails closed | filter inside a positive assertion |
| `KNOWN_REVIEW_MISSES` | fails closed | filter inside a positive assertion |
| `LANGUAGE_SPECIFIC_TOPICS` | fails closed | filter inside a positive assertion |
| `DOCTRINE_CLASSES` | fails closed | filter inside a positive assertion |
| `AUTHOR_EVIDENCE_SOURCES`, `REVIEW_EVAL_FILES` | fail closed | parametrized, and set-equality asserted |
| `REVIEW_EVAL_IDS` | fails closed | set-equality asserted |

The rule the measurement gives: **a set that drives iteration needs its own pin; a
set used as a filter inside an assertion that demands a positive result already
fails closed.** Emptying a filter empties the result and the assertion notices.
Emptying an iteration driver empties the loop and nothing notices, because a loop
that runs zero times raises nothing.

Only one set in this slice drove iteration, which is why only one was vacuous.
That is a cheaper check than reasoning about each guard: ask what the set is *for*
before asking whether it is pinned.

### What the guard does not cover, enumerated

Seven rounds produced seven defeats, five of which changed the predicate, so the
useful thing to record is not another conjunct but where the boundary now sits.
The five rows below all satisfy every conjunct and were verified green:

| Uncovered | Why |
| --- | --- |
| clause fenced in a ```` ```text ```` block | the guard reads the raw file, not the rendered document |
| clause wrapped in an HTML comment | same — its bytes survive while a reader never sees it |
| clause indented four spaces into a code block | same, and this is the one a span stripper misses, since collapsing whitespace discards leading indentation |
| clause relocated under a heading the line pattern does not recognize — a setext underline, a 1–3-space-indented ATX heading, a raw `<h2>`, or an ATX heading inside a container block such as `- ## Superseded guidance` | same class: the tracked nearest heading stays the pinned one while a renderer shows the clause under the new h2 |
| a contradicting paragraph appended under the same heading | a claim about meaning, not about form |

The first four are one class: **the predicate reads raw lines, not the rendered
document.** Two enumerations were proposed to close parts of it and both were
rejected on adjudication, for the same reason each time.

A fence-and-comment span stripper was already incomplete when proposed: the
four-space-indent case defeats it, because collapsing whitespace discards leading
indentation.

A heading-form check over setext, indented ATX and raw HTML looked different — I
argued heading syntax is a closed set, so the check would be complete, and
validated it against those three forms. The counterexample is
`- ## Superseded guidance` with the clause as indented list continuation: no line
pattern matches it, no `<h[1-6]>` scan sees it, it renders as an h2, and the
collapsed digest is unchanged. Heading *syntax* is closed; "the nearest heading
preceding this paragraph in the rendered document" is not, because container
blocks compose with heading syntax. Verified — all four conjuncts and the proposed
well-formedness check both pass on it.

That is the same mistake twice at two levels: enumerating sentences, then
enumerating the syntactic forms in which a sentence can be hidden or displaced.
Both times I validated the enumeration against the cases I had thought of, and
both times the counterexample was a case I had not.
Making the predicate categorical needs a real CommonMark parse: a new dependency
to defend two prose sentences, which the repository's cut-before-adding ladder
routes through a decision record rather than a test file.

The last is a different kind and is not closable by any predicate over prose.
Whether a later sentence contradicts an earlier one is judgment, and it stays
with review. Naming it here is the point: **the guard owns form, review owns
meaning**, and five rounds of trying to make one predicate own both is what
produced five defeats.

A second test asserts the two anchors resolve to *different* paragraphs, and it
owns a catching set none of the four conjuncts reach. An earlier version of this
record justified it wrongly — claiming a merged paragraph would leave both digests
matching, which is impossible, since one paragraph cannot hash to two different
recorded values. The real case is a merge **combined with refreshing both recorded
digests to the merged value**: then each anchor has exactly one match, both sit
under the shared `## Modes` heading, and both digests are as recorded, so every
conjunct passes and only distinctness notices that two names now resolve to one
paragraph. Verified: conjuncts green, distinctness red. `assert all(...)` in that
test is load-bearing for the same reason — one missing region and one present
region give a two-element set that satisfies the length comparison vacuously.

I had intended to delete that test as dominated. The adjudication refused the
change and was right; the reviewer's proposed replacement would have deleted the
catching set too. Both clauses sharing a heading is exactly what makes it
non-redundant.

The whole-file `SKILL.md` digest now recorded on every graded result covers any
other body change and forces re-measurement rather than a digest refresh — but it
is refreshed by that same legitimate flow, which is why the clause guard exists
as a second, narrower control rather than as a duplicate of it.

**Cost paid rather than avoided.** Two body edits moved the skill digest twice,
so both the captured responses and the activation observation were discarded and
re-taken each time. Three activation runs and three blind authoring executions
were spent to ship two contract fixes and one honest grading sheet.

**The general lesson.** A measured miss has two possible causes — the response
did the wrong thing, or the contract never said what the right thing was — and
only reading the contract distinguishes them. Recording the first miss without
checking would have shipped a skill defect as a permanent eval exemption, with
the exemption itself standing as evidence that nothing was wrong.

## Review evidence re-taken

The two graded review results were **not** carried forward from slice 2a. T4
edited the review workflow's body — replacing the unpopulated-families sentence
and adding "treat a language claim carried outside its stated ecosystem as a
finding" — after those results were recorded. Under *Always do*, recorded
evidence whose covered content changed is re-measured.

The staleness was invisible to every guard, and that is the more useful finding:
`behavior-results.json` pinned `evals/evals.json` and the eval payloads, never
the workflow body. A result graded against a superseded body satisfied every
digest check in the suite. AC5 conditions re-measurement on a pinned digest
moving, and the body was not pinned, so the condition could not fire.

Both halves are now closed:

- Every authoring result pins `SKILL.md`, and every review result pins the
  review body. Editing either body reddens that side's digest test; dropping the
  key reddens the coverage test. Both proven by mutation and restored by editing
  rather than by checkout.
- `AUTHORING_EVAL_IDS` widens from four ids to all eight. All eight authoring
  results record an `evals/evals.json` digest, so a set naming four left four
  free to carry a stale one that the parametrized sweep never read. Proven with
  a forged digest on `progressive-result-presentation`, a result the old narrow
  set did not cover.

The re-take was executed in one read-only subcontext and graded in a separate
one, with the expected identifiers and assertions withheld from the executing
context. It reproduces the recorded verdicts: **10 of 11 assertions
true and 12 of 12 declared markers present**, recorded as `review_iteration` 6.
The eleventh is the recorded miss `("detect-script-contract-failure", 5)`, which
stays `false` and stays exempted. No recorded verdict changed, so the re-take
confirms the evidence rather than replacing it — but it is now bound to the body
that produced it, which is the part that was missing.

An earlier version of this record said "10 of 10", which was wrong twice: the two
cases declare 5 and 6 assertions, so 11 were graded, and the headline erased the
one recorded miss. It read as a clean sweep. A reviewer recounted the fixture.

**The two graders disagree on that eleventh assertion, and the disagreement is
kept rather than resolved.** The committed fixture records it `false`. The
grading context for this re-take reached `true`, explicitly "on the naming",
while flagging the same assertion as having no observable in a review-mode
response — review never reaches optimization, so nothing in the output can
falsify the ordering the assertion asserts. The recorded `false` therefore stands
and the exemption stands with it.

Adopting the friendlier verdict because a second grader offered it is the act the
Boundaries forbid, and it would have been unusually easy to justify here: the
newer measurement is the one bound to the current body. But the assertion's own
ill-posedness is *why* two careful graders diverge, so the divergence is evidence
about the assertion, not about the response. Recording it is worth more than
either verdict.

The grading context flagged three assertions as ill-posed. They are recorded, not
reworded, because rewording an assertion after seeing its result is exactly what
the Boundaries forbid and no authorised ground applies:

- Assertion 0 in **both** cases — read-only and no-execution are checkable only
  against the response's own attestation. No artifact in the graded set can
  contradict it, so a dishonest response scores identically. Unfalsifiable from
  the response alone.
- Assertion 5 in `detect-script-contract-failure` — the clause "before
  optimization" has no observable in a review-mode response, since review never
  reaches optimization. It also bundles replay, exit, and cleanup without saying
  whether they must appear in the prescribed remedy or merely be named as
  absent; the response satisfies the latter, and for cleanup only the latter.
- Assertion 4 in `detect-activation-failure` — "least-authority portable
  behavior" names no identifier and no threshold, so it grades on remedy
  vocabulary rather than substance.

## An answer key inside the artifact under review — third independent observation

Both review candidates open with an `INERT REVIEW FIXTURE` comment naming some
of the seeded identifiers. Slice 2a recorded this as a known weakness of the
fixture design and deliberately did not repair it: the header is what stops an
agent treating a deliberately defective fixture as instructions, so removing it
would trade a measurement risk for a safety one.

The re-taking context rediscovered it independently, without having read 2a's
record, and reported it unprompted as a caveat on its own result. The grading
context then verified the leak directly and found it **wider than either earlier
record states**: the identifiers are named in three files for the second case,
not one.

| Case | Files leaking | Identifiers leaked | Required markers that are blind |
| --- | --- | --- | --- |
| `detect-activation-failure` | `catchall-SKILL.md` | `ASE-ACT-01`, `ASE-AUTH-01`, `ASE-SEC-01` | 1 of 4 — only `ASE-PORT-01` |
| `detect-script-contract-failure` | `nondeterministic-SKILL.md`, `nondeterministic-reference.md`, and an inline comment in `nondeterministic-helper.py` | `ASE-DET-01`, `ASE-CTX-01`, `ASE-CONC-01`, `ASE-PROG-01` | 2 of 6 — `ASE-WRITE-01` and `ASE-FAIL-01` |

Stated plainly: **most of the identifier recall these two cases measure is not
blind.** The part that is blind is the part beyond the key — three confirmed
defects in the first case and five in the second that no comment names, plus four
identifiers dispositioned in the first case as applicable-without-defect or
not-applicable with reasons. Those judgments are the stronger signal in both
cases, and the recall of leaked identifiers should not be read as evidence of
detection at all.

2a's disposition stands — removing the header would trade a measurement risk for
a safety one — but the earlier record understated the cost, and the honest
summary is that these two cases measure checklist application and disposition
quality, not identifier discovery. Narrowing the leak without losing the inert
marker is left to the owning slice rather than taken here.

## Skill-contract ambiguities observed during execution

Surfaced by executing contexts, unresolved and not blocking:

- **The mode line is a template, not a literal.** The review skill says to open
  the result with a line "exactly" and then shows `Mode: review | optimize`.
  Emitted exactly, it prints both modes. The executing context read `|` as
  alternation. The declared `expect.output_contains` agrees with that reading,
  so no measurement depends on the ambiguity, but the instruction and its
  example contradict each other.
- **A bare `*-SKILL.md` file as a skill root** still has no stated disposition.
  An executing context hit it and worked around it visibly. It bears on no
  declared marker, so fixing it here would be scope taken without a reason.
- **Confinement discipline routes through a sibling pack's reference.** The
  review skill sends the reader to
  `author-or-update-agent-skill/references/safety-and-authority.md` for
  resolve-before-read; a reader treating step 1's link as optional would skip
  it.

## Failure attribution

The *Always do* Boundary requires every failure this slice's gate chain observed
to carry the invocation that reproduces it, the base it was seen on, an
attribution, and who attributed it. Nothing observed is dropped.

| Failure | Reproducing invocation | Attribution | Attributor |
| --- | --- | --- | --- |
| `test_guide_typed_asides.py::test_ledger_has_complete_terminal_classifications` and `::test_ledger_matches_converted_asides_and_unchanged_quotations` | `python3 -m pytest tools/test_guide_typed_asides.py -q` → 2 failed, 2 passed | `owned-elsewhere`. Reproduces on `origin/main` independently of this branch: the owning spec declares 165 parser-visible blockquote blocks while its ledger carries 175 rows, and neither file is touched by this branch. Routed against the existing `[backlog].open` entry `guide-blockquote-ledger-has-no-regenerator`, whose subject is the same ungated ledger. | Claude, this session |
| `test_build_site_routing.py::test_the_committed_now_projection_matches_the_changelog_source` | `python3 -m pytest tools/test_build_site_routing.py -q` → 93 passed, 1 skipped | `caused-here`, **fixed**. Adding the release entry restaled the committed `/now/` projection, which the marketing build reads. Regenerated with `python3 tools/build-site.py --journeys-only`, the command the failure message names. Re-running it a second time changes nothing, so the committed bytes are what the command produces. | Claude, this session |
| Ruff `I001` on an unsorted import block in the T2 test module | `make lint-ruff` → `All checks passed!` | `caused-here`, **fixed**. Caught locally this time; the identical defect reached CI in slice 2a because `make lint-ruff` was in the documented command set but not in the per-edit loop. | Claude, this session |
| Two blind authoring executions wrote to one output directory concurrently; four files were overwritten mid-run and five were removed under a live writer | Both runs pointed at one `responses/` path; the second was dispatched while the first was working, and the supervisor then moved the first run's files aside while the second was writing | `caused-here`, **contained**. Not a worker defect. The supervisor reused one output path for a discarded run and its replacement, then mutated that directory under an active writer. The executing context detected the interference, restored its own text, re-verified, and reported the collision unprompted — the only reason the evidence survived. Later runs write to a path unique per run, so provenance is structural rather than inferred. | Claude, this session |
| A grading sheet reported two false marker mismatches | regenerated from the current declarations → mismatches resolved | `caused-here`, **fixed**. The sheet was built before the declarations were corrected, so it compared against declarations that no longer existed. Derived artifacts must be rebuilt after their source changes — the same propagation defect that dominated four of this slice's spec-amendment review rounds — a different sequence from the guard rounds above — appearing in evidence tooling rather than in prose. | Claude, this session |
| Three subagents and one Codex worker returned no verdict | re-dispatched; each replacement completed | `environmental`, **not carried**. Three were killed by the host sleeping mid-response (`API Error: Your computer went to sleep`); one Codex run was load-shed with the 1-minute load average at 184.76. A run that reached no verdict is not a measurement, so each was discarded and re-taken rather than recorded as partial. Re-dispatch after a host kill is recovery, not an additional attempt. | Claude, this session |
| Codex worker T3 first run produced zero changes | re-dispatched with the discharge stated at the top of the brief → task completed | `caused-here`, **fixed**. A briefing gap, not a worker defect: the worker's own workflow requires a base-freshness check, and the brief never said that check was already discharged or that its refusal is not a stop condition. | Claude, this session |

## Gates

| Gate | Invocation | Result |
| --- | --- | --- |
| Pack suite | `python3 -m pytest packs/agent-skill-engineering/tests -q` | 143 passed |
| Repository suites | `python3 -m pytest tests/ -q` | 1040 passed, 6 skipped |
| Tooling suite | `python3 -m pytest tools/ -q` | 1207 passed, 2 skipped, 85 subtests; 2 failures attributed `owned-elsewhere` above |
| Packaging suite | `python3 -m pytest packages/agentbundle/tests -q` | see below |
| Lint | `make lint-ruff` | All checks passed |
| Pack-test boundary | `python3 tools/lint-pack-test-boundary.py` | passed, 8 cases; 63 destinations, 8 declared unrun |
| Spec metadata | `lint-spec-status.py --root .` | spec metadata clean |
| Brief coverage | `lint-brief-coverage.py --root .` | 3 briefs checked |
| Plugin roster and membership | `lint-plugin-roster.py`, `lint-plugin-membership.py` | ok — 15 published, 7 withheld; ok |

### Measured evidence

| Measurement | Figure | Floor |
| --- | --- | --- |
| Retrieval precision | 0.951 | 0.90 |
| Retrieval recall | 1.000 | 0.90 |
| Exact selection | 0.951 | 0.90 |
| Declared retrieval cases | 61 | — |
| Inherited foundation pins holding | 24 of 24, 2 re-taken under recorded authority | 24 |
| Generic-engineering negatives answered | 0 of 40 | at most 2 |
| Activation | 18 of 18, zero exclusivity violations, iteration 3 | 18 |
| Graded authoring assertions | 30 of 32 true, 2 exempted and recorded | — |

### What this record does not attest

Fidelity is `observed+attested`, tier B-lite, provenance operator-attested. The
graded runs are real executions in read-only subcontexts, not harness-driven
runs against a production model endpoint. Recall of the identifiers named in the
review fixtures' own headers is not blind, for the reason recorded above.
