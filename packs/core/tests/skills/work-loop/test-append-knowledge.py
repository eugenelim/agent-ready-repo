#!/usr/bin/env python3
"""Self-test for append-knowledge.py — the canonical knowledge-base writer.

Run: python3 test-append-knowledge.py
Exit 0 = all pass; exit non-zero = at least one failure.

Each case asserts on observable bytes or exit codes rather than on the
script's internals, and each was written against a mutation: remove the
behaviour it names from append-knowledge.py and the case must go red.
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

# Windows cp1252 guard — reconfigure stdout/stderr to UTF-8 before any print.
sys.stdout.reconfigure(encoding="utf-8", errors="strict")
sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

_SKILL_DIR = Path(__file__).resolve().parents[3] / ".apm" / "skills" / "work-loop"
SCRIPT = _SKILL_DIR / "scripts" / "append-knowledge.py"

FAILURES: list[str] = []
RAN = 0


def ok(name: str) -> None:
    global RAN
    RAN += 1
    print(f"  ✓ {name}")


def fail(name: str, reason: str) -> None:
    global RAN
    RAN += 1
    FAILURES.append(name)
    print(f"  ✖ {name}: {reason}", file=sys.stderr)


# The subject resolves its confinement root from `git rev-parse` against the
# child's cwd, so every case runs inside a throwaway git repo rather than the
# real one — otherwise a passing test would be writing to the repo's own
# knowledge base, and the confinement case could not be expressed at all.
CWD: Path | None = None


def run(*args: str, timeout: float = 90.0) -> subprocess.CompletedProcess[str]:
    """Invoke the writer.

    `timeout` is not politeness: several cases exist to prove the lock's wait
    is bounded, and without it a regression there hangs the whole suite instead
    of failing the case that watches for it.
    """
    try:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            capture_output=True, text=True, encoding="utf-8", check=False,
            cwd=str(CWD) if CWD else None, timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(
            args, returncode=124, stdout="",
            stderr=f"TIMEOUT: no exit within {timeout:.0f}s (unbounded wait)",
        )


def entry(**over: object) -> str:
    base = {"id": "K-0001", "kind": "pattern", "scope": "x",
            "title": "t", "body": "b", "source": "s"}
    base.update(over)
    return json.dumps(base, ensure_ascii=False)


def _append_args(target: Path, **over: str) -> list[str]:
    fields = {"--kind": "gotcha", "--scope": "packs/core/**",
              "--title": "A title", "--body": "A body", "--source": "PR#1"}
    fields.update(over)
    args: list[str] = []
    for flag, value in fields.items():
        args += [flag, value]
    return args + ["--file", str(target)]


def test_non_ascii_body_lands_raw(target: Path) -> None:
    """AC13. The whole point: a non-ASCII body must reach disk as UTF-8 bytes,
    not as a \\uXXXX escape. Asserted on bytes — a decoded-string comparison
    passes for both forms and would not catch the drift."""
    name = "non-ascii-body-lands-raw"
    target.write_text("", encoding="utf-8")
    proc = run(*_append_args(target, **{"--body": "an em dash — and café"}))
    if proc.returncode != 0:
        fail(name, f"exit {proc.returncode}: {proc.stderr}")
        return
    raw = target.read_bytes()
    if b"\\u2014" in raw:
        fail(name, "em dash was written as a \\u2014 escape")
    elif "—".encode() not in raw or "café".encode() not in raw:
        fail(name, f"raw UTF-8 not found in output: {raw!r}")
    else:
        ok(name)


def test_id_allocation_tolerates_gaps(target: Path) -> None:
    """AC13. Ids are unique, not dense — the README says gaps are fine."""
    name = "id-allocation-tolerates-gaps"
    target.write_text(entry(id="K-0001") + "\n" + entry(id="K-0007") + "\n",
                      encoding="utf-8")
    proc = run(*_append_args(target))
    if proc.returncode != 0:
        fail(name, f"exit {proc.returncode}: {proc.stderr}")
        return
    ids = [json.loads(ln)["id"] for ln in
           target.read_text(encoding="utf-8").splitlines() if ln.strip()]
    if ids[-1] != "K-0008":
        fail(name, f"expected K-0008, got {ids[-1]}")
    else:
        ok(name)


def test_missing_trailing_newline_does_not_join(target: Path) -> None:
    """AC13. Appending to a file with no final newline must not fuse two
    entries into one unparseable line."""
    name = "missing-trailing-newline-does-not-join"
    target.write_text(entry(id="K-0001"), encoding="utf-8")  # no newline
    proc = run(*_append_args(target))
    if proc.returncode != 0:
        fail(name, f"exit {proc.returncode}: {proc.stderr}")
        return
    lines = [ln for ln in target.read_text(encoding="utf-8").splitlines()
             if ln.strip()]
    if len(lines) != 2:
        fail(name, f"expected 2 lines, got {len(lines)}")
        return
    try:
        for ln in lines:
            json.loads(ln)
    except json.JSONDecodeError as exc:
        fail(name, f"line did not parse: {exc.msg}")
        return
    ok(name)


def test_out_of_root_target_refused(target: Path) -> None:
    """AC14. --file is argv-controlled and so is the content written through
    it; the target must be confined to docs/knowledge after resolution.

    The decoy sits at the repo root, NOT in `target.parent` — that directory is
    the confinement root itself, so a path inside it is supposed to be
    accepted."""
    name = "out-of-root-target-refused"
    assert CWD is not None
    outside = CWD / "escaped.jsonl"
    proc = run(*_append_args(outside))
    if proc.returncode == 0:
        fail(name, f"accepted an out-of-root target: {outside}")
    elif outside.exists():
        fail(name, "refused but created the out-of-root file anyway")
    else:
        ok(name)


def test_symlink_escape_refused(target: Path) -> None:
    """AC14. The containment check runs after resolve(), so a link that lives
    inside the root but points outside it is still refused."""
    name = "symlink-escape-refused"
    assert CWD is not None
    real = CWD / "outside-target.jsonl"
    real.write_text("", encoding="utf-8")
    link = target.parent / "sneaky.jsonl"
    if link.exists() or link.is_symlink():
        link.unlink()
    try:
        link.symlink_to(real)
    except (OSError, NotImplementedError):
        ok(f"{name} (skipped — no symlink support)")
        return
    proc = run(*_append_args(link))
    if proc.returncode == 0:
        fail(name, "accepted a symlink resolving outside the root")
    elif real.read_bytes() != b"":
        fail(name, "refused but wrote through the symlink anyway")
    else:
        ok(name)


def test_decoy_git_dir_does_not_move_the_root(target: Path) -> None:
    """AC15. The confinement root comes from `git rev-parse`; if the child
    inherits GIT_DIR / GIT_WORK_TREE the root is attacker-steerable and the
    confinement of AC14 is anchored to a moved goalpost."""
    name = "decoy-git-dir-does-not-move-the-root"
    assert CWD is not None
    target.write_text("", encoding="utf-8")
    decoy = CWD / "decoy"
    decoy.mkdir(exist_ok=True)
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), *_append_args(target)],
        capture_output=True, text=True, encoding="utf-8", check=False,
        cwd=str(CWD), env={**os.environ, "GIT_WORK_TREE": str(decoy),
                           "GIT_DIR": str(decoy / ".git")},
    )
    if proc.returncode != 0:
        fail(name, f"a decoy GIT_WORK_TREE changed the outcome: {proc.stderr}")
    elif not target.read_bytes().strip():
        fail(name, "wrote nothing — the root was steered by the decoy")
    else:
        ok(name)


def test_control_character_refused_before_write(target: Path) -> None:
    """AC16. Entries are replayed verbatim into every future agent session by
    session-start.py, so ESC and the line separators never reach the file."""
    name = "control-character-refused-before-write"
    target.write_text(entry(id="K-0001") + "\n", encoding="utf-8")
    before = target.read_bytes()
    for label, payload in (("ESC", "a\x1b[31mb"), ("U+2028", "a b")):
        proc = run(*_append_args(target, **{"--body": payload}))
        if proc.returncode == 0:
            fail(name, f"{label} in --body was accepted")
            return
        if target.read_bytes() != before:
            fail(name, f"{label} rejected but the file changed")
            return
    ok(name)


def test_rejected_entry_leaves_file_byte_identical(target: Path) -> None:
    """AC17. A failed append is a no-op, not a partial write."""
    name = "rejected-entry-leaves-file-byte-identical"
    target.write_text(entry(id="K-0001") + "\n", encoding="utf-8")
    before = target.read_bytes()
    proc = run(*_append_args(target, **{"--kind": "not-a-kind"}))
    if proc.returncode == 0:
        fail(name, "invalid --kind was accepted")
    elif target.read_bytes() != before:
        fail(name, "file was modified despite the rejection")
    else:
        ok(name)


def test_preexisting_lint_failure_is_named(target: Path) -> None:
    """AC19. A knowledge base that was already broken must not be reported as
    the caller's entry failing lint."""
    name = "preexisting-lint-failure-is-named"
    target.write_text('{"id": "nope"}\n', encoding="utf-8")
    before = target.read_bytes()
    proc = run(*_append_args(target))
    out = proc.stdout + proc.stderr
    if proc.returncode == 0:
        fail(name, "appended onto an already-failing knowledge base")
    elif "already fails lint" not in out:
        fail(name, f"message did not name the pre-existing failure: {out!r}")
    elif target.read_bytes() != before:
        fail(name, "file was modified")
    else:
        ok(name)


