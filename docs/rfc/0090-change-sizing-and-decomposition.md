# RFC-0090: Change sizing and decomposition

- **Status:** Accepted
- **Author:** eugenelim
- **Approver:** eugenelim
- **Date opened:** 2026-08-19
- **Date closed:** 2026-08-19
- **Decision weight:** heavy (modifies a top-level convention that ships to
  adopters via the core seed, and changes published agent behavior; requires a
  de-risk spike and explicit Approver sign-off)
- **Related:** commit `92edf24827866aee44db53b88d432aac6d02589a`;
  `packs/core/seeds/docs/CONVENTIONS.md`;
  `packs/core/.apm/skills/work-loop/SKILL.md`;
  `0090-notes/evidence.md`

## Reviewer brief

| Item | Summary |
| --- | --- |
| Decision | Size only the heavy tail by review shape and widen safe ride-alongs by verifiability; do not shrink the healthy median review unit. |
| Recommended outcome | Use a 2,000-reviewable-line tail-triage trigger, route wide work to reproducibility proof and mixed or deep work to dependency-ordered layers, and replace locality-only bundled fixes with three verifiable tiers. |
| Change if accepted | Edit the canonical core seed and regenerate its projection; operationalize the seed, work-loop, and new-spec; release core 2.9.2. |
| Affected surface | Core pack (the adopter-distributed bundle) conventions seed (adopter-facing source), self-host projection (generated repository copy), and work-loop skill (implementation workflow). |
| Stakes | The convention ships to adopters and governs how agents turn objectives into commits, PRs, and stacks. |
| Review focus | Test shape classification, reproducibility and inertness proof, the single-artifact floor, and seed clarity for every PR. |
| Not in scope | A global diff-size gate, new scripts or manifest fields, frozen-spec rewrites, reducing the median review unit, or a universal LOC-risk formula. |

## The ask

Approve the linked decisions below. A review unit cannot be sized sensibly
without saying how a larger objective is divided.

| ID | Question | Recommendation | Why | Decide by | Reviewer action |
| --- | --- | --- | --- | --- | --- |
| D1 | What is the review unit? | One spec may deliver one or more PRs; each is a semantic commit (one independently testable concept) or stack layer (one PR in a dependent sequence). | A spec is an objective, not a mandated review boundary. | RFC acceptance | Approve or amend the decomposition unit. |
| D2 | What numeric policy applies? | Use 2,000 reviewable behavior and test lines as a tail-triage trigger only; it requires classification and proof, never automatically a split. | The 152-line median already beats the cited guidance. In the 234-PR corpus, a generic 100-line split affects 62% of PRs: a rule that fragments most work is the exact written-but-nonbinding failure this RFC diagnoses. | RFC acceptance | Approve the trigger and its non-risk framing. |
| D3 | How is the tail handled? | Route WIDE work to reproducibility proof without splitting; decompose MIXED and DEEP work into dependency-ordered, independently reviewable layers that leave the repository working. | Splitting a mechanically uniform sweep multiplies PRs without making any of them reviewable; it helps concentrated authoring. | RFC acceptance | Approve shape routing and proof. |
| D4 | How does it ship? | Change the core seed (the adopter-facing source), regenerate the self-host projection (the generated repository copy), and release core 2.9.2. | The seed is source; the repository copy is generated output. | Follow-on | Confirm release and compatibility path. |
| D5 | Where is work first sized? | Keep `new-spec`'s qualitative one-PR-sized task rule; a task predicted above the trigger must split or declare its review shape in the plan. | Coarse tasks cannot be repaired cheaply at PR time, but a generic line cap would shrink healthy work. | RFC acceptance | Approve the operational backstop. |
| D6 | Which ride-alongs are allowed? | Replace locality-only allowance with reproducible, provably inert, and small hand-made tiers; all fail closed on design calls or behavior changes. | Verifiability, not proximity, determines whether a reviewer can safely avoid reading every line. | RFC acceptance | Approve the three tiers and evidence. |
| D7 | Where cannot the trigger apply? | Treat the single-artifact floor and one-unit test volume as scope; require approver and named-invariant evidence only for an atomic correctness window; never exempt breaking changes. | A coherent artifact cannot be split mid-file safely, while breaking changes can use expand/migrate/contract. | RFC acceptance | Approve the bounded exception path. |

