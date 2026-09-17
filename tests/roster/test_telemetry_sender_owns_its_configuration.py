"""The documented telemetry invocation needs no `agentbundle`, and still works.

Covers AC-0001 through AC-0004 of
`docs/specs/telemetry-sender-owns-its-configuration/spec.md`. It supplies
the first mechanical control for AC-0041, AC-0043 and AC-0044 of the shipped
`loop-telemetry-export` contract — three criteria that are ticked with no test
behind them. Those three stay owned by that spec; nothing here re-authors them.

Repository-level by construction: it reads the published guide, the shipped
work-loop profile and the installed sender together, so it belongs here rather
than in either package's own suite.
"""

from __future__ import annotations

import io
import json
import os
import re
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[2]
_GUIDE = _REPO / "guides/core/how-to/export-loop-telemetry.md"
_PROFILE = _REPO / "packs/core/.apm/skills/work-loop/profiles/work-loop.toml"

# The section whose blocks are the documented invocation, and the only part of
# the guide these controls quantify over. Matching ```python anywhere would let
# an unrelated Python example added later break the exact-two assertion or shift
# the indices below, for a reason with nothing to do with telemetry.
_INVOCATION_HEADING = "## Build the invocation"
_PYTHON_BLOCK = re.compile(r"```python\n(.*?)```", re.S)


def _invocation_section() -> str:
    """The guide from the invocation heading to the next `## ` heading."""
    text = _GUIDE.read_text(encoding="utf-8")
    start = text.find(_INVOCATION_HEADING)
    assert start != -1, f"the guide no longer has a {_INVOCATION_HEADING!r} section"
    rest = text[start + len(_INVOCATION_HEADING):]
    end = rest.find("\n## ")
    return rest if end == -1 else rest[:end]


def _blocks() -> list[str]:
    return _PYTHON_BLOCK.findall(_invocation_section())


# A stub on PATH standing in for the installed console script. It records the
# argv it was handed and exits 0, so executing the documented block proves the
# block runs without also requiring a Collector.
_STUB = """#!{python}
import json, sys, pathlib
pathlib.Path({record!r}).write_text(json.dumps(sys.argv[1:]), encoding="utf-8")
"""

# Refuses `agentbundle` at import, in a fresh interpreter. A finder installed
# in *this* process would never be consulted for a module already in
# `sys.modules`, and the test runner has very likely imported `agentbundle`
# already -- so the subprocess is what makes the assertion mean anything.
_BLOCKER = """
import sys
class _Refuse:
    def find_module(self, name, path=None):
        return self.find_spec(name, path)
    def find_spec(self, name, path=None, target=None):
        if name == "agentbundle" or name.startswith("agentbundle."):
            raise ImportError("agentbundle is not importable in this context")
        return None
sys.meta_path.insert(0, _Refuse())
"""


@pytest.fixture()
def documented_run(tmp_path):
    """Run a documented block in a fresh interpreter that cannot import agentbundle."""
    repo = tmp_path / "repo"
    (repo / ".loop-run").mkdir(parents=True)
    (repo / ".loop-run" / "events.jsonl").write_text("", encoding="utf-8")
    home = tmp_path / "home"
    (home / ".agentbundle").mkdir(parents=True)
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    record = tmp_path / "argv.json"
    stub = bin_dir / "jsonl-otlp-export"
    stub.write_text(_STUB.format(python=sys.executable, record=str(record)),
                    encoding="utf-8")
    stub.chmod(0o755)

    def run(block: str):
        env = dict(os.environ)
        env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"
        env["HOME"] = str(home)
        env["USERPROFILE"] = str(home)
        env.pop("PYTHONPATH", None)  # the repo's pythonpath would re-expose agentbundle
        try:
            proc = subprocess.run(
                [sys.executable, "-c", _BLOCKER + block],
                cwd=repo, env=env, capture_output=True, text=True,
                # Without a bound, a block that blocks -- on a FIFO, a prompt, a
                # socket -- hangs until the CI job's own timeout, which reports a
                # timed-out job rather than a failed criterion. 60s is generous:
                # the stub the block invokes writes one file and exits.
                timeout=60,
            )
        except subprocess.TimeoutExpired as exc:
            pytest.fail(
                "the documented invocation block did not finish within 60s; "
                f"it must not block. Block:\n{block}\nPartial stderr: {exc.stderr!r}"
            )
        argv = json.loads(record.read_text(encoding="utf-8")) if record.exists() else None
        return proc, argv, repo, home

    return run


