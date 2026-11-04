"""Construction tests for the ``git-history`` evidence entry.

Mode: TDD (proof-by-run-evidence plan T3). Each test builds a temporary
repository with a bare ``origin``, drives ``evidence-gate.py``'s ``main`` and
records every argument vector handed to ``_supervisor_git._launch``.
"""

from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import os
import subprocess
from collections.abc import Callable, Iterator
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

SCRIPTS = Path(__file__).resolve().parents[3] / ".apm" / "skills" / "work-loop" / "scripts"
ALLOWED = {"rev-parse", "symbolic-ref", "merge-base", "diff", "cat-file", "show", "log"}
HELPER_ONLY = {"version", "config"}
_FLAG_WITH_VALUE = {"-c"}
_FLAG_ONLY_PREFIXES = ("--git-dir=", "--work-tree=", "--no-replace-objects", "--literal-pathspecs")
CAP = 256 * 1024
MIB = 1024 * 1024


def _load(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, str(path))
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def gate() -> ModuleType:
    """The shipped CLI, loaded once under a name unique to this suite."""
    return _load("work_loop_test_evidence_gate", SCRIPTS / "evidence-gate.py")


def subcommand(argv: list[str]) -> str:
    """The Git subcommand of one helper argument vector."""
    index = 1
    while index < len(argv):
        token = argv[index]
        if token in _FLAG_WITH_VALUE:
            index += 2
        elif token.startswith(_FLAG_ONLY_PREFIXES):
            index += 1
        else:
            return token
    raise AssertionError(f"no subcommand in {argv}")


def is_pinning_or_config(argv: list[str]) -> bool:
    """True for the helper's own version, discovery, and config reads."""
    sub = subcommand(argv)
    if sub in HELPER_ONLY:
        return True
    return sub == "rev-parse" and "--show-toplevel" in argv and "--git-common-dir" in argv


class Launches(list[list[str]]):
    """Recorded Git vectors; a test of a refusal made before the first launch sets ``expect_empty``."""

    expect_empty = False
    version_output: bytes | None = None

    def __init__(self) -> None:
        super().__init__()
        self.envs: list[dict[str, str]] = []


def run_launches(launches: Launches) -> list[dict[str, str]]:
    """The environments of the launches made through ``HardenedGit.run``."""
    return [
        env for argv, env in zip(launches, launches.envs, strict=True)
        if any(a.startswith("--work-tree=") for a in argv)
    ]


def version_launches(launches: Launches) -> list[list[str]]:
    return [a for a in launches if subcommand(a) == "version"]


@pytest.fixture
def launches(gate: ModuleType, monkeypatch: pytest.MonkeyPatch) -> Iterator[Launches]:
    """Record every launched vector; at teardown assert the set stays inside the allowed forms."""
    module = gate.supervisor_git()
    recorded = Launches()
    real = module._launch

    def spy(argv: list[str], **kwargs: Any) -> Any:
        recorded.append(list(argv))
        recorded.envs.append(dict(kwargs["env"]))
        if recorded.version_output is not None and subcommand(argv) == "version":
            return subprocess.CompletedProcess(argv, 0, recorded.version_output, b"")
        return real(argv, **kwargs)

    monkeypatch.setattr(module, "_launch", spy)
    yield recorded
    if recorded.expect_empty:
        assert recorded == [], "a refusal made before the first launch launched Git"
    else:
        assert recorded, "no Git launch was recorded"
    for argv in recorded:
        if is_pinning_or_config(argv):
            continue
        sub = subcommand(argv)
        assert sub in ALLOWED, argv
        if sub == "diff":
            assert {"--name-only", "-z", "--no-renames"} <= set(argv), argv


