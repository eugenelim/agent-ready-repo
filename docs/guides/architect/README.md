# `architect` — guides

Solution architecture as three skills. `architect-design` frames a problem, weighs a technical choice, or designs a system without a diagram as the headline. `architect-diagram` draws the system, flow, state, data model, or deployment topology. `architect-review` critiques an existing design doc, diagram, RFC, or ADR. They lean on a repo's `reference.md` — the golden path that says how this codebase is built — when one is present.

All three are **knowledge-surface aware**. When an internal knowledge surface is reachable — an enterprise-knowledge MCP tool, an internal CLI, an in-repo doc set (public web doesn't count) — `architect-design` consults it before proposing and names what it drew from, `architect-diagram` grounds the beyond-repo parts of a document- or update-mode diagram against it, and `architect-review` flags claims about the world asserted with no cited surface. What can't be grounded becomes a named question or a flag, never a guess.

New here? [Establish your repo's reference architecture](how-to/establish-reference-architecture.md) gives the skills something to design against.

## Tutorials

- [Create and use your `reference.md`](tutorials/create-your-reference-architecture.md) — stand up the golden-path file from scratch and put it to work.

## How-to

- [Establish your repo's reference architecture](how-to/establish-reference-architecture.md) — capture the stack, patterns, and constraints the architect skills design against.
- [Diagram a system](how-to/diagram-a-system.md) — draw a system, flow, state, data-model, or deployment-topology diagram with `architect-diagram`.
- [Review an architecture artifact](how-to/review-an-architecture-artifact.md) — get a severity-tagged critique of a design doc, diagram, RFC, or ADR with `architect-review`.

## Reference

- [`reference.md` sections and the stack-pack contract](reference/reference-architecture.md) — every section of the golden-path file and how stack packs extend it.

---

Installing and upgrading live in [`../_shared/`](../_shared/).
