# Resolve-vs-surface disposition — work-item-capture

Opened at PLAN. Closed at DECIDE. One row per decision FEAT-0006 assigned to
this spec. `resolved` means a referent settled it; `surfaced` means it reaches
the human gate as an open choice.

| # | Decision | Disposition | Referent that settled it |
| --- | --- | --- | --- |
| 1 | Kinds and each kind's threshold | resolved, confirm at gate | Enum pin count superseded — see the verification ledger's site inventory + `additionalProperties: false` + `contract_version` const; the ladder's rung 1 |
| 2 | Required fields per kind | resolved | FEAT-0006 § Assumptions' four blockers; the schema's existing optional slots |
| 3 | Where validation runs, at what granularity | resolved, confirm at gate | FEAT-0006 § For the spec to decide; batch ceiling 12 in `knowledge_store.py` |
| 4 | What a refusal does | resolved | FEAT-0006 non-silent floor; CAP-0005 "no new store" |
| 5 | Operational definitions | resolved | FEAT-0006 § De-risk's kill condition wording |
| 6 | Trust boundary on a stored command | resolved, confirm at gate | Measured gap in `_validate_verification_route`; CAP-0005 § Boundary |
| 7 | Where validation rationale is surfaced | resolved | FEAT-0006 § Validation at capture, "the rationale travels with the item" |
| 8 | Reuse `lesson` or a new field | resolved | Measurement refutes the cheapness premise: any new kind already forces v2 |
| 9 | How the close-time admission rule branches | resolved | `work-loop/SKILL.md` § Capture learnings; CAT-S003 headroom |
| 10 | Compatibility with records already written | resolved | 6 observation files, all v1, 0 populating `verification_route` |
| 11 | Contract version boundary | resolved | `CONTRACT_VERSION` const in `project_knowledge.py:21` |

Three rows are marked **confirm at gate**: each is a defensible call the owner
may prefer to set differently, and each is named in the spec body at the point
it is made. None blocks planning.

## Surfaced at PLAN

None. No decision was left unresolved.

## Round 1 review — surfaced and resolved

Two pre-EXECUTE reviewers ran. The adversarial adjudication sustained 16
findings and refuted 1; the security adjudication classified `invalid`
(`indeterminate-present`) and stopped the round.

**Surfaced to the owner, and answered:**

| Question | Decision |
| --- | --- |
| Where the residual runner obligation lives | Placed on `work-item-promotion-handoff`; this spec stops claiming write-time settles execution |
| How read-only is enforced over argv | Refuse every element beginning with `-`; pin the `git` subcommand to `argv[1]` |
| What replaces the authorship self-attestation | Drop the refusal claim and its criterion; keep the field as a declaration and name the gap |

**Resolved without surfacing** — the remaining 13 sustained findings, each
repaired against re-derived evidence rather than the reviewer's number:

- The corpus claim was wrong. Re-derived: 102 records, not 6; two contracts,
  not one; 50 records carry no `contract_version` at all. D10, D11 and the
  version-selection criteria now bind only to the capture payload.
- The kind enum has nine pins, not eight. The ninth is the packaged `_data`
  mirror, gated by `check_contract_parity.py` under `make build-check`.
- `work-loop/SKILL.md` is 941 body lines, not 951, and `CAT-S003` fires as a
  warning above 500, so T6's original control was red before any edit.
- The false-or-already-fixed count required executing a stored command, which
  this spec forbids. Redefined against the freshness anchor alone.
- The 12-item cap's claimed coupling to the store's batch ceiling does not
  exist. Restated as a chosen provisional bound with a revision trigger.

## Open at approval

- Command provenance is not established at write time, by decision. Recorded
  in the spec's Assumptions as a named gap, not a control.
- The option rule may be too strict to be useful; the admissible command set
  is now four shapes. Recorded in the plan's Risks with the widening cost.

## Round 2 review — surfaced and resolved

Both adjudications classified `invalid` (`indeterminate-present`), each on a
different irreducible question. Neither was machine-checkable, so the bounded
evidence retry did not apply and both went to the owner.

