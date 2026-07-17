---
name: Release Engineering
scope: repo
tagline: "Deploy. Verify. Converge. Then ship."
skills:
  - release-loop
installCommand: "agentbundle install --pack release-engineering"
docsUrl: /docs/guides/release-engineering/
journeyUrl: /journeys/release/
---

Release Engineering installs the SRE outer loop. The `release-lead` agent drives `release-loop`: deploys the integrated whole to an ephemeral environment, runs end-to-end tests, observes telemetry, feeds deployed findings back to the inner loop — no human relay — and iterates until the deployed whole converges. Autonomy is carved by minimum-regret: the agent runs on reversible ephemeral environments unwatched; humans gate the irreversible exits. Hard-depends on `core`.
