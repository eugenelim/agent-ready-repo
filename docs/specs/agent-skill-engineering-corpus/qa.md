# QA record — agent-skill-engineering corpus (INI-009 slice 2a)

Base for every measurement below: `9d9b5904c`, taken against `origin/main` at
`9d9b5904c`. Every figure here was produced by the invocation named beside it.

The blind retrieval and behaviour measurements were taken on `f4f29a4b1`.
They are carried forward across every rebase since, rather than re-taken,
because they are bound by content digest and not by base commit: a `git diff`
over `packs/agent-skill-engineering/` across each pair of bases is empty, so the
artefacts they measured are byte-identical. The activation measurement is not
carried forward — restoring the `create`/`update` sentence moved the `SKILL.md`
digest it pins, so it was re-taken at iteration 7. The suite-level figures below
were re-run on this base.

The earlier figures in the failure-attribution table were first observed on
`706808287` against `origin/main` at `221bcb3f4`, and were re-run on this base
rather than carried forward, because a base that has moved cannot support a
same-source claim. Where a re-run changed a result the table says so.

## Failure attribution

The *Always do* Boundary requires every failure this slice's gate chain observed
to carry the invocation that reproduces it, the base it was seen on, an
attribution, and who attributed it. Nothing observed is dropped.

| Failure | Reproducing invocation | Attribution | Attributor |
| --- | --- | --- | --- |
| `test_guide_typed_asides.py::test_ledger_has_complete_terminal_classifications` and `::test_ledger_matches_converted_asides_and_unchanged_quotations` | `python3 -m pytest tools/test_guide_typed_asides.py -q` → 2 failed, 2 passed | `owned-elsewhere`. Reproduces on the base independently of this slice. The file is named in no `Makefile` line and in no workflow, so no gate this slice runs invokes it. | Claude, this session |
| `test_local_ci_shared_test_deduplication.py::test_core_pytest_semantic_node_contracts_are_exact` | `python3 -m pytest tools/test_local_ci_shared_test_deduplication.py::test_core_pytest_semantic_node_contracts_are_exact -q` → 1 passed | `inherited`, **now cleared**. Arrived red from an earlier base at 78 nodes against a pin of 73; its owner re-pinned it upstream and it passes on this base. | Claude, this session |
| Four `packs/agent-skill-engineering/tests` failures — `test_independent_router_results_meet_precision_and_recall_gate`, `test_independent_activation_results_bind_all_queries_and_descriptions`, and `test_contract.py`'s two authoring-behaviour tests | `python3 -m pytest packs/agent-skill-engineering/tests -q` → 111 passed | `inherited`, **now cleared**. Caused upstream by `c7ed3f910`, which added an eval case without moving its assertions and rewrote three `SKILL.md` files, invalidating recorded digests. Main resolved it; a rebase brought the fix. | Claude, this session |
| `gate-main`, `Caps enforcer self-test`, and `make build-check` (CI) | `python3 tools/lint-pack-test-boundary.py` → `ok [pack-tests-stay-in-pack]` | `caused-here`, **fixed**. `test_corpus_admission.py` joined a fixture-supplied name onto a path, which the boundary linter cannot prove stays in-pack. Resolved by globbing each root and indexing by stem. `make build-check` aggregates `gate-main`; one defect, three red checks. | Claude, this session |
| Three ruff errors in this slice's test modules | `make lint-ruff` → `All checks passed!` | `caused-here`, **fixed**. Extraneous blank lines. Found by CI, not locally: the pack suite and both boundary linters were run after every edit, `make lint-ruff` was not, though it is in the documented command set. | Claude, this session |
| `lint-brief-coverage` in `gate-main`, and `make build-check` which aggregates it | `python3 .claude/skills/author-delivery-brief/scripts/lint-brief-coverage.py --root .` → 3 briefs checked, exit 0 | `caused-here`, **fixed**. Moving the spec's Status from `Approved` to `Implementing` left the brief's auto-derived Spec map stale, and the rollup is fail-closed. Fixed by rolling the row up and re-pinning the brief digest in both workspace registrations, since the brief's sha256 is their `source.revision`. Seen on CI at `f2281d6be`, not locally: the build chain stops at this lint before reaching the pack suites. | Claude, this session |
| `tools/test_check_output_readability.py::test_each_publishable_pack_has_a_passing_readability_fixture` | `python3 -m pytest tools/test_check_output_readability.py -q` → 37 passed | `inherited`, **fixed here**. Re-attributed after review: the failure reproduces on the merge base independently of this branch — `origin/main` carries 22 non-underscore packs, a ledger reading 21, and no `cognitive-load-*` scenario in this pack. The row's own evidence said so and the attribution did not follow it. Fixed by seeding the review skill's readability corpus and correcting the count. | Claude, this session |
| `review-or-optimize-agent-skill` q03 recorded MISS at activation iteration 6 | `PYTHONPATH=packages/agentbundle python3 -m agentbundle pack evals run --pack agent-skill-engineering --mode headless --runs 1` → iteration 7: 18/18 | `environmental`, **not carried**. The harness reported `1 harness error(s) — trigger rates unreliable` and attributed the MISS to an errored run rather than a non-trigger. A run the harness declares unreliable is not a measurement, so iteration 6 was discarded and re-taken rather than recorded with a caveat. Iteration 7 is clean on the same tree. | Claude, this session |

