"""Direct GitHub source acquisition: grammar, bounds, link policy, transport."""

from __future__ import annotations

import ast
import gzip
import io
import ssl
import sys
import tarfile
import urllib.error
from pathlib import Path

import agentbundle.direct_source_acquisition as acquisition
import pytest
from agentbundle.direct_source_acquisition import DirectAcquisitionError

SHA = "0123456789abcdef0123456789abcdef01234567"


def _refusal(callable_, code: str) -> DirectAcquisitionError:
    """Assert a refusal carries one registered code, and return it."""

    with pytest.raises(DirectAcquisitionError) as raised:
        callable_()
    assert raised.value.diagnostic.code == code, raised.value.diagnostic.message
    return raised.value


def _archive(members: dict[str, bytes], *, revision: str = SHA) -> bytes:
    """Build a GitHub-shaped source archive carrying a pax global header."""

    raw = io.BytesIO()
    with tarfile.open(
        fileobj=raw, mode="w", format=tarfile.PAX_FORMAT, pax_headers={"comment": revision}
    ) as archive:
        for name, payload in members.items():
            info = tarfile.TarInfo(name)
            info.size = len(payload)
            archive.addfile(info, io.BytesIO(payload))
    return gzip.compress(raw.getvalue())


def test_source_grammar_refusals():
    # AC3, AC27 — every grammar refusal carries its own registered code.
    parse = acquisition.parse_direct_source
    good = f"git+https://github.com/owner/repo@{SHA}"
    assert parse(good).ref_kind == "sha"
    assert parse(good).requested == good, "AC4: the exact string is retained"
    assert parse("git+https://github.com/owner/repo@v1.2.3").ref_kind == "ref"
    assert parse("git+https://github.com/owner/repo@abc1234").ref_kind == "abbreviated-sha"

    for source, code in [
        ("https://github.com/owner/repo@v1", "CAT-D001"),
        ("git+https://github.com/owner@v1", "CAT-D001"),
        ("git+https://github.com/owner/repo/extra@v1", "CAT-D001"),
        ("git+https://github.com/ow ner/repo@v1", "CAT-D001"),
        ("git+https://github.com/owner/repo@v1?x=1", "CAT-D001"),
        ("git+https://github.com/owner/repo@v1#frag", "CAT-D001"),
        ("git+https://user:pw@github.com/owner/repo@v1", "CAT-D001"),
        ("git+https://github.com/owner/repo@../etc", "CAT-D001"),
        ("git+https://github.com/owner/repo", "CAT-D002"),
        ("git+https://github.com/owner/repo@main", "CAT-D002"),
        ("git+https://github.com/owner/repo@HEAD", "CAT-D002"),
        # Hex-shaped but too short to be an abbreviated SHA: unclassifiable.
        ("git+https://github.com/owner/repo@abc12", "CAT-D003"),
        ("git+https://github.com/owner/repo@" + "a" * 41, "CAT-D003"),
    ]:
        _refusal(lambda s=source: parse(s), code)

    # A control code point never reaches the diagnostic path raw.
    refusal = _refusal(
        lambda: parse("git+https://github.com/owner/repo@v1\r\nInjected: yes"), "CAT-D001"
    )
    assert "\r" not in refusal.diagnostic.path and "\n" not in refusal.diagnostic.path


def test_archive_url_and_redirect_equivalence():
    # AC3, AC5 — components are percent-encoded with an empty safe set, and a
    # redirect may only reach an equivalent target.
    source = acquisition.parse_direct_source(
        "git+https://github.com/owner/repo@release/1.0"
    )
    url = acquisition.archive_url(source)
    assert url == "https://github.com/owner/repo/archive/release%2F1.0.tar.gz", url
    assert "/release/1.0" not in url, "a ref slash must not become a path segment"

    permitted = acquisition.permitted_redirect_targets(source)
    assert "https://codeload.github.com/owner/repo/tar.gz/release%2F1.0" in permitted
    assert acquisition.MAX_REDIRECTS == 5

    handler = acquisition._BoundedRedirectHandler(source)
    assert handler.max_redirections == 5
    for target in (
        "http://github.com/owner/repo/archive/release%2F1.0.tar.gz",
        "https://user:pw@codeload.github.com/owner/repo/tar.gz/release%2F1.0",
        "https://evil.example/owner/repo/archive/release%2F1.0.tar.gz",
        "https://codeload.github.com/other/repo/tar.gz/release%2F1.0",
    ):
        _refusal(
            lambda t=target: handler.redirect_request(None, None, 302, "Found", {}, t),
            "CAT-D001",
        )

    # AC18: a hostile Location never reaches the message raw.
    refusal = _refusal(
        lambda: handler.redirect_request(
            None, None, 302, "Found", {}, "https://evil.example/\r\nSet-Cookie: x\x1b[31m"
        ),
        "CAT-D001",
    )
    assert "\r" not in refusal.diagnostic.message
    assert "\x1b" not in refusal.diagnostic.message


