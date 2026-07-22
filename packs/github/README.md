# github

GitHub integration for the agent-ready-repo catalogue. The pack ships one skill:

| Skill | What it does |
| --- | --- |
| `github-brief-intake` | Pull a GitHub Milestone and its issues, map them to a Shape B product brief, write it to `docs/product/briefs/<slug>.md`, and hand off to `receive-brief`. |

## Install

`github` is **user-scope by default** (your GitHub access is yours, not a project's).

```
agentbundle install --pack github <catalogue>
```

## Prerequisites

The skill uses the [`gh` CLI](https://cli.github.com) — install it and run
`gh auth login` to authenticate before using `github-brief-intake` against a
private repo. Public repos are accessible without authentication, but the skill
will note the unauthenticated posture in the produced brief.

## Usage

Ask your agent, for example:

- "Turn our Q3 milestone into specs."
- "Intake the 'v2 launch' milestone from eugenelim/my-repo as a product brief."
- "Pull GitHub milestone #4 and create a brief."

---

→ **Go deeper:** the [`github` guides](https://github.com/eugenelim/agent-ready-repo/tree/main/docs/guides/github/).
