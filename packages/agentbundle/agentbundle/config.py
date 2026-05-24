"""TOML loaders for the CLI's persistent on-disk artifacts.

Sources read here:
  - `pack.toml`                   — a pack's manifest. Schema owned by
                                    the sibling `distribution-adapters`
                                    spec and validated by F-build's
                                    `validate_pack_metadata` helper.
  - `.agent-ready-state.toml`     — install-time state. Schema documented
                                    in the sibling spec § "state schema".
  - `.adapt-discovery.toml`       — adopter values for `<adapt:NAME>`
                                    markers. CLI **reads only**; the
                                    `adapt-to-project` LLM skill writes it.
  - `--values-from <file.toml>`   — explicit override values for
                                    `agentbundle adapt`.

No source is written here — see `safety.write_jailed` for the only
sanctioned write surface.
"""

from __future__ import annotations

import hashlib
import tomllib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal


STATE_SCHEMA_VERSION = "0.2"


class ConfigError(ValueError):
    """Raised when a TOML source fails to load or fails schema invariants."""


class StateFileLegacy(ConfigError):
    """Raised when a write-capable invocation hits a v0.1 state file.

    Migration to v0.2 is destructive (irreversible without backup), so the
    CLI never silently rewrites — instead, every write-capable handler
    surfaces this exception as a one-line refuse-and-explain pointing the
    adopter at `agentbundle init-state --migrate`. Read-only paths
    catch-and-treat as repo-scope per RFC-0004 § *Backward compatibility*.

    Carries the path on disk so the formatter can name it in the stderr
    message — adopters with multiple checkouts or scopes need to know
    which file is the legacy one.
    """

    def __init__(self, path: Path) -> None:
        self.path = path
        super().__init__(
            f"state file at {path} is schema-version 0.1; "
            f"run 'agentbundle init-state --migrate' first"
        )


# ---------------------------------------------------------------------------
# pack.toml
# ---------------------------------------------------------------------------


def load_pack_toml(path: Path) -> dict[str, Any]:
    """Load and lightly normalise a pack manifest.

    Returns the raw parsed TOML dict. Schema validation against
    `pack.schema.json` is performed by F-build's `validate_pack_metadata`;
    we don't duplicate it here — keep one source of truth.

    Raises:
        ConfigError: if the file is missing, unreadable, or not valid TOML.
    """
    if not path.exists():
        raise ConfigError(f"pack.toml not found at {path}")
    try:
        return tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"pack.toml at {path} is not valid TOML: {exc}") from exc


def pack_spec_version(pack_toml: dict[str, Any]) -> str | None:
    """Return `[pack.adapter-contract] version` if declared, else None."""
    table = pack_toml.get("pack", {}).get("adapter-contract", {})
    if isinstance(table, dict):
        v = table.get("version")
        return v if isinstance(v, str) else None
    return None


# ---------------------------------------------------------------------------
# .agent-ready-state.toml
# ---------------------------------------------------------------------------


@dataclass
class PackState:
    """One installed pack's slice of `.agent-ready-state.toml`."""

    installed_version: str
    source: str = "agent-ready-repo"
    install_route: str = "cli"
    # RFC-0004: every v0.2 entry carries an explicit scope. v0.1 state
    # files are read as all-`"repo"` (the legacy implicit default);
    # `init-state --migrate` writes the column out so the file is
    # readable by both v0.1 and v0.2 consumers identically.
    scope: str = "repo"
    primitives: list[str] = field(default_factory=list)
    files: dict[str, dict[str, str]] = field(default_factory=dict)
    # Per-primitive overrides for mixed-version packs (T12). Optional;
    # absent when the pack is at a single uniform version.
    primitive_versions: dict[str, dict[str, str]] = field(default_factory=dict)

    def file_sha(self, relpath: str) -> str | None:
        entry = self.files.get(relpath)
        return entry.get("sha") if isinstance(entry, dict) else None


@dataclass
class State:
    """Parsed `.agent-ready-state.toml` — all installed packs."""

    schema_version: str = STATE_SCHEMA_VERSION
    packs: dict[str, PackState] = field(default_factory=dict)

    def projected_paths(self) -> set[str]:
        out: set[str] = set()
        for ps in self.packs.values():
            out.update(ps.files.keys())
        return out


