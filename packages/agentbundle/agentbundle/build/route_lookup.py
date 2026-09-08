"""Internal lookup for behavior declared by the distribution-route contract."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from agentbundle.build import route_agent_plugin, route_apm, route_claude_plugins


@dataclass(frozen=True)
class DistributionRouteDeclaration:
    """Route facts read from one validated contract declaration."""

    identity: str
    output_subdir: str
    admission_policy: str
    adapter_projector: str | None
    marketplace_projector: str | None
    lifecycle_trigger: str | None
    component_capabilities: Mapping[str, Mapping[str, str]]


def read_route_declarations(
    route_contract: Mapping[str, Any],
) -> Mapping[str, DistributionRouteDeclaration]:
    """Parse every declared route into route-name-free contract facts."""
    declarations = route_contract.get("route")
    if not isinstance(declarations, Mapping):
        raise ValueError("distribution route contract has no route declarations")

    parsed: dict[str, DistributionRouteDeclaration] = {}
    for route_key, declaration in declarations.items():
        if not isinstance(route_key, str) or not isinstance(declaration, Mapping):
            raise ValueError("distribution route contract contains an invalid route")
        identity = declaration.get("identity")
        layout = declaration.get("package-layout")
        manifest = declaration.get("manifest-projector")
        capabilities = declaration.get("component-capabilities")
        if (
            not isinstance(identity, str)
            or not isinstance(layout, Mapping)
            or not isinstance(manifest, Mapping)
            or not isinstance(capabilities, Mapping)
        ):
            raise ValueError(
                f"distribution route {route_key!r} contains an invalid declaration"
            )

        output_subdir = layout.get("output-subdir")
        admission_policy = manifest.get("admission-policy")
        adapter_projector = manifest.get("adapter-projector")
        marketplace_projector = declaration.get("marketplace-projector")
        lifecycle_trigger = declaration.get("lifecycle-trigger")
        if not all(
            isinstance(value, str)
            for value in (
                output_subdir,
                admission_policy,
                adapter_projector,
                marketplace_projector,
                lifecycle_trigger,
            )
        ):
            raise ValueError(
                f"distribution route {route_key!r} contains an invalid declaration"
            )

        parsed_capabilities: dict[str, dict[str, str]] = {}
        for capability_name, capability in capabilities.items():
            if (
                not isinstance(capability_name, str)
                or not isinstance(capability, Mapping)
                or not all(
                    isinstance(key, str) and isinstance(value, str)
                    for key, value in capability.items()
                )
            ):
                raise ValueError(
                    f"distribution route {route_key!r} contains an invalid declaration"
                )
            parsed_capabilities[capability_name] = dict(capability)

        if identity in parsed:
            raise ValueError(
                f"distribution route identity {identity!r} is declared more than once"
            )
        parsed[identity] = DistributionRouteDeclaration(
            identity=identity,
            output_subdir=output_subdir,
            admission_policy=admission_policy,
            adapter_projector=(
                None if adapter_projector == "none" else adapter_projector
            ),
            marketplace_projector=(
                None if marketplace_projector == "none" else marketplace_projector
            ),
            lifecycle_trigger=(
                None if lifecycle_trigger == "none" else lifecycle_trigger
            ),
            component_capabilities=parsed_capabilities,
        )
    return parsed


class RouteBehavior(Protocol):
    """Operations and invariants owned by one distribution route."""

    # Declared read-only: every registered behavior is a frozen dataclass, and a
    # settable protocol member would refuse one. Shared code only ever reads
    # these.
    @property
    def expected_admission_policy(self) -> str: ...

    @property
    def expected_adapter_projector(self) -> str | None: ...

    @property
    def requires_confined_discovery(self) -> bool: ...

    @property
    def compiles_hook_wiring(self) -> bool: ...

    @property
    def lifecycle_marker_relative_path(self) -> Path | None: ...

    @property
    def lifecycle_marker_drift_label(self) -> str | None: ...

    @property
    def lifecycle_marker_drift_after_runtime_checks(self) -> bool: ...

    @property
    def build_order(self) -> int:
        """Where this route runs in a default build.

        Route-owned because it is load-bearing, not cosmetic: a route that can
        refuse a pack must run before any route that writes one, so a refused
        build leaves no partial output tree behind.
        """

    def admits_lifecycle_marker_pack(self, pack_dir: Path) -> bool:
        """Return whether this route expects a projected marker for one pack."""

    def discover_packs(self, packs_dir: Any, operations: Any) -> list[Any]:
        """Discover packs with this route's filesystem controls."""

    def prepare_pack(self, pack: Any, operations: Any) -> None:
        """Apply route-owned checks before shared pack inspection."""

    def normalize_pack_error(
        self, pack: Any, error: OSError | ValueError, operations: Any
    ) -> BaseException:
        """Preserve this route's diagnostic policy for shared validation."""

    def run_per_pack(self, context: Any, operations: Any) -> dict[str, Any]:
        """Run this route's registered package projector."""

    def projection_contract(
        self, contract: dict[str, Any], capabilities: Mapping[str, Any]
    ) -> dict[str, Any]:
        """Return the adapter input used by this route."""


# Registration is closed and explicit. The factories identify their declaration
# by route-owned projector semantics rather than by a shared route-name table.
_ROUTE_BEHAVIOR_FACTORIES = (
    route_apm.behavior_from_declaration,
    route_claude_plugins.behavior_from_declaration,
    route_agent_plugin.behavior_from_declaration,
)


def resolve_route_behaviors(
    route_contract: Mapping[str, Any],
) -> Mapping[str, RouteBehavior]:
    """Resolve exactly one registered behavior for every declared route."""
    declarations = route_contract.get("route")
    if not isinstance(declarations, Mapping):
        raise ValueError("distribution route contract has no route declarations")

    resolved: dict[str, RouteBehavior] = {}
    for identity, declaration in declarations.items():
        if not isinstance(identity, str) or not isinstance(declaration, Mapping):
            raise ValueError("distribution route contract contains an invalid route")
        matches = tuple(
            behavior
            for factory in _ROUTE_BEHAVIOR_FACTORIES
            if (behavior := factory(declaration)) is not None
        )
        if len(matches) != 1:
            raise ValueError(
                f"distribution route {identity!r} has no unique registered behavior"
            )
        resolved[identity] = matches[0]
    return resolved
