"""``jira_align.py`` preview-then-write flow against a recording fake transport.

Drives ``plan-update``, ``update``, ``plan-undo`` and the refused write commands through
``main()``. Each test names the spec criteria (ACn) it covers. Home is redirected to a
temp dir for every test.

Every symbol is reached through the ``align_skill_scripts`` package so the CLI and the
tests share one ``GuardRefused`` class.
"""

from __future__ import annotations

import json
import os
import re
import stat
from pathlib import Path
from typing import Any

import align_skill_scripts._client as _client
import align_skill_scripts._preserve_write as pw
import align_skill_scripts.jira_align as align
import httpx
import pytest

BASE = "https://align.example.invalid"
RES, ITEM = "epics", "5"
TARGET = f"{RES}/{ITEM}"
OLD = "OLDVALUE title"
SKILL_ROOT = Path(__file__).resolve().parents[3] / ".apm/skills/jira-align"
POSIX_ONLY = pytest.mark.skipif(os.name != "posix", reason="POSIX modes and ownership")
NOT_ROOT = pytest.mark.skipif(
    not hasattr(os, "geteuid") or os.geteuid() == 0, reason="root ignores file modes"
)


@pytest.fixture(autouse=True)
def _home(tracker_home: Path) -> Path:
    return tracker_home


class Cli:
    """Run ``jira_align.main`` with fake credentials against a fake transport."""

    def __init__(self, monkeypatch: Any, capsys: Any, fake: Any) -> None:
        self.fake = fake
        self._capsys = capsys
        creds = _client.Credentials(base_url=fake.base, token="fixture", flavor="onprem")
        monkeypatch.setattr(align, "load_credentials", lambda: creds)

    def __call__(self, *argv: str) -> tuple[int, str, str]:
        rc = align.main(list(argv))
        cap = self._capsys.readouterr()
        return rc, cap.out, cap.err

    def plan(self, *argv: str) -> tuple[Path, str]:
        """Run plan-update; return (plan file, digest)."""

        rc, out, err = self("plan-update", RES, ITEM, *argv)
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


def _held() -> dict[str, Any]:
    return {
        "id": 5, "title": OLD, "description": "old description", "state": "Open", "points": 3,
        "owner": "someone",
    }


@pytest.fixture
def cli(make_fake_align: Any, monkeypatch: Any, capsys: Any) -> Cli:
    return Cli(monkeypatch, capsys, make_fake_align(BASE, {TARGET: _held()}))


REPLACE_TITLE = ("--field", "title=new title", "--disposition", "title=replace")


@pytest.mark.parametrize("resource,item", [
    (RES + "\ndigest: " + "a" * 64 + "\nplan_file: /tmp/forged", ITEM),
    (RES, ITEM + "\ndigest: " + "a" * 64 + "\nplan_file: /tmp/forged"),
    (RES + "\x1b[31m/forged", ITEM),
    (RES, ITEM + "\x1b[31m/forged"),
], ids=["resource-lines", "id-lines", "resource-escape", "id-escape"])
def test_t15_invalid_align_identifier_refuses_before_request(
    cli: Cli, tracker_home: Path, resource: str, item: str,
) -> None:
    """Keep Align's early resource and id validation ahead of every GET."""
    rc, out, err = cli("plan-update", resource, item, *REPLACE_TITLE)
    assert rc == align.EXIT_ERROR == 1
    assert cli.fake.requests == []
    assert not list(tracker_home.rglob("plans/*.json"))
    assert not any(
        line.startswith(("digest:", "plan_file:"))
        for line in (out + "\n" + err).splitlines()
    )
    assert "RESOURCE and ID must match" in err


# --- AC1, AC2, AC3, AC5, AC39: plan-update ----------------------------------------------------


def test_plan_update_sends_only_gets_and_previews_every_field(cli):
    fields = (*REPLACE_TITLE, "--field", "points=5")
    rc, out, err = cli("plan-update", RES, ITEM, *fields)
    assert rc == 0, err
    assert [r.method for r in cli.fake.requests] == ["GET"]                      # AC1
    for needle in (OLD, "new title", "disposition: replace", "field: points",
                   "current:", "proposed:", "method: PATCH"):
        assert needle in out                                                      # AC2
    assert len(_digest_lines(out, err)) == 1                                      # AC5
    plan = pw.load_plan(_plan_file(out), base_url=BASE)
    assert plan.digest == _digest(out) == plan.recomputed_digest()
    assert plan.target == TARGET and plan.flavor == "align"


def test_plan_update_records_patch_by_default_and_put_with_replace_record(cli):
    patch_path, patch_digest = cli.plan(*REPLACE_TITLE)
    put_path, put_digest = cli.plan(*REPLACE_TITLE, "--replace-record")
    assert json.loads(patch_path.read_text(encoding="utf-8"))["method"] == "PATCH"   # AC39
    assert json.loads(put_path.read_text(encoding="utf-8"))["method"] == "PUT"
    assert patch_digest != put_digest                                             # AC3: method bound
    assert cli.fake.writes == []


def test_a_patch_plan_lists_no_omitted_fields(cli):
    _, out, _ = cli("plan-update", RES, ITEM, *REPLACE_TITLE)
    assert "omitted" not in out


def test_a_put_plan_lists_every_record_field_the_body_omits(cli):
    fields = (*REPLACE_TITLE, "--field", "points=3", "--disposition", "points=keep")
    rc, out, err = cli("plan-update", RES, ITEM, *fields, "--replace-record")
    assert rc == 0, err
    assert "method: PUT" in out
    section = out.split("omitted from the PUT body", 1)[1].split("target:", 1)[0]  # AC39
    listed = set(re.findall(r"^  - (\S+)(?: \(.*\))?$", section, re.M))
    # The body holds only ``title``: every other field of the record as read is cleared.
    assert listed == {"id", "description", "state", "points", "owner"}
    assert "  - id (the record's identifier)" in section
    assert "title" not in listed
    assert len(_digest_lines(out, err)) == 1                                      # AC5
    assert out.index("omitted from the PUT body") < out.index("digest: ")       # shown before approval
    assert [r.method for r in cli.fake.requests] == ["GET"]