def test_runtime_floor_fires_at_entry(monkeypatch):
    # AC5 — the floor is read at call time and refuses before any archive byte.
    assert acquisition.RUNTIME_FLOOR == {11: 13, 12: 11, 13: 4, 14: 0}
    source = f"git+https://github.com/owner/repo@{SHA}"

    class _Version(tuple):
        major, minor, micro = 3, 12, 10

    monkeypatch.setattr(sys, "version_info", _Version((3, 12, 10)))
    _refusal(lambda: acquisition.enforce_runtime_floor(source), "CAT-D005")
    # A route that never extracts still carries the floor.
    _refusal(lambda: acquisition.acquire_git_https_archive(source), "CAT-D005")

    class _Old(tuple):
        major, minor, micro = 3, 10, 20

    monkeypatch.setattr(sys, "version_info", _Old((3, 10, 20)))
    _refusal(lambda: acquisition.enforce_runtime_floor(source), "CAT-D005")

    class _Listed(tuple):
        major, minor, micro = 3, 12, 11

    monkeypatch.setattr(sys, "version_info", _Listed((3, 12, 11)))
    acquisition.enforce_runtime_floor(source)

    class _Future(tuple):
        major, minor, micro = 3, 15, 0

    monkeypatch.setattr(sys, "version_info", _Future((3, 15, 0)))
    acquisition.enforce_runtime_floor(source)


def test_injected_seams_validate_before_they_resolve():
    # AC5 — validate, then `min`. Reversing the order lets `True` through as 1,
    # silently applying the tightest bound instead of refusing.
    source = f"git+https://github.com/owner/repo@{SHA}"
    for bad in (None, True, False, "8", 1.5, -1):
        _refusal(
            lambda b=bad: acquisition._resolve_seam(b, 100, "limit", source), "CAT-D006"
        )
    assert acquisition._resolve_seam(acquisition._UNSET, 100, "limit", source) == 100
    assert acquisition._resolve_seam(10, 100, "limit", source) == 10
    # A seam may only tighten: a larger injected value does not raise the bound.
    assert acquisition._resolve_seam(1000, 100, "limit", source) == 100

    _refusal(lambda: acquisition._validated_clock("not callable", source), "CAT-D006")
    backwards = iter([10.0, 1.0])
    _refusal(
        lambda: acquisition._validated_clock(lambda: next(backwards), source), "CAT-D006"
    )
    _refusal(lambda: acquisition._validated_progress(object(), source), "CAT-D006")
    assert acquisition._validated_clock(lambda: 1.0, source)() == 1.0


def test_extraction_bounds_and_link_policy(tmp_path: Path):
    # AC6, AC27 — member destination, links, specials, and case-fold collision.
    source = acquisition.parse_direct_source(f"git+https://github.com/owner/repo@{SHA}")

    def _extract_bytes(payload: bytes, **kwargs):
        spool = tmp_path / "a.tar.gz"
        spool.write_bytes(payload)
        destination = tmp_path / "out"
        destination.mkdir(exist_ok=True)
        return acquisition._extract(
            spool,
            destination,
            source,
            max_members=kwargs.get("max_members", 20_000),
            max_decompressed=kwargs.get("max_decompressed", 1 << 30),
        )

    revision, members, _roots = _extract_bytes(_archive({"repo-1/SKILL.md": b"ok\n"}))
    assert revision == SHA and members == 1

    # Escaping and absolute destinations, built with the library's own name.
    for name in ("../escape.md", "/absolute.md", "a\\b.md", "./x/../../y.md"):
        _refusal(lambda n=name: _extract_bytes(_archive({n: b"x"})), "CAT-D007")

    # Case-fold collision: distinct in the archive, one file on macOS/Windows.
    _refusal(
        lambda: _extract_bytes(_archive({"repo/A.md": b"x", "repo/a.md": b"y"})),
        "CAT-D007",
    )

    # Member and decompressed-byte bounds.
    _refusal(
        lambda: _extract_bytes(_archive({f"repo/{i}.md": b"x" for i in range(5)}), max_members=3),
        "CAT-D006",
    )
    _refusal(
        lambda: _extract_bytes(_archive({"repo/big.md": b"x" * 4096}), max_decompressed=100),
        "CAT-D006",
    )