**Surfaced, and answered:**

| Question | Decision |
| --- | --- |
| The runner obligation reached zero homes — the sibling disowned it | Amend `work-item-promotion-handoff` in this change; it now accepts the three runtime controls as criteria |
| FEAT-0006 puts the anchor-vs-file check in both the mechanical tier and the excluded freshness item | The tier is exactly two checks; anchor comparison stays the registered item's (§ D12) |

**Decided within the gate, and it changes what the owner saw at round 1.**
`git` is removed from the command allowlist. Under the no-options rule its
remaining surface is ref and object-id arguments, which no path rule reaches:
`git cat-file blob <oid>` reads a blob no longer in the working tree. Bounding
that means authoring a second trust boundary. `find` and `rg` go too, having no
useful option-free invocation. The allowlist is now `cat`, `wc`, `grep`, `ls`,
and no admitted command reads at an anchored revision — the `observed`/
`intended` substitute in § D2 is the designed fallback.

**Resolved without surfacing** — the remaining sustained findings:

- The privacy scan is an enumerated field list, so all seven `work_item`
  (narrowed to six on 2026-09-20: `significance` is a closed enum, so its
  case could not fail; the set is now derived from the schema)
  free-text fields were unscanned. One criterion now names the set, tested one
  field at a time so an omission reds the suite.
- `tests/roster/test_work_loop_lint_knowledge.py:496` matches kinds with
  `[a-z]+`, which cannot match `work-item`. T4 now owns the regex widening and
  both README copies.
- The plan added an `authorship` field § D6 had withdrawn. Dropped.
- "path-shaped element" was undecidable. Every element after `argv[0]` now
  satisfies `repositoryPath`.
- The inventory ground was false, the partition assumption was already settled
  in code, the corpus replay had two owners, and § D1 cited the wrong
  criterion position. All corrected.

## Open at approval

- Command provenance is not established at write time, by decision.
- The admissible command set is four shapes. If real defect records need more,
  widening means bounding `git`'s ref surface and a second security pass.

## Round 3 review — the approach changed

Both adjudications classified valid this round: security sustained 7 (2
blockers), adversarial sustained 16 (6 blockers). No indeterminates, so no
question went to the owner on the findings themselves.

The owner decision was about **method**, not content. Three rounds had produced
two systematic classes rather than convergence:

- **Class A — prose asserting validator behaviour.** Every security finding
  across three rounds was a claim about what a validator does, which nothing
  but a real validator can falsify.
- **Class B — derived facts duplicated across homes.** Citation drift from
  renumbering (most plan citations wrong), residue from the `git` removal, and
  live figures restated in three or four places. This class was produced *by*
  the repair rounds, so more rounds would make it worse.

**Decision: spike the validator, and give criteria stable identifiers.**

The spike is `notes/spike-argv-boundary.py`, kept as the derivation of § D6
cases rather than as shipping code. Running it found two rules that admitted
cases the spec claimed they refused:

- `["cat", ".env"]` was **admitted** — the `.git/`-only rule reached half the
  class. Replaced with a dot-leading-component rule.
- `["cat", "a' '-delete"]` was **admitted** — the metacharacter blocklist has
  no quote and no space, so naive shell re-serialisation splits it into two
  words with an option. Replaced with a positive character class, which also
  subsumes the newline and glob cases.

Neither was caught by three rounds of prose review. § D6's case table is now
the spike's real verdicts, and T3's tests are its rows.

Stable `AC-NNNN` identifiers replace positional citation everywhere, with the
never-renumber rule stated in the spec. That removes class B's mechanism
rather than its instances.

## Open at approval

- Command provenance is not established at write time, by decision.
- The admissible command set is four shapes: `cat`, `wc`, `ls` with a path,
  and `grep` with a pattern and a path. No anchored-revision read survives.
- The `grep` pattern must satisfy § D6's character class, so a pattern with a
  regex metacharacter is refused. Fixed-string search only.

