"""Packaged contract resources are present and parseable.

Published-mirror parity is a repository-tools concern covered from ``tools/``.
"""

from __future__ import annotations

import json
import tomllib
from importlib.resources import files
from typing import Callable

import pytest


@pytest.mark.parametrize(
    ("name", "loader"),
    [
        ("guide.schema.json", json.loads),
        ("skill.schema.json", json.loads),
        ("skill-manifest.schema.json", json.loads),
        ("target-vocab.toml", tomllib.loads),
    ],
)
def test_packaged_contract_resource_is_parseable(
    name: str,
    loader: Callable[[str], object],
) -> None:
    text = files("agentbundle").joinpath(f"_data/{name}").read_text(encoding="utf-8")
    assert loader(text)
