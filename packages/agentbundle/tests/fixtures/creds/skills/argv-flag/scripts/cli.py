"""argv-flag fixture: the AC26(b) trigger — direct `--token` literal."""
from __future__ import annotations

import argparse


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--token")
    parser.parse_args()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
