"""Regression tests for claude plugin validate failures fixed in 2026-07.

Three defects caused 35 errors from `claude plugin validate` against
`.claude-plugin/marketplace.json` on Claude Code 2.1.209:

  1. marketplace missing `name` field at the top level
  2. plugin `author` emitted as string instead of `{name, email}` object
  3. plugin `source` field absent entirely

These tests pin the generator contracts so the same failures cannot silently
re-appear in future changes to `derive_projectable_subset`, `_run_aggregate`,
or `_aggregate_marketplace`.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[4]

# Minimal pack.toml with full enriched metadata (maintainers + links).
_PACK_WITH_METADATA = {
    "pack": {
        "name": "research",
        "version": "0.2.0",
        "description": "Research skills.",
        "maintainers": [
            {"name": "Eugene Lim", "email": "eugenelim@users.noreply.github.com"}
        ],
        "links": {
            "repository": "https://github.com/eugenelim/agent-ready-repo",
        },
    }
}

# Same but no email — author object must still be emitted (name only).
_PACK_NAME_ONLY = {
    "pack": {
        "name": "research",
        "version": "0.2.0",
        "description": "Research skills.",
        "maintainers": [{"name": "Eugene Lim"}],
        "links": {
            "repository": "https://github.com/eugenelim/agent-ready-repo",
        },
    }
}

# Pack with no maintainers or links — neither author nor source should appear.
_PACK_BARE = {
    "pack": {
        "name": "bare",
        "version": "0.1.0",
        "description": "Bare pack with no enriched metadata.",
    }
}


# ---------------------------------------------------------------------------
# derive_projectable_subset — unit-level pins
# ---------------------------------------------------------------------------


class TestDeriveProjectableSubsetAuthor:
    """author must be emitted as an object, never as a string."""

    def test_author_is_object_when_maintainers_present(self):
        from agentbundle.build.main import derive_projectable_subset

        result = derive_projectable_subset(_PACK_WITH_METADATA)
        author = result.get("author")
        assert isinstance(author, dict), (
            f"author must be an object ({{name, email}}), got {author!r}"
        )

    def test_author_contains_name_key(self):
        from agentbundle.build.main import derive_projectable_subset

        result = derive_projectable_subset(_PACK_WITH_METADATA)
        assert result["author"]["name"] == "Eugene Lim"

    def test_author_contains_email_key_when_present(self):
        from agentbundle.build.main import derive_projectable_subset

        result = derive_projectable_subset(_PACK_WITH_METADATA)
        assert result["author"]["email"] == "eugenelim@users.noreply.github.com"

    def test_author_omits_email_key_when_absent(self):
        from agentbundle.build.main import derive_projectable_subset

        result = derive_projectable_subset(_PACK_NAME_ONLY)
        assert result["author"] == {"name": "Eugene Lim"}
        assert "email" not in result["author"]

    def test_author_absent_when_no_maintainers(self):
        from agentbundle.build.main import derive_projectable_subset

        result = derive_projectable_subset(_PACK_BARE)
        assert "author" not in result


class TestDeriveProjectableSubsetSource:
    """source must be emitted as a github-shaped object when repository is a GitHub URL."""

    def test_source_is_object_when_github_repository_present(self):
        from agentbundle.build.main import derive_projectable_subset

        result = derive_projectable_subset(_PACK_WITH_METADATA)
        source = result.get("source")
        assert isinstance(source, dict), (
            f"source must be an object, got {source!r}"
        )

    def test_source_scheme_is_github(self):
        from agentbundle.build.main import derive_projectable_subset

        result = derive_projectable_subset(_PACK_WITH_METADATA)
        assert result["source"]["source"] == "github"

    def test_source_repo_is_owner_slash_name(self):
        from agentbundle.build.main import derive_projectable_subset

        result = derive_projectable_subset(_PACK_WITH_METADATA)
        assert result["source"]["repo"] == "eugenelim/agent-ready-repo"

    def test_source_branch_is_dist_branch(self):
        from agentbundle.build.main import derive_projectable_subset

        result = derive_projectable_subset(_PACK_WITH_METADATA)
        assert result["source"]["branch"] == "claude-plugins-dist"

    def test_source_directory_is_pack_name(self):
        from agentbundle.build.main import derive_projectable_subset

        result = derive_projectable_subset(_PACK_WITH_METADATA)
        assert result["source"]["directory"] == "research"

    def test_source_absent_when_no_repository(self):
        from agentbundle.build.main import derive_projectable_subset

        result = derive_projectable_subset(_PACK_BARE)
        assert "source" not in result

    def test_source_absent_for_non_github_url(self):
        from agentbundle.build.main import derive_projectable_subset

        pack = {
            "pack": {
                "name": "internal",
                "version": "0.1.0",
                "description": "Internal pack.",
                "links": {"repository": "https://gitlab.com/example/internal"},
            }
        }
        result = derive_projectable_subset(pack)
        assert "source" not in result

    def test_author_is_never_emitted_as_string(self):
        """author must never be emitted as a plain string — regression of the 2026-07 defect."""
        from agentbundle.build.main import derive_projectable_subset

        result = derive_projectable_subset(_PACK_WITH_METADATA)
        assert not isinstance(result.get("author"), str), (
            "author was emitted as string — regression of the 2026-07 defect"
        )


# ---------------------------------------------------------------------------
# _run_aggregate — marketplace name derivation unit pin
# ---------------------------------------------------------------------------


class TestRunAggregateMarketplaceName:
    """The aggregated marketplace.json must carry a top-level `name` field."""

    def _build_dist_marketplace(self, tmp_path: Path) -> dict:
        """Run `agentbundle build` against the real packs and return marketplace.json."""
        packs_shadow = tmp_path / "packs"
        shutil.copytree(REPO_ROOT / "packs", packs_shadow, symlinks=True)
        for pycache in packs_shadow.rglob("__pycache__"):
            if pycache.is_dir():
                shutil.rmtree(pycache, ignore_errors=True)

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "agentbundle.build",
                "build",
                "--packs-dir",
                str(packs_shadow),
                "--output-dir",
                str(tmp_path / "dist"),
            ],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )
        assert result.returncode == 0, (
            f"agentbundle build failed:\n{result.stdout}\n{result.stderr}"
        )
        marketplace = tmp_path / "dist" / "claude-plugins" / "marketplace.json"
        return json.loads(marketplace.read_text(encoding="utf-8"))

    def test_dist_marketplace_has_name_field(self, tmp_path):
        m = self._build_dist_marketplace(tmp_path)
        assert "name" in m, (
            "dist marketplace.json is missing the top-level `name` field — "
            "regression of the 2026-07 defect"
        )

    def test_dist_marketplace_name_is_repo_name(self, tmp_path):
        m = self._build_dist_marketplace(tmp_path)
        assert m["name"] == "agent-ready-repo"

    def test_dist_marketplace_has_owner_field(self, tmp_path):
        m = self._build_dist_marketplace(tmp_path)
        assert isinstance(m.get("owner"), dict), "owner must be an object"

    def test_dist_marketplace_every_plugin_has_object_author(self, tmp_path):
        m = self._build_dist_marketplace(tmp_path)
        missing = [p["name"] for p in m["plugins"] if "author" not in p]
        assert not missing, f"Plugins missing author: {missing}"
        string_authors = [
            p["name"]
            for p in m["plugins"]
            if isinstance(p.get("author"), str)
        ]
        assert not string_authors, (
            f"Plugins with string author — regression of the 2026-07 defect: {string_authors}"
        )

    def test_dist_marketplace_every_plugin_has_source(self, tmp_path):
        m = self._build_dist_marketplace(tmp_path)
        missing = [p["name"] for p in m["plugins"] if "source" not in p]
        assert not missing, (
            f"Plugins missing source — regression of the 2026-07 defect: {missing}"
        )

    def test_dist_marketplace_source_shapes_are_valid(self, tmp_path):
        m = self._build_dist_marketplace(tmp_path)
        for plugin in m["plugins"]:
            src = plugin.get("source")
            if src is None:
                continue
            assert isinstance(src, dict), f"{plugin['name']}.source must be object"
            assert src.get("source") == "github", (
                f"{plugin['name']}.source.source must be 'github'"
            )
            assert "/" in src.get("repo", ""), (
                f"{plugin['name']}.source.repo must be 'owner/name'"
            )
            assert src.get("branch"), f"{plugin['name']}.source.branch must be set"
            assert src.get("directory"), f"{plugin['name']}.source.directory must be set"


# ---------------------------------------------------------------------------
# self-host aggregate — working-tree marketplace.json pins
# ---------------------------------------------------------------------------


class TestSelfHostMarketplace:
    """The working-tree .claude-plugin/marketplace.json must satisfy all three
    shape invariants that caused the 2026-07 validation failures."""

    @pytest.fixture(scope="class")
    def marketplace(self):
        path = REPO_ROOT / ".claude-plugin" / "marketplace.json"
        assert path.exists(), f"missing {path} — run make build-self first"
        return json.loads(path.read_text(encoding="utf-8"))

    def test_has_name_field(self, marketplace):
        assert "name" in marketplace, (
            ".claude-plugin/marketplace.json missing `name` — 2026-07 regression"
        )

    def test_name_is_agent_ready_repo(self, marketplace):
        assert marketplace["name"] == "agent-ready-repo"

    def test_has_owner_field(self, marketplace):
        assert isinstance(marketplace.get("owner"), dict)

    def test_every_plugin_has_object_author(self, marketplace):
        """Every plugin entry must have an object author — not a string, not absent."""
        missing = [p["name"] for p in marketplace["plugins"] if "author" not in p]
        assert not missing, f"Plugins missing author: {missing}"
        string_authors = [
            p["name"]
            for p in marketplace["plugins"]
            if isinstance(p.get("author"), str)
        ]
        assert not string_authors, (
            f"String author (not object) — regression of 2026-07 defect: {string_authors}"
        )

    def test_every_plugin_has_source(self, marketplace):
        """Every plugin entry must carry a source field — not just some entries."""
        missing = [p["name"] for p in marketplace["plugins"] if "source" not in p]
        assert not missing, (
            f"Plugins missing source — regression of 2026-07 defect: {missing}"
        )

    def test_every_source_is_valid_object(self, marketplace):
        for plugin in marketplace["plugins"]:
            src = plugin.get("source")
            if src is None:
                continue
            assert isinstance(src, dict), (
                f"{plugin['name']}.source must be object, got {src!r}"
            )
