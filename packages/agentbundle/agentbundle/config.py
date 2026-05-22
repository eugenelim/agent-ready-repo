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

import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


STATE_SCHEMA_VERSION = "0.1"


class ConfigError(ValueError):
    """Raised when a TOML source fails to load or fails schema invariants."""


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


def load_state(path: Path) -> State:
    """Load `.agent-ready-state.toml`. Returns empty State if file is absent.

    Absent is **not** an error — fresh repos legitimately have no state file
    before the first install / init-state. Callers distinguish "absent" from
    "present but empty" via `path.exists()` if they need to.
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

        ps = PackState(
            installed_version=body.get("installed-version", ""),
            source=body.get("source", "agent-ready-repo"),
            install_route=body.get("install-route", "cli"),
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
    lines: list[str] = [f'schema-version = "{state.schema_version}"', ""]
    for name in sorted(state.packs):
        ps = state.packs[name]
        lines.append(f"[pack.{_toml_key(name)}]")
        lines.append(f'installed-version = "{ps.installed_version}"')
        lines.append(f'source = "{ps.source}"')
        lines.append(f'install-route = "{ps.install_route}"')
        primitives_repr = ", ".join(f'"{p}"' for p in ps.primitives)
        lines.append(f"primitives = [{primitives_repr}]")
        lines.append("")
        lines.append(f"[pack.{_toml_key(name)}.files]")
        for relpath in sorted(ps.files):
            entry = ps.files[relpath]
            inline = ", ".join(
                f'{k} = "{v}"' for k, v in sorted(entry.items())
            )
            lines.append(f'"{relpath}" = {{ {inline} }}')
        lines.append("")
        # Mixed-version primitive overrides (T12).
        for ptype, primitives in sorted(ps.primitive_versions.items()):
            for pname, version in sorted(primitives.items()):
                lines.append(f"[pack.{_toml_key(name)}.{ptype}.{_toml_key(pname)}]")
                lines.append(f'version = "{version}"')
                lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _toml_key(name: str) -> str:
    """Quote a TOML key if it contains characters that require quoting."""
    if name and all(c.isalnum() or c in "-_" for c in name):
        return name
    return f'"{name}"'


# ---------------------------------------------------------------------------
# .adapt-discovery.toml  (CLI reads, never writes)
# ---------------------------------------------------------------------------


def load_adapt_discovery(path: Path) -> dict[str, Any]:
    """Read `.adapt-discovery.toml` if present; return {} otherwise.

    Spec rail: the CLI may **read** this file but must never write it. The
    `adapt-to-project` LLM skill owns the write side.
    """
    if not path.exists():
        return {}
    try:
        return tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(
            f".adapt-discovery.toml at {path} is not valid TOML: {exc}"
        ) from exc


# ---------------------------------------------------------------------------
# --values-from <file.toml>
# ---------------------------------------------------------------------------


def load_values_from(path: Path) -> dict[str, str]:
    """Load `--values-from` TOML; return a flat dict of marker → value.

    The file shape is a single table of string values:

      [values]
      PROJECT_NAME = "myproj"
      OWNER        = "octocat"
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
    values = raw.get("values", raw)
    if not isinstance(values, dict):
        raise ConfigError("expected a [values] table of string entries")
    out: dict[str, str] = {}
    for k, v in values.items():
        if not isinstance(v, str):
            raise ConfigError(f"value for {k!r} must be a string, got {type(v).__name__}")
        out[str(k)] = v
    return out
