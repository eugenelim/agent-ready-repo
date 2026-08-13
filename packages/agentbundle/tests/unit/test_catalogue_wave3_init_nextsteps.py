"""Plain catalogue-init next-step output tests."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from unittest.mock import patch

from agentbundle.catalogue_tooling.results import (
    InitCatalogueMeta,
    InitResult,
    InitSummary,
    InitVerification,
)
from agentbundle.commands import catalogue_init


def _success_result(target: Path, *, dry_run: bool = False) -> InitResult:
    return InitResult(
        ok=True,
        diagnostics=[],
        schema_version=1,
        command="catalogue init",
        operation="init",
        agentbundle_version="9.9.9-test",
        catalogue_schema_version=1,
        dry_run=dry_run,
        target=str(target),
        catalogue=InitCatalogueMeta(
            name="test-cat",
            display_name="Test Cat",
            description="",
            owner_name="Test Cat",
            preferred_adapter="claude-code",
            minimum_agentbundle_version="9.9.9-test",
        ),
        files=[],
        verification=InitVerification(ok=True, diagnostic_count=0),
        summary=InitSummary(create=3, already_present=0, conflict=0, total=3),
    )


def _args(target: Path, *, output_format: str, dry_run: bool = False) -> argparse.Namespace:
    args = argparse.Namespace(
        preset=None,
        target=str(target),
        dry_run=dry_run,
        name=None,
        display_name=None,
        description=None,
        owner_name=None,
        preferred_adapter=None,
        format=output_format,
    )
    for attribute, _flag in catalogue_init._SELF_HOSTED_ONLY_FLAGS:
        setattr(args, attribute, None)
    return args


def test_success_table_contains_complete_next_steps(
    tmp_path: Path, capsys
) -> None:
    target = tmp_path / "catalogue"
    target.mkdir()
    with patch(
        "agentbundle.catalogue_tooling.initialise.init_catalogue",
        return_value=_success_result(target),
    ):
        assert catalogue_init.run(_args(target, output_format="table")) == 0

    stderr = capsys.readouterr().err
    assert "Next steps:" in stderr
    assert "guides/_shared/reference/catalogue-authoring-standards.md" in stderr
    assert "agentbundle catalogue contracts list" in stderr
    assert "agentbundle catalogue verify" in stderr
    assert f"--root {target}" in stderr


def test_dry_run_omits_next_steps(tmp_path: Path, capsys) -> None:
    target = tmp_path / "catalogue"
    target.mkdir()
    with patch(
        "agentbundle.catalogue_tooling.initialise.init_catalogue",
        return_value=_success_result(target, dry_run=True),
    ):
        assert (
            catalogue_init.run(
                _args(target, output_format="table", dry_run=True)
            )
            == 0
        )
    assert "Next steps:" not in capsys.readouterr().err


def test_json_output_schema_is_unchanged(tmp_path: Path, capsys) -> None:
    target = tmp_path / "catalogue"
    target.mkdir()
    with patch(
        "agentbundle.catalogue_tooling.initialise.init_catalogue",
        return_value=_success_result(target),
    ):
        assert catalogue_init.run(_args(target, output_format="json")) == 0

    document = json.loads(capsys.readouterr().out)
    assert "next_steps" not in document
