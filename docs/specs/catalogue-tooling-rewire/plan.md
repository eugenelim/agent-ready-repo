# Plan: Catalogue Tooling — Repository Rewiring

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting

## Approach

Three parallel task streams: (A) Makefile rewiring; (B) tools/ reorganization
+ shims; (C) pre-pr-catalogue thinning. Stream A and B can proceed in parallel
after a brief audit. Stream C depends on B (needs the new directory structure).
All streams require Wave 1-4 specs to be shipped.

## Constraints

- ini-005 brief Bucket 9.
- Every moved script must have a shim at the old path until the next minor release.
- hooks.json + settings.json must be updated BEFORE or simultaneously with the
  shim creation (not after) — hooks run real scripts, not shims.
- `tools/build_gate_chain.py` Windows compatibility must be preserved.
- No portable catalogue logic may be implemented in tools/ in this spec.

## Construction tests

- `test_makefile_lint_packs_calls_catalogue_lint`: parse Makefile `lint-packs`
  target; assert it contains `agentbundle catalogue lint`.
- `test_shims_delegate_correctly`: for each shim at old path, import and run
  with a no-op fixture; assert exit code equals delegate's exit code.
- `test_old_paths_still_exist`: assert `tools/publish-claude-plugins.py`,
  `tools/pre-pr-catalogue.py`, `tools/build_gate_chain.py` exist.
- `test_new_paths_exist`: assert `tools/catalogue/publish_claude_plugins.py`,
  `tools/repo/build_gate_chain.py` exist.
- `test_no_portable_logic_in_tools`: grep `tools/` for `import agentbundle.build.lint_packs`,
  `import agentbundle.build.main`, `cmd_build`, `cmd_lint_packs`, `cmd_check`
  (direct calls that bypass the new surface); assert zero hits (only shims allowed).

## Design (LLD)

### Makefile rewiring

```makefile
lint-packs:
    $(PYTHON) -m agentbundle catalogue lint --root .

build: lint-packs
    # existing recipe flags still work via --pack/--recipe
    $(PYTHON) -m agentbundle catalogue build --root . --output $(OUTPUT_DIR)

build-self:
ifeq ($(FORCE),1)
    $(PYTHON) -m agentbundle catalogue self-host --root . --write --force
else
    $(PYTHON) -m agentbundle catalogue self-host --root . --write
endif

build-self-dry-run:
    $(PYTHON) -m agentbundle catalogue self-host --root . --check

build-check:
    $(PYTHON) -m agentbundle catalogue verify --root .
    $(PYTHON) tools/repo/build_gate_chain.py build-check --packs-dir $(PACKS_DIR)
    # SAST/SCA leg appended separately (unchanged)
```

Note: `python -m agentbundle catalogue lint` uses the `-m` module invocation.
Alternatively, invoke as `$(PYTHON) -c "from agentbundle.cli import main; ..."`.
Prefer the direct `agentbundle` CLI entry point when available in the venv.

### tools/ reorganization

New structure (additions only, existing flat files kept as shims):
```
tools/
  catalogue/
    publish_claude_plugins.py   # moved from tools/publish-claude-plugins.py
    pre_pr_catalogue.py          # thinned version (calls agentbundle catalogue verify)
  repo/
    build_gate_chain.py          # moved from tools/build_gate_chain.py
    check_contract_drift.py      # moved from tools/check-contract-drift.py
  # Shims at old locations — print deprecation, delegate to new path
  publish-claude-plugins.py      # shim → tools/catalogue/publish_claude_plugins.py
  pre-pr-catalogue.py            # shim → tools/catalogue/pre_pr_catalogue.py
  build_gate_chain.py            # shim → tools/repo/build_gate_chain.py
  check-contract-drift.py        # shim → tools/repo/check_contract_drift.py
```

### Thinned pre_pr_catalogue.py

```python
#!/usr/bin/env python3
"""Catalogue pre-PR check — repo-specific portion.
Portable verification is handled by: agentbundle catalogue verify --root .
This script runs only repo-specific policy gates (spec state, traceability, etc.)
"""
import subprocess, sys

# Step 1: portable verify (mandatory)
rc = subprocess.run([sys.executable, "-m", "agentbundle", "catalogue", "verify", "--root", "."])
if rc.returncode != 0:
    sys.exit(rc.returncode)

# Step 2: repo-specific gates (unchanged from current pre-pr-catalogue.py body)
...
```

### build_gate_chain.py new flow

```python
# tools/repo/build_gate_chain.py build-check
def build_check(args):
    steps = [
        ("agentbundle catalogue verify", _run_catalogue_verify),
        ("pre-pr-catalogue", _run_pre_pr),
        ("spec-status", _run_spec_status),
        ("brief-coverage", _run_brief_coverage),
        ("traceability", _run_traceability),
    ]
    # lint-packs and build are now inside agentbundle catalogue verify
    return _run_chain(steps)
```

---

## Tasks

### T1: Makefile rewiring

**Verification mode:** Goal-based check

**Tests:**
- `test_makefile_lint_packs_calls_catalogue_lint`
- `test_makefile_build_self_calls_self_host_write`
- `test_makefile_build_check_calls_catalogue_verify`

**Approach:** Edit Makefile targets in-place. Test by extracting the command
string from the Makefile with Python string parsing (not shell execution —
avoid side effects in CI). Verify no target hard-codes old `agentbundle.build`
subcommands except in the SAST leg.

**Depends on:** all Wave 1-4 specs shipped

---

### T2: tools/ reorganization + shims

**Verification mode:** Goal-based check

**Tests:**
- `test_old_paths_still_exist` (shims)
- `test_new_paths_exist` (real scripts)
- `test_shims_delegate_correctly`

**Approach:** Create `tools/catalogue/` and `tools/repo/` directories. Copy
(then modify) scripts to new locations. Create shim wrappers at old paths.
Update hooks.json + settings.json FIRST, then add shims. Run CI locally to
confirm all workflows pass.

**Depends on:** T1 (Makefile audit determines which tools are still needed)

---

### T3: Thin pre_pr_catalogue + update build_gate_chain

**Verification mode:** Goal-based check

**Tests:**
- `test_pre_pr_catalogue_calls_catalogue_verify`: inspect the script body;
  assert it calls `agentbundle catalogue verify`.
- `test_no_portable_logic_in_tools`
- `test_build_gate_chain_verify_first`: run `build_gate_chain.py build-check`
  against a fixture with a deliberate lint failure; assert it exits at the
  verify step, not at a later gate.

**Approach:** Thin `tools/catalogue/pre_pr_catalogue.py` to call
`agentbundle catalogue verify` first, then run repo-specific checks. Update
`tools/repo/build_gate_chain.py` to remove the now-redundant portable gate
calls (lint-packs, build, check) since they run inside `catalogue verify`.

**Depends on:** T2

## Changelog
