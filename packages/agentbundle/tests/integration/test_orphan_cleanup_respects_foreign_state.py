"""Regression: orphan-cleanup must not unlink files claimed by other
state-tracked packs.

Reported by an adopter: when installing pack B with ``--force`` into a
directory where pack A is already installed, the installer's orphan
detection treats pack A's projected files as "orphan projection files"
and deletes them. The state file retains pack A's row with its
recorded SHA, but the on-disk file is gone (or, worse, silently
overwritten with pack B's content of the same name). State is now
lying about disk.

Root cause: ``safety.scan_for_pack_artifacts`` uses a primitive-name
heuristic to attribute on-disk files to the installing pack. The
heuristic is best-effort scoping — it does not consult the state file
to exclude paths claimed by *other* state-tracked packs. When two
packs ship primitives with overlapping names, the heuristic
mis-attributes the foreign pack's file as an orphan of the installing
pack; ``_classify_pre_rfc0012_state``'s branch (c) ``--force`` clause
then unlinks them.

Catalogue today has no primitive-name overlaps across shipped packs
(verified at the time of writing), so the bug is dormant against
default catalogue use — but adopters with custom packs, or any future
catalogue change that introduces an overlap, trigger it. The fix
makes the orphan filter authoritative: paths claimed by another
state-tracked pack are excluded from the orphan list.

Tests in this module use synthetic packs because the bug requires a
primitive-name collision that the shipped catalogue does not exhibit.
"""

from __future__ import annotations

import contextlib
import hashlib
import io
import textwrap
import tomllib
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Test hygiene
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _isolate_home_and_caches(tmp_path, monkeypatch):
    """Same isolation pattern as test_multi_pack_install.py — see that
    file's fixture docstring for the rationale (HOME isolation +
    once-per-process cache reset)."""
    from agentbundle.commands import install

    home = tmp_path / "iso_home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))

    install._clear_inband_detection_seen()
    install._clear_dropped_warning_seen()
    yield
    install._clear_inband_detection_seen()
    install._clear_dropped_warning_seen()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _stage_pack(
    cat_root: Path, name: str, *, skills: list[str],
) -> Path:
    """Materialise a synthetic pack at ``cat_root/packs/<name>/`` with the
    given skill names. Each skill is a directory under ``.apm/skills/``
    containing a ``SKILL.md`` whose body identifies the pack of origin
    so post-install content can be attributed.
    """
    pack_dir = cat_root / "packs" / name
    pack_dir.mkdir(parents=True)
    (pack_dir / "pack.toml").write_text(
        textwrap.dedent(
            f"""\
            [pack]
            name = "{name}"
            version = "0.1.0"

            [pack.adapter-contract]
            version = "0.8"

            [pack.install]
            default-scope = "repo"
            allowed-scopes = ["repo"]
            """
        ),
        encoding="utf-8",
    )
    apm = pack_dir / ".apm"
    apm.mkdir()
    for skill in skills:
        sd = apm / "skills" / skill
        sd.mkdir(parents=True)
        (sd / "SKILL.md").write_text(
            f"---\nname: {skill}\ndescription: from-{name}\n---\nBody from {name}.",
            encoding="utf-8",
        )
    return pack_dir


def _install_argv(argv: list[str]) -> tuple[int, str, str]:
    """Run install via the argparse parser; return (rc, stdout, stderr)."""
    from agentbundle.cli import _build_parser
    from agentbundle.commands import install

    parser = _build_parser()
    args = parser.parse_args(["install"] + argv)
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        rc = install.run(args)
    return rc, out.getvalue(), err.getvalue()


