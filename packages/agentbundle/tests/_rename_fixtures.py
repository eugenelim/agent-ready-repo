"""Fixtures shared by the rename-hint unit and integration tests.

Everything is built under a caller-supplied ``tmp_path``; nothing reads this
repository's tree.
"""

from __future__ import annotations

import os
import sys
from collections.abc import Callable
from pathlib import Path

import pytest

OLD = "governance-extras"
NEW = "repo-governance"
GOOD_MAP = f'schema = 1\n\n[[rename]]\nfrom = "{OLD}"\nto = "{NEW}"\n'
DEP = 'iac-terraform'
DEP_TOML = (
    '[pack]\nname = "iac-terraform"\n\n[[pack.dependencies.required]]\n'
    'pack = "repo-governance"\nversion = "^2.0"\n'
)
PLAIN_TOML = '[pack]\nname = "x"\n'
REPORTING = "git+https://example.test/org/repo"
NOT_FOUND = "pack 'governance-extras' not found"  # stands in for today's message
SKIP_NO_LINKS = pytest.mark.skipif(
    not hasattr(os, "symlink") or sys.platform == "win32", reason="needs symlinks"
)


def catalogue(
    tmp_path: Path,
    *,
    map_text: str | None = GOOD_MAP,
    packs: dict[str, str] | None = None,
    root_layout: tuple[str, ...] = (),
    with_target: bool = True,
) -> Path:
    """A fixture catalogue; *packs* maps name to its pack.toml text."""
    cat = tmp_path / "cat"
    cat.mkdir()
    if map_text is not None:
        (cat / "contracts" / "renames").mkdir(parents=True)
        (cat / "contracts" / "renames" / "pack-renames.toml").write_text(
            map_text, encoding="utf-8"
        )
    all_packs = dict(packs or {})
    if with_target:
        all_packs.setdefault(NEW, PLAIN_TOML)
    for name, text in all_packs.items():
        base = cat if name in root_layout else cat / "packs"
        (base / name).mkdir(parents=True)
        (base / name / "pack.toml").write_text(text, encoding="utf-8")
    return cat


BAD_MAPS = {
    "invalid-toml": "schema = = 1",
    "non-utf8": b"\xff\xfe\xfa",
    "deep": "a = " + "[" * 1000,
    "rename-string": 'schema = 1\nrename = "x"\n',
    "from-int": 'schema = 1\n[[rename]]\nfrom = 1\nto = "repo-governance"\n',
    "missing-schema": f'[[rename]]\nfrom = "{OLD}"\nto = "{NEW}"\n',
    "schema-2": f'schema = 2\n[[rename]]\nfrom = "{OLD}"\nto = "{NEW}"\n',
    "bad-from-name": 'schema = 1\n[[rename]]\nfrom = "Bad_Name"\nto = "repo-governance"\n',
    "bad-name-elsewhere": (
        f'schema = 1\n[[rename]]\nfrom = "{OLD}"\nto = "{NEW}"\n'
        '[[rename]]\nfrom = "-bad"\nto = "repo-governance"\n'
    ),
    "foreign-target": f'schema = 1\n[[rename]]\nfrom = "{OLD}"\nto = "not-here"\n',
    "extra-key": f'schema = 1\n[[rename]]\nfrom = "{OLD}"\nto = "{NEW}"\nx = 1\n',
    "empty": "",
}


def _write_bytes_map(cat: Path, body: str | bytes) -> None:
    path = cat / "contracts" / "renames" / "pack-renames.toml"
    path.unlink()
    path.write_bytes(body if isinstance(body, bytes) else body.encode("utf-8"))


def _oversized(cat: Path, tmp_path: Path) -> None:
    _write_bytes_map(cat, GOOD_MAP + "#" * (65537 - len(GOOD_MAP)))


def _symlinked_map(cat: Path, tmp_path: Path) -> None:
    real = tmp_path / "real.toml"
    real.write_text(GOOD_MAP, encoding="utf-8")
    path = cat / "contracts/renames/pack-renames.toml"
    path.unlink()
    path.symlink_to(real)


def _hard_linked_map(cat: Path, tmp_path: Path) -> None:
    os.link(cat / "contracts/renames/pack-renames.toml", tmp_path / "second-name.toml")


def _symlinked_dir(which: str) -> Callable[[Path, Path], None]:
    def mutate(cat: Path, tmp_path: Path) -> None:
        target = cat / "contracts" if which == "contracts" else cat / "contracts/renames"
        moved = tmp_path / f"moved-{which}"
        target.rename(moved)
        target.symlink_to(moved, target_is_directory=True)

    return mutate


def _regular_file_at_renames(cat: Path, tmp_path: Path) -> None:
    (cat / "contracts/renames/pack-renames.toml").unlink()
    (cat / "contracts/renames").rmdir()
    (cat / "contracts" / "renames").write_text(GOOD_MAP, encoding="utf-8")


def _fifo_map(cat: Path, tmp_path: Path) -> None:
    path = cat / "contracts/renames/pack-renames.toml"
    path.unlink()
    os.mkfifo(path)


def _directory_map(cat: Path, tmp_path: Path) -> None:
    path = cat / "contracts/renames/pack-renames.toml"
    path.unlink()
    path.mkdir()


