"""VI-1702 through VI-1705 tests for the delivery-check improvements.

Kept separate from ``test_lint_traceability_delivery_checks.py`` because that
file must start with the plan's ``# STUB: AC-0013`` block byte-for-byte and
cannot carry any additional top-level imports without violating E402.
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

APM = Path(__file__).resolve().parents[3] / ".apm"
LINTER = APM / "skills" / "work-loop" / "scripts" / "lint-traceability.py"
BINS = APM / "adapter-root-bins"
_RESOLVER_SOURCE = BINS / "intent_delivery_relations.py"
_EMPTY_SNAPSHOT: dict = {
    "schema_version": 1,
    "complete": True,
    "relations": [],
    "classifications": [],
    "provenance": [],
    "diagnostics": [],
    "artifacts": {},
}


def _write(path: Path, text: str) -> None:
    """Create parent directories and write ``text`` to ``path``."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _load_linter(suffix: str) -> object:
    """Load lint-traceability as a fresh module instance keyed by ``suffix``."""
    ms = importlib.util.spec_from_file_location(f"_trace_dc_{suffix}", str(LINTER))
    assert ms is not None and ms.loader is not None
    mod = importlib.util.module_from_spec(ms)
    ms.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------------
# VI-1702: malformed snapshot record → delivery-resolver-unavailable (hard)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "bad_snapshot,label",
    [
        # relation item is not a dict
        (
            {**_EMPTY_SNAPSHOT, "relations": [42]},
            "non-dict-relation",
        ),
        # relation item has unknown type
        (
            {
                **_EMPTY_SNAPSHOT,
                "relations": [{
                    "type": "unknown-type",
                    "intent": "intent:alpha",
                    "spec": "spec:foo",
                    "route": "spec",
                    "basis": {},
                }],
            },
            "bad-relation-type",
        ),
        # classification item is not a dict
        (
            {**_EMPTY_SNAPSHOT, "classifications": ["not-a-dict"]},
            "non-dict-classification",
        ),
        # diagnostic item has unknown code
        (
            {
                **_EMPTY_SNAPSHOT,
                "diagnostics": [{
                    "code": "totally-unknown-code",
                    "subject": "spec:foo",
                }],
            },
            "bad-diagnostic-code",
        ),
        # artifacts key not a valid identifier
        (
            {**_EMPTY_SNAPSHOT, "artifacts": {"INVALID KEY!!": "docs/specs/foo/spec.md"}},
            "bad-artifacts-key",
        ),
    ],
    ids=[
        "non-dict-relation",
        "bad-relation-type",
        "non-dict-classification",
        "bad-diagnostic-code",
        "bad-artifacts-key",
    ],
)
def test_vi1702_malformed_snapshot_record_is_hard_violation(
    tmp_path: Path, bad_snapshot: dict, label: str
) -> None:
    """A malformed snapshot record → delivery-resolver-unavailable DANGLING,
    exit 1 in every mode (including --strict), never the degraded exit-0 path."""
    _write(
        tmp_path / "docs/product/briefs/anchor.md",
        "# Brief\n\n- **Slug:** `anchor`\n",
    )

    mod = _load_linter(f"vi1702_{label}")

    def bad_provider(_root: Path) -> dict:
        return bad_snapshot

    out_lines, hard, exit_hint = mod.check(
        tmp_path, False, snapshot_provider=bad_provider
    )
    assert exit_hint == 1, (
        f"{label}: malformed record → exit 1, got {exit_hint}: {hard!r}"
    )
    assert any(
        "delivery-resolver-unavailable" in h for h in hard
    ), f"{label}: delivery-resolver-unavailable in hard violations: {hard!r}"

    # Also fails under --strict
    _, hard2, exit_strict = mod.check(
        tmp_path, True, snapshot_provider=bad_provider
    )
    assert exit_strict == 1, (
        f"{label}: --strict also exit 1, got {exit_strict}"
    )