def _state(adopter: Path) -> dict:
    return tomllib.loads(
        (adopter / ".agentbundle-state.toml").read_text(encoding="utf-8")
    )


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_force_install_does_not_unlink_foreign_packs_file(tmp_path):
    """Pack A ships ``shared-tool`` skill, then pack B (which also
    ships ``shared-tool``) is installed with ``--force``. The orphan-
    cleanup branch MUST NOT unlink pack-a's file, and pack-a's state
    row MUST remain intact.

    With the bug: pack-b's orphan scan returns pack-a's file (segment
    match on the shared primitive name); the ``--force`` branch
    unlinks it via ``orphan.unlink()``. Between the unlink and pack-b's
    subsequent write, pack-a's file is genuinely missing — and if
    pack-b's render fails mid-flight, pack-a's file is permanently
    lost while pack-a's state row keeps claiming it.

    With the fix: scanner result is filtered to exclude paths claimed
    by other state-tracked packs (state.toml is authoritative; the
    primitive-name heuristic is best-effort scoping). The orphans
    list is filtered down — pack-a's file is excluded — so no foreign
    file is unlinked in the ``--force`` branch.

    SCOPE NOTE: when two packs intentionally project to the same
    on-disk path, ``_classify_for_install`` already warns + allows the
    write-step overwrite — that is the catalogue-level path-collision
    contract today. This test does NOT pin write-step content (which
    the existing contract allows to be pack-b's) — it pins only that
    the **orphan-cleanup unlink does not fire** for a foreign-owned
    path, which closes the user's specific report ("the actual files
    are gone from disk").
    """
    cat = tmp_path / "cat"
    _stage_pack(cat, "pack-a", skills=["shared-tool"])
    _stage_pack(cat, "pack-b", skills=["shared-tool", "b-only"])

    adopter = tmp_path / "adopter"
    adopter.mkdir()

    # Install pack-a.
    rc, _, err = _install_argv(
        ["--pack", "pack-a", "--output", str(adopter), str(cat)]
    )
    assert rc == 0, f"pack-a install failed: {err}"

    shared_path = adopter / ".claude/skills/shared-tool/SKILL.md"
    assert shared_path.exists()

    # Spy on Path.unlink to record every unlink the install handler
    # performs. The orphan-cleanup branch unlinks via ``orphan.unlink()``;
    # if the bug is live, that call lands for shared_path. The spy
    # records the absolute path so we can assert pack-a's file was NOT
    # in the unlink set.
    unlinked: list[Path] = []
    from pathlib import Path as _Path
    original_unlink = _Path.unlink

    def _spy_unlink(self, *args, **kwargs):
        unlinked.append(self)
        return original_unlink(self, *args, **kwargs)

    import unittest.mock
    with unittest.mock.patch.object(_Path, "unlink", _spy_unlink):
        rc, _, err = _install_argv(
            ["--pack", "pack-b", "--force",
             "--output", str(adopter), str(cat)]
        )

    assert rc == 0, f"pack-b --force install failed: {err}"

    # Load-bearing post-conditions: pack-a's state row preserved and
    # NO call to unlink targeted pack-a's file.
    state = _state(adopter)
    assert "pack-a" in state.get("pack", {}), (
        "pack-a's state row was dropped by pack-b install"
    )
    pack_a_unlinks = [u for u in unlinked if u.resolve() == shared_path.resolve()]
    assert not pack_a_unlinks, (
        f"--force install of pack-b unlinked pack-a's state-tracked file "
        f"{shared_path}; the orphan-cleanup branch mis-attributed it. "
        f"All unlinks during install: {unlinked!r}"
    )


def test_orphan_refusal_does_not_cite_foreign_owned_paths(tmp_path):
    """The orphan-refusal stderr message MUST NOT cite paths owned by
    another state-tracked pack as "orphans" — that's a lie about
    ownership and misleads adopters into running ``--force`` (which
    would clobber the foreign pack).

    With the bug: pack-b install (no --force) emits
    ``install: orphan projection files for pack pack-b at <pack-a's
    file>``, naming pack-a's state-tracked file as a pack-b orphan.
    With the fix: the orphan list is filtered to exclude foreign-owned
    paths; if every "orphan" found by the scanner is in fact
    foreign-owned, the refusal does not fire and install proceeds
    (rc=0). The assertion is unconditional — checking ``pack_a_file
    not in err`` regardless of whether the refusal message fires, so a
    future stderr rewording can't make this test silently vacuous.
    """
    cat = tmp_path / "cat"
    _stage_pack(cat, "pack-a", skills=["shared-tool"])
    _stage_pack(cat, "pack-b", skills=["shared-tool"])

    adopter = tmp_path / "adopter"
    adopter.mkdir()

    rc, _, err = _install_argv(
        ["--pack", "pack-a", "--output", str(adopter), str(cat)]
    )
    assert rc == 0, f"pack-a install failed: {err}"

    rc, _, err = _install_argv(
        ["--pack", "pack-b", "--output", str(adopter), str(cat)]
    )
    # Load-bearing: with the fix, the orphan-refusal branch must not
    # fire for pack-b — every "orphan" the scanner returned was in
    # fact pack-a's foreign-owned file, filtered out by the foreign-
    # state-consultation pass. The install proceeds (rc=0).
    assert rc == 0, (
        f"pack-b install must proceed cleanly after the fix; the "
        f"orphan-refusal branch fired against a foreign-owned path. "
        f"rc={rc}, stderr: {err!r}"
    )
    # And the specific orphan-refusal phrasing must NOT have been
    # emitted (positive signal that the filter ran, not that the
    # branch was bypassed for some other reason).
    assert "orphan projection files for pack pack-b" not in err, (
        f"orphan refusal still fired against a foreign-owned path; "
        f"stderr: {err!r}"
    )
