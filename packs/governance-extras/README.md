# Governance Extras

Your agent can write the RFC for a proposed change, record the ADR for a decision, and look up what your repository has already decided.

## Install

You need [`agentbundle`](../../guides/_shared/how-to/install-agentbundle.md) first. Install it from inside the repository, alongside Core:

```bash
cd path/to/your-repo
agentbundle install --pack governance-extras
```

## What your agent can do

- Draft an RFC for a cross-cutting change, with the case for it and the strongest case against it.
- Fold a research brief or design doc into the RFC as its factual grounding.
- Record an ADR: the decision, the alternatives rejected, and the consequences. It links back to the RFC that led to it.
- Look up ADRs and RFCs by lifecycle state, supersession lineage, and references.
- Export the decision record as an offline HTML view.
- Amend an accepted RFC with a short signed correction, without reopening it.

## Skills

- **`new-rfc`** — Proposes a change as a structured RFC and previews it before writing.
- **`new-adr`** — Records a decision as an ADR in the repository's decision-record location.
- **`navigate-decisions`** — Reads the ADR and RFC corpus: landscape, lineage, references, and detail.

## Works with

Works with Claude Code, Codex, Cursor, GitHub Copilot, Gemini CLI, Kiro IDE, and Kiro CLI. Install [Core](../core/README.md) first, because `new-adr` asks Core where your repository keeps decision records. [Desk Research](../desk-research/README.md) and [Architect](../architect/README.md) can feed an RFC. See [Record a decision](../../guides/governance-extras/how-to/new-adr.md) and [Write an RFC](../../guides/governance-extras/how-to/new-rfc.md).

## Questions

**Is an RFC a decision?** No. It is the case for one. The ADR records the decision once it is made.

**Can an ADR be edited later?** An ADR is not edited once merged. When a decision is reversed, the old ADR is superseded, not deleted.

**Where does it save an ADR?** In your repository's own decision-record location if it has one. `docs/adr/` is only the fallback.

**Does it write to project memory?** Only when Core's `project-knowledge` is installed, and only after the RFC is written or an ADR is accepted. Drafts and previews are never captured.

## Details

Scope: repo (default) · Version: 1.0.2 · Source: [packs/governance-extras](https://github.com/eugenelim/agent-ready-repo/tree/main/packs/governance-extras)
