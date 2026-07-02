"""Tests for ledger.py (RFC-0059 D7 / ADR-0048): deterministic run-id,
append-only + schema (no free-text), resume, durable purge-exempt marker."""

from __future__ import annotations

from pathlib import Path

import pytest

import ledger as L

SALT = "fixed-test-salt"


def _entry(name: str, verdict: str = "assimilate", status: str = "done") -> dict:
    return {"path": f"src/{name}", "name": name, "content_hash": f"h-{name}",
            "verdict": verdict, "status": status, "destination": "core"}


def test_run_id_deterministic_no_stamp(tmp_path: Path) -> None:
    a = L.run_id("https://x/repo", base=tmp_path, salt=SALT)
    b = L.run_id("https://x/repo", base=tmp_path, salt=SALT)
    assert a == b  # no per-invocation stamp — resume/worktree-share depends on this
    assert a != L.run_id("https://x/other", base=tmp_path, salt=SALT)


def test_append_read_roundtrip_and_resume(tmp_path: Path) -> None:
    src = "https://x/repo"
    L.append_entry(src, _entry("alpha"), base=tmp_path, salt=SALT)
    L.append_entry(src, _entry("beta", status="pending"), base=tmp_path, salt=SALT)
    entries = L.read_entries(src, base=tmp_path, salt=SALT)
    assert [e["name"] for e in entries] == ["alpha", "beta"]
    assert L.done_names(src, base=tmp_path, salt=SALT) == {"alpha"}  # resume skips 'alpha'


def test_schema_rejects_free_text_and_bad_values(tmp_path: Path) -> None:
    bad_freetext = _entry("x")
    bad_freetext["reason"] = "verbatim source content leaks here"
    with pytest.raises(L.LedgerSchemaError):
        L.validate_entry(bad_freetext)
    with pytest.raises(L.LedgerSchemaError):
        L.validate_entry({**_entry("y"), "verdict": "maybe"})
    with pytest.raises(L.LedgerSchemaError):
        L.validate_entry({**_entry("z"), "status": "??"})
    with pytest.raises(L.LedgerSchemaError):
        L.validate_entry({"name": "n"})  # missing required keys


def test_schema_rejects_control_chars_no_toml_injection(tmp_path: Path) -> None:
    # A newline in a field would corrupt the append-only TOML and brick reads.
    evil = {**_entry("x"), "name": 'beta"\ndestination = "forged"'}
    with pytest.raises(L.LedgerSchemaError):
        L.validate_entry(evil)
    # and append_entry (which validates) must refuse it, keeping the ledger readable
    with pytest.raises(L.LedgerSchemaError):
        L.append_entry("https://x/repo", evil, base=tmp_path, salt=SALT)
    # a benign entry after the refusal still round-trips
    L.append_entry("https://x/repo", _entry("gamma"), base=tmp_path, salt=SALT)
    assert [e["name"] for e in L.read_entries("https://x/repo", base=tmp_path, salt=SALT)] == ["gamma"]


def test_durable_marker_dated_append_and_baseline(tmp_path: Path) -> None:
    src = "https://x/repo"
    L.record_sync(src, ["h1", "h2"], base=tmp_path, salt=SALT, today="2026-07-01")
    L.record_sync(src, ["h1", "h3"], base=tmp_path, salt=SALT, today="2026-07-02")
    assert L.baseline(src, base=tmp_path, salt=SALT) == {"h1", "h3"}  # latest wins


def test_classify(tmp_path: Path) -> None:
    base_set = {"h-alpha"}
    known = {"beta"}
    assert L.classify("h-alpha", base_set, known, "alpha") == "unchanged"
    assert L.classify("h-beta2", base_set, known, "beta") == "changed"
    assert L.classify("h-new", base_set, known, "gamma") == "new"


def test_purge_leaves_marker(tmp_path: Path) -> None:
    src = "https://x/repo"
    L.append_entry(src, _entry("alpha"), base=tmp_path, salt=SALT)
    L.record_sync(src, ["h1"], base=tmp_path, salt=SALT, today="2026-07-01")
    L.purge_run(src, base=tmp_path, salt=SALT)
    assert L.read_entries(src, base=tmp_path, salt=SALT) == []      # run ledger gone
    assert L.baseline(src, base=tmp_path, salt=SALT) == {"h1"}      # marker survives
