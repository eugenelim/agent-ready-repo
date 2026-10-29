"""Read, check and project ``workspace-status`` status output for the intent view.

The export gains one untrusted input: bytes a maintainer pipes in from
``workspace-status status``.  Everything here is a pure function over those
bytes, or a bounded read of one file descriptor, so the whole trust boundary
sits in this file.

* ``read`` takes at most ``limit`` bytes, waits at most a deadline, and never
  lets a failure escape.
* ``check`` accepts the bytes only when every rule holds, and otherwise returns
  one reason from ``REASONS``.
* ``start`` and ``project`` keep only node ids of loaded records, finding codes
  and ``next_action`` text.  ``start`` is decided over the checked lists before
  ``project`` drops any entry.

The module reads no file, runs no process and prints nothing.
"""

from __future__ import annotations

import json
import os
import re
import stat
import threading
from collections.abc import Callable, Mapping
from typing import Any, NamedTuple

READ_DEADLINE_SECONDS = 60
INPUT_LIMIT_BYTES = 4_194_304

#: Every reason a page can carry for unchecked readiness.  ``not_requested``
#: means the export was made without ``--readiness``; the rest follow the
#: order in which the checks run.
NOT_REQUESTED = "not_requested"
REASONS: tuple[str, ...] = (
    "unreadable",
    "timed_out",
    "too_large",
    "empty",
    "not_json",
    "no_workspace",
    "wrong_schema",
    "bad_workspace",
    "page_too_big",
)

_CHUNK = 65_536
_CODE_RE = re.compile(r"[a-z][a-z0-9_]{0,63}")
_NEXT_ACTION_MAX = 500
_WORKSPACE_FAILURE_CODES = frozenset({
    "invalid_workspace",
    "configuration_mismatch",
    "unsafe_path",
})
_STRIP = b" \t\n\r"

# A pinned copy of the finding table the shipped ``workspace-status`` engine
# emits next actions from.  A skill may not import from another, so a test
# compares this copy with the engine's table.  A finding whose code and sentence
# are not a pair here is shown as inert text under a generic label.
_KNOWN_FINDINGS: dict[str, str] = {
    "invalid_workspace": "Correct workspace.toml, then rerun reconciliation.",
    "invalid_entry": "Rewrite the entry to the accepted target contract.",
    "legacy_entry": "Materialize and register a canonical target entry.",
    "unsupported_legacy": "Route the item manually; do not infer a target entry.",
    "invalid_artifact_path": "Replace it with a confined canonical repository-relative path.",
    "missing_artifact": "Create and review the canonical artifact before dispatch.",
    "unreadable_artifact": "Restore readable repository state, then rerun reconciliation.",
    "invalid_captured_item": (
        "Fix the named field of that captured-item file, then rerun reconciliation."
    ),
    "unmigrated_captured_item": (
        "Run workspace-status repair-plan to move this captured item into its "
        "own file under docs/product/captured/."
    ),
    "missing_plan": "Create and approve the plan before dispatch.",
    "unapproved_spec": "Complete the spec approval gate.",
    "duplicate_membership": ("Remove the duplicate after choosing the authoritative membership."),
    "impossible_transition": ("Correct the artifact or membership through a reviewed transition."),
    "provenance_mismatch": (
        "Resolve provenance in the canonical artifact and mirror it deliberately."
    ),
    "cooled_child_scope_unknown": (
        "Set parent on the spec's lifecycle record: a resolving brief path, or "
        "none only when that spec has no parent brief; a tracker-origin entry "
        "declares source.parent instead."
    ),
    "refresh_conflict": "Resolve the conflict through the artifact's authority workflow.",
    "unsatisfied_dependency": "Complete or explicitly revise the dependency.",
    "missing_dependency": "Materialize or correct the dependency target.",
    "dependency_cycle": "Break the cycle through an explicit plan change.",
    "invalid_dependency": (
        "Rewrite the item as a typed reference or a captured-item path, "
        "or correct its receipt, in the waiting item's header."
    ),
    "unmigrated_needs": (
        "Move the entry's needs into the waiting item's Depends on: header "
        "with workspace-status repair-plan, then repair-apply."
    ),
    "invalid_receipt": ("Replace it with a reviewed receipt matching the pinned dependency."),
    "invalid_completion_receipt": (
        "Replace it with a valid reviewed completion receipt for that dependency."
    ),
    "inactive_initiative": (
        "Reactivate the initiative explicitly or move the work through governance."
    ),
    "configuration_mismatch": (
        "Install or select a consistent versioned configuration, then rerun."
    ),
    "invalid_source_authority": (
        "Correct the closed source-authority block, then rerun reconciliation."
    ),
    "source_authority_migration_required": (
        "Add the reviewed source-authority block before using refresh."
    ),
    "invalid_lifecycle_record": ("Repair or remove that record; other records still cool."),
    "cooling_state_unavailable": (
        "Install close-work or repair docs/lifecycle/; no artifact is excluded this run."
    ),
}


class ReadResult(NamedTuple):
    """Outcome of ``read``: the bytes, or the reason they could not be used."""

    data: bytes | None
    reason: str | None


