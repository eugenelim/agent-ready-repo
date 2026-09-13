"""T4, profile half — form, validation and confined loading.

Covers AC-0007 (the default name), AC-0035, AC-0047, AC-0048, AC-0049, AC-0050,
AC-0051, AC-0052, AC-0067.
"""

from __future__ import annotations

import os
import tomllib
from pathlib import Path

import pytest

from jsonl_otlp_exporter import profile as prof

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def _valid() -> dict:
    return tomllib.loads((FIXTURES / "reference.toml").read_text(encoding="utf-8"))


def _write(path, text):
    path.write_text(text, encoding="utf-8")
    return path


class TestClosedKeySet:
    """AC-0035 — exactly six keys, closed in both directions."""

    def test_the_reference_profile_parses(self):
        parsed = prof.parse_profile(_valid())
        assert parsed.timestamp_field == "at"
        assert parsed.identity == ("run_id", "seq")

    @pytest.mark.parametrize("missing", sorted(prof.REQUIRED_KEYS))
    def test_every_missing_key_is_refused(self, missing):
        raw = _valid()
        del raw[missing]
        with pytest.raises(prof.ProfileRefused):
            prof.parse_profile(raw)

    def test_an_extra_key_is_refused(self):
        """An unknown key would otherwise be ignored -- silently, and wrongly.

        A caller who writes `allow_list` for `allowlist` gets a profile that
        sends nothing rather than one that sends everything, only if extras are
        refused rather than skipped.
        """
        raw = _valid()
        raw["service_name"] = "sneaky"
        with pytest.raises(prof.ProfileRefused):
            prof.parse_profile(raw)


class TestValueTypes:
    """AC-0050 — each of the six values has a required shape."""

    @pytest.mark.parametrize(
        "key,bad",
        [
            ("timestamp_field", 7),
            ("severity_field", ["result"]),
            ("identity", "run_id"),
            ("identity", ["run_id", 7]),
            ("allowlist", {"a": 1}),
            ("severity_map", ["success"]),
        ],
    )
    def test_a_wrong_typed_value_is_refused(self, key, bad):
        raw = _valid()
        raw[key] = bad
        with pytest.raises(prof.ProfileRefused):
            prof.parse_profile(raw)

    def test_a_non_integer_severity_value_is_refused(self):
        raw = _valid()
        raw["severity_map"] = {"success": 9, "failure": "17"}
        with pytest.raises(prof.ProfileRefused):
            prof.parse_profile(raw)

    def test_a_boolean_severity_value_is_refused(self):
        """`bool` is an `int` subclass, so `true` passes a naive isinstance check
        and would be emitted as severity 1."""
        raw = _valid()
        raw["severity_map"] = {"success": True}
        with pytest.raises(prof.ProfileRefused):
            prof.parse_profile(raw)


class TestSeverityRange:
    """AC-0067 — OTLP severity numbers are 1 through 24, and 0 is not 'unknown'."""

    @pytest.mark.parametrize("value", [0, -1, 25, 100])
    def test_a_value_outside_the_range_is_refused(self, value):
        raw = _valid()
        raw["severity_map"] = {"success": value}
        with pytest.raises(prof.ProfileRefused):
            prof.parse_profile(raw)

    @pytest.mark.parametrize("value", [1, 9, 17, 24])
    def test_the_boundaries_and_interior_are_accepted(self, value):
        raw = _valid()
        raw["severity_map"] = {"success": value}
        assert prof.parse_profile(raw).severity_map["success"] == value


class TestTimestampFormatEnum:
    """AC-0049 — a closed enum, so an unknown format is never guessed at."""

    @pytest.mark.parametrize("fmt", sorted(prof.TIMESTAMP_FORMATS))
    def test_each_declared_format_is_accepted(self, fmt):
        raw = _valid()
        raw["timestamp_format"] = fmt
        assert prof.parse_profile(raw).timestamp_format == fmt

    @pytest.mark.parametrize("fmt", ["iso8601", "RFC3339", "unix", ""])
    def test_anything_else_is_refused(self, fmt):
        raw = _valid()
        raw["timestamp_format"] = fmt
        with pytest.raises(prof.ProfileRefused):
            prof.parse_profile(raw)