def test_vi1702_non_delivery_checks_run_when_record_malformed(tmp_path: Path) -> None:
    """When snapshot validation fails, non-delivery orphan checks still run."""
    _write(
        tmp_path / "docs/product/briefs/anchor.md",
        "# Brief\n\n- **Slug:** `anchor`\n",
    )
    # Spec with no producer → backward orphan (non-delivery check)
    _write(
        tmp_path / "docs/specs/lonely/spec.md",
        "# Spec\n\n- **Status:** Draft\n",
    )

    bad_snapshot = {**_EMPTY_SNAPSHOT, "relations": [999]}  # non-dict item

    mod = _load_linter("vi1702_nd_checks")

    def bad_provider(_root: Path) -> dict:
        return bad_snapshot

    out_lines, hard, exit_hint = mod.check(
        tmp_path, False, snapshot_provider=bad_provider
    )
    # Both delivery failure AND orphan summary must appear
    assert exit_hint == 1, f"delivery fail + orphan → exit 1, got {exit_hint}"
    assert any("delivery-resolver-unavailable" in h for h in hard), (
        f"delivery failure in hard violations: {hard!r}"
    )
    assert any("orphan" in ln.lower() for ln in out_lines), (
        f"non-delivery orphan check still reported: {out_lines!r}"
    )


# ---------------------------------------------------------------------------
# VI-1703: configured layout differs from resolver defaults → fail closed
# ---------------------------------------------------------------------------


def test_vi1703_custom_spec_base_fails_closed_with_anchor(tmp_path: Path) -> None:
    """A configured spec base that differs from the resolver default produces
    delivery-resolver-unavailable while non-delivery checks still run."""
    # Chain anchor: brief
    _write(
        tmp_path / "docs/product/briefs/anchor.md",
        "# Brief\n\n- **Slug:** `anchor`\n",
    )
    # Custom spec base via layout config
    (tmp_path / "custom" / "specs").mkdir(parents=True)
    _write(
        tmp_path / "agentbundle-layout.toml",
        '[traceability]\nspec = "custom/specs"\n',
    )

    proc = subprocess.run(
        [sys.executable, str(LINTER), "--root", str(tmp_path)],
        capture_output=True, text=True, timeout=120,
    )
    assert proc.returncode == 1, (
        f"custom spec base + anchor → exit 1 (fail closed), got {proc.returncode}: "
        f"{proc.stderr}"
    )
    assert "delivery-resolver-unavailable" in proc.stderr, (
        f"fail-closed code in stderr: {proc.stderr}"
    )


def test_vi1703_no_anchor_still_exits_zero(tmp_path: Path) -> None:
    """Without a chain anchor, a custom layout does not activate the lint at all."""
    # Custom spec base, but NO anchor (no briefs, no discovery layers)
    _write(
        tmp_path / "agentbundle-layout.toml",
        '[traceability]\nspec = "custom/specs"\n',
    )
    (tmp_path / "custom" / "specs").mkdir(parents=True)
    # Specs only (no anchor) → no-op
    _write(
        tmp_path / "custom" / "specs" / "foo" / "spec.md",
        "# Spec\n\n- **Status:** Draft\n",
    )

    proc = subprocess.run(
        [sys.executable, str(LINTER), "--root", str(tmp_path)],
        capture_output=True, text=True, timeout=120,
    )
    assert proc.returncode == 0, (
        f"no anchor + custom layout → exit 0 silently, got {proc.returncode}: {proc.stderr}"
    )
    assert proc.stdout.strip() == "", f"no anchor → no stdout: {proc.stdout!r}"


def test_vi1703_default_bases_do_not_fail_closed(tmp_path: Path) -> None:
    """Default bases (no config) do not trigger fail-closed.

    After T9 the linter finds its resolver beside its own scripts/ directory;
    no installation into .agentbundle/bin/ is needed.
    """
    # Default bases: docs/specs, docs/product/intents — create anchor only
    _write(
        tmp_path / "docs/product/briefs/anchor.md",
        "# Brief\n\n- **Slug:** `anchor`\n",
    )

    proc = subprocess.run(
        [sys.executable, str(LINTER), "--root", str(tmp_path)],
        capture_output=True, text=True, timeout=120,
    )
    # Should NOT fail closed with delivery-resolver-unavailable for default bases
    assert "delivery-resolver-unavailable" not in proc.stderr, (
        f"default bases must not fail closed: rc={proc.returncode} {proc.stderr}"
    )


# ---------------------------------------------------------------------------
# VI-1704: sanitized output — hostile resolver content never reaches output
# ---------------------------------------------------------------------------


