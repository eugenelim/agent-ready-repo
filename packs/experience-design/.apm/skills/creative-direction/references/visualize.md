# visualize — the three representations and their binding force

> **Loaded when:** `visualize` is the active operation.
> **Question:** how is the direction made concrete enough for a compositional commitment without binding tokens the design system must derive?

## The three representations

`visualize` produces one of three representations. Each carries a distinct binding force.

**Semantic direction** — the filled direction sheet produced by `converge`, carrying a token on every axis. This representation is binding: it is the agreement the work carries forward.

**Visualised candidate** — an illustrative depiction of a single direction, produced to support the human's comparison before selection. This representation is illustrative and non-binding. It informs a choice but does not supersede the direction sheet.

**Approved visual target** — a composition the human has confirmed as a structural reference for the selected direction. This representation is binding on composition only: it fixes arrangement, proportion, and spatial relationships.

## Value boundary of the approved visual target

An approved visual target never binds colour, type, spacing, or motion values — those remain `design-system`'s to derive.

An approved visual target's compositional commitments are written into `<output_dir>/direction/<slug>.md` itself, because a file beside the direction doc sits off every path a downstream consumer reads.

## Default representation

A text schematic is the default representation. It describes spatial arrangement, region proportions, and the relationships between content zones in plain prose and lightweight structural notation. No image-capable harness is required.

A simple wireframe outperforms a detailed screenshot as structured visual input. A wireframe surfaces composition and proportion without introducing colour, type, or surface-treatment decisions the direction sheet has not yet authorised. A screenshot imports all of those and forecloses decisions the direction step is designed to leave open.

## Capability gate

A rendered comp is produced only when the harness can produce one and the route is `originate`; its absence is a named skip, never a blocker. The text schematic advances the work on any harness, so the operation is never suspended by the absence of an image-capable tool.

## Write boundary

`visualize` writes no file of its own. Its output reaches a consumer only as the compositional commitments recorded in the direction doc.

---

**References:** `references/refusals.md`
