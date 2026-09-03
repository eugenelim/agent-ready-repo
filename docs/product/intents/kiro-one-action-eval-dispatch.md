# Kiro can start pack evaluation dispatch with one action

- **Status:** Draft
- **Level:** feature
- **Authority:** [spec/pack-activation-evals Phase 2](../../specs/pack-activation-evals/spec.md)

## Outcome

A Kiro user can invoke the pack-evals dispatch loop through one native action.

## Opportunity

The harness-agnostic documented procedure already works, and Claude Code validated it, but Kiro users must follow it by hand because no `.kiro/` command or hook starts the loop.

## What this absorbs

### kiro-native-in-harness-driver

- This is the optional ergonomic Phase 2 follow-on from `spec/pack-activation-evals` and RFC-0037 Errata E2.
- Add a catalogue-internal `.kiro/commands/run-pack-evals` command or hook that invokes the pack-evals dispatch loop.
- The procedure remains functional without this addition.
- `docs/specs/pack-activation-evals/plan.md:625` records: `T11 (Kiro-native ergonomic driver) deferred to workspace.toml [backlog].`
- Unblocks when: someone wants the one-click Kiro ergonomics.

## Assumptions

- None.

## Source

- Mode: repo-origin
- Locator: workspace.toml
- Revision: 581dd8b7aefba04f566e4ea9a3213da8c6afb55d
