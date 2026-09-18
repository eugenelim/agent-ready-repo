# Replay record: would the proposed check have prompted the examination?

Pre-authoring evidence, required before any normative guidance changes. The
kill condition is stated in the intake: kill or narrow if the replay finds no
material risk beyond what the existing assumptions protocol and step 5a already
direct. **Result: narrow, do not kill — narrowed across five rounds and an
extended sample to the consequence routing alone.** Every candidate
evidence-shape demand is cut; each cut is recorded below with the evidence that
defeated it. Earlier drafts of this record kept two, then one, of those demands;
those readings are superseded by § Verdict and are retained only where this
record says so explicitly.

## The baseline is current guidance, dated per delivery

Each existing catcher is dated below. § "Three of the seven sampled deliveries"
carries the measurement: three of the seven ran with all four in force, and the
four that did not are named there with what each predates. Nothing in this record
rests on a delivery for a catcher it predates:

| Existing catcher | Home | Shipped |
| --- | --- | --- |
| One targeted check per candidate assumption; Verified / Unverified split | `new-spec` step 3 | before 2026-08-29 |
| Cheapest disconfirming evidence before review | `new-spec` step 5a | 2026-08-29 (`2fb0a95c7`) |
| Grounded plan detail — discovery predicate, constraint, required outcome, verification mode | `new-spec` step 5 | before 2026-09-11 |
| A claim about what a check proves names the comparison its oracle performs | `new-spec` step 5 | 2026-09-11 (`95754ea45`) |
| Two traversal instruments — literal sweep plus semantic walk | `work-loop` DECIDE | 2026-09-13 (`91f45c796`) |
| Conditional domain-grounding | `work-loop` PLAN step 6 | shipped; scoped to *domain* claims, explicitly not machinery or library contracts |

**Per delivery, not blanket.** `91f45c796` landed 2026-09-13T22:21-05:00.
`pr-gate-suite-disposition` and `telemetry-sender-owns-its-configuration` both
merged 2026-09-17, so each ran with the whole set in force.
`loop-telemetry-export` merged 2026-09-15T08:33-05:00 and its ledger records work
from 2026-09-12, so its authoring and earliest rounds predate the DECIDE
traversal instruments; only its later rounds ran with them. Nothing below rests
on `loop-telemetry-export` for the traversal catcher, and the named target ran
with every catcher shipped.

Stating this as a blanket claim, which an earlier draft of this record did, is an
instance of the class this record argues for: a scope word wider than the work
that supports it. It is corrected here rather than defended.

## Sample

| Delivery | Rounds | Findings | Amendment evidence |
| --- | ---: | ---: | --- |
| `pr-gate-suite-disposition` (the named target) | 5 post-gates | 29 sustained, 0 refuted | 3 owner-authorised amendments |
| `telemetry-sender-owns-its-configuration` | 5 pre-approval + 6 post-gates | 27 + 28 | 1 amendment to a sibling spec; 2 amendments avoided by in-place correction |
| `loop-telemetry-export` | 3 implementation + 2 amendment + 1 security | 31 stated across rounds, plus 45 non-round implementation observations | Amendment 1, then narrowed because `approve-plan` refused; AC-0055 and T4 `Touches` **withdrawn** as unfixable |

All three record the same self-diagnosis. `pr-gate-suite-disposition`:
"Every one was a claim about scope or guarantee stated wider than the work
supported. The reviews did not find much wrong with the mechanism I built; they
found a great deal wrong with what I said about it."

## The six named probe targets for `pr-gate-suite-disposition`

