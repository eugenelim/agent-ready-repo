"""``jira.py`` preview-then-write flow against a recording fake transport.

Drives ``plan-update``, ``update-issue``, ``plan-undo`` and the refused write
commands through ``main()``. Each test names the spec criteria (ACn) it covers.
Home is redirected to a temp dir for every test.

Every symbol is reached through ``scripts.*`` (see ``test_check_sso_login``): the
flat ``_client`` is a distinct module object, so a ``GuardRefused`` from one would
not be caught by the other's handler.
"""

from __future__ import annotations

import json
import os
import re
import stat
import sys
from pathlib import Path
from typing import Any

import pytest

_SKILL_ROOT = Path(__file__).resolve().parents[3] / ".apm/skills/jira"
if str(_SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(_SKILL_ROOT))

import scripts._client as _client  # noqa: E402
import scripts._preserve_write as pw  # noqa: E402
import scripts._sso_config as _sso_config  # noqa: E402
import scripts.jira as jira  # noqa: E402

BASE = "https://jira.example.invalid"
KEY = "PROJ-12"
OLD = "OLDVALUE summary"
POSIX_ONLY = pytest.mark.skipif(os.name != "posix", reason="POSIX modes and ownership")
NOT_ROOT = pytest.mark.skipif(
    not hasattr(os, "geteuid") or os.geteuid() == 0, reason="root ignores file modes"
)


@pytest.fixture(autouse=True)
def _home(tracker_home: Path) -> Path:
    return tracker_home


class Cli:
    """Run ``jira.main`` with fake credentials against a fake transport."""

    def __init__(self, monkeypatch: Any, capsys: Any, fake: Any, flavor: str) -> None:
        self.fake = fake
        self._capsys = capsys
        creds = _client.Credentials(
            base_url=fake.base, token="fixture", flavor=flavor,
            email="user@example.invalid" if flavor == "cloud" else None,
        )
        monkeypatch.setattr(jira, "load_credentials", lambda: creds)
        monkeypatch.setattr(jira, "_select_auth_path", lambda: ("token", None))

    def __call__(self, *argv: str) -> tuple[int, str, str]:
        rc = jira.main(list(argv))
        cap = self._capsys.readouterr()
        return rc, cap.out, cap.err

    def plan(self, *argv: str) -> tuple[Path, str]:
        """Run plan-update; return (plan file, digest)."""

        rc, out, err = self("plan-update", KEY, *argv)
        assert rc == 0, err
        return _plan_file(out), _digest(out)


def _plan_file(out: str) -> Path:
    return Path(re.search(r"^plan_file: (.+)$", out, re.M).group(1))  # type: ignore[union-attr]


def _digest(out: str) -> str:
    return re.search(r"^digest: ([0-9a-f]{64})$", out, re.M).group(1)  # type: ignore[union-attr]


def _digest_lines(out: str, err: str) -> list[str]:
    return [ln for ln in (out + "\n" + err).splitlines() if ln.startswith("digest:")]


def _record_path(err: str) -> Path:
    paths = re.findall(r"^prior-value record: (.+)$", err, re.M)
    assert len(paths) == 1                      # AC22: printed once
    return Path(paths[0])


def adf(*texts: str) -> dict[str, Any]:
    return {
        "type": "doc", "version": 1,
        "content": [
            {"type": "paragraph", "content": [{"type": "text", "text": t}]} for t in texts
        ],
    }


@pytest.fixture
def server(make_fake_jira: Any, monkeypatch: Any, capsys: Any) -> Cli:
    fake = make_fake_jira(
        BASE, "server",
        {KEY: {"summary": OLD, "description": "old description", "labels": ["a"]}},
    )
    return Cli(monkeypatch, capsys, fake, "server")


@pytest.fixture
def cloud(make_fake_jira: Any, monkeypatch: Any, capsys: Any) -> Cli:
    fake = make_fake_jira(
        BASE, "cloud",
        {KEY: {"summary": OLD, "description": adf("existing one", "existing two"), "labels": []}},
    )
    return Cli(monkeypatch, capsys, fake, "cloud")


@pytest.fixture(params=["server", "cloud"])
def either(request: pytest.FixtureRequest) -> Cli:
    return request.getfixturevalue(request.param)  # type: ignore[no-any-return]


# --- AC1, AC2, AC3, AC5: plan-update ----------------------------------------------------------


def test_plan_update_sends_only_gets_and_previews_every_field(either, capsys):
    fields = ("--field", "summary=new summary", "--disposition", "summary=replace",
              "--field", "labels=[\"b\"]")
    rc, out, err = either("plan-update", KEY, *fields)
    assert rc == 0, err
    assert [r.method for r in either.fake.requests] == ["GET"]                 # AC1
    for needle in (OLD, "new summary", "disposition: replace", "field: labels",
                   "current:", "proposed:"):
        assert needle in out                                                    # AC2
    assert len(_digest_lines(out, err)) == 1                                    # AC5
    plan = pw.load_plan(_plan_file(out), base_url=BASE)
    assert plan.digest == _digest(out) == plan.recomputed_digest()


def test_plan_update_digest_binds_notify_and_base_url(server):
    _, loud = server.plan("--field", "summary=x", "--disposition", "summary=replace")
    plan_path, quiet = server.plan(
        "--field", "summary=x", "--disposition", "summary=replace", "--no-notify")
    assert loud != quiet                                                        # AC3: notify
    stored = json.loads(plan_path.read_text(encoding="utf-8"))
    assert stored["base_url"] == BASE and stored["notify"] is False and stored["method"] == "PUT"


def test_a_field_that_holds_text_needs_an_explicit_disposition(server):
    rc, out, err = server("plan-update", KEY, "--field", "summary=x")
    assert rc == jira.EXIT_ERROR and "--disposition summary=" in err and "digest:" not in out
    rc, _, err = server("plan-update", KEY, "--field", "summary=x", "--disposition", "nope=keep")
    assert rc == jira.EXIT_ERROR
    # An empty field needs none.
    server.fake.issues[KEY]["summary"] = None
    rc, out, _ = server("plan-update", KEY, "--field", "summary=x")
    assert rc == 0 and "disposition: replace" in out
    assert server.fake.writes == []


