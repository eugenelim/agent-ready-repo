# How to plan and execute non-trivial work

You have a feature to build, a refactor to drive, a migration to run —
anything past a one-line edit. This guide walks the path from "I'm
about to start" through "the PR is green and the reviewer is clean",
using the two skills that drive it: `new-spec` and `work-loop`.

For the *why* behind this discipline, read [the core pack as a
system](../explanation/core-pack.md). This guide is task-oriented; it
tells you what to type and what to expect back.

## Prerequisites

- The `core` pack installed in your target repo.
- A working directory where you can edit, commit, and run gates
  (lint / typecheck / test).
- Familiarity with the four mandatory spec sections (Objective,
  Boundaries, Testing Strategy, Acceptance Criteria) — see
  [`docs/CONVENTIONS.md`](../../CONVENTIONS.md).

## Pick your entry point

Two skills, one workflow:

| Situation | Skill to invoke |
| --- | --- |
| New feature or significant change — no spec yet | `new-spec`, then `work-loop` |
| Spec already exists in `docs/specs/<feature>/` | `work-loop` (it reads the spec) |
| Multi-file bug fix | `bug-fix` — see [how to fix a bug](bug-fix.md) |
| One-line edit, typo, single config tweak | Skip the loop — overhead isn't worth it |

If you're unsure whether the change is trivial, default to the loop.
The cost of running it on a small task is one extra minute; the cost
of vibe-coding a non-trivial task is a re-do.

> **Invoke skills by name.** Claude Code's description-based
> auto-discovery is best-effort — natural phrasings like "let's spec
> this out" usually fire the right skill, but not always. **Naming
> the skill in your request guarantees it fires.** Use the
> name-the-skill form below whenever you want the discipline,
> including on edge cases where description matching wouldn't pick it
> up.

## Step 1 — Run `new-spec` (when no spec exists)

The skill writes `docs/specs/<feature>/spec.md` and `plan.md`, and
gates body content on assumption sign-off.

Name the skill in your invocation. Two worked invocations — one
backend, one frontend:

```
use the new-spec skill to design webhook retries with exponential
backoff for the payment-events stream
```
(retry logic is a state machine — Testing Strategy will pick TDD for
this one.)

```
use the new-spec skill to spec the saved-filters chip on the
product-search results page
```
(the chip is a visible UI element — Testing Strategy will pair it
with visual / manual QA, possibly automated.)

Natural phrasings (`let's spec out X`, `new spec: Y`,
`write a spec for Z`) match the skill's description and often
trigger it, but description matching isn't guaranteed. Lead with
`use the new-spec skill to …` whenever you want the discipline to
fire reliably.

### What to put in front of it

`new-spec` ingests whatever input you give it and surfaces what's
missing. Any of these shapes work:

- A one-line idea ("add 2FA for admin login").
- A requirements doc or PRD pasted into the message.
- A linked ticket — Linear, Jira, GitHub issue. Reference the URL; the
  skill reads what's there.
- An upstream brief from a portfolio team (Feature Intent, Component
  Brief, or whatever shape your org produces).
- A bug report that's grown into a feature ("this thing should work
  differently").

The skill doesn't care which shape you brought. The assumption
checkpoint is where missing information gets named, regardless of
input shape — so an idea-shaped input surfaces more Unverified items,
a brief-shaped input surfaces fewer. The output is the same: a spec
and plan grounded in confirmed assumptions.

### What to expect

1. The skill scaffolds `docs/specs/<feature>/spec.md` and `plan.md`
   from the bundled templates.
2. It drafts assumption candidates across Technical / Product /
   Process categories, runs **one targeted check per candidate** (a
   repo read, a web lookup, or a read-only probe), then **stops** and
   emits an `ASSUMPTIONS I'M MAKING:` block split into `Verified`
   (each with a one-line citation of the check) and `Unverified`
   (each needing your input). The check happens before the bullet
   gets filed, not after.