## Problem & goals

The repository does not have a median-size problem. Across 234 landed PRs
with behavior or test content over 24 active days, the median is 152
reviewable behavior and test lines at a cadence of 9.75 PRs per active day.
That median already beats every source cited by this RFC. This policy must not
make the median smaller; it must make the thin, very heavy tail better.

The tail is substantial: p75 is 877 reviewable behavior and test lines, p90
is 2,452, p95 is 5,300, and the maximum is 17,275. In the 234-PR corpus, 97
PRs (41.5%) exceed 400 lines and carry 94.5% of volume; 34 (14.5%) exceed
2,000 and carry 71.3%; 15 (6.4%) exceed 5,000 and carry 51.8%; and six (2.6%)
exceed 10,000 and carry 27.7%.

The generic-threshold model assumes every over-threshold PR splits into
`ceil(lines / threshold)` units. At 100, 62% split, creating 12.06 times as
many review units and 117.6 PRs per active day; at 250, 51% split, 5.21 times,
and 50.8 PRs per day; at 400, 41%, 3.53 times, and 34.5; at 800, 31%, 2.15
times, and 21.0; and at 2,000, 15%, 1.35 times, and 13.2. This is not the
recommended policy and is not an improvement in reviewability.

The large tail is not homogeneous. Of 34 PRs over 2,000 reviewable behavior
and test lines, 23 are WIDE mechanical spreads with a median of at most 60
lines per file; nine are MIXED, and two are DEEP concentrated authoring. A
319-file sweep with six reviewable lines per file remains the same
undifferentiated change when divided into eight PRs. Splitting helps MIXED and
DEEP work, not WIDE work.

The recommended shape-routing policy is different from the generic-threshold
model: its 23 WIDE tail changes are proved rather than split, and only 11 MIXED
or DEEP changes split. That adds 27 units, giving 261 units and 10.88 PRs per
active day before ride-along absorption; it is not the 1.35-times, 13.2-per-day
result of splitting every PR above 2,000 lines.

Current bundled-fix guidance causes a related deferral problem. Its
sibling-confined locality rule excludes repository-wide mechanical work even
when it is reproducible and inert. The repository records 177 open backlog
entries and 164 deferred markers across 73 specifications: 341 items. Much of
the mechanical share can safely ride with a host change when it is verifiable,
but locality is a poor proxy for that property.

This RFC therefore separates tail triage from a split mandate, routes work by
review shape, and replaces locality-only ride-alongs with mechanically
checkable proof. It retains the three distinct quantities: raw diff lines for
triage, material volume after content-hash deduplication, and reviewable
behavior and test lines for every size judgement. It uses existing workflow
surfaces without a new configuration, script, or global gate.

## Proposal

### Vocabulary

A **session** is one uninterrupted agent run. Its total output is operational
telemetry, not a PR-size measure. A session may create several commits or PRs.

An **objective** is the outcome assigned to an agent. It has one goal and
explicit acceptance criteria, and it can require several review units. A
**plan task** is a planned unit of work no larger than one review unit; a review
unit may group several contiguous plan tasks.

A **recovery checkpoint** is a local reversible savepoint for undoing agent
work. It is not reviewer-facing history or a semantic boundary.

A **semantic commit** is a curated, independently testable Git commit that
expresses one concept.

A **PR/review unit** is the change a reviewer is asked to understand and
approve. It contains one semantic change, related tests, and validation
evidence.

A **stack** is an ordered set of dependent PRs. A **stack layer** is one
mergeable PR in that set. Each layer leaves the repository working and is
based on the layer below it.

**Raw diff lines** are the unmodified line count from `git diff --shortstat`.
They and changed-file count prompt examination; neither fires the tail trigger.

