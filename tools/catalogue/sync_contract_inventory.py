#!/usr/bin/env python3
"""Synchronize the packaged public-contract inventory from contracts/."""

# No `from __future__ import annotations`: check_contract_parity.py loads this
# file by path without registering it in sys.modules, which @dataclass needs
# when annotations are strings.
import argparse
import hashlib
import json
import re
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

_REPO_ROOT = Path(__file__).resolve().parents[2]
_CONTRACTS = _REPO_ROOT / "contracts"
_MANIFEST = "catalogue-spec.toml"
_INVENTORY = (
    _REPO_ROOT / "packages" / "agentbundle" / "agentbundle" / "_data" / "public-contracts.txt"
)
_MEMBERS_INVENTORY = _INVENTORY.with_name("catalogue-members.txt")
_RELEASES_DIR = ("releases", "catalogue")
_VERSION_FORM = re.compile(r"^[0-9]+\.[0-9]+$")
_DIGEST_FORM = re.compile(r"^[0-9a-f]{64}$")


class ManifestError(Exception):
    """The catalogue specification manifest is malformed."""


_ROLES = ("member", "bundled", "vendored")


@dataclass(frozen=True)
class ContractRow:
    """One `[[contract]]` row of the manifest."""

    path: str
    role: str
    upstream: str | None

    @property
    def data_name(self) -> str:
        """Name of this contract's packaged copy under `_data/`."""
        if self.role == "vendored":
            return self.path
        return PurePosixPath(self.path).name


def _check_path(
    index: int,
    path: object,
    root_dir: Path,
    label: str | None = None,
    root_name: str = "contracts/",
) -> str:
    """Confine `path` to a regular file under `root_dir`; return it unchanged.

    `label` names the row in every error; it defaults to `contract row {index}`.
    """
    label = label or f"contract row {index}"
    if not isinstance(path, str) or not path:
        raise ManifestError(f"{label}: path must be a non-empty string")
    label = f"{label} ({path})"
    if (
        path.startswith("/")
        or ".." in PurePosixPath(path).parts
        or "\\" in path
        or re.match(r"^[A-Za-z]:", path)
    ):
        raise ManifestError(
            f"{label}: path must be relative, without '..', backslash or drive letter"
        )
    root = root_dir.resolve()
    resolved = (root_dir / path).resolve()
    if not resolved.is_relative_to(root) or not resolved.is_file():
        raise ManifestError(f"{label}: path must resolve to a regular file inside {root_name}")
    return path


@dataclass(frozen=True)
class ReleaseRow:
    """One `[[release]]` row: member and page-source digests are separate key spaces."""

    version: str
    date: str
    adapter_contract: str
    members: dict[str, str]
    pages: dict[str, str]


@dataclass(frozen=True)
class CorrectionRow:
    """One `[[correction]]` row: supersedes page-source digests of one release."""

    version: str
    date: str
    note: str
    supersedes: str
    pages: dict[str, str]


def version_key(version: str) -> tuple[int, int]:
    """Numeric ordering key for a `MAJOR.MINOR` version (so 0.10 sorts above 0.9)."""
    major, minor = version.split(".")
    return int(major), int(minor)


def snapshot_dir(contracts_dir: Path, version: str) -> Path:
    """Directory holding one release's snapshot."""
    return contracts_dir.joinpath(*_RELEASES_DIR, version)


def _digest_table(
    raw: object, label: str, snapshot: Path, version: str, *, allow_empty: bool = False
) -> dict[str, str]:
    """Validate a `{snapshot-relative path: sha256}` table; keys come back normalized."""
    if not isinstance(raw, dict) or (not raw and not allow_empty):
        raise ManifestError(f"{label}: must be a non-empty table of path = digest")
    table: dict[str, str] = {}
    for key, digest in raw.items():
        _check_path(0, key, snapshot, label, f"contracts/releases/catalogue/{version}/")
        if not isinstance(digest, str) or not _DIGEST_FORM.match(digest):
            raise ManifestError(f"{label} ({key}): digest must be 64 lowercase hex characters")
        normal = PurePosixPath(key).as_posix()
        if normal in table:
            raise ManifestError(f"{label} ({key}): duplicate path")
        table[normal] = digest
    return table


def _text_field(raw: dict, name: str, label: str) -> str:
    value = raw.get(name)
    if not isinstance(value, str) or not value:
        raise ManifestError(f"{label}: {name} must be a non-empty string")
    return value


def _version_of(raw: dict, label: str) -> str:
    version = raw.get("version")
    if not isinstance(version, str) or not _VERSION_FORM.match(version):
        raise ManifestError(f"{label}: version must match MAJOR.MINOR, got {version!r}")
    return version


