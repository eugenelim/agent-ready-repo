"""Catalogue self-host wrappers.

Thin wrappers over agentbundle.build.self_host.{cmd_check, cmd_self} that
expose structured SelfHostResult types. check uses dry_run=True (read-only);
write uses dry_run=False.
"""

from __future__ import annotations

from pathlib import Path

from agentbundle.catalogue_tooling.config import load_catalogue_config
from agentbundle.catalogue_tooling.results import Diagnostic, SelfHostResult, Severity

_AGENTBUNDLE_VERSION: str | None = None


def _get_agentbundle_version() -> str:
    global _AGENTBUNDLE_VERSION
    if _AGENTBUNDLE_VERSION is None:
        try:
            from agentbundle import __version__
            _AGENTBUNDLE_VERSION = __version__
        except Exception:
            _AGENTBUNDLE_VERSION = "unknown"
    return _AGENTBUNDLE_VERSION


def _make_result(ok: bool, operation: str, config: object | None) -> SelfHostResult:
    return SelfHostResult(
        ok=ok,
        diagnostics=[],
        schema_version=1,
        command="catalogue self-host",
        operation=operation,
        agentbundle_version=_get_agentbundle_version(),
        catalogue_schema_version=getattr(config, "schema", 1) if config else 1,
    )


def _preferred_adapter(config: object | None) -> str | None:
    """Extract preferred_adapter from a loaded CatalogueConfig, or None."""
    try:
        return config.distribution.agentbundle.preferred_adapter or None  # type: ignore[union-attr]
    except AttributeError:
        return None


def check_self_host(root: Path) -> SelfHostResult:
    """Dry-run self-host check (read-only). Returns SelfHostResult with ok=True on clean."""
    from agentbundle.build.self_host import run_self_host

    config = load_catalogue_config(root)
    packs_dir = root / (config.paths.packs if config else "packs")

    rc = run_self_host(
        working_tree=root,
        packs_dir=packs_dir,
        dry_run=True,
        force=False,
        preferred_adapter=_preferred_adapter(config),
    )
    return _make_result(ok=(rc == 0), operation="check", config=config)


def write_self_host(root: Path, force: bool = False) -> SelfHostResult:
    """Write self-host projection. Returns SelfHostResult with ok=True on success."""
    from agentbundle.build.self_host import _refuse_fixture_packs_dir, run_self_host

    config = load_catalogue_config(root)
    packs_dir = root / (config.paths.packs if config else "packs")

    # Same destructive write as `build self --packs-dir`, reached by a different
    # route: here `packs_dir` comes from `catalogue.toml` rather than a flag, so
    # a catalogue pointing `[catalogue.paths] packs` at a fixture tree would
    # overwrite the working tree with fixture data. `check_self_host` is
    # dry-run and needs no guard.
    if _refuse_fixture_packs_dir(packs_dir.resolve(), dry_run=False) is not None:
        result = _make_result(ok=False, operation="write", config=config)
        # The guard prints to stderr; under `--format json` that is invisible,
        # so surface the reason where a caller can read it.
        result.diagnostics.append(
            Diagnostic(
                code="SELF-HOST-FIXTURE-PACKS",
                severity=Severity.ERROR,
                pack=None,
                path=str(packs_dir),
                line=None,
                col=None,
                message=(
                    "packs path points into a test fixture tree; a real write "
                    "would overwrite the working tree with fixture data"
                ),
                remediation=(
                    "point [catalogue.paths] packs at your real packs "
                    "directory, or set ALLOW_FIXTURE_PACKS=1 to override"
                ),
            )
        )
        return result

    rc = run_self_host(
        working_tree=root,
        packs_dir=packs_dir,
        dry_run=False,
        force=force,
        preferred_adapter=_preferred_adapter(config),
    )
    return _make_result(ok=(rc == 0), operation="write", config=config)
