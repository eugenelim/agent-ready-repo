"""Construction stubs for the direct diagnostic registry (T0e).

Red at PLAN, green when T0e lands. The imports sit inside each test body so the
module collects cleanly while the direct registry does not yet exist: a
module-level import would make pytest report a collection error rather than a
failing test, and a collection error is not a red test.

These assert behaviour rather than presence, because the plan's Design (LLD)
pins T0e's three signatures. The rest of the direct stub set is shape-only for
now — its tasks have no API in the LLD yet.
"""

from __future__ import annotations

import pytest

# The AC33 budget names BoundExceeded carries. Deliberately plain strings: the
# byte-pinned file_safety.py mirror must not import diagnostics.py.
BUDGET_NAMES = frozenset(
    {"entries", "depth", "files", "selected-skills", "per-file-bytes", "total-bytes"}
)


def test_direct_codes_registry_contract():
    # STUB: AC31 — DIRECT_CODES is an explicit frozenset of DiagnosticCode members,
    # and make_direct_diagnostic accepts only those.
    from agentbundle.catalogue_tooling.diagnostics import (
        DIRECT_CODES,
        DiagnosticCode,
        make_direct_diagnostic,
    )
    from agentbundle.catalogue_tooling.results import Severity

    assert isinstance(DIRECT_CODES, frozenset)
    assert DIRECT_CODES, "DIRECT_CODES must not be empty"
    assert all(isinstance(code, DiagnosticCode) for code in DIRECT_CODES)

    # No member-count assertion. Two were tried during review — nine, then
    # twelve — and both were stale, because a count ages every time a criterion
    # adds a refusal. Assert the members the ACs pin BY NAME instead; that
    # cannot go stale, and AC31's lint is what enforces exact coverage.
    for pinned in (
        "measured-path-integrity",       # AC27, AC34
        "source-untraversable-or-changed",  # AC31
        "invalid-direct-identity",       # AC31, AC11
    ):
        assert any(code.value.endswith(pinned) or pinned in code.name.lower().replace("_", "-")
                   for code in DIRECT_CODES), f"DIRECT_CODES must register {pinned}"

    # One registered member per AC33 budget, each independently reachable.
    for budget in sorted(BUDGET_NAMES):
        assert any(budget in code.name.lower().replace("_", "-") for code in DIRECT_CODES), (
            f"AC33 requires a registered DIRECT_CODES member for the {budget} budget"
        )

    # Positive case first — a registered code is accepted and round-trips.
    # Without this the negative assertion below is satisfied by a function that
    # rejects everything, which is not the contract.
    registered = next(iter(sorted(DIRECT_CODES)))
    produced = make_direct_diagnostic(
        registered,
        Severity.ERROR,
        "message",
        path="skills/example/SKILL.md",
        remediation="remediation",
    )
    assert produced.code == registered.value
    assert produced.path == "skills/example/SKILL.md"
    # Severity is an IntEnum, not a str: the established serializer emits
    # `d.severity.name` (lint.py:2272), which is the shape AC21 pins, and a
    # bare "error" string would raise AttributeError there.
    assert produced.severity is Severity.ERROR

    # Negative case — a registered DiagnosticCode outside DIRECT_CODES is refused.
    # CAT_L001 is a catalogue lint code and must never be reachable as a direct code.
    assert DiagnosticCode.CAT_L001 not in DIRECT_CODES
    with pytest.raises(ValueError):
        make_direct_diagnostic(
            DiagnosticCode.CAT_L001,
            Severity.ERROR,
            "message",
            path="skills/example/SKILL.md",
            remediation="remediation",
        )


