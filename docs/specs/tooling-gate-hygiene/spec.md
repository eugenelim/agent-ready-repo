# Spec: tooling-gate-hygiene

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Contract:** none new. One user-visible message gains a branch; one on-demand
  check becomes a gate.

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

<!-- Mode: full. One risk trigger fires: structural / CI-behaviour change —
promoting the contract-drift check to a build-check gate changes what can merge.
The G-plan human gates are satisfied by the operator's standing authorization for
this run; every other full-mode obligation is run as written. -->

## Objective

Three tooling defects that each make a check less useful than it appears: a
read-only flag that writes, a diagnostic that names the wrong cause, and a
correct check that gates nothing because it only runs when asked.

## Acceptance Criteria

- [x] **AC1 — `build-site.py --dry-run` writes nothing.** Every write in the
  script honoured the flag except one `mkdir` for the generated `packs/`
  directory, which ran unconditionally — so a dry run created directories on its
  way to reporting that it would create them. That makes the flag useless as a
  read-only check: it fails outright against a non-writable tree, and against a
  writable one it leaves generated directories behind.

- [x] **AC2 — the dry-run guarantee is pinned behaviourally.** A test runs the
  real script as a subprocess and asserts no generated directory appears.
  **Mutation-verified:** reverting the guard fails exactly this test, and
  restoring it passes. A structural companion test asserts no *function* writes
  without referencing `dry_run` — and its docstring states plainly that it would
  NOT have caught this defect (the unguarded `mkdir` lived in `main()`, which
  references `dry_run` throughout), so nobody mistakes it for the real guarantee.

- [x] **AC3 — WSL gets a diagnosis naming a cause it can act on.** A WSL
  distribution reports `sys.platform == "linux"` and does not inherit the Windows
  trust store, so an authority pushed by Group Policy or Intune is invisible until
  installed into the distribution too. The old message said the fallback is
  macOS-only: true, and useless. The new branch names the two-trust-store split
  and the `update-ca-certificates` remedy.

- [x] **AC4 — detection only; no reach across the trust boundary.**
  `running_under_wsl` reads `WSL_DISTRO_NAME` / `WSL_INTEROP` and `/proc/version`.
  A test asserts its source contains no `/mnt/c`, `certutil`, `powershell.exe`,
  `cmd.exe`, or `wslpath` — reading the Windows store from inside WSL would
  auto-trust material from outside the distribution's own trust domain.

- [x] **AC5 — both message branches are covered, and cannot swap.** A test drives
  the WSL branch end-to-end and asserts the generic platform message does *not*
  also fire; the pre-existing plain-linux test now asserts the WSL text does not
  appear. Either branch silently taking the other's traffic fails a test.

- [x] **AC6 — the contract-drift check is a gate.** It is a `build_gate_chain.py`
  step, so it runs in `make build-check` and in CI, which invokes the same target.
  No `lint-ci-parity` disposition is needed for that reason.

- [x] **AC7 — the calibration bar is met and recorded.** The deferral asked for
  two clean passes on `origin/main` with no false positive. Three are recorded:
  2026-08-01, 2026-08-15, 2026-08-16.

- [x] **AC8 — the gate-chain anchor tests are updated, not bypassed.**
  `test_build_gate_chain.py` pins the exact step sequence and caught the addition;
  its pinned list is extended.

- [x] **AC9 — the deferral marker is cleared.** The deferral bullet naming this promotion in
  `spec/digital-experience-contract` records delivery, and notes that the path it
  names was since relocated to `tools/repo/check_contract_drift.py`.

- [x] **AC10 — the three backlog entries are removed.** Verified by diffing the
  slug set against `origin/main`: exactly three removed, none added.

## Boundaries

### Never do

- Never read the Windows trust store from inside WSL. AC4 is the rail.
- Never widen the drift check's scope while promoting it. Promotion is a wiring
  change; the check's logic is untouched.

## Testing Strategy

- **TDD + mutation** for AC1/AC2. **TDD** for AC3–AC5. **Goal-based** for
  AC6–AC10.
