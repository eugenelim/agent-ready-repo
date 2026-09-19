# Verification ledger — ride-along-admission-test

Execution observations. Not contract; the spec and plan are.

## 2026-09-19 — T1: the control is red, and AC23 cannot be checked from a pack test

**Observed.** `packs/core/tests/pack/test_ride_along_admission_test.py` was
created with 16 test functions covering AC1–AC7, AC9–AC13 and AC20–AC23.
`python3 -m pytest packs/core/tests/pack/test_ride_along_admission_test.py -q`
→ 16 failed, 0 errors, every named function present as an `AssertionError`
rather than a collection error. `python3 -m pytest packs/core/tests/pack/ -q`
→ the sibling 234 tests still pass.

**Plan error found.** `python3 tools/lint-pack-test-boundary.py` → exit 1, 3
failures, check `pack-tests-stay-in-pack`:

```
FAIL: packs/core/tests/pack/test_ride_along_admission_test.py:39: pack test reaches above packs/core via `PACK_ROOT.parent.parent`
FAIL: packs/core/tests/pack/test_ride_along_admission_test.py:40: pack test reaches above packs/core via `REPO_ROOT / 'guides' / 'core' / 'explanation' / 'core-pack.md'`
FAIL: packs/core/tests/pack/test_ride_along_admission_test.py:464: pack test reaches above packs/core via `GUIDE`
```

AC23 reads `guides/core/explanation/core-pack.md`, which is outside
`packs/core/`. The rule is unconditional and the lint runs in `docs.yml` on any
`packs/**` change. Only AC23 trips it; AC22's `evals.json` read stays inside the
pack and is clean. The plan's `Design (LLD)` § Component decomposition and T1's
`Touches` both pinned exactly one new file, and the spec's Agent Rules said the
test "lives beside the existing core pack tests" — so the correction is a
contract amendment, not an in-place fix.

**Method note.** The first attempt to verify this blocker ran the lint through
`| tail -8`, which truncated the three FAIL lines and reported `tail`'s exit
status as 0. The lint was re-run unfiltered before the finding was accepted.

**Owner decision, 2026-09-19 (eugenelim).** Amend by the split precedent in
commit `b14725c01`: AC23's check moves alone to
`tests/roster/test_capture_rename_guide.py`, registered per `tests/AGENTS.md`
with its named step placed above the bulk `pytest tests/ -q` step so it can
report; AC1–AC22 stay in the pack-local file unchanged. AC23's substance is
unchanged. Rejected: verifying the guide by a delivery-time grep (loses the
standing control), and deferring the guide to a follow-on (ships a renamed step
whose published documentation still uses the old name).

**Deviation accepted, T1/AC21.** `test_in_file_anchors_resolve` is scoped to
links targeting `#capture` rather than every anchor in `SKILL.md`. An unscoped
check passes today, because every existing `#capture-learnings` link resolves
against the un-renamed heading, so it could not be red for the stated reason.
The scoped form reds now and stays meaningful after the rename.

## 2026-09-19 — T2: eleven sites landed; one Host-markers defect found

**Observed.** `python3 -m pytest packs/core/tests/pack/test_ride_along_admission_test.py -q`
→ 8 passed, 7 failed. Green: C1, C2, C3 identity; AC4 anchor counts; AC6 sync
comments; AC7 vocabulary; AC12 (C6); AC13 (C7). Red and correctly so, all
T3/T4-owned: AC5 (fails on C4/C5, not yet landed — C1/C2/C3 placement inside
it is satisfied), AC9, AC10, AC11, AC20, AC21, AC22. Sibling suite
`packs/core/tests/pack/ -q` → 234 passed with this file deselected.
`make lint-ruff lint-mypy` → clean, 148 source files. The four-file
`git grep` for retired vocabulary returns nothing.

**Spec defect found, repaired in place.** § Host markers named
`**Bundled fixes:**` as C6's host marker in `implementer.md`, but that marker
occurs only *inside* the fenced report template, and AC5 forbids a clause
sitting inside a fenced block. The two obligations could not both be met as
written. Resolution: a new occurrence of the marker as prose immediately above
the fence carries C6, and the fenced template is otherwise unchanged. This
needs no amendment — AC5 and AC12 both pass, and § Host markers names a marker
rather than an occurrence.

