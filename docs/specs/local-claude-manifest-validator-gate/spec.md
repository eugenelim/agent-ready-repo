# Spec: local-claude-manifest-validator-gate

- **Status:** Implementing <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim

Mode: light (no risk trigger fired)

## Objective

Wire the existing `tools/validate-claude-plugin-manifests.py` into `make build-check` / `python tools/build_gate_chain.py build-check` so a manifest contract failure is caught locally, matching what `publish-claude-plugins.yml` catches in CI.

## Acceptance Criteria

- [x] `tools/build_gate_chain.py build_check()` includes a `validate-claude-plugin-manifests` step immediately after the `build` step.
- [x] `build_gate_chain.py` module docstring and `build_check` docstring name the new step.
- [x] The validator step runs AFTER `build` so `dist/claude-plugins/` exists.

## Tasks

1. Add `_script_step("validate-claude-plugin-manifests", "tools", "validate-claude-plugin-manifests.py")` after the `build` step in `build_check()`.
2. Update `build_check()` docstring and module-level docstring to name the new step.

**Verification:** goal-based — `grep "validate-claude-plugin-manifests" tools/build_gate_chain.py` returns ≥1 hit inside the `steps` list.

**Declined:**
- Adding a dedicated self-test — the validator has its own tests; the gate-chain step is trivially verified by grep and the build-check run.
- Moving the validator before build — it requires `dist/` to exist.
