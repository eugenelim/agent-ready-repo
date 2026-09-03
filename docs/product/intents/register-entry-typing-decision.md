# Register entry typing decision

- **Status:** Draft
- **Level:** feature
- **Authority:** [spec/workspace-backlog-reconciliation AC7](../../specs/workspace-backlog-reconciliation/spec.md)

## Outcome

The workspace register uses an explicitly chosen, engine-consistent representation for its reanchor entries without fabricating canonical artifact paths.

## Opportunity

The five reanchor entries have inert `type = "spec"` metadata and classify as `unsupported_legacy`, while build-room backlog items have no supported legacy representation.

## What this absorbs

### reanchor-entry-typing-decision

Decide the routing surfaced on 2026-08-15 by auditing every `[backlog].open` entry against the engine classifier. The five reanchor entries use `type = "spec"`, but `packages/agentbundle/agentbundle/_data/workspace_status_engine.py:4369` defines `_SHAPING_TYPES` as `frozenset({"shape", "research", "strategy", "signal", "design"})`; `spec` classifies as `unsupported_legacy`, exactly like an untyped build entry. The key is therefore human documentation only.

Choose one of three recorded options: (a) retain `type = "spec"` as honest human documentation, permanently `unsupported_legacy` and inert; (b) remove the key so entries become ordinary build entries and classify identically, without implying an unsupported vocabulary; or (c) add `spec` to `_SHAPING_TYPES`, an ENGINE change that routes them into the shape room and before `check_shaping_guard`, contrary to the reanchor comment. Option (c) requires its own RFC. The wider constraint is that a build-room `backlog.open` item has no supported legacy form: `_accepted_legacy_entry` requires a `_SHAPING_TYPES` member for its `backlog.open` branch, and the only other supported shape is a canonical target with a real artifact `path`; 136 entries cannot migrate out of `unsupported_legacy` without an engine change or fabricated paths. Do not fabricate paths. Unblocks when picked up; it has no dependency.

## Assumptions

- None.

## Source

- Mode: repo-origin
- Locator: workspace.toml
- Revision: 581dd8b7aefba04f566e4ea9a3213da8c6afb55d
