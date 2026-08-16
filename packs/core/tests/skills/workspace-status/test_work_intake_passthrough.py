"""Construction test for work-intake status delegation."""

from pathlib import Path

_SKILLS = Path(__file__).resolve().parents[3] / ".apm" / "skills"


def _body(name: str) -> str:
    path = _SKILLS / name / "SKILL.md"
    if not path.is_file():
        raise NotImplementedError  # STUB: AC12
    return path.read_text(encoding="utf-8")


def test_status_passthrough() -> None:
    intake = _body("work-intake")
    status = _body("workspace-status")
    assert "workspace-status" in intake
    assert "unchanged" in intake
    assert "canonical.ready" in status
    assert "repair-plan" in status


def test_consumer_boundary_metadata() -> None:
    for name in ("work-intake", "workspace-status"):
        body = _body(name)
        assert "metadata:" in body, name
        assert "boundaries:" in body, name
        assert "allowed-tools:" in body, name
