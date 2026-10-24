#!/usr/bin/env python3
"""Check 3, tree half, of the catalogue release gate: releases are append-only.

Every released row, correction row, snapshot path and member digest in the
anchor commit must survive unchanged in the head tree. The anchor lies outside
the pushed commit, chosen by the event that started the run:

  pull_request          merge base with the base branch (`origin/<base>`)
  push to main          the ref's pre-push value (`before` in the event
                        payload), so every commit in the push is measured
  workflow_dispatch     the head commit's first parent -- the author's own
                        commit, so the run proves self-consistency only
  no / other event      merge base with `origin/main` (every local run)

The check fails closed when the anchor cannot be resolved, or when a pre-push
value is absent or is not an ancestor of the tip. A snapshot page-source edit
is admitted only when the path is a key of that release's `pages` table and
the head's governing correction row carries the new bytes' digest.

Usage:
  python3 tools/catalogue/check_release_immutability.py   # exits 0 ok / 1 fail

Wired into make build-check via tools/repo/build_gate_chain.py. Pure stdlib.
"""

from __future__ import annotations

import importlib.util
import json
import os
import re
import subprocess
import sys
import tomllib
from collections.abc import Mapping
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parents[1]
_MANIFEST = "contracts/catalogue-spec.toml"
_RELEASES = "contracts/releases/catalogue"
_SHA = re.compile(r"^[0-9a-f]{40}([0-9a-f]{24})?$")
_REF = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9._/-]*$")
_VERSION = re.compile(r"^[0-9]+\.[0-9]+$")
_DEFAULT_BASE = "main"


