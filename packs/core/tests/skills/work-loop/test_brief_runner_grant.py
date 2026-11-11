"""Run grant, integration: binding, Ready-only, exemption and the grant answers of the runner.

Every case reads real commits: a bare ``origin``, a main worktree that carries a committed copy
of the work-loop skill, and linked slice worktrees, built by the brief-runner harness. The
runner is called in-process so that its clock (``_now``) can be patched where a case depends on
the fixed exemption end time; every other grant is built relative to the real clock.
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import itertools
import json
import sys
from collections.abc import Callable, Sequence
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

_HARNESS_PATH = Path(__file__).resolve().parent / "test_brief_runner.py"


def _harness() -> ModuleType:
    """The brief-runner integration harness, loaded by path under a unique name."""
    alias = "core_work_loop_test_brief_runner_harness"
    if alias not in sys.modules:
        spec = importlib.util.spec_from_file_location(alias, _HARNESS_PATH)
        assert spec is not None and spec.loader is not None
        sys.modules[alias] = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(sys.modules[alias])
    return sys.modules[alias]


hx = _harness()
h = hx.h
sup = hx.sup
World = hx.World
pytestmark = sup.INTEGRATION

UTC_Z = "%Y-%m-%dT%H:%M:%SZ"
OWNER = "grantor-x"
BEFORE_END = datetime(2026, 11, 1, tzinfo=UTC)
ENDS = datetime(2026, 11, 30, tzinfo=UTC)
_SERIAL = itertools.count(1)


# ── fixture construction ────────────────────────────────────────────────────


def brief_text(slugs: Sequence[str], status: str = "Ready", body: str = "") -> str:
    rows = "\n".join(f"| `{slug}` | <auto> |" for slug in slugs)
    return (
        f"# Brief\n\n- **Status:** {status}\n\n## Spec map\n\n| Spec | Status |\n"
        f"| --- | --- |\n{rows}\n{body}"
    )


def with_record(text: str, stamp: str | None) -> str:
    """*text* with its run-grant record line replaced by one for *stamp* (None: removed)."""
    lines = [line for line in text.split("\n") if "**Run grant:**" not in line]
    if stamp is not None:
        at = next(i for i, line in enumerate(lines) if line.startswith("- **Status:**"))
        lines.insert(at + 1, f"- **Run grant:** required (confirmed {stamp})")
    return "\n".join(lines)


def make_world(
    tmp: Path,
    briefs: dict[str, tuple[list[str], str]],
    edit: Callable[[Path], None] | None = None,
) -> World:
    """A world whose briefs are ``name -> (Spec map slugs, Status)``."""

    def apply(main: Path) -> None:
        for name, (slugs, status) in briefs.items():
            hx._write(main, f"docs/product/briefs/{name}.md", brief_text(slugs, status))
        if edit is not None:
            edit(main)

    return hx.build_world(tmp, briefs={n: s for n, (s, _) in briefs.items()}, edit=apply)


def brief_file(brief: str) -> str:
    return f"docs/product/briefs/{brief}.md"


def grant_file(brief: str) -> str:
    return f"docs/product/run-grants/{brief}.toml"


def grant_toml(
    brief: str,
    slices: Sequence[str],
    confirmed: datetime,
    expires: datetime,
    *,
    done_when: str = "all-granted-merged",
    budget: int = 0,
    held: Sequence[str] = ("push",),
    extra: str = "",
) -> str:
    return (
        f'schema_version = 1\nbrief = "{brief}"\nconfirmed_by = "{OWNER}"\n'
        f"confirmed_at = {confirmed.strftime(UTC_Z)}\nexpires_at = {expires.strftime(UTC_Z)}\n"
        f'done_when = "{done_when}"\nslices = {json.dumps(list(slices))}\n'
        f"retry_budget = {budget}\nmax_slices_in_flight = 1\n"
        f"held_actions = {json.dumps(list(held))}\n{extra}"
    )


def add_grant(
    w: World,
    brief: str,
    slices: Sequence[str],
    *,
    expired: bool = False,
    commit: bool = True,
    **toml: Any,
) -> datetime:
    """Commit the grant file and the brief's record line, one confirmation, one commit.

    Valid: confirmed one hour ago, expiring in one day. Expired: confirmed ten days ago,
    expired nine days ago. The minutes differ per call, so a renewal is a new confirmation.
    """
    now = datetime.now(UTC).replace(microsecond=0)
    serial = timedelta(minutes=next(_SERIAL))
    confirmed = now - (timedelta(days=10) if expired else timedelta(hours=1)) - serial
    expires = now - timedelta(days=9) if expired else now + timedelta(days=1)
    hx._write(w.main, grant_file(brief), grant_toml(brief, slices, confirmed, expires, **toml))
    edit_brief(w, brief, lambda t: with_record(t, confirmed.strftime(UTC_Z)))
    if commit:
        w.commit(f"grant {brief}")
    return confirmed


def edit_brief(w: World, brief: str, change: Callable[[str], str]) -> None:
    path = w.main / brief_file(brief)
    path.write_text(change(path.read_text("utf-8")), **h._LF)


def call(
    w: World, verb: str, brief: str, *extra: str, now: datetime | None = None
) -> tuple[int, dict[str, Any]]:
    """Run one verb in-process; *now* patches the runner's clock for the call."""
    run = w.runner
    saved = run._now
    if now is not None:
        run._now = lambda: now
    raw = io.BytesIO()
    out = io.TextIOWrapper(raw, encoding="utf-8")  # the runner's siblings reconfigure stdout
    try:
        with contextlib.redirect_stdout(out):
            code = run.main([verb, brief, *extra, "--root", str(w.main)])
        out.flush()
    finally:
        run._now = saved
    return code, json.loads(raw.getvalue().decode("utf-8"))


def nxt(w: World, brief: str, *, now: datetime | None = None) -> dict[str, Any]:
    code, out = call(w, "next", brief, now=now)
    assert code == 0, out
    return out


