"""Offline view assembly and publication for the navigate-intents export.

Receives the payload that ``navigate_intents.build_view_payload`` builds and
never derives the intent graph itself.  Standard-library-only.
"""
from __future__ import annotations

import contextlib
import datetime as _dt
import hashlib
import importlib.util
import json
import os
import re
import stat as _stat
import subprocess
import sys
import tempfile
from pathlib import Path, PurePath
from typing import Any, NamedTuple
from urllib.parse import quote

try:
    from datetime import UTC as _UTC
except ImportError:  # Python < 3.11
    _UTC = _dt.timezone.utc  # type: ignore[assignment]  # noqa: UP017

# Characters that must never appear raw inside the HTML data block.
_DATA_ESCAPES = {
    "<": "\\u003c",
    ">": "\\u003e",
    "&": "\\u0026",
    "\u2028": "\\u2028",
    "\u2029": "\\u2029",
}


EXPORT_BUDGET_BYTES = 104_857_600
_NAME_RULE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,99}\.html")
_GIT_TIMEOUT_SECONDS = 5
_GITDIR_FILE_LIMIT = 4096


class ViewRefusal(Exception):
    """A refusal to build or publish the view, carrying the closed error fields."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        limits: dict[str, Any] | None = None,
        observed: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.limits = limits or {}
        self.observed = observed or {}


def data_block_json(payload: dict[str, Any]) -> str:
    """Serialise *payload* so it is safe inside a ``<script>`` data block."""
    text = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    for raw, escaped in _DATA_ESCAPES.items():
        text = text.replace(raw, escaped)
    return text


def build_html(payload: dict[str, Any]) -> str:
    """Return the HTML document that carries *payload* in its one data block."""
    return (
        "<!doctype html>\n"
        '<html lang="en">\n'
        '<head><meta charset="utf-8"><title>Intent graph</title></head>\n'
        "<body>\n"
        '<script type="application/json" id="intent-data">'
        f"{data_block_json(payload)}</script>\n"
        "</body>\n"
        "</html>\n"
    )


class Destination(NamedTuple):
    """A validated publication target: real directory, file name, and identity."""

    directory: str
    name: str
    identity: tuple[int, int]


def _git_run(root: Path, args: list[str]) -> subprocess.CompletedProcess[bytes]:
    """Run one hardened Git call: no shell, fixed argv, no prompt, no inherited GIT_ state.

    Raises ``OSError`` when Git cannot start and ``subprocess.TimeoutExpired`` on timeout.
    """
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env["GIT_TERMINAL_PROMPT"] = "0"
    return subprocess.run(  # noqa: S603
        ["git", "-C", str(root), "-c", "core.fsmonitor=false", *args],  # noqa: S607
        shell=False,
        env=env,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        timeout=_GIT_TIMEOUT_SECONDS,
        check=False,
    )


_ALLOWED_HOSTS = frozenset({"github.com"})
_PART = r"[A-Za-z0-9][A-Za-z0-9._-]{0,99}"
_REMOTE_FORMS = (
    re.compile(r"https://(?P<host>[^/@:?#\s]+)/(?P<owner>[^/\s]+)/(?P<repo>[^/\s]+)"),
    re.compile(r"git@(?P<host>[^/@:?#\s]+):(?P<owner>[^/\s]+)/(?P<repo>[^/\s]+)"),
    re.compile(r"ssh://git@(?P<host>[^/@:?#\s]+)/(?P<owner>[^/\s]+)/(?P<repo>[^/\s]+)"),
)
_COMMIT_LENGTH = {"sha1": 40, "sha256": 64}
_LINK_DIRS = ("docs/product/intents", "docs/product/briefs", "docs/specs")
_safety_mod: Any = None


def _parse_github_remote(url: str) -> str | None:
    """Return ``owner/repo`` when *url* is exactly a recognised GitHub remote, else None."""
    for form in _REMOTE_FORMS:
        found = form.fullmatch(url)
        if found is None:
            continue
        repo = found["repo"]
        if repo.endswith(".git"):
            repo = repo[: -len(".git")]
        owner = found["owner"]
        if found["host"] not in _ALLOWED_HOSTS:
            return None
        if not all(re.fullmatch(_PART, part) for part in (owner, repo)):
            return None
        return f"{owner}/{repo}"
    return None


def _file_safety() -> Any:
    """Load the co-located ``_file_safety.py`` at most once; None when unavailable."""
    global _safety_mod
    if _safety_mod is not None:
        return _safety_mod
    path = Path(__file__).resolve().parent / "_file_safety.py"
    name = "core_navigate_intents_view_file_safety"
    try:
        if not _stat.S_ISREG(os.lstat(path).st_mode):
            return None
        spec = importlib.util.spec_from_file_location(name, path)
        if spec is None or spec.loader is None:
            return None
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    except Exception:  # noqa: BLE001
        sys.modules.pop(name, None)
        return None
    _safety_mod = mod
    return mod


def _git_text(root: Path, args: list[str]) -> str | None:
    """Run one hardened Git call and return stdout text, or None on any failure."""
    try:
        done = _git_run(root, args)
    except (OSError, subprocess.SubprocessError):
        return None
    if done.returncode != 0:
        return None
    return done.stdout.decode("utf-8", "surrogateescape")


def _tree_blobs(root: Path) -> dict[str, str] | None:
    """Return ``{link path: blob id}`` for the corpus directories at HEAD, or None."""
    try:
        done = _git_run(root, ["ls-tree", "-r", "-z", "--full-name", "HEAD", "--", *_LINK_DIRS])
    except (OSError, subprocess.SubprocessError):
        return None
    if done.returncode != 0:
        return None
    blobs: dict[str, str] = {}
    for entry in done.stdout.decode("utf-8", "surrogateescape").split("\0"):
        meta, tab, path = entry.partition("\t")
        fields = meta.split(" ")
        if tab and len(fields) == 3 and fields[0] != "120000" and fields[1] == "blob":
            blobs[path] = fields[2]
    return blobs


def _blob_id(data: bytes, object_format: str) -> str:
    """Return the Git blob id of *data* under *object_format* (``sha1`` or ``sha256``)."""
    digest = hashlib.new(object_format)
    digest.update(b"blob %d\0" % len(data))
    digest.update(data)
    return digest.hexdigest()


def _tree_matches(
    root: Path, nodes: list[dict[str, Any]], prefix: str, object_format: str
) -> bool:
    """Return whether every node file's bytes equal HEAD's blob at its link path."""
    safety = _file_safety()
    blobs = _tree_blobs(root)
    if safety is None or blobs is None:
        return False
    real_root = Path(os.path.realpath(root))
    for node in nodes:
        rel = node.get("path", "")
        expected = blobs.get(f"{prefix}/{rel}" if prefix else rel)
        if expected is None:
            return False
        try:
            data = safety.read_confined_regular_file(real_root, real_root / rel)
        except Exception:  # noqa: BLE001
            return False
        if _blob_id(data, object_format) != expected:
            return False
    return True


def _encode_path(path: str) -> str:
    """Percent-encode each segment of a slash-separated *path*; only unreserved characters stay."""
    return "/".join(quote(segment, safe="") for segment in path.split("/"))


def source_links(
    root: Path, nodes: list[dict[str, Any]]
) -> tuple[dict[str, dict[str, Any]], str | None]:
    """Map each node id to its source link and return the commit used, or None.

    A recognised GitHub ``origin`` gives ``commit`` links when ``HEAD`` is on ``origin`` and
    every node file matches ``HEAD``'s tree, otherwise ``latest`` links.  Anything else, or
    any failed Git call, gives ``inert`` links (the path as plain text).
    """
    inert = {n["id"]: {"kind": "inert", "path": n.get("path", "")} for n in nodes}
    remote = _git_text(root, ["config", "--get", "remote.origin.url"])
    repo = _parse_github_remote(remote.rstrip("\n")) if remote else None
    toplevel = _git_text(root, ["rev-parse", "--show-toplevel"])
    if repo is None or not toplevel:
        return inert, None
    prefix = os.path.relpath(os.path.realpath(root), os.path.realpath(toplevel.rstrip("\n")))
    prefix = "" if prefix == "." else Path(prefix).as_posix()
    if prefix == ".." or prefix.startswith("../"):
        return inert, None
    head = (_git_text(root, ["rev-parse", "HEAD"]) or "").strip()
    fmt = (_git_text(root, ["rev-parse", "--show-object-format"]) or "").strip()
    commit: str | None = None
    if (
        fmt in _COMMIT_LENGTH
        and len(head) == _COMMIT_LENGTH[fmt]
        and re.fullmatch(r"[0-9a-f]+", head)
        and (_git_text(root, ["for-each-ref", "--contains", "HEAD", "refs/remotes/origin/"]) or "")
        .strip()
        and _tree_matches(root, nodes, prefix, fmt)
    ):
        commit = head
    ref = commit or "HEAD"
    kind = "commit" if commit else "latest"
    links: dict[str, dict[str, Any]] = {}
    for node in nodes:
        rel = node.get("path", "")
        link_path = f"{prefix}/{rel}" if prefix else rel
        links[node["id"]] = {
            "kind": kind,
            "path": link_path,
            "url": f"https://github.com/{repo}/blob/{ref}/{_encode_path(link_path)}",
        }
    return links, commit


def _under(path: str, base: str) -> bool:
    """Return whether *path* equals or lies under *base*, component by component."""
    p, b = PurePath(path), PurePath(base)
    return p == b or b in p.parents


def _enclosing_git_entries(real_root: str) -> list[str]:
    """Return *real_root* and each ancestor that holds a ``.git`` entry, nearest first."""
    found: list[str] = []
    here = PurePath(real_root)
    for candidate in (here, *here.parents):
        if os.path.lexists(candidate / ".git"):
            found.append(str(candidate))
    return found


def _read_gitdir_target(checkout: str) -> str | None:
    """Return the real path a ``.git`` file's single ``gitdir:`` line names, or None."""
    git_file = Path(checkout) / ".git"
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    if not hasattr(os, "O_NOFOLLOW"):
        return None
    try:
        fd = os.open(git_file, flags)
    except OSError:
        return None
    try:
        if not _stat.S_ISREG(os.fstat(fd).st_mode):
            return None
        data = b""
        while len(data) <= _GITDIR_FILE_LIMIT:
            chunk = os.read(fd, _GITDIR_FILE_LIMIT + 1 - len(data))
            if not chunk:
                break
            data += chunk
    except OSError:
        return None
    finally:
        os.close(fd)
    if len(data) > _GITDIR_FILE_LIMIT:
        return None
    try:
        lines = data.decode("utf-8").splitlines()
    except UnicodeDecodeError:
        return None
    targets = [ln[len("gitdir:"):].strip() for ln in lines if ln.startswith("gitdir:")]
    if len(targets) != 1 or not targets[0]:
        return None
    return os.path.realpath(Path(checkout) / targets[0])