def git(cwd: Path, *args: str, stdin: bytes | None = None) -> str:
    env = {
        **{k: v for k, v in os.environ.items() if not k.startswith("GIT_")},
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_AUTHOR_NAME": "T", "GIT_AUTHOR_EMAIL": "t@example.invalid",
        "GIT_COMMITTER_NAME": "T", "GIT_COMMITTER_EMAIL": "t@example.invalid",
    }
    done = subprocess.run(
        ["git", *args], cwd=cwd, env=env, input=stdin, capture_output=True, check=True
    )
    return done.stdout.decode("utf-8", "replace").strip()


def commit_file(repo: Path, name: str, data: bytes | str, message: str = "c") -> str:
    target = repo / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data if isinstance(data, bytes) else data.encode())
    git(repo, "--literal-pathspecs", "add", "-f", "--", name)
    git(repo, "commit", "-q", "-m", message)
    return git(repo, "rev-parse", "HEAD")


class Repo:
    """A clone of a bare origin with ``origin/HEAD`` set and a pushed base commit."""

    def __init__(self, root: Path) -> None:
        self.origin = root / "origin.git"
        self.path = root / "work"
        git(root, "init", "-q", "--bare", "-b", "main", str(self.origin))
        self.path.mkdir()
        git(self.path, "init", "-q", "-b", "main")
        git(self.path, "remote", "add", "origin", str(self.origin))
        commit_file(self.path, "kept_untouched_zq.txt", "untouched\n")
        commit_file(self.path, "mod_target_zq.txt", "base content\n")
        commit_file(self.path, "-dash_zq", "dash base\n")
        self.base = commit_file(self.path, ":(glob)star_zq*", "magic base\n")
        git(self.path, "push", "-q", "origin", "main")
        git(self.path, "remote", "set-head", "origin", "--auto")
        git(self.path, "checkout", "-q", "-b", "topic")

    def commit(self, name: str, data: bytes | str, message: str = "c") -> str:
        return commit_file(self.path, name, data, message)


@pytest.fixture
def repo(tmp_path: Path) -> Repo:
    return Repo(tmp_path)


@pytest.fixture
def run(gate: ModuleType, repo: Repo, launches: Launches,
        capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch) -> Callable[..., Any]:
    """Run ``main`` inside the repository and return ``(exit code, parsed stdout)``."""
    monkeypatch.chdir(repo.path)

    def invoke(*argv: str) -> tuple[int, dict[str, Any]]:
        code = gate.main(["git-history", *argv])
        out = capsys.readouterr().out
        return code, json.loads(out)

    return invoke


def never_launched(launches: Launches, value: str) -> None:
    assert value
    assert not [a for a in launches if any(value in element for element in a)], value


def non_helper(launches: Launches) -> list[list[str]]:
    return [a for a in launches if not is_pinning_or_config(a)]


def subcommands(launches: Launches) -> list[str]:
    return [subcommand(a) for a in non_helper(launches)]


# ── happy paths ─────────────────────────────────────────────────────────────


def test_t3_added_path_is_absent_at_base_with_its_commit(
    run: Callable[..., Any], repo: Repo
) -> None:
    added = repo.commit("added_file_zq.txt", "new\n", "add it")
    code, out = run("--path", "added_file_zq.txt")
    assert code == 0
    assert out["gate_id"] == "git-history"
    assert out["present_at_base"] is False
    assert out["commits"] == [added]
    assert out["log_truncated"] is False
    assert out["change_base"] == repo.base
    assert out["subject_commit"] == added
    assert out["isolation"] == "git-object-store"
    assert out["network"] == "no-remote-objects"
    assert out["exit_status"] == 0
    assert out["timeout_s"] == 60.0
    assert out["cwd"] == str(repo.path.resolve())


def test_t3_envelope_hashes_each_vector_and_the_environment(
    gate: ModuleType, run: Callable[..., Any], repo: Repo
) -> None:
    repo.commit("added_file_zq.txt", "new\n")
    _, out = run("--path", "added_file_zq.txt")
    assert out["environment_sha256"] == hashlib.sha256(
        json.dumps(
            gate.supervisor_git().hardened_env(no_lazy_fetch=True),
            sort_keys=True, separators=(",", ":"), ensure_ascii=True,
        ).encode("ascii")
    ).hexdigest()
    assert len(out["argv_sha256"]) >= 5
    assert all(len(h) == 64 for h in out["argv_sha256"])


