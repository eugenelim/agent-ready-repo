---
name: Core
pluginInstallable: false
scope: repo
tagline: "The agentic build loop that cannot self-certify."
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

Core is a complete build system for coding agents. Non-trivial work runs through `work-loop`: surface assumptions → plan → implement → lint, typecheck, and test → cold independent review → fix or finish. The adversarial reviewer is the hard review gate; security and quality lenses join when the diff warrants them. Fingerprinted findings expose stasis instead of letting the agent repeat the same failed approach.

The loop scales its ceremony with risk, but it never self-certifies. It stops at plan approval, unresolved boundaries, repeated findings, and PR merge. Who answers those gates—a person or a control harness—is up to you.
