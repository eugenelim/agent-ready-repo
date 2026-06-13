# How to fix a bug

You have a defect — a deviation between what the code does and what it's supposed to do — and you want to drive it through the project's fix discipline rather than vibe-patching it. The `bug-fix` skill (shipped in `core`) is the entry point. This page walks the path from "I have a bug" through "the fix is in main and the regression test will catch this if it ever comes back."

For the *why* behind the loop discipline the skill runs under the hood, read [the core pack as a system](../explanation/core-pack.md). This guide is task-oriented; it tells you what to type and what to expect back.

## Prerequisites

- The `core` pack installed in your target repo.
- A working directory where you can edit, commit, and run gates (lint / typecheck / test).
- Either a reproducer in hand, or enough signal (stack trace, log line, user report) to drive toward one. The skill won't let you skip the reproducer step — see [Step 1](#step-1--reproduce-the-bug).

## Is `bug-fix` the right entry point?

| Situation | Skill to invoke |
| --- | --- |
| Code does the wrong thing and you want to fix it | `bug-fix` |
| Code does what was specified but the spec is wrong | `new-spec` — this is a behavior change, not a fix |
| Refactor that preserves behavior | Open a PR; skip both skills |
| You don't know yet whether it's a bug or intended behavior | Investigate first; come back when the answer is "bug" |

The line that matters: `bug-fix` is for **deviations from intended behavior in code that already exists.** If the conversation turns into "actually this should work differently," the skill stops and tells you to switch to `new-spec` — that boundary is in the skill description, not a mid-flow auto-routing.

> **Invoke skills by name.** Claude Code's description-based auto-discovery is best-effort — natural phrasings like "fix this bug" usually fire the skill, but not always. **Naming the skill in your request guarantees it fires.** Use the name-the-skill form below whenever you want the discipline, including on edge cases where description matching wouldn't pick it up.

## Step 1 — Reproduce the bug

This is the load-bearing step. No reproduction, no fix — the skill will refuse to draft code until you have one of: a failing test, documented manual steps that fail reliably, or a captured error / stack trace / log signature. The obvious fix is wrong about a third of the time, and you can't tell which third until the bug fails red in front of you.

Name the skill in your invocation. Two worked invocations:

```
use the bug-fix skill to diagnose and fix the off-by-one in the
pagination cursor on the orders list endpoint — repro: GET
/orders?cursor=X returns 11 items instead of 10
```
(Reproducer is in hand — a curl that returns the wrong count. The skill goes straight to writing the failing test.)

