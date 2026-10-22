"""The pack-evals Claude Code projection uses the bundled adapter contract."""

from __future__ import annotations

from pathlib import Path

from agentbundle.commands.pack_evals import ClaudeCodeDetector


def test_projection_ignores_catalogue_contracts_folder(tmp_path: Path) -> None:
    root = tmp_path / "cat"
    (root / "contracts").mkdir(parents=True)
    (root / "contracts" / "adapter.toml").write_text(
        "this is [[[ not toml\n", encoding="utf-8", newline="\n"
    )
    pack = tmp_path / "pack"
    skill = pack / ".apm" / "skills" / "demo-skill"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text(
        "---\nname: demo-skill\ndescription: A demo skill.\n---\nBody.\n",
        encoding="utf-8",
        newline="\n",
    )
    (pack / "pack.toml").write_text(
        '[pack]\nname = "demo"\nversion = "0.1.0"\ndescription = "d"\n',
        encoding="utf-8",
        newline="\n",
    )
    out = tmp_path / "out"
    out.mkdir()
    ClaudeCodeDetector().project(pack, out, catalogue_root=root)
    projected = list(out.rglob("SKILL.md"))
    assert projected, "expected the projected skill under the output root"
