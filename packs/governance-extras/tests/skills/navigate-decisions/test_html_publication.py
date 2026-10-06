"""Tests for the navigate-decisions HTML publication surface (T3).

Verification modes: TDD (destination safety, inert content, CSP, parity) and
goal-based (bounded mode, source-link encoding).

Spec: docs/specs/decision-navigation/spec.md
Plan task: T3 — Offline publication is safe, reviewable, and evidence-sized
ACs covered: AC-0008, AC-0009, AC-0010, AC-0011, AC-0012, AC-0013, AC-0014,
             AC-0021, AC-0022

Boundary: pack tests may not read outside their pack tree except via run_query
against the fixtures/mixed corpus; all destinations are under tmp_path.
"""

from __future__ import annotations

import base64
import hashlib
import importlib.util
import json
import os
import pathlib
import re
import stat
import sys

import pytest

sys.dont_write_bytecode = True
HERE = pathlib.Path(__file__).resolve().parent
SCRIPTS = HERE.parents[2] / ".apm/skills/navigate-decisions/scripts"
FIXTURE = HERE / "fixtures/mixed"

# ── Module loaders ─────────────────────────────────────────────────────────────


def _load_module(name: str, path: pathlib.Path) -> object:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader, f"cannot load {path}"
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


NAV = _load_module(
    "governance_extras_navigate_decisions_pub",
    SCRIPTS / "navigate_decisions.py",
)
EXPLORER = _load_module(
    "governance_extras_explorer_pub",
    SCRIPTS / "explorer.py",
)


# ── Helpers ────────────────────────────────────────────────────────────────────


def _publish(
    tmp_path: pathlib.Path,
    *,
    fixture: pathlib.Path = FIXTURE,
    mode: str = "full",
    confirm_over_budget: bool = False,
    assertions: list | None = None,
) -> dict:
    """Call publish_explorer with a tmp_path destination and return the result."""
    return EXPLORER.publish_explorer(
        fixture,
        destination=tmp_path,
        mode=mode,
        confirm_over_budget=confirm_over_budget,
        assertions=assertions,
    )


def _html(tmp_path: pathlib.Path, **kwargs) -> str:
    r = _publish(tmp_path, **kwargs)
    assert r["status"] == "ok", r.get("error")
    return pathlib.Path(r["path"]).read_text(encoding="utf-8")


def _extract_json_data(html: str) -> dict:
    m = re.search(
        r'<script type="application/json" id="nav-data">\s*(.*?)\s*</script>',
        html,
        re.DOTALL,
    )
    assert m, "nav-data script block not found"
    raw = m.group(1)
    # The embedded JSON has \u003c etc.; JSON.parse accepts those.
    return json.loads(raw)


def _extract_runtime_js(html: str) -> str:
    # The JS runtime is in the last <script> block (no type attribute). Keep
    # every byte between the tags: the browser hashes exactly that text.
    matches = re.findall(
        r"<script(?! type)(?![^>]*type)[^>]*>(.*?)</script>",
        html,
        re.DOTALL,
    )
    assert matches, "No executable <script> block found"
    return matches[-1]


# ── AC-0008: Cross-mode fact parity ───────────────────────────────────────────


def test_fact_parity_record_ids(tmp_path: pathlib.Path) -> None:
    """Embedded JSON record IDs match run_query summary membership."""
    query_result = NAV.run_query(
        FIXTURE, {"operation": "search", "selectors": [{"kind": "ADR"}, {"kind": "RFC"}]}
    )
    assert query_result["status"] == "ok"
    query_ids = {r["id"] for r in query_result["records"]}

    html = _html(tmp_path)
    data = _extract_json_data(html)
    html_ids = {r["id"] for r in data["records"]}
    assert html_ids == query_ids, f"ID mismatch: {html_ids ^ query_ids}"


def test_fact_parity_lifecycle_values(tmp_path: pathlib.Path) -> None:
    """Embedded lifecycle values match run_query record results."""
    html = _html(tmp_path)
    data = _extract_json_data(html)
    for rec in data["records"]:
        q = NAV.run_query(FIXTURE, {"operation": "record", "id": rec["id"]})
        assert q["status"] == "ok"
        q_lc = q["records"][0]["lifecycle"]
        h_lc = rec["lifecycle"]
        assert h_lc.get("raw_value") == q_lc.get("raw_value"), (
            f"lifecycle raw_value mismatch for {rec['id']}: "
            f"HTML={h_lc.get('raw_value')!r} query={q_lc.get('raw_value')!r}"
        )


def test_fact_parity_relationship_tuples(tmp_path: pathlib.Path) -> None:
    """HTML data island relationships match the complete query output for all records.

    Aggregates relationships from all records via search/summary and compares
    the complete sorted tuple set (all trust classes, both directions) against
    the data island. No trust-class filter; both from-to and to-from directions
    are included.

    Mutation: dropping any relationship or field from the data island would fail.
    """
    html = _html(tmp_path, mode="bounded")
    data = _extract_json_data(html)
    # Collect all relationships from the HTML data island (excluding navigation_only
    # which come from caller assertions and are not in the query corpus).
    html_rels_key = frozenset(
        (
            r.get("from"),
            r.get("to"),
            r.get("relation"),
            tuple(r.get("scope", [])),
            r.get("raw_value"),
            r.get("basis"),
            r.get("trust_class"),
            r.get("resolution_state"),
            r.get("source"),
        )
        for r in data["relationships"]
        if r.get("trust_class") != "navigation_only"
    )

    # Aggregate all relationships from the query by querying every record.
    search_result = NAV.run_query(
        FIXTURE, {"operation": "search", "selectors": [{"kind": "ADR"}, {"kind": "RFC"}]}
    )
    assert search_result["status"] == "ok", f"search failed: {search_result}"
    all_ids = [r["id"] for r in search_result["records"]]

    query_rels_key: set = set()
    for rec_id in all_ids:
        rec_result = NAV.run_query(FIXTURE, {"operation": "record", "id": rec_id})
        assert rec_result["status"] == "ok", (rec_id, rec_result)
        for r in rec_result["relationships"]:
            query_rels_key.add((
                r.get("from"),
                r.get("to"),
                r.get("relation"),
                tuple(r.get("scope", [])),
                r.get("raw_value"),
                r.get("basis"),
                r.get("trust_class"),
                r.get("resolution_state"),
                r.get("source"),
            ))

    # The sets are equal: nothing missing from the HTML, nothing extra in it.
    assert query_rels_key, "the fixture must produce relationships"
    assert html_rels_key == query_rels_key, (
        f"missing from HTML: {sorted(query_rels_key - html_rels_key, key=str)[:3]}; "
        f"extra in HTML: {sorted(html_rels_key - query_rels_key, key=str)[:3]}"
    )


# ── AC-0010: Inert and visually honest content ────────────────────────────────


def test_hostile_script_tag_escaped(tmp_path: pathlib.Path) -> None:
    """'</script>' in record title/body must not appear unescaped in HTML output."""
    # The mixed fixture's ADR-0001 title has no script tag, but we use the
    # fixture's own content and verify the escaping invariant via the
    # safe_json function directly.
    hostile_input = "</script><script>alert(1)</script>"
    safe = EXPLORER._safe_json({"t": hostile_input})
    # Must not contain a literal closing script tag.
    assert "</script>" not in safe
    assert "\\u003c/script\\u003e" in safe or r"\u003c" in safe

    # Also: publish with the mixed fixture and verify the HTML contains no
    # unescaped breakout sequence in the data block.
    html = _html(tmp_path)
    # The data island must not contain an unescaped closing script tag.
    data_m = re.search(
        r'<script type="application/json" id="nav-data">(.*?)</script>',
        html,
        re.DOTALL,
    )
    assert data_m, "nav-data block not found"
    data_block = data_m.group(1)
    # No unescaped </script> may appear inside the data island.
    assert "</script>" not in data_block.lower()


def test_hostile_angle_brackets_escaped_in_data(tmp_path: pathlib.Path) -> None:
    """< and > are escaped in the embedded JSON."""
    safe = EXPLORER._safe_json({"x": "<b>test</b>"})
    assert "<b>" not in safe
    assert r"\u003c" in safe and r"\u003e" in safe


def test_bidi_controls_not_in_csp_or_boundary(tmp_path: pathlib.Path) -> None:
    """Bidi/non-printing controls must not appear unescaped in the HTML boundary notice."""
    html = _html(tmp_path)
    # The boundary notice text should not contain raw bidi overrides.
    bidi_chars = "\u202e\u200b\u200c\u200d"
    for ch in bidi_chars:
        assert ch not in html, f"Raw bidi/invisible char U+{ord(ch):04X} found in HTML"


# ── CSP: first head child and runtime hash ────────────────────────────────────


def test_csp_is_first_head_child(tmp_path: pathlib.Path) -> None:
    """The CSP <meta> must be the first meaningful child of <head>."""
    html = _html(tmp_path)
    head_m = re.search(r"<head>(.*?)</head>", html, re.DOTALL)
    assert head_m, "<head> block not found"
    head_content = head_m.group(1).lstrip()
    # First non-whitespace content in head must be the CSP meta tag.
    assert head_content.startswith('<meta http-equiv="Content-Security-Policy"'), (
        f"CSP meta is not first head child; head starts with: {head_content[:80]!r}"
    )


def test_csp_default_src_none(tmp_path: pathlib.Path) -> None:
    """CSP must include default-src 'none'."""
    html = _html(tmp_path)
    m = re.search(r'content="([^"]*)"', html)
    assert m, "CSP content attribute not found"
    assert "default-src 'none'" in m.group(1)


def test_csp_script_src_hash_matches_runtime(tmp_path: pathlib.Path) -> None:
    """The sha256 hash in CSP script-src must match the actual runtime JS."""
    html = _html(tmp_path)
    # Extract CSP hash.
    csp_m = re.search(r"script-src 'sha256-([^']+)'", html)
    assert csp_m, "sha256 hash not found in CSP"
    claimed_hash = csp_m.group(1)

    # Extract runtime JS.
    js = _extract_runtime_js(html)
    computed = base64.b64encode(hashlib.sha256(js.encode("utf-8")).digest()).decode("ascii")
    assert computed == claimed_hash, (
        f"CSP hash mismatch.\n  claimed: {claimed_hash}\n  computed: {computed}"
    )


def test_style_src_present_in_csp(tmp_path: pathlib.Path) -> None:
    """CSP must include style-src for inline styles."""
    html = _html(tmp_path)
    m = re.search(r'http-equiv="Content-Security-Policy"[^>]*content="([^"]*)"', html)
    assert m, "CSP not found"
    assert "style-src" in m.group(1)


# ── AC-0012: Self-contained — no network references ───────────────────────────


def test_no_src_attribute_pointing_to_network(tmp_path: pathlib.Path) -> None:
    """No src= attribute should reference a network URL (only allowlisted href= links)."""
    html = _html(tmp_path)
    # Find all src= attributes.
    src_values = re.findall(r'\bsrc=["\']([^"\']*)["\']', html)
    for v in src_values:
        assert not v.startswith("http://") and not v.startswith("https://"), (
            f"Network src= found: {v!r}"
        )


def test_no_url_in_css(tmp_path: pathlib.Path) -> None:
    """Inline CSS must not contain url() references."""
    html = _html(tmp_path)
    style_m = re.search(r"<style>(.*?)</style>", html, re.DOTALL)
    assert style_m, "<style> block not found"
    css = style_m.group(1)
    assert "url(" not in css.lower(), "url() found in CSS — network reference forbidden"


