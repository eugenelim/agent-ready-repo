"""Unit tests for `commands.install._append_layout_section` (T2).

Spec: docs/specs/consolidated-pack-layout/spec.md (AC9, AC10, AC11).

`_append_layout_section` maintains an adopter-owned `agentbundle-layout.toml`:
it appends a pack's scope-keyed `[pack.layout.<scope>]` default as a `[<pack>]`
table **only if the file already exists and the section is absent**. It never
creates the file and never overwrites an existing section. It is modelled on
`_append_install_marker`'s read + type-validate + re-emit upsert, so every
emitted string (table header and value alike) routes through
`_emit_basic_string`, and the write goes through the per-scope `write_jailed`
jail.
"""

from __future__ import annotations

import tomllib

import pytest

from agentbundle.commands.install import _append_layout_section
from agentbundle.safety import PathJailError


# ---------------------------------------------------------------------------
# never-create / never-overwrite (AC9)
# ---------------------------------------------------------------------------


def test_never_create_no_op_when_file_absent(tmp_path):
    """No layout file at the scope location ⇒ the append writes nothing."""
    _append_layout_section(
        tmp_path,
        "repo",
        pack_name="research",
        pack_layout={"repo": {"parent": ".context/research"}},
        allowed_prefixes=None,
    )
    assert not (tmp_path / "agentbundle-layout.toml").exists()


def test_never_overwrite_leaves_existing_section_byte_identical(tmp_path):
    """An existing `[<pack>]` section is left untouched — the whole file,
    comments and all, is byte-identical (the never-overwrite check returns
    before any re-emit)."""
    layout = tmp_path / "agentbundle-layout.toml"
    original = (
        "# my hand-written layout\n"
        '[research]\n'
        'parent = "~/my-research"  # custom\n'
    )
    layout.write_text(original, encoding="utf-8")
    _append_layout_section(
        tmp_path,
        "repo",
        pack_name="research",
        pack_layout={"repo": {"parent": ".context/research"}},
        allowed_prefixes=None,
    )
    assert layout.read_text(encoding="utf-8") == original


def test_appends_missing_section_when_file_exists(tmp_path):
    """A pre-existing file missing `[research]` gains it (the other section
    survives)."""
    layout = tmp_path / "agentbundle-layout.toml"
    layout.write_text('[architect]\nparent = "docs/design"\n', encoding="utf-8")
    _append_layout_section(
        tmp_path,
        "repo",
        pack_name="research",
        pack_layout={"repo": {"parent": ".context/research"}},
        allowed_prefixes=None,
    )
    parsed = tomllib.loads(layout.read_text(encoding="utf-8"))
    assert parsed["architect"]["parent"] == "docs/design"
    assert parsed["research"]["parent"] == ".context/research"


# ---------------------------------------------------------------------------
# scope-keyed selection + omit-`.user` no-op (AC10)
# ---------------------------------------------------------------------------


def test_scope_keyed_selection_repo_vs_user(tmp_path):
    """Repo scope sources `[pack.layout.repo]`; user scope sources
    `[pack.layout.user]`."""
    pack_layout = {
        "repo": {"parent": ".context/research"},
        "user": {"parent": "/abs/user/research"},
    }
    # Repo scope.
    repo_layout = tmp_path / "agentbundle-layout.toml"
    repo_layout.write_text('[architect]\nparent = "docs/design"\n', encoding="utf-8")
    _append_layout_section(
        tmp_path, "repo", pack_name="research", pack_layout=pack_layout,
        allowed_prefixes=None,
    )
    assert tomllib.loads(repo_layout.read_text())["research"]["parent"] == ".context/research"

    # User scope — pre-create `.agentbundle/agentbundle-layout.toml`.
    home = tmp_path / "home"
    (home / ".agentbundle").mkdir(parents=True)
    user_layout = home / ".agentbundle" / "agentbundle-layout.toml"
    user_layout.write_text('[architect]\nparent = "docs/design"\n', encoding="utf-8")
    _append_layout_section(
        home, "user", pack_name="research", pack_layout=pack_layout,
        allowed_prefixes=[".agentbundle/"],
    )
    assert tomllib.loads(user_layout.read_text())["research"]["parent"] == "/abs/user/research"


def test_omit_user_subtable_is_user_scope_no_op(tmp_path):
    """A pack declaring only `[pack.layout.repo]` ⇒ the user-scope append is a
    no-op even though the file exists (the three current consumers' shape)."""
    home = tmp_path / "home"
    (home / ".agentbundle").mkdir(parents=True)
    user_layout = home / ".agentbundle" / "agentbundle-layout.toml"
    original = '[architect]\nparent = "docs/design"\n'
    user_layout.write_text(original, encoding="utf-8")
    _append_layout_section(
        home,
        "user",
        pack_name="research",
        pack_layout={"repo": {"parent": ".context/research"}},  # no `.user`
        allowed_prefixes=[".agentbundle/"],
    )
    assert user_layout.read_text(encoding="utf-8") == original


