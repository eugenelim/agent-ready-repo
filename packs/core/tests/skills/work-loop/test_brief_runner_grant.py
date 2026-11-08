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


def test_a_brief_with_no_grant_evidence_answers_null_and_schema_two(gw: World) -> None:
    out = nxt(gw, "g")
    assert out["schema_version"] == 2 and out["grant"] is None
    assert out["brief_status"] == "Ready" and out["action"]["kind"] == "start-slice"


def test_a_valid_grant_answers_its_typed_fields_only(gw: World) -> None:
    confirmed = add_grant(gw, "g", ["alpha", "beta"], budget=1, held=["push", "open-pull-request"])
    out = nxt(gw, "g")
    grant = out["grant"]
    assert set(grant) == {
        "state", "reason", "detail", "human_only", "anchor", "expires_at", "done_when",
        "slices", "retry_budget", "max_slices_in_flight", "held_actions",
    }  # fmt: skip
    assert grant["state"] == "valid" and grant["reason"] is None and grant["detail"] is None
    assert grant["anchor"] == h.git(gw.main, "rev-parse", "HEAD").strip()
    assert grant["slices"] == ["alpha", "beta"] and grant["retry_budget"] == 1
    assert grant["done_when"] == "all-granted-merged" and grant["max_slices_in_flight"] == 1
    assert grant["held_actions"] == ["open-pull-request", "push"]
    assert grant["human_only"] == [
        "accept-protected-class-risk", "approve-plan", "approve-spec",
        "irreversible-operation", "merge", "reapprove-after-material-change",
    ]  # fmt: skip
    assert datetime.strptime(grant["expires_at"], UTC_Z).replace(tzinfo=UTC) > confirmed
    assert out["action"]["kind"] == "start-slice" and out["action"]["slice"] == "alpha"
    text = json.dumps(out)
    assert "confirmed_by" not in text and OWNER not in text and "confirmed_at" not in text


def test_status_carries_the_brief_status_and_the_grant(gw: World) -> None:
    assert call(gw, "status", "g")[1]["grant"] is None
    add_grant(gw, "g", ["alpha"])
    code, out = call(gw, "status", "g")
    assert code == 0 and out["brief_status"] == "Ready" and out["grant"]["state"] == "valid"
    assert "schema_version" not in out


def test_a_record_with_no_grant_file_is_missing(gw: World) -> None:
    edit_brief(gw, "g", lambda t: with_record(t, "2026-11-01T00:00:00Z"))
    gw.commit("record only")
    assert state_of(gw, "g") == ("refused", "missing", None)
    grant = grant_of(gw, "g")
    assert grant is not None and grant["held_actions"] == ["open-pull-request", "push"]
    assert set(grant) == {"state", "reason", "detail", "human_only", "held_actions"}
    assert nxt(gw, "g")["action"]["kind"] == "grant-refused"


def test_a_grant_file_with_no_record_is_malformed(gw: World) -> None:
    add_grant(gw, "g", ["alpha"], commit=False)
    edit_brief(gw, "g", lambda t: with_record(t, None))
    gw.commit("grant only")
    assert state_of(gw, "g") == ("refused", "malformed", "no-record")


@pytest.mark.parametrize(
    ("extra", "detail"),
    [("spend_cap = 3\n", "unknown-key"), ("[t]\nx = 1\n", "table"), ("what = \n", "not-toml")],
)
def test_a_malformed_grant_is_refused_with_its_fixed_detail(
    gw: World, extra: str, detail: str
) -> None:
    add_grant(gw, "g", ["alpha"], extra=extra)
    assert state_of(gw, "g") == ("refused", "malformed", detail)


def test_a_grant_for_a_slice_outside_the_spec_map_is_malformed(gw: World) -> None:
    add_grant(gw, "g", ["nowhere"])
    assert state_of(gw, "g") == ("refused", "malformed", "key:slices")


def test_a_budget_above_the_lease_budget_is_malformed(gw: World) -> None:
    add_grant(gw, "g", ["alpha"], budget=99)
    assert state_of(gw, "g") == ("refused", "malformed", "key:retry_budget")


