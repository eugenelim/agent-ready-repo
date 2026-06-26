"""TOML-injection hardening: emitter escaping + injection-resistance.

`config.dump_state` and `commands.install._append_install_marker` are the
two CLI write-paths that interpolate pack-sourced strings into TOML
output. Before this hardening, both used plain f-strings, so a manifest
declaring ``version = '0.1.0"\\nname = "evil"'`` could land phantom TOML
structure in `.agentbundle-state.toml` and `.adapt-install-marker.toml`.

The fix is a single `_emit_basic_string` helper that escapes per the
TOML 1.0 basic-string grammar (``\\``, ``"``, and control chars). These
tests pin the contract: every basic-string interpolation must round-trip
through `tomllib` to the original Python string, and no adversarial
value can introduce a sibling table.
"""

from __future__ import annotations

import tomllib

import pytest

from agentbundle import config
from agentbundle.config import PackState, State, dump_state


# ---------------------------------------------------------------------------
# _emit_basic_string — pure-function round-trip
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "raw",
    [
        "hello",
        "",
        'he said "hi"',
        r"path\to\file",
        "trailing-backslash\\",
        "\\\\double-leading-backslash",
        "a\nb\rc\td",
        "form\ffeed",
        "back\bspace",
        "control\x01char",
        "null\x00byte",
        "high\x7fascii",
        "unicode-ok-é-ü-中",
        '"\\\n\r\t\x00\x01\x7f',  # every escape at once
    ],
)
def test_emit_basic_string_round_trips_through_tomllib(raw: str) -> None:
    """Every basic-string position the CLI emits must reparse to the
    original Python string. The helper returns the *quoted* form so
    callers interpolate as ``key = {_emit_basic_string(v)}``."""
    quoted = config._emit_basic_string(raw)
    parsed = tomllib.loads(f"x = {quoted}")
    assert parsed["x"] == raw


def test_emit_basic_string_returns_quoted_form() -> None:
    """Helper returns the full quoted basic-string (opening + closing ``"``),
    not the bare value. Callers do not add their own quotes."""
    assert config._emit_basic_string("hello") == '"hello"'


def test_emit_basic_string_escapes_quote_and_backslash() -> None:
    assert config._emit_basic_string('a"b') == '"a\\"b"'
    assert config._emit_basic_string(r"a\b") == '"a\\\\b"'


# ---------------------------------------------------------------------------
# dump_state — injection-resistance via the helper
# ---------------------------------------------------------------------------


def test_dump_state_resists_pack_version_injection() -> None:
    """Adversarial `installed-version` must not land a phantom sibling
    pack table. Before the fix, the line broke out of the quoted
    basic-string and started a new ``[pack.evil]`` table."""
    adversarial = '0.1.0"\nname = "evil"'
    state = State()
    state.packs[("target", "claude-code")] = PackState(installed_version=adversarial)

    serialised = dump_state(state)
    parsed = tomllib.loads(serialised)

    assert parsed["pack"]["target"]["adapters"]["claude-code"]["installed-version"] == adversarial
    assert "evil" not in parsed["pack"], (
        "phantom [pack.evil] table landed via injection"
    )


def test_dump_state_resists_files_sha_injection() -> None:
    """Adversarial value in the inline-table position (``sha = "..."``)
    must not break out of its basic-string."""
    adversarial = 'cafef00d"\nname = "evil"'
    state = State()
    ps = PackState(installed_version="0.1.0")
    ps.files["AGENTS.md"] = {"sha": adversarial, "from-pack-version": "0.1.0"}
    state.packs[("core", "claude-code")] = ps

    parsed = tomllib.loads(dump_state(state))
    assert parsed["pack"]["core"]["adapters"]["claude-code"]["files"]["AGENTS.md"]["sha"] == adversarial
    assert "evil" not in parsed["pack"]


