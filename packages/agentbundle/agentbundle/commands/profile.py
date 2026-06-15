"""Profile-manifest reader (RFC-0034 / spec pack-profiles, T1).

A *profile* is a first-party-curated, single-scope set of packs an adopter
installs in one command. It is a hand-authored ``profiles/<name>.toml`` at the
catalogue root, read **only** by the ``agentbundle`` CLI — it adds zero
primitives, zero runtime, and zero adapter-contract surface (RFC-0034).

This module owns reading and validating those manifests. It does **not**
orchestrate installs (that is ``commands/install.py``'s ``_run_profile``) and it
does **not** lint the catalogue's profiles against the live ``packs/`` tree
(that is ``tools/lint-profiles.py``).

Manifest shape (closed schema ``_data/profile.schema.json``)::

    scope = "user"            # required, "user" | "repo"
    description = "..."        # required
    [[packs]]                  # required, ordered (deps-first), >= 1 entry
    pack = "architect"
    [[packs]]
    pack = "research"

The profile **id** is the filename stem, not a manifest field; it must match
``^[a-z0-9][a-z0-9-]*$`` (the same grammar packs use).
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

try:  # Python 3.11+ stdlib; the package targets 3.11+.
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - 3.10 fallback if ever needed
    import tomli as tomllib  # type: ignore[no-redef]

# Same grammar as pack names (docs/CONVENTIONS.md) and ``install._PACK_NAME_RE``.
PROFILE_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")

_HERE = Path(__file__).resolve().parent


class ProfileError(Exception):
    """A profile manifest could not be located, parsed, or validated.

    Callers print ``str(exc)`` to stderr and exit non-zero, mirroring the
    ``ConfigError`` / ``CatalogueError`` handling in the install/list-packs
    command handlers.
    """


@dataclass(frozen=True)
class Profile:
    """A parsed, schema-valid profile manifest.

    ``packs`` is the authored (deps-first) order, preserved from the TOML
    array-of-tables — the orchestrator installs in exactly this order and the
    lint enforces it is dependency-respecting.
    """

    id: str
    scope: str
    description: str
    packs: tuple[str, ...]


def _schema_path() -> Path:
    """Locate the bundled ``_data/profile.schema.json``.

    Unlike ``pack.schema.json`` (which also ships to ``docs/contracts/`` as an
    adopter-facing contract), the profile schema is internal and lives only at
    ``_data/`` — it ships with both the editable checkout and the zipapp. The
    caller surfaces a clear error if it is ever absent.
    """
    return _HERE.parent / "_data" / "profile.schema.json"


def profiles_dir(catalogue_dir: Path) -> Path:
    """Return the catalogue's ``profiles/`` directory (may not exist)."""
    return catalogue_dir / "profiles"


def _parse_and_validate(profile_id: str, toml_path: Path) -> Profile:
    """Parse + schema-validate one manifest into a :class:`Profile`.

    Raises :class:`ProfileError` with a one-line, profile-named message on any
    failure (bad id grammar, missing file, bad TOML, schema violation).
    """
    if not PROFILE_ID_RE.fullmatch(profile_id):
        raise ProfileError(
            f"profile {profile_id!r} has invalid id: "
            f"must match ^[a-z0-9][a-z0-9-]*$ (the filename stem)"
        )
    if not toml_path.exists():
        raise ProfileError(
            f"profile {profile_id!r} not found at {toml_path}; "
            f"expected <catalogue>/profiles/{profile_id}.toml"
        )
    try:
        raw = tomllib.loads(toml_path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        raise ProfileError(f"profile {profile_id!r}: invalid TOML: {exc}") from exc

    # In-house validator (no jsonschema dependency), same one validate.py uses.
    from agentbundle.build.validate import validate as validate_instance

    schema_path = _schema_path()
    if not schema_path.exists():
        raise ProfileError(
            f"profile.schema.json not found at {schema_path}"
        )
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    errors = validate_instance(raw, schema)
    if errors:
        raise ProfileError(f"profile {profile_id!r}: schema error — {errors[0]}")

    packs = tuple(entry["pack"] for entry in raw["packs"])
    return Profile(
        id=profile_id,
        scope=raw["scope"],
        description=raw["description"],
        packs=packs,
    )


def load_profile(catalogue_dir: Path, profile_id: str) -> Profile:
    """Load a single profile by id from ``<catalogue_dir>/profiles/<id>.toml``.

    Raises :class:`ProfileError` on any failure.
    """
    toml_path = profiles_dir(catalogue_dir) / f"{profile_id}.toml"
    return _parse_and_validate(profile_id, toml_path)


def list_profiles(catalogue_dir: Path) -> list[Profile]:
    """Return every valid profile under ``<catalogue_dir>/profiles/``.

    Sorted by id. A file whose stem is not a valid profile id, or whose body
    fails the schema, is skipped with a stderr note (mirrors ``list-packs``
    skipping a malformed ``pack.toml``) rather than aborting the listing.
    """
    pdir = profiles_dir(catalogue_dir)
    if not pdir.is_dir():
        return []
    out: list[Profile] = []
    for toml_path in sorted(pdir.glob("*.toml"), key=lambda p: p.stem):
        profile_id = toml_path.stem
        try:
            out.append(_parse_and_validate(profile_id, toml_path))
        except ProfileError as exc:
            print(f"list-profiles: skipping {toml_path.name}: {exc}", file=sys.stderr)
            continue
    return out