def load_state(path: Path, *, for_write: bool = False) -> State:
    """Load `.agent-ready-state.toml`. Returns empty State if file is absent.

    Absent is **not** an error — fresh repos legitimately have no state file
    before the first install / init-state. Callers distinguish "absent" from
    "present but empty" via `path.exists()` if they need to.

    RFC-0004 read-vs-write split:
      - Read paths (``for_write=False``, default): a v0.1 file is loaded
        with every ``[pack.<name>]`` entry getting an implicit
        ``scope = "repo"``; the returned ``State.schema_version`` preserves
        ``"0.1"`` so the caller can detect legacy state without re-reading
        the file. No migration is forced at read.
      - Write paths (``for_write=True``): a v0.1 file raises
        ``StateFileLegacy(path)``. The CLI's top-level handler formats this
        as ``state file at <path> is schema-version 0.1; run 'agentbundle
        init-state --migrate' first``. Migration is destructive — adopters
        running mixed CLI versions across CI and local must opt into it
        explicitly via ``init-state --migrate``.
    """
    if not path.exists():
        return State()
    try:
        raw = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(
            f".agent-ready-state.toml at {path} is not valid TOML: {exc}"
        ) from exc

    schema_version = raw.get("schema-version", STATE_SCHEMA_VERSION)
    if not isinstance(schema_version, str):
        raise ConfigError(f"schema-version must be a string, got {type(schema_version)!r}")

    # Refuse-and-explain on writes to a legacy state file. We check this
    # *before* parsing pack entries so callers can rely on the exception
    # type alone — no half-parsed State leaks out.
    if for_write and schema_version == "0.1":
        raise StateFileLegacy(path)

    state = State(schema_version=schema_version)
    pack_table = raw.get("pack", {})
    if not isinstance(pack_table, dict):
        raise ConfigError("[pack] must be a table")
    for name, body in pack_table.items():
        if not isinstance(body, dict):
            raise ConfigError(f"[pack.{name}] must be a table")
        files = body.get("files", {}) or {}
        if not isinstance(files, dict):
            raise ConfigError(f"[pack.{name}.files] must be a table")

        # Primitive-version sub-tables look like `[pack.<name>.skill.<X>]`,
        # one nested table per primitive type. We collect them lazily; if a
        # body key is one of the five primitive type names, it's a
        # mixed-version override map rather than a top-level field.
        PRIMITIVE_KEYS = ("skill", "agent", "hook-body", "hook-wiring", "command")
        primitive_versions: dict[str, dict[str, str]] = {}
        for ptype in PRIMITIVE_KEYS:
            sub = body.get(ptype)
            if isinstance(sub, dict):
                primitive_versions[ptype] = {
                    pname: pbody.get("version", "")
                    for pname, pbody in sub.items()
                    if isinstance(pbody, dict)
                }

        # RFC-0004 scope column. v0.2 carries it explicitly; v0.1 files
        # imply repo scope for every pack (read-time compatibility). A
        # v0.2 file with an unknown scope value falls back to "repo" so
        # readers never trip on a typo — schema validation catches that
        # earlier in the write path.
        raw_scope = body.get("scope") if schema_version != "0.1" else None
        scope = raw_scope if isinstance(raw_scope, str) and raw_scope in ("repo", "user") else "repo"

        ps = PackState(
            installed_version=body.get("installed-version", ""),
            source=body.get("source", "agent-ready-repo"),
            install_route=body.get("install-route", "cli"),
            scope=scope,
            primitives=list(body.get("primitives", []) or []),
            files={k: dict(v) for k, v in files.items() if isinstance(v, dict)},
            primitive_versions=primitive_versions,
        )
        state.packs[name] = ps
    return state