def test_absent_target_is_created(target: Path) -> None:
    """AC19's other half. A non-existent file is an empty knowledge base, not a
    broken one — pre-linting it unconditionally would make a fresh base
    uncreatable and misreport it as already failing."""
    name = "absent-target-is-created"
    if target.exists():
        target.unlink()
    proc = run(*_append_args(target))
    if proc.returncode != 0:
        fail(name, f"exit {proc.returncode}: {proc.stderr}")
    elif not target.is_file():
        fail(name, "target was not created")
    elif json.loads(target.read_text(encoding="utf-8").strip())["id"] != "K-0001":
        fail(name, "first entry in a fresh file should be K-0001")
    else:
        ok(name)


def test_post_lint_failure_leaves_target_identical(target: Path) -> None:
    """AC17's install path — the branch that used to need a rollback.

    Driven by `--scope ','`: the writer's own validation only requires a
    non-empty string, but the linter requires at least one non-empty glob
    segment after splitting on commas, so this is a candidate that passes every
    pre-write check and fails the *post* lint. Distinct from the argparse
    rejections above, which never reach the temp file.
    """
    name = "post-lint-failure-leaves-target-identical"
    target.write_text(entry(id="K-0001") + "\n", encoding="utf-8")
    before = target.read_bytes()
    proc = run(*_append_args(target, **{"--scope": ","}))
    out = proc.stdout + proc.stderr
    if proc.returncode == 0:
        fail(name, "a candidate the linter rejects was installed")
    elif target.read_bytes() != before:
        fail(name, "target changed on a failed post-lint")
    elif "scope" not in out:
        fail(name, f"failure did not surface the linter's reason: {out!r}")
    elif list(target.parent.glob(".append-*.jsonl.tmp")):
        fail(name, "temp file left behind")
    else:
        ok(name)


