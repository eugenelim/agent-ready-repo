"""The two skills ship byte-identical copies of ``_preserve_write.py`` (T1 parity).

An installed skill cannot import from another skill, so the shared module is
copied; this test fails the moment the copies drift. It also loads the jira-align
copy by path (no ``sys.path`` change, so the jira skill's ``_client`` is not
shadowed) to prove it imports and exposes the public API the jira-align CLI will call.
"""
from __future__ import annotations

import importlib.util
import pathlib
import sys

APM_SKILLS = pathlib.Path(__file__).resolve().parents[3] / ".apm" / "skills"
JIRA_COPY = APM_SKILLS / "jira" / "scripts" / "_preserve_write.py"
ALIGN_COPY = APM_SKILLS / "jira-align" / "scripts" / "_preserve_write.py"


def test_both_copies_exist_and_are_byte_identical() -> None:
    assert JIRA_COPY.is_file(), JIRA_COPY
    assert ALIGN_COPY.is_file(), ALIGN_COPY
    assert JIRA_COPY.read_bytes() == ALIGN_COPY.read_bytes()


def test_jira_align_copy_imports_and_exposes_the_public_api() -> None:
    spec = importlib.util.spec_from_file_location("_preserve_write_align_copy", ALIGN_COPY)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # dataclasses resolve annotations through sys.modules
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(spec.name, None)
    assert module.GUARD_EXIT_CODE == 10
    for name in module.__all__:
        assert hasattr(module, name), name
