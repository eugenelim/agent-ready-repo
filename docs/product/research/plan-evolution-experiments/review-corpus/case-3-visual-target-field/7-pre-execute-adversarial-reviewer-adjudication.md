## Main-loop result

Clean — ready to commit.

## Refuted audit

- `Nits-1` (`plan.md:766-775`, "The T5 seam still states the superseded plan-approval-only scope in the present tense before resolving it") — `refuted`; proposed mechanism: wrong; broken predicate: authority; contrary evidence: `docs/specs/visual-target-field/plan.md:777` — the resolution paragraph is contiguous with the paragraph the finding objects to, so the objection reduces to a presentation preference that no record or authority decides.

  What is true in the observation. The cited bytes exist as described. `plan.md:766-768` reads "**What is granted, and what is not.** The owner's waiver covers / `tdd-stubs.md` § *Validate*'s intended-red requirement at **plan approval**, for / these two blocks, and nothing further." and `:772-773` reads "**whether the mutation proof may stand in for it is / not decided by the current grant.**" Both clauses are in the present tense and both state a scope the owner has since extended, per `notes/amendment-2026-10-01.md:248-249`: "**The owner ruled on 2026-10-01: extend the waiver to cover § *Lifecycle*'s / EXECUTE-time intended red, for the same two T5 blocks, on the same reason.**" The cited line ranges are accurate as written; no drift to correct.

  What fails to reach a defect, weighed on the four points put to the adjudicator.

  First, nothing external decides between preserving the superseded position as dated narrative and rewording it into the past tense. `tdd-stubs.md` §§ `Lifecycle` (`:15-34`), `Validate` (`:153-185`) and `Record` (`:187-196`) were read. None governs the tense, ordering, or framing of plan prose. The finding itself concedes this ("nothing external decides between preserving the prior position as narrative and rewording it"), and it names none of the four admissible grounds — no violated acceptance criterion, no repository rule, no security property, no concrete defect.

  Second, the governing record uses the very same preserve-then-supersede shape. `notes/amendment-2026-10-01.md:233-234` closes the first waiver with "The EXECUTE-time ledger entry T5's `Done when` gates on is still / owed; this waiver concerns plan approval only." and the next heading at `:236` extends it. The note also marks a superseded section in place rather than rewriting it (`:78-79`: "**This section states the position when the amendment fired. Two of its claims / were later superseded by the supplementary rulings below; read it with those.**"). The plan's form is therefore consistent with its authority record, not in conflict with it.

  Third, the stale sentence is not reachable as a current instruction. The objected paragraph ends at `plan.md:775` and `:777` opens "**Resolved, 2026-10-01.**", followed by `:785` "The substitution is now granted at both phases, and nothing further is waived." There is no intervening heading, task boundary, or `Done when` block. Separately, the plan's self-declared current record bullet (`plan.md:142-143`) states the extended scope at `:197-202`. No surface an implementer reads as current carries the narrow scope.

  Fourth, no gate, lint, or fail-closed check reads this paragraph. The only fail-closed control in play is `tdd-stubs.md:175-181`, which blocks plan approval when stack detection, compilation, or intended-red validation fails; it reads the recorded validation results and the waiver authority, not the tense of a narrative paragraph. Its decision is identical either way.

  Consequence predicate, for the record: first test — nothing external to the finding establishes a defect; it rests on a framing preference. Second test — the cited surface is dated narrative inside a plan task seam that no gate reads, with the authoritative current record held elsewhere. Both tests land advisory, so the consequence could not sustain at blocking severity even had the authority predicate held. The proposed mechanism (past-tense rewording, or a position-before-the-extension marker, offered as "if touched at all") is recorded `wrong` because there is no established defect for it to resolve; it would change no gate outcome and no reader's current instruction.

## Indeterminate audit

None.