def _missing_map(cat: Path, tmp_path: Path) -> None:
    (cat / "contracts/renames/pack-renames.toml").unlink()


def _map_naming_other_pack(cat: Path, tmp_path: Path) -> None:
    _write_bytes_map(
        cat, 'schema = 1\n[[rename]]\nfrom = "other-old"\nto = "repo-governance"\n'
    )


def _target_missing(cat: Path, tmp_path: Path) -> None:
    import shutil

    shutil.rmtree(cat / "packs" / NEW)


def _bad_map(label: str) -> Callable[[Path, Path], None]:
    return lambda cat, tmp_path: _write_bytes_map(cat, BAD_MAPS[label])


# AC-0022 breakers: no hint, whatever the cause.
INVALID_MAP_BREAKERS: dict[str, Callable[[Path, Path], None]] = {
    **{f"invalid-{label}": _bad_map(label) for label in sorted(BAD_MAPS)},
    "missing-map": _missing_map,
    "map-names-other-pack": _map_naming_other_pack,
    "target-not-a-pack": _target_missing,
}

# AC-0027 breakers: the map or its directories are not a safe regular file.
UNSAFE_MAP_BREAKERS: dict[str, Callable[[Path, Path], None]] = {
    "oversized": _oversized,
    "directory-map": _directory_map,
    "regular-file-at-renames": _regular_file_at_renames,
}
if hasattr(os, "symlink") and sys.platform != "win32":
    UNSAFE_MAP_BREAKERS.update(
        {
            "symlinked-map": _symlinked_map,
            "hard-linked-map": _hard_linked_map,
            "symlinked-contracts": _symlinked_dir("contracts"),
            "symlinked-renames": _symlinked_dir("renames"),
        }
    )
if hasattr(os, "mkfifo"):
    UNSAFE_MAP_BREAKERS["fifo-map"] = _fifo_map

MAP_BREAKERS = {**INVALID_MAP_BREAKERS, **UNSAFE_MAP_BREAKERS}


# ---------------------------------------------------------------------------
# Installable, packageable catalogues for the command-level runs
# ---------------------------------------------------------------------------

CATALOGUE_NAME = "demo-cat"


def build_catalogue(
    root: Path,
    packs: dict[str, tuple[str, tuple[tuple[str, str], ...]]],
    *,
    renames: tuple[tuple[str, str], ...] = (),
) -> Path:
    """Build a catalogue that installs, verifies and packages.

    *packs* maps a pack name to ``(version, ((dependency, constraint), ...))``. Every
    pack is a copy of the ``_example`` pack that ``catalogue init`` writes.
    """
    import shutil

    from agentbundle.catalogue_tooling.initialise import init_catalogue

    result = init_catalogue(target=root, name=CATALOGUE_NAME)
    assert result.ok, result.diagnostics
    example = root / "packs" / "_example"
    for name, (version, deps) in packs.items():
        pack = root / "packs" / name
        shutil.copytree(example, pack)
        skill = f"{name}-skill"  # one skill per pack, so no two packs own a path
        (pack / ".apm/skills/example-skill").rename(pack / ".apm/skills" / skill)
        for path in pack.rglob("*"):
            if path.is_file():
                path.write_text(
                    path.read_text(encoding="utf-8").replace("example-skill", skill),
                    encoding="utf-8",
                )
        text = (pack / "pack.toml").read_text(encoding="utf-8")
        text = text.replace("example-pack", name).replace("0.1.1", version)
        text = text.replace("Example Pack", name)
        for dep, constraint in deps:
            text += (
                f'\n[[pack.dependencies.required]]\ncatalogue = "{CATALOGUE_NAME}"\n'
                f'pack = "{dep}"\nversion = "{constraint}"\n'
            )
        (pack / "pack.toml").write_text(text, encoding="utf-8")
        plugin = (pack / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")
        plugin = plugin.replace("example-pack", name).replace("0.1.1", version)
        (pack / ".claude-plugin" / "plugin.json").write_text(
            plugin.replace("Example Pack", name), encoding="utf-8"
        )
    if renames:
        (root / "contracts" / "renames").mkdir(parents=True)
        body = "schema = 1\n" + "".join(
            f'\n[[rename]]\nfrom = "{a}"\nto = "{b}"\n' for a, b in renames
        )
        (root / "contracts" / "renames" / "pack-renames.toml").write_text(
            body, encoding="utf-8"
        )
    catalogue_toml = root / "catalogue.toml"
    include = ", ".join(f'"packs/{name}"' for name in packs)
    catalogue_toml.write_text(
        catalogue_toml.read_text(encoding="utf-8").replace(
            "include  = []", f"include  = [{include}]"
        ),
        encoding="utf-8",
    )
    return root


def pre_rename_catalogue(root: Path, *, version: str = "1.0.3") -> Path:
    """A catalogue that still ships ``governance-extras`` and no map."""
    return build_catalogue(
        root,
        {OLD: (version, ()), DEP: ("0.1.12", ((OLD, "^1.0"),))},
    )


def post_rename_catalogue(root: Path) -> Path:
    """A catalogue that ships ``repo-governance`` 2.0.0 and carries the map."""
    return build_catalogue(
        root,
        {NEW: ("2.0.0", ()), DEP: ("0.2.0", ((NEW, "^2.0"),))},
        renames=((OLD, NEW),),
    )
