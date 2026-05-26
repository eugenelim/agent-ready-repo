"""Conforming credentialed-CLI fixture: no argv flags, no dotfile reads."""
from __future__ import annotations
from .credentials_shim import load_credentials  # AC25 fixture stub


import argparse


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--namespace", required=True)
    parser.parse_args()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
