# Catalogue Curation

Your agent can grow and maintain a skill catalogue for you: bring in outside skills, survey other repositories, propose new packs, and compile pack knowledge.

## Install

You need [`agentbundle`](../../guides/_shared/how-to/install-agentbundle.md) first. This pack is for catalogue maintainers. Install it from inside your catalogue repository:

```bash
cd path/to/your-catalogue
agentbundle install --pack catalogue-curation
```

## What your agent can do

- Bring one outside skill, subagent, or hook into your catalogue from a local path or URL, reshaped to your catalogue's conventions or rejected with a reason.
- Survey a whole outside repository and write a reviewable RFC with a verdict for each candidate.
- Check whether a new pack is additive, scaffold its shell, and write an RFC for human review.
- Compile a pack's declared knowledge bundles into portable reference skills, and check that the committed output is current.
- Pick up a survey where it stopped, across sessions and worktrees.

## Skills

- **`assimilate-primitive`** — Brings in one outside skill, subagent, hook, or command, or a small bundle, and shows a preview before it lands.
- **`assimilate-repo`** — Surveys a whole repository or catalogue and writes per-candidate verdicts to a resumable ledger.
- **`propose-catalogue-pack`** — Tests whether a new pack is additive, scaffolds it, and writes the RFC, or rejects the idea.
- **`compile-okf`** — Compiles declared OKF knowledge bundles into router and procedure skills, or checks they are current.

## Works with

Repo scope only, with Claude Code. It stands alone and needs no other pack. Pair it with [Agent Skill Engineering](../agent-skill-engineering/README.md) to write skills, and [Governance Extras](../governance-extras/README.md) for the RFCs it produces. Guides: [Import and curate skills](../../guides/catalogue-curation/how-to/survey-a-repo.md) and [Author and compile an OKF bundle](../../guides/catalogue-curation/how-to/author-an-okf-bundle.md).

## Questions

**Does it publish anything?** No. Every change is local, and a preview comes first where the workflow needs one.

**Can it change the install engine or the credential brokers?** No. A path gate blocks those trees unless a human writes an RFC for it.

**Does ingested code skip your checks?** No. It runs the repository's own lints and scans before it lands. Known anti-patterns are reshaped or rejected.

**Is it for adopters?** No. It is for the people who decide what lands in a catalogue. To start a catalogue, run `agentbundle catalogue init --preset self-hosted`.

## Details

Scope: repo (default) · Version: 0.4.7 · Source: [packs/catalogue-curation](https://github.com/eugenelim/agent-ready-repo/tree/main/packs/catalogue-curation)
