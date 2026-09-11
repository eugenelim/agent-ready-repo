"""Unit tests for `commands.install._append_layout_section` (spec AC1-AC5, AC10-AC14).

The function appends a pack's declared layout section to an adopter-owned
`agentbundle-layout.toml` — appending only, never creating the file and never
replacing a section the adopter wrote.

Two properties shape every test here.

**It is best-effort maintenance.** It never raises and never fails the
install. Every decline is reported on stderr except the three states that are
the contract working, where a message would be noise on the majority of
installs. The spec fixes one verdict per state in an ordered table; there is a
case per row below.

**Assertions state the exact complete result**, not "the adopter's content
survived". The shipped function returned early for every manifest in the
catalogue, so a survival-shaped assertion passes on a file nobody wrote to —
that is how the original defect went unseen for two releases. Fixtures are
literal bytes rather than serialised from a dict, because a serialised fixture
cannot carry the comment or the line ending the criteria are about.
"""

from __future__ import annotations

import os
import stat as statmod
import tomllib
from pathlib import Path

import pytest
from agentbundle.commands.install import _append_layout_section

_SECTION = "design"
_BASE = "docs/design"


def _layout(scope: str = "repo") -> dict:
    """A manifest keyed on the scope it will be installed at.

    Keying it on "repo" regardless would make `_append(..., scope="user")`
    hand the function a manifest with no `user` sub-table: a silent row-1
    no-op that satisfies any assertion shaped "nothing happened".
    """
    return {scope: {"section": _SECTION, "output_dir": _BASE}}


def _append(root: Path, *, scope: str = "repo", layout: dict | None = None) -> None:
    _append_layout_section(
        root,
        scope,
        pack_name="experience-design",
        pack_layout=_layout(scope) if layout is None else layout,
        allowed_prefixes=None,
    )


def _seed(tmp_path: Path, body: bytes) -> Path:
    path = tmp_path / "agentbundle-layout.toml"
    path.write_bytes(body)
    return path


def _table(newline: bytes = b"\n") -> bytes:
    return b"[design]" + newline + b'output_dir = "docs/design"' + newline


# ---------------------------------------------------------------------------
# Row 13 — the append itself (AC1, AC2, AC3)
# ---------------------------------------------------------------------------


def test_declared_pair_is_appended_and_nothing_else_changes(tmp_path: Path) -> None:
    original = b'# adopter notes\n\n[research]\noutput_dir = "vault"  # inline\n'
    path = _seed(tmp_path, original)

    _append(tmp_path)

    assert path.read_bytes() == original + _table()


def test_a_file_without_a_trailing_newline_gains_exactly_one(tmp_path: Path) -> None:
    original = b'[research]\noutput_dir = "vault"'
    path = _seed(tmp_path, original)

    _append(tmp_path)

    assert path.read_bytes() == original + b"\n" + _table()


def test_crlf_survives_and_the_appended_table_matches(tmp_path: Path) -> None:
    """A text-mode read folds CRLF to LF and rewrites the whole file."""
    original = b'[research]\r\noutput_dir = "vault"\r\n'
    path = _seed(tmp_path, original)

    _append(tmp_path)

    assert path.read_bytes() == original + _table(b"\r\n")


def test_a_mixed_ending_file_takes_its_last_terminator(tmp_path: Path) -> None:
    original = b'[a]\r\nx = "1"\n[b]\ny = "2"\n'
    path = _seed(tmp_path, original)

    _append(tmp_path)

    assert path.read_bytes() == original + _table(b"\n")


def test_an_empty_file_yields_one_table(tmp_path: Path) -> None:
    path = _seed(tmp_path, b"")

    _append(tmp_path)

    assert path.read_bytes() == _table()


def test_a_key_the_installer_does_not_model_survives(tmp_path: Path) -> None:
    original = b'[research]\noutput_dir = "vault"\nkept_by_adopter = 7\n'
    path = _seed(tmp_path, original)

    _append(tmp_path)

    assert path.read_bytes() == original + _table()