def test_bound_exceeded_carries_typed_budget_attribution():
    # STUB: AC33 — a budget breach is attributed through the exception's
    # attributes, never by parsing UnsafeContentError message text.
    from agentbundle.catalogue_tooling.file_safety import BoundExceeded, UnsafeContentError

    assert issubclass(BoundExceeded, UnsafeContentError)

    raised = BoundExceeded(
        "source tree exceeds entry limit",
        budget="entries",
        limit=2_500,
        observed=2_501,
    )
    assert raised.budget == "entries"
    assert raised.budget in BUDGET_NAMES
    assert raised.limit == 2_500
    assert raised.observed == 2_501

    # An existing catalogue caller catching UnsafeContentError still catches this,
    # so T0e's addition cannot silently escape an established handler.
    with pytest.raises(UnsafeContentError):
        raise raised


def test_read_confined_regular_file_attributes_the_per_file_bytes_budget(tmp_path):
    # STUB: AC33 — both max_bytes overrun sites in read_confined_regular_file
    # raise BoundExceeded carrying the per-file-bytes budget. Constructing
    # BoundExceeded by hand (above) is satisfied by a class that is defined and
    # never raised; this is the arm that reddens if either site stays bare.
    from agentbundle.catalogue_tooling.file_safety import (
        BoundExceeded,
        read_confined_regular_file,
    )

    root = tmp_path
    oversized = root / "SKILL.md"
    oversized.write_bytes(b"x" * 65)

    with pytest.raises(BoundExceeded) as excinfo:
        read_confined_regular_file(root, oversized, max_bytes=64)
    assert excinfo.value.budget == "per-file-bytes"
    assert excinfo.value.limit == 64

    # A value equal to the limit is admitted — AC15's bounds allow equality and
    # refuse only a greater value. Without this the refusal above is satisfied
    # by an implementation that rejects every read.
    at_limit = root / "at-limit.md"
    at_limit.write_bytes(b"x" * 64)
    assert read_confined_regular_file(root, at_limit, max_bytes=64) is not None


def test_read_confined_regular_file_attributes_the_post_read_overrun(tmp_path, monkeypatch):
    # STUB: AC33 — the SECOND max_bytes site. The pre-read size check and the
    # post-read "changed beyond byte limit" check are different code paths, and
    # a file that is simply oversized only ever reaches the first. Under-report
    # st_size so the pre-read check passes and the read overruns, which is the
    # source-mutation path: without typed attribution there a caller cannot tell
    # a mid-read growth from the other bare-UnsafeContentError conditions.
    import os as _os

    from agentbundle.catalogue_tooling import file_safety as fs
    from agentbundle.catalogue_tooling.file_safety import (
        BoundExceeded,
        read_confined_regular_file,
    )

    root = tmp_path
    target = root / "grows.md"
    target.write_bytes(b"x" * 65)

    real_fstat = _os.fstat

    def _understating_fstat(fd):
        info = real_fstat(fd)
        return type(info)(tuple(info)[:6] + (0,) + tuple(info)[7:])

    monkeypatch.setattr(fs.os, "fstat", _understating_fstat)

    with pytest.raises(BoundExceeded) as excinfo:
        read_confined_regular_file(root, target, max_bytes=64)
    assert excinfo.value.budget == "per-file-bytes"


def test_integrity_refusal_is_discriminable_from_a_budget_breach(tmp_path):
    # STUB: AC33 — an entry-integrity refusal is NOT a budget breach. A caller
    # must separate the two without parsing UnsafeContentError message text.
    from agentbundle.catalogue_tooling.file_safety import (
        BoundExceeded,
        UnsafeContentError,
        read_confined_regular_file,
    )

    root = tmp_path
    target = root / "real.md"
    target.write_bytes(b"content")
    link = root / "link.md"
    link.symlink_to(target)

    # A symlink is an integrity refusal: it must raise UnsafeContentError but
    # must NOT be a BoundExceeded, so `except BoundExceeded` cannot swallow it
    # and no message-text inspection is needed to tell the two apart.
    with pytest.raises(UnsafeContentError) as excinfo:
        read_confined_regular_file(root, link, max_bytes=1024)
    assert not isinstance(excinfo.value, BoundExceeded)