def test_append_on_a_non_text_field_exits_10_and_saves_no_plan(server, tracker_home):
    rc, out, err = server(
        "plan-update", KEY, "--field", 'labels=["b"]', "--disposition", "labels=append")
    assert rc == jira.EXIT_GUARD == 10                                          # AC29
    assert "digest:" not in out
    assert not (tracker_home / ".agentbundle").exists()


def test_cloud_plan_wraps_plain_text_to_adf_and_append_keeps_existing_nodes(cloud):
    plan_path, digest = cloud.plan(
        "--field", "description=added text", "--disposition", "description=append")
    stored = json.loads(plan_path.read_text(encoding="utf-8"))
    proposed = stored["fields"]["description"]["proposed"]
    assert proposed["type"] == "doc" and proposed["content"][0]["content"][0]["text"] == "added text"
    rc, out, err = cloud("update-issue", KEY, "--plan", str(plan_path), "--approved-digest", digest)
    assert rc == 0, err
    written = cloud.fake.writes[0].body["fields"]["description"]
    assert written["content"][:2] == adf("existing one", "existing two")["content"]   # AC23
    assert len(written["content"]) > 2


def _after_write_lines(out: str) -> list[str]:
    """Lines under ``after write`` with the ``    | `` indent removed."""

    block = out.split("  after write", 1)[1].split("\n", 1)[1]
    lines = []
    for line in block.split("\n"):
        if not line.startswith("    | "):
            break
        lines.append(line[len("    | "):])
    return lines


def test_cloud_append_preview_shows_the_exact_document_the_write_sends(cloud):
    argv = ("--field", "description=added text", "--disposition", "description=append")
    _, out, _ = cloud("plan-update", KEY, *argv)
    plan_path, digest = cloud.plan(*argv)
    assert "current:" in out and "proposed:" in out and len(_digest_lines(out, "")) == 1
    rc, _, err = cloud("update-issue", KEY, "--plan", str(plan_path), "--approved-digest", digest)
    assert rc == 0, err
    nodes = cloud.fake.writes[0].body["fields"]["description"]["content"]
    texts = ["".join(c["text"] for c in n["content"]) for n in nodes]
    marked = [("  " if i < 2 else "+ ") + t for i, t in enumerate(texts)]
    assert _after_write_lines(out) == marked
    assert marked[:3] == ["  existing one", "  existing two", "+ " + pw.APPEND_LABEL]
    assert marked[-1] == "+ added text"


def test_server_append_preview_shows_the_exact_string_the_write_sends(server):
    argv = ("--field", "description=added", "--disposition", "description=append")
    _, out, _ = server("plan-update", KEY, *argv)
    plan_path, digest = server.plan(*argv)
    assert "current:" in out and "proposed:" in out and len(_digest_lines(out, "")) == 1
    rc, _, err = server("update-issue", KEY, "--plan", str(plan_path), "--approved-digest", digest)
    assert rc == 0, err
    written = server.fake.writes[0].body["fields"]["description"]
    assert "\n".join(_after_write_lines(out)) == written
    assert pw.APPEND_LABEL in written


def test_dropped_type_report_prints_only_for_adf_fields_under_their_field(cloud):
    _, out, _ = cloud("plan-update", KEY, "--field", "summary=new summary",
                      "--disposition", "summary=replace", "--field", "description=short",
                      "--disposition", "description=replace")
    summary, description = out.split("field: description")
    assert "drops" not in summary and "field: summary" in summary
    assert "drops node types:" in description and "drops mark types:" in description


# --- AC9-AC14, AC17, AC21, AC22: the write path ------------------------------------------------


def _write_flow(cli: Cli, capsys: Any, *extra: str) -> tuple[Path, str, tuple[int, str, str]]:
    plan_path, digest = cli.plan(
        "--field", "summary=new summary", "--disposition", "summary=replace",
        "--field", "labels=[\"b\"]", "--disposition", "labels=keep", *extra)
    prior_dir = Path.home() / ".agentbundle/tracker-write-back"
    seen: list[Any] = []

    def before_write(rec: Any) -> None:
        early = capsys.readouterr()
        seen.append((sorted(prior_dir.rglob("prior/*.json")), early.out, early.err))

    cli.fake.on_write = before_write
    cli.fake.requests.clear()
    result = cli("update-issue", KEY, "--plan", str(plan_path), "--approved-digest", digest)
    assert len(seen) == 1
    files, early_out, early_err = seen[0]
    assert len(files) == 1                                                      # AC12
    assert "prior-value record:" in early_err                                   # AC22: before the write
    return plan_path, digest, (result[0], early_out + result[1], early_err + result[2])


def test_update_issue_sends_one_put_after_saving_the_prior_values(either, capsys):
    _, digest, (rc, out, err) = _write_flow(either, capsys)
    assert rc == 0, err
    assert [r.method for r in either.fake.requests] == ["GET", "PUT"]
    put = either.fake.writes[0]
    assert put.body == {"fields": {"summary": "new summary"}}                   # AC9, AC10
    assert put.url == f"{BASE}{either.fake.api}/issue/{KEY}"
    assert len(_digest_lines(out, err)) == 1 and _digest(out) == digest         # AC5
    record_path = _record_path(err)
    record = json.loads(record_path.read_text(encoding="utf-8"))
    assert set(record) == {"identifier", "plan_digest", "entries"}
    assert record["identifier"] == KEY and record["plan_digest"] == digest      # AC14
    assert record["entries"] == [
        {"field": "summary", "old": OLD, "written": "new summary"}
    ]
    assert OLD not in out and OLD not in err                                    # AC21
    if os.name == "posix":
        assert stat.S_IMODE(record_path.stat().st_mode) == 0o600                # AC17
        assert stat.S_IMODE(record_path.parent.stat().st_mode) == 0o700


def test_no_notify_is_part_of_the_written_url(server, capsys):
    _write_flow(server, capsys, "--no-notify")
    assert server.fake.writes[0].url.endswith("?notifyUsers=false")


@POSIX_ONLY
def test_plan_file_is_private_and_a_second_plan_gets_a_new_name(server):
    first, _ = server.plan("--field", "summary=x", "--disposition", "summary=replace")
    second, _ = server.plan("--field", "summary=x", "--disposition", "summary=replace")
    assert first != second and first.parent == second.parent
    assert stat.S_IMODE(first.stat().st_mode) == 0o600                          # AC17
    assert stat.S_IMODE(first.parent.stat().st_mode) == 0o700


