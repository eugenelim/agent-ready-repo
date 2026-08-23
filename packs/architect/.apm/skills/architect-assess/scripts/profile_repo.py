#!/usr/bin/env python3
"""Produce bounded, deterministic repository evidence signals.

This helper never executes repository code. It walks an explicit confined root,
classifies evidence surfaces, extracts exact Python imports with ``ast``, and
optionally reads current Git history. It emits signals for an assessor; it does
not infer architecture, severity, or risk.
"""

from __future__ import annotations

import argparse
import ast
import contextlib
import json
import os
import queue
import secrets
import stat
import subprocess
import sys
import threading
import time
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Sequence

try:
    from agentbundle.catalogue_tooling.file_safety import (
        read_confined_regular_file as catalogue_read_confined_regular_file,
    )
    from agentbundle.catalogue_tooling.file_safety import (
        validate_confined_directory as catalogue_validate_confined_directory,
    )
except ImportError:  # Projected packs intentionally work without agentbundle.
    catalogue_read_confined_regular_file = None
    catalogue_validate_confined_directory = None


SCHEMA_VERSION = "architect-repo-profile.v1"
DEFAULT_MAX_FILES = 20_000
DEFAULT_MAX_ENTRIES = 200_000
DEFAULT_MAX_FILE_BYTES = 1_048_576
DEFAULT_MAX_SECONDS = 30.0
DEFAULT_GIT_COMMITS = 200
DEFAULT_MAX_GIT_BYTES = 4_194_304
DEFAULT_MAX_GIT_PATHS = 50_000

SOURCE_SUFFIXES = {
    ".c",
    ".cc",
    ".clj",
    ".cpp",
    ".cs",
    ".dart",
    ".ex",
    ".exs",
    ".go",
    ".java",
    ".js",
    ".jsx",
    ".kt",
    ".kts",
    ".php",
    ".py",
    ".rb",
    ".rs",
    ".scala",
    ".swift",
    ".ts",
    ".tsx",
}
MANIFEST_NAMES = {
    "Cargo.toml",
    "Gemfile",
    "go.mod",
    "package.json",
    "pom.xml",
    "pyproject.toml",
    "requirements.txt",
    "settings.gradle",
    "settings.gradle.kts",
}
CI_PARTS = {".github", ".gitlab", ".circleci", "azure-pipelines.yml", "Jenkinsfile"}
DEPLOY_PARTS = {
    "Dockerfile",
    "compose.yml",
    "docker-compose.yml",
    "helm",
    "k8s",
    "kubernetes",
    "terraform",
    "pulumi",
    "cdk",
}
SCHEMA_PARTS = {"schema", "schemas", "migration", "migrations", "alembic", "prisma"}
OPS_PARTS = {"runbook", "runbooks", "operations", "ops", "slo", "slos", "monitoring"}
TEST_PARTS = {"test", "tests", "spec", "specs", "__tests__"}
DOC_PARTS = {"doc", "docs", "documentation"}
VENDORED_PARTS = {"vendor", "vendors", "third_party", "third-party", "node_modules"}
GENERATED_PARTS = {"generated", "gen", "dist", "build", "target", ".next"}
FIXTURE_PARTS = {"fixture", "fixtures", "testdata", "snapshots", "__snapshots__"}
EXAMPLE_PARTS = {"example", "examples", "sample", "samples", "demo", "demos"}
SKIP_DIRECTORY_NAMES = {".git", ".hg", ".svn", ".tox", ".venv", "venv", "__pycache__"}
PROTECTED_DIRECTORY_NAMES = {
    ".aws",
    ".gnupg",
    ".kube",
    ".mozilla",
    ".ssh",
    "keychains",
}
PROTECTED_SUFFIXES = {".key", ".keystore", ".p12", ".pem", ".pfx"}


class ProfileError(ValueError):
    """Raised when a profile boundary cannot be inspected safely."""


