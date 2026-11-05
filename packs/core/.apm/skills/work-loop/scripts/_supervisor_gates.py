"""Approval-gate digest for the work-loop supervisor.

`gate_digest` hashes a spec.md or plan.md the way an approval pins it: the
text is checked for hidden or control characters, approval-entry lines in the
region after the last `## Changelog` line are dropped, and the rest goes through the single
canonicaliser in `_loop_guards.canonical_contract`.

`park` records one local, controller-free-text-free approval gate waiting for a
human answer. It never commits, moves a ref, or writes the index or a working-tree
file; its only write is one record under the Git directory's supervisor store.

Standard library only. Sibling modules are loaded by path, unregistered.
This module writes nothing to stdout or stderr.
"""

from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import os
import re
import stat
import sys
import unicodedata
from pathlib import Path
from types import ModuleType
from typing import Any, Callable

_SCRIPTS_DIR = Path(__file__).resolve().parent
_LINE_SEPARATORS = frozenset({0x2028, 0x2029, 0xFFF9, 0xFFFA, 0xFFFB})

_modules: dict[str, ModuleType] = {}


class GateDigestRefused(Exception):
    """Raised when gate text cannot be digested; `code` names the reason."""

    def __init__(self, code: str, detail: str = "") -> None:
        """Store the refusal *code* and an optional *detail*; the code is the message."""
        super().__init__(code)
        self.code = code
        self.detail = detail


