---
title: Continue a delivery brief and confirm delivery slices
summary: Pass the human Ready gate and create specs only for confirmed slices.
pack: core
kind: how-to
---

# Continue a delivery brief and confirm delivery slices

**Use this when:** A Draft delivery brief needs a human Ready decision, with a slice cut now or later.
**Prerequisites:** The `core` pack installed, an existing repository brief, and a sense of which repo's slice of the work you own.
**Result:** A Ready brief in workspace state; if you confirm a slice, a feature-sized spec back-linked to it.

Someone handed you a PRD, solution document, or requirements packet spanning several features, and you need to turn it into work your team can ship. Use `author-delivery-brief create` to make the Draft, then `author-delivery-brief continue` to review readiness and offer delivery slices. This guide covers the continue path.

```text
Use author-delivery-brief to continue the billing portal brief and confirm its delivery slices.
```

For the *why* behind a brief sitting between the roadmap and the specs, read [Why a brief layer](../explanation/why-a-brief-layer.md). For the exact fields a brief and a derived spec carry, see [Product brief fields](../reference/product-brief-fields.md). This page is task-oriented: what to type and what to expect back.

## Before you start

You need:

- The `core` pack installed in your target repo.
- An existing Draft brief in the repository. It does not have to be complete;
  continue mode elicits what's missing.
- A sense of who owns delivering this repo's slice of the work.

## Which mode is the right entry point?

| Situation | Skill to invoke |
| --- | --- |
| You have unstructured source material and have not chosen an artifact route | `work-intake` |
| You need to author a Draft from a multi-feature source | `author-delivery-brief create` |
| You have an existing repository brief to review or slice | `author-delivery-brief continue` |
| You're authoring one feature yourself, from scratch | `new-spec` |
| You're recording a decision already made | `new-adr` |

The tell for a delivery brief is multiplicity: one coherent outcome, several independently shippable slices or repositories. A single feature goes to `new-spec` directly.

## Steps

1. **Continue the repository brief.** "Run `author-delivery-brief continue` on `docs/product/briefs/billing-portal.md`." Source locators remain passive provenance; provide already-acquired bounded content if a source comparison is needed.

2. **Answer the elicitation for the load-bearing fields.** The skill insists on only two things: the **Outcome** (the problem and the user-facing result) and the **Scope / Non-goals** (where this repo's slice begins and ends). Everything else — success metrics, appetite, user stories — it *offers* and you can supply or skip. It surfaces gaps rather than inventing answers.

3. **Run the cold shaping review, then decide whether the brief is Ready.** Review the outcome, scope, constraints and appetite, assumptions and risks, plus source provenance and revision. The owner supplies that evidence in one attributed packet to an independent reviewer; findings return for revision. A revision-bound `Clean` plus explicit human confirmation moves the whole structured entry from Draft to Ready atomically. If no isolated subagent, fresh context, or independent human is available, the owner emits `BLOCKED` and leaves the brief Draft. It does not require a spec.

4. **Choose whether to cut a slice now.** You can stop with a Ready brief and zero specs. If you confirm one independently shippable slice, the skill chains `new-spec` to create `spec.md` + `plan.md`, stamps a `Brief:` back-link on the spec, and adds the materialized spec to the brief's Spec map.

5. **Build each slice with `work-loop`, as usual.** The derived specs are ordinary specs — nothing about the brief changes how you build them. As each ships, the brief's coverage map rolls up automatically (next step).

6. **Check coverage any time.** Run the bundled coverage lint to see whether the brief is delivered:

   ```bash
   python .claude/skills/author-delivery-brief/scripts/lint-brief-coverage.py
   ```

It reads each spec's `Status:` field, follows the `Brief:` back-links, and reports each brief as *delivered* (every mapped spec Shipped) or *not delivered*. Wire it into your gate if you want coverage enforced.

## Variations

- **If the brief carries user stories** (Shape B): give each story an id (`US-1`, `US-2`, …). Decomposition becomes *grouping stories into specs*, and each satisfying acceptance criterion gets a `Satisfies: US-n` marker — so coverage is story-granular ("US-2 → `password-reset` AC3 → shipped"). A story too big for one spec is an epic; the skill flags it for splitting.

- **If the brief has no stories** (Shape A): the skill derives spec boundaries from Outcome + Scope and coverage is spec-granular. This is the common case.

- **If the brief is one slice of a cross-repo effort:** record the external coordinator's id in the brief's optional `Epic:` field. You own this repo's slice only — the pointer is the nod to the wider effort, not a hub you build.

- **If you do not want to scaffold a slice now:** stop at Ready with an empty Spec map. A brief can grow its map over time as slices are confirmed; no placeholder spec is required.

- **If the brief cites an RFC or ADR:** keep it under Governance references,
  not in the Spec map. Governance can constrain delivery but never affects the
  execution or closure rollup.

## Common pitfalls

- **A brief arrives missing metrics or appetite** — that's normal input, not an error. Supply your best guess or skip; the skill won't block on it.
- **The cut splits by component, not by shippability** — "backend, then frontend" is not two slices. Push back: each slice should ship and test on its own. The skill aims for this, but you're the check.
- **Hand-editing the Status column in the brief** — don't. It's auto-derived; a hand-written status drifts the moment a spec ships, which is the exact failure the coverage lint exists to catch.
- **Cramming the whole brief into one spec** — that breaks the one-feature sizing rule and the per-spec build loop. Several features means several specs.

## What you have now

You have a Ready delivery brief and, when confirmed, feature-sized specs linked
back to it. Build each approved slice through its own `work-loop` rather than
turning the brief into an implementation plan.

## See also

- [Product brief fields](../reference/product-brief-fields.md) — the full field list for briefs and derived specs.
- [Why a brief layer](../explanation/why-a-brief-layer.md) — the altitude and the handoff this closes.
- [Plan and execute non-trivial work](plan-and-execute-non-trivial-work.md) — the `work-loop` each derived slice runs through.