def _after_write_block(out: str) -> str:
    """The text under ``after write`` with the ``    | `` indent removed."""

    block = out.split("  after write", 1)[1].split("\n", 1)[1]
    lines = []
    for line in block.split("\n"):
        if not line.startswith("    | "):
            break
        lines.append(line[len("    | "):])
    return "\n".join(lines)


def test_an_append_preview_shows_the_exact_string_the_update_writes(cli):
    plan_path, digest = cli.plan(
        "--field", "description=added", "--disposition", "description=append")
    _, out, _ = cli("plan-update", RES, ITEM, "--field", "description=added",
                    "--disposition", "description=append")
    assert "current:" in out and "proposed:" in out and len(_digest_lines(out, "")) == 1
    rc, _, err = cli("update", RES, ITEM, "--plan", str(plan_path), "--approved-digest", digest)
    assert rc == 0, err
    written = cli.fake.writes[0].body["description"]
    assert _after_write_block(out) == written
    assert pw.APPEND_LABEL in written


def test_an_align_plan_prints_no_dropped_type_report(cli):
    _, out, _ = cli("plan-update", RES, ITEM, *REPLACE_TITLE)
    assert "drops" not in out


def test_a_field_that_holds_text_needs_an_explicit_disposition(cli):
    rc, out, err = cli("plan-update", RES, ITEM, "--field", "title=x")
    assert rc == align.EXIT_ERROR and "--disposition title=" in err and "digest:" not in out
    rc, _, _ = cli("plan-update", RES, ITEM, "--field", "title=x", "--disposition", "nope=keep")
    assert rc == align.EXIT_ERROR
    cli.fake.records[TARGET]["title"] = None                  # an empty field needs none
    rc, out, _ = cli("plan-update", RES, ITEM, "--field", "title=x")
    assert rc == 0 and "disposition: replace" in out
    assert cli.fake.writes == []


def test_append_on_a_non_text_field_exits_10_and_saves_no_plan(cli, tracker_home):
    rc, out, _ = cli(
        "plan-update", RES, ITEM, "--field", "points=2", "--disposition", "points=append")
    assert rc == align.EXIT_GUARD == 10                                           # AC29
    assert "digest:" not in out
    assert not (tracker_home / ".agentbundle").exists()


def test_a_bad_resource_or_id_sends_nothing(cli):
    for argv in (("plan-update", "ep ics", "5"), ("plan-update", "epics", "0"),
                 ("plan-update", "epics", "5/children"), ("plan-update", "../epics", "5")):
        rc, out, _ = cli(*argv, "--field", "title=x")
        assert rc != 0 and "digest:" not in out
    assert cli.fake.requests == []


def test_update_has_no_method_flag_and_no_direct_field_flags(cli):
    for extra in (["--method", "PATCH"], ["--method", "PUT"], ["--field", "title=x"],
                  ["--data-file", "x.json"]):
        with pytest.raises(SystemExit):
            align.main(["update", RES, ITEM, "--plan", "p.json", "--approved-digest", "a" * 64,
                        *extra])
    with pytest.raises(SystemExit):
        align.main(["update", RES, ITEM, "--field", "title=x"])
    assert cli.fake.requests == []


# --- AC9-AC14, AC17, AC21, AC22, AC40, AC41: the write path ----------------------------------------


def _write_flow(cli: Cli, capsys: Any, *extra: str) -> tuple[Path, str, tuple[int, str, str]]:
    plan_path, digest = cli.plan(
        *REPLACE_TITLE, "--field", "points=9", "--disposition", "points=keep", *extra)
    prior_dir = Path.home() / ".agentbundle/tracker-write-back"
    seen: list[Any] = []

    def before_write(rec: Any) -> None:
        early = capsys.readouterr()
        seen.append((sorted(prior_dir.rglob("prior/*.json")), early.out, early.err))

    cli.fake.on_write = before_write
    cli.fake.requests.clear()
    result = cli("update", RES, ITEM, "--plan", str(plan_path), "--approved-digest", digest)
    assert len(seen) == 1
    files, early_out, early_err = seen[0]
    assert len(files) == 1                                                        # AC12
    assert "prior-value record:" in early_err                                     # AC22: before the write
    return plan_path, digest, (result[0], early_out + result[1], early_err + result[2])


def test_update_sends_one_patch_after_saving_the_prior_values(cli, capsys):
    before = dict(_held())
    _, digest, (rc, out, err) = _write_flow(cli, capsys)
    assert rc == 0, err
    assert [r.method for r in cli.fake.requests] == ["GET", "PATCH", "GET"]       # write then re-read
    patch = cli.fake.writes[0]
    assert patch.body == {"title": "new title"}                                   # AC9, AC10
    assert patch.url == f"{BASE}/rest/align/api/2/{TARGET}"
    assert len(_digest_lines(out, err)) == 1 and _digest(out) == digest           # AC5
    record_path = _record_path(err)
    record = json.loads(record_path.read_text(encoding="utf-8"))
    assert set(record) == {"identifier", "plan_digest", "entries", "record"}
    assert record["identifier"] == TARGET and record["plan_digest"] == digest     # AC14
    assert record["entries"] == [{"field": "title", "old": OLD, "written": "new title"}]
    assert record["record"] == before                                             # AC41: full record as read
    assert OLD not in out and OLD not in err                                      # AC21
    if os.name == "posix":
        assert stat.S_IMODE(record_path.stat().st_mode) == 0o600                  # AC17
        assert stat.S_IMODE(record_path.parent.stat().st_mode) == 0o700


def test_the_write_sends_exactly_the_method_the_approved_plan_records(cli, capsys):
    _, _, (rc, _, err) = _write_flow(cli, capsys, "--replace-record")
    assert rc == 0, err
    assert [r.method for r in cli.fake.writes] == ["PUT"]                         # AC40
    assert cli.fake.writes[0].body == {"title": "new title"}


