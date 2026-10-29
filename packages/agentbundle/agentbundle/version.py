"""Version constants — CLI version and spec version both pinned at import time.

Spec version is parsed from the bundled canonical `adapter.toml` once, at
module import; mutating the on-disk file after import has no effect on
`SPEC_VERSION`. This pins the contract version the running CLI ships against
to the value present when the process started — which is the value users see
in `agentbundle --version` and the value every pack-version-mismatch refusal
cites.
"""

from __future__ import annotations

import json
import re
import tomllib
from importlib.resources import files

CLI_VERSION = "0.59.0"


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


_INVENTORY = "catalogue-members.txt"
_ID_VERSION = re.compile(r"^https://[^/]+/(?:.+/)?docs/spec/catalogue/(\d+\.\d+)/([^/]+)$")


def _read_bundled_text(name: str) -> str:
    """Read `_data/<name>` through `importlib.resources`, naming it on failure."""
    resource = files("agentbundle").joinpath(f"_data/{name}")
    try:
        if not resource.is_file():
            raise FileNotFoundError(f"bundled contract missing: _data/{name}")
        return resource.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        if isinstance(exc, FileNotFoundError):
            raise
        raise ValueError(f"bundled contract unreadable: _data/{name}: {exc}") from exc


def _member_version(name: str) -> str:
    """Return the catalogue specification version in a member's `$id`."""
    try:
        document = json.loads(_read_bundled_text(name))
    except json.JSONDecodeError as exc:
        raise ValueError(f"bundled contract unreadable: _data/{name}: {exc}") from exc
    identifier = document.get("$id") if isinstance(document, dict) else None
    match = _ID_VERSION.match(identifier) if isinstance(identifier, str) else None
    if match is None or match.group(2) != name:
        raise ValueError(f"bundled contract has no usable $id: _data/{name}")
    return match.group(1)


def catalogue_spec_version() -> str:
    """Return the catalogue specification version the bundled members carry.

    Computed on each call, never at import, so a malformed bundled copy fails
    only the reports that ask for it. Fails closed with `ValueError` or
    `FileNotFoundError` naming the offending `_data/` file.
    """
    try:
        inventory = _read_bundled_text(_INVENTORY)
    except (OSError, ValueError) as exc:
        raise ValueError(f"bundled inventory unusable: _data/{_INVENTORY}: {exc}") from exc
    names = [line.strip() for line in inventory.splitlines() if line.strip()]
    if not names:
        raise ValueError(f"bundled inventory empty: _data/{_INVENTORY}")
    versions = {_member_version(name) for name in names}
    if len(versions) != 1:
        raise ValueError(
            f"bundled contracts disagree on the version: _data/{_INVENTORY}: "
            f"{sorted(versions)}"
        )
    return versions.pop()