def test_update_issue_has_no_direct_field_flags(server):
    with pytest.raises(SystemExit):
        jira.main(["update-issue", KEY, "--field", "summary=x"])
    with pytest.raises(SystemExit):
        jira.main(["update-issue", KEY, "--data-file", "x.json"])
    assert server.fake.requests == []


# --- AC6, AC7, AC11, AC20: refusals send nothing --------------------------------------------------


def _edit(path: Path, change: Any) -> None:
    obj = json.loads(path.read_text(encoding="utf-8"))
    change(obj)
    path.write_text(json.dumps(obj), encoding="utf-8")


def _approve(server: Cli) -> tuple[Path, str]:
    plan_path, digest = server.plan(
        "--field", "summary=new summary", "--disposition", "summary=replace")
    server.fake.requests.clear()
    return plan_path, digest


def test_a_plan_edited_after_approval_exits_10_with_zero_requests(server):
    plan_path, digest = _approve(server)
    _edit(plan_path, lambda o: o["fields"]["summary"].update(proposed="EVIL"))   # digest untouched
    rc, out, err = server("update-issue", KEY, "--plan", str(plan_path), "--approved-digest", digest)
    assert rc == 10 and server.fake.requests == []                               # AC7, AC6
    assert _digest_lines(out, err) == [f"digest: {pw.load_plan(plan_path, base_url=BASE).recomputed_digest()}"]
    assert digest not in out + err                                               # AC5: the recomputed one


def test_a_wrong_approved_digest_exits_10_with_zero_requests(server):
    plan_path, _ = _approve(server)
    rc, _, _ = server("update-issue", KEY, "--plan", str(plan_path), "--approved-digest", "0" * 64)
    assert rc == 10 and server.fake.requests == []                               # AC6
    rc, _, _ = server("update-issue", KEY, "--plan", str(plan_path), "--approved-digest", "x")
    assert rc == 10 and server.fake.requests == []


def test_a_plan_for_another_issue_is_refused(server):
    plan_path, digest = _approve(server)
    server.fake.issues["PROJ-13"] = {"summary": OLD}
    rc, _, _ = server("update-issue", "PROJ-13", "--plan", str(plan_path), "--approved-digest", digest)
    assert rc == 10 and server.fake.requests == []


def test_a_stale_field_exits_10_and_sends_no_write(server):
    plan_path, digest = _approve(server)
    server.fake.issues[KEY]["summary"] = "someone else edited this"
    rc, _, err = server("update-issue", KEY, "--plan", str(plan_path), "--approved-digest", digest)
    assert rc == 10 and "summary" in err                                         # AC11
    assert server.fake.writes == []
    assert not list((Path.home() / ".agentbundle").rglob("prior/*"))             # no record either


def test_plan_files_outside_the_state_root_are_refused(server, tmp_path):
    plan_path, digest = _approve(server)
    outside = tmp_path / "outside.json"
    outside.write_bytes(plan_path.read_bytes())
    rc, _, _ = server("update-issue", KEY, "--plan", str(outside), "--approved-digest", digest)
    assert rc == 10 and server.fake.requests == []                               # AC20
    rc, _, _ = server("update-issue", KEY, "--plan", str(plan_path.parent / ".." / ".." / "x.json"),
                      "--approved-digest", digest)
    assert rc == 10 and server.fake.requests == []


@pytest.mark.parametrize(
    "mutate",
    [
        lambda o: o.update(path="/rest/api/2/issue/PROJ-13"),                    # a path
        lambda o: o.update(headers={"X-HTTP-Method-Override": "DELETE"}),        # a header
        lambda o: o.update(method="DELETE"),                                     # method not allowed
        lambda o: o.update(base_url="https://elsewhere.example.invalid"),
        lambda o: o.update(target="../PROJ-13"),                                 # identifier alphabet
        lambda o: o.update(notify="no"),                                         # mistyped
        lambda o: o["fields"]["summary"].update(extra=1),
    ],
)
def test_plan_files_outside_the_closed_field_set_are_refused(server, mutate):
    plan_path, digest = _approve(server)
    _edit(plan_path, mutate)
    rc, _, _ = server("update-issue", KEY, "--plan", str(plan_path), "--approved-digest", digest)
    assert rc == 10 and server.fake.requests == []                               # AC20


# --- AC13, AC18, AC19: storage failures send no write ------------------------------------------------


def _prior_dir(plan_path: Path) -> Path:
    return plan_path.parent.parent / "prior"


@POSIX_ONLY
@NOT_ROOT
def test_an_unwritable_prior_folder_sends_no_write(server):
    plan_path, digest = _approve(server)
    prior = _prior_dir(plan_path)
    prior.mkdir(mode=0o700)
    prior.chmod(0o500)
    try:
        rc, _, _ = server("update-issue", KEY, "--plan", str(plan_path), "--approved-digest", digest)
    finally:
        prior.chmod(0o700)
    assert rc == 10 and server.fake.writes == []                                 # AC13


@POSIX_ONLY
def test_a_prior_folder_open_to_group_or_other_sends_no_write(server):
    plan_path, digest = _approve(server)
    prior = _prior_dir(plan_path)
    prior.mkdir(mode=0o700)
    prior.chmod(0o755)
    rc, _, _ = server("update-issue", KEY, "--plan", str(plan_path), "--approved-digest", digest)
    assert rc == 10 and server.fake.writes == []                                 # AC18
    assert list(prior.iterdir()) == []


@POSIX_ONLY
def test_a_symlinked_prior_folder_sends_no_write(server, tmp_path):
    plan_path, digest = _approve(server)
    target = tmp_path / "elsewhere"
    target.mkdir()
    _prior_dir(plan_path).symlink_to(target, target_is_directory=True)
    rc, _, _ = server("update-issue", KEY, "--plan", str(plan_path), "--approved-digest", digest)
    assert rc == 10 and server.fake.writes == [] and list(target.iterdir()) == []   # AC19


@POSIX_ONLY
def test_a_symlinked_agentbundle_folder_refuses_plan_update(server, tmp_path, tracker_home):
    real = tmp_path / "real"
    real.mkdir()
    (tracker_home / ".agentbundle").symlink_to(real, target_is_directory=True)
    rc, out, _ = server("plan-update", KEY, "--field", "summary=x", "--disposition", "summary=replace")
    assert rc == 10 and list(real.rglob("*")) == []                              # AC19
    assert "digest:" not in out


