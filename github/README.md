# GitHub

Start repository work from GitHub, then review source changes and confirm
narrow coordination write-back through the approved `gh` boundary.

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
required human choice. A later refresh can add a trace link, pull-request link,
display-status label, comment, or closure only after a separate fresh
confirmation for that exact mutation. Requirement and Issue-body rewrites are
not supported.

## Install

```bash
agentbundle install --pack github --scope user <catalogue>
```

Install the [`gh` CLI](https://cli.github.com). Authenticate it for repositories
that require access. Host selection must come from trusted repository or
administrator configuration, never Issue or Milestone text.

→ [Intake GitHub work](../../guides/github/how-to/intake-a-github-milestone-as-a-brief.md)
→ [Refresh tracked work safely](../../guides/_shared/how-to/use-work-intake.md)
