"""``agentbundle show`` — command tests (catalogue-runtime-inventory spec).

Two paths exercised through ``run(args)``:

  - **T3 / primary (catalogue):** a temp catalogue fixture plus the working-tree
    catalogue (`show core`), asserting AC1 (table block), AC2 (full untagged
    inventory), AC3 (JSON shape), AC4 (empty lists), AC5 (unknown pack).
  - **T4 / degrade (install state):** an unresolvable catalogue (a `git+ssh://`
    URI raises `CatalogueError`) plus fabricated state files, asserting AC6
    (two-scope union, extension-agnostic recovery, null metadata) and AC7
    (not-installed error).

Plus unit coverage of the pure relpath name-recovery helpers.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

from agentbundle.commands import show
from agentbundle.config import PackState, State, dump_state

# Repo root = the working-tree catalogue (contains packs/core/...).
REPO_ROOT = Path(__file__).resolve().parents[4]

# A URI that forces CatalogueError (SSH is deferred → raises immediately).
UNRESOLVABLE = "git+ssh://example.com/owner/repo"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _args(pack: str, *, catalogue: str | None = None, fmt: str = "table",
          root: str = ".") -> SimpleNamespace:
    return SimpleNamespace(
        pack=pack, catalogue=catalogue, format=fmt, root=root, _user_config=None
    )


def _make_catalogue(root: Path, *, name: str = "demo",
                    skills: tuple[str, ...] = ("zeta", "alpha"),
                    agents: tuple[str, ...] = ("beta", "aardvark"),
                    meta: bool = True) -> Path:
    """Build ``<root>/packs/<name>/`` with pack.toml + .apm tree; return root."""
    pack = root / "packs" / name
    toml = f'[pack]\nname = "{name}"\n'
    if meta:
        toml += 'version = "1.2.3"\ndescription = "Demo fixture pack"\n'
    (pack).mkdir(parents=True)
    (pack / "pack.toml").write_text(toml, encoding="utf-8")
    for s in skills:
        (pack / ".apm" / "skills" / s).mkdir(parents=True)
        (pack / ".apm" / "skills" / s / "SKILL.md").write_text("# s\n", encoding="utf-8")
    for a in agents:
        (pack / ".apm" / "agents").mkdir(parents=True, exist_ok=True)
        (pack / ".apm" / "agents" / f"{a}.md").write_text("# a\n", encoding="utf-8")
    return root


# ---------------------------------------------------------------------------
# T3 / AC1 — primary path, table block
# ---------------------------------------------------------------------------


def test_primary_table_has_metadata_and_sorted_inventory(tmp_path, capsys):
    cat = _make_catalogue(tmp_path)
    rc = show.run(_args("demo", catalogue=str(cat)))
    out = capsys.readouterr().out
    assert rc == 0
    assert "demo" in out and "1.2.3" in out and "Demo fixture pack" in out
    # Sorted ascending in the rendered comma lists.
    assert out.index("alpha") < out.index("zeta")
    assert out.index("aardvark") < out.index("beta")


def test_primary_via_default_source_chain(tmp_path, capsys):
    """The real CLI has no catalogue flag on `show`, so it resolves via the
    default-source chain, not a layer-1 override. Drive that path: catalogue
    unset, source supplied through `_user_config` (layer 2)."""
    cat = _make_catalogue(tmp_path)
    # A layer-2 [settings].source is marker-validated: it needs both packs/ and
    # .claude-plugin/marketplace.json (layer-1 overrides skip this check).
    marker = cat / ".claude-plugin" / "marketplace.json"
    marker.parent.mkdir(parents=True)
    marker.write_text("{}\n", encoding="utf-8")
    args = SimpleNamespace(
        pack="demo", catalogue=None, format="json", root=".",
        _user_config=SimpleNamespace(source=str(cat)),
    )
    rc = show.run(args)
    obj = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert obj["source"] == "catalogue"
    assert obj["skills"] == ["alpha", "zeta"]


# ---------------------------------------------------------------------------
# T3 / AC2 — working-tree `show core` lists the FULL inventory, not evals subset
# ---------------------------------------------------------------------------


def test_show_core_lists_full_inventory_not_evals_subset(capsys):
    rc = show.run(_args("core", catalogue=str(REPO_ROOT), fmt="json"))
    out = capsys.readouterr().out
    assert rc == 0
    obj = json.loads(out)
    skills = set(obj["skills"])
    # [pack.evals].skills lists only 5; the tree ships 9. The deliberately
    # eval-excluded skills must still appear (full, untagged inventory).
    assert {"security-checklists", "operational-safety", "work-loop"} <= skills
    assert len(skills) >= 9


# ---------------------------------------------------------------------------
# T3 / AC3 — JSON shape
# ---------------------------------------------------------------------------


def test_json_exact_keys_sorted_arrays_source_catalogue(tmp_path, capsys):
    cat = _make_catalogue(tmp_path)
    rc = show.run(_args("demo", catalogue=str(cat), fmt="json"))
    out = capsys.readouterr().out
    assert rc == 0
    obj = json.loads(out)  # parses as valid JSON
    assert set(obj) == {"name", "version", "description", "skills", "agents", "source"}
    assert obj["source"] == "catalogue"
    assert obj["name"] == "demo"
    assert obj["skills"] == ["alpha", "zeta"]
    assert obj["agents"] == ["aardvark", "beta"]
    assert obj["version"] == "1.2.3"
    assert obj["description"] == "Demo fixture pack"


# ---------------------------------------------------------------------------
# T3 / AC4 — empty skills/agents → empty list, no error
# ---------------------------------------------------------------------------


def test_pack_with_no_apm_dirs_shows_empty_lists(tmp_path, capsys):
    cat = _make_catalogue(tmp_path, skills=(), agents=())
    rc = show.run(_args("demo", catalogue=str(cat), fmt="json"))
    out = capsys.readouterr().out
    assert rc == 0
    obj = json.loads(out)
    assert obj["skills"] == [] and obj["agents"] == []


# ---------------------------------------------------------------------------
# T3 / AC5 — unknown pack → one-line stderr, empty stdout, exit non-zero
# ---------------------------------------------------------------------------


def test_unknown_pack_errors_empty_stdout(tmp_path, capsys):
    cat = _make_catalogue(tmp_path)
    rc = show.run(_args("nope", catalogue=str(cat)))
    captured = capsys.readouterr()
    assert rc != 0
    assert captured.out == ""
    assert "nope" in captured.err and captured.err.count("\n") == 1


def test_unknown_pack_json_still_empty_stdout(tmp_path, capsys):
    cat = _make_catalogue(tmp_path)
    rc = show.run(_args("nope", catalogue=str(cat), fmt="json"))
    captured = capsys.readouterr()
    assert rc != 0
    assert captured.out == ""  # no error object — consumer keys on exit code
    assert captured.err.strip()


# ---------------------------------------------------------------------------
# T4 / AC6 — degrade to install state (repo scope)
# ---------------------------------------------------------------------------


def test_degrade_installed_repo_scope(tmp_path, capsys):
    _write_state(
        tmp_path / ".agentbundle-state.toml",
        State(packs={
            ("demo", "claude-code"): PackState(
                installed_version="0.9.0",
                files={
                    ".claude/skills/zeta/SKILL.md": {"sha": "a"},
                    ".claude/skills/alpha/SKILL.md": {"sha": "b"},
                    ".claude/agents/beta.md": {"sha": "c"},
                },
            )
        }),
    )
    rc = show.run(_args("demo", catalogue=UNRESOLVABLE, fmt="json", root=str(tmp_path)))
    out = capsys.readouterr().out
    assert rc == 0
    obj = json.loads(out)
    assert obj["source"] == "installed-state"
    assert obj["name"] == "demo"
    assert obj["version"] is None and obj["description"] is None
    assert obj["skills"] == ["alpha", "zeta"]
    assert obj["agents"] == ["beta"]


def test_degrade_table_omits_version_prints_source_line(tmp_path, capsys):
    _write_state(
        tmp_path / ".agentbundle-state.toml",
        State(packs={
            ("demo", "claude-code"): PackState(
                installed_version="0.9.0",
                files={".claude/skills/alpha/SKILL.md": {"sha": "b"}},
            )
        }),
    )
    rc = show.run(_args("demo", catalogue=UNRESOLVABLE, root=str(tmp_path)))
    out = capsys.readouterr().out
    assert rc == 0
    assert "installed-state (catalogue unavailable)" in out
    assert "1.2.3" not in out  # no version row on the fallback path


def test_degrade_multi_adapter_dedupes_across_extensions(tmp_path, capsys):
    """AC6: claude(.md) + codex(.toml) + kiro(.json) + copilot(.agent.md) rows
    collapse to one entry per logical skill/agent (extension-agnostic recovery)."""
    _write_state(
        tmp_path / ".agentbundle-state.toml",
        State(packs={
            ("demo", "claude-code"): PackState(
                installed_version="0.9.0",
                files={
                    ".claude/skills/alpha/SKILL.md": {"sha": "1"},
                    ".claude/agents/bot.md": {"sha": "2"},
                },
            ),
            ("demo", "codex"): PackState(
                installed_version="0.9.0",
                files={
                    ".agents/skills/alpha/SKILL.md": {"sha": "3"},
                    ".codex/agents/bot.toml": {"sha": "4"},
                },
            ),
            ("demo", "kiro"): PackState(
                installed_version="0.9.0",
                files={".kiro/agents/bot.json": {"sha": "5"}},
            ),
            ("demo", "copilot"): PackState(
                installed_version="0.9.0",
                files={".github/agents/bot.agent.md": {"sha": "6"}},
            ),
        }),
    )
    rc = show.run(_args("demo", catalogue=UNRESOLVABLE, fmt="json", root=str(tmp_path)))
    obj = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert obj["skills"] == ["alpha"]
    assert obj["agents"] == ["bot"]  # never "bot.agent" / "bot.json"


def test_degrade_legacy_state_scope_warned_not_fatal(
    tmp_path, capsys, _isolate_user_config_dir
):
    """A legacy/incompatible state file in one scope is warned-and-skipped (not
    fatal): recovery still succeeds from the other scope, and a stderr warning
    names the skipped scope — mirroring `list-installed`."""
    # Repo scope: a legacy-schema state file that `load_state` refuses.
    (tmp_path / ".agentbundle-state.toml").write_text(
        'schema-version = "0.3"\n', encoding="utf-8"
    )
    # User scope: a valid state carrying the installed pack.
    _write_state(
        _isolate_user_config_dir / ".agentbundle" / "state.toml",
        State(packs={
            ("demo", "claude-code"): PackState(
                installed_version="0.9.0",
                files={".claude/skills/recovered/SKILL.md": {"sha": "x"}},
            )
        }),
    )
    rc = show.run(_args("demo", catalogue=UNRESOLVABLE, fmt="json", root=str(tmp_path)))
    captured = capsys.readouterr()
    obj = json.loads(captured.out)
    assert rc == 0
    assert obj["skills"] == ["recovered"]
    assert "skipping repo scope" in captured.err


def test_degrade_installed_user_scope_only(tmp_path, capsys, _isolate_user_config_dir):
    """A pack installed only at USER scope is still recovered (both scopes read)."""
    user_state = _isolate_user_config_dir / ".agentbundle" / "state.toml"
    _write_state(
        user_state,
        State(packs={
            ("demo", "claude-code"): PackState(
                installed_version="0.9.0",
                files={".claude/skills/solo/SKILL.md": {"sha": "x"}},
            )
        }),
    )
    # repo root (tmp_path) has no state → recovery must come from user scope.
    rc = show.run(_args("demo", catalogue=UNRESOLVABLE, fmt="json", root=str(tmp_path)))
    obj = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert obj["skills"] == ["solo"]


# ---------------------------------------------------------------------------
# T4 / AC7 — unresolvable catalogue + not installed → error
# ---------------------------------------------------------------------------


def test_degrade_not_installed_errors(tmp_path, capsys):
    rc = show.run(_args("ghost", catalogue=UNRESOLVABLE, root=str(tmp_path)))
    captured = capsys.readouterr()
    assert rc != 0
    assert captured.out == ""
    assert "ghost" in captured.err


def test_degrade_not_installed_json_empty_stdout(tmp_path, capsys):
    rc = show.run(_args("ghost", catalogue=UNRESOLVABLE, fmt="json", root=str(tmp_path)))
    captured = capsys.readouterr()
    assert rc != 0
    assert captured.out == ""


# ---------------------------------------------------------------------------
# Pure relpath name-recovery helpers
# ---------------------------------------------------------------------------


def test_skill_from_relpath_across_layouts():
    assert show._skill_from_relpath(".claude/skills/foo/SKILL.md") == "foo"
    assert show._skill_from_relpath(".agents/skills/bar/scripts/x.py") == "bar"
    assert show._skill_from_relpath(".kiro/skills/baz/SKILL.md") == "baz"
    assert show._skill_from_relpath(".claude/agents/foo.md") is None


def test_agent_from_relpath_extension_agnostic():
    assert show._agent_from_relpath(".claude/agents/foo.md") == "foo"
    assert show._agent_from_relpath(".codex/agents/foo.toml") == "foo"
    assert show._agent_from_relpath(".kiro/agents/foo.json") == "foo"
    assert show._agent_from_relpath(".github/agents/foo.agent.md") == "foo"
    # A file not directly under an `agents/` component is not an agent.
    assert show._agent_from_relpath(".claude/skills/foo/SKILL.md") is None


# ---------------------------------------------------------------------------
# AC8 — no-persist: a `show` run writes no files under the run root
# ---------------------------------------------------------------------------


def test_show_run_writes_no_files(tmp_path, capsys):
    _make_catalogue(tmp_path / "cat")
    before = {p for p in (tmp_path / "cat").rglob("*")}
    rc = show.run(_args("demo", catalogue=str(tmp_path / "cat"), fmt="json",
                        root=str(tmp_path)))
    capsys.readouterr()
    after = {p for p in (tmp_path / "cat").rglob("*")}
    assert rc == 0
    assert before == after  # nothing created/removed under the catalogue
    # And no repo-scope state file was written by the read-only command.
    assert not (tmp_path / ".agentbundle-state.toml").exists()


# ---------------------------------------------------------------------------
# AC10 — CLI surface (real subprocess): `show --help` documents --format
# ---------------------------------------------------------------------------


def test_show_help_documents_format():
    proc = subprocess.run(
        [sys.executable, "-m", "agentbundle", "show", "--help"],
        capture_output=True, text=True,
    )
    assert proc.returncode == 0
    assert "--format" in proc.stdout
    assert "{table,json}" in proc.stdout


# ---------------------------------------------------------------------------
# Test helper
# ---------------------------------------------------------------------------


def _write_state(path: Path, state: State) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dump_state(state), encoding="utf-8")
