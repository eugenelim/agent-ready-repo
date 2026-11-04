"""Approval-gate digest for the work-loop supervisor.

`gate_digest` hashes a spec.md or plan.md the way an approval pins it: the
text is checked for hidden or control characters, a trailing `## Changelog`
section is validated and dropped, and the rest goes through the single
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
from typing import Any

_SCRIPTS_DIR = Path(__file__).resolve().parent
_HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
_FENCE_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})")
_LINE_SEPARATORS = frozenset({0x2028, 0x2029, 0xFFF9, 0xFFFA, 0xFFFB})

_modules: dict[str, ModuleType] = {}


class GateDigestRefused(Exception):
    """Raised when gate text cannot be digested; `code` names the reason."""

    def __init__(self, code: str) -> None:
        """Store the refusal *code* and use it as the message."""
        super().__init__(code)
        self.code = code


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


def _unsafe(text: str, is_hidden_char) -> bool:  # type: ignore[no-untyped-def]
    """True when *text* holds a control, format, hidden or separator character."""
    for i, ch in enumerate(text):
        if ch in ("\t", "\n"):
            continue
        if ch == "\r":
            if text[i + 1 : i + 2] == "\n":
                continue
            return True
        if unicodedata.category(ch) in ("Cc", "Cf") or ord(ch) in _LINE_SEPARATORS:
            return True
        if is_hidden_char(ch):
            return True
    return False


def _strip_changelog(text: str) -> str:
    """Validate and drop a trailing `## Changelog` section from LF-normalised *text*."""
    lines = text.split("\n")
    headings: list[int] = []
    fence: str | None = None
    for idx, line in enumerate(lines):
        m = _FENCE_RE.match(line)
        if m:
            marker = m.group(1)[0]
            if fence is None:
                fence = marker
            elif fence == marker:
                fence = None
            continue
        if fence is None and line.startswith("## "):
            headings.append(idx)
    changelog = [i for i in headings if lines[i].strip() == "## Changelog"]
    if not changelog:
        return text
    start = changelog[0]
    if len(changelog) != 1 or headings[-1] != start:
        raise GateDigestRefused("gate-changelog-shape")
    body = _HTML_COMMENT_RE.sub("", "\n".join(lines[start + 1 :]))
    for line in body.split("\n"):
        if line.strip() == "" or line.startswith("- ") or line[:1].isspace():
            continue
        raise GateDigestRefused("gate-changelog-shape")
    return "\n".join(lines[:start])


def gate_digest(text_or_bytes: str | bytes, *, name: str) -> str:
    """Return the lowercase hex SHA-256 pinning *text_or_bytes* as `spec.md` or `plan.md`.

    Raises `GateDigestRefused` with code `gate-unsafe-content` or
    `gate-changelog-shape`.
    """
    if isinstance(text_or_bytes, bytes):
        try:
            text = text_or_bytes.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise GateDigestRefused("gate-unsafe-content") from exc
    else:
        text = text_or_bytes
    lint = _load_sibling("core_work_loop_gates_lint_knowledge", "lint-knowledge.py")
    if _unsafe(text, lint.is_hidden_char):
        raise GateDigestRefused("gate-unsafe-content")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    remaining = _strip_changelog(text)
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
    approvals = ws.approvals("HEAD")
    if approvals:
        refs, _cited = ws.envelope(spec_text)
        envelope = admission.sibling("_acceptance.py").derive_envelope(refs)
        latest = approvals[-1]
        if (
            latest["envelope"]["envelope_fingerprint"] == envelope["envelope_fingerprint"]
            and latest["terminal_intent"] == intent
            and latest["code_trust"] == code_trust
        ):
            raise refuse(
                "gate-already-admitted", "start would answer current for this intent and trust"
            )
    want_spec, want_plan = _GATE_STATUSES[gate]
    spec_status = admission._projector.spec_status(spec_text)
    plan_status = admission._projector.plan_status(plan_bytes.decode("utf-8", "replace"))
    if spec_status != want_spec or (want_plan is not None and plan_status != want_plan):
        raise refuse(
            "gate-status-mismatch",
            f"{gate} needs spec {want_spec}"
            + (f" and plan {want_plan}" if want_plan else "")
            + f"; found spec {spec_status or 'missing'}, plan {plan_status or 'missing'}",
        )
    digests: dict[str, str] = {}
    codes: list[str] = []
    for name, data in (("spec.md", spec_bytes), ("plan.md", plan_bytes)):
        try:
            digests[name] = gate_digest(data, name=name)
        except GateDigestRefused as exc:
            codes.append(exc.code)
    if codes:
        code = "gate-unsafe-content" if "gate-unsafe-content" in codes else codes[0]
        raise refuse(code, "an artifact has no gate digest")

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
