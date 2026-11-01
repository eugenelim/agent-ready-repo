"""The config fingerprint strips only canonical tracking blocks.

VI-0101 to VI-0104, VI-0106, VI-0113 to VI-0116. Needs no repository and no
supervisor run, so it also runs on Windows. Its only process is
``git config --file`` over the pinned shapes (VI-0116).
"""

from __future__ import annotations

import importlib.util
import os
import stat
import subprocess
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Any

import pytest

SCRIPTS = Path(__file__).resolve().parents[3] / ".apm" / "skills" / "work-loop" / "scripts"


def _load() -> ModuleType:
    alias = "core_work_loop_config_fingerprint_attempt"
    if alias not in sys.modules:
        previous = sys.dont_write_bytecode
        try:
            sys.dont_write_bytecode = True
            spec = importlib.util.spec_from_file_location(
                alias, str(SCRIPTS / "_supervisor_attempt.py")
            )
            assert spec is not None and spec.loader is not None
            module = importlib.util.module_from_spec(spec)
            sys.modules[alias] = module
            spec.loader.exec_module(module)
        finally:
            sys.dont_write_bytecode = previous
    return sys.modules[alias]


att = _load()
PREFIX = "config-view:"
CODE_RUNNING = sorted(
    {
        "diff.external",
        "core.sshcommand",
        "core.fsmonitor",
        "core.hookspath",
        "gpg.program",
        "gpg.ssh.defaultkeycommand",
        "include.path",
    }
)


def fingerprint(data: bytes) -> str:
    """The config fingerprint of *data* as the shipped code computes it."""
    return PREFIX + att._digest(att._strip_tracking_blocks(data))


def whole(data: bytes) -> str:
    return PREFIX + att._digest(data)


BASE = b'[core]\n\tbare = false\n[remote "origin"]\n\turl = /good\n\tfetch = +refs/*:refs/*\n[user]\n\temail = a@b\n'
BRANCH = b'[branch "x"]\n\tremote = origin\n\tmerge = refs/heads/x\n'


def _with_branch(block: bytes) -> bytes:
    """BASE with *block* inserted before ``[user]`` (so a header follows it)."""
    head, tail = BASE.split(b"[user]", 1)
    return head + block + b"[user]" + tail


# ── VI-0101 ─────────────────────────────────────────────────────────────────

AT_END = BASE + BRANCH
CASES_SAME = {
    "new-branch-block-at-end": AT_END,
    "new-branch-block-before-header": _with_branch(BRANCH),
    "changed-remote": BASE + b'[branch "x"]\n\tremote = other\n',
    "changed-merge": BASE + b'[branch "x"]\n\tmerge = refs/heads/y\n',
    "changed-pushremote": BASE + b'[branch "x"]\n\tpushremote = p\n',
    "changed-rebase": BASE + b'[branch "x"]\n\trebase = interactive\n',
    "changed-description": BASE + b'[branch "x"]\n\tdescription = hello world\n',
    "all-five-keys": BASE
    + b'[branch "x"]\n\tremote = o\n\tmerge = m\n\tpushremote = p\n\trebase = true\n\tdescription = d\n',
    "gh-resolved": BASE.replace(
        b"\tfetch = +refs/*:refs/*\n", b"\tfetch = +refs/*:refs/*\n\tgh-resolved = base\n"
    ),
    "gh-resolved-first-in-block": BASE.replace(
        b"\turl = /good\n", b"\turl = /good\n\tgh-resolved = other\n"
    ),
}


@pytest.mark.parametrize("name", sorted(CASES_SAME))
def test_vi_0101_canonical_tracking_blocks_leave_the_fingerprint_unchanged(name: str) -> None:
    assert fingerprint(CASES_SAME[name]) == fingerprint(BASE)


def test_vi_0101_removing_a_whole_canonical_block_leaves_the_fingerprint() -> None:
    assert fingerprint(AT_END) == fingerprint(_with_branch(BRANCH)) == fingerprint(BASE)


# ── VI-0102 ─────────────────────────────────────────────────────────────────

