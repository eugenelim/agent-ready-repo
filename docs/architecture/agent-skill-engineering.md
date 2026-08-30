# Agent skill engineering architecture

> **STATUS: PLANNED.** This document describes the future-state architecture
> accepted by [RFC-0097](../rfc/0097-agent-skill-engineering.md). It is not a
> statement of current repository behavior. [INI-009](../product/initiatives/ini-009-agent-skill-engineering.md)
> owns delivery. Keep this banner until every section described here—including
> profiles, self-hosting, migration, and closeout—is implemented and verified.
> Then update it to **CURRENT**, replace planned paths and contracts with their
> implemented forms, and record the verifying commit.

## 1. Purpose

The agent-skill-engineering capability gives authors and agent loops a portable
way to author, review, and reason about Agent Skills and adjacent extension
surfaces. It combines two active workflows with a progressively disclosed,
same-pack knowledge corpus. The corpus is useful to skill work, skill/evaluation
CI and execution design, agent-loop orchestration, and architecture analysis
without turning any consumer into a general handbook reader.

The architecture separates three concerns:

1. portable engineering workflows and knowledge;
2. product-specific, retrieval-dated runtime facts; and
3. AgentBundle catalogue, adapter, projection, and publication mechanisms.

Only the first two belong to the portable pack. AgentBundle remains an external
delivery mechanism.

## 2. Planned building blocks

```text
portable agent-skill-engineering pack
├── author-or-update-agent-skill        active, user-facing workflow
├── review-or-optimize-agent-skill      active, user-facing workflow
├── agent-skill-engineering-reference   inert, integration-facing router
├── compiled references                 ordinary Markdown, same-pack owned
└── OKF authoring corpus                 governed build-time source only

external consumers
├── work-loop
├── architect-design
└── later explicitly integrated loops

external delivery and governance
├── AgentBundle pack metadata and dependencies
├── runtime adapters and projections
├── catalogue lint, build, admission, and publication
└── repository self-host synchronization
```

The two active workflows own authoring and review behavior. The reference router
owns bounded topic selection and read-only responses. It does not edit files,
spawn agents, install dependencies, run candidate code, or grant authority.

The author/update workflow has progressive `frame`, `create`, `update`,
`knowledge-provider`, and `runtime-package` modes. M1 advertises only the first
three; M2 activates the latter two after their provider-pattern and package
profile gates pass. It selects a mode and compact pattern index first, then loads
only the relevant construction and usability topics. The repository pattern
census must classify every authored pack skill or record a reviewed exception;
it informs authoring without forcing rewrites.

## 3. Knowledge topology

The corpus is organized by task and capability rather than by source file. Of
the 36 leaves the taxonomy names, **7 are admitted and 29 are declared absent**
as of slice 2a; a leaf is in exactly one of those sets, never both and never
neither. Admission is evidence-limited, so the admitted count is expected to
stay well below the leaves enumerated below:

- foundations: framing, triggers, instruction density, progressive disclosure,
  resource placement, scripts, and exit contracts;
- reusable pattern and usability topics: inline, multi-mode, scripted, composed,
  lifecycle, knowledge-provider, orientation/read-model, workspace-resumption,
  progressive-presentation, and runtime-package designs;
- evaluation: activation, behavior, construction, fixtures, isolation, and cost;
- language topics: separate Python/pytest and TypeScript/Node guidance under
  shared portability and execution contracts;
- execution economics: skill process, pack suite, CI critical path, Git
  worktrees, state locks, and shared-host admission;
- composition: runtime-neutral capability floors for skills with subagents,
  hooks, and plugin packages;
- runtime profiles: Claude Code, Codex, GitHub Copilot, Cursor, Kiro IDE, Kiro
  CLI, Gemini CLI, and Google Antigravity;
- security and authority: instruction provenance, permissions, sandboxing,
  authentication/secret context isolation, side effects, and evidence privacy;
- maintenance: evidence promotion, applicability, measurement, regression, and
  retirement.

Admitted as of slice 2a: framing and trigger quality, instruction density and
progressive disclosure, resources/scripts/exit contracts, depth libraries and
OKF knowledge providers, activation discoverability and mode wayfinding,
progressive result presentation and next actions, and trust boundaries and
instruction provenance. Every other leaf above is recorded in the compiled
declared-absent register with why it is absent and what would admit it —
including `compatibility-and-runtime-package-patterns`, which cannot be written
without advertising a mode this slice bars, and
`inline-and-progressive-reference-skills`, which was authored and then withdrawn
because measured retrieval could not separate it from instruction density.

Open Knowledge Format (OKF) is an authoring representation. The owning pack
compiles it at build time into ordinary references and generated indexes. No
runtime component searches, interprets, or executes raw OKF.

## 4. Provider and consumer flow

```text
consumer recognizes an in-scope task
              │
              ▼
explicit semantic request (1–3 topics)
              │
              ▼
installed reference router
              │
              ├── out-of-scope / unavailable / stale-profile
              │
              ▼
generated same-pack index → selected compiled references
              │
              ▼
consumer applies advice under its own authority and gates
```

The semantic contract is versioned independently of transport. A request names
the task kind, bounded question, optional capabilities and exact runtime, and a
topic limit. A response names its status, selected topic identifiers, compiled
guidance, provenance/profile state when applicable, and warnings.

Provider use is optional. If the pack is absent, an initial consumer continues
its documented baseline workflow and reports that profile-backed augmentation
was unavailable. It must not search raw OKF or silently claim equivalent
validation. AgentBundle integration declarations are one way to install and
address the provider, but are not part of the portable contract.

## 5. Ownership and dependency rules