def test_a_patch_plan_edited_to_put_is_refused_with_zero_requests(cli):
    plan_path, digest = _approve(cli)
    _edit(plan_path, lambda o: o.update(method="PUT"))        # digest and approval unchanged
    rc, _, _ = cli("update", RES, ITEM, "--plan", str(plan_path), "--approved-digest", digest)
    assert rc == 10 and cli.fake.requests == []                                   # AC7, AC40


def test_append_keeps_the_original_text_as_a_byte_exact_prefix(cli):
    original = cli.fake.records[TARGET]["description"]
    cli.fake.records[TARGET]["description"] = original = original + " ünï   ©"
    plan_path, digest = cli.plan(
        "--field", "description=added", "--disposition", "description=append")
    rc, _, err = cli("update", RES, ITEM, "--plan", str(plan_path), "--approved-digest", digest)
    assert rc == 0, err
    written = cli.fake.writes[0].body["description"]
    assert written.encode().startswith(original.encode()) and len(written) > len(original)   # AC25
    assert "added" in written


def test_prior_values_are_saved_even_when_the_remote_write_fails(cli):
    plan_path, digest = _approve(cli)
    cli.fake.override = lambda rec: (
        httpx.Response(400, text="nope\x1b[0m") if rec.method == "PATCH" else None
    )
    rc, _, err = cli("update", RES, ITEM, "--plan", str(plan_path), "--approved-digest", digest)
    assert rc == align.EXIT_ERROR
    record = _record_path(err)
    assert record.is_file() and "saved at the record path printed above" in err
    assert err.count(str(record)) == 1                                            # AC22: printed once
    assert "\x1b" not in err and "\\x1b" in err                                   # AC4: error body


# --- AC42: post-write drift report ------------------------------------------------------------------


def test_a_patch_that_changes_an_unnamed_field_is_reported_on_stderr(cli, capsys):
    def touch(held: dict[str, Any]) -> None:
        held["state"] = "Changed\x1b[0m by server"
        held["revision"] = 2

    cli.fake.after_write = touch
    _, _, (rc, out, err) = _write_flow(cli, capsys)
    assert rc == 0, err
    drift = [ln for ln in err.splitlines() if ln.startswith("changed outside the plan:")]
    names = {ln.split(":", 2)[1].strip() for ln in drift}
    assert names == {"state", "revision"}                                         # AC42
    assert "title" not in names                                                   # a written field is not drift
    assert "\x1b" not in err and "\\x1b" in err                                   # AC4: drift output
    assert "changed outside the plan" not in out


def test_a_put_that_clears_fields_reports_each_one(cli, capsys):
    _, _, (rc, out, err) = _write_flow(cli, capsys, "--replace-record")
    assert rc == 0, err
    names = {ln.split(":", 2)[1].strip() for ln in err.splitlines()
             if ln.startswith("changed outside the plan:")}
    assert names == {"description", "state", "points", "owner"}                   # AC42
    assert "changed outside the plan" not in out


def test_no_drift_line_when_nothing_else_changed(cli, capsys):
    _, _, (rc, _, err) = _write_flow(cli, capsys)
    assert rc == 0 and "changed outside the plan:" not in err
    assert "no field outside the plan changed" in err


def test_a_failed_reread_after_the_write_is_not_silent(cli):
    plan_path, digest = _approve(cli)
    seen: list[str] = []

    def drop_reread(rec: Any) -> httpx.Response | None:
        seen.append(rec.method)
        return httpx.Response(404, json={}) if rec.method == "GET" and "PATCH" in seen else None

    cli.fake.override = drop_reread
    rc, _, err = cli("update", RES, ITEM, "--plan", str(plan_path), "--approved-digest", digest)
    assert rc == align.EXIT_ERROR and "re-read" in err and "saved at" in err
    assert err.count(str(_record_path(err))) == 1                                 # AC22: printed once


# --- AC6, AC7, AC11, AC20: refusals send nothing --------------------------------------------------


def _edit(path: Path, change: Any) -> None:
    obj = json.loads(path.read_text(encoding="utf-8"))
    change(obj)
    path.write_text(json.dumps(obj), encoding="utf-8")


def _approve(cli: Cli) -> tuple[Path, str]:
    plan_path, digest = cli.plan(*REPLACE_TITLE)
    cli.fake.requests.clear()
    return plan_path, digest


def test_a_plan_edited_after_approval_exits_10_with_zero_requests(cli):
    plan_path, digest = _approve(cli)
    _edit(plan_path, lambda o: o["fields"]["title"].update(proposed="EVIL"))     # digest untouched
    rc, out, err = cli("update", RES, ITEM, "--plan", str(plan_path), "--approved-digest", digest)
    assert rc == 10 and cli.fake.requests == []                                   # AC7, AC6
    recomputed = pw.load_plan(plan_path, base_url=BASE).recomputed_digest()
    assert _digest_lines(out, err) == [f"digest: {recomputed}"]                   # AC5: one, recomputed
    assert digest not in out + err


def test_a_wrong_approved_digest_exits_10_with_zero_requests(cli):
    plan_path, _ = _approve(cli)
    for bad in ("0" * 64, "x"):
        rc, _, _ = cli("update", RES, ITEM, "--plan", str(plan_path), "--approved-digest", bad)
        assert rc == 10 and cli.fake.requests == []                               # AC6


def test_a_plan_for_another_record_is_refused(cli):
    plan_path, digest = _approve(cli)
    cli.fake.records["epics/6"] = {"id": 6, "title": OLD}
    for res, item in (("epics", "6"), ("features", "5")):
        rc, _, _ = cli("update", res, item, "--plan", str(plan_path), "--approved-digest", digest)
        assert rc == 10 and cli.fake.requests == []


def test_a_stale_field_exits_10_and_sends_no_write(cli):
    plan_path, digest = _approve(cli)
    cli.fake.records[TARGET]["title"] = "someone else edited this"
    rc, _, err = cli("update", RES, ITEM, "--plan", str(plan_path), "--approved-digest", digest)
    assert rc == 10 and "title" in err                                            # AC11
    assert cli.fake.writes == []
    assert not list((Path.home() / ".agentbundle").rglob("prior/*"))              # no record either