def _load_generator():  # type: ignore[no-untyped-def]
    """Load the sibling generator by explicit path, independent of sys.path."""
    path = _HERE / "sync_contract_inventory.py"
    spec = importlib.util.spec_from_file_location("sync_contract_inventory", path)
    if spec is None or spec.loader is None:  # pragma: no cover - defensive
        raise ImportError(f"cannot load contract inventory generator: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


_generator = _load_generator()


class AnchorError(Exception):
    """The anchor commit cannot be established, so the check cannot run."""


def _git(root: Path, *args: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(  # noqa: S603 - fixed argv, no shell
        ["git", "-C", str(root), *args], capture_output=True, check=False
    )


def _commit(root: Path, rev: str) -> str | None:
    """Full SHA of `rev` when it names a commit, else None."""
    out = _git(root, "rev-parse", "--verify", "--quiet", f"{rev}^{{commit}}")
    return out.stdout.decode().strip() if out.returncode == 0 else None


def _merge_base_anchor(root: Path, base_name: str) -> tuple[str, str]:
    if not _REF.match(base_name):
        raise AnchorError(f"base branch name {base_name!r} is not a plain ref name")
    base = f"origin/{base_name}"
    if _commit(root, base) is None:
        raise AnchorError(f"base ref {base} is unreachable, so nothing can be measured")
    out = _git(root, "merge-base", base, "HEAD")
    sha = out.stdout.decode().strip()
    if out.returncode != 0 or not sha:
        raise AnchorError(f"no merge base between {base} and HEAD")
    return sha, f"merge base with {base}"


def _pre_push_value(env: Mapping[str, str]) -> str | None:
    path = env.get("GITHUB_EVENT_PATH")
    if not path:
        return None
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    before = payload.get("before") if isinstance(payload, dict) else None
    return before if isinstance(before, str) else None


def pick_anchor(root: Path, env: Mapping[str, str]) -> tuple[str, str, bool]:
    """(anchor sha, description, self_consistency_only) for the event in `env`."""
    event = env.get("GITHUB_EVENT_NAME", "")
    if event == "workflow_dispatch":
        parent = _commit(root, "HEAD^")
        if parent is None:
            raise AnchorError("workflow_dispatch: HEAD has no first parent to anchor on")
        return parent, "first parent of the pushed commit", True
    if event == "push" and env.get("GITHUB_REF") == "refs/heads/main":
        before = _pre_push_value(env)
        if before is None or not _SHA.match(before) or set(before) == {"0"}:
            raise AnchorError(f"push to main: pre-push value {before!r} is absent or not a commit")
        sha = _commit(root, before)
        if sha is None:
            raise AnchorError(f"push to main: pre-push commit {before} is not in this clone")
        if _git(root, "merge-base", "--is-ancestor", sha, "HEAD").returncode != 0:
            raise AnchorError(f"push to main: pre-push commit {before} is not an ancestor of HEAD")
        return sha, "pre-push value of main", False
    base = env.get("GITHUB_BASE_REF") if event == "pull_request" else None
    sha, desc = _merge_base_anchor(root, base or _DEFAULT_BASE)
    return sha, desc, False


def _rows(data: dict) -> tuple[dict[str, object], dict[tuple[str, str], object]]:
    """Release rows by version and correction rows by (version, date), unvalidated.

    Validation is check 1's job; this check only compares what the anchor
    published with what the head still carries, so a malformed row compares unequal.
    """
    releases: dict[str, object] = {}
    for raw in data.get("release", []):
        row = _generator.ReleaseRow(
            raw["version"], raw["date"], raw["adapter_contract"],
            dict(raw["members"]), dict(raw["pages"]),
        )  # fmt: skip
        releases[row.version] = row
    corrections: dict[tuple[str, str], object] = {}
    for raw in data.get("correction", []):
        crow = _generator.CorrectionRow(
            raw["version"], raw["date"], raw["note"], raw["supersedes"], dict(raw["pages"])
        )
        corrections[(crow.version, crow.date)] = crow
    return releases, corrections


def _anchor_manifest(root: Path, anchor: str) -> dict:
    """The manifest as the anchor held it; `{}` only when the anchor has no manifest.

    Absence is established by listing the path in the anchor's tree, never inferred
    from a failed read: an unreadable anchor must stop the check, not pass it.
    """
    listing = _git(root, "ls-tree", "--name-only", anchor, "--", _MANIFEST)
    if listing.returncode != 0:
        raise AnchorError(f"cannot list the anchor tree: {listing.stderr.decode().strip()}")
    if not listing.stdout.strip():
        return {}  # the manifest was absent at the anchor, so nothing was released
    out = _git(root, "show", f"{anchor}:{_MANIFEST}")
    if out.returncode != 0:
        raise AnchorError(f"cannot read the anchor manifest: {out.stderr.decode().strip()}")
    return tomllib.loads(out.stdout.decode("utf-8"))


def _snapshot_files(root: Path, anchor: str, version: str) -> list[str]:
    """Snapshot-relative paths under `version` at the anchor."""
    prefix = f"{_RELEASES}/{version}/"
    out = _git(root, "ls-tree", "-r", "--name-only", anchor, "--", prefix)
    if out.returncode != 0:
        detail = out.stderr.decode().strip()
        raise AnchorError(f"cannot list snapshot {version} at the anchor: {detail}")
    return [line[len(prefix) :] for line in out.stdout.decode().splitlines() if line]


def compare(root: Path, anchor: str) -> list[str]:
    """Every way the head tree under `root` fails to preserve the anchor's releases."""
    failures: list[str] = []
    try:
        old_releases, old_corrections = _rows(_anchor_manifest(root, anchor))
    except (KeyError, TypeError, ValueError) as exc:
        raise AnchorError(f"anchor manifest is unreadable: {exc!r}") from exc
    try:
        with (root / _MANIFEST).open("rb") as handle:
            new_releases, new_corrections = _rows(tomllib.load(handle))
    except (OSError, KeyError, TypeError, ValueError) as exc:
        return [f"  head manifest cannot be compared with the anchor: {exc!r}"]

    for version, old in old_releases.items():
        if version not in new_releases:
            failures.append(f"  release row {version} was deleted")
        elif new_releases[version] != old:
            failures.append(f"  release row {version} was edited")
    for key, old in old_corrections.items():
        if key not in new_corrections:
            failures.append(f"  correction row {key[0]} ({key[1]}) was deleted")
        elif new_corrections[key] != old:
            failures.append(f"  correction row {key[0]} ({key[1]}) was edited")

    corrections = list(new_corrections.values())
    for version, old in old_releases.items():
        if not _VERSION.match(version):
            raise AnchorError(f"anchor release version {version!r} is not MAJOR.MINOR")
        for rel in _snapshot_files(root, anchor, version):
            failures += _compare_file(root, anchor, version, old, rel, corrections)
    return failures


def _compare_file(
    root: Path, anchor: str, version: str, old: object, rel: str, corrections: list
) -> list[str]:
    where = f"snapshot {version}/{rel}"
    path = root / _RELEASES / version / rel
    if path.is_symlink() or not path.is_file():
        return [f"  {where} was deleted"]
    old_bytes = _git(root, "show", f"{anchor}:{_RELEASES}/{version}/{rel}").stdout
    new_bytes = path.read_bytes()
    if new_bytes == old_bytes:
        return []
    if rel in old.members or rel not in old.pages:  # type: ignore[attr-defined]
        return [f"  {where} was edited and is not a page source"]
    governing = _generator.governing_correction(corrections, version)
    digest = _generator.sha256_of(path)
    if governing is None or governing.pages.get(rel) != digest:
        return [f"  {where} page source was edited with no governing correction row for it"]
    return []


def run(root: Path, env: Mapping[str, str]) -> tuple[list[str], str]:
    """Failures and the one-line header naming the event and anchor measured."""
    event = env.get("GITHUB_EVENT_NAME") or "none"
    anchor, desc, self_only = pick_anchor(root, env)
    header = f"check_release_immutability: event={event} anchor={anchor} ({desc})"
    if self_only:
        header += (
            "; self-consistency evidence only - the anchor is the author's own "
            "commit, so this run is not a tamper check"
        )
    return compare(root, anchor), header


def main(*, root: Path = _ROOT, env: Mapping[str, str] | None = None) -> int:
    """Print the verdict and return 0 or 1."""
    environ = os.environ if env is None else env
    try:
        failures, header = run(root, environ)
    except AnchorError as exc:
        event = environ.get("GITHUB_EVENT_NAME") or "none"
        print(f"check_release_immutability: FAIL - event={event}: {exc}", file=sys.stderr)
        return 1
    if failures:
        print(header, file=sys.stderr)
        print("\n".join(failures), file=sys.stderr)
        print(
            "check_release_immutability: FAIL - a released row or snapshot changed",
            file=sys.stderr,
        )
        return 1
    print(f"{header}\ncheck_release_immutability: ok - releases are append-only.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