class Checked(NamedTuple):
    """Status lists that passed every check, before any entry is dropped."""

    active: list[dict[str, Any]]
    ready: list[dict[str, Any]]
    blocked: list[dict[str, Any]]
    findings: list[dict[str, Any]]


class _Refusal(Exception):
    """Internal: carries the reason a check refused."""


def unchecked(reason: str) -> dict[str, Any]:
    """Return the readiness member for a page whose readiness is not checked."""
    return {"checked": False, "reason": reason}


def read(
    opener: Callable[[], int | None],
    limit: int,
    deadline_seconds: float,
) -> ReadResult:
    """Read at most ``limit`` bytes from the descriptor ``opener`` returns.

    A thread reads the descriptor with ``os.read`` while the caller waits for
    ``deadline_seconds``.  The thread never reads past ``limit + 1`` bytes and
    records any exception instead of raising it.  A descriptor that cannot be
    used gives ``unreadable``, a terminal gives ``empty`` without a read, a
    thread still running at the deadline gives ``timed_out`` and its buffer is
    never used, and more than ``limit`` bytes give ``too_large``.
    """
    try:
        fd = opener()
        if fd is None:
            return ReadResult(None, "unreadable")
        if stat.S_ISDIR(os.fstat(fd).st_mode):
            return ReadResult(None, "unreadable")
        if os.isatty(fd):
            return ReadResult(None, "empty")
    except Exception:  # noqa: BLE001 - any failure to open or inspect is unreadable
        return ReadResult(None, "unreadable")

    buffer = bytearray()
    failure: list[BaseException] = []

    def pump() -> None:
        try:
            while len(buffer) <= limit:
                chunk = os.read(fd, min(_CHUNK, limit + 1 - len(buffer)))
                if not chunk:
                    return
                buffer.extend(chunk)
        except BaseException as exc:  # noqa: BLE001 - nothing may reach excepthook
            failure.append(exc)

    thread = threading.Thread(target=pump, daemon=True)
    try:
        thread.start()
        thread.join(deadline_seconds)
    except Exception:  # noqa: BLE001
        return ReadResult(None, "unreadable")
    if thread.is_alive():
        return ReadResult(None, "timed_out")
    if failure:
        return ReadResult(None, "unreadable")
    if len(buffer) > limit:
        return ReadResult(None, "too_large")
    return ReadResult(bytes(buffer), None)


