#!/usr/bin/env python3
"""Self-test for tools/lint-pack-renames.py and the rename map's schema.

Builds fixture catalogues under a tempdir and runs the lint as a subprocess:
one with a pack named after a retired name (AC-0007), one whose map target is
no pack (AC-0008), and one clean. Also validates the real map against its schema
(AC-0005).
"""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import tempfile
import tomllib

import selftest_harness

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
LINTER = REPO_ROOT / "tools" / "lint-pack-renames.py"
MAP = REPO_ROOT / "contracts" / "renames" / "pack-renames.toml"
SCHEMA = REPO_ROOT / "contracts" / "renames" / "pack-renames.schema.json"

_MAP_BODY = 'schema = 1\n\n[[rename]]\nfrom = "old-name"\nto = "new-name"\n'


def _catalogue(base: pathlib.Path, packs: list[str], map_body: str = _MAP_BODY) -> pathlib.Path:
    """Materialise a fixture catalogue holding the map and the named packs."""
    (base / "contracts" / "renames").mkdir(parents=True)
    (base / "contracts" / "renames" / "pack-renames.toml").write_text(map_body, encoding="utf-8")
    for name in packs:
        (base / "packs" / name).mkdir(parents=True)
        (base / "packs" / name / "pack.toml").write_text(f'[pack]\nname = "{name}"\n', encoding="utf-8")
    return base


def _run(root: pathlib.Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(LINTER), "--root", str(root)],
        capture_output=True,
        text=True,
        check=False,
        cwd=str(REPO_ROOT / "tools"),
    )


def _expect(root: pathlib.Path, code: int, needle: str) -> None:
    result = _run(root)
    combined = result.stdout + result.stderr
    assert result.returncode == code, f"exit {result.returncode}, expected {code}: {combined}"
    assert needle in combined, f"missing {needle!r} in: {combined}"


def test_clean_catalogue_passes() -> None:
    with tempfile.TemporaryDirectory() as raw:
        _expect(_catalogue(pathlib.Path(raw) / "c", ["new-name", "other"]), 0, "ok")


def test_pack_named_after_old_name_fails() -> None:
    with tempfile.TemporaryDirectory() as raw:
        root = _catalogue(pathlib.Path(raw) / "c", ["new-name", "old-name"])
        _expect(root, 1, "retired name 'old-name'")


def test_target_that_is_no_pack_fails() -> None:
    with tempfile.TemporaryDirectory() as raw:
        _expect(_catalogue(pathlib.Path(raw) / "c", ["other"]), 1, "'new-name'")


def test_target_directory_without_manifest_fails() -> None:
    with tempfile.TemporaryDirectory() as raw:
        root = _catalogue(pathlib.Path(raw) / "c", [])
        (root / "packs" / "new-name").mkdir(parents=True)
        _expect(root, 1, "'new-name'")


def test_missing_map_refuses() -> None:
    with tempfile.TemporaryDirectory() as raw:
        _expect(pathlib.Path(raw), 2, "missing")


def test_malformed_map_refuses() -> None:
    with tempfile.TemporaryDirectory() as raw:
        _expect(_catalogue(pathlib.Path(raw) / "c", [], "rename = 1\n"), 2, "[[rename]]")


def test_real_map_validates_against_schema() -> None:
    import jsonschema  # noqa: PLC0415 - only this case needs it

    data = tomllib.loads(MAP.read_text(encoding="utf-8"))
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    assert schema["x-spec"] == "docs/specs/repo-governance-rename"
    jsonschema.Draft202012Validator(schema).validate(data)
    assert data == {"schema": 1, "rename": [{"from": "governance-extras", "to": "repo-governance"}]}


def test_schema_rejects_bad_maps() -> None:
    import jsonschema  # noqa: PLC0415 - only this case needs it

    validator = jsonschema.Draft202012Validator(json.loads(SCHEMA.read_text(encoding="utf-8")))
    bad = [
        {"rename": []},
        {"schema": 2, "rename": []},
        {"schema": 1, "rename": [{"from": "a"}]},
        {"schema": 1, "rename": [{"from": "a", "to": "B"}]},
        {"schema": 1, "rename": [{"from": "a", "to": "b", "note": "x"}]},
    ]
    for case in bad:
        assert not validator.is_valid(case), case


def main() -> int:
    return selftest_harness.run_cases(globals(), "test-lint-pack-renames")


if __name__ == "__main__":
    raise SystemExit(main())
