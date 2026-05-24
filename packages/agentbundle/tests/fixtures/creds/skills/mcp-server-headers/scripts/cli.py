"""mcp-server-headers: header-naming flags are allowed for this class."""
from __future__ import annotations

import argparse


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bearer-header", default="Authorization")
    parser.add_argument("--auth-header", default=None)
    parser.add_argument("--header-prefix", default="Bearer ")
    parser.parse_args()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
