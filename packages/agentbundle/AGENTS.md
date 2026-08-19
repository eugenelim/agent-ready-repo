# AGENTS.md — `packages/agentbundle/`

Applies to `packages/agentbundle/`. Inherits the root `AGENTS.md`. Scope-specific deltas only.

## Package boundary

`agentbundle` is the catalogue engine and public CLI. Edit source inputs, not its
packaged scaffold or adapter projections. See `AGENTS.local.md` for release context.

## Package-specific traps

- Concurrent-install assertions may race on Windows; skip that focused test there.
- Normalize CRLF before byte comparisons of checked-out text.
- Use `Path.as_uri()` for `file://` URLs; string formatting makes broken Windows URLs.
- Prefer library APIs over subprocess wrappers; a justified Semgrep suppression belongs
  on the line the rule anchors.

## Essential commands

```bash
python3 -m pytest packages/agentbundle/tests/ -q
```

## Deeper pointers

The adapter contract and catalogue schemas own format details; package tests own
runtime and projection behavior.
