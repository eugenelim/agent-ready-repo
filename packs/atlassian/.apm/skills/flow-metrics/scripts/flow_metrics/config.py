"""State + issuetype config loading, integrity validation, sha derivation.

Implements the 9 startup integrity rules for state configuration
and ships the canonical-state lookup helper consumed at walk-time by
per-issue derivation.

Stdlib only. Python >= 3.10.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

EXIT_VALIDATION = 2

_ALLOWED_TEAM_FIELD_KINDS = ("single_value", "array")
_DEFERRED_TEAM_FIELD_KINDS = ("user_picker_group",)

DEFAULT_STATE_CONFIG_NAME = "states.default.json"
DEFAULT_ISSUETYPE_CONFIG_NAME = "issuetypes.default.json"


class ConfigError(Exception):
    """State / issuetype config error. Caller converts to exit 2."""

    exit_code: int = EXIT_VALIDATION

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


# ---------------------------------------------------------------------------
# Skill-root resolution
# ---------------------------------------------------------------------------
def _find_skill_root(start: Path | None = None) -> Path:
    """Walk up from ``start`` (default: this file) until a directory containing
    both ``SKILL.md`` and ``references/`` is found.

    Layout-agnostic so the same resolver works for user-scope installs
    under any of the three user-scope-capable adapters
    (``~/.claude/skills/flow-metrics/`` for claude-code,
    ``~/.kiro/skills/flow-metrics/`` for kiro,
    ``~/.agents/skills/flow-metrics/`` for codex per Codex's upstream
    skills docs) and in-pack development trees
    (``<repo>/packs/atlassian/.apm/skills/flow-metrics/``). During
    development the
    ``SKILL.md`` file may not exist yet (the skill docs add it); in that case we
    fall back to a directory that contains ``references/`` and a sibling
    ``scripts/`` so tests run from a clone before packaging is complete.
    """
    here = (start if start is not None else Path(__file__)).resolve()
    for parent in [here] + list(here.parents):
        if (parent / "SKILL.md").is_file() and (parent / "references").is_dir():
            return parent
    for parent in [here] + list(here.parents):
        if (parent / "references").is_dir() and (parent / "scripts").is_dir():
            return parent
    raise ConfigError(
        f"could not locate flow-metrics skill root (no parent of {here} contains "
        "SKILL.md + references/ or scripts/ + references/)"
    )


def _default_path(filename: str) -> Path:
    return _find_skill_root() / "references" / filename


# ---------------------------------------------------------------------------
# sha derivation
# ---------------------------------------------------------------------------
def derive_sha(parsed: Any) -> str:
    """Whitespace- and key-order-invariant sha of the parsed JSON.

    Hashes the canonicalised JSON form (``sort_keys=True``, no separators
    whitespace), NOT the raw file bytes. Two files whose ``json.loads``
    produce identical objects produce identical shas. Any semantic change
    (added/renamed/removed key, changed value) produces a different sha.
    """
    canonical = json.dumps(parsed, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# State config
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class ReworkSignal:
    from_states: frozenset[str]
    to_states: frozenset[str]


@dataclass(frozen=True)
class TeamField:
    id: str | None
    kind: str | None


@dataclass(frozen=True)
class StateConfig:
    canonical_states: Mapping[str, frozenset[str]]
    active_states: frozenset[str]
    wait_states: frozenset[str]
    terminal_non_delivery_states: frozenset[str]
    rework_signals: tuple[ReworkSignal, ...]
    commitment_state: str
    delivery_state: str
    team_field: TeamField
    sha: str
    align_join_field: str | None = None
    _raw_to_canonical: Mapping[str, str] = field(default_factory=dict, repr=False, compare=False)

    def canonical_for(self, raw_status: str) -> str | None:
        """O(1) lookup from raw Jira status name to canonical state.

        Returns ``None`` if ``raw_status`` is not mapped under any
        ``canonical_states`` entry. Per-issue derivation converts a
        ``None`` return into the data-dependent unmapped-status exit-2.
        """
        return self._raw_to_canonical.get(raw_status)

    def __hash__(self) -> int:
        # The default dataclass __hash__ delegates to field __hash__,
        # and MappingProxyType (wrapping a dict) is unhashable — so the
        # synthesized hash would TypeError. ``sha`` is a content
        # fingerprint of the source config, so hashing by it is exactly
        # the semantics any cache key would want.
        return hash(self.sha)


def _require_type(value: Any, expected_type: type, label: str) -> None:
    if not isinstance(value, expected_type):
        raise ConfigError(
            f"state config: '{label}' must be {expected_type.__name__}, got {type(value).__name__}"
        )


def _require_list_of_str(value: Any, label: str) -> list[str]:
    _require_type(value, list, label)
    for i, item in enumerate(value):
        if not isinstance(item, str):
            raise ConfigError(
                f"state config: '{label}[{i}]' must be string, got {type(item).__name__}"
            )
    return list(value)


def validate_state_config(parsed: Any) -> None:
    """Run the 9 startup integrity rules for state configuration.

    Each violation raises ``ConfigError`` with a message naming the
    offending field. The data-dependent unmapped-status check (rule for
    unmapped raw statuses) belongs to per-issue derivation — this
    routine does NOT consult any changelog data. Rule 9 (``team_field.id``
    validated against Jira's field catalog) is a startup check that
    requires the upstream wrapper; the *config-shape* portion (id is a
    string, kind is one of the allowed values) is enforced here, but the
    field-catalog lookup itself is left to the caller after the upstream
    wrapper lands.
    """
    if not isinstance(parsed, dict):
        raise ConfigError(
            f"state config: top-level must be a JSON object, got {type(parsed).__name__}"
        )

    canonical_states = parsed.get("canonical_states")
    if not isinstance(canonical_states, dict) or not canonical_states:
        raise ConfigError("state config: 'canonical_states' must be a non-empty object")
    for cname, raws in canonical_states.items():
        if not isinstance(cname, str):
            raise ConfigError("state config: 'canonical_states' keys must be strings")
        _require_list_of_str(raws, f"canonical_states.{cname}")
    canonical_keys = set(canonical_states.keys())

    active = _require_list_of_str(parsed.get("active_states", []), "active_states")
    wait = _require_list_of_str(parsed.get("wait_states", []), "wait_states")
    terminal = _require_list_of_str(
        parsed.get("terminal_non_delivery_states", []), "terminal_non_delivery_states"
    )
    commitment = parsed.get("commitment_state")
    delivery = parsed.get("delivery_state")
    if not isinstance(commitment, str) or not commitment:
        raise ConfigError("state config: 'commitment_state' must be a non-empty string")
    if not isinstance(delivery, str) or not delivery:
        raise ConfigError("state config: 'delivery_state' must be a non-empty string")

    rework_signals_raw = parsed.get("rework_signals", [])
    _require_type(rework_signals_raw, list, "rework_signals")
    rework_pairs: list[tuple[list[str], list[str]]] = []
    for i, entry in enumerate(rework_signals_raw):
        if not isinstance(entry, dict):
            raise ConfigError(
                f"state config: 'rework_signals[{i}]' must be an object"
            )
        froms = _require_list_of_str(
            entry.get("from", []), f"rework_signals[{i}].from"
        )
        tos = _require_list_of_str(
            entry.get("to", []), f"rework_signals[{i}].to"
        )
        rework_pairs.append((froms, tos))

    # Rule 1: commitment_state must be present in canonical_states.
    if commitment not in canonical_keys:
        raise ConfigError(
            f"state config: 'commitment_state' ({commitment}) is not a key of 'canonical_states'"
        )
    # Rule 2: delivery_state must be present in canonical_states.
    if delivery not in canonical_keys:
        raise ConfigError(
            f"state config: 'delivery_state' ({delivery}) is not a key of 'canonical_states'"
        )
    # Rule 3: commitment_state != delivery_state.
    if commitment == delivery:
        raise ConfigError(
            "state config: 'commitment_state' and 'delivery_state' must differ "
            f"(both = {commitment})"
        )
    # Rule 4: delivery_state not in terminal_non_delivery_states.
    if delivery in terminal:
        raise ConfigError(
            f"state config: 'delivery_state' ({delivery}) must not appear in "
            "'terminal_non_delivery_states'"
        )
    # Rule 5: commitment_state not in terminal_non_delivery_states.
    if commitment in terminal:
        raise ConfigError(
            f"state config: 'commitment_state' ({commitment}) must not appear in "
            "'terminal_non_delivery_states'"
        )
    # Rule 6: active_states ∩ wait_states == ∅.
    overlap = set(active) & set(wait)
    if overlap:
        raise ConfigError(
            "state config: 'active_states' and 'wait_states' must be disjoint; "
            f"overlap = {sorted(overlap)}"
        )
    # Rule 7: delivery_state not in (active_states ∪ wait_states).
    if delivery in active or delivery in wait:
        raise ConfigError(
            f"state config: 'delivery_state' ({delivery}) must not appear in "
            "'active_states' or 'wait_states'"
        )
    # Rule 8: every referenced canonical name is a key of canonical_states.
    def _check_refs(refs: list[str], label: str) -> None:
        for r in refs:
            if r not in canonical_keys:
                raise ConfigError(
                    f"state config: '{label}' references unknown canonical state '{r}'"
                )

    _check_refs(active, "active_states")
    _check_refs(wait, "wait_states")
    _check_refs(terminal, "terminal_non_delivery_states")
    for i, (froms, tos) in enumerate(rework_pairs):
        _check_refs(froms, f"rework_signals[{i}].from")
        _check_refs(tos, f"rework_signals[{i}].to")

    # team_field shape check. Rule 9's field-catalog lookup is deferred to
    # the upstream wrapper; here we enforce shape + the v2 deferral.
    team_field = parsed.get("team_field")
    if team_field is not None:
        if not isinstance(team_field, dict):
            raise ConfigError("state config: 'team_field' must be an object")
        tf_id = team_field.get("id")
        tf_kind = team_field.get("kind")
        if tf_id is not None and not isinstance(tf_id, str):
            raise ConfigError("state config: 'team_field.id' must be a string")
        if tf_kind is not None:
            if not isinstance(tf_kind, str):
                raise ConfigError("state config: 'team_field.kind' must be a string")
            if tf_kind in _DEFERRED_TEAM_FIELD_KINDS:
                raise ConfigError(
                    f"state config: 'team_field.kind = {tf_kind}' is deferred to v2; "
                    "use 'single_value' or 'array' instead"
                )
            if tf_kind not in _ALLOWED_TEAM_FIELD_KINDS:
                raise ConfigError(
                    f"state config: 'team_field.kind' must be one of"
                    f" {_ALLOWED_TEAM_FIELD_KINDS}; got '{tf_kind}'"
                )
        # A 'kind' without an 'id' has no anchor — the catalog check (rule 9)
        # would have nothing to validate. Treat as malformed.
        if tf_kind is not None and tf_id is None:
            raise ConfigError(
                "state config: 'team_field.kind' is set but 'team_field.id' is missing; "
                "either provide both or omit team_field entirely"
            )

    align_join_field = parsed.get("align_join_field")
    if align_join_field is not None and not isinstance(align_join_field, str):
        raise ConfigError("state config: 'align_join_field' must be a string when set")


def _build_state_config(parsed: dict) -> StateConfig:
    canonical_states_raw = parsed["canonical_states"]
    canonical_states: dict[str, frozenset[str]] = {
        cname: frozenset(raws) for cname, raws in canonical_states_raw.items()
    }

    raw_to_canonical: dict[str, str] = {}
    for cname, raws in canonical_states_raw.items():
        for raw in raws:
            if raw in raw_to_canonical and raw_to_canonical[raw] != cname:
                raise ConfigError(
                    f"state config: raw status '{raw}' is mapped to both"
                    f" '{raw_to_canonical[raw]}' and '{cname}'"
                )
            raw_to_canonical[raw] = cname

    rework = tuple(
        ReworkSignal(
            from_states=frozenset(entry.get("from", [])),
            to_states=frozenset(entry.get("to", [])),
        )
        for entry in parsed.get("rework_signals", [])
    )

    tf_raw = parsed.get("team_field") or {}
    team_field = TeamField(id=tf_raw.get("id"), kind=tf_raw.get("kind"))

    return StateConfig(
        canonical_states=MappingProxyType(canonical_states),
        active_states=frozenset(parsed.get("active_states", [])),
        wait_states=frozenset(parsed.get("wait_states", [])),
        terminal_non_delivery_states=frozenset(parsed.get("terminal_non_delivery_states", [])),
        rework_signals=rework,
        commitment_state=parsed["commitment_state"],
        delivery_state=parsed["delivery_state"],
        team_field=team_field,
        sha=derive_sha(parsed),
        align_join_field=parsed.get("align_join_field"),
        _raw_to_canonical=MappingProxyType(raw_to_canonical),
    )


def _read_json(path: Path, label: str) -> Any:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise ConfigError(f"{label}: file not found: {path}") from exc
    except OSError as e:
        raise ConfigError(f"{label}: cannot read {path}: {e}") from e
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise ConfigError(f"{label}: invalid JSON in {path}: {e}") from e


def load_state_config(path: Path | None = None) -> StateConfig:
    """Load and validate a state config. ``None`` resolves to the shipped default."""
    resolved = Path(path) if path is not None else _default_path(DEFAULT_STATE_CONFIG_NAME)
    parsed = _read_json(resolved, "state config")
    validate_state_config(parsed)
    return _build_state_config(parsed)


# ---------------------------------------------------------------------------
# Issuetype config
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class IssuetypeConfig:
    buckets: Mapping[str, frozenset[str]]
    sha: str
    _raw_to_bucket: Mapping[str, str] = field(default_factory=dict, repr=False, compare=False)

    def __hash__(self) -> int:
        return hash(self.sha)

    def bucket_for(self, raw_issuetype: str) -> str | None:
        """Return the bucket name for ``raw_issuetype``, or ``None`` if unmapped.

        Unmapped issuetypes are bucketed as ``"other"`` by the consumer
        (Flow Distribution); they do NOT exit 2.
        """
        return self._raw_to_bucket.get(raw_issuetype)


_RESERVED_ISSUETYPE_BUCKETS = ("other",)


def validate_issuetype_config(parsed: Any) -> None:
    if not isinstance(parsed, dict) or not parsed:
        raise ConfigError(
            "issuetype config: top-level must be a non-empty JSON object"
        )
    for bucket, raws in parsed.items():
        if not isinstance(bucket, str):
            raise ConfigError("issuetype config: bucket keys must be strings")
        if bucket in _RESERVED_ISSUETYPE_BUCKETS:
            # Spec § Issuetype configuration: "Unmapped issuetypes go into a
            # `other` bucket reported in `notes`." That sink name is
            # reserved; a user-configured `other` bucket collides with the
            # sink semantics, so reject at startup.
            raise ConfigError(
                f"issuetype config: bucket '{bucket}' is reserved for unmapped "
                "issuetypes; remove or rename it"
            )
        if not isinstance(raws, list):
            raise ConfigError(
                f"issuetype config: bucket '{bucket}' must map to a list"
            )
        for i, raw in enumerate(raws):
            if not isinstance(raw, str):
                raise ConfigError(
                    f"issuetype config: bucket '{bucket}'[{i}] must be a string"
                )


def _build_issuetype_config(parsed: dict) -> IssuetypeConfig:
    buckets: dict[str, frozenset[str]] = {
        bucket: frozenset(raws) for bucket, raws in parsed.items()
    }
    raw_to_bucket: dict[str, str] = {}
    for bucket, raws in parsed.items():
        for raw in raws:
            if raw in raw_to_bucket and raw_to_bucket[raw] != bucket:
                raise ConfigError(
                    f"issuetype config: raw issuetype '{raw}' is mapped to both "
                    f"'{raw_to_bucket[raw]}' and '{bucket}'"
                )
            raw_to_bucket[raw] = bucket
    return IssuetypeConfig(
        buckets=MappingProxyType(buckets),
        sha=derive_sha(parsed),
        _raw_to_bucket=MappingProxyType(raw_to_bucket),
    )


def load_issuetype_config(path: Path | None = None) -> IssuetypeConfig:
    resolved = Path(path) if path is not None else _default_path(DEFAULT_ISSUETYPE_CONFIG_NAME)
    parsed = _read_json(resolved, "issuetype config")
    validate_issuetype_config(parsed)
    return _build_issuetype_config(parsed)


# ---------------------------------------------------------------------------
# Rule 9: team_field.id validation against Jira's field catalog
# ---------------------------------------------------------------------------
def validate_team_field_against_catalog(
    state_config: StateConfig,
    override: str | None,
    jira: Any,
) -> None:
    """Spec rule 9: the configured ``team_field.id`` must exist in Jira's
    field catalog. Deferred from :func:`validate_state_config` because it
    requires the upstream wrapper.

    Resolution order: ``--team-field-override`` (if set) wins; else
    ``state_config.team_field.id``. If neither is set, this is a no-op
    (the field is optional unless team rollup is requested; that gate
    lives in the per-team rollup).

    Raises :class:`ConfigError` (exit 2) naming the offending id when
    the field is absent from ``jira: raw GET field``.
    """
    target_id = override if override is not None else state_config.team_field.id
    if target_id is None:
        return
    catalog = jira.raw_get("field")
    known: set = set()
    if isinstance(catalog, list):
        for item in catalog:
            if isinstance(item, dict) and isinstance(item.get("id"), str):
                known.add(item["id"])
    if target_id not in known:
        raise ConfigError(
            f"team_field.id {target_id!r} not found in Jira's field catalog"
        )
