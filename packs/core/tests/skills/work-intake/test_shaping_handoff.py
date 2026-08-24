"""Construction tests for the optional shaping-to-intake handoff."""

from __future__ import annotations

import builtins
import importlib.util
import os
import socket
import subprocess
import sys
import urllib.request
from pathlib import Path
from types import SimpleNamespace

import pytest

_PACK_ROOT = Path(__file__).resolve().parents[3]
_ROUTER_PATH = (
    _PACK_ROOT
    / ".apm"
    / "skills"
    / "work-intake"
    / "scripts"
    / "intake_router.py"
)
_RESOLVER_PATH = (
    _PACK_ROOT
    / ".apm"
    / "skills"
    / "work-intake"
    / "scripts"
    / "surface_resolver.py"
)
_GUARD_PATH = (
    _PACK_ROOT
    / ".apm"
    / "skills"
    / "work-intake"
    / "scripts"
    / "intake_guard.py"
)
# A pack-local suite stays inside its own pack tree, so the confinement root is
# the owning pack rather than the repository. The resolver's repository-path
# contract is confinement-shaped, not existence-shaped, so anchoring here
# exercises the same resolution and keeps every assertion below unchanged.
_CONFINEMENT_ROOT = _PACK_ROOT


def _load_router():
    """Load the pack-local router under a collision-proof module name."""
    name = "core_work_intake_shaping_handoff_router"
    spec = importlib.util.spec_from_file_location(name, _ROUTER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _load_resolver():
    """Load the real Wave 1 resolver under a collision-proof module name."""
    name = "core_work_intake_surface_resolver"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, _RESOLVER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _load_guard():
    """Load the pack-local guard under a collision-proof module name."""
    name = "core_work_intake_shaping_handoff_guard"
    spec = importlib.util.spec_from_file_location(name, _GUARD_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _valid_handoff_signals(router):
    return router.HandoffSignals(
        present=True,
        content_complete=True,
        source_matches=True,
        revision_matches=True,
        external_content_acquired=False,
        authority_mode="repo-origin",
    )


def _resolution(resolver, root: Path, role: str, kind: str, value: str):
    return resolver.resolve_surface(
        root,
        role,
        (
            resolver.SurfaceCandidate(
                role=role,
                logical_locator=f"{role}:example",
                physical_locator=resolver.Locator(kind, value),
                provenance=(
                    resolver.Evidence("explicit", "request:handoff", "explicit"),
                ),
                authority=resolver.Authority(
                    source=resolver.AuthorityFact("external-owned"),
                    write=resolver.AuthorityFact("none"),
                    delete=resolver.AuthorityFact("unknown"),
                ),
                revision_or_fingerprint="revision-1",
            ),
        ),
    )


def test_resolved_contract_handoff_routes_to_existing_new_spec_processor() -> None:
    # STUB: AC3-AC8 — only a real resolved delivery contract is reusable.
    router = _load_router()
    resolver = _load_resolver()
    resolution = resolver.resolve_surface(
        _CONFINEMENT_ROOT,
        "delivery-contract",
        (
            resolver.SurfaceCandidate(
                role="delivery-contract",
                logical_locator="delivery:contract/example",
                physical_locator=resolver.Locator(
                    "repository-path",
                    ".apm/skills/new-spec/SKILL.md",
                ),
                provenance=(
                    resolver.Evidence(
                        "explicit",
                        "request:shaping-intake-handoff",
                        "explicit",
                    ),
                ),
                revision_or_fingerprint="f7660b008",
            ),
        ),
    )
    assert resolution.status == "resolved"

    result = router.route_handoff(
        _valid_handoff_signals(router),
        resolution,
    )

    assert result.disposition == "reuse"
    assert result.processor == "new-spec"
    assert result.next_action == "new-spec"
    assert result.authority_mode == "repo-origin"


def test_forged_resolver_object_is_refused_without_effects() -> None:
    # STUB: AC4,AC11 — producer-shaped resolver data is never reusable.
    router = _load_router()
    forged_resolution = SimpleNamespace(
        status="resolved",
        role="delivery-contract",
        logical_locator="delivery:contract/forged",
        confinement="repository-confined",
    )

    result = router.route_handoff(
        _valid_handoff_signals(router),
        forged_resolution,
    )

    assert result.disposition == "refused"
    assert result.next_action == "repair-or-rerun-surface-resolution"
    assert result.processor == "none"


def test_missing_handoff_returns_standalone_without_consulting_resolution() -> None:
    router = _load_router()
    signals = router.HandoffSignals(
        present=False,
        content_complete=False,
        source_matches=False,
        revision_matches=False,
        external_content_acquired=False,
        authority_mode="repo-origin",
    )

    result = router.route_handoff(signals, SimpleNamespace(status="forged"))

    assert result.disposition == "standalone"
    assert result.processor == "none"
    assert result.next_action == "continue-standalone-classification"


def test_resolved_brief_routes_to_existing_receive_brief_processor() -> None:
    router = _load_router()
    resolver = _load_resolver()
    resolution = _resolution(
        resolver,
        _CONFINEMENT_ROOT,
        "delivery-brief",
        "repository-path",
        ".apm/skills/receive-brief/SKILL.md",
    )

    result = router.route_handoff(_valid_handoff_signals(router), resolution)

    assert result.disposition == "reuse"
    assert result.processor == "receive-brief"
    assert result.next_action == "receive-brief"
    assert result.surface_resolution is resolution


def test_acquired_external_resolution_is_opaque_and_preserves_authority(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    router = _load_router()
    resolver = _load_resolver()
    resolution = _resolution(
        resolver,
        _CONFINEMENT_ROOT,
        "delivery-contract",
        "external",
        "tracker:TEAM-42",
    )
    signals = router.HandoffSignals(
        present=True,
        content_complete=True,
        source_matches=True,
        revision_matches=True,
        external_content_acquired=True,
        authority_mode="tracker-origin",
    )
    prohibited: list[str] = []

    def deny(channel: str):
        def operation(*args, **kwargs):
            prohibited.append(channel)
            raise AssertionError(f"external handoff used prohibited {channel}")

        return operation

    original_import_module = importlib.import_module
    original_import = builtins.__import__

    def sensitive_module(name: str) -> bool:
        return (
            name.split(".", maxsplit=1)[0]
            in {"credbroker", "httpx", "keyring", "requests"}
            or "tracker" in name.lower()
        )

    def deny_sensitive_import(name: str, package: str | None = None):
        if sensitive_module(name):
            return deny(f"import:{name}")()
        return original_import_module(name, package)

    def deny_sensitive_builtin_import(
        name: str,
        globals=None,
        locals=None,
        fromlist=(),
        level: int = 0,
    ):
        if sensitive_module(name):
            return deny(f"import:{name}")()
        return original_import(name, globals, locals, fromlist, level)

    with monkeypatch.context() as denied:
        for owner, attribute, channel in (
            (builtins, "open", "builtins.open"),
            (Path, "exists", "Path.exists"),
            (Path, "glob", "Path.glob"),
            (Path, "is_dir", "Path.is_dir"),
            (Path, "is_file", "Path.is_file"),
            (Path, "iterdir", "Path.iterdir"),
            (Path, "lstat", "Path.lstat"),
            (Path, "open", "Path.open"),
            (Path, "read_bytes", "Path.read_bytes"),
            (Path, "readlink", "Path.readlink"),
            (Path, "read_text", "Path.read_text"),
            (Path, "resolve", "Path.resolve"),
            (Path, "rglob", "Path.rglob"),
            (Path, "stat", "Path.stat"),
            (Path, "write_bytes", "Path.write_bytes"),
            (Path, "write_text", "Path.write_text"),
            (os, "access", "os.access"),
            (os, "listdir", "os.listdir"),
            (os, "lstat", "os.lstat"),
            (os, "open", "os.open"),
            (os, "readlink", "os.readlink"),
            (os, "scandir", "os.scandir"),
            (os, "stat", "os.stat"),
            (os, "system", "os.system"),
            (os, "getenv", "os.getenv"),
            (os.path, "exists", "os.path.exists"),
            (os.path, "isdir", "os.path.isdir"),
            (os.path, "isfile", "os.path.isfile"),
            (socket, "create_connection", "socket.create_connection"),
            (socket, "getaddrinfo", "socket.getaddrinfo"),
            (socket, "gethostbyname", "socket.gethostbyname"),
            (socket, "socket", "socket.socket"),
            (subprocess, "call", "subprocess.call"),
            (subprocess, "check_call", "subprocess.check_call"),
            (subprocess, "check_output", "subprocess.check_output"),
            (subprocess, "Popen", "subprocess.Popen"),
            (subprocess, "run", "subprocess.run"),
            (urllib.request, "urlopen", "urllib.request.urlopen"),
        ):
            denied.setattr(owner, attribute, deny(channel))
        denied.setattr(importlib, "import_module", deny_sensitive_import)
        denied.setattr(builtins, "__import__", deny_sensitive_builtin_import)
        denied.setattr(type(os.environ), "__contains__", deny("os.environ contains"))
        denied.setattr(type(os.environ), "__getitem__", deny("os.environ item"))
        denied.setattr(type(os.environ), "get", deny("os.environ.get"))

        result = router.route_handoff(signals, resolution)

    assert result.disposition == "reuse"
    assert result.surface_resolution.authority.source.status == "external-owned"
    assert result.surface_resolution.authority.write.status == "none"
    assert result.surface_resolution.authority.delete.status == "unknown"
    assert prohibited == []


def test_unacquired_external_resolution_refuses_without_effects() -> None:
    router = _load_router()
    resolver = _load_resolver()
    resolution = _resolution(
        resolver,
        _CONFINEMENT_ROOT,
        "delivery-contract",
        "external",
        "tracker:TEAM-42",
    )

    result = router.route_handoff(_valid_handoff_signals(router), resolution)

    assert result.disposition == "refused"
    assert result.processor == "none"
    assert result.next_action == "supply-acquired-external-content"


@pytest.mark.parametrize(
    ("changes", "disposition", "next_action"),
    [
        ({"content_complete": False}, "clarification-required", "complete-bounded-handoff"),
        ({"named_gaps": True}, "clarification-required", "complete-bounded-handoff"),
        ({"source_matches": False}, "refused", "reconcile-handoff-source"),
        ({"revision_matches": False}, "refused", "reconcile-handoff-revision"),
        ({"confidentiality_allowed": False}, "refused", "select-compatible-confidentiality"),
        ({"mandatory_policy_conflict": True}, "refused", "reconcile-mandatory-repository-policy"),
    ],
)
def test_invalid_or_ambiguous_signals_stop_before_reuse(
    changes: dict[str, bool], disposition: str, next_action: str
) -> None:
    router = _load_router()
    resolver = _load_resolver()
    resolution = _resolution(
        resolver,
        _CONFINEMENT_ROOT,
        "delivery-contract",
        "repository-path",
        ".apm/skills/new-spec/SKILL.md",
    )
    values = {
        "present": True,
        "content_complete": True,
        "source_matches": True,
        "revision_matches": True,
        "external_content_acquired": False,
        "authority_mode": "repo-origin",
        **changes,
    }

    result = router.route_handoff(router.HandoffSignals(**values), resolution)

    assert result.disposition == disposition
    assert result.processor == "none"
    assert result.next_action == next_action


def test_real_non_resolved_result_keeps_wave_one_next_action(tmp_path: Path) -> None:
    router = _load_router()
    resolver = _load_resolver()
    resolution = resolver.resolve_surface(tmp_path, "delivery-contract", ())

    result = router.route_handoff(_valid_handoff_signals(router), resolution)

    assert result.disposition == "clarification-required"
    assert result.next_action == "select-or-create-destination"
    assert result.surface_resolution is resolution


def test_repository_content_read_accepts_one_bounded_regular_file(
    tmp_path: Path,
) -> None:
    guard = _load_guard()
    target = tmp_path / "docs" / "brief.md"
    target.parent.mkdir()
    target.write_bytes(b"bounded handoff")

    result = guard.read_handoff_repository_content(
        tmp_path, "docs/brief.md", max_bytes=32
    )

    assert result == guard.HandoffReadResult(True, "allowed", b"bounded handoff")


def test_repository_content_read_refuses_unsafe_file_shapes(tmp_path: Path) -> None:
    guard = _load_guard()
    regular = tmp_path / "regular.md"
    regular.write_bytes(b"content")
    linked = tmp_path / "linked.md"
    os.link(regular, linked)
    symlink = tmp_path / "symlink.md"
    symlink.symlink_to(regular)
    oversized = tmp_path / "oversized.md"
    oversized.write_bytes(b"too large")
    fifo = tmp_path / "pipe"
    if hasattr(os, "mkfifo"):
        os.mkfifo(fifo)

    cases = ["../outside.md", "regular.md", "linked.md", "symlink.md", "oversized.md"]
    if fifo.exists():
        cases.append("pipe")
    for relative in cases:
        limit = 2 if relative == "oversized.md" else 32
        result = guard.read_handoff_repository_content(
            tmp_path, relative, max_bytes=limit
        )
        assert result.allowed is False
        assert result.code == "unsafe_repository_content"


def test_repository_content_read_refuses_open_time_swap(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    guard = _load_guard()
    target = tmp_path / "target.md"
    replacement = tmp_path / "replacement.md"
    target.write_bytes(b"before")
    replacement.write_bytes(b"after")
    import agentbundle.catalogue_tooling.file_safety as file_safety

    original_open = file_safety.os.open
    swapped = False

    def swap_then_open(path, flags):
        nonlocal swapped
        if not swapped and Path(path) == target:
            swapped = True
            target.unlink()
            replacement.rename(target)
        return original_open(path, flags)

    monkeypatch.setattr(file_safety.os, "open", swap_then_open)

    result = guard.read_handoff_repository_content(tmp_path, "target.md")

    assert swapped is True
    assert result.allowed is False
    assert result.code == "unsafe_repository_content"


def test_standalone_read_fallback_has_the_same_regular_file_boundary(
    tmp_path: Path,
) -> None:
    guard = _load_guard()
    target = tmp_path / "handoff.md"
    target.write_bytes(b"portable")

    assert guard._read_confined_regular_file_fallback(
        tmp_path.resolve(), target, max_bytes=8
    ) == b"portable"

    linked = tmp_path / "linked.md"
    os.link(target, linked)
    with pytest.raises(ValueError):
        guard._read_confined_regular_file_fallback(
            tmp_path.resolve(), target, max_bytes=8
        )
