# ADR-0094: Per-worktree virtual environments are declined; the packages are imported from source instead

- **Status:** Accepted
- **Date:** 2026-08-22
- **Decision-makers:** repository maintainers
- **Supersedes:** none
- **Related:** `docs/specs/repo-tests-worktree-source/spec.md`; `docs/specs/worktree-runtime-hygiene/spec.md` (Shipped); ADR-0036

## Decision summary

- **Decision:** We will not create a per-worktree virtual environment; `agentbundle` and `credbroker` are imported from source in this repository's own gates and tests.
- **Because:** the write a venv was meant to isolate no longer happens — no repository gate installs either package.
- **Applies to:** this repository's local development and test invocations. Adopter installs and CI runner provisioning are untouched.
- **Tradeoff accepted:** each new worktree still shares one interpreter's `site-packages`, so a distribution version skew there remains observable — `importlib.metadata.version()` can disagree with the imported module.
- **Revisit if:** a repository gate ever genuinely requires an installed (not merely importable) `agentbundle` or `credbroker`, or a supported sandbox gains the ability to run `pip install` without leaving unremovable litter.

## Context

Nine worktrees of this repository share one interpreter. A per-worktree virtual
environment was proposed to stop `pip install -e` from mutating that shared
environment — a real hazard, because an editable install is global to the
interpreter and one worktree's bootstrap can disturb another's running gates.

Three facts, measured on 2026-08-21 and 2026-08-22, changed the picture.

**The install was never required.** `Makefile:7` already places both package
directories on `PYTHONPATH` for every `make` target, and every invocation is
`$(PYTHON) -m agentbundle`, never the console script. The only thing missing was
a bare `pytest`, which has neither the working directory nor a `PYTHONPATH` of
its own; declaring `pythonpath` in `pyproject.toml` closes that. After that, no
repository gate installs either package, so a virtual environment would isolate
a write that no longer occurs.

**A supervised worker cannot create a usable virtual environment at all.**
`python3 -m venv` fails inside `ensurepip` under the supervised worker's sandbox
— inside the workspace, in the system temporary directory, and with `TMPDIR`
redirected into the workspace. `python3 -m venv --without-pip` succeeds, so
directory creation is not the constraint.

**The root cause is a sandbox policy denial, not configuration.** pip's `install`
unconditionally builds a network session (`get_default_session` →
`_create_truststore_ssl_context`) even under `--no-index`. That materialises
certifi's CA bundle as a temporary file carrying the macOS
`com.apple.provenance` extended attribute, and the sandbox denies both read and
unlink on it: `PermissionError: [Errno 1] Operation not permitted`. `EPERM`, not
`EACCES` — a policy refusal rather than a file mode. So no network allowlist,
path change, or permission grant helps.

State the frame, because it is what localises the cause: those venv measurements
were taken under the supervised worker's sandbox. `python3 -m venv` succeeds
under an interactive session's sandbox on the same machine and the same
interpreter. The failure belongs to that sandbox's policy, not to the host or
the Python installation.

## Decision

**We will not introduce a per-worktree virtual environment**, and this
repository's gates and tests will import `agentbundle` and `credbroker` from
source.

Source resolution has two mechanisms and no third: `PYTHONPATH` for `make`
targets (`Makefile:7`), and `[tool.pytest.ini_options] pythonpath` for a bare
`pytest`. Neither installs anything.

The boundary is deliberate and narrow. This decision governs *this repository's
own* invocations. It says nothing about adopters, who install the package
normally, and nothing about CI, where each job provisions a fresh runner on
which nothing is on `PYTHONPATH` and an install is the correct move. An
installed copy on a maintainer's machine remains entirely legitimate — it is how
the `agentbundle` console script exists, and an editable install is ADR-0036's
layer-3 catalogue-source detection mechanism. It is simply not what these gates
use.

## Decision drivers

- **Does the isolation protect a write that still happens?** After the source-import
  change, no.
- **Can every supported agent runtime execute the mechanism?** No — the supervised
  worker cannot create a virtual environment with pip at all.
