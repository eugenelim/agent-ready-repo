"""Version constants — CLI version and spec version both pinned at import time.

Spec version is parsed from the bundled canonical `adapter.toml` once, at
module import; mutating the on-disk file after import has no effect on
`SPEC_VERSION`. This pins the contract version the running CLI ships against
to the value present when the process started — which is the value users see
in `agentbundle --version` and the value every pack-version-mismatch refusal
cites.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

CLI_VERSION = "0.1.0"

_HERE = Path(__file__).resolve().parent


def _bundled_adapter_toml() -> Path:
    """Locate the canonical adapter.toml.

    Order:
      1. `agentbundle/_data/adapter.toml` — bundled inside the package (works
         in `zipapp` and `pip install`).
      2. `<repo>/docs/contracts/adapter.toml` — dev checkout fallback when
         the package hasn't been built / copied yet.

    The Makefile's `zipapp` target copies (1) before building.
    """
    bundled = _HERE / "_data" / "adapter.toml"
    if bundled.exists():
        return bundled
    # Dev fallback: walk up to repo root.
    candidate = _HERE.parent.parent.parent / "docs" / "contracts" / "adapter.toml"
    return candidate


def _read_spec_version() -> str:
    path = _bundled_adapter_toml()
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    return data["contract"]["version"]


SPEC_VERSION: str = _read_spec_version()
