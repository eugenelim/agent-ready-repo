"""Stable diagnostic codes for catalogue_tooling commands."""

from __future__ import annotations

import enum

from agentbundle.catalogue_tooling.results import Diagnostic, Severity


class DiagnosticCode(enum.StrEnum):
    UNKNOWN = "UNKNOWN"

    # Lint codes — CAT-L001 through CAT-L031
    CAT_L001 = "CAT-L001"   # catalogue.toml present but invalid per config.py
    CAT_L002 = "CAT-L002"   # Required catalogue marker missing (packs dir or marketplace.json)
    CAT_L003 = "CAT-L003"   # Duplicate pack identity across packs dir
    CAT_L004 = "CAT-L004"   # Pack directory name differs from [pack].name in pack.toml
    CAT_L005 = "CAT-L005"   # pack.toml not parseable as TOML
    CAT_L006 = "CAT-L006"   # pack.toml fails pack.schema.json validation (WARN if schema absent)
    CAT_L007 = "CAT-L007"   # plugin.json not parseable as JSON
    CAT_L008 = "CAT-L008"   # plugin.json fails plugin schema validation
    CAT_L009 = "CAT-L009"   # pack.toml and plugin.json name or version mismatch
    CAT_L010 = "CAT-L010"   # Skill directory missing SKILL.md
    CAT_L011 = "CAT-L011"   # Skill frontmatter missing required key or invalid value
    CAT_L012 = "CAT-L012"   # Agent metadata file missing required frontmatter
    CAT_L013 = "CAT-L013"   # Command metadata structure invalid
    CAT_L014 = "CAT-L014"   # Hook or hook-wiring file structure invalid
    CAT_L015 = "CAT-L015"   # Profile schema invalid or references unknown primitive
    CAT_L016 = "CAT-L016"   # Source-relative path escapes pack root
    CAT_L017 = "CAT-L017"   # Case-insensitive path collision within pack
    CAT_L018 = "CAT-L018"   # Primitive name not unique within pack
    CAT_L019 = "CAT-L019"   # Declared adapter name not in adapter contract
    CAT_L020 = "CAT-L020"   # Allowed scope value not in permitted set
    CAT_L021 = "CAT-L021"   # Configured path escapes catalogue root
    CAT_L022 = "CAT-L022"   # Symlink in shippable pack content (WARN)
    CAT_L023 = "CAT-L023"   # Windows-poisonous path name
    CAT_L024 = "CAT-L024"   # Primitive name does not match required pattern
    CAT_L025 = "CAT-L025"   # Primitive name exceeds max length
    CAT_L026 = "CAT-L026"   # Primitive description exceeds max length
    # Scoped to agents: adapter projection rewrites agent frontmatter line by
    # line, so a block scalar reaches the target as the bare `>` indicator with
    # its text dropped. Skills are copied byte-for-byte and may use them.
    CAT_L027 = "CAT-L027"   # Block scalar in agent frontmatter is not projectable
    CAT_L028 = "CAT-L028"   # Install profile invariant violation (scope, deps, order)
    CAT_L029 = "CAT-L029"   # Catalogue seeds lint failure (blocklist, placeholder, patterns.jsonl)
    CAT_L030 = "CAT-L030"   # First-value contract violation (Level A/B fields, writes-to-repo, tutorial)  # noqa: E501
    CAT_L031 = "CAT-L031"   # Credentialed-skill convention violation (D1/D2/D2b/D3/broker-specific)  # noqa: E501

    # Direct-route codes — CAT-D001 through CAT-D019 (RFC-0098).
    #
    # Derived by walking every acceptance criterion that mandates a registered
    # direct refusal, which is the enumeration AC31's lint asserts exact
    # coverage of. The AC each member discharges is named so the walk can be
    # re-derived rather than trusted. No count is recorded anywhere: two were
    # written during review and both went stale as criteria added refusals.
    CAT_D001 = "CAT-D001"   # AC3: malformed owner/repository or invalid URL component
    CAT_D002 = "CAT-D002"   # AC3: bare or defaulted ref (`main`) refused
    CAT_D003 = "CAT-D003"   # AC3: hex-shaped tag not safely classifiable as an abbreviated SHA
    CAT_D004 = "CAT-D004"   # AC3: pax_global_header SHA absent, malformed, or ref mismatch
    CAT_D005 = "CAT-D005"   # AC5: interpreter runtime floor below the supported minor
    CAT_D006 = "CAT-D006"   # AC5: acquisition inactivity or download limit breached
    CAT_D007 = "CAT-D007"   # AC6: archive member refused by the extraction filter or link policy
    CAT_D008 = "CAT-D008"   # AC20: remote noninteractive install or upgrade missing `--yes`
    CAT_D009 = "CAT-D009"   # AC27/AC34: measured-path integrity (link-like, reparse, wrong type)
    CAT_D010 = "CAT-D010"   # AC31: source untraversable or changed during admission
    CAT_D011 = "CAT-D011"   # AC11/AC31: invalid direct identity (slug grammar or length)
    CAT_D012 = "CAT-D012"   # AC33 budget: measured-envelope entry count
    CAT_D013 = "CAT-D013"   # AC33 budget: envelope-relative path depth
    CAT_D014 = "CAT-D014"   # AC33 budget: measured file count
    CAT_D015 = "CAT-D015"   # AC33 budget: selected-skills count
    CAT_D016 = "CAT-D016"   # AC33 budget: per-file bytes
    CAT_D017 = "CAT-D017"   # AC33 budget: total bytes
    CAT_D018 = "CAT-D018"   # AC14: logical path segment carries a control or surrogate code point
    CAT_D019 = "CAT-D019"   # AC8/AC18: publisher candidate value failed the output allowlist