# --- AC-0001 -----------------------------------------------------------------

def test_the_guide_documents_both_invocation_blocks() -> None:
    """The floor under AC-0001.

    Every claim below is quantified over the guide's blocks, and all of them are
    vacuously true of a guide with none. A deletion that emptied the section
    would otherwise read as a pass.
    """
    assert len(_blocks()) == 2, "the invocation section documents two Python blocks"


@pytest.mark.parametrize("index", [0, 1])
def test_each_block_runs_with_agentbundle_unimportable(documented_run, index) -> None:
    """AC-0001, asserted by execution rather than by reading imports.

    A lexical check over parsed imports is blind to `__import__("agentbundle")`
    and to anything reached through an alias; running the block under a finder
    that refuses the package is what actually establishes the claim.
    """
    proc, _, _, _ = documented_run(_blocks()[index])
    assert proc.returncode == 0, f"block {index + 1} failed:\n{proc.stderr}"
    assert "agentbundle" not in proc.stderr


# --- AC-0003, and the frozen contract's AC-0043 / AC-0044 --------------------

def test_the_invocation_names_both_layout_scopes_and_the_right_paths(
    documented_run,
) -> None:
    """AC-0003 for the two configuration paths.

    The argv is parsed with the sender's own `build_parser`, so a flag renamed
    in the package fails here rather than at an adopter's first run. Comparing
    the guide's text against a literal list in this file would let the two agree
    while both disagreed with the sender.
    """
    sys.path.insert(0, str(_REPO / "packages/jsonl-otlp-exporter"))
    from jsonl_otlp_exporter.cli import build_parser

    _, argv, repo, home = documented_run(_blocks()[0])
    assert argv is not None, "the documented block did not invoke the sender"
    args = build_parser().parse_args(argv)

    assert Path(args.config) == repo / "agentbundle-layout.toml"
    assert Path(args.user_config) == home / ".agentbundle" / "agentbundle-layout.toml"
    # AC-0043 and AC-0044 are owned by `loop-telemetry-export`; this is their
    # first mechanical control, not a re-authoring of them.
    assert Path(args.input) == repo / ".loop-run" / "events.jsonl"
    assert Path(args.root) == repo
    assert Path(args.profile) == repo / Path(
        "packs/core/.apm/skills/work-loop/profiles/work-loop.toml"
    )


def test_the_documented_profile_path_is_the_one_this_repository_ships() -> None:
    """The guide's profile path must name a file that exists.

    Parsing argv proves the shape; only this proves the target is real, and a
    moved profile is the way the documented invocation breaks silently.
    """
    assert _PROFILE.is_file(), f"the guide names a profile that is absent: {_PROFILE}"


# --- AC-0002 -----------------------------------------------------------------