def test_dump_state_resists_relpath_key_injection() -> None:
    """The files-table key is a TOML quoted key; same escaping applies.
    A relpath that contains a quote must not start a sibling table."""
    adversarial = 'AGENTS.md"\n[pack.evil]\nname = "evil'
    state = State()
    ps = PackState(installed_version="0.1.0")
    ps.files[adversarial] = {"sha": "abc", "from-pack-version": "0.1.0"}
    state.packs[("core", "claude-code")] = ps

    parsed = tomllib.loads(dump_state(state))
    assert adversarial in parsed["pack"]["core"]["adapters"]["claude-code"]["files"]
    assert "evil" not in parsed["pack"]


def test_dump_state_resists_primitive_version_injection() -> None:
    """Mixed-version primitive override path: ``version = "..."`` is
    pack-version-sourced via `from-pack-version`; adversarial values
    must not escape their basic-string."""
    adversarial = '0.3.0"\nname = "evil"'
    state = State()
    ps = PackState(installed_version="0.2.0")
    ps.primitive_versions = {"skill": {"work-loop": adversarial}}
    state.packs[("core", "claude-code")] = ps

    parsed = tomllib.loads(dump_state(state))
    assert parsed["pack"]["core"]["adapters"]["claude-code"]["skill"]["work-loop"]["version"] == adversarial
    assert "evil" not in parsed["pack"]


# ---------------------------------------------------------------------------
# _append_install_marker — injection-resistance via the helper
# ---------------------------------------------------------------------------


def test_install_marker_resists_pack_version_injection(tmp_path) -> None:
    """``_append_install_marker`` is called by the install path with
    `pack_version` lifted straight from `pack_toml["pack"]["version"]`.
    Adversarial values must not land phantom TOML structure in
    ``.adapt-install-marker.toml``."""
    from agentbundle.commands.install import _append_install_marker

    adversarial = '0.1.0"\nname = "evil"'
    _append_install_marker(
        tmp_path,
        "repo",
        pack_name="alpha",
        pack_version=adversarial,
        unresolved_markers=[],
        new_companions=[],
        allowed_prefixes=None,
    )

    marker = tmp_path / ".adapt-install-marker.toml"
    parsed = tomllib.loads(marker.read_text(encoding="utf-8"))

    entries = parsed["packs-installed"]
    assert len(entries) == 1
    assert entries[0]["name"] == "alpha"
    assert entries[0]["version"] == adversarial
    # No phantom top-level keys from the injection.
    assert set(parsed.keys()) == {"marker-schema-version", "packs-installed"}


def test_install_marker_resists_pack_name_injection(tmp_path) -> None:
    """Defense-in-depth: even if the install-time validator missed a
    name, the emitter alone must prevent injection."""
    from agentbundle.commands.install import _append_install_marker

    adversarial = 'evil"\nname = "phantom'
    _append_install_marker(
        tmp_path,
        "repo",
        pack_name=adversarial,
        pack_version="0.1.0",
        unresolved_markers=[],
        new_companions=[],
        allowed_prefixes=None,
    )

    marker = tmp_path / ".adapt-install-marker.toml"
    parsed = tomllib.loads(marker.read_text(encoding="utf-8"))

    assert parsed["packs-installed"][0]["name"] == adversarial
    assert len(parsed["packs-installed"]) == 1


