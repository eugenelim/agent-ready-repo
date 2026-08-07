# RFC-0082 spike notes: enforcement-tool trials

Audit trail for the D5 decision in
[RFC-0082](../0082-engine-export-boundary-and-test-inclusion.md). The RFC body
carries the conclusion; this file carries the runs behind it, because D5's
recommendation rests on two candidate tools behaving differently from how they
are usually described.

**Environment.** `agentbundle` 0.29.8, `build` 1.5.0, setuptools 83.0.0,
`check-wheel-contents` 0.6.3, `pydistcheck` 0.11.3, CPython 3.13,
macOS. Both artifacts were built from a copy of `packages/agentbundle` with
`__pycache__`, `*.pyc`, `*.egg-info`, and `.pytest_cache` excluded, so the
measurements are not polluted by local build state. Nothing was written into the
repository working tree.

## Baseline — what the artifacts actually contain

```
WHEEL: 184 entries; 45 test-ish
   agentbundle/build/tests/__init__.py
   agentbundle/build/tests/test_adapter_claude_code.py
   ... (45 total)
   wheel-root test dirs: ['agentbundle']          <- nested, NOT at the root

SDIST: 218 entries; 55 test-ish
   agentbundle-0.29.8/agentbundle/build/tests/**  (the .py modules)
   agentbundle-0.29.8/tests/test_adapter_permissions_projection.py
   agentbundle-0.29.8/tests/test_linear_primitive.py
   agentbundle-0.29.8/tests/test_workspace_mcp_elicit.py
   agentbundle-0.29.8/tests/test_workspace_mcp_event_bridge.py
   agentbundle-0.29.8/tests/test_workspace_mcp_git.py
   agentbundle-0.29.8/tests/test_workspace_mcp_lifecycle.py
   agentbundle-0.29.8/tests/test_workspace_mcp_stdin.py
   agentbundle-0.29.8/tests/test_workspace_mcp_tools.py
   conftest entries: NONE
   tests/unit present: False
```

The in-package tree holds 46 `.py` files alongside 21 non-`.py` fixtures (5
JSON, 8 Markdown, 7 TOML, 1 shell). Only the `.py` files appear in either
artifact, because `[tool.setuptools.package-data]` grafts just `_data/` (two patterns) and
`build/recipes/`. That is the second, independent reason the shipped tests
cannot run — distinct from the missing `conftest.py`.

## `check-wheel-contents` — does not detect this defect

```
$ check-wheel-contents dist/agentbundle-0.29.8-py3-none-any.whl
agentbundle-0.29.8-py3-none-any.whl: W004: Module is not located at importable path:
  agentbundle/_data/install-marker.py
exit=1
```

It exits non-zero, but on an unrelated finding. Nothing is reported about the 45
test entries.

The reason is in the tool's own source. The test-name check is **W005**
("Wheel contains common toplevel name in library"), not W002 ("Wheel contains
duplicate files") as this defect is often described. W005 draws on:

```python
COMMON_NAMES = set(
    """
    .eggs .nox .tox .venv
    app build cli data dist doc docs example examples lib scripts src test
    tests venv
""".split()
)
```

`test` and `tests` are both present — but W005 applies at the *library toplevel*.
This repository's tree is nested at `agentbundle/build/tests/`, so no check
matches it. Adopting the tool would also require first resolving the pre-existing
W004.

## `pydistcheck` — works, but only with the right flag

Default run on the sdist:

```
$ pydistcheck dist/agentbundle-0.29.8.tar.gz
errors found while checking: 0
exit=0
```

Directory-pattern negation against the wheel — **silently passes**:

```
$ pydistcheck --expected-directories '!*tests*' dist/agentbundle-0.29.8-py3-none-any.whl
errors found while checking: 0
exit=0
```

The cause is visible under `--inspect`:

```
$ pydistcheck --inspect dist/agentbundle-0.29.8-py3-none-any.whl
file size
  * compressed size: 0.673M
  * uncompressed size: 2.292M
  * directories: 0                       <- nothing for a directory pattern to match
size by extension
  * (95.578K) agentbundle/build/tests/test_self_host_check.py
```

setuptools-built wheels carry no explicit directory entries in the zip, so
every directory-based pattern has an empty set to work against. The check
reports success while the property it guards is violated, and `--inspect` names
a file from the very tree the pattern was meant to catch.

File-pattern negation against the same wheel — **works**:

```
$ pydistcheck --expected-files '!*/tests/*' dist/agentbundle-0.29.8-py3-none-any.whl
44. [unexpected-files] Found unexpected file 'agentbundle/build/tests/test_workspace_status_projection.py'.
45. [unexpected-files] Found unexpected file 'agentbundle/build/tests/test_writers_emit_lf.py'.
errors found while checking: 45
exit=1
```

Positive assertion against the sdist — correctly fails when the tree is absent:

```
$ pydistcheck --expected-directories '*/tests/unit' dist/agentbundle-0.29.8.tar.gz
1. [expected-files] Did not find any directories matching pattern '*/tests/unit'.
errors found while checking: 1
exit=1
```

(Directory patterns *do* work against sdists, because tar archives carry
directory members. The asymmetry is between archive formats, not between
pattern kinds.)

## What this decided

D5 recommends an in-repo pure-stdlib gate over either tool. `check-wheel-contents`
does not fire on the actual defect. `pydistcheck` can, but only via
`--expected-files`; the more natural-reading `--expected-directories` form passes
while broken, and nothing in the tool's documentation flags that distinction. A
gate whose correct configuration is one undocumented flag away from a false green
is a poor foundation for a rule this RFC wants to be structural.

The `pydistcheck` behaviour is a property of the tool plus the wheel format, not
a bug report against it — the tool is doing what it says with the input it is
given.
