"""``agentbundle catalogue sync`` handler — dry-run and check for a derived catalogue.

Neither ``--dry-run`` nor ``--check`` writes. Both resolve the upstream
source, replay the recorded derivation in memory through
``initialise_self_hosted.replay_derivation(..., interactive=False)``, and
print a plan or an answer. This phase's write path is exactly none — see
``docs/specs/catalogue-sync-dry-run/spec.md`` § Boundaries.

``resolve_catalogue`` and ``fetch_catalogue_archive_with_provenance`` are
imported at module scope (rather than lazily per call) so a caller can
monkeypatch them by attribute name on this module without reaching into
``agentbundle.catalogue`` / ``agentbundle.https_catalogue`` directly.
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable

from agentbundle.catalogue import CatalogueError, resolve_catalogue
from agentbundle.catalogue_tooling.initialise_self_hosted import (
    ReplayError,
    SelfHostedInitConfig,
    _is_attributed,
    replay_derivation,
)
from agentbundle.https_catalogue import fetch_catalogue_archive_with_provenance

if TYPE_CHECKING:
    import argparse

# Exit codes — spec AC-0013. T5 implements the rows this task's replay reaches;
# T8 owns the ordered, total predicate table over every row.
_SUCCESS = 0
_DIFFERENCE = 1
_MALFORMED = 2
_CANNOT_ANSWER = 3

# The two digest-bearing schemes fetch_catalogue_archive_with_provenance
# handles; every other URI (local path or git+https://) goes through
# resolve_catalogue instead. Whose digest each form verifies differs — see
# docs/specs/catalogue-sync-dry-run/notes/grounding/probe-digest-provenance.py —
# which is why the two get distinct fidelity tokens rather than one shared
# "verified-digest" token.
_DIGEST_BEARING_PREFIXES = ("archive+https://", "catalogue+https://")


def _resolve_source(
    source_uri: str,
) -> tuple[Path, str, str | None, str | None, Callable[[], None] | None]:
    """Dispatch *source_uri* to its resolver.

    Returns ``(path, fidelity_token, archive_sha256, source_revision,
    cleanup)``. ``cleanup`` is a zero-argument callable that removes the
    extracted archive directory a digest-bearing fetch handed this caller
    ownership of, or ``None`` when there is nothing to clean up (a local
    path is never extracted; a ``git+https://`` fetch self-cleans via
    ``atexit`` inside ``resolve_catalogue``, so this caller owns no
    directory for that form either).
    """
    if source_uri.startswith(_DIGEST_BEARING_PREFIXES):
        result = fetch_catalogue_archive_with_provenance(source_uri)
        token = (
            "digest-publisher-asserted"
            if source_uri.startswith("catalogue+https://")
            else "digest-adopter-pinned"
        )
        extracted = result.path

        def _cleanup() -> None:
            shutil.rmtree(str(extracted), ignore_errors=True)

        return extracted, token, result.archive_sha256, result.source_revision, _cleanup

    path = resolve_catalogue(source_uri)
    token = "git-tls" if source_uri.startswith("git+https://") else "local-path"
    return path, token, None, None, None


def _plan_document(
    *,
    target: Path,
    dry_run: bool,
    check: bool,
    fidelity_token: str,
    archive_sha256: str | None,
    source_revision: str | None,
    attribution: str,
    tooling: str,
    guides: str,
    source_raw: str,
    attributed: bool,
) -> dict[str, Any]:
    doc: dict[str, Any] = {
        "command": "catalogue sync",
        "target": str(target),
        "dry_run": dry_run,
        "check": check,
        "fidelity": fidelity_token,
        "pin": {
            "archive_sha256": archive_sha256,
            "source_revision": source_revision,
        },
        "modes": {
            "attribution": attribution,
            "tooling": tooling,
            "guides": guides,
            "provenance": "flags-and-defaults",
        },
    }
    if attributed:
        doc["source"] = source_raw
    return doc


def _render_plan(doc: dict[str, Any], *, fmt: str) -> None:
    if fmt == "json":
        print(json.dumps(doc, indent=2))
        return

    modes = doc["modes"]
    lines = [
        f"fidelity: {doc['fidelity']}",
        "modes: attribution={attribution} tooling={tooling} guides={guides} "
        "(from {provenance})".format(**modes),
        f"archive_sha256: {doc['pin']['archive_sha256'] or 'absent'}",
        f"source_revision: {doc['pin']['source_revision'] or 'absent'}",
    ]
    if "source" in doc:
        lines.append(f"source: {doc['source']}")
    print("\n".join(lines))


def _refuse(
    reason: str,
    *,
    attributed: bool,
    source_raw: str,
    fmt: str,
    code: int,
) -> int:
    """Report a resolution or verification refusal.

    Never reproduces the underlying exception text: it may embed the raw
    source value (a local path is, after all, its own URI), which spec
    AC-0002 forbids surfacing outside ``attributed`` mode. Only a fixed
    reason and, when attributed, the source itself are ever printed.
    """
    if fmt == "json":
        doc: dict[str, Any] = {"ok": False, "error": reason}
        if attributed:
            doc["source"] = source_raw
        print(json.dumps(doc, indent=2))
    else:
        print(f"error: {reason}", file=sys.stderr)
        if attributed:
            print(f"  source: {source_raw}", file=sys.stderr)
    return code


def run(args: argparse.Namespace) -> int:
    target_raw: str = args.target
    target_path = Path(target_raw)
    if target_path.is_symlink():
        print(
            f"error: target {target_raw!r} is a symlink. Provide a direct path.",
            file=sys.stderr,
        )
        return _MALFORMED
    target = target_path.resolve()

    source_raw: str = args.source

    dry_run = bool(args.dry_run)
    check = bool(args.check)
    compare_tree = bool(args.compare_tree)
    if compare_tree and not check:
        print("error: --compare-tree requires --check", file=sys.stderr)
        return _MALFORMED

    attribution: str = args.attribution or "white-label"
    tooling: str = args.tooling or "external"
    guides: str = args.guides_mode or "selected"
    fmt: str = args.format
    attributed = attribution == "attributed"

    cleanup: Callable[[], None] | None = None
    try:
        source_path, fidelity_token, archive_sha256, source_revision, cleanup = (
            _resolve_source(source_raw)
        )
    except CatalogueError:
        return _refuse(
            "source could not be resolved",
            attributed=attributed,
            source_raw=source_raw,
            fmt=fmt,
            code=_CANNOT_ANSWER,
        )

    cfg = SelfHostedInitConfig(
        target=target,
        source=source_path,
        tooling=tooling,
        attribution=attribution,
        guides=guides,
        dry_run=dry_run,
    )

    try:
        replay = replay_derivation(cfg, interactive=False)
    except ReplayError:
        return _refuse(
            "source could not be verified",
            attributed=attributed,
            source_raw=source_raw,
            fmt=fmt,
            code=_CANNOT_ANSWER,
        )
    finally:
        if cleanup is not None:
            cleanup()

    # `--check` without a comparison mechanism is not yet implemented: T8
    # owns the ordered, total exit-code table over every AC-0013 row,
    # including the digest and tree comparisons this row would need. Answer
    # conservatively with "cannot answer" rather than inventing a verdict.
    if check:
        return _refuse(
            "check is not yet implemented",
            attributed=attributed,
            source_raw=source_raw,
            fmt=fmt,
            code=_CANNOT_ANSWER,
        )

    resolved_cfg = replay.config
    doc = _plan_document(
        target=target,
        dry_run=dry_run,
        check=check,
        fidelity_token=fidelity_token,
        archive_sha256=archive_sha256,
        source_revision=source_revision,
        attribution=resolved_cfg.attribution,
        tooling=resolved_cfg.tooling,
        guides=resolved_cfg.guides,
        source_raw=source_raw,
        attributed=_is_attributed(resolved_cfg),
    )
    _render_plan(doc, fmt=fmt)
    return _DIFFERENCE if replay.violations else _SUCCESS