def test_install_marker_resists_prior_installed_at_string_injection(
    tmp_path,
) -> None:
    """A hand-edited or attacker-mediated marker can land
    ``installed-at = "...\\nphantom = ..."`` (basic-string position,
    not bare datetime). ``tomllib`` parses that to a Python ``str``
    with real control chars; bare re-emission would land phantom TOML
    structure on the next install. The fix is to drop any entry whose
    ``installed-at`` isn't a ``datetime`` at read time."""
    from agentbundle.commands.install import _append_install_marker

    # Seed an adversarial prior marker. The basic-string form of
    # `installed-at` is what triggers the round-trip injection class.
    marker = tmp_path / ".adapt-install-marker.toml"
    marker.write_text(
        'marker-schema-version = "0.1"\n'
        "\n"
        "[[packs-installed]]\n"
        'name = "victim"\n'
        'version = "0.1.0"\n'
        # `installed-at` as a *basic-string* (quoted) with a real newline
        # in the value — `tomllib.loads` resolves the escape sequence to a
        # newline byte; without the read-side filter the next emission
        # would land a phantom field.
        'installed-at = "2026-01-01T00:00:00Z\\nphantom = \\"injected\\""\n'
        "unresolved-markers = []\n"
        "new-companions = []\n",
        encoding="utf-8",
    )

    _append_install_marker(
        tmp_path,
        "repo",
        pack_name="newcomer",
        pack_version="0.2.0",
        unresolved_markers=[],
        new_companions=[],
        allowed_prefixes=None,
    )

    parsed = tomllib.loads(marker.read_text(encoding="utf-8"))
    assert "phantom" not in parsed, "round-trip emission landed phantom field"
    # The malformed prior entry is dropped; only the new entry survives.
    entries = parsed["packs-installed"]
    assert len(entries) == 1
    assert entries[0]["name"] == "newcomer"


def test_install_marker_resists_unresolved_marker_and_companion_injection(
    tmp_path,
) -> None:
    """The marker emits list-of-strings positions for ``unresolved-markers``
    and ``new-companions``. Both are derived from pack-sourced inputs
    (renderer output / Tier-2 collision tally) and must escape too."""
    from agentbundle.commands.install import _append_install_marker

    bad_marker = 'name"\nname = "evil'
    bad_companion = 'path"\n[evil]\nx = "y'
    _append_install_marker(
        tmp_path,
        "repo",
        pack_name="alpha",
        pack_version="0.1.0",
        unresolved_markers=[bad_marker],
        new_companions=[bad_companion],
        allowed_prefixes=None,
    )

    marker = tmp_path / ".adapt-install-marker.toml"
    parsed = tomllib.loads(marker.read_text(encoding="utf-8"))

    entry = parsed["packs-installed"][0]
    assert entry["unresolved-markers"] == [bad_marker]
    assert entry["new-companions"] == [bad_companion]
    assert "evil" not in parsed


def test_cli_install_preserves_existing_install_route(tmp_path) -> None:
    """Blocker-2 regression: _append_install_marker re-emits existing entries
    preserving their original install-route value (not overwriting with "cli").

    Scenario: a marker was previously written by the Claude-plugins route
    (install-route = "claude-plugins").  The CLI installs a different pack.
    The pre-seeded entry must still carry install-route = "claude-plugins"
    in the resulting file; the new CLI entry must carry install-route = "cli".
    """
    import tomllib as _tomllib
    from agentbundle.commands.install import _append_install_marker
    from datetime import datetime, timezone

    # Pre-seed a marker with a claude-plugins-routed entry.
    marker = tmp_path / ".adapt-install-marker.toml"
    # We write raw TOML to seed the entry with the exact install-route value
    # the Claude-plugins writer would produce, including a bare datetime.
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    marker.write_text(
        'marker-schema-version = "0.1"\n'
        "\n"
        "[[packs-installed]]\n"
        'name = "converters"\n'
        'version = "0.1.0"\n'
        f"installed-at = {ts}\n"
        'install-route = "claude-plugins"\n',
        encoding="utf-8",
    )

    # CLI installs a different pack.
    _append_install_marker(
        tmp_path,
        "repo",
        pack_name="governance-extras",
        pack_version="0.2.0",
        unresolved_markers=[],
        new_companions=[],
        allowed_prefixes=None,
    )

    parsed = _tomllib.loads(marker.read_text(encoding="utf-8"))
    entries = parsed["packs-installed"]
    assert len(entries) == 2, f"Expected 2 entries, got {len(entries)}"

    by_name = {e["name"]: e for e in entries}

    # Pre-seeded entry must preserve its install-route.
    assert by_name["converters"]["install-route"] == "claude-plugins", (
        "pre-seeded claude-plugins entry had its install-route overwritten"
    )
    # Newly-added CLI entry must carry "cli".
    assert by_name["governance-extras"]["install-route"] == "cli", (
        "new CLI entry does not carry install-route = 'cli'"
    )


