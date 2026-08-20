#!/usr/bin/env python3
"""Self-test for `tools/lint_git_ignore.py`, the batched Git-ignore resolver.

Every property here is a criterion from `docs/specs/lint-performance-p0/spec.md`.
The resolver is the one piece of genuinely new logic in that spec, so it is the
one place a prose contract is the right tool and these assertions are explicit.

Two properties are load-bearing rather than tidy, and are worth naming:

* **Batching changes the blast radius of a bad candidate.** One `check-ignore`
  process now answers for hundreds of paths, and Git exits 128 for the *whole*
  invocation on a single unusable path while still echoing the candidates it
  processed before it. A partial result silently under-reports, so a non-0/1
  exit is a hard error here, never a policy outcome.

* **"Nothing is ignored" is not a safe default for the callers.** The boundary
  lint *subtracts* the ignored set, and two of its findings fire on the
  emptiness of what remains. So the resolver must let a caller distinguish
  "Git ran and nothing matched" from "Git never answered" — hence `degraded`.
"""

from __future__ import annotations

import base64
import importlib.util
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest import mock

sys.stdout.reconfigure(encoding="utf-8", errors="strict")
sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "tools" / "lint_git_ignore.py"
if not MODULE.is_file():
    raise SystemExit(f"resolver not found at {MODULE}")


def _load():
    spec = importlib.util.spec_from_file_location("lint_git_ignore", MODULE)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["lint_git_ignore"] = mod
    spec.loader.exec_module(mod)
    return mod


M = _load()

#: A single ~400-line main() aborts every later block on one exception, so the
#: reported count silently drops. Falling below this is a failure in itself.
_CASE_FLOOR = 95

_FAILURES: list[str] = []
_CASES = 0


def check(name: str, ok: bool, detail: str = "") -> None:
    global _CASES
    _CASES += 1
    if not ok:
        _FAILURES.append(f"{name}: {detail}" if detail else name)