def test_a_record_that_differs_from_the_grant_is_malformed(gw: World) -> None:
    add_grant(gw, "g", ["alpha"], commit=False)
    edit_brief(gw, "g", lambda t: with_record(t, "2020-01-01T00:00:00Z"))
    gw.commit("wrong record time")
    assert state_of(gw, "g") == ("refused", "malformed", "record-mismatch")


def test_a_record_only_inside_an_html_comment_is_malformed(gw: World) -> None:
    confirmed = add_grant(gw, "g", ["alpha"], commit=False)
    edit_brief(gw, "g", lambda t: with_record(t, None))
    stamp = confirmed.strftime(UTC_Z)
    edit_brief(
        gw, "g", lambda t: t.replace("\n## Spec map", f"<!--\n- **Run grant:** required "
                                     f"(confirmed {stamp})\n-->\n\n## Spec map")
    )  # fmt: skip
    gw.commit("record in a comment")
    assert state_of(gw, "g") == ("refused", "malformed", "record-form")


def test_a_second_record_is_malformed(gw: World) -> None:
    confirmed = add_grant(gw, "g", ["alpha"], commit=False)
    edit_brief(gw, "g", lambda t: t + f"\nNote: **Run grant:** again {confirmed}\n")
    gw.commit("two marks")
    assert state_of(gw, "g") == ("refused", "malformed", "record-repeated")


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


def test_a_gitlink_or_directory_at_the_grant_path_is_evidence_and_malformed(gw: World) -> None:
    hx._write(gw.main, f"{grant_file('g')}/inner.txt", "a directory where a file belongs\n")
    gw.commit("a tree entry")
    assert state_of(gw, "g")[:2] == ("refused", "malformed")


def test_a_brief_edited_after_confirmation_is_stale(gw: World) -> None:
    add_grant(gw, "g", ["alpha"])
    edit_brief(gw, "g", lambda t: t + "\nA new sentence.\n")
    gw.commit("edit the brief")
    assert state_of(gw, "g") == ("refused", "stale", "brief-changed")


def test_trailing_text_on_the_status_line_is_stale(gw: World) -> None:
    add_grant(gw, "g", ["alpha"])
    edit_brief(gw, "g", lambda t: t.replace("- **Status:** Ready", "- **Status:** Ready (cut 2)"))
    gw.commit("trailing text")
    assert state_of(gw, "g") == ("refused", "stale", "brief-changed")


def test_a_status_token_change_alone_keeps_the_grant_bound(gw: World) -> None:
    add_grant(gw, "g", ["alpha"])
    edit_brief(gw, "g", lambda t: t.replace("Status:** Ready", "Status:** Executing"))
    gw.commit("Ready to Executing")
    out = nxt(gw, "g")
    assert out["grant"]["state"] == "valid" and out["brief_status"] == "Executing"


def test_standing_orders_added_or_edited_after_confirmation_are_stale(gw: World) -> None:
    orders = "docs/product/standing-orders/g.md"
    add_grant(gw, "g", ["alpha"])
    hx._write(gw.main, orders, "1. Keep the tests green.\n")
    gw.commit("orders added")
    assert state_of(gw, "g") == ("refused", "stale", "standing-orders-changed")
    add_grant(gw, "g", ["alpha"])  # a renewal binds the orders as they now are
    assert state_of(gw, "g")[0] == "refused" or state_of(gw, "g")[0] == "valid"
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


def test_a_grant_edited_alone_is_not_reconfirmed(gw: World) -> None:
    add_grant(gw, "g", ["alpha"])
    path = gw.main / grant_file("g")
    path.write_text(path.read_text("utf-8") + "# a comment\n", **h._LF)
    gw.commit("grant edited alone")
    assert state_of(gw, "g") == ("refused", "stale", "not-reconfirmed")