The first placement put that sentence directly after the report-shape intro,
where it read as the first section of the report rather than a rule about one
of them. The controller added a lead-in — "One section below carries an
obligation the template cannot show:" — which is free prose, not a pinned
clause, and leaves the test result unchanged at 8 passed / 7 failed.

## 2026-09-19 — T4: `## Capture` lands, the suite is green, and AC14's walk and AC8's five mutations are recorded

**Observed.** `## Capture learnings` became `## Capture`; both in-file links
(the `Scratch note.` cross-reference and the Finish-checklist item) now target
`#capture`, and the checklist item reads as a scratch-note disposal item
rather than a learnings-recorded claim. The DECIDE scratch-note bullet was
replaced with C4 verbatim and C5 was added as its own paragraph in the same
section; `otherwise discard it` no longer appears anywhere in the file. The
four example bullets stayed in place, immediately after C4's bullet. The
`evals.json` case `capture-learnings-quality-attributes` now prompts "…are at
Capture." with its id unchanged. `guides/core/explanation/core-pack.md` step
10 now reads `**Capture.**` and describes routing a scratch note to one of
several destinations, not only recording a learning to a skill, ADR, or
pattern note.

`python3 -m pytest packs/core/tests/pack/test_ride_along_admission_test.py -q`
→ 15 passed, exit 0. `python3 -m pytest
tests/roster/test_capture_rename_guide.py -q` → 2 passed, exit 0 (AC23's guide
assertion goes green here). `python3 -m pytest packs/core/tests/pack/ -q` →
249 passed, exit 0. `python3 -c "import json;
json.load(open('packs/core/.apm/skills/work-loop/evals/evals.json'))"` → exit
0. `make lint-ruff lint-mypy` → clean, 148 source files, exit 0.
`work-loop/SKILL.md` body line count (total lines minus frontmatter, ending at
the second `---` on line 10): 982 total − 10 = **972**, under the `CAT-S003`
1,000 cap (it was 918 before this task began; this task added 54 body lines).

**Deferred to T7, not run here.** `agentbundle catalogue self-host --root .
--write` regenerates all packs, not only the files this task touched, and its
first run also caught up projection drift that T2 left uncommitted in
`implementer.md`, `adversarial-reviewer.md`, and `supervisor-mode.md` (92,
57, and 47 changed lines respectively across `.claude/`, `.agents/`,
`.codex/`). The plan reserves that regeneration for T7, after T1–T6 are
committed, so the write was reverted with `git checkout -- .agents .claude
.codex` and left for T7 to run against the complete tree. `docs/AGENTS.md`
was flagged by the harness as touched by that command but `git status` and
`git diff` show no change to it — no real edit occurred there.

**Method note.** The first mutation-record pass reverted a mutated file with
`git checkout -- <path>`, which restores from the last commit rather than
from the file's pre-mutation state. Because this task's own `SKILL.md` edits
were uncommitted at that point, the checkout silently discarded them along
with the mutation, reverting the file to its pre-T4 state (`## Capture
learnings` reappeared). Caught immediately by re-grepping for `## Capture`
before continuing; the three T4 edits were reapplied, confirmed green (15
passed) before any further mutation, and every mutation after that point was
captured and restored from an explicit `cp` backup instead of `git checkout`.

**(a) AC14 — the routing walk.** C4's shape: an additive seam clause applies
first to any generalisable content regardless of defect status; then, only
where the note names a defect, an ordered sequence takes the first
destination that applies and stops (ride-along dispatch → capture →
next-reviewed-unit → discard); a note naming no defect is done once the seam
has taken it, and discarded if it had nothing for the seam either.

1. **A ready-now, non-generalisable defect with a stated arbiter that fires a
   risk trigger on its own → next-reviewed-unit.**
   - Seam: excluded — not generalisable, nothing for the seam to take.
   - Ride-along dispatch: excluded — C1 clause (i) requires firing no risk
     trigger on its own; this one fires one, so the admission test refuses it
     before dispatch is reached.
   - Capture: excluded — it is ready-now, not blocked on a decision, an
     instrument, or elapsed time.
   - Next-reviewed-unit: matches — ready-now (finishable this session
     without a decision nobody present will make) and not ride-along
     eligible.
   - Discard: never reached — first-match-wins stopped at
     next-reviewed-unit; it also has a stated arbiter, so "no stated
     arbiter" would not apply anyway.