def _no_repeats(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    """Build an object, refusing a member name that occurs twice."""
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("repeated member name")
        result[key] = value
    return result


def _refuse_constant(_name: str) -> Any:
    raise ValueError("non-finite number")


def _parse(data: bytes) -> dict[str, Any]:
    """Return the top-level JSON object, or raise ``_Refusal`` with a reason."""
    if not data.strip(_STRIP):
        raise _Refusal("empty")
    try:
        text = data.decode("utf-8")
        value = json.loads(text, object_pairs_hook=_no_repeats, parse_constant=_refuse_constant)
    except (ValueError, RecursionError):
        raise _Refusal("not_json") from None
    if not isinstance(value, dict):
        raise _Refusal("not_json")
    return value


def _is_bool(value: object) -> bool:
    return isinstance(value, bool)


def _typed_finding(finding: object) -> dict[str, Any]:
    if not isinstance(finding, dict):
        raise _Refusal("wrong_schema")
    code = finding.get("code")
    action = finding.get("next_action")
    if not isinstance(code, str) or _CODE_RE.fullmatch(code) is None:
        raise _Refusal("wrong_schema")
    if not _is_bool(finding.get("dispatchable")):
        raise _Refusal("wrong_schema")
    if not isinstance(action, str) or len(action) > _NEXT_ACTION_MAX:
        raise _Refusal("wrong_schema")
    if any("\ud800" <= char <= "\udfff" for char in action):
        raise _Refusal("wrong_schema")
    return finding


def _typed_list(canonical: dict[str, Any], name: str, kind: str) -> list[dict[str, Any]]:
    items = canonical.get(name)
    if not isinstance(items, list):
        raise _Refusal("wrong_schema")
    for entry in items:
        if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
            raise _Refusal("wrong_schema")
        if not _is_bool(entry.get("dispatchable")):
            raise _Refusal("wrong_schema")
        findings = entry.get("findings")
        if not isinstance(findings, list):
            raise _Refusal("wrong_schema")
        for finding in findings:
            _typed_finding(finding)
        dispatchable = entry["dispatchable"]
        if kind == "ready" and not (dispatchable is True and not findings):
            raise _Refusal("wrong_schema")
        if kind == "active" and findings:
            raise _Refusal("wrong_schema")
        if kind == "blocked" and not (dispatchable is False and findings):
            raise _Refusal("wrong_schema")
    return items


def _walk(top: dict[str, Any]) -> Checked:
    """Apply the typed checks and return the checked lists."""
    version = top.get("schema_version")
    if type(version) is not int or version != 1:
        raise _Refusal("wrong_schema")
    if top.get("mode") != "status" or top.get("workspace_root") != ".":
        raise _Refusal("wrong_schema")
    if top.get("workspace_present") is not True:
        raise _Refusal("wrong_schema")
    canonical = top.get("canonical")
    if not isinstance(canonical, dict) or canonical.get("performed") is not True:
        raise _Refusal("wrong_schema")
    top_findings = canonical.get("findings")
    if not isinstance(top_findings, list):
        raise _Refusal("wrong_schema")
    for finding in top_findings:
        _typed_finding(finding)
    ready = _typed_list(canonical, "ready", "ready")
    active = _typed_list(canonical, "active", "active")
    blocked = _typed_list(canonical, "blocked", "blocked")
    ready_paths = {entry["path"] for entry in ready}
    active_paths = {entry["path"] for entry in active}
    blocked_paths = {entry["path"] for entry in blocked}
    if ready_paths & active_paths or ready_paths & blocked_paths or active_paths & blocked_paths:
        raise _Refusal("wrong_schema")
    return Checked(active, ready, blocked, top_findings)


def _all_findings(checked: Checked) -> list[dict[str, Any]]:
    findings = list(checked.findings)
    for entries in (checked.active, checked.ready, checked.blocked):
        for entry in entries:
            findings.extend(entry["findings"])
    return findings


def check(data: bytes) -> Checked | str:
    """Check status bytes and return the checked lists, or the reason for refusing.

    Checks run in a fixed order: empty, strict UTF-8 and JSON, a top-level
    object, ``workspace_present`` false, the typed walk, then the workspace
    failure codes.  An unexpected exception gives ``wrong_schema``.
    """
    try:
        top = _parse(data)
        if top.get("workspace_present") is False:
            return "no_workspace"
        checked = _walk(top)
        if any(f["code"] in _WORKSPACE_FAILURE_CODES for f in _all_findings(checked)):
            return "bad_workspace"
        return checked
    except _Refusal as refusal:
        return str(refusal)
    except Exception:  # noqa: BLE001 - nothing the input causes may escape
        return "wrong_schema"


def start(checked: Checked, path_to_id: Mapping[str, str]) -> dict[str, Any]:
    """Return the mark an argless ``work-loop`` would act on, from the checked lists.

    ``rule`` is ``resume`` for exactly one active entry, ``ask`` for more,
    ``start`` when a ready entry exists and ``none`` otherwise.  For ``resume``
    and ``start``, ``held`` is true when any finding names the chosen entry's
    path, and ``id`` is its node id only when it is loaded and not held.
    """
    active_count = len(checked.active)
    chosen: dict[str, Any] | None = None
    if active_count == 1:
        rule, chosen = "resume", checked.active[0]
    elif active_count > 1:
        rule = "ask"
    elif checked.ready:
        rule, chosen = "start", checked.ready[0]
    else:
        rule = "none"
    node_id: str | None = None
    held = False
    if chosen is not None:
        path = chosen["path"]
        held = any(f.get("path") == path for f in _all_findings(checked))
        if not held:
            node_id = path_to_id.get(path)
    return {"rule": rule, "id": node_id, "held": held, "active_count": active_count}


def project(checked: Checked, path_to_id: Mapping[str, str]) -> dict[str, Any]:
    """Return the readiness member for checked lists, keeping only loaded records.

    An entry appears only when its ``path`` is exactly a key of ``path_to_id``.
    A blocked path that occurs more than once appears once, with its findings in
    input order and a repeated code removed.  One pass with a set lookup per
    finding keeps the cost linear in the input, however many codes one record holds.
    """
    blocked: dict[str, list[dict[str, Any]]] = {}
    codes_seen: dict[str, set[str]] = {}
    for entry in checked.blocked:
        node_id = path_to_id.get(entry["path"])
        if node_id is None:
            continue
        found = blocked.setdefault(node_id, [])
        codes = codes_seen.setdefault(node_id, set())
        for finding in entry["findings"]:
            if finding["code"] in codes:
                continue
            codes.add(finding["code"])
            found.append({
                "code": finding["code"],
                "next_action": finding["next_action"],
                "known": _KNOWN_FINDINGS.get(finding["code"]) == finding["next_action"],
            })
    return {
        "checked": True,
        "active": [path_to_id[e["path"]] for e in checked.active if e["path"] in path_to_id],
        "ready": [path_to_id[e["path"]] for e in checked.ready if e["path"] in path_to_id],
        "blocked": [{"id": node_id, "findings": found} for node_id, found in blocked.items()],
        "start": start(checked, path_to_id),
    }


def member(data: bytes, path_to_id: Mapping[str, str]) -> dict[str, Any]:
    """Return the payload's readiness member for status bytes.

    Runs ``check`` then ``project``; a refusal, or an unexpected exception from
    the projection, gives the unchecked member with its reason.
    """
    checked = check(data)
    if isinstance(checked, str):
        return unchecked(checked)
    try:
        return project(checked, path_to_id)
    except Exception:  # noqa: BLE001 - nothing the input causes may escape
        return unchecked("wrong_schema")
