# linear pack

Linear integration for the agent-ready-repo catalogue. Turns a Linear Issue
or Project into a shippable product brief and keeps it in sync as the Issue
evolves.

## Skills

| Skill | What it does |
| --- | --- |
| `linear` | Credentialed GraphQL primitive — all Linear API reads live here. Exposes `check`, `get-issue`, and `get-project` subcommands. The agent never sees the API key. |
| `linear-brief-intake` | First-time intake: pulls an Issue or Project via `linear`, maps it onto a product brief, writes to `docs/product/briefs/<slug>.md`, and hands off to `receive-brief`. |
| `linear-brief-sync` | Delta catch-up: re-fetches the Issue, diffs Linear-sourced fields against the current brief, presents section-level before/after for PE approval, and writes only what PE approves. Refuses when brief `Status: Executing`. |

## Install

```bash
# <catalogue> is your catalogue URI: a local clone path or a git+https://… URL.
agentbundle install --pack linear <catalogue>
```

Requires the `credential-brokers` pack for API key resolution. After install,
run `credential-setup` to store your Linear Personal API Key under namespace
`linear`.

## Guides

→ [When to use linear-brief-intake vs linear-brief-sync](../../docs/guides/linear/how-to/linear-brief-intake-and-sync.md)