def _list_worktrees(root: Path, anchor: str) -> list[tuple[str, bool]]:
    """Return ``(real path, is_bare)`` for each entry of ``git worktree list``.

    Refuses with ``invalid_destination`` naming *anchor* when Git cannot list.
    """
    unavailable = ViewRefusal(
        "invalid_destination",
        f"cannot confirm the work trees of the repository enclosing {anchor}; "
        "choose a destination after making git available",
    )
    try:
        done = _git_run(root, ["worktree", "list", "--porcelain", "-z"])
    except (OSError, subprocess.SubprocessError):
        raise unavailable from None
    if done.returncode != 0 or not done.stdout:
        raise unavailable
    entries: list[tuple[str, bool]] = []
    for field in done.stdout.decode("utf-8", "surrogateescape").split("\0"):
        if field.startswith("worktree "):
            entries.append((os.path.realpath(field[len("worktree "):]), False))
        elif field == "bare" and entries:
            entries[-1] = (entries[-1][0], True)
    if not entries:
        raise unavailable
    return entries


def _containment_roots(root: Path) -> list[str]:
    """Return every real path the export must not be written under."""
    real_root = os.path.realpath(root)
    roots = [real_root]
    ancestors = _enclosing_git_entries(real_root)
    if not ancestors:
        return roots
    roots.extend(ancestors)
    anchor = ancestors[0]
    entries = _list_worktrees(root, anchor)
    belongs = any(_under(real_root, path) for path, _ in entries)
    if not belongs:
        target = _read_gitdir_target(anchor)
        belongs = target is not None and any(target == path for path, _ in entries)
    if not belongs:
        raise ViewRefusal(
            "invalid_destination",
            f"the work trees git lists do not belong to the repository enclosing {anchor}",
        )
    roots.extend(path for path, bare in entries if not bare)
    return list(dict.fromkeys(roots))