3. You read the Unverified list and confirm or revise. If the
   Unverified list is empty, the skill surfaces the Verified list with
   the highest-stakes item called out and asks you to confirm *that
   one specifically* — a vague "looks good" doesn't count.
4. Spec body fills in: Objective, Boundaries (including at least one
   structural `Never do`), Testing Strategy with a verification mode
   per outcome, Acceptance Criteria.
5. Plan body fills in: tasks with `Tests:` before `Approach:`,
   explicit `Depends on:`, verification mode per task.
6. `adversarial-reviewer` reads the spec and plan cold. Iterate to
   clean — usually one to two passes; if you can't reach clean in
   three, the skill stops and asks for human direction (the spec
   likely has a structural problem, not a wording one).
7. The skill updates `docs/specs/README.md` and reminds you that spec
   drift is a bug — update the spec in the same PR when implementation
   diverges.

If you want to stop here (pure planning, no build yet), this is the
natural exit point. The spec and plan are durable; come back to
`work-loop` whenever you're ready.

## Step 2 — Run `work-loop`

With a spec in place, invoke the loop by name. Same two domains
carried through:

```
use the work-loop skill to implement docs/specs/webhook-retries
```
(TDD-mode tasks for retry logic; goal-based for wiring.)

```
use the work-loop skill to drive the saved-filters-chip spec
```
(visual / manual QA on the chip; goal-based on the URL-state plumbing.)

Naming the skill is the reliable form. The `work-loop` description
also matches phrasings like "implement the X spec" or "let's work on
Y", but the explicit form fires the loop's full discipline — gates,
adversarial review, stasis detection, the state machine — even on
edges where description matching wouldn't pick it up automatically.

### What it does

The full procedure lives in
[the `work-loop` SKILL.md](../../../packs/core/.apm/skills/work-loop/SKILL.md).
The short version:

- **PLAN** — reads `spec.md` and `plan.md`, picks verification modes if
  not already set, designs construction tests up front, and asks you
  to name the **declined-pattern register**: one to three things you
  were tempted to add (a layer, a flag, a defensive wrapper) and
  explicitly declined. The register pairs with the spec's Boundaries
  section so REVIEW can catch drift toward declined temptations as
  self-contradiction in the diff. Pre-EXECUTE adversarial review
  fires automatically on spec amendments or on any of the four
  structural triggers (new module, new dependency, new abstraction,
  new top-level directory).
- **EXECUTE** — implements task by task. TDD-mode tasks run
  red-green-refactor; goal-based tasks run the `Done when:` one-liner;
  manual-QA tasks record the visual check.
- **GATES** — lint, typecheck, tests. Mechanical, ordered, no editing
  the gate to make it pass.
- **REVIEW** — `adversarial-reviewer` reads the diff cold against
  `AGENTS.md` + `CONVENTIONS.md` + `spec.md`. Findings come back as
  Blockers / Concerns / Nits with one-sentence fixes. The loop
  records each pass's finding fingerprints to `state.json` via
  `loop-cohort review record`, which is what enables stasis detection
  in the next phase. Specialist reviewers (`security-reviewer`,
  `quality-engineer`) run when the diff warrants.
- **DECIDE** — each finding routes to `apply` (fix in this PR) or
  `defer` (one-line entry under `Deferred:` in the PR body). Stasis
  detection fires if the same findings come back two iterations in a
  row — stop and surface to a human rather than spinning a third pass.

