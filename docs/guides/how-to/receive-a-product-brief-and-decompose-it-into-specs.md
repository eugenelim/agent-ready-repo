# How to receive a product brief and decompose it into specs

Someone handed you a product brief — a PRD, a solution document, a packet of
requirements that spans several features — and you need to turn it into work
your team can actually ship. The `receive-brief` skill (shipped in `core`) is
the entry point. This guide walks the path from "here's a brief" through
"feature-sized specs are in the normal build loop and a coverage map tracks
them automatically."

For the *why* behind a brief sitting between the roadmap and the specs, read
[Why a brief layer](../explanation/why-a-brief-layer.md). For the exact fields
a brief and a derived spec carry, see
[Product brief fields](../reference/product-brief-fields.md). This page is
task-oriented: what to type and what to expect back.

## Before you start

You need:

- The `core` pack installed in your target repo.
- A brief in some form — a pasted document, a file, a link, or even a verbal
  sketch. It does not have to be complete or well-formatted; the skill elicits
  what's missing.
- A sense of who owns delivering this repo's slice of the work.

## Is `receive-brief` the right entry point?

| Situation | Skill to invoke |
| --- | --- |
| You received a multi-feature brief and need to route it into delivery | `receive-brief` |
| You're authoring one feature yourself, from scratch | `new-spec` |
| You're recording a decision already made | `new-adr` |

The tell for `receive-brief` is **multiplicity authored by someone else**: one
outcome, several features, handed to you. A single feature you're writing
yourself is `new-spec` directly.

## Steps

1. **Invoke the skill with whatever you have.** "We got a product brief for a
   billing portal — here it is: …" The skill ingests the document and starts a
   short conversation; it won't reject a half-formed brief.

2. **Answer the elicitation for the load-bearing fields.** The skill insists on
   only two things: the **Outcome** (the problem and the user-facing result)
   and the **Scope / Non-goals** (where this repo's slice begins and ends).
   Everything else — success metrics, appetite, user stories — it *offers* and
   you can supply or skip. It surfaces gaps rather than inventing answers.

3. **Confirm the proposed decomposition.** The skill cuts the brief into
   slices, each one independently shippable and testable, and **shows you the
   cut before scaffolding anything**. Read it: does each slice ship on its own?
   Is anything in the brief left uncovered? Is any slice too big for one
   feature-sized spec? Approve, or push back and have it re-cut.

4. **Let it scaffold and back-link the specs.** For each confirmed slice the
   skill chains `new-spec` to create `spec.md` + `plan.md`, stamps a `Brief:`
   back-link on the spec, and adds a row to the brief's Spec map. The brief
   lands at `docs/product/briefs/<slug>.md`.

5. **Build each slice with `work-loop`, as usual.** The derived specs are
   ordinary specs — nothing about the brief changes how you build them. As each
   ships, the brief's coverage map rolls up automatically (next step).

6. **Check coverage any time.** Run the bundled coverage lint to see whether
   the brief is delivered:

   ```bash
   python .claude/skills/receive-brief/scripts/lint-brief-coverage.py
   ```

   It reads each spec's `Status:` field, follows the `Brief:` back-links, and
   reports each brief as *delivered* (every mapped spec Shipped) or *not
   delivered*. Wire it into your gate if you want coverage enforced.

## Variations

- **If the brief carries user stories** (Shape B): give each story an id
  (`US-1`, `US-2`, …). Decomposition becomes *grouping stories into specs*, and
  each satisfying acceptance criterion gets a `Satisfies: US-n` marker — so
  coverage is story-granular ("US-2 → `password-reset` AC3 → shipped"). A story
  too big for one spec is an epic; the skill flags it for splitting.

- **If the brief has no stories** (Shape A): the skill derives spec boundaries
  from Outcome + Scope and coverage is spec-granular. This is the common case.

- **If the brief is one slice of a cross-repo effort:** record the external
  coordinator's id in the brief's optional `Epic:` field. You own this repo's
  slice only — the pointer is the nod to the wider effort, not a hub you build.

- **If you only want to scaffold some slices now:** that's fine. A brief can
  grow its Spec map over time as slices get picked up; a spec can even predate
  its brief. The `Brief:` back-link is what ties them together.

## Common pitfalls

- **A brief arrives missing metrics or appetite** — that's normal input, not an
  error. Supply your best guess or skip; the skill won't block on it.
- **The cut splits by component, not by shippability** — "backend, then
  frontend" is not two slices. Push back: each slice should ship and test on
  its own. The skill aims for this, but you're the check.
- **Hand-editing the Status column in the brief** — don't. It's auto-derived;
  a hand-written status drifts the moment a spec ships, which is the exact
  failure the coverage lint exists to catch.
- **Cramming the whole brief into one spec** — that breaks the one-feature
  sizing rule and the per-spec build loop. Several features means several specs.

## See also

- [Product brief fields](../reference/product-brief-fields.md) — the full field
  list for briefs and derived specs.
- [Why a brief layer](../explanation/why-a-brief-layer.md) — the altitude and
  the handoff this closes.
- [Plan and execute non-trivial work](plan-and-execute-non-trivial-work.md) —
  the `work-loop` each derived slice runs through.