| Probe target | Would the proposed wording have prompted the examination? | Verdict |
| --- | --- | --- |
| Single-line contracts of reused helpers | No, on re-examination in round 4. `plan.md:30` and `:165-166` name `_segments` and `_strip_inline_comment` at approval as helpers `line_targets` reuses, and that claim was **true** — `line_targets` is per-line, so the single-line contract was respected where the plan named it. The five round-3 defects belong to `loop_targets`, which `verification-ledger.md:532` shows was created as a repair for round 1's finding and did not exist at approval. Recording the helpers' line scope would still have helped the round-2 repairer, which is a benefit and not prevention of contract damage. | **cut — not earned** |
| The workflow shell loop behind the 21 false roster entries | No — and this row was sharpened twice before being cut. `verification-ledger.md:75-90` reports residuals for the workflow instrument itself: eleven newly-read files, "Exactly one shape misreports", with the declared false-positive residual and a measured instance. So a distribution was reported, a residual check ran on the Makefile instrument, *and* a residual check ran on the workflow instrument — and the 24 suites were still invisible, because every residual reported was a false **positive** while the 24 are false **negatives**. A third sharpening would bind residuals to both directions. It is not taken: three successive repairs each reaching one further instance is the calibration pattern `grounding-probe-extensions.md` refused, and the repeatedly-failing row is deleted rather than qualified again. | **cut — not earned** |
| YAML `if: false` | No, and the proposed rule says so. `if: false` loads as Boolean `False`; the defect had a direct test oracle (`if-false-is-conditional-by-presence`) and was found by one. Routing item (c) — a cheap reversible detail with a direct test oracle belongs in code, not design prose — places it exactly where it was in fact caught. | **already correctly placed; not claimed** |
| `paths-ignore` semantics | Already owned, and this row previously overclaimed by saying "caught twice over". Half was caught: step 3's YAML-parse probe grounded the filter semantics at spec time ("Both filter kinds are therefore conditional coverage", spec Assumptions). The other half was **missed** — the filter classification was tested behind the boundary that produces it, surviving the plan and found only at T7, where `paths-ignore` carried all 27 conditional entries. That defect is a claim about what a check proves, which step 5's oracle rule owns. Pointer only. | **already owned; the earlier "caught twice" was wrong** |
| Generated measurements | No. Every instance in the sample was discovered after the approval gate *and* is owned elsewhere: the `len(SUITE_DISPOSITION)` = 118 label defect is implementation telemetry; the stale multi-home figures are companion statements, which `work-loop` DECIDE's traversal instruments own; and a figure counting one unit while labelled another is a claim about what a comparison shows, which step 5's oracle rule owns. No measurement claim in the sample cost a contract amendment. Cut, like every other candidate shape. | **cut — not earned** |
| Over-broad sweep conclusions | No, on home rather than on substance. The overclaim is real and was the delivery's own headline finding, but it was authored in a post-gates DECIDE round, after the assumptions step had finished. `work-loop`'s DECIDE already requires both traversal instruments, re-run after every repair, "until the frontier is empty" — that is the comparator. "Name the surface your conclusion covered" adds a disclosure about a claim, not a check that the claim is true, and its home is where a sweep conclusion is written. | **cut — already owned, and the wrong home for step 3** |

## Every candidate shape across the other two deliveries, kept and cut alike

Corroboration for each candidate shape, kept so every cut shows the evidence it was cut against rather than only the conclusion.

**Reused-helper contract, plus one discriminating example — CUT. This section's instances are real; § Verdict records why they do not earn an obligation.**
`telemetry-sender`: a writer-less FIFO "opens *successfully* under `O_NONBLOCK`", so the brief's `open-error` mechanism did not work; `FILE_ATTRIBUTE_REPARSE_POINT` "is defined on every platform, so the case passed for a reason unrelated to the patch"; `monkeypatch.setattr(cfg, "stat", stat)` "rebinds the module to the real `stat` it already is — a no-op"; the `short-read` arm called unreachable was already reachable — "wrong, both of us".
`loop-telemetry-export`: `importlib.metadata.distribution("")` "raises `ValueError`, **not** `PackageNotFoundError`, confirmed directly rather than assumed"; `default_service_name()` returns `Path(profile_path).stem` — "`work-loop`, not `work-loop.toml`"; `resolve()` confined a file against its own directory, "which every absolute path satisfies"; `profile.py`'s own docstring said the opposite of the shipped disclosure. The discriminating-example half is named by `pr-gate-suite-disposition` itself: a first mutation case "used `for d in $(SUITES)`, which the path-shape filter excludes for an unrelated reason. `$(SUITE_DIR)/tests/` is the discriminating shape, because it contains a slash."