def _containing_root(directory: str, roots: list[str]) -> str | None:
    """Return the containment root *directory* lies under, or None.

    Also compares each ancestor of *directory* by file identity, so a case variant on a
    case-insensitive file system is caught.
    """
    for base in roots:
        if _under(directory, base):
            return base
    here = PurePath(directory)
    for candidate in (here, *here.parents):
        for base in roots:
            try:
                if Path(candidate).samefile(base):
                    return base
            except OSError:
                continue
    return None


def validate_destination(
    root: Path, destination: str | None, name: str | None
) -> Destination:
    """Validate where the export may be written; never creates anything.

    Raises ``ViewRefusal`` with ``invalid_destination`` or ``destination_exists``.
    """
    file_name = name or _dt.datetime.now(tz=_UTC).strftime("intent-graph-%Y%m%dT%H%M%SZ.html")
    if not _NAME_RULE.fullmatch(file_name):
        raise ViewRefusal(
            "invalid_destination",
            "the name must be one path segment matching "
            "^[A-Za-z0-9][A-Za-z0-9._-]{0,99}\\.html$",
        )
    directory = os.path.realpath(destination or tempfile.gettempdir())
    if not Path(directory).is_dir():
        raise ViewRefusal("invalid_destination", "the destination is not an existing directory")
    base = _containing_root(directory, _containment_roots(root))
    if base is not None:
        raise ViewRefusal(
            "invalid_destination",
            f"the destination lies under {base}; choose a directory outside the repository",
        )
    if os.path.lexists(Path(directory) / file_name):
        raise ViewRefusal("destination_exists", "an entry with that name already exists")
    try:
        st = os.lstat(directory)
    except OSError:
        raise ViewRefusal("invalid_destination", "the destination cannot be inspected") from None
    return Destination(directory, file_name, (st.st_dev, st.st_ino))


