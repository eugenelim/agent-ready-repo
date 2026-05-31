# Spec: windows-ci-bundler

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none — CI-infrastructure change; no adapter-contract or charter impact.

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

> **Retroactive spec (2026-05-31).** Promoted from the work-loop TRIO
> ([`plan.md`](plan.md)) into the spec/plan structure after the work shipped
> (PR #77, follow-up `dfb9dc8`). The shipped design **diverged** from the
> TRIO's original plan — see Assumptions. Every AC below is verified against
> the merged tree.

## Objective

The Phase-3 bash→Python port of the repo's hooks and linters
(see [`windows-hooks-phase3`](../windows-hooks-phase3/spec.md)) was done so the
runtime works on native Windows. That port can silently regress unless a real
Windows runner exercises it. This spec adds Windows CI coverage: a green
`windows-latest` job on every code PR, with **zero** impact on the existing
Linux `make build-check` gate that is the required status check on `main`.

## Boundaries

### Always do

- Keep the Linux `build-check.yml` job (the required status check) unchanged.
- Use `python` (not `python3`, which Windows runners lack on PATH) and set
  `PYTHONUTF8=1` so the linters' glyph output encodes and pytest can decode
  stderr on Windows.

### Ask first

- Promoting the Windows job to a *required* status check on `main`.
- Folding the Windows coverage back into `build-check.yml` as an OS matrix.

### Never do

- Gate the Linux required check behind Windows-specific `paths`/`paths-ignore`
  filters — a doc-only PR must never be able to skip the Linux gate.
- Port the Linux-only ripgrep scrubs (source-attribution / Rail-C) into the
  Windows job; that is a separate concern.

## Testing Strategy

Goal-based check. The contract is observable from the workflow file and the CI
run: the YAML parses, the Linux gate is preserved, and the Windows job runs the
bundler `build` + `check` to green on `windows-latest`. The authoritative
validation is the Windows CI run itself (authoring happened on macOS).

## Acceptance Criteria

- [x] AC1. `.github/workflows/build-check-windows.yml` defines a
  `build-check-windows` job on `runs-on: windows-latest` that installs
  `agentbundle` editable plus pytest, runs `python -m agentbundle.build build`,
  then `python -m agentbundle.build check` (the Windows mirror of the Linux
  `make build-check`).
- [x] AC2. The job exports `PYTHONUTF8=1` so the linters' glyph output encodes
  and pytest can decode subprocess stderr on Windows.
- [x] AC3. The Windows coverage ships as a **separate workflow file**, not an OS
  matrix folded into `build-check.yml`, so the Linux `make build-check` job (the
  required status check on `main`) is untouched.
- [x] AC4. `build-check-windows.yml` carries `paths-ignore: docs/**` so a
  docs-only PR skips the Windows parity job, while the Linux required check still
  runs on the same PR.
- [x] AC5. `.github/workflows/build-check.yml` (the Linux gate) remains present
  and is the required status check.

## Assumptions

- Process: the shipped form **diverged** from the TRIO's "add a second job to
  `build-check.yml`" plan. GitHub `paths`/`paths-ignore` filters are
  workflow-level, not per-job, so a doc-only skip on a shared workflow would
  also gate the Linux required check. The work shipped as a *separate*
  `build-check-windows.yml` to get the doc-only skip without touching the Linux
  gate. (source: `.github/workflows/build-check-windows.yml` header comment +
  commit `dfb9dc8`)
- Technical: `windows-latest` runners default to PowerShell and lack `python3`
  on PATH; `python` + `PYTHONUTF8=1` is the portable invocation. (source:
  workflow file + commit `a85a1bf`)
