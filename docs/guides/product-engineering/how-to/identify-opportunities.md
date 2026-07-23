# How to: identify opportunities

**Use this when:** You have a confirmed problem area and want to understand what users are actually trying to get done — across functional, emotional, and social dimensions — before committing to any solution direction.
**Prerequisites:** `product-engineering` pack installed; a problem description, affected user population, and current source of pain (a prior `situation-framing.md` from `frame-situation` improves pre-population but is optional).
**Result:** A ranked `opportunity-assessment.md` with functional, emotional, and social job tables and a scored top-opportunities list ready to pass to `diverge-solutions`.

Use this skill when you have a problem area worth exploring and want to know
what users are actually trying to get done before committing to a solution direction.
The output is a ranked `opportunity-assessment.md` artifact ready to hand to `diverge-solutions`.

---

## When to use this skill

**Step 2 of the shaping sequence.** After `frame-situation` has classified a
signal and recommended an entry point, run `identify-opportunities` to map the
jobs before diverging on solutions. This is the default path when the problem
is confirmed but the solution space is open.

**Standalone, without prior situation framing.** If you are starting from a
free-form problem description — a customer complaint, a product hypothesis, or a
gap surfaced in a retro — you can run `identify-opportunities` directly without
running `frame-situation` first. Provide a problem description, the affected user
population, and what currently causes pain; the skill derives a slug and produces
the artifact from that input.

**When not to use it.** If the team has already committed to a solution bet,
use `place-bet` instead. If the signal has not been classified yet, consider
running `frame-situation` first to confirm it is worth shaping and to get a
recommended entry point — though `identify-opportunities` will proceed on
free-form input if you skip that step.

---

## Seeding from a situation-framing artifact

When `frame-situation` has already run for the same topic, a `situation-framing.md`
artifact sits at `<output_dir>/shaping/<slug>/situation-framing.md`. The skill
reads this automatically when it finds it at the slug path.

What it extracts:
- **`finding-type`** — whether the signal is an opportunity, risk, gap, or threat;
  helps calibrate which jobs are most likely to surface
- **Wardley summary** — which capability maturity stage is implicated; informs
  whether the jobs tend toward exploration or optimisation
- **`shaping-entry`** — the recommended entry point from step 1; confirms you
  are at the right step in the sequence

If the situation-framing artifact is absent, the skill proceeds on your
free-form input without prompting you further.

---

## Interpreting the output

The artifact contains three job tables (functional, emotional, social) and a
ranked top-opportunities list.

**Reading the opportunity score.** The Ulwick formula weights importance against
the gap between importance and satisfaction:

- A score of **15+** is a strong signal — the job matters greatly and current
  solutions fall significantly short. Prioritise these jobs for `diverge-solutions`.
- A score of **10–14** is a meaningful opportunity — worth including in the
  diverge brief, especially when it clusters thematically with high-scoring jobs.
- A score of **under 10** is low priority for this shaping round — the job either
  matters less or is already well served. Keep it in the artifact; revisit if the
  context shifts.

**Acting on the top-opportunities list.** The list is the recommended input for
`diverge-solutions` — pass it directly to step 3. If several high-scoring jobs
cluster around a single theme (for example, "certainty" or "coordination"), that
theme is likely the load-bearing insight for solution divergence; naming it
explicitly in the handoff helps `diverge-solutions` stay focused.

**Rating provenance.** Ratings labelled as agent-estimated were inferred from
context rather than confirmed by the PE. Where the bet has high stakes, replace
agent estimates with explicit PE-confirmed ratings before handing off to step 3.

**When `diverge-solutions` is absent.** The artifact will contain a "Step 3
readiness" section describing what step 3 provides and what to do when the skill
becomes available. The top-opportunities list in the artifact remains valid input
when you are ready to continue.