def test_no_import_in_css(tmp_path: pathlib.Path) -> None:
    """CSS must not use @import."""
    html = _html(tmp_path)
    style_m = re.search(r"<style>(.*?)</style>", html, re.DOTALL)
    assert style_m, "<style> block not found"
    assert "@import" not in style_m.group(1).lower()


# ── AC-0021: Reference-policy boundary sentence ───────────────────────────────


def test_boundary_sentence_present(tmp_path: pathlib.Path) -> None:
    """Every HTML export must contain the reference-policy boundary sentence."""
    html = _html(tmp_path)
    assert "recorded decisions" in html.lower() and "complete" in html.lower(), (
        "Boundary sentence fragment not found in HTML"
    )
    # Verify the exact BOUNDARY_NOTICE text appears in the embedded JSON.
    data = _extract_json_data(html)
    assert "boundary" in data
    boundary = data["boundary"]
    assert "recorded decisions" in boundary.lower()


# ── AC-0014: Honest bounded export ───────────────────────────────────────────


def test_bounded_mode_omits_body(tmp_path: pathlib.Path) -> None:
    """Bounded mode must include records but omit bodies, with source handoff."""
    dest = tmp_path / "bounded"
    dest.mkdir()
    r = _publish(dest, mode="bounded")
    assert r["status"] == "ok"
    html = pathlib.Path(r["path"]).read_text(encoding="utf-8")
    data = _extract_json_data(html)
    assert data["mode"] == "bounded"
    for rec in data["records"]:
        body = rec.get("body", {})
        assert not body.get("available", True), (
            f"Record {rec['id']} has available body in bounded mode"
        )
        assert body.get("omission_reason") in (
            "bounded_mode",
            "not_requested",
            "body_too_large",
        ), f"Unexpected omission reason for {rec['id']}: {body.get('omission_reason')}"


def test_bounded_mode_has_full_record_inventory(tmp_path: pathlib.Path) -> None:
    """Bounded mode must include all admitted records (complete inventory)."""
    dest_full = tmp_path / "full_inv"
    dest_full.mkdir()
    dest_bounded = tmp_path / "bounded_inv"
    dest_bounded.mkdir()
    r_full = _publish(dest_full, mode="full")
    r_bounded = _publish(dest_bounded, mode="bounded")
    assert r_full["status"] == "ok" and r_bounded["status"] == "ok"
    full_html = pathlib.Path(r_full["path"]).read_text(encoding="utf-8")
    bounded_html = pathlib.Path(r_bounded["path"]).read_text(encoding="utf-8")
    full_ids = {r["id"] for r in _extract_json_data(full_html)["records"]}
    bounded_ids = {r["id"] for r in _extract_json_data(bounded_html)["records"]}
    assert full_ids == bounded_ids, f"Record inventory differs: {full_ids ^ bounded_ids}"


def test_bounded_mode_has_relationships(tmp_path: pathlib.Path) -> None:
    """Bounded mode must include the complete relationship inventory."""
    dest = tmp_path / "bounded_rels"
    dest.mkdir()
    r = _publish(dest, mode="bounded")
    assert r["status"] == "ok"
    data = _extract_json_data(pathlib.Path(r["path"]).read_text(encoding="utf-8"))
    checked = [r for r in data["relationships"] if r["trust_class"] == "checked"]
    assert checked, "Bounded mode must include checked relationships"


def test_bounded_mode_source_handoff_present(tmp_path: pathlib.Path) -> None:
    """Bounded mode body omissions must include a source_action for handoff."""
    dest = tmp_path / "bounded_src"
    dest.mkdir()
    r = _publish(dest, mode="bounded")
    assert r["status"] == "ok"
    data = _extract_json_data(pathlib.Path(r["path"]).read_text(encoding="utf-8"))
    for rec in data["records"]:
        body = rec.get("body", {})
        if not body.get("available", True):
            reason = body.get("omission_reason", "")
            if reason in ("bounded_mode",):
                assert "source_action" in body, (
                    f"Record {rec['id']} missing source_action in bounded mode"
                )


# ── AC-0022: Destination refusals ─────────────────────────────────────────────


def test_refuses_destination_inside_worktree(tmp_path: pathlib.Path) -> None:
    """Destination inside the repository worktree must be refused."""
    fake_root = tmp_path / "repo"
    (fake_root / "docs" / "adr").mkdir(parents=True)
    (fake_root / "docs" / "rfc").mkdir(parents=True)
    dest_inside = fake_root / "output"
    dest_inside.mkdir()
    result = EXPLORER.publish_explorer(fake_root, destination=dest_inside)
    assert result["status"] == "error"
    assert result["error"]["code"] == "invalid_destination", (
        f"Expected invalid_destination code, got: {result['error']!r}"
    )
    err = result["error"]["message"].lower()
    assert "worktree" in err or "inside" in err, (
        f"Expected worktree refusal message, got: {result['error']!r}"
    )


def test_refuses_case_variant_inside_worktree(tmp_path: pathlib.Path) -> None:
    """Case-variant path inside worktree must be refused on case-insensitive FS."""
    fake_root = tmp_path / "Repo"
    (fake_root / "docs" / "adr").mkdir(parents=True)
    (fake_root / "docs" / "rfc").mkdir(parents=True)
    # Try a path that only differs in case.
    dest_variant = tmp_path / "repo"  # different case from "Repo"
    if not dest_variant.exists():
        dest_variant.mkdir()
    # Check if the FS is case-insensitive by seeing if they resolve the same.
    try:
        same = fake_root.resolve().samefile(dest_variant.resolve())
    except OSError:
        same = False
    if not same:
        pytest.skip(
            "Filesystem is case-sensitive; case-variant inside-worktree check "
            "requires a case-insensitive filesystem (e.g. macOS HFS+)"
        )
    result = EXPLORER.publish_explorer(fake_root, destination=dest_variant)
    assert result["status"] == "error", (
        "Expected refusal for case-variant destination inside worktree"
    )
    # Refused because it is the worktree, not because the path is missing.
    assert dest_variant.is_dir()
    assert result["error"]["code"] == "invalid_destination"
    assert "inside the repository worktree" in result["error"]["message"]


def test_refuses_non_html_name(tmp_path: pathlib.Path) -> None:
    """Output name not ending in .html must be refused."""
    result = EXPLORER.publish_explorer(
        FIXTURE,
        destination=str(tmp_path / "out.txt"),
    )
    # Destination is a file path: parent is tmp_path, name is out.txt
    assert result["status"] == "error"
    assert result["error"]["code"] == "invalid_destination", (
        f"Expected invalid_destination code, got: {result['error']!r}"
    )
    assert (
        ".html" in result["error"]["message"].lower()
        or "html" in result["error"]["message"].lower()
    ), f"Expected .html name refusal, got: {result['error']!r}"


def test_refuses_multi_segment_name(tmp_path: pathlib.Path) -> None:
    """Multi-segment name (containing path separator) must be refused via validator."""
    (tmp_path / "sub").mkdir()
    # Verify the name check with a truly bad name by testing the validator directly.
    with pytest.raises(ValueError, match=r"single path segment"):
        EXPLORER._validate_destination(tmp_path, "sub/decisions.html", FIXTURE)


def test_refuses_symlinked_parent(tmp_path: pathlib.Path) -> None:
    """Symlinked destination directory must be refused by file_safety."""
    real = tmp_path / "real"
    real.mkdir()
    link = tmp_path / "link"
    link.symlink_to(real)
    result = EXPLORER.publish_explorer(FIXTURE, destination=link)
    assert result["status"] == "error", "Expected refusal for symlinked destination directory"
    assert result["error"]["code"] in ("invalid_destination", "corpus_error"), (
        f"Expected machine-readable code for symlink refusal, got: {result['error']!r}"
    )


def test_refuses_existing_target(tmp_path: pathlib.Path) -> None:
    """If the target file already exists, publication must be refused."""
    r1 = _publish(tmp_path)
    assert r1["status"] == "ok"
    # Try to publish again to the same directory — a different timestamp name
    # is generated, so force the same name.
    existing = pathlib.Path(r1["path"])
    result = EXPLORER.publish_explorer(
        FIXTURE,
        destination=str(existing),  # treat as file path, parent = tmp_path
    )
    # Since this file already exists, it must be refused.
    assert result["status"] == "error"
    assert result["error"]["code"] in ("invalid_destination", "publish_failed"), (
        f"Expected invalid_destination or publish_failed code, got: {result['error']!r}"
    )
    msg = result["error"]["message"].lower()
    assert "exist" in msg or "already" in msg, (
        f"Expected existing-file refusal, got: {result['error']!r}"
    )


def test_refuses_over_budget_without_confirm(tmp_path: pathlib.Path) -> None:
    """Export exceeding budget without confirm_over_budget must be refused."""
    import unittest.mock as _mock

    with _mock.patch.object(EXPLORER, "BUDGET_BYTES", 1):  # 1-byte budget
        result = _publish(tmp_path, mode="bounded", confirm_over_budget=False)
    # Should error because estimated size > 1 byte
    assert result["status"] == "error"
    assert result["error"]["code"] == "over_budget", (
        f"Expected over_budget code, got: {result['error']!r}"
    )
    msg = result["error"]["message"].lower()
    assert "budget" in msg or "exceed" in msg, (
        f"Expected budget-exceeded message, got: {result['error']!r}"
    )


def test_export_refusal_carries_machine_readable_code() -> None:
    """Every export refusal must carry a machine-readable code in error["code"].

    Tests the invalid-mode code as the simplest refusal path.

    Mutation: changing error to a plain string instead of a dict with 'code' would
    fail the isinstance check and the code assertion.
    """
    result = EXPLORER.publish_explorer(FIXTURE, mode="unknown_mode")
    assert result["status"] == "error"
    err = result["error"]
    assert isinstance(err, dict), f"error must be a dict with code/message; got {type(err)}"
    assert "code" in err, f"error dict must have 'code' field; got {err!r}"
    assert "message" in err, f"error dict must have 'message' field; got {err!r}"
    assert err["code"] == "invalid_mode", f"expected code='invalid_mode'; got {err['code']!r}"


def test_confirm_over_budget_allows_publish(tmp_path: pathlib.Path) -> None:
    """confirm_over_budget=True allows publication past the budget."""
    import unittest.mock as _mock

    dest = tmp_path / "budget_confirm"
    dest.mkdir()
    with _mock.patch.object(EXPLORER, "BUDGET_BYTES", 1):
        result = _publish(dest, confirm_over_budget=True)
    assert result["status"] == "ok"


# ── AC-0022: Temp sibling and published file modes ────────────────────────────