def test_link_and_special_members_are_direct_only_refusals(tmp_path: Path):
    # AC6 — symlink, hard link, FIFO, and device members refuse on the direct
    # route. The catalogue route deliberately keeps symlinks, so this rule
    # cannot live in shared extraction code.
    source = acquisition.parse_direct_source(f"git+https://github.com/owner/repo@{SHA}")

    def _with_member(kind: int, *, linkname: str = "target.md") -> bytes:
        raw = io.BytesIO()
        with tarfile.open(
            fileobj=raw, mode="w", format=tarfile.PAX_FORMAT, pax_headers={"comment": SHA}
        ) as archive:
            info = tarfile.TarInfo("repo/link.md")
            info.type = kind
            info.linkname = linkname
            archive.addfile(info)
        return gzip.compress(raw.getvalue())

    for kind in (tarfile.SYMTYPE, tarfile.LNKTYPE, tarfile.FIFOTYPE, tarfile.CHRTYPE):
        spool = tmp_path / "a.tar.gz"
        spool.write_bytes(_with_member(kind))
        destination = tmp_path / "out"
        destination.mkdir(exist_ok=True)
        _refusal(
            lambda s=spool, d=destination: acquisition._extract(
                s, d, source, max_members=100, max_decompressed=1 << 30
            ),
            "CAT-D007",
        )

    # An escaping link target is named as the offender, not the member.
    spool = tmp_path / "b.tar.gz"
    spool.write_bytes(_with_member(tarfile.SYMTYPE, linkname="../../etc/passwd"))
    destination = tmp_path / "out2"
    destination.mkdir()
    refusal = _refusal(
        lambda: acquisition._extract(
            spool, destination, source, max_members=100, max_decompressed=1 << 30
        ),
        "CAT-D007",
    )
    assert "escapes the root" in refusal.diagnostic.message


def test_revision_binding_to_the_requested_ref(tmp_path: Path):
    # AC3 — the archive SHA binds the installed bytes to the requested source.
    def _revision_for(requested: str, recorded: str):
        source = acquisition.parse_direct_source(requested)
        spool = tmp_path / "a.tar.gz"
        spool.write_bytes(_archive({"repo/SKILL.md": b"x"}, revision=recorded))
        destination = tmp_path / f"out-{abs(hash((requested, recorded)))}"
        destination.mkdir()
        return acquisition._extract(
            spool, destination, source, max_members=100, max_decompressed=1 << 30
        )[0]

    assert _revision_for(f"git+https://github.com/o/r@{SHA}", SHA) == SHA
    assert _revision_for("git+https://github.com/o/r@v1.0", SHA) == SHA
    assert _revision_for("git+https://github.com/o/r@0123456", SHA) == SHA
    # A moved 40-hex ref, a non-extending abbreviation, and an absent SHA.
    _refusal(lambda: _revision_for(f"git+https://github.com/o/r@{SHA}", "f" * 40), "CAT-D004")
    _refusal(lambda: _revision_for("git+https://github.com/o/r@fedcba9", SHA), "CAT-D004")
    _refusal(lambda: _revision_for("git+https://github.com/o/r@v1.0", "not-a-sha"), "CAT-D004")


def test_transport_classification_is_separable_and_shared(monkeypatch, tmp_path: Path):
    # AC37 — the shared entry point returns a classified outcome carrying the
    # originating exception, and separates four failures a smaller enum could
    # not. It never raises and never formats a message.
    from agentbundle import catalogue

    cert_error = ssl.SSLCertVerificationError("certificate verify failed")
    cases = [
        (urllib.error.URLError(cert_error), True),
        (urllib.error.URLError(ssl.SSLError("handshake alert")), False),
        (urllib.error.HTTPError("u", 404, "Not Found", {}, None), False),
        (TimeoutError("timed out"), False),
    ]
    monkeypatch.setattr(catalogue, "_system_trust_module", lambda: _StubTrust())
    for exception, expected_cert in cases:

        def attempt(context, exc=exception):
            raise exc

        outcome = catalogue.classify_transport_attempt(attempt)
        assert outcome.ok is False
        assert outcome.exception is exception, "the originating exception is carried"
        assert outcome.certificate_failure is expected_cert, exception

    # A non-2xx HTTPError stays distinguishable from the URLError it subclasses.
    http, url_error = cases[2][0], cases[1][0]
    assert isinstance(http, urllib.error.URLError)
    assert http is not url_error

    assert catalogue.classify_transport_attempt(lambda context: None).ok is True