Routing: the two guides ledger failures are routed against the existing
`[backlog].open` entry `guide-blockquote-ledger-has-no-regenerator`
(`workspace.toml:278`), whose subject is the same ungated ledger. Extending an
existing entry's summary adds no legacy-shaped entry, so the ceiling is not
reached and no raise is proposed.

## Ratchet raise — recorded, not implied

`unsatisfied_dependency`'s tolerated ceiling was raised 8 to 9 in
`tests/roster/test_workspace_status_projection.py`. This is an *Ask first*
action under the spec's Boundaries, and the approval is recorded here rather
than only in a code comment.

| Field | Value |
| --- | --- |
| Raised | 8 to 9, `unsatisfied_dependency` |
| Approved by | the repository owner, in session, 2026-08-29 |
| Evidence shown at approval | 8 pre-existing edges — 6 product intents, 2 from portfolio-first-run-pilot — and 1 new: `docs/specs/agent-skill-engineering-corpus/spec.md`, the 2b→2a dependency |
| Reason | the edge is real and transient: it clears when 2a ships. Dropping it would make a queued slice look startable while it is blocked; raising the ceiling was chosen over falsifying the edge |
| Verified after repair | the engine's reported cause is now `dependency not terminal`, matching the recorded rationale. Before the provenance and status repairs above it read `dependency has findings`, because 2a was structurally blocked by its own registration defects |

The spec's Assumption that this slice "raises no ratchet" and the plan's
constraint that it touches "no ratchet" were both true when written and are
superseded by this approval. Both were frozen while the waves ran, so this
record carried the correction; both are now corrected in place at ship, and
this row remains the evidence for the approval itself.

## Foundation pin re-take — the record AC8 now requires

Two of the 24 foundation retrieval pins were re-taken during this slice. AC8
originally forbade the pins fixture being written by any later re-recording
step; the commit that recorded the post-corpus measurement wrote both that
measurement and the pins, which defeated the control. The authority existed but
lived only in a commit message, so nothing committed could show a reader why
the pins moved. AC8 now admits a re-take on explicit owner authority *and*
requires this record; it is written here so the fixture can still detect the
regression it exists for.

| Field | Value |
| --- | --- |
| Authorised by | the repository owner, in session |
| Pins re-taken | 2 of 24 |
| Detected by | an independent acceptance-criteria verification pass at the ship gate, not by a gate |

**`authorization-at-trigger`** — was `[framing-and-trigger-quality,
resources-scripts-and-exit-contracts]`, now `[framing-and-trigger-quality]`.
The corpus change is `resources-scripts-and-exit-contracts` gaining a scope
line that explicitly redirects activation and authorization timing to
`framing-and-trigger-quality`. The original pin therefore named a topic the
corpus now tells readers not to route there. Four independent judges measured
framing alone, one of them against a cleanly compiled pre-T7 corpus, which is
what distinguishes a wrong original value from a moved measurement.

