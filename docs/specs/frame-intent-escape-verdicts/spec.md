# Spec: three escape forms, three verdicts

- **Status:** Draft
- **Owner:** eugenelim
- **Mode:** full
- **Plan:** [`plan.md`](plan.md)
- **Brief:** brief:intent-identity-and-registration
- **Constrained by:** ADR-0030

## Objective

`frame-intent` gives three different answers to three different out-of-root cases, where its body currently gives one. `SKILL.md:239-243` calls any repo-sourced value resolving outside the tree untrusted-origin and confirms before writing. A symlink leaving the anchoring root and a `..` segment are not that case: the first is a security control and the second is already rejected by ADR-0030 D6.

The split is three-way, and each arm is decided by a record rather than a preference.

- **A symlink out of the anchoring root refuses.** `security-checklists/references/path-and-file.md:30-32` requires resolving links before the boundary check and refusing "to follow links into untrusted trees". `AGENTS.md` forbids cutting a security control.
- **A `..` segment refuses.** ADR-0030 **D6** already decides this: the skill resolves the full absolute path "realpath-resolved and `~`-expanded, **with `..` rejected**". This slice does not introduce that rule; it stops the body collapsing it into the confirm-and-proceed verdict.
- **An absolute value that resolves outside the repository, with no `..` and no symlink, is asked about.** ADR-0030 **D7** decides it as an untrusted-origin, Ask-first deviation, with D6's disclosure of the resolved absolute path as its control. That record is the owner's explicit reconciliation with the confinement default: the checklist would otherwise confine every resolved path to a designated root, and D7 accepts a confirmed destination outside it for a value the adopter configured. The spec relies on that record rather than treating the control as inapplicable.

## Boundaries

This slice changes how **two contract surfaces** — the skill body and its shipped layout reference — distinguish **three arms**. It refuses nothing that ADR-0030 D7 permits, so it supersedes no decision and needs no new record. Being outside the repository remains legitimate on its own: a user-profile destination is fine, and what does not change for it is that verdict — a symlink or `..` escape from its *own* anchoring root still refuses.

Out of scope: the resolution order and whether a pack default precedes elicitation, which is an unreconciled conflict between RFC-0040's resolution tail and RFC-0096 § 4 and is registered against ADR-0030; where a repository intent is written, which is a pinned core hand-off and needs no work beyond stating that rule for intents as it is already stated for briefs, registered separately; and any change to how `frame-intent` executes anything.

## Testing Strategy

- **The two refusing arms (AC-0001, AC-0002):** goal-based check on the skill body's own text. Stated plainly: this establishes that the instruction says the right thing, not that a program does it. `frame-intent` is prompt-only, and the repository verifies its prose with pack-level assertions; this is the strongest evidence available for this surface and it is weaker than a test over code.
- **The asking arm (AC-0003, AC-0004):** goal-based check, asserting the body keeps Ask-first for the absolute-only form with the realpath disclosed, and states that being outside the repository is legitimate at personal scope. Without these the change reads as a blanket refusal, which would contradict ADR-0030 D7. They do not exempt personal scope from AC-0001 or AC-0002: a symlink or `..` escape from that scope's own anchoring root still refuses.
- **The three arms are distinguishable (AC-0005):** goal-based check that the body states all three and collapses none of them into a single verdict.
- **Both contract surfaces agree (AC-0006):** goal-based check across the body and the shipped layout reference, because the reference carries its own copy of the old single verdict and a corrected body beside a stale reference gives an adopter two answers.
- **Nothing else regressed:** run `packs/product-engineering/tests/pack/test_frame_intent_shaping_review.py` unamended. This is a construction check rather than an acceptance outcome, so it lives here and in the plan and carries no criterion.
- **Observed once (AC-0007):** visual / manual QA at the consumer, recorded in the verification ledger. A prose assertion cannot distinguish a body that says "refuse" from an agent that asks anyway, and this is the only criterion in the slice that reaches behaviour.

## Acceptance Criteria

- [ ] **AC-0001.** The body instructs refusal, before any write, of a destination whose resolution passes through a symlink leaving its anchoring root — the repository root at repository scope, the configured directory at personal scope.
- [ ] **AC-0002.** The body instructs refusal of a destination whose path carries a `..` segment, per ADR-0030 D6, rather than routing it to confirmation.
- [ ] **AC-0003.** The body instructs Ask-first for a repository-scope destination that resolves outside the repository root by an absolute value alone — no `..`, no symlink — with the resolved absolute realpath disclosed first, and cites ADR-0030 D7 as the record that permits it.
- [ ] **AC-0004.** The body instructs that being outside the repository is not itself grounds for refusal: a personal-scope destination is legitimate, with disclosure of the resolved absolute realpath as its control. This does not lift AC-0001 or AC-0002, which apply within that scope's own anchoring root.
- [ ] **AC-0005.** The body distinguishes all three arms, so no single verdict — blanket refusal or blanket confirmation — satisfies it.
- [ ] **AC-0006.** `references/agentbundle-layout.md` expresses the same three-way distinction, or replaces its own verdict with a pointer to the body that owns it, so a stale reference cannot contradict a corrected body.
- [ ] **AC-0007.** One recorded consumer invocation shows the symlink arm refusing, with the observed output and a tree state showing no file created.

## Assumptions

- **Prose evidence, accepted knowingly.** `frame-intent` is prompt-only: its resolution lives in its body, not in code. A source-text assertion can be satisfied by wording that reads correctly and is never followed, so AC-0001 through AC-0006 are written as instruction-level outcomes and say so in their own wording. AC-0007 is the one observation that reaches behaviour, and it is one observation, not a suite. The slice is isolated so this weakness is visible rather than hidden inside a code slice whose evidence looks stronger.
- The failure the refusing arm prevents is a write through an attacker-placed link out of the repository. The failure the asking arm accepts is a document written to a directory the adopter confirmed after seeing its absolute path. Treating those as one case is what the current body does.