def test_the_retired_resolver_provides_no_module() -> None:
    """AC-0002's own observable, in an interpreter containing only this tree.

    `importlib.util.find_spec` is the criterion's literal wording, and it is run
    here rather than paraphrased. It must run in a **subprocess started with
    `-S`**, because the answer otherwise depends on the developer's environment
    rather than on the distribution under test. Measured 2026-09-16: an editable
    install of `agentbundle` pointing at a *sibling checkout* appends a finder to
    `sys.meta_path`; `agentbundle.__path__` holds only this worktree, so
    `PathFinder` correctly misses the deleted submodule, falls through to that
    appended finder, and resolves it from the other checkout -- reporting a
    module this repository does not ship. `-S` skips site processing, so no
    editable finder is installed, and `PYTHONPATH` supplies exactly this tree.

    `find_spec` rather than an import attempt: a tombstone module whose body
    raises `ModuleNotFoundError` would satisfy an import attempt while still
    occupying the path.

    **Why this stays in roster.** By `packages/AGENTS.md`'s test-home table it
    reads as a distribution-level assertion, and it derives its package
    directory from a path rather than needing a repository root -- so moving it
    to `packages/agentbundle/tests/` looks right. It cannot live there. AC-0004
    sweeps `packages/` for any file naming the retired module, and a control
    asserting the module's absence must name it. Moving it was tried and forced
    two exclusions AC-0004 does not admit -- the control itself, and the
    `.pytest_cache` node-id entry its own presence creates -- which makes the
    implementation wider than the criterion. Outside every swept tree, AC-0004
    holds exactly as written.
    """
    package_parent = _REPO / "packages/agentbundle"
    assert (package_parent / "agentbundle").is_dir(), "the package directory moved"
    env = dict(os.environ)
    env["PYTHONPATH"] = str(package_parent)
    probe = ("import importlib.util, sys;"
             "spec = importlib.util.find_spec('agentbundle.telemetry_layout');"
             "print('ABSENT' if spec is None else f'PRESENT {spec.origin}')")
    try:
        proc = subprocess.run(
            [sys.executable, "-S", "-c", probe],
            env=env, capture_output=True, text=True, timeout=60,
        )
    except subprocess.TimeoutExpired:
        pytest.fail(
            "the `-S` find_spec probe did not finish within 60s: "
            f"{sys.executable} -S -c {probe!r}"
        )
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == "ABSENT", proc.stdout.strip()


# --- AC-0004 -----------------------------------------------------------------

_LIVE_TREES = ("packages", "guides", "packs", "tools")
_RETIRED = "telemetry_layout"
_CHANGELOG = _REPO / "packages/agentbundle/CHANGELOG.md"


def _occurrences() -> list[Path]:
    """Every file under the live trees naming the retired module."""
    found: list[Path] = []
    for tree in _LIVE_TREES:
        for path in sorted((_REPO / tree).rglob("*")):
            if not path.is_file() or path.is_symlink():
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            if _RETIRED in text:
                found.append(path)
    return found


def test_no_live_surface_names_the_retired_module() -> None:
    """A deleted module with a surviving claim still misleads a reader.

    AC-0002 passes the moment the module is gone; this is the half that outlives
    the deletion, and it is why the two are separate criteria.
    """
    stragglers = [p.relative_to(_REPO) for p in _occurrences() if p != _CHANGELOG]
    assert stragglers == [], f"live surfaces still name {_RETIRED}: {stragglers}"


def test_every_changelog_mention_sits_in_an_admitted_release_context() -> None:
    """Two contexts, each admitted for its own reason.

    The `[0.45.0]` entry describes what that release shipped and stays accurate
    about it; a `### Removed` subsection is where this delivery must name what
    it removed. Every other position — a current-version `Added` or `Changed`
    entry still advertising the resolver — is a live stale claim and fails.
    """
    version = subsection = None
    offenders: list[str] = []
    for number, line in enumerate(
        _CHANGELOG.read_text(encoding="utf-8").splitlines(), start=1
    ):
        if line.startswith("## "):
            version, subsection = line, None
        elif line.startswith("### "):
            subsection = line
        elif _RETIRED in line:
            admitted = (version or "").startswith("## [0.45.0]") or (
                subsection or ""
            ).strip() == "### Removed"
            if not admitted:
                offenders.append(f"{number}: under {version!r} / {subsection!r}")
    assert offenders == [], f"changelog mentions outside an admitted context: {offenders}"


def test_the_changelog_records_the_removal() -> None:
    """Pairs with the rule above, which a changelog naming nothing also passes."""
    text = _CHANGELOG.read_text(encoding="utf-8")
    assert "### Removed" in text
    assert _RETIRED in text.split("### Removed", 1)[1].split("## ", 1)[0]


