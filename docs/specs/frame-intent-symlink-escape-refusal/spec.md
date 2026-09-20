# Spec: a placement path that resolves through a symlink out of its root refuses

- **Status:** Draft
- **Owner:** eugenelim
- **Mode:** full
- **Plan:** [`plan.md`](plan.md)
- **Brief:** docs/product/briefs/intent-identity-and-registration.md
- **Constrained by:** ADR-0030

## Objective

`frame-intent` refuses a repository-scope destination whose resolution passes through a symlink leaving its anchoring root, and keeps asking about every other out-of-repository resolution. The two cases are different and its body currently treats them the same: `SKILL.md:239-243` calls any repo-sourced value resolving outside the tree untrusted-origin and confirms before writing.

The split is not a preference. A symlink escape is the case the security checklist names non-waivable — "resolve links before the boundary check, and refuse to follow links into untrusted trees" (`security-checklists/references/path-and-file.md:30-32`). An absolute or `..`-bearing value that resolves to a real directory outside the repository is a configuration choice, and ADR-0030 D7 already decides it: an untrusted-origin, Ask-first deviation, with D6's disclosure of the resolved absolute path as its control. Refusing that case would remove a legitimate destination an adopter chose.

## Boundaries

This slice changes how one prose section distinguishes two arms. It refuses nothing that ADR-0030 D7 permits, so it supersedes no decision and needs no new record. The personal branch is untouched: a user-profile destination is legitimately outside the repository.

Out of scope: the resolution order and whether a pack default precedes elicitation, which is an unreconciled conflict between RFC-0040's resolution tail and RFC-0096 § 4 and is registered against ADR-0030; where a repository intent is written, which is a pinned core hand-off and needs no work beyond stating that rule for intents as it is already stated for briefs, registered separately; and any change to how `frame-intent` executes anything.

## Testing Strategy

- **The refusing arm (AC-0001):** goal-based check on the skill body's own text. Stated plainly: this establishes that the instruction says the right thing, not that a program does it. `frame-intent` is prompt-only, and the repository verifies its prose with pack-level assertions; this is the strongest evidence available for this surface and it is weaker than a test over code.
- **The asking arm (AC-0002, AC-0003):** goal-based check, one case per non-symlink form, asserting the body keeps Ask-first with the resolved absolute realpath disclosed. Without these the change reads as a blanket refusal, which would contradict ADR-0030 D7.
- **The two arms are distinguishable (AC-0004):** goal-based check that the body states both and does not collapse them into one verdict.
- **Nothing else regressed (AC-0005):** run `packs/product-engineering/tests/pack/test_frame_intent_shaping_review.py` unamended.
- **Observed once (AC-0006):** visual / manual QA at the consumer, recorded in the verification ledger. A prose assertion cannot distinguish a body that says "refuse" from an agent that asks anyway.

## Acceptance Criteria

- [ ] **AC-0001.** A repository-scope destination whose resolution passes through a symlink leaving the anchoring root is refused before any write, and the body states that refusal.
- [ ] **AC-0002.** A repository-scope destination that resolves outside the repository root without traversing a symlink — through a `..` segment or an absolute value — is not refused: the body keeps ADR-0030 D7's Ask-first deviation, with the resolved absolute realpath disclosed first.
- [ ] **AC-0003.** A personal-scope destination outside the repository is not refused; its control remains disclosure of the resolved absolute realpath before the first write.
- [ ] **AC-0004.** The body distinguishes the two arms explicitly, so neither a blanket refusal nor a blanket confirmation can satisfy it.
- [ ] **AC-0005.** `packs/product-engineering/tests/pack/test_frame_intent_shaping_review.py` passes unamended.
- [ ] **AC-0006.** One recorded consumer invocation shows the symlink arm refusing, with the observed output and the tree state showing no file created.

## Assumptions

- **Prose evidence, accepted knowingly.** `frame-intent` is prompt-only: its resolution lives in its body, not in code. A source-text assertion can be satisfied by wording that reads correctly and is never followed, so AC-0001 through AC-0004 bind the instruction rather than the behaviour. AC-0006 is the one observation that reaches behaviour, and it is one observation, not a suite. The slice is isolated so this weakness is visible rather than hidden inside a code slice whose evidence looks stronger.
- The failure the refusing arm prevents is a write through an attacker-placed link out of the repository. The failure the asking arm accepts is a document written to a directory the adopter confirmed after seeing its absolute path. Treating those as one case is what the current body does.