def _load_sibling(alias: str, filename: str) -> ModuleType:
    """Load a sibling script by path under a unique name, cached, unregistered."""
    cached = _modules.get(alias)
    if cached is not None:
        return cached
    path = _SCRIPTS_DIR / filename
    try:
        info = path.lstat()
    except OSError as exc:
        raise ImportError(f"cannot locate {filename}: {exc}") from exc
    if not stat.S_ISREG(info.st_mode):
        raise ImportError(f"{filename} is not a regular file")
    previous = sys.dont_write_bytecode
    real_out, real_err = sys.stdout, sys.stderr
    # A sibling reconfigures the standard streams at import; a caller whose stream
    # lacks `reconfigure` (a captured one) must not make that raise, nor be changed.
    sink_out = io.TextIOWrapper(io.BytesIO(), encoding="utf-8")
    sink_err = io.TextIOWrapper(io.BytesIO(), encoding="utf-8")
    try:
        sys.dont_write_bytecode = True
        sys.stdout, sys.stderr = sink_out, sink_err
        spec = importlib.util.spec_from_file_location(alias, str(path))
        if spec is None or spec.loader is None:
            raise ImportError(f"no import spec for {path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = previous
        sys.stdout, sys.stderr = real_out, real_err
        sink_out.close()
        sink_err.close()
    _modules[alias] = module
    return module


def _unsafe(
    text: str, is_hidden_char: Callable[[str], bool], lint: ModuleType | None = None
) -> int | None:
    """The index of the first offending character of *text*, or None when it is safe.

    An offender is a control, format, hidden or separator character.

    With *lint* (the knowledge lint's module), also true when the zero-width joiners
    and presentation selectors it allows run past its adjacency cap or its budget; a
    budget overrun points at the first such joiner or selector.
    """
    run = invisible = 0
    first_invisible = -1
    for i, ch in enumerate(text):
        if lint is not None and ch in lint._RUN_CHARS:
            run += 1
            invisible += 1
            if first_invisible < 0:
                first_invisible = i
            if run > lint._MAX_ADJACENT_INVISIBLE:
                return i
        else:
            run = 0
        if ch in ("\t", "\n"):
            continue
        if ch == "\r":
            if text[i + 1 : i + 2] == "\n":
                continue
            return i
        if unicodedata.category(ch) in ("Cc", "Cf") or ord(ch) in _LINE_SEPARATORS:
            return i
        if is_hidden_char(ch):
            return i
    if lint is not None and invisible:
        visible = len(text) - invisible
        # The lint's own bound: never more hidden than shown, and a share of the length.
        if invisible > min(lint.invisible_budget(text, cap=_INVISIBLE_CAP), visible):
            return first_invisible
    return None


# The budget's length basis is capped at 2,000 characters. At the lint's one
# invisible character per 50 characters of basis that buys at most 40 invisible
# characters (rounded up for a short text); padding the artifact cannot buy more.
_INVISIBLE_CAP = 2000


_APPROVAL_ENTRY_RE = re.compile(
    r"^- [0-9]{4}-[0-9]{2}-[0-9]{2}: (spec|plan|amendment) approved by "
    r"[A-Za-z0-9][A-Za-z0-9-]{0,38}"
    r"( \((scope|build strategy|scope and build strategy)\))?\.?$",
    re.ASCII,
)


def _drop_approval_entries(text: str) -> str:
    """Drop approval-entry lines in the region after the last `## Changelog` line of *text*.

    The heading is the last line whose `str.rstrip()` form is exactly `## Changelog`.
    The region runs from the line after it up to, not including, the first later line
    whose `str.lstrip()` form starts with `#`, "```" or "~~~". Only inside the region
    are entry lines dropped, blank-line runs folded and trailing blank lines removed.
    From the region's end on every line is kept byte for byte, set off from the region
    by one blank line when the region is not empty. With no heading the text is unchanged.
    """
    lines = text.split("\n")
    heading = max(
        (i for i, line in enumerate(lines) if line.rstrip() == "## Changelog"), default=None
    )
    if heading is None:
        return text
    end = next(
        (
            i
            for i in range(heading + 1, len(lines))
            if lines[i].lstrip().startswith(("#", "```", "~~~"))
        ),
        len(lines),
    )
    kept = lines[: heading + 1]
    for line in lines[heading + 1 : end]:
        if _APPROVAL_ENTRY_RE.match(line.rstrip()):
            continue
        if line.strip() == "" and kept[-1].strip() == "":
            continue
        kept.append(line)
    while len(kept) > heading + 1 and kept[-1].strip() == "":
        kept.pop()
    if end < len(lines):
        kept.append("")
    return "\n".join(kept + lines[end:])


def gate_digest(text_or_bytes: str | bytes, *, name: str) -> str:
    """Return the lowercase hex SHA-256 pinning *text_or_bytes* as `spec.md` or `plan.md`.

    Raises `GateDigestRefused` with code `gate-unsafe-content`.
    """
    if isinstance(text_or_bytes, bytes):
        try:
            text = text_or_bytes.decode("utf-8")
        except UnicodeDecodeError as exc:
            line = text_or_bytes[: exc.start].count(b"\n") + 1
            raise GateDigestRefused(
                "gate-unsafe-content", f"{name} line {line} is not valid UTF-8"
            ) from exc
    else:
        text = text_or_bytes
    lint = _load_sibling("core_work_loop_gates_lint_knowledge", "lint-knowledge.py")
    offender = _unsafe(text, lint.is_hidden_char, lint)
    if offender is not None:
        # A lone CR is itself an offender, so before the first one only CRLF breaks lines.
        line = text[:offender].replace("\r\n", "\n").count("\n") + 1
        raise GateDigestRefused(
            "gate-unsafe-content",
            f"{name} line {line} holds a hidden or control character",
        )
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    remaining = _drop_approval_entries(text)
    guards = _load_sibling("core_work_loop_gates_loop_guards", "_loop_guards.py")
    canonical = guards.canonical_contract(remaining, ac_section_only=(name != "plan.md"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# ── park ─────────────────────────────────────────────────────────────────────

_GATE_STATUSES = {"spec-approved": ("Draft", None), "plan-approved": ("Approved", "Drafting")}
_SAFE_SEGMENT_RE = re.compile(r"[A-Za-z0-9._][A-Za-z0-9._-]*")
_HEX64_RE = re.compile(r"[0-9a-f]{64}")
_COMMIT_RE = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})")
_RECORD_KEYS = frozenset({
    "schema_version", "spec_dir", "gate", "intent", "code_trust",
    "spec_digest", "plan_digest", "commit",
})
_MAX_RECORD_BYTES = 4096
_MAX_ARTIFACT_BYTES = 4 * 1024 * 1024
_STORE_REL = "agentbundle-supervisor/gates"


def safe_spec_path(spec_dir: object) -> bool:
    """True when *spec_dir* is a safe repository-relative spec path."""
    if not isinstance(spec_dir, str) or not spec_dir or spec_dir.startswith("/"):
        return False
    parts = spec_dir.split("/")
    return all(p not in (".", "..") and _SAFE_SEGMENT_RE.fullmatch(p) for p in parts)


def record_name(spec_rel: str) -> str:
    """The park record's file name for *spec_rel*."""
    return hashlib.sha256(spec_rel.encode("utf-8")).hexdigest()[:16] + ".json"


def canonical_record(body: dict[str, Any]) -> bytes:
    """The record bytes: canonical JSON with sorted keys and one trailing newline."""
    return (json.dumps(body, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def _plain_dirs(root: Path, spec_dir: str) -> bool:
    """True when every part of *spec_dir* under *root* is an existing plain directory."""
    current = root
    for part in spec_dir.split("/"):
        current = current / part
        try:
            info = os.lstat(current)
        except OSError:
            return False
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
            return False
    return True


def valid_record(root: Path, data: bytes) -> dict[str, Any] | None:
    """The park record in *data* when it is valid, else ``None``."""
    if len(data) > _MAX_RECORD_BYTES:
        return None
    try:
        rec = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        return None
    if not isinstance(rec, dict) or set(rec) != _RECORD_KEYS:
        return None
    version = rec["schema_version"]
    if isinstance(version, bool) or version != 1:
        return None
    ok = (
        safe_spec_path(rec["spec_dir"])
        and rec["gate"] in _GATE_STATUSES
        and rec["intent"] in ("code", "spec-plan")
        and rec["code_trust"] in ("trusted", "untrusted")
        and all(isinstance(rec[k], str) and _HEX64_RE.fullmatch(rec[k])
                for k in ("spec_digest", "plan_digest"))
        and isinstance(rec["commit"], str)
        and _COMMIT_RE.fullmatch(rec["commit"]) is not None
    )
    if not ok or not _plain_dirs(root, rec["spec_dir"]):
        return None
    return rec


def _read_artifact(ws: Any, fs: Any, name: str) -> bytes | None:
    """The working-tree bytes of the spec's *name*, or ``None`` when unreadable."""
    path = ws.root / ws.spec_rel / name
    try:
        return bytes(fs.read_confined_regular_file(ws.root, path, max_bytes=_MAX_ARTIFACT_BYTES))
    except (OSError, fs.UnsafeContentError):
        return None


def _is_clean(ws: Any, rel: str, data: bytes) -> bool:
    """Whether *rel* is committed and the working bytes match, without writing the index."""
    out = ws.git.run("ls-files", "-s", "--", rel, literal_pathspecs=True)
    lines = [line for line in out.decode("utf-8", "replace").split("\n") if line]
    if len(lines) != 1:
        return False
    meta = lines[0].partition("\t")[0].split()
    if len(meta) != 3 or meta[2] != "0":
        return False
    blob = meta[1]
    head = ws.git.run("rev-parse", "--verify", "--quiet", f"HEAD:{rel}", check=False)
    if head.decode("utf-8", "replace").strip() != blob:
        return False
    for candidate in (data, data.replace(b"\r\n", b"\n")):
        hashed = ws.git.run("hash-object", "--no-filters", "--stdin", stdin=candidate)
        if hashed.decode("utf-8", "replace").strip() == blob:
            return True
    return False


def _recorded_commit_holds(ws: Any, admission: Any, rec: dict[str, Any]) -> bool:
    """Whether the recorded commit is readable and holds the recorded gate digests."""
    try:
        for name, key in (("spec.md", "spec_digest"), ("plan.md", "plan_digest")):
            blob = ws.git.show(f"{ws.spec_rel}/{name}", rec["commit"])
            if blob is None or gate_digest(blob, name=name) != rec[key]:
                return False
    except (GateDigestRefused, admission._git.SupervisorGitError):
        return False
    return True


def _already_admitted(
    ws: Any, admission: Any, spec_text: str, intent: str, code_trust: str
) -> bool:
    """Whether `start` with *intent* and *code_trust* would answer `current` for the spec.

    True when the latest approval pair at HEAD carries the envelope fingerprint the
    spec derives now, *intent*, and *code_trust*. May raise `admission.Refusal` or
    a Git error when the records cannot be read.
    """
    approvals = ws.approvals("HEAD")
    if not approvals:
        return False
    refs, _cited = ws.envelope(spec_text)
    envelope = admission.sibling("_acceptance.py").derive_envelope(refs)
    latest = approvals[-1]
    return bool(
        latest["envelope"]["envelope_fingerprint"] == envelope["envelope_fingerprint"]
        and latest["terminal_intent"] == intent
        and latest["code_trust"] == code_trust
    )


def _status_fit(
    admission: Any, gate: str, spec_text: str, plan_text: str
) -> tuple[bool, str | None, str | None]:
    """``(fits, spec status, plan status)``: whether *gate* fits the two artifacts' statuses."""
    want_spec, want_plan = _GATE_STATUSES[gate]
    spec_status = admission._projector.spec_status(spec_text)
    plan_status = admission._projector.plan_status(plan_text)
    fits = spec_status == want_spec and (want_plan is None or plan_status == want_plan)
    return fits, spec_status, plan_status


def _foreign_objects(ws: Any, admission: Any) -> bool:
    """True when the repository's objects may come from outside its own store.

    A partial clone, a promisor remote or an alternates file: the same test
    `git_history` applies. A record-named commit is never read there, because the
    read could start a fetch on a Git that ignores `GIT_NO_LAZY_FETCH`.
    """
    history = admission.sibling("_git_history.py")
    try:
        history.refuse_object_sources(ws.git.hardened)
    except history.GitHistoryRefused:
        return True
    return False


def park(
    ws: Any, admission: Any, *, gate: str, intent: str, code_trust: str
) -> dict[str, Any]:
    """Record that *gate* of the spec waits for a human answer.

    Refuses, first applicable in the documented order, with ``admission.Refusal``.
    Returns the printed payload; writes at most one record under the Git directory.
    """
    refusal = admission.Refusal

    def refuse(code: str, detail: str) -> Exception:
        return refusal(code, "controller", detail)

    spec_rel = ws.spec_rel
    if not safe_spec_path(spec_rel):
        raise refuse("gate-unsafe-path", "the spec directory is not a safe path")
    if _foreign_objects(ws, admission):
        raise refusal(
            "unsupported-git-config",
            "owner",
            "this repository is a partial clone or has a promisor remote or alternates; "
            "park reads a recorded commit only from a repository whose objects are all local",
        )
    ws.git.hardened.no_lazy_fetch = True  # a missing object fails, never fetches
    fs = admission.sibling("_file_safety.py")
    spec_bytes = _read_artifact(ws, fs, "spec.md")
    plan_bytes = _read_artifact(ws, fs, "plan.md")
    if spec_bytes is not None:
        spec_text = spec_bytes.decode("utf-8", "replace")
        try:
            declared = admission._projector.terminal_intent(spec_text)
        except admission._projector.ProjectionRefused as exc:
            raise refusal(exc.code, exc.owner, exc.detail) from exc
        if declared is not None and declared != intent:
            raise refusal(
                "intent-mismatch",
                "owner",
                f"--intent {intent} differs from the spec's Terminal Intent {declared}",
            )
    if spec_bytes is None or plan_bytes is None:
        raise refuse("gate-uncommitted", "spec.md or plan.md cannot be read as a plain file")
    for name, data in (("spec.md", spec_bytes), ("plan.md", plan_bytes)):
        if not _is_clean(ws, f"{spec_rel}/{name}", data):
            raise refuse("gate-uncommitted", f"{name} differs from its committed bytes at HEAD")
    if _already_admitted(ws, admission, spec_text, intent, code_trust):
        raise refuse(
            "gate-already-admitted", "start would answer current for this intent and trust"
        )
    want_spec, want_plan = _GATE_STATUSES[gate]
    fits, spec_status, plan_status = _status_fit(
        admission, gate, spec_text, plan_bytes.decode("utf-8", "replace")
    )
    if not fits:
        raise refuse(
            "gate-status-mismatch",
            f"{gate} needs spec {want_spec}"
            + (f" and plan {want_plan}" if want_plan else "")
            + f"; found spec {spec_status or 'missing'}, plan {plan_status or 'missing'}",
        )
    digests: dict[str, str] = {}
    refusals: list[GateDigestRefused] = []
    for name, data in (("spec.md", spec_bytes), ("plan.md", plan_bytes)):
        try:
            digests[name] = gate_digest(data, name=name)
        except GateDigestRefused as exc:
            refusals.append(exc)
    if refusals:
        first = refusals[0]
        raise refuse(first.code, first.detail or "an artifact has no gate digest")

    git_dir = ws.git.hardened.pins.git_dir
    gates_dir = git_dir / _STORE_REL
    path = gates_dir / record_name(spec_rel)
    existing: dict[str, Any] | None = None
    existing_bytes = b""
    try:
        existing_bytes = bytes(
            fs.read_confined_regular_file(gates_dir, path, max_bytes=_MAX_RECORD_BYTES)
        )
        existing = valid_record(ws.root, existing_bytes)
    except (OSError, fs.UnsafeContentError):
        existing = None
    if existing is not None and existing["spec_dir"] != spec_rel:
        existing = None
    if gate == "plan-approved" and (
        existing is None or existing["spec_digest"] != digests["spec.md"]
    ):
        raise refuse(
            "gate-spec-changed", "the spec changed since its spec-approved gate was parked"
        )

    body: dict[str, Any] = {
        "schema_version": 1,
        "spec_dir": spec_rel,
        "gate": gate,
        "intent": intent,
        "code_trust": code_trust,
        "spec_digest": digests["spec.md"],
        "plan_digest": digests["plan.md"],
        "commit": ws.git.head(),
    }
    if existing is not None:
        same = canonical_record({**body, "commit": existing["commit"]}) == existing_bytes
        if same and _recorded_commit_holds(ws, admission, existing):
            return {"status": "current", **{k: v for k, v in existing.items()
                                            if k != "schema_version"}}
    cm = admission.sibling("_confined_mutation.py")
    try:
        admission._commit.ensure_directory(git_dir, _STORE_REL)
        write = cm.confined_atomic_replace if os.path.lexists(path) else cm.confined_create
        write(gates_dir, path, canonical_record(body), max_bytes=_MAX_RECORD_BYTES)
    except (cm.MutationDenied, OSError, admission._git.SupervisorGitError) as exc:
        raise refuse(
            "gate-record-unwritable", f"the park record could not be written: {exc}"
        ) from exc
    return {"status": "parked", **{k: v for k, v in body.items() if k != "schema_version"}}


# ── gates ────────────────────────────────────────────────────────────────────

_RECORD_NAME_RE = re.compile(r"[0-9a-f]{16}\.json")
_READ_PREFIX = "git --no-pager --no-replace-objects --no-lazy-fetch cat-file blob"
_NO_ANSWER = (
    "the gate stays unapproved; the controller dispatches no implementation work for this spec"
)
_ENTRY_FORM = (
    "one line under the last ## Changelog heading: "
    "- YYYY-MM-DD: spec|plan|amendment approved by <handle>; "
    "the form is in the Parked gates section of the supervisor reference"
)
_REJECT = "the pair returns to Draft and Drafting and is reviewed again"
ANSWERS: dict[str, dict[str, str]] = {
    "spec-approved": {
        "approve": "the spec approver writes Status: Approved and the plan Changelog entry "
        f"({_ENTRY_FORM}); the controller then parks plan-approved",
        "reject": _REJECT,
        "no-answer": _NO_ANSWER,
    },
    "plan-approved": {
        "approve": "the plan approver writes Status: Approved and the Changelog entry "
        f"({_ENTRY_FORM}); the "
        "controller runs start with the spec digest from the spec approver's own answer and "
        "the plan digest from the plan approver's own answer",
        "reject": _REJECT,
        "no-answer": _NO_ANSWER,
    },
}


def _store_state(git_dir: Path) -> str:
    """``absent``, ``plain`` or ``bad``: what the store's `gates/` path is, link-free."""
    current = git_dir
    for part in _STORE_REL.split("/"):
        current = current / part
        try:
            info = os.lstat(current)
        except FileNotFoundError:
            return "absent"
        except OSError:
            return "bad"
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
            return "bad"
    return "plain"


def _read_entry(fs: Any, gates_dir: Path, name: str) -> bytes | None:
    """The bytes of one store entry, or ``None`` when it is not a readable small regular file.

    A non-regular entry or one over the size bound is judged by `lstat` alone, unread.
    """
    path = gates_dir / name
    try:
        info = os.lstat(path)
        if not stat.S_ISREG(info.st_mode) or info.st_size > _MAX_RECORD_BYTES:
            return None
        return bytes(fs.read_confined_regular_file(gates_dir, path, max_bytes=_MAX_RECORD_BYTES))
    except (OSError, fs.UnsafeContentError):
        return None


def _invalid_entry(name: str, data: bytes | None) -> dict[str, Any]:
    """The listing entry for a store entry that is not a valid park record."""
    entry: dict[str, Any] = {"state": "invalid"}
    if data is not None:
        try:
            body = json.loads(data.decode("utf-8"))
        except (UnicodeDecodeError, ValueError):
            body = None
        if isinstance(body, dict) and safe_spec_path(body.get("spec_dir")):
            entry["spec_dir"] = body["spec_dir"]
    if _RECORD_NAME_RE.fullmatch(name):
        entry["record"] = name
    return entry


def _is_pending(ws: Any, admission: Any, fs: Any, name: str, rec: dict[str, Any]) -> bool:
    """Whether the record still describes a waiting gate: name, commit, working tree, statuses."""
    if name != record_name(rec["spec_dir"]):
        return False
    texts: dict[str, str] = {}
    try:
        for art, key in (("spec.md", "spec_digest"), ("plan.md", "plan_digest")):
            committed = ws.git.show(f"{ws.spec_rel}/{art}", rec["commit"])
            working = _read_artifact(ws, fs, art)
            if committed is None or working is None:
                return False
            if gate_digest(committed, name=art) != rec[key]:
                return False
            if gate_digest(working, name=art) != rec[key]:
                return False
            texts[art] = committed.decode("utf-8")
        return _status_fit(admission, rec["gate"], texts["spec.md"], texts["plan.md"])[0]
    except (GateDigestRefused, admission._git.SupervisorGitError, OSError, ValueError):
        return False


def _valid_entry(
    root: Path, admission: Any, fs: Any, name: str, rec: dict[str, Any]
) -> dict[str, Any] | None:
    """The listing entry for a valid record, or ``None`` when `park` would call it admitted."""
    ws = admission.Workspace(root, rec["spec_dir"])
    ws.git.hardened.no_lazy_fetch = True  # a missing object fails, never fetches
    state = "stale"
    try:
        working_spec = _read_artifact(ws, fs, "spec.md")
        if working_spec is not None and _already_admitted(
            ws, admission, working_spec.decode("utf-8"), rec["intent"], rec["code_trust"]
        ):
            return None
        if (
            working_spec is not None
            and not _foreign_objects(ws, admission)
            and _is_pending(ws, admission, fs, name, rec)
        ):
            state = "pending"
    except (
        admission.Refusal, admission._git.SupervisorGitError, OSError, ValueError, KeyError,
        TypeError,
    ):
        state = "stale"  # records that cannot be read never list as approvable
    return {
        "spec_dir": rec["spec_dir"],
        "gate": rec["gate"],
        "spec_digest": rec["spec_digest"],
        "plan_digest": rec["plan_digest"],
        "intent": rec["intent"],
        "code_trust": rec["code_trust"],
        "commit": rec["commit"],
        "read": [f"{_READ_PREFIX} {rec['commit']}:{rec['spec_dir']}/{art}"
                 for art in ("spec.md", "plan.md")],
        "answers": dict(ANSWERS[rec["gate"]]),
        "state": state,
    }


def list_gates(root: Path, admission: Any) -> list[dict[str, Any]]:
    """Every park record's listing entry, sorted by spec directory then record; writes nothing."""
    fs = admission.sibling("_file_safety.py")
    git_dir = admission._git.HardenedGit(root).pins.git_dir
    kind = _store_state(git_dir)
    if kind == "absent":
        return []
    if kind == "bad":
        return [{"state": "invalid"}]
    gates_dir = git_dir / _STORE_REL
    try:
        with os.scandir(gates_dir) as scan:
            names = sorted(entry.name for entry in scan)
    except OSError:
        return [{"state": "invalid"}]
    found: list[tuple[str, str, dict[str, Any]]] = []
    for name in names:
        data = _read_entry(fs, gates_dir, name)
        rec = valid_record(root, data) if data is not None else None
        entry = _invalid_entry(name, data) if rec is None else _valid_entry(
            root, admission, fs, name, rec
        )
        if entry is not None:
            found.append((entry.get("spec_dir", ""), entry.get("record", name), entry))
    found.sort(key=lambda item: item[:2])
    return [item[2] for item in found]
