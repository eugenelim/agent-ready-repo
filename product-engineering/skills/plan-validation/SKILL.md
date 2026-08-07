---
name: plan-validation
description: Use to turn a converged product's load-bearing assumptions into a validation plan — and to scaffold the primary-research instruments that would test them. Triggers on "plan the validation", "how do we validate these assumptions", "turn assumptions into a validation plan", "scaffold an interview guide / usability test", "what would confirm this". Produces assumption → kill-condition → real-world-activity hooks and the instrument scaffolds (interview guide, usability-test plan, transcript-synthesis frame). Do NOT use to run the sessions (out of charter — a human runs them), to test a single bet (use `de-risk-intent`), or to converge (the discovery loop's job).
---

# Skill: plan-validation

**Turn a converged product's load-bearing assumptions into a validation plan, and
scaffold the instruments that would test them.** This is the discovery loop's
**validation** stage (the third leg of divergence → convergence → validation). A
converged blackboard is internally coherent but **not validated** — *converged ≠
validated* — and this skill makes that gap a worked plan, not a footnote.

It is **prompt-only** (CHARTER Principle 3): no engine, no survey tool, no
transcript pipeline — the agent writes the plan and the instrument scaffolds. **No
new agent, no new reviewer.**

## Output rendering

Key–value / one record — For a single record's fields, use an aligned key: value list, not a two-row table.

## The charter boundary (read this first)

`plan-validation` **scaffolds and synthesizes**; **a human runs the sessions.**

- **In charter:** designing the validation plan, authoring the interview guide /
  usability-test plan, and synthesizing transcripts a human brings back.
- **Out of charter:** running interviews, facilitating live usability tests,
  recruiting participants, full business-viability / market-sizing / pricing, GTM.

This is the GAP-1 boundary of a code-building catalogue: we design the test; people
run it.

## When to invoke

1. There is a **converged or converging spine** with load-bearing assumptions —
   typically at G2, when the decision brief is being emitted as a connected
   hypothesis.
2. The assumptions have **validation hooks worth planning** — kill conditions that
   only real users can confirm (the `to-validate` label). A fully `grounded` spine
   with no `to-validate` assumptions needs no validation plan; say so.

## Procedure

1. **Collect the assumptions and their hooks.** Read each load-bearing assumption
   from the blackboard / the de-risked intents — each already carries (or you
   author) a **validation-hook field** (`de-risk-intent`'s
   `assumption → kill_condition → activity`).
2. **Turn each into a validation-plan entry.** For each:
   - `assumption` — restated.
   - `kill_condition` — the predeclared line in the test's own currency (reuse
     `de-risk-intent`'s kill-condition discipline — declare it *before* the
     result).
   - `activity` — the real-world activity that confirms or enriches it: interview /
     diary study / Wizard-of-Oz pilot / usability test.
   - `validation_status` — `hypothesis → validating → validated | refuted`.
3. **Scaffold the primary-research instruments** the activity needs (the templates
   below) — the artifact a human takes into the field.
4. **Write the `validation-plan` slot** (the discovery-loop sidecar schema) and set
   each plan-tree node's `validation_status` + `validation_hook`, so *converged ≠
   validated* is a **structural property of the tree**.
5. **Synthesize, when transcripts come back.** Given transcripts a human ran,
   cluster findings against the assumptions and flip each `validation_status` to
   `validated` / `refuted` — a refuted assumption routes back to the loop (a
   rejection/recovery cascade).

## The instrument scaffolds (carried schemas, prompt-only)

**Interview guide:**

```markdown
# Interview guide — <assumption>
- Goal: confirm/refute "<assumption>" against the kill condition
- Screener: <who qualifies as a target user>
- Warm-up: <2–3 rapport questions>
- Core (non-leading): <open questions probing the real activity, not the product>
- Behavior over opinion: "Tell me about the last time you…" (not "would you…")
- Wrap: <anything we missed?>
```

**Usability-test plan:**

```markdown
# Usability-test plan — <screen/flow>
- Task scenarios: <realistic tasks, not feature tours>
- Success measure: <task completion / time / error — the predeclared bar>
- Think-aloud prompts; what to observe (not what to hope for)
- Severity rubric for issues found
```

**Transcript-synthesis frame:**

```markdown
# Synthesis — <assumption>
- Evidence for / against (per participant)
- Pattern across participants
- Verdict vs. kill condition: validated | refuted | inconclusive (run more)
```

## Anti-patterns to refuse

- **Claiming validation from desk research.** Desk-grounding is not validation; the
  hook stays `to-validate` until a real-world activity confirms it.
- **Running the sessions.** Out of charter — scaffold and synthesize; a human runs
  them.
- **Leading questions / opinion over behavior.** "Would you use this?" validates
  nothing; ask about the last time they did the activity.
- **A kill condition set after the result.** Declare the line before the activity
  runs (the `de-risk-intent` discipline).
- **Building a research engine.** Prompt-only — the agent writes the plan and the
  scaffolds; there is no survey tool or transcript pipeline.