def test_t15_every_run_launch_shares_the_hashed_environment(
    run: Callable[..., Any], launches: Launches, repo: Repo
) -> None:
    repo.commit("added_file_zq.txt", "new\n")
    _, out = run("--path", "added_file_zq.txt")
    envs = run_launches(launches)
    assert len(envs) >= 5 and all(env == envs[0] for env in envs)
    canonical = json.dumps(envs[0], sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    assert out["environment_sha256"] == hashlib.sha256(canonical.encode("ascii")).hexdigest()


def test_t15_success_path_pins_once_and_never_lazy_fetches(
    run: Callable[..., Any], launches: Launches, repo: Repo
) -> None:
    repo.commit("added_file_zq.txt", "new\n")
    code, _ = run("--path", "added_file_zq.txt")
    assert code == 0
    assert non_helper(launches)
    assert len(version_launches(launches)) == 1
    envs = run_launches(launches)
    assert envs and all(env.get("GIT_NO_LAZY_FETCH") == "1" for env in envs)


@pytest.mark.parametrize("reported", [b"git version 2.40.0\n", b"git version 2.31.1\n"])
def test_t15_old_git_is_refused_before_any_non_helper_launch(
    run: Callable[..., Any], launches: Launches, repo: Repo, reported: bytes
) -> None:
    repo.commit("added_file_zq.txt", "new\n")
    launches.version_output = reported
    code, out = run("--path", "added_file_zq.txt")
    assert (code, out["refused"]) == (2, "denied-git-version")
    assert len(version_launches(launches)) == 1
    _only_helper_reads(launches)


def test_t15_helper_without_the_opt_in_passes_no_lazy_fetch_variable(
    gate: ModuleType, launches: Launches, repo: Repo
) -> None:
    helper = gate.supervisor_git().HardenedGit(repo.path)
    helper.run("rev-parse", "HEAD")
    envs = run_launches(launches)
    assert envs and all("GIT_NO_LAZY_FETCH" not in env for env in envs)
    assert helper.git_version >= (2, 32)
    assert len(version_launches(launches)) == 1


def test_t3_modified_path_present_with_base_content(
    run: Callable[..., Any], repo: Repo
) -> None:
    modified = repo.commit("mod_target_zq.txt", "changed\n")
    code, out = run("--path", "mod_target_zq.txt", "--base", repo.base)
    assert code == 0
    assert out["present_at_base"] is True
    assert out["content"] == "base content\n"
    assert out["truncated"] is False
    assert out["commits"] == [modified]
    assert out["blob_id"] == git(repo.path, "rev-parse", f"{repo.base}:mod_target_zq.txt")


def test_t3_log_is_bounded_at_fifty_commits(
    run: Callable[..., Any], launches: Launches, repo: Repo
) -> None:
    for number in range(51):
        repo.commit("busy_zq.txt", f"v{number}\n")
    code, out = run("--path", "busy_zq.txt")
    assert code == 0
    assert len(out["commits"]) == 50
    assert out["log_truncated"] is True
    log = [a for a in launches if subcommand(a) == "log"]
    assert len(log) == 1
    assert "--max-count=51" in log[0] and "--format=%H" in log[0]


# ── refusals ────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "path", ["../distinct_traversal_zq", "/distinct_absolute_zq", "kept_untouched_zq.txt"]
)
def test_t3_path_outside_the_change_set_is_refused(
    run: Callable[..., Any], launches: Launches, repo: Repo, path: str
) -> None:
    repo.commit("something_else_zq.txt", "x\n")
    code, out = run("--path", path)
    assert (code, out["refused"]) == (2, "denied-path-not-in-change")
    never_launched(launches, path)
    never_launched(launches, path.lstrip("./"))