| Concern | Planned owner | Must not become |
| --- | --- | --- |
| Author/update and review/optimize procedure | Agent-skill-engineering pack | Catalogue-only workflow |
| OKF source, generated topic indexes, compiled references | Same owning pack | Runtime knowledge service |
| Consumer task authority and fallback | Invoking loop | Authority delegated to retrieved prose |
| Runtime capability facts | Retrieval-dated profile | Claim that all runtimes behave alike |
| AgentBundle metadata, adapters, projections, and publishing | AgentBundle/catalogue owners | Portable skill doctrine |
| Repository safety, enforcement, and exact commands | Existing repository owners | Optional retrieved knowledge |
| Provider integration declaration | Consuming/delivery pack metadata | Hidden dependency in portable instructions |

Allowed dependency direction is consumer → installed provider → provider-owned
compiled references. Generated projections are never authoring dependencies.
The provider does not depend on a consumer and does not resolve another pack's
raw knowledge source.

## 6. Trust and execution boundary

Candidate skills, scripts, hooks, subagent definitions, plugins, OKF, and
external pages are untrusted input. Intake is passive and confined; static
inspection precedes any execution. The workflows do not automatically install,
activate, or run candidate components. Any execution remains a separate,
explicitly approved action under the active managed permission profile, with
declared dependencies/network needs and least authority.

Authentication is outside the model context. A workflow can request a bounded
capability or invoke a trusted tool that attaches authentication beyond the
model boundary, but it does not read, copy, transform, persist, or print raw
credentials. The portable pack defines that separation without depending on or
naming any repository-specific credential broker.

Compiled output is deterministic and confined. Metadata is escaped, paths and
links are validated, and hostile input cannot write outside the build target.
Promoted evidence is minimized and redacted; published material excludes
credentials, raw sessions, personal identifiers, absolute home paths, private
hostnames, and unrelated enterprise details.

Hooks remain executable runtime mechanisms, not prose enforcement. Subagents
receive only needed context and authority, have explicit write ownership and
concurrency limits, and return results to the parent for synthesis. Managed
enterprise policy and the actually exposed tool surface always override local
configuration or corpus advice.

## 7. Runtime-profile lifecycle

Every runtime claim records its source URI, date retrieved, exposed source
version or update date, claim scope, and last verification result. Capability
claims use four explicit states:

- `verified`: current official evidence plus a passing contract fixture or
  bounded manual probe;
- `experimental`: sourced but preview-only or not independently probed;
- `stale`: the verification window elapsed or relevant source/release changed;
  operative advice is withheld;
- `unavailable`: evidence conflicts, the capability is absent, or safe
  verification cannot be performed.

A profile is `complete-current` when every required capability row has current
first-party evidence and one of `verified`, `experimental`, or `unavailable`.
An unavailable capability is an explicit product delta, not an incomplete
profile. Any stale row rolls the profile to `needs-revalidation`; any missing
required row makes it `incomplete`.

For every runtime package format the profile covers, required rows include
scope and precedence, namespace/collision behavior, package provenance or
integrity, install/update/disable/uninstall recovery, managed policy, and
authentication/secret handling. Package fixtures verify that disable or
uninstall leaves no active hook, executable component, permission, writable
state, or shadowing user/team entry unless the runtime explicitly documents and
surfaces retained user data.

A knowledge profile is not an adapter-support claim. A surface may have useful
direct-install guidance without an AgentBundle projection adapter. Adapter
support changes remain separately governed and tested outside the pack.

## 8. Self-hosting and migration

Self-hosting proceeds add → integrate → route and compare → collapse. Existing
guidance remains authoritative until the installed provider and cold-agent task
fixtures demonstrate replacement coverage.

The migration may shorten duplicated explanatory practice in
`AGENTS.local.md`, scoped pack guidance, catalogue-curation, maintainer and
author guides, and tooling explanations. It must retain always-loaded safety,
repository facts, exact commands, executable checks, pack metadata mechanics,
and fallback routes at their current owners. A footprint change is complete
only when fixed task checklists retain correctness while always-loaded lines and
median retrieved bytes decrease.

## 9. Delivery and verification

RFC-0097 defines four gates: corpus/router, workflow behavior, runtime profiles,
and self-host footprint. The foundation slices of corpus/router and workflow
behavior block the foundation pack release. Their expanded pattern/usability
slices and runtime profiles block M2, not the already-valid portable floor.
Runtime-profile failures constrain the affected profile state. Footprint
failures block the corresponding deletion.

The delivery specs must replace planned names and paths in this document with
implemented contracts, link their tests, and update the architecture index.
Only when every described foundation, corpus, profile, integration, self-host,
migration, and closeout contract is live and verified does this document become
the maintained current architecture reference; RFC-0097 remains the decision
history.

## 10. Governing records

- [RFC-0097 — Agent skill engineering](../rfc/0097-agent-skill-engineering.md)
- [ADR-0093 — OKF reference corpora remain governed build-time sources](../adr/0093-okf-reference-corpora-remain-governed-build-time-sources.md)
- [INI-009 — Agent skill engineering](../product/initiatives/ini-009-agent-skill-engineering.md)

## 11. Last verified

Planned architecture drafted 2026-08-26. Slice 2a (corpus) verified 2026-08-30
against pack version 0.2.0: 7 topics admitted of 36 leaves, retrieval measured
at 40/40 exact-set agreement over 40 declared cases, and a fixed 40-prompt
generic-engineering negative set returning a topic body for 0 of 40 against a
bar of at most five percent. Activation observed headless at 18/18 with zero
exclusivity violations. This document stays **PLANNED**: runtime profiles,
language and execution topics, and the composition floors described above are
not implemented, and slice 2a claims no surface belonging to them.
