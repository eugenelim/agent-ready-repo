"""Registered behavior for the APM distribution route."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Mapping

if TYPE_CHECKING:
    from agentbundle.build.route_lookup import RouteBehavior


@dataclass(frozen=True)
class ApmRouteBehavior:
    """Keep APM packaging on its existing generic filesystem controls."""

    expected_admission_policy: str = "all-packs"
    expected_adapter_projector: str | None = None
    # This route uses the established generic discovery.
    requires_confined_discovery: bool = False
    # This route projects hook wiring as files, not a manifest.
    compiles_hook_wiring: bool = False
    lifecycle_marker_relative_path: Path | None = Path(
        ".apm/hooks/install-marker.py"
    )
    lifecycle_marker_drift_label: str | None = "APM writer-template drift"
    lifecycle_marker_drift_after_runtime_checks: bool = True
    # Runs after the refusing route and before the portable one; this route
    # admits every pack, so it writes rather than refuses.
    build_order: int = 1

    def admits_lifecycle_marker_pack(self, pack_dir: Path) -> bool:
        """Expect the lifecycle marker for every discovered source pack."""
        return True

    def discover_packs(self, packs_dir: Any, operations: Any) -> list[Any]:
        """Use the established generic pack discovery path."""
        return operations.discover_generic(packs_dir)

    def prepare_pack(self, pack: Any, operations: Any) -> None:
        """Leave route-independent uniqueness checks to shared code."""

    def normalize_pack_error(
        self, pack: Any, error: OSError | ValueError, operations: Any
    ) -> BaseException:
        """Keep generic validation errors unchanged."""
        return error

    def run_per_pack(self, context: Any, operations: Any) -> dict[str, Any]:
        """Run the existing APM projector after its source-tree preflight."""
        operations.preflight_source_trees(context.packs, context.resolved_route)
        return operations.run_apm(
            context.recipe,
            context.packs,
            context.output_dir,
            context.resolved_route,
        )

    def projection_contract(
        self, contract: dict[str, Any], capabilities: Mapping[str, Any]
    ) -> dict[str, Any]:
        """Use the adapter contract without route-specific rewriting."""
        return contract


def behavior_from_declaration(
    declaration: Mapping[str, Any],
) -> ApmRouteBehavior | None:
    """Recognize the declaration for the APM package projector."""
    manifest = declaration.get("manifest-projector")
    if not isinstance(manifest, Mapping) or manifest.get("name") != "apm-package":
        return None
    return ApmRouteBehavior()


if TYPE_CHECKING:  # pragma: no cover - structural conformance only
    # Binding the concrete behavior to the Protocol is what makes mypy check
    # that this module still satisfies the dispatch surface. Without it the
    # lookup's cast would be the only thing asserting conformance, and a
    # dropped member would surface as an AttributeError mid-build.
    _conforms: RouteBehavior = ApmRouteBehavior()