def _parse_releases(
    data: dict, contracts_dir: Path, member_paths: list[str]
) -> tuple[list[ReleaseRow], list[CorrectionRow]]:
    """Parse and validate `[[release]]` and `[[correction]]` rows."""
    raw_releases = data["release"]
    raw_corrections = data.get("correction", [])
    if not isinstance(raw_corrections, list):
        raise ManifestError(f"{_MANIFEST}: 'correction' must be an array of tables")
    releases: list[ReleaseRow] = []
    seen: dict[tuple[int, int], str] = {}
    for index, raw in enumerate(raw_releases):
        label = f"release row {index}"
        if not isinstance(raw, dict):
            raise ManifestError(f"{label}: must be a table")
        version = _version_of(raw, label)
        label = f"release row {index} ({version})"
        if version_key(version) in seen:
            raise ManifestError(f"{label}: duplicate of release row {seen[version_key(version)]}")
        seen[version_key(version)] = version
        snapshot = snapshot_dir(contracts_dir, version)
        date = _text_field(raw, "date", label)
        adapter = _text_field(raw, "adapter_contract", label)
        members = _digest_table(raw.get("members"), f"{label} members", snapshot, version)
        pages = _digest_table(raw.get("pages"), f"{label} pages", snapshot, version)
        shared = sorted(set(members) & set(pages))
        if shared:
            raise ManifestError(f"{label}: members and pages share key {shared[0]!r}")
        for path in member_paths:
            if (snapshot / path).is_file() and path not in members:
                raise ManifestError(f"{label}: members table lacks a digest for {path}")
        releases.append(ReleaseRow(version, date, adapter, members, pages))

    by_version = {row.version: row for row in releases}
    corrections: list[CorrectionRow] = []
    for index, raw in enumerate(raw_corrections):
        label = f"correction row {index}"
        if not isinstance(raw, dict):
            raise ManifestError(f"{label}: must be a table")
        version = _version_of(raw, label)
        label = f"correction row {index} ({version})"
        if "members" in raw:
            raise ManifestError(f"{label}: a correction row carries no members table")
        release = by_version.get(version)
        if release is None:
            raise ManifestError(f"{label}: names a version with no release row")
        pages = _digest_table(
            raw.get("pages"), f"{label} pages", snapshot_dir(contracts_dir, version), version
        )
        outside = sorted(set(pages) - set(release.pages))
        if outside:
            raise ManifestError(f"{label}: pages key {outside[0]!r} is not a release page source")
        corrections.append(
            CorrectionRow(
                version,
                _text_field(raw, "date", label),
                _text_field(raw, "note", label),
                _text_field(raw, "supersedes", label),
                pages,
            )
        )
    _check_supersedes(corrections)
    return releases, corrections


def _check_supersedes(corrections: list[CorrectionRow]) -> None:
    """Require each version's corrections to form one chain rooted at its release.

    A correction's `supersedes` is the version string for the first correction,
    otherwise the `date` of the correction of the same version it replaces.
    """
    for version in sorted({row.version for row in corrections}):
        rows = [row for row in corrections if row.version == version]
        dates = [row.date for row in rows]
        if len(set(dates)) != len(dates):
            raise ManifestError(f"corrections for {version}: duplicate date")
        targets = [row.supersedes for row in rows]
        if len(set(targets)) != len(targets):
            raise ManifestError(f"corrections for {version}: duplicated supersedes link")
        for target in targets:
            if target != version and target not in dates:
                raise ManifestError(f"corrections for {version}: dangling supersedes {target!r}")
        by_target = {row.supersedes: row for row in rows}
        reached, cursor = 0, by_target.get(version)
        while cursor is not None:
            reached += 1
            cursor = by_target.get(cursor.date)
        if reached != len(rows):
            raise ManifestError(
                f"corrections for {version}: supersedes chain is not rooted at the release"
            )


def governing_correction(corrections: list[CorrectionRow], version: str) -> CorrectionRow | None:
    """Head of `version`'s supersedes chain (independent of row order), or None."""
    rows = [row for row in corrections if row.version == version]
    superseded = {row.supersedes for row in rows}
    heads = [row for row in rows if row.date not in superseded]
    return heads[0] if heads else None


def load_releases(contracts_dir: Path) -> tuple[list[ReleaseRow], list[CorrectionRow]]:
    """Validated release and correction rows of `catalogue-spec.toml`."""
    data = _read_manifest(contracts_dir)
    return _parse_releases(data, contracts_dir, _member_paths(data))


def latest_release(releases: list[ReleaseRow]) -> ReleaseRow | None:
    """The highest-version release row; corrections never change it."""
    return max(releases, key=lambda row: version_key(row.version), default=None)


