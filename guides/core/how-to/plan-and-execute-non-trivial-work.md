---
title: How to plan and execute non-trivial work
summary: Turn an approved spec into a locked plan, checked implementation, independent review, and merge-ready change.
pack: core
kind: how-to
---

# How to plan and execute non-trivial work

**Use this when:** You are about to start a feature, refactor, or multi-file change that goes beyond a one-line edit.
**Prerequisites:** `core` pack installed, a working directory with edit/commit/gate access, and familiarity with the four mandatory spec sections; see Prerequisites below.
**Result:** A spec and plan in `docs/specs/<feature>/`, a green-gates PR, and an adversarial-reviewer-clean diff ready to ship.

You have a feature to build, a refactor to drive, a migration to run — anything past a one-line edit. This guide walks the path from "I'm about to start" through "the PR is green and the reviewer is clean", using the two skills that drive it: `new-spec` and `work-loop`.

```text
Use the new spec skill to design webhook retries, then use work-loop to implement it.
```

For the *why* behind this discipline, read [the core pack as a system](../explanation/core-pack.md). This guide is task-oriented; it tells you what to type and what to expect back.

## Prerequisites

- The `core` pack installed in your target repo.
- A working directory where you can edit, commit, and run gates (lint / typecheck / test).
- Familiarity with the mandatory spec sections — Agent Rules, Testing Strategy and Acceptance Criteria, read in the frame Outcome and What Changes set above them — see the `new-spec` skill's spec-and-plan contract reference.

## Pick your entry point

Two skills, one workflow:

| Situation | Skill to invoke |
| --- | --- |
| New feature or significant change — no spec yet | `new-spec`, then `work-loop` |
| Spec already exists in `docs/specs/<feature>/` | `work-loop` (it reads the spec) |
| Multi-file bug fix | `bug-fix` — see [how to fix a bug](bug-fix.md) |
| One-line edit, typo, single config tweak | Skip the loop — overhead isn't worth it |

If you're unsure whether the change is trivial, default to the loop. The cost of running it on a small task is one extra minute; the cost of vibe-coding a non-trivial task is a re-do.

:::tip
**Invoke skills by name.** Claude Code's description-based auto-discovery is best-effort — natural phrasings like "let's spec this out" usually fire the right skill, but not always. **Naming the skill in your request guarantees it fires.** Use the name-the-skill form below whenever you want the discipline, including on edge cases where description matching wouldn't pick it up.
:::

## Run `new-spec` (when no spec exists)

The skill writes `docs/specs/<feature>/spec.md` and `plan.md`, and gates body content on assumption sign-off.

Name the skill in your invocation. Two worked invocations — one backend, one frontend:

```
use the new-spec skill to design webhook retries with exponential
backoff for the payment-events stream
```
(retry logic is a state machine — Testing Strategy will pick TDD for this one.)

```
use the new-spec skill to spec the saved-filters chip on the
product-search results page
```
(the chip is a visible UI element — Testing Strategy will pair it with visual / manual QA, possibly automated.)

Natural phrasings (`let's spec out X`, `new spec: Y`, `write a spec for Z`) match the skill's description and often trigger it, but description matching isn't guaranteed. Lead with `use the new-spec skill to …` whenever you want the discipline to fire reliably.

### What to put in front of it

`new-spec` ingests whatever input you give it and surfaces what's missing. Any of these shapes work:

- A one-line idea ("add 2FA for admin login").
- A requirements doc or PRD pasted into the message.
- A linked ticket — Linear, Jira, GitHub issue. Reference the URL; the skill reads what's there.
- An upstream brief from a portfolio team (Feature Intent, Component Brief, or whatever shape your org produces).
- A bug report that's grown into a feature ("this thing should work differently").

The skill doesn't care which shape you brought. The assumption checkpoint is where missing information gets named, regardless of input shape — so an idea-shaped input surfaces more Unverified items, a brief-shaped input surfaces fewer. The output is the same: a spec and plan grounded in confirmed assumptions.

