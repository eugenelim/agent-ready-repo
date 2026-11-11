# Verification ledger: Architect output reaches shaping and specs

Execution observations recorded after plan approval. The approved spec and
plan stay pinned; these entries correct or ground them without amending.

## 2026-10-10 — Outcome overstates the absent-architect path

The spec's Outcome says teams without `architect` "see no change at all". That
is too strong. Without `architect` no architect offer, mention, note, or error
appears, which AC-0011 pins. But some changes apply either way:

- `frame-intent` parks system-shape questions in `Assumptions`.
- `frame-domain` reuses a current-architecture artifact first.
- `decompose-intent` checks slices against subsystem boundaries.
- `explore-options` and `diverge-solutions` note feasibility against current architecture.

Outcome is working material. The published changelog highlight uses the
corrected wording.

## 2026-10-10 — frame-intent probe prohibition scoped

`frame-intent`'s experience handoff said it "must not invoke, install, require,
or probe for any downstream pack", which reads as forbidding the roster check
AC-0007 requires. The sentence now scopes the prohibition to Experience Design.
