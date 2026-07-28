"""dotfile-grep fixture: bare dotfile read with no opt-out marker."""
from __future__ import annotations

from pathlib import Path


def leak():
    return Path("~/.agentbundle/credentials.env").expanduser().open(encoding="utf-8").read()


if __name__ == "__main__":
    leak()
