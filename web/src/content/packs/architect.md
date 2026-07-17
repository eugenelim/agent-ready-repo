---
name: Architect
scope: user
tagline: "Design docs, diagrams, and reviews — workspace-agnostic."
skills:
  - architect-design
  - architect-diagram
  - architect-review
installCommand: "agentbundle install --pack architect --scope user"
docsUrl: /docs/guides/architect/
---

Architect installs three solution-architecture skills: `architect-design` (Google-style design docs), `architect-diagram` (Mermaid diagrams — C4, sequence, state, ER), and `architect-review` (rubric-routed critique). A forked-context `design-reviewer` subagent gives every design an independent read — it does not review its own work. No required configuration; workspace-agnostic by default.