class _StubTrust:
    """A trust module that reports no anchors and no opt-out."""

    def build_context(self):
        return ssl.create_default_context()

    def system_trust_disabled(self):
        return False

    def default_store_is_empty(self):
        return False

    def system_anchor_pem(self, include_public_roots=False):
        return ""


def test_acquisition_holds_no_second_copy_of_the_classifier():
    # AC37 — a per-route restatement of the classifier or the retry would pass
    # every other arm in this module while drifting from the catalogue route.
    module = Path(acquisition.__file__)
    tree = ast.parse(module.read_text(encoding="utf-8"))

    functions = {
        node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
    }
    assert "classify_transport_attempt" not in functions
    assert not any("system_trust" in name for name in functions), functions

    source = module.read_text(encoding="utf-8")
    # Checked against the module's *code*, not its text. A docstring that
    # explains why this module does not build its own context would otherwise
    # trip a ban on building one — a comment about a rule reading as a
    # violation of it.
    #
    # The earlier version of this list also banned `system_anchor_pem` and
    # `default_store_is_empty` as raw text, which pinned the absence of AC37's
    # retry rather than the absence of a second copy of it: the module consumed
    # neither, and the test called that correct.
    referenced = {
        node.attr if isinstance(node, ast.Attribute) else node.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Attribute | ast.Name)
    }
    for restated in (
        "_is_cert_verification_failure",
        "build_context",
        "PROTOCOL_TLS_CLIENT",
    ):
        assert restated not in referenced, (
            f"{restated} is called in the direct module; it belongs to the "
            f"one shared entry point in catalogue.py"
        )
    assert not any(
        name.startswith("_retry") for name in functions
    ), "the trust retry belongs to catalogue.py, not to a per-route copy"
    # Both halves of AC37's seam are consumed, not just the classifier.
    assert "classify_transport_attempt" in source, "the shared classifier must be used"
    assert "retry_with_system_trust" in source, (
        "AC37's single system-trust retry must be performed on this route too"
    )


def test_the_classified_context_reaches_the_request(monkeypatch, tmp_path: Path):
    # AC37 — an opener built without an HTTPSHandler silently uses urllib's
    # ambient default context, so `build_context()`'s additive
    # `load_verify_locations` never reaches the socket and AGENTBUNDLE_CA_BUNDLE
    # is inert. Nothing else here would notice: every other assertion in this
    # module passes with the context dropped.
    import urllib.request

    source = acquisition.parse_direct_source(f"git+https://github.com/o/r@{SHA}")
    sentinel = ssl.create_default_context()
    seen: dict[str, object] = {}

    real_build_opener = urllib.request.build_opener

    def _capture(*handlers):
        for handler in handlers:
            if isinstance(handler, urllib.request.HTTPSHandler):
                seen["context"] = handler._context
        return real_build_opener(*handlers)

    monkeypatch.setattr(urllib.request, "build_opener", _capture)
    # The fetch itself fails — there is no server. What matters is which
    # context the opener was built with before it tried.
    with pytest.raises(urllib.error.URLError):
        acquisition._download(
            "https://github.com/o/r/archive/x.tar.gz",
            source,
            tmp_path / "spool",
            context=sentinel,
            max_bytes=1024,
            inactivity=90,
            clock=lambda: 0.0,
            progress=None,
        )
    assert seen.get("context") is sentinel, (
        "the classified context must reach the request, not urllib's default"
    )


def test_bounds_match_the_recorded_e11_values():
    # AC5 — the module constants are the bound of record; a silent change here
    # is a policy change that `Ask first` governs.
    assert acquisition.MAX_DOWNLOAD_BYTES == 256 * 1024 * 1024
    assert acquisition.MAX_ARCHIVE_MEMBERS == 20_000
    assert acquisition.MAX_DECOMPRESSED_BYTES == 1024 * 1024 * 1024
    assert acquisition.SOCKET_TIMEOUT_SECONDS == 30
    assert acquisition.INACTIVITY_TIMEOUT_SECONDS == 90
    assert acquisition.LIST_INSTALLED_CHECK_DEADLINE_SECONDS == 90
    assert acquisition.LIST_INSTALLED_CHECK_MAX_RESOLUTIONS == 25


