# Architecture

How the code is *currently* organized. Not why (that's in
[`../adr/`](../adr/)) and not what we want (that's in
[`../rfc/`](../rfc/)) — **what is**.

- [`overview.md`](overview.md) — the map of the monorepo. What's in
  `apps/`, `packages/`, `tools/`, `packs/`, and how they relate.
  Read this first.
- `<subsystem>.md` — one file per non-trivial subsystem (add as the repo
  grows). Each describes the structure, the entry points, and links to
  the ADRs that explain why.

Architecture docs are the *rolled-up snapshot* — the answer to "what
does this codebase look like today" without replaying ADR history.
Lifecycle: living. Update whenever the layout or major dependencies
change.
