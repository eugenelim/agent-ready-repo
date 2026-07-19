---
hide:
  - navigation
  - toc
---

<div class="hero-section" markdown>
# Reference documentation

Pack reference, getting-started guides, and the full skill catalogue.  
For an overview of the supervised loops and the pack catalogue, see the [platform site](https://eugenelim.github.io/agent-ready-repo/).

<div class="hero-actions" markdown>
[Getting started :octicons-arrow-right-24:](getting-started/index.md){ .md-button .md-button--primary .md-button--large }
[Browse packs :octicons-arrow-right-24:](packs/index.md){ .md-button .md-button--large }
</div>
</div>

## Quick install

=== "Flagship loop"

    ```bash
    pip install agentbundle
    agentbundle install --pack core
    ```

=== "With discovery"

    ```bash
    agentbundle install --pack core
    agentbundle install --pack product-engineering --scope user
    ```

=== "Full inception profile"

    ```bash
    agentbundle install --profile inception
    ```

=== "Solution architect"

    ```bash
    agentbundle install --profile solution-architect
    ```

## Packs

**Supervised loops (start here):**

| Pack | Scope | What it installs |
|---|---|---|
| [Core](packs/core.md) | `repo` | `work-loop`, `new-spec`, `bug-fix`, specialist reviewers, hooks |
| [Product Engineering](packs/product-engineering.md) | `user` | `discovery-loop`, `frame-intent`, `de-risk-intent`, `decompose-intent` |
| [Release Engineering](packs/release-engineering.md) | `repo` | `release-loop`, `release-lead` |

**User-scope packs (follow you across repos):**

| Pack | What it installs |
|---|---|
| [Desk Research](packs/desk-research.md) | `desk-research`, `source-map`, `compare-hypotheses`, `devils-advocate`, `decision-archaeology` |
| [Architect](packs/architect.md) | `architect-design`, `architect-diagram`, `architect-review`, `design-reviewer` subagent |
| [Experience](packs/experience.md) | Journey mapping, screen flows, aesthetic direction, experience reviewers |
| [Contracts](packs/contracts.md) | `api-contract` (OpenAPI 3.1), `event-contract` (AsyncAPI) |
| [Converters](packs/converters.md) | PDF/DOCX/PPTX → Markdown, Markdown → HTML/Word/PowerPoint/Excel |
| [Atlassian](packs/atlassian.md) | `jira`, `jira-align`, `confluence-crawler`, `confluence-publisher`, `flow-metrics` |
| [Figma](packs/figma.md) | Figma REST API — files, frames, variables, FigJam → Mermaid |
| [Credential Brokers](packs/credential-brokers.md) | `credbroker`, `sso-broker`, `credential-setup` |

**Repo-scope packs (per-project conventions):**

| Pack | What it installs |
|---|---|
| [Governance Extras](packs/governance-extras.md) | `new-rfc`, `new-adr`, `update-conventions` |
| [User Guide (Diátaxis)](packs/user-guide-diataxis.md) | `new-guide`, Diátaxis `guides/` skeleton |
| [Monorepo Extras](packs/monorepo-extras.md) | `new-package`, `packages/_example/` template |

## A foundation to build on

Adopt the catalogue as-is, or fork it as your own org's catalogue.

[:octicons-arrow-right-24: How to build your org's catalogue](guides/_shared/how-to/build-an-org-stack-pack.md)