def test_length_caps_enforced_at_the_boundary(target: Path) -> None:
    """AC16. A cap with no test is not a contract."""
    name = "length-caps-enforced-at-the-boundary"
    for field, cap in (("--title", 120), ("--body", 2000)):
        target.write_text("", encoding="utf-8")
        at = run(*_append_args(target, **{field: "x" * cap}))
        if at.returncode != 0:
            fail(name, f"{field} at exactly {cap} was refused: {at.stderr}")
            return
        over = run(*_append_args(target, **{field: "x" * (cap + 1)}))
        if over.returncode == 0:
            fail(name, f"{field} at {cap + 1} was accepted")
            return
        if str(cap) not in (over.stdout + over.stderr):
            fail(name, f"{field} refusal did not name the limit {cap}")
            return
    ok(name)


def test_invisible_formatting_characters_refused(target: Path) -> None:
    """AC16. `Cc` is only half the control. `Cf` carries bidi overrides and the
    Unicode Tag block (U+E0000-E007F), which encodes arbitrary ASCII at zero
    visual width — invisible in a diff, and replayed into every session by the
    session-start hook. ZWJ/ZWNJ stay legal: they are text shaping, not a way
    to hide payload."""
    name = "invisible-formatting-characters-refused"
    target.write_text("", encoding="utf-8")
    for label, payload in (
        ("RLO bidi override", "Prefer the boring one\u202e"),
        ("LRI isolate", "text\u2066more"),
        ("zero-width space", "a\u200bb"),
        ("Tag-block letter", "helper\U000e0053\U000e0059"),
    ):
        proc = run(*_append_args(target, **{"--body": payload}))
        out = proc.stdout + proc.stderr
        if proc.returncode == 0:
            fail(name, f"{label} was accepted")
            return
        if target.read_bytes():
            fail(name, f"{label} rejected but something was written")
            return
        # The linter refuses these too, so a bare non-zero cannot tell the two
        # layers apart. Pin the *writer's* pre-write refusal: a post-lint
        # rejection is reported as "the new entry does not lint".
        if "does not lint" in out:
            fail(name, f"{label} reached the post-lint — the writer's own "
                       f"validation did not refuse it")
            return
    zwj = run(*_append_args(target, **{"--body": "family \U0001f468\u200d\U0001f469\u200d\U0001f466 emoji"}))
    if zwj.returncode != 0:
        fail(name, f"a legitimate ZWJ sequence was refused: {zwj.stderr}")
    else:
        ok(name)


