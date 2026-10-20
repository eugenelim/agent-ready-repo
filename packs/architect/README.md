# Architect

Your agent can assess the architecture you have, design the one you need, draw it, and review it.

## Install

You need [`agentbundle`](../../guides/_shared/how-to/install-agentbundle.md) first. Install it once for your user account:

```bash
agentbundle install --pack architect
```

In Claude Code you can install it as a plugin instead:

```bash
claude plugin install architect@agent-ready-repo
```

## What your agent can do

- Assess a repository: map the system, show where its evidence is thin, drill into hotspots, and propose action waves in dependency order.
- Design a system, subsystem, or change from a one-page concept, with the rationale beside each model.
- Draw Mermaid diagrams for flows, sequences, deployments, data models, and roadmaps, with an optional editable draw.io file.
- Review an assessment, design doc, diagram, RFC, or ADR and return a verdict with findings ranked by severity.
- Write a solution reference architecture for a coordinating repo with no app code.
- Turn a design into a physical architecture and bill of materials (BOM) covering cloud services, container images, open-source libraries, hardware, network connections, and licences, with a delta BOM for a change.
- Check a design against well-architected lenses, including cloud and agentic workloads.

## Skills

- **`architect-assess`** — Maps the implemented system, shows evidence coverage and attention hotspots, and proposes action waves. Read-only by default.
- **`architect-design`** — Shapes a concept first, then writes a design doc matched to the scope of the change. Also writes a solution reference architecture and, on request, a physical architecture and BOM.
- **`architect-diagram`** — Draws a Mermaid diagram chosen from what you ask for, and checks it before it shows you.
- **`architect-review`** — Critiques an architecture artifact and gives a verdict with severity-tagged findings.
- **`architecture-lenses-reference`** — An internal knowledge router for the others. You never invoke it yourself.

Subagent: **`design-reviewer`** is a read-only reviewer that works in a fresh context, so it does not grade its own work.

## Works with

Works with Claude Code, Codex, Cursor, GitHub Copilot, Gemini CLI, Kiro IDE, and Kiro CLI. Add [Core](../core/README.md) to save a design where your repository keeps its architecture records, and to reconcile it after the change ships. Your reference architecture guides each design. [Product Engineering](../product-engineering/README.md) offers it at some shaping steps when both are installed. Guides that use this pack: [Design the architecture](../../guides/architect/README.md) and [Assess a repository](../../guides/architect/how-to/assess-a-repository.md).

## Questions

**Does an assessment change my repository?** No. It reads documents, source, tests, CI, and local Git history. Saving a file is optional, and you approve it.

**Does it run my build, tests, or deploys?** No, not without asking. Runtime access and experiments need separate approval.

**What if I have no reference architecture?** The design says so in its concept. It offers Core's `adapt-to-project` or `init-project` to set one up when Core is installed. For a solution repo with no app code, it authors a solution reference architecture itself in its solution reference mode.

**Does the BOM include prices?** Each line is `priced` with its source, date, and region, `unpriced` when no grounded price exists, or `no direct cost`. Unpriced lines are counted and left out of the total. No price comes from model memory, and prices are in USD unless you name another currency.

**What does a BOM line identify?** Its kind and the exact item. A cloud service shows its plan code (SKU) and tier. A container image shows its registry address. An open-source library shows its package URL, a standard name that includes the version, and its licence. A node shows its hardware model and spec. A network link shows its endpoints and bandwidth. A commercial licence shows its product and edition. A design with no deployment section gets no BOM until the design names what runs where. If the physical choices contradict the design, the agent raises it as a design finding.

**Can it work without Core?** Yes. Without Core it returns the result in chat or saves to a personal workspace you choose.

## Details

Scope: user (default), repo · Version: 0.15.19 · Source: [packs/architect](https://github.com/eugenelim/agent-ready-repo/tree/main/packs/architect)