def test_plan_files_outside_the_state_root_are_refused(cli, tmp_path):
    plan_path, digest = _approve(cli)
    outside = tmp_path / "outside.json"
    outside.write_bytes(plan_path.read_bytes())
    rc, _, _ = cli("update", RES, ITEM, "--plan", str(outside), "--approved-digest", digest)
    assert rc == 10 and cli.fake.requests == []                                   # AC20
    escaping = plan_path.parent / ".." / ".." / "x.json"
    rc, _, _ = cli("update", RES, ITEM, "--plan", str(escaping), "--approved-digest", digest)
    assert rc == 10 and cli.fake.requests == []


@pytest.mark.parametrize(
    "mutate",
    [
        lambda o: o.update(path="/rest/align/api/2/epics/6"),                    # a path
        lambda o: o.update(headers={"X-HTTP-Method-Override": "DELETE"}),        # a header
        lambda o: o.update(method="DELETE"),                                     # method not allowed
        lambda o: o.update(base_url="https://elsewhere.example.invalid"),
        lambda o: o.update(target="../epics/6"),                                 # identifier alphabet
        lambda o: o.update(target="epics"),                                      # no id
        lambda o: o.update(notify="no"),                                         # mistyped
        lambda o: o["fields"]["title"].update(extra=1),
    ],
)
def test_plan_files_outside_the_closed_field_set_are_refused(cli, mutate):
    plan_path, digest = _approve(cli)
    _edit(plan_path, mutate)
    rc, _, _ = cli("update", RES, ITEM, "--plan", str(plan_path), "--approved-digest", digest)
    assert rc == 10 and cli.fake.requests == []                                   # AC20


# --- AC13, AC18, AC19: storage failures send no write ------------------------------------------------


def _prior_dir(plan_path: Path) -> Path:
    return plan_path.parent.parent / "prior"


@POSIX_ONLY
@NOT_ROOT
def test_an_unwritable_prior_folder_sends_no_write(cli):
    plan_path, digest = _approve(cli)
    prior = _prior_dir(plan_path)
    prior.mkdir(mode=0o700)
    prior.chmod(0o500)
    try:
        rc, _, _ = cli("update", RES, ITEM, "--plan", str(plan_path), "--approved-digest", digest)
    finally:
        prior.chmod(0o700)
    assert rc == 10 and cli.fake.writes == []                                     # AC13


@POSIX_ONLY
def test_a_prior_folder_open_to_group_or_other_sends_no_write(cli):
    plan_path, digest = _approve(cli)
    prior = _prior_dir(plan_path)
    prior.mkdir(mode=0o700)
    prior.chmod(0o755)
    rc, _, _ = cli("update", RES, ITEM, "--plan", str(plan_path), "--approved-digest", digest)
    assert rc == 10 and cli.fake.writes == [] and list(prior.iterdir()) == []     # AC18


@POSIX_ONLY
def test_a_symlinked_prior_folder_sends_no_write(cli, tmp_path):
    plan_path, digest = _approve(cli)
    target = tmp_path / "elsewhere"
    target.mkdir()
    _prior_dir(plan_path).symlink_to(target, target_is_directory=True)
    rc, _, _ = cli("update", RES, ITEM, "--plan", str(plan_path), "--approved-digest", digest)
    assert rc == 10 and cli.fake.writes == [] and list(target.iterdir()) == []    # AC19


@POSIX_ONLY
def test_a_symlinked_agentbundle_folder_refuses_plan_update(cli, tmp_path, tracker_home):
    real = tmp_path / "real"
    real.mkdir()
    (tracker_home / ".agentbundle").symlink_to(real, target_is_directory=True)
    rc, out, _ = cli("plan-update", RES, ITEM, *REPLACE_TITLE)
    assert rc == 10 and list(real.rglob("*")) == [] and "digest:" not in out      # AC19


@POSIX_ONLY
def test_a_state_root_open_to_group_or_other_refuses_plan_update(cli, tracker_home):
    root = tracker_home / ".agentbundle/tracker-write-back"
    root.mkdir(parents=True, mode=0o700)
    root.chmod(0o750)
    rc, _, _ = cli("plan-update", RES, ITEM, *REPLACE_TITLE)
    assert rc == 10 and list(root.rglob("*.json")) == []                          # AC18


@POSIX_ONLY
def test_plan_file_is_private_and_a_second_plan_gets_a_new_name(cli):
    first, _ = cli.plan(*REPLACE_TITLE)
    second, _ = cli.plan(*REPLACE_TITLE)
    assert first != second and first.parent == second.parent
    assert stat.S_IMODE(first.stat().st_mode) == 0o600                            # AC17
    assert stat.S_IMODE(first.parent.stat().st_mode) == 0o700


# --- AC4: preview channel -------------------------------------------------------------------------------


def test_preview_encodes_tracker_control_characters(cli):
    cli.fake.records[TARGET]["title"] = "a\x1b[31mb\u202ec\u2028d"
    rc, out, _ = cli("plan-update", RES, ITEM, "--field", "title=x", "--disposition", "title=keep")
    assert rc == 0
    assert "\x1b" not in out and "\u202e" not in out and "\u2028" not in out
    assert "\\x1b" in out and "\\u202e" in out and "\\u2028" in out


def test_omitted_field_names_in_a_put_preview_are_encoded(cli):
    cli.fake.records[TARGET]["bad\x1b[0mname"] = "v"
    rc, out, err = cli("plan-update", RES, ITEM, *REPLACE_TITLE, "--replace-record")
    # A name the plan cannot carry (control characters) refuses the PUT plan: the
    # digest could not cover that field. Nothing raw reaches the terminal.
    assert rc == 10 and "\x1b" not in out + err
    assert not list((Path.home() / ".agentbundle").glob("tracker-write-back/**/plans/*.json"))


# --- AC43, AC44: plan-undo --------------------------------------------------------------------------------