def test_concurrent_appends_do_not_lose_entries(target: Path) -> None:
    """AC17. `max(existing) + 1` then replace-the-file is a read-modify-write.
    Unlocked, concurrent callers allocate the same id and one entry is silently
    dropped — while both callers are told it was recorded, which is worse than
    a crash."""
    name = "concurrent-appends-do-not-lose-entries"
    target.write_text("", encoding="utf-8")
    n = 6
    procs = [
        subprocess.Popen(
            [sys.executable, str(SCRIPT), *_append_args(target, **{"--body": f"body {i}"})],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=str(CWD),
        )
        for i in range(n)
    ]
    reported = []
    for proc in procs:
        out, err = proc.communicate()
        if proc.returncode != 0:
            fail(name, f"a concurrent append failed: {err}")
            return
        reported.append(out.strip())
    lines = [ln for ln in target.read_text(encoding="utf-8").splitlines() if ln.strip()]
    on_disk = [json.loads(ln)["id"] for ln in lines]
    if len(on_disk) != n:
        fail(name, f"{n} appends reported success, {len(on_disk)} landed: {on_disk}")
    elif sorted(reported) != sorted(on_disk):
        fail(name, f"ids reported {sorted(reported)} != ids on disk {sorted(on_disk)}")
    elif len(set(on_disk)) != n:
        fail(name, f"duplicate ids allocated: {on_disk}")
    else:
        ok(name)


def test_file_mode_is_preserved(target: Path) -> None:
    """AC17. mkstemp creates 0600 and os.replace carries that onto the target,
    silently narrowing a committed world-readable file. Git tracks only the
    exec bit, so the change is invisible in a diff and to CI."""
    name = "file-mode-is-preserved"
    target.write_text(entry(id="K-0001") + "\n", encoding="utf-8")
    target.chmod(0o644)
    proc = run(*_append_args(target))
    if proc.returncode != 0:
        fail(name, f"exit {proc.returncode}: {proc.stderr}")
        return
    mode = target.stat().st_mode & 0o777
    ok(name) if mode == 0o644 else fail(name, f"mode changed 0o644 -> {oct(mode)}")


def test_lint_runs_out_of_process(target: Path) -> None:
    """AC18. lint-knowledge.py chdirs to the repo root at module scope, so an
    in-process import would relocate this writer's relative paths. Asserted on
    the writer's own stdout: it prints exactly the allocated id, whereas an
    in-process linter would also print its own `Knowledge lint: passed.` there.
    That also pins the print-the-id contract."""
    name = "lint-runs-out-of-process"
    target.write_text("", encoding="utf-8")
    proc = run(*_append_args(target))
    if proc.returncode != 0:
        fail(name, f"exit {proc.returncode}: {proc.stderr}")
    elif proc.stdout.strip() != "K-0001":
        fail(name, f"stdout was {proc.stdout.strip()!r}, expected exactly 'K-0001' "
                   f"— linter output leaking in means it ran in-process")
    else:
        ok(name)