@pytest.mark.skipif(os.name != "posix", reason="POSIX-only file mode test")
def test_temp_sibling_mode_0600_before_write(tmp_path: pathlib.Path) -> None:
    """fchmod 0o600 must be called before content is written, and the actual
    temp-file mode must be 0o600 at write time.

    Checks both call order AND actual filesystem mode — the original test only
    checked call order, so a mutation swapping fchmod(0o644) would have passed.

    Mutation: changing 0o600 to 0o644 in the fchmod call would make the actual-mode
    assertion fail while the (now-corrected) event filter still catches it.
    """
    import unittest.mock as _mock

    events: list[tuple] = []
    real_fchmod = os.fchmod
    actual_modes_at_fchmod: list[int] = []

    def mock_fchmod(fd: int, mode: int) -> None:
        real_fchmod(fd, mode)
        # Read back the actual mode from the OS to confirm the requested mode landed.
        actual = stat.S_IMODE(os.fstat(fd).st_mode)
        actual_modes_at_fchmod.append(actual)
        events.append(("fchmod", mode))

    real_fdopen = os.fdopen

    def mock_fdopen(fd: int, flag: str, *args, **kwargs):  # type: ignore[return]
        handle = real_fdopen(fd, flag, *args, **kwargs)
        real_write = handle.write

        def intercepted_write(data: bytes) -> int:
            events.append(("write",))
            return real_write(data)

        handle.write = intercepted_write  # type: ignore[method-assign]
        return handle

    with (
        _mock.patch.object(os, "fchmod", mock_fchmod),
        _mock.patch.object(os, "fdopen", mock_fdopen),
    ):
        result = _publish(tmp_path)

    assert result["status"] == "ok", result.get("error")

    fchmod_indices = [i for i, e in enumerate(events) if e[0] == "fchmod" and e[1] == 0o600]
    write_indices = [i for i, e in enumerate(events) if e[0] == "write"]
    assert fchmod_indices, "os.fchmod(fd, 0o600) was never called"
    assert write_indices, "write was never called"
    assert min(fchmod_indices) < min(write_indices), "fchmod(0o600) must be called before write"
    # Verify actual filesystem mode, not just the argument passed to fchmod.
    assert any(m == 0o600 for m in actual_modes_at_fchmod), (
        f"Actual file mode after fchmod was not 0o600; got {[oct(m) for m in actual_modes_at_fchmod]}"
    )


@pytest.mark.skipif(os.name != "posix", reason="POSIX-only file mode test")
def test_published_file_mode_0600(tmp_path: pathlib.Path) -> None:
    """Published file must have owner-only mode 0o600 on POSIX."""
    r = _publish(tmp_path)
    assert r["status"] == "ok"
    path = pathlib.Path(r["path"])
    mode = stat.S_IMODE(path.stat().st_mode)
    assert mode == 0o600, f"Expected 0o600, got {oct(mode)}"


@pytest.mark.skipif(os.name != "posix", reason="POSIX-only fd-leak test")
def test_fchmod_failure_closes_fd(tmp_path: pathlib.Path) -> None:
    """The temp-file descriptor is closed even when fchmod raises an error.

    Captures the specific fd opened for the temporary file and asserts it is closed
    after the fchmod failure — no external binary, no count slack.

    Mutation: removing the fd_owned_by_fdopen close in the finally block would
    leave the descriptor open; this test detects the leak by testing that the
    exact captured fd is no longer valid after the call.
    """
    import unittest.mock as _mock

    captured_fds: list[int] = []
    real_open = os.open

    def capturing_open(path, flags, mode=0o777, *, dir_fd=None):  # type: ignore[no-untyped-def]
        fd = real_open(path, flags, mode, dir_fd=dir_fd)
        if str(path).endswith(".tmp"):
            captured_fds.append(fd)
        return fd

    target_dir = tmp_path / "out"
    target_dir.mkdir()
    target_path = target_dir / "out.html"

    with (
        _mock.patch.object(os, "open", side_effect=capturing_open),
        _mock.patch.object(os, "fchmod", side_effect=OSError("fchmod blocked")),
        pytest.raises(OSError, match="fchmod blocked"),
    ):
        EXPLORER._publish_atomically(target_dir, target_path, b"content")

    assert captured_fds, "the temporary file was never opened"
    leaked_fd = captured_fds[0]
    # If the fd is still open, os.fstat(leaked_fd) succeeds.
    # If it was properly closed, it raises OSError (Bad file descriptor).
    try:
        os.fstat(leaked_fd)
    except OSError:
        pass  # Closed as expected.
    else:
        pytest.fail(f"fd {leaked_fd} was not closed after fchmod failure — descriptor leaked")


# ── SEC-7: Temp file identity validated before link ──────────────────────────


@pytest.mark.skipif(os.name != "posix", reason="POSIX-only identity test")
def test_validated_dir_used_for_publication(tmp_path: pathlib.Path) -> None:
    """publish_explorer uses the resolved (validated) directory for publication.

    The destination returned by _validate_destination is the resolved canonical
    path.  Publication must use that path, not re-derive it from the original
    argument.

    Mutation: bypassing _validate_destination and deriving the path from the raw
    destination argument would fail when a symlink is involved — a symlinked
    parent is refused by validate_destination, so a bypass would either use the
    wrong path or skip the check.

    This test confirms the resolved canonical path is used: it creates a valid
    directory, publishes to it, and checks that the output file has the expected
    resolved path as its parent.
    """
    real_dir = tmp_path / "real"
    real_dir.mkdir()
    result = EXPLORER.publish_explorer(
        FIXTURE,
        destination=real_dir,
        name="validated.html",
        mode="bounded",
    )
    assert result["status"] == "ok", f"expected ok; got {result!r}"
    out_path = pathlib.Path(result["path"])
    # The published file must be inside the resolved canonical directory.
    assert out_path.resolve().parent == real_dir.resolve(), (
        f"Published file must be in the validated directory {real_dir.resolve()}; "
        f"got {out_path.resolve().parent}"
    )


@pytest.mark.skipif(os.name != "posix", reason="POSIX-only nlink test")
def test_publish_atomically_rejects_extra_hard_link(tmp_path: pathlib.Path) -> None:
    """_publish_atomically refuses when the temp file has extra hard links.

    Simulates a race: another process hard-links the temp file before os.link.
    The nlink check must detect nlink > 1 and refuse.

    Mutation: removing the nlink check would allow publication even with a
    compromised temp file.
    """
    import types
    import unittest.mock as _mock

    target_dir = tmp_path / "out"
    target_dir.mkdir()
    target_path = target_dir / "out.html"

    # Build a fake stat_result with st_nlink=2 but correct st_mode (0o100600 = reg+0o600)
    real_stat = os.stat

    call_count = [0]

    def patched_stat(path, **kw):
        st = real_stat(path, **kw)
        path_str = str(path)
        if ".nav-decisions-" in path_str and ".tmp" in path_str:
            call_count[0] += 1
            # Return a namespace that mimics stat_result with st_nlink=2
            fake = types.SimpleNamespace(**{
                attr: getattr(st, attr) for attr in dir(st) if attr.startswith("st_")
            })
            fake.st_nlink = 2  # inject extra link
            return fake
        return st

    with (
        _mock.patch.object(os, "stat", patched_stat),
        pytest.raises(OSError, match="links before os.link"),
    ):
        EXPLORER._publish_atomically(target_dir, target_path, b"content")


# ── AC-0013, AC-0022: Failure leaves no partial file ─────────────────────────


def test_no_partial_file_on_link_failure(tmp_path: pathlib.Path) -> None:
    """If os.link fails, no partial file must remain at the destination.

    Uses a valid destination so the test actually reaches os.link.
    Mutation: removing the unlink-on-failure cleanup would leave a partial file.
    """
    import unittest.mock as _mock

    called_paths: list[pathlib.Path] = []

    def failing_link(src: str, dst: str, **kwargs: object) -> None:
        called_paths.append(tmp_path / dst)
        raise OSError("injected link failure")

    with _mock.patch.object(os, "link", failing_link):
        result = EXPLORER.publish_explorer(
            FIXTURE,
            destination=tmp_path,
            name="decisions.html",
            mode="bounded",
        )

    assert result["status"] == "error"
    # os.link must have been called — if it wasn't, the test proves nothing.
    assert called_paths, "os.link was never called; test did not reach the atomic-publish path"
    # No file at any of the attempted destination paths.
    for p in called_paths:
        assert not p.exists(), f"Partial file left at {p}"


def test_no_temp_sibling_left_on_failure(tmp_path: pathlib.Path) -> None:
    """Temp sibling must be cleaned up even when publication fails."""
    import unittest.mock as _mock

    def failing_link(src: str, dst: str, **kwargs: object) -> None:
        raise OSError("injected link failure")

    # Record what files exist in tmp_path before and after.
    before = set(tmp_path.iterdir())
    with _mock.patch.object(os, "link", failing_link):
        _publish(tmp_path)
    after = set(tmp_path.iterdir())
    new_files = after - before
    # No .tmp siblings should remain.
    tmp_files = [f for f in new_files if f.suffix == ".tmp"]
    assert not tmp_files, f"Temp files left behind: {tmp_files}"


# ── AC-0011: Source-link encoding and allowlist ────────────────────────────────


def test_hostile_basename_question_mark_encoded() -> None:
    """A basename containing '?' must be percent-encoded in the source link."""
    encoded = EXPLORER._encode_path("docs/adr/0001-?foo.md")
    assert "?" not in encoded
    assert "%3F" in encoded.upper() or "?" not in encoded


def test_hostile_basename_hash_encoded() -> None:
    """A basename containing '#' must be percent-encoded."""
    encoded = EXPLORER._encode_path("docs/adr/0001-#bar.md")
    assert "#" not in encoded


def test_hostile_basename_percent_encoded() -> None:
    """A basename containing '%' must be percent-encoded."""
    encoded = EXPLORER._encode_path("docs/adr/0001-%evil.md")
    # The % must itself be encoded so it can't form a percent-escape.
    assert encoded.count("%") == 1 or "%25" in encoded.upper()


def test_dot_segment_degrades_to_inert() -> None:
    """Paths containing '..' segments are refused (returned as-is); the link builder
    must then produce no clickable URL for such a path (inert provenance only).

    File_safety-sourced paths never contain '..', so this defends against any
    future code path that might bypass the confined read.
    """
    import unittest.mock as _mock

    hostile = "docs/adr/../../../etc/passwd"
    encoded = EXPLORER._encode_path(hostile)
    # _encode_path returns the raw string when it finds a dot-segment.
    assert encoded == hostile, (
        f"Expected raw string returned for dot-segment path, got: {encoded!r}"
    )

    # _build_source_links should produce inert provenance when the path
    # would result in a non-percent-encoded URL (the URL contains '..').
    def mock_git(args, cwd, timeout=5):
        if args == ["config", "--get", "remote.origin.url"]:
            return "https://github.com/owner/repo.git"
        if args == ["rev-parse", "HEAD"]:
            return "a" * 40
        return None

    with _mock.patch.object(EXPLORER, "_run_git", side_effect=mock_git):
        links = EXPLORER._build_source_links(FIXTURE, [hostile])

    sl = links.get(hostile, {})
    # Should either be inert (url=None) or produce a URL without raw '..'.
    url = sl.get("url", "") or ""
    assert ".." not in url.split("/"), f"Dot-segment traversal found in URL: {url!r}"


def test_non_allowlisted_host_degrades_to_inert(tmp_path: pathlib.Path) -> None:
    """A remote URL on a non-allowlisted host produces inert provenance, not a link."""
    import unittest.mock as _mock

    with _mock.patch.object(
        EXPLORER, "_run_git", return_value="https://bitbucket.org/owner/repo.git"
    ):
        links = EXPLORER._build_source_links(FIXTURE, ["docs/adr/0001-alpha.md"])

    sl = links.get("docs/adr/0001-alpha.md", {})
    assert sl.get("url") is None or sl.get("kind") == "inert", (
        f"Non-allowlisted host should produce inert link, got: {sl}"
    )