**Set, roster or classification — CUT, and the corroboration is why the cut is right.**
These instances are real and the shape reads compelling from them. They are
retained to show what the cut costs, not to argue against it: none of them
demonstrates that a residual report the author would actually have written would
have reached the defect, and the named target shows one that did not.
`loop-telemetry-export`: AC-0031 named four enumeration sites; five were required, then six — "A sixth site, and the one that mattered most" — and "the plan's own Risks section predicted this class and undercounted it". The four-versus-six count then turned up on a third and a fourth surface in two successive amendment rounds.
`telemetry-sender`: "The brief named two pre-existing survivors; there are three, plus one that hangs"; "one bump has five homes".

**Generated or compiled output — CUT. This section's earlier "earned on the bounded sample" reading is superseded by § Verdict.**
Stated plainly because no reviewer has raised it: the named target's probe for
this shape was `if: false`, which this record marks as not a catch. So this
shape rests entirely on the two other sampled deliveries and on committed
project knowledge, and not at all on `pr-gate-suite-disposition`. That is
weaker support than the reused-helper shape has, and the difference is recorded
rather than averaged away.
`loop-telemetry-export`: `[severity_map]` written as a section made `identity` and `allowlist` members of that table; AC-0054's third string "was introduced wrapped, and passed nothing"; the payload's `resource` block was never disclosed because "Every field inside a log record had been traced; nothing had traced what wraps them".
`telemetry-sender`: a stale untracked `.egg-info` on the suite's `pythonpath` reports `Version: 0.2.0`, "That is why the hardcoded-literal mutation for Fix 3 came out green as specified."
Independent corroboration from committed project knowledge, topic
`plan-a-corpus-change-against-the-projected-tree-not-the-authored-one`: "Two
owner-authorized amendments in one delivery came from the same blind spot: the
anchor-test sweep checked digests and counts over authored sources, while two
separate shipped guards scan the compiled projection."

**Generated measurement — CUT, and every instance names its real owner.**
Retained to show the cut's basis: each of these was found after the gate, and
each belongs to DECIDE's companion sweep or to step 5's oracle rule.
`telemetry-sender`: `addopts = "-q"` plus a command-line `-q` doubles to `-qq` and suppresses pytest's summary line — "Every exporter-suite run recorded earlier in this ledger was read from its progress dots, not from a count"; and zsh's 1-indexed `PIPESTATUS` reported `EXIT=0` for a run make had failed.
`loop-telemetry-export`: mypy "went on reporting 'Success: no issues found in 139 source files' — the same count as before the change. The package was not checked at all"; suite size 279, not the brief's 410; the core version moved 2.25.27 → 2.27.0 → 2.26.5 across five surfaces, "the fifth was found by sweeping rather than by remembering".

**What a check proves — already owned by step 5's oracle rule, and it still fired.**
`loop-telemetry-export`: "**A literal-string criterion cannot see a wrong sentence**" — AC-0020 checks three literal strings, "all of which were present through all four wrong drafts"; "**Three controls could not fail**".
`telemetry-sender`: a guard "carried the message *'a hardcoded literal must not be able to satisfy this'* while being exactly that"; an expected severity derived from the profile's own `severity_map`, which the encoder also reads, so the mutation "moved both sides together and **survived**"; "A green standalone guard is ambiguous between 'passed' and 'never ran'."
This is the existing rule's own subject, and the existing rule lives in step 5,
reachable only while authoring the plan. The delta is a routing reference from
step 3, where the claim is first written — not a second copy of the rule.