**`asset-or-reference`** — was `[instruction-density-and-progressive-disclosure,
resources-scripts-and-exit-contracts]`, now
`[instruction-density-and-progressive-disclosure]`. The asset-versus-reference
axis was unarbitrated when the pin was taken, so both topics matched and the
pin recorded the ambiguity rather than a routing. A reciprocal redirect now
assigns kind-decisions to `instruction-density-and-progressive-disclosure` and
kind-behaviour to `resources-scripts-and-exit-contracts`; it was verified
symmetric from both entry points with no loop, and three script-behaviour
controls held.

The remaining 22 pins are unchanged and hold against the current measurement.

## Behaviour and review evidence

Graded by `python3 -m agentbundle pack evals run --pack agent-skill-engineering
--mode in-harness --check behavior --reports <driver payload>`; tier B-lite,
fidelity `observed+attested`, provenance `operator-attested`. Author cases at
iteration 2, review cases at iteration 5 — the fixture's
`graded_run.review_iteration` is the authority for that number.

Eight durable results: six authoring, two review. **Twenty-three of twenty-four
authoring assertions and ten of eleven review assertions hold.** Author cases
sit at iteration 2, review cases at iteration 5.

Execution and attestation were held apart from authoring. One context read only
each skill's `SKILL.md` and the prompts — markers, assertions, expected output,
the pack README, and every test file withheld — and wrote each response to its
eval workspace. A separate context judged the assertions against those
responses, briefed that a clean sheet would make the judgement suspect and that
a borderline case must be recorded false.

### One recorded miss, named rather than absorbed

`cross-session-resumption` assertion 2 measured **false**. The response declined
to commit to a durable resumption record, because persisting one would widen the
skill past `filesystem_read_untrusted` and contradict its own promise not to
modify files; it surfaced both options and put the choice to the user. That is
defensible behaviour and arguably a defective case — the attesting context
independently found assertions 2 and 4 contradictory, since a response that
waits for authorization cannot have *added* anything.

It is recorded as measured rather than reworded. Rewriting an assertion after
seeing its verdict is tuning. `test_contract.py` names the exact `(case, index)`
pair, so a different miss still reddens while this one does not read as a pass.

### Two circular derivations found and closed

Both workflow skills declared an output marker in `expect.output_contains` that
the skill itself instructed nowhere:

- **Authoring — `Write status:`.** Present only in `evals.json`,
  `behavior-results.json`, and a README example. An independent execution
  produced `Mode:` every time and `Write status:` never, so the shipped
  foundation result for `frame-new-skill`, which records that marker as
  observed, was not reproducible from the skill.
- **Review — `Mode: review`.** The skill said only "Finish with the mode,
  target, applicable checks…", an unlabelled comma list fixing no spelling. Both
  review responses produced every check identifier and missed only that marker.

The predecessor's QA record documents finding and fixing this same circularity
once, on the review side's `actual_findings`. Two further instances survived
because nothing re-derived the markers from a blind run. Both receipts now
instruct their graded lines, and after the fix every declared marker appears in
real captured output.

The two halves are recorded differently, and the distinction matters. The **two
review results** carry the five runner values, so `Mode: review` is attested by
a measured `output_ok`; the gap the predecessor could only declare is closed
with evidence there. The **six authoring results** carry `actual_markers` and no
runner values, so `Write status:` is attested by the transcribed marker list
rather than by a runner verdict.

**Known weakness in that fix.** Both instructions are written as templates with
alternatives on one line (`Mode: review | optimize`; three write-status values).
The executing context noted that a fenced template admits three readings — emit
the alternation literally, emit the resolved value, or reproduce the fence — and
that "a grader keying on an exact first line would reject two of the three."
Both runs landed on the reading the grader needs, but that is the executor's
judgement rather than a property of the wording. Recorded rather than treated as
settled by two successful runs.

