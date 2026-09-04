---
title: Install the whole lifecycle
summary: Compose the user-scope shaping profile, the repo-scope build profile, and the packs in neither, in the order a new team needs them.
pack: _shared
kind: how-to
---

# Install the whole lifecycle

**Use this when:** you are setting a team up to run shaping, building, governance,
and release from this catalogue, and you want the whole path rather than one pack.

**Before you start:** the `agentbundle` CLI on your PATH. See
[Choose an install route](../explanation/install-routes.md) if you do not have it
yet.

There is no single command that installs everything. The lifecycle crosses two
scopes — shaping follows *you* across repositories, building belongs to *the
repository* — and a profile installs at one fixed scope with no override. So a
team composes it. This page is that composition, in order.

## 1. The build loop, into the repository

Do this first. Every lifecycle pack downstream of shaping either depends on
`core` or hands work to it.

```bash
agentbundle install --profile full-ceremony .
```

That is `core` (the build loop), `governance-extras` (RFCs and ADRs),
`product-documentation`, and `monorepo-extras`, all at repo scope.

Then, in a fresh agent session, adapt the repository to itself:

```text
Run adapt-to-project for a read-only readiness check.
```

For a brand-new repository, use `init-project` instead — see
[Start a project](../../core/how-to/start-a-project.md).

## 2. The shaping toolkit, at user scope

```bash
agentbundle install --profile inception
```

That is `desk-research`, `product-engineering`, and `architect`. It installs at
**user** scope deliberately: shaping travels with you across every repository you
work in, and the profile's scope is fixed.

A solution architect who does not shape product can install
`solution-architect` instead — `architect`, `desk-research`, and `contracts`.

## 3. The packs in neither profile

Fourteen packs are in no profile. Install the ones your team actually uses:

| Pack | Install when | Scope |
| --- | --- | --- |
| `product-strategy` | you set direction, OKRs, or market position | user |
| `experience-design` | you design journeys, flows, and screens | user |
| `frontend-engineering` | you build UI surfaces against a page contract | repo |
| `contracts` | you author API or event contracts | repo |
| `release-engineering` | you validate a deployed artifact — **needs `core`** | repo |
| `iac-terraform` | you author governed Terraform | repo |
| `atlassian`, `linear`, `github` | your team uses that tracker | scope of its credentials |
| `figma`, `converters`, `credential-brokers` | you pull from those sources | as needed |
| `catalogue-curation`, `agent-skill-engineering` | you build your own packs | user |
| `user-guide-diataxis` | you write Diátaxis-shaped user guides | user |

```bash
agentbundle install --pack release-engineering .
```

`release-engineering` hard-depends on `core`, so step 1 must be done first. The
installer checks every precondition before writing anything and refuses by name
if one fails.

## 4. Confirm the whole path works

Start a fresh agent session in the repository and orient:

```text
workspace status
```

You should see the repository's queues and the skills each installed pack
contributes. If a skill you expect is missing, start a new session — a
just-installed skill is not available to a session that was already running.

## What you have now

A repository that can carry work from a raw idea to a ratified production ship:
shaping at user scope, the build loop and governance in the repository, and
whichever release, design, or tracker packs your team uses. The next step is to
shape something — see
[Shape a feature intent](../../product-engineering/how-to/shape-a-feature-intent.md),
then
[Hand an intent to the build loop](../../product-engineering/how-to/hand-an-intent-to-build.md).

## See also

- [The three loops](../explanation/the-three-loops.md) — why shaping, building, and release are separate
- [Install a profile](install-a-profile.md) — what a profile is and what it prints
- [Choose an install route](../explanation/install-routes.md) — marketplace, APM, CLI, or clone
- [Run a full inception](run-a-full-inception.md) — which shaping stages a new engagement actually needs