def test_exclusive_lock_actually_excludes(target: Path) -> None:
    """AC17. The first version of this lock did not exclude: it broke a lock
    once *the waiter* had waited `timeout`, so a merely-slow holder lost it,
    and the unconditional release then deleted its successor's lock. Three
    processes ended up in the critical section at once."""
    name = "exclusive-lock-actually-excludes"
    spec = importlib.util.spec_from_file_location("_ak", str(SCRIPT))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    target.write_text("", encoding="utf-8")
    inside, overlaps, guard = [], [], threading.Lock()

    def hold(seconds: float) -> None:
        with mod.exclusive(target, timeout=20.0):
            with guard:
                inside.append(1)
                if len(inside) > 1:
                    overlaps.append(len(inside))
            time.sleep(seconds)
            with guard:
                inside.pop()

    # One slow holder plus two waiters that must queue behind it.
    threads = [threading.Thread(target=hold, args=(s,)) for s in (3.0, 0.2, 0.2)]
    for th in threads:
        th.start()
        time.sleep(0.05)
    for th in threads:
        th.join()
    ok(name) if not overlaps else fail(name, f"{max(overlaps)} holders at once")


def test_lock_timeout_reports_instead_of_hanging(target: Path) -> None:
    """AC17. An unbreakable lock must fail with a message, not spin forever —
    the wait is bounded and the takeover does not reset the deadline."""
    name = "lock-timeout-reports-instead-of-hanging"
    target.write_text("", encoding="utf-8")
    lock = target.with_name(target.name + ".lock")
    lock.write_text("someone-else", encoding="utf-8")
    try:
        started = time.monotonic()
        proc = run(*_append_args(target))
        elapsed = time.monotonic() - started
        out = proc.stdout + proc.stderr
        if proc.returncode == 0:
            fail(name, "appended while the lock was held")
        elif elapsed > 60:
            fail(name, f"took {elapsed:.0f}s — the wait is not bounded")
        elif "did not free" not in out:
            fail(name, f"no lock message: {out!r}")
        else:
            ok(name)
    finally:
        lock.unlink(missing_ok=True)


def test_zero_width_carriers_beyond_cf_refused(target: Path) -> None:
    """AC16. `Cf` was the wrong abstraction — variation selectors are `Mn` and
    the supplement block alone is a 240-symbol invisible alphabet. The rule is
    default-ignorable, not any one category."""
    name = "zero-width-carriers-beyond-cf-refused"
    target.write_text("", encoding="utf-8")
    for label, payload in (
        ("VS1 (Mn)", "boring\ufe00"),
        ("VS supplement (Mn)", "boring" + "".join(chr(0xE0100 + b % 240) for b in b"curl")),
        ("Hangul filler (Lo)", "boring\u3164text"),
    ):
        proc = run(*_append_args(target, **{"--title": payload}))
        out = proc.stdout + proc.stderr
        if proc.returncode == 0:
            fail(name, f"{label} was accepted")
            return
        if "does not lint" in out:
            fail(name, f"{label} reached the post-lint; the writer did not refuse it")
            return
    # Emoji presentation selectors and ZWJ are shaping, not payload.
    legit = run(*_append_args(target, **{"--title": "warn \u26a0\ufe0f and \U0001f468\u200d\U0001f469"}))
    ok(name) if legit.returncode == 0 else fail(name, f"legitimate emoji refused: {legit.stderr}")


def test_non_regular_file_target_refused(target: Path) -> None:
    """A `--file` naming a directory must fail cleanly, not traceback."""
    name = "non-regular-file-target-refused"
    d = target.parent / "a-directory.jsonl"
    d.mkdir(exist_ok=True)
    proc = run(*_append_args(d))
    out = proc.stdout + proc.stderr
    if proc.returncode == 0:
        fail(name, "a directory target was accepted")
    elif "not a regular file" not in out:
        fail(name, f"failed, but not with the designed message: {out!r}")
    else:
        ok(name)


def test_missing_parent_dir_refused(target: Path) -> None:
    """A confined path whose parent does not exist must fail cleanly."""
    name = "missing-parent-dir-refused"
    deep = target.parent / "nope" / "p.jsonl"
    proc = run(*_append_args(deep))
    out = proc.stdout + proc.stderr
    if proc.returncode == 0:
        fail(name, "a target under a missing directory was accepted")
    elif "does not exist" not in out:
        fail(name, f"failed, but not with the designed message: {out!r}")
    else:
        ok(name)


