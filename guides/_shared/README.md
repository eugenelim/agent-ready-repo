---
title: Shared guides
summary: Find cross-catalogue guidance for installing, upgrading, authoring, integrating, and understanding packs regardless of which packs you use.
pack: _shared
kind: explanation
---

# Shared guides

Guides about the catalogue itself — installing it, upgrading it, seeing what each agent tool supports, authoring new skills — rather than any one pack. Pack-specific guides live under each pack's own home; these are the cross-cutting ones.

## How-to

- [Install agentbundle](how-to/install-agentbundle.md) — pip, a clone, or APM, and corporate-network fixes.
- [Install packs for your agent](how-to/install-packs.md) — scopes, adapters, profiles, the whole lifecycle, and `--dry-run`.
- [Configure agentbundle](how-to/configure-agentbundle.md) — default adapter, catalogue source, and sign-in.
- [Upgrade packs](how-to/upgrade-packs.md) — pull new pack content without clobbering your edits.
- [Author a skill](how-to/author-a-skill.md) — write a new skill for any pack, to the catalogue's standards.
- [Author a browser-automation skill](how-to/browser-automation-skill.md) — persistent-profile auth, bearer token interception, probe files, and `ui-patterns.md` maintenance for skills that drive a browser.
- [Choose a tracker integration](how-to/choose-a-tracker-integration.md) — pick the right brief-intake skill for your tracker (GitHub, Linear, Jira, Jira Align, or none).
- [Start, remember, inspect, or refresh repository work](how-to/use-work-intake.md) — use the shared content-based front door and keep local and remote writes explicit.
- [Create an external catalogue](how-to/create-external-catalogue.md) — scaffold a catalogue outside this repository, validate it, and publish it via CI.

## Reference

- [`agentbundle` reference](reference/agentbundle.md) — install the CLI, install a pack, configure the default adapter, source-resolution chain, environment variables.
- [Catalogue CI contract](reference/catalogue-ci-contract.md) — provider-neutral contract for validation, packaging, publication ordering, exit codes, and responsibility boundaries in a catalogue CI pipeline.
- [Adapter support matrix](reference/adapter-support.md) — which primitives each agent tool receives, and where it degrades.
- [Tracker vocabulary](reference/tracker-vocabulary.md) — how brief and spec levels map across GitHub, Linear, Jira, and Jira Align; skill routing table.
- [Work-intake routing and lifecycle](reference/work-intake-routing-and-lifecycle.md) — exact cross-profile routes, authority modes, dispatch rules, refresh states, and migration boundary.
- [Output rendering directives](reference/output-rendering.md) — the canonical directive catalog: which shape to declare in `## Output rendering` (Table, Status list, Severity list, Diagram, etc.) and when to omit.
- [Skill UX patterns](reference/skill-ux-patterns.md) — craft-depth companion to output-rendering: column alignment rules, truncation limits, persistent command bar, delete-gate box, card format for review flows.
- [Skill script conventions](reference/skill-script-conventions.md) — CLI flag conventions, usage docblocks, shortcut IDs, shared-libs pattern, idempotent setup, pack-config API.

## Explanation

- [The operating model](explanation/the-operating-model.md) — how work flows from idea to production, which packs help at each stage, and why discovery, build, and release are separate loops.
- [The pack catalogue](explanation/pack-catalogue.md) — what a pack is, how the catalogue is composed, and how you build your own.
- [The file-safety contract](explanation/file-safety-contract.md) — why your edits are never silently overwritten.
- [Shaping a new engagement](explanation/shaping-a-new-engagement.md) — how a product vision, a product strategy, and an architecture concept co-shape each other at the start of a new engagement.
- [How work records divide responsibility](explanation/work-artifact-responsibilities.md) — why source evidence, canonical artifacts, workspace state, processors, and the migration ledger have separate jobs.

---

Each quadrant subdirectory also carries a short writing-rules README ([tutorials](tutorials/README.md) · [how-to](how-to/README.md) · [reference](reference/README.md) · [explanation](explanation/README.md)) — what belongs in that kind of guide, for anyone authoring one.
