# Repository Governance

Your agent can write the RFC for a proposed change, record the ADR for a decision, and look up what your repository has already decided.

## Install

You need [`agentbundle`](../../guides/_shared/how-to/install-agentbundle.md) first. Install it from inside the repository, on its own or alongside Core:

```bash
cd path/to/your-repo
agentbundle install --pack repo-governance
```

## What your agent can do

- Draft an RFC for a cross-cutting change, with the case for it and the strongest case against it.
- Fold a research brief or design doc into the RFC as its factual grounding.
- Record an ADR: the decision, the alternatives rejected, and the consequences. It links back to the RFC that led to it.
- Look up ADRs and RFCs by lifecycle state, supersession lineage, and references.
- Export the decision record as an offline HTML view.
- Set up governance: draft a `GOVERNANCE.md`, a `CODEOWNERS` file or a charter link from the handles you supply, and write it only after you confirm the exact preview.
- Amend an accepted RFC with a short signed correction, without reopening it.

## Skills

- **`new-rfc`** — Proposes a change as a structured RFC and previews it before writing. Its `governance` mode drafts a `GOVERNANCE.md`, a `CODEOWNERS` file or a charter link from handles you supply, and writes only after you confirm the exact preview. See [Set up governance](../../guides/repo-governance/how-to/set-up-governance.md).
- **`new-adr`** — Records a decision as an ADR in the repository's decision-record location.
- **`navigate-decisions`** — Reads the ADR and RFC corpus: landscape, lineage, references, and detail. Its read-only `route` mode says which record a decision needs, whether it is a one-way door, and whom to consult; it writes nothing. Its read-only `health` mode lists due or stale decisions, superseded ADRs still cited, and missing confirmation checks; it runs none of the checks and writes nothing.

## Works with

Works with Claude Code, Codex, Cursor, GitHub Copilot, Gemini CLI, Kiro IDE, and Kiro CLI. Core is optional: `new-adr` picks the decision-record folder itself, and [Core](../core/README.md) adds work-loop risk triggers, the follow-on queue and reviewer agents to `new-rfc` when it is installed. [Desk Research](../desk-research/README.md) and [Architect](../architect/README.md) can feed an RFC. See [Record a decision](../../guides/repo-governance/how-to/new-adr.md) and [Write an RFC](../../guides/repo-governance/how-to/new-rfc.md).

## Migrating from governance-extras

This pack was named `governance-extras` before 2.0.0, and `iac-terraform` 0.2.0 requires it. To move over, run these steps from the repository that has the old pack installed:

```text
1. agentbundle uninstall --pack governance-extras --scope repo
2. agentbundle install --pack repo-governance --scope repo --adapter claude-code git+https://github.com/eugenelim/agent-ready-repo
3. agentbundle upgrade --pack iac-terraform --scope repo git+https://github.com/eugenelim/agent-ready-repo
```

Replace `claude-code` with the adapter your `governance-extras` is installed for.

CLIs older than 0.57.0 print plain "not found" for the old name, so use these steps with them. From 0.57.0, `install` and `upgrade` print the same steps.

## Questions

**Is an RFC a decision?** No. It is the case for one. The ADR records the decision once it is made.

**Can an ADR be edited later?** An ADR is not edited once merged. When a decision is reversed, the old ADR is superseded, not deleted.

**Where does it save an ADR?** In your repository's own decision-record location if it has one. `docs/adr/` is only the fallback.

**Does it write to project memory?** Only when Core's `project-knowledge` is installed, and only after the RFC is written or an ADR is accepted. Drafts and previews are never captured.

## Details

Scope: repo (default) · Version: 2.3.0 · Source: [packs/repo-governance](https://github.com/eugenelim/agent-ready-repo/tree/main/packs/repo-governance)
