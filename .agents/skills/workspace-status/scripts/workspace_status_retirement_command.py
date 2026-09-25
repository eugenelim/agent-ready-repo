#!/usr/bin/env python3
"""Read-only orchestration for the ``retirement-candidates`` subcommand."""

from __future__ import annotations

import importlib.util
import json
import os
import stat
import subprocess
import sys
import tomllib
from pathlib import Path
from types import ModuleType


def _load_sibling(module_name: str, filename: str) -> ModuleType:
    """Load one sibling module without depending on an installed package."""
    loaded = sys.modules.get(module_name)
    if loaded is not None:
        return loaded
    module_spec = importlib.util.spec_from_file_location(
        module_name, Path(__file__).with_name(filename)
    )
    if module_spec is None or module_spec.loader is None:
        raise ImportError(f"cannot load {filename}")
    module = importlib.util.module_from_spec(module_spec)
    sys.modules[module_name] = module
    module_spec.loader.exec_module(module)
    return module


retirement = _load_sibling(
    "workspace_status_retirement", "workspace_status_retirement.py"
)
candidates = _load_sibling(
    "workspace_status_retirement_candidates",
    "workspace_status_retirement_candidates.py",
)
contract = _load_sibling(
    "workspace_status_retirement_contract", "workspace_status_retirement_contract.py"
)

_GIT_TIMEOUT_SECONDS = 30
_TEXT_SUFFIXES = frozenset(
    {".json", ".md", ".py", ".toml", ".txt", ".yaml", ".yml"}
)


def _run_git(root: Path, arguments: list[str]) -> subprocess.CompletedProcess[bytes]:
    """Run one bounded, read-only Git query at the resolved repository root."""
    return subprocess.run(
        ["git", "-C", str(root.resolve(strict=True)), *arguments],
        check=False,
        capture_output=True,
        timeout=_GIT_TIMEOUT_SECONDS,
    )


def _bounded(value: object, limit: int) -> str:
    """Return one bounded, control-free public string."""
    text = value if isinstance(value, str) else str(value)
    clean = "".join(character for character in text if 32 <= ord(character) != 127)
    return clean[:limit]


def _workspace_spec_paths(value: object) -> list[str]:
    """Return every workspace entry path that claims to name a spec body."""
    found: list[str] = []

    def walk(node: object) -> None:
        if isinstance(node, dict):
            path = node.get("path")
            if isinstance(path, str) and path.startswith("docs/specs/"):
                found.append(path)
            for child in node.values():
                walk(child)
        elif isinstance(node, list):
            for child in node:
                walk(child)

    walk(value)
    return sorted(set(found))


def _slug_from_spec_path(value: str) -> str | None:
    """Return the slug from an exact, confined spec-body path."""
    parts = value.split("/")
    if (
        len(parts) == 4
        and parts[:2] == ["docs", "specs"]
        and parts[3] == "spec.md"
        and candidates._slug_from_spec_path(value) is not None
        and retirement._is_retirement_path(value)
    ):
        return parts[2]
    return None


def _candidate_slugs_from_disk(root: Path) -> tuple[set[str], list[str]]:
    """List immediate spec directories without following link-like entries."""
    slugs: set[str] = set()
    unsafe: list[str] = []
    specs_dir = root / "docs" / "specs"
    try:
        with os.scandir(specs_dir) as entries:
            for entry in entries:
                try:
                    inspected = entry.stat(follow_symlinks=False)
                except OSError:
                    continue
                relative = f"docs/specs/{entry.name}"
                reparse = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
                if stat.S_ISLNK(inspected.st_mode) or (
                    reparse
                    and getattr(inspected, "st_file_attributes", 0) & reparse
                ):
                    unsafe.append(relative)
                elif stat.S_ISDIR(inspected.st_mode):
                    slugs.add(entry.name)
    except OSError:
        return set(), []
    return slugs, sorted(unsafe)


def _parse_toml(root: Path, rel_path: str) -> tuple[dict | None, str | None]:
    """Read a TOML substrate and return data or its refusal code."""
    try:
        raw = retirement.confined_read_bytes(root, rel_path)
    except retirement.ConfinementRefusal as exc:
        return None, exc.code
    try:
        return tomllib.loads(raw.decode("utf-8")), None
    except (UnicodeDecodeError, tomllib.TOMLDecodeError):
        return None, "input-unparseable"


