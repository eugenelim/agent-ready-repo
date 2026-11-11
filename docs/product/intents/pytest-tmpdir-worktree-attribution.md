# Attribute pytest temporary trees to their worktrees

- **Slug:** `pytest-tmpdir-worktree-attribution`
- **Status:** Withdrawn
- **Level:** feature
- **Owner:** eugenelim
- **Governed by:** [RFC-0097 worktree attribution](../../rfc/0097-agent-skill-engineering.md)

## Disposition — withdrawn 2026-11-05, decided: not worth doing now

no incident is recorded for dead-worktree pytest temporary trees, no `TMPDIR` or `basetemp` setting exists in `pyproject.toml`, `Makefile` or any `conftest.py`, and the only trace is an RFC-0097 backlog row that says "keep open". Reopen with a measured case of temporary trees that could not be reclaimed.

## Outcome

Pytest temporary trees can be attributed to their worktree and reclaimed when that worktree is dead, while single-checkout behavior remains unchanged.

## Opportunity

Pytest has no per-worktree `TMPDIR` attribution, so a dead worktree's temporary trees cannot be distinguished for safe reclamation.

## What this absorbs

### pytest-tmpdir-worktree-attribution

Use `TMPDIR` to give pytest temporary trees per-worktree attribution. Detect workspace versus single-checkout users from Git topology, leaving single-checkout behavior unchanged. The `pytest-tmpdir-worktree-attribution` row of the backlog table in `docs/rfc/0097-agent-skill-engineering.md` says: “Keep open; make it an application case for worktree attribution.” No per-worktree pytest `TMPDIR` implementation was found.

## Assumptions

- Git topology can distinguish a workspace worktree from a single checkout without changing the latter's behavior.

## Source

- Mode: repo-origin
- Locator: workspace.toml
- Revision: 581dd8b7aefba04f566e4ea9a3213da8c6afb55d