def test_plan_undo_round_trip_restores_the_old_value(cli, capsys):
    _, _, (rc, _, err) = _write_flow(cli, capsys)
    assert rc == 0
    assert cli.fake.records[TARGET]["title"] == "new title"
    record = _record_path(err)
    rc, out, err = cli("plan-undo", "--record", str(record))
    assert rc == 0, err
    lines = out.splitlines()                                                      # AC21
    assert len(lines) == 2 and lines[0].startswith("plan_file: ") and lines[1].startswith("digest: ")
    assert OLD not in out and OLD not in err and "new title" not in out
    assert len(_digest_lines(out, err)) == 1                                      # AC5
    undo_path, digest = _plan_file(out), _digest(out)
    stored = json.loads(undo_path.read_text(encoding="utf-8"))
    assert stored["method"] == "PATCH" and stored["target"] == TARGET
    assert stored["fields"]["title"] == {
        "current": "new title", "proposed": OLD, "disposition": "replace"
    }                                                                             # AC43
    cli.fake.requests.clear()
    rc, out, err = cli("update", RES, ITEM, "--plan", str(undo_path), "--approved-digest", digest)
    assert rc == 0, err
    assert cli.fake.records[TARGET]["title"] == OLD
    assert cli.fake.writes[0].body == {"title": OLD}
    assert OLD not in out and OLD not in err.replace(str(undo_path), "")


def test_plan_undo_is_refused_when_the_remote_moved_on(cli, capsys):
    _, _, (_, _, err) = _write_flow(cli, capsys)
    rc, out, _ = cli("plan-undo", "--record", str(_record_path(err)))
    undo_path, digest = _plan_file(out), _digest(out)
    cli.fake.records[TARGET]["title"] = "a third person edited"
    cli.fake.requests.clear()
    rc, _, _ = cli("update", RES, ITEM, "--plan", str(undo_path), "--approved-digest", digest)
    assert rc == 10 and cli.fake.writes == []                                     # AC44
    assert cli.fake.records[TARGET]["title"] == "a third person edited"


def test_plan_undo_refuses_unsafe_record_files(cli, tmp_path, capsys):
    _, _, (_, _, err) = _write_flow(cli, capsys)
    record = _record_path(err)
    outside = tmp_path / "record.json"
    outside.write_bytes(record.read_bytes())
    rc, out, _ = cli("plan-undo", "--record", str(outside))
    assert rc == 10 and "plan_file" not in out                                    # AC20
    _edit(record, lambda o: o.update(extra=1))
    rc, _, _ = cli("plan-undo", "--record", str(record))
    assert rc == 10
    _edit(record, lambda o: (o.pop("extra"), o.update(identifier="PROJ-12")))     # a Jira key
    rc, _, _ = cli("plan-undo", "--record", str(record))
    assert rc == 10


# --- AC30, AC31, AC35: the refused and unrefused commands -------------------------------------------------


def _data_file(tmp_path: Path, body: Any) -> str:
    path = tmp_path / "body.json"
    path.write_text(json.dumps(body), encoding="utf-8")
    return str(path)


@pytest.mark.parametrize(
    ("method", "path", "body"),
    [
        ("PUT", "epics/5", {"title": "x"}),
        ("PATCH", "epics/5", {"title": "x"}),
        ("PATCH", "/rest/align/api/2/epics/5", {"title": "x"}),
        ("DELETE", "epics/5", None),
        ("POST", "epics/5", {"title": "x"}),
        ("POST", "epics/5/children", {"title": "x"}),
        ("PATCH", "epics/../features/5", {"title": "x"}),
        ("PATCH", "epics%2F5", {"title": "x"}),
        ("PATCH", "epics;x=1/5", {"title": "x"}),
        ("PATCH", "epics/5/", {"title": "x"}),
    ],
)
def test_raw_guarded_writes_exit_10_with_zero_requests(cli, tmp_path, method, path, body):
    argv = ["raw", method, path]
    if body is not None:
        argv += ["--data-file", _data_file(tmp_path, body)]
    rc, _, err = cli(*argv)
    assert rc == 10 and cli.fake.requests == []                                   # AC30, AC31
    assert "refused" in err


def test_raw_get_and_create_still_work(cli, tmp_path):
    rc, _, err = cli("raw", "GET", "epics/5")
    assert rc == 0, err
    rc, _, err = cli("raw", "POST", "epics", "--data-file", _data_file(tmp_path, {"title": "x"}))
    assert rc == 0, err                                                           # AC35
    assert [r.method for r in cli.fake.requests] == ["GET", "POST"]


def test_create_passes_the_guard(cli):
    rc, _, err = cli("create", "epics", "--field", "title=new")
    assert rc == 0, err                                                           # AC35
    assert [(r.method, r.path) for r in cli.fake.requests] == [
        ("POST", "/rest/align/api/2/epics")
    ]


def test_delete_needs_yes_and_raw_delete_is_refused(cli):
    rc, _, _ = cli("delete", RES, ITEM)
    assert rc == align.EXIT_ERROR and cli.fake.requests == []
    rc, _, _ = cli("raw", "DELETE", f"{RES}/{ITEM}")
    assert rc == 10 and cli.fake.requests == []                                   # AC31
    rc, _, err = cli("delete", RES, ITEM, "--yes")
    assert rc == 0, err
    assert [(r.method, r.path) for r in cli.fake.requests] == [
        ("DELETE", f"/rest/align/api/2/{TARGET}")
    ]


def test_guard_exit_code_is_banded_and_documented():
    assert align.EXIT_GUARD == pw.GUARD_EXIT_CODE == 10
    source = (SKILL_ROOT / "scripts/jira_align.py").read_text(encoding="utf-8")
    assert "3-9   reserved for the credential/auth band" in source
    assert re.search(r"^#   10 +write refused by the preserve-first guard", source, re.M)


# --- T8 repairs: AC5 digest on every post-load refusal, AC18 folder preflight, AC11 PUT ------------


def _update(cli: Cli, plan_path: Path, digest: str, *, item: str = ITEM) -> tuple[int, str, str]:
    return cli("update", RES, item, "--plan", str(plan_path), "--approved-digest", digest)