@dataclass(frozen=True)
class Limits:
    """Finite work limits for one profile run."""

    max_files: int = DEFAULT_MAX_FILES
    max_file_bytes: int = DEFAULT_MAX_FILE_BYTES
    max_seconds: float = DEFAULT_MAX_SECONDS
    git_commits: int = DEFAULT_GIT_COMMITS
    max_entries: int = DEFAULT_MAX_ENTRIES
    max_git_bytes: int = DEFAULT_MAX_GIT_BYTES
    max_git_paths: int = DEFAULT_MAX_GIT_PATHS


@dataclass
class WorkBudget:
    """One deadline and entry budget shared by every profiling phase."""

    deadline: float
    max_entries: int
    entries_seen: int = 0

    def expired(self) -> bool:
        """Return whether the shared wall-clock deadline has elapsed."""

        return time.monotonic() >= self.deadline

    def remaining_seconds(self, ceiling: float | None = None) -> float:
        """Return positive remaining time, optionally capped by *ceiling*."""

        remaining = max(0.0, self.deadline - time.monotonic())
        return min(remaining, ceiling) if ceiling is not None else remaining

    def admit_entry(self) -> bool:
        """Charge one directory entry and return whether it is within budget."""

        if self.entries_seen >= self.max_entries:
            return False
        self.entries_seen += 1
        return True


@dataclass(frozen=True)
class Entry:
    """A safely inspected regular file and its repository-relative path."""

    path: Path
    relative: str
    size: int


def _is_reparse_point(result: os.stat_result) -> bool:
    """Return whether *result* is a Windows reparse point."""

    attribute = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    return bool(getattr(result, "st_file_attributes", 0) & attribute)


def _relative(path: Path, root: Path) -> str:
    """Return a normalized repository-relative path or raise safely."""

    try:
        relative = path.relative_to(root).as_posix() or "."
    except ValueError as exc:
        raise ProfileError("path is outside the declared root") from exc
    if not _is_safe_display(relative):
        raise ProfileError("path contains unsafe display characters")
    return relative


def _is_safe_display(value: str) -> bool:
    """Return whether repository-controlled text is safe in JSON and Markdown."""

    try:
        value.encode("utf-8", errors="strict")
    except UnicodeEncodeError:
        return False
    for character in value:
        codepoint = ord(character)
        if (
            character == "`"
            or codepoint < 0x20
            or 0x7F <= codepoint <= 0x9F
            or codepoint in {0x2028, 0x2029}
            or 0x202A <= codepoint <= 0x202E
            or 0x2066 <= codepoint <= 0x2069
            or 0xD800 <= codepoint <= 0xDFFF
        ):
            return False
    return True


def _is_protected_path(path: Path, root: Path) -> bool:
    """Return whether *path* belongs to a credential or browser-profile class."""

    try:
        path.relative_to(root)
    except ValueError:
        return True
    # Inspect canonical absolute components as well as the repo-relative path.
    # The absolute form is what catches a selected root that is itself a
    # protected directory rather than merely containing one.
    lowered = tuple(part.casefold() for part in path.parts)
    name = lowered[-1] if lowered else ""
    suffix = Path(name).suffix
    if any(part in PROTECTED_DIRECTORY_NAMES for part in lowered):
        return True
    if suffix in PROTECTED_SUFFIXES or name.startswith("privatekey"):
        return True
    if name == ".env" or name.startswith(".env."):
        return True
    if name in {".npmrc", ".pypirc", ".dockercfg"}:
        return True
    if ".docker" in lowered and name == "config.json":
        return True
    if ".cargo" in lowered and name == "credentials":
        return True
    if ".pip" in lowered and name == "pip.conf":
        return True
    if ".git" in lowered and name == "credentials":
        return True
    browser_names = {
        "chromium",
        "firefox",
        "google chrome",
        "google-chrome",
        "microsoft edge",
        "microsoft-edge",
    }
    parts = set(lowered)
    return (
        any(part in browser_names for part in lowered)
        or {"google", "chrome"} <= parts
        or {"microsoft", "edge"} <= parts
        or (".config" in lowered and "gcloud" in lowered)
    )


