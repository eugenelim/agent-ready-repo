# Spec: Claude installs get the workspace-MCP permissions without clobbering the user's

- **Status:** Draft
- **Owner:** eugenelim
- **Plan:** none — authored after approval
- **Constrained by:** RFC-0078
- **Brief:** brief:workspace-mcp-production-readiness-delivery
- **Discovery:** capability:workspace-mcp-production-readiness
- **Contract:** none
- **Shape:** integration

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Outcome`, `What Changes`, `Durable Outputs`, `Follow-ons` and
> `Assumptions` are working material: they orient a reader and an author corrects them in place
> as the work teaches, without an amendment and without a review round.

## Outcome

An operator installing the core pack into a Claude repository gets the six workspace-MCP tools allowed for headless runs, with every permission and setting they already had left in place. Installing twice changes nothing.

## What Changes

- `agentbundle install core` adds the six `mcp__workspace-mcp__*` ids to `permissions.allow` in `.claude/settings.json` — the Claude adapter projection under `packages/agentbundle/`.
- The adapter contract gains one additive projection mode that appends unique entries to an array under a managed key, because the spike below shows `merge-json` cannot — `packages/agentbundle/agentbundle/_data/adapter.toml` and `adapter.schema.json`, with their `contracts/` copies and the catalogue-specification pin.
- The four skipped stubs in `test_adapter_permissions_projection.py` become passing tests — that file.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Interface compatibility | Applicable — the new mode extends a published adapter contract | `packages/agentbundle/agentbundle/_data/adapter.toml`, `adapter.schema.json`, their `contracts/` copies, and the `adapter_contract` and hash pins in `contracts/catalogue-spec.toml` | eugenelim | Contract minor version bumped (currently 0.18) and named in the changelog | `close-work` verifies the version rule in `packages/AGENTS.md` |
| User promise | Applicable — adopters see new entries in their settings file | the install guide section for the core pack | eugenelim | The guide says what is added and how to remove it | `close-work` reads the guide |
| Release history | Applicable | the repository changelog and `packages/agentbundle` `version.py` and `pyproject.toml` | eugenelim | Both version files bumped | Versions match |
| Current product truth | Applicable | `docs/product/briefs/workspace-mcp-production-readiness-delivery.md` Spec map | `lint-brief-coverage` | Roll-up resolves this spec through its `Brief:` link | No status hand-written into the brief |
| Current architecture | Applicable — the shipped `workspace-mcp` spec carries deferred AC17 for this behavior | `docs/specs/workspace-mcp/spec.md` AC17 | eugenelim | A note pointing at this spec, as the spec's own amendment route allows | The deferral points at its delivery |

## Agent Rules

### Always do

- Add exactly the six ids named in AC17 of `docs/specs/workspace-mcp/spec.md` and no others.
- Write the settings file only through the confined filesystem helpers in `agentbundle.catalogue_tooling.file_safety`.
- Land with an `Engine-Change-RFC: RFC-0078` trailer and bump both `version.py` and `pyproject.toml`.

### Ask first

- Any widening of the id list, or an id with a wildcard.
- Any contract change beyond adding the one mode value and bumping the minor version, such as changing an existing mode's meaning. That stops this spec and needs a follow-on RFC.

### Never do

- Never remove, reorder or rewrite an existing `permissions.allow` entry or any other settings key.
- Never project permissions for an adapter other than Claude.
- Never grant the entries on a path where AC14's `output_pattern` scoping and push branch check from `docs/specs/workspace-mcp/spec.md` are not in force.

## Testing Strategy

- **TDD:** the four stubs in `test_adapter_permissions_projection.py` become tests over a temporary repository: clean install, pre-populated entries, second install, and an unrelated settings key. Each parses the JSON and asserts on the parsed value, not on a grep count.
- **Goal-based check:** the adapter schema test and the contract-parity checks pass after the contract change.
- **Security review:** a spec-stage and an implementation-stage `security-reviewer` pass, because the change grants tool permissions.

## Acceptance Criteria

- [ ] On a clean Claude repository, `agentbundle install core` leaves `.claude/settings.json` `permissions.allow` holding exactly the six ids from AC17, as parsed JSON.
- [ ] A `permissions.allow` entry present before the install is still present, in its original position, after it.
- [ ] A second `agentbundle install core` leaves `permissions.allow` byte-identical to the first.
- [ ] A settings key unrelated to `permissions.allow` is unchanged by the install.
- [ ] The four stubs in `test_adapter_permissions_projection.py` run and pass with no `skip`.
- [ ] An install for any non-Claude adapter writes no `permissions` key.

## Follow-ons

- eugenelim: `docs/product/briefs/workspace-mcp-production-readiness-delivery.md` slices 2 to 5 — the remaining stub files and the brief-exposure test.

## Spike result

2026-11-05, run in a disposable git worktree under `.context/`, removed afterwards; nothing was committed or left in the main tree.

- **Method.** Called `project_merge_json` (`packages/agentbundle/agentbundle/build/projections/merge_json.py`) on a fixture `.claude/settings.json` holding a user `permissions.allow` entry (`Bash(ls:*)`), a `permissions.deny` entry and a `model` key, with a source TOML carrying two of the six ids and `managed-key = "permissions"`. Validated variants of the real `adapter.toml` against `adapter.schema.json` with `jsonschema`.
- **Observed.** `merge-json` replaces the whole `allow` array: the user's `Bash(ls:*)` entry is gone after the merge. It keeps `deny` and `model`, and a second run is identical. The schema accepts a `merge-json` rule with `managed-key = "permissions"`, so the contract admits the rule but the semantics are wrong. `user-merge-json` and `merge-into-agent-json` append to arrays but only for `hooks` event arrays with synthesized ids. The schema rejects an unknown mode, since its `mode` enum is closed.
- **Precedent.** Earlier commits added modes to that enum without a breaking change (`codex-agent-toml`, `copilot-hooks-json`, `gemini-command-toml`; commit 63f36552d added Claude plugin hook handling), each a feature change to the schema and `adapter.toml`.
- **Verdict.** Needs a non-breaking addition. No existing mode expresses additive append to `permissions.allow`; one new mode value plus a minor contract version bump does, and no follow-on RFC is needed. A change to an existing mode's meaning would be breaking and is excluded by Agent Rules.

## Assumptions

- Defaulted: Technical: the new mode reads its entries from a TOML file in the pack's `hook-wiring` source directory, as `merge-json` does, and the plan fixes the exact shape — default: that source; if wrong: the plan names another source directory (settled by: the plan author).
- Defaulted: Product: uninstall removes only the six ids this install added — default: that behavior; if wrong: uninstall leaves them and the guide says so (settled by: eugenelim).
- Defaulted: Technical: the adapter contract `version` takes a minor bump for the added mode — default: minor, matching earlier mode additions; if wrong: the bump level changes (settled by: eugenelim).
