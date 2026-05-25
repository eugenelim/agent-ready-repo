"""Enable ``python -m ai_adoption_report``.

Thin shim that delegates to :func:`ai_adoption_report.main` so the
package is invocable both as ``python -m`` (the form the spec's
smoke-test examples use) and via the installed console script.
"""
from __future__ import annotations

import sys

from . import main


if __name__ == "__main__":
    sys.exit(main())
