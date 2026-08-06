"""Red stubs for spec/claude-plugins-manifest-correctness.

Materialised at PLAN per docs/CONVENTIONS.md § Stub → EXECUTE handoff. Every
test here asserts a contract surface the spec's Acceptance Criteria determine;
none is a bare TODO. They are expected to FAIL until their task lands.

Task map:
  T0 → AC9   marketplace entries are validated, on both paths
  T1 → AC7   no assertion pins the old source shape
  T2 → AC1, AC5, AC8   source shape, envelope, schema
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[4]
CONTRACTS = REPO_ROOT / "contracts"
DATA = REPO_ROOT / "packages" / "agentbundle" / "agentbundle" / "_data"


def _validate(instance: dict, schema: dict) -> list[str]:
    """Use the validator the BUILD gates on, not `jsonschema`.

    `agentbundle.build.validate` is stdlib-only and is what
    `build/main.py:31` and `verify.py:600` call. `jsonschema` is absent from
    `pyproject.toml` `dependencies = []` and from CI Gate A's install list, so
    an `importorskip` here would turn these into silent skips on CI — the exact
    looks-like-a-gate failure this spec exists to fix.
    """
    from agentbundle.build.validate import validate

    return validate(instance, schema)


def _assert_valid(instance: dict, schema: dict) -> None:
    errors = _validate(instance, schema)
    assert not errors, f"expected valid, got: {errors}"


def _assert_invalid(instance: dict, schema: dict) -> None:
    errors = _validate(instance, schema)
    assert errors, "expected rejection, but the validator accepted it"


GIT_SUBDIR_SOURCE = {
    "source": "git-subdir",
    "url": "https://github.com/eugenelim/agent-ready-repo.git",
    "path": "core",
    "ref": "claude-plugins-dist",
}
LEGACY_SOURCE = {
    "source": "github",
    "repo": "eugenelim/agent-ready-repo",
    "branch": "claude-plugins-dist",
    "directory": "core",
}


def _entry_schema() -> dict:
    """The marketplace-entry schema T0 introduces.

    Distinct from the derived plugin.json schema: an entry REQUIRES `source`
    and permits `category`, while plugin.json carries neither
    (build/main.py:545-546 pops both before validation).
    """
    path = CONTRACTS / "marketplace-entry.schema.json"
    if not path.exists():  # STUB: AC9 — T0 has not landed yet
        pytest.fail(
            "marketplace-entry schema absent: one schema cannot both forbid "
            "`source` (plugin.json) and require it (marketplace entry)"
        )
    return json.loads(path.read_text(encoding="utf-8"))


# --- T0 / AC9 -------------------------------------------------------------


def test_marketplace_entry_schema_requires_source() -> None:
    """# STUB: AC9 — an entry without `source` must be rejected."""
    schema = _entry_schema()
    assert "source" in schema.get("required", []), (
        "a marketplace entry must require `source`; this is the invariant the "
        "existing regression test at test_marketplace_manifest_regression.py:236 "
        "was written to protect"
    )


def test_marketplace_entry_schema_permits_category() -> None:
    """# STUB: AC9 — every live entry carries `category`.

    The derived schema forbids it under additionalProperties: false, which is
    the proof that entries have never been validated: all 21 would fail today.
    """
    schema = _entry_schema()
    assert "category" in schema.get("properties", {}), (
        "`category` must be admitted or the new gate rejects all 21 live entries"
    )


def _build_dist_marketplace(tmp_path: Path) -> dict:
    """Build the dist marketplace into tmp_path.

    `dist/` is gitignored (.gitignore:73) and CI Gate A runs no `make build`, so
    a test that reads the working tree silently SKIPS on CI — coverage that
    looks present and is not.
    """
    from agentbundle.build.main import Recipe, _run_aggregate

    plugin_dir = tmp_path / "claude-plugins" / "core"
    (plugin_dir / ".claude-plugin").mkdir(parents=True)
    (plugin_dir / ".claude-plugin" / "plugin.json").write_text(
        json.dumps({"name": "core", "version": "2.2.0", "description": "d",
                    "source": GIT_SUBDIR_SOURCE}), encoding="utf-8")
    (plugin_dir / "pack.toml").write_text(
        '[pack]\nname = "core"\n'
        '[pack.links]\nrepository = "https://github.com/eugenelim/agent-ready-repo"\n',
        encoding="utf-8")
    recipe = Recipe(name="marketplace", type="aggregate", adapter=None,
                    output_subdir=None, input_subdir="claude-plugins",
                    output_file="marketplace.json", units=[],
                    fragment_path=None, manifest_path=None)
    _run_aggregate(recipe, tmp_path)  # returns a summary; the payload is written
    return json.loads((tmp_path / "marketplace.json").read_text(encoding="utf-8"))


