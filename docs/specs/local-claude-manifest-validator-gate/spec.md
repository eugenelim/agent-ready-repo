# Spec: local-claude-manifest-validator-gate

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

Mode: light (no risk trigger fired)

## Objective

`tools/validate-claude-plugin-manifests.py` exists and is used by
`.github/workflows/publish-claude-plugins.yml` as a CI gate before publishing.
It is not wired into the local `make build-check` chain, so a malformed
manifest can only be caught by the publish CI run — not during local development.

This spec wires `validate-claude-plugin-manifests.py` into the `build_check`
function in `tools/build_gate_chain.py` as the final script step, after
`lint-first-value-contract`. The script's `dist/claude-plugins/` dependency is
satisfied by the `cmd_build` step that runs earlier in the same chain.

The fix touches: `tools/build_gate_chain.py` (source) and
`tools/test_build_gate_chain.py` (test — count 9→10 and add path to expected
spawned list).

## Boundaries

### Always do

- Add `_script_step("validate-claude-plugin-manifests", "tools", "validate-claude-plugin-manifests.py")` as the last entry in the `steps` list inside `build_check`.
- Update `test_full_step_sequence_and_namespaces` in `tools/test_build_gate_chain.py`: change `["script"] * 9` to `["script"] * 10`, and append `"tools/validate-claude-plugin-manifests.py"` to the `spawned` expected list.
- Update the comment on line 122 from "nine spawned scripts" to "ten spawned scripts".

### Ask first

- Any change to the order of existing script steps.

### Never do

- Change the validator script itself (`tools/validate-claude-plugin-manifests.py`).
- Remove the validator from `publish-claude-plugins.yml`.
- Add build-check wiring to the Makefile (the chain already handles it).

## Testing Strategy

**TDD** — the existing `BuildCheckChainTest.test_full_step_sequence_and_namespaces`
in `tools/test_build_gate_chain.py` asserts both the step count and the ordered
list of spawned script paths. Updating those assertions and confirming the test
passes is the primary gate.

Secondary gate: `make build-check` exits 0 end-to-end, proving the validator
runs without error in a real chain execution.

## Acceptance Criteria

- [x] **AC1.** `tools/build_gate_chain.py` `build_check` function includes
  `_script_step("validate-claude-plugin-manifests", "tools", "validate-claude-plugin-manifests.py")`
  as the last entry in its `steps` list.
- [x] **AC2.** `tools/test_build_gate_chain.py` `test_full_step_sequence_and_namespaces`
  expects `["script"] * 10` (was 9) and includes `"tools/validate-claude-plugin-manifests.py"`
  as the last element of the `spawned` expected list.
- [x] **AC3.** `python tools/test_build_gate_chain.py` exits 0.
- [x] **AC4.** `make build-check` exits 0.

## Assumptions

- Technical: `cmd_build` runs before the script steps in `build_check`, so `dist/claude-plugins/` is guaranteed to exist when `validate-claude-plugin-manifests.py` runs (source: `build_gate_chain.py` step order verified by reading the file).
- Technical: `validate-claude-plugin-manifests.py` returns 1 if `dist/claude-plugins/` does not exist (line 37: `return 1`), so even if `cmd_build` somehow failed silently the validator will fail fast rather than producing a false pass.
- Technical: the `_script_step` wrapper spawns `[sys.executable, <path>]` with `check=False`, matching the existing Windows-clean pattern — no new platform concerns introduced.
- Technical: `validate-claude-plugin-manifests.py` hardcodes `REPO_ROOT/dist/claude-plugins` as its input directory (line 23). This is correct for the default `--output-dir=dist` but would produce a spurious failure or stale-dist false-pass if `build-check --output-dir=<other>` were used. The coupling is intentional (the validator is not parametrised); it is documented here so it is not mistaken for a general guarantee. The default is the only supported mode for this gate.
