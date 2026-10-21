"""_supervisor_review — reviewer selection data, the selection record, and the policy resolver.

``review-rules.json`` lists every reviewer role with its roster text and its
obligation. The trusted controller answers a selection request with the
conditional roles it selects and the ones it omits, each omission with a reason;
the supervisor commits that answer as one ``delivery/review-selections.jsonl``
line per delivery subject and changed-path digest. The resolver turns the rules
and that record into one Slice 2 review-policy.

A role is mandatory when selected unless ``SKILL.md`` allows a named skip
(``mandatory_when`` is ``always``, ``selected``, or ``never``). Every refusal
names its code and none of them resolves a role as optional: a missing file, a
value outside a closed set, a selection line that does not parse, or a repeated
key without an owner ``reselect-review`` decision leaves the review stage
unsatisfied.

Standard library only. Python 3.11+.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import stat
import sys
from dataclasses import dataclass, field
from pathlib import Path
from types import ModuleType
from typing import Any

_SCRIPTS_DIR = Path(__file__).resolve().parent


def _supervisor(filename: str) -> ModuleType:
    """Load a supervisor module once per process, shared by every supervisor module.

    Registered under a name unique to this scripts directory, so two installed
    copies of the skill never share an instance.
    """
    tag = hashlib.sha256(str(_SCRIPTS_DIR).encode("utf-8")).hexdigest()[:12]
    alias = f"_work_supervisor_{tag}_" + filename.removesuffix(".py").strip("_").replace("-", "_")
    module = sys.modules.get(alias)
    if module is not None:
        return module
    path = _SCRIPTS_DIR / filename
    if not stat.S_ISREG(os.lstat(path).st_mode):
        raise ImportError(f"{path.name} is not a regular file")
    spec = importlib.util.spec_from_file_location(alias, str(path))
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path.name}")
    module = importlib.util.module_from_spec(spec)
    previous = sys.dont_write_bytecode
    sys.modules[alias] = module
    try:
        sys.dont_write_bytecode = True
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(alias, None)
        raise
    finally:
        sys.dont_write_bytecode = previous
    return module


_admission = _supervisor("_supervisor_admission.py")
Refusal = _admission.Refusal

__all__ = [
    "RULES_PATH",
    "SELECTIONS_FILE",
    "DECISIONS_FILE",
    "Selection",
    "admit_decision",
    "admit_selection",
    "candidates",
    "current_policy",
    "load_rules",
    "resolve_policy",
    "selection_key",
    "selection_status",
]

RULES_PATH = _SCRIPTS_DIR.parent / "review-rules.json"
SELECTIONS_FILE = "review-selections.jsonl"
DECISIONS_FILE = "review-decisions.jsonl"
_MAX_BYTES = 4 * 1024 * 1024
_ROLE_RE = re.compile(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*")
_KEY_RE = re.compile(r"[0-9a-f]{64}")
MODES = ("light", "full")
ROLE_KINDS = ("always", "conditional")
MANDATORY_WHEN = ("always", "selected", "never")
DECISIONS = ("reselect-review", "accept-risk")
_ROLE_FIELDS = frozenset({
    "role", "kind", "condition", "mode_limit", "boundary", "fallback", "mandatory_when"
})
_SELECTION_FIELDS = frozenset({
    "run_id", "sequence", "selection_key", "selected", "omitted", "authority_ref", "authorized_by"
})
_DECISION_FIELDS = frozenset({
    "run_id", "request_id", "decision", "authority_ref", "selection_key", "finding_ids"
})


def _reject_constant(name: str) -> None:
    raise ValueError(f"non-finite JSON constant {name}")


def _text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


# ── the rules ───────────────────────────────────────────────────────────────


def _invalid_rules(detail: str) -> Refusal:
    return Refusal("review-rules-invalid", "skill maintainer", detail)


def load_rules(path: Path | None = None) -> dict[str, Any]:
    """Read and validate the review rules; every defect refuses ``review-rules-invalid``."""
    target = path or RULES_PATH
    try:
        info = os.lstat(target)
        if not stat.S_ISREG(info.st_mode) or info.st_size > _MAX_BYTES:
            raise _invalid_rules("review-rules.json is not a bounded regular file")
        data = json.loads(target.read_bytes().decode("utf-8"), parse_constant=_reject_constant)
    except (OSError, ValueError, RecursionError) as exc:
        raise _invalid_rules(f"review-rules.json is unreadable: {type(exc).__name__}") from exc
    return validate_rules(data)


def validate_rules(data: object) -> dict[str, Any]:
    """Check the closed shape and value sets of a parsed rules document."""
    if not isinstance(data, dict):
        raise _invalid_rules("review-rules.json is not an object")
    if not _text(data.get("rules_version")):
        raise _invalid_rules("rules_version is missing")
    cap = data.get("max_review_retries")
    if isinstance(cap, bool) or not isinstance(cap, int) or cap < 0:
        raise _invalid_rules("max_review_retries is not a non-negative integer")
    if not isinstance(data.get("high_risk_definition"), str):
        raise _invalid_rules("high_risk_definition is missing")
    roles = data.get("roles")
    if not isinstance(roles, list) or not roles:
        raise _invalid_rules("roles is not a non-empty list")
    seen: set[str] = set()
    for entry in roles:
        if not isinstance(entry, dict) or set(entry) != _ROLE_FIELDS:
            raise _invalid_rules("a role entry does not hold exactly the role fields")
        name = entry["role"]
        if not isinstance(name, str) or not _ROLE_RE.fullmatch(name) or name in seen:
            raise _invalid_rules(f"role name {name!r} is malformed or repeated")
        seen.add(name)
        if entry["kind"] not in ROLE_KINDS:
            raise _invalid_rules(f"{name}: kind {entry['kind']!r} is outside {ROLE_KINDS}")
        if entry["mandatory_when"] not in MANDATORY_WHEN:
            raise _invalid_rules(
                f"{name}: mandatory_when {entry['mandatory_when']!r} is outside {MANDATORY_WHEN}"
            )
        if (entry["kind"] == "always") != (entry["mandatory_when"] == "always"):
            raise _invalid_rules(f"{name}: kind always and mandatory_when always go together")
        limit = entry["mode_limit"]
        if (
            not isinstance(limit, list)
            or not limit
            or len(set(limit)) != len(limit)
            or any(mode not in MODES for mode in limit)
        ):
            raise _invalid_rules(f"{name}: mode_limit is not a non-empty subset of {MODES}")
        for text_field in ("condition", "boundary", "fallback"):
            if not isinstance(entry[text_field], str):
                raise _invalid_rules(f"{name}: {text_field} is not a string")
    if not any(entry["kind"] == "always" for entry in roles):
        raise _invalid_rules("no role is always selected")
    return data


def _in_full_mode(entry: dict[str, Any]) -> bool:
    return "full" in entry["mode_limit"]


def candidates(rules: dict[str, Any]) -> list[str]:
    """The conditional roles the controller selects or omits in full mode, in rules order."""
    return [
        e["role"] for e in rules["roles"] if e["kind"] == "conditional" and _in_full_mode(e)
    ]


# ── the selection record ────────────────────────────────────────────────────


def selection_key(subject_fp: str, changed_paths: list[str]) -> str:
    """The delivery subject plus a digest of the sorted changed paths, as one sha256."""
    paths = hashlib.sha256("\0".join(sorted(changed_paths)).encode("utf-8")).hexdigest()
    return hashlib.sha256(f"{subject_fp}\0{paths}".encode()).hexdigest()


def _invalid_selection(detail: str) -> Refusal:
    return Refusal("review-selection-invalid", "controller", detail)


def check_selection(
    rules: dict[str, Any], selection: object
) -> tuple[list[str], list[dict[str, str]]]:
    """Validate a selection against the rules; return its ``(selected, omitted)`` in rules order.

    Every candidate role is either selected or omitted with a reason. A role the
    rules do not list, an always-selected role, a role the full mode does not
    allow, and a role named twice are all refused.
    """
    if not isinstance(selection, dict):
        raise _invalid_selection("the selection is not an object")
    selected, omitted = selection.get("selected"), selection.get("omitted")
    if not isinstance(selected, list) or not isinstance(omitted, list):
        raise _invalid_selection("selected and omitted must be lists")
    known = {e["role"] for e in rules["roles"]}
    allowed = set(candidates(rules))
    chosen: set[str] = set()
    for role in selected:
        if not isinstance(role, str) or role not in known:
            raise _invalid_selection(f"{role!r} is not a role in review-rules.json")
        if role not in allowed:
            raise _invalid_selection(f"{role} is not a conditional role the full mode selects")
        if role in chosen:
            raise _invalid_selection(f"{role} is selected twice")
        chosen.add(role)
    reasons: dict[str, str] = {}
    for item in omitted:
        if not isinstance(item, dict) or set(item) != {"role", "reason"}:
            raise _invalid_selection("an omission holds exactly a role and a reason")
        role = item["role"]
        if not isinstance(role, str) or role not in known:
            raise _invalid_selection(f"{role!r} is not a role in review-rules.json")
        if role not in allowed:
            raise _invalid_selection(f"{role} is not a conditional role the full mode selects")
        if not _text(item["reason"]):
            raise _invalid_selection(f"the omission of {role} carries no reason")
        if role in chosen or role in reasons:
            raise _invalid_selection(f"{role} is named twice")
        reasons[role] = item["reason"]
    missing = sorted(allowed - chosen - set(reasons))
    if missing:
        raise _invalid_selection("omitted without a reason: " + ", ".join(missing))
    order = candidates(rules)
    return (
        [r for r in order if r in chosen],
        [{"role": r, "reason": reasons[r]} for r in order if r in reasons],
    )


def resolve_policy(rules: dict[str, Any], record: dict[str, Any]) -> dict[str, Any]:
    """The Slice 2 review-policy for the rules and one selection record.

    Every always role comes from the rules, then each selected role; a role is
    ``mandatory`` when ``mandatory_when`` is ``always`` or ``selected`` and
    ``optional`` only when the rules allow a named skip (``never``).
    """
    selected, _omitted = check_selection(rules, record)
    chosen = set(selected)
    roles = [
        {
            "role": e["role"],
            "kind": "optional" if e["mandatory_when"] == "never" else "mandatory",
        }
        for e in rules["roles"]
        if _in_full_mode(e) and (e["kind"] == "always" or e["role"] in chosen)
    ]
    ordered = [[r["role"], r["kind"]] for r in roles]
    identity = json.dumps(
        {"rules_version": rules["rules_version"], "roles": ordered},
        sort_keys=True,
        separators=(",", ":"),
    )
    return {
        "policy_id": "work-supervisor-review-rules",
        "policy_version": rules["rules_version"],
        "review_policy_fingerprint": "review-policy-sha256:"
        + hashlib.sha256(identity.encode("utf-8")).hexdigest(),
        "selector": "work-supervisor-review-rules",
        "roles": roles,
        "waivers": [],
    }


def _lines(
    raw: bytes, name: str, fields: frozenset[str], required: frozenset[str], code: str
) -> list[dict[str, Any]]:
    """Parse a committed ``delivery/`` jsonl file into closed-shape records."""
    if raw and not raw.endswith(b"\n"):
        raise Refusal(code, "controller", f"{name} ends in a truncated line")
    records = []
    for number, text in enumerate(raw.splitlines(), 1):
        if not text.strip():
            continue
        try:
            line = json.loads(text)
        except ValueError:
            line = None
        if not isinstance(line, dict) or not required <= set(line) <= fields:
            raise Refusal(code, "controller", f"{name} line {number} is malformed")
        records.append(line)
    return records


def parse_selections(raw: bytes) -> list[dict[str, Any]]:
    """The records in ``delivery/review-selections.jsonl``; a bad line refuses."""
    records = _lines(
        raw,
        SELECTIONS_FILE,
        _SELECTION_FIELDS,
        frozenset({"selection_key", "selected", "omitted", "authority_ref"}),
        "review-selection-invalid",
    )
    for number, line in enumerate(records, 1):
        if (
            not isinstance(line["selection_key"], str)
            or not _KEY_RE.fullmatch(line["selection_key"])
            or not isinstance(line["selected"], list)
            or not isinstance(line["omitted"], list)
            or not _text(line["authority_ref"])
        ):
            raise _invalid_selection(f"{SELECTIONS_FILE} line {number} is malformed")
    return records


def parse_decisions(raw: bytes) -> list[dict[str, Any]]:
    """The records in ``delivery/review-decisions.jsonl``; a bad line refuses."""
    records = _lines(
        raw,
        DECISIONS_FILE,
        _DECISION_FIELDS,
        frozenset({"request_id", "decision", "authority_ref"}),
        "review-decision-invalid",
    )
    for number, line in enumerate(records, 1):
        if line["decision"] not in DECISIONS or not _text(line["authority_ref"]):
            raise Refusal(
                "review-decision-invalid",
                "controller",
                f"{DECISIONS_FILE} line {number} is malformed",
            )
    return records


@dataclass
class Selection:
    """Where one selection key stands: its records, authorized repeats, and what is needed."""

    key: str
    records: list[dict[str, Any]] = field(default_factory=list)
    authorizing: list[str] = field(default_factory=list)

    @property
    def authorized(self) -> int:
        """How many owner ``reselect-review`` decisions name the key."""
        return len(self.authorizing)

    @property
    def required(self) -> bool:
        """True while the key has no record, or an owner reselection awaits its record."""
        return len(self.records) < 1 + self.authorized

    @property
    def sequence(self) -> int:
        """The ``n`` of the next selection request for the key."""
        return len(self.records) + 1

    @property
    def latest(self) -> dict[str, Any]:
        return self.records[-1]


def _delivery_bytes(ws: Any, name: str) -> bytes:
    return ws.git.show(f"{ws.git.delivery_rel}/{name}") or b""


def selection_status(ws: Any, rules: dict[str, Any], key: str) -> Selection:
    """Read the committed selection and decision records for *key*.

    Refuses ``review-selection-invalid`` on a bad line or a record that does not
    resolve against the rules, and ``review-selection-exists`` when the key
    repeats without an owner ``reselect-review`` decision for each repeat.
    """
    records = parse_selections(_delivery_bytes(ws, SELECTIONS_FILE))
    owner = ws.policy["authority_roles"]["reselect_review"]
    decisions = parse_decisions(_delivery_bytes(ws, DECISIONS_FILE))
    seen: dict[str, int] = {}
    for record in records:
        count = seen.get(record["selection_key"], 0) + 1
        seen[record["selection_key"]] = count
        if count > 1 + len(_authorizing(decisions, record["selection_key"], owner)):
            raise Refusal(
                "review-selection-exists",
                "owner",
                f"review-selections.jsonl repeats key {record['selection_key'][:12]} "
                "without an owner reselect-review decision",
            )
    mine = [r for r in records if r["selection_key"] == key]
    for record in mine:
        check_selection(rules, record)
    return Selection(key, mine, _authorizing(decisions, key, owner))


def _authorizing(decisions: list[dict[str, Any]], key: str, owner: str) -> list[str]:
    """Request ids of the owner ``reselect-review`` decisions that name *key*."""
    return [
        d["request_id"]
        for d in decisions
        if d["decision"] == "reselect-review"
        and d.get("selection_key") == key
        and _admission.check_authority_ref(d["authority_ref"], owner)
    ]


def current_policy(ws: Any, state: Any, key: str | None = None) -> dict[str, Any]:
    """The review-policy for the run's current selection record.

    Raises ``review-rules-invalid``, ``review-selection-invalid``,
    ``review-selection-exists``, or ``review-selection-missing``; it never
    returns a policy that defaulted a role.
    """
    rules = load_rules()
    if key is None:
        readiness = _supervisor("_supervisor_readiness.py")
        key = readiness.current_selection_key(ws, state)
    status = selection_status(ws, rules, key)
    if status.required:
        raise Refusal(
            "review-selection-missing",
            "controller",
            "no review selection record exists for the current subject and changed paths",
        )
    return resolve_policy(rules, status.latest)


def admit_selection(
    rules: dict[str, Any], status: Selection, selection: object
) -> dict[str, Any]:
    """The ``review-selections.jsonl`` record for a controller's selection, or a refusal.

    Refuses an unknown role, an omission without a reason, and a second record
    for a key unless an owner ``reselect-review`` decision for that key exists.
    """
    if not status.required:
        raise Refusal(
            "review-selection-exists",
            "owner",
            "this subject and changed-path digest already has a selection record; "
            "only an owner reselect-review decision allows another",
        )
    selected, omitted = check_selection(rules, selection)
    assert isinstance(selection, dict)
    authority = selection.get("authority_ref")
    if not isinstance(authority, str) or not _admission._AUTHORITY_RE.fullmatch(authority):
        raise _invalid_selection("authority_ref is not an authority reference")
    record: dict[str, Any] = {
        "selection_key": status.key,
        "sequence": status.sequence,
        "selected": selected,
        "omitted": omitted,
        "authority_ref": authority,
    }
    # The first record for a key stands alone; each later one cites the owner
    # decision that allowed it.
    if status.records:
        record["authorized_by"] = status.authorizing[len(status.records) - 1]
    if selection.get("authorized_by", record.get("authorized_by")) != record.get("authorized_by"):
        raise _invalid_selection("authorized_by does not name the authorizing decision")
    return record


def admit_decision(
    ws: Any, state: Any, request: dict[str, Any], result: dict[str, Any]
) -> dict[str, Any]:
    """The ``review-decisions.jsonl`` record for a ``human-decision`` result, or a refusal.

    Only the ``review-not-eligible`` request takes a decision. ``reselect-review``
    needs an owner authority reference naming the request's selection key; every
    other decision, role, or reason refuses ``authority-refused``.
    """
    if request.get("reason") != "review-not-eligible":
        raise Refusal(
            "authority-refused", "controller", "only a review-not-eligible request takes one"
        )
    decision = result.get("decision")
    if not isinstance(decision, dict):
        raise Refusal("invalid-result", "controller", "a human-decision result needs decision")
    kind, ref = decision.get("decision"), decision.get("authority_ref")
    roles = ws.policy["authority_roles"]
    if kind != "reselect-review":
        raise Refusal("authority-refused", "controller", f"decision {kind!r} is not admitted here")
    if not _admission.check_authority_ref(ref, roles["reselect_review"]):
        raise Refusal(
            "authority-refused",
            "owner",
            f"reselect-review needs a {roles['reselect_review']} authority reference",
        )
    if decision.get("selection_key") != request.get("selection_key"):
        raise Refusal(
            "invalid-result", "controller", "the decision names another selection key"
        )
    return {
        "run_id": state.run_id,
        "request_id": request["request_id"],
        "decision": kind,
        "authority_ref": ref,
        "selection_key": decision["selection_key"],
    }
