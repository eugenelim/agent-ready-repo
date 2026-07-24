"""TOML loaders for the CLI's persistent on-disk artifacts.

Sources read here:
  - `pack.toml`                   — a pack's manifest. Schema owned by
                                    the sibling `distribution-adapters`
                                    spec and validated by F-build's
                                    `validate_pack_metadata` helper.
  - `.agentbundle-state.toml`     — install-time state. Schema documented
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
import re
import tomllib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal
from urllib.parse import urlsplit
from urllib.request import url2pathname


_WIN_DRIVE_RE = re.compile(r"^[A-Za-z]:[\\/]")
_CREDENTIAL_SUBSTRINGS = ("token", "key", "secret", "password", "auth")

STATE_SCHEMA_VERSION = "0.4"

# Read-time default for v0.3 rows lacking explicit ``target-file`` when the
# resolved adapter is ``claude-code`` — the adapter's user-scope settings
# file is the only place a claude-code hook-wiring row could land
# (RFC-0005 § State-file impact).
_CLAUDE_CODE_USER_SETTINGS_DEFAULT = "~/.claude/settings.json"


class ConfigError(ValueError):
    """Raised when a TOML source fails to load or fails schema invariants."""


class StateFileLegacy(ConfigError):
    """Raised when a state file's ``schema-version`` is not the one this
    binary speaks.

    The v0.4 schema (RFC-0052 / ADR-0039) re-keyed state to
    ``[pack.<name>.adapters.<adapter>]`` and made cross-version handling a
    **hard refusal**: a reader refuses any ``schema-version`` it does not
    recognise, on **both read and write** (not the v0.1/v0.2-write-only
    refusal that preceded it). Without this, a v0.3-era binary reading a
    v0.4 file would parse ``[pack.research.adapters.claude-code]`` as a pack
    literally named ``research`` with an ``adapters`` sub-table and zero
    files, then a later uninstall/install would corrupt ownership.

    Migration is **greenfield** (RFC-0052 Decision 8): there is no
    converter from a legacy version: an adopter on an older state file
    **re-installs** rather than auto-upgrading. The refuse-and-explain
    message therefore directs re-install, not ``init-state --migrate``.

    Carries the path on disk plus the offending version so the formatter
    can name both in the stderr message — adopters running mixed CLI
    versions across CI and local need to know which file is which.
    """

    def __init__(self, path: Path, version: str = "0.1") -> None:
        self.path = path
        self.version = version
        super().__init__(
            f"state file at {path} is schema-version {version}, but this "
            f"agentbundle speaks {STATE_SCHEMA_VERSION}; reinstall the pack "
            f"to regenerate state (no legacy migration — RFC-0052 D8)"
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
# .agentbundle-state.toml
# ---------------------------------------------------------------------------


@dataclass
class PackState:
    """One installed pack's slice of `.agentbundle-state.toml`."""

    installed_version: str
    source: str | None = None
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
    # RFC-0005 v0.3 additions — optional, read-time defaulted.
    # ``adapter`` defaults to ``"claude-code"`` when absent on read
    # (covers v0.2-vintage rows preserved across the header-only
    # migration and v0.3-vintage claude-code rows omitting the field as
    # a write-time space saving). ``target_file`` defaults to
    # ``~/.claude/settings.json`` for claude-code rows; **required**
    # (no default) for kiro rows. ``hook_wiring_owned`` is the per-pack
    # array-of-tables that uninstall walks to remove the right entries
    # from the right files.
    adapter: str = "claude-code"
    target_file: str | None = None
    hook_wiring_owned: list[dict[str, str]] = field(default_factory=list)

    def file_sha(self, relpath: str) -> str | None:
        entry = self.files.get(relpath)
        return entry.get("sha") if isinstance(entry, dict) else None