class TestLoading:
    """AC-0047, AC-0048, AC-0051, AC-0052 — how a profile is acquired."""

    def test_no_profile_is_refused_and_nothing_is_built_in(self):
        with pytest.raises(prof.ProfileRefused):
            prof.load_profile(None)

    def test_a_profile_over_the_ceiling_is_refused(self, tmp_path):
        body = (FIXTURES / "reference.toml").read_text(encoding="utf-8")
        padded = body + "\n#" + "x" * prof.MAX_PROFILE_BYTES
        target = _write(tmp_path / "big.toml", padded)
        assert target.stat().st_size > prof.MAX_PROFILE_BYTES
        with pytest.raises(prof.ProfileRefused):
            prof.load_profile(target, tmp_path)

    def test_unparseable_toml_is_refused(self, tmp_path):
        target = _write(tmp_path / "bad.toml", "timestamp_field = \n[oops")
        with pytest.raises(prof.ProfileRefused):
            prof.load_profile(target, tmp_path)

    def test_a_symlinked_profile_is_refused(self, tmp_path):
        real = _write(tmp_path / "real.toml", (FIXTURES / "reference.toml").read_text(encoding="utf-8"))
        link = tmp_path / "link.toml"
        try:
            link.symlink_to(real)
        except OSError:
            pytest.skip("symlinks unavailable on this platform")
        with pytest.raises(prof.ProfileRefused):
            prof.load_profile(link, tmp_path)

    def test_a_profile_outside_the_root_is_refused(self, tmp_path):
        """AC-0048 confines --profile to --root, unlike --config (AC-0062).

        A profile decides the payload, so it is data this tool acts on rather
        than an operator preference pointed at from anywhere.
        """
        root = tmp_path / "root"
        root.mkdir()
        outside = _write(tmp_path / "outside.toml", (FIXTURES / "reference.toml").read_text(encoding="utf-8"))
        with pytest.raises(prof.ProfileRefused):
            prof.load_profile(outside, root)

    def test_a_profile_is_parsed_as_data_not_imported(self, tmp_path):
        """AC-0047. The file is valid TOML *and* valid Python that would raise.

        If any part of it were imported or evaluated, the marker file would
        exist. It is refused on schema instead, which is the whole point of the
        profile being data.
        """
        marker = tmp_path / "executed.marker"
        hostile = (
            'timestamp_field = "at"\n'
            'timestamp_format = "rfc3339"\n'
            'severity_field = "result"\n'
            'identity = ["run_id"]\n'
            'allowlist = ["x"]\n'
            f'__import__ = "open({str(marker)!r}, \'w\').close()"\n'
            "[severity_map]\nsuccess = 9\n"
        )
        target = _write(tmp_path / "hostile.toml", hostile)
        with pytest.raises(prof.ProfileRefused):
            prof.load_profile(target, tmp_path)
        assert not marker.exists(), "no part of a profile may be evaluated"

    def test_a_valid_profile_inside_the_root_loads(self, tmp_path):
        target = _write(tmp_path / "p.toml", (FIXTURES / "reference.toml").read_text(encoding="utf-8"))
        assert prof.load_profile(target, tmp_path).severity_map == {"success": 9, "failure": 17}


class TestDefaultServiceName:
    """AC-0007 — the default is the --profile filename stem, not a profile key."""

    def test_the_default_is_the_filename_stem(self, tmp_path):
        target = tmp_path / "work-loop.toml"
        assert prof.default_service_name(target) == "work-loop"

    def test_the_default_comes_from_the_name_not_the_contents(self, tmp_path):
        """The stem differs from every value inside the file, so a build that
        reads the default out of the profile's contents fails here."""
        body = (FIXTURES / "reference.toml").read_text(encoding="utf-8")
        target = _write(tmp_path / "chosen-name.toml", body)
        name = prof.default_service_name(target)
        assert name == "chosen-name"
        assert name not in body

    def test_no_profile_key_can_supply_a_name(self):
        """The reason AC-0007 stopped citing the profile: there is no such key."""
        assert "service_name" not in prof.REQUIRED_KEYS
        assert "name" not in prof.REQUIRED_KEYS
