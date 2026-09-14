# Owner decisions

Decisions the task owner made during execution that an artifact has to cite. A
conversation is not a reference; this file is.

## 2026-09-13 — the engine path-gate exemption carrier

**Decision: the approved spec carries the exemption. No RFC is required.**

`make build-check` failed at `lint-catalogue-curation-guard`: the changeset
touches `packages/agentbundle/agentbundle/catalogue_tooling/lint.py`, and
RFC-0059 D6 requires an engine-scoped RFC for a change under that tree. No RFC
governs this change.

The owner accepted the approved spec as the carrier, on the grounds that it
contracts the lint relaxation in ACs 8-10 and names the trust-boundary widening
in its Risks. ADR-0056 is the precedent: it names itself the exemption carrier
for its own landing PR, establishing that an approved artifact can stand in for
an RFC.

`n/a` was rejected as false. Engine behaviour does change: the lint's
accept/reject surface moves, and so does the selection between the confined
64 KiB read and a plain `read_text`.

Carried by the trailer on the empty commit `69e050224`.

## 2026-09-13 — the sweep criterion's exemption list

**Decision: add `docs/product/changelog.md` to the list.**

The criterion requires `rg --hidden -l 'agents/rules/cognitive-load'` to return
no hit outside a named set. Running it returns ten files; nine are exempt. The
tenth is `docs/product/changelog.md` — and the changelog criterion in the same
spec *requires* the Upgrading section to name the retired path, so an adopter
knows what to delete by hand. The contract forbade a hit it also mandated.

Two corrections ride along in the same criterion, both owner-approved:

- "these **four** bounded out of scope" precedes a list of five.
- A duplicated sentence: "This criterion is closed by running the command; it
  has been wrong three times when read. The criterion is closed by running the
  command, not by reading it." One point, said twice, which this repository's
  own prose rules forbid.

This is the `reason_ref` for the contract amendment that carries the edit.

## 2026-09-13 — the post-amendment gates

**Decision: proceed. The amendment's two human gates are answered by the
approval that authorized it.**

The contract amendment returned the engine to the spec/plan phase, which carries
two human gates: "Does this spec define the right thing to build?" and "Does this
plan describe the right way to build it?" Both were answered in advance. The
owner approved the criterion correction, and the plan was not touched by the
amendment — its hash is unchanged at `09965cec2bab`, and the completed task
sections are pinned against edits.

The amendment changed one acceptance criterion's exemption list. It changed no
objective, no boundary, no task, and no testing strategy.

## 2026-09-13 — the router's read becomes unconditional

**Decision: `AGENTS.md` reads `AGENT_RULES.md` every time and checks there
whether any of its rules apply. The per-row condition moves into
`AGENT_RULES.md` itself.**

Review round 6 found that "Read `AGENT_RULES.md` only when one of its `when`
rows matches the work in hand" cannot be evaluated: the rows are inside the file,
so an agent cannot know a row matches without first reading it. On this
repository the table is empty and nothing is lost; for an adopter who merges the
new `AGENTS.md`, existing rows go inert — the opposite of the extension point
the changelog advertises.

The owner's reasoning: the lookup is worth keeping, but a conditional activation
is exactly the thing this change exists to stop relying on. We have already seen
that a model-directed conditional read does not happen. So the read is
unconditional and cheap — the table ships empty — and the conditionality lives
where it can actually be evaluated, one line into the file being read.

This amends the acceptance criterion requiring "no unconditional read of
`AGENT_RULES.md`". That criterion was written to kill the three-hop chain whose
skippable hops carried the behavioural rules. Those rules are now inline, so a
single bounded read of a short index does not restore what it was written
against.

## 2026-09-13 — the stale sentence inside T3's plan section

**Decision: leave it, and say so here.**

`plan.md:269` still reads "The rewrite must keep that mention while removing the
unconditional read", which describes the criterion before the router amendment
reversed it. T3 is a completed task and its plan section is pinned by
`completed_task_section_hashes`; editing it is refused, by design, so that a
finished task's record cannot be rewritten after the fact.

Every live claim was corrected instead: the spec's Outcome 1 prose, the amended
criterion, both `AGENTS.md` files, the roster test and its commentary, the
changelog, and the measurement brief. The plan sentence stays as the record of
what T3 was asked to do at the time, which is what a completed task section is
for.
