# Spec: an adopter can inspect what a directly installed skill declares

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** none — authored after the spec is approved
- **Mode:** full (protected `packages/agentbundle/**`, a new CLI flag, and a consent-related surface)
- **Constrained by:** RFC-0098
- **Brief:** brief:direct-skill-lifecycle-delivery
- **Discovery:** none
- **Depends on:** none
- **Contract:** none
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Outcome

Someone who installed a skill straight from a repository can see the `allowed-tools`, `boundaries`, and credentialed status it declares, as installed, and can tell when the installed file no longer matches what they consented to.

## What Changes

- `agentbundle list-installed` gains a capabilities view for direct-skill rows, in table and JSON formats. Today `show` takes only a pack name and `list-installed` shows an installation record, and neither shows the three axes.
- The view reads the axes with the integrity-bound reader `_read_projected_capability_axes` in `packages/agentbundle/agentbundle/direct_install.py`, which parses the projected `SKILL.md` and returns unknown when the file's SHA-256 differs from the recorded one. No state-schema change.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| User promise | Applicable: a new flag | the CLI reference guide that documents `list-installed` | eugenelim | Flag documented | Guide updated |
| Release history | Applicable | agentbundle changelog and version bumps | eugenelim | One entry | Entry present |

## Agent Rules

### Always do

- Print publisher-controlled values through the existing bounded and escaped printer, as install does.
- Report `unknown` when the installed file fails its integrity check, never the parsed value.

### Ask first

- Any change to the state schema.

### Never do

- Never read outside the installed projection root.
- Never print an unescaped publisher string.

## Testing Strategy

- **TDD** with a fixture skill installed on temporary roots (no network): declared values, no values, and an edited file.
- Existing `list-installed` tests stay green.

## Acceptance Criteria

- [ ] For an installed direct skill declaring `allowed-tools`, two boundaries, and a credentialed value, the view prints all three axes.
- [ ] For a skill declaring no credentialed value, the view prints `undeclared` for that axis.
- [ ] For a skill whose installed `SKILL.md` was edited after install, the view prints `unknown` for all three axes.
- [ ] JSON output carries the three axes under stable keys for each direct-skill row.
- [ ] A publisher string containing a terminal escape sequence is printed escaped in both formats.
- [ ] Rows that are not direct skills print identically to today.
- [ ] `state.toml` and `.agentbundle-state.toml` are byte-identical before and after running the view.

## Follow-ons

- eugenelim: [`direct-skill-lifecycle-delivery`](../../product/briefs/direct-skill-lifecycle-delivery.md) slice D2 — capability difference rendering and the acceptance flag.

## Assumptions

- Technical: the surface. Default: a `--capabilities` flag on `list-installed`, because RFC-0098 D6 extends existing commands and `show` takes a pack positional (settled by: eugenelim). Owner decision 2026-11-05 on the upgrade flag set the precedent that a new flag needs no RFC amendment. If wrong: a `--skill` selector on `show`.
- Defaulted: Engine-Change-RFC: cite RFC-0098 (settled by: eugenelim).