def grant_of(w: World, brief: str) -> dict[str, Any] | None:
    grant: dict[str, Any] | None = nxt(w, brief)["grant"]
    return grant


def state_of(w: World, brief: str) -> tuple[str, str | None, str | None]:
    grant = grant_of(w, brief)
    assert grant is not None
    return grant["state"], grant["reason"], grant["detail"]


def reasons(out: dict[str, Any]) -> dict[str, str]:
    assert out["action"]["kind"] == "blocked", out["action"]
    return {r["slice"]: r["reason"] for r in out["action"]["rows"]}


@pytest.fixture
def gw(tmp_path: Path) -> World:
    """A fresh world with brief ``g`` (Ready; alpha, beta, delta), no grant."""
    return make_world(tmp_path, {"g": (["alpha", "beta", "delta"], "Ready")})


# ── the status token's span ─────────────────────────────────────────────────


@pytest.fixture(scope="module")
def runner() -> ModuleType:
    return hx._load_runner(hx.sup.SCRIPTS / "brief-runner.py")


@pytest.mark.parametrize(
    "text",
    [
        "# B\n\n- **Status:** Ready\n\n## Spec map\n",
        "# B\n\n- **Status:** `Ready` (cut 2)\n",
        "# B\n\n- **Status:** Ready <!-- Draft | Ready -->\n",
        "# B\n\n<!-- **Status:** Draft -->\n- **Status:** Executing → Shipped\n",
        "# B\r\n\r\n- **Status:**   Withdrawn  \r\n",
        "# B\n\n<!-- x --> - **Status:** Ready\n",
        "# B\n\n- **Status:** Ré<!-- c -->ady\n",
    ],
)
def test_the_bound_form_replaces_exactly_the_token_the_status_parser_reads(
    runner: ModuleType, text: str
) -> None:
    token = runner.parse_status(text)
    assert token
    span = runner._status_token_span(text)
    assert span is not None
    first, last = span
    assert text[first:last].replace("<!-- c -->", "") == token
    bound = runner.bound_form(text.encode()).decode()
    assert bound == text[:first] + runner.STATUS_PLACEHOLDER + text[last:]
    if "<!-- c -->" not in text:  # another token binds to the same bytes
        other = text[:first] + "Draft" + text[last:]
        assert runner.bound_form(other.encode()).decode() == bound


@pytest.mark.parametrize("text", ["# B\n\n## Spec map\n- **Status:** Ready\n", "no status\n"])
def test_a_brief_without_a_readable_status_is_its_own_bound_form(
    runner: ModuleType, text: str
) -> None:
    assert runner.parse_status(text) is None
    assert runner.bound_form(text.encode()) == text.encode()


# ── AC-0001, AC-0002: Ready-only and the exemption ──────────────────────────

DRAFT_BRIEFS: dict[str, tuple[list[str], str]] = {
    "d-start": (["alpha", "delta"], "Draft"),
    "d-flight": (["wa", "alpha"], "Draft"),
    "d-nospec": (["brand-new"], "Draft"),
    "d-gate": (["wa"], "Draft"),
    "d-seen": (["wa", "alpha"], "Draft"),
    "d-weird": (["alpha"], "Whatever"),
    "d-closed": (["alpha"], "Withdrawn"),
    "r-ready": (["wa", "alpha"], "Ready"),
    "r-exec": (["alpha"], "Executing"),
}


@pytest.fixture(scope="module")
def dw(tmp_path_factory: pytest.TempPathFactory) -> World:
    w = make_world(tmp_path_factory.mktemp("grant-draft"), DRAFT_BRIEFS)
    hx.make_slice(w, "d-flight", "wa", "implementing")
    hx.make_slice(w, "d-nospec", "brand-new", "drafting")
    hx.make_slice(w, "d-gate", "wa", "parked")
    hx.make_slice(w, "d-seen", "wa", "implementing")
    hx.make_slice(w, "r-ready", "wa", "implementing")
    return w


@pytest.mark.parametrize("brief", ["d-start", "d-weird", "d-closed"])
def test_a_brief_that_is_not_runnable_starts_nothing_and_reads_brief_not_ready(
    dw: World, brief: str
) -> None:
    out = nxt(dw, brief, now=BEFORE_END)
    assert out["grant"] is None
    assert reasons(out)["alpha"] == "brief-not-ready"
    _, status = call(dw, "status", brief)
    assert status["brief_status"] == out["brief_status"] and status["grant"] is None
    assert nxt(dw, brief, now=ENDS + timedelta(days=1))["action"]["kind"] == "blocked"


def test_a_draft_brief_with_an_approved_dispatchable_row_names_no_start(dw: World) -> None:
    ready = nxt(dw, "r-exec")
    assert ready["action"]["kind"] == "start-slice" and ready["brief_status"] == "Executing"
    draft = nxt(dw, "d-start", now=BEFORE_END)
    assert draft["brief_status"] == "Draft" and draft["action"]["kind"] == "blocked"
    assert reasons(draft) == {"alpha": "brief-not-ready", "delta": "brief-not-ready"}


def test_brief_status_is_null_for_a_status_outside_the_vocabulary(dw: World) -> None:
    assert nxt(dw, "d-weird", now=BEFORE_END)["brief_status"] is None
    assert nxt(dw, "d-closed", now=BEFORE_END)["brief_status"] == "Withdrawn"


def test_a_draft_brief_resumes_an_in_flight_slice_that_has_a_spec_with_the_exemption(
    dw: World,
) -> None:
    action = nxt(dw, "d-flight", now=BEFORE_END)["action"]
    assert action["kind"] == "resume-slice" and action["slice"] == "wa"
    assert action["exemption"] == "pre-ready-in-flight"


def test_only_the_pre_ready_resume_carries_an_exemption(dw: World) -> None:
    ready = nxt(dw, "r-ready", now=BEFORE_END)["action"]
    assert ready["kind"] == "resume-slice" and "exemption" not in ready
    for brief in ("d-start", "d-nospec", "d-gate"):
        assert "exemption" not in nxt(dw, brief, now=BEFORE_END)["action"], brief


