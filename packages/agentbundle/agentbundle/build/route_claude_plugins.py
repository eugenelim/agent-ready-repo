"""Registered behavior for the Claude Plugins distribution route."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Mapping

if TYPE_CHECKING:
    from agentbundle.build.route_lookup import RouteBehavior


@dataclass(frozen=True)
class ClaudePluginsRouteBehavior:
    """Keep Claude packaging and consent controls together."""

    expected_admission_policy: str = "user-publishable-with-consent"
    expected_adapter_projector: str | None = "claude-code"
    # This route uses the established generic discovery.
    requires_confined_discovery: bool = False
    # This route compiles hook wiring into its plugin manifest.
    compiles_hook_wiring: bool = True
    lifecycle_marker_relative_path: Path | None = Path(
        ".claude-plugin/scripts/install-marker.py"
    )
    lifecycle_marker_drift_label: str | None = "writer-template drift"
    lifecycle_marker_drift_after_runtime_checks: bool = False
    # First in a default build: this route refuses a pack that publishes hooks
    # without consent, and that refusal has to precede any route's first write.
    build_order: int = 0

    def admits_lifecycle_marker_pack(self, pack_dir: Path) -> bool:
        """Expect a marker only for a publishable source plugin pack."""
        from agentbundle.build.main import pack_is_publishable

        return (
            (pack_dir / ".claude-plugin" / "plugin.json").exists()
            and pack_is_publishable(pack_dir)
        )

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
        """Run the existing adapter-backed package projector."""
        return operations.run_adapter(context)

    def projection_contract(
        self, contract: dict[str, Any], capabilities: Mapping[str, Any]
    ) -> dict[str, Any]:
        """Compile route capabilities into a fresh adapter projection."""
        projection: list[dict[str, Any]] = []
        for source_entry in contract["adapter"]["claude-code"].get("projection", []):
            primitive = source_entry["primitive"]
            capability = capabilities[primitive]
            if (
                capability["status"] == "dropped"
                or capability["mode"] == "compiled-manifest"
            ):
                entry = {"primitive": primitive, "mode": "dropped"}
            else:
                entry = dict(source_entry)
                entry["mode"] = capability["mode"]
                entry["target-path"] = capability["target-path"]
            projection.append(entry)
        adapters = dict(contract["adapter"])
        adapters["claude-code"] = {
            **contract["adapter"]["claude-code"],
            "projection": projection,
        }
        return {**contract, "adapter": adapters}


def behavior_from_declaration(
    declaration: Mapping[str, Any],
) -> ClaudePluginsRouteBehavior | None:
    """Recognize the declaration for the Claude package projector."""
    manifest = declaration.get("manifest-projector")
    if (
        not isinstance(manifest, Mapping)
        or manifest.get("name") != "claude-plugin"
    ):
        return None
    return ClaudePluginsRouteBehavior()


if TYPE_CHECKING:  # pragma: no cover - structural conformance only
    # Binding the concrete behavior to the Protocol is what makes mypy check
    # that this module still satisfies the dispatch surface. Without it the
    # lookup's cast would be the only thing asserting conformance, and a
    # dropped member would surface as an AttributeError mid-build.
    _conforms: RouteBehavior = ClaudePluginsRouteBehavior()