@dataclass
class State:
    """Parsed `.agentbundle-state.toml` — all installed pack/adapter rows.

    Keyed by the ``(pack_name, adapter)`` tuple (RFC-0052 / ADR-0039): one
    pack can carry multiple adapter rows at a single scope, so the v0.3
    pack-name-keyed dict is replaced by a flat tuple-keyed one. The flat
    shape is deliberate — every whole-pack access (`del state.packs[name]`,
    `name in state.packs`) fails loudly under the tuple key, forcing each
    call site to declare whether it means "any adapter row of this pack"
    (`has_pack`) or "this specific row" (`row`).
    """

    schema_version: str = STATE_SCHEMA_VERSION
    packs: dict[tuple[str, str], PackState] = field(default_factory=dict)

    def has_pack(self, name: str) -> bool:
        """True if any adapter row of *name* is installed at this scope."""
        return any(p == name for (p, _a) in self.packs)

    def rows_for_pack(self, name: str) -> dict[str, PackState]:
        """Return {adapter: PackState} for every row of *name*."""
        return {a: ps for (p, a), ps in self.packs.items() if p == name}

    def adapters_for_pack(self, name: str) -> list[str]:
        """Return the adapters *name* is installed for, sorted."""
        return sorted(a for (p, a) in self.packs if p == name)

    def row(self, name: str, adapter: str) -> "PackState | None":
        """Return the ``(name, adapter)`` row, or None if absent."""
        return self.packs.get((name, adapter))

    def owners_of(self, relpath: str) -> list[tuple[str, str]]:
        """Return every ``(pack, adapter)`` row whose footprint claims *relpath*.

        This is the derived-ownership primitive (ADR-0039): nothing is
        stored per-file beyond the SHA already in ``PackState.files``;
        the owner-set is computed by scanning rows.
        """
        return [key for key, ps in self.packs.items() if relpath in ps.files]

    def shas_for(self, relpath: str) -> set[str]:
        """Return the set of recorded SHAs for *relpath* across all rows.

        Co-owned rows hold an identical SHA by construction (the install
        gate refuses a same-path/different-SHA collision), so this set is
        normally a singleton; a multi-element set means corruption.
        """
        out: set[str] = set()
        for ps in self.packs.values():
            sha = ps.file_sha(relpath)
            if sha:
                out.add(sha)
        return out

    def projected_paths(self) -> set[str]:
        out: set[str] = set()
        for ps in self.packs.values():
            out.update(ps.files.keys())
        return out


# ---------------------------------------------------------------------------
# Footprint ownership (RFC-0052 / ADR-0039) — pure, derived, no I/O
# ---------------------------------------------------------------------------


import enum as _enum


class FootprintVerdict(_enum.Enum):
    """Aggregate verdict for an incoming ``(pack, adapter)`` install."""

    ALREADY_INSTALLED = "already-installed"
    PROCEED = "proceed"
    REFUSE = "refuse"


def classify_incoming_path(
    state: State, pack_name: str, adapter: str, relpath: str, incoming_sha: str
) -> str:
    """Per-relpath ownership verdict for an incoming install.

    Returns one of:
      - ``"new"``      — no row owns ``relpath`` → write it, claim it.
      - ``"own"``      — this exact ``(pack, adapter)`` row already owns it at
                         the incoming SHA (upgrade/no-op).
      - ``"coown"``    — a **sibling adapter row of the same pack** owns it at
                         the **same SHA** → co-own (record, skip the write).
      - ``"conflict"`` — owned at a **different SHA**, or owned by a **different
                         pack** (even at equal SHA). Co-ownership is intra-pack
                         and content-addressed only (ADR-0039).
    """
    owners = state.owners_of(relpath)
    if not owners:
        return "new"
    for (op, oa) in owners:
        if op != pack_name:
            return "conflict"  # cross-pack claim — never silently co-owned
        if state.row(op, oa).file_sha(relpath) != incoming_sha:
            return "conflict"  # same pack, different content
    return "own" if (pack_name, adapter) in owners else "coown"


@dataclass
class FootprintPlan:
    """The footprint gate's verdict for an incoming install (ADR-0039)."""

    verdict: FootprintVerdict
    per_path: dict[str, str]  # relpath -> new|own|coown|conflict
    conflicts: list[str]      # sorted relpaths in conflict (named on refuse)


def footprint_plan(
    state: State, pack_name: str, adapter: str, incoming: dict[str, str]
) -> FootprintPlan:
    """Aggregate the per-relpath verdicts for an incoming install.

    *incoming* maps each relpath the install would write to its content SHA.

    Aggregate rule (spec AC):
      - any path in conflict → ``REFUSE`` (with the conflicting paths named).
      - else every path already owned by **this** row at matching SHA →
        ``ALREADY_INSTALLED`` (the upgrade path).
      - else (some new or co-owned, no conflict) → ``PROCEED``.
    """
    per = {
        r: classify_incoming_path(state, pack_name, adapter, r, sha)
        for r, sha in incoming.items()
    }
    conflicts = sorted(r for r, v in per.items() if v == "conflict")
    if conflicts:
        return FootprintPlan(FootprintVerdict.REFUSE, per, conflicts)
    if per and all(v == "own" for v in per.values()):
        return FootprintPlan(FootprintVerdict.ALREADY_INSTALLED, per, [])
    return FootprintPlan(FootprintVerdict.PROCEED, per, [])


