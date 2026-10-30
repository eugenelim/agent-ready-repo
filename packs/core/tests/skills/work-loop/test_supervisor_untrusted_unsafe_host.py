"""Every verb refuses untrusted or undetermined code on a host without race-free writes.

The host query is patched false on the module the supervisor loads, so a real
descriptor-walk host drives the refusal paths, and a refusal writes nothing.
"""

from __future__ import annotations

import hashlib
import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

_HELPER_PATHS = {
    "supervisor_harness": Path(__file__).resolve().parent / "supervisor_harness.py",
    "supervisor_support": Path(__file__).resolve().parent / "supervisor_support.py",
}


def _helper(name: str) -> ModuleType:
    """Load a shared supervisor test helper by path under a pack- and skill-qualified name."""
    alias = f"core_work_loop_{name}"
    if alias not in sys.modules:
        spec = importlib.util.spec_from_file_location(alias, _HELPER_PATHS[name])
        assert spec is not None and spec.loader is not None
        sys.modules[alias] = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(sys.modules[alias])
    return sys.modules[alias]


h = _helper("supervisor_harness")
sup = _helper("supervisor_support")

pytestmark = sup.INTEGRATION

OWNER = "owner:0123456789ab"
REVIEWER = "plan-reviewer:0123456789ab"
CODE = "untrusted-unsafe-host"


def _verbs() -> list[str]:
    parser = h.cli._parser()
    (action,) = [a for a in parser._actions if getattr(a, "choices", None)]
    return sorted(action.choices)


def _argv(repo: Path, verb: str, tmp_path: Path, trust: str = "untrusted") -> list[str]:
    spec = h.SPEC_DIR
    if verb == "start":
        return ["start", spec, "--intent", "code", "--code-trust", trust,
                "--authority-ref", OWNER, "--review-authority-ref", REVIEWER]
    if verb == "report":
        result = tmp_path / "result.json"
        result.write_text("{}", encoding="utf-8")
        return ["report", spec, str(result)]
    if verb == "resolve-effect":
        return ["resolve-effect", spec, "--operation", "op", "--decision", "approve",
                "--authority-ref", OWNER]
    return [verb, spec]


def _snapshot(repo: Path) -> dict[str, tuple[int, str]]:
    found: dict[str, tuple[int, str]] = {}
    for path in sorted(repo.rglob("*")):
        if path.is_file() and not path.is_symlink():
            data = path.read_bytes()
            found[path.relative_to(repo).as_posix()] = (len(data), hashlib.sha256(data).hexdigest())
    return found


@pytest.fixture
def query() -> object:
    """The module the supervisor reads the host query from."""
    return h.commit_module.sibling("_confined_mutation.py")


def _race_free(monkeypatch: pytest.MonkeyPatch, query: object, value: bool) -> None:
    monkeypatch.setattr(query, "race_free_mutation", lambda: value)


def _refused(repo: Path, argv: list[str]) -> None:
    before = _snapshot(repo)
    code, out = h.run_cli(repo, *argv)
    assert code == 1, out
    assert out["refusal"]["code"] == CODE, out
    assert _snapshot(repo) == before


def _admit(repo: Path, tmp_path: Path, trust: str) -> dict:
    code, out = h.run_cli(repo, *_argv(repo, "start", tmp_path, trust))
    assert code == 0, out
    return out


def _commit_approvals(repo: Path, text: str) -> None:
    target = repo / h.SPEC_DIR / "delivery"
    target.mkdir(parents=True, exist_ok=True)
    (target / "approvals.jsonl").write_text(text, encoding="utf-8")
    h.git(repo, "add", "-A")
    h.git(repo, "commit", "-q", "-m", "approvals")


def test_verb_list_is_read_from_the_parser() -> None:
    assert {"start", "next", "report", "status", "resolve-effect"} <= set(_verbs())


def test_start_untrusted_refuses(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, query: object) -> None:
    repo = h.make_repo(tmp_path)
    _race_free(monkeypatch, query, False)
    _refused(repo, _argv(repo, "start", tmp_path, "untrusted"))


def test_every_verb_refuses_a_resumed_untrusted_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, query: object
) -> None:
    repo = h.make_repo(tmp_path)
    _admit(repo, tmp_path, "untrusted")
    _race_free(monkeypatch, query, False)
    for verb in _verbs():
        _refused(repo, _argv(repo, verb, tmp_path))


def test_malformed_approvals_at_head_refuse(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, query: object
) -> None:
    repo = h.make_repo(tmp_path)
    _commit_approvals(repo, "{not json\n")
    _race_free(monkeypatch, query, False)
    for verb in _verbs():
        if verb != "start":
            _refused(repo, _argv(repo, verb, tmp_path))


def test_working_copy_saying_trusted_does_not_override_head(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, query: object
) -> None:
    repo = h.make_repo(tmp_path)
    _admit(repo, tmp_path, "untrusted")
    path = repo / h.SPEC_DIR / "delivery" / "approvals.jsonl"
    path.write_text(path.read_text(encoding="utf-8").replace('"untrusted"', '"trusted"'),
                    encoding="utf-8")
    _race_free(monkeypatch, query, False)
    for verb in _verbs():
        if verb != "start":
            _refused(repo, _argv(repo, verb, tmp_path))