def _git(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    """Run git in the scrubbed environment the resolver itself must use."""
    return subprocess.run(
        ["git", *args], cwd=str(cwd), capture_output=True, text=True,
        check=False, env=M.hermetic_git_env(os.environ, repo_root=cwd),
    )


def _repo(tmp: Path, gitignore: str = "ig/\n*.ignored\n") -> Path:
    """A real, hermetic Git worktree — fixtures must not inherit host config."""
    root = tmp / "repo"
    root.mkdir()
    _git(["init", "-q", "."], root)
    # An explicit empty excludes file: a host `core.excludesFile` matching a
    # fixture path would otherwise rewrite the answers under us.
    empty = tmp / "empty-excludes"
    empty.write_text("", encoding="utf-8")
    _git(["config", "core.excludesFile", str(empty)], root)
    (root / ".gitignore").write_text(gitignore, encoding="utf-8")
    return root


class _Recorder:
    """Captures every subprocess.run the resolver makes, and fakes the reply."""

    def __init__(self, stdout=b"", returncode=0, stderr=b"", raises=None):
        self.calls: list[dict] = []
        self._stdout, self._rc, self._stderr, self._raises = (
            stdout, returncode, stderr, raises,
        )

    def __call__(self, argv, **kwargs):
        self.calls.append({"argv": argv, "kwargs": kwargs})
        if self._raises is not None:
            raise self._raises
        return subprocess.CompletedProcess(
            argv, self._rc, self._stdout, self._stderr
        )


def main() -> int:  # noqa: C901 — a flat list of independent contract checks
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        root = _repo(tmp)

        # ---- no candidates launches no process ---------------------------
        rec = _Recorder()
        with mock.patch.object(M.subprocess, "run", rec):
            res = M.git_ignored_paths(
                root, [], missing_git_policy=M.MissingGitPolicy.FAIL_OPEN,
                timeout=30.0,
            )
        check("empty: no subprocess", len(rec.calls) == 0, f"{len(rec.calls)} calls")
        check("empty: no ignored", res.ignored == ())
        check("empty: not degraded", res.degraded is False)

        # ---- one candidate, each direction ------------------------------
        (root / "a.ignored").write_text("x", encoding="utf-8")
        (root / "b.kept").write_text("x", encoding="utf-8")
        res = M.git_ignored_paths(
            root, [root / "a.ignored"],
            missing_git_policy=M.MissingGitPolicy.FAIL_OPEN, timeout=30.0,
        )
        check("one ignored", res.ignored == (root / "a.ignored",), repr(res.ignored))
        res = M.git_ignored_paths(
            root, [root / "b.kept"],
            missing_git_policy=M.MissingGitPolicy.FAIL_OPEN, timeout=30.0,
        )
        check("one not ignored", res.ignored == (), repr(res.ignored))

        # ---- mixed batch partitions ------------------------------------
        res = M.git_ignored_paths(
            root, [root / "a.ignored", root / "b.kept"],
            missing_git_policy=M.MissingGitPolicy.FAIL_OPEN, timeout=30.0,
        )
        check("mixed batch", res.ignored == (root / "a.ignored",), repr(res.ignored))

        # ---- hundreds of candidates, exactly one process ----------------
        many = [root / f"f{i}.ignored" for i in range(500)]
        rec = _Recorder(stdout=b"\0".join(f"f{i}.ignored".encode() for i in range(500)))
        with mock.patch.object(M.subprocess, "run", rec):
            res = M.git_ignored_paths(
                root, many, missing_git_policy=M.MissingGitPolicy.FAIL_OPEN,
                timeout=30.0,
            )
        check("500 candidates: one process", len(rec.calls) == 1, f"{len(rec.calls)}")
        check("500 candidates: all resolved", len(res.ignored) == 500,
              f"{len(res.ignored)}")

        # ---- duplicates collapse before Git sees them -------------------
        rec = _Recorder(stdout=b"a.ignored\0")
        with mock.patch.object(M.subprocess, "run", rec):
            M.git_ignored_paths(
                root, [root / "a.ignored"] * 7,
                missing_git_policy=M.MissingGitPolicy.FAIL_OPEN, timeout=30.0,
            )
        payload = rec.calls[0]["kwargs"]["input"]
        entries = [e for e in payload.split(b"\0") if e]
        check("duplicates collapsed", len(entries) == 1, f"payload entries={entries}")

        # ---- candidate domain: absolute, relative, non-existent ---------
        res = M.git_ignored_paths(
            root, [Path("a.ignored")],
            missing_git_policy=M.MissingGitPolicy.FAIL_OPEN, timeout=30.0,
        )
        check("root-relative candidate resolves",
              res.ignored == (Path("a.ignored"),), repr(res.ignored))
        res = M.git_ignored_paths(
            root, [Path("never/created.ignored")],
            missing_git_policy=M.MissingGitPolicy.FAIL_OPEN, timeout=30.0,
        )
        check("non-existent candidate resolves",
              res.ignored == (Path("never/created.ignored"),), repr(res.ignored))
        # Membership must be testable with the caller's OWN object, and identity
        # must survive normalisation. lint-agents-md hands in relative,
        # non-existent probes and compares the answer against those same objects,
        # so an absolute-Path answer would never match and every probe would look
        # un-ignored. Make the probe genuinely ignored, then assert identity.
        (root / ".gitignore").write_text(
            "ig/\n*.ignored\ndocs/specs/example/state.json\n", encoding="utf-8"
        )
        probe = Path("docs/specs/example/state.json")
        res = M.git_ignored_paths(
            root, [probe], missing_git_policy=M.MissingGitPolicy.FAIL_OPEN,
            timeout=30.0,
        )
        check("a relative non-existent probe is reported ignored",
              res.ignored == (probe,), repr(res.ignored))
        check("the returned object IS the caller's object",
              res.ignored and res.ignored[0] is probe, repr(res.ignored))
        # Mixed absolute + relative in one batch: each keyed to what was supplied.
        rel, absolute = Path("a.ignored"), root / "b.kept"
        res = M.git_ignored_paths(
            root, [rel, absolute],
            missing_git_policy=M.MissingGitPolicy.FAIL_OPEN, timeout=30.0,
        )
        check("mixed absolute/relative keeps each caller's form",
              res.ignored == (rel,), repr(res.ignored))
        (root / ".gitignore").write_text("ig/\n*.ignored\n", encoding="utf-8")

        # ---- lexical containment, not resolve() -------------------------
        # Containment must be decided lexically: a link-crossing candidate stays
        # inside the root rather than being relocated out of it and refused for
        # the wrong reason. Git then declines to answer for it — `fatal: pathspec
        # ... is beyond a symbolic link`, exit 128 — which surfaces as a
        # GitIgnoreError naming the path. That is a documented precondition:
        # callers prune links while collecting candidates (both current callers
        # already do), because detecting it here would mean an lstat walk per
        # candidate, reintroducing the per-path filesystem work this module
        # exists to remove.
        (root / "real").mkdir()
        (root / "real" / "s.ignored").write_text("x", encoding="utf-8")
        try:
            (root / "link").symlink_to(root / "real", target_is_directory=True)
            linked_ok = True
        except OSError:
            linked_ok = False
        if linked_ok:
            raised = None
            try:
                M.git_ignored_paths(
                    root, [root / "link" / "s.ignored"],
                    missing_git_policy=M.MissingGitPolicy.FAIL_OPEN, timeout=30.0,
                )
            except M.GitIgnoreError as exc:
                raised = exc
            check("link-crossing candidate is refused, not silently degraded",
                  raised is not None, repr(raised))
            check("link-crossing refusal is actionable",
                  raised is not None and "Prune links" in str(raised), str(raised))
            check("link-crossing refusal is not a ValueError (containment is lexical)",
                  not isinstance(raised, ValueError))

        for bad, label in (
            (Path("/etc/hosts"), "absolute outside root"),
            (root.parent / "outside.ignored", "sibling outside root"),
            (Path("../outside.ignored"), "relative escaping root"),
        ):
            raised = None
            try:
                M.git_ignored_paths(
                    root, [bad], missing_git_policy=M.MissingGitPolicy.FAIL_OPEN,
                    timeout=30.0,
                )
            except ValueError as exc:
                raised = exc
            check(f"out-of-root raises ValueError ({label})", raised is not None)
            check(f"out-of-root names the path ({label})",
                  raised is not None and str(bad.name) in str(raised), str(raised))

        # ---- pathspec magic is rejected at the boundary -----------------
        # Probed: `:!x`, `:(glob)x` etc. make git exit 128 with a PARTIAL echo,
        # so one such candidate would zero every verdict in the batch.
        for magic in (":!weird.ignored", ":(glob)weird.ignored",
                      ":(exclude)weird.ignored"):
            raised = None
            try:
                M.git_ignored_paths(
                    root, [Path(magic)],
                    missing_git_policy=M.MissingGitPolicy.FAIL_OPEN, timeout=30.0,
                )
            except ValueError as exc:
                raised = exc
            check(f"pathspec magic rejected ({magic})", raised is not None)

        # ---- special filenames survive the NUL round trip ---------------
        specials = ["with space.ignored", "with\ttab.ignored",
                    "with\nnewline.ignored", "ünïcodé.ignored",
                    "-leading-dash.ignored", "!leading-bang.ignored"]
        made = []
        for name in specials:
            try:
                (root / name).write_text("x", encoding="utf-8")
                made.append(name)
            except OSError:
                pass          # a filesystem may refuse a shape; skip only that one
        res = M.git_ignored_paths(
            root, [root / n for n in made],
            missing_git_policy=M.MissingGitPolicy.FAIL_OPEN, timeout=30.0,
        )
        check("special filenames round-trip",
              {p.name for p in res.ignored} == set(made),
              f"missing={set(made) - {p.name for p in res.ignored}}")

        # ---- argv shape: no shell, no --no-index, no :(literal) ---------
        rec = _Recorder(stdout=b"")
        with mock.patch.object(M.subprocess, "run", rec):
            M.git_ignored_paths(
                root, [root / "a.ignored"],
                missing_git_policy=M.MissingGitPolicy.FAIL_OPEN, timeout=30.0,
            )
        call = rec.calls[0]
        argv, kwargs = call["argv"], call["kwargs"]
        check("argv is a list", isinstance(argv, list), repr(type(argv)))
        check("argv uses --stdin -z",
              "--stdin" in argv and "-z" in argv, repr(argv))
        check("argv has no --no-index", "--no-index" not in argv, repr(argv))
        check("no shell=True", kwargs.get("shell") in (None, False), repr(kwargs))
        check("timeout forwarded", kwargs.get("timeout") == 30.0, repr(kwargs))
        check("payload carries no :(literal)",
              b":(literal)" not in kwargs["input"])
        check("stdin used, not argv paths",
              not any("a.ignored" in a for a in argv), repr(argv))
        check("hermetic env passed", "env" in kwargs and
              kwargs["env"].get("GIT_CONFIG_NOSYSTEM") == "1", repr(kwargs.get("env")))
        for leaked in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE",
                       "GIT_COMMON_DIR"):
            check(f"hermetic env drops {leaked}",
                  leaked not in kwargs["env"], repr(kwargs["env"].get(leaked)))
        # GIT_CEILING_DIRECTORIES is deliberately SET, not dropped: it is the one
        # variable in this family whose removal *widens* discovery, letting a
        # non-worktree root answer from an ancestor repository.
        check("GIT_CEILING_DIRECTORIES fences discovery at the repo root",
              kwargs["env"].get("GIT_CEILING_DIRECTORIES") == str(root),
              repr(kwargs["env"].get("GIT_CEILING_DIRECTORIES")))

        # ---- one communicate()-backed call, large payload ---------------
        big = [root / f"{'p' * 200}{i}.ignored" for i in range(6000)]
        rec = _Recorder(stdout=b"")
        with mock.patch.object(M.subprocess, "run", rec):
            M.git_ignored_paths(
                root, big, missing_git_policy=M.MissingGitPolicy.FAIL_OPEN,
                timeout=30.0,
            )
        check("large payload: one call", len(rec.calls) == 1, f"{len(rec.calls)}")
        check("large payload exceeds a pipe buffer",
              len(rec.calls[0]["kwargs"]["input"]) > 1 << 20,
              f"{len(rec.calls[0]['kwargs']['input'])} bytes")

        # Against REAL git, unmocked. The mocked case above proves only that a
        # >1 MiB `input=` was passed once; a `Popen`+`write`+`wait`
        # implementation would deadlock on a payload this size, and only a real
        # subprocess can demonstrate that it does not.
        real_big = [root / f"{'q' * 200}{i}.ignored" for i in range(6000)]
        import signal

        # SIGALRM does not exist on Windows, and this suite is a required
        # gate-chain step — so the watchdog leg is skipped with a counted case
        # rather than raising AttributeError there. The alarm is set strictly
        # ABOVE the resolver's own timeout, or a slow runner produces a coin flip
        # between "watchdog tripped" and "resolver degraded" — both red, for
        # different reasons.
        if not hasattr(signal, "SIGALRM"):
            check("large-payload watchdog skipped (no SIGALRM on this host)",
                  True)
            sys.stderr.write("SKIP unmocked large-payload watchdog — this host "
                             "has no SIGALRM\n")
        else:
            def _timeout(_sig, _frm):
                raise TimeoutError("git_ignored_paths blocked on a large payload")

            previous = signal.signal(signal.SIGALRM, _timeout)
            signal.alarm(90)                      # > the 60s resolver timeout
            blocked = None
            try:
                big_res = M.git_ignored_paths(
                    root, real_big,
                    missing_git_policy=M.MissingGitPolicy.FAIL_OPEN,
                    timeout=60.0,
                )
            except TimeoutError as exc:
                blocked, big_res = exc, None
            finally:
                signal.alarm(0)
                signal.signal(signal.SIGALRM, previous)
            check("a >1 MiB payload completes against real git (no deadlock)",
                  blocked is None, repr(blocked))
            check("the large real batch resolved every candidate",
                  big_res is not None and len(big_res.ignored) == 6000,
                  f"{None if big_res is None else len(big_res.ignored)}")

        # ---- bytes payload, not str ------------------------------------
        check("payload is bytes",
              isinstance(rec.calls[0]["kwargs"]["input"], bytes))
        # A surrogate-escaped name must not raise UnicodeEncodeError. The file
        # cannot be created on APFS (Errno 92), so assert the encode path itself.
        surrogate = os.fsdecode(b"bad\xffname.ignored")
        raised = None
        rec = _Recorder(stdout=b"")
        with mock.patch.object(M.subprocess, "run", rec):
            try:
                M.git_ignored_paths(
                    root, [root / surrogate],
                    missing_git_policy=M.MissingGitPolicy.FAIL_OPEN, timeout=30.0,
                )
            except UnicodeEncodeError as exc:
                raised = exc
        check("surrogate name does not raise UnicodeEncodeError", raised is None,
              repr(raised))

        # ---- ordering is sorted and stable ------------------------------
        shuffled = [root / f"z{i}.ignored" for i in (5, 1, 4, 2, 3)]
        for p in shuffled:
            p.write_text("x", encoding="utf-8")
        first = M.git_ignored_paths(
            root, shuffled, missing_git_policy=M.MissingGitPolicy.FAIL_OPEN,
            timeout=30.0,
        ).ignored
        second = M.git_ignored_paths(
            root, list(reversed(shuffled)),
            missing_git_policy=M.MissingGitPolicy.FAIL_OPEN, timeout=30.0,
        ).ignored
        check("ordering: sorted", list(first) == sorted(first), repr(first))
        check("ordering: input-order independent", first == second)
        check("ordering: is a tuple", isinstance(first, tuple), repr(type(first)))

        # Stable across processes: hash randomisation is live in a fresh one.
        probe_src = (
            "import sys, importlib.util, os\n"
            f"spec = importlib.util.spec_from_file_location('m', {str(MODULE)!r})\n"
            "m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)\n"
            "from pathlib import Path\n"
            f"root = Path({str(root)!r})\n"
            "names = [f'z{i}.ignored' for i in (5,1,4,2,3)]\n"
            "r = m.git_ignored_paths(root, [root / n for n in names],\n"
            "    missing_git_policy=m.MissingGitPolicy.FAIL_OPEN, timeout=30.0)\n"
            "print('\\n'.join(str(p) for p in r.ignored))\n"
        )
        outs = set()
        for _ in range(2):
            r = subprocess.run([sys.executable, "-c", probe_src],
                               capture_output=True, text=True, check=False)
            outs.add(r.stdout)
        check("ordering: identical across processes", len(outs) == 1, repr(outs))

        # ---- exit codes 0 and 1 are both normal -------------------------
        for rc in (0, 1):
            rec = _Recorder(stdout=b"", returncode=rc)
            with mock.patch.object(M.subprocess, "run", rec):
                res = M.git_ignored_paths(
                    root, [root / "a.ignored"],
                    missing_git_policy=M.MissingGitPolicy.FAIL_OPEN, timeout=30.0,
                )
            check(f"exit {rc} is normal", res.degraded is False, repr(res))

        # ---- any other exit is a HARD error, not a policy outcome -------
        rec = _Recorder(stdout=b"a.ignored\0", returncode=128,
                        stderr=b"fatal: 'x' is outside repository at '/abs/where'")
        raised = None
        with mock.patch.object(M.subprocess, "run", rec):
            try:
                M.git_ignored_paths(
                    root, [root / "a.ignored"],
                    missing_git_policy=M.MissingGitPolicy.FAIL_OPEN, timeout=30.0,
                )
            except M.GitIgnoreError as exc:
                raised = exc
        check("exit 128 raises GitIgnoreError rather than returning a partial "
              "result", raised is not None, repr(raised))
        check("exit 128 carries git stderr",
              raised is not None and "fatal:" in str(raised), str(raised))
        # It relativizes what it knows — the root and the home directory. It does
        # NOT claim to scrub an arbitrary absolute path git happens to name; what
        # keeps such a message out of a committed baseline is that a non-0/1 exit
        # raises rather than being captured.
        rec = _Recorder(stdout=b"", returncode=128,
                        stderr=f"fatal: bad thing at {root}/x and {Path.home()}/y"
                               .encode())
        raised = None
        with mock.patch.object(M.subprocess, "run", rec):
            try:
                M.git_ignored_paths(
                    root, [root / "a.ignored"],
                    missing_git_policy=M.MissingGitPolicy.FAIL_OPEN, timeout=30.0,
                )
            except M.GitIgnoreError as exc:
                raised = exc
        check("detail redacts the repository root",
              raised is not None and str(root) not in str(raised), str(raised))
        check("detail redacts the home directory",
              raised is not None and str(Path.home()) not in str(raised),
              str(raised))
        check("detail is length-bounded",
              len(M._bound_detail(root, "x" * 99999)) < 99999)

        # ---- Git absent / error / timeout follow the policy -------------
        for exc_obj, label in (
            (FileNotFoundError("git"), "git absent"),
            (subprocess.TimeoutExpired(cmd="git", timeout=30.0), "timeout"),
            (OSError("exec failed"), "exec error"),
        ):
            rec = _Recorder(raises=exc_obj)
            with mock.patch.object(M.subprocess, "run", rec):
                res = M.git_ignored_paths(
                    root, [root / "a.ignored"],
                    missing_git_policy=M.MissingGitPolicy.FAIL_OPEN, timeout=30.0,
                )
            check(f"FAIL_OPEN degrades ({label})", res.degraded is True, repr(res))
            check(f"FAIL_OPEN empties ignored ({label})", res.ignored == ())
            check(f"FAIL_OPEN records a reason ({label})", bool(res.detail))
            check(f"degraded reason distinguishes cause ({label})",
                  res.reason is not None, repr(res))

            rec = _Recorder(raises=exc_obj)
            raised = None
            with mock.patch.object(M.subprocess, "run", rec):
                try:
                    M.git_ignored_paths(
                        root, [root / "a.ignored"],
                        missing_git_policy=M.MissingGitPolicy.RAISE, timeout=30.0,
                    )
                except Exception as exc:  # noqa: BLE001 — any propagation counts
                    raised = exc
            check(f"RAISE propagates ({label})", raised is not None)

        # distinct reasons, so a caller can say WHICH degradation happened
        reasons = set()
        for exc_obj in (FileNotFoundError("git"),
                        subprocess.TimeoutExpired(cmd="git", timeout=1.0)):
            rec = _Recorder(raises=exc_obj)
            with mock.patch.object(M.subprocess, "run", rec):
                reasons.add(M.git_ignored_paths(
                    root, [root / "a.ignored"],
                    missing_git_policy=M.MissingGitPolicy.FAIL_OPEN, timeout=1.0,
                ).reason)
        check("absence and timeout are distinguishable reasons",
              len(reasons) == 2, repr(reasons))

        # ---- required keyword arguments ---------------------------------
        for kwargs, label in (
            ({"timeout": 30.0}, "missing_git_policy"),
            ({"missing_git_policy": M.MissingGitPolicy.FAIL_OPEN}, "timeout"),
        ):
            raised = None
            try:
                M.git_ignored_paths(root, [root / "a.ignored"], **kwargs)
            except TypeError as exc:
                raised = exc
            check(f"{label} is a required keyword argument", raised is not None)

        # ---- the helper is silent ---------------------------------------
        import contextlib
        import io
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            M.git_ignored_paths(
                root, [root / "a.ignored"],
                missing_git_policy=M.MissingGitPolicy.FAIL_OPEN, timeout=30.0,
            )
        check("helper prints nothing to stdout", out.getvalue() == "", out.getvalue())
        check("helper prints nothing to stderr", err.getvalue() == "", err.getvalue())

        # ---- tracked files stay excluded (no --no-index) ----------------
        (root / "tracked.ignored").write_text("x", encoding="utf-8")
        _git(["add", "-f", "tracked.ignored"], root)
        res = M.git_ignored_paths(
            root, [root / "tracked.ignored"],
            missing_git_policy=M.MissingGitPolicy.FAIL_OPEN, timeout=30.0,
        )
        check("a tracked file is not reported ignored", res.ignored == (),
              repr(res.ignored))

        # ---- hermeticity: a hostile global excludes file is ignored -----
        hostile = tmp / "hostile-excludes"
        hostile.write_text("*.kept\n", encoding="utf-8")
        env = dict(os.environ)
        env["GIT_CONFIG_GLOBAL"] = str(hostile)
        with mock.patch.dict(os.environ, env, clear=False):
            res = M.git_ignored_paths(
                root, [root / "b.kept"],
                missing_git_policy=M.MissingGitPolicy.FAIL_OPEN, timeout=30.0,
            )
        check("hostile global excludes cannot leak in", res.ignored == (),
              f"leaked: {res.ignored!r}")

        # ---- base64 round trip helpers used by the golden harness -------
        # No `hasattr` guard: these are unconditionally defined and exported, so
        # a guard would silently delete its own case if one were ever removed.
        blob = b"line\0with\xffbytes\n"
        check("stream encode/decode round-trips bytes",
              M.decode_stream(M.encode_stream(blob)) == blob)
        check("encoded form is ascii-safe json text",
              base64.b64decode(M.encode_stream(blob)) == blob)
        check("both codecs are exported",
              {"encode_stream", "decode_stream"} <= set(M.__all__),
              repr(M.__all__))

        # ---- SEC-1: the config-injection channel is closed ---------------
        # GIT_CONFIG_COUNT survives GIT_CONFIG_NOSYSTEM and redirected global and
        # system config, and it is the only channel that leaks SILENTLY (rc=0
        # with an extra path reported ignored, rather than a fail-closed 128).
        hostile_excludes = tmp / "hostile-excludes-file"
        hostile_excludes.write_text("*.kept\n", encoding="utf-8")
        injected = dict(os.environ)
        injected.update({
            "GIT_CONFIG_COUNT": "1",
            "GIT_CONFIG_KEY_0": "core.excludesFile",
            "GIT_CONFIG_VALUE_0": str(hostile_excludes),
            "GIT_GLOB_PATHSPECS": "1",
        })
        scrubbed_env = M.hermetic_git_env(injected, repo_root=root)
        # The caller's one-off config is dropped; the scrub then sets its OWN
        # single entry to pin core.excludesFile. So the test is not "absent" but
        # "replaced by ours" — asserting absence would now forbid the fix.
        for dropped in ("GIT_GLOB_PATHSPECS", "GIT_CONFIG_PARAMETERS"):
            check(f"hermetic env drops {dropped}", dropped not in scrubbed_env,
                  repr(scrubbed_env.get(dropped)))
        check("the caller's injected excludesFile value is replaced",
              scrubbed_env.get("GIT_CONFIG_VALUE_0") == os.devnull,
              repr(scrubbed_env.get("GIT_CONFIG_VALUE_0")))
        check("the scrub owns exactly one config entry",
              scrubbed_env.get("GIT_CONFIG_COUNT") == "1"
              and scrubbed_env.get("GIT_CONFIG_KEY_0") == "core.excludesFile",
              repr({k: scrubbed_env.get(k) for k in
                    ("GIT_CONFIG_COUNT", "GIT_CONFIG_KEY_0")}))
        check("no caller GIT_CONFIG_KEY_n beyond the scrub's own survives",
              not [k for k in scrubbed_env
                   if k.startswith("GIT_CONFIG_KEY_") and k != "GIT_CONFIG_KEY_0"],
              repr([k for k in scrubbed_env if k.startswith("GIT_CONFIG_KEY_")]))
        with mock.patch.dict(os.environ, injected, clear=False):
            res = M.git_ignored_paths(
                root, [root / "b.kept"],
                missing_git_policy=M.MissingGitPolicy.FAIL_OPEN, timeout=30.0,
            )
        check("an injected core.excludesFile cannot leak in", res.ignored == (),
              f"leaked: {res.ignored!r}")

        # Every channel that can change the answer, each verified to leak before
        # it was closed. GIT_CONFIG_PARAMETERS is how `git -c k=v` propagates
        # into subprocesses and hooks, and outranks GIT_CONFIG_COUNT.
        fake_home = tmp / "fakehome"
        (fake_home / "git").mkdir(parents=True, exist_ok=True)
        (fake_home / "git" / "ignore").write_text("*.kept\n", encoding="utf-8")
        home_dir = tmp / "homedir"
        (home_dir / ".config" / "git").mkdir(parents=True, exist_ok=True)
        (home_dir / ".config" / "git" / "ignore").write_text(
            "*.kept\n", encoding="utf-8"
        )
        channels = {
            "GIT_CONFIG_PARAMETERS":
                {"GIT_CONFIG_PARAMETERS":
                 f"'core.excludesFile={hostile_excludes}'"},
            "GIT_CONFIG_COUNT":
                {"GIT_CONFIG_COUNT": "1",
                 "GIT_CONFIG_KEY_0": "core.excludesFile",
                 "GIT_CONFIG_VALUE_0": str(hostile_excludes)},
            # `GIT_CONFIG_GLOBAL=os.devnull` leaves core.excludesFile UNSET, and
            # unset is exactly when git consults these two. Emptying the global
            # config opens the fallback; the default has to be pinned.
            "XDG_CONFIG_HOME fallback": {"XDG_CONFIG_HOME": str(fake_home)},
            "HOME fallback": {"HOME": str(home_dir), "XDG_CONFIG_HOME": ""},
        }
        for label, overrides in channels.items():
            with mock.patch.dict(os.environ, {**os.environ, **overrides},
                                 clear=True):
                leaked = M.git_ignored_paths(
                    root, [root / "b.kept"],
                    missing_git_policy=M.MissingGitPolicy.FAIL_OPEN,
                    timeout=30.0,
                )
            check(f"{label} cannot influence the ignore answer",
                  leaked.ignored == (), f"leaked: {leaked.ignored!r}")
        check("the scrub pins core.excludesFile rather than leaving it unset",
              M.hermetic_git_env(os.environ, repo_root=root)
              .get("GIT_CONFIG_VALUE_0") == os.devnull,
              repr(M.hermetic_git_env(os.environ, repo_root=root)
                   .get("GIT_CONFIG_VALUE_0")))

        # Discovery is FENCED, not widened. Dropping GIT_CEILING_DIRECTORIES
        # would let a non-worktree root resolve upward and answer from an
        # ancestor repository's .gitignore.
        fenced = M.hermetic_git_env(os.environ, repo_root=root)
        check("a repo_root fences discovery via GIT_CEILING_DIRECTORIES",
              fenced.get("GIT_CEILING_DIRECTORIES") == str(root),
              repr(fenced.get("GIT_CEILING_DIRECTORIES")))
        check("discovery does not cross filesystems",
              fenced.get("GIT_DISCOVERY_ACROSS_FILESYSTEM") == "0")
        # repo_root is keyword-REQUIRED: an optional parameter meant four of five
        # call sites silently kept the unfenced behaviour.
        raised = None
        try:
            M.hermetic_git_env(os.environ)
        except TypeError as exc:
            raised = exc
        check("repo_root is a required keyword argument", raised is not None,
              "an omitted repo_root must not silently mean 'do not fence'")
        check("an explicit None means do-not-fence",
              "GIT_CEILING_DIRECTORIES"
              not in M.hermetic_git_env(os.environ, repo_root=None))
        not_a_repo = tmp / "notarepo"
        not_a_repo.mkdir(exist_ok=True)
        (not_a_repo / "x.kept").write_text("x", encoding="utf-8")
        # Fenced discovery makes this fail closed — git cannot find a repository
        # at all, so it raises rather than quietly answering from the ancestor
        # worktree this directory happens to sit inside. Either outcome is
        # acceptable; silently answering is not.
        outside_ignored = None
        try:
            outside_ignored = M.git_ignored_paths(
                not_a_repo, [not_a_repo / "x.kept"],
                missing_git_policy=M.MissingGitPolicy.FAIL_OPEN, timeout=30.0,
            ).ignored
        except M.GitIgnoreError:
            outside_ignored = ()          # refused outright: the stronger outcome
        check("a non-worktree root never answers from an ancestor repo",
              outside_ignored == (), f"leaked: {outside_ignored!r}")

        # A ValueError detail is redacted like every other diagnostic.
        raised = None
        try:
            M.git_ignored_paths(
                root, [Path("/etc/hosts")],
                missing_git_policy=M.MissingGitPolicy.FAIL_OPEN, timeout=30.0,
            )
        except ValueError as exc:
            raised = exc
        check("an out-of-root ValueError redacts the root",
              raised is not None and str(root) not in str(raised), str(raised))

        # ---- degradation details are redacted ----------------------------
        rec = _Recorder(raises=OSError(
            f"Not a directory: '{Path.home()}/somewhere/deep'"))
        with mock.patch.object(M.subprocess, "run", rec):
            degraded = M.git_ignored_paths(
                root, [root / "a.ignored"],
                missing_git_policy=M.MissingGitPolicy.FAIL_OPEN, timeout=30.0,
            )
        check("a degradation detail redacts the home directory",
              degraded.detail is not None
              and str(Path.home()) not in degraded.detail,
              repr(degraded.detail))

    if _CASES < _CASE_FLOOR:
        _FAILURES.append(
            f"only {_CASES} cases ran, below the floor of {_CASE_FLOOR}; a run "
            f"that stops early must not report green"
        )

    for f in _FAILURES:
        sys.stderr.write(f"FAIL {f}\n")
    if _FAILURES:
        sys.stderr.write(f"✖ lint_git_ignore: {len(_FAILURES)} of {_CASES} failed\n")
        return 1
    sys.stderr.write(f"ok — {_CASES} cases passed\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