- **Does the mechanism leave the shared environment worse than it found it?** Yes:
  each failed attempt leaves roughly 265KB of temporary files that the worker
  itself cannot delete, because the same policy that blocks reading them blocks
  unlinking them.
- **Does existing tooling already assume the mechanism is absent?** Yes — see the
  latent trap below.

## Consequences

**Positive.** No repository gate depends on the state of a shared interpreter,
so one worktree's setup cannot disturb another's running tests. A supervised
worker can run `pytest <path>` — the only form it can issue, with no environment
prefix — and get this worktree's source. Nothing must be provisioned before the
gates run beyond the genuine tooling (`ruff`, `mypy`, `pytest`, and the
requirements files named in the `Makefile`).

**Negative, accepted.** All worktrees continue to share one `site-packages`. When
the worktree source version leads the installed distribution — the normal state
during development — `importlib.metadata.version()` and the imported module
report different versions, and code that consults the former sees the older one.
That is a consequence to know about, not a defect to fix: both values are
legitimate, and the repository's own gates resolve the module from source.

**A latent trap this decision also avoids.** `tools/repo/worktree_hygiene.py`
lists `.venv`, `venv`, and `env` as deletable `dependencies` candidates
(`:63-65`). That is correct and stays. But its in-use guard resolves
distributions from `importlib.metadata.distributions()` on **the interpreter
running the cleaner** (`_installed_distribution_locations`, `:862-870`, consumed
by `_is_in_use` at `:1161` and at `:1736`). A per-worktree virtual environment
would therefore never be recognised as in use unless the cleaner happened to be
running from inside it — so the cleanup tool could delete a live environment out
from under a peer worktree. Introducing virtual environments would require
fixing that guard first. Not introducing them leaves nothing to fix.

**Revisit if:** a repository gate ever genuinely requires an installed rather
than importable `agentbundle` or `credbroker`, or a supported sandbox gains the
ability to run `pip install` without leaving unremovable litter.

## Confirmation

- **Mode:** lint/CI
- **Signal:** `make lint-editable-install` (`tools/repo/editable_install_guard.py`)
  fails when an editable install of either package points at a worktree other
  than the one being worked in — the state in which this decision has already
  been violated by someone. `test-unleased` depends on it, so the gates cannot
  pass in that state.
- **Residual:** the guard describes installs; it cannot prevent one being made.
  A plain wheel install and an editable install pointing at the current worktree
  are both deliberately allowed, so a maintainer can still reach the harm state
  transiently by re-pointing an editable install while a peer's gates run. And
  nothing prevents creating a `.venv` by hand — the decision governs what the
  repository *requires*, not what a machine contains;
  `tools/repo/worktree_hygiene.py` would treat such a directory as a deletable
  dependency candidate, which is the trap the Consequences describe.

## Alternatives considered

**Per-worktree `.venv` (rejected).** Isolates a write that no longer happens;
cannot be created by the supervised worker at all; and would expose the
`_is_in_use` trap above. Rejected against all four decision drivers.

**Uninstall the global `agentbundle` and `credbroker` (rejected).** The
maintainer's installed copy is deliberate and is a real consumer surface — the
console script and ADR-0036's editable detection both depend on it. Removing it
to make tests tidier would break a legitimate workflow to fix a problem that
source imports already solve.

**One shared virtual environment for all worktrees (rejected).** Reintroduces
exactly the shared mutable state the proposal set out to eliminate, and still
cannot be created by the supervised worker.

**Do nothing (rejected).** Leaves a bare `pytest` importing whatever is
installed, and leaves the `Makefile` instructing each new session to write to
the shared environment — the write that caused the original hazard.

## References

- `tools/repo/build_gate_chain.py:60-72` — records that both packages are
  importable from source, so neither needs `pip install -e`.
- `tools/repo/worktree_hygiene.py:862-870`, `:1161`, `:1736` — the in-use guard
  that resolves distributions from the interpreter running the cleaner.

<!-- Spec pointers stay in `Related:` above rather than here: CONVENTIONS
     § Cite upward, never downward — an ADR does not cite a spec as a source. -->