def test_reapproval_to_untrusted_over_trusted_head_refuses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, query: object
) -> None:
    repo = h.make_repo(tmp_path)
    _admit(repo, tmp_path, "trusted")
    _race_free(monkeypatch, query, False)
    _refused(repo, _argv(repo, "start", tmp_path, "untrusted"))


def test_reapproval_to_trusted_over_untrusted_head_proceeds(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, query: object
) -> None:
    repo = h.make_repo(tmp_path)
    _admit(repo, tmp_path, "untrusted")
    _race_free(monkeypatch, query, False)
    code, out = h.run_cli(repo, *_argv(repo, "start", tmp_path, "trusted"))
    assert code == 0 and out["status"] == "admitted" and out["sequence"] == 2, out


def test_next_without_approvals_at_head_refuses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, query: object
) -> None:
    repo = h.make_repo(tmp_path)
    _race_free(monkeypatch, query, False)
    _refused(repo, _argv(repo, "next", tmp_path))


def test_trusted_run_proceeds(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, query: object) -> None:
    repo = h.make_repo(tmp_path)
    _race_free(monkeypatch, query, False)
    out = _admit(repo, tmp_path, "trusted")
    assert out["status"] == "admitted"
    code, payload = h.run_cli(repo, "next", h.SPEC_DIR)
    assert payload.get("refusal", {}).get("code") != CODE
    code, status = h.run_cli(repo, "status", h.SPEC_DIR)
    assert code == 0 and status["refusal"] in ({}, None)


def test_untrusted_run_proceeds_when_the_host_is_race_free(tmp_path: Path) -> None:
    repo = h.make_repo(tmp_path)
    assert _admit(repo, tmp_path, "untrusted")["status"] == "admitted"


# ── the refusal says why ─────────────────────────────────────────────────────


def _detail(repo: Path, argv: list[str]) -> str:
    code, out = h.run_cli(repo, *argv)
    assert code == 1 and out["refusal"]["code"] == CODE, out
    return out["refusal"]["detail"]


def test_detail_names_untrusted_when_head_says_untrusted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, query: object
) -> None:
    repo = h.make_repo(tmp_path)
    _admit(repo, tmp_path, "untrusted")
    _race_free(monkeypatch, query, False)
    detail = _detail(repo, _argv(repo, "next", tmp_path))
    assert '"untrusted"' in detail and "undetermined" not in detail


def test_detail_names_untrusted_for_start(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, query: object
) -> None:
    repo = h.make_repo(tmp_path)
    _race_free(monkeypatch, query, False)
    assert '"untrusted"' in _detail(repo, _argv(repo, "start", tmp_path, "untrusted"))


def test_detail_names_absent(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, query: object) -> None:
    repo = h.make_repo(tmp_path)
    _race_free(monkeypatch, query, False)
    detail = _detail(repo, _argv(repo, "next", tmp_path))
    assert '"undetermined"' in detail and "absent" in detail


def test_detail_names_malformed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, query: object
) -> None:
    repo = h.make_repo(tmp_path)
    _commit_approvals(repo, "{not json\n")
    _race_free(monkeypatch, query, False)
    detail = _detail(repo, _argv(repo, "next", tmp_path))
    assert '"undetermined"' in detail and "malformed" in detail


def test_detail_names_unknown_value(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, query: object
) -> None:
    repo = h.make_repo(tmp_path)
    _admit(repo, tmp_path, "trusted")
    path = repo / h.SPEC_DIR / "delivery" / "approvals.jsonl"
    path.write_text(path.read_text(encoding="utf-8").replace('"trusted"', '"bogus"'),
                    encoding="utf-8")
    h.git(repo, "add", "-A")
    h.git(repo, "commit", "-q", "-m", "tamper")
    _race_free(monkeypatch, query, False)
    detail = _detail(repo, _argv(repo, "next", tmp_path))
    assert '"undetermined"' in detail and "unknown value" in detail


def test_git_error_is_named_and_logged_as_unverifiable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, query: object
) -> None:
    repo = h.make_repo(tmp_path)
    _admit(repo, tmp_path, "untrusted")
    _race_free(monkeypatch, query, False)
    git_error = h.commit_module.SupervisorGitError

    def broken(self: object, *a: object, **k: object) -> bytes:
        raise git_error("denied-git-control-state", "control state changed", unverifiable=True)

    monkeypatch.setattr(h.commit_module.GitPort, "show", broken)
    detail = _detail(repo, _argv(repo, "next", tmp_path))
    assert '"undetermined"' in detail and "git" in detail.lower()
    log = (repo / h.SPEC_DIR / ".supervisor" / "security-events.jsonl").read_text(encoding="utf-8")
    assert "denied-git-control-state" in log
