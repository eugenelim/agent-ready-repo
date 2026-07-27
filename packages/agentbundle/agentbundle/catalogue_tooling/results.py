"""Shared result and diagnostic types for catalogue_tooling commands.

These types are the stable contract between all catalogue_tooling modules.
Wave 2-4 specs populate the logic; this module defines the shape.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass


class Severity(enum.IntEnum):
    ERROR = 3
    WARN = 2
    INFO = 1


@dataclass
class Diagnostic:
    code: str
    severity: Severity
    pack: str | None
    path: str | None
    line: int | None
    col: int | None
    message: str
    remediation: str | None


@dataclass
class CommandResult:
    ok: bool
    diagnostics: list[Diagnostic]
    schema_version: int
    command: str
    operation: str
    agentbundle_version: str
    catalogue_schema_version: int


@dataclass
class LintResult(CommandResult):
    pass


@dataclass
class VerifyResult(CommandResult):
    pass


@dataclass
class BuildResult(CommandResult):
    pass


@dataclass
class SelfHostResult(CommandResult):
    pass


@dataclass
class PackageResult(CommandResult):
    pass


@dataclass
class SyncDefaultsResult(CommandResult):
    pass
