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

import ast
import json
import shutil
import sys
import tomllib
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable

from agentbundle.catalogue import CatalogueError, resolve_catalogue
from agentbundle.catalogue_tooling.file_safety import (
    UnsafeContentError,
    read_confined_regular_file,
)
from agentbundle.catalogue_tooling.initialise_self_hosted import (
    _OWNERSHIP_STATE_FILE,
    ReplayError,
    SelfHostedInitConfig,
    _is_attributed,
    _is_safe_recipe_text,
    _load_ownership_state,
    _load_self_host_recipe,
    _migrate_managed_paths,
    _plan_stale_owned_paths,
    replay_derivation,
)
from agentbundle.commands._common import check_spec_version_gate
from agentbundle.config import PackState, State
from agentbundle.https_catalogue import fetch_catalogue_archive_with_provenance
from agentbundle.safety import Tier, classify, companion_path

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

# `_plan_stale_owned_paths` decline tokens spec AC-0017 marks undecided — the
# confinement refusal and the unreadable entry. Every other decline reason is
# decided (compared) even though it declines removal. See that function's
# docstring for the full reason set.
_UNDECIDED_DECLINE_TOKENS = frozenset(
    {"path-confinement-refused", "recorded-entry-unreadable"}
)


def _synthesize_state(recorded: dict[str, str | None]) -> State:
    """Build the one-row ``State`` :func:`safety.classify` reads.

    A null-sha entry is recorded with the ``"sha"`` key omitted rather than
    present-and-``None`` — see plan.md's Design decisions: ``dict[str, str]``
    carrying ``None`` is a type lie that survives only through
    ``no_strict_optional`` and an ``Any`` hole.
    """
    files: dict[str, dict[str, str]] = {
        path: ({"sha": sha} if sha is not None else {})
        for path, sha in recorded.items()
    }
    return State(packs={("sync", "sync"): PackState(installed_version="0", files=files)})


def _safe_scalar(field: str, value: str | None, rejections: list[str]) -> str | None:
    """Return *value* when it passes the bounded terminal-safe scalar check.

    Spec AC-0012: every value this command renders that it did not itself
    author, whatever its origin, is routed through this gate before it
    reaches stdout, stderr, or the ``--format json`` document. A rejection
    names the field and the reason and never reproduces the value — so
    ``rejections`` accumulates a fixed message, not *value* itself.

    ``value=None`` is not a hostile value (an absent pin is reported as
    "absent", not rejected), so it passes through unchanged.
    """
    if value is None:
        return None
    if _is_safe_recipe_text(value):
        return value
    rejections.append(
        f"rejected {field}: value failed the terminal-safe scalar check"
    )
    return None


def _parse_decline_reason(reason: str) -> tuple[str, str] | None:
    """Recover ``(path, token)`` from one ``_plan_stale_owned_paths`` reason.

    Mirrors that function's fixed ``f"skipped removal of {rel_path!r}:
    {token}"`` shape. Parsing failure returns ``None`` so the caller fails
    closed to "uncompared" rather than misreporting a decided verdict.
    """
    prefix = "skipped removal of "
    if not reason.startswith(prefix) or ": " not in reason:
        return None
    path_repr, _, token = reason[len(prefix) :].rpartition(": ")
    if not path_repr:
        return None
    try:
        path = ast.literal_eval(path_repr)
    except (ValueError, SyntaxError):
        return None
    return (path, token) if isinstance(path, str) else None


def _underivable_condition(target: Path, source: Path) -> str | None:
    """Return spec AC-0009's underivable-selection condition, or ``None``.

    Every condition AC-0009 enumerates is checked here, before any call that
    would resolve an absent or discarded selection to the source's full
    contents (``select_packs``/``_select_profiles`` widen to "every pack"
    when passed ``None`` — exactly the widening AC-0009 forbids).
    """
    state_path = target / _OWNERSHIP_STATE_FILE
    if not state_path.exists() and not state_path.is_symlink():
        return "no state file at the target"

    diagnostics: list[str] = []
    raw_state = _load_ownership_state(target, diagnostics)
    if raw_state is None:
        return "the ownership-state loader could not return a state object"

    if "recipe" not in raw_state:
        return "the recorded state has no recipe key"

    raw_recipe = raw_state["recipe"]
    if not isinstance(raw_recipe, dict):
        return "the recorded recipe is not a JSON object"

    recipe = _load_self_host_recipe(raw_state, source, diagnostics)
    if recipe is None:
        # Every condition under which _load_self_host_recipe itself returns
        # None (raw_state is None, no "recipe" key, recipe not a dict) is
        # already handled above; reached only if that contract changes.
        return "the recorded recipe could not be read"

    if recipe.packs is None and recipe.profiles is None:
        if "packs" in raw_recipe or "profiles" in raw_recipe:
            return "the recorded packs or profiles selection was discarded"
        return "the recorded recipe carries neither packs nor profiles"

    return None


