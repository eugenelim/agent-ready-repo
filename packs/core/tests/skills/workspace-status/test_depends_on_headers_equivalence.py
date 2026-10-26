"""Frozen `needs`-form outcomes for the `Depends on:` header equivalence suite.

Spec: docs/specs/depends-on-headers/spec.md (AC-0003, AC-0007, AC-0008).
Verification mode: TDD, paired fixtures.

Each case is one repository whose waiting item has a single dependency edge,
written as a typed ``needs`` entry in ``workspace.toml``. The outcome of the
unchanged engine (commit ``1f9c27342``) is frozen in
``fixtures/depends-on-headers/expected.json``. A later task writes the same
edge as a header, from the ``Case`` fields below, and must reproduce it.

To re-record, run with ``DEPENDS_ON_HEADERS_RECORD=1`` set; the recorder must
only run against an engine whose ``needs`` reading is unchanged.
"""
from __future__ import annotations

import dataclasses
import importlib.util
import json
import os
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

_PACK_ROOT = Path(__file__).resolve().parents[3]
_ENGINE_PATH = (
    _PACK_ROOT / ".apm/skills/workspace-status/scripts/workspace_status_engine.py"
)
_EXPECTED_PATH = Path(__file__).parent / "fixtures/depends-on-headers/expected.json"
_RECORD = os.environ.get("DEPENDS_ON_HEADERS_RECORD") == "1"
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
    ))
    return cases


CASES = _build_cases()


def _write_repo(root: Path, case: Case) -> None:
    """Write the case's files and a workspace.toml holding its edge."""
    for rel, text in case.files.items():
        target = root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
    tables: dict[tuple[str, str], list[str]] = {
        ("work", "queue"): [_entry(case.waiting_path, needs=case.needs)],
    }
    for table, name, rendered in case.extras:
        tables.setdefault((table, name), []).append(rendered)

    def array(key: tuple[str, str]) -> str:
        items = tables.get(key, [])
        return "[" + ", ".join(items) + "]"

    lines = [
        '["ini-001"]', 'name = "Equivalence fixture"', 'status = "active"',
        'milestone = "m1"', "", '["ini-001".work]',
    ]
    lines += [f"{n} = {array(('work', n))}" for n in ("queue", "active", "shipped")]
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


def observe_case(tmp_path: Path, case: Case) -> dict[str, Any]:
    """Build the case's repository under ``tmp_path`` and observe it."""
    _write_repo(tmp_path, case)
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


def test_needs_form_reproduces_frozen_expectations(tmp_path: Path) -> None:
    """Each `needs`-form case reproduces expected.json; the recorder rewrites it."""
    observed = {
        case.case_id: observe_case(tmp_path / case.case_id, case) for case in CASES
    }
    if _RECORD:
        _EXPECTED_PATH.parent.mkdir(parents=True, exist_ok=True)
        _EXPECTED_PATH.write_text(
            json.dumps(observed, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        pytest.skip("recorded expected.json from the current engine")
    expected = json.loads(_EXPECTED_PATH.read_text(encoding="utf-8"))
    assert observed == expected


def test_frozen_outcomes_match_case_names() -> None:
    """Every recorded waiter outcome is the one its case id says."""
    expected = json.loads(_EXPECTED_PATH.read_text(encoding="utf-8"))
    for case in CASES:
        record = expected[case.case_id]
        assert record["dispatchable"][WAITER] is _WAITER_DISPATCHABLE[case.case_id], case.case_id