def load_state(path: Path, *, for_write: bool = False) -> State:
    """Load `.agentbundle-state.toml`. Returns empty State if file is absent.

    Absent is **not** an error — fresh repos legitimately have no state file
    before the first install / init-state. Callers distinguish "absent" from
    "present but empty" via `path.exists()` if they need to.

    **Hard cross-version refusal (RFC-0052 Decision 4 / ADR-0039).** A v0.4
    reader refuses any ``schema-version`` it does not recognise, on **both
    read and write** — the refusal is an allowlist (``== "0.4"``), not a
    denylist of known-legacy versions, and an **absent** ``schema-version``
    raises rather than defaulting to the current constant. This closes the
    stale-binary mis-parse the prior parse-through default left open: a v0.3
    file (flat ``[pack.<name>]`` rows) loaded under v0.4 rules, or a v0.4
    file (``[pack.<name>.adapters.<adapter>]``) loaded by a v0.3 binary,
    would otherwise corrupt ownership silently. Migration is greenfield
    (Decision 8) — no converter; the adopter re-installs.

    ``for_write`` is retained for call-site compatibility but no longer
    gates the refusal (it is now unconditional, read and write).
    """
    if not path.exists():
        return State()
    try:
        raw = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(
            f".agentbundle-state.toml at {path} is not valid TOML: {exc}"
        ) from exc

    # Allowlist gate: anything that is not exactly the version this binary
    # speaks is refused — including an absent version (which previously
    # defaulted to the current constant and parsed through).
    schema_version = raw.get("schema-version")
    if schema_version != STATE_SCHEMA_VERSION:
        display = schema_version if isinstance(schema_version, str) else "absent"
        raise StateFileLegacy(path, version=display)

    state = State(schema_version=schema_version)
    pack_table = raw.get("pack", {})
    if not isinstance(pack_table, dict):
        raise ConfigError("[pack] must be a table")
    for name, pack_body in pack_table.items():
        if not isinstance(pack_body, dict):
            raise ConfigError(f"[pack.{name}] must be a table")
        adapters = pack_body.get("adapters", {})
        if not isinstance(adapters, dict):
            raise ConfigError(f"[pack.{name}.adapters] must be a table")
        for adapter, body in adapters.items():
            if not isinstance(body, dict):
                raise ConfigError(
                    f"[pack.{name}.adapters.{adapter}] must be a table"
                )
            state.packs[(name, adapter)] = _parse_adapter_row(name, adapter, body)
    return state


def _parse_adapter_row(name: str, adapter: str, body: dict[str, Any], default_scope: str = "repo") -> "PackState":
    """Parse one ``[pack.<name>.adapters.<adapter>]`` row into a PackState.

    The adapter is part of the table key, so it is passed in rather than
    read from a field. ``target-file`` is read-time-defaulted to the
    claude-code user settings path for claude-code rows; kiro rows have no
    implicit default (consumers surface their own error if they need it).
    """
    files = body.get("files", {}) or {}
    if not isinstance(files, dict):
        raise ConfigError(f"[pack.{name}.adapters.{adapter}.files] must be a table")

    # Primitive-version sub-tables look like
    # `[pack.<name>.adapters.<adapter>.skill.<X>]`, one nested table per
    # primitive type — a mixed-version override map, not a top-level field.
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

    raw_scope = body.get("scope")
    scope = raw_scope if isinstance(raw_scope, str) and raw_scope in ("repo", "user") else default_scope

    raw_target = body.get("target-file")
    if isinstance(raw_target, str):
        target_file: str | None = raw_target
    elif adapter == "claude-code":
        target_file = _CLAUDE_CODE_USER_SETTINGS_DEFAULT
    else:
        target_file = None

    raw_owned = body.get("hook-wiring-owned", []) or []
    hook_wiring_owned: list[dict[str, str]] = []
    if isinstance(raw_owned, list):
        for i, entry in enumerate(raw_owned):
            if not isinstance(entry, dict):
                raise ConfigError(
                    f"[pack.{name}.adapters.{adapter}.hook-wiring-owned] "
                    f"entry {i} must be a table"
                )
            hook_wiring_owned.append({
                k: str(v) for k, v in entry.items() if isinstance(v, str)
            })

    return PackState(
        installed_version=body.get("installed-version", ""),
        source=body.get("source"),
        install_route=body.get("install-route", "cli"),
        scope=scope,
        primitives=list(body.get("primitives", []) or []),
        files={k: dict(v) for k, v in files.items() if isinstance(v, dict)},
        primitive_versions=primitive_versions,
        adapter=adapter,
        target_file=target_file,
        hook_wiring_owned=hook_wiring_owned,
    )



