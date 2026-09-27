"""Package entry point so ``python -m jira_epic_outcome_view`` works.

The CLI lives in ``__init__.py``; this file only forwards the process's
exit status, so the invocation documented in ``SKILL.md`` runs from a
working copy of this pack.
"""
from __future__ import annotations

import sys

from . import main

if __name__ == "__main__":
    sys.exit(main())
