# ADR-0158: Review obligation policy: a two-round cap and diff-derived review tiers on the supervisor's review gate

- **Status:** Accepted
- **Date:** 2026-11-05
- **Areas:** work-loop, review
- **Reversibility:** high
- **Decision-makers:** eugenelim
- **Supersedes:** none
- **Supersedes in part:** ADR-0144 D8
- **Superseded by:** none
- **Superseded in part:** none
- **Related:** spec:execution-supervisor-review-gate (Agent Rules and § Scope, which this record amends); spec:structured-review-boundary (obligation and disposition tables, which this record amends); spec:execution-supervisor-core (the reanchor evidence restart, which this record narrows for review); ADR-0157 (owner decisions read only supervisor-owned text)

## Decision summary

- **Decision:** The supervisor's review gate runs every selected reviewer once per unit of work, then asks each repaired revision only for the reports its diff earns: none for a wording-only repair, one delta pass for a rebase or a minor fix, the full set otherwise. An unprotected unit's code-review stage gets two rounds, after which the owner decides from the named open findings. Protected roles report on every revision, and a protected unit is never capped.
- **Because:** every repair reruns every selected reviewer today with no round limit, yet 43-65% of findings come from one reviewer alone, so the cost has to come out of rounds, not reviewers.
- **Applies to:** the execution supervisor's code-review stage in full-mode `code` runs. Not the pre-approval reviews, light mode, or the reviewers themselves.
- **Tradeoff accepted:** a non-protected reviewer does not re-read a small repair it raised no finding on, and an unprotected loop that has not converged after two rounds goes to the owner rather than a third round.
- **Revisit if:** a defect escapes that a skipped or delta-only pass would have caught, or owners routinely answer the cap with another round.

## Context

A supported finding becomes repair work, and the repaired product is a new review subject: the identity the supervisor reviews, made of the delivery subject, the changed paths, and the reviewer policy. Readiness matches reports, assessments, and dispositions to the current subject's fingerprint, so every repair needs a fresh report from every mandatory role. The controller also selects reviewers again for each subject, because the selection key hashes the whole product. Nothing caps review rounds; only the implementation retry cap stops a run.

These facts constrain the answer:

- **Most findings come from one reviewer.** A measurement over 88 multi-reviewer rounds, 2026-10-25 to 2026-11-03, found that 305-460 of 708 anchored findings (43-65%) came from only one reviewer; the range runs from a strict location match to a looser one. So shaping and spec-mode adversarial review stay separate, and no reviewer is dropped.
- **Prose limits do not bind.** `new-spec` already says spec-mode review should converge in one or two passes and surface at three, and runs still reach seven rounds.
- **Three accepted rules stand in the way, and this record amends each.** ADR-0144 D8 closes review only when every selected obligation has a current typed report. The structured-review-boundary spec treats a report bound to an older subject as stale. The review-gate spec forbids encoding a reviewer trigger as a mechanical predicate and puts changes to which roles are skippable behind the owner.
- **Two mechanisms were tightened on 2026-11-05 after security review, before the first merge.** D3's patch comparison uses `--verbatim` rather than `--stable`, which ignores whitespace. D6 names findings by supervisor-made references, because finding and report ids are free text a reviewer writes.
- **A reanchor restarts evidence.** An adopted rebase that changes the product salts the evidence fingerprint, so "nothing recorded before it counts", and today gates and reviews all run again.

## Decision

We will add review obligation policy to the supervisor's structured review readiness: a diff-derived tier decides which selected roles must report again on a repaired subject, a typed carry record stands in for the rest, and a round cap hands an unprotected unit's open findings to the owner.

