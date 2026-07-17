"""Package entry point so ``python -m flow_metrics`` works.

The CLI itself lives in :mod:`flow_metrics` (``__init__.py``); this file
only forwards ``sys.argv``-equivalents to :func:`flow_metrics.main` so
the documented invocation in ``SKILL.md`` is runnable from a working
copy of this pack. A packaged install can also expose a ``flow-metrics``
console-script shim that calls the same ``main`` function — both forms
produce identical behaviour.

Note: importing this module triggers ``__init__.py``'s top-level
``_check_python_version()`` guard, so on a sub-3.10 interpreter the
process exits 2 *before* reaching the ``sys.exit(main())`` line below.
That's correct behaviour (Python-version errors should surface before
argparse) but it means failures appear to come from the import, not
from ``main``.
"""
from __future__ import annotations

import sys

from . import main


if __name__ == "__main__":
    sys.exit(main())
