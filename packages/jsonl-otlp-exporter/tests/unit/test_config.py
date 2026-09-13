"""T2 — configuration resolution and the off-by-default proof.

Covers AC-0001, AC-0002, AC-0003, AC-0004, AC-0033, AC-0056, AC-0060, AC-0062.

Every case here runs with no network. The `_ExplodingTransport` seam is the
off-by-default proof: it raises if it is ever constructed, so "nothing was sent"
is asserted by construction rather than by trusting that no socket appeared.
"""

from __future__ import annotations

import os
import stat
import pytest

from jsonl_otlp_exporter import config as cfg


class _ExplodingTransport:
    """Constructing this is the failure. AC-0001 has no other observable here."""

    def __init__(self, *args, **kwargs):  # pragma: no cover - must never run
        raise AssertionError("a transport was constructed with no endpoint configured")


def _write(path, text: str):
    path.write_text(text, encoding="utf-8")
    return path


class TestEndpointPrecedence:
    """AC-0002 — first present of LOGS_ENDPOINT, ENDPOINT, then the config file."""

    def test_logs_endpoint_wins_over_both_others(self, tmp_path):
        config = _write(tmp_path / "c.toml", '[telemetry]\nendpoint = "https://file:4318"\n')
        resolved = cfg.resolve_endpoint(
            {
                "OTEL_EXPORTER_OTLP_LOGS_ENDPOINT": "https://logs:4318/v1/logs",
                "OTEL_EXPORTER_OTLP_ENDPOINT": "https://base:4318",
            },
            config_path=config,
        )
        assert resolved == "https://logs:4318/v1/logs"

    def test_base_endpoint_wins_over_the_config_file(self, tmp_path):
        config = _write(tmp_path / "c.toml", '[telemetry]\nendpoint = "https://file:4318"\n')
        resolved = cfg.resolve_endpoint(
            {"OTEL_EXPORTER_OTLP_ENDPOINT": "https://base:4318"}, config_path=config
        )
        assert resolved == "https://base:4318/v1/logs"

    def test_config_file_is_used_when_no_variable_is_present(self, tmp_path):
        config = _write(tmp_path / "c.toml", '[telemetry]\nendpoint = "https://file:4318"\n')
        assert cfg.resolve_endpoint({}, config_path=config) == "https://file:4318/v1/logs"

    def test_an_empty_variable_is_not_present(self, tmp_path):
        """An exported-but-empty variable must not shadow the next source.

        This is the case a truthiness check gets right and a `in env` check gets
        wrong, and it is how a shell export of an unset value silently disables
        a configured endpoint.
        """
        config = _write(tmp_path / "c.toml", '[telemetry]\nendpoint = "https://file:4318"\n')
        resolved = cfg.resolve_endpoint(
            {"OTEL_EXPORTER_OTLP_LOGS_ENDPOINT": "", "OTEL_EXPORTER_OTLP_ENDPOINT": ""},
            config_path=config,
        )
        assert resolved == "https://file:4318/v1/logs"


class TestEndpointTransformation:
    """AC-0003 — the logs variable is unmodified. AC-0004 — everything else gains /v1/logs."""

    def test_logs_endpoint_is_requested_unmodified(self):
        # Deliberately NOT already ending in /v1/logs: a build that appends
        # unconditionally, and one that appends only when absent, both fail here.
        resolved = cfg.resolve_endpoint(
            {"OTEL_EXPORTER_OTLP_LOGS_ENDPOINT": "https://logs:4318/custom/path"},
            config_path=None,
        )
        assert resolved == "https://logs:4318/custom/path"

    def test_base_endpoint_gains_the_signal_path(self):
        resolved = cfg.resolve_endpoint(
            {"OTEL_EXPORTER_OTLP_ENDPOINT": "https://base:4318"}, config_path=None
        )
        assert resolved == "https://base:4318/v1/logs"

    def test_a_trailing_slash_does_not_double(self):
        resolved = cfg.resolve_endpoint(
            {"OTEL_EXPORTER_OTLP_ENDPOINT": "https://base:4318/"}, config_path=None
        )
        assert resolved == "https://base:4318/v1/logs"


