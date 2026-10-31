#!/usr/bin/env python3
"""Roster for pre-cutover-closure.

Spec: docs/specs/pre-cutover-closure/spec.md

AC-0005: the Status line of docs/specs/closure-eligibility-check/spec.md still
begins ``Shipped``, keeps its earlier supersession note, and records the
supersession by pre-cutover-closure (criterion 0031, the packet's registry
field).
AC-0006: close-work's eval file holds one case whose assertions require that the
closure packet names no ``workspace.toml`` entry.

AC-0012: the upgrade-notes draft's frontmatter validates against
contracts/guide.schema.json (pack core, kind how-to) and its H1 equals the title.
AC-0013: the draft names workspace-status, repair-plan, then repair-apply --yes.
AC-0014: the draft names each removed behavior in backticks.
AC-0015: the draft links the RFC errata and the retirement record, both tracked,
and states the dates 2026-10-25 and 2026-10-30.
AC-0016 (partial): the verification ledger's Approvals table binds the draft's
current SHA-256 and holds the retirement spec and plan hashes.

Needs PyYAML and jsonschema besides the standard library and pytest; the checks
read files and write nothing.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path

import jsonschema
import yaml

_REPO = Path(__file__).resolve().parents[2]
_SPEC = "docs/specs/closure-eligibility-check/spec.md"
_EVALS = "packs/core/.apm/skills/close-work/evals/evals.json"
_CASE_ID = "eligible-packet-names-no-registry-entry"


def _status_line() -> str:
    """Return the ``- **Status:**`` line of the closure-eligibility-check spec."""
    for line in (_REPO / _SPEC).read_text(encoding="utf-8").splitlines():
        if line.startswith("- **Status:**"):
            return line
    raise AssertionError(f"no Status line in {_SPEC}")


def test_ac0005_status_records_supersession() -> None:
    """The Status line stays Shipped and names pre-cutover-closure's criterion 0031."""
    status = _status_line()
    assert status.removeprefix("- **Status:**").strip().startswith("Shipped")
    assert "close-work-intent-graph-convergence" in status
    assert "(../pre-cutover-closure/spec.md)" in status
    assert "0031" in status


def test_ac0006_eval_case_requires_no_registry_entry() -> None:
    """Exactly one eval case asserts the packet names no `workspace.toml` entry."""
    cases = json.loads((_REPO / _EVALS).read_text(encoding="utf-8"))["evals"]
    matching = [c for c in cases if c["id"] == _CASE_ID]
    assert len(matching) == 1
    hits = [
        a
        for a in matching[0]["assertions"]
        if "`workspace.toml`" in a and "names no" in a
    ]
    assert len(hits) == 1


_DRAFT = "docs/specs/pre-cutover-closure/notes/upgrade-notes.md"
_LEDGER = "docs/specs/pre-cutover-closure/notes/verification-ledger.md"
_GUIDE_SCHEMA = "contracts/guide.schema.json"


def _draft_text() -> str:
    """Return the draft's full text."""
    return (_REPO / _DRAFT).read_text(encoding="utf-8")


def _split_draft() -> tuple[dict[str, object], str]:
    """Return the draft's parsed frontmatter and its body."""
    lines = _draft_text().splitlines()
    assert lines[0] == "---"
    end = lines.index("---", 1)
    meta = yaml.safe_load("\n".join(lines[1:end]))
    return meta, "\n".join(lines[end + 1 :])


def _approvals() -> dict[str, str]:
    """Return {file: sha} for the ledger's eugenelim rows in ``## Approvals``."""
    text = (_REPO / _LEDGER).read_text(encoding="utf-8")
    section = text.split("\n## Approvals", 1)[1].split("\n## ", 1)[0]
    rows: dict[str, str] = {}
    for line in section.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) == 5 and cells[1] == "eugenelim":
            rows[cells[3].strip("`")] = cells[4].strip("`")
    return rows


def test_ac0012_frontmatter_validates_and_h1_matches_title() -> None:
    """The draft's frontmatter fits the guide schema and its H1 repeats the title."""
    meta, body = _split_draft()
    schema = json.loads((_REPO / _GUIDE_SCHEMA).read_text(encoding="utf-8"))
    jsonschema.validate(meta, schema)
    assert meta["pack"] == "core"
    assert meta["kind"] == "how-to"
    h1 = next(line for line in body.splitlines() if line.startswith("# "))
    assert h1 == "# " + str(meta["title"])


def test_ac0013_names_plan_before_apply_in_a_session() -> None:
    """The draft names the three commands in order and mentions a session."""
    text = _draft_text()
    assert "workspace-status" in text
    assert "repair-plan" in text
    assert "repair-apply --yes" in text
    assert text.index("repair-plan") < text.index("repair-apply --yes")
    assert "session" in text


def test_ac0014_each_removed_behavior_is_named_in_backticks() -> None:
    """Every removed behavior appears in its backticked form."""
    text = _draft_text()
    for name in (
        "<initiative>",
        "<initiative>.name",
        "<initiative>.status",
        "<initiative>.milestone",
        "<initiative>.parent",
        "entry position",
        "behavior outside tracked files",
        "origin_mode",
        "profile",
        "refresh",
    ):
        assert f"`{name}`" in text, name


def test_ac0015_links_resolve_to_tracked_files_and_dates_are_stated() -> None:
    """The two required links resolve to git-tracked files; both dates appear."""
    text = _draft_text()
    targets = re.findall(r"\]\(([^)]+)\)", text)
    required = (
        "../../../rfc/0106-stop-registering-derivable-work.md#errata",
        "../../workspace-retirement/retirement-record.md#disposition",
    )
    tracked = set(
        subprocess.run(
            ["git", "ls-files"], cwd=_REPO, capture_output=True, text=True, check=True
        ).stdout.splitlines()
    )
    base = (_REPO / _DRAFT).parent
    for target in required:
        assert target in targets, target
        resolved = (base / target.split("#", 1)[0]).resolve()
        assert resolved.is_file(), target
        assert resolved.relative_to(_REPO.resolve()).as_posix() in tracked, target
    assert "2026-10-25" in text
    assert "2026-10-30" in text


def test_ac0016_ledger_binds_the_draft_hash_and_the_retirement_amendment() -> None:
    """The ledger holds the draft's current SHA-256 and the spec and plan hashes."""
    rows = _approvals()
    digest = hashlib.sha256((_REPO / _DRAFT).read_bytes()).hexdigest()
    assert rows.get(_DRAFT) == digest
    for name in ("spec.md", "plan.md"):
        sha = rows.get(f"docs/specs/workspace-retirement/{name}", "")
        assert re.fullmatch(r"[0-9a-f]{64}", sha), name