def test_t3_context_path_refused_even_when_committed(
    run: Callable[..., Any], launches: Launches, repo: Repo
) -> None:
    repo.commit(".context/notes_zq.txt", "secret\n")
    code, out = run("--path", ".context/notes_zq.txt")
    assert (code, out["refused"]) == (2, "denied-artifact-path")
    launches.expect_empty = True
    never_launched(launches, "notes_zq")
    assert not {"cat-file", "show", "log"} & set(subcommands(launches))


@pytest.mark.parametrize(
    "suffix", ["^", "~1", "..HEAD", ":x", "^{}", "\n"]
)
def test_t3_malformed_full_id_is_refused(
    run: Callable[..., Any], launches: Launches, repo: Repo, suffix: str
) -> None:
    repo.commit("added_file_zq.txt", "new\n")
    supplied = repo.base + suffix
    code, out = run("--path", "added_file_zq.txt", "--base", supplied)
    assert (code, out["refused"]) == (2, "denied-ref-form")
    launches.expect_empty = True
    never_launched(launches, repo.base)


@pytest.mark.parametrize("kind", ["symbolic", "short", "dash"])
def test_t3_non_id_base_is_refused(
    run: Callable[..., Any], launches: Launches, repo: Repo, kind: str
) -> None:
    repo.commit("added_file_zq.txt", "new\n")
    supplied = {"symbolic": "topic_distinct_zq", "short": repo.base[:12],
                "dash": "-" + repo.base[1:]}[kind]
    code, out = run("--path", "added_file_zq.txt", f"--base={supplied}")
    assert (code, out["refused"]) == (2, "denied-ref-form")
    launches.expect_empty = True
    never_launched(launches, supplied)


def test_t3_base_outside_history_or_older_is_refused(
    run: Callable[..., Any], launches: Launches, repo: Repo
) -> None:
    first = git(repo.path, "rev-parse", "HEAD~3")
    repo.commit("added_file_zq.txt", "new\n")
    git(repo.path, "checkout", "-q", "--orphan", "stray")
    outside = commit_file(repo.path, "stray_zq.txt", "s\n")
    git(repo.path, "checkout", "-q", "topic")
    for supplied in (outside, first):
        code, out = run("--path", "added_file_zq.txt", "--base", supplied)
        assert (code, out["refused"]) == (2, "denied-ref-outside-subject-history")
        never_launched(launches, supplied)


def test_t3_missing_origin_head_is_refused_before_path_work(
    run: Callable[..., Any], launches: Launches, repo: Repo
) -> None:
    repo.commit("added_file_zq.txt", "new\n")
    git(repo.path, "remote", "set-head", "origin", "--delete")
    code, out = run("--path", "added_file_zq.txt")
    assert (code, out["refused"]) == (2, "denied-no-change-base")
    assert "git remote set-head origin --auto" in out["detail"]
    assert not {"diff", "cat-file", "show", "log"} & set(subcommands(launches))


@pytest.mark.parametrize(
    "argv",
    [
        ["--path", "a", "extra"],
        ["--path", "a", "--unknown", "x"],
        ["--path", "a", "--path", "b"],
        ["--path", "a", "--base", "b" * 40, "--base", "b" * 40],
        [],
        ["--base", "b" * 40],
        ["--pat", "a"],
    ],
)
def test_t3_unrecognized_arguments_refuse_before_any_launch(
    gate: ModuleType, repo: Repo, launches: Launches,
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch, argv: list[str],
) -> None:
    monkeypatch.chdir(repo.path)
    code = gate.main(["git-history", *argv])
    assert (code, json.loads(capsys.readouterr().out)["refused"]) == (2, "denied-not-in-catalog")
    assert launches == []
    launches.expect_empty = True