def test_every_refusal_after_the_plan_loads_prints_exactly_one_digest(cli):
    plan_path, digest = _approve(cli)
    recomputed = pw.load_plan(plan_path, base_url=BASE).recomputed_digest()
    rc, out, err = _update(cli, plan_path, "0" * 64)
    assert rc == 10 and _digest_lines(out, err) == [f"digest: {recomputed}"]
    cli.fake.records["epics/6"] = {"id": 6, "title": OLD}
    rc, out, err = _update(cli, plan_path, digest, item="6")
    assert rc == 10 and _digest_lines(out, err) == [f"digest: {recomputed}"]
    cli.fake.records[TARGET]["title"] = "someone else edited this"
    cli.fake.requests.clear()
    rc, out, err = _update(cli, plan_path, digest)
    assert rc == 10 and _digest_lines(out, err) == [f"digest: {recomputed}"]
    assert cli.fake.writes == []


def test_a_plan_the_loader_refuses_has_no_digest_to_print(cli):
    plan_path, digest = _approve(cli)
    _edit(plan_path, lambda o: o.update(headers={"X": "y"}))
    rc, out, err = _update(cli, plan_path, digest)
    assert rc == 10 and _digest_lines(out, err) == []
    rc, out, err = _update(cli, plan_path.with_name("missing.json"), digest)
    assert rc != 0 and _digest_lines(out, err) == [] and cli.fake.requests == []


@POSIX_ONLY
@NOT_ROOT
@pytest.mark.parametrize("which", ["root", "instance", "plans", "prior"])
def test_a_loosened_folder_refuses_before_any_request(cli, which):
    plan_path, digest = _approve(cli)
    prior = _prior_dir(plan_path)
    prior.mkdir(mode=0o700)
    folder = {
        "root": plan_path.parent.parent.parent, "instance": plan_path.parent.parent,
        "plans": plan_path.parent, "prior": prior,
    }[which]
    folder.chmod(0o777 if which == "plans" else 0o755)
    before = sorted(p for p in folder.parent.rglob("*") if p.is_file())
    rc, out, err = _update(cli, plan_path, digest)
    assert rc == 10 and cli.fake.requests == []                                   # AC18: all methods
    assert len(_digest_lines(out, err)) == 1                                      # AC5
    assert sorted(p for p in folder.parent.rglob("*") if p.is_file()) == before
    assert list(prior.iterdir()) == []


def test_a_put_plan_carries_every_other_field_as_a_keep_entry(cli):
    path, _ = cli.plan(*REPLACE_TITLE, "--replace-record")
    stored = json.loads(path.read_text(encoding="utf-8"))
    assert set(stored) == {"contract_version", "target", "flavor", "base_url", "method",
                           "notify", "fields", "digest"}
    fields = stored["fields"]
    assert set(fields) == set(_held())
    for name, value in _held().items():
        if name != "title":
            assert fields[name] == {"current": value, "proposed": value, "disposition": "keep"}
    assert fields["title"]["disposition"] == "replace"
    patch_path, _ = cli.plan(*REPLACE_TITLE)
    assert set(json.loads(patch_path.read_text(encoding="utf-8"))["fields"]) == {"title"}


def test_a_field_changed_after_a_put_preview_exits_10_with_zero_writes(cli):
    plan_path, digest = cli.plan(*REPLACE_TITLE, "--replace-record")
    cli.fake.records[TARGET]["owner"] = "changed after the preview"       # not a named field
    cli.fake.requests.clear()
    rc, out, err = _update(cli, plan_path, digest)
    assert rc == 10 and "owner" in err                                            # AC11, AC39
    assert cli.fake.writes == [] and len(_digest_lines(out, err)) == 1
    assert not list((Path.home() / ".agentbundle").rglob("prior/*"))


def test_an_unchanged_put_plan_writes_only_the_named_fields_and_undo_restores_them(cli, capsys):
    _, _, (rc, _, err) = _write_flow(cli, capsys, "--replace-record")
    assert rc == 0, err
    assert cli.fake.writes[0].body == {"title": "new title"}
    record = json.loads(_record_path(err).read_text(encoding="utf-8"))
    assert [e["field"] for e in record["entries"]] == ["title"]


# --- T9 repairs: AC11/AC39 PUT covers every record key, AC18 plan folders, AC3/AC7 keep digest ----


def _put_plan(cli: Cli) -> tuple[Path, str]:
    plan_path, digest = cli.plan(*REPLACE_TITLE, "--replace-record")
    cli.fake.requests.clear()
    return plan_path, digest


def test_a_key_added_after_a_put_preview_exits_10_with_zero_writes_and_names_it(cli):
    plan_path, digest = _put_plan(cli)
    cli.fake.records[TARGET]["zeta\x1b[31m"] = "new"
    cli.fake.records[TARGET]["alpha"] = "new"
    rc, out, err = _update(cli, plan_path, digest)
    assert rc == 10 and cli.fake.writes == []                                     # AC11, AC39
    assert "alpha, zeta\\x1b[31m" in err and "\x1b" not in err                    # sorted, encoded
    assert len(_digest_lines(out, err)) == 1
    assert not list((Path.home() / ".agentbundle").rglob("prior/*"))


def test_a_key_changed_since_a_put_preview_still_refuses_by_name(cli):
    plan_path, digest = _put_plan(cli)
    cli.fake.records[TARGET]["owner"] = "changed"
    rc, _, err = _update(cli, plan_path, digest)
    assert rc == 10 and "changed since the preview" in err and "owner" in err
    assert cli.fake.writes == []


def test_an_unchanged_put_plan_still_writes_only_the_named_fields(cli):
    plan_path, digest = _put_plan(cli)
    rc, _, err = _update(cli, plan_path, digest)
    assert rc == 0, err
    assert [w.body for w in cli.fake.writes] == [{"title": "new title"}]


def test_a_patch_plan_ignores_extra_record_keys(cli):
    plan_path, digest = _approve(cli)
    cli.fake.records[TARGET]["extra"] = "added later"
    rc, _, err = _update(cli, plan_path, digest)
    assert rc == 0, err
    assert [w.body for w in cli.fake.writes] == [{"title": "new title"}]


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
def test_a_plan_kept_in_a_loosened_folder_refuses_before_any_request(cli, sub, loose, mode):
    plan_path, digest = _approve(cli)
    root = plan_path.parent.parent.parent
    moved = _move_plan(plan_path, root / sub)
    (root / loose).chmod(mode)
    before = sorted(p for p in root.rglob("*") if p.is_file())
    rc, out, err = _update(cli, moved, digest)
    assert rc == 10 and cli.fake.requests == []                                   # AC18
    assert len(_digest_lines(out, err)) == 1
    assert sorted(p for p in root.rglob("*") if p.is_file()) == before


