# AGENTS.md — packages/agentbundle

This package is the `agentbundle` CLI and engine.

## Engine-change guard

Any PR that modifies files under `packages/agentbundle/` (except
`agentbundle/build/recipes/**` and `tests/**`) is treated as an
engine-behaviour change by `tools/lint-catalogue-curation-guard.py`
(RFC-0059 D6). That check will hard-fail CI unless at least one commit
message in the branch contains the trailer:

```
Engine-Change-RFC: <rfc-or-ini-id>
```

Add a commit with that trailer before pushing. An empty commit is fine:

```bash
git commit --allow-empty -m "chore: exempt engine-change guard

Engine-Change-RFC: <rfc-or-ini-id>"
```

The trailer must match the RFC or initiative driving the change.