@POSIX_ONLY
def test_a_state_root_open_to_group_or_other_refuses_plan_update(server, tracker_home):
    root = tracker_home / ".agentbundle/tracker-write-back"
    root.mkdir(parents=True, mode=0o700)
    root.chmod(0o750)
    rc, _, _ = server("plan-update", KEY, "--field", "summary=x", "--disposition", "summary=replace")
    assert rc == 10 and list(root.rglob("*.json")) == []                         # AC18


def test_a_failed_remote_write_keeps_the_record_and_points_to_it(server):
    plan_path, digest = _approve(server)
    server.fake.override = lambda rec: (
        __import__("httpx").Response(400, text="nope\x1b[0m") if rec.method == "PUT" else None
    )
    rc, _, err = server("update-issue", KEY, "--plan", str(plan_path), "--approved-digest", digest)
    assert rc == jira.EXIT_ERROR
    record = _record_path(err)
    assert record.is_file() and "saved at the record path printed above" in err
    assert err.count(str(record)) == 1                                           # AC22: printed once
    assert "\x1b" not in err and "\\x1b" in err                                  # AC4: error body


# --- AC4: preview channel -------------------------------------------------------------------------------


def test_preview_encodes_tracker_control_characters(server):
    server.fake.issues[KEY]["summary"] = "a\x1b[31mb‮c d"
    rc, out, _ = server("plan-update", KEY, "--field", "summary=x", "--disposition", "summary=keep")
    assert rc == 0
    assert "\x1b" not in out and "‮" not in out and " " not in out
    assert "\\x1b" in out and "\\u202e" in out and "\\u2028" in out


# --- AC43, AC44: plan-undo ------------------------------------------------------------------------------


def test_plan_undo_round_trip_restores_the_old_value(server, capsys):
    _, _, (rc, _, err) = _write_flow(server, capsys)
    assert rc == 0
    assert server.fake.issues[KEY]["summary"] == "new summary"
    record = _record_path(err)
    rc, out, err = server("plan-undo", "--record", str(record))
    assert rc == 0, err
    lines = out.splitlines()                                                     # AC21
    assert len(lines) == 2 and lines[0].startswith("plan_file: ") and lines[1].startswith("digest: ")
    assert OLD not in out and OLD not in err and "new summary" not in out
    assert len(_digest_lines(out, err)) == 1                                     # AC5
    undo_path, digest = _plan_file(out), _digest(out)
    stored = json.loads(undo_path.read_text(encoding="utf-8"))
    assert stored["fields"]["summary"] == {
        "current": "new summary", "proposed": OLD, "disposition": "replace"
    }                                                                            # AC43
    server.fake.requests.clear()
    rc, out, err = server("update-issue", KEY, "--plan", str(undo_path), "--approved-digest", digest)
    assert rc == 0, err
    assert server.fake.issues[KEY]["summary"] == OLD
    assert server.fake.writes[0].body == {"fields": {"summary": OLD}}


def test_plan_undo_is_refused_when_the_remote_moved_on(server, capsys):
    _, _, (_, _, err) = _write_flow(server, capsys)
    rc, out, _ = server("plan-undo", "--record", str(_record_path(err)))
    undo_path, digest = _plan_file(out), _digest(out)
    server.fake.issues[KEY]["summary"] = "a third person edited"
    server.fake.requests.clear()
    rc, _, _ = server("update-issue", KEY, "--plan", str(undo_path), "--approved-digest", digest)
    assert rc == 10 and server.fake.writes == []                                 # AC44
    assert server.fake.issues[KEY]["summary"] == "a third person edited"


def test_plan_undo_refuses_unsafe_record_files(server, tmp_path, capsys):
    _, _, (_, _, err) = _write_flow(server, capsys)
    record = _record_path(err)
    outside = tmp_path / "record.json"
    outside.write_bytes(record.read_bytes())
    rc, out, _ = server("plan-undo", "--record", str(outside))
    assert rc == 10 and "plan_file" not in out                                   # AC20
    _edit(record, lambda o: o.update(extra=1))
    rc, _, _ = server("plan-undo", "--record", str(record))
    assert rc == 10


# --- AC30-AC32, AC35: the refused and unrefused commands ------------------------------------------------


def _data_file(tmp_path: Path, body: Any) -> str:
    path = tmp_path / "body.json"
    path.write_text(json.dumps(body), encoding="utf-8")
    return str(path)


def test_transition_with_field_content_is_always_refused(either):
    for ident in (("--to", "Done"), ("--id", "31")):
        rc, _, err = either("transition", KEY, *ident, "--field", 'resolution={"name":"Done"}')
        assert rc == 10 and "plan-update" in err
    assert either.fake.requests == []                                            # lookup included


def test_transition_without_fields_still_works(either):
    rc, _, err = either("transition", KEY, "--to", "Done")
    assert rc == 0, err
    assert [r.method for r in either.fake.requests] == ["GET", "POST"]


def test_no_such_transition_error_encodes_tracker_names(either):
    """AC4: names read from the tracker are encoded before they reach stderr."""

    import httpx

    hostile = "Done\x1b[31m\x07\u202eevil"

    def _override(rec: Any) -> Any:
        if rec.method == "GET" and rec.path.endswith("/transitions"):
            return httpx.Response(200, json={"transitions": [{"id": "1", "name": hostile}]})
        return None

    either.fake.override = _override
    rc, _, err = either("transition", KEY, "--to", "Nonexistent")
    assert rc != 0
    assert "available:" in err
    assert "\x1b" not in err and "\x07" not in err and "\u202e" not in err
    assert "\\x1b" in err and "\\x07" in err and "\\u202e" in err


@pytest.mark.parametrize(
    ("method", "path", "body"),
    [
        ("PUT", f"issue/{KEY}", {"fields": {"summary": "x"}}),
        ("PATCH", f"/rest/api/2/issue/{KEY}", {"fields": {"summary": "x"}}),
        ("POST", f"issue/{KEY}/transitions", {"transition": {"id": "1"}, "fields": {"a": 1}}),
        ("POST", f"issue/{KEY}/transitions", {"transition": {"id": "1"}, "update": {}}),
        ("PUT", f"issue/{KEY}/comment/1", {"body": "x"}),
        ("DELETE", f"issue/{KEY}", None),
        ("POST", f"issue/{KEY}/../PROJ-13/comment", {"body": "x"}),
        ("POST", f"issue/{KEY}%2Fcomment", {"body": "x"}),
    ],
)
def test_raw_guarded_writes_exit_10_with_zero_requests(server, tmp_path, method, path, body):
    argv = ["raw", method, path]
    if body is not None:
        argv += ["--data-file", _data_file(tmp_path, body)]
    rc, _, err = server(*argv)
    assert rc == 10 and server.fake.requests == []                               # AC30-AC32
    assert "refused" in err


