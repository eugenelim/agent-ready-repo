# Atomic composition: build systems, not pages

A design system stays coherent because it's built **bottom-up from small
reusable parts**, not top-down as a pile of finished screens. You define a
thing once and compose it upward. The payoff is consistency that holds as the
product grows, instead of drift you chase screen by screen.

## The three levels

Keep a clear line between what each level *is*:

- **Primitive token** — a single named decision with no internal structure: a
  surface tone, a spacing step, a type step. The atoms of the system. They
  hold values (derived per `token-taxonomy-derivation.md`) and nothing else.
- **Composed component** — a reusable element assembled *from primitives and
  other components*: a button, a field, a card. A component references tokens
  by their semantic role; it never hard-codes a value. Defined once, reused
  everywhere.
- **Page** — an arrangement of components for a specific job. A page composes;
  it does not introduce new primitives or one-off values. If a page needs
  something the system doesn't have, that's a signal to add a token or a
  component to the system — not to special-case the page.

The discipline: **decisions live at the lowest level that can own them.** A
color decision is a token, not a per-component override. A spacing rhythm is a
scale step, not a number typed into a page.

## Define once, reuse

When the same element appears twice, it's one component used twice — never two
look-alikes. Two copies drift the moment one is touched and the other isn't;
that drift is exactly the incoherence a system exists to prevent.

- See a pattern twice → promote it to a component.
- See a value twice → promote it to a token.
- Need a variant → parameterize the existing component (a named option), don't
  fork it.

## Why this keeps the system coherent as it grows

- **Change propagates.** Re-point a semantic token or fix a component once, and
  every consumer updates. With one-off pages, the same change is a manual sweep
  you'll do incompletely.
- **The vocabulary stays small.** A bounded set of tokens and components is
  learnable; an unbounded set of bespoke screens is not. New work composes from
  known parts instead of inventing new ones.
- **Intent stays traceable.** Because components bind to semantic tokens and
  tokens trace to named goals, you can follow any pixel on a page back to the
  aesthetic direction that justified it. One-off page styling severs that trace.

## When you're tempted to design a page

Ask first: *which existing components compose this?* If the answer is "all of
them," you're done — assemble and move on. If the answer is "most, plus this
one new thing," add the new thing to the *system* (as a token or component),
then compose the page from the system. The page is always the output of the
system, never a place the system gets bypassed.
