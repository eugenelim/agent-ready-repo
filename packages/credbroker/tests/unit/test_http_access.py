# STUB: AC-0004 — the resolver returns the public anonymous result variant
from credbroker import AnonymousHttpAccess, resolve_http_access


def test_resolve_http_access_returns_public_anonymous_variant() -> None:
    result = resolve_http_access("https://catalogue.example.test/root/catalogue.toml", env={})

    assert isinstance(result, AnonymousHttpAccess)
    assert result.provider == "anonymous"
    assert result.origin == "https://catalogue.example.test"