```
use the bug-fix skill to investigate the intermittent 500 from the
checkout webhook receiver — repro is flaky, only on production
traffic shape
```
(Differs from above: the reproducer is flaky, not in-hand. The skill refuses to draft a fix without a deterministic reproduction — if you can't build one, it stops and asks rather than writing speculative code.)

Natural phrasings (`fix this bug`, `this is broken`, `investigate this regression`) match the skill's description and often trigger it, but description matching isn't guaranteed. Lead with `use the bug-fix skill to …` whenever you want the discipline to fire reliably.

## Step 2 — Write the failing test (red)

Once the bug is reproducible, the skill writes a test that fails *because of the bug*. The test pins the **observable contract being violated**, not the current implementation — so it survives the fix and lives in the suite as the regression test.

The skill pushes back on two common failure modes here:

- **Mock-shape assertions.** `expect(mock).toHaveBeenCalledWith(...)` when the observable contract is actually a returned value or a state change. Test the contract, not the implementation.
- **Test passes for the wrong reason.** Before declaring the test red, the skill runs it against the unfixed code and confirms it fails *because of the bug*, not because the setup is broken.

The failing test you write here is the regression test you ship. Don't plan to delete it after the fix lands.

## Step 3 — Identify root cause before writing the fix

Symptom-hunting is the most expensive failure mode in bug fixing. Before the diff opens, the skill writes down a one-line answer to each:

1. **Where is the defect actually?** In the called function, the caller, their shared assumption, or upstream of both? A null that crashes in `parse()` may originate in the loader that should never have produced null.
2. **When did it start?** `git log` and `git blame` on the affected code. For regressions, the breaking commit often tells you why; even for non-regressions, the surrounding history surfaces original intent.
3. **Could the same class of bug exist elsewhere?** Grep for the same pattern. If yes, decide whether the fix widens or whether you file follow-ups and add an explicit non-goal ("fix here only").

These three answers go in the commit body. The diff shows *what*; the commit body shows *why*.

## Step 4 — Write the minimum fix

The smallest change that turns the failing test green. The skill refuses to fix adjacent issues in the same PR — each cleanup is its own PR with its own justification. Bug-fix PRs are for fixing the named bug.

The exception is the same-area, same-concern, mechanical ride-along carve-out described in the [`work-loop` skill](../../../../packs/core/.apm/skills/work-loop/SKILL.md). A typo on the line above the fix is fine; a refactor of the surrounding module isn't. When in doubt, defer.

## Step 5 — Verify root vs. symptom

Look at the diff against the answers from step 3. Does this fix address the root cause, or does it mask the symptom? The skill refuses these symptom-only anti-patterns:

- **Catch-all exception handlers** that swallow the bug instead of making the failing call not throw.
- **Defensive checks at every call site** when the invariant should hold upstream. Twelve `if (x == null) return` callers of a function that should never return null is masking, not fixing.
- **Retries around flaky code** when the right fix is to make the code deterministic.
- **Feature flags that disable the broken path** instead of fixing it. Flags are for staged rollout, not for hiding bugs.

If the failing test from step 2 still passes under a symptom-only fix, the test is wrong — go back to step 2 and sharpen it.

## Step 6 — Run gates and ship

Run lint / typecheck / tests and open the PR. The commit follows Conventional Commits format (`fix(<scope>): <subject>`) with a body documenting the root cause from step 3.

For multi-file fixes, treat the work as non-trivial and run it through `work-loop` for the gate / review / fix iteration: the same iteration cap, stasis detection, and adversarial-reviewer pass that any other multi-file change goes through. See [how to plan and execute non-trivial work](plan-and-execute-non-trivial-work.md) for the loop mechanics. The `bug-fix` skill itself doesn't dispatch the loop — that's your call based on the diff's shape.

If there's a tracker ticket, the final step is commenting the PR URL on it and transitioning state. The mechanism is adopter-specific (`gh issue comment`, Jira MCP, Linear CLI, or whatever your team uses); the obligation — keeping the ticket synced — is universal.

## Variations

### Single-file fix vs. multi-file fix

A one-file, one-function fix runs steps 1–6 inline; the work-loop overhead isn't worth it. If the fix touches multiple files or crosses a module boundary, treat it as non-trivial work and run the gate / review / fix iteration through `work-loop` at step 6. That's an operator-side call — the skill doesn't decide.

### Production hotfix pressure

The discipline still applies when production is on fire, but the order can flex on your call. Step 1 (reproduce) and step 4 (minimum fix) are non-negotiable. Step 2 (failing test) can ship as a follow-up PR if writing it would block the hotfix by more than minutes — file the follow-up explicitly so the regression test still lands. This is adopter pressure-handling, not skill behaviour; the skill itself runs regression-test-first.

### Reproducer needs investigation

If the bug is intermittent or production-only, the skill refuses to draft a fix without a deterministic reproduction. If you can't build one after investigation, the skill stops and asks rather than writing speculative code. "Couldn't reproduce on my machine" is a hypothesis worth testing, not a closing condition.

## Pitfalls

> **Fixing forward without a reproduction.** The obvious fix is wrong about a third of the time, and the only way to tell is the failing test. Don't skip step 1.

> **Fixing the bug plus adjacent cleanup in one PR.** Each cleanup is its own PR with its own justification. The same-area mechanical ride-along carve-out is narrow — a typo, not a refactor.

> **Adjusting the spec or the test to match the buggy behavior.** If the spec and the fix disagree, one of them is wrong. Surface that explicitly; don't paper over it.

> **Closing as "not reproducible" without trying hard enough.** Document what was tried, on what version, with what data, before giving up. The cost of an extra hour of investigation is small compared to a bug that resurfaces in three months.

> **Deleting the failing test after the fix turns it green.** The test is the regression test. It lives in the suite forever; that's the point.

## When not to use this workflow

- **New features.** If "fixing" the bug means changing what the code *should* do, that's a behavior change. Use `new-spec` instead — see [how to plan and execute non-trivial work](plan-and-execute-non-trivial-work.md).
- **Refactors that preserve behavior.** No bug, no fix — just a PR with a clear rationale. See [`docs/CONVENTIONS.md` § Pull requests](../../../CONVENTIONS.md#pull-requests).
- **Spikes and throwaway exploration.** If the output is going to be thrown away, the skill's discipline adds friction for no gain.
- **You don't know whether it's a bug.** Investigate first; come back when you have an answer shaped like "the code does X, it should do Y."

## Related

- [The core pack as a system](../explanation/core-pack.md) — why the discipline exists and how the parts compose.
- [`bug-fix` skill](../../../../packs/core/.apm/skills/bug-fix/SKILL.md) — authoritative procedure.
- [How to plan and execute non-trivial work](plan-and-execute-non-trivial-work.md) — the loop discipline that `bug-fix` hands off to for multi-file fixes.
- [`docs/CONVENTIONS.md` § How we do non-trivial work](../../../CONVENTIONS.md#how-we-do-non-trivial-work) — the contributor-side rationale.
- [`docs/CONVENTIONS.md` § Commits](../../../CONVENTIONS.md#commits) — Conventional Commits format and the body conventions the skill follows.
- [How to write a new RFC](../../governance-extras/how-to/new-rfc.md) — when a "bug" turns out to be a cross-cutting design question.
- [How to record a new ADR](../../governance-extras/how-to/new-adr.md) — when the root-cause analysis surfaces a decision worth pinning.