## Round 5 and the split

Round 5 sustained 21 findings (8 security, 13 adversarial). Both adjudications
were valid — no indeterminates — so nothing went to the owner on the findings
themselves. The owner decision was again about method.

**Why the split.** Five rounds sustained 25, 23, 23, 27 and 21 findings. Flat,
not converging, and the share introduced by the previous round's repair was
rising. Round 5's own crop included a corrupted case table (my generator
mangled two rows containing shell quotes), a negative control contradicting the
task it was added to, and three stale counts — all introduced in round 4's
repair.

Roughly two thirds of the findings in rounds 3 to 5 were the stored-command
surface. Meanwhile the record contract's own central control went unnoticed for
five rounds: **nothing verified that the necessity razor refuses an item.**
FEAT-0006 calls that razor the test that keeps the well a well rather than a
heap, and a validator admitting everything that cleared the mechanical tier
passed all 42 criteria. The two surfaces were competing for attention, and the
one the intent treats as secondary was winning.

So the command surface became
`docs/specs/work-item-command-contract/spec.md` with its own loop and budget,
taking § D6, its case table, 13 criteria and the argv derivation. The residual
execution obligations followed it, which also removes the cross-spec coupling
that produced the zero-homes problem in round 2.

**What stayed and grew.** The record contract keeps 31 criteria and gains the
two the razor needed: `AC-0044` for a razor refusal and `AC-0045` for an unmet
shape threshold, both owned by T5 and both driven through the reasoning tier
rather than the field validator.

## Open at approval

- Command provenance is not established at write time. Recorded in the
  command contract's Assumptions.
- The false-or-already-fixed count is withdrawn to the freshness owner; both
  instruments that could derive it are closed to this spec.
- The 12-item cap is chosen, not observed.

## A method note worth keeping

Four defects in the command boundary were found only by running something,
never by reading: `find -delete`, the `.env` admission, the trailing-newline
anchor, and the partition allowlist. A fifth — the corrupted case table — was
found by running the derivation and diffing it against the spec. Prose about a
validator cannot be wrong until something executes it, and a generator's output
still needs checking against its input.

## Reversal: the split is undone (2026-09-20)

The command contract was split out to shrink the artifact under review, on the
hypothesis that size drove the finding count. Round 6 refuted it — the split
produced the worst round of the run (34 findings, 16 blockers, roughly 15 of
them caused by the split itself). The two halves are one seam: the schema, the
validator and the reason-code catalog are single artifacts that both halves
edit, so every edge between them had to be carried in prose that nothing
checks, and `loop-cohort.py` discards cross-plan `Depends on:` edges outright.

`docs/specs/work-item-command-contract/` is deleted. Its § D1 is the capture
spec's § D6, its § D2 folded into § D4, and its thirteen criteria are
`AC-0049`-`AC-0061`. The handoff spec's six residual controls (briefly seven on 2026-09-20, then returned to six when the prose obligation was withdrawn to a disclosed, unowned residual in § D10) now point at
§ D6. Nothing was lost: the directory was never committed, and its Testing
Strategy and Agent Rules entries were rewritten against the capture spec's own
sections rather than transplanted.

## Rounds 4 and 5 after the merge — the loop was stopped deliberately

Round 4 adjudicated 29 sustained, 0 refuted. Round 5 adjudicated 20 sustained
and 1 refuted, which the adjudicator collapsed to **15 distinct defects**
because several findings named one defect twice.

**Twelve of those fifteen were introduced by the round-4 repairs**, not found
for the first time. That is the measurement that ended the loop. Nine rounds
had held roughly 20-30 sustained findings each regardless of what changed, and
round 5 showed why: the substance — the decisions, the argv boundary, the case
table, the version model — had stopped moving, while prose *about* the prose
kept generating findings at the rate it was edited.

**Decision (owner, 2026-09-20): stop reviewing and gate.** The repair that
converges here is deletion, not another control.

**Withdrawn, because every self-policing criterion authored in this run was
itself a defect:**