For the end-to-end narrative with the parts in context, read
[core-pack.md § How they tie together](../explanation/core-pack.md#how-they-tie-together).

### Termination cues you'll see

- **Gates green and review clean** → ship.
- **`loop-cohort.py check` exits non-zero** → the script tells you
  which cap fired (iteration cap, token budget, consecutive errors,
  plan not approved, or fingerprint stasis). Read the message; don't
  override.
- **Diff is shrinking but findings aren't** → you're spot-fixing
  without addressing root cause. Back to PLAN.

If any of these fire and the work isn't done, the task is bigger than
you thought. Re-plan rather than expanding scope silently.

## Variations

### Resume an in-flight spec

`work-loop` reads `docs/specs/<feature>/` and picks up from
`state.json`. Phrase as "resume the X work" or "continue on
`docs/specs/X`". Pre-EXECUTE review won't re-fire unless you amended
the spec or plan since the last pass — or the re-plan introduced one
of the four structural triggers.

`state.json` is gitignored session-scratch — on a fresh checkout
(new machine, after `git clean`, a teammate's box), the loop
re-initializes it via `loop-cohort.py init` and treats the spec /
plan / diff as authoritative.

### Spec amendment mid-flight

If EXECUTE discovers a missing or wrong task, update `plan.md` first,
then resume. The pre-EXECUTE adversarial review re-fires automatically
if the re-plan introduces any structural trigger. This is by design —
most over-engineering surfaces mid-flight, not during initial PLAN.

### Parallel implementers (supervisor mode)

If your plan has two or more tasks declaring `Depends on: none`,
`work-loop` fans out into supervisor mode and dispatches one
`implementer` subagent per independent task. The procedure lives in
[`references/supervisor-mode.md`](../../../packs/core/.apm/skills/work-loop/references/supervisor-mode.md);
the loop loads it on demand.

## Pitfalls

> **Skipping `new-spec` for "small" multi-file work.** If the change
> touches more than one file, the spec is cheap insurance. A
> three-paragraph spec is fine — the discipline is the point, not the
> document length.

> **Editing `state.json` by hand.** The file is owned by the
> `loop-cohort` tool. Hand edits desync the loop's view of plan
> approval and fingerprint state. Run the tool's verbs; don't reach
> in.

> **Treating gates as sufficient.** Gates are necessary. Review
> catches what gates can't — missing edge cases, scope creep, spec
> drift. Don't skip the reviewer pass because "it'll be fine".

> **Skipping pre-EXECUTE review on a structural change.** The four
> triggers (new module boundary, new dependency, new abstraction
> layer, new top-level directory) are exactly the cases where
> over-engineering is most expensive to undo. The cost of catching it
> at PLAN is a sentence; at REVIEW it's a re-do.

> **Letting the spec drift from the implementation.** When
> implementation diverges from the spec, the spec is wrong. Update the
> spec in the same PR — drift is a bug, not paperwork debt.

## When not to use this workflow

- **Genuine one-line edits** — typo, config tweak, copy-paste fix.
  The loop's overhead exceeds the work.
- **Spikes and throwaway exploration.** If the output is going to be
  thrown away, the spec / plan / review machinery adds friction for no
  gain. Mark the work explicitly as a spike and skip the loop.
- **Investigation before implementation.** If you don't yet know what
  to build, you're not ready for `new-spec`. Investigate first; come
  back with a question shaped like a feature.

For bug-shaped work that crosses multiple files, see
[how to fix a bug](bug-fix.md) — the `bug-fix` skill is the right
entry point.

## Related

- [The core pack as a system](../explanation/core-pack.md) — why the
  loop exists and how the parts compose.
- [`docs/CONVENTIONS.md` § How we do non-trivial work](../../CONVENTIONS.md#how-we-do-non-trivial-work) —
  the contributor-side rationale.
- [`new-spec` skill](../../../packs/core/.apm/skills/new-spec/SKILL.md) —
  authoritative procedure for the planning skill.
- [`work-loop` skill](../../../packs/core/.apm/skills/work-loop/SKILL.md) —
  authoritative procedure for the loop itself.
- [How to fix a bug](bug-fix.md) — `bug-fix` is the entry point for
  bug-shaped work.
- [How to adapt the pack to your project](adapt-to-project.md) —
  post-install setup; do this before your first feature.