def test_a_drafting_row_with_no_spec_is_never_exempt(dw: World) -> None:
    assert dw.rows("d-nospec")["brand-new"].stage == "drafting"
    action = nxt(dw, "d-nospec", now=BEFORE_END)["action"]
    assert action["kind"] == "blocked" and "exemption" not in json.dumps(action)


def test_a_row_with_a_pending_gate_is_not_exempt(dw: World) -> None:
    assert nxt(dw, "d-gate", now=BEFORE_END)["action"]["kind"] == "await-gates"


def test_nothing_resumes_at_or_after_the_exemption_end(dw: World) -> None:
    just_before = ENDS - timedelta(seconds=1)
    assert nxt(dw, "d-seen", now=just_before)["action"]["kind"] == "resume-slice"
    for moment in (ENDS, ENDS + timedelta(days=30)):
        out = nxt(dw, "d-seen", now=moment)
        assert out["action"]["kind"] == "blocked", moment
        assert reasons(out)["alpha"] == "brief-not-ready"


def test_the_exemption_end_is_the_fixed_time_in_the_runners_code(runner: ModuleType) -> None:
    assert runner.PRE_READY_EXEMPTION_ENDS == ENDS


def test_grant_evidence_removes_the_exemption(tmp_path: Path) -> None:
    w = make_world(tmp_path, {"g": (["wa", "alpha"], "Draft")})
    hx.make_slice(w, "g", "wa", "implementing")
    assert nxt(w, "g", now=BEFORE_END)["action"]["kind"] == "resume-slice"
    edit_brief(w, "g", lambda t: with_record(t, "2026-11-01T00:00:00Z"))
    w.commit("a record on a Draft brief")
    out = nxt(w, "g", now=BEFORE_END)
    assert out["action"]["kind"] == "grant-refused" and out["grant"]["reason"] == "brief-not-ready"


# ── AC-0006, AC-0007, AC-0009, AC-0015: the grant's states ──────────────────
#
# Read-only cases share one module-scoped world with one brief per case: a state is a function
# of its own brief's commits, and nothing here changes history after the fixture is built. The
# cases that read history as it changes across commits keep a function-scoped world (`gw`).

STATE_SLICES = ["alpha", "beta", "delta"]
STATE_CASES = (
    "s-none", "s-valid", "s-record-only", "s-grant-only", "s-key", "s-table", "s-toml",
    "s-slices", "s-budget", "s-mismatch", "s-comment", "s-twice", "s-dir", "s-brief-edit",
    "s-trailing", "s-token", "s-grant-alone", "s-grant-and-brief", "s-renewal", "s-draft",
    "s-expired", "s-both-removed", "s-file-removed", "s-record-removed", "s-done",
    "s-merge-ready-merged", "s-merge-ready-stopped",
)  # fmt: skip
STATE_CONFIRMED: dict[str, datetime] = {}


def _touch_grant(w: World, brief: str) -> None:
    path = w.main / grant_file(brief)
    path.write_text(path.read_text("utf-8") + "# a comment\n", **h._LF)


def _build_state_cases(w: World) -> None:
    """Commit each case's history, one brief at a time."""
    for brief, extra in (("s-key", "spend_cap = 3\n"), ("s-table", "[t]\nx = 1\n"),
                         ("s-toml", "what = \n")):  # fmt: skip
        add_grant(w, brief, ["alpha"], extra=extra)
    STATE_CONFIRMED["s-valid"] = add_grant(
        w, "s-valid", ["alpha", "beta"], budget=1, held=["push", "open-pull-request"]
    )
    edit_brief(w, "s-record-only", lambda t: with_record(t, "2026-11-01T00:00:00Z"))
    w.commit("record only")
    add_grant(w, "s-grant-only", ["alpha"], commit=False)
    edit_brief(w, "s-grant-only", lambda t: with_record(t, None))
    w.commit("grant only")
    add_grant(w, "s-slices", ["nowhere"])
    add_grant(w, "s-budget", ["alpha"], budget=99)
    add_grant(w, "s-mismatch", ["alpha"], commit=False)
    edit_brief(w, "s-mismatch", lambda t: with_record(t, "2020-01-01T00:00:00Z"))
    w.commit("wrong record time")
    stamp = add_grant(w, "s-comment", ["alpha"], commit=False).strftime(UTC_Z)
    edit_brief(w, "s-comment", lambda t: with_record(t, None))
    edit_brief(
        w, "s-comment", lambda t: t.replace("\n## Spec map", f"<!--\n- **Run grant:** required "
                                            f"(confirmed {stamp})\n-->\n\n## Spec map")
    )  # fmt: skip
    w.commit("record in a comment")
    again = add_grant(w, "s-twice", ["alpha"], commit=False)
    edit_brief(w, "s-twice", lambda t: t + f"\nNote: **Run grant:** again {again}\n")
    w.commit("two marks")
    hx._write(w.main, f"{grant_file('s-dir')}/inner.txt", "a directory where a file belongs\n")
    w.commit("a tree entry")
    add_grant(w, "s-brief-edit", ["alpha"])
    edit_brief(w, "s-brief-edit", lambda t: t + "\nA new sentence.\n")
    w.commit("edit the brief")
    add_grant(w, "s-trailing", ["alpha"])
    edit_brief(w, "s-trailing", lambda t: t.replace("Status:** Ready", "Status:** Ready (cut 2)"))
    w.commit("trailing text")
    add_grant(w, "s-token", ["alpha"])
    edit_brief(w, "s-token", lambda t: t.replace("Status:** Ready", "Status:** Executing"))
    w.commit("Ready to Executing")
    add_grant(w, "s-grant-alone", ["alpha"])
    _touch_grant(w, "s-grant-alone")
    w.commit("grant edited alone")
    add_grant(w, "s-grant-and-brief", ["alpha"])
    _touch_grant(w, "s-grant-and-brief")
    edit_brief(w, "s-grant-and-brief", lambda t: t + "\nAn edit.\n")
    w.commit("grant comment and brief edit together")
    add_grant(w, "s-renewal", ["alpha"])
    edit_brief(w, "s-renewal", lambda t: t + "\nAn edit.\n")
    add_grant(w, "s-renewal", ["alpha", "beta"])
    add_grant(w, "s-draft", ["alpha"])
    edit_brief(w, "s-draft", lambda t: t.replace("Status:** Ready", "Status:** Draft"))
    w.commit("back to Draft")
    add_grant(w, "s-expired", ["alpha"], expired=True)
    add_grant(w, "s-both-removed", ["alpha"])
    h.git(w.main, "rm", "-q", grant_file("s-both-removed"))
    edit_brief(w, "s-both-removed", lambda t: with_record(t, None))
    w.commit("remove both")
    add_grant(w, "s-file-removed", ["alpha"])
    h.git(w.main, "rm", "-q", grant_file("s-file-removed"))
    w.commit("grant file deleted, record stays")
    add_grant(w, "s-record-removed", ["alpha"], commit=False)
    edit_brief(w, "s-record-removed", lambda t: with_record(t, None))
    w.commit("record removed, grant stays")
    add_grant(w, "s-done", ["shipped"])
    add_grant(w, "s-merge-ready-merged", ["wa"], done_when="all-granted-merged")
    add_grant(w, "s-merge-ready-stopped", ["wa"], done_when="all-granted-stopped")