def _read_text(
    root: Path, rel_path: str, *, spec_body: bool = False
) -> tuple[str | None, str | None]:
    """Read a UTF-8 text substrate and return text or its refusal code."""
    try:
        raw = retirement.confined_read_bytes(root, rel_path, spec_body=spec_body)
    except retirement.ConfinementRefusal as exc:
        return None, exc.code
    try:
        return raw.decode("utf-8"), None
    except UnicodeDecodeError:
        return None, "input-unparseable"


def _read_json(root: Path, rel_path: str) -> tuple[dict | None, str | None]:
    """Read a JSON object substrate and return data or its refusal code."""
    text, refusal = _read_text(root, rel_path)
    if refusal is not None:
        return None, refusal
    try:
        value = json.loads(text or "")
    except json.JSONDecodeError:
        return None, "input-unparseable"
    return (value, None) if isinstance(value, dict) else (None, "input-unparseable")


def _git_query(
    root: Path, arguments: list[str]
) -> tuple[bytes | None, str | None]:
    """Return bytes from Git or the stable refusal for a bounded failure."""
    try:
        result = _run_git(root, arguments)
    except subprocess.TimeoutExpired:
        return None, "subprocess-timeout"
    except (OSError, RuntimeError, ValueError):
        return None, "evidence-ungathered"
    if result.returncode != 0:
        return None, "evidence-ungathered"
    return result.stdout, None


def _append_blocker(
    reasons: list[dict], code: str, declared_by: list[str] | None = None
) -> None:
    """Append one blocker once, with deterministic declaring evidence."""
    item: dict[str, object] = {"code": code}
    if declared_by:
        item["declared_by"] = sorted(set(declared_by))
    if item not in reasons:
        reasons.append(item)


