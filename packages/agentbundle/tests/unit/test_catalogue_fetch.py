# STUB: AC-0008 — a fetch session resolves one provider for the acquisition
from agentbundle.catalogue_fetch import open_fetch_session


def test_open_fetch_session_resolves_anonymous_access_once() -> None:
    with open_fetch_session(
        "https://catalogue.example.test/root/catalogue.toml",
        env={},
    ) as session:
        assert session.provider == "anonymous"
        assert session.target_origin == "https://catalogue.example.test"
