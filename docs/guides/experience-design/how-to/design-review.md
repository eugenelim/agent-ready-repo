# Run a design review before the independent pass

**Use this when:** you have a concrete screen, flow, or mockup to evaluate before
the independent `experience-reviewer` pass — a self-check that the authoring session can still catch.
**Prerequisites:** `experience-design` pack installed; a concrete artifact to review (not a vibe).
**Result:** a prioritized, severity-rated findings list that turns "this feels off"
into something a stakeholder can argue and a builder can act on.

> **How-to** — task-oriented. Runs the `design-review` three-pass structure. For
> *why* this structure exists and how it connects to the design thread, read
> [The experience thread](../explanation/the-experience-thread.md). For the
> quality-floor state set that drives Pass 3, see the
> [State coverage reference](../reference/state-coverage.md).

`design-review` is an **authoring-time** self-check — it runs with the author,
in the same session the design was made. It is **not** a fresh-context review.
The genuine independent pass is the forked-context `experience-reviewer` agent,
which runs separately and does not mark its own homework.

## The three-pass structure

Every design review runs exactly three passes, in this order:

1. **Pass 1 — Cold-read** (audience and job check)
2. **Pass 2 — Primary task and one unhappy path** (task completion across viewports and accessibility modes)
3. **Pass 3 — Contract review** (full quality-floor, heuristics, marketing clarity, taste)

Run all three passes before presenting findings. Do not skip Pass 1 because you
authored the design — its value is precisely that it forces you to read the
surface as a stranger would.

---

## Pass 1 — Cold-read

Ask your agent:

> "Before we look at the brief, read this screen as a first-time visitor.
> Who is this for, and what are they trying to do? What does it communicate
> in the first five seconds?"

**What happens:** the agent looks only at the rendered surface and names the
audience and job without consulting the brief. If it cannot answer both questions
from the first screen without scrolling, that is a finding.

**What to watch for:** if the audience or job named by the cold-read doesn't
match the intended audience or job, you have a Pass 1 finding — the surface
is communicating the wrong thing to the wrong person. This is most common with:
- **Architecture-first heroes** — the hero communicates organizational structure
  ("Our company was founded in…" or "Our product family includes…") before
  naming the reader's problem.
- **Inventory-first pack pages** — the page lists everything the product does
  with equal visual weight before communicating what problem it solves.

A Pass 1 finding earns a **Blocker** if the five-second scan cannot answer
all three questions (what / who / should I care?). It earns a **Concern** if
the answer is present but hard to reach.

---

## Pass 2 — Primary task and one unhappy path

Ask your agent:

> "Walk the primary task and one unhappy path across desktop, tablet, and mobile.
> Then check keyboard navigation, focus management, 200% zoom, and reduced-motion."

**What happens:** the agent walks the task at three viewport widths and four
accessibility modes, recording whether the task is completable and which
quality-floor states are missing or broken.

**What to watch for:**
- **Desktop-only designs** — if the design only exists at wide viewports, Pass 2
  finds that mobile task completion is unverified; rate every mobile gap as at
  least a Concern, and any interaction that is unreachable on mobile as a Blocker.
- **Missing unhappy-path states** — a design that only shows the happy path will
  fail Pass 2 for any absent state along the unhappy path (error, blocked,
  no-results, offline, permission/denied, destructive-confirmation).
- **Keyboard-only gaps** — any action unreachable by keyboard alone is a Blocker.
- **Missing focus indicators** — visible focus is an accessibility floor
  commitment; absent focus indicators are Blockers, not Suggestions.

---

## Pass 3 — Contract review

Ask your agent:

> "Now run the full contract review: quality-floor for all 18 states,
> accessibility floor, heuristic evaluation, marketing clarity pass if
> this is a marketing surface, and taste critique if we have a grounded
> aesthetic reference."

**What happens:** the agent runs the full quality-floor checklist (18 states),
the accessibility floor, Nielsen's heuristics, and optionally the marketing
clarity pass and taste critique — using the observations from Passes 1 and 2 as
evidence.

**What to watch for:**
- **Every-section-as-cards** — using card components for every content type
  (testimonials, features, pricing, navigation) removes the hierarchy that tells
  users what matters most. A card is a decision unit; using it for everything
  makes every decision equally weighted, which is a heuristic violation (match
  between system and real world; recognition rather than recall).
- **Missing permission states** — a design that has no state for an unauthorized
  or locked-out viewer is missing the `permission/denied` state; rate as Blocker.
- **Attractive UI with unclear write consequences** — visual polish does not
  substitute for the `destructive-confirmation` state. A design that lacks
  explicit confirmation for an irreversible action is a Blocker regardless
  of how good it looks.

---

## Severity rubric

| Tier | When to use | Key rules |
|---|---|---|
| **Blocker** | The surface cannot ship with this unresolved | WCAG failure at required level; any state that leaves the user with no path forward; marketing above-fold failure where audience/job/value are indeterminate; missing destructive-confirmation; missing permission/denied on a gated surface |
| **Concern** | Meaningful degradation but task completion still possible | Heuristic violations at severity 2–3; states missing but with degraded fallback; copy weak but not misleading |
| **Suggestion** | Documented improvement with low urgency | Severity 0–1 heuristic findings; grounded aesthetic observations |

**Two hard rules:**
1. **Never soften an accessibility failure to Suggestion.** An a11y failure at
   the required conformance level is a Blocker.
2. **Never present a pure aesthetic preference as a Blocker or Concern.** An
   aesthetic observation without a grounded reference warrant (from the aesthetic
   direction doc or a recognized platform convention) goes in Director's notes,
   not the findings list.

---

## After the review

- Apply all **Blockers** before design intent feeds the build loop.
- Apply **Concerns** before the `experience-reviewer` independent pass.
- Carry **Suggestions** and **Director's notes** to the backlog.
- When the review is complete, invoke the `experience-reviewer` in a forked
  context — it does not see the authoring session and gives an independent pass.

For the complete state reference, including example treatments for all 18 states,
see [State coverage reference](../reference/state-coverage.md).