CASES_DIFFER = {
    "hooksPath": BASE + b"[core]\n\thooksPath = /evil\n",
    "remote-url": BASE.replace(b"/good", b"/other"),
    "remote-fetch": BASE.replace(b"+refs/*:refs/*", b"+refs/x:refs/x"),
    "user-email": BASE.replace(b"a@b", b"c@d"),
    "branch-no-subsection": BASE + b"[branch]\n\tremote = o\n",
    "core-after-branch-block": BASE + BRANCH + b"[core]\n\teditor = e\n",
    "non-excluded-key-in-branch": BASE + b'[branch "x"]\n\tremote = o\n\tvcs = x\n',
    "excluded-key-noncanonical": BASE + b'[branch "x"]\n\tremote=o\n',
}
for _key in ("uploadpack", "receivepack", "pushurl", "vcs", "proxy"):
    CASES_DIFFER[f"gh-resolved-beside-{_key}"] = BASE.replace(
        b"\turl = /good\n", b"\turl = /good\n\tgh-resolved = base\n\t" + _key.encode() + b" = x\n"
    )


def _code_running_line(key: str) -> bytes:
    section, _, variable = key.rpartition(".")
    return f"[{section}]\n\t{variable} = /evil\n".encode()


for _key in CODE_RUNNING:
    CASES_DIFFER[f"{_key}-before-block"] = BASE + _code_running_line(_key) + BRANCH
    CASES_DIFFER[f"{_key}-after-block"] = BASE + BRANCH + _code_running_line(_key)


@pytest.mark.parametrize("name", sorted(CASES_DIFFER))
def test_vi_0102_any_byte_outside_a_canonical_block_changes_the_fingerprint(name: str) -> None:
    assert fingerprint(CASES_DIFFER[name]) != fingerprint(BASE)


# ── VI-0103 and VI-0116 ─────────────────────────────────────────────────────

