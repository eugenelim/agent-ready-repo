# Spec: every installed-state write goes through the state lock

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** none — authored after the spec is approved
- **Mode:** full (protected `packages/agentbundle/**`, and a data-loss defect on persisted state)
- **Constrained by:** none
- **Brief:** brief:agentbundle-install-integrity-delivery
- **Discovery:** none
- **Depends on:** none
- **Contract:** none
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Outcome

Someone who runs install, uninstall, upgrade, or init-state while another agentbundle command runs against the same repository does not lose an installed-pack row. Single-command behaviour does not change.

## What Changes

- `commands/uninstall.py`: the state removal at the `del state.packs[...]` step serialises through `statelock.persist_state_locked` with a fresh-state mutate closure.
- `commands/upgrade.py`: `_apply_single_row` does the same.
- `commands/install.py`: the legacy dist-tree detection path that writes state with `write_text(dump_state(repo_state))` does the same.
- `commands/init_state.py`: the final `dump_state` plus `write_jailed` does the same.

All paths are under `packages/agentbundle/agentbundle/`. Four call sites write state without the lock today; `persist_state_locked` is used only by `commands/install.py` and `direct_install.py` (checked 2026-11-05).

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Release history | Applicable: engine fix | agentbundle changelog, version bumps in `pyproject.toml` and `version.py` | eugenelim | One entry | Entry and matching versions present |
| User promise | Not applicable: no CLI or output change | none | none | none | none |

## Agent Rules

### Always do

- Re-read state inside the lock before mutating, so a concurrent row is merged and not overwritten.
- Keep exit codes and printed messages unchanged on a single-process run.

### Ask first

- Any change to the state file format or schema version.

### Never do

- Never hold the lock across a network call or a long file copy.
- Never catch and hide a lock timeout; it surfaces as the existing refusal.

## Testing Strategy

- **TDD** with a multi-process test: two processes run commands against one temporary root, and the test checks every row survives. The test fails on the current tree by losing a row.
- **Goal-based** for the closed set: a test greps the package for `dump_state(` call sites.
- Existing single-process suites must stay green unchanged.

## Acceptance Criteria

- [ ] Every `dump_state(` call site in `packages/agentbundle/agentbundle/` lies in `statelock.py` or `config.py`; a test over the source tree enforces this.
- [ ] Two concurrent uninstalls of different packs on one root leave both packs absent and every other row present.
- [ ] An uninstall running concurrently with an install leaves the installed pack's row present.
- [ ] An upgrade running concurrently with an install of another pack leaves both rows present.
- [ ] An `init-state` running concurrently with an install leaves both rows present.
- [ ] A state file in a legacy schema still produces the existing refusal from each of the four commands.
- [ ] The existing install, uninstall, upgrade, and init-state test suites pass unmodified.

## Follow-ons

- eugenelim: [`agentbundle-install-integrity-delivery`](../../product/briefs/agentbundle-install-integrity-delivery.md) slices I1 and I3 — the install-path lint gate and catalogue identity.

## Assumptions

- Defaulted: Engine-Change-RFC: the trailer cites RFC-0076, which earlier commits to `statelock.py` cite (settled by: eugenelim). If wrong: it names the RFC that governs each command.
- Technical: whether upgrade can mutate one row under the lock without holding it across its file work. Default: yes, because `_apply_single_row` computes the row before serialising (settled by: the plan's read of `commands/upgrade.py`).