@pytest.fixture(scope="module")
def stw(tmp_path_factory: pytest.TempPathFactory) -> World:
    """One world, one Ready brief per case in ``STATE_CASES``, each with its own history."""
    rows = {
        "s-done": ["shipped", "alpha"],
        "s-merge-ready-merged": ["wa", "alpha"],
        "s-merge-ready-stopped": ["wa", "alpha"],
    }
    briefs = {name: (rows.get(name, STATE_SLICES), "Ready") for name in STATE_CASES}
    w = make_world(tmp_path_factory.mktemp("grant-states"), briefs)
    for brief in ("s-merge-ready-merged", "s-merge-ready-stopped"):
        hx.make_slice(w, brief, "wa", "terminal")
    _build_state_cases(w)
    return w


def test_a_brief_with_no_grant_evidence_answers_null_and_schema_two(stw: World) -> None:
    out = nxt(stw, "s-none")
    assert out["schema_version"] == 2 and out["grant"] is None
    assert out["brief_status"] == "Ready" and out["action"]["kind"] == "start-slice"


def test_a_valid_grant_answers_its_typed_fields_only(stw: World) -> None:
    out = nxt(stw, "s-valid")
    grant = out["grant"]
    assert set(grant) == {
        "state", "reason", "detail", "human_only", "anchor", "expires_at", "done_when",
        "slices", "retry_budget", "max_slices_in_flight", "held_actions",
    }  # fmt: skip
    assert grant["state"] == "valid" and grant["reason"] is None and grant["detail"] is None
    anchor = h.git(stw.main, "log", "-1", "--format=%H", "--", grant_file("s-valid")).strip()
    assert grant["anchor"] == anchor
    assert grant["slices"] == ["alpha", "beta"] and grant["retry_budget"] == 1
    assert grant["done_when"] == "all-granted-merged" and grant["max_slices_in_flight"] == 1
    assert grant["held_actions"] == ["open-pull-request", "push"]
    assert grant["human_only"] == [
        "accept-protected-class-risk", "approve-plan", "approve-spec",
        "irreversible-operation", "merge", "reapprove-after-material-change",
    ]  # fmt: skip
    expires = datetime.strptime(grant["expires_at"], UTC_Z).replace(tzinfo=UTC)
    assert expires > STATE_CONFIRMED["s-valid"]
    assert out["action"]["kind"] == "start-slice" and out["action"]["slice"] == "alpha"
    text = json.dumps(out)
    assert "confirmed_by" not in text and OWNER not in text and "confirmed_at" not in text


def test_status_carries_the_brief_status_and_the_grant(stw: World) -> None:
    assert call(stw, "status", "s-none")[1]["grant"] is None
    code, out = call(stw, "status", "s-valid")
    assert code == 0 and out["brief_status"] == "Ready" and out["grant"]["state"] == "valid"
    assert "schema_version" not in out


def test_a_record_with_no_grant_file_is_missing(stw: World) -> None:
    assert state_of(stw, "s-record-only") == ("refused", "missing", None)
    grant = grant_of(stw, "s-record-only")
    assert grant is not None and grant["held_actions"] == ["open-pull-request", "push"]
    assert set(grant) == {"state", "reason", "detail", "human_only", "held_actions"}
    assert nxt(stw, "s-record-only")["action"]["kind"] == "grant-refused"


def test_a_grant_file_with_no_record_is_malformed(stw: World) -> None:
    assert state_of(stw, "s-grant-only") == ("refused", "malformed", "no-record")


@pytest.mark.parametrize(
    ("brief", "detail"),
    [("s-key", "unknown-key"), ("s-table", "table"), ("s-toml", "not-toml")],
)
def test_a_malformed_grant_is_refused_with_its_fixed_detail(
    stw: World, brief: str, detail: str
) -> None:
    assert state_of(stw, brief) == ("refused", "malformed", detail)


def test_a_grant_for_a_slice_outside_the_spec_map_is_malformed(stw: World) -> None:
    assert state_of(stw, "s-slices") == ("refused", "malformed", "key:slices")


def test_a_budget_above_the_lease_budget_is_malformed(stw: World) -> None:
    assert state_of(stw, "s-budget") == ("refused", "malformed", "key:retry_budget")


def test_a_record_that_differs_from_the_grant_is_malformed(stw: World) -> None:
    assert state_of(stw, "s-mismatch") == ("refused", "malformed", "record-mismatch")


