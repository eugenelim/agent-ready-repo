"""Frozen `needs`-form outcomes for the `Depends on:` header equivalence suite.

Spec: docs/specs/depends-on-headers/spec.md (AC-0003, AC-0007, AC-0008).
Verification mode: TDD, paired fixtures.

Each case is one repository whose waiting item has a single dependency edge,
written as a typed ``needs`` entry in ``workspace.toml``. The outcome of the
unchanged engine (commit ``1f9c27342``) is frozen in
``fixtures/depends-on-headers/expected.json``. A later task writes the same
edge as a header, from the ``Case`` fields below, and must reproduce it.

The header form of each case must reproduce that outcome, and the ``needs`` form
under the current engine is refused as ``unmigrated_needs``. ``expected.json``
stays the frozen record: it is never re-recorded.

The cooled brief cases were not in that record. Their ``needs``-form outcome is
recorded in ``fixtures/depends-on-headers/expected-cooled-brief.json`` from the
engine at commit ``1f9c27342``, checked out as a ``git worktree`` so its sibling
modules are that commit's. To re-record, run this file with
``DEPENDS_ON_HEADERS_ENGINE=<worktree>/packs/core/.apm/skills/workspace-status/scripts/workspace_status_engine.py``
and ``DEPENDS_ON_HEADERS_RECORD_COOLED_BRIEF=1`` set.
"""
from __future__ import annotations

import dataclasses
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

_PACK_ROOT = Path(__file__).resolve().parents[3]
_SCRIPTS = _PACK_ROOT / ".apm/skills/workspace-status/scripts"
_ENGINE_PATH = Path(
    os.environ.get(
        "DEPENDS_ON_HEADERS_ENGINE", _SCRIPTS / "workspace_status_engine.py"
    )
)
_STATUS_PATH = _SCRIPTS / "workspace_status.py"
_FIXTURES = Path(__file__).parent / "fixtures/depends-on-headers"
_EXPECTED_PATH = _FIXTURES / "expected.json"
_COOLED_BRIEF_PATH = _FIXTURES / "expected-cooled-brief.json"
_RECORD_COOLED_BRIEF = os.environ.get("DEPENDS_ON_HEADERS_RECORD_COOLED_BRIEF") == "1"
_MODULE_NAME = "workspace_status_engine_depends_on_headers_equivalence"

WAITER = "docs/specs/waiter/spec.md"
PEER = "docs/specs/peer/spec.md"
BRIEF_DIR = "docs/product/briefs"
INTENT_DIR = "docs/product/intents"
RECEIPT_BLOCK_OK = "remote-rev-9"
_ABSENT = object()


