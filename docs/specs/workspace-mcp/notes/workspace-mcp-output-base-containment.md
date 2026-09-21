# Workspace-MCP output-base containment

AC10's slug-containment guard checks a formatted `output_pattern` against the
repository root. AC10 states that base and calls tightening it to the item
type's own output base a later hardening item, so this note owns the decision
that tightening needs.

## What the guard does now

`workspace_mcp.py` verifies the formatted path stays under `repo_root`:

```python
static_base = repo_root
assert_under(static_base, resolved)
```

An item failing the check is dropped from the payload with a warning.

## Why that is sufficient today

The slug regex `^[a-zA-Z0-9._-]+$` rejects `..` and any single-segment escape
before formatting, so a crafted slug cannot leave the repository root. The
guard's stated job — prove a slug cannot escape its base — is discharged by the
repository root as the base. Tightening would narrow the blast radius of a
future regex change, not close a reachable escape today.

## The decision this needs

Tightening the base is not a local edit, because the base a `design` or
`research` item should be held to is now the **configured** base, not the
manifest constant. Three questions have to be settled together:

- Does the guard check the convention base, the configured base, or both?
- A user-scope `output_dir` is required to be absolute, so it can resolve
  outside the repository. Such a base cannot satisfy any
  `assert_under(repo_root, …)` check. Does the item then drop from the payload,
  or does the guard scope itself to bases inside the repository?
- `_GitTools.git_commit` performs its own containment through
  `Path.is_relative_to` when it intersects candidate paths against
  `git status` output. Tightening one surface and not the other leaves the two
  on different rules, which is the defect class the configured-path repair
  closed.

The first question is a contract choice, so it is spec work before it is code
work.

## Scope

Pre-existing, and not introduced by the configured-path repair. That change
left the guard deliberately on the un-overridden pattern; the reasoning is
recorded beside the guard in `workspace_mcp.py`.

`docs/specs/workspace-mcp/spec.md` is Shipped and frozen, and AC10 is accepted
and ticked. Recording the hardening does not reopen that criterion, and this
note carries no deferral marker against it.

A separate follow-on covers the published pattern's character screening; the
two share a file and nothing else.
