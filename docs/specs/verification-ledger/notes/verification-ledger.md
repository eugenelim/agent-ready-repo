# Verification ledger

Observations produced by executing this delivery. The approved `spec.md` and
`plan.md` name the obligations; this file records what was observed while
discharging them. Neither approved artifact is edited to hold any of it — which
is the contract this delivery ships.

Run `cc200010-b3b1-43ca-a3f4-05e0f3301623`, code mode.
`approved_spec_hash=e57bec981b37…`, `approved_plan_hash=8840dc2e1241…`.

## The first guard was inadequate, and eight green proofs hid it

**Superseded — read this before the table below.** The first version of
`tests/roster/test_verification_ledger_contract.py` asserted only that each
governing source said substantive edits end at approval. It asserted **nothing**
about the ledger destination — the delivery's entire point. Independent quality
review raised it as a Blocker and I confirmed it by experiment: deleting the
ledger-routing clause from the convention seed, from the plan template, or from
the pre-execute note each left the guard at `4 passed`.

The eight proofs in the table below were all *replacements* of the mutability
clause, so not one of them could see a *deletion* of the routing clause. Eight
green mutations produced confidence that was not earned. That is the failure
mode this repository calls a control that cannot fail, and it survived my own
review because I checked that the mutations reddened rather than asking what
class of regression they could not reach.

Two further defects, both confirmed by experiment on the real tree:

- **Under-broad.** Appending "A maintainer may revise task text after approval
  when execution reveals new facts" — a licence the hash guard genuinely
  refuses — left the guard green, because its negative check keyed on the token
  `` `Executing` `` rather than on the permission.
- **Over-broad.** Appending "`Executing` remains a legal status after approval,
  but a substantive edit is still refused" — a *correct* clarification — turned
  it red, because the check matched mere co-occurrence of `edit` and
  `` `Executing` `` under `DOTALL`.

Quality review raised nine further defects on the same file: a template region
truncated at its first HTML comment so two of three template edits were
unguarded; `_between` failing open to end-of-file on a missing terminator, which
made the `state-schema.md` region overrun by 69 lines; whitespace normalisation
that left blockquote markers in place, so a pure re-wrap reddened the suite and
forced clauses to be split into separately satisfiable fragments; a shared
failure message that named neither file nor clause and was emitted for two
opposite causes; and a hash-pin "proof" that was nine exact source substrings of
`_loop_guards.py` rather than its behaviour.

### What replaced it

The guard now asserts **two independently killable halves per source** — the
pinned clause and the routing clause — loads `_loop_guards.py` and **exercises**
it (the exemption does not move the digest; a substantive edit does) instead of
pinning its source text, extracts regions by heading, bold paragraph lead, or
whole file with every shape failing loudly rather than widening, strips
blockquote and list leaders before comparing so a re-wrap is invisible, and
names the file and the failing clause in every message.

### The rewrite was still hollow — a second review round

An independent re-review of the rewrite returned **GUARD STILL HOLLOW** with
four Blockers. Each was reproduced on the real tree before being fixed, and all
four passed the guard as shipped:

| Hole | Probe | Before |
| --- | --- | --- |
| `SOURCES` both defined and drove the clause tests, so deleting a row removed its own assertions | delete the `state-schema.md` row | `8 passed` |
| Routing checks accepted any plausible phrasing, not a destination | point the convention at `notes/execution-log.md` | `8 passed` |
| The status test asserted `"Executing"` appeared in the private `_LEGAL_AFTER_APPROVAL` table, never calling the guard | — | proves a string, not behaviour |
| The release check took the first `[core]` heading *anywhere* | insert a heading between `[Unreleased]` and it | `8 passed` |

Fixes: AC3's six paths are pinned independently of the loop that iterates them;
every routing surface must name the canonical path or a resolvable pointer to
the section owning it, and the convention seed now *names*
`notes/verification-ledger.md` rather than describing it; the status test calls
`assert_status_legal` on `tmp_path` fixtures (admits `Executing`, refuses a
regressed `Drafting`) so this delivery's own artifacts cannot make it pass or
fail for an unrelated reason; and the release check reads the first versioned
heading after `[Unreleased]` and requires it to be core at the shipped version.

### I destroyed my own uncommitted fixes with `git checkout`