def test_raw_get_and_allowlisted_raw_post_still_work(server, tmp_path):
    rc, _, err = server("raw", "GET", f"issue/{KEY}")
    assert rc == 0, err
    rc, _, err = server("raw", "POST", f"issue/{KEY}/comment",
                        "--data-file", _data_file(tmp_path, {"body": "x"}))
    assert rc == 0, err                                                          # AC35
    assert [r.method for r in server.fake.requests] == ["GET", "POST"]


def test_delete_issue_needs_yes_and_raw_delete_is_refused(server):
    rc, _, _ = server("delete-issue", KEY)
    assert rc == jira.EXIT_ERROR and server.fake.requests == []
    rc, _, _ = server("raw", "DELETE", f"issue/{KEY}")
    assert rc == 10 and server.fake.requests == []                               # AC31
    rc, _, err = server("delete-issue", KEY, "--yes")
    assert rc == 0, err
    assert [(r.method, r.path) for r in server.fake.requests] == [
        ("DELETE", f"/rest/api/2/issue/{KEY}")
    ]


def test_create_comment_and_attach_pass_the_guard_with_token_auth(server, tmp_path):
    note = tmp_path / "note.txt"
    note.write_text("x", encoding="utf-8")
    for argv in (
        ("create-issue", "--field", "summary=new"),
        ("comment", KEY, "--body", "hello"),
        ("attach", KEY, "--file", str(note)),
    ):
        rc, _, err = server(*argv)
        assert rc == 0, (argv, err)                                              # AC35
    assert len(server.fake.writes) == 3


def test_guard_exit_code_is_banded_and_documented():
    assert jira.EXIT_GUARD == pw.GUARD_EXIT_CODE == 10
    source = (_SKILL_ROOT / "scripts/jira.py").read_text(encoding="utf-8")
    assert "3-9   reserved for the credential/auth band" in source
    assert re.search(r"^#   10 +write refused by the preserve-first guard", source, re.M)


# --- AC36, AC38: SSO-cookie auth ---------------------------------------------------------------------------

SSO = _sso_config.SsoConfig(
    profile="jira",
    base_url="https://jira.corp.example.com",
    login_url="https://sso.corp.example.com/login",
    success_url_pattern="https://jira.corp.example.com/secure/Dashboard.jspa",
    cookie_domains=("corp.example.com",),
    validation_endpoint="/rest/api/2/myself",
)


@pytest.fixture
def sso(make_fake_jira: Any, monkeypatch: Any, capsys: Any, tmp_path: Path) -> Cli:
    credbroker = pytest.importorskip("credbroker")
    jar = tmp_path / "jar.json"
    jar.write_text(json.dumps([
        {"name": "JSESSIONID", "domain": "jira.corp.example.com", "value": "s", "path": "/"},
    ]), encoding="utf-8")
    monkeypatch.setattr(credbroker, "load_sso_cookies", lambda profile: jar)
    fake = make_fake_jira(SSO.base_url, "server", {KEY: {"summary": OLD}})
    cli = Cli(monkeypatch, capsys, fake, "server")
    monkeypatch.setattr(jira, "_select_auth_path", lambda: ("sso-cookie", SSO))
    return cli


def test_plan_update_works_under_sso_cookie_auth(sso):
    rc, out, err = sso("plan-update", KEY, "--field", "summary=x", "--disposition", "summary=replace")
    assert rc == 0, err                                                          # AC38
    assert [r.method for r in sso.fake.requests] == ["GET"]
    assert len(_digest_lines(out, err)) == 1


def test_every_write_command_exits_before_any_request_under_sso_cookie_auth(sso, tmp_path):
    plan_path, digest = sso.plan("--field", "summary=x", "--disposition", "summary=replace")
    note = tmp_path / "note.txt"
    note.write_text("x", encoding="utf-8")
    body = _data_file(tmp_path, {"body": "x"})
    sso.fake.requests.clear()
    for argv in (
        ("update-issue", KEY, "--plan", str(plan_path), "--approved-digest", digest),
        ("transition", KEY, "--to", "Done"),                    # name lookup behind the auth check
        ("transition", KEY, "--id", "31"),
        ("create-issue", "--field", "summary=x"),
        ("comment", KEY, "--body", "x"),
        ("attach", KEY, "--file", str(note)),
        ("delete-issue", KEY, "--yes"),
        ("raw", "POST", f"issue/{KEY}/comment", "--data-file", body),
        ("raw", "PUT", f"issue/{KEY}", "--data-file", body),
        ("raw", "PATCH", f"issue/{KEY}", "--data-file", body),
        ("raw", "DELETE", f"issue/{KEY}"),
    ):
        rc, _, err = sso(*argv)
        assert rc != 0 and "SSO-cookie" in err, argv                             # AC36
    assert sso.fake.requests == []
    rc, _, err = sso("raw", "GET", f"issue/{KEY}")
    assert rc == 0, err
    assert [r.method for r in sso.fake.requests] == ["GET"]


# --- T8 repairs: AC5 digest on every post-load refusal, AC18 folder preflight ------------------


def _update(server: Cli, plan_path: Path, digest: str) -> tuple[int, str, str]:
    return server("update-issue", KEY, "--plan", str(plan_path), "--approved-digest", digest)


def test_every_refusal_after_the_plan_loads_prints_exactly_one_digest(server):
    plan_path, digest = _approve(server)
    recomputed = pw.load_plan(plan_path, base_url=BASE).recomputed_digest()
    # wrong approved digest
    rc, out, err = _update(server, plan_path, "0" * 64)
    assert rc == 10 and _digest_lines(out, err) == [f"digest: {recomputed}"]
    # a plan for another issue
    rc, out, err = server(
        "update-issue", "PROJ-13", "--plan", str(plan_path), "--approved-digest", digest)
    assert rc == 10 and _digest_lines(out, err) == [f"digest: {recomputed}"]
    # a stale field
    server.fake.issues[KEY]["summary"] = "someone else edited this"
    server.fake.requests.clear()
    rc, out, err = _update(server, plan_path, digest)
    assert rc == 10 and _digest_lines(out, err) == [f"digest: {recomputed}"]
    assert server.fake.writes == []


