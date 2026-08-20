#!/usr/bin/env python3
"""Run repository-specific catalogue leak checks outside AgentBundle."""

from __future__ import annotations

import argparse
import os
import re
import stat
import sys
import tomllib
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="strict")
sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

_APM_PATTERNS = (
    (re.compile(r"agent-ready-repo"), "catalogue name 'agent-ready-repo'"),
    (re.compile(r"RFC-00\d\d"), "catalogue RFC reference (RFC-NNNN)"),
    (re.compile(r"K-00\d\d"), "catalogue knowledge entry (K-NNNN)"),
)
_SEED_PATTERNS = (
    *_APM_PATTERNS,
    (
        re.compile(
            r"\b(distribution-adapters|self-hosting|agent-spec-cli|"
            r"user-scope-hooks|converters-pack|claude-plugins-install-route|"
            r"codex-native-skills|apm-install-route-parity|skill-secrets|"
            r"wire-session-start-hook|kiro-ide-hook|windows-ci-bundler|"
            r"windows-hooks-phase3)\b"
        ),
        "catalogue spec name",
    ),
)
_SENTINEL_RE = re.compile(
    r"^\s*<!--\s*seed-content-lint-ignore:\s*([^>]+?)\s*-->\s*$"
)


class UnsafeTreeError(ValueError):
    """A scanned entry cannot be proven to be a confined regular file."""


def _path_is_junction(path: Path) -> bool:
    """Return whether *path* is a Windows junction, failing closed on errors."""
    checker = getattr(path, "is_junction", None)
    if checker is None:
        return False
    try:
        return bool(checker())
    except OSError:
        return True


