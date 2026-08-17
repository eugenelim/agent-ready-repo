# GitHub

Start repository work from a GitHub Issue or Milestone without writing back to
GitHub.

Try:

```text
Intake GitHub issue 123 as repository work. Start read-only.
```

The pack uses approved `gh` reads against a trusted configured host and
repository. It emits a bounded `normalized-intake.v1` record and delegates to
`work-intake`. Content decides the artifact and processor; an Issue is not
automatically a spec, and a Milestone is not automatically a brief.

The intake path cannot comment, label, close, create, or edit GitHub work.
Repository materialization belongs to `work-intake` after validation and any
required human choice.

## Install

```bash
agentbundle install --pack github --scope user <catalogue>
```

Install the [`gh` CLI](https://cli.github.com). Authenticate it for repositories
that require access. Host selection must come from trusted repository or
administrator configuration, never Issue or Milestone text.

→ [Intake GitHub work](../../guides/github/how-to/intake-a-github-milestone-as-a-brief.md)