# --- the frozen contract's AC-0041, AC-0043 and AC-0044 ---------------------
#
# Three criteria in `docs/specs/loop-telemetry-export/spec.md`, ticked with no
# test behind them. They stay owned by that spec; this is their first control.
# The run below takes the argv the guide itself produces and feeds it to the
# real sender, with this repository's real work-loop profile copied into place,
# so the guide, the profile and the sender are checked against one another
# rather than each against a restatement in this file.

# AC-0044 says "a line the engine actually emitted", so the line is taken from
# the recorded corpus rather than authored here. A hand-written literal would
# satisfy every assertion below while proving nothing about the shape the engine
# produces -- which is the whole subject of that criterion.
_CORPUS = _REPO / "packs/core/tests/skills/work-loop/fixtures/event-corpus.jsonl"


def _engine_emitted_line() -> tuple[str, dict]:
    """The first recorded line whose `result` the shipped profile maps."""
    mapped = {"success", "failure"}
    for raw in _CORPUS.read_text(encoding="utf-8").splitlines():
        record = json.loads(raw)
        if record.get("result") in mapped:
            return raw + "\n", record
    raise AssertionError(
        f"no recorded line carries a result the profile maps: {_CORPUS}")


class _Recorder:
    def __init__(self):
        self.destinations = []
        self.bodies = []

    def factory(self, scheme, host, port, timeout, context):
        self.destinations.append((scheme, host, port))
        outer = self

        class _Resp:
            status = 200

            def __init__(self):
                self._p = b"{}"

            def getheaders(self):
                return []

            def read(self, n):
                c, self._p = self._p[:n], self._p[n:]
                return c

        class _Conn:
            def request(self, method, path, body=None, headers=None):
                outer.bodies.append(body)

            def getresponse(self):
                return _Resp()

            def close(self):
                pass

        return _Conn()

    def records(self):
        out = []
        for body in self.bodies:
            out.extend(json.loads(body)["resourceLogs"][0]["scopeLogs"][0]["logRecords"])
        return out

    def service_name(self):
        attrs = json.loads(self.bodies[0])["resourceLogs"][0]["resource"]["attributes"]
        return next(a["value"]["stringValue"] for a in attrs if a["key"] == "service.name")


@pytest.fixture()
def documented_send(documented_run, tmp_path):
    """Run the documented argv through the real sender, with the real profile."""
    sys.path.insert(0, str(_REPO / "packages/jsonl-otlp-exporter"))
    from jsonl_otlp_exporter import cli

    def send(repo_layout: str | None, user_layout: str | None):
        _, argv, repo, home = documented_run(_blocks()[0])
        assert argv is not None, "the documented block did not invoke the sender"
        # The guide names `<repo>/packs/core/.apm/.../work-loop.toml`; put this
        # repository's real profile exactly there, so a guide naming the wrong
        # path fails rather than being quietly given whatever is present.
        profile_at = repo / Path(
            "packs/core/.apm/skills/work-loop/profiles/work-loop.toml")
        profile_at.parent.mkdir(parents=True, exist_ok=True)
        profile_at.write_text(_PROFILE.read_text(encoding="utf-8"), encoding="utf-8")
        # The sole event lives only at the documented input path.
        line, _ = _engine_emitted_line()
        (repo / ".loop-run" / "events.jsonl").write_text(line, encoding="utf-8")
        if repo_layout is not None:
            (repo / "agentbundle-layout.toml").write_text(repo_layout, encoding="utf-8")
        if user_layout is not None:
            (home / ".agentbundle" / "agentbundle-layout.toml").write_text(
                user_layout, encoding="utf-8")
        rec = _Recorder()
        stream = io.StringIO()
        status = cli.main(argv, env={}, stream=stream, out=io.StringIO(),
                          connection_factory=rec.factory)
        return status, rec, stream.getvalue()

    return send


def test_the_repository_scope_wins_a_setting_both_files_declare(documented_send) -> None:
    """AC-0041 claims precedence, and only a conflicting pair can show it.

    A fixture whose two files declare different settings proves both arrive and
    stays green if the two flags are swapped.
    """
    status, rec, err = documented_send(
        '[telemetry]\nendpoint = "http://127.0.0.1:4318"\nservice_name = "repo-wins"\n',
        '[telemetry]\nendpoint = "http://127.0.0.1:4319"\nservice_name = "user-loses"\n',
    )
    assert status == 0, err
    assert len(rec.records()) == 1, err
    assert rec.destinations == [("http", "127.0.0.1", 4318)]
    assert rec.service_name() == "repo-wins"