Worth recording because the instruction that prevents it was explicit. The
mutation harness restores each mutated file with `git checkout -- <file>`. The
first attempt at these four fixes was **uncommitted**, and one probe mutated
the guard file itself — so the restore reverted the working tree to the last
commit and silently discarded every fix. The symptom was subtle: subsequent
probes reported `8 passed` where the fixed file has 12 tests, and the count was
the only signal that the file under test was no longer the file I had written.

The fixes were redone and **committed before any probe ran**. A restore-by-
checkout harness is only safe against committed state; against uncommitted work
it is a delete.

### Coverage after both rounds

| Class | Count | Result |
| --- | --- | --- |
| Routing-clause deletion (round-1 blind spot) | 5 | all redden |
| Retired-licence replacement | 7 | all redden |
| Closed-set membership deletion (round-2 blind spot) | 1 | reddens |
| Ledger destination diverging from canonical | 1 | reddens |
| Changelog adjacency broken | 2 | both redden |
| False-positive probes that must stay green | 2 | both green |
| **Known limit — additive licence in new wording** | 1 | **still passes** |

Sixteen killing mutations across six classes, two false-positive probes, one
documented limit. Two independent review rounds each found a class the previous
round's proofs could not reach; both are recorded above rather than folded into
a clean-looking total.

The known limit is deliberate and documented in the module. `RETIRED_LICENCES`
is a bounded regression backstop against the specific wordings that caused this
defect, not a proof that no new permission can be phrased. Proving prose free of
an arbitrary permission is not mechanisable; claiming otherwise would rebuild
the same false confidence in a new place. AC3 claims only reversion detection,
which is what the sixteen killing mutations establish.

## The superseded eight proofs, kept for the record

The plan requires eight killing mutations against
`tests/roster/test_verification_ledger_contract.py`. Each was applied to the
committed tree at `cb2648b9b`, measured, then reverted **by editing the file
back** — never `git checkout`, `reset`, or `stash`. Unmutated baseline: `4
passed`.

| # | Mutation | Observed | Assertion that failed |
| --- | --- | --- | --- |
| 1 | convention seed: restore the `Drafting` **or** `Executing` licence | `1 failed, 3 passed` | `test_closed_rule_sources_reject_executing_time_substantive_edits` |
| 2 | plan template: same licence restored in the `Plan contract` blockquote | `1 failed, 3 passed` | same |
| 3 | lifecycle reference: replace "retain obligations only" with an `Executing` edit permission | `1 failed, 3 passed` | same |
| 4 | explanation guide: re-point the clause at `Executing` | `1 failed, 3 passed` | same |
| 5 | `pre-execute-review.md`: replace "immutable in substance" with "may change while `Executing`" | `1 failed, 3 passed` | same |
| 6 | `state-schema.md`: replace "Everything else stays pinned" with a task-text licence | `1 failed, 3 passed` | same |
| 7 | how-to: delete the ledger clause | `1 failed, 3 passed` | `test_how_to_keeps_immutability_and_ledger_destination` |
| 8 | `work-loop/SKILL.md`: replace the pointer with prose | `1 failed, 3 passed` | `test_work_loop_uses_a_pointer_without_a_second_ledger_rule` |

Mutation 6 is the one the guard would not have had before review round 3 found
`state-schema.md`. It confirms the sixth source is genuinely load-bearing
rather than defensive: without its coverage, the most precise statement of the
boundary in the repository could be reverted while every other mutation still
reddened.

### A contaminated measurement, and the correction

The first pass recorded **M8 as `2 failed, 2 passed`**. That was wrong, and the
cause was in the harness rather than the guard: M7's restore step passed an
empty string as the search term, and `str.replace("", x, 1)` **inserts at
position 0** instead of restoring in place. So the how-to was left with the
clause prepended ahead of its `---` frontmatter opener and still missing from
its mid-flight paragraph. M8 then ran against that damaged tree and its
inflated count included M7's still-failing test.

Both were re-measured in isolation after a verified byte-exact restore:
M7 → `1 failed` (`test_how_to_keeps_immutability_and_ledger_destination`),
M8 → `1 failed` (`test_work_loop_uses_a_pointer_without_a_second_ledger_rule`).
The table above carries the isolated figures.

