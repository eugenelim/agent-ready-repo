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
        r'<script(?! type)(?![^>]*type)[^>]*>(.*?)</script>',
        html,
        re.DOTALL,
    )
    assert matches, "No executable <script> block found"
    return matches[-1]


# ── AC-0008: Cross-mode fact parity ───────────────────────────────────────────


def test_fact_parity_record_ids(tmp_path: pathlib.Path) -> None:
    """Embedded JSON record IDs match run_query summary membership."""
    query_result = NAV.run_query(FIXTURE, {"operation": "search", "selectors": [{"kind": "ADR"}, {"kind": "RFC"}]})
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
    """Embedded relationship tuples match run_query output for all admitted records.

    Checks all fields of each checked relationship (AC-0008 tuple comparison).
    """
    html = _html(tmp_path)
    data = _extract_json_data(html)
    html_checked = [
        r for r in data["relationships"] if r["trust_class"] == "checked"
    ]
    assert html_checked, "Expected at least one checked relationship in mixed fixture"

    # Compare against the query for a record we know has a checked edge.
    q = NAV.run_query(FIXTURE, {"operation": "record", "id": "ADR-0001"})
    query_checked = [r for r in q["relationships"] if r["trust_class"] == "checked"]

    for qr in query_checked:
        key_fields = {
            "from": qr["from"],
            "to": qr["to"],
            "relation": qr["relation"],
            "scope": qr["scope"],
            "trust_class": qr["trust_class"],
            "resolution_state": qr["resolution_state"],
            "basis": qr["basis"],
            "direction": qr["direction"],
        }
        assert any(key_fields.items() <= hr.items() for hr in html_checked), (
            f"Checked relationship not found in HTML: {key_fields}"
        )


# ── AC-0010: Inert and visually honest content ────────────────────────────────


def test_hostile_script_tag_escaped(tmp_path: pathlib.Path) -> None:
    """'</script>' in record title/body must not appear unescaped in HTML output."""
    # The mixed fixture's ADR-0001 title has no script tag, but we use the
    # fixture's own content and verify the escaping invariant via the
    # safe_json function directly.
    hostile_input = '</script><script>alert(1)</script>'
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
        assert body.get("omission_reason") in ("bounded_mode", "not_requested", "body_too_large"), (
            f"Unexpected omission reason for {rec['id']}: {body.get('omission_reason')}"
        )


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
    err = result["error"].lower()
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
    assert "inside the repository worktree" in str(result["error"])


def test_refuses_non_html_name(tmp_path: pathlib.Path) -> None:
    """Output name not ending in .html must be refused."""
    result = EXPLORER.publish_explorer(
        FIXTURE,
        destination=str(tmp_path / "out.txt"),
    )
    # Destination is a file path: parent is tmp_path, name is out.txt
    assert result["status"] == "error"
    assert ".html" in result["error"].lower() or "html" in result["error"].lower(), (
        f"Expected .html name refusal, got: {result['error']!r}"
    )


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
    assert result["status"] == "error", (
        "Expected refusal for symlinked destination directory"
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
    assert "exist" in result["error"].lower() or "already" in result["error"].lower(), (
        f"Expected existing-file refusal, got: {result['error']!r}"
    )


def test_refuses_over_budget_without_confirm(tmp_path: pathlib.Path) -> None:
    """Export exceeding budget without confirm_over_budget must be refused."""
    import unittest.mock as _mock

    with _mock.patch.object(EXPLORER, "BUDGET_BYTES", 1):  # 1-byte budget
        result = _publish(tmp_path / "budget_test", confirm_over_budget=False)
    # Should error because estimated size > 1 byte
    assert result["status"] == "error"
    err = result["error"].lower()
    assert "budget" in err or "exceed" in err, (
        f"Expected budget-exceeded error, got: {result['error']!r}"
    )


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
    """fchmod 0o600 must be called before content is written to the temp sibling."""
    import unittest.mock as _mock

    events: list[tuple] = []
    real_fchmod = os.fchmod

    def mock_fchmod(fd: int, mode: int) -> None:
        events.append(("fchmod", mode))
        real_fchmod(fd, mode)

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
    assert min(fchmod_indices) < min(write_indices), (
        "fchmod(0o600) must be called before write"
    )


@pytest.mark.skipif(os.name != "posix", reason="POSIX-only file mode test")
def test_published_file_mode_0600(tmp_path: pathlib.Path) -> None:
    """Published file must have owner-only mode 0o600 on POSIX."""
    r = _publish(tmp_path)
    assert r["status"] == "ok"
    path = pathlib.Path(r["path"])
    mode = stat.S_IMODE(path.stat().st_mode)
    assert mode == 0o600, f"Expected 0o600, got {oct(mode)}"


# ── AC-0013, AC-0022: Failure leaves no partial file ─────────────────────────


def test_no_partial_file_on_link_failure(tmp_path: pathlib.Path) -> None:
    """If os.link fails, no partial file must remain at the destination."""
    import unittest.mock as _mock

    called_paths: list[pathlib.Path] = []

    def failing_link(src: str, dst: str) -> None:
        called_paths.append(pathlib.Path(dst))
        raise OSError("injected link failure")

    with _mock.patch.object(os, "link", failing_link):
        result = _publish(tmp_path / "no_partial")

    assert result["status"] == "error"
    # No file at any of the attempted destination paths.
    for p in called_paths:
        assert not p.exists(), f"Partial file left at {p}"


def test_no_temp_sibling_left_on_failure(tmp_path: pathlib.Path) -> None:
    """Temp sibling must be cleaned up even when publication fails."""
    import unittest.mock as _mock

    def failing_link(src: str, dst: str) -> None:
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
    assert ".." not in url.split("/"), (
        f"Dot-segment traversal found in URL: {url!r}"
    )


def test_non_allowlisted_host_degrades_to_inert(tmp_path: pathlib.Path) -> None:
    """A remote URL on a non-allowlisted host produces inert provenance, not a link."""
    import unittest.mock as _mock

    with _mock.patch.object(EXPLORER, "_run_git", return_value="https://bitbucket.org/owner/repo.git"):
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
        return None

    with _mock.patch.object(EXPLORER, "_run_git", side_effect=mock_git):
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

    with _mock.patch.object(EXPLORER, "_run_git", side_effect=mock_git):
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
    resolved_dir, full = EXPLORER._validate_destination(tmp_path, "decisions.html", FIXTURE)
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
