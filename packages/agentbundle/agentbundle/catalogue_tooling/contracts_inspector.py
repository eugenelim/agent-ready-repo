"""Read and export the public contracts bundled with AgentBundle."""

from __future__ import annotations

from dataclasses import dataclass
from importlib.resources import files as resource_files
from importlib.resources.abc import Traversable
from pathlib import Path

from agentbundle.safety import assert_portable_name, write_files_no_follow

_INVENTORY = "public-contracts.txt"


class ContractResourceError(RuntimeError):
    """A bundled public-contract resource is missing or invalid."""


@dataclass(frozen=True)
class ContractInfo:
    """Metadata for one public bundled contract."""

    name: str
    kind: str
    file: str


def _data_dir() -> Traversable:
    """Return the package-data root without consulting source checkout paths."""
    return resource_files("agentbundle").joinpath("_data")


def _inventory_names() -> list[str]:
    """Read and validate the generated positive-membership inventory."""
    try:
        inventory = _data_dir().joinpath(_INVENTORY).read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise ContractResourceError(
            "bundled contract inventory is unavailable"
        ) from exc
    names = [line for line in inventory.splitlines() if line]
    # An empty inventory means a truncated or mis-built wheel. Without this
    # check `contracts list` prints a bare header and exits 0 — reporting
    # success for an installation that ships no contracts at all.
    if not names:
        raise ContractResourceError("bundled contract inventory is empty")
    if names != sorted(names) or len(names) != len(set(names)):
        raise ContractResourceError("bundled contract inventory is invalid")
    for name in names:
        if (
            name in {".", ".."}
            or "/" in name
            or "\\" in name
            or not name.endswith((".json", ".toml"))
        ):
            raise ContractResourceError("bundled contract inventory is invalid")
        # `assert_portable_name` covers Windows-poisonous names but not
        # control characters; a NUL would otherwise reach
        # `Traversable.joinpath` and surface as an uncaught ValueError.
        if any(character < " " or character == "\x7f" for character in name):
            raise ContractResourceError("bundled contract inventory is invalid")
        try:
            assert_portable_name(name)
        except ValueError as exc:
            raise ContractResourceError(
                "bundled contract inventory is invalid"
            ) from exc
    return names


def _kind(name: str) -> str:
    if name.endswith(".schema.json"):
        return "json-schema"
    if name.endswith(".toml"):
        return "toml"
    return "json"


def list_bundled_contracts() -> list[ContractInfo]:
    """Return ordered metadata for positively inventoried public contracts."""
    return [
        ContractInfo(name=name, kind=_kind(name), file=name)
        for name in _inventory_names()
    ]


def show_contract(name: str) -> str | None:
    """Return one public bundled contract, or ``None`` for an unknown name."""
    if "/" in name or "\\" in name:
        return None
    if name not in {contract.name for contract in list_bundled_contracts()}:
        return None
    try:
        return _data_dir().joinpath(name).read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise ContractResourceError("bundled contract resource is unavailable") from exc


def export_contracts(output_dir: Path) -> list[str]:
    """Export every public bundled contract through the no-follow batch writer."""
    contracts = list_bundled_contracts()
    data = _data_dir()
    try:
        contents = {
            contract.file: data.joinpath(contract.file).read_bytes()
            for contract in contracts
        }
    except OSError as exc:
        raise ContractResourceError("bundled contract resource is unavailable") from exc
    # Report what the writer actually wrote, not what we intended to write —
    # the two can only diverge through a bug, and this way the manifest says so.
    return [path.name for path in write_files_no_follow(output_dir, contents)]