def dump_state(state: State) -> str:
    """Serialise a State to TOML.

    Stdlib `tomllib` is read-only; we emit a deterministic textual form by
    hand. Order: schema-version, then packs sorted by name, then per-pack
    fields in fixed order, then files sorted by path. Determinism matters
    because the state file participates in diffing and merging.
    """
    # Every basic-string interpolation routes through `_emit_basic_string`
    # (helper emits the surrounding quotes) so pack-sourced values like
    # `installed-version` can never break out into phantom TOML structure.
    lines: list[str] = [
        f"schema-version = {_emit_basic_string(state.schema_version)}",
        "",
    ]
    for name in sorted(state.packs):
        ps = state.packs[name]
        lines.append(f"[pack.{_toml_key(name)}]")
        lines.append(f"installed-version = {_emit_basic_string(ps.installed_version)}")
        lines.append(f"source = {_emit_basic_string(ps.source)}")
        lines.append(f"install-route = {_emit_basic_string(ps.install_route)}")
        # RFC-0004: emit `scope` only when the state file's schema is v0.2+.
        # A v0.1 file round-trips unchanged (no scope column) because the
        # read-only-as-repo-scope contract works at *read* time; the only
        # write path through this branch is `init-state --migrate`, which
        # bumps schema_version before calling dump_state.
        if state.schema_version != "0.1":
            lines.append(f"scope = {_emit_basic_string(ps.scope)}")
        primitives_repr = ", ".join(_emit_basic_string(p) for p in ps.primitives)
        lines.append(f"primitives = [{primitives_repr}]")
        lines.append("")
        lines.append(f"[pack.{_toml_key(name)}.files]")
        for relpath in sorted(ps.files):
            entry = ps.files[relpath]
            inline = ", ".join(
                f"{k} = {_emit_basic_string(v)}" for k, v in sorted(entry.items())
            )
            lines.append(f"{_emit_basic_string(relpath)} = {{ {inline} }}")
        lines.append("")
        # Mixed-version primitive overrides (T12).
        for ptype, primitives in sorted(ps.primitive_versions.items()):
            for pname, version in sorted(primitives.items()):
                lines.append(f"[pack.{_toml_key(name)}.{ptype}.{_toml_key(pname)}]")
                lines.append(f"version = {_emit_basic_string(version)}")
                lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _toml_key(name: str) -> str:
    """Quote a TOML key if it contains characters that require quoting.

    A quoted key follows TOML 1.0 basic-string escaping (§ Keys), so
    delegate the quoting path to :func:`_emit_basic_string` rather than
    inlining ``f'"{name}"'`` — otherwise a key containing ``"`` or a
    backslash would land malformed TOML, the same injection shape the
    value-side emitters guard against.
    """
    if name and all(c.isalnum() or c in "-_" for c in name):
        return name
    return _emit_basic_string(name)


# Control characters that TOML 1.0 § Strings forbids unescaped inside a
# basic-string. Everything in U+0000..U+001F except `\t` (which has a
# short escape), plus U+007F. The `\uXXXX` long-form covers them all.
_TOML_SHORT_ESCAPES = {
    "\b": "\\b",
    "\t": "\\t",
    "\n": "\\n",
    "\f": "\\f",
    "\r": "\\r",
    '"': '\\"',
    "\\": "\\\\",
}


def _emit_basic_string(value: str) -> str:
    """Serialise *value* as a TOML 1.0 basic-string literal (incl. quotes).

    Every CLI write-path that interpolates a pack-sourced string into
    TOML output routes through here. The grammar matches what
    ``tomllib`` will accept: short escapes for ``\\b \\t \\n \\f \\r ``
    ``\\"  \\\\``, ``\\uXXXX`` for any other control char (U+0000..U+001F
    and U+007F), and verbatim emission for everything else (including
    multi-byte UTF-8).

    Returns the *quoted* form ``"...escaped..."`` so callers write
    ``key = {_emit_basic_string(v)}`` without re-adding quotes.

    Raises ``ConfigError`` (not ``TypeError``) if *value* is not a
    string. Callers ship a typed contract; this guard means an
    accidental non-string field on a future ``State``/``AdaptDiscovery``
    extension surfaces as a domain-shaped refusal rather than a
    ``for-char-in-non-iterable`` traceback.
    """
    if not isinstance(value, str):
        raise ConfigError(
            f"basic-string position expects str, got {type(value).__name__}"
        )
    chunks: list[str] = ['"']
    for ch in value:
        short = _TOML_SHORT_ESCAPES.get(ch)
        if short is not None:
            chunks.append(short)
        elif ord(ch) < 0x20 or ord(ch) == 0x7F:
            chunks.append(f"\\u{ord(ch):04X}")
        else:
            chunks.append(ch)
    chunks.append('"')
    return "".join(chunks)