- **D1: Tiers decide re-reporting, never selection.** The controller still selects the roles for each subject. The tier is `full` whenever the resolved roles, their kinds, or the declared protected classes differ from the anchor round's. The anchor round is the last round on which every selected role reported. An open finding, below, is a supported material finding raised on any subject since the anchor round and not yet closed by `fixed-by` or `accept-risk`. A tier only decides whether a selected role reports again or carries its latest report forward. This is the one approved exception to the review-gate rule against mechanical reviewer predicates: the predicate may lower re-reporting, never selection.
- **D2: A carry record replaces "current report" for carried roles, amending ADR-0144 D8.** For each role a tier lets off, the supervisor writes one `review-carry.v1` record binding the role, the role's latest report or carry on an earlier subject, the current subject, the tier, and the digest of the classifier's input. Readiness accepts that record as the role's current report on the current subject. The carried report's assessments and dispositions count with it. The supervisor writes a carry record only for a role with no open finding, and never for a protected role. Every other rule of ADR-0144 D8 stands.
- **D3: Tiers come from the diff and fail closed.** The supervisor compares the current result with the anchor result over the run's own changed product paths, using `git diff --raw --no-renames`. Any status other than a modification, any mode change, a binary or unreadable file, a missing anchor, or any error while classifying makes the tier `full`. The other tiers are:
  - **`wording-only`:** no finding is open; every changed path matches the prose allowlist in `review-rules.json` and no instruction-name entry; and no changed line falls inside a fenced code block, front matter, inline code, a link target, an HTML comment, or raw HTML. The allowlist is positive: a path not on it is never `wording-only`. The shipped default allows Markdown and plain text under `docs/` and named root documents such as `README.md`. Instruction names such as `SKILL.md` and `AGENTS.md` are refused even inside an allowed path.
  - **`rebase`:** an adopted reanchor changed the product but not the spec directory, and the run's own patch is unchanged: the same changed-path set, and for each path the same `git patch-id --verbatim` of its diff from base to result as at the anchor round. `--verbatim` keeps whitespace, so a re-indent counts as a change; it needs Git 2.39 or later, and with older Git a rebase classifies `full`.
  - **`minor-fix`:** at least one finding is open; every changed path is already in the anchor's changed set; and added plus removed lines stay within `minor_fix_max_lines` in `review-rules.json`. The delta is measured from the anchor result, so small fixes cannot add up past the threshold unseen.
  - **`full`:** everything else.
  The controller may ask for `full` on any subject. Nothing may ask for a lower tier than the diff earns.
- **D4: Each tier names who reports.** `wording-only` asks for no report. `rebase` asks for one delta pass from the always-selected role over the upstream changes to the paths the run touches. `minor-fix` asks for one delta pass from each role that raised an open finding; that report closes the repaired findings with `fixed-by`. A delta pass is an ordinary `review-report.v1` on the current subject, and its request names the anchor result and the findings it repairs. Under `rebase`, the reanchor still restarts gates and criteria evidence; only review facts carry.
- **D5: Protection is declared per unit and fails closed.** Every selection record states `protected_classes`, possibly empty, from five classes: security boundary, data loss or durability, migration, public interface, and irreversible operation. A record without the field is refused. `review-rules.json` maps each class to one reviewer: security boundary to `security-reviewer`; data loss or durability, and migration, to `quality-engineer`; public interface and irreversible operation to `adversarial-reviewer`. A declared class makes its mapped reviewer a protected role for the unit. A declaration whose mapped reviewer is not selected is refused, and so is selecting `security-reviewer` without declaring security boundary. The classes join the review policy's identity, so changing them changes its fingerprint. A protected role reports on every new subject under every tier, at least as a delta pass, and never carries.
- **D6: An unprotected unit gets two rounds.** A unit is one run's code-review stage. It is protected when any of its selections declares a protected class or selects a protected role. Protection only grows within a unit: a selection whose classes or protected roles are not a superset of the unit's earlier ones is refused unless an owner's `reselect-review` decision authorizes it. A round is the unit's first full-set subject and each subject reached by repairing supported findings, counted for the whole unit and never reset by a reselection. `rebase` and `wording-only` subjects are not rounds, and a `wording-only` subject cannot follow an open finding (D3). The cap is `code_review_round_cap` in `review-rules.json`, default 2, and stays outside the parity check that ties `max_review_retries` to cohort state. When the cap round in an unprotected unit leaves a supported material finding open, `review-cap` replaces `review-not-eligible`. It is keyed to the cap event, not the subject, and names each open finding by a supervisor-made reference (a sha256 over its report id and finding id), its role, and the evidence-log position of its report. No reviewer-supplied identifier or text appears in it. The owner answers `accept-risk` (a risk owner, as today), `extend-review` (an owner grants one more round), or `reselect-review`. No answer, a timeout, or a malformed answer leaves the findings open.
- **D7: A protected unit keeps today's loop.** The cap never applies to it. Its review ends by a fix, a risk owner's `accept-risk`, or the implementation retry cap, as today.
- **D8: The cap covers the code-review stage only.** Pre-approval review (shaping, spec-mode adversarial, and security review of the spec and plan) runs outside the supervisor and keeps its five-round budget, which an owner may lift. A cap on those loops is a follow-on.