# (bytes, keys and values Git reports for them, from the plan's probe)
HEADER = [
    (b'[branch "x"][core]hooksPath = /evil\n', ["core.hookspath=/evil"]),
    (b'[branch "x\\\\"][filter "y"]clean = "/evil"]\n', ["filter.y.clean=/evil]"]),
    (b'[branch "x"] [remote "origin"]url = /evil\n', ["remote.origin.url=/evil"]),
    (b'[branch "x"]\r[core]\n\thookspath = /evil\n', ["core.hookspath=/evil"]),
    (b'[Branch "x"]\n\tremote = o\n', ["branch.x.remote=o"]),
    (b'\xef\xbb\xbf[branch "x"]\n\tremote = o\n', ["branch.x.remote=o"]),
]
KEYVALUE = [
    (b'[branch "x"]\n\tRemote = o\n', ["branch.x.remote=o"]),
    (b'[branch "x"]\n\tremote=o\n', ["branch.x.remote=o"]),
    (b'[branch "x"]\n\tremote = "o"\n', ["branch.x.remote=o"]),
    (b'[branch "x"]\n\tremote = o;x\n', ["branch.x.remote=o"]),
    (b'[branch "x"]\n\tremote = o#x\n', ["branch.x.remote=o"]),
    (
        b'[branch "x"]\n\tremote = o\n\thookspath = /evil\n',
        ["branch.x.remote=o", "branch.x.hookspath=/evil"],
    ),
    (b"[include]\n\tpath = /x\n", ["include.path=/x"]),
    (b'[includeIf "gitdir:/x/"]\n\tpath = /y\n', ["includeif.gitdir:/x/.path=/y"]),
    (
        b'[branch "x"]\n\tremote = o\\\n[core]\n\tbare = false\n',
        ["branch.x.remote=o[core]", "branch.x.bare=false"],
    ),
]
CONTINUATION = [  # each is a precondition case
    (
        b'[remote "origin"]\n\turl = /x\\\r\n[branch "b"]\n\tremote = o\n[core]\n\thooksPath = /evil\n',
        ["remote.origin.url=/x[branch b]", "remote.origin.remote=o", "core.hookspath=/evil"],
    ),
    (
        b'[remote "origin"]\n\turl = /x\\\r\n\tgh-resolved = base\n\tpushurl = /evil\n',
        ["remote.origin.url=/x\tgh-resolved = base", "remote.origin.pushurl=/evil"],
    ),
    (
        b'[remote "o"]\n\turl = /good\\\r\n[branch "b"]\n\tremote = one\n[core]\n\tbare = false\n',
        ["remote.o.url=/good[branch b]", "remote.o.remote=one", "core.bare=false"],
    ),
    (
        b'[remote "o"]\n\turl = /good\\\r\n[branch "b"]\n\tremote = two\n[core]\n\tbare = false\n',
        ["remote.o.url=/good[branch b]", "remote.o.remote=two", "core.bare=false"],
    ),
    (
        b'[remote "o"]\n\turl = /good\\\r\n\tgh-resolved = one\n',
        ["remote.o.url=/good\tgh-resolved = one"],
    ),
    (
        b'[remote "o"]\n\turl = /good\\\r\n\tgh-resolved = two\n',
        ["remote.o.url=/good\tgh-resolved = two"],
    ),
    (
        b'[include]\n\tpath = /x\\\r\n[branch "b"]\n\tremote = o\n[core]\n\tbare = false\n',
        ["include.path=/x[branch b]", "include.remote=o", "core.bare=false"],
    ),
    (
        b'[remote "o"]\n\turl = /good\\\n[branch "b"]\n\tremote = o\n[core]\n\tbare = false\n',
        ["remote.o.url=/good[branch b]", "remote.o.remote=o", "core.bare=false"],
    ),
]
LINE_ENDING = [
    (b'[branch "x"]\r\n\tremote = o\r\n', ["branch.x.remote=o"]),
    (  # precondition
        b'[core]\r\n\tbare = false\r\n[branch "x"]\n\tremote = o\n[core]\n\teditor = e\n',
        ["core.bare=false", "branch.x.remote=o", "core.editor=e"],
    ),
    (  # precondition
        b'[core]\n\tbare = false\n[branch "x"]\n\tremote = o\n[core]\n\teditor = a\rb\n',
        ["core.bare=false", "branch.x.remote=o", "core.editor=a\rb"],
    ),
    (b'[branch "x"]\n\tremote = o', ["branch.x.remote=o"]),
    (  # precondition
        b'[branch "x"]\n\tremote = o\n[core]\n\tbare = false',
        ["branch.x.remote=o", "core.bare=false"],
    ),
]
# One keep-case per fail-closed rule of the canonical form (VI-0121); each is also
# part of the VI-0103 and VI-0116 tables through PINNED.
FAIL_CLOSED = {
    "header-only-branch": (
        b'[core]\n\tbare = false\n[branch "x"]\n',
        ["core.bare=false"],
    ),
    "header-only-branch-before-section": (
        b'[branch "x"]\n[user]\n\temail = e\n',
        ["user.email=e"],
    ),
    "non-member-line-before-gh-resolved": (
        b'[remote "o"]\n\turl = /u\n\t[core]\n\tgh-resolved = b\n',
        ["remote.o.url=/u", "core.gh-resolved=b"],
    ),
    "control-byte-in-branch-value": (
        b'[branch "x"]\n\tremote = o\x01p\n',
        ["branch.x.remote=o\x01p"],
    ),
    "control-byte-in-gh-resolved-value": (
        b'[remote "o"]\n\turl = /u\n\tgh-resolved = b\x01c\n',
        ["remote.o.url=/u", "remote.o.gh-resolved=b\x01c"],
    ),
    "backslash-in-branch-subsection": (
        b'[branch "a\\\\b"]\n\tremote = o\n',
        ["branch.a\\b.remote=o"],
    ),
    "control-byte-in-branch-subsection": (
        b'[branch "a\x01b"]\n\tremote = o\n',
        ["branch.a\x01b.remote=o"],
    ),
    "backslash-in-remote-subsection": (
        b'[remote "a\\\\b"]\n\turl = /u\n\tgh-resolved = b\n',
        ["remote.a\\b.url=/u", "remote.a\\b.gh-resolved=b"],
    ),
    "control-byte-in-remote-subsection": (
        b'[remote "a\x01b"]\n\turl = /u\n\tgh-resolved = b\n',
        ["remote.a\x01b.url=/u", "remote.a\x01b.gh-resolved=b"],
    ),
}
PINNED = HEADER + KEYVALUE + CONTINUATION + LINE_ENDING + list(FAIL_CLOSED.values())
CONTROL = (
    b'[core]\n\tbare = false\n[branch "x"]\n\tremote = o\n[core]\n\teditor = e\n',
    ["core.bare=false", "branch.x.remote=o", "core.editor=e"],
)
BASE_LIST = [
    "core.bare=false",
    "remote.origin.url=/good",
    "remote.origin.fetch=+refs/*:refs/*",
    "user.email=a@b",
]