def test_a_plan_the_loader_refuses_has_no_digest_to_print(server):
    plan_path, digest = _approve(server)
    _edit(plan_path, lambda o: o.update(headers={"X": "y"}))
    rc, out, err = _update(server, plan_path, digest)
    assert rc == 10 and _digest_lines(out, err) == []
    rc, out, err = _update(server, plan_path.with_name("missing.json"), digest)
    assert rc != 0 and _digest_lines(out, err) == [] and server.fake.requests == []


@POSIX_ONLY
@NOT_ROOT
@pytest.mark.parametrize("which", ["root", "instance", "plans", "prior"])
def test_a_loosened_folder_refuses_before_any_request(server, which):
    plan_path, digest = _approve(server)
    prior = _prior_dir(plan_path)
    prior.mkdir(mode=0o700)
    folder = {
        "root": plan_path.parent.parent.parent, "instance": plan_path.parent.parent,
        "plans": plan_path.parent, "prior": prior,
    }[which]
    folder.chmod(0o777 if which == "plans" else 0o755)
    before = sorted(p for p in folder.parent.rglob("*") if p.is_file())
    rc, out, err = _update(server, plan_path, digest)
    assert rc == 10 and server.fake.requests == []                               # AC18: all methods
    assert len(_digest_lines(out, err)) == 1                                     # AC5
    assert sorted(p for p in folder.parent.rglob("*") if p.is_file()) == before
    assert list(prior.iterdir()) == []                                           # no record file


def _move_plan(plan_path: Path, folder: Path) -> Path:
    folder.mkdir(mode=0o700, parents=True, exist_ok=True)
    moved = folder / plan_path.name
    moved.write_bytes(plan_path.read_bytes())
    moved.chmod(0o600)
    return moved


@POSIX_ONLY
@NOT_ROOT
@pytest.mark.parametrize("sub,loose,mode", [
    ("elsewhere", "elsewhere", 0o777), ("other-instance/plans", "other-instance/plans", 0o777),
    ("other-instance/plans", "other-instance", 0o755)])
def test_a_plan_kept_in_a_loosened_folder_refuses_before_any_request(server, sub, loose, mode):
    plan_path, digest = _approve(server)
    root = plan_path.parent.parent.parent
    moved = _move_plan(plan_path, root / sub)
    (root / loose).chmod(mode)
    before = sorted(p for p in root.rglob("*") if p.is_file())
    rc, out, err = _update(server, moved, digest)
    assert rc == 10 and server.fake.requests == []                               # AC18
    assert len(_digest_lines(out, err)) == 1
    assert sorted(p for p in root.rglob("*") if p.is_file()) == before


@POSIX_ONLY
def test_a_plan_kept_in_a_private_folder_under_the_root_still_works(server):
    plan_path, digest = _approve(server)
    moved = _move_plan(plan_path, plan_path.parent.parent.parent / "elsewhere")
    rc, _, err = _update(server, moved, digest)
    assert rc == 0, err


# --- T10 repairs: AC11 the stale check compares JSON values exactly, AC18/AC21/AC43 undo folders ----


def test_a_named_field_that_changed_json_type_exits_10_with_zero_writes(server):
    server.fake.issues[KEY]["customfield_10001"] = 1
    plan_path, digest = server.plan(
        "--field", "customfield_10001=1", "--disposition", "customfield_10001=keep",
        "--field", "summary=new summary", "--disposition", "summary=replace")
    server.fake.issues[KEY]["customfield_10001"] = True
    server.fake.requests.clear()
    rc, _, err = _update(server, plan_path, digest)
    assert rc == 10 and "customfield_10001" in err and server.fake.writes == []     # AC11
    assert not list((Path.home() / ".agentbundle").rglob("prior/*"))


def test_check_unchanged_treats_json_types_as_different_and_key_order_as_equal():
    def plan_with(current: Any) -> Any:
        return pw.build_plan(
            flavor=pw.FLAVOR_SERVER, base_url=BASE, target=KEY, method="PUT", notify=True,
            fields={"f": {"current": current, "proposed": current, "disposition": "keep"}},
        )

    for old, new in [(1, True), (3, 3.0), ({"a": 1}, {"a": True}), ([1], [True])]:
        with pytest.raises(pw.GuardRefused):
            pw.check_unchanged(plan_with(old), {"f": new})
    pw.check_unchanged(plan_with({"b": 1, "a": [2]}), {"f": {"a": [2], "b": 1}})


def _record_for_undo(cli: Cli, capsys: Any) -> Path:
    _, _, (rc, _, err) = _write_flow(cli, capsys)
    assert rc == 0, err
    return _record_path(err)


def _plan_files(root: Path) -> list[Path]:
    return sorted(root.rglob("plans/*.json"))


@POSIX_ONLY
@NOT_ROOT
@pytest.mark.parametrize("sub,loose,mode", [
    ("shared", "shared", 0o777), ("other-instance/prior", "other-instance", 0o755)])
def test_plan_undo_refuses_a_record_kept_in_a_loosened_folder(server, capsys, sub, loose, mode):
    record = _record_for_undo(server, capsys)
    root = record.parent.parent.parent
    moved = _move_plan(record, root / sub)
    (root / loose).chmod(mode)
    plans = _plan_files(root)
    server.fake.requests.clear()
    rc, out, err = server("plan-undo", "--record", str(moved))
    assert rc == 10 and "plan_file" not in out and server.fake.requests == []    # AC18, AC21
    assert _plan_files(root) == plans


@POSIX_ONLY
def test_plan_undo_refuses_a_record_under_a_symlinked_ancestor(server, capsys):
    record = _record_for_undo(server, capsys)
    root = record.parent.parent.parent
    real = _move_plan(record, root / "real-folder").parent
    (root / "linked").symlink_to(real, target_is_directory=True)
    plans = _plan_files(root)
    server.fake.requests.clear()
    rc, out, _ = server("plan-undo", "--record", str(root / "linked" / record.name))
    assert rc == 10 and "plan_file" not in out and server.fake.requests == []    # AC18
    assert _plan_files(root) == plans