def test_a_nested_table_and_a_non_string_value_survive(tmp_path: Path) -> None:
    original = b'[research]\noutput_dir = "vault"\nretries = 3\n\n[research.nested]\nk = "v"\n'
    path = _seed(tmp_path, original)

    _append(tmp_path)

    assert path.read_bytes() == original + _table()
    parsed = tomllib.loads(path.read_text(encoding="utf-8"))
    assert parsed["research"]["nested"] == {"k": "v"}
    assert parsed["design"]["output_dir"] == _BASE


def test_a_top_level_non_table_value_survives(tmp_path: Path) -> None:
    """The old re-emit dropped any top-level key it had no model for."""
    original = b'stray = "adopter value"\n[research]\noutput_dir = "vault"\n'
    path = _seed(tmp_path, original)

    _append(tmp_path)

    assert path.read_bytes() == original + _table()


# ---------------------------------------------------------------------------
# Rows 1, 3, 10 — the silent states (AC5)
# ---------------------------------------------------------------------------


def test_absent_file_is_not_created_and_says_nothing(
    tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    _append(tmp_path)

    assert not (tmp_path / "agentbundle-layout.toml").exists()
    captured = capsys.readouterr()
    assert captured.out == "" and captured.err == ""


@pytest.mark.parametrize(
    "scope_table",
    [{"output_dir": _BASE}, {"section": _SECTION}, {}],
    ids=["no-section", "no-output-dir", "neither"],
)
def test_an_incomplete_declaration_is_a_silent_no_op(
    tmp_path: Path, capsys: pytest.CaptureFixture, scope_table: dict
) -> None:
    original = b'[research]\noutput_dir = "vault"\n'
    path = _seed(tmp_path, original)

    _append(tmp_path, layout={"repo": scope_table})

    assert path.read_bytes() == original
    captured = capsys.readouterr()
    assert captured.out == "" and captured.err == ""


def test_an_existing_section_is_not_replaced_and_says_nothing(
    tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    """The steady state on every re-install of a configured pack."""
    original = b'[design]\noutput_dir = "the adopter\'s own choice"\n'
    path = _seed(tmp_path, original)

    _append(tmp_path)

    assert path.read_bytes() == original
    captured = capsys.readouterr()
    assert captured.out == "" and captured.err == ""


def test_a_manifest_fault_outranks_an_already_present_section(
    tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    """Order: manifest faults are decided before the file's own state.

    Without this the confinement and class guards can be moved below the
    occupancy check and the whole suite stays green, while a misdeclared pack
    goes silent on every re-install of an already-configured adopter.
    """
    original = b'[design]\noutput_dir = "the adopter\'s own choice"\n'
    path = _seed(tmp_path, original)

    _append(tmp_path, layout={"repo": {"section": _SECTION, "output_dir": "/etc"}})

    assert path.read_bytes() == original
    _assert_reported(capsys, "outside")


def test_a_bad_class_outranks_an_already_present_section(
    tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    original = b'[design]\noutput_dir = "mine"\n'
    path = _seed(tmp_path, original)

    _append(tmp_path, layout={"repo": {"section": "Bad/Name", "output_dir": _BASE}})

    assert path.read_bytes() == original
    _assert_reported(capsys, "Bad/Name")


# ---------------------------------------------------------------------------
# Rows 2, 4, 5, 6, 7, 8, 9, 11 — the reporting states (AC4)
# ---------------------------------------------------------------------------


def _assert_reported(capsys: pytest.CaptureFixture, *needles: str) -> None:
    err = capsys.readouterr().err
    assert err, "a reporting state must say something"
    for needle in needles:
        assert needle in err, f"{needle!r} missing from {err!r}"


def test_a_symlinked_layout_file_is_refused_and_left_a_symlink(
    tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    real = tmp_path / "real.toml"
    real.write_bytes(b'[research]\noutput_dir = "vault"\n')
    link = tmp_path / "agentbundle-layout.toml"
    try:
        link.symlink_to(real)
    except OSError:  # pragma: no cover - platform without symlink support
        pytest.skip("symlinks unavailable")

    _append(tmp_path)

    assert link.is_symlink(), "the link must survive, not be replaced by a file"
    assert real.read_bytes() == b'[research]\noutput_dir = "vault"\n'
    _assert_reported(capsys, "symbolic link", _SECTION)


def test_a_dangling_symlink_reports_rather_than_reading_as_absent(
    tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    """`Path.exists()` follows the link, so this would go silent under a
    followed-existence probe — contradicting the report promised for every
    symlinked path."""
    link = tmp_path / "agentbundle-layout.toml"
    try:
        link.symlink_to(tmp_path / "gone.toml")
    except OSError:  # pragma: no cover
        pytest.skip("symlinks unavailable")

    _append(tmp_path)

    assert link.is_symlink()
    _assert_reported(capsys, "symbolic link")


@pytest.mark.parametrize("section", ["a/b", "Design", "with space", "-lead", ""])
def test_a_section_outside_the_character_class_is_refused(
    tmp_path: Path, capsys: pytest.CaptureFixture, section: str
) -> None:
    original = b'[research]\noutput_dir = "vault"\n'
    path = _seed(tmp_path, original)

    _append(tmp_path, layout={"repo": {"section": section, "output_dir": _BASE}})

    assert path.read_bytes() == original
    _assert_reported(capsys, repr(section))


@pytest.mark.parametrize("value", ["/etc", "../../etc", "~/.ssh"])
def test_an_output_dir_outside_the_root_is_refused(
    tmp_path: Path, capsys: pytest.CaptureFixture, value: str
) -> None:
    """`output_dir` is catalogue-sourced and reaches a filesystem root here for
    the first time, so it is confined to the root the write jail uses."""
    original = b'[research]\noutput_dir = "vault"\n'
    path = _seed(tmp_path, original)

    _append(tmp_path, layout={"repo": {"section": _SECTION, "output_dir": value}})

    assert path.read_bytes() == original
    _assert_reported(capsys, "outside")


def test_a_relative_user_scope_output_dir_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    """The resolver rejects this shape, so writing it installs dead config."""
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("AGENTBUNDLE_USER_ROOT", str(tmp_path))
    state = tmp_path / ".agentbundle"
    state.mkdir(mode=0o700)
    original = b'[research]\noutput_dir = "/abs/vault"\n'
    path = state / "agentbundle-layout.toml"
    path.write_bytes(original)

    _append(
        tmp_path,
        scope="user",
        layout={"user": {"section": _SECTION, "output_dir": "relative/vault"}},
    )

    assert path.read_bytes() == original
    _assert_reported(capsys, "relative")


def test_an_unreadable_file_is_reported_not_raised(
    tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    path = _seed(tmp_path, b'[research]\noutput_dir = "vault"\n')
    path.chmod(0o000)
    try:
        if os.access(path, os.R_OK):  # pragma: no cover - running as root
            pytest.skip("cannot make a file unreadable as this user")
        _append(tmp_path)
        _assert_reported(capsys, "cannot read")
    finally:
        path.chmod(0o644)


def test_a_directory_where_the_file_belongs_is_reported_not_raised(
    tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    (tmp_path / "agentbundle-layout.toml").mkdir()

    _append(tmp_path)

    _assert_reported(capsys, "cannot read")


def test_a_non_utf8_file_is_reported_and_untouched(
    tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    """Today's wide handler absorbs this; the decode must stay inside the
    refusal boundary or it escapes as a traceback."""
    original = b'# caf\xe9\n[research]\noutput_dir = "vault"\n'
    path = _seed(tmp_path, original)

    _append(tmp_path)

    assert path.read_bytes() == original
    _assert_reported(capsys, "UTF-8")


def test_a_malformed_file_is_reported_and_untouched(
    tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    original = b"this is not = valid toml ] [\n"
    path = _seed(tmp_path, original)

    _append(tmp_path)

    assert path.read_bytes() == original
    _assert_reported(capsys, "malformed")


def test_a_lone_cr_file_is_refused_as_malformed(
    tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    """It parses today only because `read_text` translates lone CR; under a
    byte-preserving read it is unparseable, and that narrowing is reported."""
    original = b'[research]\routput_dir = "vault"\r'
    path = _seed(tmp_path, original)

    _append(tmp_path)

    assert path.read_bytes() == original
    _assert_reported(capsys, "malformed")


@pytest.mark.parametrize(
    "occupant", [b"design = 1\n", b'[[design]]\nx = "y"\n'], ids=["scalar", "array"]
)
def test_an_occupied_name_of_another_type_is_refused(
    tmp_path: Path, capsys: pytest.CaptureFixture, occupant: bytes
) -> None:
    """TOML cannot express `[design]` beside `design = 1`, so preserving the
    adopter's value and appending are jointly unsatisfiable."""
    path = _seed(tmp_path, occupant)

    _append(tmp_path)

    assert path.read_bytes() == occupant
    _assert_reported(capsys, _SECTION)


# ---------------------------------------------------------------------------
# AC13 / AC14 — outcomes a byte comparison cannot see
# ---------------------------------------------------------------------------


def test_the_files_mode_survives_the_atomic_replace(tmp_path: Path) -> None:
    """`mkstemp` creates 0600 and `replace` carries that onto the target."""
    path = _seed(tmp_path, b'[research]\noutput_dir = "vault"\n')
    path.chmod(0o644)

    _append(tmp_path)

    assert statmod.S_IMODE(path.stat().st_mode) == 0o644


# ---------------------------------------------------------------------------
# AC10 — injection safety, carried by `output_dir`
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "payload",
    ['a"b', "a]b", "a\nb = 1\n[evil]\nx", "a\\b"],
    ids=["quote", "bracket", "newline", "backslash"],
)
def test_a_hostile_output_dir_lands_one_string_in_one_table(
    tmp_path: Path, payload: str
) -> None:
    """The value is manifest-supplied and an external catalogue is reachable.

    Each payload resolves inside the root, so the confinement row does not
    refuse it first — otherwise the observation would be vacuous.
    """
    path = _seed(tmp_path, b'[research]\noutput_dir = "vault"\n')

    _append(
        tmp_path, layout={"repo": {"section": _SECTION, "output_dir": payload}}
    )

    parsed = tomllib.loads(path.read_text(encoding="utf-8"))
    assert list(parsed) == ["research", "design"]
    assert parsed["design"] == {"output_dir": payload}


# ---------------------------------------------------------------------------
# AC14 — user-scope confinement is the prefix surface, not the whole home
# ---------------------------------------------------------------------------


def _user_scope_append(home: Path, output_dir: str) -> Path:
    state = home / ".agentbundle"
    state.mkdir(mode=0o700, exist_ok=True)
    path = state / "agentbundle-layout.toml"
    path.write_bytes(b'[research]\noutput_dir = "/already/set"\n')
    _append_layout_section(
        home,
        "user",
        pack_name="third-party",
        pack_layout={"user": {"section": _SECTION, "output_dir": output_dir}},
        allowed_prefixes=[".claude/", ".agentbundle/"],
    )
    return path


def test_a_user_scope_base_outside_the_write_prefixes_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    """The user root is the adopter's whole home — far wider than what the
    installer may write.

    `output_dir` is manifest-supplied and an external catalogue is reachable,
    so a home-wide check would let a pack name any dot-directory under the
    home: an agent-configuration directory, a credential store. A document
    later written to the first of those carries instruction authority into
    every session. The confinement is therefore the adapter's declared prefix
    surface, the same one `write_jailed` enforces.
    """
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("AGENTBUNDLE_USER_ROOT", str(tmp_path))
    # A dot-directory under the home that is not a declared write prefix. The
    # name is deliberately neutral; the property under test is "not in the
    # prefix list", not this directory in particular.
    path = _user_scope_append(tmp_path, str(tmp_path / ".unlisted-config"))

    assert path.read_bytes() == b'[research]\noutput_dir = "/already/set"\n'
    _assert_reported(capsys, "outside the prefixes")


def test_a_sibling_of_a_write_prefix_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    """`.agentbundle/` must not admit `.agentbundlefoo`.

    This is the trailing-slash invariant `safety` documents and owns. The
    check routes through that module's helper rather than re-implementing
    containment, so the two cannot drift apart.
    """
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("AGENTBUNDLE_USER_ROOT", str(tmp_path))
    path = _user_scope_append(tmp_path, str(tmp_path / ".agentbundlefoo"))

    assert path.read_bytes() == b'[research]\noutput_dir = "/already/set"\n'
    _assert_reported(capsys, "outside the prefixes")


def test_a_user_scope_base_inside_a_write_prefix_is_admitted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The refusal must be the prefix surface, not a blanket user-scope ban."""
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("AGENTBUNDLE_USER_ROOT", str(tmp_path))
    path = _user_scope_append(tmp_path, str(tmp_path / ".agentbundle" / "design"))

    assert _SECTION.encode() in path.read_bytes()


def test_the_home_root_itself_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("AGENTBUNDLE_USER_ROOT", str(tmp_path))
    path = _user_scope_append(tmp_path, str(tmp_path))

    assert path.read_bytes() == b'[research]\noutput_dir = "/already/set"\n'
    _assert_reported(capsys, "user root itself")


def test_an_empty_output_dir_is_reported(
    tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    """Present-but-empty is malformed, not absent — the same verdict `section`
    gets. Leaving this on the silent path gave two keys of identical shape
    opposite verdicts."""
    original = b'[research]\noutput_dir = "vault"\n'
    path = _seed(tmp_path, original)

    _append(tmp_path, layout={"repo": {"section": _SECTION, "output_dir": ""}})

    assert path.read_bytes() == original
    _assert_reported(capsys, "empty output_dir")


def test_a_crlf_file_without_a_trailing_newline_gains_a_crlf_separator(
    tmp_path: Path,
) -> None:
    """The separator must take the file's own style, not always LF.

    Replacing the separator with an unconditional `b"\\n"` left every other
    case green, because the only non-empty-separator fixture used LF.
    """
    original = b'[research]\r\noutput_dir = "vault"'
    path = _seed(tmp_path, original)

    _append(tmp_path)

    assert path.read_bytes() == original + b"\r\n" + _table(b"\r\n")


def test_a_file_with_no_terminator_at_all_gains_lf(tmp_path: Path) -> None:
    """The `last_lf == -1` branch: a non-empty file carrying no line ending."""
    original = b'x = "no terminator"'
    path = _seed(tmp_path, original)

    _append(tmp_path)

    assert path.read_bytes() == original + b"\n" + _table()


def test_a_failing_write_is_reported_and_the_install_continues(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    """Row 12 — the write itself failing. Previously unexecuted."""
    from agentbundle import safety

    original = b'[research]\noutput_dir = "vault"\n'
    path = _seed(tmp_path, original)

    def _fail(*_args, **_kwargs):
        raise safety.WriteError("simulated write failure")

    # `safety` is imported inside the function under test, so the patch has to
    # land on the module itself rather than on an attribute of `install`.
    monkeypatch.setattr(safety, "write_jailed", _fail)

    _append(tmp_path)  # must not raise

    assert path.read_bytes() == original
    _assert_reported(capsys, "cannot write")


def test_an_unenumerated_failure_is_reported_and_the_function_returns(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    """Row 14 — the catch-all, which is the sole reason "no state raises" holds.

    `write_jailed` raises `TypeError` when `scope="user"` and
    `allowed_prefixes is None`, which row 12's `except (OSError, PathJailError)`
    does not catch. Without the catch-all that escapes as a traceback after
    the projection and marker are already on disk.
    """
    from agentbundle import safety

    original = b'[research]\noutput_dir = "vault"\n'
    path = _seed(tmp_path, original)

    def _boom(*_args, **_kwargs):
        raise TypeError("a failure none of rows 1-13 name")

    monkeypatch.setattr(safety, "write_jailed", _boom)

    _append(tmp_path)  # must not raise

    assert path.read_bytes() == original
    _assert_reported(capsys, "layout maintenance failed")