# ---------------------------------------------------------------------------
# .adapt-discovery.toml — typed schema (v0.1)
#
# Spec rail: the CLI may **read** this file but must never write it.
# The `adapt-to-project` LLM skill owns the write side.
# ---------------------------------------------------------------------------

_KNOWN_DISCOVERY_SCHEMA_VERSIONS = {"0.1"}
_KNOWN_FINDING_KINDS = {"companion-merge", "restructure", "consolidate"}


@dataclass(frozen=True)
class Finding:
    """One structural finding in `.adapt-discovery.toml`.

    `accepted` is True when the finding lives under ``[[findings.accepted]]``
    and False when it lives under ``[[findings.declined]]``.
    `recorded_at` holds `accepted-at` or `declined-at` (whichever is present);
    None when the timestamp was omitted.
    """

    finding_id: str
    kind: str  # one of: "companion-merge" | "restructure" | "consolidate"
    source_path: str
    destination_path: str
    action: str | None
    recorded_at: datetime | None
    accepted: bool


@dataclass
class AdaptDiscovery:
    """Parsed `.adapt-discovery.toml` in typed form.

    `markers` is always a dict; it is empty ``{}`` for user-scope files
    (which must not carry a ``[markers]`` table per RFC-0004).
    """

    schema_version: str
    markers: dict[str, str] = field(default_factory=dict)
    findings_accepted: list[Finding] = field(default_factory=list)
    findings_declined: list[Finding] = field(default_factory=list)


def finding_id_for(
    pack: str,
    kind: str,
    source_paths: list[str],
    dest_paths: list[str],
) -> str:
    """Return the canonical finding-id for the given inputs.

    Visible form  : ``<pack>/<kind>:<8-hex>``
    Hashed input  : ``<pack>:<kind>:<sorted-source-paths>:<sorted-dest-paths>``
                    (fields joined by ``:``, paths within a field joined by
                    ``:`` after sorting — mirrors the spec's hash grammar).
    Hash algorithm: SHA-1; first 8 hex chars form the visible tail.

    Per spec AC2: ``/`` separates pack from kind (pack names never contain
    ``/``); ``:`` separates the hash-input fields because path values may
    contain ``/``.
    """
    raw = f"{pack}:{kind}:{':'.join(sorted(source_paths))}:{':'.join(sorted(dest_paths))}"
    digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:8]
    return f"{pack}/{kind}:{digest}"


