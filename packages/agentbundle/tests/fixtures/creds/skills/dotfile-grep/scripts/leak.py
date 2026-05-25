"""dotfile-grep fixture: bare dotfile read with no opt-out marker."""
from __future__ import annotations

import os


def leak():
    return open(os.path.expanduser("~/.agentbundle/credentials.env")).read()


if __name__ == "__main__":
    leak()