2. **The same defect, but whose verification cannot be stated →
   next-reviewed-unit.**
   - Seam: excluded — still non-generalisable.
   - Ride-along dispatch: excluded — C1 clause (iii) requires stating how it
     was verified; unable to state it, the admission test refuses it (on top
     of the risk-trigger refusal already inherited from note 1).
   - Capture: excluded — an unstateable verification is not "blocked on a
     decision, an instrument, or elapsed time"; nothing here waits on
     anything.
   - Next-reviewed-unit: matches — still ready-now and still not ride-along
     eligible, for a different clause of the same admission test.
   - Discard: never reached — matched at next-reviewed-unit first.

3. **A ride-along candidate whose only bar is an unresolved design call with
   no citation and no answer → capture.**
   - Seam: excluded — presented as a defect candidate, not a generalisable
     lesson; nothing for the seam to take.
   - Ride-along dispatch: excluded — C1 clause (ii) refuses any unresolved
     design call; C2 names "no citation exists and no answer was given" as
     exactly that state, so admission fails before dispatch.
   - Capture: matches — C2's closing sentence routes an item with no
     citation and no answer to `blocked_on: decision`, which is what "a
     defect blocked on a decision" names.
   - Next-reviewed-unit: never reached — matched at capture; also not
     ready-now, since it is blocked on a decision nobody present resolved.
   - Discard: never reached — matched at capture first.

4. **A pure lesson with no defect attached → seam, and nothing else.**
   - Seam: matches — generalisable content that would have changed the
     approach goes to the seam; a pure lesson is exactly that.
   - The entire defect-disposal sequence (dispatch, capture,
     next-reviewed-unit, discard): excluded as a block — the note names no
     defect, so C4's closing sentence applies instead: "a note that names no
     defect is done once the seam has taken it." No later destination is
     ever considered.

5. **A generalisable, decision-blocked defect → seam and capture, and
   nothing else.**
   - Seam: matches — the seam clause is additive and fires on generalisable
     content independently of whatever the defect-disposal sequence later
     decides.
   - Ride-along dispatch: excluded — blocked-on-a-decision is not an
     admissible state under C1 clause (ii); the admission test refuses it.
   - Capture: matches — "a defect blocked on a decision, an instrument, or
     elapsed time is captured" names this note directly.
   - Next-reviewed-unit: never reached — matched at capture; also not
     ready-now.
   - Discard: never reached — matched at capture first.
   - Result: two destinations, seam and capture, which is the seam's stated
     additive exception rather than a defect in the walk — no note here
     reached zero or an unauthorized second destination.

No note reached zero destinations or an unauthorized second destination; note
5's second destination is the seam's own additive rule, stated as an
exception in the same clause.

**(b) AC8 — the five mutations, applied one at a time to the complete tree
and reverted before the next.** Baseline: `test_ride_along_admission_test.py`
green at 15 passed before each mutation.

1. **Change one interior word of C1 in exactly one file.** `SKILL.md`: "fires
   no risk trigger" → "fires no risk signal". Result: 1 failed, 14 passed.
   Caught by `test_c1_is_identical_across_the_four_sites`
   (`AssertionError: C1 diverges across sites`).
2. **Add a second copy of C1 to exactly one file.** Appended the full C1
   sentence again as plain prose (preceded by an unrelated HTML comment
   marking the addition as scratch) to the end of `implementer.md`. Result:
   1 failed, 14 passed. Caught by
   `test_clause_anchors_occur_exactly_once_where_carried`
   (`AssertionError: C1 opening appears 2 times in implementer.md, expected
   exactly 1`).
3. **Move one file's C1 out of its host into an adjacent HTML comment.**
   Wrapped `adversarial-reviewer.md`'s C1 paragraph in `<!-- -->` in place.
   Result: 1 failed, 14 passed. Caught by `test_clauses_sit_in_their_hosts`
   (`AssertionError: C1 occurrence in adversarial-reviewer.md sits inside an
   HTML comment`).