def _classify_planned_paths(
    target: Path,
    old_state: dict[str, Any] | None,
    planned_paths: set[str],
    rejections: list[str],
) -> tuple[dict[str, int], list[tuple[str, str, str | None]]]:
    """Classify every recorded and planned path, reconciling the seven counts.

    Walks the raw ``managed_paths`` array exactly once: every entry lands in
    exactly one bucket, so a silently dropped entry breaks the
    ``compared + uncompared`` identity rather than passing it by
    construction (spec AC-0016).

    Spec AC-0012: a recorded path (``managed_paths``) and a source-tree entry
    name (``planned_paths`` — a path the replay planned from the *source*,
    not the recorded state) are both unauthored input, so both are routed
    through the terminal-safe check before they can reach a printed row;
    a rejection is appended to *rejections* by field name only.
    """
    counts: dict[str, int] = {
        "would_update": 0,
        "would_companion": 0,
        "untouched": 0,
        "would_remove": 0,
        "schema_1_inert": 0,
        "compared": 0,
        "uncompared": 0,
    }
    rows: list[tuple[str, str, str | None]] = []

    managed_paths_raw = (old_state or {}).get("managed_paths", [])
    if not isinstance(managed_paths_raw, list):
        managed_paths_raw = []

    migrated = _migrate_managed_paths(old_state or {})
    # Entries _migrate_managed_paths drops outright (not a dict/str, or a
    # dict with no "path" key) never reach either bucket below.
    counts["uncompared"] += len(managed_paths_raw) - len(migrated)

    recorded: dict[str, str | None] = {}
    for entry in migrated:
        path = entry.get("path", "")
        sha = entry.get("sha256")
        if not _is_safe_recipe_text(path):
            counts["uncompared"] += 1
            rejections.append(
                "rejected managed_paths: entry failed the terminal-safe "
                "scalar check"
            )
            continue
        if path in recorded:
            counts["uncompared"] += 1
            continue
        recorded[path] = sha if isinstance(sha, str) else None

    # `planned_paths` names come from the replayed *source* tree, not the
    # recorded state — a source-tree entry name is unauthored input too
    # (spec AC-0012), so it is filtered the same way before it can reach a
    # printed row.
    safe_planned_paths: set[str] = set()
    for path in planned_paths:
        if _is_safe_recipe_text(path):
            safe_planned_paths.add(path)
        else:
            rejections.append(
                "rejected planned_paths: entry failed the terminal-safe "
                "scalar check"
            )
    planned_paths = safe_planned_paths

    state = _synthesize_state(recorded)
    stale_paths = [path for path in recorded if path not in planned_paths]

    for path in sorted(planned_paths):
        tier = classify(path, target, state)
        if tier is Tier.TIER_3:
            counts["untouched"] += 1
            rows.append((path, "untouched", None))
            continue
        counts["compared"] += 1
        if tier is Tier.TIER_1:
            counts["would_update"] += 1
            rows.append((path, "would-update", None))
        elif recorded.get(path) is None:
            counts["schema_1_inert"] += 1
            rows.append((path, "schema-1-inert", None))
        else:
            # `safety.companion_path` is a computed value derived from an
            # already-checked *path*, but spec AC-0012 is origin-agnostic —
            # it is routed through the same gate at its own render site
            # rather than trusted because its input already passed.
            companion = _safe_scalar(
                "companion_path", str(companion_path(Path(path))), rejections
            )
            counts["would_companion"] += 1
            rows.append((path, "would-companion", companion))

    if stale_paths:
        removable, reasons = _plan_stale_owned_paths(
            target, old_state or {}, planned_paths
        )
        removable_set = set(removable)
        decline_tokens: dict[str, str] = {}
        for reason in reasons:
            parsed = _parse_decline_reason(reason)
            if parsed is not None:
                decline_tokens[parsed[0]] = parsed[1]
        for path in stale_paths:
            if path in removable_set:
                counts["compared"] += 1
                counts["would_remove"] += 1
                rows.append((path, "would-remove", None))
                continue
            token = decline_tokens.get(path)
            if token is None or token in _UNDECIDED_DECLINE_TOKENS:
                counts["uncompared"] += 1
            else:
                counts["compared"] += 1

    return counts, rows


