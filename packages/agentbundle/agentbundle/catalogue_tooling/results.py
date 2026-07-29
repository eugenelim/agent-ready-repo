"""Shared result and diagnostic types for catalogue_tooling commands.

These types are the stable contract between all catalogue_tooling modules.
Wave 2-4 specs populate the logic; this module defines the shape.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field


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


# ---------------------------------------------------------------------------
# catalogue init types
# ---------------------------------------------------------------------------

class FileAction(enum.StrEnum):
    CREATE = "create"
    ALREADY_PRESENT = "already-present"
    CONFLICT = "conflict"


@dataclass
class FilePlan:
    path: str
    kind: str  # "generated" | "scaffold"
    action: FileAction
    sha256: str
    conflict_reason: str | None = None


@dataclass
class InitVerification:
    ok: bool
    diagnostic_count: int


@dataclass
class InitSummary:
    create: int
    already_present: int
    conflict: int
    total: int


@dataclass
class InitCatalogueMeta:
    name: str
    display_name: str
    description: str
    owner_name: str
    preferred_adapter: str
    minimum_agentbundle_version: str


@dataclass
class InitResult(CommandResult):
    dry_run: bool = False
    target: str = ""
    catalogue: InitCatalogueMeta = field(
        default_factory=lambda: InitCatalogueMeta("", "", "", "", "", "")
    )
    files: list[FilePlan] = field(default_factory=list)
    verification: InitVerification = field(
        default_factory=lambda: InitVerification(ok=False, diagnostic_count=0)
    )
    summary: InitSummary = field(
        default_factory=lambda: InitSummary(0, 0, 0, 0)
    )
