"""The supervisor's read and write access kinds match the access-attestation schema.

Roster-owned: it reads ``contracts/``, which a pack suite may not reach. The kinds have one
owner in the supervisor (the meets relation's module); the launcher's shape check imports
them, and the schema enumerates them again.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = REPO_ROOT / "packs" / "core" / ".apm" / "skills" / "work-loop" / "scripts"
SCHEMA = REPO_ROOT / "contracts" / "delivery" / "access-attestation.v1.schema.json"


def _load(filename: str) -> ModuleType:
    tag = hashlib.sha256(str(SCRIPTS).encode("utf-8")).hexdigest()[:12]
    alias = f"_work_supervisor_{tag}_" + filename.removesuffix(".py").strip("_")
    cached = sys.modules.get(alias)
    if cached is not None:
        return cached
    spec = importlib.util.spec_from_file_location(alias, str(SCRIPTS / filename))
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[alias] = module
    spec.loader.exec_module(module)
    return module


def _schema_kinds(field: str) -> set[str]:
    schema = json.loads(SCHEMA.read_text("utf-8"))
    return set(schema["properties"][field]["items"]["properties"]["kind"]["enum"])


def test_the_meets_module_kinds_equal_the_schema_enumerations() -> None:
    conc = _load("_supervisor_concurrency.py")
    assert set(conc.READ_KINDS) == _schema_kinds("reads")
    assert set(conc.WRITE_KINDS) == _schema_kinds("writes")


def test_the_launcher_shape_check_uses_the_same_kinds() -> None:
    conc = _load("_supervisor_concurrency.py")
    launcher = _load("_supervisor_launcher.py")
    assert launcher._READ_KINDS is conc.READ_KINDS
    assert launcher._WRITE_KINDS is conc.WRITE_KINDS
