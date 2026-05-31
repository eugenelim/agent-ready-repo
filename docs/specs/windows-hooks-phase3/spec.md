# Spec: windows-hooks-phase3

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none — runtime-portability port; no adapter-contract or charter impact.

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

> **Retroactive spec (2026-05-31).** Promoted from the work-loop TRIO
> ([`plan.md`](plan.md)) into the spec/plan structure after the work shipped.
> The plan carries the full per-script behaviour matrices; this spec records the
> contract the merged tree satisfies. Every AC below is verified against the
> merged tree.

## Objective

Step 3 of the repo's Windows-support plan: rewrite the seven bash scripts that
form the pre-PR and session-start runtime as pure-stdlib Python so the hooks and
linters run on native Windows (where bash is absent by default). The port is
parity-pinned — identical stdout shapes, exit codes, and check semantics as the
bash originals — and the `.sh` siblings are removed so there is one runtime, not
two. Windows CI coverage is a sibling concern handled by
[`windows-ci-bundler`](../windows-ci-bundler/spec.md).

## Boundaries

### Always do

- Preserve bash parity: identical stdout block/label shapes, identical exit
  codes, identical check semantics. The existing `tools/test-*.sh` runners are a
  second oracle alongside the new pytest smoke tests.
- Spawn child processes with `sys.executable` (not a literal `python`) so the
  child interpreter matches the parent, and use list-form `subprocess.run`
  (never `shell=True`, never string-interpolation into argv).

### Ask first

- Consolidating the five separate linters into one umbrella linter with
  subcommands (that is a refactor needing an RFC, not a port).
- Porting the `tools/test-*.sh` runner *bodies* to pytest (only the
  bash→python invocation line inside each runner changes here).

### Never do

- Add a third-party dependency — the ports are stdlib-only (a hard constraint,
  also enforced by `lint-build.py`'s import audit).
- Leave a `.sh` sibling in place once its `.py` lands (no dual runtime).

## Testing Strategy

- **TDD / parity-pinned** for the two hooks and the load-bearing linters: new
  pytest smoke tests under `packages/agentbundle/tests/hooks/` assert exit code
  and stdout shape, mirroring the corruption cases the bash runners exercised.
- **Goal-based check** for the thin linter ports and the `.sh`-deletion sweep:
  the existing `tools/test-*.sh` runners stay green after the invocation flip,
  and a clean `python tools/hooks/pre-pr.py` exits 0.

## Acceptance Criteria

- [x] AC1. The two core hooks ship as stdlib Python at
  `packs/core/.apm/hooks/{session-start,pre-pr}.py`, with the self-host mirrors
  `tools/hooks/{session-start,pre-pr}.py`; the `.sh` siblings are removed.
- [x] AC2. The five Phase-3 linters ship as stdlib Python under `tools/`
  (`lint-agents-md`, `lint-build`, `lint-knowledge`, `lint-agent-artifacts`,
  and `lint-skill-spec`); no `.sh` sibling of those five remains. (The Phase-3
  `lint-skill-deps` port was renamed to `tools/lint-skill-spec.py` in a later
  PR; the rename is noted in [`plan.md`](plan.md). A later, unrelated
  `tools/lint-credentialed-skills.sh` was added after this port and is out of
  its scope.)
- [x] AC3. pytest smoke tests at
  `packages/agentbundle/tests/hooks/{test_session_start_py.py,test_pre_pr_py.py}`
  invoke the ported hooks as subprocesses and assert exit code plus the stdout
  shapes Claude Code expects, mirroring the bash runners' corruption cases.
- [x] AC4. `python tools/hooks/pre-pr.py` on a clean checkout emits a `✓` line
  per linter check and exits 0.
- [x] AC5. `lint-agents-md.py` check #2 accepts both a real `CLAUDE.md` →
  `AGENTS.md` symlink **and** the Windows-materialised shape (a regular file
  whose content is exactly the string `AGENTS.md`); any other regular-file
  content still fails as a drift hazard.
- [x] AC6. The ports are stdlib-only — no third-party imports in any ported hook
  or linter, enforced by `lint-build.py`'s import audit.
- [x] AC7. `tools/hooks/README.md` example wiring uses
  `python tools/hooks/session-start.py` (not bash) and notes Python ≥ 3.11.

## Assumptions

- Technical: the single Windows-hostile surface in the audited set was
  `Path("CLAUDE.md").is_symlink()` returning `False` on a default Windows
  checkout (no Developer Mode); AC5's dual-shape acceptance is the remediation.
  All other surfaces (`rglob`, `re`, `git` plumbing, `stat().st_mtime`,
  list-form `subprocess`, `tomllib`, `json`, `argparse`) are portable as-is.
  (source: [`plan.md`](plan.md) § *Audited Windows-hostile surfaces*)
- Process: the linter set has grown since the port (e.g. `lint-seeds`,
  credentialed-skill lints, the `lint-skill-deps`→`lint-skill-spec` rename), so
  `pre-pr.py`'s ✓-line set is larger than the TRIO's original five; AC4 pins the
  invariant (a ✓ per check, exit 0), not a fixed count. (source: running
  `python tools/hooks/pre-pr.py` 2026-05-31)