def test_a_record_only_inside_an_html_comment_is_malformed(stw: World) -> None:
    assert state_of(stw, "s-comment") == ("refused", "malformed", "record-form")


def test_a_second_record_is_malformed(stw: World) -> None:
    assert state_of(stw, "s-twice") == ("refused", "malformed", "record-repeated")


def test_a_symlink_or_an_oversize_entry_at_the_grant_path_is_malformed(gw: World) -> None:
    path = gw.main / grant_file("g")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.symlink_to("../../../README-target")
    gw.commit("a symlink, no record")
    assert state_of(gw, "g") == ("refused", "malformed", "no-record")
    edit_brief(gw, "g", lambda t: with_record(t, "2026-11-01T00:00:00Z"))
    gw.commit("a symlink and a record")
    assert state_of(gw, "g") == ("refused", "malformed", "not-regular")
    path.unlink()
    path.write_text("# " + "x" * 5000 + "\n", **h._LF)
    gw.commit("oversize")
    assert state_of(gw, "g") == ("refused", "malformed", "oversize")
    edit_brief(gw, "g", lambda t: with_record(t, None))
    gw.commit("oversize, no record")
    assert state_of(gw, "g")[:2] == ("refused", "malformed")


def test_a_gitlink_or_directory_at_the_grant_path_is_evidence_and_malformed(stw: World) -> None:
    assert state_of(stw, "s-dir")[:2] == ("refused", "malformed")


def test_a_brief_edited_after_confirmation_is_stale(stw: World) -> None:
    assert state_of(stw, "s-brief-edit") == ("refused", "stale", "brief-changed")


def test_trailing_text_on_the_status_line_is_stale(stw: World) -> None:
    assert state_of(stw, "s-trailing") == ("refused", "stale", "brief-changed")


def test_a_status_token_change_alone_keeps_the_grant_bound(stw: World) -> None:
    out = nxt(stw, "s-token")
    assert out["grant"]["state"] == "valid" and out["brief_status"] == "Executing"


def test_standing_orders_added_or_edited_after_confirmation_are_stale(gw: World) -> None:
    orders = "docs/product/standing-orders/g.md"
    add_grant(gw, "g", ["alpha"])
    hx._write(gw.main, orders, "1. Keep the tests green.\n")
    gw.commit("orders added")
    assert state_of(gw, "g") == ("refused", "stale", "standing-orders-changed")
    add_grant(gw, "g", ["alpha"])  # a renewal binds the orders as they now are
    assert state_of(gw, "g") == ("valid", None, None)
    hx._write(gw.main, orders, "1. Keep the tests green.\n2. Ask first.\n")
    gw.commit("orders edited")
    assert state_of(gw, "g") == ("refused", "stale", "standing-orders-changed")


def test_standing_orders_removed_after_confirmation_are_stale(tmp_path: Path) -> None:
    w = make_world(
        tmp_path, {"g": (["alpha"], "Ready")},
        edit=lambda main: hx._write(main, "docs/product/standing-orders/g.md", "1. Be kind.\n"),
    )  # fmt: skip
    add_grant(w, "g", ["alpha"])
    assert state_of(w, "g") == ("valid", None, None)
    h.git(w.main, "rm", "-q", "docs/product/standing-orders/g.md")
    w.commit("orders removed")
    assert state_of(w, "g") == ("refused", "stale", "standing-orders-changed")


def test_a_grant_edited_alone_is_not_reconfirmed(stw: World) -> None:
    assert state_of(stw, "s-grant-alone") == ("refused", "stale", "not-reconfirmed")


def test_a_comment_only_grant_edit_beside_a_brief_edit_is_not_reconfirmed(stw: World) -> None:
    assert state_of(stw, "s-grant-and-brief") == ("refused", "stale", "not-reconfirmed")


def test_a_renewal_with_a_new_confirmation_is_valid(stw: World) -> None:
    assert state_of(stw, "s-renewal") == ("valid", None, None)


# AC-0007: a history cut short never reads as "no earlier commit". Real shallow clones.


def shallow_clone(w: World, name: str = "shallow") -> World:
    """A real ``git clone --depth 1`` of the world's origin, with its own copy of the runner."""
    clone = w.tmp / name
    h.git(w.tmp, "clone", "-q", "--depth", "1", f"file://{w.tmp / 'origin.git'}", str(clone))
    assert h.git(clone, "rev-parse", "--is-shallow-repository").strip() == "true"
    return World(w.tmp, clone, hx._load_runner(clone / hx.RUNNER_REL))


def test_a_grant_edited_alone_reads_stale_in_a_shallow_clone(
    gw: World, capsys: pytest.CaptureFixture[str]
) -> None:
    add_grant(gw, "g", ["alpha"])
    _touch_grant(gw, "g")
    gw.commit("grant edited alone")
    assert state_of(gw, "g") == ("refused", "stale", "not-reconfirmed")  # whole history
    cut = shallow_clone(gw)
    capsys.readouterr()
    assert state_of(cut, "g") == ("refused", "stale", "anchor-not-found")
    err = capsys.readouterr().err
    assert err == "grant binding failed: shallow-repository\n"
    assert str(gw.tmp) not in err


def test_a_brief_edited_after_confirmation_reads_stale_in_a_shallow_clone(gw: World) -> None:
    add_grant(gw, "g", ["alpha"])
    edit_brief(gw, "g", lambda t: t + "\nA new sentence.\n")
    gw.commit("edit the brief")
    assert state_of(gw, "g") == ("refused", "stale", "brief-changed")  # whole history
    assert state_of(shallow_clone(gw), "g") == ("refused", "stale", "anchor-not-found")


def test_a_grafted_history_fails_closed(gw: World, capsys: pytest.CaptureFixture[str]) -> None:
    add_grant(gw, "g", ["alpha"])
    assert state_of(gw, "g") == ("valid", None, None)
    (gw.main / ".git" / "info").mkdir(exist_ok=True)
    (gw.main / ".git" / "info" / "grafts").write_text("", **h._LF)
    capsys.readouterr()
    assert state_of(gw, "g") == ("refused", "stale", "anchor-not-found")
    assert capsys.readouterr().err == "grant binding failed: grafted-history\n"