def _relative(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return "<outside-root>"


def _entry_present(root: Path, path: Path, label: str) -> bool:
    """Return presence without following links; fail closed on inspection errors."""
    try:
        path.lstat()
    except FileNotFoundError:
        return False
    except OSError as exc:
        raise UnsafeTreeError(
            f"cannot inspect {label}: {_relative(root, path)}"
        ) from exc
    return True


def _read_confined_utf8(root: Path, path: Path) -> str:
    """Read one confined single-link regular file without following links."""
    relative = _relative(root, path)
    try:
        before = path.lstat()
    except OSError as exc:
        raise UnsafeTreeError(f"cannot inspect {relative}") from exc
    if not stat.S_ISREG(before.st_mode):
        raise UnsafeTreeError(f"not a regular file: {relative}")
    if before.st_nlink > 1:
        raise UnsafeTreeError(f"hard link not allowed: {relative}")
    try:
        path.resolve(strict=True).relative_to(root.resolve(strict=True))
    except (OSError, RuntimeError, ValueError) as exc:
        raise UnsafeTreeError(f"path escapes its scan root: {relative}") from exc

    flags = os.O_RDONLY
    for name in ("O_CLOEXEC", "O_NOFOLLOW", "O_NONBLOCK"):
        flags |= getattr(os, name, 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise UnsafeTreeError(f"cannot open safely: {relative}") from exc
    try:
        after = os.fstat(descriptor)
        if not stat.S_ISREG(after.st_mode):
            raise UnsafeTreeError(f"not a regular file: {relative}")
        if after.st_nlink > 1:
            raise UnsafeTreeError(f"hard link not allowed: {relative}")
        if (before.st_dev, before.st_ino) != (after.st_dev, after.st_ino):
            raise UnsafeTreeError(f"file changed while opening: {relative}")
        with os.fdopen(descriptor, "rb") as handle:
            descriptor = -1
            raw = handle.read()
    finally:
        if descriptor >= 0:
            os.close(descriptor)
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise UnsafeTreeError(f"invalid UTF-8: {relative}") from exc


def _require_real_directory(root: Path, path: Path) -> None:
    relative = _relative(root, path)
    try:
        metadata = path.lstat()
    except OSError as exc:
        raise UnsafeTreeError(f"cannot inspect directory: {relative}") from exc
    if (
        stat.S_ISLNK(metadata.st_mode)
        or _path_is_junction(path)
        or not stat.S_ISDIR(metadata.st_mode)
    ):
        raise UnsafeTreeError(f"not a real directory: {relative}")
    try:
        path.resolve(strict=True).relative_to(root.resolve(strict=True))
    except (OSError, RuntimeError, ValueError) as exc:
        raise UnsafeTreeError(f"directory escapes repository root: {relative}") from exc


def _walk_files(repository_root: Path, scan_root: Path) -> list[Path]:
    """Return confined files beneath *scan_root*, refusing linked traversal."""
    _require_real_directory(repository_root, scan_root)
    files: list[Path] = []
    pending = [scan_root]
    while pending:
        directory = pending.pop()
        try:
            entries = sorted(os.scandir(directory), key=lambda entry: entry.name)
        except OSError as exc:
            raise UnsafeTreeError(
                f"cannot enumerate directory: {_relative(repository_root, directory)}"
            ) from exc
        for entry in entries:
            path = Path(entry.path)
            try:
                metadata = entry.stat(follow_symlinks=False)
            except OSError as exc:
                raise UnsafeTreeError(
                    f"cannot inspect entry: {_relative(repository_root, path)}"
                ) from exc
            if stat.S_ISLNK(metadata.st_mode) or _path_is_junction(path):
                raise UnsafeTreeError(
                    f"linked entry not allowed: {_relative(repository_root, path)}"
                )
            if stat.S_ISDIR(metadata.st_mode):
                pending.append(path)
            elif stat.S_ISREG(metadata.st_mode):
                files.append(path)
            else:
                raise UnsafeTreeError(
                    f"special entry not allowed: {_relative(repository_root, path)}"
                )
    return sorted(files)


def _scan_lines(
    repository_root: Path,
    scan_root: Path,
    patterns: tuple[tuple[re.Pattern[str], str], ...],
    *,
    markdown_only: bool,
    seed_exemptions: bool,
) -> list[str]:
    """Scan eligible UTF-8 files without weakening tree-safety checks."""
    findings: list[str] = []
    for path in _walk_files(repository_root, scan_root):
        if markdown_only and path.suffix.lower() != ".md":
            continue
        text = _read_confined_utf8(scan_root, path)
        in_fence = False
        ignore_next_content = False
        for line_number, line in enumerate(text.splitlines(), 1):
            stripped = line.strip()
            if seed_exemptions and stripped.startswith("```"):
                in_fence = not in_fence
                continue
            if seed_exemptions and _SENTINEL_RE.fullmatch(line):
                ignore_next_content = True
                continue
            if seed_exemptions and (in_fence or not stripped):
                continue
            if seed_exemptions and ignore_next_content:
                ignore_next_content = False
                continue
            for pattern, label in patterns:
                if pattern.search(line):
                    findings.append(
                        f"{_relative(repository_root, path)}:{line_number}: leaked {label}"
                    )
    return findings


def verify_host_checks(root: Path) -> list[str]:
    """Return host-policy findings for *root*."""
    root = root.resolve(strict=True)
    findings: list[str] = []
    packs_root = root / "packs"
    try:
        if not _entry_present(root, packs_root, "packs root"):
            return findings
        _require_real_directory(root, packs_root)
        for entry in sorted(os.scandir(packs_root), key=lambda item: item.name):
            pack_dir = Path(entry.path)
            metadata = entry.stat(follow_symlinks=False)
            if stat.S_ISLNK(metadata.st_mode) or _path_is_junction(pack_dir):
                raise UnsafeTreeError(f"linked pack not allowed: {_relative(root, pack_dir)}")
            if not stat.S_ISDIR(metadata.st_mode) or entry.name.startswith("_"):
                continue
            manifest = pack_dir / "pack.toml"
            if not _entry_present(root, manifest, "manifest"):
                continue
            contract = tomllib.loads(_read_confined_utf8(pack_dir, manifest))
            pack_table = contract.get("pack", {})
            if not isinstance(pack_table, dict) or pack_table.get("lint-seeds") is not True:
                continue
            seeds = pack_dir / "seeds"
            if _entry_present(root, seeds, "seed root"):
                findings.extend(
                    _scan_lines(
                        root,
                        seeds,
                        _SEED_PATTERNS,
                        markdown_only=False,
                        seed_exemptions=True,
                    )
                )

        core = packs_root / "core"
        apm = core / ".apm"
        apm_skills = apm / "skills"
        if _entry_present(root, apm, "core .apm root"):
            _require_real_directory(root, core)
            _require_real_directory(root, apm)
        if _entry_present(root, apm_skills, "core skills root"):
            _require_real_directory(root, apm_skills)
            findings.extend(
                _scan_lines(
                    root,
                    apm_skills,
                    _APM_PATTERNS,
                    markdown_only=True,
                    seed_exemptions=False,
                )
            )
    except (OSError, RuntimeError, tomllib.TOMLDecodeError, UnsafeTreeError) as exc:
        findings.append(f"unsafe catalogue tree: {exc}")
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)
    try:
        findings = verify_host_checks(args.root)
    except (OSError, RuntimeError) as exc:
        findings = [f"cannot inspect catalogue root: {exc}"]
    for finding in findings:
        print(f"host catalogue check: {finding}", file=sys.stderr)
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