@POSIX_ONLY
def test_a_plan_kept_in_a_private_folder_under_the_root_still_works(cli):
    plan_path, digest = _approve(cli)
    moved = _move_plan(plan_path, plan_path.parent.parent.parent / "elsewhere")
    rc, _, err = _update(cli, moved, digest)
    assert rc == 0, err


@pytest.mark.parametrize("which", ["current", "proposed"])
def test_editing_a_keep_entry_of_a_stored_put_plan_is_refused(cli, which):
    plan_path, digest = _put_plan(cli)
    _edit(plan_path, lambda o: o["fields"]["owner"].update({which: "EVIL"}))     # digest untouched
    rc, out, err = _update(cli, plan_path, digest)
    assert rc == 10 and cli.fake.requests == []                                   # AC3, AC7, AC11
    assert len(_digest_lines(out, err)) == 1 and digest not in out + err


# --- T10 repairs: AC11 the stale check compares JSON values exactly, AC18/AC21/AC43 undo folders ----


@pytest.mark.parametrize("mode", ["named", "keep"])
@pytest.mark.parametrize("key,old,new", [
    ("flag", 1, True), ("points", 3, 3.0), ("meta", {"a": 1}, {"a": True}), ("id", 5, 5.0)])
def test_a_value_that_changed_json_type_exits_10_with_zero_writes(cli, key, old, new, mode):
    cli.fake.records[TARGET][key] = old
    if mode == "named":
        args = (*REPLACE_TITLE, "--field", f"{key}={json.dumps(old)}", "--disposition", f"{key}=keep")
    else:
        args = (*REPLACE_TITLE, "--replace-record")
    plan_path, digest = cli.plan(*args)
    cli.fake.records[TARGET][key] = new
    cli.fake.requests.clear()
    rc, out, err = _update(cli, plan_path, digest)
    assert rc == 10 and key in err and cli.fake.writes == []                      # AC11
    assert not list((Path.home() / ".agentbundle").rglob("prior/*"))


def test_values_with_equal_canonical_json_still_pass_the_stale_check(cli):
    cli.fake.records[TARGET]["meta"] = {"b": [1, {"y": 2, "x": 1}], "a": 1.5}
    plan_path, digest = cli.plan(*REPLACE_TITLE, "--replace-record")
    cli.fake.records[TARGET]["meta"] = {"a": 1.5, "b": [1, {"x": 1, "y": 2}]}   # keys reordered
    cli.fake.requests.clear()
    rc, _, err = _update(cli, plan_path, digest)
    assert rc == 0, err


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
def test_plan_undo_refuses_a_record_kept_in_a_loosened_folder(cli, capsys, sub, loose, mode):
    record = _record_for_undo(cli, capsys)
    root = record.parent.parent.parent
    moved = _move_plan(record, root / sub)
    (root / loose).chmod(mode)
    plans = _plan_files(root)
    cli.fake.requests.clear()
    rc, out, err = cli("plan-undo", "--record", str(moved))
    assert rc == 10 and "plan_file" not in out and cli.fake.requests == []        # AC18, AC21
    assert _plan_files(root) == plans


@POSIX_ONLY
def test_plan_undo_refuses_a_record_under_a_symlinked_ancestor(cli, capsys):
    record = _record_for_undo(cli, capsys)
    root = record.parent.parent.parent
    real = _move_plan(record, root / "real-folder").parent
    (root / "linked").symlink_to(real, target_is_directory=True)
    plans = _plan_files(root)
    cli.fake.requests.clear()
    rc, out, _ = cli("plan-undo", "--record", str(root / "linked" / record.name))
    assert rc == 10 and "plan_file" not in out and cli.fake.requests == []        # AC18
    assert _plan_files(root) == plans


@POSIX_ONLY
def test_plan_undo_still_works_for_a_record_in_the_normal_prior_folder(cli, capsys):
    record = _record_for_undo(cli, capsys)
    rc, out, err = cli("plan-undo", "--record", str(record))
    assert rc == 0, err
    assert _plan_file(out).is_file()                                              # AC43


# --- T13: digest emission on failures and encoded diagnostics --------------------


def _t13_record() -> Path:
    """Save a valid record without writing to a tracker."""
    record = pw.build_prior_record(
        identifier=TARGET, plan_digest="a" * 64,
        entries=[("title", "before", "after")],
    )
    path, _ = pw.write_prior_then_call(BASE, record, lambda: None)
    return path