def _pack_toml_from_replay(name: str, file_bytes: dict[str, bytes]) -> dict[str, Any] | None:
    """Parse the source's planned ``pack.toml`` for *name*, or ``None``.

    ``file_bytes`` is the replay's already-confined read (see
    ``_collect_bytes`` in ``initialise_self_hosted.py``); this parses it
    without a second filesystem read.
    """
    content = file_bytes.get(f"packs/{name}/pack.toml")
    if content is None:
        return None
    try:
        return tomllib.loads(content.decode("utf-8"))
    except (UnicodeDecodeError, tomllib.TOMLDecodeError):
        return None


def check_adapter_contract_gate(
    pack_names: list[str], file_bytes: dict[str, bytes]
) -> int | None:
    """Refuse when a selected pack's adapter-contract major differs from the
    CLI's own (spec AC-0019).

    Reuses ``check_spec_version_gate`` — the existing uniform-refusal gate
    every other pack-manifest consumer calls — rather than re-implementing
    the major-version comparison. Returns the gate's refusal code, or
    ``None`` when every selected pack's major agrees (or declares none).
    """
    for name in pack_names:
        pack_toml = _pack_toml_from_replay(name, file_bytes)
        if pack_toml is None:
            continue
        gate = check_spec_version_gate(pack_toml)
        if gate is not None:
            return gate
    return None


def _read_baseline_pack_toml(target: Path, name: str) -> dict[str, Any] | None:
    """Read the derived tree's own copy of *name*'s manifest, or ``None``.

    Goes through the declared ``file_safety`` confinement helper rather than
    an inline path check (spec AC-0020) — a new pack the derived tree does
    not yet carry has no baseline to compare, which reads the same as any
    other confinement refusal: no signal.
    """
    baseline_path = target / "packs" / name / "pack.toml"
    try:
        baseline_bytes = read_confined_regular_file(target, baseline_path)
    except UnsafeContentError:
        return None
    try:
        return tomllib.loads(baseline_bytes.decode("utf-8"))
    except (UnicodeDecodeError, tomllib.TOMLDecodeError):
        return None


