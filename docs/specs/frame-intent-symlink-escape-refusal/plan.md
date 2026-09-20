# Plan: a placement path that resolves through a symlink out of its root refuses

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting
- **Repository anchors:** `packs/product-engineering/.apm/skills/frame-intent/SKILL.md:229-243` (the "Resolve, then surface, then write" block and the untrusted-origin sentence this supersedes); `packs/product-engineering/.apm/skills/frame-intent/references/agentbundle-layout.md:56-58` (the same rule restated in the shipped schema doc, which must move with it); `packs/product-engineering/tests/pack/test_frame_intent_shaping_review.py` (the prose-assertion pattern this pack already uses). Named uncertainty: prose verification cannot establish behaviour, recorded as an accepted limitation in the spec's `## Assumptions`.

## Approach

One distinction, two homes, one test file. The skill body's single untrusted-origin-confirm verdict splits three ways: a symlink out of the anchoring root refuses, a `..` segment refuses because ADR-0030 D6 already rejects it, and an absolute-only resolution outside the repository keeps Ask-first. The reference doc that restates the rule moves with it. What does not change is that a destination outside the repository is legitimate on its own; what does change for every scope is that a symlink or `..` escape from its own anchoring root refuses. The work is small; the care is in not over-reaching — a blanket refusal would contradict ADR-0030 D7 and break a destination an adopter legitimately chose, and that is the likely defect if this is rushed.

Amend prose, do not shorten it. The section already carries the anchoring and realpath rules that make an escape detectable; what changes is the verdict, not the detection.

## Constraints

- **The security control, for the symlink arm.** `security-checklists/references/path-and-file.md:30-32` requires refusing to follow links into untrusted trees, and `AGENTS.md` forbids cutting a security control.
- **ADR-0030 D6 for the `..` arm.** D6 resolves the absolute path "with `..` rejected", so traversal was never an Ask-first case and this slice only stops the body implying it was.
- **ADR-0030 D7 for the absolute-only arm**, which this slice conforms to rather than supersedes. D7 is also the owner's recorded reconciliation with the confinement default: the checklist would confine every resolved path to a designated root, and D7 accepts a confirmed destination outside it for an adopter-configured value.
- **ADR-0030** keeps each pack's default and posture in its own skill body, so this rule belongs in `frame-intent`'s body rather than in a shared contract.
- **Prompt-only.** `frame-intent` reads a file and reasons about a path; there is no engine behind it, and this slice adds none.

## Construction tests

**Integration tests:** none — there is no code seam to integrate.

**Manual verification:** one session, and its setup must traverse a symlink rather than merely resolve outside the repository — an absolute-only external path is the D7 arm and must *ask*, so a setup that omits the link would assert the wrong verdict. Invoke `frame-intent` in a tree whose repo-root `output_dir` resolves through a symlink leaving the repository root, and record that it refuses rather than offering a confirmation. Recorded in the verification ledger with the invocation and observed output. A prose assertion cannot distinguish a body that says "refuse" from an agent that asks anyway; this session is the only evidence that reaches the behaviour.

## Durable-output map

No `## Durable Outputs` table in the spec, so nothing to mirror. Each task names the criteria it discharges.

## Tasks

### T1: Each of the three arms gets its own verdict, at both scopes

**Depends on:** none

**Mode:** Goal-based check

**Tests:**
- The body instructs refusal for a resolution passing through a symlink out of the anchoring root (AC-0001), and for a path carrying a `..` segment (AC-0002).
- The body instructs Ask-first for an absolute-only resolution outside the repository, realpath disclosed first, citing ADR-0030 D7 (AC-0003).
- The body states that a personal-scope destination outside the repository stays legitimate, with realpath disclosure as its control (AC-0004).
- The body states all three arms, so no single verdict satisfies it (AC-0005).
- `references/agentbundle-layout.md` carries the same distinction or points at the body that owns it, so a stale reference cannot contradict a corrected body (AC-0006).
- `packs/product-engineering/tests/pack/test_frame_intent_shaping_review.py` passes unamended. Construction check, no criterion: it constrains verification mechanics rather than describing contract behaviour.

**Approach:**
- Move the distinction into both homes together — the body and `references/agentbundle-layout.md` — because a reference carrying the old single verdict leaves the adopter two answers. AC-0006 is what makes that non-optional.

**Done when:** the pack suite is green, the prose assertions cover all three escape forms, and `agentbundle validate` accepts the manifest.

**Touches:** packs/product-engineering/.apm/skills/frame-intent/SKILL.md, packs/product-engineering/.apm/skills/frame-intent/references/agentbundle-layout.md, packs/product-engineering/tests/pack/*.py

### T2: The refusal is observed once at the consumer

**Depends on:** T1

**Mode:** Visual / manual QA

**Tests:**
- Invoke `frame-intent` with a repo-root `output_dir` whose resolution passes through a symlink out of the repository. Record the invocation, the observed refusal, and the tree state showing no file was created (AC-0007).
- Record any scope documented but not exercised.

**Approach:**
- This is the only evidence in the slice that reaches behaviour rather than wording. T1's assertions prove the instruction; nothing in them proves an agent follows it.

**Done when:** the session is recorded in `notes/verification-ledger.md` with its observed output.

**Touches:** docs/specs/frame-intent-symlink-escape-refusal/notes/verification-ledger.md

## Rollout

Pack content only. Adopters pick it up on the next install. One behaviour change to flag in the pack's changelog entry, and it is narrower than it first looks: an adopter whose configured path crosses a symlink out of its anchoring root, or carries a `..` segment, starts getting a refusal where they previously got a prompt. An adopter whose absolute path simply resolves outside the repository keeps the prompt, unchanged.

## Risks

- **Collapsing three arms into one verdict.** The likely defect in either direction: refusing everything contradicts D7 and breaks a legitimately configured out-of-tree destination; asking about everything contradicts D6 and the security control. AC-0003, AC-0004 and AC-0005 fail on the first, AC-0001 and AC-0002 on the second, and AC-0005 is the criterion to check first in review.
- **Prose that reads right and is never followed.** Accepted and recorded in the spec's `## Assumptions`; T2's single session is the mitigation, and it is one observation rather than a suite.

## Changelog

- 2026-09-20 — Split three ways after shaping review found ADR-0030 D6 already rejects `..`, so it was never an Ask-first case; the reference-doc criterion and the instruction-level wording of each criterion came from the same round. Originally drafted as a separate slice of `intent-identity-and-registration`, split out of `intent-placement-and-admission` so a safety change with prose-level evidence is reviewed on its own terms. Narrowed the same day to the symlink arm: the brief's blanket refusal claim traced to no source and contradicted ADR-0030 D7, while the security checklist's link-following control covers the symlink case alone.