def test_cli_install_emits_install_route_cli(tmp_path) -> None:
    """AC13: every [[packs-installed]] entry written by _append_install_marker
    carries install-route = "cli". Regression pin — the field must appear on
    every entry regardless of the unresolved-markers / new-companions content."""
    from agentbundle.commands.install import _append_install_marker

    _append_install_marker(
        tmp_path,
        "repo",
        pack_name="core",
        pack_version="0.1.0",
        unresolved_markers=[],
        new_companions=[],
        allowed_prefixes=None,
    )

    marker = tmp_path / ".adapt-install-marker.toml"
    parsed = tomllib.loads(marker.read_text(encoding="utf-8"))

    entries = parsed["packs-installed"]
    assert len(entries) == 1
    assert entries[0]["install-route"] == "cli", (
        "install-route field must be 'cli' on every CLI-written marker entry"
    )


def test_cli_install_coerces_malformed_unresolved_markers_field(tmp_path) -> None:
    """Security Concern 1 regression: _append_install_marker read-loop coerces
    unresolved-markers = "string" (non-list) on a pre-existing entry.

    Scenario: an adversarial or hand-edited marker has
    ``unresolved-markers = "bad"`` (a TOML basic-string, not array).
    Without the coercion, _emit_basic_string raises ValueError on the
    non-list value, bricking every subsequent CLI install.

    Expected behaviour after this fix:
      (a) the call does not raise;
      (b) the new entry is present in the resulting marker;
      (c) the pre-seeded entry survived but its unresolved-markers field
          is absent (bad field dropped, rest of entry preserved);
      (d) exit code is implicitly 0 (no exception).
    """
    from agentbundle.commands.install import _append_install_marker
    import datetime as _dt

    # Seed a marker with a valid-looking entry but malformed unresolved-markers.
    marker = tmp_path / ".adapt-install-marker.toml"
    ts = _dt.datetime(2026, 1, 1, 0, 0, 0, tzinfo=_dt.timezone.utc)
    marker.write_text(
        'marker-schema-version = "0.1"\n'
        "\n"
        "[[packs-installed]]\n"
        'name = "victim"\n'
        'version = "0.1.0"\n'
        f"installed-at = {ts.strftime('%Y-%m-%dT%H:%M:%SZ')}\n"
        'install-route = "cli"\n'
        # Non-list value triggers the coercion path.
        'unresolved-markers = "bad-string-not-a-list"\n'
        "new-companions = []\n",
        encoding="utf-8",
    )

    # Should not raise; CLI install for a different pack must succeed.
    _append_install_marker(
        tmp_path,
        "repo",
        pack_name="newcomer",
        pack_version="0.2.0",
        unresolved_markers=[],
        new_companions=[],
        allowed_prefixes=None,
    )

    parsed = tomllib.loads(marker.read_text(encoding="utf-8"))
    entries = parsed["packs-installed"]
    by_name = {e["name"]: e for e in entries}

    # (b) new entry is present.
    assert "newcomer" in by_name, "New entry missing after malformed-field coercion"
    # (c) pre-seeded entry survived (not dropped entirely).
    assert "victim" in by_name, "Pre-seeded entry was dropped instead of coerced"
    # (c) the malformed string value was coerced — the CLI emit loop always emits
    # unresolved-markers as an array, so after coercion the field re-emits as `[]`
    # (not absent). The critical invariant is that the call did NOT raise and the
    # new entry was written successfully.
    victim_um = by_name["victim"].get("unresolved-markers")
    assert isinstance(victim_um, list), (
        f"Expected unresolved-markers to be coerced to a list, got {victim_um!r}"
    )