**Material volume** is raw diff lines after **content-hash deduplication** and
generated output removal. Within one diff, files with the same post-image blob
SHA from `git diff --raw` are one artifact and count once. This identifies
byte-identical projections or packaged copies without new tooling.

**Documentation prose** is non-executable explanatory text for people: guides,
reference pages, changelogs, design records, and human-directed comments.
It is sized by coherence, not line count: one coherent document is one review
unit however long it is.

**Reviewable behavior and test lines** are material volume that expresses
behavior, executable structure, direct tests, or behavior-bearing content.
They exclude deterministic mechanical edits, whole-file deletions, and
non-executable documentation prose. They include agent skill and instruction
files, agent and command definitions, interpreted content embedded in
documentation such as MDX, and fenced code that is extracted, executed, or
tested. Classification follows operational role, never file extension. A mixed
file is classified by its behavior-bearing portion. The 2,000-line tail trigger
applies only to this quantity. An extension-based carve-out would exempt agent
instruction files, which are behavior rather than prose. Authored declarative
data or configuration is reported separately because it can be risky without
being executable code.

A **review shape** is the median reviewable behavior and test lines per changed,
content-deduplicated file containing at least one such line. Documentation
prose, generated output, and byte-identical duplicate copies have zero such
lines and are excluded from both numerator and denominator. **WIDE** is 60 or
fewer lines per file. **MIXED** is above 60 and below 200. **DEEP** is 200 or
more. If classification is ambiguous or contested, treat it as DEEP and
decompose. Shape routes review, not defect risk.

A **Tier 1 reproducible ride-along** is produced by a stated command whose
re-run produces a zero diff. A **Tier 2 provably inert ride-along** is a
bounded dead-code or unused-import removal supported by a search with no
remaining references and green tests. A **Tier 3 hand-made ride-along** is the
existing same-area, same-concern, visibly smaller mechanical change. Tiers 1
and 2 turn on mechanically checkable properties: a re-run produces no diff or
a search returns no references. Tier 3 remains bounded by judgement, so it
retains its locality and size limits.

### Normal lane

The former 100/250/400 policy is removed; there is no normal-lane line target
or generic split mandate. One
specification may deliver one or more PRs, and plan tasks remain qualitative:
small enough to be one PR when they form one independently reviewable semantic
change. Keep behavior with its related tests, separate refactoring from
behavior changes, and make each curated commit one concept and independently
testable. Documentation prose remains coherence-sized, never line-capped.

A plan task predicted to exceed 2,000 reviewable behavior and test lines must
either be split or declare its expected review shape. File count and
concentration can prompt that triage, but are not split thresholds. The trigger
is calibrated to reviewer burden and cadence; it makes no defect-risk claim.

### Tail-triage lane

A **tail-triage lane** is the proof-bearing workflow for intended review units
over 2,000 reviewable behavior and test lines. Raw diff lines, changed-file
count, and concentration are triage inputs only. Report raw diff lines,
material volume, and reviewable behavior and test lines separately, then
classify the review shape before deciding boundaries. This trigger is not an
automatic instruction to split.

Before implementation, identify intended semantic-commit, PR, or stack
boundaries. Classify material volume as:

- authored behavior or structure;
- authored declarative data or configuration;
- deterministic mechanical transformation;
- generated output; or
- deletion.

For WIDE work, do not split. Provide the source artifact, exact transformation
command, transformation invariant, a zero diff on re-run, targeted tests,
sampled review, and rollback evidence.
Splitting a mechanically uniform sweep multiplies PRs without making any of
them reviewable. For MIXED or DEEP work, decompose into dependency-ordered
layers; each must be independently reviewable and leave the repository
working. A handwritten executable file remains authored work even if the
overall feature is described as atomic.