- `AC-0063`, which was to lint the residual-obligation set for drift. It was
  unsatisfiable as specified (§ D10 had no enumerable member, the sibling's
  wording already differed), self-contradictory on its own list count, wired
  to no gate, and in breach of `tools/AGENTS.md`'s shared-driver rule. Six of
  the fifteen defects were its.
- `AC-0064`, which was to pin the character class over `grep`'s exempt slot.
  The § D6 row `["grep", "AKIA\n", "src/a.py"]` already witnesses that
  property, so it could not fail while the table passed. § D6 now states the
  coverage relation in prose instead.

**Returned to disclosed-and-unowned, having been briefly and partially owned:**

- *The dot-component rule's residual.* An untracked secret named without a
  leading dot — `config/prod.env`, `keys/id_rsa`, `credentials.json` — is
  admitted and clears the privacy scan. Round 4 routed this to obligation 1,
  post-resolution repository confinement, whose only criterion refuses a path
  resolving *outside* the repository. An in-repo untracked secret never does,
  so the residual had zero homes, not one.
- *The write-time prose controls.* Round 4 handed the sibling one obligation
  covering `AC-0035` alone. The write path's actual prose control is
  `assert_persistable_text`'s eight patterns plus `AC-0036`'s framing, so the
  repair re-established one of nine and read as coverage of the class. § D10
  now discloses all three controls as not re-established, and the sibling's
  owed trust-boundary decision names the residual it must settle.

Both reverted for the same reason: **a partial control reads as coverage and
invites the reader to stop, so it is worse than the honest disclosure it
replaced.**

## Open at approval

- Command provenance is not established at write time, by decision.
- The admissible command set is four shapes.
- **The dot-component rule reaches dot-leading names only.** An untracked
  secret under any other name is admitted. Accepted, unmitigated, disclosed in
  § D6.
- **No write-time prose control is re-established at execution.** A merged
  record's prose reaches a classifier and a durable artifact unscanned and
  unframed. Accepted, unmitigated, disclosed in § D10; the sibling's
  trust-boundary decision is where it gets settled.

## Rounds 6 and 7 — the strip is confirmed

Round 6, the first review of the stripped artifacts, returned **3 findings**
against round 5's 20, and the shape mattered more than the count: all three
were determined single-answer fixes. None asked for a new criterion, none was
a judgement call, and none was a control that could not fail. Every earlier
round produced at least two of those.

| Finding | What it was |
| --- | --- |
| Blocker | The withdrawal left a stale companion sentence. § D6's dot bullet still read "which is obligation 1's, not write time's" directly above the new paragraph saying the residual is unowned — so the paragraph that withdrew the routing still asserted it. |
| Concern | The dot residual reached no durable security documentation, while the prose residual did. T8's `security.md` check now requires both. |
| Nit | The enumeration was not reproducible. The alphabet was rendered in one backtick pair, making the space indistinguishable from a separator, so the stated 33 recomputes as **29** over the nine visible symbols. |

The nit is worth keeping as evidence: the reviewer recomputed the figure and
got a different number. Re-running it gives **29 without the space and 33
with** — the reviewer was right and the rendering was ambiguous. The
load-bearing half, that **zero** differing strings clear the character class,
holds under both readings, so the argument survived; only the figure needed
naming properly. The spec now lists all ten symbols individually and states
both counts.

Round 7 confirmed all three repairs and returned `Clean — ready to commit.`,
having independently reproduced the enumeration against the live schema and
re-derived the case table byte-for-byte.

**What the two rounds establish.** Rounds 4 and 5 averaged 25 sustained
findings with most caused by the previous round's repairs; rounds 6 and 7
returned 3 and 0. The variable that changed was not effort or attention but
the withdrawal of self-policing criteria and partial controls. The defects
were being generated by the repairs, and deletion was the repair that
converged.

## Round 8 — the security lens found a real hole, and it was closed

