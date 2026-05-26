"""dotfile-with-optout fixture: opt-out marker on the same line keeps lint silent."""
from __future__ import annotations
from .credentials_shim import load_credentials  # AC25 fixture stub


import os


def read():
    path = os.path.expanduser("~/.agentbundle/credentials.env")  # credentialed-primitive: reads-creds-directly
    return open(path).read()


if __name__ == "__main__":
    read()
