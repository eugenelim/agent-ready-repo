#!/usr/bin/env python3
"""Validate an orchestrator-owned review artifact without disclosing its path or body."""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import stat
import sys
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, NoReturn, Sequence

sys.stdout.reconfigure(encoding="utf-8", errors="strict")
sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

MAX_REPORT_BYTES = 1_048_576
REVIEW_STAGES = frozenset({"pre-execute", "post-gates"})
ARTIFACT_KINDS = frozenset({"raw", "adjudication", "evidence"})
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
ROLE_RE = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
MAX_ROLE_LENGTH = 64


class UsageError(ValueError):
    """The CLI shape or orchestrator-owned metadata is invalid."""


class ArtifactError(RuntimeError):
    """A report artifact failed the validation boundary."""

    def __init__(self, code: str) -> None:
        """Create a non-sensitive, fixed-code refusal."""
        super().__init__(code)
        self.code = code


class QuietArgumentParser(argparse.ArgumentParser):
    """Argument parser that never reflects attacker-controlled values on errors."""

    def error(self, message: str) -> NoReturn:
        """Convert argparse diagnostics into a fixed caller-owned refusal."""
        del message
        raise UsageError("invalid-command")


@dataclass(frozen=True)
class ArtifactMetadata:
    """Validated metadata from which the report location is derived."""

    root: Path
    run_id: str
    round_number: int
    review_stage: str
    reviewer_role: str
    kind: str
    expected_sha256: str | None = None

    @property
    def filename(self) -> str:
        """Return the deterministic report filename."""
        return (
            f"{self.round_number}-{self.review_stage}-"
            f"{self.reviewer_role}-{self.kind}.md"
        )


def _parse_metadata(args: argparse.Namespace) -> ArtifactMetadata:
    """Validate CLI metadata without using it in diagnostics."""
    try:
        parsed_run_id = uuid.UUID(args.run_id)
    except (AttributeError, TypeError, ValueError) as exc:
        raise UsageError("invalid-metadata") from exc
    if str(parsed_run_id) != args.run_id:
        raise UsageError("invalid-metadata")

    round_text = str(args.round_number)
    if not round_text.isascii() or not round_text.isdecimal():
        raise UsageError("invalid-metadata")
    round_number = int(round_text)
    if round_number < 1:
        raise UsageError("invalid-metadata")

    role = str(args.reviewer_role)
    if len(role) > MAX_ROLE_LENGTH or ROLE_RE.fullmatch(role) is None:
        raise UsageError("invalid-metadata")
    if args.review_stage not in REVIEW_STAGES or args.kind not in ARTIFACT_KINDS:
        raise UsageError("invalid-metadata")
    expected_sha256 = args.expected_sha256
    if expected_sha256 is not None and (
        args.kind != "evidence" or SHA256_RE.fullmatch(expected_sha256) is None
    ):
        raise UsageError("invalid-metadata")

    try:
        root = Path(args.root).resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise ArtifactError("unsafe-artifact") from exc
    if not root.is_dir():
        raise ArtifactError("unsafe-artifact")

    return ArtifactMetadata(
        root=root,
        run_id=args.run_id,
        round_number=round_number,
        review_stage=args.review_stage,
        reviewer_role=role,
        kind=args.kind,
        expected_sha256=expected_sha256,
    )


def _open_with_descriptor_walk(metadata: ArtifactMetadata) -> BinaryIO:
    """Open the report beneath no-follow directory descriptors."""
    directory_flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    nofollow = getattr(os, "O_NOFOLLOW", 0)
    close_on_exec = getattr(os, "O_CLOEXEC", 0)
    nonblock = getattr(os, "O_NONBLOCK", 0)
    current_fd = os.open(metadata.root, directory_flags | close_on_exec)
    try:
        for segment in (".context", "reviews", metadata.run_id):
            next_fd = os.open(
                segment,
                directory_flags | nofollow | close_on_exec,
                dir_fd=current_fd,
            )
            os.close(current_fd)
            current_fd = next_fd
        report_info = os.stat(
            metadata.filename,
            dir_fd=current_fd,
            follow_symlinks=False,
        )
        if not stat.S_ISREG(report_info.st_mode) or report_info.st_nlink > 1:
            raise ArtifactError("unsafe-artifact")
        report_fd = os.open(
            metadata.filename,
            os.O_RDONLY | nonblock | nofollow | close_on_exec,
            dir_fd=current_fd,
        )
        opened = os.fstat(report_fd)
        if not stat.S_ISREG(opened.st_mode) or opened.st_nlink > 1:
            os.close(report_fd)
            raise ArtifactError("unsafe-artifact")
    finally:
        os.close(current_fd)
    return os.fdopen(report_fd, "rb", closefd=True)


def _is_windows_reparse_point(info: os.stat_result) -> bool:
    """Return whether stat metadata identifies a Windows reparse point."""
    marker = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    attributes = getattr(info, "st_file_attributes", 0)
    return bool(attributes & marker)


