"""AC-0040: the work-loop mapping profile this catalogue ships.

The profile is data, not code (ADR-0115): a TOML file at a path the criterion
fixes, with keys the criterion fixes. So these assertions need no symbol from
`jsonl-otlp-exporter`, and they run whether or not the sender is installed.

The allowlist is asserted against a line the supervisor actually emits rather than
against a name list, so a field added to the envelope fails this test instead of
being dropped from the payload in silence.
"""
from __future__ import annotations

import json
import tomllib
from pathlib import Path

# Anchored at the owning pack, not the repository root. Every path this file
# needs is inside `packs/core`, so routing up to the root and back down was a
# reach outside the pack that bought nothing -- and the pack-test boundary
# lint refuses it.
_PACK = Path(__file__).resolve().parents[3]
_PROFILE = _PACK / ".apm/skills/work-loop/profiles/work-loop.toml"


# Each shared helper by literal path, so every file this suite loads stays visibly inside the pack.
_HELPER_PATHS = {
    "supervisor_harness": Path(__file__).resolve().parent / "supervisor_harness.py",
    "supervisor_support": Path(__file__).resolve().parent / "supervisor_support.py",
}


def _helper(name: str):
    """A shared supervisor test helper, loaded by path under a pack- and skill-unique name."""
    import importlib.util
    import sys

    alias = f"core_work_loop_{name}"
    if alias not in sys.modules:
        spec = importlib.util.spec_from_file_location(alias, _HELPER_PATHS[name])
        assert spec is not None and spec.loader is not None
        sys.modules[alias] = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(sys.modules[alias])
    return sys.modules[alias]


def _one_emitted_line(tmp_path: Path) -> dict:
    """Admit one supervisor run and return the event line it appended."""
    h = _helper("supervisor_harness")
    repo = h.make_repo(tmp_path)
    assert h.start(repo)[0] == 0
    h.run_cli(repo, "next", h.SPEC_DIR)
    return json.loads((repo / ".loop-run" / "events.jsonl").read_text().splitlines()[-1])


class TestWorkLoopProfile:
    def test_profile_declares_the_envelope_fields(self) -> None:
        # STUB: AC-0040
        profile = tomllib.loads(_PROFILE.read_text(encoding="utf-8"))
        assert profile["timestamp_field"] == "at"
        assert profile["timestamp_format"] == "rfc3339"
        assert profile["severity_field"] == "result"
        assert profile["identity"] == ["run_id", "seq"]

    def test_severity_map_is_the_pinned_pairs(self) -> None:
        # STUB: AC-0040
        profile = tomllib.loads(_PROFILE.read_text(encoding="utf-8"))
        assert profile["severity_map"] == {"success": 9, "failure": 17}

    @_helper("supervisor_support").INTEGRATION
    def test_allowlist_is_exactly_the_unrouted_emitted_keys(self, tmp_path) -> None:
        # STUB: AC-0040
        profile = tomllib.loads(_PROFILE.read_text(encoding="utf-8"))
        emitted = set(_one_emitted_line(tmp_path))
        routed = {"at", "result", "run_id", "seq"}
        assert set(profile["allowlist"]) == emitted - routed