Deduplicate and classify before deciding boundaries. A single coherent artifact
is a floor the trigger cannot go below: it is a bundling limit, not an artifact
limit. The author must name its single unit and state why no split preserves
working layers; otherwise decomposition is required. When it qualifies,
nothing else rides with it and no approval is needed. Five of the eight
observed single-artifact cases are test files. A regular test suite is one
review unit only when its author names the single unit it tests and states why
no split preserves working layers; otherwise decomposition is required.

An atomic correctness window is the only judgement exception. Where no split
can leave every layer working, such as a partially applied security fix, the
repository owner or named maintainer must accept it before review and record
the named invariant, classification, validation, and rollback evidence. A
breaking interface change is explicitly not an exception: use
expand/migrate/contract.

### Proposed replacement seed text

The implementation changes only the third paragraph of `## Pull requests` in
the canonical seed. A **seed** is the adopter-facing source file carried
by a pack. A **self-host projection** is the generated repository copy
built from that source. `packs/core/seeds/docs/CONVENTIONS.md` is the source
and `docs/CONVENTIONS.md` is its self-host projection. The implementation
edits the seed and runs `make build-self`; it must never hand-edit
the projection.

This text is hard-wrapped for the conventions file. It contains no internal
governance citation because it ships into adopter repositories.

~~~markdown
Size a PR as a reviewable semantic change, not as an agent session or a whole
specification. One specification may deliver one PR or a dependency-ordered
stack; each layer must be independently reviewable and leave the repository
working. Keep behavior with its related tests, separate refactoring from
behavior changes, and keep each curated commit independently testable.

Use 2,000 reviewable behavior and test lines only as a tail-triage trigger,
not as an automatic split rule. Classify by operational role, never file
extension: agent instruction files and executed content count as behavior.
Non-executable documentation prose is sized by coherence, not line count.
Report raw diff lines for triage, material volume after content-hash
deduplication, and reviewable behavior and test lines for size judgement.
Raw diff lines and changed-file count only prompt examination. Classify tail
shape by the median reviewable lines per changed, deduplicated file with at
least one such line; exclude prose, generated output, and duplicate copies.
WIDE is 60 or fewer, MIXED is above 60 and below 200, and DEEP is 200 or more.
If classification is ambiguous or contested, treat it as DEEP and decompose.

For mechanically uniform WIDE work, do not split: give the source artifact,
exact command, transformation invariant, zero diff on re-run, targeted tests,
sampled review, and rollback evidence.
For MIXED or DEEP work, split into dependency-ordered working layers. A single
coherent artifact is a floor: when it alone exceeds the trigger, nothing else
rides with it only if the author names its single unit and states why no split
preserves working layers. The same evidence is required for a regular test
suite serving one unit; otherwise decompose. An atomic correctness window
needs prior approver acceptance, a named invariant, volume classification,
validation evidence, and a rollback path; a breaking interface change is not
grounds and uses expand/migrate/contract.

Bundled fixes must be listed under `Bundled fixes:` and fail closed on design
calls or behavior changes. Tier 1 is reproducible: state the command and show
a zero diff on re-run; it may span the repository. Tier 2 is provably inert:
show no remaining references and green tests for bounded dead-code or
unused-import removal. Tier 3 is hand-made: same-area, same-concern, visibly
smaller mechanical work. Tier 1 and Tier 2 require their command or evidence.
~~~

The seed keeps triage deliberately simple. File count and concentration remain
workflow inputs, not standing split rules or claims about defect risk.

### Proposed work-loop behavior

Documentation alone leaves agents likely to discover volume after producing
it. Work-loop is the shipped implementation workflow. Its three quoted blocks
are PLAN, Finish, and Bundled fixes; with the seed and two new-spec blocks,
they are the six quoted blocks in this RFC. Insert them verbatim at their named
anchors in its adopter-shipped skill file. They operationalize PLAN and REVIEW
with prose only. Do not add a
script, manifest field, hook, configuration flag, or hard global gate. Use the
existing plan task list plus `git diff --numstat`, `git diff --shortstat`, and
`git diff --raw`.