def load_adapt_discovery_typed(
    path: Path,
    *,
    scope: Literal["repo", "user"] = "repo",
) -> AdaptDiscovery:
    """Read `.adapt-discovery.toml` and return a typed ``AdaptDiscovery``.

    Raises ``ConfigError`` on any of:
      - File not valid TOML.
      - Top-level ``[accepted]`` table (legacy CLI shape, AC8).
      - Top-level ``[adapt]`` table (legacy self-host shape, AC9).
      - Unknown ``discovery-schema-version`` (AC16).
      - ``scope="user"`` and file contains a ``[markers]`` table (AC2/RFC-0004).
      - A ``[[findings.*]]`` entry with an unknown ``kind``.

    Returns an ``AdaptDiscovery`` with ``markers={}`` when the file lacks a
    ``[markers]`` table (valid for both scopes).

    Missing file returns ``AdaptDiscovery(schema_version="0.1")`` (no
    markers, no findings) rather than raising — absent is not an error.
    """
    if not path.exists():
        return AdaptDiscovery(schema_version="0.1")

    try:
        raw = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(
            f".adapt-discovery.toml at {path} is not valid TOML: {exc}"
        ) from exc

    # AC8: legacy [accepted] top-level table (old CLI shape).
    if "accepted" in raw:
        raise ConfigError(
            "legacy [accepted] table; migrate to [markers] per "
            "docs/specs/adapt-to-project/spec.md"
        )

    # AC9: legacy [adapt] top-level table (old self-host shape).
    if "adapt" in raw:
        raise ConfigError(
            "legacy [adapt] table; migrate to [markers] per "
            "docs/specs/adapt-to-project/spec.md"
        )

    # AC16: unknown schema version.
    schema_version = raw.get("discovery-schema-version")
    if schema_version not in _KNOWN_DISCOVERY_SCHEMA_VERSIONS:
        known = ", ".join(sorted(_KNOWN_DISCOVERY_SCHEMA_VERSIONS))
        raise ConfigError(
            f"unknown discovery-schema-version {schema_version!r}; "
            f"known: {known}"
        )

    # AC2 / RFC-0004: user-scope files must not carry [markers].
    if scope == "user" and "markers" in raw:
        raise ConfigError(
            "user-scope .adapt-discovery.toml may not contain a [markers] table; "
            "markers are repo-only per RFC-0004"
        )

    markers: dict[str, str] = {}
    raw_markers = raw.get("markers", {})
    if isinstance(raw_markers, dict):
        import re as _re

        marker_key_re = _re.compile(r"^[a-z][a-z0-9-]*$")
        for k, v in raw_markers.items():
            # Spec § Canonical .adapt-discovery.toml schemas (v0.1):
            # "a repo-scope file with [markers] that contains keys
            # violating the lowercase-hyphen grammar is refused".
            if not marker_key_re.fullmatch(str(k)):
                raise ConfigError(
                    f"marker key {k!r} violates lowercase-hyphen grammar "
                    f"^[a-z][a-z0-9-]*$ per docs/specs/adapt-to-project/spec.md"
                )
            if not isinstance(v, str):
                raise ConfigError(
                    f"markers[{k!r}] must be a string, got {type(v).__name__}"
                )
            markers[k] = v

    findings_raw = raw.get("findings", {})
    findings_accepted = _parse_findings(findings_raw.get("accepted", []), accepted=True)
    findings_declined = _parse_findings(findings_raw.get("declined", []), accepted=False)

    return AdaptDiscovery(
        schema_version=schema_version,
        markers=markers,
        findings_accepted=findings_accepted,
        findings_declined=findings_declined,
    )


def _parse_findings(entries: list[Any], *, accepted: bool) -> list[Finding]:
    out: list[Finding] = []
    for i, entry in enumerate(entries):
        if not isinstance(entry, dict):
            raise ConfigError(f"findings entry {i} must be a table")

        kind = entry.get("kind", "")
        if kind not in _KNOWN_FINDING_KINDS:
            raise ConfigError(
                f"unknown finding kind {kind!r}; "
                f"known: {', '.join(sorted(_KNOWN_FINDING_KINDS))}"
            )

        # Timestamps: accepted-at or declined-at depending on bucket.
        ts_key = "accepted-at" if accepted else "declined-at"
        ts_raw = entry.get(ts_key)
        recorded_at: datetime | None = None
        if isinstance(ts_raw, datetime):
            recorded_at = ts_raw if ts_raw.tzinfo is not None else ts_raw.replace(tzinfo=timezone.utc)

        out.append(
            Finding(
                finding_id=str(entry.get("finding-id", "")),
                kind=kind,
                source_path=str(entry.get("source-path", "")),
                destination_path=str(entry.get("destination-path", "")),
                action=entry.get("action") if isinstance(entry.get("action"), str) else None,
                recorded_at=recorded_at,
                accepted=accepted,
            )
        )
    return out


