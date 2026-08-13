"""Offline cold-read navigation tests for bundled contracts."""

from __future__ import annotations

import socket
from pathlib import Path

import pytest
from agentbundle.catalogue_tooling.contracts_inspector import (
    export_contracts,
    list_bundled_contracts,
    show_contract,
)


def test_all_listed_contracts_can_be_shown_without_network(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """List, show, and export every contract without constructing a socket."""

    def no_socket(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("socket constructed during offline contract navigation")

    monkeypatch.setattr(socket, "socket", no_socket)
    contracts = list_bundled_contracts()
    assert contracts
    for contract in contracts:
        content = show_contract(contract.name)
        assert content is not None
        assert content
    assert export_contracts(tmp_path / "offline-export") == [
        contract.file for contract in contracts
    ]


def test_exported_bytes_match_shown_content_and_create_no_links(
    tmp_path: Path,
) -> None:
    output = tmp_path / "contracts"
    written = export_contracts(output)
    contracts = list_bundled_contracts()
    assert written == [contract.file for contract in contracts]
    for contract in contracts:
        shown = show_contract(contract.name)
        assert shown is not None
        destination = output / contract.file
        assert destination.read_bytes() == shown.encode("utf-8")
        assert not destination.is_symlink()