Two things this cost, worth recording because neither is visible from a green
run: an unrestored mutation makes every later mutation's count lie, and a
harness that reports "RESTORED" from its own replace call is asserting nothing —
only `git diff --quiet` against the committed blob established restoration.

## The status-token exemption, observed rather than assumed

Writing `Status: Implementing` into the pinned `spec.md` before the first
implementation write left both guards green:

```
loop-cohort: schedule check-current OK for verification-ledger
loop-cohort: plan check-current OK for verification-ledger
```

That is the exemption `state-schema.md` § *What the pin covers* describes,
demonstrated on this delivery's own artifact.

## T1 deviation: guidance restored that the task did not ask to change

T1's brief asked for the false licence to be corrected in the convention seed.
The first implementation also deleted the adjacent `**Lifecycle:**` paragraph
and renamed the section heading from *…when the spec ships* to *…when the plan
is approved*.

Both were reverted, because three frozen specs cite that section for the
ship-time freeze it asserted — `thirty-day-cooling-and-retirement/spec.md:310`,
`cooling-scope-closure/spec.md:427`,
`cooling-untrusted-input-refusals/spec.md:408` — and
`thirty-day-cooling-and-retirement/notes/resolve-vs-surface.md:11` records an
owner decision of 2026-08-27 that turned on it. The rename also left a dangling
back-reference in § 4.

The underlying defect was conflating two independent facts. Both are now
stated: the pair is **pinned in substance** at plan approval (protecting the
contract during the build) and the directory is **frozen** when the spec ships
(protecting the record afterwards). The heading is unchanged, so the three
citations still resolve.

## Measured surfaces at completion

- `packs/core/.apm/skills/work-loop/SKILL.md`: **834** lines against the
  1000-line ceiling at `tests/roster/test_wave4_durable_outputs_and_release.py:99`
  (was 832; +2 for the pointer). Lifecycle-reference link count **5** against a
  floor of 3.
- `docs/CONVENTIONS.md` is byte-identical to `packs/core/seeds/docs/CONVENTIONS.md`
  after `FORCE=1 make build-self`, which
  `tests/roster/test_shaping_review_documentation_contract.py:53` asserts exactly.

## Pre-existing failure, unchanged by this delivery

`packs/core/tests/skills/new-spec/test_acceptance_criteria_discipline.py::test_spec_review_accepts_only_exact_clean_before_adjudication`
fails on a clean `origin/main` worktree and still fails here, with the same
`1 failed, 52 passed` count before and after every task. It asserts a phrase in
`packs/core/.apm/skills/new-spec/SKILL.md`, which this delivery does not touch.
Registered as `pre-existing-new-spec-exact-clean-phrase-drift`.

## Round 3: a false-positive sweep, and the terminator that was too eager

Recorded late — commit `126eba299` shipped this fix but its evidence lived only
in the commit message, which is exactly the gap this delivery exists to close.

The guard had 16 confirmed killing mutations against only 2 confirmed
innocent-edit probes. That imbalance is itself a finding: a guard that cries
wolf gets weakened by the next maintainer, which is how this defect class
returns. Sweeping for false positives found one.

`_section`'s bold-lead terminator treated **any** line-initial `**` as a
paragraph lead. Re-wrapping `state-schema.md` so that the inline span
`**Canonical form**` began a line truncated the region before "Everything else
stays pinned" and reddened the suite on an edit that changed no meaning. A real
bold paragraph lead in that file is blank-line separated, so the terminator now
requires `\n\n`. Verified in both directions: the re-wrap stays green, an
inserted bold-lead paragraph still terminates the region, and the R6 killing
mutation still reddens — the widened boundary does not let a deleted clause be
satisfied from neighbouring prose.

## Round 4: the guard read one region of the rule owner and none of the rest

Two independent reviews, adversarial and repo-wide investigation. Baseline
before any fix: `12 passed`.

The convention seed states the post-approval boundary **three times**: in the
section the guard anchors at (`:119-142`), again at `:402` where `plan.md` is
introduced, and again in the `:417` Lifecycle paragraph. The first region ends
at `### Superseding a frozen document` on `:143`, so the other two were unread.

Measured, not argued: restoring the literal first entry of `RETIRED_LICENCES` —
`` `Drafting` or `Executing` `` — into the rule owner itself at `:402` left the
suite at **`12 passed`**. The delivery's own canonical source could be reverted
without the guard noticing, which is precisely what AC3 claims to detect.

