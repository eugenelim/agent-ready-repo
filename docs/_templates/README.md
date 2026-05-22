# Document templates

Skeletons for the four document kinds the bundle ships. Each is a
starting point — copy, rename, fill in.

- [`adr.md`](adr.md) — Architecture Decision Records (frozen history)
- [`rfc.md`](rfc.md) — Request For Comments (in-flight proposals)
- [`spec.md`](spec.md) + [`plan.md`](plan.md) — feature spec and plan
- [`state.json`](state.json) — work-loop state schema (gitignored at
  runtime; copied to `docs/specs/<feature>/state.json` per spec)

The naming, lifecycle, and review rules for each kind live in
[`../CONVENTIONS.md`](../CONVENTIONS.md).
