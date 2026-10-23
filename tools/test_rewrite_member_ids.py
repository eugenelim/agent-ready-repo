"""Tests for tools/catalogue/rewrite_member_ids.py."""

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CAT = ROOT / "tools" / "catalogue"
DATA = ROOT / "packages" / "agentbundle" / "agentbundle" / "_data"


def _load(name: str):  # type: ignore[no-untyped-def]
    spec = importlib.util.spec_from_file_location(name, CAT / f"{name}.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


rewrite = _load("rewrite_member_ids")
inventory = _load("sync_contract_inventory")
URL = rewrite.member_id("0.1", "x.schema.json")
SCHEMA = b'  "$schema": "https://json-schema.org/draft/2020-12/schema",\n'


class RewriteBytesTests(unittest.TestCase):
    def test_existing_id_value_only_replaced(self) -> None:
        data = b'{\n  "$schema": "s",\n  "$id": "x.schema.json",\n  "type": "object"\n}\n'
        out = rewrite.rewrite_bytes(data, URL)
        self.assertEqual(out, data.replace(b'"x.schema.json"', f'"{URL}"'.encode()))

    def test_missing_id_and_schema_inserted_after_brace(self) -> None:
        data = b'{\n  "type": "object"\n}\n'
        out = rewrite.rewrite_bytes(data, URL)
        self.assertEqual(out, b"{\n" + SCHEMA + f'  "$id": "{URL}",\n'.encode() + data[2:])

    def test_missing_schema_only_inserts_that_line(self) -> None:
        data = b'{\n  "$id": "a",\n  "type": "object"\n}\n'
        out = rewrite.rewrite_bytes(data, URL)
        self.assertEqual(out, b"{\n" + SCHEMA + data[2:].replace(b'"a"', f'"{URL}"'.encode()))

    def test_idempotent(self) -> None:
        data = b'{\n  "type": "object"\n}\n'
        once = rewrite.rewrite_bytes(data, URL)
        self.assertEqual(rewrite.rewrite_bytes(once, URL), once)

    def test_unparseable_result_refused(self) -> None:
        with self.assertRaises(ValueError):
            rewrite.rewrite_bytes(b'{\n  "type": \n}\n', URL)
        with self.assertRaises(ValueError):
            rewrite.rewrite_bytes(b'[1]\n', URL)

    def test_non_member_refused(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "other.json"
            path.write_bytes(b"{\n}\n")
            with self.assertRaises(ValueError):
                rewrite.rewrite_file(path, "0.1", {"x.schema.json"})
            self.assertEqual(path.read_bytes(), b"{\n}\n")


class MemberSetTests(unittest.TestCase):
    def test_predicate_is_exactly_json_member_rows(self) -> None:
        rows = inventory.json_schema_members(ROOT / "contracts")
        expected = [
            r
            for r in inventory.load_manifest(ROOT / "contracts")
            if r.role == "member" and r.path.endswith(".json")
        ]
        self.assertEqual(rows, expected)
        self.assertEqual(len(rows), 8)

    def test_rewrite_tool_uses_the_shared_helper(self) -> None:
        source = (CAT / "rewrite_member_ids.py").read_text(encoding="utf-8")
        self.assertIn("json_schema_members", source)
        self.assertNotIn('endswith(".json")', source)
        self.assertNotIn('suffix == ".json"', source)


class RealTreeTests(unittest.TestCase):
    def test_json_members_carry_versioned_id_and_schema(self) -> None:
        for row in inventory.json_schema_members(ROOT / "contracts"):
            name = Path(row.path).name
            for root in (ROOT / "contracts", DATA):
                doc = json.loads((root / name).read_text(encoding="utf-8"))
                self.assertEqual(doc["$id"], rewrite.member_id("0.1", name), f"{root}/{name}")
                self.assertIn("$schema", doc)

    def test_toml_members_unchanged_and_copies_identical(self) -> None:
        for name in ("adapter.toml", "target-vocab.toml"):
            self.assertEqual((ROOT / "contracts" / name).read_bytes(), (DATA / name).read_bytes())
            self.assertNotIn(b"catalogue/0.1", (ROOT / "contracts" / name).read_bytes())
        for row in inventory.json_schema_members(ROOT / "contracts"):
            name = Path(row.path).name
            self.assertEqual((ROOT / "contracts" / name).read_bytes(), (DATA / name).read_bytes())


if __name__ == "__main__":
    unittest.main()
