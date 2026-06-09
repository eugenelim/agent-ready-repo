"""shared-libs/ source enumeration for the adapter-root-bins companion rail.

Source rule: ``packs/<pack>/.apm/shared-libs/*.py``.

RFC-0023 retired the original projection contract. The build pipeline
no longer byte-copies ``shared-libs/*.py`` into every skill declaring
``metadata.auth: creds`` — those consumers now resolve credentials via
the pip-installable ``credbroker`` library imported in-process, and the
18 vendored copies (six consumer ``scripts/`` × three shim files) were
removed. What survives in this module is **source enumeration**:
``adapter_root_bins`` calls ``collect_sources`` (and reads
``SOURCE_SUBDIR``) to locate ``credentials_shim.py`` for the AC22b
companion-shim projection into ``<scope-root>/.agentbundle/bin/`` and to
detect inter-pack basename collisions. The shim *source* under
``packs/credential-brokers/.apm/shared-libs/`` is therefore kept — it is
the projection source for the ``sso-broker`` companion shim, whose
per-platform Tier-2 backend modules import ``Tier2HardFailError`` from
it (``adapter_root_bins._assert_shim_companion_present``).

Inter-pack collision: two packs both shipping ``shared-libs/<file>``
under the same basename is a hard error (``ValueError``) at enumeration
time. The v1 catalogue ships one source pack (``credential-brokers``);
the rail exists to refuse a future second-pack collision before it can
silently overwrite.

The detection of ``metadata.auth: creds`` and the projection/drift
machinery that consumed it were removed with the projection in RFC-0023;
the standing regression that no shim copy reappears under a consumer
``scripts/`` lives in ``tests/test_shared_libs_projection.py``.
"""

from __future__ import annotations

from pathlib import Path

# Pin the source path so a downstream consumer that wants to
# enumerate shim sources doesn't hardcode the literal repeatedly.
SOURCE_SUBDIR = ".apm/shared-libs"


def collect_sources(packs_dir: Path) -> dict[str, Path]:
    """Return ``{basename → source_path}`` for every ``.apm/shared-libs/*.py``.

    Raises ``ValueError`` on inter-pack basename collision — two packs
    shipping the same basename produces non-deterministic projection
    order and silent overwrites; refuse hard at enumeration time.

    Consumed by ``adapter_root_bins`` for the AC22b companion-shim
    projection and its collision rail; the original skill-``scripts/``
    projection was retired in RFC-0023.
    """
    sources: dict[str, Path] = {}
    for pack in sorted(packs_dir.iterdir()):
        if not pack.is_dir() or not (pack / "pack.toml").exists():
            continue
        shared = pack / SOURCE_SUBDIR
        if not shared.is_dir():
            continue
        for src in sorted(shared.glob("*.py")):
            if src.name in sources:
                raise ValueError(
                    f"shared-libs collision: '{src.name}' shipped by both "
                    f"{sources[src.name]} and {src}"
                )
            sources[src.name] = src
    return sources