# The direct-route subset, as an explicit frozenset literal of enum members.
#
# Explicit and literal on purpose: `tools/lint-direct-code-table.py` reads this
# by `ast` parse WITHOUT importing the module, so that a stale editable install
# or an unrelated copy on `sys.path` cannot satisfy the published-table check.
# A comprehension or a filter over `DiagnosticCode` would be invisible to it.
DIRECT_CODES: frozenset[DiagnosticCode] = frozenset(
    {
        DiagnosticCode.CAT_D001,
        DiagnosticCode.CAT_D002,
        DiagnosticCode.CAT_D003,
        DiagnosticCode.CAT_D004,
        DiagnosticCode.CAT_D005,
        DiagnosticCode.CAT_D006,
        DiagnosticCode.CAT_D007,
        DiagnosticCode.CAT_D008,
        DiagnosticCode.CAT_D009,
        DiagnosticCode.CAT_D010,
        DiagnosticCode.CAT_D011,
        DiagnosticCode.CAT_D012,
        DiagnosticCode.CAT_D013,
        DiagnosticCode.CAT_D014,
        DiagnosticCode.CAT_D015,
        DiagnosticCode.CAT_D016,
        DiagnosticCode.CAT_D017,
        DiagnosticCode.CAT_D018,
        DiagnosticCode.CAT_D019,
    }
)

# AC33's budget names, as carried by `file_safety.BoundExceeded.budget`, mapped
# to the member that reports each. The mapping lives here rather than in
# `file_safety.py` because that module is mirrored byte-for-byte into trees
# where this registry is unimportable, so it carries the budget as a plain
# string and the direct caller resolves it through this table.
BUDGET_CODES: dict[str, DiagnosticCode] = {
    "entries": DiagnosticCode.CAT_D012,
    "depth": DiagnosticCode.CAT_D013,
    "files": DiagnosticCode.CAT_D014,
    "selected-skills": DiagnosticCode.CAT_D015,
    "per-file-bytes": DiagnosticCode.CAT_D016,
    "total-bytes": DiagnosticCode.CAT_D017,
}


def make_direct_diagnostic(
    code: DiagnosticCode,
    severity: Severity,
    message: str,
    *,
    pack: str | None = None,
    path: str | None = None,
    line: int | None = None,
    col: int | None = None,
    remediation: str | None = None,
) -> Diagnostic:
    """Build a direct-route diagnostic, refusing any unregistered code.

    Mirrors `lint.py`'s `_diag` shape so the direct route emits the same
    `Diagnostic` the established JSON envelope serialises.

    Raises `ValueError` when `code` is outside `DIRECT_CODES`. That is a
    programmer error at a registration boundary rather than an admission
    refusal, so it is not an `UnsafeContentError` and carries no diagnostic of
    its own; AC27's rule that unregistered strings cannot reach users is
    enforced here, at construction, rather than at a rendering surface.
    """
    if code not in DIRECT_CODES:
        raise ValueError(
            f"{code.value} is not a registered direct diagnostic code; "
            "add it to DIRECT_CODES and the published table, or use a "
            "catalogue-route constructor"
        )
    return Diagnostic(
        code=code.value,
        severity=severity,
        pack=pack,
        path=path,
        line=line,
        col=col,
        message=message,
        remediation=remediation,
    )