def test_a_comment_only_grant_edit_beside_a_brief_edit_is_not_reconfirmed(gw: World) -> None:
    add_grant(gw, "g", ["alpha"])
    path = gw.main / grant_file("g")
    path.write_text(path.read_text("utf-8") + "# a comment\n", **h._LF)
    edit_brief(gw, "g", lambda t: t + "\nAn edit.\n")
    gw.commit("grant comment and brief edit together")
    assert state_of(gw, "g") == ("refused", "stale", "not-reconfirmed")


def test_a_renewal_with_a_new_confirmation_is_valid(gw: World) -> None:
    add_grant(gw, "g", ["alpha"])
    edit_brief(gw, "g", lambda t: t + "\nAn edit.\n")
    add_grant(gw, "g", ["alpha", "beta"])
    assert state_of(gw, "g") == ("valid", None, None)


def test_a_shallow_history_has_no_anchor_and_fails_closed(
    gw: World, monkeypatch: pytest.MonkeyPatch
) -> None:
    add_grant(gw, "g", ["alpha"])
    real = gw.runner.git

    def failing(root: Path, *args: str, **kwargs: Any) -> Any:
        if args and args[0] == "log":
            raise gw.runner.Refusal("git-unavailable", "boom")
        return real(root, *args, **kwargs)

    monkeypatch.setattr(gw.runner, "git", failing)
    assert state_of(gw, "g") == ("refused", "stale", "anchor-not-found")


def test_removing_both_grant_and_record_is_a_no_grant_run(gw: World) -> None:
    add_grant(gw, "g", ["alpha"])
    h.git(gw.main, "rm", "-q", grant_file("g"))
    edit_brief(gw, "g", lambda t: with_record(t, None))
    gw.commit("remove both")
    assert nxt(gw, "g")["grant"] is None


def test_removing_only_one_of_them_refuses_and_the_other_reads_missing(gw: World) -> None:
    add_grant(gw, "g", ["alpha"])
    h.git(gw.main, "rm", "-q", grant_file("g"))
    gw.commit("grant file deleted, record stays")
    assert state_of(gw, "g") == ("refused", "missing", None)
    add_grant(gw, "g", ["alpha"])
    edit_brief(gw, "g", lambda t: with_record(t, None))
    gw.commit("record removed, grant stays")
    assert state_of(gw, "g") == ("refused", "malformed", "no-record")


def test_a_draft_brief_with_a_grant_is_not_ready_and_names_no_slice(gw: World) -> None:
    add_grant(gw, "g", ["alpha"])
    edit_brief(gw, "g", lambda t: t.replace("Status:** Ready", "Status:** Draft"))
    gw.commit("back to Draft")
    out = nxt(gw, "g", now=BEFORE_END)
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


def test_an_expired_grant_is_spent(gw: World) -> None:
    add_grant(gw, "g", ["alpha"], expired=True)
    out = nxt(gw, "g")
    assert (out["grant"]["state"], out["grant"]["reason"]) == ("spent", "expired")
    assert out["grant"]["anchor"] and out["grant"]["expires_at"]
    assert out["action"]["kind"] == "grant-spent" and "slice" not in out["action"]


def test_a_grant_expires_at_the_instant_of_expiry(gw: World) -> None:
    add_grant(gw, "g", ["alpha"])
    expires = datetime.strptime(nxt(gw, "g")["grant"]["expires_at"], UTC_Z).replace(tzinfo=UTC)
    assert nxt(gw, "g", now=expires - timedelta(seconds=1))["grant"]["state"] == "valid"
    assert nxt(gw, "g", now=expires)["grant"]["reason"] == "expired"


def test_done_when_all_granted_merged_is_spent_when_every_granted_slice_is_merged(
    tmp_path: Path,
) -> None:
    w = make_world(tmp_path, {"g": (["shipped", "alpha"], "Ready")})
    add_grant(w, "g", ["shipped"])
    out = nxt(w, "g")
    assert (out["grant"]["state"], out["grant"]["reason"]) == ("spent", "done")
    assert out["action"]["kind"] == "grant-spent"


