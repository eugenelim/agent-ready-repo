#!/usr/bin/env python3
"""Self-test for ``lint-pack-maintainer-emails.py``.

Matches the ``tools/test-lint-*.py`` convention: pure stdlib, no pytest, prints
a pass line and exits 0, or raises on the first failure.
"""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location(
    "lint_pack_maintainer_emails", _HERE / "lint-pack-maintainer-emails.py"
)
assert _spec and _spec.loader
lint = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(lint)


def _pack(packs: Path, name: str, email: str | None) -> None:
    pack = packs / name
    pack.mkdir(parents=True)
    body = f'[pack]\nname = "{name}"\nversion = "0.0.1"\n'
    if email is not None:
        body += "\n[[pack.maintainers]]\nname = \"Maintainer\"\n"
        body += f"email = {json.dumps(email)}\n"
    (pack / "pack.toml").write_text(body, encoding="utf-8", newline="\n")


def test_non_no_reply_address_is_flagged() -> None:
    """The control must fail on a fixture, never by changing a real pack."""
    with tempfile.TemporaryDirectory() as tmp:
        packs = Path(tmp) / "packs"
        _pack(packs, "leaky", "person@example.test")
        violations = lint.find_violations(packs)
    assert len(violations) == 1, violations
    assert "leaky" in violations[0]
    assert "person@example.test" in violations[0]


def test_reviewed_host_passes() -> None:
    """The one host this repository actually publishes from."""
    with tempfile.TemporaryDirectory() as tmp:
        packs = Path(tmp) / "packs"
        _pack(packs, "ok", "12345+someone@users.noreply.github.com")
        assert lint.find_violations(packs) == []


def test_the_three_review_bypasses_are_rejected() -> None:
    """Regression cases from the round-1 review of this lint.

    The first draft matched a `.noreply.` pattern rather than a reviewed host
    set. Each address below defeated it. They are pinned here because a future
    "simplification" back to a pattern would reopen all three at once.
    """
    cases = [
        # Identifying local part AND identifying host, but the host carried a
        # `.noreply.` label, so the pattern cleared it.
        "alice.smith@alice-smith.noreply.example.test",
        # Person moved into the host; the `noreply` local part cleared it.
        "noreply@alice-smith.example.test",
        # Not a valid address at all. Splitting on the FIRST `@` left the local
        # part reading `noreply`, so it was cleared.
        "noreply@alice-smith@example.test",
    ]
    for address in cases:
        with tempfile.TemporaryDirectory() as tmp:
            packs = Path(tmp) / "packs"
            _pack(packs, "bypass", address)
            violations = lint.find_violations(packs)
        assert len(violations) == 1, f"{address!r} was cleared: {violations}"


def test_structurally_unparseable_addresses_are_refused_not_cleared() -> None:
    """An address the lint cannot resolve must fail, never default to allowed."""
    for address in ("no-at-sign", "@host.test", "local@", "a b@users.noreply.github.com"):
        with tempfile.TemporaryDirectory() as tmp:
            packs = Path(tmp) / "packs"
            _pack(packs, "weird", address)
            assert len(lint.find_violations(packs)) == 1, address


def test_allowlisted_address_passes() -> None:
    address = "release-team@example.test"
    original = lint.ALLOWED_EMAILS
    lint.ALLOWED_EMAILS = frozenset({address})
    try:
        with tempfile.TemporaryDirectory() as tmp:
            packs = Path(tmp) / "packs"
            _pack(packs, "role", address)
            assert lint.find_violations(packs) == []
    finally:
        lint.ALLOWED_EMAILS = original


def test_a_malformed_allowlist_entry_does_not_bypass_the_parser() -> None:
    """The escape hatch must not reopen the defect the rule closed.

    Round-2 review finding: `ALLOWED_EMAILS` was consulted before
    `_split_address`, so a malformed entry would clear the structural check
    that exists to refuse malformed addresses.
    """
    address = "role@a@example.test"
    original = lint.ALLOWED_EMAILS
    lint.ALLOWED_EMAILS = frozenset({address})
    try:
        with tempfile.TemporaryDirectory() as tmp:
            packs = Path(tmp) / "packs"
            _pack(packs, "malformed-exception", address)
            assert len(lint.find_violations(packs)) == 1
    finally:
        lint.ALLOWED_EMAILS = original


def test_absent_email_is_ignored() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        packs = Path(tmp) / "packs"
        _pack(packs, "unowned", None)
        assert lint.find_violations(packs) == []


def test_malformed_pack_toml_is_not_a_crash() -> None:
    """Schema validation owns that defect; this lint must not double-report."""
    with tempfile.TemporaryDirectory() as tmp:
        packs = Path(tmp) / "packs"
        pack = packs / "broken"
        pack.mkdir(parents=True)
        (pack / "pack.toml").write_text("not toml [[[", encoding="utf-8")
        assert lint.find_violations(packs) == []


def test_directory_without_pack_toml_is_skipped() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        packs = Path(tmp) / "packs"
        (packs / "not-a-pack").mkdir(parents=True)
        assert lint.find_violations(packs) == []


def test_missing_packs_dir_is_not_a_crash() -> None:
    """`find_violations` stays pure; the fail-closed decision lives in main."""
    with tempfile.TemporaryDirectory() as tmp:
        assert lint.find_violations(Path(tmp) / "nope") == []


def test_scanning_nothing_is_an_error_not_a_pass() -> None:
    """A run that examined zero manifests must not read as clean.

    This is the case that makes the control real. Without it a wrong --root
    prints a pass line over an empty scan, which is indistinguishable from a
    genuinely clean catalogue.
    """
    with tempfile.TemporaryDirectory() as tmp:
        # packs/ absent entirely
        assert lint.main(["--root", tmp]) == 2
    with tempfile.TemporaryDirectory() as tmp:
        # packs/ present but carrying no pack.toml
        (Path(tmp) / "packs" / "not-a-pack").mkdir(parents=True)
        assert lint.main(["--root", tmp]) == 2


def test_real_packs_are_clean() -> None:
    """The in-tree catalogue must satisfy its own lint."""
    packs = _HERE.parent / "packs"
    if packs.is_dir():
        assert lint.find_violations(packs) == [], lint.find_violations(packs)


def test_exit_codes() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _pack(root / "packs", "leaky", "person@example.test")
        assert lint.main(["--root", str(root)]) == 1
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _pack(root / "packs", "quiet", "12345+someone@users.noreply.github.com")
        assert lint.main(["--root", str(root)]) == 0


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
    print("test-lint-pack-maintainer-emails: all cases passed.")
    sys.exit(0)
