# The `quality-floor` checklist

The shared floor every design-craft artifact is held to. The authoring
skills (`aesthetic-direction`, `design-system-foundations`,
`layout-and-information-architecture`) reference it as they work;
`design-critique` applies it as an explicit pass. It is three commitments,
not a values sheet — it points at the recognized standards and names the
principle, never the numbers.

## 1. Handle all states

A surface is not designed until every state it can be in is designed. The
happy path is one state among several; the others are where products feel
broken. For each interactive surface, decide what the user sees and can do
in each of:

- **Empty** — nothing yet, or nothing matches. Distinguish *first-run*
  (never had data — orient and invite the first action) from *no-results*
  (a filter or search emptied it — show how to recover).
- **Loading** — work is in flight. Communicate that something is happening
  and, where you can, roughly how much is left; preserve layout so the
  surface doesn't jump when content arrives.
- **Error** — something failed. Say what happened in the user's terms, what
  it means for them, and the next action. Never a dead end.
- **Success** — the action completed. Confirm it visibly enough to be
  believed, proportionate to the action's weight.
- **Partial** — some data, some missing; some succeeded, some failed. Show
  what you have and mark what you don't, rather than hiding the whole.
- **Disabled / unavailable** — an action can't be taken right now. Make the
  *why* recoverable (what would re-enable it), not just the *that*.

## 2. Accessibility floor

Accessibility is a floor the design clears, not a feature added later. Hold
the work to the **recognized standard — WCAG, at the conformance level your
context requires** — and read the criteria from the source; this checklist
points to them rather than reprinting any threshold. The principles that
recur:

- **Perceivable contrast** between text/meaningful elements and their
  background, at the standard's required level — verified against the
  standard, never eyeballed.
- **Operable without a pointer** — every action reachable and completable by
  keyboard and other non-pointer input, in a sensible order, with the
  current focus always visible.
- **Meaning never carried by one channel alone** — not by color alone, not
  by position alone; pair it with text, shape, or label.
- **Named for assistive tech** — every control and image has an accessible
  name and role that conveys what a sighted user sees.
- **Targets and timing forgiving** — interactive targets large enough to hit;
  time limits avoidable or extendable.

When a choice can't meet the floor, that is a finding to surface, not a
detail to defer.

## 3. Motion communicates state — honor reduced-motion

Motion earns its place by carrying meaning: it shows a **state change**,
preserves **continuity** across a transition, or expresses a **spatial
relationship** (where a thing came from, where it went). Motion that
communicates nothing is decoration, and decoration is the first thing to
distract or nauseate.

Two commitments follow:

- **Every animation answers "what does this tell the user?"** If the answer
  is "nothing," cut it.
- **Always provide a reduced-motion path.** Some users need motion
  minimized — for vestibular safety, for focus, by preference. The design
  must honor that signal: replace movement with an instant or gentle
  state change that preserves the *information* the motion carried, never
  stripping the meaning along with the movement. Express this as the
  principle in the design intent; the build wires it to the platform's
  own reduced-motion signal.