def _load_engine() -> ModuleType:
    """Load the engine by file path under a unique module name."""
    spec = importlib.util.spec_from_file_location(_MODULE_NAME, _ENGINE_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load {_ENGINE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[_MODULE_NAME] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(_MODULE_NAME, None)
    return module


ENGINE = _load_engine()


@dataclasses.dataclass(frozen=True)
class Case:
    """One equivalence case: a waiting item, its edge, and the files around it.

    ``target`` is the reference a header would carry (``spec:<slug>``,
    ``brief:<slug>``, ``intent:<slug>``, or a captured-item path). ``needs`` is
    the TOML inline table of the same edge. ``receipt`` is the receipt the edge
    carries, as ``("completion", fields)`` or ``("coordination", fields)``.
    ``files`` maps repository paths to content and always holds the waiting
    item, whose preamble can take a ``- **Depends on:**`` line. ``extras`` are
    ``(table, list, rendered_entry)`` registry entries beyond the waiter.
    ``cooled`` lists spec paths that get a lifecycle record.
    """

    case_id: str
    waiting_path: str
    target: str
    needs: str
    files: dict[str, str]
    extras: tuple[tuple[str, str, str], ...] = ()
    cooled: tuple[str, ...] = ()
    receipt: tuple[str, dict[str, str]] | None = None
    waiter_workspace_kind: str = "spec"
    # The header form of a case whose `extras` carry a `needs` edge of their own.
    header_extras: tuple[tuple[str, str, str], ...] | None = None
    # `(path, reference)`: a second waiting item and the header edge it carries.
    peer_header: tuple[str, str] | None = None


def _entry(path: str, kind: str = "spec", *, parent: Any = _ABSENT, needs: str = "[]") -> str:
    """Render one canonical registry entry as a TOML inline table."""
    clause = "" if parent is _ABSENT else f', parent = "{parent}"'
    return (
        f'{{path = "{path}", kind = "{kind}", source = {{mode = "repo-origin"{clause}}}, '
        f'summary = "fixture", needs = {needs}}}'
    )


def _spec_file(slug: str, status: str = "Approved", extra: str = "") -> str:
    return f"# Spec: {slug}\n\n- **Status:** {status}\n- **Brief:** none\n{extra}"


def _local_need(kind: str, path: str, receipt: dict[str, str] | None = None) -> str:
    need = f'{{type = "local", kind = "{kind}", path = "{path}"'
    if receipt is not None:
        rendered = ", ".join(f'{k} = "{v}"' for k, v in receipt.items())
        need += f", receipt = {{{rendered}}}"
    return need + "}"


def _cross_need(brief_path: str, revision: str) -> str:
    return (
        f'{{type = "cross-repo", kind = "brief", path = "{brief_path}", '
        f'containing_brief = "{brief_path}", receipt_id = "remote-prereq", '
        f'accepted_revision = "{revision}"}}'
    )


def _waiter_files() -> dict[str, str]:
    """The waiting spec and its sibling plan."""
    return {
        WAITER: _spec_file("waiter"),
        "docs/specs/waiter/plan.md": "# Plan\n\n- **Status:** Approved\n",
    }


def _record(delivery_id: str, locator: str) -> str:
    """A schema-valid Cooling lifecycle record, as JSON text."""
    return json.dumps(
        {
            "schema": "delivery-lifecycle-record.v1",
            "delivery_id": delivery_id,
            "locator": locator,
            "aliases": [],
            "fingerprint": "sha256:" + "0" * 64,
            "disposition": "cool-30-days",
            "post_closeout_result": "Cooling",
            "completion_event": "merge",
            "completion_evidence_ref": "commit:" + "1" * 40,
            "completed_on": "2026-01-01",
            "timezone": "Asia/Singapore",
            "review_on": "2026-01-31",
            "authority": {n: {"status": "confirmed"} for n in ("source", "write", "delete")},
            "confirmation_proof": "sha256:" + "2" * 64,
        }
    )


def _simple(case_id: str, kind: str, target: str, path: str, files: dict[str, str], **kw: Any) -> Case:
    """A case whose edge is a plain local need on ``path``."""
    return Case(
        case_id=case_id,
        waiting_path=WAITER,
        target=target,
        needs=f"[{_local_need(kind, path)}]",
        files={**_waiter_files(), **files},
        **kw,
    )


def _receipt_fields(outcome: str) -> dict[str, str]:
    return {
        "delivery_id": "delivery-123",
        "outcome": outcome,
        "completion_event": "merge",
        "evidence_ref": "pr:123",
    }


def _coordination_brief(revision: str, *, valid: bool = True) -> str:
    body = (
        "[[coordination_receipts]]\n"
        'id = "remote-prereq"\nremote_kind = "brief"\n'
        'remote_ref = "example-service://projects/example-artifact"\n'
        f'accepted_revision = "{revision}"\n'
        'required_status = "Shipped"\nreported_status = "Shipped"\n'
        'reviewed_by = "Example Reviewer"\nreviewed_at = "2026-08-10T00:00:00Z"\n'
        "refresh_conflict = false\n"
    )
    if not valid:
        body = body.replace('required_status = "Shipped"\n', "")
    return (
        "# Brief: remote\n\n- **Status:** Shipped\n- **Slug:** remote\n\n"
        f"```toml coordination-receipts\n{body}```\n"
    )


def _build_cases() -> list[Case]:
    cases: list[Case] = []

    # Spec, brief, intent targets: terminal and not.
    for status, label in (("Shipped", "terminal"), ("Approved", "open")):
        cases.append(_simple(
            f"spec-{label}", "spec", "spec:target",
            "docs/specs/target/spec.md",
            {"docs/specs/target/spec.md": _spec_file("target", status),
             "docs/specs/target/plan.md": "# Plan\n\n- **Status:** Approved\n"},
        ))
    for status, label in (("Shipped", "terminal"), ("Draft", "open")):
        cases.append(_simple(
            f"brief-{label}", "brief", "brief:target",
            f"{BRIEF_DIR}/target.md",
            {f"{BRIEF_DIR}/target.md": f"# Brief: target\n\n- **Status:** {status}\n- **Slug:** target\n"},
        ))
    for status, label in (("Accepted", "terminal"), ("Draft", "open")):
        cases.append(_simple(
            f"intent-{label}", "intent", "intent:target",
            f"{INTENT_DIR}/target.md",
            {f"{INTENT_DIR}/target.md": f"# Intent: target\n\n- **Status:** {status}\n- **Slug:** target\n"},
        ))

    # Defect targets.
    closed = "docs/backlog/defect-closed.md"
    cases.append(_simple(
        "defect-closed-member", "defect", closed, closed,
        {closed: "# Defect\n\n- **Status:** Closed\n- **Resolution:** fixed\n- **Kind:** defect\n"},
        extras=(("backlog", "closed", _entry(closed, "defect")),),
    ))
    opened = "docs/backlog/defect-open.md"
    cases.append(_simple(
        "defect-open-member", "defect", opened, opened,
        {opened: "# Defect\n\n- **Status:** Open\n- **Kind:** defect\n"},
        extras=(("backlog", "open", _entry(opened, "defect")),),
    ))
    loose = "docs/backlog/defect-loose.md"
    cases.append(_simple(
        "defect-no-member", "defect", loose, loose,
        {loose: "# Defect\n\n- **Status:** Open\n- **Kind:** defect\n"},
    ))

    # Cooled target: a lifecycle record names it, so its body is never opened.
    cases.append(_simple(
        "spec-cooled", "spec", "spec:target", "docs/specs/target/spec.md",
        {"docs/specs/target/spec.md": _spec_file("target", "Approved"),
         "docs/specs/target/plan.md": "# Plan\n\n- **Status:** Approved\n",
         "docs/lifecycle/target.json": _record("target", "docs/specs/target/spec.md")},
        cooled=("docs/specs/target/spec.md",),
    ))

    # Brief target whose child scope is unknown: a cooled child declares no parent.
    child = "docs/specs/child/spec.md"
    brief = f"{BRIEF_DIR}/target.md"
    cases.append(_simple(
        "brief-child-scope-unknown", "brief", "brief:target", brief,
        {brief: "# Brief: target\n\n- **Status:** Shipped\n- **Slug:** target\n",
         child: _spec_file("child", "Shipped"),
         "docs/specs/child/plan.md": "# Plan\n\n- **Status:** Done\n",
         "docs/lifecycle/child.json": _record("child", child)},
        extras=(
            ("work", "shipped", _entry(child)),
            ("brief_queue", "shipped", _entry(brief, "brief")),
        ),
        cooled=(child,),
    ))

    # Missing targets without receipts.
    cases.append(_simple("spec-missing", "spec", "spec:gone", "docs/specs/gone/spec.md", {}))
    cases.append(_simple("brief-missing", "brief", "brief:gone", f"{BRIEF_DIR}/gone.md", {}))
    cases.append(_simple("intent-missing", "intent", "intent:gone", f"{INTENT_DIR}/gone.md", {}))
    cases.append(_simple("defect-missing", "defect", "docs/backlog/gone.md", "docs/backlog/gone.md", {}))

    # Missing typed targets with a completion receipt.
    missing = {
        "spec": ("spec:gone", "docs/specs/gone/spec.md"),
        "brief": ("brief:gone", f"{BRIEF_DIR}/gone.md"),
        "intent": ("intent:gone", f"{INTENT_DIR}/gone.md"),
    }
    for kind, (target, path) in missing.items():
        for outcome in ("completed", "abandoned", "invalid"):
            fields = _receipt_fields(outcome)
            cases.append(Case(
                case_id=f"{kind}-missing-receipt-{outcome}",
                waiting_path=WAITER,
                target=target,
                needs=f"[{_local_need(kind, path, fields)}]",
                files=_waiter_files(),
                receipt=("completion", fields),
            ))

    # Coordination receipts on a containing brief.
    remote = f"{BRIEF_DIR}/remote.md"
    coordination = {
        "coordination-match": (RECEIPT_BLOCK_OK, True),
        "coordination-revision-differs": ("remote-rev-8", True),
        "coordination-block-invalid": (RECEIPT_BLOCK_OK, False),
    }
    for case_id, (need_revision, valid) in coordination.items():
        cases.append(Case(
            case_id=case_id,
            waiting_path=WAITER,
            target="brief:remote",
            needs=f"[{_cross_need(remote, need_revision)}]",
            files={**_waiter_files(),
                   remote: _coordination_brief(RECEIPT_BLOCK_OK, valid=valid)},
            receipt=("coordination", {
                "remote_kind": "brief", "receipt_id": "remote-prereq",
                "accepted_revision": need_revision,
            }),
        ))

    # AC-0007: a two-spec cycle. Each spec's own preamble can carry the header.
    peer_files = {
        PEER: _spec_file("peer"),
        "docs/specs/peer/plan.md": "# Plan\n\n- **Status:** Approved\n",
    }
    cases.append(Case(
        case_id="cycle-two-specs",
        waiting_path=WAITER,
        target="spec:peer",
        needs=f"[{_local_need('spec', PEER)}]",
        files={**_waiter_files(), **peer_files},
        extras=(("work", "queue", _entry(PEER, needs=f"[{_local_need('spec', WAITER)}]")),),
        header_extras=(("work", "queue", _entry(PEER)),),
        peer_header=(PEER, "spec:waiter"),
    ))
    return cases


CASES = _build_cases()


def _header_lines(case: Case) -> str:
    """The waiting item's `Depends on:` line, and its receipt line when it has one."""
    lines = f"- **Depends on:** {case.target}\n"
    if case.receipt is not None:
        kind, fields = case.receipt
        tokens = list(fields.values())
        lines += f"- **Dependency receipts:** {case.target} {kind} {' '.join(tokens)}\n"
    return lines


def _write_repo(root: Path, case: Case, form: str = "needs") -> None:
    """Write the case's files and a workspace.toml holding its edge.

    `form` is `needs` (a typed registry entry), `header` (the same edge in the
    waiting item's header, with `needs = []`), or `bare` (no edge at all).
    """
    files = dict(case.files)
    if form == "header":
        files[case.waiting_path] += _header_lines(case)
        if case.peer_header is not None:
            peer_path, reference = case.peer_header
            files[peer_path] += f"- **Depends on:** {reference}\n"
    for rel, text in files.items():
        target = root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
    extras = case.extras
    if form != "needs" and case.header_extras is not None:
        extras = case.header_extras
    tables: dict[tuple[str, str], list[str]] = {
        ("work", "queue"): [
            _entry(case.waiting_path, needs=case.needs if form == "needs" else "[]")
        ],
    }
    for table, name, rendered in extras:
        tables.setdefault((table, name), []).append(rendered)

    def array(key: tuple[str, str]) -> str:
        items = tables.get(key, [])
        return "[" + ", ".join(items) + "]"

    lines = [
        '["ini-001"]', 'name = "Equivalence fixture"', 'status = "active"',
        'milestone = "m1"', "", '["ini-001".work]',
    ]
    lines += [f"{n} = {array(('work', n))}" for n in ("queue", "active", "shipped")]
    lines += ["", '["ini-001".shaping_queue]']
    lines += [f"{n} = {array(('shaping_queue', n))}" for n in ("active", "backlog")]
    lines += ["", '["ini-001".brief_queue]']
    lines += [
        f"{n} = {array(('brief_queue', n))}"
        for n in ("draft", "ready", "executing", "shipped", "withdrawn", "cancelled")
    ]
    lines += ["", "[backlog]", f"open = {array(('backlog', 'open'))}",
              f"closed = {array(('backlog', 'closed'))}", ""]
    (root / "workspace.toml").write_text("\n".join(lines), encoding="utf-8")


def observe(root: Path) -> dict[str, Any]:
    """Run the real seams over a repository and return the comparable outcome."""
    workspace = ENGINE.parse_workspace(root / "workspace.toml")
    cooled, _ = ENGINE._resolve_cooled_state(root)
    canonical = ENGINE.run_canonical_reconciliation(workspace, root, cooled)
    status = ENGINE.analyze(root)
    ready = sorted(c.entry.path for c in status.classifications if c.is_ready)
    blocked = sorted(
        (c.entry.path, list(c.blocking_needs))
        for c in status.classifications if not c.is_ready
    )
    return {
        "findings": sorted([f.code, f.path] for f in canonical.findings),
        "dispatchable": {
            path: ev.dispatchable for path, ev in sorted(canonical.dispatch_by_path.items())
        },
        "legacy": {"ready": ready, "blocked": [[p, n] for p, n in blocked]},
    }


def observe_case(tmp_path: Path, case: Case, form: str = "needs") -> dict[str, Any]:
    """Build the case's repository under ``tmp_path`` and observe it."""
    _write_repo(tmp_path, case, form)
    return observe(tmp_path)


# What each case must mean, independent of the recorded file: the waiter's
# dispatchability. A recorded outcome that contradicts its name is a bad fixture.
_WAITER_DISPATCHABLE = {
    "spec-terminal": True, "spec-open": False,
    "brief-terminal": True, "brief-open": False,
    "intent-terminal": True, "intent-open": False,
    "defect-closed-member": True, "defect-open-member": False,
    "defect-no-member": False, "spec-cooled": True,
    "brief-child-scope-unknown": False,
    "spec-missing": False, "brief-missing": False,
    "intent-missing": False, "defect-missing": False,
    "spec-missing-receipt-completed": True, "spec-missing-receipt-abandoned": False,
    "spec-missing-receipt-invalid": False,
    "brief-missing-receipt-completed": True, "brief-missing-receipt-abandoned": False,
    "brief-missing-receipt-invalid": False,
    "intent-missing-receipt-completed": True, "intent-missing-receipt-abandoned": False,
    "intent-missing-receipt-invalid": False,
    "coordination-match": True, "coordination-revision-differs": False,
    "coordination-block-invalid": False, "cycle-two-specs": False,
}


def test_every_case_has_a_named_meaning() -> None:
    """The case list and the meaning table stay in step, ids stay unique."""
    ids = [case.case_id for case in CASES]
    assert len(ids) == len(set(ids))
    assert set(ids) == set(_WAITER_DISPATCHABLE)


def _expected() -> dict[str, Any]:
    return json.loads(_EXPECTED_PATH.read_text(encoding="utf-8"))


def _at_the_reference(case: Case, record: dict[str, Any]) -> dict[str, Any]:
    """The frozen outcome, with a missing brief or intent target placed at its reference.

    A typed reference with no target is a missing target at `docs/specs/<slug>/spec.md`
    for a spec, and at the reference itself otherwise. Every other path is kept.
    """
    if not case.target.startswith(("brief:", "intent:")) or "missing" not in case.case_id:
        return record
    directory = BRIEF_DIR if case.target.startswith("brief:") else INTENT_DIR
    needs_path = f"{directory}/{case.target.split(':', 1)[1]}.md"
    return {
        **record,
        "findings": sorted(
            [code, case.target if path == needs_path else path]
            for code, path in record["findings"]
        ),
    }


@pytest.mark.parametrize("case", CASES, ids=[case.case_id for case in CASES])
def test_header_form_reproduces_the_frozen_needs_outcome(
    tmp_path: Path, case: Case
) -> None:
    """AC-0003, AC-0007: a header edge gives the finding codes, dispatchability and
    legacy lists the same edge gave as a typed `needs` entry."""
    observed = observe_case(tmp_path, case, "header")
    assert observed == _at_the_reference(case, _expected()[case.case_id])


@pytest.mark.parametrize("case", CASES, ids=[case.case_id for case in CASES])
def test_needs_form_is_refused_and_decides_nothing(tmp_path: Path, case: Case) -> None:
    """AC-0005: an entry still carrying `needs` is refused whatever the edge says.

    The outcome is the no-edge outcome plus `unmigrated_needs` for each entry that
    carries `needs`: the edge contributes no finding, no block, and no legacy need.
    """
    refused = observe_case(tmp_path / "needs", case, "needs")
    bare = observe_case(tmp_path / "bare", case, "bare")
    carriers = [case.waiting_path]
    if case.case_id == "cycle-two-specs":
        carriers.append(PEER)
    assert refused["findings"] == sorted(
        [*bare["findings"], *(["unmigrated_needs", path] for path in carriers)]
    )
    assert refused["dispatchable"][WAITER] is False
    assert refused["legacy"] == bare["legacy"]


def test_unmigrated_needs_names_the_repair_and_blocks_a_satisfied_edge(
    tmp_path: Path,
) -> None:
    """AC-0005: a satisfied `needs` edge with an empty header is still refused."""
    case = next(c for c in CASES if c.case_id == "spec-terminal")
    assert _expected()["spec-terminal"]["dispatchable"][WAITER] is True
    _write_repo(tmp_path, case, "needs")
    workspace = ENGINE.parse_workspace(tmp_path / "workspace.toml")
    result = ENGINE.run_canonical_reconciliation(workspace, tmp_path)
    refusals = [f for f in result.findings if f.code == "unmigrated_needs"]
    assert [f.path for f in refusals] == [WAITER]
    assert "workspace-status repair-plan" in refusals[0].next_action
    assert result.dispatch_by_path[WAITER].dispatchable is False


# ── The cooled brief target (amendment 1) ─────────────────────────────────────

_BRIEF_TARGET = f"{BRIEF_DIR}/target.md"


def _cooled_brief_cases() -> list[Case]:
    """A cooled brief target with `Slug:` equal to its stem, and one with no `Slug:`."""
    cases = []
    for case_id, slug_line in (
        ("brief-cooled-slug-is-stem", "- **Slug:** target\n"),
        ("brief-cooled-no-slug", ""),
    ):
        cases.append(_simple(
            case_id, "brief", "brief:target", _BRIEF_TARGET,
            {_BRIEF_TARGET: f"# Brief: target\n\n- **Status:** Draft\n{slug_line}",
             "docs/lifecycle/target.json": _record("target", _BRIEF_TARGET)},
            cooled=(_BRIEF_TARGET,),
        ))
    return cases


COOLED_BRIEF_CASES = _cooled_brief_cases()


def test_cooled_brief_needs_form_is_recorded_from_the_old_engine(tmp_path: Path) -> None:
    """The recorder: run against the engine at commit 1f9c27342 to write the file."""
    if not _RECORD_COOLED_BRIEF:
        pytest.skip("set DEPENDS_ON_HEADERS_RECORD_COOLED_BRIEF=1 to record")
    observed = {
        case.case_id: observe_case(tmp_path / case.case_id, case, "needs")
        for case in COOLED_BRIEF_CASES
    }
    _COOLED_BRIEF_PATH.write_text(
        json.dumps(observed, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    pytest.skip("recorded expected-cooled-brief.json from the engine in use")


@pytest.mark.parametrize(
    "case", COOLED_BRIEF_CASES, ids=[case.case_id for case in COOLED_BRIEF_CASES]
)
def test_cooled_brief_header_form_reproduces_the_recorded_outcome(
    tmp_path: Path, case: Case
) -> None:
    """AC-0003: a cooled brief admitted by its stem gives the `needs` outcome."""
    recorded = json.loads(_COOLED_BRIEF_PATH.read_text(encoding="utf-8"))
    assert observe_case(tmp_path, case, "header") == recorded[case.case_id]


# ── AC-0008: the legacy view, explain, the MCP tools, and shaping ─────────────

def _cli(root: Path, *args: str) -> dict[str, Any]:
    done = subprocess.run(
        [sys.executable, str(_STATUS_PATH), *args, "--root", str(root)],
        check=False, capture_output=True, text=True,
    )
    assert done.returncode == 0, done.stderr
    return json.loads(done.stdout)


def test_explain_reports_a_header_edge_as_it_reported_the_needs_edge(
    tmp_path: Path,
) -> None:
    """AC-0008: `explain` blocks on the header edge with the frozen finding codes."""
    case = next(c for c in CASES if c.case_id == "spec-open")
    _write_repo(tmp_path, case, "header")
    item = _cli(tmp_path, "explain", "--item", "waiter")["explained_item"]
    frozen_codes = [
        code for code, path in _expected()["spec-open"]["findings"]
    ]
    assert item["classification"] == "blocked"
    assert item["blocking_needs"] == frozen_codes == ["unsatisfied_dependency"]
    # The bounded analysis the MCP tools read carries the same edge as the string
    # a typed need showed.
    legacy = ENGINE.analyze_bounded(tmp_path, autonomous_dispatch=True).blocked
    assert [(c.entry.path, c.blocking_needs) for c in legacy] == [
        (WAITER, ["unsupported-typed-need"])
    ]


def test_a_shaping_backlog_intent_edge_is_read_from_its_header(tmp_path: Path) -> None:
    """AC-0008: a canonical intent in `shaping_queue.backlog` waits on its header.

    The legacy shaping lists never held a canonical entry, so both forms leave
    them empty; the edge is seen by the canonical reconciliation alone.
    """
    intent = f"{INTENT_DIR}/shaper.md"
    entry = _entry(intent, "intent")
    files = {
        **_waiter_files(),
        PEER: _spec_file("peer", "Approved"),
        "docs/specs/peer/plan.md": "# Plan\n\n- **Status:** Approved\n",
    }
    outcomes = {}
    for form in ("needs", "header"):
        root = tmp_path / form
        waiting = "# Intent: shaper\n\n- **Status:** Draft\n- **Slug:** shaper\n"
        if form == "header":
            waiting += "- **Depends on:** spec:peer\n"
            entry = _entry(intent, "intent")
        else:
            entry = _entry(intent, "intent", needs=f"[{_local_need('spec', PEER)}]")
        case = Case(
            case_id="shaping", waiting_path=WAITER, target="spec:peer",
            needs="[]", files={**files, intent: waiting},
            extras=(("shaping_queue", "backlog", entry),),
        )
        _write_repo(root, case, "bare")
        status = ENGINE.analyze(root)
        outcomes[form] = observe(root)
        assert status.shaping_classifications == []
    # What the engine at commit 1f9c27342 reported for the `needs` form of this
    # case: the waiting intent not dispatchable, and its open target named.
    assert outcomes["header"]["findings"] == [["unsatisfied_dependency", PEER]]
    assert outcomes["header"]["dispatchable"][intent] is False
    assert outcomes["needs"]["findings"] == [["unmigrated_needs", intent]]
    assert outcomes["needs"]["dispatchable"][intent] is False


# ── The routing identity ──────────────────────────────────────────────────────

def _identity(root: Path) -> str:
    workspace = ENGINE.parse_workspace(root / "workspace.toml")
    cooled, _ = ENGINE._resolve_cooled_state(root)
    canonical = ENGINE.run_canonical_reconciliation(workspace, root, cooled)
    return ENGINE.canonical_repository_identity(workspace, canonical, root)


def _edit(root: Path, rel: str, old: str, new: str) -> None:
    path = root / rel
    text = path.read_text(encoding="utf-8")
    assert old in text, (rel, old)
    path.write_text(text.replace(old, new), encoding="utf-8")


@pytest.mark.parametrize(
    ("case_id", "rel", "old", "new"),
    [
        ("spec-open", WAITER, "spec:target", "spec:other"),
        (
            "spec-missing-receipt-completed", WAITER,
            "delivery-123 completed", "delivery-124 completed",
        ),
        ("brief-open", f"{BRIEF_DIR}/target.md", "Slug:** target", "Slug:** renamed"),
    ],
    ids=["header-item", "receipt", "target-slug"],
)
def test_editing_a_header_edge_changes_the_routing_identity(
    tmp_path: Path, case_id: str, rel: str, old: str, new: str
) -> None:
    """The header edges, not the registry's `needs`, are fingerprinted."""
    case = next(c for c in CASES if c.case_id == case_id)
    _write_repo(tmp_path, case, "header")
    before = _identity(tmp_path)
    assert _identity(tmp_path) == before, "the identity is not stable"
    _edit(tmp_path, rel, old, new)
    assert _identity(tmp_path) != before


# ── A cooled waiting item is never opened (AC-0006) ───────────────────────────

def test_a_cooled_waiting_item_is_never_opened(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-0006: an unreadable cooled waiting file gives no finding, and no read.

    The uncooled control with the same unreadable file does give
    `unreadable_artifact`, so the absence is the cooling and not a quiet fixture.
    """
    case = next(c for c in CASES if c.case_id == "spec-open")
    seen: list[str] = []
    real = ENGINE.read_header_dependencies

    def probe(root: Path, waiting_path: str, **kwargs: Any) -> Any:
        seen.append(waiting_path)
        return real(root, waiting_path, **kwargs)

    monkeypatch.setattr(ENGINE, "read_header_dependencies", probe)
    outcomes = {}
    for label, cooled in (("control", False), ("cooled", True)):
        root = tmp_path / label
        _write_repo(root, case, "header")
        if cooled:
            (root / "docs/lifecycle").mkdir(parents=True)
            (root / "docs/lifecycle/waiter.json").write_text(
                _record("waiter", WAITER), encoding="utf-8"
            )
        (root / WAITER).chmod(0)
        seen.clear()
        try:
            workspace = ENGINE.parse_workspace(root / "workspace.toml")
            cooled_set, _ = ENGINE._resolve_cooled_state(root)
            result = ENGINE.run_canonical_reconciliation(workspace, root, cooled_set)
            outcomes[label] = (
                {f.code for f in result.findings if f.path == WAITER},
                WAITER in seen,
                bool(cooled_set),
            )
        finally:
            (root / WAITER).chmod(0o644)
    if os.geteuid() == 0:
        pytest.skip("a superuser reads a mode 0 file")
    assert "unreadable_artifact" in outcomes["control"][0]
    assert outcomes["control"][1] is True
    assert outcomes["cooled"][2] is True, "the record did not cool the waiting item"
    assert "unreadable_artifact" not in outcomes["cooled"][0]
    assert outcomes["cooled"][1] is False


def test_frozen_outcomes_match_case_names() -> None:
    """Every recorded waiter outcome is the one its case id says."""
    expected = json.loads(_EXPECTED_PATH.read_text(encoding="utf-8"))
    for case in CASES:
        record = expected[case.case_id]
        assert record["dispatchable"][WAITER] is _WAITER_DISPATCHABLE[case.case_id], case.case_id
