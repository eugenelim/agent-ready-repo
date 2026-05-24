"""argv-flag-derived: round-2 lint widening fixtures.

Three obfuscation shapes the original walker missed; each is still
literal-derivable at parse time so the widened walker MUST flag them:

  - ``JoinedStr``  — f-string with literal-only parts.
  - ``Starred(Tuple)`` argument spread.
  - ``Subscript`` constant indexing into a literal tuple.
"""
from __future__ import annotations

import argparse


def main() -> int:
    parser = argparse.ArgumentParser()
    # JoinedStr with a literal-only FormattedValue.
    parser.add_argument(f"--{'token'}")
    # Starred(Tuple) argument spread.
    parser.add_argument(*("--api-key",))
    # Subscript constant indexing on a literal tuple.
    parser.add_argument(("--bearer",)[0])
    parser.parse_args()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