@pytest.mark.parametrize("index", range(len(PINNED)))
def test_vi_0103_a_pinned_shape_keeps_every_byte(index: int) -> None:
    data = PINNED[index][0]
    assert fingerprint(data) == whole(data)


def test_vi_0103_the_control_file_loses_exactly_its_block() -> None:
    data = CONTROL[0]
    assert att._strip_tracking_blocks(data) == data.replace(b'[branch "x"]\n\tremote = o\n', b"")


def _git_list(tmp_path: Path, data: bytes) -> list[str]:
    target = tmp_path / "config-under-test"
    target.write_bytes(data)
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env["GIT_CONFIG_GLOBAL"] = os.devnull
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    done = subprocess.run(
        ["git", "config", "--file", str(target), "--list"],
        capture_output=True,
        env=env,
        check=False,
    )
    assert done.returncode == 0, done.stderr
    return done.stdout.decode().replace("\r\n", "\n").rstrip("\n").split("\n")


@pytest.mark.parametrize("index", range(len(PINNED)))
def test_vi_0116_git_reads_each_pinned_shape_as_the_case_claims(
    tmp_path: Path, index: int
) -> None:
    data, expected = PINNED[index]
    assert _git_list(tmp_path, data) == expected


def test_vi_0116_git_reads_the_control_file_and_the_base(tmp_path: Path) -> None:
    assert _git_list(tmp_path, CONTROL[0]) == CONTROL[1]
    assert _git_list(tmp_path, BASE) == BASE_LIST


# ── VI-0104 ─────────────────────────────────────────────────────────────────


def test_vi_0104_every_config_fingerprint_is_prefixed_and_no_raw_one_is() -> None:
    every = (
        [BASE, *CASES_SAME.values(), *CASES_DIFFER.values(), CONTROL[0]]
        + [data for data, _ in PINNED]
    )
    for data in every:
        assert fingerprint(data).startswith(PREFIX)
        assert not att._digest(data).startswith(PREFIX)


# ── VI-0114 ─────────────────────────────────────────────────────────────────

NEAR_MISS = {
    "gh-resolved-x": b'[remote "origin"]\n\turl = /u\n\tgh-resolved-x = {v}\n',
    "remotes": b'[branch "x"]\n\tremotes = {v}\n',
    "Merge": b'[branch "x"]\n\tMerge = {v}\n',
    "gh-resolved-in-branch": b'[branch "x"]\n\tgh-resolved = {v}\n',
}


@pytest.mark.parametrize("name", sorted(NEAR_MISS))
def test_vi_0114_a_near_miss_key_stays_in_the_fingerprint(name: str) -> None:
    template = NEAR_MISS[name]
    one = fingerprint(BASE + template.replace(b"{v}", b"one"))
    two = fingerprint(BASE + template.replace(b"{v}", b"two"))
    assert one != two


# ── VI-0106 and VI-0115 ─────────────────────────────────────────────────────

_AUDIT_FAIL = {
    "subprocess.Popen",
    "os.system",
    "os.posix_spawn",
    "os.spawn",
    "os.exec",
    "os.fork",
    "os.startfile",
}
_guard = {"active": False}


def _audit(event: str, args: tuple[Any, ...]) -> None:
    if _guard["active"] and event in _AUDIT_FAIL:
        raise AssertionError(f"git_state() launched a process: {event}")


sys.addaudithook(_audit)


def _attempts(root: Path) -> Any:
    git_dir = root / ".git"
    git_dir.mkdir(exist_ok=True)
    pins = SimpleNamespace(root=root, git_dir=git_dir, common_dir=git_dir)
    ws = SimpleNamespace(git=SimpleNamespace(hardened=SimpleNamespace(pins=pins)))
    return att.Attempts(ws)


def test_vi_0106_git_state_creates_no_process(tmp_path: Path) -> None:
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "config").write_bytes(BASE + BRANCH)
    attempts = _attempts(tmp_path)
    _guard["active"] = True
    try:
        state = attempts.git_state()
    finally:
        _guard["active"] = False
    assert state["git:config"] == fingerprint(BASE)


