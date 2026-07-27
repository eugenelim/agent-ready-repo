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