### Case-wording defects, recorded separately from the verdicts

Named by the attesting contexts, none of which changed a verdict:

1. `cross-session-resumption` #2 and #4 are mutually contradictory as written.
2. `cross-session-resumption` #1 is unfalsifiable: the prompt names a path that
   does not resolve, so both compliance and a correct refusal satisfy it.
3. `progressive-result-presentation` #2 and its `expected_output` disagree on
   the state set.
4. "Uses frame as the **default** read-only mode" (three cases) cannot test
   "default" from output text; only the read-only half is observable.
5. `detect-script-contract-failure` #5 bundles four claims and files one of them
   under the wrong check identifier; its "needed before optimization" clause is
   unfalsifiable as written.
6. `detect-activation-failure` #4 and #5 are compound, with no stated mapping
   from identifier to harm.

### What this record does not attest

Both markers are enforced at run time by the grader's `output_ok`, and **the
marker check is not re-checkable from the committed artifact**. For the two
review results that verdict is recorded, so it can be read back; for the six
authoring results it is not, and their `actual_markers` list is a transcription
of what the run produced rather than a re-derivable check. Re-running the
graded command is the only way to re-establish either.

The semantic assertion half is likewise not re-derivable: those verdicts are
attested by a named context, not computable from the fixture. That is the seam
the RFC-0097 erratum establishes — form checked mechanically, soundness by a
named judge — and it is stated here rather than implied.

### The re-measured review round, and its second recorded miss

Both review cases were re-taken blind against the corrected case. Execution and
adjudication were held in separate contexts, and the adjudicating one was told a
clean sheet would make its judgement suspect.

| Case | Reported | Sustained | Declared | Assertions |
| --- | --- | --- | --- | --- |
| `detect-activation-failure` | 6 | 5 | 4 | 5 of 5 |
| `detect-script-contract-failure` | 9 | 9 | 6 | 5 of 6 |

Containment holds in both directions that matter: every declared identifier was
reported, and every reported one is a checklist identifier the skill defines.
`ASE-PROG-01` is now sustained on its own evidence — the seeded reference is
loaded "whatever the task is" and duplicates its caller's rules — which is what
the seeding was for.

**The one over-report.** `ASE-WRITE-01` on the activation candidate was ruled
over-reported in both rounds for the same reason: the identifier's subject is
*conflicting* writes, and that candidate has one writer, one pass, and no
fan-out, so there is no overlap for a serialization or refusal rule to attach
to. Its real gap — unbounded, unauthorized write scope — is the same clause
already charged under `ASE-AUTH-01`. The adjudicator recorded this as the
closest call on the sheet, since the checklist entry bundles "write sets are
explicit" with "safe under overlap" under one title, and the candidate does
violate the first. The ambiguity is in the checklist, not only in the output.

**The recorded miss.** Assertion 6 measured **false**. It asks the review to
name the replay, exit, and cleanup contract `ASE-DET-01` requires. Two of three
limbs were met — the response prescribed injected-input determinism and distinct
exit classes, as things that should hold rather than as absences — and cleanup
was never returned to: neither prescribed nor disposed of as vacuous, which it
arguably is, since the helper writes no file. It is recorded as measured rather
than reworded, and `test_contract.py` names the exact `(case, index)` pair, so a
different miss still reddens while this one does not read as a pass. A case
carrying a known miss must also record `assertions_ok` and `passed` as False;
exempting those instead would let a re-record claim a clean pass for a run that
missed.

**A premise that had to be withdrawn.** The adjudicator's first ruling on
assertion 6 carried a second ground — that the review output contained no
smallest-safe-response element at all, making it non-conformant to the skill's
step 5. That was an artefact of how the outputs were summarised for grading, not
a property of the output; every one of its nine findings carries the clause. Put
to the adjudicator with the verbatim text, it struck that ground and re-ruled on
the cleanup limb alone. The verdict survived the correction; the reason for it
did not, and a verdict resting on a briefing error is not evidence.