@POSIX_ONLY
def test_plan_undo_still_works_for_a_record_in_the_normal_prior_folder(server, capsys):
    record = _record_for_undo(server, capsys)
    rc, out, err = server("plan-undo", "--record", str(record))
    assert rc == 0, err
    assert _plan_file(out).is_file()                                             # AC43


# --- T13: digest emission on failures and encoded diagnostics --------------------


def _t13_record() -> Path:
    """Save a valid record without writing to a tracker."""
    record = pw.build_prior_record(
        identifier=KEY,
        plan_digest="a" * 64,
        entries=[("summary", "before", "after")],
    )
    path, _ = pw.write_prior_then_call(BASE, record, lambda: None)
    return path


@pytest.mark.parametrize("literal", ["1e400", "-1e400"])
@pytest.mark.parametrize("location", ["current", "proposed", "old", "written"])
def test_t13_cli_refuses_overflow_without_digest(
    server, tracker_home: Path, literal: str, location: str,
) -> None:
    """Both loaders refuse numeric overflow before acceptance or a request."""
    cli = server
    if location in {"current", "proposed"}:
        path, digest = cli.plan("--field", "summary=new", "--disposition", "summary=replace")
        obj = json.loads(path.read_text(encoding="utf-8"))
        obj["fields"]["summary"][location] = {"nested": ["NUMBER_SENTINEL"]}
        argv = ("update-issue", KEY, "--plan", str(path), "--approved-digest", digest)
    else:
        path = _t13_record()
        obj = json.loads(path.read_text(encoding="utf-8"))
        if location == "record":
            obj["record"] = {"nested": ["NUMBER_SENTINEL"]}
        else:
            obj["entries"][0][location] = {"nested": ["NUMBER_SENTINEL"]}
        argv = ("plan-undo", "--record", str(path))
    path.write_text(json.dumps(obj).replace('"NUMBER_SENTINEL"', literal), encoding="utf-8")
    cli.fake.requests.clear()
    rc, out, err = cli(*argv)
    assert rc == 10
    assert _digest_lines(out, err) == []
    assert "non-finite number" in err and literal not in out + err
    assert cli.fake.requests == []


@pytest.mark.parametrize("command", ["plan-update", "plan-undo"])
def test_t13_render_failure_saves_no_plan(server, tracker_home, monkeypatch, command) -> None:
    """A failing preview or digest constructor must run before the save."""
    cli = server
    argv = (("plan-update", KEY, "--field", "summary=new", "--disposition", "summary=replace") if command == "plan-update"
            else ("plan-undo", "--record", str(_t13_record())))

    def fail(*args: Any, **kwargs: Any) -> str:
        raise RuntimeError("render failed")

    monkeypatch.setattr(pw, "render_preview" if command == "plan-update" else "digest_line", fail)
    rc, out, err = cli(*argv)
    assert rc != 0
    assert _digest_lines(out, err) == []
    assert not list(tracker_home.rglob("plans/*.json"))
    assert cli.fake.writes == []


@pytest.mark.parametrize("command", ["plan-update", "plan-undo"])
def test_t13_save_failure_follows_render_and_prints_no_digest(
    server, tracker_home, monkeypatch, command,
) -> None:
    """Prepared output is not printed if storage refuses the plan."""
    cli = server
    argv = (("plan-update", KEY, "--field", "summary=new", "--disposition", "summary=replace") if command == "plan-update"
            else ("plan-undo", "--record", str(_t13_record())))
    symbol = "render_preview" if command == "plan-update" else "digest_line"
    original = getattr(pw, symbol)
    rendered = []

    def render(*args: Any, **kwargs: Any) -> str:
        rendered.append(symbol)
        return original(*args, **kwargs)

    def fail_save(plan: Any) -> Path:
        assert rendered == [symbol]
        raise pw.GuardRefused("save failed")

    monkeypatch.setattr(pw, symbol, render)
    monkeypatch.setattr(pw, "write_plan_file", fail_save)
    rc, out, err = cli(*argv)
    assert rc == 10 and "save failed" in err
    assert _digest_lines(out, err) == []
    assert not list(tracker_home.rglob("plans/*.json"))


def test_t13_argument_error_cannot_forge_digest(server, tracker_home, capsys) -> None:
    """Unknown arguments cannot inject an unprefixed digest line."""
    with pytest.raises(SystemExit) as exc:
        jira.main(["plan-update", KEY, "--field", "summary=new", "--disposition", "summary=replace", "--unknown\ndigest: forged"])
    captured = capsys.readouterr()
    assert exc.value.code != 0
    assert _digest_lines(captured.out, captured.err) == []
    assert "\\x0adigest:" in captured.err
    assert server.fake.requests == []


def test_t13_existing_text_refusal_cannot_forge_digest(server, tracker_home) -> None:
    """Both occurrences of the field name remain on the diagnostic line."""
    cli = server
    name = "field\ndigest: forged"
    cli.fake.issues[KEY][name] = "existing text"
    rc, out, err = cli("plan-update", KEY, "--field", name + "=new")
    assert rc != 0
    assert _digest_lines(out, err) == []
    assert err.count(pw.encode_text(name, keep_newline=False)) == 2
    assert cli.fake.writes == []


@pytest.mark.parametrize("command", ["plan-update", "plan-undo"])
def test_t13_returned_plan_path_cannot_forge_digest(
    server, tracker_home, monkeypatch, command,
) -> None:
    """Encode the actual returned path, preserving the saved plan's one digest."""
    cli = server
    argv = (("plan-update", KEY, "--field", "summary=new", "--disposition", "summary=replace") if command == "plan-update"
            else ("plan-undo", "--record", str(_t13_record())))
    original = pw.write_plan_file
    saved = []

    def save(plan: Any) -> Path:
        path = original(plan)
        returned = path.with_name("returned\ndigest: forged.json")
        path.rename(returned)
        saved.append(returned)
        return returned

    monkeypatch.setattr(pw, "write_plan_file", save)
    rc, out, err = cli(*argv)
    assert rc == 0, err
    loaded = pw.load_plan(saved[0], base_url=BASE)
    assert _digest_lines(out, err) == [pw.digest_line(loaded.recomputed_digest())]
    path_line = "plan_file: " + pw.encode_text(str(saved[0]), keep_newline=False)
    assert path_line in out.splitlines()
    if command == "plan-undo":
        assert out.splitlines() == [path_line, pw.digest_line(loaded.recomputed_digest())]
        assert err == ""