def resolve_root(root: Path) -> Path:
    """Resolve and validate an explicit repository root."""

    try:
        resolved = root.expanduser().resolve(strict=True)
        inspected = resolved.lstat()
    except (OSError, RuntimeError) as exc:
        raise ProfileError("declared root cannot be resolved safely") from exc
    if not stat.S_ISDIR(inspected.st_mode) or _is_reparse_point(inspected):
        raise ProfileError("declared root is not a safe directory")
    if _is_protected_path(resolved, resolved):
        raise ProfileError("declared root is protected and cannot be profiled")
    return resolved


def _inspect_directory(root: Path, path: Path) -> os.stat_result:
    """Validate a directory immediately before traversal."""

    relative = _relative(path, root)
    try:
        inspected = path.lstat()
        resolved = path.resolve(strict=True)
        resolved.relative_to(root)
    except (OSError, RuntimeError, ValueError) as exc:
        raise ProfileError(f"directory boundary cannot be inspected: {relative}") from exc
    if (
        not stat.S_ISDIR(inspected.st_mode)
        or stat.S_ISLNK(inspected.st_mode)
        or _is_reparse_point(inspected)
    ):
        raise ProfileError(f"directory boundary is unsafe: {relative}")
    if catalogue_validate_confined_directory is not None:
        try:
            catalogue_validate_confined_directory(root, path)
        except (ValueError, OSError, RuntimeError) as exc:
            raise ProfileError(f"directory boundary is unsafe: {relative}") from exc
    return inspected


def _safe_read(root: Path, entry: Entry, max_bytes: int) -> bytes:
    """Read a confined, unchanged, single-link regular file without following links."""

    relative = entry.relative
    if catalogue_read_confined_regular_file is not None:
        try:
            return catalogue_read_confined_regular_file(root, entry.path, max_bytes=max_bytes)
        except (ValueError, OSError, RuntimeError) as exc:
            raise ProfileError(f"file cannot be read safely: {relative}") from exc
    try:
        before = entry.path.lstat()
        entry.path.resolve(strict=True).relative_to(root)
    except (OSError, RuntimeError, ValueError) as exc:
        raise ProfileError(f"file cannot be inspected safely: {relative}") from exc
    if not stat.S_ISREG(before.st_mode) or _is_reparse_point(before) or before.st_nlink > 1:
        raise ProfileError(f"file is not a confined single-link regular file: {relative}")
    if before.st_size > max_bytes:
        raise ProfileError(f"file exceeds byte limit: {relative}")

    flags = os.O_RDONLY
    for option in ("O_CLOEXEC", "O_NOFOLLOW", "O_NONBLOCK"):
        flags |= getattr(os, option, 0)
    descriptor = -1
    try:
        descriptor = os.open(entry.path, flags)
        after = os.fstat(descriptor)
        if (
            not stat.S_ISREG(after.st_mode)
            or _is_reparse_point(after)
            or after.st_nlink > 1
            or (before.st_dev, before.st_ino) != (after.st_dev, after.st_ino)
        ):
            raise ProfileError(f"file changed or became unsafe: {relative}")
        with os.fdopen(descriptor, "rb") as handle:
            descriptor = -1
            data = handle.read(max_bytes + 1)
    except ProfileError:
        raise
    except OSError as exc:
        raise ProfileError(f"file cannot be opened safely: {relative}") from exc
    finally:
        if descriptor >= 0:
            os.close(descriptor)
    if len(data) > max_bytes:
        raise ProfileError(f"file changed beyond byte limit: {relative}")
    return data


