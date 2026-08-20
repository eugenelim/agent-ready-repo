---
title: The pack catalogue
summary: Understand how packs, profiles, adapters, catalogues, and `agentbundle` compose into an organization-owned workflow distribution system.
pack: _shared
kind: explanation
---

# The pack catalogue

The catalogue is an organization-owned distribution system for repeatable agent workflows. It is not a starter template and it is not one indivisible operating model. You choose packs for the work your team does, combine them into profiles when a standard starting set is useful, and use `agentbundle` to project the same source into each supported agent's native layout.

This repository is both a reference catalogue and a self-hosted adopter of that system. Its `packs/` sources produce the skills and agent primitives it uses itself, so the published material and the repository's working practice can be checked for drift.

## The four parts

| Part | What it owns |
| --- | --- |
| **Pack** | A cohesive workflow or capability: skills, agents, hooks, commands, configuration, and optional seed files |
| **Profile** | A curated, single-scope list of packs installed together in dependency order |
| **Adapter** | The projection from portable pack primitives into an agent's on-disk conventions |
| **Catalogue** | The organization-owned inventory, defaults, contracts, validation, packaging, and distribution policy |

`agentbundle` is the transport and safety layer. It discovers catalogues, validates their contracts, installs or upgrades packs, records state, preserves adopter edits, and builds catalogue distributions. It is not a hosted service and it does not execute the installed skills.

## Start with an outcome, install a pack

Pack names are the stable installation layer, not the discovery language. A product manager may begin with “decide what to build” and arrive at `product-strategy`, `desk-research`, and `product-engineering`. An infrastructure team may begin with “provision and release safely” and arrive at `architect`, `contracts`, `iac-terraform`, `release-engineering`, and the supervised `core` loop.

The [guide hub](../../) maps the catalogue by outcome and role. Each pack guide then explains its natural-language starter request, expected artifact, safety boundary, and install route.

`core` is the flagship pack because supervised software implementation is a short, verifiable demonstration of the model. It provides the work loop, repository context, mechanical gates, and independent reviewers. Other packs can be useful before, beside, or after it; the catalogue is broader than the build loop.

## Repo scope and user scope

Scope answers where a pack belongs, not who it is for.

- **Repo-scope packs** install into a project and can carry repository-specific hooks, conventions, or seed files.
- **User-scope packs** install into an adapter's user root and follow a practitioner across projects.
- Some portable packs allow either scope. The pack manifest declares the allowed scopes and default; `agentbundle` refuses an unsupported placement.

Adapter support is also declared rather than assumed. The [adapter support reference](../reference/adapter-support.md) shows which primitive types each supported agent can represent and where fidelity differs.

## Profiles are starting sets, not mega-packs

A profile promotes a useful pack combination into one installable unit. It adds no primitives of its own and does not hide the packs it contains. Preflight validates the entire single-scope set before the first write, then installs it in dependency order.

Use [`agentbundle list-profiles`](../reference/agentbundle.md) to see the current sets and [install a profile](../how-to/install-a-profile.md) when one matches your role or project. Upgrade and removal continue to operate on individual packs.

## Composition stays visible

Packs may require another pack or declare an optional integration with one. Required dependencies control safe installation order. Optional `[[pack.integrations]]` entries describe useful composition without silently installing or dispatching another pack.

This keeps the unit of ownership visible: installing a product-shaping pack does not quietly add an infrastructure workflow, and installing an integration does not grant it permission to mutate an external system. Each pack retains its own scope, dependencies, safety boundary, and human decision point.

When two installed packs target the same path, the [file-safety contract](file-safety-contract.md) protects adopter-owned changes. Catalogue-owned files can upgrade in place; changed files are preserved and the new upstream version is written as a companion for deliberate merging.

## Own and self-host the system

An organization does not need to fork this repository to create a catalogue. Initialize the managed scaffold:

```bash
agentbundle catalogue init my-catalogue --name my-catalogue
```

Then add or adapt packs, declare profiles and defaults, validate the contracts, and package the result through the portable catalogue commands. The [create-a-catalogue guide](../how-to/create-a-catalogue.md) walks through the first valid catalogue; the [authoring standards](../reference/catalogue-authoring-standards.md) define the pack, profile, guide, and contract boundaries; the [catalogue CI contract](../reference/catalogue-ci-contract.md) defines verify → package → publish without prescribing a CI provider.

The full public guide tree is documentation source mirrored into this project's technical site. It is not currently included in archives produced by `agentbundle catalogue package`; catalogue operators should publish or distribute the guide site separately until that packaging contract changes.

## What you own after installation

Installed primitives are files you can read and version. There is no agent runtime or hosted control plane between your team and those files. The adapter projection is reproducible, and local changes remain visible in `git diff` or the user-scope filesystem.

For sensitive integrations, the [`credential-brokers` guide](../../credential-brokers/) explains how credentials resolve inside the helper process instead of being copied into prompts or command arguments.

## Where to go next

- [Choose work by outcome or role](../../).
- [Compare install routes](install-routes.md).
- [Preview an install or upgrade](../how-to/preview-install-or-upgrade.md).
- [Understand the three supervised loops](the-three-loops.md).
- [Create a catalogue](../how-to/create-a-catalogue.md).
