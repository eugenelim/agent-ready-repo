---
name: Architect
pluginInstallable: true
scope: user
tagline: "Assess what exists, decide what to do next, design, diagram, and review."
skills:
  - architect-assess
  - architect-design
  - architect-diagram
  - architect-review
installCommand: "agentbundle install --pack architect --scope user"
docsUrl: /docs/guides/architect/
journeyUrl: /journeys/architect/
---

Understand the architecture you have before you fund the change. Start with:

> Assess architecture and provide an action plan.

Architect returns a correctable current-state model, evidence coverage, an
attention heat map, bounded hotspot drill-downs, and dependency-aware action
waves. It can also shape a future-state design, draw Mermaid diagrams, or review
an assessment or design artifact in a cold context. Repository inspection is
read-only by default; private knowledge, executable checks, runtime evidence,
experiments, and file writes require approval.
