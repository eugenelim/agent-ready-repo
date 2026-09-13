---
title: "Run the loop"
summary: "Plan, execute, gate, review, decide — and do not enter review on a red build."
pack: core
kind: how-to
order: 3
---

# Run the loop

**Step 3 of 4 — Run the loop**
<!-- rung: packs/core/JOURNEY.md -->

**What changes:** An approved contract becomes a reviewed change, with the gates and rounds recorded.
<!-- rung: packs/core/JOURNEY.md -->

**What you need first:** An approved spec and its plan.
<!-- rung: authored -->

*Skipping costs:* Work proceeds without a stated plan, and review rounds are spent on findings a gate would have caught.
<!-- rung: authored -->

**Concepts:**
<!-- rung: authored -->

- [The two-room model](../explanation/two-room-model.md) explains why shaping and building are separate rooms.
- [Why work begins with an artifact](../explanation/why-work-begins-with-an-artifact.md) explains why the loop refuses to start from a chat message.

## What you will run

| Skill | Needs | What it produces | Needed? |
| --- | --- | --- | --- |
| `work-loop` | An approved spec and plan | The change, its gates, and its review rounds. | Required |
| `bug-fix` | A reproducible defect | The fix, with a test that fails without it. | Optional |

Prompts go into an AI agent session with this pack installed — the same session
throughout. `<slug>` is the short kebab-case name for this piece of work; it
names the spec directory and stays the same until the work closes.

<!-- rung: packs/core/JOURNEY.md -->

## Run `work-loop` — build it

**You type:**
<!-- rung: packs/core/.apm/skills/work-loop/SKILL.md -->

```
Run the work loop on this spec.
```

**Agent returns:**
<!-- rung: packs/core/.apm/skills/work-loop/SKILL.md -->

> **Agent:** Done — I've written the loop running — plan, execute, gates, review, decide — pausing where a human decision is required. Nothing was written to disk.

**You push back:**
<!-- rung: packs/core/.apm/skills/work-loop/SKILL.md -->

> **You:** You moved to review with a failing gate. Go back to gates; review findings on a red build are noise.
>
> **Agent:** I returned to gates, fixed the failure, and re-entered review from a green build.

**Output varies** with the risk triggers the work fires, which decide whether it runs light or full.
<!-- rung: packs/core/.apm/skills/work-loop/SKILL.md -->

**You decide:** Approve the plan before execution — the pack's `approve-plan` gate. This is where scope is still cheap to change.
<!-- rung: packs/core/JOURNEY.md -->

**Check (testable):** Ask which gate last ran and what it returned; this surfaces a loop reporting progress it has not verified.
<!-- rung: packs/core/.apm/skills/work-loop/SKILL.md -->

**Watch out for:** The loop reports state confidently, including state it inferred. Notice a review round starting while a gate is red — findings from a broken build waste a round.
<!-- rung: packs/core/.apm/skills/work-loop/SKILL.md -->

**Writes no artifact.** It reports in the agent session and does not change files.
<!-- rung: packs/core/.apm/skills/work-loop/SKILL.md -->

**What it looks like:**
<!-- rung: authored -->

```markdown
Work loop — <slug>

Phase: GATES
Gates: lint ok · typecheck ok · tests 3 failed
Review rounds: 0

Next: fix the failing gate before entering review
```

*Section shape only. The loop reports in the session; the artifacts it writes belong to the spec — confirm the shape against what you get back.*

## Run `bug-fix` — a bounded defect

**You type:**
<!-- rung: packs/core/.apm/skills/bug-fix/SKILL.md -->

```
Fix this: the login test passes locally and fails in CI about one run in five.
```

**Agent returns:**
<!-- rung: packs/core/.apm/skills/bug-fix/SKILL.md -->

> **Agent:** Done — I've written a diagnosis, a failing test that reproduces it, and the fix that makes it pass. Nothing was written to disk.

**You push back:**
<!-- rung: packs/core/.apm/skills/bug-fix/SKILL.md -->

> **You:** The test you added passes with and without the fix. Make it fail on the original code first.
>
> **Agent:** I reverted the fix, watched the test pass anyway, and rewrote it to bind to the actual race before reapplying.

**Output varies** with how reproducible the defect is and how much of the system it touches.
<!-- rung: packs/core/.apm/skills/bug-fix/SKILL.md -->

**No decision gate at this step.**
<!-- rung: authored -->

**Check (falsifiable):** Revert the fix and ask whether the new test fails; this surfaces a test that asserts the fix rather than the defect.
<!-- rung: packs/core/.apm/skills/bug-fix/SKILL.md -->

**Watch out for:** A test written after a fix tends to describe the fix, and passes on the broken code too. The revert is the only check that settles it.
<!-- rung: packs/core/.apm/skills/bug-fix/SKILL.md -->

**Writes no artifact.** It reports in the agent session and does not change files.
<!-- rung: packs/core/.apm/skills/bug-fix/SKILL.md -->

**What it looks like:**
<!-- rung: authored -->

```markdown
Bug fix — <defect>

Reproduction: <the failing case>
Diagnosis: <the actual cause, not the symptom>
Test added: <what it binds to>
Verified: fails on the original code, passes on the fix
```

*Section shape only. This skill reports in the session and writes its change to the codebase — confirm the shape against what you get back.*

## Where this leads

**Done with this step:** You can move on when every mechanical gate is green and review has returned clean.
<!-- rung: authored -->

Stage 3 of four, and the pack's first human gate. Plan approval is where scope is still cheap to change.

**Next:** [Close it out](close-it-out.md).
<!-- rung: authored -->

**Go deeper:** [the `core` pack reference](../explanation/core-pack.md) — how the loop, the gates and the reviewers fit together.
<!-- rung: authored -->