class TestOffByDefault:
    """AC-0001, AC-0033, AC-0060 — nothing configured means nothing happens, loudly enough."""

    def test_no_source_resolves_to_nothing(self):
        assert cfg.resolve_endpoint({}, config_path=None) is None

    def test_unconfigured_run_constructs_no_transport_and_reports_zero(self, capsys):
        status = cfg.run_unconfigured_check(
            {}, config_path=None, transport_factory=_ExplodingTransport
        )
        assert status == 0
        assert "no endpoint is configured" in capsys.readouterr().err

    def test_the_note_goes_to_stderr_not_stdout(self, capsys):
        """stdout is reserved for a machine consumer; a note there would corrupt it."""
        cfg.run_unconfigured_check({}, config_path=None, transport_factory=_ExplodingTransport)
        captured = capsys.readouterr()
        assert captured.out == ""
        assert captured.err.strip() != ""


class TestConfigFileAcquisition:
    """AC-0056 — the size ceiling. AC-0062 — what is opened, proven on the descriptor."""

    def test_a_file_over_64_kib_is_refused_before_parsing(self, tmp_path):
        # Valid TOML, so only the size check can reject it. A build that parses
        # first and measures afterwards passes a size check and fails this.
        padding = "#" + "x" * (64 * 1024)
        config = _write(tmp_path / "big.toml", f'[telemetry]\nendpoint = "https://c:4318"\n{padding}\n')
        assert config.stat().st_size > cfg.MAX_CONFIG_BYTES
        with pytest.raises(cfg.ConfigRefused):
            cfg.read_config_file(config)

    def test_a_file_at_exactly_the_ceiling_is_accepted(self, tmp_path):
        """The boundary belongs to the accepted side; an off-by-one rejects a legal file."""
        head = '[telemetry]\nendpoint = "https://c:4318"\n#'
        config = _write(tmp_path / "exact.toml", head + "x" * (cfg.MAX_CONFIG_BYTES - len(head)))
        assert config.stat().st_size == cfg.MAX_CONFIG_BYTES
        assert cfg.read_config_file(config)["telemetry"]["endpoint"] == "https://c:4318"

    def test_a_symlink_is_refused(self, tmp_path):
        real = _write(tmp_path / "real.toml", '[telemetry]\nendpoint = "https://c:4318"\n')
        link = tmp_path / "link.toml"
        try:
            link.symlink_to(real)
        except OSError:  # Windows without developer mode
            pytest.skip("symlinks unavailable on this platform")
        with pytest.raises(cfg.ConfigRefused):
            cfg.read_config_file(link)

    def test_a_fifo_is_refused(self, tmp_path):
        if not hasattr(os, "mkfifo"):  # Windows has no FIFO
            pytest.skip("FIFOs unavailable on this platform")
        fifo = tmp_path / "fifo.toml"
        os.mkfifo(fifo)
        assert stat.S_ISFIFO(os.lstat(fifo).st_mode)
        with pytest.raises(cfg.ConfigRefused):
            cfg.read_config_file(fifo)

    def test_a_directory_is_refused(self, tmp_path):
        d = tmp_path / "dir.toml"
        d.mkdir()
        with pytest.raises(cfg.ConfigRefused):
            cfg.read_config_file(d)

    def test_a_regular_file_outside_any_root_is_accepted(self, tmp_path):
        """AC-0062 imposes no --root confinement, and this is the case that proves it.

        A build that reuses --input's confined-open predicate passes every
        refusal case above and fails here, which is the whole point of the split.
        """
        elsewhere = tmp_path / "elsewhere"
        elsewhere.mkdir()
        outside = _write(elsewhere / "c.toml", '[telemetry]\nendpoint = "https://c:4318"\n')
        assert cfg.read_config_file(outside)["telemetry"]["endpoint"] == "https://c:4318"

    def test_an_absent_config_path_is_not_a_refusal(self, tmp_path):
        """`--config` is optional: absent means "this source contributes nothing"."""
        assert cfg.read_config_file(tmp_path / "missing.toml") == {}

    def test_unparseable_toml_is_refused(self, tmp_path):
        config = _write(tmp_path / "bad.toml", "[telemetry\nendpoint =\n")
        with pytest.raises(cfg.ConfigRefused):
            cfg.read_config_file(config)


class TestTransportSeamIsReal:
    """The exploding-factory assertion only means something if some branch reaches it."""

    def test_a_resolved_endpoint_does_construct_the_transport(self):
        built = []
        status = cfg.run_unconfigured_check(
            {"OTEL_EXPORTER_OTLP_ENDPOINT": "https://base:4318"},
            config_path=None,
            transport_factory=lambda endpoint: built.append(endpoint),
        )
        assert status is None, "a configured run is not this function's case"
        assert built == ["https://base:4318/v1/logs"]
