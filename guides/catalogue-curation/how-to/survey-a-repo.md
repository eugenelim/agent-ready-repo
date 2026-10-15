---
title: "Import and curate skills"
summary: "Adopt good skills from other repositories without adopting their risks."
pack: catalogue-curation
kind: how-to
---

# Import and curate skills

Adopt good skills from other repositories without adopting their risks, one skill at a time or a whole repository at once. Your agent does the work, and you review what it fetched and approve what lands.

## Import one skill

Point your agent at the skill's source:

```text
Assimilate the skill at https://github.com/some-org/their-repo (the summarize-thread skill) into our catalogue.
```

The `assimilate-primitive` skill fetches it over `https` or `git` only, refusing `file:` URLs and private addresses before it reads anything.

## Review and land it

The agent shows you the fetched body exactly as it arrived, so read it as untrusted instructions. It then shapes the skill to your conventions, and after you approve it writes the skill into the destination pack. Rebuild and confirm the pack lists the skill:

```bash
make build-self && agentbundle show <pack>
```

[Your first assimilation](../tutorials/first-assimilation.md) walks through every guardrail and the full definition of done.

## Survey a whole repository

To judge an entire outside repository or catalogue instead of one skill, ask for a survey:

```text
Survey https://github.com/some-org/their-catalogue for skills we can adopt.
```

The `assimilate-repo` skill gives each candidate a verdict of assimilate, reject, or needs-new-pack, and writes a reviewable RFC. A re-run after an interruption, or after the source changes, skips candidates it already decided.

Next, read [the ledger and the engine guard](../reference/ledger-and-guard.md) to see how progress is stored and protected.
