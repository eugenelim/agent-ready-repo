---
hide:
  - navigation
  - toc
---

<div class="hero-section" markdown>
# The Complete AI Operating Model<br>for Software Teams

Three supervised loops, fourteen curated packs, any agent, any stack — from first idea to production.

<div class="hero-actions" markdown>
[Get started :octicons-arrow-right-24:](getting-started/index.md){ .md-button .md-button--primary .md-button--large }
[Browse packs :octicons-arrow-right-24:](packs/index.md){ .md-button .md-button--large }
</div>
</div>

## Three supervised loops. One handoff chain.

The leverage in agent coding moved from the prompt to the **loop** — it plans, executes, verifies, and decides what comes next. But a loop running unattended is also a loop making mistakes unattended, so it has to check its own work harder than you would.

Software delivery needs more than one loop. Three peer supervisors span the full lifecycle:

<div class="grid cards" markdown>

-   :material-lightbulb-outline:{ .lg .middle } **Discovery Loop**

    ---

    `product-engineering` · `discovery-lead`

    Raw idea → ratified brief. Five candidate shapes explored in parallel, collapsed through product, UX, architecture, and safety lenses. Human gates at G0, G1.5, G2. A connected hypothesis with validation hooks — not a validated solution.

    [:octicons-arrow-right-24: Product Engineering](packs/product-engineering.md)

-   :material-cog-outline:{ .lg .middle } **Build Loop**

    ---

    `core` · `work-loop`

    Spec → shipped code. Hard mechanical gates (lint, typecheck, tests), three specialist reviewers each reading the diff cold, adversarial in a fresh session. The loop the agent can't self-certify its way out of.

    [:octicons-arrow-right-24: Core pack](packs/core.md)

-   :material-rocket-launch-outline:{ .lg .middle } **Release Loop**

    ---

    `release-engineering` · `release-lead`

    Built → production. Autonomous e2e convergence on ephemeral environments. Deployed findings feed back to the build loop automatically. Prod ship always surfaces to a human — G5 is never autonomous.

    [:octicons-arrow-right-24: Release Engineering](packs/release-engineering.md)

</div>

```
product-engineering           core                    release-engineering
───────────────────           ────                    ───────────────────
discovery-lead                work-loop               release-lead
Raw idea → Brief       ─G3─▶  Spec → Shipped   ─G4─▶  Built → Production
```

## Install in one line

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

One command lands the loop in your repo. Any agent that reads a skill file inherits it automatically.

## The catalogue

Fourteen curated packs — each distilled from the best practices of its discipline through research and architecture decisions. `repo` packs install into the current repository; `user` packs install once for all repos.

**Start with the loops:**

<div class="grid cards" markdown>

-   **Core** `repo`

    The build loop. `work-loop`, `new-spec`, `bug-fix`, four specialist reviewers, hooks. **Install this even if you install nothing else.**

    [:octicons-arrow-right-24: Core](packs/core.md)

-   **Product Engineering** `user`

    The discovery loop. `discovery-loop`, `frame-intent`, `de-risk-intent`, `decompose-intent`, `voice-and-microcopy`, `align-value-stream`.

    [:octicons-arrow-right-24: Product Engineering](packs/product-engineering.md)

-   **Release Engineering** `repo`

    The release loop. `release-loop`, `release-lead`. Autonomous e2e convergence. Hard-depends on core.

    [:octicons-arrow-right-24: Release Engineering](packs/release-engineering.md)

</div>

**Add what your team needs:**

<div class="grid cards" markdown>

-   **Research** `user`

    Evidence-grounded research. `research`, `source-map`, `compare-hypotheses`, `devils-advocate`, `decision-archaeology`, two retrieval subagents.

    [:octicons-arrow-right-24: Research](packs/research.md)

-   **Architect** `user`

    System design. `architect-design`, `architect-diagram`, `architect-review`, `design-reviewer` subagent.

    [:octicons-arrow-right-24: Architect](packs/architect.md)

