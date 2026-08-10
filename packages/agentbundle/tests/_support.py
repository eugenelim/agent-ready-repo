"""Small fixture builders shared by the self-contained engine suite."""

from __future__ import annotations

from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = PACKAGE_ROOT / "agentbundle" / "_data"

_USER_PACKS = frozenset({
    "architect",
    "atlassian",
    "contracts",
    "converters",
    "credential-brokers",
    "desk-research",
})


def bundled_data_path(relative_path: str) -> Path:
    """Return a source-tree path to one installed engine data resource."""
    return DATA_ROOT / relative_path


def stage_installable_pack(
    catalogue_root: Path,
    name: str,
    pack_toml: str,
) -> Path:
    """Write one installable pack with caller-owned manifest semantics."""
    pack = catalogue_root / "packs" / name
    pack.mkdir(parents=True)
    (pack / "pack.toml").write_text(pack_toml, encoding="utf-8", newline="\n")
    skill = pack / ".apm" / "skills" / "dummy"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text(
        "---\nname: dummy\ndescription: Fixture skill.\n---\nFixture skill.\n",
        encoding="utf-8",
        newline="\n",
    )
    return pack


def stage_primitives(
    pack: Path,
    *,
    skills: tuple[str, ...] = (),
    agents: tuple[str, ...] = (),
) -> None:
    """Add named skill and agent primitives to a staged pack."""
    for name in skills:
        skill = pack / ".apm" / "skills" / name
        skill.mkdir(parents=True, exist_ok=True)
        (skill / "SKILL.md").write_text(
            f"---\ndescription: Fixture {name}.\n---\nFixture.\n",
            encoding="utf-8",
            newline="\n",
        )
    for name in agents:
        agent = pack / ".apm" / "agents" / f"{name}.md"
        agent.parent.mkdir(parents=True, exist_ok=True)
        agent.write_text(
            f"---\nname: {name}\ndescription: Fixture agent.\n"
            "tools: Read\n---\n\n# Fixture agent\n",
            encoding="utf-8",
            newline="\n",
        )


def materialize_catalogue(
    destination: Path,
    *,
    packs: tuple[str, ...],
    profiles: tuple[str, ...] = (),
) -> Path:
    """Materialise a small engine-behaviour catalogue at *destination*."""
    destination.mkdir(parents=True)
    for name in packs:
        user_scope = name in _USER_PACKS
        default_scope = "user" if user_scope else "repo"
        scopes = '["user", "repo"]' if user_scope else '["repo"]'
        dependencies = ""
        if name == "governance-extras":
            dependencies = """
[[pack.dependencies.required]]
catalogue = "fixture"
pack = "core"
version = "^2.0"
"""
        elif name == "atlassian":
            dependencies = """
[[pack.dependencies.required]]
catalogue = "fixture"
pack = "credential-brokers"
version = "^0.1"
"""
        allowed_adapters = (
            '\nallowed-adapters = ["claude-code", "kiro-ide", "kiro", '
            '"codex", "copilot", "cursor", "gemini"]'
            if user_scope
            else ""
        )
        version = "2.0.0" if name == "core" else "0.1.0"
        pack = stage_installable_pack(
            destination,
            name,
            f"""\
[pack]
name = "{name}"
version = "{version}"
[pack.adapter-contract]
version = "0.8"
{dependencies}[pack.install]
default-scope = "{default_scope}"
allowed-scopes = {scopes}{allowed_adapters}
""",
        )
        skills: tuple[str, ...] = (f"{name}-skill",)
        agents: tuple[str, ...] = ()
        if name == "core":
            skills = ("work-loop", "security-checklists", "operational-safety")
            agents = ("quality-engineer",)
        elif name == "governance-extras":
            skills = ("new-rfc", "new-adr", "update-conventions")
        elif name == "converters":
            skills = ("file-to-markdown", "markdown-to-html", "msg-to-markdown")
        elif name == "desk-research":
            skills = (
                "identify-perspectives",
                "build-outline",
                "source-map",
                "desk-research",
                "devils-advocate",
                "compare-hypotheses",
                "decision-archaeology",
            )
            agents = ("evidence-retriever", "source-extractor")
        stage_primitives(pack, skills=skills, agents=agents)
        dummy = pack / ".apm" / "skills" / "dummy"
        (dummy / "SKILL.md").unlink()
        dummy.rmdir()
        if name == "core":
            hook = pack / ".apm" / "hooks" / "session-start.py"
            hook.parent.mkdir(parents=True)
            hook.write_text("print('fixture')\n", encoding="utf-8")
            wiring = pack / ".apm" / "hook-wiring" / "session-start.toml"
            wiring.parent.mkdir(parents=True)
            wiring.write_text(
                "[[hooks.SessionStart]]\n"
                'hooks = [{ type = "command", command = '
                '"python tools/hooks/session-start.py" }]\n',
                encoding="utf-8",
            )
            command = pack / ".apm" / "commands" / "fixture.md"
            command.parent.mkdir(parents=True)
            command.write_text("# Fixture command\n", encoding="utf-8")
            for relative, content in {
                "AGENTS.md": "# Fixture agents\n",
                ".gitignore": ".agentbundle-state.toml\n",
                "docs/CHARTER.md": "# Fixture charter\n",
                "docs/CONVENTIONS.md": "# Fixture conventions\n",
            }.items():
                seed = pack / "seeds" / relative
                seed.parent.mkdir(parents=True, exist_ok=True)
                seed.write_text(content, encoding="utf-8")

    profile_defs = {
        "full-ceremony": (
            "repo",
            ("core", "governance-extras", "product-documentation", "monorepo-extras"),
        ),
        "solution-architect": (
            "user",
            ("architect", "desk-research", "contracts"),
        ),
    }
    for profile_name in profiles:
        scope, members = profile_defs[profile_name]
        profile = destination / "profiles" / f"{profile_name}.toml"
        profile.parent.mkdir(parents=True, exist_ok=True)
        rows = "\n".join(f'[[packs]]\npack = "{member}"' for member in members)
        profile.write_text(
            f'scope = "{scope}"\ndescription = "Fixture profile."\n{rows}\n',
            encoding="utf-8",
        )
    marketplace = destination / ".claude-plugin" / "marketplace.json"
    marketplace.parent.mkdir(parents=True)
    marketplace.write_text(
        '{"name":"fixture","owner":{"name":"fixture"},"plugins":[]}\n',
        encoding="utf-8",
    )
    return destination
