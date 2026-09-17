"""Report where a package resolved, under whatever pytest config actually won.

Loaded with `-p` into a child pytest run by
`tests/roster/test_package_pytest_pythonpath.py`. `pytest_configure` fires after
the configfile has been chosen and its `pythonpath` applied, so the import below
sees exactly the `sys.path` the real suite sees. Printing the answer beats
reasoning about it: the parent then needs no model of configfile precedence,
entry order, or module suffixes.

The verdict goes to a file named by the environment rather than to stdout, so
the parent does not have to pick it out of pytest's own collection output, and
an absent file is unambiguous evidence that this plugin never ran.

Not a test module and not collected -- the filename does not match `test_*.py`.
The parent imports nothing from here; `tests/` holds two different `fixtures`
directories, and a cross-directory import would bind to whichever landed on
`sys.path` first.
"""

from __future__ import annotations

import json
import os
from pathlib import Path


def pytest_configure(config: object) -> None:
    """Import the package under test and record where it came from."""
    del config
    name = os.environ["PYTEST_RESOLUTION_PROBE_IMPORT"]
    try:
        module = __import__(name)
    except BaseException as exc:  # noqa: BLE001 - the failure IS the finding
        payload = {"state": "unimportable", "detail": f"{type(exc).__name__}: {exc}"}
    else:
        payload = {"state": "resolved", "path": getattr(module, "__file__", None)}
    destination = Path(os.environ["PYTEST_RESOLUTION_PROBE_OUTPUT"])
    destination.write_text(json.dumps(payload), encoding="utf-8")