def _walk(
    root: Path, limits: Limits, budget: WorkBudget
) -> tuple[list[Entry], list[dict[str, str]], list[str]]:
    """Walk *root* without following unsafe entries and return visible limits."""

    pending = [root]
    visited: set[tuple[int, int]] = set()
    entries: list[Entry] = []
    exclusions: list[dict[str, str]] = []
    limit_reasons: list[str] = []

    while pending:
        if budget.expired():
            limit_reasons.append("elapsed work limit reached; remaining directories uncovered")
            break
        current = pending.pop()
        inspected_dir = _inspect_directory(root, current)
        identity = (inspected_dir.st_dev, inspected_dir.st_ino)
        if identity in visited:
            exclusions.append({"path": _relative(current, root), "reason": "directory loop"})
            continue
        visited.add(identity)
        try:
            with os.scandir(current) as iterator:
                children: list[os.DirEntry[str]] = []
                for child in iterator:
                    if budget.expired():
                        limit_reasons.append(
                            "elapsed work limit reached; remaining directories uncovered"
                        )
                        pending.clear()
                        break
                    if not budget.admit_entry():
                        limit_reasons.append(
                            "directory entry limit reached; remaining entries uncovered"
                        )
                        pending.clear()
                        break
                    children.append(child)
                children.sort(key=lambda item: item.name, reverse=True)
        except OSError as exc:
            raise ProfileError(
                f"directory cannot be traversed safely: {_relative(current, root)}"
            ) from exc

        for child in children:
            child_path = Path(child.path)
            if _is_protected_path(child_path, root):
                exclusions.append({
                    "path": "[protected]",
                    "reason": "protected path excluded before inventory",
                })
                continue
            try:
                relative = _relative(child_path, root)
            except ProfileError:
                exclusions.append({
                    "path": "[unsafe-path]",
                    "reason": "unsafe display path excluded before inventory",
                })
                continue
            try:
                inspected = child.stat(follow_symlinks=False)
            except OSError:
                exclusions.append({"path": relative, "reason": "inspection denied"})
                continue
            if stat.S_ISLNK(inspected.st_mode) or _is_reparse_point(inspected):
                exclusions.append({"path": relative, "reason": "link-like entry"})
                continue
            if stat.S_ISDIR(inspected.st_mode):
                if child.name in SKIP_DIRECTORY_NAMES:
                    exclusions.append({"path": relative, "reason": "excluded metadata/cache"})
                else:
                    pending.append(child_path)
                continue
            if not stat.S_ISREG(inspected.st_mode) or inspected.st_nlink > 1:
                exclusions.append({"path": relative, "reason": "non-regular or hard-linked entry"})
                continue
            if len(entries) >= limits.max_files:
                limit_reasons.append("file count limit reached; remaining entries uncovered")
                pending.clear()
                break
            entries.append(Entry(child_path, relative, inspected.st_size))

    entries.sort(key=lambda item: item.relative)
    exclusions.sort(key=lambda item: (item["path"], item["reason"]))
    return entries, exclusions, sorted(set(limit_reasons))


def _path_tags(relative: str) -> list[str]:
    """Classify content that can distort architecture signals."""

    parts = {part.lower() for part in PurePosixPath(relative).parts}
    tags: list[str] = []
    for tag, candidates in (
        ("vendored", VENDORED_PARTS),
        ("generated", GENERATED_PARTS),
        ("fixture", FIXTURE_PARTS),
        ("example", EXAMPLE_PARTS),
    ):
        if parts & candidates:
            tags.append(tag)
    return tags


def _surface_kinds(relative: str) -> list[str]:
    """Return probable evidence-surface categories for a path."""

    path = PurePosixPath(relative)
    parts = {part.lower() for part in path.parts}
    name = path.name
    lower_name = name.lower()
    suffix = path.suffix.lower()
    kinds: list[str] = []
    if suffix in SOURCE_SUFFIXES:
        kinds.append("source")
    if parts & TEST_PARTS or lower_name.startswith("test_") or lower_name.endswith("_test.py"):
        kinds.append("tests")
    if parts & DOC_PARTS or suffix in {".md", ".rst", ".adoc"}:
        kinds.append("documentation")
    if name in MANIFEST_NAMES or lower_name.endswith((".lock", ".csproj", ".sln")):
        kinds.append("manifest")
    if parts & {item.lower() for item in CI_PARTS} or name in CI_PARTS:
        kinds.append("ci_cd")
    if (
        parts & {item.lower() for item in DEPLOY_PARTS}
        or name in DEPLOY_PARTS
        or suffix in {".tf", ".bicep"}
    ):
        kinds.append("deployment_iac")
    if parts & SCHEMA_PARTS or suffix in {".sql", ".graphql", ".proto"}:
        kinds.append("schema_migration")
    if parts & OPS_PARTS:
        kinds.append("operations")
    if lower_name.endswith((".yaml", ".yml", ".toml", ".json", ".ini", ".cfg")):
        kinds.append("configuration")
    return sorted(set(kinds))