**Sweep or completeness — CUT, owned by `work-loop` DECIDE.**
These instances are real and all three deliveries show them. They are retained
because they are the evidence that DECIDE's instruments are the right owner and
that the assumptions step is the wrong home, not as support for an obligation
there.
`telemetry-sender`: escaping-control coverage restated 1 → 7 → 9 → 10 of ten sites, having "read as covering 'path escaping'"; "Every one of the five review rounds has found exactly one stale companion statement, each time in prose beside a change rather than in the change."
`loop-telemetry-export`: "**The blocker is the partial-surface class, inside the repair for it.** The walk was performed on the spec and on the task, and not on the plan's own summary table"; and a wiring sweep "reported fifteen defects and had run the wrong suite" — "Nothing in the output says 'I ran a different suite.'"

## Timing: why the routing half is the load-bearing half

The proposed routing rule — a claim that could change intent, acceptance
criteria, architecture, a dependency choice, a security or data boundary, the
task graph, or a verification mechanism is spiked *before* approval — is
answerable from the sample, and the answer is not a preference.

`loop-telemetry-export` records the consequence in its own words: "An amendment
that corrects a task's contract has to happen before that task's completion is
recorded, or not at all… **A contract error found by doing the work may be
unfixable in the contract.**" Amendment 1 was narrowed because `approve-plan`
refused with `completed task section changed: T2, T4`; T4's `Touches`
correction was **withdrawn** because T4 was complete and frozen, and **AC-0055
was withdrawn** because "a criterion needs a task entry, and its only honest
home is T2, which is frozen". AC-0055's identifier had reached pushed history,
so it is now carried as retired though it was never approved.
`pr-gate-suite-disposition` hit the same refusal: "`approve-plan` refused the
amended baseline with *completed task section changed*."

Both are claim-shaped defects discovered after the gate that could no longer be
repaired at the contract layer. Every finding in all three ledgers is recorded
after the approval gate; the only pre-approval corrections in the sample came
from reviewers, not from the author's own evidence step.

## What the existing guidance already catches, stated so nothing is renamed

| Risk | Existing owner | Proposed rule's action |
| --- | --- | --- |
| A criterion claiming live behaviour with no probe | step 5a; rubric class 3 | none — untouched |
| A claim about what a check proves | step 5, oracle-comparison rule | routing reference from step 3; no second copy |
| An ungrounded seam in an unstarted task | step 5, "Grounded plan detail" (discovery predicate, constraint, required outcome, verification mode) | one added field — a **kill condition** — and nothing else |
| Repeated text and paraphrased companions after a repair | `work-loop` DECIDE, two traversal instruments | none — untouched; the proposed rule bounds a *conclusion*, which DECIDE does not |
| An ungrounded business-domain claim | `work-loop` PLAN step 6, conditional domain-grounding | none — that hook is scoped to domain claims and stays so |
| A cheap reversible detail with a direct test oracle | code | explicit routing *away* from design prose |

## Extended sample, 2026-09-17 — seven deliveries

Owner instruction after round 4: extend the sample. Four deliveries were added —
`agent-skill-engineering-subagent-and-plugin-concepts`,
`agent-skill-engineering-corpus`, `construction-time-razor`, and
`work-loop-in-process-guards` — replayed under the same method by two Codex
investigators and two subagents, with a fifth agent dating every delivery against
every catcher.

### The discriminator this record adopted in round 3 is not testable, and is withdrawn

Round 3 adopted a test: a shape earns its place if a claim of that shape was
written into a `spec.md` or `plan.md` that then froze on it. Dating the extended
sample established that **no plan in any of the five deliveries searched records
an owner-approval line**. Both Codex investigators reached the same conclusion
independently and one returned `VERDICT: indeterminate — no line records owner
approval of the construction-time-razor spec and plan`. The corpus delivery's
boundary had to be reconstructed from a revision-8 `approve-plan` refusal; the
in-process-guards boundary from a sentence in an implementation log.

