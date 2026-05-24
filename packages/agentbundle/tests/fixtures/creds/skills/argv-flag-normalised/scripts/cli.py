"""argv-flag-normalised: every AC27 obfuscation path the lint must defeat.

The lint normalises the flag name (strip leading ``-``, casefold, ``-``
→ ``_``) and compares against the banned set. Each ``add_argument`` call
below resolves to a banned name after normalisation; T10 must flag all
three.
"""
from __future__ import annotations

import argparse


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--Token")              # casing variant → "token"
    parser.add_argument("--api-Key")            # kebab + casing → "api_key"
    parser.add_argument("--" + "password")      # BinOp(Add) → "password"
    parser.parse_args()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
