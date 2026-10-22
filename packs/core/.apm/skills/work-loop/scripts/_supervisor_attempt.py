"""_supervisor_attempt — the manifest, the open-attempt check, and residue.

Issuing a worker request (``implement-task``, ``write-stub``, ``review-role``,
or ``assess-finding``) records a manifest in the supervisor store, under the
pinned Git directory: the size and sha256 of every trusted file (the spec, the
plan, the records the spec cites, and the installed skill directory) and of
every Git control state file. While that issuance is open, every ``next``,
``report``, and ``start`` first compares the working tree with the manifest
and with ``HEAD``, before any derivation and before any write. A difference
refuses the attempt: the store keeps a refusal record, and ``next`` answers
``attempt-residue`` until the named paths are restored and ``next`` clears it.

An issuance is open until it is refused, superseded by a different request, or
reported. ``report`` records the report in the store once the result is
committed, so a rebase never reopens a reported attempt. A moved ``HEAD`` is
accepted only when every commit after the manifest's is in the store's list of
commits the supervisor made; a trailer alone never counts.

A ``run-gates`` or ``regenerate`` request is issued under a manifest too, and
supervisor-launched repository code (a red proof) runs under one, so a write to a
trusted file by launched code is refused before any commit. A ``regenerate``
request's manifest leaves out the installed skill.

The store also holds the pinned digests of the installed supervisor files. The
admitted ``start`` records them once; every other entry point compares against
them, and an open ``regenerate`` request also accepts the digests of the pack
source at ``HEAD``, which the supervisor re-pins when it admits the result.

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
from collections.abc import Generator, Iterable
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any

_SCRIPTS_DIR = Path(__file__).resolve().parent
# The installed skill directory the supervisor runs from; a test points it at a copy.
SKILL_DIR = _SCRIPTS_DIR.parent


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
sibling = _commit.sibling
ensure_directory = _commit.ensure_directory
SupervisorGitError = _commit.SupervisorGitError

__all__ = [
    "ATTEMPT_KINDS",
    "Attempts",
    "Issuance",
    "SOURCE_REL",
    "WORKER_KINDS",
    "differences",
    "regenerate_request_id",
]

WORKER_KINDS = frozenset({"implement-task", "write-stub", "review-role", "assess-finding"})
# Requests whose result the controller reports after running repository code or
# regenerating the installed skill; each is issued under a manifest.
ATTEMPT_KINDS = WORKER_KINDS | {"run-gates", "regenerate"}
SOURCE_REL = "packs/core/.apm/skills/work-loop"
PINS_FILE = "pins.json"
REGENERATE_FILE = "regenerate.json"
ORPHAN_FILE = "orphan"
ADMITTED_FILE = "admitted-skill.json"
_POLICY_FILES = ("supervisor-policy.json", "review-rules.json")
_HEX_RE = re.compile(r"[0-9a-f]{64}")
_MAX_PIN_BYTES = 1024 * 1024
_SCHEMA_VERSION = 1
_RUN_ID_RE = re.compile(r"run-[0-9a-f]{16}")
_SHA_RE = re.compile(r"[0-9a-f]{40,64}")
_FILE_RE = re.compile(r"(\d{6})(\.json|\.refused\.json|\.cleared|\.superseded|\.reported)")
_SYMREF_RE = re.compile(r"ref: (refs/[\x21-\x7e]+)\s*")
_MAX_ENTRIES = 50_000
_MAX_FILE_BYTES = 64 * 1024 * 1024
_MAX_RECORD_BYTES = 16 * 1024 * 1024
_MAX_SMALL_BYTES = 64 * 1024
_NAMED_PATHS = 20
_PRUNED = "__pycache__"
_STORE_ROOT = "agentbundle-supervisor"


def _unverifiable(code: str, detail: str) -> SupervisorGitError:
    """A check that could not be made: it refuses, and the entry point logs a security event."""
    return SupervisorGitError(code, detail, unverifiable=True)


def _refusal(code: str, detail: str) -> Exception:
    """A ``Refusal``, loaded when needed because admission imports this module."""
    return _supervisor("_supervisor_admission.py").Refusal(code, "controller", detail)


def _json(record: dict[str, Any]) -> bytes:
    return json.dumps(record, sort_keys=True, separators=(",", ":")).encode()


def regenerate_request_id(source: dict[str, str]) -> str:
    """The id of the ``regenerate`` request for a pack source with these digests."""
    return "regenerate:" + hashlib.sha256(_json(source)).hexdigest()[:24]


def _digest(data: bytes) -> str:
    return f"{len(data)}:{hashlib.sha256(data).hexdigest()}"


def differences(old: dict[str, str], new: dict[str, str]) -> list[str]:
    """Labels whose entry was added, removed, or changed, sorted."""
    return sorted(k for k in old.keys() | new.keys() if old.get(k) != new.get(k))


def _named(paths: Iterable[str]) -> str:
    """Printable, bounded path names for a refusal message."""
    clean = sorted({re.sub(r"[^\x20-\x7e]", "?", p)[:200] for p in paths})
    shown = ", ".join(clean[:_NAMED_PATHS])
    return shown + (f", and {len(clean) - _NAMED_PATHS} more" if len(clean) > _NAMED_PATHS else "")


@dataclass(frozen=True)
class Issuance:
    """One recorded issuance of a worker request and its manifest."""

    seq: int
    run_id: str
    request_id: str
    kind: str
    head: str
    head_ref: str | None
    trusted: dict[str, str]
    git: dict[str, str]
    marks: frozenset[str]
    store: Path

    @property
    def refused(self) -> bool:
        return ".refused.json" in self.marks

    @property
    def cleared(self) -> bool:
        return ".cleared" in self.marks

    @property
    def superseded(self) -> bool:
        return ".superseded" in self.marks

    @property
    def reported(self) -> bool:
        return ".reported" in self.marks


class Attempts:
    """The attempt checks for one workspace; ``Workspace`` builds one and wires its Git helper."""

    def __init__(self, ws: Any) -> None:
        self.ws = ws
        self.open: Issuance | None = None
        self._manifest: Issuance | None = None
        # The digests of the installed supervisor files, hashed before any sibling
        # loaded; ``None`` when a caller drives the modules without the entry point.
        self.installed: dict[str, str] | None = None
        ws.git.hardened.control_check = self._control_check

    # ── reading files ───────────────────────────────────────────────────────

    @staticmethod
    def _entry(base: Path, path: Path) -> str | None:
        """The digest of one file under *base*, ``None`` when it is absent."""
        fs = sibling("_file_safety.py")
        try:
            info = os.lstat(path)
        except FileNotFoundError:
            return None
        except OSError as exc:
            raise _unverifiable(
                "denied-attempt-unreadable", f"{path.name} cannot be read"
            ) from exc
        if stat.S_ISLNK(info.st_mode):
            return "link:" + hashlib.sha256(os.fsencode(path.readlink())).hexdigest()
        if not stat.S_ISREG(info.st_mode):
            return "special"
        try:
            return _digest(
                bytes(fs.read_confined_regular_file(base, path, max_bytes=_MAX_FILE_BYTES))
            )
        except FileNotFoundError:
            return None
        except fs.UnsafeContentError:
            return "unsafe"
        except OSError as exc:
            raise _unverifiable(
                "denied-attempt-unreadable", f"{path.name} cannot be read"
            ) from exc

    def _walk(self, base: Path, prefix: str) -> dict[str, str]:
        """Every entry under *base*, labelled ``prefix + path``; ``__pycache__`` is skipped."""
        found: dict[str, str] = {}
        pending = [base]
        while pending:
            current = pending.pop()
            try:
                entries = sorted(os.scandir(current), key=lambda e: e.name)
            except FileNotFoundError:
                continue
            except OSError as exc:
                raise _unverifiable(
                    "denied-attempt-unreadable", f"{current.name} cannot be listed"
                ) from exc
            for entry in entries:
                path = Path(entry.path)
                if entry.name == _PRUNED and entry.is_dir(follow_symlinks=False):
                    continue
                if entry.is_dir(follow_symlinks=False):
                    pending.append(path)
                    continue
                digest = self._entry(base, path)
                if digest is not None:
                    found[prefix + path.relative_to(base).as_posix()] = digest
                if len(found) > _MAX_ENTRIES:
                    raise _unverifiable(
                        "denied-attempt-too-large", f"{base.name} holds too many files"
                    )
        return found

    def _text(self, directory: Path, rel: str) -> str | None:
        """A short Git control file's text, ``None`` when it is absent or not a plain file."""
        fs = sibling("_file_safety.py")
        path = directory / rel
        try:
            if not stat.S_ISREG(os.lstat(path).st_mode):
                return None
            data = fs.read_confined_regular_file(directory, path, max_bytes=_MAX_SMALL_BYTES)
        except (FileNotFoundError, fs.UnsafeContentError):
            return None
        except OSError as exc:
            raise _unverifiable("denied-attempt-unreadable", f"{rel} cannot be read") from exc
        return bytes(data).decode("utf-8", "replace")

    # ── the state the manifest records ──────────────────────────────────────

    def _directories(self) -> list[tuple[str, Path]]:
        pins = self.ws.git.hardened.pins
        dirs = [("git", pins.git_dir)]
        if pins.common_dir != pins.git_dir:
            dirs.append(("common", pins.common_dir))
        return dirs

    def git_state(self) -> dict[str, str]:
        """Git control state by direct file reads; the refs ``HEAD`` names are not part of it."""
        pins = self.ws.git.hardened.pins
        state: dict[str, str] = {}
        dot_git = pins.root / ".git"
        if not Path(dot_git).is_dir() or Path(dot_git).is_symlink():
            digest = self._entry(pins.root, dot_git)
            if digest is not None:
                state[".git"] = digest
        for label, directory in self._directories():
            for rel in ("config", "config.worktree", "commondir", "objects/info/alternates"):
                digest = self._entry(directory, directory / rel)
                if digest is not None:
                    state[f"{label}:{rel}"] = digest
            for rel in ("info", "hooks", "refs/replace"):
                state.update(self._walk(directory / rel, f"{label}:{rel}/"))
            packed = self._text(directory, "packed-refs")
            if packed is not None:
                lines = [ln for ln in packed.splitlines() if " refs/replace/" in ln]
                if lines:
                    state[f"{label}:packed-refs/replace"] = _digest("\n".join(lines).encode())
        return state

    def head_state(self) -> tuple[str | None, str]:
        """``HEAD``'s symbolic ref (``None`` when detached) and the commit it resolves to."""
        pins = self.ws.git.hardened.pins
        text = self._text(pins.git_dir, "HEAD")
        if text is None:
            raise _unverifiable("denied-git-control-state", "HEAD cannot be read")
        match = _SYMREF_RE.fullmatch(text)
        if match is None:
            sha = text.strip()
            if not _SHA_RE.fullmatch(sha):
                raise _unverifiable("denied-git-control-state", "HEAD is not a ref or a commit id")
            return None, sha
        ref = match.group(1)
        if ".." in ref.split("/"):
            raise _unverifiable("denied-git-control-state", "HEAD names a malformed ref")
        directories = [pins.git_dir, *({pins.common_dir} - {pins.git_dir})]
        for directory in directories:
            loose = self._text(directory, ref)
            if loose is not None and _SHA_RE.fullmatch(loose.strip()):
                return ref, loose.strip()
        for directory in reversed(directories):
            for line in (self._text(directory, "packed-refs") or "").splitlines():
                sha, _, name = line.partition(" ")
                if name == ref and _SHA_RE.fullmatch(sha):
                    return ref, sha
        raise _unverifiable("denied-git-control-state", "the branch HEAD names cannot be read")

    def trusted_paths(self, state: Any) -> list[str]:
        """The spec, the plan, and every cited record, repository-relative."""
        rel = self.ws.spec_rel
        return [f"{rel}/spec.md", f"{rel}/plan.md", *state.cited_paths]

    def _trusted_state(self, paths: Iterable[str], *, skill: bool = True) -> dict[str, str]:
        found: dict[str, str] = {}
        for rel in paths:
            try:
                content = self.ws.git.read_working(rel)
            except SupervisorGitError as exc:
                if exc.code != "denied-unsafe-path":
                    raise
                found[rel] = "unsafe"
                continue
            if content is not None:
                found[rel] = _digest(content)
        if skill:
            found.update(self._walk(Path(SKILL_DIR), "skill:"))
        return found

    # ── the supervisor store ────────────────────────────────────────────────

    def _store_dir(self, run_id: str) -> Path:
        return self.ws.git.hardened.pins.git_dir / self.ws.git._store_rel(run_id)

    def _write(self, run_id: str, name: str, data: bytes) -> None:
        """Create *name* under the run's ``attempts/`` directory; an existing one stays."""
        cm = sibling("_confined_mutation.py")
        git_dir = self.ws.git.hardened.pins.git_dir
        rel = self.ws.git._store_rel(run_id)
        self.ws.git.ensure_store(run_id)
        ensure_directory(git_dir, f"{rel}/attempts")
        store = git_dir / rel
        try:
            cm.confined_create(store, store / "attempts" / name, data)
        except cm.MutationDenied as exc:
            if exc.denial_code != "denied-already-exists":
                raise _unverifiable(
                    "denied-attempt-store", "the attempt record cannot be written"
                ) from exc

    def _put(self, run_id: str, name: str, data: bytes, *, replace: bool = False) -> None:
        """Write *name* in the run's store; an existing file stays unless *replace*."""
        cm = sibling("_confined_mutation.py")
        store = self.ws.git.ensure_store(run_id)
        try:
            if replace:
                cm.confined_atomic_replace(store, store / name, data)
            else:
                cm.confined_create(store, store / name, data)
        except cm.MutationDenied as exc:
            if replace or exc.denial_code != "denied-already-exists":
                raise _unverifiable(
                    "denied-attempt-store", f"{name} cannot be written to the store"
                ) from exc

    def _load(self, run_id: str, store: Path) -> Issuance | None:
        """The run's latest issuance for this spec, with its marks."""
        fs = sibling("_file_safety.py")
        attempts = store / "attempts"
        if not os.path.lexists(attempts):
            return None
        try:
            files = fs.list_confined_regular_files(store, attempts, max_files=_MAX_ENTRIES)
        except (fs.UnsafeContentError, OSError) as exc:
            raise _unverifiable(
                "denied-attempt-record", "the attempt store cannot be listed"
            ) from exc
        marks: dict[int, set[str]] = {}
        for path in files:
            match = _FILE_RE.fullmatch(path.name)
            if match:
                marks.setdefault(int(match.group(1)), set()).add(match.group(2))
        recorded = sorted(seq for seq, kinds in marks.items() if ".json" in kinds)
        if not recorded:
            return None
        seq = recorded[-1]
        path = attempts / f"{seq:06d}.json"
        try:
            record = json.loads(
                bytes(fs.read_confined_regular_file(store, path, max_bytes=_MAX_RECORD_BYTES))
            )
        except (ValueError, fs.UnsafeContentError, OSError) as exc:
            raise _unverifiable(
                "denied-attempt-record", "the attempt record is unreadable"
            ) from exc
        if not self._valid(record, run_id):
            raise _unverifiable("denied-attempt-record", "the attempt record is malformed")
        if record["spec"] != self.ws.spec_rel:
            return None
        return Issuance(
            seq=seq,
            run_id=run_id,
            request_id=record["request_id"],
            kind=record["kind"],
            head=record["head"],
            head_ref=record["head_ref"],
            trusted=record["trusted"],
            git=record["git"],
            marks=frozenset(marks[seq]),
            store=store,
        )

    @staticmethod
    def _valid(record: object, run_id: str) -> bool:
        def entries(value: object) -> bool:
            return isinstance(value, dict) and all(
                isinstance(k, str) and isinstance(v, str) for k, v in value.items()
            )

        return (
            isinstance(record, dict)
            and record.get("schema_version") == _SCHEMA_VERSION
            and record.get("run_id") == run_id
            and all(isinstance(record.get(k), str) for k in ("spec", "request_id", "kind"))
            and isinstance(record.get("head"), str)
            and bool(_SHA_RE.fullmatch(record["head"]))
            and (record.get("head_ref") is None or isinstance(record["head_ref"], str))
            and entries(record.get("trusted"))
            and entries(record.get("git"))
        )

    def _latest(self) -> list[Issuance]:
        """The latest issuance of every run that has one for this spec."""
        fs = sibling("_file_safety.py")
        git_dir = self.ws.git.hardened.pins.git_dir
        base = git_dir / _STORE_ROOT
        if not os.path.lexists(base):
            return []
        try:
            runs = fs.list_confined_directories(git_dir, base)
        except (fs.UnsafeContentError, OSError) as exc:
            raise _unverifiable(
                "denied-attempt-record", "the supervisor store cannot be listed"
            ) from exc
        latest = (self._load(d.name, d) for d in runs if _RUN_ID_RE.fullmatch(d.name))
        return [issuance for issuance in latest if issuance is not None]

    def _mark(self, issuance: Issuance, suffix: str, data: bytes = b"") -> None:
        self._write(issuance.run_id, f"{issuance.seq:06d}{suffix}", data)

    # ── comparing the working tree with a manifest ──────────────────────────

    def _history(self, issuance: Issuance, current: str) -> bool:
        """Whether ``HEAD`` left the manifest's by a commit the supervisor did not make.

        The manifest's ``HEAD`` must be an ancestor of the current one and every
        commit after it must be in the store's list of commits the supervisor made.
        Trailers alone never count.
        """
        made = self.ws.git.made_commits(issuance.run_id)
        out = self.ws.git.run(
            "log", "--left-right", "--format=%m%x1f%H", f"{issuance.head}...{current}"
        )
        for line in out.decode("utf-8", "replace").splitlines():
            side, _, sha = line.partition("\x1f")
            if side != ">" or sha not in made:
                return True
        return False

    def _delivery(self) -> list[str]:
        try:
            _lagging, foreign = self.ws.git.delivery_lag()
        except SupervisorGitError as exc:
            if exc.code != "denied-unsafe-path":
                raise
            return [f"{self.ws.git.delivery_rel}/"]
        return foreign

    def _differences(
        self, issuance: Issuance, current: str, symref: str | None, bad: bool
    ) -> list[str]:
        paths = differences(issuance.git, self.git_state())
        paths += differences(issuance.trusted, self._files(issuance))
        if bad or symref != issuance.head_ref:
            paths.append("HEAD")
        paths += self._delivery()
        return sorted(set(paths))

    def _files(self, issuance: Issuance) -> dict[str, str]:
        """The trusted files as they stand now, for comparison with *issuance*'s manifest."""
        trusted = [k for k in issuance.trusted if not k.startswith("skill:")]
        return self._trusted_state(trusted, skill=issuance.kind != "regenerate")

    def _control_check(self, hardened: Any) -> None:
        """The helper's pre-check: Git control state must match the open attempt's manifest."""
        manifest = self._manifest
        if manifest is None:
            return
        changed = differences(manifest.git, self.git_state())
        if changed:
            raise SupervisorGitError(
                "denied-git-control-state",
                f"Git control state differs from the open attempt's manifest: {_named(changed)}",
            )

    # ── the check ───────────────────────────────────────────────────────────

    def guard(self, verb: str) -> Issuance | None:
        """Refuse when an open attempt differs from its manifest or a refusal stands.

        Runs before any derivation and any write. Returns the open attempt that
        passed, or ``None``; only ``next`` clears a refusal whose paths are restored.
        """
        self.open = None
        self._manifest = None
        for issuance in self._latest():
            if issuance.superseded or issuance.reported or (issuance.refused and issuance.cleared):
                continue
            # Git control state first, by direct file reads: no supervisor git call may
            # read state a worker changed, and a refusal here is still recorded.
            git_paths = differences(issuance.git, self.git_state())
            if git_paths:
                paths = sorted({*git_paths, *differences(issuance.trusted, self._files(issuance))})
            else:
                current_ref, current = self.head_state()
                bad = current != issuance.head and self._history(issuance, current)
                paths = self._differences(issuance, current, current_ref, bad)
            if issuance.refused:
                if paths:
                    raise _refusal("attempt-residue", self._detail(paths, standing=True))
                if verb == "next":
                    self._mark(issuance, ".cleared")
                    continue
                if verb == "report":
                    raise _refusal(
                        "attempt-residue",
                        "the attempt was refused and its paths are restored; run next to clear "
                        "the refusal and re-issue the request",
                    )
                continue
            if paths:
                self._refuse(issuance, paths, verb)
            self.open = self._manifest = issuance
        return self.open

    @staticmethod
    def _detail(paths: list[str], *, standing: bool) -> str:
        head = (
            "a refused attempt still differs from its manifest"
            if standing
            else ("the attempt differs from its manifest")
        )
        return f"{head}: {_named(paths)}; restore these paths"

    def _refuse(self, issuance: Issuance, paths: list[str], verb: str) -> None:
        """Record the refusal in the store, log it, and refuse."""
        record = {"schema_version": _SCHEMA_VERSION, "verb": verb, "paths": paths[:1000]}
        self._mark(issuance, ".refused.json", json.dumps(record, sort_keys=True).encode())
        code = "attempt-refused" if verb == "report" else "attempt-residue"
        self._log(code)
        raise _refusal(code, self._detail(paths, standing=False))

    def _log(self, reason: str) -> None:
        """Write one ``security-event.v1`` denial; the refusal stands even if it is not stored."""
        events = sibling("_security_events.py")
        events.emit_denial_best_effort(
            self.ws.local.security_sink(),
            events.SecurityEvent(
                schema_version=1,
                operation_id=events.make_operation_id(),
                correlation_id=self.ws.spec_rel,
                event_type="supervisor-attempt-check",
                outcome="denied",
                reason_code=reason,
                timestamp=self.ws.clock(),
            ),
        )

    def close(self, result: dict[str, Any]) -> None:
        """Record in the store that the open attempt's request has been reported."""
        open_attempt = self.open
        if (
            open_attempt is not None
            and open_attempt.request_id == result.get("request_id")
            and open_attempt.kind == result.get("kind")
        ):
            self._mark(open_attempt, ".reported")
            self.open = self._manifest = None

    # ── issuing ─────────────────────────────────────────────────────────────

    def issue(self, state: Any, action: Any) -> None:
        """Record a manifest when ``next`` issues or re-issues a worker request.

        An open attempt for the same request keeps its manifest. A different
        request or a terminal step supersedes it.
        """
        request = action.request if action.kind == "request" else None
        open_attempt = self.open
        if request is not None and request["kind"] in ATTEMPT_KINDS:
            if open_attempt is not None and open_attempt.request_id == request["request_id"]:
                return
            self._confirm_admitted_skill(state.run_id)
            if open_attempt is not None:
                self._supersede(open_attempt)
            regenerating = request["kind"] == "regenerate"
            self._record(state, request, skill=not regenerating)
            if regenerating:
                self._put(
                    state.run_id,
                    REGENERATE_FILE,
                    _json({
                        "schema_version": _SCHEMA_VERSION,
                        "run_id": state.run_id,
                        "request_id": request["request_id"],
                        "source": action.detail["source_digests"],
                    }),
                    replace=True,
                )
        elif open_attempt is not None and (request is not None or action.kind == "terminal"):
            self._supersede(open_attempt)
            self.open = self._manifest = None

    def _supersede(self, issuance: Issuance) -> None:
        """Mark *issuance* superseded; a ``regenerate`` request's recorded source goes with it."""
        self._mark(issuance, ".superseded")
        if issuance.kind == "regenerate":
            (issuance.store / REGENERATE_FILE).unlink(missing_ok=True)

    def _record(self, state: Any, request: dict[str, Any], *, skill: bool = True) -> None:
        run_id = state.run_id
        store = self._store_dir(run_id)
        previous = self._load(run_id, store)
        seq = (previous.seq if previous is not None else 0) + 1
        symref, head = self.head_state()
        record = {
            "schema_version": _SCHEMA_VERSION,
            "spec": self.ws.spec_rel,
            "run_id": run_id,
            "request_id": request["request_id"],
            "kind": request["kind"],
            "head": head,
            "head_ref": symref,
            "trusted": self._trusted_state(self.trusted_paths(state), skill=skill),
            "git": self.git_state(),
        }
        body = _json(record)
        self._write(run_id, f"{seq:06d}.json", body)
        self.open = self._manifest = self._load(run_id, store)

    # ── launched code ───────────────────────────────────────────────────────

    @contextmanager
    def launched(self, state: Any, label: str) -> Generator[None]:
        """Run repository code the supervisor launches, then check what it left behind.

        With an attempt open, the attempt's manifest is the baseline; otherwise the
        launch is issued under its own manifest. A difference afterwards refuses the
        result the same way a refused attempt does, and leaves residue.
        """
        own = self.open is None
        if own:
            self._record(state, {"request_id": f"launch:{label}", "kind": "red-proof"})
        issuance = self.open
        assert issuance is not None
        try:
            yield
        finally:
            current_ref, current = self.head_state()
            bad = current != issuance.head and self._history(issuance, current)
            paths = self._differences(issuance, current, current_ref, bad)
            if paths:
                self._refuse(issuance, paths, "report")
            if own:
                self._mark(issuance, ".reported")
                self.open = self._manifest = None

    # ── pinned digests ──────────────────────────────────────────────────────

    def _store_record(self, run_id: str, name: str) -> dict[str, Any] | None:
        """A store record of this run; ``None`` when absent, a refusal when it is not valid."""
        store = self._store_dir(run_id)
        path = store / name
        if not os.path.lexists(path):
            return None
        fs = sibling("_file_safety.py")
        try:
            record = json.loads(
                bytes(fs.read_confined_regular_file(store, path, max_bytes=_MAX_PIN_BYTES))
            )
        except (ValueError, fs.UnsafeContentError, OSError) as exc:
            raise _unverifiable("supervisor-changed", f"{name} cannot be read") from exc
        if (
            not isinstance(record, dict)
            or record.get("schema_version") != _SCHEMA_VERSION
            or record.get("run_id") != run_id
        ):
            raise _unverifiable("supervisor-changed", f"{name} is malformed")
        return record

    @staticmethod
    def _digest_map(record: dict[str, Any], key: str, name: str) -> dict[str, str]:
        digests = record.get(key)
        if (
            not isinstance(digests, dict)
            or not digests
            or not all(
                isinstance(k, str) and _HEX_RE.fullmatch(str(v)) for k, v in digests.items()
            )
        ):
            raise _unverifiable("supervisor-changed", f"{name} is malformed")
        return digests  # type: ignore[no-any-return]

    def _pin_record(self, run_id: str) -> dict[str, str] | None:
        """The digests a run pinned; ``None`` when it has no record."""
        record = self._store_record(run_id, PINS_FILE)
        if record is None:
            return None
        if record.get("spec") != self.ws.spec_rel:
            raise _unverifiable("supervisor-changed", f"{PINS_FILE} names another spec")
        return self._digest_map(record, "digests", PINS_FILE)

    def _open_regeneration(self, run_id: str) -> dict[str, str] | None:
        """The pack source digests a ``regenerate`` request recorded, while it is open."""
        record = self._store_record(run_id, REGENERATE_FILE)
        if record is None:
            return None
        source = self._digest_map(record, "source", REGENERATE_FILE)
        issuance = self._load(run_id, self._store_dir(run_id))
        if (
            issuance is None
            or issuance.kind != "regenerate"
            or issuance.request_id != record.get("request_id")
            or issuance.superseded
            or issuance.reported
            or issuance.refused
        ):
            return None
        return source

    def _pin_body(self, run_id: str, digests: dict[str, str]) -> bytes:
        return _json({
            "schema_version": _SCHEMA_VERSION,
            "run_id": run_id,
            "spec": self.ws.spec_rel,
            "digests": digests,
        })

    def check_pins(self, verb: str = "") -> None:
        """Refuse unless the installed files match the admitted run's pins.

        The entry point compared them before any sibling loaded; this reads the
        committed approvals, so a damaged working copy hides nothing. An open
        ``regenerate`` request also accepts the digests of the pack source it recorded.
        An admission that crashed before its pin was written has only its own approval
        and terminal steps, every one in the store's made-commit record; a ``start``
        records it then, and nothing else may. A run with no such record, as one
        admitted before pinning shipped, is never pinned.
        """
        installed = self.installed
        if installed is not None and verb == "start":
            self.retire_orphans()
        approvals = self.ws.approvals() if installed is not None else []
        if installed is None or not approvals:
            return
        run_id = approvals[0]["run_id"]
        pinned = self._pin_record(run_id)
        if pinned is None:
            commits = self.ws.git.supervisor_commits(run_id)
            made = self.ws.git.made_commits(run_id)
            if (
                verb == "start"
                and len(approvals) == 1
                and made
                and all(c.sha in made and c.operation in ("approval", "terminal") for c in commits)
            ):
                self.pin(run_id)
                return
            raise _unverifiable("supervisor-changed", "the supervisor's pin record is missing")
        if installed != pinned and installed != self._open_regeneration(run_id):
            raise _refusal(
                "supervisor-changed", "the installed supervisor differs from its pinned digests"
            )

    def retire_orphans(self) -> None:
        """Mark this spec's unpinned run directories whose approval never reached ``HEAD``.

        A directory is an orphan when none of its made-commit ids is reachable from
        ``HEAD``, judged through the hardened helper. The mark lets the entry point's
        pre-import check pass it; the directory is kept.
        """
        fs = sibling("_file_safety.py")
        git_dir = self.ws.git.hardened.pins.git_dir
        base = git_dir / _STORE_ROOT
        if not os.path.lexists(base):
            return
        try:
            runs = fs.list_confined_directories(git_dir, base)
        except (fs.UnsafeContentError, OSError) as exc:
            raise _unverifiable(
                "denied-attempt-record", "the supervisor store cannot be listed"
            ) from exc
        for directory in runs:
            if not _RUN_ID_RE.fullmatch(directory.name) or any(
                os.path.lexists(directory / name) for name in (PINS_FILE, ORPHAN_FILE)
            ):
                continue
            try:
                recorded = bytes(
                    fs.read_confined_regular_file(
                        directory, directory / "spec", max_bytes=_MAX_SMALL_BYTES
                    )
                ).decode("utf-8", "replace")
            except (fs.UnsafeContentError, OSError):
                continue  # unreadable: the entry point already refused it
            if recorded != self.ws.spec_rel:
                continue
            made = self.ws.git.made_commits(directory.name)
            landed = {c.sha for c in self.ws.git.supervisor_commits(directory.name)} & made
            if not landed:
                self._put(directory.name, ORPHAN_FILE, b"")

    def pin(self, run_id: str) -> None:
        """Record the installed digests once the run's first approval has landed.

        A record that already exists is never overwritten, and a different one refuses.
        """
        installed = self.installed
        if installed is None:
            return
        recorded = self._pin_record(run_id)
        if recorded is None:
            self._put(run_id, PINS_FILE, self._pin_body(run_id, installed))
        elif recorded != installed:
            raise _refusal(
                "supervisor-changed", "the installed supervisor differs from its pinned digests"
            )

    # ── regeneration ────────────────────────────────────────────────────────

    @staticmethod
    def _pinned_name(rel: str) -> bool:
        """Whether *rel*, relative to a skill directory, is a pinned file."""
        if rel in _POLICY_FILES:
            return True
        parts = rel.split("/")
        nested = parts[0] == "scripts" and _PRUNED not in parts
        return nested and len(parts) > 1 and bool(parts[-1])

    def _blobs_at_head(self, prefix: str, *, pinned_only: bool) -> dict[str, bytes] | None:
        """The bytes of each file under *prefix* at ``HEAD``; ``None`` when there are none."""
        entries = {
            p[len(prefix) :]: oid for p, oid in self.ws.git.tree_entries() if p.startswith(prefix)
        }
        if not entries:
            return None
        wanted = {
            rel: oid for rel, oid in entries.items() if not pinned_only or self._pinned_name(rel)
        }
        oids = sorted(set(wanted.values()))
        out = self.ws.git.run("cat-file", "--batch", stdin=("\n".join(oids) + "\n").encode())
        blobs: dict[str, bytes] = {}
        position = 0
        for oid in oids:
            end = out.index(b"\n", position)
            fields = out[position:end].split()
            if len(fields) != 3 or fields[0].decode() != oid or fields[1] != b"blob":
                raise _unverifiable("denied-attempt-record", "the pack source cannot be read")
            size = int(fields[2])
            blobs[oid] = out[end + 1 : end + 1 + size]
            position = end + 1 + size + 1
        return {rel: blobs[oid] for rel, oid in sorted(wanted.items())}

    def source_digests(self) -> dict[str, str] | None:
        """Digests of the pack source's pinned files at ``HEAD``; ``None`` without that source."""
        blobs = self._blobs_at_head(SOURCE_REL + "/", pinned_only=True)
        if blobs is None:
            return None
        return {rel: hashlib.sha256(data).hexdigest() for rel, data in blobs.items()}

    def _whole_skill_at_head(self, prefix: str) -> dict[str, str] | None:
        """Every file under *prefix* at ``HEAD``, labelled like ``_walk`` labels the install."""
        blobs = self._blobs_at_head(prefix, pinned_only=False)
        if blobs is None:
            return None
        return {rel: _digest(data) for rel, data in blobs.items()}

    def _tracked_skill_prefix(self) -> str | None:
        """The installed skill's path in the work tree, ``/``-ended; ``None`` outside it."""
        try:
            rel = Path(os.path.realpath(SKILL_DIR)).relative_to(os.path.realpath(self.ws.root))
        except ValueError:
            return None
        return rel.as_posix() + "/"

    def pending_regeneration(self) -> dict[str, str] | None:
        """The pack source's digests while a ``regenerate`` request is due or still open.

        It is due when ``HEAD`` holds the source and the installed skill differs. Once the
        controller has regenerated, the request stays current until it is reported.
        """
        if self.installed is None:
            return None
        source = self.source_digests()
        if source is None:
            return None
        if source != self.installed:
            return source
        open_attempt = self.open
        if (
            open_attempt is not None
            and open_attempt.kind == "regenerate"
            and open_attempt.request_id == regenerate_request_id(source)
        ):
            return source
        return None

    def admit_regeneration(self, result: dict[str, Any]) -> None:
        """Admit a ``regenerate`` result: the installed files must equal the source at ``HEAD``.

        Re-pins the installed digests and closes the request's acceptance of source digests.
        """
        issuance = self.open
        if (
            issuance is None
            or issuance.kind != "regenerate"
            or issuance.request_id != result.get("request_id")
        ):
            raise _refusal("not-current-attempt", "the result is not for the current request")
        source = self.source_digests()
        whole = self._whole_skill_at_head(SOURCE_REL + "/")
        installed_tree = self._walk(SKILL_DIR, "")
        if (
            self.installed is None
            or source is None
            or source != self.installed
            or whole != installed_tree
        ):
            raise _refusal(
                "supervisor-changed",
                "the installed skill does not match the pack source at HEAD",
            )
        self._put(
            issuance.run_id, PINS_FILE, self._pin_body(issuance.run_id, source), replace=True
        )
        (issuance.store / REGENERATE_FILE).unlink(missing_ok=True)
        # A tracked install is committed by the controller; the next issuance checks that
        # what it committed is what was admitted.
        prefix = self._tracked_skill_prefix()
        if prefix is not None and self._whole_skill_at_head(prefix) is not None:
            self._put(
                issuance.run_id,
                ADMITTED_FILE,
                _json({
                    "schema_version": _SCHEMA_VERSION,
                    "run_id": issuance.run_id,
                    "tree": installed_tree,
                }),
                replace=True,
            )

    def _confirm_admitted_skill(self, run_id: str) -> None:
        """Before the first issuance after a regeneration, check the committed install.

        The controller commits a tracked install; what it committed must equal what the
        regeneration admitted, or nothing more is issued.
        """
        record = self._store_record(run_id, ADMITTED_FILE)
        if record is None:
            return
        tree = self._digest_map_any(record, "tree")
        prefix = self._tracked_skill_prefix()
        committed = self._whole_skill_at_head(prefix) if prefix is not None else None
        if committed != tree:
            raise _refusal(
                "supervisor-changed",
                "the committed installed skill differs from the one the regeneration admitted",
            )
        (self._store_dir(run_id) / ADMITTED_FILE).unlink(missing_ok=True)

    @staticmethod
    def _digest_map_any(record: dict[str, Any], key: str) -> dict[str, str]:
        tree = record.get(key)
        if not isinstance(tree, dict) or not all(
            isinstance(k, str) and isinstance(v, str) for k, v in tree.items()
        ):
            raise _unverifiable("supervisor-changed", f"{ADMITTED_FILE} is malformed")
        return tree

    # ── the change set ──────────────────────────────────────────────────────

    def check_change_set(self, state: Any, changed: list[str]) -> None:
        """Refuse a link that leaves the root or points at a trusted file or Git."""
        root = Path(os.path.realpath(self.ws.root))
        git_dirs = [Path(os.path.realpath(d)) for _, d in self._directories()]
        trusted = {Path(os.path.realpath(self.ws.root / p)) for p in self.trusted_paths(state)}
        skill = Path(os.path.realpath(SKILL_DIR))
        for rel in changed:
            path = self.ws.root / rel
            if not path.is_symlink():
                continue
            target = Path(os.path.realpath(path))
            if any(target == d or d in target.parents for d in git_dirs):
                where = "the Git directory"
            elif target in trusted or target == skill or skill in target.parents:
                where = "a trusted file"
            elif target != root and root not in target.parents:
                where = "a place outside the execution root"
            else:
                continue
            self._log("unsafe-link")
            raise _refusal("unsafe-link", f"{_named([rel])} is a link into {where}")
