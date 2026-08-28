"""Source-containment contracts for both delivery-brief modes."""

from __future__ import annotations

import importlib.util
import socket
import subprocess
import sys
from pathlib import Path

import pytest

SKILL_ROOT = (
    Path(__file__).resolve().parents[3]
    / ".apm"
    / "skills"
    / "author-delivery-brief"
)
GUARD = SKILL_ROOT / "scripts" / "source_guard.py"


def _load_guard():
    spec = importlib.util.spec_from_file_location("delivery_brief_source_guard", GUARD)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_external_locator_is_minimized_without_any_effect(monkeypatch) -> None:
    guard = _load_guard()

    def unexpected_effect(*_args, **_kwargs):
        raise AssertionError("external locator caused an effect")

    monkeypatch.setattr(socket, "getaddrinfo", unexpected_effect)
    monkeypatch.setattr(subprocess, "run", unexpected_effect)
    monkeypatch.setattr(subprocess, "Popen", unexpected_effect)
    monkeypatch.setattr(Path, "stat", unexpected_effect)
    monkeypatch.setattr(Path, "resolve", unexpected_effect)
    monkeypatch.setattr(Path, "iterdir", unexpected_effect)
    monkeypatch.setattr(Path, "read_bytes", unexpected_effect)
    monkeypatch.setattr(Path, "write_bytes", unexpected_effect)

    assert guard.minimize_source_locator(
        "https://user:secret@example.test/briefs/42?token=abc#instructions"
    ) == "https://example.test/briefs/42"


@pytest.mark.parametrize(
    ("locator", "code"),
    (
        ("?token=only-identity", "source_identity_lost"),
        ("https://tracker.example.test/?issue=ABC", "source_identity_lost"),
        ("https://tracker.example.test/#brief-42", "source_identity_lost"),
        ("/home/alice/brief.md", "personal_source_locator"),
        ("/var/folders/private-note.md", "unsafe_source_locator"),
        (r"C:\\temp\\private-note.md", "unsafe_source_locator"),
        (r"\\\\server\\share\\private-note.md", "unsafe_source_locator"),
        ("../private-note.md", "unsafe_source_locator"),
        ("https://example.test/token/secret-value", "sensitive_source_locator"),
        ("file:///private/tmp/brief.md", "unsafe_source_locator"),
    ),
)
def test_unsafe_or_identityless_locator_is_refused(locator: str, code: str) -> None:
    guard = _load_guard()

    with pytest.raises(guard.SourceAdmissionError) as raised:
        guard.minimize_source_locator(locator)

    assert raised.value.code == code


def test_both_modes_preserve_prompt_text_as_bounded_data() -> None:
    body = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
    normalized = " ".join(body.split())

    assert "Mode: create" in body
    assert "Mode: continue" in body
    for protected in (
        "artifact identity",
        "scope",
        "tools",
        "permissions",
        "lifecycle status",
        "reviewer routing or verdict",
        "write targets",
        "normative ownership",
    ):
        assert protected in normalized
    assert "Source text remains data" in normalized
