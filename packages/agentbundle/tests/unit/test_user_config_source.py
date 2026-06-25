"""T2: the user `[settings].source` config key — RFC-0046 / ADR-0036.

Covers the write/read/unset round-trip, the read-back that layer 2 consumes,
the parseable-only write validation (no scheme gate at write time), the
`config get source` provenance, and independent fail-soft (a malformed
`source` does not drop a valid `adapter`).
"""

from __future__ import annotations

import pytest

from agentbundle.commands.config import _effective_value
from agentbundle.scope import shipped_adapters_from_contract
from agentbundle.source_defaults import resolve_default_source
from agentbundle.user_config import (
    UserConfig,
    _KNOWN_KEYS,
    read_user_config,
    unset_setting,
    write_setting,
)


def test_source_is_a_known_key():
    assert "source" in _KNOWN_KEYS


def test_write_read_unset_round_trip(tmp_path):
    p = tmp_path / "config.toml"
    write_setting(p, "source", "git+https://github.com/x/y")
    assert read_user_config(p).source == "git+https://github.com/x/y"
    unset_setting(p, "source")
    assert read_user_config(p).source is None


def test_read_back_is_consumed_as_layer_2(tmp_path):
    # The load-bearing invariant: a value written by `config set source` is
    # parsed back onto UserConfig.source AND consumed by resolve_default_source.
    p = tmp_path / "config.toml"
    write_setting(p, "source", "git+https://github.com/x/y")
    cfg = read_user_config(p)
    out = resolve_default_source(
        None, config_source=cfg.source, dist=None, read_packaged=lambda: None
    )
    assert out == "git+https://github.com/x/y"


def test_write_validation_is_parseable_only(tmp_path):
    p = tmp_path / "config.toml"
    # Empty / whitespace is refused at write time.
    with pytest.raises(ValueError):
        write_setting(p, "source", "  ")
    # A non-git+https URL is accepted-but-inert (the scheme gate is at
    # resolution, not at write time) — it must persist.
    write_setting(p, "source", "http://accepted-but-inert")
    assert read_user_config(p).source == "http://accepted-but-inert"


def test_effective_value_provenance(tmp_path):
    assert _effective_value("source", UserConfig(source="git+https://github.com/x/y")) == (
        "git+https://github.com/x/y",
        "file",
    )
    assert _effective_value("source", UserConfig()) == ("", "unset")


def test_source_and_adapter_are_independent_failsoft(tmp_path):
    # A non-string `source` is dropped (warned) without dropping a valid adapter.
    adapter = sorted(shipped_adapters_from_contract())[0]
    p = tmp_path / "config.toml"
    p.write_text(f'[settings]\nadapter = "{adapter}"\nsource = 42\n', encoding="utf-8")
    cfg = read_user_config(p)
    assert cfg.adapter == adapter
    assert cfg.source is None


def test_adapter_round_trip_unaffected(tmp_path):
    # Regression: adding `source` did not break the existing adapter path.
    adapter = sorted(shipped_adapters_from_contract())[0]
    p = tmp_path / "config.toml"
    write_setting(p, "adapter", adapter)
    assert read_user_config(p).adapter == adapter
