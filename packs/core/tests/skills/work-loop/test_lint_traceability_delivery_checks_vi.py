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
    the configured-base message in delivery-resolver-unavailable while
    non-delivery checks still run.

    The resolver ships beside the linter in scripts/ (T9); the configured-base
    check fires before the resolver is invoked, so the specific message is the
    only reliable discriminator.
    """
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
    assert "configured spec or intent base differs from resolver defaults" in proc.stderr, (
        f"configured-base message must appear in stderr: {proc.stderr}"
    )


def test_vi1703_custom_intent_base_fails_closed_with_anchor(tmp_path: Path) -> None:
    """A configured intent base that differs from the resolver default produces
    the configured-base message in delivery-resolver-unavailable while
    non-delivery checks still run.
    """
    # Chain anchor: brief
    _write(
        tmp_path / "docs/product/briefs/anchor.md",
        "# Brief\n\n- **Slug:** `anchor`\n",
    )
    # Custom intent/outcome base via layout config
    (tmp_path / "custom" / "intents").mkdir(parents=True)
    _write(
        tmp_path / "agentbundle-layout.toml",
        '[traceability]\noutcome = "custom/intents"\n',
    )

    proc = subprocess.run(
        [sys.executable, str(LINTER), "--root", str(tmp_path)],
        capture_output=True, text=True, timeout=120,
    )
    assert proc.returncode == 1, (
        f"custom intent base + anchor → exit 1 (fail closed), got {proc.returncode}: "
        f"{proc.stderr}"
    )
    assert "configured spec or intent base differs from resolver defaults" in proc.stderr, (
        f"configured-base message must appear in stderr: {proc.stderr}"
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
    assert proc.returncode == 0, (
        f"default bases + anchor → exit 0, got {proc.returncode}: {proc.stderr}"
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

    # Snapshot with a diagnostic whose code contains all three hostile markers
    # verbatim so that the assertions are non-vacuous.
    bad_snapshot = {
        **_EMPTY_SNAPSHOT,
        "diagnostics": [{
            "code": (
                "INJECTION:/absolute/path/to/secret "
                "TOKEN=abc123secret "
                "Traceback (most recent call last):"
            ),
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
    """A stub resolver that sleeps past a test-lowered timeout appears as a
    delivery-resolver-unavailable hard violation and exit 1 from check().

    The stub writes a valid complete snapshot after sleeping 5 s.  The timeout
    is lowered to 1 s; elapsed wall-clock must be less than the stub's sleep to
    prove the timeout fired (not the stub completing normally).
    """
    stub = tmp_path / "sleeping_resolver.py"
    stub.write_text(
        "import time, sys, json\n"
        "time.sleep(5)\n"
        "snap = {\n"
        "    'schema_version': 1, 'complete': True,\n"
        "    'relations': [], 'classifications': [], 'provenance': [],\n"
        "    'diagnostics': [], 'artifacts': {},\n"
        "}\n"
        "sys.stdout.write(json.dumps(snap) + '\\n')\n",
        encoding="utf-8",
    )
    _write(
        tmp_path / "docs/product/briefs/anchor.md",
        "# Brief\n\n- **Slug:** `anchor`\n",
    )

    mod = _load_linter("vi1705_timeout")
    # Lower the timeout so the test is fast.
    mod._RESOLVER_TIMEOUT = 1

    def timeout_provider(root: object) -> dict:
        return mod._run_resolver(root, _resolver_path=stub)

    import time as _time
    _t0 = _time.monotonic()
    out_lines, hard, exit_hint = mod.check(
        tmp_path, False, snapshot_provider=timeout_provider
    )
    _elapsed = _time.monotonic() - _t0

    assert exit_hint == 1, (
        f"timeout → exit 1 from check(), got {exit_hint}: {hard!r}"
    )
    assert any("delivery-resolver-unavailable" in h for h in hard), (
        f"timeout → delivery-resolver-unavailable in hard violations: {hard!r}"
    )
    assert _elapsed < 4, (
        f"timeout must fire before stub finishes (stub sleeps 5 s), "
        f"elapsed={_elapsed:.2f}s"
    )


def test_vi1705_provider_kwarg_not_module_global(tmp_path: Path) -> None:
    """The snapshot_provider kwarg to check() is the sole injection seam.
    No module-level global is read; the kwarg provider succeeds independently."""
    _write(
        tmp_path / "docs/product/briefs/anchor.md",
        "# Brief\n\n- **Slug:** `anchor`\n",
    )

    mod = _load_linter("vi1705_kwarg_prio")

    # Pass a valid provider via the kwarg — it must be used
    out_lines, hard, exit_hint = mod.check(
        tmp_path, False, snapshot_provider=lambda _: _EMPTY_SNAPSHOT
    )
    # The kwarg provider succeeds → no delivery failure
    assert exit_hint == 0, (
        f"kwarg provider → exit 0, got {exit_hint}: {hard!r}"
    )
    assert not any("delivery-resolver-unavailable" in h for h in hard), (
        f"kwarg provider succeeds → no delivery failure: {hard!r}"
    )


# ---------------------------------------------------------------------------
# VI-2405: resolver JSON parse raising RecursionError, and 200-char label truncation
# ---------------------------------------------------------------------------


def test_vi2405_recursion_error_in_json_parse_yields_unavailable(tmp_path: Path) -> None:
    """A resolver whose json.loads raises RecursionError yields
    delivery-resolver-unavailable with exit 1 and no traceback.

    json.loads is patched to raise RecursionError unconditionally so the handler
    fires on every supported interpreter regardless of its C-scanner recursion
    limit.  _parse_and_validate_snapshot catches RecursionError and re-raises
    ValueError.  check() then adds the sanitized message to hard violations.
    The test goes red if RecursionError is removed from the except clause at
    _parse_and_validate_snapshot.
    """
    from unittest.mock import patch

    _write(
        tmp_path / "docs/product/briefs/anchor.md",
        "# Brief\n\n- **Slug:** `anchor`\n",
    )
    stub = tmp_path / "json_resolver.py"
    stub.write_text("print('{}')\n", encoding="utf-8")

    mod = _load_linter("vi2405_recursion")

    def recursion_provider(root: Path) -> dict:
        return mod._run_resolver(root, _resolver_path=stub)

    with patch.object(
        mod.json,
        "loads",
        side_effect=RecursionError("maximum recursion depth exceeded"),
    ):
        out_lines, hard, exit_hint = mod.check(
            tmp_path, False, snapshot_provider=recursion_provider
        )
    assert exit_hint == 1, (
        f"RecursionError in JSON parse → exit 1, got {exit_hint}: {hard!r}"
    )
    assert any("delivery-resolver-unavailable" in h for h in hard), (
        f"RecursionError in JSON parse → delivery-resolver-unavailable in hard: {hard!r}"
    )
    all_output = "\n".join(out_lines + hard)
    assert "Traceback" not in all_output, (
        f"traceback must not appear in output: {all_output!r}"
    )


def test_vi2405_subject_longer_than_200_chars_is_truncated(tmp_path: Path) -> None:
    """A diagnostic subject or target longer than 200 characters is truncated
    to 200 characters with an ellipsis in the printed label.

    The snapshot carries a valid delivery-target-missing diagnostic whose spec:
    subject is 201 characters long.  The printed DANGLING label must contain the
    truncated subject (first 200 chars + ellipsis) and must NOT contain the full
    over-long subject anywhere in the output.  The test goes red if either the
    subject cap or target cap is removed, or if the uncapped prefix returns.

    A second case exercises the over-long target cap: delivery-target-missing
    on a spec: subject with a 201-char target.  The printed entry must contain
    the truncated target and must NOT contain the full over-long target.
    """
    _write(
        tmp_path / "docs/product/briefs/anchor.md",
        "# Brief\n\n- **Slug:** `anchor`\n",
    )
    # Construct a valid spec: identifier of length 201
    long_slug = "a" * (201 - len("spec:"))  # 196 chars → spec: prefix → 201 total
    long_subject = f"spec:{long_slug}"
    assert len(long_subject) == 201

    snapshot = {
        **_EMPTY_SNAPSHOT,
        "diagnostics": [
            {"code": "delivery-target-missing", "subject": long_subject},
        ],
    }

    mod = _load_linter("vi2405_truncation")
    out_lines, hard, exit_hint = mod.check(
        tmp_path, False, snapshot_provider=lambda _: snapshot
    )

    # delivery-target-missing with a spec: subject → DANGLING → exit 1
    assert exit_hint == 1, (
        f"delivery-target-missing → exit 1; got {exit_hint}: {hard!r}"
    )
    truncated_subj = long_subject[:200] + "\u2026"
    all_output = "\n".join(out_lines + hard)
    dangling_text = " ".join(hard)
    assert truncated_subj in dangling_text, (
        f"truncated subject (first 200 chars + ellipsis) not found in hard; "
        f"hard={hard!r}"
    )
    # Full over-long subject must be absent from every output line and hard violations
    assert long_subject not in all_output, (
        f"full over-long subject must be absent from all output; "
        f"found in: {all_output!r}"
    )

    # Over-long target case: delivery-target-missing with a 201-char canonical target.
    # Use docs/product/briefs/<name>.md form so the target passes _is_canonical_target.
    _brief_prefix = "docs/product/briefs/"
    _brief_suffix = ".md"
    long_target_name = "a" * (201 - len(_brief_prefix) - len(_brief_suffix))
    long_target = f"{_brief_prefix}{long_target_name}{_brief_suffix}"
    assert len(long_target) == 201
    snapshot_with_target = {
        **_EMPTY_SNAPSHOT,
        "diagnostics": [
            {
                "code": "delivery-target-missing",
                "subject": "spec:foo",
                "targets": [long_target],
            },
        ],
    }
    mod2 = _load_linter("vi2405_truncation_target")
    out2, hard2, exit2 = mod2.check(
        tmp_path, False, snapshot_provider=lambda _: snapshot_with_target
    )
    all_output2 = "\n".join(out2 + hard2)
    truncated_tgt = long_target[:200] + "\u2026"
    assert truncated_tgt in all_output2, (
        f"truncated target not found in output; out={out2!r} hard={hard2!r}"
    )
    assert long_target not in all_output2, (
        f"full over-long target must be absent from all output; "
        f"found in: {all_output2!r}"
    )


# ---------------------------------------------------------------------------
# VI-2404 negative validator tests for lint-traceability
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "bad_record,label",
    [
        (
            {"subject": "spec:foo", "field": "Parent intent", "intent": "intent:alpha"},
            "subject-not-brief-typed",
        ),
        (
            {"subject": "brief:foo", "field": "Parent intent"},
            "missing-intent",
        ),
        (
            {"subject": "brief:foo", "field": "Parent intent", "intent": "brief:alpha"},
            "non-intent-typed-intent",
        ),
        (
            {"subject": "brief:foo", "field": "Parent intent", "intent": "intent:"},
            "prefix-only-intent",
        ),
        (
            {"subject": "brief:foo", "field": "Parent intent", "intent": "intent:A/../b"},
            "path-like-intent",
        ),
    ],
    ids=[
        "subject-not-brief-typed",
        "missing-intent",
        "non-intent-typed-intent",
        "prefix-only-intent",
        "path-like-intent",
    ],
)
def test_vi2404_lint_rejects_malformed_parent_intent_provenance(
    tmp_path: Path, bad_record: dict, label: str
) -> None:
    """lint-traceability _validate_snapshot_dict raises delivery-resolver-unavailable
    for a malformed Parent intent provenance record; each case goes red when its
    specific check is removed from the validator."""
    _write(
        tmp_path / "docs/product/briefs/anchor.md",
        "# Brief\n\n- **Slug:** `anchor`\n",
    )
    snapshot = {**_EMPTY_SNAPSHOT, "provenance": [bad_record]}

    mod = _load_linter(f"vi2404_lint_neg_{label}")

    out_lines, hard, exit_hint = mod.check(
        tmp_path, False, snapshot_provider=lambda _: snapshot
    )
    assert exit_hint == 1, (
        f"{label}: malformed Parent intent provenance → exit 1; "
        f"got {exit_hint}: {hard!r}"
    )
    assert any("delivery-resolver-unavailable" in h for h in hard), (
        f"{label}: delivery-resolver-unavailable expected in hard; "
        f"hard={hard!r}"
    )
