# Plan: a placement path that resolves through a symlink out of its root refuses

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting
- **Repository anchors:** `packs/product-engineering/.apm/skills/frame-intent/SKILL.md:229-243` (the "Resolve, then surface, then write" block and the untrusted-origin sentence this supersedes); `packs/product-engineering/.apm/skills/frame-intent/references/agentbundle-layout.md:56-58` (the same rule restated in the shipped schema doc, which must move with it); `packs/product-engineering/tests/pack/test_frame_intent_shaping_review.py` (the prose-assertion pattern this pack already uses). Named uncertainty: prose verification cannot establish behaviour, recorded as an accepted limitation in the spec's `## Assumptions`.

## Approach

One distinction, two homes, one test file. The skill body's single untrusted-origin-confirm verdict splits in two: a symlink escape refuses, every other out-of-repository resolution keeps Ask-first. The reference doc that restates the rule moves with it, and the personal branch is untouched. The work is small; the care is in not over-reaching — a blanket refusal would contradict ADR-0030 D7 and break a destination an adopter legitimately chose, and that is the likely defect if this is rushed.

Amend prose, do not shorten it. The section already carries the anchoring and realpath rules that make an escape detectable; what changes is the verdict, not the detection.

## Constraints

- **The security control, for the symlink arm only.** `security-checklists/references/path-and-file.md:30-32` requires refusing to follow links into untrusted trees, and `AGENTS.md` forbids cutting a security control. That is why a confirmation prompt is not sufficient for that arm.
- **ADR-0030 D7 governs the other arm**, and this slice conforms to it rather than superseding it: a repo-sourced value resolving outside the repo without a symlink stays an untrusted-origin, Ask-first deviation. D6 supplies its control by disclosing the resolved absolute path.
- **ADR-0030** keeps each pack's default and posture in its own skill body, so this rule belongs in `frame-intent`'s body rather than in a shared contract.
- **Prompt-only.** `frame-intent` reads a file and reasons about a path; there is no engine behind it, and this slice adds none.

## Construction tests

**Integration tests:** none — there is no code seam to integrate.

**Manual verification:** one session. Invoke `frame-intent` in a tree whose repo-root `output_dir` resolves outside the repository, and record that it refuses rather than offering a confirmation. Recorded in the verification ledger with the invocation and observed output. A prose assertion cannot distinguish a body that says "refuse" from an agent that asks anyway; this session is the only evidence that reaches the behaviour.

## Durable-output map

No `## Durable Outputs` table in the spec, so nothing to mirror. Each task names the criteria it discharges.

## Tasks

### T1: The repository branch refuses, and the personal branch does not

**Depends on:** none

**Mode:** Goal-based check

**Tests:**
- The body states refusal for a resolution passing through a symlink out of the anchoring root (AC-0001).
- The body keeps Ask-first for a `..` segment and for an absolute value resolving outside the root, with the resolved absolute realpath disclosed first (AC-0002).
- The body states that a personal-scope destination outside the repository stays legitimate, with realpath disclosure as its control (AC-0003).
- The body states both arms so neither a blanket refusal nor a blanket confirmation satisfies it (AC-0004).
- `packs/product-engineering/tests/pack/test_frame_intent_shaping_review.py` passes unamended (AC-0005).

**Approach:**
- Move the distinction into both homes together — the body and `references/agentbundle-layout.md:56-58` — because a reference doc carrying the old single verdict leaves the adopter two answers.

**Done when:** the pack suite is green, the prose assertions cover all three escape forms, and `agentbundle validate` accepts the manifest.

**Touches:** packs/product-engineering/.apm/skills/frame-intent/SKILL.md, packs/product-engineering/.apm/skills/frame-intent/references/agentbundle-layout.md, packs/product-engineering/tests/pack/*.py

### T2: The refusal is observed once at the consumer

**Depends on:** T1

**Mode:** Visual / manual QA

**Tests:**
- Invoke `frame-intent` with a repo-root `output_dir` whose resolution passes through a symlink out of the repository. Record the invocation, the observed refusal, and the tree state showing no file was created (AC-0006).
- Record any scope documented but not exercised.

**Approach:**
- This is the only evidence in the slice that reaches behaviour rather than wording. T1's assertions prove the instruction; nothing in them proves an agent follows it.

**Done when:** the session is recorded in `notes/verification-ledger.md` with its observed output.

**Touches:** docs/specs/frame-intent-symlink-escape-refusal/notes/verification-ledger.md

## Rollout

Pack content only. Adopters pick it up on the next install. One behaviour change to flag in the pack's changelog entry: an adopter whose repo-root `output_dir` currently resolves outside the repository, and who has been confirming that prompt, will start getting a refusal.

## Risks

- **Over-reach into a blanket refusal.** The likely defect is wording that refuses every out-of-repository resolution, which contradicts ADR-0030 D7 and breaks both the personal branch and a legitimately configured out-of-tree destination. AC-0002, AC-0003 and AC-0004 exist to fail in that case and are the criteria to check first in review.
- **Prose that reads right and is never followed.** Accepted and recorded in the spec's `## Assumptions`; T2's single session is the mitigation, and it is one observation rather than a suite.

## Changelog

- 2026-09-20 — Drafted as a separate slice of `intent-identity-and-registration`, split out of `intent-placement-and-admission` so a safety change with prose-level evidence is reviewed on its own terms. Narrowed the same day to the symlink arm: the brief's blanket refusal claim traced to no source and contradicted ADR-0030 D7, while the security checklist's link-following control covers the symlink case alone.
