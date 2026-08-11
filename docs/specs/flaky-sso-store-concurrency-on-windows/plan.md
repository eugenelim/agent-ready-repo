# Plan: Flaky SSO store concurrency on Windows

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Approved | Executing | Done -->

## Mode

Full mode, one dependent implementation task. Authentication and filesystem
confinement risk triggers require specialist review and Windows CI evidence.

## Constraints

- Keep `_sso_lock_path()` / `_contained()` as the fail-closed validation
  boundary and retain `ProfileConfinementError` exit code `3`.
- Preserve locking, timeout, diagnostic, and file-mode behavior.
- Use Python 3.11 Windows path-resolution behavior as the platform contract.
- Add no dependency, module, option, retry, sleep, flaky marker, quarantine,
  relaxed comparison, or platform-specific production branch.
- Derive the `credential-brokers` patch-version increment from
  `packs/credential-brokers/pack.toml` during execution; do not duplicate a
  version literal in planning artifacts.
- Do not change the `credbroker` package version because package runtime code
  and its public interface are unchanged.

## Approach

Add a deterministic construction regression that models the Windows
non-strict-resolution transition: before the fixed parent exists, the child
resolve observes a lexical parent form; after a simulated competing creation,
the parent resolve observes its canonical form. The original order fails
without threads or timing. Add a boundary regression that enters
`_profile_lock()` with an escaping profile and proves no child is opened.

After demonstrating red, create the fixed `_SSO_LOCK_DIR` before calculating
the confined child lock path. This is the only production change. The fixed
parent contains no profile input; the child remains validated by
`_sso_lock_path()` / `_contained()` before `os.open()`, so traversal and
wrong-parent inputs remain fail-closed.

Then increment the pack patch version, rebuild generated projections, run the
macOS gates, review the diff, and open a PR. Treat the existing Windows
workflow and its credential-broker suite as the platform oracle.

## T1: Reproduce and fix first-use lock-path canonicalisation

**Depends on:** none  
**Acceptance criteria:** AC1, AC2, AC3, AC4, AC5, AC6, AC7, AC8, AC9
**Verification mode:** TDD for AC1-AC2; goal-based construction and existing
regressions for AC3-AC5; goal-based named gates/artifacts for AC6-AC9

### Files

- `packages/credbroker/tests/unit/test_sso_profile_lock.py`
- `packs/credential-brokers/.apm/adapter-root-bins/sso-broker.py`
- `packs/credential-brokers/pack.toml`
- `packs/credential-brokers/.claude-plugin/plugin.json`
- `docs/product/changelog.md`
- Generated projection files changed by `FORCE=1 make build-self`

### Tests

`stub: draft (uncompiled)` — the managed shell cannot create bytecode, pytest
temp directories, or generated output. Materialize these stubs at the start of
execution and have the user run the targeted command before any runtime edit.

```python
# STUB: AC1, AC2
def test_profile_lock_confines_after_first_use_parent_creation(
    broker: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Confinement must compare child and parent in one existence state."""
    lexical_parent = broker._SSO_LOCK_DIR.parent / "LEXICAL-locks"
    canonical_parent = broker._SSO_LOCK_DIR.parent / "canonical-locks"
    original_resolve = Path.resolve
    original_mkdir = Path.mkdir
    parent_exists = False
    opened: list[Path] = []

    def resolve_with_existence_transition(
        path: Path,
        *args: object,
        **kwargs: object,
    ) -> Path:
        nonlocal parent_exists
        if path == broker._SSO_LOCK_DIR:
            return canonical_parent if parent_exists else lexical_parent
        if path.parent == broker._SSO_LOCK_DIR:
            resolved_parent = canonical_parent if parent_exists else lexical_parent
            parent_exists = True  # Simulate the competing first-use mkdir.
            return resolved_parent / path.name
        return original_resolve(path, *args, **kwargs)

    def mkdir_with_existence_transition(
        path: Path,
        *args: object,
        **kwargs: object,
    ) -> None:
        nonlocal parent_exists
        if path == broker._SSO_LOCK_DIR:
            parent_exists = True
            return
        original_mkdir(path, *args, **kwargs)

    def record_open(path: Path, *args: object, **kwargs: object) -> int:
        opened.append(Path(path))
        return 101

    monkeypatch.setattr(Path, "resolve", resolve_with_existence_transition)
    monkeypatch.setattr(Path, "mkdir", mkdir_with_existence_transition)
    monkeypatch.setattr(os, "open", record_open)
    monkeypatch.setattr(os, "close", lambda fd: None)
    monkeypatch.setattr(broker, "_acquire_once", lambda fd: None)
    monkeypatch.setattr(broker, "_release_once", lambda fd: None)

    with broker._profile_lock("jira"):
        pass

    # `_contained()` validates canonical forms but returns the original path.
    assert opened == [broker._SSO_LOCK_DIR / "jira.lock"]


# CONSTRUCTION: AC3
def test_profile_lock_refuses_escape_before_open(
    broker: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The lock boundary may create its fixed parent but never an escape."""
    broker._SSO_LOCK_DIR.parent.mkdir(parents=True, exist_ok=True)
    opened: list[Path] = []
    created: list[Path] = []
    original_mkdir = Path.mkdir

    def record_open(path: Path, *args: object, **kwargs: object) -> int:
        opened.append(Path(path))
        return 101

    def record_mkdir(
        path: Path,
        *args: object,
        **kwargs: object,
    ) -> None:
        created.append(path)
        original_mkdir(path, *args, **kwargs)

    monkeypatch.setattr(os, "open", record_open)
    monkeypatch.setattr(Path, "mkdir", record_mkdir)

    with pytest.raises(broker.ProfileConfinementError):
        with broker._profile_lock("../escape"):
            pass

    assert set(created) <= {broker._SSO_LOCK_DIR}
    assert opened == []
```

