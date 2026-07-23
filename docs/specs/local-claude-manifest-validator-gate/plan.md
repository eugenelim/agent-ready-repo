# Plan: local-claude-manifest-validator-gate

- **Spec:** [`spec.md`](spec.md)
- **Status:** Draft

## Constraints

- `tools/build_gate_chain.py` `build_check` uses `_script_step(label, *path_parts)` — consistent with all existing script steps.
- The test file `tools/test_build_gate_chain.py` asserts exact step count and exact ordered list of spawned paths — both must be updated atomically.

## Risks

- `make build-check` invokes the real `validate-claude-plugin-manifests.py` which requires `dist/claude-plugins/` to exist. The `cmd_build` step that precedes it creates this directory, so no risk of missing dist. But if an existing pack plugin.json has a schema error that was previously undetected, `build-check` will start failing. Mitigate: run `python tools/validate-claude-plugin-manifests.py` manually first to confirm it passes before adding to the chain.

## Tasks

### Task 1 — Add script step to build_gate_chain.py

**Mode:** Goal-based check
**Depends on:** none

In `tools/build_gate_chain.py`, in `build_check`, after:
```python
        _script_step("lint-first-value-contract", "tools", "lint-first-value-contract.py"),
```
Add:
```python
        _script_step("validate-claude-plugin-manifests", "tools", "validate-claude-plugin-manifests.py"),
```

**Done when:** The function's `steps` list ends with `validate-claude-plugin-manifests`.

---

### Task 2 — Update the test: step count

**Mode:** TDD
**Depends on:** none

In `tools/test_build_gate_chain.py`, `test_full_step_sequence_and_namespaces`, change:
- Comment on line 122: `"nine spawned scripts"` → `"ten spawned scripts"`
- Assertion: `["script"] * 9` → `["script"] * 10`

**Done when:** The assertion reads `["script"] * 10`.

---

### Task 3 — Update the test: spawned path list

**Mode:** TDD
**Depends on:** Task 2

In the same test, append `"tools/validate-claude-plugin-manifests.py"` as the last entry in the `spawned` expected list.

**Done when:** The list has 10 entries ending with `"tools/validate-claude-plugin-manifests.py"`.

---

### Task 4 — Run unit test

**Mode:** Goal-based check
**Depends on:** Tasks 1, 2, 3

Run `python tools/test_build_gate_chain.py`.

**Done when:** Command exits 0.

---

### Task 5 — Smoke the validator standalone

**Mode:** Goal-based check
**Depends on:** none (can run before gate chain wiring)

Run `make build` first if `dist/claude-plugins/` is absent, then:
`python tools/validate-claude-plugin-manifests.py`

**Done when:** Command exits 0 (confirms no pre-existing manifest errors that would block build-check).

---

### Task 6 — Full gate

**Mode:** Goal-based check
**Depends on:** Tasks 4, 5

Run `make build-check`.

**Done when:** Command exits 0.