-   **Experience** `user`

    The full design thread — journey to realization. Journey mapping, screen flows, service blueprints, aesthetic direction, WCAG-aware quality floor.

    [:octicons-arrow-right-24: Experience](packs/experience.md)

-   **Contracts** `user`

    API-first design. `api-contract` for OpenAPI 3.1, `event-contract` for AsyncAPI.

    [:octicons-arrow-right-24: Contracts](packs/contracts.md)

-   **Converters** `user`

    Document conversion. PDF/DOCX/PPTX → Markdown, Markdown → HTML/Word/PowerPoint/Excel, email → Markdown, Mermaid rendering.

    [:octicons-arrow-right-24: Converters](packs/converters.md)

-   **Atlassian** `user`

    Jira and Confluence from the agent. `jira`, `jira-align`, `confluence-crawler`, flow metrics, DORA metrics. SSO-cookie authenticated.

    [:octicons-arrow-right-24: Atlassian](packs/atlassian.md)

-   **Figma** `user`

    Read and render Figma designs. Files, nodes, variables, frame renders, FigJam → Mermaid.

    [:octicons-arrow-right-24: Figma](packs/figma.md)

-   **Governance Extras** `repo`

    Decision trail. `new-rfc`, `new-adr`, `update-conventions`, RFC/ADR ceremony for long-lived repos.

    [:octicons-arrow-right-24: Governance Extras](packs/governance-extras.md)

-   **User Guide (Diataxis)** `repo`

    Docs scaffold. Diátaxis skeleton with `new-guide`.

    [:octicons-arrow-right-24: User Guide Diataxis](packs/user-guide-diataxis.md)

-   **Monorepo Extras** `repo`

    Package scaffolding. `new-package`, example package template.

    [:octicons-arrow-right-24: Monorepo Extras](packs/monorepo-extras.md)

-   **Credential Brokers** `user`

    Credential resolution. Environment variable → OS keyring → dotfile. Cleartext never reaches the model.

    [:octicons-arrow-right-24: Credential Brokers](packs/credential-brokers.md)

</div>

## Works with every major agent { #adapters }

One adapter pipeline projects the same skills and subagents into the layout every agent expects.

| Agent | Skills | Subagents | Hooks | Commands |
|---|---|---|---|---|
| Claude Code | Yes | Yes | Yes | Yes |
| Codex | Yes | Yes | Yes | No |
| Cursor | Yes | Yes | Yes | No |
| Copilot | Yes | Yes | Yes | No |
| Gemini CLI | Yes | Yes | Yes | No |
| Kiro | Yes | Yes | No | No |

## Built on solid foundations

<div class="grid" markdown>

<div markdown>

**Harness-agnostic.** One adapter pipeline projects the same primitives into every agent's layout. Switch adapters with one flag.

**Inspectable and forkable.** Skills, subagents, and hooks are files you own — no SDK, runtime, or service to run. Outgrow a default? Edit the file.

</div>

<div markdown>

**Composable.** Packs layer cleanly. Your edits are never silently overwritten — colliding files land as `*.upstream` companions to merge, not clobber.

**Curated by discipline.** Every pack is shaped through practitioner research and RFC-and-ADR governance. Not random defaults — the best available practices encoded as runnable skills.

</div>

</div>

The two pip packages underneath are standalone and useful beyond this repo:

- **[`agentbundle`](https://pypi.org/project/agentbundle/)** — installs and upgrades packs, projects each primitive into the layout every agent expects, and builds catalogues of your own.
- **[`credbroker`](https://pypi.org/project/credbroker/)** — credential resolution for credentialed skills. Resolves secrets through environment → OS keyring → dotfile. Cleartext never reaches the model.

## A foundation to build on

Adopt the catalogue as-is, or fork it as your own. Write your house conventions and review standards into `core`, add skills for your stack, and ship one catalogue every engineer installs in a single line — the loop, the reviewers, and the standards come out identical on every machine and in every agent.

[:octicons-arrow-right-24: How to build your org's catalogue](guides/_shared/how-to/build-an-org-stack-pack.md)