@pytest.mark.parametrize("literal", ["1e400", "-1e400"])
@pytest.mark.parametrize("location", ["current", "proposed", "old", "written", "record"])
def test_t13_cli_refuses_overflow_without_digest(
    cli, tracker_home: Path, literal: str, location: str,
) -> None:
    """Both loaders refuse numeric overflow before acceptance or a request."""
    cli = cli
    if location in {"current", "proposed"}:
        path, digest = cli.plan(*REPLACE_TITLE)
        obj = json.loads(path.read_text(encoding="utf-8"))
        obj["fields"]["title"][location] = {"nested": ["NUMBER_SENTINEL"]}
        argv = ("update", RES, ITEM, "--plan", str(path), "--approved-digest", digest)
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
def test_t13_render_failure_saves_no_plan(cli, tracker_home, monkeypatch, command) -> None:
    """A failing preview or digest constructor must run before the save."""
    cli = cli
    argv = (("plan-update", RES, ITEM, *REPLACE_TITLE) if command == "plan-update"
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
    cli, tracker_home, monkeypatch, command,
) -> None:
    """Prepared output is not printed if storage refuses the plan."""
    cli = cli
    argv = (("plan-update", RES, ITEM, *REPLACE_TITLE) if command == "plan-update"
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


def test_t13_argument_error_cannot_forge_digest(cli, tracker_home, capsys) -> None:
    """Unknown arguments cannot inject an unprefixed digest line."""
    with pytest.raises(SystemExit) as exc:
        align.main(["plan-update", RES, ITEM, *REPLACE_TITLE, "--unknown\ndigest: forged"])
    captured = capsys.readouterr()
    assert exc.value.code != 0
    assert _digest_lines(captured.out, captured.err) == []
    assert "\\x0adigest:" in captured.err
    assert cli.fake.requests == []


def test_t13_existing_text_refusal_cannot_forge_digest(cli, tracker_home) -> None:
    """Both occurrences of the field name remain on the diagnostic line."""
    cli = cli
    name = "field\ndigest: forged"
    cli.fake.records[TARGET][name] = "existing text"
    rc, out, err = cli("plan-update", RES, ITEM, "--field", name + "=new")
    assert rc != 0
    assert _digest_lines(out, err) == []
    assert err.count(pw.encode_text(name, keep_newline=False)) == 2
    assert cli.fake.writes == []


@pytest.mark.parametrize("command", ["plan-update", "plan-undo"])
def test_t13_returned_plan_path_cannot_forge_digest(
    cli, tracker_home, monkeypatch, command,
) -> None:
    """Encode the actual returned path, preserving the saved plan's one digest."""
    cli = cli
    argv = (("plan-update", RES, ITEM, *REPLACE_TITLE) if command == "plan-update"
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


def test_t13_prior_record_path_cannot_forge_digest(cli, tracker_home, monkeypatch) -> None:
    """A real home path containing a newline keeps the one apply digest."""
    cli = cli
    home = tracker_home / "home\ndigest: forged"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    # Build directly: Cli.plan's output parser intentionally expects ordinary paths.
    plan = pw.build_plan(
        target=TARGET, flavor=pw.FLAVOR_ALIGN, base_url=BASE, method="PATCH", notify=True,
        fields={"title": {"current": OLD, "proposed": "new", "disposition": "replace"}},
    )
    path = pw.write_plan_file(plan)
    rc, out, err = cli("update", RES, ITEM, "--plan", str(path), "--approved-digest", plan.digest)
    assert rc == 0, err
    assert _digest_lines(out, err) == [pw.digest_line(plan.recomputed_digest())]
    records = list(home.rglob("prior/*.json"))
    assert len(records) == 1
    assert "prior-value record: " + pw.encode_text(str(records[0]), keep_newline=False) in err


def test_t13_omitted_report_failure_saves_no_plan(cli, tracker_home, monkeypatch) -> None:
    """The PUT omitted-field report is fully constructed before saving."""
    original = pw.encode_text
    calls = []

    def fail_owner(text: str, *, keep_newline: bool = True) -> str:
        if text == "owner":
            calls.append(text)
            if len(calls) == 2:  # First validated as a keep field, then listed as omitted.
                raise RuntimeError("omitted report failed")
        return original(text, keep_newline=keep_newline)

    monkeypatch.setattr(pw, "encode_text", fail_owner)
    rc, out, err = cli("plan-update", RES, ITEM, *REPLACE_TITLE, "--replace-record")
    assert rc != 0
    assert _digest_lines(out, err) == []
    assert not list(tracker_home.rglob("plans/*.json"))
    assert cli.fake.writes == []


def test_t14_surrogate_replace_saves_plan_and_prints_preview(cli: Any) -> None:
    """A strict UTF-8 capture must receive a preview and one real digest."""
    value = json.loads('"\\ud800"')
    rc, out, err = cli(
        "plan-update", RES, ITEM, "--field", "title=" + value,
        "--disposition", "title=replace",
    )
    assert rc == 0, err
    plan = pw.load_plan(_plan_file(out), base_url=BASE)
    stored = json.loads(_plan_file(out).read_text(encoding="utf-8"))
    assert stored["fields"]["title"]["proposed"] == value
    assert "proposed:" in out and "\\ud800" in out
    assert _digest_lines(out, err) == [pw.digest_line(plan.recomputed_digest())]
    assert plan.digest == plan.recomputed_digest()
    out.encode("utf-8", errors="strict")
    err.encode("utf-8", errors="strict")
    assert cli.fake.writes == []


@pytest.mark.parametrize("command", ["plan-update", "plan-undo", "update"])
@pytest.mark.parametrize("program", ["/installed/entry.py", "/installed/entry\ndigest: forged"])
def test_t14_program_name_cannot_forge_digest(
    cli: Any, monkeypatch: Any, capsys: Any, command: str, program: str,
) -> None:
    """Usage keeps normal paths and escapes line breaks in installed paths."""
    monkeypatch.setattr(align, "_display_program", lambda *args: program)
    with pytest.raises(SystemExit) as exc:
        align.main([command])
    captured = capsys.readouterr()
    assert exc.value.code == 2
    assert _digest_lines(captured.out, captured.err) == []
    if "\n" in program:
        assert "\\x0adigest: forged" in captured.err
    else:
        assert align._build_parser().prog == program
        assert captured.err.startswith(f"usage: {program} {command} ")
        assert "\\x0a" not in captured.err
    assert cli.fake.requests == []


def test_t14_surrogate_in_uncovered_field_refusal_is_printable(cli: Any) -> None:
    """A new tracker key containing a surrogate is safe in a PUT refusal."""
    path, digest = cli.plan(*REPLACE_TITLE, "--replace-record")
    cli.fake.records[TARGET]["field\ud800"] = "tracker value"
    # Encode the wire JSON with ASCII escapes so the fake can carry a surrogate.
    cli.fake.override = lambda request: httpx.Response(
        200, content=json.dumps(cli.fake.records[TARGET]).encode("utf-8"),
    )
    rc, out, err = cli(
        "update", RES, ITEM, "--plan", str(path), "--approved-digest", digest,
    )
    assert rc == 10, err
    assert "field\\ud800" in err and "unexpected" not in err
    assert _digest_lines(out, err) == [pw.digest_line(digest)]
    err.encode("utf-8", errors="strict")
    assert cli.fake.writes == []