def test_t3_subcommands_are_exactly_two(
    gate: ModuleType, capsys: pytest.CaptureFixture[str]
) -> None:
    assert gate.main(["frobnicate"]) == 2
    assert json.loads(capsys.readouterr().out)["refused"] == "denied-not-in-catalog"
    assert gate.main([]) == 2
    assert json.loads(capsys.readouterr().out)["refused"] == "denied-not-in-catalog"
    assert gate.SUBCOMMANDS == ("proof-run", "git-history")


def _only_helper_reads(launches: Launches) -> None:
    assert launches
    assert all(is_pinning_or_config(a) for a in launches), non_helper(launches)


def test_t3_alternates_file_is_refused(
    run: Callable[..., Any], launches: Launches, repo: Repo
) -> None:
    repo.commit("added_file_zq.txt", "new\n")
    info = repo.path / ".git" / "objects" / "info"
    info.mkdir(parents=True, exist_ok=True)
    (info / "alternates").write_text(str(repo.origin / "objects") + "\n")
    code, out = run("--path", "added_file_zq.txt")
    assert (code, out["refused"]) == (2, "denied-object-source")
    _only_helper_reads(launches)


@pytest.mark.parametrize(
    "setting", [("extensions.partialClone", "origin"), ("remote.origin.promisor", "true")]
)
def test_t3_partial_clone_settings_are_refused(
    run: Callable[..., Any], launches: Launches, repo: Repo, setting: tuple[str, str]
) -> None:
    repo.commit("added_file_zq.txt", "new\n")
    git(repo.path, "config", *setting)
    code, out = run("--path", "added_file_zq.txt")
    assert (code, out["refused"]) == (2, "denied-object-source")
    _only_helper_reads(launches)


def _plant_marker_uploadpack(repo: Repo) -> Path:
    marker = repo.path.parent / "uploadpack-ran"
    script = repo.path.parent / "uploadpack.sh"
    script.write_text(f"#!/bin/sh\necho ran >> '{marker}'\nexit 1\n")
    script.chmod(0o755)
    git(repo.path, "config", "remote.origin.uploadpack", str(script))
    return marker


@pytest.mark.parametrize(
    "setting",
    [
        ("extensions.partialClone", ""),
        ("remote.origin.partialclonefilter", "blob:none"),
        ("remote.origin.partialclonefilter", ""),
    ],
    ids=["empty-partial-clone", "filter-blob-none", "filter-empty"],
)
def test_t15_partial_clone_forms_are_refused_before_any_non_helper_launch(
    run: Callable[..., Any], launches: Launches, repo: Repo, setting: tuple[str, str]
) -> None:
    repo.commit("added_file_zq.txt", "new\n")
    marker = _plant_marker_uploadpack(repo)
    git(repo.path, "config", *setting)
    code, out = run("--path", "added_file_zq.txt")
    assert (code, out["refused"]) == (2, "denied-object-source")
    assert not marker.exists()
    _only_helper_reads(launches)


def _craft_signed_head(repo: Repo, armor: str) -> None:
    """Rewrite HEAD as the same commit carrying a ``gpgsig`` header with the given armor."""
    lines = armor.splitlines()
    header = "gpgsig " + "\n ".join(line or "" for line in lines) + "\n"
    body = git(repo.path, "cat-file", "commit", "HEAD")
    head, _, message = body.partition("\n\n")
    crafted = f"{head}\n{header}\n{message}\n"
    new = git(repo.path, "hash-object", "-t", "commit", "-w", "--stdin", stdin=crafted.encode())
    git(repo.path, "update-ref", "HEAD", new)