def _failing_git(
    gw: World, monkeypatch: pytest.MonkeyPatch, fails: Callable[[tuple[str, ...]], bool]
) -> None:
    """Make Git fail for the calls *fails* names, once the binding's anchor lookup has begun."""
    real = gw.runner.git
    armed = False

    def wrapped(root: Path, *args: str, **kwargs: Any) -> Any:
        nonlocal armed
        armed = armed or "--first-parent" in args  # the binding's own reads come after this
        if armed and fails(args):
            raise gw.runner.Refusal("git-unavailable", "boom /secret/path")
        return real(root, *args, **kwargs)

    monkeypatch.setattr(gw.runner, "git", wrapped)


@pytest.mark.parametrize(
    ("fails", "reason"),
    [
        (lambda a: a[0] == "log" and "--first-parent" in a, "read-failed"),
        (lambda a: a[0] == "log" and "--no-walk" in a, "anchor-parent-unreadable"),
        (lambda a: a[0] == "ls-tree" and a[-1] == "docs/product/standing-orders/g.md",
         "read-failed"),
        (lambda a: a[0] == "ls-tree" and a[-1] == "docs/product/briefs/g.md", "read-failed"),
        (lambda a: a[0] == "cat-file" and "blob" in a, "read-failed"),
    ],
    ids=["no-anchor", "unreadable-parent", "unreadable-orders", "unreadable-brief", "unreadable-blob"],
)
def test_an_unreadable_anchor_parent_or_entry_never_reads_as_absent(
    gw: World,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    fails: Callable[[tuple[str, ...]], bool],
    reason: str,
) -> None:
    confirmed = add_grant(gw, "g", ["alpha"])
    base = gw.runner.base_checks(gw.main)
    anchor = gw.runner.binding_problem(gw.main, base, "g", confirmed)
    assert anchor == (h.git(gw.main, "rev-parse", "HEAD").strip(), None)
    _failing_git(gw, monkeypatch, fails)
    capsys.readouterr()
    assert gw.runner.binding_problem(gw.main, base, "g", confirmed) == (None, "anchor-not-found")
    err = capsys.readouterr().err
    assert err == f"grant binding failed: {reason}\n" and "secret" not in err


def test_the_anchor_parent_is_the_first_parent_and_none_only_for_a_root_commit(
    tmp_path: Path,
) -> None:
    w = make_world(tmp_path, {"g": (["alpha"], "Ready")})
    add_grant(w, "g", ["alpha"])
    head = h.git(w.main, "rev-parse", "HEAD").strip()
    assert w.runner._first_parent(w.main, head) == h.git(w.main, "rev-parse", "HEAD~1").strip()
    root = h.git(w.main, "rev-list", "--max-parents=0", "HEAD").strip()
    assert w.runner._first_parent(w.main, root) is None


def test_removing_both_grant_and_record_is_a_no_grant_run(stw: World) -> None:
    assert nxt(stw, "s-both-removed")["grant"] is None


def test_removing_only_one_of_them_refuses_and_the_other_reads_missing(stw: World) -> None:
    assert state_of(stw, "s-file-removed") == ("refused", "missing", None)
    assert state_of(stw, "s-record-removed") == ("refused", "malformed", "no-record")


def test_a_draft_brief_with_a_grant_is_not_ready_and_names_no_slice(stw: World) -> None:
    out = nxt(stw, "s-draft", now=BEFORE_END)
    assert (out["grant"]["state"], out["grant"]["reason"]) == ("refused", "brief-not-ready")
    assert out["grant"]["detail"] is None
    assert out["action"]["kind"] == "grant-refused" and "slice" not in out["action"]


@pytest.mark.parametrize("status", ["Shipped", "Withdrawn", "Cancelled"])
def test_a_closed_brief_with_a_grant_is_spent_and_complete_when_all_merged(
    tmp_path: Path, status: str
) -> None:
    w = make_world(tmp_path, {"g": (["shipped", "alpha"], "Ready"), "m": (["shipped"], "Ready")})
    for brief, slugs in (("g", ["alpha"]), ("m", ["shipped"])):
        add_grant(w, brief, slugs)
        edit_brief(w, brief, lambda t: t.replace("Status:** Ready", f"Status:** {status}"))
    w.commit("close both")
    out = nxt(w, "g")
    assert (out["grant"]["state"], out["grant"]["reason"]) == ("spent", "brief-closed")
    assert set(out["grant"]) == {"state", "reason", "detail", "human_only", "held_actions"}
    assert out["action"]["kind"] == "grant-spent" and out["action"]["reason"] == "brief-closed"
    assert nxt(w, "m")["action"] == {"kind": "complete", "base": out["base"]}


def test_an_expired_grant_is_spent(stw: World) -> None:
    out = nxt(stw, "s-expired")
    assert (out["grant"]["state"], out["grant"]["reason"]) == ("spent", "expired")
    assert out["grant"]["anchor"] and out["grant"]["expires_at"]
    assert out["action"]["kind"] == "grant-spent" and "slice" not in out["action"]


def test_a_grant_expires_at_the_instant_of_expiry(stw: World) -> None:
    expires = datetime.strptime(nxt(stw, "s-valid")["grant"]["expires_at"], UTC_Z).replace(tzinfo=UTC)
    assert nxt(stw, "s-valid", now=expires - timedelta(seconds=1))["grant"]["state"] == "valid"
    assert nxt(stw, "s-valid", now=expires)["grant"]["reason"] == "expired"


def test_done_when_all_granted_merged_is_spent_when_every_granted_slice_is_merged(
    stw: World,
) -> None:
    out = nxt(stw, "s-done")
    assert (out["grant"]["state"], out["grant"]["reason"]) == ("spent", "done")
    assert out["action"]["kind"] == "grant-spent"


