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

CLI_VERSION = "0.55.0"


def _read_bundled_adapter_toml_text() -> str:
    """Read the bundled adapter.toml as text.

    Reads `agentbundle/_data/adapter.toml` through `importlib.resources`,
    which works in a `pip install`, a `zipapp` and an editable install.
    A missing copy raises `FileNotFoundError` naming it; no other source
    is tried.
    """
    resource = files("agentbundle").joinpath("_data/adapter.toml")
    if not resource.is_file():
        raise FileNotFoundError("bundled contract missing: _data/adapter.toml")
    return resource.read_text(encoding="utf-8")


def _read_spec_version() -> str:
    try:
        data = tomllib.loads(_read_bundled_adapter_toml_text())
    except (UnicodeDecodeError, tomllib.TOMLDecodeError) as exc:
        raise ValueError(f"bundled contract unreadable: _data/adapter.toml: {exc}") from exc
    return data["contract"]["version"]


SPEC_VERSION: str = _read_spec_version()
