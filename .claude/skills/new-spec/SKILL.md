---
name: new-spec
description: Use this skill when the user wants to start a new feature with a spec, or wants to write a spec for something they're about to build. Triggers on "new spec", "write a spec for X", "let's spec this out", "start a feature for…". Spec-driven development; the spec drives implementation. Do NOT use for cross-cutting proposals (use `new-rfc`) or recording decisions (use `new-adr`).
---

# Skill: new-spec

Create a new feature spec under `docs/specs/<feature>/` with both `spec.md`
and `plan.md`.

## When to invoke

The user is about to build something nontrivial. The spec is the contract;
the plan is the strategy. Even a one-day feature benefits from a one-paragraph
spec — it forces the question "what does done look like?" before any code.

## Procedure

1. Pick a kebab-case feature name from the user's description. Keep it short
   and noun-y: `user-onboarding`, `webhook-retries`, not
   `improve-the-onboarding-experience`.

2. Create the directory and copy templates:

   ```bash
   mkdir -p docs/specs/<feature>
   cp docs/_templates/spec.md docs/specs/<feature>/spec.md
   cp docs/_templates/plan.md docs/specs/<feature>/plan.md
   ```

3. Fill in the spec first — including the **Contract tests** section. Push
   back hard on these failure modes:
   - **Behavior section is vague.** "It should be fast" is not a behavior.
     "Returns within 200ms at p99 for payloads under 1KB" is.
   - **Contract tests section empty or hand-wavy.** Contract tests are part
     of the spec, not an afterthought — if you can't write the test for a
     Behavior bullet, the bullet is too vague. Sharpen the bullet, then the
     test follows.
   - **No non-goals listed.** Specs without explicit non-goals get
     scope-crept by both humans and agents. Make the user list at least
     two things this feature explicitly will not do.
   - **No acceptance criteria.** Without a checklist, "done" is opinion.

4. Fill in the plan second. The plan should:
   - Cite any ADRs or RFCs it follows from.
   - Break the work into tasks small enough to be a single PR each.
   - Carry **construction tests** per task — `Tests:` before `Approach:`
     in each task, designed up front. "We'll test it" is not a strategy.

   Push back hard on these plan-stage failure modes (mirror of step 3):
   - **Task too big.** "Implement the feature" is not a task; "add the
     validation function for X" is. Each task should fit a single PR
     and a single context window. Split coarse tasks until they do.
   - **`Depends on:` omitted.** Every task must state `Depends on:`
     explicitly — prior task IDs or `none`. Don't let authors lean on
     task order to imply dependency; that hides serial-by-default
     thinking and makes the plan unparseable.
   - **Verification mode unstated.** Every task must declare its mode —
     TDD, goal-based check, or visual / manual QA. Silent defaults
     produce mock-shape tests on config-shape tasks and untested
     invariants on logic-shape tasks.
   - **Tasks without spec mapping.** Each task should reference which
     Behavior bullet (or Contract test) in the spec it implements.
     Orphan tasks are scope creep in disguise; behaviours with no
     implementing task are gaps.
   - **Specificity miss.** Task descriptions should reference exact
     file paths and function or symbol names where they're known.
     "Update the parser" is too coarse to verify; "add a null-check
     in `parser/lex.ts:Lexer.next`" is the right level.

5. Update `docs/specs/README.md` to add the feature to the active list.

6. Remind the user: when implementation diverges from the spec, the spec is
   wrong. Update the spec in the same PR.

## Anti-patterns to refuse

- Drafting a spec for something already half-built without checking against
  the existing code → ask the user to either align the spec with current
  behavior (and note any divergences) or write a new spec for what should
  change.
- Writing a spec that reads like a design doc (full of implementation) → the
  spec is the contract, not the design. Move implementation detail to
  `plan.md`.
- Skipping non-goals → mandatory section.