@pytest.mark.parametrize(
    ("brief", "state"),
    [("s-merge-ready-merged", "valid"), ("s-merge-ready-stopped", "spent")],
)
def test_a_merge_ready_granted_slice_is_done_only_for_all_granted_stopped(
    stw: World, brief: str, state: str
) -> None:
    assert stw.rows(brief)["wa"].stop == "merge-ready"
    assert nxt(stw, brief)["grant"]["state"] == state


# ── AC-0012: grant-refused and grant-spent ──────────────────────────────────

GATE_STATES = {"wa": "parked", "wb": "terminal", "wc": "implementing"}


@pytest.fixture(scope="module")
def gates_world(tmp_path_factory: pytest.TempPathFactory) -> World:
    briefs = {name: (["wa", "wb", "wc"], "Ready") for name in ("g-plain", "g-stale", "g-spent")}
    w = make_world(tmp_path_factory.mktemp("grant-gates"), briefs)
    for brief in briefs:
        for slug, state in GATE_STATES.items():
            hx.make_slice(w, brief, slug, state)
    add_grant(w, "g-stale", ["wa", "wb", "wc"])
    edit_brief(w, "g-stale", lambda t: t + "\nEdited after the stop.\n")
    add_grant(w, "g-spent", ["wa", "wb", "wc"], expired=True)
    return w


@pytest.mark.parametrize(
    ("brief", "kind", "reason"),
    [("g-stale", "grant-refused", "stale"), ("g-spent", "grant-spent", "expired")],
)
def test_a_refused_or_spent_grant_carries_gates_and_merge_ready_and_names_no_slice(
    gates_world: World, brief: str, kind: str, reason: str
) -> None:
    plain = nxt(gates_world, "g-plain")["action"]
    assert plain["kind"] == "resume-slice" and plain["slice"] == "wc"  # a row is resumable
    action = nxt(gates_world, brief)["action"]
    assert action["kind"] == kind and action["reason"] == reason
    assert action["detail"] == ("brief-changed" if reason == "stale" else None)
    assert [(g["slice"], g["state"]) for g in action["gates"]] == [("wa", "pending")]
    assert action["gates"][0]["worktree"] == str(gates_world.wt(brief, "wa"))
    assert action["merge_ready"] == ["wb"] and action["spec_paths"] == ["docs/specs/wb"]
    assert not {"slice", "worktree", "stage", "branch", "mode"} & set(action)


# ── AC-0013: a valid grant over rows ────────────────────────────────────────

SLICE_BRIEFS: dict[str, tuple[list[str], dict[str, str], list[str]]] = {
    "s-start": (["alpha", "delta"], {}, ["alpha"]),
    "s-earlier": (["alpha", "delta"], {}, ["delta"]),
    "s-pilot": (["alpha", "wa"], {}, ["wa"]),
    "s-cap": (["wa", "alpha"], {"wa": "decision"}, ["alpha"]),
    "s-cap-granted": (["wa", "alpha"], {"wa": "decision"}, ["wa", "alpha"]),
    "s-refused": (["wc", "alpha"], {"wc": "residue"}, ["alpha"]),
    "s-parked": (["shipped", "wa", "alpha"], {"wa": "parked"}, ["wa", "alpha"]),
    "s-impl-other": (["wa", "alpha"], {"wa": "implementing"}, ["alpha"]),
    "s-impl-own": (["wa", "alpha"], {"wa": "implementing"}, ["wa"]),
    "s-merged-first": (["shipped", "alpha", "wa"], {}, ["alpha", "wa"]),
}


def _slice_world(tmp: Path, *, granted: bool) -> World:
    """The slice-state fixture briefs, each with a valid grant, or with none (the sibling)."""
    briefs = {name: (rows, "Ready") for name, (rows, _, _) in SLICE_BRIEFS.items()}
    w = make_world(tmp, briefs)
    for name, (_, states, slices) in SLICE_BRIEFS.items():
        for slug, state in states.items():
            hx.make_slice(w, name, slug, state)
        if granted:
            add_grant(w, name, slices)
    return w


@pytest.fixture(scope="module")
def sw(tmp_path_factory: pytest.TempPathFactory) -> World:
    return _slice_world(tmp_path_factory.mktemp("grant-slices"), granted=True)


@pytest.fixture(scope="module")
def sw_plain(tmp_path_factory: pytest.TempPathFactory) -> World:
    """The same briefs and slice states as ``sw``, with no grant evidence at all."""
    return _slice_world(tmp_path_factory.mktemp("grant-slices-plain"), granted=False)


def test_a_granted_ready_row_starts(sw: World) -> None:
    action = nxt(sw, "s-start")["action"]
    assert action["kind"] == "start-slice" and action["slice"] == "alpha"


def test_a_non_granted_row_is_not_granted_and_never_named(sw: World) -> None:
    assert sw.rows("s-earlier")["alpha"].ready
    out = nxt(sw, "s-earlier")
    assert reasons(out) == {"alpha": "not-granted", "delta": "waits-on-ungranted"}


def test_a_granted_row_behind_a_non_granted_pilot_waits_on_it(sw: World) -> None:
    rows = sw.rows("s-pilot")
    assert rows["alpha"].ready and rows["wa"].ready, "the fixture needs two ready rows"
    assert reasons(nxt(sw, "s-pilot")) == {"alpha": "not-granted", "wa": "waits-on-ungranted"}


def test_a_granted_row_under_a_cap_filled_by_a_non_granted_row_waits_on_it(sw: World) -> None:
    assert reasons(nxt(sw, "s-cap")) == {"wa": "awaiting-decision", "alpha": "waits-on-ungranted"}


def test_a_granted_in_flight_row_filling_the_cap_keeps_the_cap_reason(sw: World) -> None:
    assert reasons(nxt(sw, "s-cap-granted")) == {
        "wa": "awaiting-decision", "alpha": "in-flight-cap",
    }  # fmt: skip


