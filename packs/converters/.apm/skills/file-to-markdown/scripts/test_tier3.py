"""Tests for tier3.py — the transport-free Tier-3 managed-API assembly interface.

Covers the declaration validator (fail-closed refusals, SSRF-adjacent /
credential-smuggling guards), the assembled contract (tier / fixed low confidence
/ requires-review, content-type derivation, auditable egress provenance), and the
injection-safety of the echoed provenance values. The vendor OCR read itself is
external and not asserted here — only the deterministic gate + stamp around it.

Run with `python -m pytest` from this directory.
"""
from __future__ import annotations

from pathlib import Path

import pytest

import contract
import tier3


def _valid_decl():
    return {"endpoint-allowlist": ["ocr.vendor.example"], "residency-region": "eu-west-1"}


def frontmatter_and_body(text: str):
    lines = text.splitlines()
    assert lines[0] == "---"
    end = lines.index("---", 1)
    return lines[1:end], lines[end + 1:]


# --- AC4: declaration validation (fail-closed) ------------------------------


def test_valid_declaration_returns_cleaned_endpoints_and_residency():
    endpoints, residency = tier3.validate_declaration(_valid_decl())
    assert endpoints == ["ocr.vendor.example"]
    assert residency == "eu-west-1"


@pytest.mark.parametrize("bad", ["", " ", "*", ".", "0.0.0.0", "::"])
def test_rejects_wildcard_and_catchall_endpoints(bad):
    decl = {"endpoint-allowlist": [bad], "residency-region": "eu"}
    with pytest.raises(tier3.DeclarationError):
        tier3.validate_declaration(decl)


@pytest.mark.parametrize("ip", [
    "127.0.0.1",              # loopback
    "169.254.169.254",        # link-local metadata (AWS/GCP IMDS)
    "10.0.0.5",               # RFC-1918 private
    "192.168.1.1",            # RFC-1918 private
    "::1",                    # IPv6 loopback
    "fe80::1",                # IPv6 link-local
    "fc00::1",                # IPv6 ULA (private)
    "::ffff:169.254.169.254", # IPv4-mapped IPv6 metadata — the sharp case
    "::ffff:127.0.0.1",       # IPv4-mapped IPv6 loopback
])
def test_rejects_internal_ip_targets(ip):
    decl = {"endpoint-allowlist": [ip], "residency-region": "eu"}
    with pytest.raises(tier3.DeclarationError):
        tier3.validate_declaration(decl)


@pytest.mark.parametrize("host", ["localhost", "sub.localhost", "metadata",
                                  "metadata.google.internal", "svc.internal"])
def test_rejects_metadata_and_loopback_hostnames(host):
    decl = {"endpoint-allowlist": [host], "residency-region": "eu"}
    with pytest.raises(tier3.DeclarationError):
        tier3.validate_declaration(decl)


@pytest.mark.parametrize("bad", ["::/0", "0.0.0.0/0", "10.0.0.0/8"])
def test_rejects_cidr_and_malformed_literals(bad):
    """A CIDR / over-broad literal is rejected, not silently treated as a hostname."""
    decl = {"endpoint-allowlist": [bad], "residency-region": "eu"}
    with pytest.raises(tier3.DeclarationError):
        tier3.validate_declaration(decl)


def test_rejects_absent_or_empty_residency():
    for residency in ["", "   "]:
        decl = {"endpoint-allowlist": ["ok.example"], "residency-region": residency}
        with pytest.raises(tier3.DeclarationError):
            tier3.validate_declaration(decl)


def test_rejects_empty_endpoint_list():
    with pytest.raises(tier3.DeclarationError):
        tier3.validate_declaration({"endpoint-allowlist": [], "residency-region": "eu"})


def test_rejects_unknown_field_credential_smuggling():
    """AC4/AC5: key set must equal EXACTLY the two allowed keys — an auth-looking
    extra field (or any unknown field) is refused."""
    for extra in ("authorization", "x-api-key", "token", "password"):
        decl = {**_valid_decl(), extra: "secret-value"}
        with pytest.raises(tier3.DeclarationError, match="exactly"):
            tier3.validate_declaration(decl)


def test_rejects_non_mapping_declaration():
    with pytest.raises(tier3.DeclarationError):
        tier3.validate_declaration(["ocr.vendor.example"])  # type: ignore[arg-type]