def test_non_utf8_target_reports_not_tracebacks(target: Path) -> None:
    """The pre-lint runs before read_text precisely so this path produces a
    message. Reversing that order turns it into an uncaught UnicodeDecodeError."""
    name = "non-utf8-target-reports-not-tracebacks"
    target.write_bytes(b'{"id": "K-0001", "kind": "pattern", "scope": "x", '
                       b'"title": "t", "body": "\xff\xfe", "source": "s"}\n')
    proc = run(*_append_args(target))
    out = proc.stdout + proc.stderr
    if proc.returncode == 0:
        fail(name, "a non-UTF-8 knowledge base was appended to")
    elif "Traceback" in out:
        fail(name, "tracebacked instead of reporting")
    elif "already fails lint" not in out and "not valid UTF-8" not in out:
        fail(name, f"no designed message: {out!r}")
    else:
        ok(name)


def test_lock_release_only_unlinks_what_it_owns(target: Path) -> None:
    """AC17a's second rule, and the one that made the first version cascade.
    After a stale takeover the displaced holder must NOT remove its successor's
    lock — otherwise every waiter behind it acquires at once."""
    name = "lock-release-only-unlinks-what-it-owns"
    spec = importlib.util.spec_from_file_location("_ak2", str(SCRIPT))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    target.write_text("", encoding="utf-8")
    lock = target.with_name(target.name + ".lock")
    # Enter, then let a "takeover" replace our lock with a foreign token.
    cm = mod.exclusive(target, timeout=5.0, stale_after=0.01)
    cm.__enter__()
    lock.write_text("someone-elses-token", encoding="utf-8")
    cm.__exit__(None, None, None)
    if not lock.exists():
        fail(name, "release removed a lock it no longer owned — this is the cascade")
        return
    lock.unlink()
    ok(name)


def test_lock_reports_on_an_unremovable_lock(target: Path) -> None:
    """AC17a. A lock path that cannot be unlinked must report, not busy-spin —
    both `continue` paths in the retry loop used to skip the deadline."""
    name = "lock-reports-on-an-unremovable-lock"
    target.write_text("", encoding="utf-8")
    lock = target.with_name(target.name + ".lock")
    lock.mkdir()  # a directory here: O_EXCL fails, and so does unlink
    # Backdate it past `stale_after`, or the takeover branch — the one that
    # discovers the path is unremovable — is never reached at all.
    old = time.time() - 10_000
    os.utime(lock, (old, old))
    try:
        started = time.monotonic()
        proc = run(*_append_args(target))
        elapsed = time.monotonic() - started
        out = proc.stdout + proc.stderr
        if proc.returncode == 0:
            fail(name, "appended despite an unusable lock path")
        elif elapsed > 30:
            fail(name, f"took {elapsed:.0f}s — it should report at once, not wait out "
                       f"the deadline or busy-spin")
        elif "cannot be removed" not in out:
            fail(name, f"did not name the unremovable lock: {out!r}")
        else:
            ok(name)
    finally:
        lock.rmdir()


def test_dangling_symlink_lock_is_bounded(target: Path) -> None:
    """AC17a. `O_EXCL` raises FileExistsError for a dangling symlink while
    `stat` raises FileNotFoundError — the branch that used to `continue` past
    both the deadline and the sleep, busy-spinning a core forever."""
    name = "dangling-symlink-lock-is-bounded"
    target.write_text("", encoding="utf-8")
    lock = target.with_name(target.name + ".lock")
    try:
        lock.symlink_to(target.parent / "does-not-exist")
    except (OSError, NotImplementedError):
        ok(f"{name} (skipped — no symlink support)")
        return
    try:
        started = time.monotonic()
        proc = run(*_append_args(target))
        elapsed = time.monotonic() - started
        if proc.returncode == 0:
            fail(name, "appended through a dangling-symlink lock")
        elif elapsed > 60:
            fail(name, f"busy-spun for {elapsed:.0f}s")
        elif "could not be inspected" not in (proc.stdout + proc.stderr):
            # Not just "bounded" — the message must not claim an age of 0s for a
            # lock whose stat failed.
            fail(name, f"message did not name the un-inspectable lock: "
                       f"{(proc.stdout + proc.stderr)!r}")
        else:
            ok(name)
    finally:
        lock.unlink(missing_ok=True)