def compatibility_warnings(
    target: Path,
    pack_names: list[str],
    file_bytes: dict[str, bytes],
    rejections: list[str],
) -> list[str]:
    """Advisory rows for spec AC-0018 — warn-only, never change the exit code.

    Compares each selected pack's ``[pack] version`` and
    ``[pack.adapter-contract] version`` against the derived tree's own copy
    of that pack's manifest (read through :func:`_read_baseline_pack_toml`),
    and evaluates ``[pack.dependencies]`` ``required``/``conflicts`` edges
    against the replay's resolved selection. One row per signal; a signal
    that is absent contributes nothing.

    Every compared value here is unauthored — a source or baseline
    manifest's own text (spec AC-0012) — so a hostile one is reported to
    *rejections* by field name rather than embedded in an advisory line.
    """
    selected = set(pack_names)
    warnings: list[str] = []
    source_tomls: dict[str, dict[str, Any]] = {}

    for name in pack_names:
        source_toml = _pack_toml_from_replay(name, file_bytes)
        if source_toml is None:
            continue
        source_tomls[name] = source_toml

        baseline_toml = _read_baseline_pack_toml(target, name)
        if baseline_toml is None:
            continue

        source_pack = source_toml.get("pack", {})
        baseline_pack = baseline_toml.get("pack", {})
        if not isinstance(source_pack, dict) or not isinstance(baseline_pack, dict):
            continue

        source_version = source_pack.get("version")
        baseline_version = baseline_pack.get("version")
        if isinstance(source_version, str) and isinstance(baseline_version, str):
            safe_source_version = _safe_scalar(
                "pack_version", source_version, rejections
            )
            safe_baseline_version = _safe_scalar(
                "pack_version", baseline_version, rejections
            )
            if (
                safe_source_version is not None
                and safe_baseline_version is not None
                and safe_source_version != safe_baseline_version
            ):
                warnings.append(
                    f"advisory: pack version differs for {name!r} — derived "
                    f"tree carries {safe_baseline_version!r}, source "
                    f"declares {safe_source_version!r}"
                )

        source_contract = source_pack.get("adapter-contract", {})
        baseline_contract = baseline_pack.get("adapter-contract", {})
        source_contract_version = (
            source_contract.get("version") if isinstance(source_contract, dict) else None
        )
        baseline_contract_version = (
            baseline_contract.get("version")
            if isinstance(baseline_contract, dict)
            else None
        )
        safe_source_contract_version = (
            _safe_scalar("adapter_contract_version", source_contract_version, rejections)
            if isinstance(source_contract_version, str)
            else None
        )
        safe_baseline_contract_version = (
            _safe_scalar("adapter_contract_version", baseline_contract_version, rejections)
            if isinstance(baseline_contract_version, str)
            else None
        )
        source_contract_hostile = (
            isinstance(source_contract_version, str)
            and safe_source_contract_version is None
        )
        baseline_contract_hostile = (
            isinstance(baseline_contract_version, str)
            and safe_baseline_contract_version is None
        )
        # Either side may omit `[pack.adapter-contract]` entirely — the field
        # is optional (unlike `[pack] version`), so "differs" has to compare
        # against an absent baseline too, not only a baseline that also
        # declares one. A hostile value on either side is already reported
        # to *rejections* above; the comparison itself is skipped rather
        # than risking a display built from a value that failed the check.
        if (
            not source_contract_hostile
            and not baseline_contract_hostile
            and safe_source_contract_version != safe_baseline_contract_version
            and (
                isinstance(safe_source_contract_version, str)
                or isinstance(safe_baseline_contract_version, str)
            )
        ):
            baseline_display = (
                safe_baseline_contract_version
                if isinstance(safe_baseline_contract_version, str)
                else "absent"
            )
            source_display = (
                safe_source_contract_version
                if isinstance(safe_source_contract_version, str)
                else "absent"
            )
            warnings.append(
                f"advisory: adapter-contract version differs for {name!r} — "
                f"derived tree carries {baseline_display!r}, source "
                f"declares {source_display!r}"
            )

    for name, source_toml in source_tomls.items():
        deps = source_toml.get("pack", {}).get("dependencies", {})
        if not isinstance(deps, dict):
            continue
        for entry in deps.get("required") or []:
            if not isinstance(entry, dict):
                continue
            dep_name = entry.get("pack")
            if not isinstance(dep_name, str):
                continue
            safe_dep_name = _safe_scalar("dependency_edge_name", dep_name, rejections)
            if safe_dep_name is not None and safe_dep_name not in selected:
                warnings.append(
                    f"advisory: pack {name!r} declares a required dependency on "
                    f"{safe_dep_name!r}, which the resolved selection does not include"
                )
        for entry in deps.get("conflicts") or []:
            if not isinstance(entry, dict):
                continue
            dep_name = entry.get("pack")
            if not isinstance(dep_name, str):
                continue
            safe_dep_name = _safe_scalar("dependency_edge_name", dep_name, rejections)
            if safe_dep_name is not None and safe_dep_name in selected:
                warnings.append(
                    f"advisory: pack {name!r} declares a conflict with "
                    f"{safe_dep_name!r}, which the resolved selection includes"
                )

    return warnings


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
    pack_names: list[str],
    profile_names: list[str],
    summary: dict[str, int],
    verdict_rows: list[tuple[str, str, str | None]],
    compatibility: list[str],
    rejections: list[str],
) -> dict[str, Any]:
    """Build the plan document, following ``upgrade._build_json_doc``'s
    ``summary``-carrying shape and vocabulary.

    Spec AC-0012: ``archive_sha256``, ``source_revision`` and — under
    ``attributed`` — the source URI are all unauthored (resolved from a
    remote document or the adopter's own ``--source`` flag rather than
    written by this command), so each is routed through the terminal-safe
    check here, at the one place they are assembled for rendering.
    """
    safe_archive_sha256 = _safe_scalar("archive_sha256", archive_sha256, rejections)
    safe_source_revision = _safe_scalar("source_revision", source_revision, rejections)
    doc: dict[str, Any] = {
        "command": "catalogue sync",
        "target": str(target),
        "dry_run": dry_run,
        "check": check,
        "fidelity": fidelity_token,
        "pin": {
            "archive_sha256": safe_archive_sha256,
            "source_revision": safe_source_revision,
        },
        "modes": {
            "attribution": attribution,
            "tooling": tooling,
            "guides": guides,
            "provenance": "flags-and-defaults",
        },
        "packs": pack_names,
        "profiles": profile_names,
        "summary": summary,
        "compatibility": compatibility,
        "verdicts": [
            {
                "path": path,
                "verdict": verdict,
                **({"companion": companion} if companion else {}),
            }
            for path, verdict, companion in verdict_rows
        ],
    }
    if attributed:
        safe_source = _safe_scalar("source", source_raw, rejections)
        if safe_source is not None:
            doc["source"] = safe_source
    doc["rejections"] = list(rejections)
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
    lines.append("packs: " + (", ".join(doc["packs"]) or "(none)"))
    lines.append("profiles: " + (", ".join(doc["profiles"]) or "(none)"))
    for line in doc.get("rejections", []):
        lines.append(line)
    for line in doc.get("compatibility", []):
        lines.append(line)
    for row in doc["verdicts"]:
        line = f"{row['verdict']}: {row['path']}"
        if "companion" in row:
            line += f" -> companion {row['companion']}"
        lines.append(line)
    counts = doc["summary"]
    lines.append(
        "counts: would-update={would_update} would-companion={would_companion} "
        "untouched={untouched} would-remove={would_remove} "
        "schema-1-inert={schema_1_inert} compared={compared} "
        "uncompared={uncompared}".format(**counts)
    )
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
    reason and, when attributed, the source itself are ever printed — and
    even then only once it passes AC-0012's terminal-safe check, same as
    every other unauthored value this command renders.
    """
    rejections: list[str] = []
    safe_source = _safe_scalar("source", source_raw, rejections) if attributed else None
    if fmt == "json":
        doc: dict[str, Any] = {"ok": False, "error": reason}
        if attributed:
            if safe_source is not None:
                doc["source"] = safe_source
            else:
                doc["rejections"] = rejections
        print(json.dumps(doc, indent=2))
    else:
        print(f"error: {reason}", file=sys.stderr)
        if attributed:
            if safe_source is not None:
                print(f"  source: {safe_source}", file=sys.stderr)
            else:
                for line in rejections:
                    print(f"  {line}", file=sys.stderr)
    return code


def run(args: argparse.Namespace) -> int:
    target_raw: str = args.target
    source_raw: str = args.source
    dry_run = bool(args.dry_run)
    check = bool(args.check)
    compare_tree = bool(args.compare_tree)
    attribution: str = args.attribution or "white-label"
    tooling: str = args.tooling or "external"
    guides: str = args.guides_mode or "selected"
    fmt: str = args.format
    attributed = attribution == "attributed"

    # Rendering is bounded on all three channels (stdout, stderr, and the
    # `--format json` document) from the first refusal onward — every
    # branch below reaches `_refuse`, never a bespoke print, so a malformed
    # invocation gets the same JSON-aware shape as every other refusal.
    target_path = Path(target_raw)
    if target_path.is_symlink():
        return _refuse(
            f"target {target_raw!r} is a symlink. Provide a direct path.",
            attributed=attributed,
            source_raw=source_raw,
            fmt=fmt,
            code=_MALFORMED,
        )
    target = target_path.resolve()

    if compare_tree and not check:
        return _refuse(
            "--compare-tree requires --check",
            attributed=attributed,
            source_raw=source_raw,
            fmt=fmt,
            code=_MALFORMED,
        )

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
        condition = _underivable_condition(target, source_path)
        if condition is not None:
            return _refuse(
                f"no recorded selection is derivable: {condition}",
                attributed=attributed,
                source_raw=source_raw,
                fmt=fmt,
                code=_CANNOT_ANSWER,
            )
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

    # Spec AC-0019 — a selected pack's adapter-contract major differing from
    # the CLI's own refuses uniformly, via the same gate every other pack-
    # manifest consumer calls. Unlike AC-0018's warnings below, this changes
    # the exit code and prints no plan.
    gate_code = check_adapter_contract_gate(replay.pack_names, replay.file_bytes)
    if gate_code is not None:
        return gate_code

    resolved_cfg = replay.config
    planned_paths = set(replay.file_bytes.keys())
    # One shared rejections list: every value this command did not itself
    # author — a recorded path, a source-tree entry name, a manifest's own
    # version string, the resolved digest/revision, and the source URI
    # itself — is routed through the terminal-safe check before it can
    # reach any output surface (spec AC-0012), and every rejection lands
    # here regardless of which stage produced it.
    rejections: list[str] = []
    summary_counts, verdict_rows = _classify_planned_paths(
        target, replay.old_state, planned_paths, rejections
    )
    compatibility = compatibility_warnings(
        target, replay.pack_names, replay.file_bytes, rejections
    )
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
        pack_names=replay.pack_names,
        profile_names=replay.profile_names,
        summary=summary_counts,
        verdict_rows=verdict_rows,
        compatibility=compatibility,
        rejections=rejections,
    )
    _render_plan(doc, fmt=fmt)
    return _DIFFERENCE if replay.violations else _SUCCESS