Two further holes from the same root premise — the guard pins one sentence, so a
restatement or truncation elsewhere in an enumerated file escapes it:

- the lifecycle reference's no-amendment half was unasserted, so truncating
  "The ledger is not hash-pinned, so recording an observation there needs no
  amendment to either approved artifact." to its first clause stayed green
  while AC1's guarantee disappeared;
- AC2 requires `work-loop/SKILL.md` to state no rule of its own, but Step 2 was
  checked only for the pointer and for retired licences, so a *correct*
  restatement of the rule passed.

### The fix reopened the round-2 defect one level down

Letting one path own several regions made the closure test compare **distinct
paths**. Deleting one of the two new seed rows therefore left the path tuple
unchanged and its clauses unasserted, at `12 passed`. That is the round-2
finding — a table that both defines and drives its own assertions — recurring
at the region level. `AC3_REQUIRED_REGIONS` now enumerates the regions too.

### Proofs at commit `3c06fdca9`

Unmutated baseline `12 passed`. Each mutation applied alone to the committed
tree, restored by writing back a **verbatim byte snapshot**, and every
restoration verified with `git diff --quiet` against the committed blob — never
by the harness's own report.

| # | Region | Mutation | Observed | Test that failed |
| --- | --- | --- | --- | --- |
| M1 | seed `:402` | restore the `Drafting` or `Executing` licence | `2 failed, 10 passed` | `..._states_the_pinned_half` + `..._carries_a_retired_edit_licence` |
| M2 | seed `:402` | delete the pinned clause | `1 failed, 11 passed` | `..._states_the_pinned_half` |
| M3 | seed `:417` | licence the in-flight correction | `1 failed, 11 passed` | `..._states_the_pinned_half` |
| M4 | seed `:417` | delete the routing clause | `1 failed, 11 passed` | `..._routes_observations_to_the_ledger` |
| M5 | lifecycle ref | truncate the no-amendment half | `1 failed, 11 passed` | `..._routes_observations_to_the_ledger` |
| M6 | `SKILL.md` Step 2 | add a *correct* rule restatement | `1 failed, 11 passed` | `..._points_at_the_procedure_without_restating_it` |
| M7 | the guard itself | delete one of the two new seed regions | `1 failed, 11 passed` | `..._keeps_every_member_ac3_names` |
| P1 | seed `:402` | re-wrap, no meaning change | `12 passed` | — stays green |
| P2 | seed `:417` | re-wrap, no meaning change | `12 passed` | — stays green |
| P3 | `SKILL.md` Step 2 | append an unrelated sentence | `12 passed` | — stays green |

Before the fix, M1 returned `12 passed`. Only M1-M7 were re-run at this
revision; the sixteen earlier proofs are not re-asserted here as fresh, and the
cumulative claim is 23 killing-mutation runs and 5 innocent-edit probes across
all rounds, not one campaign.

### The harness reproduced the bug this file already warned about

For the two deletion mutations the replacement text was `""`, so restoring with
`replace(new, old, 1)` became `replace("", old, 1)` and **prepended** the clause
ahead of the seed's `# Repository Conventions` heading — the same defect
recorded above for M7 in round 1, in a harness written after reading that
warning. The `git diff --quiet` check caught it and halted the run. Guarding
`old == ""` is not enough; the harness now snapshots bytes and writes them back
verbatim, which cannot express the fault at all.

## Round 5: the round-4 fix introduced three defects of its own

Two further independent reviews, adversarial and spec-drift. All five
falsifiable findings were reproduced on the real tree before being accepted.

| # | Finding | Observed | Attribution |
| --- | --- | --- | --- |
| V1 | the destination test concatenates every region of one path, so the `:417` paragraph can name `notes/execution-log.md` and be satisfied by `:128`'s canonical path | `12 passed` | **(b)** round-4 fix |
| V2 | the plan template is one whole-file region, so its `Done when:` rule can route to a wrong path while the top-of-file Plan contract satisfies the destination check | `12 passed` | (a) pre-existing |
| V3 | `change substantively` in `RESTATED_RULE_MARKERS` fires on ordinary Step 2 prose that grants no edit permission | `1 failed, 11 passed` | **(b)** round-4 fix |
| V4 | the new-spec re-pin dropped the literal `` `Clean — ready to commit.` `` sentinel, so the clean-result contract can change unnoticed | `32 passed` | **(b)** commit `16102892a` |
| V5 | the template's `## Changelog` rule — corrected by this delivery — is not independently guarded; reverting it to the `origin/main` wording reddens nothing | `12 passed` | (a) pre-existing |