_ARMORS = {
    "gpg": "-----BEGIN PGP SIGNATURE-----\n\niQEzBAABCAAdFiEEAAAAAAAAAAAAAAAAAAAAAAAAAAAFAmAAAAAACgkQAAAAAAAA\n"
           "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA==\n=AAAA\n"
           "-----END PGP SIGNATURE-----",
    "gpgsm": "-----BEGIN SIGNED MESSAGE-----\nMIAGCSqGSIb3DQEHAqCAMIACAQExDzANBglghkgBZQMEAgEFADCABgkqhkiG9w0B\n"
             "BwEAAAAAAAA=\n-----END SIGNED MESSAGE-----",
    "ssh-keygen": "-----BEGIN SSH SIGNATURE-----\nU1NIU0lHAAAAAQAAADMAAAALc3NoLWVkMjU1MTkAAAAgAAAAAAAAAAAAAAAAAAAA\n"
                  "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=\n-----END SIGNATURE-----",
}


@pytest.mark.parametrize("verifier", ["gpg", "gpgsm", "ssh-keygen"])
def test_t15_signature_verifier_never_runs(
    run: Callable[..., Any], repo: Repo, tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch, verifier: str
) -> None:
    stubs = tmp_path / "stubs"
    stubs.mkdir()
    marker = tmp_path / f"{verifier}-ran"
    stub = stubs / verifier
    stub.write_text(f"#!/bin/sh\necho ran >> '{marker}'\nexit 1\n")
    stub.chmod(0o755)
    monkeypatch.setenv("PATH", f"{stubs}{os.pathsep}{os.environ['PATH']}")
    repo.commit("signed_file_zq.txt", "new\n")
    _craft_signed_head(repo, _ARMORS[verifier])
    git(repo.path, "config", "log.showSignature", "true")
    if verifier == "ssh-keygen":
        signers = tmp_path / "allowed_signers"
        signers.write_text("")
        git(repo.path, "config", "gpg.ssh.allowedSignersFile", str(signers))
    git(repo.path, "log", "--format=%H", "--", "signed_file_zq.txt")
    if not marker.exists():
        pytest.skip(f"the fixture cannot make git launch the {verifier} stub on this host")
    marker.unlink()
    code, out = run("--path", "signed_file_zq.txt")
    assert code == 0, out
    assert len(out["commits"]) == 1
    assert not marker.exists()


def test_t3_code_running_config_is_refused(
    run: Callable[..., Any], launches: Launches, repo: Repo
) -> None:
    repo.commit("added_file_zq.txt", "new\n")
    git(repo.path, "config", "gpg.program", "/bin/false")
    git(repo.path, "config", "log.showSignature", "true")
    code, out = run("--path", "added_file_zq.txt")
    assert (code, out["refused"]) == (2, "denied-git-config")
    _only_helper_reads(launches)


# ── bounds and inert forms ──────────────────────────────────────────────────


def test_t3_large_base_blob_is_truncated_without_show(
    run: Callable[..., Any], launches: Launches, repo: Repo
) -> None:
    repo.base = commit_file(repo.path, "big_zq.bin", b"x" * (CAP + 1))
    git(repo.path, "push", "-q", "origin", "topic:main")
    git(repo.path, "fetch", "-q", "origin")
    git(repo.path, "remote", "set-head", "origin", "--auto")
    repo.commit("big_zq.bin", b"small\n")
    code, out = run("--path", "big_zq.bin")
    assert code == 0
    assert out["present_at_base"] is True and out["truncated"] is True
    assert out["size"] == CAP + 1
    assert out["blob_id"] == git(repo.path, "rev-parse", f"{out['change_base']}:big_zq.bin")
    assert "content" not in out
    assert "show" not in subcommands(launches)
    assert len(json.dumps(out).encode()) <= MIB


def test_t3_invalid_utf8_content_never_exceeds_the_envelope_bound(
    run: Callable[..., Any], repo: Repo
) -> None:
    repo.base = commit_file(repo.path, "bin_zq.bin", b"\xff" * CAP)
    git(repo.path, "push", "-q", "origin", "topic:main")
    git(repo.path, "fetch", "-q", "origin")
    git(repo.path, "remote", "set-head", "origin", "--auto")
    repo.commit("bin_zq.bin", b"small\n")
    code, out = run("--path", "bin_zq.bin")
    assert code == 0
    assert len(json.dumps(out).encode()) <= MIB