### What to expect

1. The skill scaffolds `docs/specs/<feature>/spec.md` and `plan.md` from the bundled templates.
2. It drafts assumption candidates across Technical / Product / Process categories, **verifies each before filing it** (a repo read, a web lookup, or a read-only probe — not a sweep), then **stops** and emits an `ASSUMPTIONS I'M MAKING:` block split into `Verified` (each with a one-line citation of the check) and `Unverified` (each needing your input). The check happens before the bullet gets filed, not after.
   Some candidates cannot be settled at the checkpoint. The skill's assumptions step owns what happens to one — when its routing rule fires, and where the claim goes — under the anchor `load-bearing-claim-routing`. Read it there; this guide states neither, so the two cannot drift.
   Some code works on every entry of a shared structure without naming each one, such as search, rebuilds, and cleanup. When your change adds or changes a member of such a structure, like a new node kind in a graph or a new entry in a registry, the skill does more. It checks what that member can break elsewhere. Then it writes a criterion for each existing behavior that must survive. It skips this for a private helper with one caller, or for a new item that every shared read path already filters out, once it has confirmed that from the repository. The rules live in [the skill's shared-substrate preservation reference](../../../packs/core/.apm/skills/new-spec/references/shared-substrate-preservation.md).
3. You read the Unverified list and confirm or revise. If the Unverified list is empty, the skill surfaces the Verified list with the highest-stakes item called out and asks you to confirm *that one specifically* — a vague "looks good" doesn't count.
4. Spec body fills in: Outcome (two sentences), What Changes (the delta as bullets), Agent Rules (including at least one structural `Never do`), Testing Strategy with a verification mode per outcome, Acceptance Criteria.
5. Plan body fills in: tasks led by `Tests:`, an `Approach:` only where the task carries an ordering or seam decision, explicit `Depends on:`, verification mode per task.
6. `shaping-reviewer` first reads the draft contract cold for scope and observability. `adversarial-reviewer` then reads the complete spec and plan for construction risk; `security-reviewer` and `quality-engineer` remain later code-review lenses, each owning concerns the others do not repeat.
7. Every `adversarial-reviewer` report is persisted first, then classified from
   the persisted bytes. A report that is clean — by exact bytes, or by structure
   with nothing but blank lines around the clean sentence — closes the round
   without an adjudicator call. A report carrying findings, or
   `security-reviewer`'s coverage-disclosure footer, goes through
   `finding-adjudicator` before the author classifies it or edits either
   artifact. Only sustained findings can change the spec or plan; refuted
   findings stay in the audit, and an indeterminate result stops for your
   direction.
8. Before each repair, the author marks the finding `draft-origin` or
   `prior-round-repair`. If the review history cannot establish either one,
   unresolved origin stops for your direction. When a green gate supports a
   disposition, the author also states what that gate proves and one relevant
   blind spot; the spec-status lint's own module contract remains the source for
   its scope.
9. Review iterates to direct or adjudicated clean — usually one to two passes. If it
   cannot reach clean in three, the skill stops and asks for human direction;
   the spec likely has a structural problem, not a wording one.
10. The skill reminds you that spec drift is a bug — update the spec in the same
    PR when implementation diverges. There is no spec index to maintain: specs
    are discovered by listing `docs/specs/`.

If you want to stop here (pure planning, no build yet), this is the natural exit point. The spec and plan are durable; come back to `work-loop` whenever you're ready.

## Run `work-loop`

With a spec in place, invoke the loop by name. Same two domains carried through:

```
use the work-loop skill to implement docs/specs/webhook-retries
```
(TDD-mode tasks for retry logic; goal-based for wiring.)

```
use the work-loop skill to drive the saved-filters-chip spec
```
(visual / manual QA on the chip; goal-based on the URL-state plumbing.)

Naming the skill is the reliable form. The `work-loop` description also matches phrasings like "implement the X spec" or "let's work on Y", but the explicit form fires the loop's full discipline — gates, adversarial review, the iteration cap, the state machine — even on edges where description matching wouldn't pick it up automatically.

### What it does

The full procedure lives in [the `work-loop` SKILL.md](../../../packs/core/.apm/skills/work-loop/SKILL.md). The short version:

- **PLAN** — reads `spec.md` and `plan.md`, picks verification modes if not already set, and describes each test up front. For a TDD task, `Tests:` names the behavior, where it is checked, and how; PLAN writes no test code and adds no test file, so a run that stops after approval leaves the repository's tests passing. Pre-EXECUTE adversarial review fires automatically on spec amendments or on any of the four structural triggers (new module, new dependency, new abstraction, new top-level directory).
  - PLAN records a declined architectural addition only when it materially affects scope or design.
  - It sizes each task for one PR, then asks whether the review unit can be independently understood, verified, or reviewed. If yes, the unit proceeds; if not, it is split — or carries a transformation/reproducibility proof when it is mechanically uniform WIDE work.
  - About 2,000 reviewable behavior and test lines is a prompt for extra scrutiny, not a gate.
- **EXECUTE** — implements task by task. For a TDD task, the red test is written at EXECUTE: the agent writes the test at its real path and shows it fails for the right reason (red), then writes code until it passes (green), then tidies the code (refactor). Goal-based tasks run the `Done when:` one-liner; manual-QA tasks record the visual check.

  When the accepted criteria say an existing behavior must survive a change, the loop also loads a reference on the evidence that proves it: an independent expected side, an oracle seen to fail on a named mutation, and what counts as missing, stale, tautological, or feature-only. See [the preservation-evidence reference](../../../packs/core/.apm/skills/work-loop/references/preservation-evidence.md).
- **GATES** — lint, typecheck, tests. Mechanical, ordered, no editing the gate to make it pass.
- **REVIEW** — `adversarial-reviewer` reads the diff cold against `AGENTS.md` + `spec.md`. Findings come back as Blockers / Concerns / Nits with one-sentence fixes. In a full-mode run the supervisor closes review from structured review readiness: it asks for a reviewer selection, then a typed report per selected role, then an assessment of each finding, and it returns the task to implementation for each supported finding until a fresh report no longer carries it. Pre-approval review and light mode use `review-artifact.py` (`classify`, `raw-classify`, `inspect`, `record`) with a run id: `review-artifact.py record --run-id <uuid>` keeps one `<round>-record.md` per round under `.context/reviews/<run-id>/` and counts the review budget from those files. Pass `--operation-id <run-id>:<sequence>` and re-issuing the identical recording is a no-op rather than a second round, so a session that dies before it knows whether the write landed can simply repeat it. There, lifting the cap takes `--allow-retry-cap-override` with an `owner` authority reference passed as `--authority-ref`. Specialist reviewers run when the diff warrants. Either reviewer can return its findings as a typed report when the caller asks, and on a shared-substrate change `adversarial-reviewer` asks whether every reachable consumer class has a preservation criterion while `quality-engineer` asks whether each preservation criterion has current, independent evidence.
- **DECIDE** — requiredness decides each finding: work the current intent requires, or that blocks correctness or security, becomes the next review unit in the same session when it cannot share this one. Work no obligation names is excluded — acknowledged in the PR, captured only if its owner asks — not scheduled. If the same findings come back two iterations in a row, that is surfaced to a human; the iteration cap is what bounds the loop.

Sometimes the plan cannot yet know which function the code will hook into, or
how a design will be built. The plan then marks that spot
`implementation-discovered` in its design section and records four things:

- what will reveal the answer;
- the limits the answer must respect;
- the result it must deliver;
- how that result is checked.

When the answer turns up, you write it into the plan's design section as a
working-plan change between requests, and the supervisor commits it without a
new approval. The
[verification ledger](../../../packs/core/.apm/skills/work-loop/references/delivery-contract-lifecycle.md#verification-ledger)
keeps what the run observed. Don't use the mark to restate an acceptance
criterion.

For the end-to-end narrative with the parts in context, read [core-pack.md § How they tie together](../explanation/core-pack.md#how-they-tie-together).

### Termination cues you'll see

- **Gates green and review clean** → ship.
- **`work-supervisor.py status --check` exits 3, or a `retry-cap` decision opens** → the implementation retry cap fired. The loop stopped converging, so the default answer is to stop and re-plan or split the task, not to push past it; no replan, amendment, or approval resets the count. An agent running unattended should stop and surface it.
- **Diff is shrinking but findings aren't** → you're spot-fixing without addressing root cause. Back to PLAN.

If any of these fire and the work isn't done, the task is bigger than you thought. Re-plan rather than expanding scope silently.

## What you have now

This how-to has two exits, and they end in different places.

**If you stopped after PLAN** — you have an approved spec and plan at
`docs/specs/<feature>/`, both carrying your explicit approval. Nothing has been
implemented. Start `work-loop` when you are ready, or return to the spec when
the intended outcome changes.

**If you ran the loop through** — you have the change implemented against that
spec, every mechanical gate green, the adversarial reviewer and any triggered
security or quality reviewer reporting clean, findings resolved or explicitly
dispositioned, the spec marked `Shipped` and the plan `Done`, and a
merge-ready PR. The merge decision is yours; the loop does not take it.

## Variations

### Resume an in-flight spec

`work-loop` reads `docs/specs/<feature>/` and picks up from Git history and the committed `delivery/` records. Phrase as "resume the X work" or "continue on `docs/specs/X`". The Session Resumption protocol in the skill runs `work-supervisor.py status --json` first, then `next`, and answers what it issues. A deleted `.supervisor/` directory loses nothing, because the supervisor re-derives the run from commits and committed records.

### Spec amendment mid-flight

After `start`, the approval covers the spec's protected sections, its terminal intent, and the reviewed execution envelope. A change to tasks, tests, stubs, design, or approach is a working-plan edit: you make it between requests, while no attempt is open, and the supervisor commits it as a `replan` with no new approval. A change to a protected section or the terminal intent is refused and names its owner; it takes an amendment, which returns through review and both approvals and ends with `start` again. Record an execution observation through the [verification-ledger procedure](../../../packs/core/.apm/skills/work-loop/references/delivery-contract-lifecycle.md#verification-ledger).

### Parallel implementers (supervisor mode)

The supervisor issues one `implement-task` request at a time, in the plan's dependency order. When an `implementer` subagent is installed, the controller dispatches each plan task sequentially, one implementer at a time; the reviewer fan-out rules are in [`references/supervisor-mode.md`](../../../packs/core/.apm/skills/work-loop/references/supervisor-mode.md).

## Pitfalls

:::caution
**Reaching for `new-spec` because the change touches several files.** File count stopped deciding this a long time ago; risk decides it, and so does durability. A bounded, low-risk change you are doing now runs direct-light with its plan in the session and no spec at all, however many files it touches. Write a spec when the work needs a durable contract — a risk trigger fires, it needs queueing, another session, another person, an external orchestrator, an approval that outlives the context, or it defines published behavior. The discipline is the loop, not the document. A request that bundles independent tasks — no task depends on another, no two write the same files, and each finished diff stays in its own files — splits into one unit per task, and each unit is judged on its own. A plain edit to an existing agent-guidance file runs light, with a content-pin test: a test that checks the edited section's key phrases. It stays in full mode if it changes a tool surface, an authority or gate, a security boundary, or a published schema. A new guidance file and policy prose also stay in full mode.
:::

:::caution
**Editing `.supervisor/` or `delivery/` by hand.** The supervisor owns those records, and a hand edit refuses the next verb. Run the supervisor's verbs; don't reach in.
:::

:::caution
**Treating gates as sufficient.** Gates are necessary. Review catches what gates can't — missing edge cases, scope creep, spec drift. Don't skip the reviewer pass because "it'll be fine".
:::

:::caution
**Skipping pre-EXECUTE review on a structural change.** The four triggers (new module boundary, new dependency, new abstraction layer, new top-level directory) are exactly the cases where over-engineering is most expensive to undo. The cost of catching it at PLAN is a sentence; at REVIEW it's a re-do.
:::

:::caution
**Letting the spec drift from the implementation.** When implementation diverges from the spec, the spec is wrong. Update the spec in the same PR — drift is a bug, not paperwork debt.
:::

:::caution
**In Kiro, pick Vibe — not spec mode.** Kiro nudges hard toward its own spec-driven session (a generated `requirements.md` / `design.md` / `tasks.md`). For work the loop should own, choose **Vibe** at the session picker so `work-loop` drives; Kiro's spec mode is one-shot per task and doesn't iterate against a cold reviewer the way the loop does. There's no global off-switch — it's a per-session choice each time you start work. [Why the loop beats one-shot spec modes](../explanation/core-pack.md#how-it-differs-from-spec-kit-and-kiro-ide).
:::

## When not to use this workflow

- **Genuine one-line edits** — typo, config tweak, copy-paste fix. The loop's overhead exceeds the work.
- **Spikes and throwaway exploration.** If the output is going to be thrown away, the spec / plan / review machinery adds friction for no gain. Mark the work explicitly as a spike and skip the loop.
- **Investigation before implementation.** If you don't yet know what to build, you're not ready for `new-spec`. Investigate first; come back with a question shaped like a feature.

For bug-shaped work that crosses multiple files, see [how to fix a bug](bug-fix.md) — the `bug-fix` skill is the right entry point.

## Related

- [The core pack as a system](../explanation/core-pack.md) — why the loop exists and how the parts compose.
- [`core-pack.md` § Why the loop](../../core/explanation/core-pack.md#why-the-loop) — the contributor-side rationale.
- [`new-spec` skill](../../../packs/core/.apm/skills/new-spec/SKILL.md) — authoritative procedure for the planning skill.
- [`work-loop` skill](../../../packs/core/.apm/skills/work-loop/SKILL.md) — authoritative procedure for the loop itself.
- [How to fix a bug](bug-fix.md) — `bug-fix` is the entry point for bug-shaped work.
- [How to adapt the pack to your project](adapt-to-project.md) — post-install setup; do this before your first feature.

## Enforcement

Two layered mechanisms enforce discipline before a PR opens:

| Layer | Mechanism | What it gates |
|---|---|---|
| Caps | `scripts/work-supervisor.py status --check` in the `work-loop` skill | The implementation retry cap (exit 3) and any standing refusal (exit 1), for every spec holding `delivery/approvals.jsonl` (see `references/state-schema.md` in the `work-loop` skill). |
| Your gate | `tools/hooks/pre-pr.py` | Runs the supervisor check, then **your project's own** lint / typecheck / test commands — wire them into the stub in `pre-pr.py` (or let the `adapt-to-project` skill fill them in from your detected build commands). |

This is **Shift Left**: catch problems as early as possible, locally
before CI, at PLAN before EXECUTE. The pre-EXECUTE adversarial review
in the work-loop skill is the same pattern at a different layer —
moving review left from after code is written to before it is.

`session-start.py` is shipped pre-wired by the install pipeline: the
SessionStart binding lands in the adapter's local settings file
automatically, no manual paste. `pre-pr.py` stays consumer-wired,
because Claude Code has no PR-open lifecycle event (`Stop` fires after
every agent turn — wrong semantics). Wire `pre-pr.py` via
`.git/hooks/pre-push` if you want it automatic, or run it by hand
before opening a PR.