**A gap this sheet cannot close.** No assertion on the activation case touches
`ASE-WRITE-01` or `ASE-FAIL-01`, and nothing anywhere penalises over-reporting,
so a padded finding list can still score 5 of 5. The `CHECKLIST_IDS` bound stops
padding with invented identifiers but not with real ones the candidate does not
exhibit. Closing it needs an assertion of the form "reports no identifier the
candidate does not exhibit", which is a new declaration and therefore a new
measurement. Recorded, not taken here.

## The ship-gate review round

Three reviewers ran against the complete diff and every report was adjudicated.
Nine blocking claims went to adjudication: **seven sustained, two refuted, two
indeterminate**. Both refutations matter as much as the sustains, because both
would otherwise have been fixed on a wrong premise.

**Refuted — a padded-record scenario that cannot occur.** A reviewer held that
`seeded <= actual` survives only because the graded runs over-report, and would
redden once the over-reported `ASE-WRITE-01` is dropped. `ASE-WRITE-01` is
reported by *both* graded results, so dropping the over-reported instance leaves
the union at all ten and the assertion holds. The structural half — that a
maximally padded pair would satisfy both the floor and the `CHECKLIST_IDS`
ceiling — is accurate, and is the gap this record already declares below rather
than a new defect.

**Refuted — a path join that is not the one that broke CI.** A reviewer found
the variable-operand form recurring in `test_foundation_corpus.py`. Its base is
a `tmp_path` staging directory, not a pack path, so the pack-test boundary rule
does not govern it and the linter's silence is correct rather than a blind spot.
The earlier fix was tied to a join rooted at a real pack path; it did not
establish a repository-wide ban on variable operands.

**Sustained, and the reviewer's own fix was wrong.** The symlink clause in the
staged-read helper could never fail: `.resolve(strict=True)` collapses every
link before `not target.is_symlink()` runs. The proposed remedy was to adopt the
blessed `read_confined_regular_file`. That would have been a regression — it
reads through `_open_confined_regular_file` rather than `Path.read_text`, and
the checkout-unavailable guard works by monkeypatching exactly `Path.read_text`,
so the blessed helper would have silently defeated the guard this call site
exists to exercise. The probe moved ahead of resolution instead, and the read
stays where the guard can see it.

### What the round changed

| Finding | Disposition |
| --- | --- |
| AC9's portability clause had no verifying artifact | Guard landed as the plan specified, with a 37-file non-vacuity floor and a three-form positive control; all three confirmed by mutation |
| The plan still asserted the control AC8's amendment deleted | Both restatements corrected to the amended control |
| The CI entry was ancestor-shaped, falsifying a lint exemption's premise | Replaced with the four compatibility-class members the Makefile names |
| *Never do* forbade the ratchet raise *Ask first* permits | Scoped to engine code and `packs/core`; the false "within the existing ceiling" claim corrected; the amendment recorded in Follow-ons |
| A shipped mode sentence was rewritten against an explicit plan prohibition | Restored, at the cost of re-measuring activation |
| A doctrine group would have received zero parity checking, silently | The skip now fails with the reason, so the gap announces itself at admission |
| The gate table recorded 106 where the tree collects 111 | Corrected |

### A branch this suite still cannot exercise

Every admitted topic declares `observed-practice`, so the `doctrine` arm of the
admission predicate — its promotion classes, the two-runtime clause equality,
the shared-mechanism check, the repetition floor, and source attributability —
has never executed against any input. Deleting it would leave the suite green.
The plan records seven mutation proofs for it, but that method leaves no
committed trace by design, so nothing in the tree preserves them.

This is recorded rather than repaired. The absence of any doctrine group is a
deliberate, evidence-limited outcome, not an oversight, and manufacturing a
synthetic one to exercise the branch would put a claim group in the admission
record that no evidence supports. The honest state is that the first slice to
admit doctrine inherits an unexercised predicate, and now also inherits a parity
check that fails loudly instead of skipping.

