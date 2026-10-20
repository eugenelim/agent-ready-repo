"""_supervisor_admission — the run's workspace, approval pair, and ``start``.

``start`` imports the current approved spec policy through the shared policy
import port and commits exactly one ``delivery/approvals.jsonl`` line holding
one ``approval-record.v1`` and one ``initial-plan-review.v1``, bound to the
reviewed-envelope fingerprint, terminal intent, code-trust classification, run
id, and both authority references. A later ``start`` after an amendment appends
a new pair under the same run id.

It never opens a legacy ``engine-state.json`` or cohort ``state.json``.

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
import tempfile
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
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


_commit = _supervisor("_supervisor_commit.py")
_journal = _supervisor("_supervisor_journal.py")
_projector = _supervisor("_supervisor_projector.py")
sibling = _commit.sibling

__all__ = ["Refusal", "Workspace", "check_authority_ref", "start"]

_POLICY_PATH = _SCRIPTS_DIR.parent / "supervisor-policy.json"
_MAX_TEXT_BYTES = 4 * 1024 * 1024
_AUTHORITY_RE = re.compile(r"(?P<role>[a-z][a-z-]{0,62})(?::[0-9a-f]{12,64})?")
_SPEC_STATUSES = ("Approved", "Implementing")
_PLAN_STATUSES = ("Approved", "Executing")
SCHEMA_VERSION = 1
_LOCK_MARGIN_SECONDS = 300.0
_APPROVAL_FIELDS = frozenset({
    "run_id",
    "sequence",
    "base",
    "code_trust",
    "terminal_intent",
    "authority_ref",
    "review_authority_ref",
    "envelope",
    "approval",
    "initial_plan_review",
})
_RECORD_FIELDS = {
    "effect-resolutions.jsonl": frozenset({"entry", "operation_key", "run_id", "effect", "scope"}),
}
INTENTS = ("code", "spec-plan")
CODE_TRUST = ("trusted", "untrusted")


class Refusal(Exception):
    """A refused operation: a stable code and the owner who can resolve it."""

    def __init__(self, code: str, owner: str, detail: str = "") -> None:
        super().__init__(detail or code)
        self.code = code
        self.owner = owner
        self.detail = detail or code

    def as_dict(self) -> dict[str, str]:
        return {"code": self.code, "owner": self.owner, "detail": self.detail}


def utc_now() -> str:
    """The current UTC instant, RFC 3339, second precision."""
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


# The clock every workspace reads unless one is passed; tests pin it here.
CLOCK: list[Callable[[], str]] = [utc_now]


def check_authority_ref(value: object, role: str) -> bool:
    """True when *value* is an authority reference for exactly *role*."""
    if not isinstance(value, str):
        return False
    m = _AUTHORITY_RE.fullmatch(value)
    return bool(m) and m.group("role") == role


def load_policy() -> dict[str, Any]:
    """Read the skill's supervisor policy data."""
    data = json.loads(_POLICY_PATH.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("schema_version") != SCHEMA_VERSION:
        raise Refusal("invalid-policy", "skill maintainer", "supervisor-policy.json is malformed")
    # The run lock's own rule: a contender's wait < the longest hold < the stale
    # window. Red proof is the longest hold, so its budget plus a margin for the
    # git work around it must end before the lock can be judged stale.
    wait = float(data["run_lock_timeout_seconds"])
    hold = float(data["red_proof_budget_seconds"]) + _LOCK_MARGIN_SECONDS
    if not wait < hold < float(data["run_lock_stale_seconds"]):
        raise Refusal(
            "invalid-policy",
            "skill maintainer",
            "run_lock_timeout_seconds < red_proof_budget_seconds + "
            f"{_LOCK_MARGIN_SECONDS:g} < run_lock_stale_seconds must hold",
        )
    return data


def canonical_line(record: dict[str, Any]) -> bytes:
    return (json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


@dataclass
class Workspace:
    """One spec directory inside one repository, with its ports."""

    root: Path
    spec_rel: str
    clock: Callable[[], str] | None = None
    policy: dict[str, Any] = field(default_factory=lambda: load_policy())

    def __post_init__(self) -> None:
        if self.clock is None:
            self.clock = CLOCK[0]
        self.git = _commit.GitPort(self.root, self.spec_rel, clock=self.clock)
        self.local = _journal.LocalState(self.root, self.spec_rel, clock=self.clock)
        self.spec_path = self.root / self.spec_rel / "spec.md"
        self.plan_path = self.root / self.spec_rel / "plan.md"

    # ── confined reads ──────────────────────────────────────────────────────

    def read_text(self, rel: str) -> str:
        """Read a repository file through the confined, bounded reader."""
        fs = sibling("_file_safety.py")
        try:
            data = fs.read_confined_regular_file(
                self.root, self.root / rel, max_bytes=_MAX_TEXT_BYTES
            )
        except FileNotFoundError as exc:
            raise OSError(f"{rel} is missing") from exc
        except fs.UnsafeContentError as exc:
            raise OSError(f"{rel}: {exc}") from exc
        return bytes(data).decode("utf-8")

    def list_dir(self, rel: str) -> list[str]:
        directory = self.root / rel
        if not directory.is_dir() or directory.is_symlink():
            return []
        return sorted(entry.name for entry in directory.iterdir())

    def spec_text(self) -> str:
        return self.read_text(f"{self.spec_rel}/spec.md")

    def plan_text(self) -> str:
        return self.read_text(f"{self.spec_rel}/plan.md")

    def envelope(self, spec_text: str) -> tuple[dict[str, str], tuple[str, ...]]:
        """The working spec's six references and the cited record paths."""
        try:
            projection = _projector.envelope_references(
                spec_text, read_record=self.read_text, list_dir=self.list_dir
            )
        except _projector.ProjectionRefused as exc:
            raise Refusal(exc.code, exc.owner, exc.detail) from exc
        return projection.refs, projection.cited_paths

    # ── committed records ───────────────────────────────────────────────────

    def _lines(self, name: str, rev: str, required: frozenset[str]) -> list[dict[str, Any]]:
        """Parse a committed ``delivery/`` file, refusing a line this supervisor did not write."""
        raw = self.git.show(f"{self.git.delivery_rel}/{name}", rev) or b""
        lines = []
        for number, text in enumerate(raw.splitlines(), 1):
            if not text.strip():
                continue
            try:
                line = json.loads(text)
            except ValueError:
                line = None
            if not isinstance(line, dict) or not required <= set(line):
                raise Refusal(
                    "malformed-record",
                    "controller",
                    f"{self.git.delivery_rel}/{name} line {number} is malformed",
                )
            lines.append(line)
        return lines

    def approvals(self, rev: str = "HEAD") -> list[dict[str, Any]]:
        lines = self._lines("approvals.jsonl", rev, _APPROVAL_FIELDS)
        for number, line in enumerate(lines, 1):
            envelope = line["envelope"]
            if (
                not isinstance(envelope, dict)
                or not isinstance(envelope.get("refs"), dict)
                or not isinstance(line["approval"], dict)
            ):
                raise Refusal(
                    "malformed-record", "controller", f"approvals.jsonl line {number} is malformed"
                )
        return lines

    def records(self, name: str) -> list[dict[str, Any]]:
        return self._lines(name, "HEAD", _RECORD_FIELDS.get(name, frozenset()))

    def evidence_bytes(self) -> bytes:
        return self.git.show(f"{self.git.delivery_rel}/evidence.jsonl") or b""

    # ── the shared write ports ──────────────────────────────────────────────

    def grant(self, scopes: list[str]) -> tuple[object, object]:
        """An in-process issuer and a writer grant over *scopes*."""
        sc = sibling("_security_capability.py")
        issuer = sc.CapabilityIssuer()
        grant = issuer.issue_root_grant(
            roots=["delivery"],
            operations=["append"],
            trust_class="trusted",
            writes_allowed_roots=scopes,
            control_denies=[],
        )
        return issuer, grant

    def evidence_append(
        self,
        receipts: list[dict[str, Any]] = (),  # type: ignore[assignment]
        writer: Callable[[object, object, object, Callable[[object], None]], None] | None = None,
    ) -> bytes:
        """Frames the evidence store appends after HEAD's ``evidence.jsonl``.

        The store runs on a private copy of the committed log, so the bytes it
        writes become part of a supervisor commit, never a working-tree edit.
        """
        es = sibling("_evidence_store.py")
        head = self.evidence_bytes()
        sink = self.local.security_sink()
        issuer, grant = self.grant(["evidence"])
        with tempfile.TemporaryDirectory(prefix="work-supervisor-evidence-") as scratch:
            log = Path(scratch).resolve() / "evidence.jsonl"
            log.write_bytes(head)
            store = es.EvidenceStore(log)
            store.open(audit_sink=sink)
            for receipt in receipts:
                store.append_receipt(
                    receipt,
                    transaction_id=f"tx:{receipt['receipt_id']}",
                    issuer=issuer,
                    grant=grant,
                    audit_sink=sink,
                )
            if writer is not None:
                writer(store, issuer, grant, sink)
            after = log.read_bytes()
        if not after.startswith(head):
            raise Refusal(
                "evidence-rewritten", "skill maintainer", "the evidence log was rewritten"
            )
        return after[len(head) :]

    def open_evidence(self) -> object:
        """A read-only evidence store over HEAD's committed log."""
        es = sibling("_evidence_store.py")
        head = self.evidence_bytes()
        with tempfile.TemporaryDirectory(prefix="work-supervisor-read-") as scratch:
            log = Path(scratch).resolve() / "evidence.jsonl"
            log.write_bytes(head)
            store = es.EvidenceStore(log)
            store.open()  # replays the whole log into memory; the copy is not needed after
        return store

    def run_lock(self) -> Any:
        """The exclusive run lock under ``.supervisor/``.

        Its stale window exceeds the red-proof budget, the longest work done
        while holding it, so a live holder is never judged dead.
        """
        self.local.ensure()
        return sibling("_statelock.py").exclusive(
            self.local.lock_target,
            timeout=float(self.policy["run_lock_timeout_seconds"]),
            stale_after=float(self.policy["run_lock_stale_seconds"]),
        )


def _status_refusals(ws: Workspace, spec_text: str, plan_text: str, intent: str) -> None:
    spec_status = _projector.spec_status(spec_text)
    if spec_status not in _SPEC_STATUSES:
        raise Refusal("spec-not-approved", "owner", f"spec status is {spec_status or 'missing'}")
    plan_status = _projector.plan_status(plan_text)
    if plan_status not in _PLAN_STATUSES:
        raise Refusal("plan-not-approved", "owner", f"plan status is {plan_status or 'missing'}")
    try:
        declared = _projector.terminal_intent(spec_text)
    except _projector.ProjectionRefused as exc:
        raise Refusal(exc.code, exc.owner, exc.detail) from exc
    if declared is not None and declared != intent:
        raise Refusal(
            "intent-mismatch",
            "owner",
            f"--intent {intent} differs from the spec's Terminal Intent {declared}",
        )


def _identified(
    record: dict[str, Any],
    key: str,
    value: str,
    when: str,
    validate: Callable[[dict[str, Any]], tuple[bool, str]],
) -> dict[str, Any]:
    """Give an imported record a deterministic id and the run's clock, revalidated."""
    out = dict(record, **{key: value, "timestamp": when})
    ok, code = validate(out)
    if not ok:
        raise Refusal("invalid-approval-record", "skill maintainer", code)
    return out


def start(
    ws: Workspace,
    *,
    intent: str,
    code_trust: str,
    authority_ref: str,
    review_authority_ref: str,
) -> dict[str, Any]:
    """Admit the approved pair; under ``spec-plan`` also commit the terminal step."""
    roles = ws.policy["authority_roles"]
    if not check_authority_ref(authority_ref, roles["start_authority_ref"]):
        raise Refusal(
            "invalid-authority-ref",
            "owner",
            f"--authority-ref must be {roles['start_authority_ref']}[:<hex>]",
        )
    if not check_authority_ref(review_authority_ref, roles["start_review_authority_ref"]):
        raise Refusal(
            "invalid-authority-ref",
            "owner",
            f"--review-authority-ref must be {roles['start_review_authority_ref']}[:<hex>]",
        )
    if intent not in INTENTS or code_trust not in CODE_TRUST:
        raise Refusal("invalid-argument", "owner", "unknown intent or code-trust value")
    spec_text, plan_text = ws.spec_text(), ws.plan_text()
    _status_refusals(ws, spec_text, plan_text, intent)
    refs, _cited = ws.envelope(spec_text)
    acceptance = sibling("_acceptance.py")
    envelope = acceptance.derive_envelope(refs)
    approvals = ws.approvals()
    head = ws.git.head()
    if approvals:
        run_id = approvals[0]["run_id"]
        base = approvals[0]["base"]
        latest = approvals[-1]
        commits = ws.git.supervisor_commits(run_id)
        foreign = ws.git.sync(commits[-1].sha if commits else None)
        if foreign:
            raise Refusal("foreign-delivery-edit", "controller", ", ".join(foreign))
        if (
            latest["envelope"]["envelope_fingerprint"] == envelope["envelope_fingerprint"]
            and latest["terminal_intent"] == intent
        ):
            if intent == "spec-plan":
                _supervisor("_supervisor_loop.py").commit_terminal(ws, run_id)
            return {"status": "current", "run_id": run_id, "sequence": latest["sequence"]}
    else:
        run_id = "run-" + hashlib.sha256(f"{ws.spec_rel}\0{head}".encode()).hexdigest()[:16]
        base = head
    sequence = len(approvals) + 1
    pi = sibling("_policy_import.py")
    issuer, grant = ws.grant(["delivery/policy-import"])
    try:
        approval, review = pi.import_policy(
            spec_path=ws.spec_path,
            plan_path=ws.plan_path,
            refs=refs,
            terminal_intent=intent,
            writer_grant=grant,
            issuer=issuer,
            audit_sink=ws.local.security_sink(),
            store=pi.ImportStore(),
            approval_identity=authority_ref,
            approval_role=roles["start_authority_ref"],
            reviewer_identity=review_authority_ref,
            reviewer_role=roles["start_review_authority_ref"],
            approved_spec_digest=pi.compute_spec_digest(ws.spec_path),
            approved_plan_digest=pi.compute_plan_digest(ws.plan_path),
            approved_envelope_fingerprint=envelope["envelope_fingerprint"],
        )
    except pi.PolicyImportRefused as exc:
        raise Refusal(exc.denial_code, "owner", "policy import refused") from exc
    when = ws.clock()
    seed = hashlib.sha256(f"{run_id}:{sequence}".encode()).hexdigest()
    line = {
        "run_id": run_id,
        "sequence": sequence,
        "base": base,
        "code_trust": code_trust,
        "terminal_intent": intent,
        "authority_ref": authority_ref,
        "review_authority_ref": review_authority_ref,
        "envelope": envelope,
        "approval": _identified(
            approval, "approval_id", f"appr-{seed[:24]}", when, pi.validate_approval_dict
        ),
        "initial_plan_review": _identified(
            review, "review_id", f"rev-{seed[24:48]}", when, pi.validate_initial_review_dict
        ),
    }
    ws.git.build_commit(
        run_id=run_id,
        step=f"approval:{sequence}",
        operation="approval",
        appends={"approvals.jsonl": canonical_line(line)},
        summary=f"admit approval pair {sequence}",
    )
    result = {"status": "admitted", "run_id": run_id, "sequence": sequence}
    if intent == "spec-plan":
        loop = _supervisor("_supervisor_loop.py")
        loop.commit_terminal(ws, run_id)
        result["status"] = "terminal"
    return result
