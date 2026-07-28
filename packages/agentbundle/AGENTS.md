# packages/agentbundle — agent context

## PyPI publishing

Tag from `main` only. Never tag from a feature or research branch — there is no branch guard on the release workflow.

**Workflow:**
1. Bump `version.py` (`CLI_VERSION`), `pyproject.toml` (`version`), and CHANGELOG in the same PR.
2. Merge to `main`.
3. `git tag agentbundle-v<version> <sha> && git push origin agentbundle-v<version>`
4. Confirm `release-agentbundle` / `publish-pypi` goes green.

**Version rule:** next after what's on PyPI — run `pip index versions agentbundle` before choosing.

## Engine-Change-RFC requirement

Every PR touching `packages/agentbundle/**` needs an `Engine-Change-RFC: <RFC-NNNN or ADR-NNNN>` trailer in at least one commit. Use ADR-0056 for general additions. `lint-catalogue-curation-guard` enforces this; missing trailer = build failure.

## Windows portability — test isolation

**User-scope root isolation.** Patching `HOME` alone doesn't work on Windows — `expanduser` reads `USERPROFILE`. Also patch `AGENTBUNDLE_USER_ROOT` (checked first, bypasses `expanduser`):
```python
patch.dict(os.environ, {"HOME": str(self.home), "AGENTBUNDLE_USER_ROOT": str(self.home)})
```

**Shell dispatch.** Don't call `sh -c <path>` in tests — Git Bash strips backslashes from Windows paths. Guard with `if sys.platform == "win32": return`.

**Concurrent install race.** Thread-based concurrent-install tests that assert both adapter rows land can race on Windows (TOCTOU in inband-detection). Skip with `@unittest.skipIf(sys.platform == "win32", ...)`.

**Subprocess encoding (cp1252).** Force UTF-8 in subprocess env to avoid `UnicodeEncodeError` on characters like `✓`:
```python
env = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"}
result = subprocess.run([sys.executable, str(script)], env=env,
                        capture_output=True, text=True, encoding="utf-8")
```

**CRLF vs LF byte comparisons.** Git `autocrlf` converts line endings on Windows checkout. Normalize before byte-comparing:
```python
def _norm(p): return p.read_bytes().replace(b"\r\n", b"\n")
```

**Symlinks and execute bits.** `os.symlink()` and `os.chmod(..., 0o755)` require Developer Mode on Windows CI. Skip tests that rely on them:
```python
@unittest.skipIf(sys.platform == "win32", "symlinks require Developer Mode on Windows")
```

**Root-path detection.** `str(path) == "/"` is always `False` on Windows. Use `normalised == normalised.parent`.

**`file://` URLs.** `f"file://{path.as_posix()}"` produces `file://C:/path` (broken on Windows). Use `path.as_uri()` → `file:///C:/path`.

## Gate G — release impact

Changes under `packages/agentbundle/agentbundle/` trigger Gate G. PR must have all three:
1. Version bump in `version.py` and `pyproject.toml`.
2. Changelog entry in `CHANGELOG.md`.
3. `Engine-Change-RFC:` trailer.

**Version collision on rebase.** If main bumped while your branch was open, resolve to `<main-version> + 0.0.1` (e.g. main at `0.21.0` → use `0.21.1`). In rebase conflicts `HEAD` = main — take its version, increment patch.

## SAST (Semgrep) false-positives

`dangerous-subprocess-use-tainted-env-args` fires on `subprocess.run` even with `shell=False`. Prefer the library API (`zipapp.create_archive` over `python -m zipapp`). If `# nosemgrep` is needed, place it on the line Semgrep anchors to — for multi-line calls that's the first argument-list line, not `subprocess.run(`.