def test_vi1704_hostile_snapshot_content_not_in_output(tmp_path: Path) -> None:
    """Hostile content in a resolver response never reaches stdout or stderr.

    When the snapshot fails validation, only ``delivery-resolver-unavailable``
    appears — the hostile markers do not leak into any output channel.
    """
    _write(
        tmp_path / "docs/product/briefs/anchor.md",
        "# Brief\n\n- **Slug:** `anchor`\n",
    )
    hostile_markers = [
        "/absolute/path/to/secret",
        "TOKEN=abc123secret",
        "Traceback (most recent call last):",
    ]

    # Snapshot with a diagnostic whose code contains hostile content.
    bad_snapshot = {
        **_EMPTY_SNAPSHOT,
        "diagnostics": [{
            "code": "INJECTION:/absolute/path TOKEN=abc123secret Traceback",
            "subject": "spec:foo",
        }],
    }

    mod = _load_linter("vi1704_hostile")

    def hostile_provider(_root: Path) -> dict:
        return bad_snapshot

    out_lines, hard, exit_hint = mod.check(
        tmp_path, False, snapshot_provider=hostile_provider
    )
    blob = "\n".join(out_lines) + "\n".join(hard)
    for marker in hostile_markers:
        assert marker not in blob, (
            f"hostile marker {marker!r} must not appear in output: {blob!r}"
        )


def test_vi1704_diagnostic_output_contains_only_stable_codes(tmp_path: Path) -> None:
    """A valid snapshot with known diagnostic codes prints those codes in output."""
    _write(
        tmp_path / "docs/product/briefs/anchor.md",
        "# Brief\n\n- **Slug:** `anchor`\n",
    )
    snapshot = {
        **_EMPTY_SNAPSHOT,
        "diagnostics": [{
            "code": "delivery-projection-mismatch",
            "subject": "intent:alpha",
            "targets": ["spec:s1", "spec:s2"],
        }],
    }

    mod = _load_linter("vi1704_stable_codes")

    out_lines, hard, _exit_hint = mod.check(
        tmp_path, False, snapshot_provider=lambda _r: snapshot
    )
    # The stable code must appear in informational output
    assert any("delivery-projection-mismatch" in ln for ln in out_lines), (
        f"known code appears in output: {out_lines!r}"
    )
    # No unknown content in output
    assert all("INJECTION" not in ln for ln in out_lines + hard), (
        f"no unknown content in output: {out_lines + hard!r}"
    )


# ---------------------------------------------------------------------------
# VI-1705: fail-closed through stub resolver; check() kwarg
# ---------------------------------------------------------------------------


def test_vi1705_check_accepts_snapshot_provider_kwarg(tmp_path: Path) -> None:
    """check() accepts snapshot_provider as a keyword argument (not module global)."""
    _write(
        tmp_path / "docs/product/briefs/anchor.md",
        "# Brief\n\n- **Slug:** `anchor`\n",
    )

    called: list[bool] = []

    def tracking_provider(_root: Path) -> dict:
        called.append(True)
        return _EMPTY_SNAPSHOT

    mod = _load_linter("vi1705_kwarg")
    out_lines, hard, exit_hint = mod.check(
        tmp_path, False, snapshot_provider=tracking_provider
    )
    assert called, "snapshot_provider kwarg was not called"
    assert exit_hint == 0, f"clean snapshot → exit 0: {hard!r}"


def test_vi1705_stub_hostile_stderr_not_forwarded(tmp_path: Path) -> None:
    """A stub resolver that writes hostile stderr content: no hostile marker
    reaches _run_resolver's ValueError message.

    After T9 the linter finds its resolver beside its own scripts/ directory.
    The seam (_resolver_path kwarg) points _run_resolver at the stub so the
    test does not modify the sibling copy.
    """
    stub = tmp_path / "hostile_resolver.py"
    stub.write_text(
        "import sys\n"
        "sys.stderr.write('/absolute/path/to/secret\\n')\n"
        "sys.stderr.write('TOKEN=abc123\\n')\n"
        "sys.stderr.write('Traceback (most recent call last):\\n')\n"
        "sys.exit(1)\n",
        encoding="utf-8",
    )

    mod = _load_linter("vi1705_hostile")
    raised = False
    exc_msg = ""
    try:
        mod._run_resolver(tmp_path, _resolver_path=stub)
    except ValueError as exc:
        raised = True
        exc_msg = str(exc)
    assert raised, "_run_resolver must raise ValueError for hostile/failing stub"
    assert "delivery-resolver-unavailable" in exc_msg
    for hostile in ["/absolute/path/to/secret", "TOKEN=abc123"]:
        assert hostile not in exc_msg, (
            f"hostile marker {hostile!r} must not appear in error message: {exc_msg!r}"
        )