def _require_resolved_under(path: Path, root: Path) -> None:
    """Reject a resolved fallback component that escapes the repository root."""
    try:
        path.resolve(strict=True).relative_to(root)
    except (OSError, RuntimeError, ValueError) as exc:
        raise ArtifactError("unsafe-artifact") from exc


def _open_with_path_checks(metadata: ArtifactMetadata) -> BinaryIO:
    """Portable fallback when descriptor-relative opens are unavailable."""
    current = metadata.root
    for segment in (".context", "reviews", metadata.run_id):
        current /= segment
        info = os.lstat(current)
        if (
            stat.S_ISLNK(info.st_mode)
            or _is_windows_reparse_point(info)
            or not stat.S_ISDIR(info.st_mode)
        ):
            raise ArtifactError("unsafe-artifact")
        _require_resolved_under(current, metadata.root)
    report = current / metadata.filename
    info = os.lstat(report)
    if (
        stat.S_ISLNK(info.st_mode)
        or _is_windows_reparse_point(info)
        or info.st_nlink > 1
        or not stat.S_ISREG(info.st_mode)
    ):
        raise ArtifactError("unsafe-artifact")
    _require_resolved_under(report, metadata.root)
    flags = (
        os.O_RDONLY
        | getattr(os, "O_NONBLOCK", 0)
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_CLOEXEC", 0)
    )
    fd = os.open(report, flags)
    opened = os.fstat(fd)
    if opened.st_nlink > 1 or (opened.st_dev, opened.st_ino) != (
        info.st_dev,
        info.st_ino,
    ):
        os.close(fd)
        raise ArtifactError("unsafe-artifact")
    return os.fdopen(fd, "rb", closefd=True)


def _open_report(metadata: ArtifactMetadata) -> BinaryIO:
    """Open the expected report without following target or parent symlinks."""
    descriptor_walk_supported = (
        os.open in os.supports_dir_fd and bool(getattr(os, "O_NOFOLLOW", 0))
    )
    try:
        if descriptor_walk_supported:
            return _open_with_descriptor_walk(metadata)
        return _open_with_path_checks(metadata)
    except PermissionError as exc:
        raise ArtifactError("unreadable") from exc
    except ArtifactError:
        raise
    except OSError as exc:
        raise ArtifactError("unsafe-artifact") from exc


def validate_artifact(metadata: ArtifactMetadata) -> tuple[int, str]:
    """Return the byte size and SHA-256 digest for one safe UTF-8 report."""
    with _open_report(metadata) as report:
        before = os.fstat(report.fileno())
        if not stat.S_ISREG(before.st_mode) or before.st_nlink > 1:
            raise ArtifactError("unsafe-artifact")
        if before.st_size > MAX_REPORT_BYTES:
            raise ArtifactError("too-large")
        data = report.read(MAX_REPORT_BYTES + 1)
        after = os.fstat(report.fileno())

    if len(data) > MAX_REPORT_BYTES or after.st_size > MAX_REPORT_BYTES:
        raise ArtifactError("too-large")
    # `before` and `after` fstat the same open file description, so their
    # (st_dev, st_ino) are identical by construction — comparing them would read
    # as a substitution-during-read control while being unable to fail. The
    # re-checks that DO carry information are st_nlink (a hard link created
    # while the descriptor was open) and st_size below.
    if after.st_nlink > 1:
        raise ArtifactError("unsafe-artifact")
    if after.st_size != len(data):
        raise ArtifactError("unstable-artifact")
    try:
        data.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise ArtifactError("invalid-utf8") from exc
    return len(data), hashlib.sha256(data).hexdigest()


def _build_parser() -> QuietArgumentParser:
    """Build the closed validator CLI without arbitrary path arguments."""
    parser = QuietArgumentParser(prog="review-artifact", add_help=True)
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate = subparsers.add_parser("validate", add_help=True)
    validate.add_argument("--root", required=True)
    validate.add_argument("--run-id", required=True)
    validate.add_argument("--round", dest="round_number", required=True)
    validate.add_argument("--review-stage", required=True)
    validate.add_argument("--reviewer-role", required=True)
    validate.add_argument("--kind", required=True)
    validate.add_argument("--expected-sha256")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Validate one report and emit only fixed status, size, and digest fields."""
    try:
        args = _build_parser().parse_args(argv)
        metadata = _parse_metadata(args)
        size, digest = validate_artifact(metadata)
        if metadata.expected_sha256 is not None and digest != metadata.expected_sha256:
            raise ArtifactError("unstable-artifact")
    except UsageError:
        print("INVALID invalid-metadata")
        return 2
    except ArtifactError as exc:
        print(f"INVALID {exc.code}")
        return 3
    except (OSError, ValueError):
        print("INVALID unsafe-artifact")
        return 3
    print(f"VALID size={size} sha256={digest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