def test_the_github_wrapper_directory_is_descended(tmp_path: Path):
    # A GitHub source archive prefixes every member with `<repo>-<ref>/`, and
    # admission looks for `SKILL.md`, `skills/`, or `pack.toml` — none of which
    # sit beside that wrapper. Acquisition must return the source root.
    #
    # This is the defect a live remote run found and these fixtures had missed:
    # every archive built here previously placed members at the archive root,
    # so acquisition and admission were each correct in isolation and did not
    # join. The prefix is derived from the member names rather than by listing
    # the extracted tree.
    from agentbundle.direct_source import validate_direct_source

    source = acquisition.parse_direct_source(f"git+https://github.com/o/r@{SHA}")
    wrapper = f"r-{SHA}"
    payload = _archive(
        {
            f"{wrapper}/README.md": b"# repo\n",
            f"{wrapper}/skills/alpha/SKILL.md": b"---\nname: alpha\n---\n# alpha\n",
        }
    )
    spool = tmp_path / "a.tar.gz"
    spool.write_bytes(payload)
    destination = tmp_path / "out"
    destination.mkdir()

    revision, members, roots = acquisition._extract(
        spool, destination, source, max_members=100, max_decompressed=1 << 30
    )
    assert revision == SHA
    assert roots == {wrapper}, "the single root segment is the wrapper"

    # Descending is what makes the two halves join.
    descended = destination / wrapper
    assert validate_direct_source(destination).ok is False
    admitted = validate_direct_source(descended)
    assert admitted.ok is True, admitted.diagnostics
    assert admitted.classification is not None
    assert admitted.classification.shape == "collection"


def test_members_at_the_archive_root_are_not_descended_into(tmp_path: Path):
    # The positive control for the rule above. An archive whose members really
    # do sit at its root has more than one first segment, so nothing is
    # descended — a rule written as "if there is one directory, enter it" would
    # wrongly enter a lone `skills/`.
    source = acquisition.parse_direct_source(f"git+https://github.com/o/r@{SHA}")
    payload = _archive({"SKILL.md": b"---\nname: a\n---\n# a\n", "README.md": b"x"})
    spool = tmp_path / "b.tar.gz"
    spool.write_bytes(payload)
    destination = tmp_path / "out2"
    destination.mkdir()
    _, _, roots = acquisition._extract(
        spool, destination, source, max_members=100, max_decompressed=1 << 30
    )
    assert len(roots) > 1, "no single wrapper segment, so nothing to descend"


def test_the_working_directory_is_carried_not_derived():
    # `AcquiredArchive` declares the tree its caller must remove. Deriving it by
    # walking up from `root` is wrong the moment `root` is not nested at the
    # expected depth: with no wrapper to descend through, two levels up from
    # `root` is the system temporary directory, and the cleanup would delete it.
    import dataclasses

    fields = {field.name for field in dataclasses.fields(acquisition.AcquiredArchive)}
    assert "working" in fields, (
        "the caller-owned temporary directory must be declared, not inferred "
        "from the root's depth"
    )


def test_the_decompressed_bound_measures_bytes_read_not_declared_sizes(tmp_path: Path):
    # E11 bounds "incrementally measured decompressed bytes on the decompressed
    # side of gzip". Summing `TarInfo.size` measures what the archive DECLARES
    # in its headers, which a hostile archive controls independently of what it
    # ships. This fixture is the plan's: declared member sizes stay tiny while
    # the decompressed stream is far larger, so only a reader-side counter can
    # see it.
    source = acquisition.parse_direct_source(f"git+https://github.com/o/r@{SHA}")

    # Every member declares 8 bytes, but tar pads each to a 512-byte block and
    # prefixes a 512-byte header — so the stream carries roughly 128x what the
    # headers claim. Forty members declare 320 bytes and read past 40 KiB.
    members = 40
    raw = io.BytesIO()
    with tarfile.open(
        fileobj=raw, mode="w", format=tarfile.PAX_FORMAT, pax_headers={"comment": SHA}
    ) as archive:
        for index in range(members):
            info = tarfile.TarInfo(f"repo/small{index}.txt")
            info.size = 8
            archive.addfile(info, io.BytesIO(b"x" * 8))
    payload = gzip.compress(raw.getvalue())

    spool = tmp_path / "lying.tar.gz"
    spool.write_bytes(payload)
    destination = tmp_path / "out"
    destination.mkdir()

    declared_total = members * 8
    bound = 4096
    assert declared_total < bound, "the declared sizes must stay under the bound"

    refusal = _refusal(
        lambda: acquisition._extract(
            spool, destination, source, max_members=100, max_decompressed=bound
        ),
        "CAT-D006",
    )
    assert "read" in refusal.diagnostic.message, (
        "the refusal must report bytes read, not the declared total"
    )
