---
name: Core
scope: repo
tagline: "The build loop. Spec → shipped code. Supervised."
skills:
  - work-loop
  - new-spec
  - bug-fix
  - contract-acquisition
  - receive-brief
  - init-project
  - adapt-to-project
installCommand: "agentbundle install --pack core"
docsUrl: /docs/guides/core/
journeyUrl: /journeys/core/
---

Core is the engine of the build loop. After installing it, every coding task runs through `work-loop`: plan → execute → verify → adversarial review. Mechanical gates (lint, typecheck, tests) and three specialist reviewers run every diff before it reaches a decision point — whether that decision is yours at a keyboard or your harness answering a gate programmatically.

The loop cannot self-certify. It always stops at plan approval and PR merge. Who answers those gates — a person or a control harness — is up to you.