def test_no_layout_table_is_no_op(tmp_path):
    """A pack shipping no `[pack.layout]` at all ⇒ no-op (safe to call for
    every pack)."""
    layout = tmp_path / "agentbundle-layout.toml"
    original = '[architect]\nparent = "docs/design"\n'
    layout.write_text(original, encoding="utf-8")
    _append_layout_section(
        tmp_path, "repo", pack_name="core", pack_layout={}, allowed_prefixes=None,
    )
    assert layout.read_text(encoding="utf-8") == original


# ---------------------------------------------------------------------------
# injection-safe emit + re-emit type-validation (AC11)
# ---------------------------------------------------------------------------


def test_injection_safe_roundtrip_of_default_parent(tmp_path):
    """A `[pack.layout]` default containing `"`, `]`, newline, and `../`
    round-trips intact and well-formed; no smuggled sibling table materialises."""
    layout = tmp_path / "agentbundle-layout.toml"
    layout.write_text('[architect]\nparent = "docs/design"\n', encoding="utf-8")
    hostile = 'a"b]c\n[evil]\nx = "../../etc"'
    _append_layout_section(
        tmp_path, "repo", pack_name="research",
        pack_layout={"repo": {"parent": hostile}}, allowed_prefixes=None,
    )
    text = layout.read_text(encoding="utf-8")
    parsed = tomllib.loads(text)  # raises if malformed
    assert parsed["research"]["parent"] == hostile  # intact
    assert "evil" not in parsed  # no phantom table
    assert set(parsed) == {"architect", "research"}


def test_reemit_drops_tampered_existing_parent(tmp_path):
    """A tampered existing section (`parent = 42`, `parent = ["x"]`) is dropped
    on re-emit, not crashed on; the new section still lands."""
    layout = tmp_path / "agentbundle-layout.toml"
    layout.write_text(
        '[architect]\nparent = 42\n\n[oldpack]\nparent = ["x"]\n',
        encoding="utf-8",
    )
    _append_layout_section(
        tmp_path, "repo", pack_name="research",
        pack_layout={"repo": {"parent": ".context/research"}},
        allowed_prefixes=None,
    )
    parsed = tomllib.loads(layout.read_text(encoding="utf-8"))
    assert parsed["research"]["parent"] == ".context/research"
    assert "architect" not in parsed  # non-str parent dropped
    assert "oldpack" not in parsed


def test_malformed_file_left_untouched(tmp_path):
    """An unparseable existing file is left byte-identical (warn + no-op),
    never corrupted by an append."""
    layout = tmp_path / "agentbundle-layout.toml"
    original = "this is not = valid toml ] [\n"
    layout.write_text(original, encoding="utf-8")
    _append_layout_section(
        tmp_path, "repo", pack_name="research",
        pack_layout={"repo": {"parent": ".context/research"}},
        allowed_prefixes=None,
    )
    assert layout.read_text(encoding="utf-8") == original


# ---------------------------------------------------------------------------
# jailed write — user scope succeeds; symlink target fails closed (AC11, AC14)
# ---------------------------------------------------------------------------


def test_user_scope_write_succeeds_against_real_prefix_list(tmp_path):
    """The user-scope write succeeds against a real `allowed-prefixes.user`
    list carrying `.agentbundle/` (not merely the TypeError-when-omitted rail)."""
    home = tmp_path / "home"
    (home / ".agentbundle").mkdir(parents=True)
    user_layout = home / ".agentbundle" / "agentbundle-layout.toml"
    user_layout.write_text('[architect]\nparent = "docs/design"\n', encoding="utf-8")
    _append_layout_section(
        home,
        "user",
        pack_name="research",
        pack_layout={"user": {"parent": "~/research-projects"}},
        allowed_prefixes=[".claude/", ".agentbundle/"],
    )
    parsed = tomllib.loads(user_layout.read_text(encoding="utf-8"))
    assert parsed["research"]["parent"] == "~/research-projects"


def test_symlink_layout_file_fails_closed(tmp_path):
    """When the layout *file path itself* is a symlink escaping `root`, the
    append's `write_jailed` → `assert_under` realpath-resolve raises
    `PathJailError` — it never follows the link out of tree."""
    outside = tmp_path / "outside"
    outside.mkdir()
    real_target = outside / "agentbundle-layout.toml"
    real_target.write_text('[architect]\nparent = "docs/design"\n', encoding="utf-8")

    repo = tmp_path / "repo"
    repo.mkdir()
    link = repo / "agentbundle-layout.toml"
    link.symlink_to(real_target)  # escapes `repo`

    with pytest.raises(PathJailError):
        _append_layout_section(
            repo, "repo", pack_name="research",
            pack_layout={"repo": {"parent": ".context/research"}},
            allowed_prefixes=None,
        )
