"""enriched-pack-manifest T4: derive the projectable subset from pack.toml.

The build maps a pack's rich ``pack.toml`` metadata to the lossy,
schema-compliant subset carried in the ``plugin.json`` / ``marketplace.json``
entry. Two invariants are load-bearing:

  - **Fixed mapping** — author←maintainers[0], category←categories[0],
    displayName←display_name, license/keywords/homepage/repository verbatim.
  - **Emit-only-when-present (legacy invariance)** — a pack.toml with none of
    the enriched fields yields ``{}``, so the projected manifest is
    byte-identical to the pre-enrichment output.
"""

from __future__ import annotations

import json
import tomllib
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[5]
DERIVED_SCHEMA_PATH = (
    REPO_ROOT / "docs" / "contracts" / "plugin-manifest.derived.schema.json"
)

ENRICHED_TOML = """
[pack]
name = "research"
version = "0.1.0"
description = "Evidence-grounded research."
display_name = "Research"
license = "Apache-2.0"
categories = ["research", "documentation"]
keywords = ["osint", "synthesis", "citations"]

[[pack.maintainers]]
name = "Eugene Lim"
email = "eugenelim@users.noreply.github.com"

[pack.links]
homepage = "https://example.com"
repository = "https://github.com/example/repo"
documentation = "https://example.com/docs"
"""

LEGACY_TOML = """
[pack]
name = "core"
version = "0.4.0"
description = "Core skills."
"""


class DeriveProjectableSubsetTests(unittest.TestCase):
    def test_enriched_pack_maps_full_subset(self) -> None:
        from agentbundle.build.main import derive_projectable_subset

        subset = derive_projectable_subset(tomllib.loads(ENRICHED_TOML))
        self.assertEqual(
            subset,
            {
                "author": "Eugene Lim <eugenelim@users.noreply.github.com>",
                "license": "Apache-2.0",
                "homepage": "https://example.com",
                "repository": "https://github.com/example/repo",
                "keywords": ["osint", "synthesis", "citations"],
                "category": "research",
                "displayName": "Research",
            },
        )

    def test_legacy_pack_yields_empty_subset(self) -> None:
        """Emit-only-when-present: no enriched fields → {} (byte-identity)."""
        from agentbundle.build.main import derive_projectable_subset

        self.assertEqual(derive_projectable_subset(tomllib.loads(LEGACY_TOML)), {})

    def test_maintainer_without_name_emits_no_author(self) -> None:
        """A maintainer entry missing `name` reaching the projector (e.g. via
        `_aggregate_marketplace` on not-yet-schema-validated pack.toml) emits no
        `author` key rather than a malformed one."""
        from agentbundle.build.main import derive_projectable_subset

        self.assertEqual(
            derive_projectable_subset(
                {"pack": {"maintainers": [{"email": "x@y.z"}]}}
            ),
            {},
        )

    def test_author_without_email_is_name_only(self) -> None:
        from agentbundle.build.main import derive_projectable_subset

        toml = """
[pack]
name = "x"
version = "0.1.0"
[[pack.maintainers]]
name = "Solo Maintainer"
"""
        self.assertEqual(
            derive_projectable_subset(tomllib.loads(toml)),
            {"author": "Solo Maintainer"},
        )

    def test_category_is_first_of_categories(self) -> None:
        from agentbundle.build.main import derive_projectable_subset

        toml = """
[pack]
name = "x"
version = "0.1.0"
categories = ["governance", "testing"]
"""
        self.assertEqual(
            derive_projectable_subset(tomllib.loads(toml)), {"category": "governance"}
        )

    def test_subset_output_validates_against_derived_schema(self) -> None:
        """The mapped subset, merged into a real derived manifest, is schema-valid."""
        from agentbundle.build.main import derive_projectable_subset
        from agentbundle.build.validate import validate

        manifest = {
            "name": "research",
            "version": "0.1.0",
            "description": "Evidence-grounded research.",
            "hooks": {"SessionStart": [{"command": "python3 x.py"}]},
        }
        manifest.update(derive_projectable_subset(tomllib.loads(ENRICHED_TOML)))
        schema = json.loads(DERIVED_SCHEMA_PATH.read_text(encoding="utf-8"))
        self.assertEqual(validate(manifest, schema), [])

    def test_merging_empty_subset_leaves_manifest_byte_identical(self) -> None:
        """Legacy invariance at the merge site: update({}) changes nothing."""
        from agentbundle.build.main import derive_projectable_subset

        before = {
            "name": "core",
            "version": "0.4.0",
            "description": "Core skills.",
            "hooks": {"SessionStart": [{"command": "python3 x.py"}]},
        }
        after = dict(before)
        after.update(derive_projectable_subset(tomllib.loads(LEGACY_TOML)))
        self.assertEqual(
            json.dumps(before, sort_keys=True),
            json.dumps(after, sort_keys=True),
        )


class ProjectPackReadmeTests(unittest.TestCase):
    """T5: `_project_pack_readme` copies a pack's README into the route, and is
    a no-op (no error) when the pack ships none."""

    def test_copies_readme_when_present(self) -> None:
        import tempfile

        from agentbundle.build.main import _project_pack_readme

        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            pack = root / "pack"
            pack.mkdir()
            (pack / "README.md").write_text("# demo\n", encoding="utf-8")
            route = root / "route"
            route.mkdir()
            _project_pack_readme(pack, route)
            self.assertTrue((route / "README.md").is_file())
            self.assertEqual((route / "README.md").read_text(encoding="utf-8"), "# demo\n")

    def test_no_readme_is_noop_not_error(self) -> None:
        import tempfile

        from agentbundle.build.main import _project_pack_readme

        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            pack = root / "pack"
            pack.mkdir()  # no README.md
            route = root / "route"
            route.mkdir()
            _project_pack_readme(pack, route)  # must not raise
            self.assertFalse((route / "README.md").exists())


if __name__ == "__main__":
    unittest.main()