def _member_paths(data: dict) -> list[str]:
    return [
        raw["path"]
        for raw in data.get("contract", [])
        if isinstance(raw, dict)
        and raw.get("role") == "member"
        and isinstance(raw.get("path"), str)
    ]


def sha256_of(path: Path) -> str:
    """SHA-256 hex digest of a file's bytes."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_manifest(contracts_dir: Path) -> dict:
    try:
        with (contracts_dir / _MANIFEST).open("rb") as handle:
            data = tomllib.load(handle)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise ManifestError(f"{_MANIFEST}: cannot read manifest: {exc}") from exc
    if not isinstance(data.get("release"), list):
        raise ManifestError(f"{_MANIFEST}: top-level 'release' key must be an array")
    return data


def load_manifest(contracts_dir: Path) -> list[ContractRow]:
    """Parse and validate `catalogue-spec.toml`, raising `ManifestError`."""
    data = _read_manifest(contracts_dir)
    raw_rows = data.get("contract", [])
    if not isinstance(raw_rows, list):
        raise ManifestError(f"{_MANIFEST}: 'contract' must be an array of tables")
    rows: list[ContractRow] = []
    seen_paths: set[str] = set()
    seen_names: dict[str, str] = {}
    for index, raw in enumerate(raw_rows):
        if not isinstance(raw, dict):
            raise ManifestError(f"contract row {index}: must be a table")
        path = _check_path(index, raw.get("path"), contracts_dir)
        label = f"contract row {index} ({path})"
        role = raw.get("role")
        if role not in _ROLES:
            raise ManifestError(f"{label}: unknown role {role!r}")
        upstream = raw.get("upstream")
        if role == "vendored":
            if not isinstance(upstream, str) or not upstream.startswith("https://"):
                raise ManifestError(f"{label}: vendored row needs an https:// upstream")
            try:
                schema_id = json.loads((contracts_dir / path).read_text(encoding="utf-8")).get(
                    "$id"
                )
            except (ValueError, AttributeError) as exc:
                raise ManifestError(f"{label}: cannot read $id: {exc}") from exc
            if upstream != schema_id:
                raise ManifestError(f"{label}: upstream differs from the file's $id")
        else:
            upstream = None
        if path in seen_paths:
            raise ManifestError(f"{label}: duplicate path")
        seen_paths.add(path)
        row = ContractRow(path, role, upstream)
        if role != "vendored":
            if row.data_name in seen_names:
                raise ManifestError(
                    f"{label}: file name {row.data_name!r} already used by "
                    f"{seen_names[row.data_name]}"
                )
            seen_names[row.data_name] = path
        rows.append(row)
    _parse_releases(data, contracts_dir, [r.path for r in rows if r.role == "member"])
    return rows


def json_schema_members(contracts_dir: Path = _CONTRACTS) -> list[ContractRow]:
    """The manifest's member rows whose path ends in `.json`, in manifest order."""
    return [
        row
        for row in load_manifest(contracts_dir)
        if row.role == "member" and row.path.endswith(".json")
    ]


def _render(contracts_dir: Path = _CONTRACTS) -> str:
    """Sorted `_data/` names of the member and bundled rows, one per line."""
    names = sorted(row.data_name for row in load_manifest(contracts_dir) if row.role != "vendored")
    return "".join(f"{name}\n" for name in names)


def _render_members(contracts_dir: Path = _CONTRACTS) -> str:
    """Sorted `_data/` names of the JSON-schema member rows, one per line."""
    names = sorted(row.data_name for row in json_schema_members(contracts_dir))
    return "".join(f"{name}\n" for name in names)


def _read_or_empty(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def main(
    argv: list[str] | None = None,
    *,
    contracts_dir: Path = _CONTRACTS,
    inventory: Path = _INVENTORY,
    members_inventory: Path | None = None,
) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    if members_inventory is None:
        members_inventory = inventory.with_name(_MEMBERS_INVENTORY.name)

    try:
        expected = _render(contracts_dir)
        expected_members = _render_members(contracts_dir)
    except ManifestError as exc:
        print(f"sync_contract_inventory: FAIL - {exc}", file=sys.stderr)
        return 1
    if args.write:
        inventory.write_text(expected, encoding="utf-8")
        members_inventory.write_text(expected_members, encoding="utf-8")
        print(f"sync_contract_inventory: wrote {inventory} and {members_inventory}")
        return 0

    actual = _read_or_empty(inventory)
    if actual != expected or _read_or_empty(members_inventory) != expected_members:
        print(
            "sync_contract_inventory: FAIL — run with --write",
            file=sys.stderr,
        )
        return 1
    print("sync_contract_inventory: ok — public-contract inventory is current")
    return 0


if __name__ == "__main__":
    sys.exit(main())
