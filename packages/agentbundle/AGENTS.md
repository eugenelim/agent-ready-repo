# packages/agentbundle — agent context

## PyPI publishing

**Publish only from `main`.** Never push an `agentbundle-v*` tag from a
feature branch, research branch, or worktree. Tags pushed from non-`main`
refs trigger the release workflow and will publish to PyPI — there is no
branch guard.

**After every merge to `main` that bumps the version, tag and push immediately.**
A merged version bump that isn't tagged leaves PyPI stale. The release workflow
runs on tag push only (`push: tags: agentbundle-v*`); it does not run on merge.

**Workflow:**
1. Bump `version.py` `CLI_VERSION`, `pyproject.toml` `version`, and CHANGELOG in the same PR.
2. Merge to `main`.
3. Tag the merge commit: `git tag agentbundle-v<version> <sha> && git push origin agentbundle-v<version>`.
4. Confirm the `release-agentbundle` workflow's `publish-pypi` job completes green.

**Version rule:** the next version after what is currently on PyPI. Check
`pip index versions agentbundle` before choosing a version number to avoid
collisions with any prior research-branch publish.

## Engine-Change-RFC requirement

Any PR that touches `packages/agentbundle/**` must include an
`Engine-Change-RFC: <RFC-NNNN or ADR-NNNN>` trailer in at least one commit
message. The `lint-catalogue-curation-guard` tool enforces this on every
build; without the trailer the build will fail. Cite the RFC or ADR that
governs the change — or ADR-0056 for general engine additions — and place the
trailer on its own line after the commit message body.

## Windows portability — test isolation

Two patterns cause test failures on `windows-latest` CI; avoid them in new
integration tests:

**User-scope root isolation.** `patch.dict(os.environ, {"HOME": ...})` does
not redirect user-scope installs on Windows because `scope.resolve_user_root()`
calls `Path("~").expanduser()` which reads `USERPROFILE`, not `HOME`. Two
equivalent patterns exist in the suite; use whichever fits the test shape:

- Preferred for `setUp`-based tests: also patch `AGENTBUNDLE_USER_ROOT`.
  `resolve_user_root()` checks it first and bypasses `expanduser` entirely.
  ```python
  patch.dict(os.environ, {"HOME": str(self.home), "AGENTBUNDLE_USER_ROOT": str(self.home)})
  ```
- Existing tests that patch `USERPROFILE` directly also work, since
  `expanduser` reads `USERPROFILE` on Windows.

**Shell dispatch.** Do not invoke `sh -c <path>` (or `/usr/bin/bash -c
<path>`) in tests — on Windows, Git for Windows bash strips backslashes from
paths (`C:\Users\...` → `C:Users...`). Guard the dispatch portion only,
keeping platform-independent assertions intact:

```python
if sys.platform == "win32":
    return  # sh -c <windows-path> strips backslashes
result = subprocess.run(["sh", "-c", command], ...)
```

**Concurrent install race.** Thread-based concurrent-install tests that
assert both adapter rows land can fail on Windows: the inband-detection
TOCTOU window (disk state visible before state-file commit) causes cursor to
detect orphans and return rc=1. This is a test-harness artifact — the
statelock's cross-process `O_CREAT|O_EXCL` guarantee is not exercised by
thread-based tests on any platform. Skip failing concurrent tests with
`@unittest.skipIf(sys.platform == "win32", ...)` and open a follow-up to
either root-cause the thread-model race or convert workers to subprocesses.

**Subprocess encoding (cp1252).** On Windows the default stdout encoding is
cp1252. Any subprocess that prints a Unicode character outside that range
(e.g. `✓` U+2713) crashes with `UnicodeEncodeError` before producing output,
so the calling test sees an empty string and fails. Fix: force UTF-8 in the
subprocess env and decode with the same encoding:

```python
env = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"}
result = subprocess.run([sys.executable, str(script)], env=env,
                        capture_output=True, text=True, encoding="utf-8")
```

**CRLF vs LF byte comparisons.** Git's `autocrlf` setting converts line
endings on Windows checkout, so `file_a.read_bytes() == file_b.read_bytes()`
fails even when the logical content is identical. Normalize before comparing:

```python
def _norm(p): return p.read_bytes().replace(b"\r\n", b"\n")
assert _norm(path_a) == _norm(path_b)
```

**Symlinks and execute bits.** `os.symlink()`, `Path.symlink_to()`, and
`os.chmod(..., 0o755)` require Developer Mode on Windows CI and raise
`WinError 4390` or silently no-op without it. Skip tests that rely on these:

```python
@unittest.skipIf(sys.platform == "win32", "symlinks require Developer Mode on Windows")
```

**Root-path detection.** `str(path) == "/"` is always `False` on Windows
(paths have drive letters). The cross-platform root check is:
`normalised == normalised.parent`.

**`path.as_uri()` vs manual `file://` construction.** `f"file://{path.as_posix()}"`
produces `file://C:/path` on Windows — `C` is parsed as the netloc authority,
not the path. Use `path.as_uri()` which emits `file:///C:/path` (three slashes).
For URLs with an explicit host, add a separator: `sep = "" if posix.startswith("/") else "/"`.

## Gate G — release impact

Any change to production source under `packages/agentbundle/agentbundle/`
triggers Gate G. The PR must have **all three**:
1. Version bump in `version.py` (`CLI_VERSION`) and `pyproject.toml` (`version`).
2. Changelog entry in `packages/agentbundle/CHANGELOG.md`.
3. `Engine-Change-RFC:` trailer (see section above).

**Version collision on rebase.** If main landed a version bump while your
branch was open, your bump will conflict. Resolve to `<main-version> + 0.0.1`
(e.g. main at `0.21.0` → your branch becomes `0.21.1`). In `git rebase`
conflicts, `HEAD` is main — take main's version number as the base, then
increment patch.

## SAST (Semgrep) false-positives

`dangerous-subprocess-use-tainted-env-args` fires on `subprocess.run` when
any argument derives from user input, even with `shell=False` (which is safe).
Prefer the library API over subprocess when one exists (e.g. `zipapp.create_archive`
instead of `python -m zipapp`). When `# nosemgrep` is unavoidable, place it on
the line Semgrep anchors the finding to — for multi-line calls that is the first
line of the argument list, not the `subprocess.run(` call line.
