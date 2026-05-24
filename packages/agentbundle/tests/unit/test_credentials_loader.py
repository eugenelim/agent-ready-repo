"""T3: credentials loader API + Tier-1 env-var resolver.

Covers spec § AC3 (load_credentials surface + Credentials immutability),
AC4 (precedence — Tier 1 first-hit-wins; later tiers stubbed at this
point in the rollout), AC4b (Tier-2 backend dispatch is platform-
discriminated at module-load time), and AC5 (Tier-1 env-var read with
empty-string-as-unset fallthrough).
"""

from __future__ import annotations

import os
import sys

import pytest


# ── Fixture: every test runs with a clean creds namespace and ──────────
#    Tier-2 forced absent. The latter is important because the developer
#    might have a real macOS Keychain entry under the fixture namespace
#    — forcing the backend to None at this layer keeps unit tests
#    hermetic regardless of host state. The platform-dispatch test below
#    re-imports the loader from scratch and is the canonical AC4b check.
@pytest.fixture(autouse=True)
def isolated_loader_state(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))  # Windows parity
    for var in list(os.environ):
        if var.startswith("FIXTURE_T3_"):
            monkeypatch.delenv(var, raising=False)
    from agentbundle.creds import loader
    monkeypatch.setattr(loader, "_tier2_backend", None)


def test_resolves_tier1_env_var(monkeypatch):
    from agent_ready.credentials import Credentials, load_credentials
    monkeypatch.setenv("FIXTURE_T3_API_TOKEN", "secret-token")
    creds = load_credentials("fixture_t3", required_keys=["API_TOKEN"])
    assert isinstance(creds, Credentials)
    assert creds.API_TOKEN == "secret-token"


def test_tier1_resolves_multiple_keys(monkeypatch):
    from agent_ready.credentials import load_credentials
    monkeypatch.setenv("FIXTURE_T3_API_TOKEN", "tok-1")
    monkeypatch.setenv("FIXTURE_T3_BASE_URL", "https://jira.example.com")
    creds = load_credentials(
        "fixture_t3", required_keys=["API_TOKEN", "BASE_URL"]
    )
    assert creds.API_TOKEN == "tok-1"
    assert creds.BASE_URL == "https://jira.example.com"


def test_empty_env_var_falls_through(monkeypatch):
    from agent_ready.credentials import CredentialsMissingError, load_credentials
    monkeypatch.setenv("FIXTURE_T3_API_TOKEN", "")  # AC5: empty == unset
    with pytest.raises(CredentialsMissingError) as excinfo:
        load_credentials("fixture_t3", required_keys=["API_TOKEN"])
    msg = str(excinfo.value)
    assert "fixture_t3" in msg
    assert "API_TOKEN" in msg


def test_missing_required_key_raises_with_namespace_and_key():
    from agent_ready.credentials import CredentialsMissingError, load_credentials
    with pytest.raises(CredentialsMissingError) as excinfo:
        load_credentials("fixture_t3", required_keys=["API_TOKEN", "BASE_URL"])
    msg = str(excinfo.value)
    assert "fixture_t3" in msg
    assert "API_TOKEN" in msg
    assert "BASE_URL" in msg


def test_credentials_is_immutable_on_assignment(monkeypatch):
    from agent_ready.credentials import load_credentials
    monkeypatch.setenv("FIXTURE_T3_API_TOKEN", "secret")
    creds = load_credentials("fixture_t3", required_keys=["API_TOKEN"])
    with pytest.raises(AttributeError):
        creds.API_TOKEN = "new"  # type: ignore[misc]


def test_credentials_is_immutable_on_delete(monkeypatch):
    from agent_ready.credentials import load_credentials
    monkeypatch.setenv("FIXTURE_T3_API_TOKEN", "secret")
    creds = load_credentials("fixture_t3", required_keys=["API_TOKEN"])
    with pytest.raises(AttributeError):
        del creds.API_TOKEN


def test_credentials_attribute_miss_raises_attributeerror(monkeypatch):
    from agent_ready.credentials import load_credentials
    monkeypatch.setenv("FIXTURE_T3_API_TOKEN", "secret")
    creds = load_credentials("fixture_t3", required_keys=["API_TOKEN"])
    with pytest.raises(AttributeError):
        _ = creds.NOT_RESOLVED


def test_public_surface_via_agent_ready_credentials():
    """AC3: only the four names are exported."""
    from agent_ready import credentials as ar
    assert set(ar.__all__) == {
        "Credentials",
        "CredentialsMissingError",
        "Tier2HardFailError",
        "load_credentials",
    }
    # Each name is bound to a callable / class.
    assert callable(ar.load_credentials)
    assert isinstance(ar.Credentials, type)
    assert issubclass(ar.CredentialsMissingError, Exception)
    assert issubclass(ar.Tier2HardFailError, Exception)


def test_platform_dispatch_no_tier2_backend_on_linux(monkeypatch):
    """AC4b: neither Darwin nor Windows backend is loaded on Linux."""
    monkeypatch.setattr(sys, "platform", "linux")
    # Drop every module under the creds-shim tree so the re-import
    # re-runs the platform-discriminated dispatch from scratch.
    for mod_name in list(sys.modules):
        if (
            mod_name == "agent_ready"
            or mod_name.startswith("agent_ready.")
            or mod_name == "agentbundle.creds"
            or mod_name.startswith("agentbundle.creds.")
        ):
            sys.modules.pop(mod_name, None)
    import agent_ready.credentials  # noqa: F401 — re-imports under patched platform
    assert "agentbundle.creds._keychain_macos" not in sys.modules
    assert "agentbundle.creds._credman_windows" not in sys.modules