def adapt_discovery_to_toml(d: AdaptDiscovery) -> str:
    """Serialise an ``AdaptDiscovery`` to a TOML string.

    Deterministic key order: schema-version, markers (keys sorted),
    findings.accepted (sorted by finding-id), findings.declined (sorted
    by finding-id). Timestamps are omitted when ``recorded_at`` is None.

    This helper is used by the round-trip test (T1) and will be used by
    T13's idempotency story.
    """
    # Every basic-string interpolation routes through `_emit_basic_string`
    # for consistency with `dump_state` and `_append_install_marker`. The
    # CLI is read-only on `.adapt-discovery.toml` today (the skill owns
    # the write side), but keeping the discipline here means a future
    # caller can't reintroduce the injection class — and the round-trip
    # test in test_config covers this helper, so the escape behaviour is
    # pinned wherever it ships.
    lines: list[str] = [
        f"discovery-schema-version = {_emit_basic_string(d.schema_version)}",
        "",
    ]

    if d.markers:
        lines.append("[markers]")
        for k in sorted(d.markers):
            # Marker keys are loader-constrained by
            # `load_adapt_discovery_typed` to `^[a-z][a-z0-9-]*$`, but
            # the dataclass has no constructor validator. Route through
            # `_toml_key` so a directly-built `AdaptDiscovery` with a
            # malformed key still emits well-formed TOML — no phantom
            # structure can land. The loader-side grammar still applies
            # on re-read; the asymmetry is intentional (the emitter's
            # job is structural safety, the loader's is grammar
            # enforcement).
            lines.append(f"{_toml_key(k)} = {_emit_basic_string(d.markers[k])}")
        lines.append("")

    for finding in sorted(d.findings_accepted, key=lambda f: f.finding_id):
        lines.append("[[findings.accepted]]")
        lines.append(f"finding-id       = {_emit_basic_string(finding.finding_id)}")
        lines.append(f"kind             = {_emit_basic_string(finding.kind)}")
        lines.append(f"source-path      = {_emit_basic_string(finding.source_path)}")
        lines.append(f"destination-path = {_emit_basic_string(finding.destination_path)}")
        if finding.action is not None:
            lines.append(f"action           = {_emit_basic_string(finding.action)}")
        if finding.recorded_at is not None:
            ts = finding.recorded_at.strftime("%Y-%m-%dT%H:%M:%SZ")
            lines.append(f"accepted-at      = {ts}")
        lines.append("")

    for finding in sorted(d.findings_declined, key=lambda f: f.finding_id):
        lines.append("[[findings.declined]]")
        lines.append(f"finding-id       = {_emit_basic_string(finding.finding_id)}")
        lines.append(f"kind             = {_emit_basic_string(finding.kind)}")
        lines.append(f"source-path      = {_emit_basic_string(finding.source_path)}")
        lines.append(f"destination-path = {_emit_basic_string(finding.destination_path)}")
        if finding.action is not None:
            lines.append(f"action           = {_emit_basic_string(finding.action)}")
        if finding.recorded_at is not None:
            ts = finding.recorded_at.strftime("%Y-%m-%dT%H:%M:%SZ")
            lines.append(f"declined-at      = {ts}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


# ---------------------------------------------------------------------------
# --values-from <file.toml>
# ---------------------------------------------------------------------------


_VALUES_DISCOVERY_RESERVED = frozenset(
    {"discovery-schema-version", "findings", "marker-schema-version"}
)


def load_values_from(path: Path) -> dict[str, str]:
    """Load `--values-from` TOML; return a flat dict of marker → value.

    Accepts (in order tried):

      1. A ``[markers]`` table — canonical ``.adapt-discovery.toml`` shape
         when the skill hands a discovery file directly to the CLI.
      2. A ``[values]`` table — original ``--values-from`` shape kept
         for hand-authored override files.
      3. A flat top-level table — keys at the root, skipping the
         reserved discovery keys (``discovery-schema-version``,
         ``findings``, ``marker-schema-version``) so a canonical
         user-scope discovery file (no ``[markers]``, no ``[values]``)
         passes through cleanly as an empty mapping.

    Presence of *both* ``[markers]`` and ``[values]`` is ambiguous and
    refused — per AC15.
    """
    if not path.exists():
        raise ConfigError(f"--values-from path not found: {path}")
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise ConfigError(
            f"--values-from at {path} is not a readable text file: {exc}"
        ) from exc
    try:
        raw = tomllib.loads(text)
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(
            f"--values-from at {path} is not valid TOML: {exc}"
        ) from exc

    has_markers = isinstance(raw.get("markers"), dict)
    has_values = isinstance(raw.get("values"), dict)
    if has_markers and has_values:
        raise ConfigError(
            "ambiguous --values-from file: both [markers] and [values] "
            "tables present; use one"
        )

    if has_markers:
        values = raw["markers"]
    elif has_values:
        values = raw["values"]
    else:
        values = {
            k: v for k, v in raw.items()
            if k not in _VALUES_DISCOVERY_RESERVED
        }
    if not isinstance(values, dict):
        raise ConfigError("expected a [values] table of string entries")
    out: dict[str, str] = {}
    for k, v in values.items():
        if not isinstance(v, str):
            raise ConfigError(f"value for {k!r} must be a string, got {type(v).__name__}")
        out[str(k)] = v
    return out