## Where the readability corpus was placed, and what it cost

Every publishable pack must ship a `cognitive-load-*` eval scenario whose
markdown seeds the repository's readability gate. Three placements were
possible and none was free:

| Placement | Cost |
| --- | --- |
| `ase-okf-reference` | Free — no recorded result pins its `evals/evals.json`. Rejected: the skill declares it "answers no user request, performs no user task", so an output-quality scenario there contradicts its own contract |
| `author-or-update-agent-skill` | Six graded results pin that file's digest; all six would need re-measuring |
| `review-or-optimize-agent-skill` | Two graded results pin it. **Chosen** |

The digest pin is whole-file, so appending a third, unrelated scenario moved it
even though the two graded cases' prompts, assertions and candidate files are
byte-identical. Re-stamping the new digest onto the old observations was
available and was not taken: it is the same back-filling the retrieval
re-measurement above refused. The evidence was re-taken instead.

The new scenario is deliberately ungraded. It declares `assertions` but no
`expect.output_contains`, because a declared marker that no recorded result
attests is precisely the circular derivation this pack has already had to
remove twice. It is listed in `REVIEW_READABILITY_FILES` rather than
`REVIEW_EVAL_FILES` for the same reason: every member of the latter is
parametrized into the digest test, which would demand a recorded result that
should not exist.

## What re-measuring the review cases exposed

Re-taking the two graded review measurements did not reproduce the recorded
result, and the discrepancies were defects in the eval rather than in the skill.
Three were found and all three are fixed.

**The eval declared a defect its candidate did not contain.** `ASE-PROG-01` was
declared in `expect.output_contains` and in the seeded set, but the candidate
shipped no references, so there was no reference-without-a-caller and no
eagerly-loaded reference to observe. The fixture's own header agreed: it named
`ASE-DET-01 / ASE-CTX-01 / ASE-CONC-01` and never claimed `ASE-PROG-01`. Closed
by seeding the defect for real — the candidate now carries a reference that
restates its caller's rules and is loaded unconditionally — rather than by
deleting the declaration to match the observation.

**One assertion rewarded padding.** `Reports ASE-PROG-01 and ASE-CTX-01 for
duplicated unrouted instructions` demanded two identifiers off a single
sentence, and the adjudicating context named it the direct cause of the run's
one over-report: as written it could not distinguish a correct review from a
padded one. It is now satisfiable honestly because the second identifier has
its own evidence.

**One assertion straddled two identifiers.** `Reports ASE-FAIL-01 and names the
deterministic replay, exit, and cleanup contract needed before optimization` was
four conjuncts scored as one boolean, three of which belong to `ASE-DET-01`
rather than the `ASE-FAIL-01` it cites. Split along that seam, so a failure now
says which half failed.

### The recorded contract was stricter than the check it records

The per-result assertion required `actual_findings` to *equal* the declared
markers. But `expect.output_contains` is graded by the runner as a substring
check, so it declares a floor, and the equality made a review that finds a real
defect beyond the seeded set into a failure. It is now containment, bounded
above by the identifiers the shipped checklist actually defines — derived from
`review-checklist.md` at test time rather than restated, so retiring a check
cannot leave the bound describing a vocabulary the skill no longer has. The
floor therefore cannot be padded with invented identifiers.

### An answer key inside the artifact under review

Both candidates open with an `INERT REVIEW FIXTURE` comment that names the
seeded identifiers. It earns its place — it is what stops an agent treating a
deliberately defective fixture as instructions — but it also puts part of the
expected answer inside the material being reviewed, and a review could score
well by reading it rather than by applying the checklist. Two independent
contexts reported handling it correctly: the executing one said it ran the full
checklist first and neither removed findings to match the header nor added any
because of it, and the adjudicating one confirmed neither output cited the
comment as authority, noting that treating it as authority would itself be an
`ASE-SEC-01` failure by the reviewer. Both runs returned more identifiers than
the header names, which is the evidence that neither anchored on it. Recorded as
a known weakness of the fixture design, not repaired here: removing the header
would trade a measurement risk for a safety one.

