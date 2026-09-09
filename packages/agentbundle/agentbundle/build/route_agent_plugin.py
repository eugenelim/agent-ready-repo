"""Registered behavior for the Agent Plugin distribution route."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Mapping

if TYPE_CHECKING:
    from agentbundle.build.route_lookup import RouteBehavior


@dataclass(frozen=True)
class AgentPluginRouteBehavior:
    """Keep portable packaging on its confined filesystem controls."""

    expected_admission_policy: str = "skills-only"
    expected_adapter_projector: str | None = None
    # This route reads pack metadata without following links and validates
    # every root against the confined-file helpers.
    requires_confined_discovery: bool = True
    # This route drops hook wiring.
    compiles_hook_wiring: bool = False
    lifecycle_marker_relative_path: Path | None = None
    lifecycle_marker_drift_label: str | None = None
    lifecycle_marker_drift_after_runtime_checks: bool = False
    # Last of the per-pack routes: it only ever admits or excludes a pack, so
    # nothing downstream depends on it having run first.
    build_order: int = 2

    def admits_lifecycle_marker_pack(self, pack_dir: Path) -> bool:
        """Exclude packs because this route declares no lifecycle marker."""
        return False

    def discover_packs(self, packs_dir: Any, operations: Any) -> list[Any]:
        """Use no-follow discovery backed by the confined file helpers."""
        return operations.discover_confined(packs_dir)

    def prepare_pack(self, pack: Any, operations: Any) -> None:
        """Validate portable roots before generic code can enumerate them."""
        operations.preflight_confined_pack(pack)

    def normalize_pack_error(
        self, pack: Any, error: OSError | ValueError, operations: Any
    ) -> BaseException:
        """Keep the portable route's stable, sanitized diagnostics."""
        return operations.normalize_confined_error(pack, error)

    def run_per_pack(self, context: Any, operations: Any) -> dict[str, Any]:
        """Run the existing bounded portable package projector."""
        return operations.run_agent_plugin(
            context.recipe,
            context.packs,
            context.output_dir,
            context.resolved_route,
        )

    def projection_contract(
        self, contract: dict[str, Any], capabilities: Mapping[str, Any]
    ) -> dict[str, Any]:
        """Use no runtime-adapter projection for portable packages."""
        return contract


def behavior_from_declaration(
    declaration: Mapping[str, Any],
) -> AgentPluginRouteBehavior | None:
    """Recognize the declaration for the portable root-manifest projector."""
    manifest = declaration.get("manifest-projector")
    if (
        not isinstance(manifest, Mapping)
        or manifest.get("name") != "agent-plugin-root-manifest"
    ):
        return None
    return AgentPluginRouteBehavior()


def identity_from_contract(route_contract: Mapping[str, Any]) -> str:
    """Return the declared identity owned by this behavior module."""
    declarations = route_contract.get("route")
    if not isinstance(declarations, Mapping):
        raise ValueError("distribution route contract has no route declarations")
    matches = [
        identity
        for identity, declaration in declarations.items()
        if isinstance(identity, str)
        and isinstance(declaration, Mapping)
        and behavior_from_declaration(declaration) is not None
    ]
    if len(matches) != 1:
        raise ValueError("portable distribution route has no unique declaration")
    return matches[0]


if TYPE_CHECKING:  # pragma: no cover - structural conformance only
    # Binding the concrete behavior to the Protocol is what makes mypy check
    # that this module still satisfies the dispatch surface. Without it the
    # lookup's cast would be the only thing asserting conformance, and a
    # dropped member would surface as an AttributeError mid-build.
    _conforms: RouteBehavior = AgentPluginRouteBehavior()