@pytest.mark.parametrize("name", ["-dash_zq", ":(glob)star_zq*"])
def test_t3_leading_dash_and_pathspec_magic_stay_inert(
    run: Callable[..., Any], launches: Launches, repo: Repo, name: str
) -> None:
    changed = repo.commit(name, "after\n")
    before = sorted(p.name for p in repo.path.iterdir())
    code, out = run(f"--path={name}", f"--base={repo.base}")
    assert code == 0
    assert out["present_at_base"] is True
    assert out["commits"] == [changed]
    assert sorted(p.name for p in repo.path.iterdir()) == before
    for argv in non_helper(launches):
        sub = subcommand(argv)
        if sub == "log":
            assert "--literal-pathspecs" in argv
            cut = argv.index("--")
            assert argv[cut + 1:] == [name]
            assert name not in argv[:cut]
        elif sub in {"show", "cat-file", "rev-parse"} and any(name in e for e in argv):
            holders = [e for e in argv if name in e]
            assert len(holders) == 1 and holders[0].endswith(f":{name}"), argv
        elif sub == "diff":
            assert not any(name in e for e in argv)


# ── no process launch outside the helper ────────────────────────────────────

_BANNED_IMPORTS = {"subprocess", "pty", "asyncio", "multiprocessing", "ctypes"}
_BANNED_OS = ("system", "popen", "exec", "spawn", "posix_spawn", "fork")


@pytest.mark.parametrize("index", [0, 1])
def test_t3_no_process_launch_primitives(index: int) -> None:
    source = (SCRIPTS / "evidence-gate.py", SCRIPTS / "_git_history.py")[index]
    tree = ast.parse(source.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert not {a.name.split(".")[0] for a in node.names} & _BANNED_IMPORTS
        elif isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] not in _BANNED_IMPORTS
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
                if func.value.id == "os":
                    assert not func.attr.startswith(_BANNED_OS), func.attr
                if func.value.id == "importlib":
                    assert func.attr != "import_module"
            if isinstance(func, ast.Name):
                assert func.id != "__import__"


def test_t5_adjudication_guidance_names_git_history_entry() -> None:
    path = SCRIPTS.parent / "references" / "finding-adjudication.md"
    text = path.read_text(encoding="utf-8")
    start = text.index("\n## Bounded evidence retry\n") + 1
    end = text.index("\n## ", start + 1)
    section = " ".join(text[start:end].split())
    assert "`git-history`" in section
    assert "`show <oid>:<path>`" in section
    assert "`log --no-show-signature --format=%H --max-count=51 <base>..<head> -- <path>`" in section
    assert "`GIT_NO_LAZY_FETCH=1`" in section
    assert "Git 2.44 or later" in section
    assert "computes the change base itself" in section
    assert "`refs/remotes/origin/HEAD`" in section
    assert "only a path in the change's path set" in section
    assert "under `.context/`" in section
    assert "scoped exception to the process-level read allowlist" in section
    assert "committed objects only" in section
    assert "alternate or promisor object source" in section
    assert "`_supervisor_git.HardenedGit`" in section
    assert "evidence-gate.py' git-history --path <path>" in section
    assert "supplies the printed envelope" in section


def test_t13_guidance_states_log_bound_and_checkout_root() -> None:
    """The subsection states the 50-commit report bound and where to run the entry."""
    path = SCRIPTS.parent / "references" / "finding-adjudication.md"
    text = path.read_text(encoding="utf-8")
    start = text.index("\n## Bounded evidence retry\n") + 1
    end = text.index("\n## ", start + 1)
    section = " ".join(text[start:end].split())
    assert "reports up to 50 of them; a 51st marks the list truncated" in section
    assert "capped at 51" not in section
    assert "runs it from the checkout root" in section