Before materializing, add only imports already established by the test module
(`os`, `Path`, and `ModuleType`) if absent. The TDD stub must fail on the
original ordering with `ProfileConfinementError`; the AC3 construction test
must remain green before and after the production change. A passing TDD stub
before the runtime edit means the seam is invalid and implementation must
stop. Running the targeted module supplies the compile/collect check
unavailable here.

### Implementation

1. Materialize the two test stubs without changing runtime code.
2. Run the targeted profile-lock and concurrency tests and capture the
   deterministic red result for the first stub.
3. In `_profile_lock()`, move the existing fixed-directory `mkdir()` before
   the existing `_sso_lock_path(profile)` call. Do not alter either operation.
4. Re-run the targeted tests; confirm the deterministic regression, both
   `test_file_floor_path_is_serialised_too` parameter cases, and confinement
   regressions are green without skip.
5. Run the full `packages/credbroker` suite and local lint/type gates.
6. Increment the `credential-brokers` pack patch version from its current
   value in both `pack.toml` and `.claude-plugin/plugin.json`, add the required
   `docs/product/changelog.md` entry, run `FORCE=1 make build-self`, inspect
   generated changes, and run `make build-check`.
7. Run adversarial, security, and quality review; address findings within the
   three-iteration cap.
8. Obtain implementation approval, create a Conventional Commit, push the
   branch, and open the PR.
9. Wait for `.github/workflows/build-check-windows.yml` job
   `build-check-windows` (`make build-check (windows)`). Inspect the
   `credbroker suite (process-tree kill parity)` step and iterate on any real
   failure until the complete job is green. Do not use an unchanged rerun as
   acceptance evidence.

### Local verification commands

- Targeted red/green:
  `python3 -m pytest -p no:cacheprovider packages/credbroker/tests/unit/test_sso_profile_lock.py packages/credbroker/tests/unit/test_sso_store_concurrency.py::test_file_floor_path_is_serialised_too -q`
- Full package:
  `python3 -m pytest -p no:cacheprovider packages/credbroker/tests/ -q`
- Lint and types: `make lint-ruff`, then `make lint-mypy`.
- Projection: `FORCE=1 make build-self`.
- Repository gate: `make build-check`.

## Verification evidence required

- Captured deterministic red result before the production change.
- Captured targeted green and full `packages/credbroker` green on macOS.
- Green `make lint-ruff`, `make lint-mypy`, `FORCE=1 make build-self`, and
  `make build-check` on macOS.
- Reviewer-clean evidence and both human approvals.
- PR URL and green Windows `build-check-windows` job URL/identifier showing
  completion of the credential-broker suite.

## Declined patterns

- Retry, sleep, stress-loop, flaky marker, quarantine, or rerun-only response.
- Case-insensitive string comparison as a substitute for a stable filesystem
  observation.
- Catching `ProfileConfinementError` and continuing without the profile lock.
- Moving `_contained()` or adding a Windows-only confinement branch.
- Adding a new abstraction for one reordered operation.
