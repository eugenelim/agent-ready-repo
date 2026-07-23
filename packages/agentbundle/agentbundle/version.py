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
from importlib.resources import files
from pathlib import Path

CLI_VERSION = "0.12.1"

_HERE = Path(__file__).resolve().parent


def _read_bundled_adapter_toml_text() -> str:
    """Read the canonical adapter.toml as text.

    Resolution:
      1. `agentbundle._data/adapter.toml` via `importlib.resources` —
         works inside a `zipapp`, a `pip install`, and a dev checkout
         that has `_data/` populated.
      2. `<repo>/docs/contracts/adapter.toml` — dev-checkout fallback
         for the (rare) case where `_data/` is missing in the source
         tree (mostly during initial scaffolding).
    """
    try:
        resource = files("agentbundle").joinpath("_data/adapter.toml")
        if resource.is_file():
            return resource.read_text(encoding="utf-8")
    except (FileNotFoundError, ModuleNotFoundError):
        pass

    fallback = _HERE.parent.parent.parent / "docs" / "contracts" / "adapter.toml"
    return fallback.read_text(encoding="utf-8")


def _read_spec_version() -> str:
    data = tomllib.loads(_read_bundled_adapter_toml_text())
    return data["contract"]["version"]


SPEC_VERSION: str = _read_spec_version()
