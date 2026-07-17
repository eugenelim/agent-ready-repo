# Taste critique: method reference

The taste mode is the third pass `design-critique` runs — after the quality-floor
checklist and the heuristic evaluation — when a **grounded aesthetic reference**
from `aesthetic-direction` is present. It checks the screen against two things:
(1) the grounded aesthetic reference the authoring session produced, and (2) the
platform conventions for the declared surface. It does not introduce a new values
table or a fresh opinion; it holds the screen to the referents already recorded.

> **Authoring-time self-review only.** This pass runs in the authoring session,
> with the author. It is **not** a fresh-context pass and **not** an adversarial
> check. The genuine fresh-context UX review — the one that does not mark its own
> homework — is the forked-context **`experience-reviewer`** agent. Invoke that
> agent for an independent review after the authoring session ends.

## What the grounded aesthetic reference is

`aesthetic-direction` records a set of named aesthetic goals, each grounded in:

- **Persona** — the lived context, needs, and expectations of the primary user;
  elicited inline when no Domain Framing artifact exists.
- **Precedent** — a brief survey of comparable products' taste, refreshed only
  when the authoring loop needs it; not a permanent catalogue.
- **Standards** — recognized design and platform guidance the goals reference;
  pointed to, never reprinted.
- **Platform conventions** — the surface-specific norms for the declared platform
  (responsive-web / iOS / Android / cross-platform).

The recorded direction names *what grounds each goal*. The taste critique points
back to those grounds as warrants — it never introduces new referents or fresh
opinions mid-critique.

## Step 1 — check aesthetic alignment

For each named goal in the grounded reference, ask one question: does the screen
under review **advance**, stay **neutral to**, or **contradict** that goal?

- **Advance** — the screen reinforces the goal in a way the referent supports.
  No finding; note briefly so the record is complete.
- **Neutral** — the screen neither helps nor hurts. No finding.
- **Contradict** — the screen works against the goal, and the referent supports
  the verdict. This is a finding. State the goal name, what the screen does that
  contradicts it, and the specific part of the referent (persona expectation,
  precedent signal, standard) that makes the contradiction legible — not a fresh
  preference.

A verdict of "contradicts" with no referent to point to is not a taste finding;
it is an unrated opinion and must be dropped.

## Step 2 — check platform fit

Verify the screen respects the conventions of its declared platform surface.

- **responsive-web** — consult MDN responsive-design guidance and PWA conventions
  (where applicable); check that the screen's intent is consistent with what those
  sources describe as standard behavior.
- **iOS** — consult the Apple Human Interface Guidelines; check that the screen's
  intent is consistent with their component vocabulary and navigation patterns.
- **Android** — consult Material 3 guidance; check that the screen's intent is
  consistent with its component vocabulary and adaptive-layout guidance.
- **cross-platform** — check that the shared intent is coherent, and that any
  per-surface adaptation is named (chrome, navigation, gestures differ per surface;
  the shared intent does not).

The warrant for any platform-fit finding is the platform's own published guidance —
point to it by name. Never reprint a value, measurement, or literal from that
guidance; the critique names the *principle* the screen contradicts and points to
the *source*, so the builder reads the standard directly.

## Step 3 — map and rate taste findings

Each taste finding follows the same shape as a heuristic finding:

- **Severity** (0–4) — using the same frequency × impact × persistence rubric
  from `references/heuristics.md`. Severity 0 is reserved for genuine
  disagreement where the grounded referent does not clearly resolve the call;
  these should be surfaced honestly rather than suppressed, but clearly marked
  as unresolved.
- **Source** — the aesthetic goal name or the platform convention violated.
- **Observation** — what the screen does, concretely.
- **Why it costs the design** — the consequence in terms of the goal or platform
  fit, not abstract taste.
- **Recommendation** — one concrete, portable change expressed as design intent;
  points to the grounded referent or platform standard as the warrant. Never a
  stack-specific implementation.

## What this mode never does

- **Reprints values.** The taste critique points to the grounded reference and
  platform standards; it never reprints palette entries, type scales, spacing
  values, motion durations, easing curves, breakpoints, or any literal the
  reference or a platform standard contains.
- **Introduces fresh referents.** If a referent was not recorded in the current
  session's `aesthetic-direction` output, it is not a valid warrant for a taste
  finding. Use only what the session grounded.
- **Substitutes for the fresh-context review.** This pass is authoring-time
  self-review. Findings it produces should be treated as a draft checklist,
  not an independent verdict. The `experience-reviewer` agent provides the
  independent verdict.