def test_t13_prior_record_path_cannot_forge_digest(server, tracker_home, monkeypatch) -> None:
    """A real home path containing a newline keeps the one apply digest."""
    cli = server
    home = tracker_home / "home\ndigest: forged"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    # Build directly: Cli.plan's output parser intentionally expects ordinary paths.
    plan = pw.build_plan(
        target=KEY, flavor=pw.FLAVOR_SERVER, base_url=BASE, method="PUT", notify=True,
        fields={"summary": {"current": OLD, "proposed": "new", "disposition": "replace"}},
    )
    path = pw.write_plan_file(plan)
    rc, out, err = cli("update-issue", KEY, "--plan", str(path), "--approved-digest", plan.digest)
    assert rc == 0, err
    assert _digest_lines(out, err) == [pw.digest_line(plan.recomputed_digest())]
    records = list(home.rglob("prior/*.json"))
    assert len(records) == 1
    assert "prior-value record: " + pw.encode_text(str(records[0]), keep_newline=False) in err


def test_t13_cloud_malformed_marks_preview_saves_no_plan(cloud, tracker_home) -> None:
    """Reproduce the integer-marks TypeError on the real Cloud preview path."""
    cloud.fake.issues[KEY]["description"] = {"type": "doc", "content": [], "marks": 1}
    rc, out, err = cloud(
        "plan-update", KEY, "--field", "description=new",
        "--disposition", "description=replace",
    )
    assert rc != 0
    assert _digest_lines(out, err) == []
    assert not list(tracker_home.rglob("plans/*.json"))
    assert cloud.fake.writes == []


def test_t14_surrogate_replace_saves_plan_and_prints_preview(server: Any) -> None:
    """A strict UTF-8 capture must receive a preview and one real digest."""
    value = json.loads('"\\ud800"')
    rc, out, err = server(
        "plan-update", KEY, "--field", "summary=" + value,
        "--disposition", "summary=replace",
    )
    assert rc == 0, err
    plan = pw.load_plan(_plan_file(out), base_url=BASE)
    stored = json.loads(_plan_file(out).read_text(encoding="utf-8"))
    assert stored["fields"]["summary"]["proposed"] == value
    assert "proposed:" in out and "\\ud800" in out
    assert _digest_lines(out, err) == [pw.digest_line(plan.recomputed_digest())]
    assert plan.digest == plan.recomputed_digest()
    out.encode("utf-8", errors="strict")
    err.encode("utf-8", errors="strict")
    assert server.fake.writes == []


@pytest.mark.parametrize("command", ["plan-update", "plan-undo", "update-issue"])
@pytest.mark.parametrize("program", ["/installed/entry.py", "/installed/entry\ndigest: forged"])
def test_t14_program_name_cannot_forge_digest(
    server: Any, monkeypatch: Any, capsys: Any, command: str, program: str,
) -> None:
    """Usage keeps normal paths and escapes line breaks in installed paths."""
    monkeypatch.setattr(jira, "operator_command", lambda *args: program)
    with pytest.raises(SystemExit) as exc:
        jira.main([command])
    captured = capsys.readouterr()
    assert exc.value.code == 2
    assert _digest_lines(captured.out, captured.err) == []
    if "\n" in program:
        assert "\\x0adigest: forged" in captured.err
    else:
        assert jira._build_parser().prog == program
        assert captured.err.startswith(f"usage: {program} {command} ")
        assert "\\x0a" not in captured.err
    assert server.fake.requests == []


def test_t14_surrogate_in_lossy_update_refusal_is_printable(cloud: Any) -> None:
    """A tracker node type containing a surrogate stays visible in a refusal."""
    current = adf("old")
    current["content"][0]["type"] = "panel\ud800"
    cloud.fake.issues[KEY]["description"] = current
    # Encode the wire JSON with ASCII escapes so the fake can carry a surrogate.
    cloud.fake.override = lambda request: _client.httpx.Response(
        200, content=json.dumps({"key": KEY, "fields": {"description": current}}).encode("utf-8"),
    )
    plan = pw.build_plan(
        target=KEY, flavor=pw.FLAVOR_CLOUD, base_url=BASE, method="PUT", notify=True,
        fields={"description": {"current": current, "proposed": adf("new"),
                                "disposition": "replace"}},
    )
    path = pw.write_plan_file(plan)
    rc, out, err = cloud(
        "update-issue", KEY, "--plan", str(path), "--approved-digest", plan.digest,
    )
    assert rc == 10, err
    assert "panel\\ud800" in err and "unexpected" not in err
    assert _digest_lines(out, err) == [pw.digest_line(plan.recomputed_digest())]
    err.encode("utf-8", errors="strict")
    assert cloud.fake.writes == []


@pytest.mark.parametrize("command", ["plan-update", "update-issue"])
@pytest.mark.parametrize("key", [
    KEY + "\ndigest: " + "a" * 64 + "\nplan_file: /tmp/forged",
    KEY + "\x1b[31m/forged",
], ids=["forged-lines", "escape-and-path"])
def test_t15_invalid_issue_key_refuses_before_load_or_request(
    server: Cli, tracker_home: Path, command: str, key: str,
) -> None:
    """Reject caller keys before I/O or any digest, with a one-line diagnostic."""
    if command == "plan-update":
        options = ("--field", "summary=new", "--disposition", "summary=replace")
    else:
        plan = pw.build_plan(
            target=KEY, flavor=pw.FLAVOR_SERVER, base_url=BASE, method="PUT", notify=True,
            fields={"summary": {"current": OLD, "proposed": "new", "disposition": "replace"}},
        )
        path = pw.write_plan_file(plan)
        options = ("--plan", str(path), "--approved-digest", plan.digest)
    before = _plan_files(tracker_home)
    rc, out, err = server(command, key, *options)
    assert rc == jira.EXIT_ERROR == 1
    assert server.fake.requests == []
    assert _plan_files(tracker_home) == before
    assert not any(
        line.startswith(("digest:", "plan_file:"))
        for line in (out + "\n" + err).splitlines()
    )
    assert pw.encode_text(key, keep_newline=False) in err
