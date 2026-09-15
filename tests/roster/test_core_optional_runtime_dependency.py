"""AC-0039: core declares an optional runtime dependency, and lint only reports it.

Roster-owned, and it has to be. The assertion is about THIS repository's
`packs/core/pack.toml` and the catalogue rooted here, so the test runs catalogue
lint with the repository as its root. It previously sat in
`packages/agentbundle/tests/unit/`, which ships inside the agentbundle sdist and
is re-run against an extracted workspace containing neither `catalogue.toml` nor
`packs/core` -- there, lint correctly reported `CAT-L002` instead, and the sdist
artifact gate failed.

The package-level behaviour -- that a missing optional dependency produces an
informational diagnostic -- stays in the package suite against fixture
catalogues. What lives here is the repository fact those fixtures cannot carry.

`build-check.yml` names this file explicitly; roster is not auto-discovered.
"""
from __future__ import annotations

import importlib.metadata as importlib_metadata
import os
import subprocess
from pathlib import Path
from types import SimpleNamespace

import agentbundle.catalogue_tooling.lint as _lint_module
from agentbundle.commands import catalogue_lint as catalogue_lint_command

_REPO = Path(__file__).resolve().parents[2]


def test_core_optional_runtime_dependency_is_report_only(
    monkeypatch,
    capsys,
) -> None:
    """AC-0039: an absent optional dependency is informational and read-only."""
    real_distribution = _lint_module.importlib_metadata.distribution

    def distribution_without_exporter(name: str) -> importlib_metadata.Distribution:
        """Make exporter absence deterministic without hiding other distributions."""
        if name == "jsonl-otlp-exporter":
            raise _lint_module.importlib_metadata.PackageNotFoundError(name)
        return real_distribution(name)

    process_launches: list[tuple[object, ...]] = []

    def reject_process_launch(*args: object, **kwargs: object) -> None:
        """Fail if catalogue lint tries to invoke any external process."""
        process_launches.append(args)
        raise AssertionError(f"catalogue lint invoked a process: {args!r} {kwargs!r}")

    monkeypatch.setattr(
        _lint_module.importlib_metadata,
        "distribution",
        distribution_without_exporter,
    )
    monkeypatch.setattr(subprocess, "Popen", reject_process_launch)
    monkeypatch.setattr(os, "system", reject_process_launch)

    status = catalogue_lint_command.run(SimpleNamespace(
        root=str(_REPO),
        pack="core",
        format="table",
        deep=False,
    ))
    report = capsys.readouterr().err

    assert "── core ──" in report
    assert "jsonl-otlp-exporter" in report
    assert "optional runtime dependency" in report
    assert "unsatisfied" in report
    assert status == 0
    # Not redundant with the raise inside the hook: if catalogue lint ever
    # caught the AssertionError on its way out, the launch would still be
    # recorded here and this line is what would report it.
    assert process_launches == []