@pytest.mark.parametrize(
    ("done_when", "state"), [("all-granted-merged", "valid"), ("all-granted-stopped", "spent")]
)
def test_a_merge_ready_granted_slice_is_done_only_for_all_granted_stopped(
    tmp_path: Path, done_when: str, state: str
) -> None:
    w = make_world(tmp_path, {"g": (["wa", "alpha"], "Ready")})
    hx.make_slice(w, "g", "wa", "terminal")
    assert w.rows("g")["wa"].stop == "merge-ready"
    add_grant(w, "g", ["wa"], done_when=done_when)
    assert nxt(w, "g")["grant"]["state"] == state


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


@pytest.fixture(scope="module")
def sw(tmp_path_factory: pytest.TempPathFactory) -> World:
    briefs = {name: (rows, "Ready") for name, (rows, _, _) in SLICE_BRIEFS.items()}
    w = make_world(tmp_path_factory.mktemp("grant-slices"), briefs)
    for name, (_, states, slices) in SLICE_BRIEFS.items():
        for slug, state in states.items():
            hx.make_slice(w, name, slug, state)
        add_grant(w, name, slices)
    return w


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


def test_the_cap_of_a_valid_grant_is_one(sw: World) -> None:
    assert sw.runner.read_lease_cap(sw.main, sw.runner.base_checks(sw.main)) == 2
    _, rows = sw.runner.read_brief(sw.main, "s-parked")
    sw.runner.attach_gates(rows)
    assert sw.runner.decide_next(rows, 2)["kind"] == "start-slice"  # the no-grant answer
    assert nxt(sw, "s-parked")["action"]["kind"] == "await-gates"


def test_an_in_flight_row_that_is_not_granted_is_not_resumed(sw: World) -> None:
    out = nxt(sw, "s-impl-other")
    assert reasons(out) == {"wa": "not-granted", "alpha": "waits-on-ungranted"}


def test_an_in_flight_granted_row_is_resumed(sw: World) -> None:
    action = nxt(sw, "s-impl-own")["action"]
    assert action["kind"] == "resume-slice" and action["slice"] == "wa"
    assert "exemption" not in action


# ── AC-0014: a grant never widens what next may name ────────────────────────


def allowed_slices(runner: ModuleType, rows: list[Any], cap: int) -> set[str]:
    """The slices the no-grant rule may name: resumable rows, and ready rows if the cap allows."""
    out = {row.slice for row in rows if runner._resumable(row)}
    in_flight = sum(1 for row in rows if row.present and row.stop == "none")
    pilot = runner._pilot(rows)
    if in_flight < cap:
        out |= {row.slice for row in rows if row.ready and pilot in (None, row.slice)}
    return out


def test_a_valid_grant_names_only_a_slice_the_same_brief_allows_without_one(
    sw: World, gates_world: World
) -> None:
    checked = 0
    for world, briefs in ((sw, list(SLICE_BRIEFS)), (gates_world, ["g-stale", "g-spent"])):
        for brief in briefs:
            out = nxt(world, brief)
            named = out["action"].get("slice")
            _, rows = world.runner.read_brief(world.main, brief)
            world.runner.attach_gates(rows)
            cap = world.runner.read_lease_cap(world.main, world.runner.base_checks(world.main))
            allowed = allowed_slices(world.runner, rows, cap)
            if out["action"]["kind"] in ("resume-slice", "start-slice"):
                assert named in allowed, brief
                assert out["grant"]["state"] == "valid", brief
                assert named in out["grant"]["slices"], brief
            checked += 1
            if not allowed:
                assert named is None, brief
    assert checked == len(SLICE_BRIEFS) + 2


def test_every_fixture_brief_with_a_valid_grant_stays_inside_the_no_grant_choice(
    sw: World,
) -> None:
    for brief in SLICE_BRIEFS:
        granted = nxt(sw, brief)
        _, rows = sw.runner.read_brief(sw.main, brief)
        sw.runner.attach_gates(rows)
        plain = sw.runner.decide_next(rows, 2)
        if granted["action"]["kind"] in ("resume-slice", "start-slice"):
            assert plain["kind"] in ("resume-slice", "start-slice"), brief


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
