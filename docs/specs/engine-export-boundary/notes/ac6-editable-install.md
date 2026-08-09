# AC6 — editable install after the relocation

Closes AC6 of [`../spec.md`](../spec.md). The plan declares this goal-based, so
the artifact is the recorded transcript rather than a test file: the check is
that the *real* install path still works, and a unit test asserting the same
thing from inside the repo would not exercise it.

Run 2026-08-08 against the committed tree, into a throwaway venv:

```
$ python3 -m venv /tmp/ac6venv
$ /tmp/ac6venv/bin/pip install -e packages/agentbundle
  (exit 0)

$ /tmp/ac6venv/bin/python -c "import agentbundle, agentbundle.build; print(agentbundle.__file__)"
  import ok: packages/agentbundle/agentbundle/__init__.py

$ /tmp/ac6venv/bin/agentbundle --version
  agentbundle 0.30.0 (spec 0.17)

$ /tmp/ac6venv/bin/python -c "import agentbundle.build.tests"
  ModuleNotFoundError: No module named 'agentbundle.build.tests'
```

All four AC6 clauses hold: the editable install succeeds, both package imports
resolve, the console script reports the bumped version, and the one name the
relocation removes no longer resolves — which is the point rather than a
side-effect.

**Why it was never at risk.** Editable install is driven by
`[tool.setuptools.packages.find] include = ["agentbundle*"]`, which resolves the
*package* directory. A sibling `tests/` tree is outside its reach. This is
already how `packages/credbroker/` installs, and it is the reason the relocation
needed no packaging change at all — only the tree had to move.
