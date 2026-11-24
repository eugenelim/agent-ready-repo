---
title: Platform Engineering guides
summary: Author reviewed infrastructure, collect release evidence, and validate a deployed change before deciding to ship.
pack: platform-engineering
kind: reference
---

# Platform Engineering guides

These guides help you author reviewed infrastructure and validate releases before your production decision.

## Start here


- [Change infrastructure](how-to/change-infrastructure.md) — Turn a plain-language request into reviewed Terraform or OpenTofu, and keep your environment in sync.

## Infrastructure reference and explanation

- [Authoring gate](reference/authoring-gate.md) — Commands, record fields, stop codes and limits for governance and review.
- [Plan bundle](reference/plan-bundle.md) — Fields, commands, limits and validation outcomes for reviewed saved plans.

- [Deciding before generating](explanation/deciding-before-generating.md) — Why decisions are recorded before infrastructure is generated.
- [Infrastructure in the release loop](explanation/infrastructure-in-the-release-loop.md) — Infrastructure as the release loop with a different payload.
- [What the preview cannot tell you](explanation/what-the-preview-cannot-tell-you.md) — The three blind spots of the change preview.


- [Release a change](how-to/run-a-release.md) — Deploy a finished change to a test environment, check it works, and record your approval to ship it to production.

## Release reference and explanation

- [Run a release with GitHub Actions](how-to/run-a-release-with-github-actions.md) — Prepare and review a release, approve its exact digest, and check the protected job's deployment and cleanup evidence.

- [Release admission](reference/release-admission.md) — Collection gaps, admission records, focused review results and stage checks.

- [Release handoff](reference/release-handoff.md) — Candidate fields, v1 import gaps, commands and validation outcomes.

- [Your first release](tutorials/your-first-release.md) — A complete walkthrough of a release cycle from deploy-ready build to a ratified ship decision — deploy, converge, and ratify G5.
- [The release loop explained](explanation/the-release-loop.md) — Why a deploy-verify-converge outer loop closes the gap between passing tests and working in production — and why the reversibility carve is the key design decision.
- [Release-readiness record](reference/release-readiness-record.md) — Field reference for the release-readiness record — sections, verdicts, and when G5 is available.

- [Migrate your platform packs](how-to/migrate-from-iac-terraform-and-release-engineering.md) — Move installed packs in two phases, preserve edits, and roll back from a pinned catalogue.
