"""AC-0040: the work-loop mapping profile this catalogue ships.

The profile is data, not code (ADR-0115): a TOML file at a path the criterion
fixes, with keys the criterion fixes. So these assertions need no symbol from
`jsonl-otlp-exporter`, and they run whether or not the sender is installed.

The allowlist is asserted against a line the engine actually emits rather than
against a name list, so a field added to the envelope fails this test instead of
being dropped from the payload in silence.
"""
from __future__ import annotations

import json
import tomllib
from pathlib import Path

_REPO = Path(__file__).resolve().parents[5]
_PROFILE = _REPO / "packs/core/.apm/skills/work-loop/profiles/work-loop.toml"


def _engine_module():
    """The engine loaded by path — the same recipe the envelope suite uses."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "core_work_loop_loop_engine_profile_under_test",
        _REPO / "packs/core/.apm/skills/work-loop/scripts/loop-engine.py",
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _one_emitted_line(tmp_path: Path) -> dict:
    """Drive one real transition and return the line it appended."""
    # Sorted to satisfy ruff I001. The approved stub in plan.md lists these
    # names in a different order; only the ordering differs, no assertion does.
    from test_loop_engine_events_jsonl import (
        _LOOP_ENGINE,
        _engine_init,
        _init_git_repo,
        _make_spec_dir,
        _run,
    )

    repo = _init_git_repo(tmp_path)
    spec_dir = _make_spec_dir(repo)
    _engine_init(repo, spec_dir)
    _run(_LOOP_ENGINE, "transition", str(spec_dir), "spec-ready", cwd=repo)
    return json.loads((repo / ".loop-run" / "events.jsonl").read_text().splitlines()[-1])


class TestWorkLoopProfile:
    def test_profile_declares_the_envelope_fields(self) -> None:
        # STUB: AC-0040
        profile = tomllib.loads(_PROFILE.read_text(encoding="utf-8"))
        assert profile["timestamp_field"] == "at"
        assert profile["timestamp_format"] == "rfc3339"
        assert profile["severity_field"] == "result"
        assert profile["identity"] == ["run_id", "seq"]

    def test_severity_map_is_the_pinned_pairs_and_covers_every_gate_result(self, tmp_path) -> None:
        # STUB: AC-0040
        profile = tomllib.loads(_PROFILE.read_text(encoding="utf-8"))
        assert profile["severity_map"] == {"success": 9, "failure": 17}
        # The pinned pairs and the engine's own values are asserted together on
        # purpose: pinning literals alone would silently stop covering the engine
        # the day a third gate result is added.
        missing = set(_engine_module()._GATE_RESULTS.values()) - set(profile["severity_map"])
        assert not missing, f"severity_map omits {sorted(missing)}"

    def test_allowlist_is_exactly_the_unrouted_emitted_keys(self, tmp_path) -> None:
        # STUB: AC-0040
        profile = tomllib.loads(_PROFILE.read_text(encoding="utf-8"))
        emitted = set(_one_emitted_line(tmp_path))
        routed = {"at", "result", "run_id", "seq"}
        assert set(profile["allowlist"]) == emitted - routed
