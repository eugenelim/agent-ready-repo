# Spec: work-loop script paths

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** integration

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

Every executable Python command taught by the work-loop skill runs from an
agent's repository-root working directory without script discovery. The skill
defines one installed-directory placeholder, applies it consistently to all
Python invocations, and gives the finish-time spec-status lint its complete
repository-root command. Generated projections carry the same instructions, and
the workspace-status drift anchor records the reconciled finish-checklist
contract.

## Boundaries

### Always do

- Edit the canonical work-loop source under `packs/core/.apm/skills/work-loop/`
  and regenerate projections through the repository build chain.
- Quote the resolved script path as one argument and keep repository inputs
  explicitly rooted with `--root .` where the invoked CLI supports it.
- Keep shell execution within the active permission profile: invoke only the
  installed work-loop scripts against the current repository, with no new tool
  authority, network source, or path outside the workspace.
- Reconcile the pinned finish-checklist window against
  `workspace_status_engine.py` before updating its expected hash.

### Ask first

- Change an executable script's CLI, state-machine behavior, or filesystem
  semantics.
- Broaden this delivery slice beyond the work-loop skill and its generated or
  contract-pinning artifacts.
- Re-pin any other prose-contract window.

### Never do

- Hand-edit `.agents/skills/work-loop/` or `.claude/skills/work-loop/`.
- Rewrite the remaining cross-pack bare-relative commands while the active
  `okf-authoring-projection` spec owns an overlapping skill surface.
- Claim a repaired command works from the repository root without executing a
  generated command there and observing exit 0.

## Testing Strategy

- **Goal-based check:** source searches prove that the work-loop has one concise
  `<skill-dir>` rule, no remaining bare-relative Python script invocation, and
  an explicit finish-time lint command with `--root .`.
- **Goal-based integration check:** the rebuilt installed projection is invoked
  verbatim from the repository root and exits 0, proving the documented path
  convention rather than merely matching text.
- **Goal-based regression gates:** the work-loop contract anchor, pack eval
  structure, projection parity, build checks, lint, typecheck, and tests cover
  the affected publishing and workspace-status boundaries.

## Acceptance Criteria

- [x] The canonical work-loop skill defines `<skill-dir>` tersely as the
  installer- or harness-supplied directory containing the active `SKILL.md`,
  and says resolved script paths are passed as one quoted argument.
- [x] All Python script invocations in the canonical work-loop skill use
  `python '<skill-dir>/scripts/<name>.py'`; none use bare-relative
  `python scripts/`.
- [x] The finish checklist says exactly how to run the metadata lint from the
  repository root:
  `python '<skill-dir>/scripts/lint-spec-status.py' --root .`.
- [x] The workspace-status finish-window hash matches the revised canonical
  prose after an explicit review establishes that the command-path correction
  changes no workspace-status engine semantics.
- [x] The skill grants no new capability: the active runtime permission profile
  remains authoritative, the substituted script path is one quoted argument,
  and the examples introduce no external content or out-of-workspace target.
- [x] A work-loop eval covers repository-root invocation without path discovery.
- [x] The active-spec index lists this delivery slice, the core pack release
  metadata and changelog describe the correction, and regenerated Codex and
  Claude projections are byte-identical to the canonical skill content.
- [x] From the repository root, the repaired generated
  `loop-engine.py --help` command exits 0.
- [x] The remaining 15 affected skills across seven packs stay unchanged in this
  slice and remain recorded as a cross-pack RFC candidate, including the active
  `compile-okf` ownership conflict.

## Assumptions

- Technical: `lint-spec-status.py` accepts `--root` (source:
  `packs/core/.apm/skills/work-loop/scripts/lint-spec-status.py` argument parser).
- Technical: `packs/` is the source of truth and installed skill directories
  are generated projections (source:
  `packages/agentbundle/agentbundle/build/self_host.py`).
- Process: the finish-checklist hash requires comparison with
  `workspace_status_engine.py` before its constant changes (source:
  `tools/test_workspace_status.py` contract-anchor comment).
- Product: this slice includes the reviewed work-loop finish-checklist fix and
  hash reconciliation but excludes the other packs (source: user confirmation
  2026-08-21).
- Process: `okf-authoring-projection` actively owns
  `packs/catalogue-curation/.apm/skills/compile-okf/**` (source:
  `docs/specs/okf-authoring-projection/plan.md`).