def _publish_failed() -> ViewRefusal:
    return ViewRefusal("publish_failed", "the file could not be published; nothing was written")


def _same_directory(directory: str, identity: tuple[int, int]) -> bool:
    try:
        st = os.lstat(directory)
    except OSError:
        return False
    return (st.st_dev, st.st_ino) == identity


def publish(html: str, destination: Destination) -> Path:
    """Publish *html* at its final name complete or not at all; return its path.

    Raises ``ViewRefusal``: ``export_too_large``, ``destination_exists``, or
    ``publish_failed``.  Leaves no temporary file on any failure.
    """
    data = html.encode("utf-8")
    if len(data) > EXPORT_BUDGET_BYTES:
        raise ViewRefusal(
            "export_too_large",
            "the view exceeds the export budget; export one intent's subtree with --from",
            limits={"budget_bytes": EXPORT_BUDGET_BYTES, "bounded_route": "--from"},
            observed={"bytes": len(data)},
        )
    supports = getattr(os, "supports_dir_fd", set())
    if (
        not hasattr(os, "O_NOFOLLOW")
        or not hasattr(os, "O_DIRECTORY")
        or os.open not in supports
        or os.link not in supports
    ):
        raise _publish_failed()
    directory, name, identity = destination
    temp_name = f".intent-graph-{os.urandom(8).hex()}.tmp"
    try:
        dir_fd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    except OSError:
        raise _publish_failed() from None
    try:
        st = os.fstat(dir_fd)
        if (st.st_dev, st.st_ino) != identity or not _same_directory(directory, identity):
            raise _publish_failed()
        try:
            fd = os.open(
                temp_name,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                0o600,
                dir_fd=dir_fd,
            )
        except OSError:
            raise _publish_failed() from None
        try:
            try:
                os.fchmod(fd, 0o600)
                view = memoryview(data)
                while view:
                    view = view[os.write(fd, view):]
                os.fsync(fd)
                made = os.fstat(fd)
                if not _stat.S_ISREG(made.st_mode) or made.st_nlink != 1:
                    raise OSError("temporary file is not a single-link regular file")
            finally:
                os.close(fd)
            if not _same_directory(directory, identity):
                raise _publish_failed()
            os.link(temp_name, name, src_dir_fd=dir_fd, dst_dir_fd=dir_fd, follow_symlinks=False)
        except FileExistsError:
            raise ViewRefusal(
                "destination_exists", "an entry with that name already exists"
            ) from None
        except OSError:
            raise _publish_failed() from None
        finally:
            with contextlib.suppress(OSError):
                os.unlink(temp_name, dir_fd=dir_fd)
    finally:
        os.close(dir_fd)
    return Path(directory) / name