4. **Reword C3 in exactly one mirror.** `implementer.md`: "(§ Select: light
   or full mode)" → "(§ Choose: light or full mode)" — an interior reword
   that leaves C3's open/close anchor literals intact so only the identity
   assertion fires. Result: 1 failed, 14 passed. Caught by
   `test_c3_is_identical_across_the_three_mirrors` (`AssertionError: C3
   diverges across mirrors`).
5. **Change one carve-out sync comment back to naming three sites.**
   `implementer.md`'s sync comment reworded from "kept in sync across four
   sites: work-loop/SKILL.md, implementer.md, adversarial-reviewer.md, and
   work-loop/references/supervisor-mode.md" to "kept in sync across three
   sites: work-loop/SKILL.md, implementer.md, and adversarial-reviewer.md."
   Result: 1 failed, 14 passed. Caught by `test_sync_comments_name_four_sites`
   (`AssertionError: implementer.md's carve-out comment is missing
   'work-loop/references/supervisor-mode.md'`).

Every mutation reds; none was papered over. Each file was restored from an
explicit pre-mutation backup and diffed byte-identical against it before the
next mutation, and the suite was confirmed green (15 passed) after the last
revert.

## 2026-09-19 — REVIEW: six adversarial findings and four introduced security Blockers

**Adversarial implementation review** (`.context/reviews/<run>/7-impl-adversarial-reviewer-raw.md`),
six Blockers, all sustained on inspection:

1. AC12 does not hold. C6 sits beside the report template, not in it, and the
   control's scan window spans both, so it passes while the template carries
   nothing.
2. The clause controls compare the four extractions to each other, never to
   the canonical `C1`/`C2`/`C3` constants the same file defines. A
   synchronised reword at every site passes green: the control proves
   consistency, not correctness.
3. The roster control matches `routes|routing` anywhere in the guide and
   flattens all CI jobs, so AC23 or AC24 can be broken while it passes.
4. The rename left live shipped references. `packs/core/.apm/hooks/pre-pr.py:13,115`,
   `tools/hooks/pre-pr.py:13,115` and `tools/hooks/README.md:66` say
   `Capture-learnings`. The controller's rename sweep searched
   `Capture learnings|capture-learnings` and missed the capitalised hyphenated
   form — a case-sensitive pattern over a name with three spellings.
5. The plan's post-T7 manual-QA walk of the installed artifact was not run.
6. No security review had been recorded for an agent-authority change.

**Security review** (`llm-agent` + `agentic-skills` modules inlined), four
Blockers **introduced by this change**, four Concerns, one Nit:

- **S1 (Blocker, introduced).** C1 does not exclude agent-guidance surfaces.
  An unplanned edit to `SKILL.md`, `implementer.md`, `adversarial-reviewer.md`
  or `supervisor-mode.md` fires no risk trigger, reads as "no behaviour
  change" because the artifact is prose, and satisfies clause (iii) by
  comparison — so an agent may rewrite the text bounding its own unplanned
  write authority. Locality blocked this by construction; removing it removed
  the block without replacing it.
- **S2 (Blocker, introduced).** A citation may be authored by the same change
  that cites it. In the worktree case the implementer is the commit owner, so
  it writes the commit message that "records the decision" and then cites it.
- **S3 (Blocker, introduced).** The new DECIDE row discharges the owner
  scope-change gate on the assertion that a ride-along "alters no acceptance
  criterion and moves no contract pin" — which C1 never tests.
- **S4 (Blocker, pre-existing, worsened).** The carve-out grant is
  unauthenticated in-band prose and denial is by omission, so authorization
  text inside any content the implementer reads re-grants it. This change
  widens the forged grant from same-area to repository-spanning.
- Concerns: attendance decided by counting declarations over an undelimited
  brief; "the human gate's own record" names no artifact and the reply nonce
  is text the agent wrote; the `blocked_on: decision` store is undesigned and
  the path is barred from surfacing; post-merge dedup can drop a landed
  mutation from the PR body.

**Owner decision, 2026-09-19 (eugenelim).** Fix the four introduced Blockers
now — S1, S2, S3 and the six adversarial findings — by amending C1 and C2.
Defer S4's channel weakness and the dedup gap as follow-ons with a named
owner, because they pre-date this change. Rejected: fixing only S1;
reinstating locality as a second route (it restores most of what the tiers
did); and halting to rescope.