def test_github_allowlisted_host_produces_link(tmp_path: pathlib.Path) -> None:
    """A github.com remote produces a clickable link with percent-encoded path."""
    import unittest.mock as _mock

    def mock_git(args: list, cwd: str, timeout: int = 5):
        if args == ["config", "--get", "remote.origin.url"]:
            return "https://github.com/test-owner/test-repo.git"
        if args == ["rev-parse", "HEAD"]:
            return "a" * 40
        if args[0] == "status":
            return ""  # clean working tree
        if args[:3] == ["branch", "-r", "--contains"]:
            return "  origin/main"  # HEAD is on remote
        return None

    # _build_source_links no longer checks git root; the caller (publish_explorer)
    # does via _git_root_matches.  Mock that check True to exercise link building.
    with (
        _mock.patch.object(EXPLORER, "_run_git", side_effect=mock_git),
        _mock.patch.object(EXPLORER, "_git_root_matches", return_value=True),
    ):
        links = EXPLORER._build_source_links(FIXTURE, ["docs/adr/0001-alpha.md"])

    sl = links.get("docs/adr/0001-alpha.md", {})
    assert sl.get("url", "").startswith("https://github.com/"), (
        f"Expected github.com link, got: {sl}"
    )
    assert sl.get("kind") == "commit_pinned"
    assert "docs/adr/0001-alpha.md" in sl["url"]


def test_branch_link_labelled_may_be_newer(tmp_path: pathlib.Path) -> None:
    """When no HEAD sha is available, source link is labelled as potentially newer."""
    import unittest.mock as _mock

    def mock_git(args: list, cwd: str, timeout: int = 5):
        if args == ["config", "--get", "remote.origin.url"]:
            return "https://github.com/owner/repo.git"
        return None  # no HEAD sha

    # _build_source_links no longer checks git root; mock _git_root_matches True.
    with (
        _mock.patch.object(EXPLORER, "_run_git", side_effect=mock_git),
        _mock.patch.object(EXPLORER, "_git_root_matches", return_value=True),
    ):
        links = EXPLORER._build_source_links(FIXTURE, ["docs/adr/0001-alpha.md"])

    sl = links["docs/adr/0001-alpha.md"]
    assert sl["kind"] == "branch_latest"
    assert "newer" in sl["label"].lower() or "HEAD" in sl["label"]


# ── validate_destination unit tests ───────────────────────────────────────────


def test_validate_rejects_non_html_name(tmp_path: pathlib.Path) -> None:
    with pytest.raises(ValueError, match=r"\.html"):
        EXPLORER._validate_destination(tmp_path, "output.txt", FIXTURE)


def test_validate_rejects_absolute_name(tmp_path: pathlib.Path) -> None:
    with pytest.raises(ValueError):
        EXPLORER._validate_destination(tmp_path, "/etc/passwd.html", FIXTURE)


def test_validate_rejects_dotdot_name(tmp_path: pathlib.Path) -> None:
    with pytest.raises(ValueError):
        EXPLORER._validate_destination(tmp_path, "../escape.html", FIXTURE)


def test_validate_accepts_valid_name(tmp_path: pathlib.Path) -> None:
    resolved_dir, full, _identity = EXPLORER._validate_destination(
        tmp_path, "decisions.html", FIXTURE
    )
    assert full == tmp_path / "decisions.html"
    assert resolved_dir == tmp_path.resolve()


# ── is_inside_worktree unit tests ─────────────────────────────────────────────


def test_is_inside_worktree_same(tmp_path: pathlib.Path) -> None:
    assert EXPLORER._is_inside_worktree(tmp_path, tmp_path) is True


def test_is_inside_worktree_subdir(tmp_path: pathlib.Path) -> None:
    sub = tmp_path / "sub"
    sub.mkdir()
    assert EXPLORER._is_inside_worktree(sub, tmp_path) is True