So the approval anchor is not an artifact fact in this repository, and the
round-3 discriminator could never have been applied to the corpus. It is
withdrawn. The cuts it was used to justify are re-grounded below on **ownership
and home**, which are testable, and one of them is re-opened.

### Three of the seven sampled deliveries ran with every catcher in force

| Delivery | Start proxy | `2fb0a95c7` 08-29 | `e0a53883e` 08-30 | `95754ea45` 09-11 | `91f45c796` 09-13 |
| --- | --- | :--: | :--: | :--: | :--: |
| `work-loop-in-process-guards` | 2026-08-17 | no | no | no | no |
| `agent-skill-engineering-corpus` | 2026-08-28 | straddle | straddle | no | no |
| `agent-skill-engineering-subagent-and-plugin-concepts` | 2026-09-09 | yes | yes | no | no |
| `loop-telemetry-export` | 2026-09-13 | yes | yes | yes | straddle |
| `telemetry-sender-owns-its-configuration` | 2026-09-17 | yes | yes | yes | yes |
| `pr-gate-suite-disposition` | 2026-09-17 | yes | yes | yes | yes |
| `construction-time-razor` | 2026-09-17 | yes | yes | yes | yes |

Seven rows, one per sampled delivery. Start proxy is each delivery's first commit
adding its `spec.md`; real work began earlier, so every "yes" is the weaker claim
and every straddle may be wider. `jsonl-otlp-exporter` was dated alongside these
but is **not** in the sample and carries no weight here.

Three deliveries — `telemetry-sender-owns-its-configuration`,
`pr-gate-suite-disposition`, and `construction-time-razor` — ran with all four
catchers shipped. An earlier draft of this record said one, which understated its
own table; the table is the measurement and the sentence was wrong. This
table is the reason the extended sample cannot rescue a cut shape: the two
deliveries with the richest set-membership and sweep-scope damage —
`work-loop-in-process-guards` with nine membership instances and three
sweep-scope instances, and `agent-skill-engineering-corpus` with its eighth
partial edit — both **predate the catchers those shapes would supplement**. Their
evidence cannot show the shipped catchers insufficient, because the shipped
catchers were not there.

### Every evidence-shape demand is cut, and `generated-output` is cut on its own terms

`agent-skill-engineering-subagent-and-plugin-concepts` was added specifically to
earn `generated-output`, because a committed project-knowledge topic sourced from
its plan carries the only two-amendment evidence for that shape. It does not earn
it. Its first amendment's stated reason is a wave-ordering and task-boundary
problem: "Not recompiling fails the doctrine projection… Recompiling passes it but
moves `source_digest` and fails the two recorded-run digest assertions until the
retrieval re-measurement, which the approved cut places three waves later." Its
second amendment's frozen text "required content in an authored profile; it did
not make a claim about the generated tree", and the investigator's conclusion is
decisive on scope: "Counting it would broaden the proposed obligation from claims
about generated artifacts to every authored source that will later be projected.
The supplied obligation does not state that broader rule."

`agent-skill-engineering-corpus` returns the same answer from four independent
generated-output instances: "none of the three amendments recorded in section 2
traces to a bucket-(c) claim."

## Verdict

**Ship the consequence routing. Kill every evidence-shape demand.**

### What the routing rule earns, across five of seven deliveries

The freeze-time mechanism is the one finding the corpus states over and over, in
its own words rather than mine.

