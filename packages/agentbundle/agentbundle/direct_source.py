"""Direct-source manifest admission.

The direct route intentionally has a narrower manifest profile than a
catalogue pack.  Keep this boundary here rather than encoding it in the shared
schema: the bundled validator does not support conditional schema constructs.
"""

from __future__ import annotations

import json
from importlib.resources import files
from typing import Any

from agentbundle.build.validate import validate

MANIFESTLESS_VERSION_SENTINEL = "0.0.0"

_DIRECT_TOP_LEVEL_KEYS = frozenset({"schema", "pack"})
_DIRECT_PACK_KEYS = frozenset(
    {
        "name",
        "version",
        "description",
        "readme",
        "display_name",
        "license",
        "categories",
        "keywords",
        "maintainers",
        "links",
        "metadata",
        "install",
    }
)
_DIRECT_INSTALL_KEYS = frozenset({"default-scope", "allowed-scopes"})


class DirectManifestError(ValueError):
    """Raised when a direct pack manifest is outside the supported profile."""


def validate_direct_manifest(
    manifest: dict[str, Any], *, schema: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Validate and return a schema-1, skills-only direct pack manifest.

    Catalogue callers continue to validate against the shared schema directly,
    where an absent ``schema`` means schema major 1.  Direct publishers must
    state that major explicitly so a future major cannot be interpreted under
    this route's narrower rules.
    """

    schema_major = manifest.get("schema")
    if type(schema_major) is not int or schema_major != 1:
        raise DirectManifestError("direct pack.toml must declare schema = 1")

    _reject_unknown(manifest, _DIRECT_TOP_LEVEL_KEYS, "pack.toml")

    pack = manifest.get("pack")
    if not isinstance(pack, dict):
        raise DirectManifestError("direct pack.toml must contain a [pack] table")
    _reject_unknown(pack, _DIRECT_PACK_KEYS, "[pack]")

    install = pack.get("install")
    if install is not None:
        if not isinstance(install, dict):
            raise DirectManifestError("[pack.install] must be a table")
        _reject_unknown(install, _DIRECT_INSTALL_KEYS, "[pack.install]")
        _validate_direct_install_scope(install)

    if pack.get("version") == MANIFESTLESS_VERSION_SENTINEL:
        raise DirectManifestError(
            f"direct pack.toml version must not be {MANIFESTLESS_VERSION_SENTINEL!r}"
        )

    active_schema = schema if schema is not None else _load_pack_schema()
    errors = validate(manifest, active_schema)
    if errors:
        raise DirectManifestError(f"direct pack.toml fails schema validation: {errors[0]}")
    return manifest


def _load_pack_schema() -> dict[str, Any]:
    """Load the bundled shared pack schema for direct admission."""

    return json.loads(
        files("agentbundle").joinpath("_data/pack.schema.json").read_text(
            encoding="utf-8"
        )
    )


def _reject_unknown(
    values: dict[str, Any], allowed: frozenset[str], label: str
) -> None:
    """Refuse fields outside one direct-route manifest table profile."""

    unknown = sorted(set(values) - allowed)
    if unknown:
        raise DirectManifestError(f"{label}: unsupported direct field(s): {unknown}")


def _validate_direct_install_scope(install: dict[str, Any]) -> None:
    """Preserve the local-scope opt-in rule the shared subset cannot express."""

    allowed_scopes = install.get("allowed-scopes")
    if (
        isinstance(allowed_scopes, list)
        and "local" in allowed_scopes
        and "repo" not in allowed_scopes
    ):
        raise DirectManifestError(
            "[pack.install]: local allowed-scope requires repo allowed-scope"
        )