The surfaces have deliberately different reach. The conventions seed is the
**full-reach surface**, meaning it applies to every PR regardless of how the
work was produced. Work-loop prompts add depth when work runs that
workflow. `new-spec` task sizing reaches specification-authored
work. The latter two surfaces do not replace the seed because most landed
volume is not traceable to a written specification.

Enforcement has three layers, with leverage inverted from the usual
PR-only approach. Layer 1 is the specification: it sizes review units and
has the highest leverage. Layer 2 is work-loop PLAN: it declares
boundaries and sanity-checks task sizing before EXECUTE, when splitting
is a text edit. Layer 3 is the PR and Finish checklist: it measures, confirms,
or demands proof. It is a backstop and cannot redesign completed work.
Pressure belongs at layers 1 and 2, not as punitive late enforcement at layer
3.

Insert this at the end of **Step 1 PLAN, item 5**, immediately after the
assumption trio (the touched files, proving tests, and excluded work), in
`packs/core/.apm/skills/work-loop/SKILL.md`:

~~~markdown
- **Size the tail.** A plan task predicted above 2,000 reviewable behavior
  and test lines must be split or declare its expected WIDE, MIXED, or DEEP
  review shape. Use the task graph to name intended PR or stack boundaries.
  WIDE work needs reproducibility proof; MIXED and DEEP layers must remain
  independently reviewable and working. Do not invent tasks only to make PRs.
~~~

Insert this in the **Finish checklist**, immediately before the **PR opened
(or merged directly)** item, which requires the four-question PR template
(the required What, Why, verification, and
considered-but-not-changed answers):

~~~markdown
- **Tail-triage check completed.** Inspect raw diff lines, material volume,
  and reviewable behavior and test lines for each intended PR or stack layer.
  Above 2,000 reviewable behavior and test lines, record review shape. WIDE
  work links its source artifact, transformation invariant, command, zero-diff
  re-run, tests, sampled review, and rollback; MIXED and DEEP work links its
  dependency-ordered boundaries.
~~~

### Proposed new-spec behavior

`new-spec` is the shipped specification-authoring skill. Its
existing Step 5 already says to make tasks small enough for one PR, but it
does not define that size. Replace the following **Step 5 plan bullet** in
`packs/core/.apm/skills/new-spec/SKILL.md`:

~~~markdown
- Break the work into plan tasks small enough for one PR. A task predicted
  above 2,000 reviewable behavior and test lines must be split or declare its
  expected WIDE, MIXED, or DEEP review shape.
~~~

Replace the **Task too big** failure-mode bullet in that same Step 5 with:

~~~markdown
- **Task too big.** "Implement the feature" is not a task; "add the validation
  function for X" is. Each task should be small enough for one PR and one
  context window. A task predicted above 2,000 reviewable behavior and test
  lines must be split or declare its expected review shape in the plan.
~~~

This reconciles existing policy. The **bug-fix skill** is the shipped
workflow for correcting existing behavior; it already declines combining a bug
fix with adjacent cleanup. Replace the bundled-fixes carve-out locality
sentence at the **Bundled fixes** anchor in work-loop with the following text.
It is the sixth quoted block; the three mirrored sites named in Follow-on must
stay synchronized.

~~~markdown
Bundled fixes: list each under `Bundled fixes:`. Tier 1 reproducible work must
state its command and produce a zero diff on re-run; Tier 2 inert work must
show no remaining references and green tests; Tier 3 hand-made work remains
same-area, same-concern, visibly smaller, and mechanical. All tiers fail
closed on a design call or behavior change.
~~~

### Migration and adopter impact

Apply this policy prospectively. Do not rewrite frozen specifications or
accepted RFCs that say “one PR.” **Frozen** means an accepted or shipped
artifact whose body is no longer edited. An active task may record new
delivery boundaries in its planning artifact. **Errata** are correction
sections for frozen artifacts.