def test_zero_width_run_refused_by_the_writer(target: Path) -> None:
    """AC16. The linter refuses a run too, so a bare non-zero cannot tell the
    layers apart — pin the writer's pre-write refusal, which names the field.
    Caught only by the post-lint, the message points at a temp file that no
    longer exists."""
    name = "zero-width-run-refused-by-the-writer"
    target.write_text("", encoding="utf-8")
    proc = run(*_append_args(target, **{"--body": "a\u200d\u200d\u200db"}))
    out = proc.stdout + proc.stderr
    if proc.returncode == 0:
        fail(name, "a three-joiner run was accepted")
    elif "does not lint" in out:
        fail(name, "reached the post-lint; the writer's own validation did not refuse it")
    elif "body" not in out:
        fail(name, f"refusal did not name the field: {out!r}")
    else:
        ok(name)


def test_losing_a_stale_break_race_is_a_retry_not_a_refusal(target: Path) -> None:
    """AC17a. When several waiters cross `stale_after` together they all try to
    break the same abandoned lock; the losers get FileNotFoundError from their
    unlink. That is "someone else already removed it — retry", not "cannot be
    removed", which is how a won race turned into a spurious refusal.

    Threaded rather than subprocess: the window between one waiter's unlink and
    the next one's is microseconds, and ~26ms of process spawn per waiter is far
    too coarse to land in it — a subprocess version of this ran 24 attempts
    without once reproducing.
    """
    name = "losing-a-stale-break-race-is-a-retry-not-a-refusal"
    spec = importlib.util.spec_from_file_location("_ak3", str(SCRIPT))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    target.write_text("", encoding="utf-8")
    lock = target.with_name(target.name + ".lock")
    refusals: list[str] = []

    def contend(barrier: threading.Barrier) -> None:
        barrier.wait()
        try:
            with mod.exclusive(target, timeout=20.0, stale_after=0.001):
                time.sleep(0.001)
        except mod.LockUnavailable as exc:
            refusals.append(str(exc))

    for _ in range(40):
        lock.write_text("abandoned", encoding="utf-8")
        old = time.time() - 10_000          # backdate past stale_after
        os.utime(lock, (old, old))
        barrier = threading.Barrier(6)
        threads = [threading.Thread(target=contend, args=(barrier,)) for _ in range(6)]
        for th in threads:
            th.start()
        for th in threads:
            th.join()
        lock.unlink(missing_ok=True)
    if refusals:
        fail(name, f"{len(refusals)} waiter(s) refused after losing a break race; "
                   f"first: {refusals[0][:120]}")
    else:
        ok(name)


def main() -> int:
    global CWD
    if not SCRIPT.is_file():
        print(f"✖ test-append-knowledge: subject not found at {SCRIPT}",
              file=sys.stderr)
        return 1
    with tempfile.TemporaryDirectory() as td:
        CWD = Path(td)
        subprocess.run(["git", "init", "-q", str(CWD)],
                       capture_output=True, check=True)
        root = CWD / "docs" / "knowledge"
        root.mkdir(parents=True)
        for case in (
            test_non_ascii_body_lands_raw,
            test_id_allocation_tolerates_gaps,
            test_missing_trailing_newline_does_not_join,
            test_out_of_root_target_refused,
            test_symlink_escape_refused,
            test_decoy_git_dir_does_not_move_the_root,
            test_control_character_refused_before_write,
            test_rejected_entry_leaves_file_byte_identical,
            test_preexisting_lint_failure_is_named,
            test_absent_target_is_created,
            test_post_lint_failure_leaves_target_identical,
            test_lint_runs_out_of_process,
            test_exclusive_lock_actually_excludes,
            test_lock_release_only_unlinks_what_it_owns,
            test_losing_a_stale_break_race_is_a_retry_not_a_refusal,
            test_lock_reports_on_an_unremovable_lock,
            test_dangling_symlink_lock_is_bounded,
            test_lock_timeout_reports_instead_of_hanging,
            test_zero_width_carriers_beyond_cf_refused,
            test_zero_width_run_refused_by_the_writer,
            test_non_regular_file_target_refused,
            test_missing_parent_dir_refused,
            test_non_utf8_target_reports_not_tracebacks,
            test_length_caps_enforced_at_the_boundary,
            test_invisible_formatting_characters_refused,
            test_concurrent_appends_do_not_lose_entries,
            test_file_mode_is_preserved,
        ):
            case(root / "patterns.jsonl")

    print()
    if FAILURES:
        print(f"✖ test-append-knowledge: {len(FAILURES)} of {RAN} cases failed",
              file=sys.stderr)
        return 1
    print(f"✓ test-append-knowledge: passed ({RAN} cases).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