Three of the five are fix-induced. Under this repository's review protocol a
(b)-dominant round is a stop condition, not another repair cycle, so the ship
sequence halted here with the acceptance criteria unticked and nothing pushed.

V3 is the round-3 lesson recurring: a marker list broad enough to catch a
restatement is also broad enough to reject correct prose. V1 is the round-4
lesson recurring: widening a comparison to accommodate one source weakens it
for every source sharing that path.

The transferable finding, now observed five rounds running: verifying that
mutations redden is not the same as knowing which class they cannot reach, and
each repair that widens a region or a marker list creates a new class. Pinning
exact sentences across many prose regions has produced defects at roughly the
rate the reviews close them.

## AC3 was not tickable at the stop point

The spec-drift review returned AC1 **DISCHARGED**, AC2 **DISCHARGED**,
AC4 **DISCHARGED**, AC3 **NOT DISCHARGED**, for two reasons that differ in kind.

V5 is a plain guard gap and is fixable by a test. The second is not: AC3's
closing sentence — "a seventh surface stating the boundary is a defect in this
criterion, not an omission the guard tolerates" — is unqualified, and accepted
decision records state the same boundary (`docs/rfc/0099…:501`,
`docs/adr/0099…:52`, `docs/rfc/0096…:365`, `docs/adr/0061…:12`). Editing
`RFC-0099` to licence in-place edits leaves the guard green, because it never
reads that path.

The reviewer's argument that the public how-to also contradicts the closed set
is **refuted**: AC3's next sentence gives the how-to its own killing mutation
explicitly, so it is accounted for rather than omitted.

Whether governance history belongs inside AC3's universe is a contract
question, not a test question. Both `spec.md` and `plan.md` are hash-pinned and
sealed, so narrowing that sentence needs controlled amendment, reapproval and
resealing. That is an owner decision and it is where this delivery stopped.

## A follow-on I raised and then measured away

The approved spec carried a follow-on asking whether the approval pin's
status-token and progress-checkbox exemptions should shrink. While amending the
contract I sharpened it into a claimed *type defect*: that
`canonical_contract(ac_section_only=False)` normalizes checkbox brackets
**file-wide** for `plan.md`, so a semantic change wearing checkbox markup would
pass the pin. `_loop_guards.py:781` records the reason as corpus shape rather
than semantics — "A plan has no such section: every checkbox in it is task
progress, and four plans here carry them, so a plan is normalized file-wide".

Measured before asserting it, and the measurement refuses the claim.

Still exactly **4 of 376** plans carry a checkbox, and every one of the four is
in a progress position: `## Finish-time checklist`
(`agentbundle-first-value-handoff`), `## Commit checklist`
(`catalogue-wave1-contract-convergence`), and `## Tasks` (`kiro-ide-hook`,
`queue-add`). **Zero sit in a governed position.**

The asymmetry between the two callers is principled, not sloppy. A spec has a
governed section the pin must protect — a checkbox under `## Boundaries` is a
`Never do` item — so the spec side is bounded to Acceptance Criteria and the
comment names that hazard explicitly. A plan has no such section, so a file-wide
checkbox exemption exposes nothing. Only the bracket contents normalize; the
constraint text stays pinned either way.

`frozen-spec-supersession:45` had already reasoned "No new exemption is needed",
which is the opposite direction and does not dispose of a shrink request. The
razor does: an addition that is not genuinely needed is skipped and said once.
There is also no live carrier for it — `work-loop-in-process-guards` owns
`_loop_guards.py` and is `Shipped`, and `cooling-scope-closure`, the only
unshipped spec citing the freeze section, touches the seam in zero files.

Recorded because the reasoning is the durable part: I reached the type defect by
pattern-matching this delivery's own shape-versus-role theme onto a neighbouring
mechanism, and the corpus said the mechanism was calibrated to its real usage.
