"""``resolve_git_ref`` — spec/catalogue-sync-apply T1.

AC-0037's ``git+https://`` row records the ref the URI names, or ``"main"``
when none is given. This module asserts that value is readable without a
fetch, and that ``_resolve_https`` reads it from the same parse rather than a
second one that could disagree.
"""

from __future__ import annotations

from agentbundle.catalogue import _github_archive_url, resolve_git_ref


def test_explicit_ref_is_returned():
    uri = "git+https://github.com/owner/repo@v1.2.3"
    assert resolve_git_ref(uri) == "v1.2.3"


def test_missing_ref_defaults_to_main():
    uri = "git+https://github.com/owner/repo"
    assert resolve_git_ref(uri) == "main"


def test_local_path_yields_none():
    assert resolve_git_ref("./some/local/path") is None


def test_archive_https_yields_none():
    uri = "archive+https://example.test/owner/repo/archive.tar.gz#sha256=deadbeef"
    assert resolve_git_ref(uri) is None


def test_catalogue_https_yields_none():
    uri = "catalogue+https://example.test/catalogue.tar.gz#sha256=deadbeef"
    assert resolve_git_ref(uri) is None


def test_resolve_https_builds_its_archive_url_from_the_same_ref(monkeypatch):
    """The fetch's ref and the pin's ref must be the same value.

    Rather than asserting each is separately "correct", this pins the
    invariant the plan requires: whatever ``resolve_git_ref`` returns for a
    URI is the exact ref ``_github_archive_url`` receives when
    ``_resolve_https`` builds its tarball URL. A change to the default in one
    place reaches both call sites because there is only one parse.
    """
    captured: dict[str, str] = {}
    real_github_archive_url = _github_archive_url

    def _spy(owner: str, repo: str, ref: str) -> str:
        captured["ref"] = ref
        return real_github_archive_url(owner, repo, ref)

    monkeypatch.setattr("agentbundle.catalogue._github_archive_url", _spy)

    # No real fetch is exercised: only that _resolve_https requests the
    # archive URL for the same ref resolve_git_ref names.
    import agentbundle.catalogue as catalogue_module

    def _no_fetch(url: str, dest) -> None:
        return None

    monkeypatch.setattr(catalogue_module, "_fetch_and_extract", _no_fetch)
    monkeypatch.setattr(
        catalogue_module,
        "_find_inner_dir",
        lambda tmpdir: tmpdir,
    )

    uri = "git+https://github.com/owner/repo@v1.2.3"
    catalogue_module._resolve_https(uri)

    assert captured["ref"] == resolve_git_ref(uri) == "v1.2.3"
