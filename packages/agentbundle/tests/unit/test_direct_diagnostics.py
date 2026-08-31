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
    # AC31 — DIRECT_CODES is an explicit frozenset of DiagnosticCode members,
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

    # No member-count assertion: two were tried during review — nine, then
    # twelve — and both went stale as later criteria added refusals. Assert
    # structural properties that cannot age instead. AC31's lint owns exact
    # coverage against the published table.

    # The direct namespace is disjoint from the catalogue lint namespace, so a
    # catalogue code can never be emitted as a direct one and vice versa.
    assert all(code.value.startswith("CAT-D") for code in DIRECT_CODES)
    assert DiagnosticCode.CAT_L001 not in DIRECT_CODES

    # AC33: one registered member per budget, all distinct, all direct. This is
    # the checkable form of "each budget is independently reachable" — the
    # module exposes the mapping BoundExceeded.budget resolves through, so the
    # assertion binds to a real seam rather than to a member-naming convention.
    from agentbundle.catalogue_tooling.diagnostics import BUDGET_CODES

    assert set(BUDGET_CODES) == BUDGET_NAMES, (
        "BUDGET_CODES must map exactly AC33's six budget names"
    )
    assert set(BUDGET_CODES.values()) <= DIRECT_CODES
    assert len(set(BUDGET_CODES.values())) == len(BUDGET_NAMES), (
        "each AC33 budget needs its own member, not a shared one"
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
    # AC33 — a budget breach is attributed through the exception's
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
    # AC33 — both max_bytes overrun sites in read_confined_regular_file
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
    # AC33 — the SECOND max_bytes site. The pre-read size check and the
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
    # AC33 — an entry-integrity refusal is NOT a budget breach. A caller
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


def test_every_registered_direct_code_has_a_raise_site():
    # AC31 requires every DIRECT_CODES member to be reachable. Nothing asserted
    # it, which is how CAT-D018 was registered, published in the adopter table,
    # and lint-checked for set equality while having no raise site at all — the
    # table lint compares the registry to the document, so it certified a code
    # that could never be emitted.
    #
    # Checked structurally rather than by exercising a fixture per code: some
    # codes need a network failure or a Windows filesystem to reach. A raise
    # site is weaker than a reached refusal, and this docstring says so — but it
    # is the difference between "declared" and "wired to nothing".
    import ast
    from pathlib import Path

    import agentbundle.direct_install as direct_install
    import agentbundle.direct_source as direct_source
    import agentbundle.direct_source_acquisition as direct_source_acquisition
    from agentbundle.catalogue_tooling.diagnostics import DIRECT_CODES

    referenced: set[str] = set()
    for module in (direct_source, direct_source_acquisition, direct_install):
        tree = ast.parse(Path(module.__file__).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Attribute)
                and isinstance(node.value, ast.Name)
                and node.value.id == "DiagnosticCode"
            ):
                referenced.add(node.attr)

    # The six budget codes are emitted through the BUDGET_CODES mapping — the
    # typed `BoundExceeded.budget` is looked up rather than named — so a direct
    # reference to them does not exist by design. Credit them only when a
    # module actually consumes that mapping.
    from agentbundle.catalogue_tooling.diagnostics import BUDGET_CODES

    consumes_mapping = any(
        "BUDGET_CODES" in Path(module.__file__).read_text(encoding="utf-8")
        for module in (direct_source, direct_source_acquisition, direct_install)
    )
    if consumes_mapping:
        referenced |= {code.name for code in BUDGET_CODES.values()}

    registered = {code.name for code in DIRECT_CODES}
    unreachable = sorted(registered - referenced)
    assert unreachable == [], (
        f"registered and published but never raised: {unreachable}. A code the "
        f"adopter table documents must be emittable, or the table promises a "
        f"refusal that cannot happen."
    )


