"""dotfile-with-optout fixture: opt-out marker on the same line keeps lint silent."""
from __future__ import annotations

from pathlib import Path


def read():
    path = Path("~/.agentbundle/credentials.env").expanduser()  # credentialed-primitive: reads-creds-directly  # noqa: E501
    return path.open(encoding="utf-8").read()


if __name__ == "__main__":
    read()