def test_root_marketplace_entries_validate() -> None:
    """# STUB: AC9 — the root marketplace is committed, so this always runs.

    verify.py `_step_plugin_manifests` reads only `tmpdir/dist/claude-plugins`
    (:594), so the root marketplace — written by
    self_host._aggregate_marketplace (:602) — is currently gated by nothing.
    """
    path = REPO_ROOT / ".claude-plugin" / "marketplace.json"
    entries = json.loads(path.read_text(encoding="utf-8")).get("plugins", [])
    assert len(entries) >= 1, "assert coverage, not a brittle fixed count"
    for entry in entries:
        _assert_valid(entry, _entry_schema())


def test_dist_marketplace_entries_validate(tmp_path: Path) -> None:
    """# STUB: AC9 — built into tmp_path, never read from the gitignored tree."""
    payload = _build_dist_marketplace(tmp_path)
    entries = payload.get("plugins", [])
    assert len(entries) >= 1
    for entry in entries:
        _assert_valid(entry, _entry_schema())


def test_malformed_source_is_rejected() -> None:
    """# STUB: AC9 — the negative case; without this the gate proves nothing."""
    bad = {"name": "x", "version": "1.0.0", "description": "d",
           "source": {"source": "git-subdir"}}  # no url, no path, no ref/sha
    _assert_invalid(bad, _entry_schema())


# --- T2 / AC8 -------------------------------------------------------------


@pytest.mark.parametrize("schema_path", [
    CONTRACTS / "plugin-manifest.derived.schema.json",
    CONTRACTS / "plugin-manifest.schema.json",
    DATA / "plugin-manifest.derived.schema.json",
    DATA / "plugin-manifest.schema.json",
])
def test_all_four_schemas_drop_legacy_source_keys(schema_path: Path) -> None:
    """# STUB: AC8 — all four copies, including the byte-equality-gated twins."""
    text = schema_path.read_text(encoding="utf-8")
    assert '"branch"' not in text, f"{schema_path.name} still declares `branch`"
    assert '"directory"' not in text, f"{schema_path.name} still declares `directory`"


def test_source_requires_ref_or_sha() -> None:
    """# STUB: AC8 — a ref-less, sha-less payload silently fetches the default
    branch, which is the original defect wearing a valid shape."""
    schema = json.loads(
        (CONTRACTS / "plugin-manifest.derived.schema.json").read_text(encoding="utf-8")
    )
    unpinned = dict(GIT_SUBDIR_SOURCE)
    unpinned.pop("ref")
    _assert_invalid(unpinned, schema["properties"]["source"])


@pytest.mark.parametrize("bad_url", [
    "http://github.com/eugenelim/agent-ready-repo.git",   # scheme
    "https://gitlab.com/eugenelim/agent-ready-repo.git",  # host
])
def test_source_url_is_constrained(bad_url: str) -> None:
    """# STUB: AC8 — git-subdir moves the fetch host from the schema into data."""
    schema = json.loads(
        (CONTRACTS / "plugin-manifest.derived.schema.json").read_text(encoding="utf-8")
    )
    payload = dict(GIT_SUBDIR_SOURCE, url=bad_url)
    _assert_invalid(payload, schema["properties"]["source"])


# --- T2 / AC1 + AC5 -------------------------------------------------------


def test_derive_projectable_subset_emits_git_subdir() -> None:
    """# STUB: AC1 — the generator is `derive_projectable_subset`, main.py:199."""
    from agentbundle.build.main import derive_projectable_subset

    derived = derive_projectable_subset({
        "pack": {
            "name": "core",
            "links": {"repository": "https://github.com/eugenelim/agent-ready-repo"},
        }
    })
    assert derived["source"] == GIT_SUBDIR_SOURCE


def test_http_repository_link_is_rejected_not_upgraded() -> None:
    """# STUB: AC1 — _GITHUB_URL_RE (main.py:49-51) is `^https?://` today, so an
    http:// link matches and would be silently emitted as https://."""
    from agentbundle.build.main import derive_projectable_subset

    with pytest.raises(ValueError):
        derive_projectable_subset({
            "pack": {
                "name": "core",
                "links": {"repository": "http://github.com/eugenelim/agent-ready-repo"},
            }
        })


def test_dist_envelope_survives_repo_key_removal(tmp_path: Path) -> None:
    """# STUB: AC5 — main.py:705-717 splits src["repo"] to derive name/owner;
    git-subdir has no `repo`, so both would silently drop."""
    payload = _build_dist_marketplace(tmp_path)
    for key in ("name", "owner", "description"):
        assert key in payload, f"dist marketplace envelope lost `{key}`"
