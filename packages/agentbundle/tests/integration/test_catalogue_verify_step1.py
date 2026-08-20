"""Step-1 catalogue configuration regressions."""

from agentbundle.catalogue_tooling.verify import verify_catalogue


def test_malformed_catalogue_toml_returns_bounded_diagnostic(tmp_path):
    secret = "sensitive-value"
    (tmp_path / "catalogue.toml").write_text(
        f'[catalogue\nname = "{secret}"\n', encoding="utf-8"
    )
    result = verify_catalogue(tmp_path)
    findings = [item for item in result.diagnostics if item.code == "CAT-V-001"]
    assert findings
    rendered = " ".join(item.message for item in findings)
    assert secret not in rendered
    assert str(tmp_path) not in rendered


def test_absent_catalogue_toml_does_not_create_step1_diagnostic(tmp_path):
    result = verify_catalogue(tmp_path)
    assert not [item for item in result.diagnostics if item.code == "CAT-V-001"]