def _emitted_codes(tmp_path) -> set[str]:
    """Every direct code an actual refusal emits, one scenario per code.

    AC31 requires that across committed direct fixtures "every emitted direct
    `code` ... exactly covers that set". The sibling test above scans for raise
    SITES, which its own docstring calls weaker: a code can have a raise site
    that no input reaches. These scenarios reach them.
    """
    import gzip
    import io
    import sys
    import tarfile
    import unicodedata

    import agentbundle.direct_source as direct_source
    import agentbundle.direct_source_acquisition as acquisition
    from agentbundle.direct_install import (
        DirectInstallError,
        sanitise_publisher_value,
        select_collection_skills,
    )

    emitted: set[str] = set()

    def _record(call) -> None:
        try:
            call()
        except (
            direct_source.DirectAdmissionError,
            acquisition.DirectAcquisitionError,
            DirectInstallError,
        ) as exc:
            emitted.add(exc.diagnostic.code)

    def _skill(path, name="s"):
        path.mkdir(parents=True, exist_ok=True)
        (path / "SKILL.md").write_text(f"---\nname: {name}\n---\n# {name}\n")
        return path

    sha = "0" * 40
    # --- acquisition grammar and transport ---------------------------------
    _record(lambda: acquisition.parse_direct_source("git+https://github.com/o/r@v1?x=1"))
    _record(lambda: acquisition.parse_direct_source("git+https://github.com/o/r@main"))
    _record(lambda: acquisition.parse_direct_source("git+https://github.com/o/r@abc12"))

    source = acquisition.parse_direct_source(f"git+https://github.com/o/r@{sha}")

    def _archive(members, revision=sha):
        raw = io.BytesIO()
        with tarfile.open(
            fileobj=raw, mode="w", format=tarfile.PAX_FORMAT,
            pax_headers={"comment": revision},
        ) as archive:
            for member_name, payload in members.items():
                info = tarfile.TarInfo(member_name)
                info.size = len(payload)
                archive.addfile(info, io.BytesIO(payload))
        return gzip.compress(raw.getvalue())

    def _extract(payload, **kwargs):
        spool = tmp_path / f"a{len(emitted)}.tar.gz"
        spool.write_bytes(payload)
        destination = tmp_path / f"out{len(emitted)}"
        destination.mkdir(exist_ok=True)
        return acquisition._extract(
            spool, destination, source,
            max_members=kwargs.get("max_members", 20_000),
            max_decompressed=kwargs.get("max_decompressed", 1 << 30),
        )

    # SHA mismatch, member limit, escaping member.
    _record(lambda: _extract(_archive({"r/SKILL.md": b"x"}, revision="f" * 40)))
    _record(lambda: _extract(_archive({f"r/{i}.md": b"x" for i in range(4)}), max_members=2))
    _record(lambda: _extract(_archive({"../escape.md": b"x"})))

    class _Old(tuple):
        major, minor, micro = 3, 10, 0

    real_version = sys.version_info
    sys.version_info = _Old((3, 10, 0))  # type: ignore[assignment]
    try:
        _record(lambda: acquisition.enforce_runtime_floor("git+https://github.com/o/r@v1"))
    finally:
        sys.version_info = real_version  # type: ignore[assignment]

    # --- admission shape, identity, integrity, logical path ----------------
    ambiguous = tmp_path / "amb"
    _skill(ambiguous / "skills" / "a", "a")
    _skill(ambiguous / ".claude" / "skills" / "b", "b")
    _record(lambda: direct_source.admit_direct_source(ambiguous))

    bad_identity = tmp_path / "ident"
    _skill(bad_identity / "skills" / "Bad_Name", "x")
    _record(lambda: direct_source.admit_direct_source(bad_identity))

    nfd = tmp_path / "nfd"
    envelope = _skill(nfd / "skills" / "a", "a")
    (envelope / "scripts").mkdir()
    (envelope / "scripts" / unicodedata.normalize("NFD", "café.py")).write_text("x")
    _record(lambda: direct_source.admit_direct_source(nfd))

    # CAT-D010 is the marker-probe failure: a path whose containing directory
    # cannot be searched makes `lstat` raise, which is neither "absent" nor a
    # shape refusal. Reached with a mode-000 parent rather than a missing path,
    # because a missing path is simply absent.
    unsearchable = tmp_path / "unsearchable"
    (unsearchable / "skills").mkdir(parents=True)
    unsearchable.chmod(0o000)
    try:
        _record(lambda: direct_source.admit_direct_source(unsearchable))
    finally:
        unsearchable.chmod(0o755)

    # --- budgets ------------------------------------------------------------
    entries = _skill(tmp_path / "entries", "entries")
    (entries / "scripts").mkdir()
    for index in range(direct_source.DIRECT_MAX_ENTRIES + 1):
        (entries / "scripts" / f"d{index}").mkdir()
    _record(lambda: direct_source.admit_direct_source(entries))

    depth = tmp_path / "depth"
    deep_envelope = _skill(depth / "skills" / "d", "d")
    deep = deep_envelope / "scripts"
    for index in range(direct_source.DIRECT_MAX_DEPTH):
        deep = deep / f"l{index}"
    deep.mkdir(parents=True)
    (deep / "x.txt").write_text("x")
    _record(lambda: direct_source.admit_direct_source(depth))

    files = _skill(tmp_path / "files", "files")
    (files / "scripts").mkdir()
    for index in range(direct_source.DIRECT_MAX_FILES):
        (files / "scripts" / f"f{index}.txt").write_text("x")
    _record(lambda: direct_source.admit_direct_source(files))

    skills_over = tmp_path / "skills-over"
    for index in range(direct_source.DIRECT_MAX_SELECTED_SKILLS + 1):
        _skill(skills_over / "skills" / f"s{index:04d}", f"s{index:04d}")
    _record(lambda: direct_source.admit_direct_source(skills_over))

    per_file = _skill(tmp_path / "perfile", "perfile")
    (per_file / "scripts").mkdir()
    (per_file / "scripts" / "big.txt").write_bytes(
        b"x" * (direct_source.DIRECT_MAX_FILE_BYTES + 1)
    )
    _record(lambda: direct_source.admit_direct_source(per_file))

    total = _skill(tmp_path / "total", "total")
    (total / "scripts").mkdir()
    for index in range(26):
        (total / "scripts" / f"p{index}").write_bytes(
            b"x" * (direct_source.DIRECT_MAX_FILE_BYTES - 1)
        )
    _record(lambda: direct_source.admit_direct_source(total))

    # --- selection and publisher values -------------------------------------
    collection = tmp_path / "collection"
    _skill(collection / "skills" / "alpha", "alpha")
    _skill(collection / "skills" / "beta", "beta")
    admitted = direct_source.admit_direct_source(collection)
    _record(
        lambda: select_collection_skills(
            admitted, source=str(collection), requested=None, all_skills=False
        )
    )
    _record(lambda: sanitise_publisher_value("aㅤb", "description", source="s"))
    return emitted


def test_every_registered_direct_code_is_emitted_by_a_fixture(tmp_path):
    # AC31's coverage half. The raise-site scan above proves a code is wired to
    # something; this proves an input reaches it. CAT-D018 passed a set-equality
    # lint against the published table while having no raise site at all, so
    # "declared" and "reachable" are demonstrably different properties.
    from agentbundle.catalogue_tooling.diagnostics import DIRECT_CODES

    emitted = _emitted_codes(tmp_path)
    registered = {code.value for code in DIRECT_CODES}

    # Every emitted code is registered — nothing invents a string.
    assert emitted <= registered, sorted(emitted - registered)

    unreached = sorted(registered - emitted)
    assert unreached == [], (
        f"registered but reached by no fixture: {unreached}. A code the adopter "
        f"table publishes must be emittable by some input, or the table promises "
        f"a refusal that cannot happen."
    )