## Decision drivers

- No finding a separate reviewer would raise on the first full pass is lost.
- Work that crosses a protected class keeps today's coverage on every revision and today's loop.
- Classification is mechanical where it can be, and uncertainty costs review, not coverage.
- In an unprotected unit, a human, not a counter, ends a review loop that has not converged.

## Consequences

**Positive:**

- A typical repair costs one delta pass instead of the full set.
- An unprotected review that does not converge stops after two rounds with a decision the owner can read in typed terms.
- A clean rebase reruns one reviewer and every protected role, not the full set.

**Negative:**

- A non-protected reviewer that raised no finding does not see a minor fix to code it already passed.
- The supervisor gains a diff classifier, a carry record, a decision type, and an `execution-result.v1` decision value that its tests and script pins must cover.
- The controller must now declare protected classes on every selection, and a wrong empty declaration is caught only by the security-reviewer pairing rule.
- A unit declaring public interface or irreversible operation keeps `adversarial-reviewer` on every revision, so its repairs cost at least that pass.
- A protected unit gets no round saving from the cap, and its loop still ends only by fix, accepted risk, or the retry cap.
- The costliest loops, before code exists, are not capped by this record. Follow-on: a cap on the pre-approval review loops.

**Revisit if:** a defect escapes that a skipped or delta-only pass would have caught, or owners routinely answer the cap with another round.

## Confirmation

- **Mode:** lint/CI
- **Signal:** core pack tests prove each tier from fixture diffs, and that each uncertain case classifies `full`. They prove that a reselection changing roles, kinds, or protected classes gives `full`, and that a wording-only repair of an open finding still asks for a report. They prove that a request for a lower tier than earned is refused, and that a selected `security-reviewer` reports on every new subject under every tier. They prove that a finding raised on a rebase delta pass stays open through a later `wording-only` or `minor-fix` subject. They prove that a selection dropping a protected class without an owner decision is refused, and that a reselection does not reset the round count. Finally, they prove that a protected unit never opens `review-cap`, and that no answer leaves a `review-cap` decision open.
- **Owner:** core pack maintainers

## Alternatives considered

- **Merge shaping and spec-mode adversarial review into one pass:** rejected against "no finding a separate reviewer would raise is lost". The measurement shows 43-65% of findings come from one reviewer alone.
- **Lower the retry budget only:** rejected against "a human ends a loop". A smaller count still reruns every reviewer each round and ends in a refusal, not a decision from named findings.
- **Rerun every carried role on the delta instead of a carry record:** rejected because it keeps the full set's cost on every repair, which is the cost this record removes.
- **Let the controller choose the tier:** rejected against "classification is mechanical where it can be". Here the controller's judgement can only raise the tier.
- **Protect findings by class instead of units:** rejected for now because `finding.v1` carries no class, so the supervisor could not tell a protected finding from an ordinary one without a contract change. Unit-level protection fails closed instead.
- **Force the full set on every revision of a protected unit:** rejected against the cost driver. Security-boundary work is common, and it would then save nothing, while the class-to-reviewer map already keeps each class's reviewer on every revision.
- **Exempt protected classes from the cap only:** rejected against "protected classes keep today's coverage". A migration's `wording-only` or `minor-fix` repair would then skip its quality review.
- **Exempt protected roles only from the cap:** rejected against "protected classes keep today's coverage". A `wording-only` edit to a security guide would then skip security review.