The adversarial lens returned clean at round 7. The security lens, which had
last run at round 5, was re-run before claiming `reviewers-clean` because
every change since round 5 had **removed** controls, and a stale pass is not
a confirmation. It returned 3 concerns and 2 nits, and the first was
substantive.

**`verification_route.path` escaped every § D6 path rule.** § D6 spent a
paragraph closing `.git/config`, `.env`, `.ssh/` and `.aws/` on argv
elements, while the sibling field of the same object was validated only by
`_expect_repo_path`. Running that function confirms it: it accepts `.env`,
`.git/config` and `.ssh/id_rsa`, refusing only traversal, absolute paths and
control characters. So `{"command": ["ls","docs"], "path": ".ssh/id_rsa"}`
was admitted, and the class the dot rule exists to refuse stayed reachable
through a field § D6 declared settled.

This corrects a claim made two rounds earlier. The stop-reviewing
recommendation rested on "the substance is sound, only the prose churns."
The substance had an unexamined hole, found on the seventh round by the lens
that had run least often. **The lesson is about lens coverage, not round
count:** rounds 6 and 7 were both adversarial, and no number of them would
have found this.

**Owner decision: close it, not disclose it.** A third residual would have
been consistent with the honest-disclosure principle, but one rule extension
actually closes the class, and a disclosed gap that is cheap to close is not
an honest trade. § D6's dot rule now binds the stored-path set as a whole,
defined once and including `verification_route.path`. `AC-0065` drives
`.ssh/id_rsa`, `.env` and `.git/config` and is **red against the current
validator**, so it can fail — the test that the two withdrawn criteria could
not pass.

The other four were repaired as stated: § D6 now defines the stored-path set
once and `AC-0013` dereferences it; `AC-0011` named `work_item.cited_artifact`
(later withdrawn — see the round 11 entry)
and requires the confined read `project_knowledge.py` already performs;
`AC-0057` states outright that its re-anchoring is unfalsifiable by the case
table and why; and the Durable Outputs architecture row names both residuals.

One open implementation choice is recorded on T3 rather than settled here:
`_expect_repo_path` has other callers — `scope`, `producer`, destination
hints — so widening it in place changes their behaviour too. T3 must record
whether it widens the shared predicate or routes `path` through the argv
predicate instead.

## Rounds 9-11 — § D12's input field, surfaced rather than invented

Three consecutive security rounds turned on one question: **which field do
§ D12's two mechanical checks read?** § D12 says "the cited artifact" — the
file the item proposes to repair — and the record contract has no field with
that meaning. Two attempts were made and both were wrong.

| Attempt | Shape | Why it failed |
| --- | --- | --- |
| Round 9 | Invented `work_item.cited_artifact` | Cost permanent v2 surface and re-opened three settled sets — the privacy-scan derivation, § D6's stored-path set, and a fail-open rule for its absence. Produced 8 findings across two rounds. |
| Round 11 | Reused `freshness_anchor.path` | Semantically wrong. § D5 contracts the anchor as the *provenance pin*, not the repair target, and a submitter chooses both independently — so the tier would refuse a frozen **anchor** and never a frozen **target**. Produced 8 more. |

`AC-0066`, added in round 11 to close the refusal-diagnostic oracle, was
withdrawn with them: no catalog code exists for a § D12 refusal and § D4 adds
none, so `AC-0037` forces a baseline code while `AC-0066` demanded equality
with nothing to be equal to — and the equality is unsatisfiable anyway while
the diagnostic populates `path`, since the four causes need four different
files. That is the third criterion authored in this run that could not work.

**Decision (owner): surface it, do not invent it.** § D12 now carries the
question as open at the gate, with both rejected candidates and their grounds
recorded so neither is retried. `AC-0010` and `AC-0011` are **blocked** until
it is settled. The decision also owes two things the attempts exposed: the
§ D4 catalog code a § D12 refusal returns, and whether the refusal causes must
be indistinguishable — `SAFE_DIAGNOSTIC_FIELDS` admits `path` and `line`, so
distinguishable refusals make the capture API an existence-and-shape oracle
over working-tree files the close output's reader may not hold.