def test_vi_0115_one_read_per_config_file_and_the_fingerprint_follows_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    (git_dir / "config").write_bytes(BASE)
    (git_dir / "config.worktree").write_bytes(BASE)
    attempts = _attempts(tmp_path)
    fs = att.sibling("_file_safety.py")
    real = fs.read_confined_regular_file
    reads: list[str] = []
    served = BASE + b'[core]\n\teditor = served\n'

    def counting(base: Path, path: Path, **kwargs: Any) -> Any:
        if path.name in ("config", "config.worktree"):
            reads.append(path.name)
            return served
        return real(base, path, **kwargs)

    monkeypatch.setattr(fs, "read_confined_regular_file", counting)
    state = attempts.git_state()
    assert sorted(reads) == ["config", "config.worktree"]
    assert state["git:config"] == state["git:config.worktree"] == fingerprint(served)
    assert fingerprint(served) != fingerprint(BASE)


def test_vi_0115_an_oversized_config_is_unsafe(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    (git_dir / "config").write_bytes(b"[core]\n\tbare = false\n" + b"#" * 64)
    monkeypatch.setattr(att, "_MAX_FILE_BYTES", 32)
    assert _attempts(tmp_path).git_state()["git:config"] == "unsafe"


def _special_cases() -> list[str]:
    """Only the file types this platform can create are collected."""
    found = []
    probe = Path(os.path.realpath(os.environ.get("TMPDIR", "/tmp")))
    if hasattr(os, "symlink") and sys.platform != "win32":
        found.append("link")
    if hasattr(os, "mkfifo") and probe.exists():
        found.append("fifo")
    return found


def _link_or_special_config_keeps_its_value(tmp_path: Path, kind: str) -> None:
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    target = tmp_path / "elsewhere"
    target.write_bytes(BASE)
    config = git_dir / "config"
    if kind == "link":
        config.symlink_to(target)
    else:
        os.mkfifo(config)
        assert stat.S_ISFIFO(os.lstat(config).st_mode)
    value = _attempts(tmp_path).git_state()["git:config"]
    if kind == "link":
        assert value.startswith("link:")
    else:
        assert value == "special"


# Defined only where the platform can create a kind: an empty parameter list
# would still collect one skipped case, which the zero-skip CI check refuses.
if _special_cases():
    test_vi_0115_a_link_or_special_config_keeps_its_value = pytest.mark.parametrize(
        "kind", _special_cases()
    )(_link_or_special_config_keeps_its_value)


# ── VI-0119 ─────────────────────────────────────────────────────────────────


def _reference_strip(data: bytes) -> bytes:
    """The rule as first written: a backward walk per gh-resolved line (quadratic)."""
    if not data.endswith(b"\n") or b"\r" in data or b"\\\n" in data:
        return data
    lines = data.splitlines(keepends=True)
    drop: set[int] = set()
    i = 0
    while i < len(lines):
        line = lines[i]
        if att._BRANCH_HEADER.fullmatch(line):
            end = i + 1
            while end < len(lines) and att._BRANCH_KEY.fullmatch(lines[end]):
                end += 1
            if end > i + 1 and (end == len(lines) or lines[end].startswith(b"[")):
                drop.update(range(i, end))
                i = end
                continue
        elif att._GH_RESOLVED.fullmatch(line):
            back = i - 1
            while back >= 0 and att._MEMBER_LINE.match(lines[back]):
                back -= 1
            if back >= 0 and att._REMOTE_HEADER.fullmatch(lines[back]):
                drop.add(i)
        i += 1
    return b"".join(line for n, line in enumerate(lines) if n not in drop)


def _line_soup(seed: int, count: int) -> bytes:
    """A deterministic mix of canonical, near-canonical, and foreign lines."""
    import random

    pool = [
        b'[branch "x"]\n', b'[branch "y"]\n', b'[remote "o"]\n', b'[remote "p"]\n',
        b"[core]\n", b"\tremote = a\n", b"\tmerge = m\n", b"\tdescription = d\n",
        b"\tgh-resolved = b\n", b"\turl = /u\n", b"\t[core]\n", b"\tfoo = 1\n",
        b"\tgh-resolved = b;c\n", b"\tRemote = a\n", b"  indented\n", b"\n",
    ]
    rng = random.Random(seed)
    return b"".join(rng.choice(pool) for _ in range(count))


def test_vi_0119_the_single_pass_rule_equals_the_reference_on_the_corpus() -> None:
    corpus = [BASE, CONTROL[0], *CASES_SAME.values(), *CASES_DIFFER.values()]
    corpus += [data for data, _ in PINNED]
    corpus += [_line_soup(seed, 40) for seed in range(300)]
    for data in corpus:
        assert att._strip_tracking_blocks(data) == _reference_strip(data)


def test_vi_0119_a_huge_gh_resolved_block_is_fingerprinted_in_bounded_time() -> None:
    import time

    lines = 200_000
    data = b'[remote "o"]\n\turl = /u\n' + b"\tgh-resolved = b\n" * lines
    started = time.monotonic()
    stripped = att._strip_tracking_blocks(data)
    elapsed = time.monotonic() - started
    assert stripped == b'[remote "o"]\n\turl = /u\n'
    assert elapsed < 5, f"{lines} gh-resolved lines took {elapsed:.1f}s"


# ── VI-0120 ─────────────────────────────────────────────────────────────────

PATTERN_KEYS = [
    ("filter", "y", "clean"),
    ("diff", "d", "textconv"),
    ("includeIf", "gitdir:/x/", "path"),
    ("gpg", "ssh", "defaultKeyCommand"),
]


def _key_sections() -> dict[str, tuple[str, str]]:
    """Each code-running key as ``(section header, variable)``."""
    found = {}
    for key in CODE_RUNNING:
        section, _, variable = key.rpartition(".")
        found[key] = (f"[{section}]\n", variable)
    for section, name, variable in PATTERN_KEYS:
        found[f"{section}.{name}.{variable}"] = (f'[{section} "{name}"]\n', variable)
    return found


def _pair(key: str, where: str, value: bytes) -> bytes:
    header, variable = _key_sections()[key]
    line = f"\t{variable} = ".encode() + value + b"\n"
    if where == "before-block":
        return BASE + header.encode() + line + BRANCH
    if where == "after-block":
        return BASE + BRANCH + header.encode() + line
    if where == "inside-branch-block":  # Git reads it as branch.x.<variable>
        return BASE + b'[branch "x"]\n\tremote = o\n' + line
    return BASE.replace(b"\turl = /good\n", b"\turl = /good\n\tgh-resolved = base\n" + line)


@pytest.mark.parametrize("where", ["before-block", "after-block", "inside-branch-block", "after-gh-resolved"])
@pytest.mark.parametrize("key", sorted(_key_sections()))
def test_vi_0120_a_code_running_key_value_change_changes_the_fingerprint(
    key: str, where: str
) -> None:
    assert fingerprint(_pair(key, where, b"/a")) != fingerprint(_pair(key, where, b"/b"))


# ── VI-0121 ─────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("name", sorted(FAIL_CLOSED))
def test_vi_0121_each_fail_closed_rule_keeps_every_byte_and_git_agrees(
    tmp_path: Path, name: str
) -> None:
    data, expected = FAIL_CLOSED[name]
    assert fingerprint(data) == whole(data)
    assert _git_list(tmp_path, data) == expected


# ── VI-0122 ─────────────────────────────────────────────────────────────────

# The special file kinds each platform can create, and the named gap where it cannot.
EXPECTED_KINDS = {"posix": ("link", "fifo"), "win32": ()}
PLATFORM_GAPS = {
    "win32": "no symlink without privilege and no mkfifo: link and special files cannot be created",
}


def test_vi_0122_each_expected_kind_is_creatable_here_and_gaps_are_named(tmp_path: Path) -> None:
    platform = "win32" if sys.platform == "win32" else "posix"
    for kind in EXPECTED_KINDS[platform]:
        made = tmp_path / kind
        if kind == "link":
            made.symlink_to(tmp_path)
            assert stat.S_ISLNK(os.lstat(made).st_mode)
        else:
            os.mkfifo(made)
            assert stat.S_ISFIFO(os.lstat(made).st_mode)
    assert set(EXPECTED_KINDS["posix"]) == {"link", "fifo"}
    assert (platform in PLATFORM_GAPS) == (EXPECTED_KINDS[platform] == ())


# ── VI-0124 ─────────────────────────────────────────────────────────────────

SKILL = SCRIPTS.parent


def test_vi_0124_the_gh_guidance_and_its_eval_name_the_repository() -> None:
    reference = (SKILL / "references" / "supervisor.md").read_text("utf-8")
    assert "--repo" in reference
    assert "with or without a pull request number" in " ".join(reference.split())
    evals = (SKILL / "evals" / "evals.json").read_text("utf-8")
    assert "--repo" in evals