def retirement_candidates_document(
    root: Path, *, run_date: str, stale_after_days: int = 30
) -> dict:
    """Build one deterministic retirement-candidate document from ``root``."""
    root = root.resolve(strict=True)
    cutoff = candidates.compute_cutoff_date(run_date, stale_after_days)
    disk_slugs, unsafe_directories = _candidate_slugs_from_disk(root)

    workspace, workspace_refusal = _parse_toml(root, "workspace.toml")
    workspace_paths = _workspace_spec_paths(workspace or {})
    path_slugs = {
        slug
        for path in workspace_paths
        if (slug := _slug_from_spec_path(path)) is not None
    }
    slugs = sorted(disk_slugs | path_slugs)
    state: dict[str, dict] = {
        slug: {"eligible": True, "blockers": []} for slug in slugs
    }
    refusals: list[dict] = []

    def refuse(
        code: str,
        path: str,
        suppresses: list[str] | None = None,
        *,
        declared_at: str | None = None,
        offending_value: str | None = None,
    ) -> None:
        affected = sorted(set(slugs if suppresses is None else suppresses))
        item: dict[str, object] = {
            "code": code,
            "path": _bounded(path, 1024),
            "suppresses": affected,
        }
        if declared_at is not None:
            item["declared_at"] = _bounded(declared_at, 1024)
        if offending_value is not None:
            item["offending_value"] = _bounded(offending_value, 256)
        signature = json.dumps(item, sort_keys=True)
        if all(json.dumps(existing, sort_keys=True) != signature for existing in refusals):
            refusals.append(item)
        retirement.apply_refusals(
            state,
            [retirement.Refusal(code=code, path=path, suppresses=affected)],
        )

    if workspace_refusal is not None:
        refuse(workspace_refusal, "workspace.toml")

    for unsafe in unsafe_directories:
        slug = unsafe.rsplit("/", 1)[-1]
        if slug not in state:
            state[slug] = {"eligible": True, "blockers": []}
            slugs.append(slug)
            slugs.sort()
        refuse("path-escapes-root", unsafe, [slug])

    unavailable_specs = {
        unsafe.rsplit("/", 1)[-1] for unsafe in unsafe_directories
    }
    for path in workspace_paths:
        slug = _slug_from_spec_path(path)
        if slug is None:
            refuse(
                "path-escapes-root",
                "workspace.toml",
                [],
                declared_at="workspace.toml",
                offending_value=path,
            )
    for slug in slugs:
        if slug in unavailable_specs:
            continue
        spec_dir = root / "docs" / "specs" / slug
        try:
            inspected = spec_dir.lstat()
        except OSError:
            refuse("spec-directory-absent", f"docs/specs/{slug}", [slug])
            unavailable_specs.add(slug)
            continue
        if not stat.S_ISDIR(inspected.st_mode):
            if stat.S_ISLNK(inspected.st_mode):
                refuse("path-escapes-root", f"docs/specs/{slug}", [slug])
            else:
                refuse("spec-directory-absent", f"docs/specs/{slug}", [slug])
            unavailable_specs.add(slug)
            continue
        try:
            spec_info = (spec_dir / "spec.md").lstat()
        except OSError:
            refuse("spec-file-absent", f"docs/specs/{slug}/spec.md", [slug])
            unavailable_specs.add(slug)
            continue
        if stat.S_ISLNK(spec_info.st_mode):
            refuse("path-escapes-root", f"docs/specs/{slug}/spec.md", [slug])
            unavailable_specs.add(slug)

    tracked_raw, git_refusal = _git_query(root, ["ls-files", "-z"])
    tracked_files: list[str] = []
    if git_refusal is not None:
        refuse(git_refusal, ".git")
    else:
        try:
            tracked_files = sorted(
                path for path in (tracked_raw or b"").decode("utf-8").split("\0") if path
            )
        except UnicodeDecodeError:
            refuse("evidence-ungathered", ".git")

    namespaces = retirement.infer_namespaces(tracked_files)
    manifest, manifest_refusal = _parse_toml(root, ".workspace-prune-protected.toml")
    if manifest_refusal is not None:
        refuse(manifest_refusal, ".workspace-prune-protected.toml")
    protected_slugs = candidates.extract_protected_slugs(manifest or {})

    xspec_slugs: set[str] = set()
    for path in tracked_files:
        if not path.startswith("contracts/") or not path.endswith(".json"):
            continue
        contract, contract_refusal = _read_json(root, path)
        if contract_refusal is not None:
            refuse(contract_refusal, path)
        elif contract is not None:
            xspec_slugs.update(candidates.extract_xspec_slugs(contract))

    scanned_files: list[tuple[str, str]] = []
    scan_prefixes = tuple(
        prefix for prefix in candidates.INBOUND_CITED_SURFACES if prefix != "workspace.toml"
    )
    for path in tracked_files:
        if path != "workspace.toml" and not path.startswith(scan_prefixes):
            continue
        if Path(path).suffix.lower() not in _TEXT_SUFFIXES and path != "workspace.toml":
            continue
        text, text_refusal = _read_text(root, path)
        if text_refusal is not None:
            refuse(text_refusal, path)
        elif text is not None:
            scanned_files.append((path, text))

    shipped_briefs: list[tuple[str, str]] = []
    for path, body in scanned_files:
        if not path.startswith("docs/product/briefs/"):
            continue
        status = candidates.parse_spec_status(body)
        if status is not None and status[0] == "Shipped":
            shipped_briefs.append((path, body))

    needed_by, bad_needs = candidates.build_needed_by_index(workspace or {})
    inflight, bad_collections = candidates.build_inflight_index(workspace or {})
    for source in sorted(bad_needs):
        refuse("needs-shape-unrecognised", "workspace.toml", declared_at=source)
    for collection in sorted(bad_collections):
        refuse(
            "collection-unrecognised",
            "workspace.toml",
            declared_at="workspace.toml",
            offending_value=collection,
        )

    existing_paths = frozenset(tracked_files)
    documents: list[dict] = []
    for slug in slugs:
        candidate_state = state[slug]
        spec_path = f"docs/specs/{slug}/spec.md"
        body: str | None = None
        if slug not in unavailable_specs:
            body, body_refusal = _read_text(root, spec_path, spec_body=True)
            if body_refusal is not None:
                refuse(body_refusal, spec_path, [slug])

        status_token: str | None = None
        if body is not None:
            parsed_status = candidates.parse_spec_status(body)
            if parsed_status is None or parsed_status[0] not in candidates.CANONICAL_STATUSES:
                refuse("spec-status-unrecognised", spec_path, [slug])
            else:
                status_token = parsed_status[0]

        history_raw, history_refusal = _git_query(
            root, ["log", "-1", "--format=%cs", "--", spec_path]
        )
        last_touched: str | None = None
        if history_refusal is not None:
            refuse(history_refusal, spec_path, [slug])
        else:
            try:
                history_value = (history_raw or b"").decode("ascii").strip()
                if history_value:
                    candidates.compute_cutoff_date(history_value, 0)
                    last_touched = history_value
            except (UnicodeDecodeError, ValueError):
                refuse("evidence-ungathered", spec_path, [slug])

        reasons: list[dict] = []

        for code in candidate_state["blockers"]:
            _append_blocker(reasons, code)
        if status_token is not None and candidates.detect_status_not_terminal(status_token):
            _append_blocker(reasons, "status-not-terminal")
        dependencies = candidates.detect_needed_by(slug, needed_by)
        if dependencies:
            _append_blocker(reasons, "needed-by", dependencies)
        citations = candidates.detect_inbound_cited(slug, scanned_files)
        if citations:
            _append_blocker(reasons, "inbound-cited", citations)
        briefs = candidates.detect_shipped_brief_member(slug, shipped_briefs)
        if briefs:
            _append_blocker(reasons, "shipped-brief-member", briefs)
        if candidates.detect_protected(slug, protected_slugs):
            _append_blocker(reasons, "protected")
        if candidates.detect_xspec_pinned(slug, frozenset(xspec_slugs)):
            _append_blocker(reasons, "xspec-pinned")
        if candidates.detect_inflight(slug, inflight):
            _append_blocker(reasons, "inflight")
        if last_touched is None:
            _append_blocker(reasons, "history-missing")
        elif candidates.detect_recently_changed(last_touched, cutoff):
            _append_blocker(reasons, "recently-changed")
        if body is not None:
            unresolved = candidates.detect_references_unresolved(
                slug, body, existing_paths
            )
            if unresolved:
                _append_blocker(reasons, "references-unresolved")

        notes_files = sorted(
            path
            for path in tracked_files
            if path.startswith(f"docs/specs/{slug}/notes/")
        )
        obligations = candidates.build_lasting_facts_obligations(
            notes_files, scanned_files, slug
        )
        if obligations:
            _append_blocker(reasons, "lasting-facts-unsettled")

        document: dict[str, object] = {
            "slug": slug,
            "area": retirement.attribute_spec(body or "", namespaces),
            "eligible": not reasons,
            "held_back_by": sorted(reasons, key=lambda item: str(item["code"])),
            "obligations": obligations,
        }
        if status_token is not None:
            document["status"] = status_token
        if last_touched is not None:
            document["last_touched"] = last_touched
        documents.append(document)

    return candidates.build_retirement_document(
        run_date=run_date,
        stale_after_days=stale_after_days,
        area_map={
            "present": True,
            "freshness": "in-memory",
            "namespaces": sorted(namespaces),
        },
        candidates=documents,
        refusals=sorted(
            refusals,
            key=lambda item: (
                str(item["code"]),
                str(item.get("path", "")),
                json.dumps(item, sort_keys=True),
            ),
        ),
        inbound_surfaces_not_reached=[],
        inbound_forms_recognised=sorted(candidates.INBOUND_FORMS_RECOGNISED),
        inbound_forms_not_reached=sorted(candidates.INBOUND_FORMS_NOT_REACHED),
    )


def validate_retirement_document(root: Path, document: dict) -> list[str]:
    """Validate a document against the repository's live retirement schema."""
    schema, refusal = _read_json(
        root, "contracts/jsonschema/spec-retirement-candidates.schema.json"
    )
    if refusal is not None or schema is None:
        return ["retirement schema is unavailable"]
    return contract.validate_document(document, schema)