Core adopters receive this behavior through the canonical seed and the shipped
work-loop skill. This non-cosmetic core pack content change bumps both
`pack.toml` and `.claude-plugin/plugin.json` from 2.9.1 to 2.9.2. Run
`FORCE=1 make build-self` (`make build-self` regenerates projected content;
`FORCE=1` also re-aggregates marketplace metadata) to re-aggregate
`marketplace.json`, then add a
`## [core][2.9.2] — YYYY-MM-DD` section to `docs/product/changelog.md`. No
adopter configuration is required.

## Options considered

| Option | Consequence | Decision |
| --- | --- | --- |
| Do nothing | Preserves a rule that attempts to shrink a healthy median and leaves locality-driven deferral intact. | Rejected. |
| Generic split thresholds | In the 234-PR generic-threshold model, 400 splits 41% of PRs, producing 3.53 times as many review units and 34.5 PRs per active day; it makes WIDE work no more reviewable. | Rejected. |
| Hard-cap all diffs | Is simple but rejects valid generated projections, regular test suites, and safe broad mechanical work. | Rejected. |
| Remove numeric guidance | Avoids false precision but removes the tail-triage backstop for concentrated reviewer burden. | Rejected. |
| Shape-routed tail triage | Preserves the healthy median, proves WIDE work, and decomposes MIXED and DEEP work. | Accepted. |
| Locality-only ride-alongs | Fails closed on provably inert repo-wide work and drives mechanical work into deferred backlogs. | Rejected. |
| Verifiability-tier ride-alongs | Allows only mechanically checkable reproducibility or inertness proof, retaining a narrow hand-made tier. | Accepted. |
| Seed-only documentation | Changes the adopter convention but discovers tail shape after implementation. | Rejected. |
| Specification sizing plus PLAN and Finish prompts | Sizes work upstream and records classification without a new enforcement system. | Accepted. |
| Blocking global hook | Would fail much of current history and conflicts with consumer-wired projected gates. | Rejected. |

## Risks & what would make this wrong

The largest untested assumption is behavioral. PLAN and REVIEW prompts may not
change classification, decomposition, or ride-along decisions. The evidence is
historical shape and cadence, not review outcomes. A later enforcement proposal
needs proof-quality, classification-consistency, and rework evidence.

The 2,000-line trigger is calibrated to reviewer burden and cadence, not to
defect risk. It can create noise or miss concentrated work; file count and
concentration remain triage inputs. Revise calibration only through a later
convention decision.

WIDE classification could become a convenient label. The policy fails closed:
the exact command must re-run to a zero diff, with targeted tests, sampled
review, and rollback. Tier 2 likewise requires a search with no remaining
references, not an author's convenience judgement. A maximally permissive
stacking rule would remove the review boundary this policy is meant to protect.

Dependency layers can encourage shallow stacks. Each MIXED or DEEP layer must
be independently reviewable and leave the repository working. Only an atomic
correctness window may depart from that invariant, with approver acceptance and
named-invariant evidence.

No LOC number measures risk universally. Security, authorization, data
migration, external I/O, and unfamiliar-domain changes can be risky at ten
lines. A deterministic projection can be large and cheaply verified. This RFC
does not replace existing risk triggers or specialist review.

The code/prose boundary requires judgement. A change that mixes a large
document with behavior-bearing content is sized on its behavior-bearing
portion, while its documentation prose remains a coherence review.
Documentation still contributes raw diff lines to wide-change triage and
reports its volume there.

The conventions seed is the only full-reach surface for most work. Its clarity
therefore matters more than workflow prompts for PRs that do not run work-loop
or have no written specification. A later blocking gate would be the only
universal operational mechanism. This RFC accepts partial operational reach to
avoid adding that global gate now.

## Evidence & prior art

See [the evidence ledger](0090-notes/evidence.md) for fetched-and-verified
citations, exact quotes, repository measurement methods, and their limits.