def test_is_inside_worktree_sibling(tmp_path: pathlib.Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    sibling = tmp_path / "other"
    sibling.mkdir()
    assert EXPLORER._is_inside_worktree(sibling, root) is False


# ══════════════════════════════════════════════════════════════════════════════
# ADV-7: AC-0022 destination shapes — symlink ancestor, hostile-record proof
# ══════════════════════════════════════════════════════════════════════════════


@pytest.mark.skipif(os.name != "posix", reason="POSIX-only symlink test")
def test_refuses_ancestor_symlink_in_destination_path(tmp_path: pathlib.Path) -> None:
    """A symlink in an ancestor component of the destination path must be refused.

    The destination directory itself may be a real directory, but if any
    component below it in the path is a symlink, publication is refused.
    AC-0022 requires that destination ancestors are not symlinks.

    Mutation: removing the ancestor-symlink walk would allow publication
    through a symlinked path component.
    """
    real = tmp_path / "real"
    real.mkdir()
    link = tmp_path / "link"
    link.symlink_to(real)
    # sub is a real directory accessed via the symlink in link.
    sub = real / "sub"
    sub.mkdir()
    # Supply link/sub as destination — the link component is a symlink.
    result = EXPLORER.publish_explorer(FIXTURE, destination=link / "sub")
    assert result["status"] == "error", (
        "destination path going through a symlink ancestor must be refused"
    )
    assert result["error"]["code"] in ("invalid_destination", "corpus_error"), (
        f"expected stable refusal code; got: {result['error']!r}"
    )


def test_hostile_record_does_not_redirect_destination(tmp_path: pathlib.Path) -> None:
    """Instruction-shaped record text cannot redirect the export destination.

    The export API takes destination only from its argument.  Exporting the
    instruction fixture (which has prompt-injection text) must produce a file
    in the given directory, not somewhere else.

    Mutation: routing destination from record content would make the file land
    outside tmp_path.
    """
    instruction_fixture = HERE / "fixtures" / "negative" / "instruction"
    dest = tmp_path / "out"
    dest.mkdir()
    result = EXPLORER.publish_explorer(instruction_fixture, destination=dest)
    # The corpus has one well-formed record, so the export must succeed.
    assert result["status"] == "ok", (
        f"instruction fixture must export successfully; got {result!r}"
    )
    out_path = pathlib.Path(result["path"])
    # The output file must reside inside the given destination directory.
    assert out_path.resolve().parent == dest.resolve(), (
        f"file must land in {dest.resolve()}; got {out_path.resolve().parent}"
    )


# ══════════════════════════════════════════════════════════════════════════════
# ADV-9 / SEC-4 / QE-1: export register safety and summary parity
# ══════════════════════════════════════════════════════════════════════════════


def test_export_refuses_unsafe_register(tmp_path: pathlib.Path) -> None:
    """A dangling symlink register file must refuse the export with unsafe_input.

    The export must read registers through the same code path as the query so
    that an unsafe or oversized register stops the whole export.

    Mutation: catching UnsafeContentError and returning 'absent' would allow
    the export to succeed with a false inventory.
    """
    import shutil

    corpus = tmp_path / "mixed"
    shutil.copytree(str(FIXTURE), str(corpus))
    reg_dir = corpus / "docs" / "product" / "findings"
    reg_dir.mkdir(parents=True, exist_ok=True)
    reg_file = reg_dir / "rfc-candidates.md"
    if reg_file.exists() or reg_file.is_symlink():
        reg_file.unlink()
    reg_file.symlink_to("/absolutely/nonexistent/dangling/target")
    assert reg_file.is_symlink() and not reg_file.exists(), "register must be a dangling symlink"
    result = EXPLORER.publish_explorer(corpus, destination=tmp_path / "dest")
    assert result["status"] == "error", "dangling symlink register must refuse the export"
    assert result["error"]["code"] in ("unsafe_input", "corpus_error"), (
        f"expected unsafe_input or corpus_error; got {result['error']!r}"
    )


def test_export_two_table_register_sum(tmp_path: pathlib.Path) -> None:
    """Export summary counts data rows across every table in the register file.

    A two-table register with 1 and 2 data rows must report row_count=3.

    Mutation: stopping after the first table would report row_count=1.
    """
    import shutil

    corpus = tmp_path / "mixed"
    shutil.copytree(str(FIXTURE), str(corpus))
    reg_dir = corpus / "docs" / "product" / "findings"
    reg_dir.mkdir(parents=True, exist_ok=True)
    reg_file = reg_dir / "rfc-candidates.md"
    if reg_file.exists() or reg_file.is_symlink():
        reg_file.unlink()
    two_table = (
        "# RFC Candidates\n\n"
        "| RFC | Description |\n"
        "|-----|-------------|\n"
        "| RFC-0001 | First candidate |\n"
        "\n"
        "## Archived\n\n"
        "| RFC | Reason |\n"
        "|-----|--------|\n"
        "| RFC-0002 | Done |\n"
        "| RFC-0003 | Withdrawn |\n"
    )
    reg_file.write_text(two_table)
    dest = tmp_path / "dest"
    dest.mkdir()
    result = EXPLORER.publish_explorer(corpus, destination=dest, mode="bounded")
    assert result["status"] == "ok", f"export must succeed; got {result!r}"
    html = pathlib.Path(result["path"]).read_text(encoding="utf-8")
    data = _extract_json_data(html)
    row_count = data["summary"]["register_files"]["rfc_candidates"]["row_count"]
    assert row_count == 3, f"two-table register (1 + 2 data rows) must count 3; got {row_count}"


def test_export_summary_parity_with_query_summary(tmp_path: pathlib.Path) -> None:
    """Export embedded summary must match the query summary operation.

    The export builds its summary from the same code as the query, so the
    by_kind, by_lifecycle_value, and unresolved counts must be identical.

    Mutation: a divergent summary path would produce different counts.
    """
    query_payload = NAV.run_query(FIXTURE, {"operation": "summary"})
    assert query_payload["status"] == "ok", f"query must succeed; got {query_payload!r}"
    q_summary = query_payload["summary"]

    dest = tmp_path / "dest"
    dest.mkdir()
    result = EXPLORER.publish_explorer(FIXTURE, destination=dest, mode="bounded")
    assert result["status"] == "ok", f"export must succeed; got {result!r}"
    html = pathlib.Path(result["path"]).read_text(encoding="utf-8")
    data = _extract_json_data(html)
    e_summary = data["summary"]

    assert e_summary["by_kind"] == q_summary["by_kind"], (
        f"by_kind mismatch: export={e_summary['by_kind']} query={q_summary['by_kind']}"
    )
    assert e_summary["by_lifecycle_value"] == q_summary["by_lifecycle_value"], (
        "by_lifecycle_value mismatch between export and query summary"
    )
    assert e_summary["unresolved_reference_count"] == q_summary["unresolved_reference_count"], (
        "unresolved_reference_count mismatch between export and query summary"
    )
    assert e_summary["register_files"] == q_summary["register_files"], (
        "register_files mismatch between export and query summary"
    )


# ══════════════════════════════════════════════════════════════════════════════
# ADV-18: Full export embeds every admitted body (up to 2 MiB admission bound)
# ══════════════════════════════════════════════════════════════════════════════


def test_full_export_embeds_body_larger_than_1_mib(tmp_path: pathlib.Path) -> None:
    """Full export embeds record bodies between 1 MiB and 2 MiB.

    The record query operation limits body to 1 MiB; the full export must embed
    every admitted body up to the 2 MiB admission limit.

    Mutation: reusing the record-query body_available flag (1 MiB threshold) for
    the full export would mark bodies > 1 MiB as body_too_large instead of
    embedding them.
    """
    corpus = tmp_path / "corpus"
    adr_dir = corpus / "docs" / "adr"
    adr_dir.mkdir(parents=True)
    # Body is 1.5 MiB (above the 1 MiB query limit, below the 2 MiB admission limit).
    big_body = "x" * (1024 * 1024 + 512 * 1024)
    content = (
        f"# ADR-0001: Big body record\n\n- **Status:** Accepted\n\n## Context\n\n{big_body}\n"
    )
    (adr_dir / "0001-big.md").write_text(content)
    dest = tmp_path / "dest"
    dest.mkdir()
    result = EXPLORER.publish_explorer(corpus, destination=dest, mode="full")
    assert result["status"] == "ok", f"large-body export must succeed; got {result!r}"
    html = pathlib.Path(result["path"]).read_text(encoding="utf-8")
    data = _extract_json_data(html)
    body = data["records"][0]["body"]
    assert body.get("available") is True, f"full export must embed 1.5 MiB body; got {body!r}"
    assert isinstance(body.get("content"), str) and big_body in body["content"], (
        "full export must carry the 1.5 MiB body text itself, not only an availability flag"
    )
    assert "omission_reason" not in body or body.get("omission_reason") is None, (
        f"full export must not omit admitted body; got {body!r}"
    )


# ══════════════════════════════════════════════════════════════════════════════
# ADV-19: Commit-pinned link only when working tree is clean
# ══════════════════════════════════════════════════════════════════════════════


def test_commit_pinned_link_only_when_clean(tmp_path: pathlib.Path) -> None:
    """A commit-pinned link is emitted only when the working tree is clean and HEAD is pushed.

    Mutation: skipping the status check would emit commit_pinned even with
    uncommitted changes, giving a link that points to content differing from
    the export.
    """
    import unittest.mock as _mock

    def mock_git_clean(args: list, cwd: str, timeout: int = 5) -> str | None:
        if args == ["config", "--get", "remote.origin.url"]:
            return "https://github.com/owner/repo.git"
        if args == ["rev-parse", "HEAD"]:
            return "b" * 40
        if args[0] == "status":
            return ""  # clean working tree
        if args[:3] == ["branch", "-r", "--contains"]:
            return "  origin/main"  # HEAD is on remote
        return None

    with (
        _mock.patch.object(EXPLORER, "_run_git", side_effect=mock_git_clean),
        _mock.patch.object(EXPLORER, "_git_root_matches", return_value=True),
    ):
        links = EXPLORER._build_source_links(FIXTURE, ["docs/adr/0001-alpha.md"])

    sl = links["docs/adr/0001-alpha.md"]
    assert sl["kind"] == "commit_pinned", (
        f"clean working tree with HEAD sha on remote must produce commit_pinned; got {sl['kind']!r}"
    )


def test_dirty_working_tree_link_labelled_may_be_newer(tmp_path: pathlib.Path) -> None:
    """A dirty working tree degrades the link to branch_latest with 'may be newer' label.

    Mutation: skipping the status check would keep commit_pinned even when
    the working tree has uncommitted changes.
    """
    import unittest.mock as _mock

    def mock_git_dirty(args: list, cwd: str, timeout: int = 5) -> str | None:
        if args == ["config", "--get", "remote.origin.url"]:
            return "https://github.com/owner/repo.git"
        if args == ["rev-parse", "HEAD"]:
            return "c" * 40
        if args[0] == "status":
            return "M docs/adr/0001-alpha.md"  # dirty — uncommitted change
        if args[:3] == ["branch", "-r", "--contains"]:
            return "  origin/main"  # HEAD is on remote (dirty takes precedence)
        return None

    with (
        _mock.patch.object(EXPLORER, "_run_git", side_effect=mock_git_dirty),
        _mock.patch.object(EXPLORER, "_git_root_matches", return_value=True),
    ):
        links = EXPLORER._build_source_links(FIXTURE, ["docs/adr/0001-alpha.md"])

    sl = links["docs/adr/0001-alpha.md"]
    assert sl["kind"] == "branch_latest", (
        f"dirty working tree must produce branch_latest; got {sl['kind']!r}"
    )
    assert "newer" in sl["label"].lower() or "HEAD" in sl["label"], (
        f"branch_latest label must mention 'newer' or 'HEAD'; got {sl['label']!r}"
    )


def test_unpushed_head_produces_branch_latest() -> None:
    """An unpushed HEAD (not reachable on any remote) produces branch_latest.

    Emitting a commit-pinned link to an unpushed commit would create a broken
    URL. The remote-reachability check prevents this.

    Mutation: removing the 'branch -r --contains HEAD' check would allow
    commit_pinned links to unpushed commits.
    """
    import unittest.mock as _mock

    def mock_git_unpushed(args: list, cwd: str, timeout: int = 5) -> str | None:
        if args == ["config", "--get", "remote.origin.url"]:
            return "https://github.com/owner/repo.git"
        if args == ["rev-parse", "HEAD"]:
            return "e" * 40
        if args[0] == "status":
            return ""  # clean working tree
        if args[:3] == ["branch", "-r", "--contains"]:
            return ""  # HEAD is NOT on any remote branch
        return None

    with (
        _mock.patch.object(EXPLORER, "_run_git", side_effect=mock_git_unpushed),
        _mock.patch.object(EXPLORER, "_git_root_matches", return_value=True),
    ):
        links = EXPLORER._build_source_links(FIXTURE, ["docs/adr/0001-alpha.md"])

    sl = links["docs/adr/0001-alpha.md"]
    assert sl["kind"] == "branch_latest", (
        f"unpushed HEAD must produce branch_latest; got {sl['kind']!r}"
    )
    assert "newer" in sl["label"].lower() or "HEAD" in sl["label"], (
        f"branch_latest label must mention 'newer' or 'HEAD'; got {sl['label']!r}"
    )


# ══════════════════════════════════════════════════════════════════════════════
# SEC-8: Dot-segment owner or repo degrades to inert; allowlist is checked
# ══════════════════════════════════════════════════════════════════════════════


def test_dot_segment_owner_repo_degrades_to_inert() -> None:
    """A URL with dot-segment owner or repo must produce inert provenance.

    'https://github.com/../..' has owner='..' and repo='..'; both are refused
    so no clickable link is emitted.  _SOURCE_HOST_ALLOWLIST governs which
    hosts are permitted; github.com is in the allowlist.

    Mutation: removing the dot-segment owner/repo check would emit a link
    that normalises to an unintended path on the forge.
    """
    result = EXPLORER._parse_github_identity("https://github.com/../..")
    assert result is None, f"dot-segment owner/repo must be refused; got {result!r}"

    import unittest.mock as _mock

    def mock_git_dot(args: list, cwd: str, timeout: int = 5) -> str | None:
        if args == ["config", "--get", "remote.origin.url"]:
            return "https://github.com/../.."
        if args == ["rev-parse", "HEAD"]:
            return "d" * 40
        if args[0] == "status":
            return ""
        return None

    with (
        _mock.patch.object(EXPLORER, "_run_git", side_effect=mock_git_dot),
        _mock.patch.object(EXPLORER, "_git_root_matches", return_value=True),
    ):
        links = EXPLORER._build_source_links(FIXTURE, ["docs/adr/0001-alpha.md"])

    sl = links["docs/adr/0001-alpha.md"]
    assert sl.get("url") is None or sl.get("kind") == "inert", (
        f"dot-segment remote URL must produce inert link; got {sl!r}"
    )


# ── Stage-2 T7 findings: ADV-5/QE-3, ADV-6, ADV-8/SEC-2, ADV-13/SEC-3 ───────


def test_caller_assertions_in_relationships_data_island(tmp_path: pathlib.Path) -> None:
    """Caller assertions are embedded as navigation_only tuples in relationships.

    Assertions are no longer a separate key; they appear in the relationships
    list with trust_class='navigation_only' and resolution_state='caller_asserted'.
    The data island must not carry an 'embedded_assertions' key.
    """
    raw_assert = {"from": "ADR-0001", "to": "ADR-0002", "text": "caller text"}
    r = EXPLORER.publish_explorer(
        FIXTURE,
        destination=tmp_path,
        assertions=[raw_assert],
    )
    assert r["status"] == "ok", r.get("error")
    html = pathlib.Path(r["path"]).read_text(encoding="utf-8")
    data = _extract_json_data(html)
    # The data island must not carry a separate embedded_assertions key.
    assert "embedded_assertions" not in data, (
        "data island must not carry 'embedded_assertions'; assertions go in relationships"
    )
    nav_only = [
        r for r in data.get("relationships", []) if r.get("trust_class") == "navigation_only"
    ]
    assert len(nav_only) == 1, f"expected 1 navigation_only relationship; got {nav_only!r}"
    a = nav_only[0]
    assert a.get("trust_class") == "navigation_only", (
        f"trust_class must be 'navigation_only'; got {a.get('trust_class')!r}"
    )
    assert a.get("resolution_state") == "caller_asserted", (
        f"resolution_state must be 'caller_asserted'; got {a.get('resolution_state')!r}"
    )
    assert a.get("raw_value") == "caller text", (
        f"raw_value must equal assertion 'text'; got {a.get('raw_value')!r}"
    )
    assert a.get("from") == "ADR-0001"
    assert a.get("to") == "ADR-0002"


def test_export_invalid_assertion_non_list_refused(tmp_path: pathlib.Path) -> None:
    """Export refuses a non-list assertions value with invalid_assertion error shape."""
    r = EXPLORER.publish_explorer(
        FIXTURE,
        destination=tmp_path,
        assertions="not a list",  # type: ignore[arg-type]
    )
    assert r["status"] == "error", f"non-list assertions must be refused; got {r!r}"
    assert r["error"]["code"] == "invalid_assertion", (
        f"expected invalid_assertion; got {r['error']['code']!r}"
    )
    # Nothing published.
    assert not list(pathlib.Path(tmp_path).glob("*.html")), (
        "no HTML file must be published on assertion refusal"
    )


def test_export_invalid_assertion_non_dict_element_refused(
    tmp_path: pathlib.Path,
) -> None:
    """Export refuses a non-dict assertion element with invalid_assertion error shape."""
    r = EXPLORER.publish_explorer(
        FIXTURE,
        destination=tmp_path,
        assertions=["plain string"],  # type: ignore[list-item]
    )
    assert r["status"] == "error", f"non-dict element must be refused; got {r!r}"
    assert r["error"]["code"] == "invalid_assertion", (
        f"expected invalid_assertion; got {r['error']['code']!r}"
    )
    assert not list(pathlib.Path(tmp_path).glob("*.html")), (
        "no HTML file must be published on assertion refusal"
    )


def test_export_invalid_assertion_partial_dict_refused(
    tmp_path: pathlib.Path,
) -> None:
    """Export refuses a partial assertion dict missing 'text' with invalid_assertion."""
    r = EXPLORER.publish_explorer(
        FIXTURE,
        destination=tmp_path,
        assertions=[{"from": "ADR-0001", "to": "ADR-0002"}],
    )
    assert r["status"] == "error", f"partial assertion dict must be refused; got {r!r}"
    assert r["error"]["code"] == "invalid_assertion", (
        f"expected invalid_assertion; got {r['error']['code']!r}"
    )
    assert not list(pathlib.Path(tmp_path).glob("*.html")), (
        "no HTML file must be published on assertion refusal"
    )


def test_support_refs_in_data_island_mixed(tmp_path: pathlib.Path) -> None:
    """ADV-6: Support references are discovered and embedded in the data island.

    The mixed fixture has:
    - docs/adr/0001-notes/ → notes_dir for ADR-0001
    - docs/adr/0002-x-research.md → research_file for ADR-0002
    - docs/adr/README.md → readme in corpus_support_refs
    """
    r = EXPLORER.publish_explorer(FIXTURE, destination=tmp_path, mode="bounded")
    assert r["status"] == "ok", r.get("error")
    html = pathlib.Path(r["path"]).read_text(encoding="utf-8")
    data = _extract_json_data(html)

    # Per-record support refs.
    records = {rec["id"]: rec for rec in data["records"]}
    adr1_refs = records.get("ADR-0001", {}).get("support_refs", [])
    assert any(sr["kind"] == "notes_dir" for sr in adr1_refs), (
        f"ADR-0001 should have a notes_dir support ref; got {adr1_refs!r}"
    )
    adr2_refs = records.get("ADR-0002", {}).get("support_refs", [])
    assert any(sr["kind"] == "research_file" for sr in adr2_refs), (
        f"ADR-0002 should have a research_file support ref; got {adr2_refs!r}"
    )

    # Corpus-level support refs (README.md).
    corpus_refs = data.get("corpus_support_refs", [])
    readme_refs = [sr for sr in corpus_refs if sr.get("kind") == "readme"]
    assert readme_refs, f"corpus_support_refs should include a readme; got {corpus_refs!r}"
    readme_paths = [sr["path"] for sr in readme_refs]
    assert any("README.md" in p for p in readme_paths), (
        f"README.md path expected in corpus refs; got {readme_paths!r}"
    )


def test_support_refs_paths_are_inert_strings(tmp_path: pathlib.Path) -> None:
    """ADV-6: Support ref paths are plain strings, not clickable links."""
    r = EXPLORER.publish_explorer(FIXTURE, destination=tmp_path, mode="bounded")
    assert r["status"] == "ok", r.get("error")
    html = pathlib.Path(r["path"]).read_text(encoding="utf-8")
    data = _extract_json_data(html)
    all_refs: list = list(data.get("corpus_support_refs", []))
    for rec in data["records"]:
        all_refs.extend(rec.get("support_refs", []))
    for sr in all_refs:
        # Each support ref must have path (str) and kind (str).
        assert isinstance(sr.get("path"), str), f"support ref path must be a string; got {sr!r}"
        assert isinstance(sr.get("kind"), str), f"support ref kind must be a string; got {sr!r}"
        # No URL field — inert references only.
        assert "url" not in sr, f"support refs must not have a url field; got {sr!r}"


def test_provenance_not_interpolated_in_html(tmp_path: pathlib.Path) -> None:
    """ADV-13/SEC-3: Provenance is not interpolated into the HTML template.

    The provenance must be in the data island only (D.provenance) and rendered
    into #prov-pre via textContent, never raw-interpolated into the HTML body.
    """
    r = EXPLORER.publish_explorer(FIXTURE, destination=tmp_path)
    assert r["status"] == "ok", r.get("error")
    html = pathlib.Path(r["path"]).read_text(encoding="utf-8")

    # The provenance <pre> must be empty in the static HTML (JS fills it).
    assert 'id="prov-pre"' in html, "prov-pre element must be present"
    # The raw provenance JSON key 'generated_at' must only appear inside the
    # data island script block, not anywhere else in the HTML.
    data_m = re.search(
        r'<script type="application/json" id="nav-data">(.*?)</script>',
        html,
        re.DOTALL,
    )
    assert data_m, "nav-data block not found"
    data_block = data_m.group(1)
    # Strip the data island, remaining HTML must not contain provenance keys.
    html_without_data = html.replace(data_block, "")
    assert "generated_at" not in html_without_data, (
        "provenance key 'generated_at' must not be interpolated into the HTML "
        "outside the data island; render via textContent from D.provenance instead"
    )


def test_status_filter_options_use_display_value(tmp_path: pathlib.Path) -> None:
    """ADV-8/SEC-2: Status filter option labels use display_value, not raw_value.

    The JS must build status <option> elements with o.textContent = display_value
    so bidi-corrupted or hostile status values show their escaped form.
    """
    js = _extract_runtime_js(_html(tmp_path, fixture=FIXTURE))
    # The JS must read display_value when building status options.
    assert "display_value" in js, (
        "JS runtime must reference 'display_value' for status filter options"
    )
    # Must not set both value and textContent to the raw_value (old pattern).
    assert "o.value=o.textContent=s" not in js, (
        "status filter must use display_value for option text, not raw_value"
    )


def test_hostile_export_csp_no_script_execution(tmp_path: pathlib.Path) -> None:
    """ADV-8/SEC-2: Hostile fixture export has a valid CSP that blocks script injection."""
    hostile_fixture = HERE / "fixtures/negative/hostile"
    r = EXPLORER.publish_explorer(hostile_fixture, destination=tmp_path)
    assert r["status"] == "ok", r.get("error")
    html = pathlib.Path(r["path"]).read_text(encoding="utf-8")
    # CSP must be present — both patterns are equivalent; match the canonical form.
    csp_m = re.search(r'<meta http-equiv="Content-Security-Policy" content="([^"]*)"', html)
    assert csp_m, "CSP meta tag not found in hostile export"
    csp = csp_m.group(1)
    # script-src must exist in the CSP.
    assert "script-src" in csp, f"CSP must include script-src directive; got {csp!r}"
    # script-src must not allow 'unsafe-inline'.
    assert "unsafe-inline" not in csp.split("script-src")[1].split(";")[0], (
        "CSP script-src must not allow 'unsafe-inline'"
    )
    # The title tag must not contain raw script tags.
    title_m = re.search(r"<title>(.*?)</title>", html, re.DOTALL)
    assert title_m, "HTML must contain a <title> element"
    assert "<script>" not in title_m.group(1).lower(), (
        "title must not contain raw script tag from hostile record"
    )


def test_bidi_export_data_island_contains_display_value(tmp_path: pathlib.Path) -> None:
    """SEC-2: Bidi fixture export encodes display_value with escaped bidi controls."""
    bidi_fixture = HERE / "fixtures/negative/bidi"
    r = EXPLORER.publish_explorer(bidi_fixture, destination=tmp_path)
    assert r["status"] == "ok", r.get("error")
    html = pathlib.Path(r["path"]).read_text(encoding="utf-8")
    data = _extract_json_data(html)
    records = data.get("records", [])
    assert records, "bidi export must have at least one record"
    lc = records[0].get("lifecycle", {})
    # display_value must be present and different from raw_value when bidi is present.
    raw = lc.get("raw_value", "")
    display = lc.get("display_value", "")
    # Raw value must preserve the bidi control (U+202E).
    assert "‮" in raw, f"raw_value must preserve U+202E bidi override; got {raw!r}"
    # Display value must not contain the raw bidi override character.
    assert "‮" not in display, f"display_value must escape U+202E bidi override; got {display!r}"


def test_trust_labels_in_own_elements_js(tmp_path: pathlib.Path) -> None:
    """ADV-8: JS runtime uses separate span elements for trust labels, not mixed text nodes."""
    js = _extract_runtime_js(_html(tmp_path, fixture=FIXTURE))
    # The new JS creates a span with class trust-label for every trust class label.
    assert "trust-label" in js, (
        "JS runtime must render trust labels in their own .trust-label span elements"
    )
    # Must not set the entire rel-item content via a single textContent assignment
    # that mixes the trust label with the record data.
    assert "li.textContent='['+r.trust_class" not in js, (
        "trust label must not be mixed with record data in a single textContent assignment"
    )


def test_normalize_assertion_function_output() -> None:
    """ADV-5/QE-3: _normalize_assertion produces the expected tuple structure."""
    fn = EXPLORER._normalize_assertion
    # Dict with raw_value.
    result = fn({"from": "A", "to": "B", "raw_value": "text"})
    assert result["trust_class"] == "navigation_only"
    assert result["resolution_state"] == "caller_asserted"
    assert result["raw_value"] == "text"
    assert result["from"] == "A"
    assert result["to"] == "B"
    # Non-dict.
    result2 = fn("bare string")
    assert result2["trust_class"] == "navigation_only"
    assert result2["raw_value"] == "bare string"
    # Dict without raw_value but with text.
    result3 = fn({"text": "fallback text"})
    assert result3["raw_value"] == "fallback text"


# ── T7 stage 2a: ITEM 2 — safe Markdown renderer has no forbidden APIs ────────


def test_markdown_renderer_no_unsafe_apis(tmp_path: pathlib.Path) -> None:
    """The inlined JS runtime must not contain forbidden DOM-mutation APIs."""
    html = _html(tmp_path)
    js = _extract_runtime_js(html)
    forbidden = [
        "innerHTML",
        "outerHTML",
        "insertAdjacentHTML",
        "eval(",
        "Function(",
        "setAttribute('on",
        'setAttribute("on',
    ]
    for api in forbidden:
        assert api not in js, f"Forbidden API {api!r} found in inlined JS runtime"


# ── T7 stage 2a: ITEM 3 — CSP has all required directives ────────────────────


def test_csp_all_directives_present(tmp_path: pathlib.Path) -> None:
    """CSP must carry all five required directives including base-uri and form-action."""
    html = _html(tmp_path)
    m = re.search(r'http-equiv="Content-Security-Policy"[^>]*content="([^"]*)"', html)
    assert m, "CSP meta tag not found"
    csp = m.group(1)
    required = [
        "default-src 'none'",
        "script-src 'sha256-",
        "style-src 'unsafe-inline'",
        "base-uri 'none'",
        "form-action 'none'",
    ]
    for directive in required:
        assert directive in csp, f"CSP directive {directive!r} missing; full CSP: {csp!r}"


# ── T7 stage 2a: ITEM 4 — superseded_by derives from checked relationships ───


def test_superseded_by_from_checked_only(tmp_path: pathlib.Path) -> None:
    """Records must carry superseded_by derived from checked relationships only."""
    data = _extract_json_data(_html(tmp_path))
    rec_by_id = {r["id"]: r for r in data["records"]}

    # ADR-0001 is superseded in part by ADR-0020 in scope D3 (checked).
    r1 = rec_by_id["ADR-0001"]
    sup1 = r1.get("superseded_by", [])
    assert len(sup1) == 1, f"ADR-0001 superseded_by expected 1 entry, got {sup1!r}"
    assert sup1[0]["by"] == "ADR-0020", f"ADR-0001 superseder: {sup1[0]!r}"
    assert sup1[0]["partial"] is True, f"ADR-0001 must be partial: {sup1[0]!r}"
    assert sup1[0]["scope"] == ["D3"], f"ADR-0001 scope must be [D3]: {sup1[0]!r}"

    # ADR-0002 is superseded (fully) by ADR-0003 (checked — both sides agree).
    r2 = rec_by_id["ADR-0002"]
    sup2 = r2.get("superseded_by", [])
    assert len(sup2) == 1, f"ADR-0002 superseded_by expected 1 entry, got {sup2!r}"
    assert sup2[0]["by"] == "ADR-0003", f"ADR-0002 superseder: {sup2[0]!r}"
    assert sup2[0]["partial"] is False, f"ADR-0002 must be full supersession: {sup2[0]!r}"

    # ADR-0003 supersedes others; it is not itself superseded.
    r3 = rec_by_id["ADR-0003"]
    assert r3.get("superseded_by", []) == [], (
        f"ADR-0003 must have empty superseded_by; got {r3.get('superseded_by')!r}"
    )


def test_csp_provenance_not_in_static_html(tmp_path: pathlib.Path) -> None:
    """SEC-3: Provenance fields must not appear verbatim in the static HTML outside the data island."""
    r = EXPLORER.publish_explorer(FIXTURE, destination=tmp_path)
    assert r["status"] == "ok", r.get("error")
    html = pathlib.Path(r["path"]).read_text(encoding="utf-8")
    # Strip the data island entirely.
    data_m = re.search(
        r'(<script type="application/json" id="nav-data">)(.*?)(</script>)',
        html,
        re.DOTALL,
    )
    assert data_m, "nav-data block not found"
    html_without_data = html[: data_m.start(2)] + html[data_m.end(2) :]
    # The word "untrusted_data" is a provenance-only key and must not appear in static HTML.
    assert "untrusted_data" not in html_without_data, (
        "provenance key 'untrusted_data' must not be interpolated into static HTML; "
        "use textContent rendering from D.provenance instead"
    )


# ── T7 stage 3: lineage.js security checks (AC-0026) ─────────────────────────


def _extract_lineage_js(html: str) -> str:
    """Extract the inlined lineage.js content from the script block."""
    m = re.search(r"<script>(.*?)</script>", html, re.DOTALL)
    assert m, "script block not found in HTML"
    # lineage.js defines 'var Lineage='; extract its section from the script block
    return m.group(1)


def test_lineage_js_no_forbidden_strings(tmp_path: pathlib.Path) -> None:
    """AC-0026: lineage.js must not contain forbidden DOM-mutation or SVG-injection APIs."""
    html = _html(tmp_path)
    js = _extract_lineage_js(html)
    # These strings are forbidden in the inlined script.
    # The comment check targets code patterns, not comment text — so we look for the
    # actual API call patterns that would constitute policy violations.
    forbidden_patterns = [
        ".innerHTML",
        ".insertAdjacentHTML",
        ".outerHTML",
        "eval(",
        "Function(",
        "foreignObject",
        "<use",
        "xlink:href",
    ]
    for pat in forbidden_patterns:
        assert pat not in js, (
            f"Forbidden pattern {pat!r} found in inlined script (lineage.js or runtime)"
        )


def test_lineage_js_defines_lineage_var(tmp_path: pathlib.Path) -> None:
    """AC-0026: lineage.js is inlined and defines the Lineage global."""
    html = _html(tmp_path)
    js = _extract_lineage_js(html)
    assert "var Lineage=" in js or "var Lineage =" in js, (
        "Lineage global not found in inlined script — lineage.js may not be included"
    )


def test_lineage_js_csp_hash_matches_script_block(tmp_path: pathlib.Path) -> None:
    """AC-0026: CSP sha256 hash in the meta tag matches the actual inlined script block."""
    import base64
    import hashlib

    r = EXPLORER.publish_explorer(FIXTURE, destination=tmp_path)
    assert r["status"] == "ok", r.get("error")
    html = pathlib.Path(r["path"]).read_text(encoding="utf-8")
    # Extract CSP hash from <meta> tag
    csp_m = re.search(r"http-equiv=\"Content-Security-Policy\"[^>]*content=\"([^\"]+)\"", html)
    assert csp_m, "CSP meta tag not found"
    csp = csp_m.group(1)
    hash_m = re.search(r"'sha256-([^']+)'", csp)
    assert hash_m, f"sha256 hash not found in CSP: {csp!r}"
    csp_hash = hash_m.group(1)
    # Extract the actual script block content
    script_m = re.search(r"<script>(.*?)</script>", html, re.DOTALL)
    assert script_m, "script block not found"
    script_content = script_m.group(1)
    # Compute expected hash
    digest = hashlib.sha256(script_content.encode("utf-8")).digest()
    expected_hash = base64.b64encode(digest).decode("ascii")
    assert csp_hash == expected_hash, (
        f"CSP hash {csp_hash!r} does not match computed hash {expected_hash!r} "
        "of the inlined script block — lineage.js may have been added without "
        "recomputing the hash"
    )


def test_lineage_js_uses_createelementns(tmp_path: pathlib.Path) -> None:
    """AC-0026: lineage.js builds SVG via createElementNS, not innerHTML."""
    html = _html(tmp_path)
    js = _extract_lineage_js(html)
    assert "createElementNS" in js, (
        "createElementNS not found in inlined script — SVG must be built via createElementNS"
    )


# ══════════════════════════════════════════════════════════════════════════════
# SEC-5 / ADV-17: _parse_github_identity checks parsed host against allowlist
# ══════════════════════════════════════════════════════════════════════════════


def test_parse_github_identity_non_allowlisted_host_returns_none() -> None:
    """_parse_github_identity returns None for a host not in _SOURCE_HOST_ALLOWLIST.

    The host is parsed from the URL and compared against the allowlist;
    it is not hardcoded. A gitlab.com or bitbucket.org URL must be refused.

    Mutation: hardcoding 'github.com' without an allowlist check would pass
    github.com URLs but not correctly enforce the allowlist boundary.
    """
    # HTTPS non-allowlisted host.
    result = EXPLORER._parse_github_identity("https://gitlab.com/owner/repo.git")
    assert result is None, f"gitlab.com is not in allowlist; expected None, got {result!r}"
    # SSH non-allowlisted host.
    result2 = EXPLORER._parse_github_identity("git@bitbucket.org:owner/repo.git")
    assert result2 is None, f"bitbucket.org is not in allowlist; expected None, got {result2!r}"
    # Allowlisted host still works.
    result3 = EXPLORER._parse_github_identity("https://github.com/owner/repo.git")
    assert result3 == ("owner", "repo"), f"github.com must be accepted; got {result3!r}"


# ══════════════════════════════════════════════════════════════════════════════
# ADV-9 / SEC-4: Directory-identity swap test
# ══════════════════════════════════════════════════════════════════════════════


@pytest.mark.skipif(os.name != "posix", reason="POSIX-only dir-swap test")
@pytest.mark.parametrize("swap_phase", ["open", "os.link"])
def test_directory_swap_between_validation_and_publish_refused(
    tmp_path: pathlib.Path, swap_phase: str
) -> None:
    """A directory swapped after validation is refused with publish_failed and
    leaves no file of any name in either directory.

    Phase "open": the swap happens right after the directory descriptor opens,
    before the temporary file exists. Phase "os.link": the swap happens after
    the temporary file is written. Publication works relative to the validated
    directory's descriptor, so at "os.link" the link itself would succeed (into
    the renamed, validated directory); only the pre-link path check refuses it,
    so this case fails when that check is a no-op. The temporary file is removed
    through the same descriptor, so nothing is left behind.
    """
    import unittest.mock as _mock

    real_dir = tmp_path / "dest"
    real_dir.mkdir()
    swapped_dir = tmp_path / "dest_original"
    swap_done = {"done": False}

    real_check_dir_identity = EXPLORER._check_dir_identity

    def swapping_check(dir_path, expected, phase):  # type: ignore[no-untyped-def]
        if phase == swap_phase and not swap_done["done"]:
            swap_done["done"] = True
            # Rename the real directory away and put a new one in its place.
            real_dir.rename(swapped_dir)
            real_dir.mkdir()  # New directory — different inode.
        real_check_dir_identity(dir_path, expected, phase)

    real_os_open = os.open
    temp_files_created: list[str] = []

    def recording_open(path, flags, *args, **kwargs):  # type: ignore[no-untyped-def]
        if str(path).endswith(".tmp"):
            temp_files_created.append(str(path))
        return real_os_open(path, flags, *args, **kwargs)

    with (
        _mock.patch.object(EXPLORER, "_check_dir_identity", side_effect=swapping_check),
        _mock.patch.object(EXPLORER.os, "open", side_effect=recording_open),
    ):
        result = EXPLORER.publish_explorer(
            FIXTURE,
            destination=real_dir,
            name="swapped.html",
            mode="bounded",
        )

    assert result["status"] == "error", f"directory swap must cause a refusal; got {result!r}"
    assert swap_done["done"], "the swap must have happened at the named phase"
    assert result["error"]["code"] == "publish_failed", result
    assert not list(real_dir.iterdir()), list(real_dir.iterdir())
    assert not list(swapped_dir.iterdir()), list(swapped_dir.iterdir())
    if swap_phase == "open":
        # The open-phase check must refuse before any temporary file exists.
        assert temp_files_created == [], temp_files_created


def test_directory_swap_before_descriptor_open_refused(tmp_path: pathlib.Path) -> None:
    """A directory swapped after validation but before its descriptor opens is
    refused by the descriptor identity comparison, before the path check runs
    and before any temporary file exists."""
    import unittest.mock as _mock

    real_dir = tmp_path / "dest"
    real_dir.mkdir()
    swapped_dir = tmp_path / "dest_original"
    real_os_open = os.open
    calls = {"swapped": False, "temp": 0}

    def swapping_open(path, flags, *args, **kwargs):  # type: ignore[no-untyped-def]
        if str(path) == str(real_dir) and not calls["swapped"]:
            calls["swapped"] = True
            real_dir.rename(swapped_dir)
            real_dir.mkdir()
        if str(path).endswith(".tmp"):
            calls["temp"] += 1
        return real_os_open(path, flags, *args, **kwargs)

    path_check = _mock.MagicMock(wraps=EXPLORER._check_dir_identity)
    with (
        _mock.patch.object(EXPLORER.os, "open", side_effect=swapping_open),
        _mock.patch.object(EXPLORER, "_check_dir_identity", path_check),
    ):
        result = EXPLORER.publish_explorer(
            FIXTURE, destination=real_dir, name="swapped.html", mode="bounded"
        )

    assert calls["swapped"], "the swap must have happened before the descriptor opened"
    assert result["status"] == "error", result
    assert result["error"]["code"] == "publish_failed", result
    assert path_check.call_count == 0, "the descriptor comparison must refuse first"
    assert calls["temp"] == 0
    assert not list(real_dir.iterdir()), list(real_dir.iterdir())
    assert not list(swapped_dir.iterdir()), list(swapped_dir.iterdir())


# ══════════════════════════════════════════════════════════════════════════════
# ADV-15/SEC-2: display_source, display_path, display_from, display_to (Python)
# ══════════════════════════════════════════════════════════════════════════════


def test_display_source_present_on_records(tmp_path: pathlib.Path) -> None:
    """Every record in the export carries display_source (escaped source path).

    An RLM or ALM in a source basename is shown as [U+XXXX] in display_source
    but preserved as-is in source.
    """
    html = _html(tmp_path, mode="bounded")
    data = _extract_json_data(html)
    for rec in data.get("records", []):
        assert "display_source" in rec, f"record {rec.get('id')} missing display_source"
        # display_source must be a string.
        assert isinstance(rec["display_source"], str), (
            f"display_source must be a string; got {type(rec['display_source'])!r}"
        )


def test_display_path_present_on_support_refs(tmp_path: pathlib.Path) -> None:
    """Every support reference carries display_path (escaped path).

    display_path must be present on per-record support_refs and corpus_support_refs.
    """
    r = EXPLORER.publish_explorer(FIXTURE, destination=tmp_path, mode="bounded")
    assert r["status"] == "ok", r.get("error")
    html = pathlib.Path(r["path"]).read_text(encoding="utf-8")
    data = _extract_json_data(html)
    for rec in data.get("records", []):
        for sref in rec.get("support_refs", []):
            assert "display_path" in sref, (
                f"support_ref for {rec.get('id')} missing display_path: {sref!r}"
            )
    for sref in data.get("corpus_support_refs", []):
        assert "display_path" in sref, f"corpus_support_ref missing display_path: {sref!r}"


def test_assertion_tuple_has_display_from_display_to(tmp_path: pathlib.Path) -> None:
    """Caller assertion tuples carry display_from and display_to.

    An RLM or ALM in an assertion endpoint is shown as [U+XXXX] in the
    display_from/display_to field but preserved as-is in 'from'/'to'.
    """
    bidi_from = "ADR‮0001"  # RLO before "0001"
    bidi_to = "RFC-​0050"  # ZWS in the middle
    r = EXPLORER.publish_explorer(
        FIXTURE,
        destination=tmp_path,
        assertions=[{"from": bidi_from, "to": bidi_to, "text": "informs"}],
    )
    assert r["status"] == "ok", r.get("error")
    html = pathlib.Path(r["path"]).read_text(encoding="utf-8")
    data = _extract_json_data(html)
    nav_only = [
        rel for rel in data.get("relationships", []) if rel.get("trust_class") == "navigation_only"
    ]
    assert nav_only, "no navigation_only relationship in data island"
    a = nav_only[0]
    assert "display_from" in a, f"display_from missing from assertion tuple: {a!r}"
    assert "display_to" in a, f"display_to missing from assertion tuple: {a!r}"
    # Raw values are preserved unchanged.
    assert a["from"] == bidi_from, f"'from' must preserve bidi control; got {a['from']!r}"
    assert a["to"] == bidi_to, f"'to' must preserve bidi control; got {a['to']!r}"
    # Display values must not contain the raw bidi controls.
    assert "‮" not in a["display_from"], (
        f"display_from must escape U+202E; got {a['display_from']!r}"
    )
    assert "​" not in a["display_to"], f"display_to must escape U+200B; got {a['display_to']!r}"


# ══════════════════════════════════════════════════════════════════════════════
# ADV-5: Unresolved claims for unparseable superseded-by entries in export
# ══════════════════════════════════════════════════════════════════════════════


def test_unresolved_claims_from_unparseable_superseded_by(
    tmp_path: pathlib.Path,
) -> None:
    """An unparseable superseded-by entry produces an unresolved_claims entry.

    An unparseable entry (e.g. 'EXTERNAL-SYSTEM') has to=None in the relationship.
    The declaring record must receive an unresolved_claims entry carrying the
    raw_value and display_value regardless of whether 'to' is set.
    """
    corpus_dir = tmp_path / "corpus"
    corpus_dir.mkdir()
    adr_dir = corpus_dir / "docs" / "adr"
    adr_dir.mkdir(parents=True)
    (adr_dir / "0001-alpha.md").write_text(
        "# ADR-0001: Unresolved claim test\n\n"
        "- **Status:** Accepted\n"
        "- **Supersedes:** none\n"
        "- **Supersedes in part:** none\n"
        "- **Superseded by:** EXTERNAL-SYSTEM-V2\n"
        "- **Superseded in part:** none\n\n"
        "## Decision\n\nBody.\n",
        encoding="utf-8",
    )
    # Destination is a sibling of corpus — outside the corpus root.
    dest = tmp_path / "dest"
    dest.mkdir()
    r = EXPLORER.publish_explorer(corpus_dir, destination=dest, mode="bounded")
    assert r["status"] == "ok", f"export failed: {r!r}"
    html = pathlib.Path(r["path"]).read_text(encoding="utf-8")
    data = _extract_json_data(html)
    records = {rec["id"]: rec for rec in data.get("records", [])}
    assert "ADR-0001" in records, "ADR-0001 missing from export"
    claims = records["ADR-0001"].get("unresolved_claims", [])
    assert claims, (
        f"ADR-0001 with unparseable superseded-by must have unresolved_claims; got {claims!r}"
    )
    claim = claims[0]
    # The claim carries raw_value and display_value; 'by' may be None.
    assert "raw_value" in claim, f"unresolved_claims entry must carry raw_value; got {claim!r}"
    assert "EXTERNAL-SYSTEM-V2" in claim["raw_value"], (
        f"raw_value must contain the unparseable text; got {claim['raw_value']!r}"
    )


# ══════════════════════════════════════════════════════════════════════════════
# ADV-2/3: Assertion parity between query context and HTML data island
# ══════════════════════════════════════════════════════════════════════════════


def test_assertion_tuple_parity_query_vs_export(tmp_path: pathlib.Path) -> None:
    """Same assertion input produces identical non-display tuples in query and export.

    The assertion tuple that _op_context builds must match the one embedded
    in the HTML data island (excluding display_* fields).
    """
    assertion = {"from": "ADR-0001", "to": "ADR-0002", "text": "informs design"}

    # Query side.
    q = NAV.run_query(
        FIXTURE,
        {
            "operation": "context",
            "selectors": [{"kind": "ADR"}],
            "assertions": [assertion],
        },
    )
    assert q["status"] == "ok", f"context query failed: {q!r}"
    query_nav = [
        r for r in q.get("relationships", []) if r.get("trust_class") == "navigation_only"
    ]
    assert query_nav, "query context must include navigation_only relationship"
    q_tuple = {k: v for k, v in query_nav[0].items() if not k.startswith("display_")}

    # Export side.
    r = EXPLORER.publish_explorer(
        FIXTURE,
        destination=tmp_path,
        assertions=[assertion],
        mode="bounded",
    )
    assert r["status"] == "ok", f"export failed: {r!r}"
    html = pathlib.Path(r["path"]).read_text(encoding="utf-8")
    data = _extract_json_data(html)
    export_nav = [
        rel for rel in data.get("relationships", []) if rel.get("trust_class") == "navigation_only"
    ]
    assert export_nav, "export data island must include navigation_only relationship"
    e_tuple = {k: v for k, v in export_nav[0].items() if not k.startswith("display_")}

    # Tuples must match on all non-display fields.
    assert q_tuple == e_tuple, (
        f"query and export assertion tuples differ:\n  query:  {q_tuple}\n  export: {e_tuple}"
    )


# ══════════════════════════════════════════════════════════════════════════════
# ADV-11: Export refusal error shape (limits/observed)
# ══════════════════════════════════════════════════════════════════════════════


def test_export_over_budget_error_has_limits_observed(tmp_path: pathlib.Path) -> None:
    """An over-budget export refusal carries limits and observed with the budget numbers."""
    import unittest.mock as _mock

    # Patch BUDGET_BYTES to a very small value so the export exceeds it.
    with _mock.patch.object(EXPLORER, "BUDGET_BYTES", 1):
        r = EXPLORER.publish_explorer(FIXTURE, destination=tmp_path)

    assert r["status"] == "error", f"over-budget export must be refused; got {r!r}"
    assert r["error"]["code"] == "over_budget", f"expected over_budget; got {r['error']['code']!r}"
    assert "limits" in r["error"], "over_budget error must carry 'limits'"
    assert "observed" in r["error"], "over_budget error must carry 'observed'"
    assert "budget_bytes" in r["error"]["limits"], "limits must carry budget_bytes"
    assert "estimated_bytes" in r["error"]["observed"], "observed must carry estimated_bytes"


def test_export_invalid_destination_error_has_limits_observed(
    tmp_path: pathlib.Path,
) -> None:
    """An invalid destination refusal carries limits and observed."""
    # Try to publish inside the repository worktree (always refused).
    r = EXPLORER.publish_explorer(
        FIXTURE,
        destination=FIXTURE,  # inside the worktree
        name="test.html",
    )
    assert r["status"] == "error", f"invalid destination must be refused; got {r!r}"
    assert r["error"]["code"] == "invalid_destination", (
        f"expected invalid_destination; got {r['error']['code']!r}"
    )
    assert "limits" in r["error"], "error must carry 'limits'"
    assert "observed" in r["error"], "error must carry 'observed'"


@pytest.mark.parametrize(
    ("remote_branches", "expected"),
    [("  upstream/main\n  fork/feature", "branch_latest"), ("  origin/main", "commit_pinned")],
    ids=["only-on-other-remote", "on-origin"],
)
def test_commit_pinned_requires_head_on_origin(remote_branches: str, expected: str) -> None:
    """The link points at origin, so a commit-pinned link needs HEAD on an origin
    tracking branch; a HEAD only on another remote gets the may-be-newer label."""
    import unittest.mock as _mock

    def mock_git(args: list, cwd: str, timeout: int = 5) -> str | None:
        if args == ["config", "--get", "remote.origin.url"]:
            return "https://github.com/owner/repo.git"
        if args == ["rev-parse", "HEAD"]:
            return "e" * 40
        if args[0] == "status":
            return ""
        if args[:3] == ["branch", "-r", "--contains"]:
            return remote_branches
        return None

    with (
        _mock.patch.object(EXPLORER, "_run_git", side_effect=mock_git),
        _mock.patch.object(EXPLORER, "_git_root_matches", return_value=True),
    ):
        links = EXPLORER._build_source_links(FIXTURE, ["docs/adr/0001-alpha.md"])
    assert links["docs/adr/0001-alpha.md"]["kind"] == expected


def test_export_register_refusal_carries_the_query_limit(tmp_path: pathlib.Path) -> None:
    """An oversized register refuses the export with the same limit the query
    reports, max_register_bytes."""
    import shutil

    root = tmp_path / "corpus"
    shutil.copytree(FIXTURE, root)
    reg = root / "docs" / "product" / "findings" / "rfc-candidates.md"
    reg.parent.mkdir(parents=True, exist_ok=True)
    reg.write_text("| a |\n| - |\n" + "| x |\n" * 700_000, encoding="utf-8")
    out = tmp_path / "out"
    out.mkdir()
    result = EXPLORER.publish_explorer(root, destination=out, name="r.html", mode="bounded")
    query = NAV.run_query(root, {"operation": "summary"})
    assert result["status"] == "error" and query["status"] == "error", (result, query)
    assert result["error"]["code"] == query["error"]["code"] == "input_too_large"
    assert result["error"]["limits"] == query["error"]["limits"], (result, query)


def test_bounded_export_keeps_a_multi_line_header_value(tmp_path: pathlib.Path) -> None:
    """AC-0014: a bounded export carries a wrapped header value exactly, line
    breaks and the continuation's own indentation included."""
    corpus = tmp_path / "corpus"
    adr = corpus / "docs" / "adr"
    adr.mkdir(parents=True)
    (adr / "0001-wrapped.md").write_text(
        "# ADR-0001: Wrapped\n\n- **Status:** Accepted\n"
        "- **Related:** ADR-0002 (first line\n  continues here)\n\n## Context\n\nx\n",
        encoding="utf-8",
    )
    out = tmp_path / "out"
    out.mkdir()
    result = EXPLORER.publish_explorer(corpus, destination=out, name="b.html", mode="bounded")
    assert result["status"] == "ok", result.get("error")
    data = _extract_json_data(pathlib.Path(result["path"]).read_text(encoding="utf-8"))
    fields = {f["label"]: f["raw_value"] for f in data["records"][0]["header_fields"]}
    assert fields["Related"] == "ADR-0002 (first line\n  continues here)", fields