**The pattern this run kept reproducing.** Every criterion authored to police
another criterion, and every field invented to satisfy an underspecified
check, became a defect: `AC-0063`, `AC-0064`, `AC-0066`, `cited_artifact`, and
the anchor binding. What converged was deletion and disclosure. Rounds that
removed something ended at 3 findings and then 0; rounds that added something
ended at 8.

## Open at approval

- Command provenance is not established at write time, by decision.
- The admissible command set is four shapes.
- **The dot-component rule reaches dot-leading names only** on both the argv
  elements and `verification_route.path`. An untracked secret under any other
  name is admitted. Accepted, unmitigated, disclosed in § D6.
- **No write-time prose control is re-established at execution.** Accepted,
  unmitigated, disclosed in § D10; the sibling's trust-boundary decision is
  where it gets settled.
- **§ D12's input field is undecided**, and with it the § D4 code a § D12
  refusal returns and the indistinguishability question. `AC-0010` and
  `AC-0011` are blocked on it. This is a decision for the gate, not a residual.

## Owner decision: build now, review later (2026-09-20)

The spec and plan are **approved by the owner** and EXECUTE starts without a
clean reviewer round. This is recorded because it is an owner decision, not a
reviewer verdict, and the loop's state should not imply otherwise.

**State at the decision.** The last security pass returned one blocker, now
repaired: the delivery's only fail-closed rule was specified as executable
assertions — a spy, a timeout, a per-item correspondence — against a surface
that is skill prose, where every existing test is a source-text assertion.
The repair moved the gate to the write path in `project_knowledge.py`: the
writer refuses any submission not carrying a recognized verdict for that item,
so an agent that skips or mis-configures the dispatch cannot produce the token
the writer demands. That repair has **not** been reviewed.

**What is verified.** 47 criteria, none blocked, all cited and owned by
exactly one task; no duplicate ids; waves clean with zero same-wave file
collisions; the argv case table byte-identical to its derivation at 46 rows;
spec metadata lint clean; base rebased onto origin/main with the four
load-bearing codebase measurements re-run and reproducing exactly.

**What is not.** The last repair round, and the four rounds before it, each
found a blocker in *how a control was specified for verification* rather than
in the spec's substance. The substance — the argv boundary, the version model,
the reason codes, the case table — has been stable for roughly twenty rounds.
The residual risk is concentrated in the two criteria written after the
mechanical-tier split, and it will surface at implementation rather than at
review.

**Two residuals ship accepted and unmitigated**, both disclosed in the spec:
the dot-component rule reaches dot-leading names only, and no write-time prose
control is re-established at execution.

## Known transient: the register has no slot for approved-and-unmerged

`tests/roster/test_workspace_status_projection.py::RepositoryHealthTests::test_no_fail_closed_lifecycle_findings`
reports an `impossible_transition` against this spec, and it is **correct**:
the spec is registered in `[backlog].open`, which holds work not yet started,
and its `Status:` is now `Approved`.

**Caused by this delivery**, not pre-existing. The entry was `Draft` in
`[backlog].open`, which is valid; approving the spec is what made the pairing
impossible. An implementer report called it pre-existing; that was wrong.

**Left open deliberately, 2026-09-20.** The register has no honest slot for
this state. The top-level `[backlog]` carries only `open`; an initiative's
work collections carry `active` and `shipped`; this spec is approved and
implemented but **not merged**, so none of the three is true. The three ways
to silence the gate now are: mark it shipped (false), revert its status to
draft (false), or invent an `active` list at the top level (a schema change
to a shared file, which is the repository owner's call and not this
delivery's).

**Resolves at merge.** When the branch lands the spec becomes `Shipped` and
the entry moves to a terminal collection, which is the transition
`[backlog].shipped` exists for elsewhere in this file. Until then the finding
is expected and this note is the record that it was seen, understood and
chosen rather than missed.

Anyone running the full roster suite before that merge will see one failure.
It is this one.
