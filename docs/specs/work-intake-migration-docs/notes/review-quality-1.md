# Quality implementation review — round 1

## Blockers

**1. Changelog release inserted at the wrong boundary.** `docs/product/changelog.md:184`. The new `## [agentbundle][0.38.7]` heading sits immediately after `## [Unreleased]`, closing that region before the existing marooned `### [core][2.10.3]` entries, so the ratchet no longer tracks those deferred entries and the changelog nests them under the AgentBundle release. Fix: move the AgentBundle 0.38.7 section above `## [Unreleased]` with the other released entries, leaving the existing marooned `###` entries under Unreleased until their dedicated promotion work.
