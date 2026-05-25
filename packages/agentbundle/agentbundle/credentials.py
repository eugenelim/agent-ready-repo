"""Public surface for credentialed-primitive authors.

Per spec § AC3, this is the **only** import root primitive authors are
expected to touch:

    from agentbundle.credentials import load_credentials

Re-exports the loader surface from ``agentbundle.creds.loader`` /
``agentbundle.creds.exceptions``. Adding a new public name here is an
ADR-level decision — keep the surface narrow.
"""

from __future__ import annotations

from agentbundle.creds.exceptions import (
    CredentialsMissingError,
    Tier2HardFailError,
)
from agentbundle.creds.loader import Credentials, load_credentials

__all__ = [
    "Credentials",
    "CredentialsMissingError",
    "Tier2HardFailError",
    "load_credentials",
]