def test_vi1705_stub_invalid_json_fails_closed(tmp_path: Path) -> None:
    """A stub resolver that emits invalid JSON → delivery-resolver-unavailable."""
    stub = tmp_path / "invalid_json_resolver.py"
    stub.write_text(
        "import sys\n"
        "sys.stdout.reconfigure(encoding='utf-8')\n"
        "sys.stdout.write('not valid json {{{\\n')\n",
        encoding="utf-8",
    )

    mod = _load_linter("vi1705_invalid_json")
    raised = False
    try:
        mod._run_resolver(tmp_path, _resolver_path=stub)
    except ValueError as exc:
        raised = True
        assert "delivery-resolver-unavailable" in str(exc)
    assert raised, "_run_resolver must raise ValueError for invalid JSON"


def test_vi1705_stub_complete_false_fails_closed(tmp_path: Path) -> None:
    """A stub resolver that emits complete:false → delivery-resolver-unavailable."""
    incomplete_payload = json.dumps({
        "schema_version": 1,
        "complete": False,
        "relations": [],
        "classifications": [],
        "provenance": [],
        "diagnostics": [],
        "artifacts": {},
    })
    stub = tmp_path / "incomplete_resolver.py"
    stub.write_text(
        "import sys\n"
        "sys.stdout.reconfigure(encoding='utf-8')\n"
        f"sys.stdout.write({incomplete_payload!r})\n",
        encoding="utf-8",
    )

    mod = _load_linter("vi1705_incomplete")
    raised = False
    try:
        mod._run_resolver(tmp_path, _resolver_path=stub)
    except ValueError as exc:
        raised = True
        assert "delivery-resolver-unavailable" in str(exc)
    assert raised, "_run_resolver must raise ValueError for complete:false"


def test_vi1705_timeout_lowered_and_fails_closed(tmp_path: Path) -> None:
    """A stub resolver that sleeps past a test-lowered timeout →
    delivery-resolver-unavailable. The timeout is a module constant so the
    test can monkeypatch it.

    After T9 the seam (_resolver_path kwarg) points _run_resolver at the stub.
    """
    stub = tmp_path / "sleeping_resolver.py"
    stub.write_text(
        "import time\ntime.sleep(10)\n",
        encoding="utf-8",
    )

    mod = _load_linter("vi1705_timeout")
    # Lower the timeout so the test is fast.
    mod._RESOLVER_TIMEOUT = 1

    raised = False
    try:
        mod._run_resolver(tmp_path, _resolver_path=stub)
    except ValueError as exc:
        raised = True
        assert "delivery-resolver-unavailable" in str(exc), (
            f"timeout raises delivery-resolver-unavailable: {exc}"
        )
    assert raised, "timeout must raise ValueError"


def test_vi1705_provider_kwarg_not_module_global(tmp_path: Path) -> None:
    """The snapshot_provider kwarg to check() takes precedence over the module
    global _delivery_snapshot_provider; both are independently injectable."""
    _write(
        tmp_path / "docs/product/briefs/anchor.md",
        "# Brief\n\n- **Slug:** `anchor`\n",
    )

    mod = _load_linter("vi1705_kwarg_prio")
    # Set the module global to a failing provider
    mod._delivery_snapshot_provider = lambda _: (_ for _ in ()).throw(
        ValueError("delivery-resolver-unavailable: from global")
    )

    # But pass a valid provider via the kwarg — it should win
    out_lines, hard, exit_hint = mod.check(
        tmp_path, False, snapshot_provider=lambda _: _EMPTY_SNAPSHOT
    )
    # The kwarg provider succeeds → no delivery failure
    assert not any("from global" in h for h in hard), (
        f"kwarg provider must take precedence over global: {hard!r}"
    )
