# Spec: portfolio-first-run-pilot-governance-extras

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Mode:** light (no risk trigger fired)
- **Owner:** eugenelim
- **Constrained by:** RFC-0064 Amendment #4 — preview-confirm repository write archetype pilot; spec/portfolio-pack-first-value-contract (Shipped — defines the Level B contract governance-extras already satisfies)

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

Governance-extras is the "preview-confirm repository write" pilot archetype: it writes a shared governance record (an ADR or RFC) to the user's repo and must show the user what will be written, where, and why before any file is created. The first-value contract fields are already in place; the `tutorial` field is absent until this spec ships the tutorial file that proves the path works.

This spec authors `docs/guides/governance-extras/tutorials/governance-extras-first-session.md`: a step-by-step walkthrough that takes a user from install to a committed ADR, with explicit preview-confirm coverage at the write step. After this spec ships, the `tutorial` field is added to `packs/governance-extras/pack.toml`, completing the pilot contract.

## Acceptance Criteria

- [x] AC1 — Tutorial file at `docs/guides/governance-extras/tutorials/governance-extras-first-session.md` exists and covers all five preview-confirm-write elements in named steps: (1) what the skill will write (ADR content preview), (2) where it will land (target path shown before write), (3) why (the decision being recorded), (4) how to confirm, (5) how to stop or revise before confirmation.

- [x] AC2 — `packs/governance-extras/pack.toml` has `tutorial = "docs/guides/governance-extras/tutorials/governance-extras-first-session.md"` in `[pack.first-value]`; pack version bumped from `0.8.1` to `0.8.2`.

- [x] AC3 — `make build-check` exits 0 after changes (`lint-first-value-contract.py` validates the tutorial path resolves to an existing `.md` file); `make build-self FORCE=1` exits 0.

- [x] AC4 — Tutorial's starter prompt matches `starter-prompt` in pack.toml byte-for-byte (no consumer drift); tutorial uses the exact install command `agentbundle install governance-extras --scope repo`.

- [x] AC5 — Tutorial includes a recovery section covering: verification failure after install, wrong path shown in preview (how to cancel), and post-confirm undo (the file is a plain markdown file; delete it before committing if you change your mind).

- [x] AC6 — An evaluator who completes the tutorial can explain without external help: what will be written, where, why, how to stop before the file is created, and how to revise the draft before confirmation. The tutorial is cold-start-sufficient: no undocumented terminal or repo knowledge required.

- [x] AC7 — `docs/product/changelog.md` `[Unreleased]` has one entry for this pilot (governance-extras 0.8.2, tutorial added). `workspace.toml` moves `spec/portfolio-first-run-pilot-governance-extras` from `queue` to `shipped`.

## Task list

1. Write `docs/guides/governance-extras/tutorials/governance-extras-first-session.md`
2. Edit `packs/governance-extras/pack.toml`: add `tutorial` field, bump version to `0.8.2`
3. Run `make build-self FORCE=1` (regenerates plugin.json, marketplace.json)
4. Run `make build-check`; fix any failures
5. Add changelog entry; update workspace.toml

## Assumptions

1. `packs/governance-extras/pack.toml` already has a fully-populated `[pack.first-value]` section (Level A + Level B + `writes-to-repo = true` + `safety-gate`) — confirmed from the shipped portfolio-pack-first-value-contract spec.
2. No `tutorials/` directory exists yet under `docs/guides/governance-extras/` — confirmed by inspection; creating it is in scope.
3. The tutorial's starter prompt can be pasted into any repo that has governance-extras installed at repo scope, regardless of whether `docs/adr/` already exists (the `new-adr` skill creates it on first use).
4. `make build-self FORCE=1` regenerates `plugin.json` from `pack.toml`; no manual `plugin.json` edit is needed (confirmed from portfolio-pack-first-value-contract plan).