## Skill-contract ambiguities observed during execution

Surfaced by the executing contexts, unresolved and not blocking:

- Authoring: `not authorized` versus `awaiting explicit authorization` for a
  design request that implies an eventual write.
- Authoring: `update` mode's entry condition requires an unambiguous root, while
  the description promises that resolving an unresolved target is the workflow's
  first step; the two pull opposite ways.
- Authoring: a "skill root" that is a bare `*-SKILL.md` file rather than a
  directory has no stated disposition.
- Review: no severity vocabulary is defined anywhere in the skill.
- Review: every check identifier ends `-01`, so two distinct defects under one
  check share an identifier with no defined way to disambiguate.
- Review: "verification" is undefined for a read-only mode.
- Review: provider-capability detection names no inspection surface for a
  filesystem-only session, and a reader who treated the repository's own
  reference skill as that surface would violate the same document's ban on
  inferring a provider from a familiar filename.

## Gates

| Gate | Invocation | Outcome |
| --- | --- | --- |
| Pack suite | `python3 -m pytest packs/agent-skill-engineering/tests -q` | 116 passed |
| Shared OKF compiler | `python3 -m pytest packs/catalogue-curation/tests/skills/compile-okf/ -q` | 150 passed |
| Pack-test boundary | `python3 tools/lint-pack-test-boundary.py` | ok, 210 files |
| Boundary structural self-test | `python3 tools/test-lint-boundary-structural.py` | 117 cases |
| Caps enforcer self-test | `python3 tools/test-lint-pack-test-boundary.py` | 154 cases |
| Style | `make lint-ruff` | All checks passed |
| Spec metadata | `python3 .claude/skills/work-loop/scripts/lint-spec-status.py --root .` | clean |
| Activation | `python3 -m agentbundle pack evals run --pack agent-skill-engineering --mode headless --runs 1` | iteration 7: 18/18, zero errors, zero exclusivity violations |
| Catalogue verify | `PYTHONPATH=packages/agentbundle python3 -m agentbundle catalogue verify --root .` | ok |
| Catalogue deep lint | `PYTHONPATH=packages/agentbundle python3 -m agentbundle catalogue lint --root . --deep` | ok, 70 informational findings |
| Brief coverage | `python3 .claude/skills/author-delivery-brief/scripts/lint-brief-coverage.py --root .` | 3 briefs checked, exit 0 |
| Output readability | `python3 -m pytest tools/test_check_output_readability.py -q` | 37 passed |
| Workspace reconciliation | `python3 -m pytest tests/roster/test_workspace_status_projection.py -q` | 26 passed, 12 subtests passed |
| Web rendered output | `npm test --prefix web` after `make bootstrap-sites && make site-build` | 129 passed, 18 files |
| Projection parity | `PYTHONPATH=packages/agentbundle python3 -m agentbundle catalogue self-host --root . --check` | ok |

The `PYTHONPATH` prefix is load-bearing. A bare `python3 -m agentbundle`
resolves through whatever install is on PATH; run that way, `catalogue verify`
reported two `CAT-V-002` errors against `packs/core/seeds/`, a pack this slice
never touches. `pack_evals.py` is byte-identical between the installed and
worktree trees, so the behaviour and activation evidence above was graded by the
same code; the differing files are `lint.py`, `file_safety.py`,
`workspace_status_engine.py` and scaffold data, which is what produced the
phantom findings.

The reconciliation row is the gate that was missing when this record was first
written, and its absence is why two non-canonical registrations and a spec
status defect reached code review.

That row previously named `run_canonical_reconciliation` over `workspace.toml`
and reported three counts. It is corrected here because the invocation does not
reproduce: `agentbundle` exposes no `workspace-status` command, and calling the
internal directly with a parsed table skips path resolution, which reports 28
`missing_artifact` and 12 `provenance_mismatch` findings that do not exist. The
projection test is the instrument that actually owns the ratchet, so it is what
the row now names. The counts it replaced were not re-derivable from anything
committed.