| Evidence | Finding | Confidence and limit |
| Cadence and shape, 234 landed PRs over 24 active days | 9.75 PRs per active day; median 152 reviewable behavior and test lines, p75 877, p90 2,452, p95 5,300, and maximum 17,275. | High for this corpus; excludes PRs with no behavior or test content and makes no review-outcome claim. |
| Tail review shape, 34 PRs over 2,000 lines | 23 are WIDE at at most 60 median lines per file, nine MIXED, and two DEEP. | Historical classification; supports routing, not a defect-risk claim. |
| Net-effect model | Tail routing adds 27 review units; there are 60 absorption candidates. The combined policy breaks even near 46% absorption and ranges from 10.88 to 8.38 PRs per day at 0% to 100%. | Absorbability is inferred from subjects, not verified host changes; 100% is unreachable. Deferred mechanical work is upside, not counted. |
| Indivisibility | Eight PRs (3.4%) contain one file over 2,000 reviewable lines; largest is 3,676 and five are test files. All three breaking changes are spread. | Supports the single-artifact floor and regular-test treatment; a small historical sample. |
| --- | --- | --- |
| Repository spike, 337 squash merges | Median 790 raw diff lines, mean 2,257 raw diff lines, 64% over 400 raw diff lines, and 25% over 25 files. | High for this sample; no causality or safe threshold. |
| Three quantities, 187 landed PRs | Median raw diff lines 1,068; material volume 1,057; reviewable behavior and test lines 231. Respectively, 72%, 70%, and 40% exceed 400 of the named quantity. | Single-repository historical sample with no review-outcome data. Deduplication changes the headline little; it matters most for giant replicated diffs. |
| Repository plans | 305 of 380 spec directories contain `Depends on:`; observed dependencies include 426 `none`, 293 `T1`, and chains through task 14. This is available decomposition input, not proof that every task boundary is good. | High that usable dependency structure exists; per-task quality varies. |
| `4f5b978f` decomposition analysis | Its four strict-linear plan tasks could have formed four layers, but roughly twelve tasks were needed to approach 400 reviewable behavior and test lines per layer; its 45% replicated volume inflated raw diff size. | One PR in one repository; historical analysis with no review-outcome data. |
| Replication across 116 wide PRs | Median replicated share is 0%, mean 7%, and maximum 71%; the six largest diffs carry roughly 37–45% replication. Content-hash deduplication reduces overstatement where it matters most. | Single repository and historical sample; no review-outcome data. |
| Specification-tracking reach, 337 PRs | Only 76 PRs carry a written-spec footer; the other 261 contribute 73% of changed volume. Written-spec PRs are not smaller. | Missing footer does not prove work-loop was skipped because light mode uses inline specs; tool-usage analytics is needed to separate paths. |
| Single-file concentration, 91 landed PRs | After excluding documentation and generated paths, median single-file share is 28%, p75 52%, p90 62%; 26% have a file at least 50%, and 17 have one at least 1,000 authored lines. | Single-repository historical sample with no review-outcome data; supports triage calibration, not a risk threshold. |
| Commit `92edf24827866aee44db53b88d432aac6d02589a` | Current 100/400 raw-diff-line wording added a “quantitative anchor” and cited no empirical source. | High provenance evidence; not proof the numbers are invalid. |
| Google Small CLs | “100 lines is usually a reasonable size for a CL, and 1000 lines is usually too large”; refactors are usually separate and large CLs need consent. | Strong practitioner guidance; not agent-specific. |
| Chromium `cl_tips` | Try to keep changes below 500 code lines including tests; regular test patterns can be larger; a CL should effect one type of change. | Strong operational prior art; not a universal limit. |
| SmartBear/Cisco study | Performance probably degrades after 300–400 LOC; review should be under 90 minutes and reviewers wear out after 60. The 200-LOC figure is descriptive, not advice. | Useful field evidence; 2006 context limits transfer. |
| di Biase et al., PeerJ CS 5:e193 (2019), 28 developers | Decomposition produced fewer wrongly reported issues and more context-seeking. It did not increase defects found or improve comprehension. | Controlled but narrow evidence; no LOC cap follows. |
| OpenAI, How OpenAI uses Codex | Codex works best with well-scoped tasks taking about an hour or a few hundred implementation lines. | Agent-specific guidance; capability changes over time. |
| OpenAI, Harness engineering and Symphony | Depth-first building blocks, rails, task trees, dependency ordering, and multiple PRs support separating objectives from PRs. | Relevant practice, not a threshold study. |
| GitHub Copilot and stacked PR guidance | Good tasks have clear criteria and changed-file scope; agent code can map tasks to dependent stacked PRs. | Relevant workflow guidance; do not force one task per PR. |
| Graphite | Flag PRs over 250 lines or 25 files and review each stack PR independently. | Vendor guidance; supports advisory signals only. |
| Aider, Cline, Cursor, Anthropic checkpoint practice | Tools converge on recovery checkpoints and rollbacks, not reviewer-facing commit-size rules. | Strong vocabulary distinction; no numeric conclusion. |
| arXiv 2606.15689 and 2603.26130 | One preprint reports F1 from 0.657 under 10 lines to 0.043 over 150 using five models and 150 samples; another reports monotonic degradation and attention dilution. | Low-confidence preprints. They reject the claim that AI review makes an undifferentiated 17,000-line PR safe. They cannot set production thresholds. |

