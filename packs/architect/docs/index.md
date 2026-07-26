# Architect

> A user-scope pack of three architecture skills plus a forked-context design-reviewer subagent — workspace-agnostic, no configuration required.

## Why this pack exists

Architecture decisions made without a structured format tend to live in PR descriptions or Slack threads where they are hard to find, hard to critique independently, and impossible to compare against alternatives. With this pack, an agent can produce a Google-style design document that surfaces context, proposal, alternatives, and risks in a consistent shape — and then hand it to an independent subagent for a critique that doesn't share the authoring assumptions.

## What it is

**Skills (3):** `architect-design` (frame a problem and produce a design document — TL;DR, context, proposal, alternatives considered, and risks), `architect-diagram` (produce Mermaid diagrams across eight view types: system context, container, component, sequence, state machine, entity-relationship, C4, and roadmap), `architect-review` (critique an architecture artifact with severity-tagged findings and a SHIP IT / SHIP WITH CHANGES / MAJOR REWRITE / WRONG ARTIFACT verdict).

**Subagents (1):** `design-reviewer` — forked-context, read-only architecture critique subagent. It receives only the artifact and the agreed constraints, never the authoring chain of thought, so it gives an independent second opinion.

No hooks. No seeds.

See the README for the complete manifest table.

## What it is not

- Not a UML modeling tool — it produces Mermaid diagrams as design intent artifacts, not as formal model-driven engineering inputs.
- Not a diagramming GUI — it generates diagram source that renders in any Mermaid-compatible viewer.
- Not a code architecture linter — it evaluates design documents and diagrams, not source code structure.

## How it relates to other packs

No required pack dependencies. `core`'s `adversarial-reviewer` subagent complements `architect-review` when an architectural change is part of a larger implementation: architect-review evaluates the design document; adversarial-reviewer evaluates the implementation diff against the spec.