`work-loop-in-process-guards` states it as a design finding and says so:
"**Worth folding back into the work-loop itself.** This is the second time the
same friction bit this run, and it is a design finding, not an accident… the
tooling forbids exactly the mid-execution amendment the contract invites, and the
only sanctioned escape is a destructive reset that clears the retry counters. **A
correction found during review — a wrong count, a stale citation — is the ordinary
case, not an exceptional one.**" Eight amendments were queued for the human gate
rather than applied; one correction was "Applied once, then reverted to restore
hash currency"; and T7's `Touches:` field still states a false two-file
version-bump surface in four places of the shipped contract, with no amendment
covering it.

`agent-skill-engineering-corpus`: an `approve-plan` refusal whose "recovery steps
scoped to the second were applied to the first — preserving the hashes but not the
gates"; `contract-amendment` unavailable because no task had run, forcing a reset
of both state machines; a pin "unsatisfiable without writing a false count back
into a completed section, and **no re-pin primitive exists**"; and a deliberate
acceptance-criterion numbering gap, because "renumbering it to AC17 would edit T3,
a completed task section, which is the rule that already cost this change a cohort
replay."

`agent-skill-engineering-subagent-and-plugin-concepts`: amendment 1 is named as
consequence routing outright — "coupled gate consequences must be resolved at the
task boundary where they first become unavoidable."

`loop-telemetry-export`: AC-0055 and T4's `Touches` both withdrawn as unfixable.
`pr-gate-suite-disposition`: the same `approve-plan` refusal.

### Of the three fully-baselined deliveries, the one replayed against this rule corroborates it in both directions

`construction-time-razor` is one of the three deliveries that ran with all four
catchers shipped, the only one of those three replayed against the routing rule,
and the closest analogue to this change — it also amended authoring prose in this
pack.

*For the rule:* "every recorded contract error was discoverable before approval.
None required the completed delivery to reveal it."

*Against over-firing, which is the rule's own risk:* its required-construction
control was rebuilt and measured — "One run built the named class and module;
another built no new module. Both satisfied the pre-existing consumer's `render`
protocol and both passed" — so "A pre-approval spike intended to select the class,
module, or helper shape would therefore have been wasted design work. The exact
local method was cheap, reversible, and had a direct test oracle; leaving it to
implementation was correct." That is the third destination validated by
measurement rather than asserted.

*The exact delta over shipped guidance, which is what stops this being a rename:*
the existing pre-review step "does not, however, require a check for every
unresolved consequence-bearing claim; it requires 'one throwaway check' of the
load-bearing mechanism. This delivery could comply with it — and did — while
leaving the inadequate-candidate, refusal-status, schema-field, and
required-construction claims unresolved. The grounded-detail rule also lacks the
proposed kill condition and does not classify claims by whether they could change
intent, architecture, dependencies, boundaries, task graph, or verification."

### The honest limits

- **n=3 on the full baseline, and only one of those three was replayed against
  the routing rule.** `telemetry-sender-owns-its-configuration`,
  `pr-gate-suite-disposition`, and `construction-time-razor` all ran with every
  catcher, but only `construction-time-razor` was examined for what the routing
  rule would have changed; the other two were replayed for evidence shapes. The
  freeze-damage evidence spans five deliveries, three of which predate one or
  more catchers, so those three establish that the damage is real and recurrent
  rather than that today's guidance fails to prevent it.
- **No approval anchor is recorded anywhere**, so no future replay of this kind
  can do better without that datum. Recording it is a cheap change and is named
  as a follow-on rather than smuggled into this one.
- **Seven claims of this record's own were refuted across four rounds**, and the
  discriminator withdrawn above is the eighth. The rounds found little wrong with
  the idea and a great deal wrong with the scope claimed for it.

### Out of scope, and routed rather than absorbed

`work-loop-in-process-guards` and `agent-skill-engineering-corpus` jointly
establish a better-evidenced finding that is **not** this slice: the plan contract
invites mid-execution amendment while the tooling forbids it, and the only
sanctioned escape is destructive. That is a post-gate replanning channel — S2's
subject, excluded here by the intake's own scope boundary — and it is recorded
for that owner, not built.