## Open questions

1. Should WIDE proof use the current flexible PR template or a standard
   subsection? Recommended default: retain the flexible form; the policy adds
   no machinery. Owner: eugenelim. Decide by: follow-on implementation.
2. What absorption rate is reached for Tier 1 and Tier 3 candidates?
   Recommended default: measure after 100 landed PRs and compare review-unit
   cadence with the 46% break-even estimate. Owner: eugenelim. Decide by: the
   next convention review.
3. What outcome measures would justify a later blocking check? Recommended
   default: require proof-quality, classification-consistency, and rework
   evidence, not a line-count outcome alone. Owner: eugenelim. Decide by: any
   RFC proposing a gate.

## Follow-on artifacts

If accepted, follow-on work must:

1. Edit `packs/core/seeds/docs/CONVENTIONS.md` with the quoted text and
   regenerate `docs/CONVENTIONS.md` through `make build-self`.
2. Apply the three quoted work-loop insertions at their named anchors. Keep the
   bundled-fixes carve-out synchronized across its canonical site in
   `work-loop/SKILL.md`, `implementer.md`'s operating envelope, and
   `adversarial-reviewer.md`'s scope check #4.
3. Add task-sizing guidance to `new-spec`, the specification-authoring skill.
   This is an additional shipped core-pack surface and rides the same version
   bump as the seed and work-loop changes.
4. Bump both core versions to 2.9.2, re-aggregate marketplace metadata with
   `FORCE=1 make build-self`, and add the core changelog entry.
5. Verify seed/projection synchronization, version consistency, generated
   marketplace metadata, RFC/document conventions, and applicable core pack
   build and test gates.
6. Add focused tests only if existing validation cannot prove projected content,
   version consistency, or workflow text. This RFC does not justify a new
   size-check script or global blocking hook.

Compliance has two layers. Existing validation proves that the shipped seed
and projection remain synchronized. Work-loop PLAN and REVIEW records prove a
tail change was classified, decomposed, or proved reproducible. The second
layer is deliberately reviewable workflow evidence, not universal LOC-based
failure.

## Errata

The body above is frozen. Corrections are recorded here.

- **2026-08-19 — two corrections found during implementation, both applied to
  the shipped text.** First, the single-artifact floor was written as a
  conditional: "nothing else rides with it only if the author names its single
  unit and states why no split preserves working layers." That makes the
  prohibition contingent on the justification, which inverts the intent. The
  floor is a scope statement, not a discretionary exception. The shipped
  wording is unconditional: nothing else rides with it, and the author
  separately names the single unit it serves and states why no split preserves
  working layers. Second, the qualifier "mechanically uniform" was dropped from
  the WIDE routing rule in the `work-loop` and `new-spec` surfaces, which would
  have let any WIDE-shaped change avoid decomposition on reproducibility proof
  alone rather than only mechanically uniform work. The qualifier is restored at
  every routing site. Approver: eugenelim.