def test_a_setting_the_repository_omits_falls_through_to_the_user_file(
    documented_send,
) -> None:
    """AC-0041's second half: the fallthrough, per setting rather than per file."""
    status, rec, err = documented_send(
        '[telemetry]\nendpoint = "http://127.0.0.1:4318"\n',
        '[telemetry]\nservice_name = "from-user"\n',
    )
    assert status == 0, err
    assert len(rec.records()) == 1, err
    assert rec.destinations == [("http", "127.0.0.1", 4318)]
    assert rec.service_name() == "from-user"


def test_the_printed_invocation_agrees_with_the_executed_one(documented_run) -> None:
    """AC-0003 over the guide's *second* block.

    The second block prints the command instead of running it, so the recording
    stub never sees it — and a wrong path in that block alone would ship while
    every other control here passed. Its printed line is shell-quoted, so it is
    split back with `shlex` and compared against the block that executes.
    """
    import shlex

    executed_proc, executed_argv, _, _ = documented_run(_blocks()[0])
    assert executed_argv is not None
    printed_proc, _, _, _ = documented_run(_blocks()[1])
    assert printed_proc.returncode == 0, printed_proc.stderr

    tokens = shlex.split(printed_proc.stdout.strip())
    assert tokens, f"the second block printed nothing: {printed_proc.stdout!r}"
    assert tokens[0] == "jsonl-otlp-export"
    assert tokens[1:] == executed_argv, (
        "the printed invocation and the executed one disagree; a reader copying "
        "the printed form would run a different command"
    )


def test_the_documented_input_and_profile_carry_a_real_event(documented_send) -> None:
    """AC-0043 and AC-0044, with an assertion that can fail.

    The only event in the tree sits at the documented `--input`, and the profile
    at the documented `--profile` is this repository's real one — so a guide
    naming either path wrongly sends nothing and reds here. The emitted record
    is then checked against what that profile declares.
    """
    status, rec, err = documented_send(
        '[telemetry]\nendpoint = "http://127.0.0.1:4318"\n', None)
    assert status == 0, err
    records = rec.records()
    assert len(records) == 1, f"the documented input yielded no record: {err}"
    emitted = records[0]
    _, source = _engine_emitted_line()

    # `at` -> timeUnixNano and `result` -> severityNumber are what the shipped
    # profile declares. The two expected values are established differently on
    # purpose: the instant is recomputed from the corpus record with `datetime`,
    # an implementation independent of the encoder's own RFC 3339 parse, while
    # the level is pinned below as a contract literal rather than read back from
    # the profile the encoder also reads.
    from datetime import datetime

    instant = datetime.fromisoformat(source["at"].replace("Z", "+00:00"))
    assert emitted["timeUnixNano"] == str(int(instant.timestamp()) * 10**9)

    # The severity level is written here rather than read back from the profile.
    # Deriving it from `severity_map` made this a tautology: the encoder reads
    # the same table, so changing `failure = 17` moved both sides together and
    # the case survived the mutation. `loop-telemetry-export`'s AC-0040 pins the
    # map to exactly `success = 9` and `failure = 17`, so these are contract
    # values and this is their only written form in this test.
    expected_severity = {"success": 9, "failure": 17}[source["result"]]
    assert emitted["severityNumber"] == expected_severity

    # AC-0044 also names the identity fields. `identity` is read from the
    # profile because it selects *which* fields to look for rather than
    # supplying the value being compared — the comparison is presence in the
    # emitted attributes, which the profile cannot satisfy on the encoder's
    # behalf.
    profile = tomllib.loads(_PROFILE.read_text(encoding="utf-8"))
    attributes = {a["key"]: a["value"] for a in emitted["attributes"]}
    for field in profile["identity"]:
        assert field in attributes, f"the profile declares {field} as identity"