def test_accepts_multiple_public_hosts():
    endpoints, _ = tier3.validate_declaration(
        {"endpoint-allowlist": ["a.example", "b.example ", " c.example"],
         "residency-region": "us"})
    assert endpoints == ["a.example", "b.example", "c.example"]  # stripped


# --- AC4/AC10: assembled contract -------------------------------------------


def test_assemble_stamps_tier3_low_requires_review(tmp_path):
    ocr = tmp_path / "vendor_out.txt"
    ocr.write_text("Extracted invoice text from the vendor OCR.\n")
    md = tier3.assemble_tier3(ocr, "invoice.pdf", _valid_decl())
    fm, body = frontmatter_and_body(md)
    fm_text = "\n".join(fm)  # nested keys are indented, so match on the block text
    assert f'tier: "{contract.TIER_3}"' in fm_text
    assert 'content-type: "pdf"' in fm_text             # from the --source suffix
    assert 'extraction-confidence: "low"' in fm_text    # fixed — unverified vendor OCR
    assert "requires-review: true" in fm_text
    assert 'egress-endpoint: "ocr.vendor.example"' in fm_text
    assert 'egress-residency: "eu-west-1"' in fm_text
    assert "Extracted invoice text" in "\n".join(body)


def test_content_type_falls_back_to_managed_ocr(tmp_path):
    ocr = tmp_path / "out.txt"
    ocr.write_text("text")
    md = tier3.assemble_tier3(ocr, "no_suffix_source", _valid_decl())
    fm, _ = frontmatter_and_body(md)
    assert 'content-type: "managed-ocr"' in fm


def test_endpoint_is_comma_joined_scalar(tmp_path):
    ocr = tmp_path / "out.txt"
    ocr.write_text("text")
    decl = {"endpoint-allowlist": ["a.example", "b.example"], "residency-region": "eu"}
    fm, _ = frontmatter_and_body(tier3.assemble_tier3(ocr, "s.pdf", decl))
    assert 'egress-endpoint: "a.example,b.example"' in fm


def test_assemble_refuses_before_reading_on_bad_declaration(tmp_path):
    """Fail-closed: a malformed declaration refuses even when the OCR file is absent
    (validation runs before any read, so nothing is ever stamped)."""
    with pytest.raises(tier3.DeclarationError):
        tier3.assemble_tier3(tmp_path / "missing.txt", "s.pdf",
                             {"endpoint-allowlist": ["*"], "residency-region": "eu"})


def test_ocr_text_read_through_check_input_size(tmp_path, monkeypatch):
    """AC4: the --ocr-text input is read through safe_io.check_input_size (the
    unbounded-read DoS guard) — a ceiling refusal propagates, no output stamped."""
    import safe_io
    ocr = tmp_path / "big.txt"
    ocr.write_text("text")
    seen: dict = {}

    def fake_check(path, **kw):
        seen["path"] = Path(path)
        raise safe_io.ResourceCeilingError("over ceiling")

    monkeypatch.setattr(safe_io, "check_input_size", fake_check)
    with pytest.raises(safe_io.ResourceCeilingError):
        tier3.assemble_tier3(ocr, "s.pdf", _valid_decl())
    assert seen["path"] == ocr  # the guard was invoked on the OCR-text path


# --- AC4: injection-safe provenance -----------------------------------------


def test_injection_bearing_endpoint_is_escaped_not_break_out(tmp_path):
    """An endpoint element carrying a newline + forged fence is escaped by the
    contract emitter — it cannot open a second frontmatter block or forge a key."""
    ocr = tmp_path / "out.txt"
    ocr.write_text("body")
    decl = {"endpoint-allowlist": ['evil.example\n---\ninjected: "true"'],
            "residency-region": "eu"}
    md = tier3.assemble_tier3(ocr, "s.pdf", decl)
    fm, body = frontmatter_and_body(md)
    # the whole hostile value is one escaped scalar in the block; no forged key leaks
    assert not any(ln.strip().startswith("injected:") for ln in fm)
    assert "\\n" in "\n".join(fm)  # the newline was escaped, not emitted raw


def test_injection_bearing_source_name_is_escaped(tmp_path):
    ocr = tmp_path / "out.txt"
    ocr.write_text("body")
    md = tier3.assemble_tier3(ocr, 'doc\n---\ninjected: "true"', _valid_decl())
    fm, _ = frontmatter_and_body(md)
    assert not any(ln.strip().startswith("injected:") for ln in fm)