def canonicalize_source(value: str | None) -> str | None:
    """Normalize a pack source URI to a canonical, credential-free form.

    Returns None for:
    - None input
    - The legacy "agent-ready-repo" sentinel
    - Empty or whitespace-only strings
    - Local paths that raise OSError on resolve
    - file:// URLs with a non-empty, non-localhost netloc
    - URLs with user-info (``@``) in the netloc
    - URLs whose query-string keys or fragment contain a credential substring

    For all other inputs, returns a normalized URI:
    - Local paths (schemeless or Windows drive paths, or ``file://``) are
      resolved to an absolute POSIX path string via :func:`Path.resolve`.
    - Remote URIs are lowercased in scheme and netloc; trailing slashes are
      stripped from non-root paths; query and fragment pass through unchanged.
    """
    # Rule 1
    if value is None:
        return None
    # Rule 2 — legacy sentinel is treated as "absent"
    if value == "agent-ready-repo":
        return None
    # Rule 3 — empty / blank
    if not value or not value.strip():
        return None

    # Rule 4 — Windows drive path or schemeless → local path
    if _WIN_DRIVE_RE.match(value):
        try:
            return str(Path(value).resolve())
        except OSError:
            return None

    parsed = urlsplit(value)

    if not parsed.scheme:
        # Schemeless → local path
        try:
            return str(Path(value).resolve())
        except OSError:
            return None

    # Rule 5 — file:// scheme
    if parsed.scheme == "file":
        # Reject non-empty, non-localhost netloc (remote file:// is unsafe)
        if parsed.netloc and parsed.netloc not in ("", "localhost"):
            return None
        try:
            return str(Path(url2pathname(parsed.path)).resolve())
        except OSError:
            return None

    # Rule 6 — user-info in netloc
    if "@" in parsed.netloc:
        return None

    # Rule 7 — credential substrings in query or fragment
    from urllib.parse import parse_qsl, SplitResult
    for key, _val in parse_qsl(parsed.query):
        if any(cred in key.lower() for cred in _CREDENTIAL_SUBSTRINGS):
            return None
    if any(cred in parsed.fragment.lower() for cred in _CREDENTIAL_SUBSTRINGS):
        return None

    # Rule 8 — normalize scheme + netloc to lowercase; strip trailing slash
    normalized_scheme = parsed.scheme.lower()
    normalized_netloc = parsed.netloc.lower()
    path = parsed.path.rstrip("/") if parsed.path and parsed.path != "/" else parsed.path
    return SplitResult(
        normalized_scheme, normalized_netloc, path, parsed.query, parsed.fragment
    ).geturl()


def dump_state(state: State) -> str:
    """Serialise a State to TOML in the v0.4 ``[pack.<name>.adapters.<adapter>]``
    shape.

    Stdlib `tomllib` is read-only; we emit a deterministic textual form by
    hand. Order: schema-version, then rows sorted by ``(pack, adapter)``,
    then per-row fields in fixed order, then files sorted by path.
    Determinism matters because the state file participates in diffing and
    merging.

    The adapter is part of the table key, so it is not re-emitted as a
    field. Every key segment — pack name **and** adapter name — routes
    through `_toml_key` so a non-`[alnum-_]` name cannot inject phantom
    TOML structure (ADR-0039 / security review).
    """
    lines: list[str] = [
        f"schema-version = {_emit_basic_string(state.schema_version)}",
        "",
    ]
    for name, adapter in sorted(state.packs):
        ps = state.packs[(name, adapter)]
        prefix = f"pack.{_toml_key(name)}.adapters.{_toml_key(adapter)}"
        lines.append(f"[{prefix}]")
        lines.append(f"installed-version = {_emit_basic_string(ps.installed_version)}")
        if ps.source is not None:
            lines.append(f"source = {_emit_basic_string(ps.source)}")
        lines.append(f"install-route = {_emit_basic_string(ps.install_route)}")
        lines.append(f"scope = {_emit_basic_string(ps.scope)}")
        # ``target-file`` is emitted when set (even if it equals the
        # claude-code default) so round-trip is byte-stable for
        # explicit-default rows the install/upgrade writers may produce.
        if ps.target_file is not None:
            lines.append(f"target-file = {_emit_basic_string(ps.target_file)}")
        primitives_repr = ", ".join(_emit_basic_string(p) for p in ps.primitives)
        lines.append(f"primitives = [{primitives_repr}]")
        lines.append("")
        lines.append(f"[{prefix}.files]")
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
                lines.append(f"[{prefix}.{ptype}.{_toml_key(pname)}]")
                lines.append(f"version = {_emit_basic_string(version)}")
                lines.append("")
        # `[[pack.<name>.adapters.<adapter>.hook-wiring-owned]]` rows. Order
        # is the in-memory order — install appends; uninstall walks the
        # stored list.
        if ps.hook_wiring_owned:
            for entry in ps.hook_wiring_owned:
                lines.append(f"[[{prefix}.hook-wiring-owned]]")
                for key in sorted(entry):
                    lines.append(f"{key} = {_emit_basic_string(entry[key])}")
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
    digest = hashlib.sha1(raw.encode("utf-8"), usedforsecurity=False).hexdigest()[:8]
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