def test_a_non_granted_row_keeps_its_own_slice_state_reason(sw: World) -> None:
    out = nxt(sw, "s-refused")
    assert reasons(out) == {"wc": "refused", "alpha": "waits-on-ungranted"}
    (refused,) = [r for r in out["action"]["rows"] if r["slice"] == "wc"]
    assert refused["code"] == "attempt-residue"


def test_the_cap_of_a_valid_grant_is_one(sw: World, sw_plain: World) -> None:
    assert sw.runner.read_lease_cap(sw.main, sw.runner.base_checks(sw.main)) == 2
    assert nxt(sw_plain, "s-parked")["action"]["kind"] == "start-slice"  # the no-grant answer
    assert nxt(sw, "s-parked")["action"]["kind"] == "await-gates"


def test_an_in_flight_row_that_is_not_granted_is_not_resumed(sw: World) -> None:
    out = nxt(sw, "s-impl-other")
    assert reasons(out) == {"wa": "not-granted", "alpha": "waits-on-ungranted"}


def test_an_in_flight_granted_row_is_resumed(sw: World) -> None:
    action = nxt(sw, "s-impl-own")["action"]
    assert action["kind"] == "resume-slice" and action["slice"] == "wa"
    assert "exemption" not in action


# ── AC-0014: a grant never widens what next may name ────────────────────────


def test_a_valid_grant_names_only_a_slice_the_same_brief_names_without_one(
    sw: World, sw_plain: World
) -> None:
    named_under_grant = 0
    for brief in SLICE_BRIEFS:
        granted = nxt(sw, brief)
        plain = nxt(sw_plain, brief)  # a real `next` on the same brief with no grant evidence
        assert granted["grant"]["state"] == "valid" and plain["grant"] is None, brief
        slice_named = granted["action"].get("slice")
        if granted["action"]["kind"] in ("resume-slice", "start-slice"):
            named_under_grant += 1
            assert plain["action"]["kind"] == granted["action"]["kind"], brief
            assert plain["action"]["slice"] == slice_named, brief
            assert slice_named in granted["grant"]["slices"], brief
        else:
            assert slice_named is None, brief
    assert named_under_grant >= 3  # the property is not vacuous over these fixtures


# ── AC-0016: nothing is written ─────────────────────────────────────────────


def test_no_verb_changes_git_state_or_a_slice_store_over_a_granted_brief(sw: World) -> None:
    before = hx._snapshot(sw)
    slice_files = {
        str(p): p.read_bytes()
        for brief in SLICE_BRIEFS
        for p in sorted(sw.tmp.glob(f"wt-{brief}-*/**/*"))
        if p.is_file() and ".git" not in p.parts
    }
    for brief in ("s-start", "s-impl-own", "s-cap", "s-parked"):
        for verb in ("status", "next", "gates"):
            assert call(sw, verb, brief)[0] == 0
    wa = hx.task_id_of(sw.wt("s-impl-own", "wa"), "wa")
    assert call(sw, "classify", "s-impl-own", "--slice", "wa", "--task", wa, "--class", "stuck")[0] == 0
    assert hx._snapshot(sw) == before
    after = {
        str(p): p.read_bytes()
        for brief in SLICE_BRIEFS
        for p in sorted(sw.tmp.glob(f"wt-{brief}-*/**/*"))
        if p.is_file() and ".git" not in p.parts
    }
    assert after == slice_files


def test_the_binding_starts_only_read_only_git(sw: World, monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list[list[str]] = []
    real = sw.runner.subprocess.run

    def record(argv: list[str], *a: Any, **k: Any) -> Any:
        seen.append([str(x) for x in argv])
        return real(argv, *a, **k)

    monkeypatch.setattr(sw.runner.subprocess, "run", record)
    assert call(sw, "next", "s-start")[0] == 0
    git_calls = [a for a in seen if a[0] == "git" and "-C" in a]
    assert any(a[a.index("-C") + 2] == "log" for a in git_calls)
    assert all(a[a.index("-C") + 2] in hx.READ_ONLY_GIT for a in git_calls)


# ── AC-0017: classify under a grant ─────────────────────────────────────────


def test_classify_uses_the_grant_budget_and_surfaces_under_a_refused_grant(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def edit(main: Path) -> None:
        hx._write(main, "docs/specs/wa/plan.md", hx.PLAIN_PLAN)

    w = make_world(tmp_path, {"g": (["wa"], "Ready")}, edit=edit)
    wt = w.add_slice("g", "wa")
    hx.start_run(wt, "wa")
    monkeypatch.setattr(h, "SPEC_DIR", "docs/specs/wa")
    controller = h.Controller(wt, tmp_path / "effects.log")
    task = hx.task_id_of(wt, "wa")

    def classify(cls: str = "network") -> tuple[int, dict[str, Any]]:
        return call(w, "classify", "g", "--slice", "wa", "--task", task, "--class", cls)

    assert classify()[1]["action"] == "retry"  # no grant: the lease's budget
    add_grant(w, "g", ["wa"], budget=0)
    assert classify()[1] == {
        "base": h.git(w.main, "rev-parse", "HEAD").strip(), "action": "retry",
        "failed_attempts": 0,
    }  # fmt: skip
    _, payload = h.run_cli(wt, "next", "docs/specs/wa")
    result = controller.work(payload["request"])
    result["gate"] = {"passed": False}
    assert controller.report(result)[0] == 0
    code, out = classify()
    assert code == 0 and out["failed_attempts"] == 1 and out["action"] == "abandon-and-replan"
    edit_brief(w, "g", lambda t: t + "\nEdited after the stop.\n")
    w.commit("stale")
    for cls in hx.CLASSES:
        assert classify(cls)[1]["action"] == "surface-to-human", cls
    h.git(w.main, "rm", "-q", grant_file("g"))
    w.commit("grant file deleted")  # the record stays: refused, missing
    assert classify()[1]["action"] == "surface-to-human"