def _decode_python(data: bytes, relative: str) -> tuple[str | None, str | None]:
    """Decode Python source without exposing its content in diagnostics."""

    try:
        return data.decode("utf-8"), None
    except UnicodeDecodeError:
        return None, f"decode failed: {relative}"


def _python_imports(source: str, relative: str) -> tuple[list[dict[str, Any]], str | None]:
    """Extract exact import statements from Python source."""

    try:
        tree = ast.parse(source, filename=relative)
    except (SyntaxError, ValueError):
        return [], f"AST parse failed: {relative}"
    imports: list[dict[str, Any]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append({
                    "file": relative,
                    "kind": "import",
                    "module": alias.name,
                    "alias": alias.asname,
                    "line": node.lineno,
                    "confidence": "exact_ast",
                })
        elif isinstance(node, ast.ImportFrom):
            module = "." * node.level + (node.module or "")
            for alias in node.names:
                imports.append({
                    "file": relative,
                    "kind": "from",
                    "module": module,
                    "name": alias.name,
                    "alias": alias.asname,
                    "line": node.lineno,
                    "confidence": "exact_ast",
                })
    imports.sort(
        key=lambda item: (
            item["file"],
            item["line"],
            item["kind"],
            item["module"],
            item.get("name") or "",
        )
    )
    return imports, None


def _git_churn(
    root: Path,
    commits: int,
    budget: WorkBudget,
    max_bytes: int,
    max_paths: int,
) -> tuple[list[dict[str, Any]], str | None]:
    """Return bounded path churn from current local refs without updating Git state."""

    if commits <= 0:
        return [], "git history disabled by limit"
    command = [
        "git",
        "-c",
        "core.quotepath=false",
        "log",
        "--format=",
        "--name-only",
        "-z",
        "-n",
        str(commits),
        "--",
        ".",
    ]
    if budget.expired():
        return [], "git history skipped because elapsed work limit was reached"
    try:
        process = subprocess.Popen(
            command,
            cwd=root,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
    except (FileNotFoundError, OSError, subprocess.SubprocessError):
        return [], "git history unavailable"
    assert process.stdout is not None
    chunks: queue.Queue[bytes | None] = queue.Queue(maxsize=2)

    def _read_stdout() -> None:
        """Feed bounded chunks to the controlling thread."""

        try:
            while True:
                chunk = process.stdout.read(65_536)
                chunks.put(chunk or None)
                if not chunk:
                    return
        except (OSError, ValueError):
            chunks.put(None)

    reader = threading.Thread(target=_read_stdout, name="architect-profile-git", daemon=True)
    reader.start()
    captured = bytearray()
    diagnostic: str | None = None
    while True:
        remaining = budget.remaining_seconds(10.0)
        if remaining <= 0:
            diagnostic = "git history partial: elapsed work limit reached"
            break
        try:
            chunk = chunks.get(timeout=min(0.05, remaining))
        except queue.Empty:
            if process.poll() is not None and not reader.is_alive():
                break
            continue
        if chunk is None:
            break
        if len(captured) + len(chunk) > max_bytes:
            available = max(0, max_bytes - len(captured))
            captured.extend(chunk[:available])
            diagnostic = "git history partial: byte limit reached"
            break
        captured.extend(chunk)
    if diagnostic:
        process.kill()
    try:
        returncode = process.wait(timeout=max(0.1, budget.remaining_seconds(1.0)))
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=1)
        diagnostic = diagnostic or "git history partial: process timeout"
        returncode = process.returncode
    if returncode != 0 and diagnostic is None:
        return [], "git history unavailable"
    records = bytes(captured).split(b"\0")
    if diagnostic and records:
        records = records[:-1]
    counts: Counter[str] = Counter()
    for raw in records:
        if not raw:
            continue
        try:
            path = raw.decode("utf-8", errors="strict").strip().replace("\\", "/")
        except UnicodeDecodeError:
            diagnostic = diagnostic or "git history partial: undecodable path excluded"
            continue
        if (
            not path
            or path.startswith("/")
            or ".." in PurePosixPath(path).parts
            or not _is_safe_display(path)
        ):
            diagnostic = diagnostic or "git history partial: unsafe path excluded"
            continue
        if path not in counts and len(counts) >= max_paths:
            diagnostic = diagnostic or "git history partial: path count limit reached"
            break
        counts[path] += 1
    return [
        {"path": path, "changes": count, "source": f"git_log_last_{commits}_commits"}
        for path, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    ], diagnostic


def build_profile(root: Path, limits: Limits | None = None) -> dict[str, Any]:
    """Build a deterministic evidence profile for *root*."""

    active_limits = limits or Limits()
    if (
        active_limits.max_files < 1
        or active_limits.max_entries < 1
        or active_limits.max_file_bytes < 1
        or active_limits.max_seconds <= 0
        or active_limits.git_commits < 0
        or active_limits.max_git_bytes < 1
        or active_limits.max_git_paths < 1
    ):
        raise ProfileError("limits must be positive, except git_commits may be zero")
    resolved_root = resolve_root(root)
    budget = WorkBudget(time.monotonic() + active_limits.max_seconds, active_limits.max_entries)
    entries, exclusions, limit_reasons = _walk(resolved_root, active_limits, budget)

    surfaces: dict[str, list[str]] = defaultdict(list)
    concentration: list[dict[str, Any]] = []
    python_imports: list[dict[str, Any]] = []
    diagnostics: list[str] = []
    tag_counts: Counter[str] = Counter()

    for entry in entries:
        if budget.expired():
            limit_reasons.append("elapsed work limit reached; semantic inspection incomplete")
            break
        tags = _path_tags(entry.relative)
        tag_counts.update(tags)
        for kind in _surface_kinds(entry.relative):
            surfaces[kind].append(entry.relative)
        if "source" in _surface_kinds(entry.relative) and not tags:
            concentration.append({
                "path": entry.relative,
                "bytes": entry.size,
                "source": "filesystem_metadata",
            })
        if entry.relative.endswith(".py") and not tags:
            try:
                data = _safe_read(resolved_root, entry, active_limits.max_file_bytes)
            except ProfileError as exc:
                diagnostics.append(str(exc))
                continue
            source, diagnostic = _decode_python(data, entry.relative)
            if diagnostic:
                diagnostics.append(diagnostic)
                continue
            assert source is not None
            imports, diagnostic = _python_imports(source, entry.relative)
            python_imports.extend(imports)
            if diagnostic:
                diagnostics.append(diagnostic)
            if budget.expired():
                limit_reasons.append("elapsed work limit reached; semantic inspection incomplete")
                break

    for paths in surfaces.values():
        paths.sort()
    concentration.sort(key=lambda item: (-item["bytes"], item["path"]))
    churn, git_diagnostic = _git_churn(
        resolved_root,
        active_limits.git_commits,
        budget,
        active_limits.max_git_bytes,
        active_limits.max_git_paths,
    )
    if git_diagnostic:
        diagnostics.append(git_diagnostic)

    classified_paths = (
        set().union(*(set(paths) for paths in surfaces.values())) if surfaces else set()
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "partial" if limit_reasons or diagnostics or exclusions else "complete",
        "root": ".",
        "limits": {
            "max_files": active_limits.max_files,
            "max_entries": active_limits.max_entries,
            "max_file_bytes": active_limits.max_file_bytes,
            "max_seconds": active_limits.max_seconds,
            "git_commits": active_limits.git_commits,
            "max_git_bytes": active_limits.max_git_bytes,
            "max_git_paths": active_limits.max_git_paths,
        },
        "coverage": {
            "files_seen": len(entries),
            "files_classified": len(classified_paths),
            "limit_reasons": limit_reasons,
            "diagnostics": sorted(set(diagnostics)),
            "excluded": exclusions,
        },
        "content_tags": dict(sorted(tag_counts.items())),
        "evidence_surfaces": dict(sorted(surfaces.items())),
        "signals": {
            "file_concentration": concentration,
            "git_churn": churn,
            "python_imports": python_imports,
        },
        "interpretation": {
            "architecture_model": "not produced",
            "composite_risk_score": "not produced",
            "signal_confidence": {
                "filesystem": "observed_metadata",
                "python_imports": "exact_ast",
                "git_churn": "bounded_current_local_refs" if not git_diagnostic else "unavailable",
            },
        },
    }


def render_json(profile: dict[str, Any]) -> str:
    """Render strict deterministic JSON."""

    return (
        json.dumps(profile, ensure_ascii=False, allow_nan=False, sort_keys=True, indent=2) + "\n"
    )


def render_markdown(profile: dict[str, Any]) -> str:
    """Render a compact Markdown evidence profile."""

    lines = [
        "# Repository evidence profile",
        "",
        f"Status: {profile['status']}",
        f"Files seen: {profile['coverage']['files_seen']}",
        "Architecture model: not produced",
        "Composite risk score: not produced",
        "",
        "## Evidence surfaces",
        "",
        "| Surface | Files |",
        "| --- | ---: |",
    ]
    for surface, paths in profile["evidence_surfaces"].items():
        lines.append(f"| {surface} | {len(paths)} |")
    lines.extend(["", "## Concentration signals", ""])
    for item in profile["signals"]["file_concentration"][:20]:
        lines.append(f"- `{item['path']}` — {item['bytes']} bytes")
    lines.extend(["", "## Coverage limits", ""])
    limits = profile["coverage"]["limit_reasons"] + profile["coverage"]["diagnostics"]
    if limits:
        lines.extend(f"- {item}" for item in limits)
    else:
        lines.append("- None reported.")
    return "\n".join(lines) + "\n"


def _confine_output(output: Path, approved_root: Path) -> Path:
    """Resolve an explicit output beneath an existing approved output root."""

    root = resolve_root(approved_root)
    if ".." in output.parts:
        raise ProfileError("output path contains a parent escape")
    candidate = output if output.is_absolute() else root / output
    try:
        parent = candidate.parent.resolve(strict=True)
        parent.relative_to(root)
        inspected_parent = parent.lstat()
    except (OSError, RuntimeError, ValueError) as exc:
        raise ProfileError("output parent is outside or not safely inspectable") from exc
    if not stat.S_ISDIR(inspected_parent.st_mode) or _is_reparse_point(inspected_parent):
        raise ProfileError("output parent is not a safe directory")
    resolved = parent / candidate.name
    if resolved.exists():
        try:
            inspected = resolved.lstat()
        except OSError as exc:
            raise ProfileError("output destination cannot be inspected") from exc
        if (
            stat.S_ISLNK(inspected.st_mode)
            or not stat.S_ISREG(inspected.st_mode)
            or _is_reparse_point(inspected)
            or inspected.st_nlink > 1
        ):
            raise ProfileError("output destination is not a single-link regular file")
    return resolved


def _open_confined_directory(root: Path, directory: Path) -> int:
    """Open *directory* by walking no-follow descriptors from *root*."""

    if os.open not in os.supports_dir_fd:
        raise ProfileError("descriptor-confined output is unsupported on this platform")
    directory_flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    directory_flags |= getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        expected_root = root.lstat()
        descriptor = os.open(root, directory_flags)
        opened_root = os.fstat(descriptor)
        if (
            not stat.S_ISDIR(opened_root.st_mode)
            or _is_reparse_point(opened_root)
            or (opened_root.st_dev, opened_root.st_ino)
            != (expected_root.st_dev, expected_root.st_ino)
        ):
            raise ProfileError("approved output root changed or became unsafe")
        for part in directory.relative_to(root).parts:
            child = os.open(part, directory_flags, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = child
            inspected = os.fstat(descriptor)
            if not stat.S_ISDIR(inspected.st_mode) or _is_reparse_point(inspected):
                raise ProfileError("approved output parent changed or became unsafe")
        return descriptor
    except ProfileError:
        if "descriptor" in locals() and descriptor >= 0:
            os.close(descriptor)
        raise
    except (OSError, ValueError) as exc:
        if "descriptor" in locals() and descriptor >= 0:
            os.close(descriptor)
        raise ProfileError("approved output parent changed or became unsafe") from exc


def _write_output(path: Path, content: str, approved_root: Path | None = None) -> None:
    """Atomically replace one confined output through a validated directory fd."""

    root = resolve_root(approved_root or path.parent)
    destination = _confine_output(path, root)
    descriptor = -1
    temporary_name = f".{destination.name}.tmp-{secrets.token_hex(12)}"
    temp_descriptor = -1
    try:
        descriptor = _open_confined_directory(root, destination.parent)
        if os.rename not in os.supports_dir_fd:
            raise ProfileError("descriptor-confined output is unsupported on this platform")
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        flags |= getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
        temp_descriptor = os.open(temporary_name, flags, 0o600, dir_fd=descriptor)
        inspected = os.fstat(temp_descriptor)
        if (
            not stat.S_ISREG(inspected.st_mode)
            or inspected.st_nlink != 1
            or _is_reparse_point(inspected)
        ):
            raise ProfileError("approved output temporary file is unsafe")
        payload = content.encode("utf-8", errors="strict")
        offset = 0
        while offset < len(payload):
            written = os.write(temp_descriptor, payload[offset:])
            if written <= 0:
                raise ProfileError("approved output could not be written safely")
            offset += written
        os.fsync(temp_descriptor)
        os.close(temp_descriptor)
        temp_descriptor = -1
        try:
            existing = os.stat(destination.name, dir_fd=descriptor, follow_symlinks=False)
        except FileNotFoundError:
            existing = None
        if existing is not None and (
            not stat.S_ISREG(existing.st_mode)
            or existing.st_nlink != 1
            or _is_reparse_point(existing)
        ):
            raise ProfileError("output destination became unsafe before replacement")
        os.rename(
            temporary_name,
            destination.name,
            src_dir_fd=descriptor,
            dst_dir_fd=descriptor,
        )
        temporary_name = ""
        os.fsync(descriptor)
    except ProfileError:
        raise
    except OSError as exc:
        raise ProfileError("approved output could not be written safely") from exc
    finally:
        if temp_descriptor >= 0:
            os.close(temp_descriptor)
        if descriptor >= 0 and temporary_name:
            with contextlib.suppress(OSError):
                os.unlink(temporary_name, dir_fd=descriptor)
        if descriptor >= 0:
            os.close(descriptor)


def _parser() -> argparse.ArgumentParser:
    """Create the command-line parser."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path, help="explicit repository root")
    parser.add_argument("--format", choices=("json", "markdown"), default="json")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--approved-output-root", type=Path)
    parser.add_argument("--max-files", type=int, default=DEFAULT_MAX_FILES)
    parser.add_argument("--max-entries", type=int, default=DEFAULT_MAX_ENTRIES)
    parser.add_argument("--max-file-bytes", type=int, default=DEFAULT_MAX_FILE_BYTES)
    parser.add_argument("--max-seconds", type=float, default=DEFAULT_MAX_SECONDS)
    parser.add_argument("--git-commits", type=int, default=DEFAULT_GIT_COMMITS)
    parser.add_argument("--max-git-bytes", type=int, default=DEFAULT_MAX_GIT_BYTES)
    parser.add_argument("--max-git-paths", type=int, default=DEFAULT_MAX_GIT_PATHS)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the profiler CLI."""

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="strict")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")
    args = _parser().parse_args(argv)
    if bool(args.output) != bool(args.approved_output_root):
        print(
            "profile_repo: --output and --approved-output-root must be used together",
            file=sys.stderr,
        )
        return 2
    try:
        profile = build_profile(
            args.root,
            Limits(
                max_files=args.max_files,
                max_file_bytes=args.max_file_bytes,
                max_seconds=args.max_seconds,
                git_commits=args.git_commits,
                max_entries=args.max_entries,
                max_git_bytes=args.max_git_bytes,
                max_git_paths=args.max_git_paths,
            ),
        )
        content = render_json(profile) if args.format == "json" else render_markdown(profile)
        if args.output:
            destination = _confine_output(args.output, args.approved_output_root)
            _write_output(destination, content, args.approved_output_root)
            print(f"profile_repo: wrote {destination.name}", file=sys.stderr)
        else:
            sys.stdout.write(content)
    except ProfileError as exc:
        print(f"profile_repo: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
