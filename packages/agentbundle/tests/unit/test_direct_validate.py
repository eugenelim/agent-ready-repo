"""Direct validate output: the AC21 envelope, its exits, and its help."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
from agentbundle.commands import validate as validate_cmd
from agentbundle.direct_source import validate_direct_source
from agentbundle.direct_validate import (
    render_direct_validation_json,
    render_direct_validation_text,
)

ENVELOPE_KEYS = {
    "schema_version",
    "command",
    "operation",
    "agentbundle_version",
    "catalogue_schema_version",
    "ok",
    "diagnostics",
    "summary",
}
DIAGNOSTIC_KEYS = {
    "code", "severity", "pack", "path", "line", "col", "message", "remediation",
}


def _write_skill(path: Path, name: str) -> None:
    path.mkdir(parents=True, exist_ok=True)
    (path / "SKILL.md").write_text(f"---\nname: {name}\n---\n# {name}\n")


def test_direct_validate_json_contract(tmp_path: Path):
    # AC7, AC21 — the established envelope keys plus `summary`, rendered with
    # sort_keys=True and indent=2 so the bytes are stable across runs.
    source = tmp_path / "good"
    _write_skill(source, "good")
    rendered = render_direct_validation_json(validate_direct_source(source))
    payload = json.loads(rendered)

    assert set(payload) == ENVELOPE_KEYS, set(payload) ^ ENVELOPE_KEYS
    assert payload["command"] == "validate"
    assert payload["operation"] == "direct"
    assert payload["ok"] is True
    assert payload["diagnostics"] == []
    # The direct route has no catalogue, so its default is 1 rather than a
    # value read from a catalogue that is not there.
    assert payload["catalogue_schema_version"] == 1
    assert payload["summary"] == {"shape": "root-single", "selected_skills": ["good"]}

    assert rendered == json.dumps(payload, sort_keys=True, indent=2)
    assert rendered == render_direct_validation_json(validate_direct_source(source))

    # A refusal fills `diagnostics` with the full established field set.
    refused = tmp_path / "bad"
    _write_skill(refused / "skills" / "one", "one")
    _write_skill(refused / ".claude" / "skills" / "two", "two")
    failed = json.loads(render_direct_validation_json(validate_direct_source(refused)))
    assert failed["ok"] is False
    assert failed["diagnostics"], "a refusal must report at least one diagnostic"
    for diagnostic in failed["diagnostics"]:
        assert set(diagnostic) == DIAGNOSTIC_KEYS
        assert diagnostic["severity"] == "ERROR"
        assert diagnostic["code"].startswith("CAT-D")
    assert failed["summary"]["shape"] is None


def test_direct_validate_exit_codes(tmp_path: Path, capsys):
    # AC21 — success is 0 and a refusal is 1. Usage errors stay argparse's 2.
    source = tmp_path / "good"
    _write_skill(source, "good")
    assert validate_cmd._run_direct(source, "json") == 0
    assert json.loads(capsys.readouterr().out)["ok"] is True

    refused = tmp_path / "bad"
    _write_skill(refused / "skills" / "one", "one")
    _write_skill(refused / ".claude" / "skills" / "two", "two")
    assert validate_cmd._run_direct(refused, "json") == 1
    assert json.loads(capsys.readouterr().out)["ok"] is False

    assert validate_cmd._run_direct(tmp_path / "missing", "text") == 1
    capsys.readouterr()


def test_direct_validate_text_form(tmp_path: Path):
    # A refusal's text form carries the code, the path, and the recovery.
    refused = tmp_path / "bad"
    _write_skill(refused / "skills" / "one", "one")
    _write_skill(refused / ".claude" / "skills" / "two", "two")
    rendered = render_direct_validation_text(validate_direct_source(refused))
    assert rendered.startswith("FAIL:")
    assert "CAT-D009" in rendered

    source = tmp_path / "good"
    _write_skill(source, "good")
    assert render_direct_validation_text(validate_direct_source(source)).startswith("ok:")


@pytest.mark.parametrize("shape", ["root-single", "collection", "direct-pack"])
def test_summary_reports_every_shape(tmp_path: Path, shape):
    # AC21 — the summary names the shape and the selected skills for each form.
    root = tmp_path / shape
    if shape == "root-single":
        # The identity is the envelope directory name, so it is `shape` here;
        # `solo` in the frontmatter is only a display string.
        _write_skill(root, "solo")
        expected = [shape]
    else:
        _write_skill(root / "skills" / "alpha", "alpha")
        _write_skill(root / "skills" / "beta", "beta")
        expected = ["alpha", "beta"]
        if shape == "direct-pack":
            (root / "pack.toml").write_text(
                'schema = 1\n[pack]\nname = "pack"\nversion = "1.0.0"\n'
            )
    admission = validate_direct_source(root)
    assert admission.ok, admission.diagnostics
    payload = json.loads(render_direct_validation_json(admission))
    assert payload["summary"] == {"shape": shape, "selected_skills": expected}


def test_validate_help_describes_the_direct_form():
    # AC7 — help for validate describes the direct source form.
    result = subprocess.run(
        [sys.executable, "-m", "agentbundle", "validate", "--help"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).resolve().parents[2],
    )
    assert result.returncode == 0, result.stderr
    assert "--format" in result.stdout
    assert "direct source" in result.stdout


def test_every_refusal_names_an_offending_path(tmp_path: Path):
    # AC27 — a refusal with a null path leaves the reader with a rule and
    # nothing to look at. Manual QA caught this: the shared entry point
    # reported `path: null` for every refusal that did not name a more
    # specific one at its raise site.
    refused = tmp_path / "bad"
    _write_skill(refused / "skills" / "one", "one")
    _write_skill(refused / ".claude" / "skills" / "two", "two")

    admission = validate_direct_source(refused)
    assert admission.ok is False
    for diagnostic in admission.diagnostics:
        assert diagnostic.path, f"{diagnostic.code} carries no offending path"
    assert str(refused) in admission.diagnostics[0].path
    assert admission.diagnostics[0].remediation, "a refusal needs a next step"


def test_json_reaches_a_direct_pack_despite_its_pack_toml(tmp_path: Path):
    # AC7 — a direct pack is one of the three direct shapes. Manual QA caught
    # `--format json` being silently ignored for it, because `pack.toml` sent
    # the invocation down the catalogue route, whose output for a valid pack is
    # nothing at all.
    root = tmp_path / "dpack"
    _write_skill(root / "skills" / "one", "one")
    (root / "pack.toml").write_text(
        'schema = 1\n[pack]\nname = "dpack"\nversion = "1.0.0"\n'
    )

    admission = validate_direct_source(root)
    assert admission.ok and admission.classification is not None
    assert admission.classification.shape == "direct-pack"

    class _Args:
        pack_path = str(root)
        strict = False
        format = "json"

    import io
    from contextlib import redirect_stdout

    captured = io.StringIO()
    with redirect_stdout(captured):
        exit_code = validate_cmd.run(_Args())
    assert exit_code == 0
    payload = json.loads(captured.getvalue())
    assert payload["summary"]["shape"] == "direct-pack"
    assert payload["operation"] == "direct"


@pytest.mark.parametrize("output_format", ["text", "json"])
def test_a_direct_pack_takes_the_direct_route_in_either_format(
    tmp_path: Path, output_format: str, capsys
):
    # The route is a property of the source, not of how the caller wants it
    # printed. Routing on `--format` made the same directory take the catalogue
    # route in text and the direct route in JSON, so `validate` and `install`
    # disagreed about what the source was. T2 gives the discriminator: a direct
    # manifest declares a top-level `schema` and a catalogue manifest does not.
    root = tmp_path / f"dpack-{output_format}"
    _write_skill(root / "skills" / "one", "one")
    (root / "pack.toml").write_text(
        'schema = 1\n[pack]\nname = "dpack"\nversion = "1.0.0"\n'
    )

    class _Args:
        pack_path = str(root)
        strict = False
        format = output_format

    assert validate_cmd.run(_Args()) == 0
    captured = capsys.readouterr()
    combined = captured.out + captured.err
    if output_format == "json":
        assert json.loads(captured.out)["operation"] == "direct"
    else:
        assert "direct source valid" in combined
        assert "direct-pack" in combined


def test_a_catalogue_pack_keeps_the_catalogue_route_in_text(tmp_path: Path, capsys):
    # The other half of the discriminator, so the change cannot silently drag
    # every catalogue pack onto the direct route.
    root = tmp_path / "catalogue-pack"
    _write_skill(root / "skills" / "one", "one")
    (root / "pack.toml").write_text('[pack]\nname = "cpack"\nversion = "1.0.0"\n')

    class _Args:
        pack_path = str(root)
        strict = False
        format = "text"

    validate_cmd.run(_Args())
    combined = "".join(capsys.readouterr())
    assert "direct source" not in combined, (
        "a manifest with no top-level schema is a catalogue pack"
    )


def test_a_root_level_collection_is_routed_by_both_commands(tmp_path: Path, capsys):
    # Manual QA found `_has_direct_marker` gating on SKILL.md / skills/ /
    # .claude/skills/, so a repository whose own root IS the collection carried
    # none of them: classification admitted the shape and the CLI in front of it
    # refused with a usage error. Nothing guarded the gate — the only
    # root-collection test called `validate_direct_source` directly, bypassing
    # exactly the code that was broken. Reverting the marker list leaves that
    # test green and this one red.
    from agentbundle.commands import install as install_cmd

    root = tmp_path / "rootcol"
    for name in ("alt-text", "brand-yml"):
        _write_skill(root / name, name)
    (root / "README.md").write_text("# repo\n")

    class _VArgs:
        pack_path = str(root)
        strict = False
        format = "json"

    assert validate_cmd.run(_VArgs()) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["operation"] == "direct"
    assert payload["summary"]["shape"] == "collection"

    target = tmp_path / "target"
    target.mkdir()

    class _IArgs:
        catalogue = str(root)
        output = str(target)
        pack = profile = scope = adapter = skill = None
        all_skills = True
        dry_run = force = yes = False
        yes = True

    assert install_cmd.run(_IArgs()) == 0, (
        "install must route a root-level collection to the direct path, not "
        "refuse it with the `--pack / --profile` usage error"
    )
    capsys.readouterr()
    assert (target / ".claude" / "skills" / "alt-text" / "SKILL.md").exists()


def _validate_args(path: Path, output_format: str = "text"):
    class _A:
        pack_path = str(path)
        format = output_format
        strict = False

    return _A()


def test_a_refusal_raised_while_choosing_the_route_is_not_a_traceback(
    tmp_path: Path, capsys
):
    # `_has_direct_marker` probes the source, so it can refuse: both the entry
    # bound and the marker probe raise `DirectAdmissionError`. Neither
    # `validate.run` nor `install._run` handled it and `cli.main` has no
    # boundary, so an ordinary directory produced a stack trace carrying
    # internal paths on stderr instead of AC21's registered exit-1 refusal.
    from agentbundle.direct_source import DIRECT_MAX_ENTRIES

    crowded = tmp_path / "crowded"
    crowded.mkdir()
    for index in range(DIRECT_MAX_ENTRIES + 1):
        (crowded / f"d{index:05d}").mkdir()

    assert validate_cmd.run(_validate_args(crowded)) == 1
    printed = capsys.readouterr()
    assert "FAIL: direct source refused" in printed.err
    assert "CAT-D012" in printed.err
    assert "Traceback" not in printed.err and "Traceback" not in printed.out

    # The JSON envelope carries the same refusal, not a different one.
    assert validate_cmd.run(_validate_args(crowded, "json")) == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is False
    assert [d["code"] for d in payload["diagnostics"]] == ["CAT-D012"]


def test_install_renders_a_routing_refusal_rather_than_raising(tmp_path: Path, capsys):
    # The same seam on the install side, which routes through the same helper.
    from agentbundle.commands import install as install_cmd
    from agentbundle.direct_source import DIRECT_MAX_ENTRIES

    crowded = tmp_path / "crowded"
    crowded.mkdir()
    for index in range(DIRECT_MAX_ENTRIES + 1):
        (crowded / f"d{index:05d}").mkdir()

    class _A:
        catalogue = str(crowded)
        output = str(tmp_path / "target")
        pack = profile = scope = adapter = None
        skill = None
        all_skills = dry_run = force = False
        yes = True

    assert install_cmd._run(_A()) == 1
    printed = capsys.readouterr().err
    assert "[CAT-D012]" in printed and "Traceback" not in printed


def test_a_root_name_reaching_the_renderer_is_escaped(tmp_path: Path, capsys):
    # `validate_direct_source` assigns `diagnostic.path` AFTER
    # `make_direct_diagnostic` escaped the fields it constructs, and
    # `render_direct_validation_text` prints that field on the strength of that
    # chokepoint. A remote source's root name comes from publisher-controlled
    # archive member names, so the assignment put raw bidi on the terminal.
    # The refusal must be one that supplies NO path of its own, because the
    # assignment under test is the `if not diagnostic.path` fallback. An empty
    # collection root is exactly that shape.
    hostile = tmp_path / "src\u202edrowssap"
    (hostile / "skills").mkdir(parents=True)

    assert validate_cmd.run(_validate_args(hostile)) == 1
    printed = capsys.readouterr()
    assert "no skill envelopes" in printed.err, "the pathless refusal was not reached"
    assert "\u202e" not in printed.err and "\u202e" not in printed.out
    assert "\\u202e" in printed.err

    # And the JSON envelope, whose escaping is otherwise incidental — a
    # `json.dumps` default rather than this chokepoint.
    assert validate_cmd.run(_validate_args(hostile, "json")) == 1
    payload = json.loads(capsys.readouterr().out)
    assert "\u202e" not in json.dumps(payload, ensure_ascii=False)


def test_a_direct_pack_manifest_is_opened_exactly_once_on_the_validate_route(
    tmp_path: Path, monkeypatch
):
    # AC15: "no direct source file is opened twice on any route". The router
    # had to know whether `pack.toml` declares the top-level `schema` before it
    # could choose a route, and answered with `exists()` + `read_text()` — a
    # second open, and one that followed a symlink out of the source, blocked
    # on a FIFO, and materialised an arbitrarily large publisher file before
    # any bound applied. The router now performs the ONE measured read and
    # hands it to admission.
    #
    # Counted at the confined primitive itself, so neither the router nor the
    # inventory can satisfy this by reading through some other door.
    from agentbundle.catalogue_tooling import file_safety

    source = tmp_path / "pack"
    envelope = source / "skills" / "alpha"
    envelope.mkdir(parents=True)
    (envelope / "SKILL.md").write_text(
        "---\nname: alpha\ndescription: A skill inside a direct pack.\n---\n# alpha\n"
    )
    (source / "pack.toml").write_text(
        'schema = 1\n[pack]\nname = "demo"\nversion = "1.0.0"\n'
        'description = "A direct pack used to count manifest reads."\n'
    )

    opens: list[str] = []
    real = file_safety.read_confined_regular_file

    def _counting(root, path, **kwargs):
        opens.append(Path(path).name)
        return real(root, path, **kwargs)

    monkeypatch.setattr(file_safety, "read_confined_regular_file", _counting)
    monkeypatch.setattr(
        "agentbundle.direct_source.read_confined_regular_file", _counting
    )

    assert validate_cmd.run(_validate_args(source)) == 0
    assert opens.count("pack.toml") == 1, (
        f"the root manifest was opened {opens.count('pack.toml')} times on one "
        f"validate run; AC15 allows exactly one read per direct file"
    )
    # The positive control: the run really did read the manifest and the skill,
    # so a count of one is "read once", not "never routed here".
    assert opens.count("SKILL.md") == 1
