"""Construction stubs for direct-source admission and normalization."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from typing import Callable

import pytest


def _write_skill(path: Path, name: str) -> None:
    """Create the smallest admitted direct skill envelope."""

    path.mkdir(parents=True, exist_ok=True)
    (path / "SKILL.md").write_text(f"---\nname: {name}\n---\n# {name}\n")


def _refusal_code(callable_: Callable[[], object], code: str) -> None:
    """Assert a direct admission call emits one registered refusal code."""

    import agentbundle.direct_source as direct_source

    with pytest.raises(direct_source.DirectAdmissionError) as raised:
        callable_()
    assert raised.value.diagnostic.code == code


def test_classification_contract(tmp_path: Path):
    # AC1, AC2, AC14–AC17, AC25, AC32–AC34
    import agentbundle.direct_source as direct_source

    root_single = tmp_path / "root-single"
    _write_skill(root_single, "root-skill")
    (root_single / "repository-context").mkdir()
    (root_single / "repository-context" / "ignored").write_text("ignored")
    root_result = direct_source.admit_direct_source(root_single)
    assert root_result.shape == "root-single"
    assert root_result.files == 1
    assert root_result.entries == 1
    # AC1/E17: identity is the envelope directory name for every shape, so one
    # source cannot carry two identity rules. The envelope here is `root-single`
    # while the frontmatter says `root-skill`, so this asserts which one wins.
    assert root_result.skills[0].name == "root-single"

    collection = tmp_path / "collection"
    _write_skill(collection / "skills" / "category" / "nested-skill", "nested-skill")
    category_result = direct_source.admit_direct_source(collection)
    assert category_result.shape == "collection"
    assert category_result.skills[0].envelope == collection / "skills" / "category" / "nested-skill"

    direct_pack = tmp_path / "direct-pack"
    _write_skill(direct_pack / "skills" / "pack-skill", "pack-skill")
    (direct_pack / "pack.toml").write_text(
        'schema = 1\n[pack]\nname = "pack"\nversion = "1.0.0"\n'
    )
    assert direct_source.admit_direct_source(direct_pack).shape == "direct-pack"

    ambiguous = tmp_path / "ambiguous"
    _write_skill(ambiguous / "skills" / "one", "one")
    _write_skill(ambiguous / ".claude" / "skills" / "two", "two")
    _refusal_code(lambda: direct_source.admit_direct_source(ambiguous), "CAT-D009")

    entry_limit = tmp_path / "entry-limit"
    _write_skill(entry_limit, "entry-limit")
    scripts = entry_limit / "scripts"
    scripts.mkdir()
    for index in range(direct_source.DIRECT_MAX_ENTRIES + 1):
        (scripts / f"entry-{index}").mkdir()
    _refusal_code(lambda: direct_source.admit_direct_source(entry_limit), "CAT-D012")

    depth_limit = tmp_path / "depth-limit"
    envelope = depth_limit / "skills" / "category" / "depth-skill"
    _write_skill(envelope, "depth-skill")
    deep = envelope / "scripts"
    for index in range(direct_source.DIRECT_MAX_DEPTH - 1):
        deep = deep / f"level-{index}"
    deep.mkdir(parents=True)
    (deep / "too-deep.txt").write_text("x")
    _refusal_code(lambda: direct_source.admit_direct_source(depth_limit), "CAT-D013")

    file_limit = tmp_path / "file-limit"
    _write_skill(file_limit, "file-limit")
    payload = file_limit / "scripts"
    payload.mkdir()
    for index in range(direct_source.DIRECT_MAX_FILES):
        (payload / f"file-{index}").write_text("x")
    _refusal_code(lambda: direct_source.admit_direct_source(file_limit), "CAT-D014")

    skill_limit = tmp_path / "skill-limit"
    for index in range(direct_source.DIRECT_MAX_SELECTED_SKILLS + 1):
        _write_skill(skill_limit / "skills" / f"s{index}", f"s{index}")
    _refusal_code(lambda: direct_source.admit_direct_source(skill_limit), "CAT-D015")

    per_file_limit = tmp_path / "per-file-limit"
    _write_skill(per_file_limit, "per-file-limit")
    (per_file_limit / "scripts").mkdir()
    (per_file_limit / "scripts" / "large.txt").write_bytes(
        b"x" * (direct_source.DIRECT_MAX_FILE_BYTES + 1)
    )
    _refusal_code(lambda: direct_source.admit_direct_source(per_file_limit), "CAT-D016")

    total_limit = tmp_path / "total-limit"
    _write_skill(total_limit, "total-limit")
    (total_limit / "scripts").mkdir()
    # Twenty-six files are the minimum that can exceed 25 MiB while each is
    # below 1 MiB; see the T3 plan's contradictory two-file wording.
    for index in range(26):
        (total_limit / "scripts" / f"part-{index}").write_bytes(
            b"x" * (direct_source.DIRECT_MAX_FILE_BYTES - 1)
        )
    _refusal_code(lambda: direct_source.admit_direct_source(total_limit), "CAT-D017")


def test_normalization_projection_parity(tmp_path: Path):
    # AC24, AC25 — the canonical tree is always `skills/<leaf>/`, a collection
    # category level disappears, and nothing survives a refusal.
    import agentbundle.direct_source as direct_source

    # A category-grouped collection and a flat one whose leaves match must
    # normalize to byte-identical trees. That equality IS the flattening
    # claim: `_project_direct_directory` projects exactly one `skills/`
    # level, so a surviving category would silently fail to project.
    grouped = tmp_path / "grouped"
    _write_skill(grouped / "skills" / "category" / "alpha", "alpha")
    (grouped / "skills" / "category" / "alpha" / "scripts").mkdir()
    (grouped / "skills" / "category" / "alpha" / "scripts" / "run.py").write_text("x = 1\n")
    flat = tmp_path / "flat"
    _write_skill(flat / "skills" / "alpha", "alpha")
    (flat / "skills" / "alpha" / "scripts").mkdir()
    (flat / "skills" / "alpha" / "scripts" / "run.py").write_text("x = 1\n")

    def _tree(root: Path) -> dict[str, bytes]:
        return {
            str(path.relative_to(root)): path.read_bytes()
            for path in sorted(root.rglob("*"))
            if path.is_file()
        }

    with direct_source.normalize_direct_source(
        direct_source.admit_direct_source(grouped)
    ) as grouped_norm:
        grouped_tree = _tree(grouped_norm.root)
        grouped_root = grouped_norm.root
        assert grouped_norm.skills == ("alpha",)
        assert grouped_norm.files == 2
    with direct_source.normalize_direct_source(
        direct_source.admit_direct_source(flat)
    ) as flat_norm:
        flat_tree = _tree(flat_norm.root)

    assert grouped_tree == flat_tree
    assert set(grouped_tree) == {"skills/alpha/SKILL.md", "skills/alpha/scripts/run.py"}
    # AC25: the tree is gone once the block exits, on the success path too.
    assert not grouped_root.exists()


def test_normalization_removes_its_tree_when_the_caller_raises(tmp_path: Path):
    # AC25 — a refusal downstream of normalization leaves no temporary tree.
    import agentbundle.direct_source as direct_source

    source = tmp_path / "src"
    _write_skill(source, "leftover")
    captured: list[Path] = []
    with (
        pytest.raises(RuntimeError),
        direct_source.normalize_direct_source(
            direct_source.admit_direct_source(source)
        ) as normalized,
    ):
        captured.append(normalized.root)
        assert normalized.root.exists()
        raise RuntimeError("caller refused after normalization")
    assert captured and not captured[0].exists()


def test_normalized_bytes_are_the_digested_bytes_not_a_second_read(tmp_path: Path):
    # AC15, AC24 — a source replaced between admission and copy cannot change
    # what is installed. This is the replacement race: admission reads and
    # measures the bytes, the source is then rewritten, and normalization must
    # still write what was measured. An implementation that re-reads the source
    # during normalization installs bytes no digest ever covered.
    import agentbundle.direct_source as direct_source

    # The envelope directory name is the identity; `racer` in the frontmatter
    # is only a display string.
    source = tmp_path / "racer"
    _write_skill(source, "racer")
    payload = source / "scripts"
    payload.mkdir()
    (payload / "run.py").write_bytes(b"admitted = True\n")

    admitted = direct_source.admit_direct_source(source)

    # The attacker's window: after measurement, before the copy.
    (payload / "run.py").write_bytes(b"substituted = True\n")
    (source / "SKILL.md").write_text("---\nname: racer\n---\n# substituted\n")

    with direct_source.normalize_direct_source(admitted) as normalized:
        installed = (normalized.root / "skills" / "racer" / "scripts" / "run.py").read_bytes()
    assert installed == b"admitted = True\n", "installed bytes must be the digested bytes"


def test_direct_modules_never_use_a_source_copy_api(tmp_path: Path):
    # AC15, AC24 — the replacement race above is closed by construction, not by
    # care: no direct module may reach a `shutil` copy API, because every one
    # of them re-reads the source at copy time. `shutil.rmtree` is permitted;
    # it deletes the normalization tree and never reads the source.
    import ast

    import agentbundle.direct_source as direct_source

    banned = {"copy", "copy2", "copyfile", "copytree", "copyfileobj", "copymode", "copystat"}
    module_path = Path(direct_source.__file__)
    tree = ast.parse(module_path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr in banned:
            raise AssertionError(
                f"{module_path.name}:{node.lineno} uses shutil.{node.attr}; the direct "
                f"route must write already-measured bytes, never re-read the source"
            )
        if isinstance(node, ast.ImportFrom) and node.module == "shutil":
            for alias in node.names:
                assert alias.name not in banned, (
                    f"{module_path.name}:{node.lineno} imports {alias.name} from shutil"
                )


def test_normalization_reduces_modes_to_executable_or_not(tmp_path: Path):
    # AC24 — a direct source may not carry setuid, setgid, or world-writable
    # bits into a projection; only the executable distinction survives.
    import agentbundle.direct_source as direct_source

    source = tmp_path / "modes"
    _write_skill(source, "modes")
    (source / "scripts").mkdir()
    script = source / "scripts" / "run.sh"
    script.write_text("#!/bin/sh\n")
    script.chmod(0o4777)
    plain = source / "scripts" / "notes.txt"
    plain.write_text("x")
    plain.chmod(0o666)

    with direct_source.normalize_direct_source(
        direct_source.admit_direct_source(source)
    ) as normalized:
        skills = normalized.root / "skills" / "modes" / "scripts"
        assert skills.joinpath("run.sh").stat().st_mode & 0o7777 == 0o755
        assert skills.joinpath("notes.txt").stat().st_mode & 0o7777 == 0o644


def test_bounded_metadata_characterization(monkeypatch):
    # AC14, AC15, AC16, AC17, AC18, AC19, AC20
    import agentbundle.bounded_metadata as bounded_metadata
    from agentbundle.catalogue_tooling import okf_discovery

    limits = bounded_metadata.MetadataLimits()
    discovery_limits = okf_discovery.DiscoveryLimits()
    valid_frontmatter = b"---\nname: demo\ndescription: concise\nmetadata:\n  boundaries:\n    - filesystem_read\n---\n# Demo\n"

    assert bounded_metadata.parse_bounded_metadata(valid_frontmatter) == {
        "name": "demo",
        "description": "concise",
        "metadata": {"boundaries": ["filesystem_read"]},
    }
    assert bounded_metadata.parse_bounded_toml(b"schema = 1\n[pack]\nname = 'demo'\n") == {
        "schema": 1,
        "pack": {"name": "demo"},
    }
    assert limits.max_skill_bytes == 2 * 1024 * 1024
    assert limits.max_pack_toml_bytes == 1024 * 1024
    assert limits.max_frontmatter_bytes == discovery_limits.max_frontmatter_bytes
    assert limits.max_frontmatter_depth == discovery_limits.max_frontmatter_depth
    assert limits.max_list_items == discovery_limits.max_list_items
    assert limits.max_compatibility_keys == discovery_limits.max_compatibility_keys
    assert bounded_metadata.parse_bounded_metadata(valid_frontmatter) == okf_discovery._parse_frontmatter(
        valid_frontmatter,
        "SKILL.md",
        discovery_limits,
    )
    assert bounded_metadata.parse_bounded_metadata(
        valid_frontmatter + b"x" * (1024 * 1024 + 1)
    )["name"] == "demo"

    for forbidden in (b"description: !tag value", b"description: &anchor value", b"description: *anchor"):
        with pytest.raises(bounded_metadata.BoundedMetadataError):
            bounded_metadata.parse_bounded_metadata(b"---\nname: demo\n" + forbidden + b"\n---\n")
    # An unrecognized top-level key is dropped, not refused. Every field in the
    # Agent Skills spec is optional and publishers add their own (`requires`
    # alone appears 832 times in the surveyed corpus), so refusing unknown keys
    # would reject most real skills over metadata the installer never reads.
    assert bounded_metadata.parse_bounded_metadata(
        b"---\nname: demo\nunknown: value\n---\n"
    ) == {"name": "demo"}

    for invalid_toml in (b"[pack\n", b"name = \xff"):
        with pytest.raises(bounded_metadata.BoundedMetadataError):
            bounded_metadata.parse_bounded_toml(invalid_toml)
    with pytest.raises(bounded_metadata.BoundedMetadataError):
        bounded_metadata.parse_bounded_toml(b"x = 1", limits=bounded_metadata.MetadataLimits(max_pack_toml_bytes=0))
    monkeypatch.setattr(
        bounded_metadata.tomllib,
        "loads",
        lambda _: (_ for _ in ()).throw(RuntimeError("parser fault")),
    )
    with pytest.raises(bounded_metadata.BoundedMetadataError):
        bounded_metadata.parse_bounded_toml(b"schema = 1")

    assert bounded_metadata.validate_publisher_value("x" * 4096, "description") == "x" * 4096
    for label in ("name", "description"):
        with pytest.raises(bounded_metadata.BoundedMetadataError):
            bounded_metadata.validate_publisher_value("x" * 4097, label)

    previous_yaml = sys.modules.pop("yaml", None)
    sys.modules.pop("agentbundle.bounded_metadata", None)
    try:
        importlib.import_module("agentbundle.bounded_metadata")
        assert "yaml" not in sys.modules
    finally:
        sys.modules.pop("agentbundle.bounded_metadata", None)
        if previous_yaml is not None:
            sys.modules["yaml"] = previous_yaml


def test_direct_admission_diagnostic_registry(tmp_path: Path):
    # AC9, AC11, AC14, AC21, AC27 — one shared entry point, identical
    # diagnostics, and every emitted code registered.
    import agentbundle.direct_source as direct_source
    from agentbundle.catalogue_tooling.diagnostics import DIRECT_CODES

    # AC14: validation and install preflight are the same call. Asserting they
    # agree would be weaker than this — two implementations can agree on the
    # day they are written. There is one function, and both routes call it.
    assert callable(direct_source.validate_direct_source)

    admitted = tmp_path / "good"
    _write_skill(admitted, "good")
    result = direct_source.validate_direct_source(admitted)
    assert result.ok is True
    assert result.diagnostics == ()
    assert result.classification is not None
    assert result.classification.shape == "root-single"

    # A refusal is reported, never raised, and carries a registered code with
    # its offending path — the same tuple whichever route asked.
    refused = tmp_path / "bad"
    _write_skill(refused / "skills" / "one", "one")
    _write_skill(refused / ".claude" / "skills" / "two", "two")
    first = direct_source.validate_direct_source(refused)
    assert first.ok is False and first.classification is None
    registered = {code.value for code in DIRECT_CODES}
    for diagnostic in first.diagnostics:
        assert diagnostic.code in registered, diagnostic.code
        assert diagnostic.message

    # AC14's parity claim, driven through the two REAL routes. Comparing two
    # calls of `validate_direct_source` to each other — which is what this did
    # — cannot fail: it asserts a function is deterministic, not that install
    # preflight and validation agree. Install must reach the same tuple by
    # actually going through its own entry point.
    import io
    from contextlib import redirect_stderr, redirect_stdout

    from agentbundle.commands import validate as validate_cmd
    from agentbundle.direct_install import run_direct_install

    validate_err = io.StringIO()
    with redirect_stderr(validate_err), redirect_stdout(io.StringIO()):
        validate_exit = validate_cmd._run_direct(refused, "text")

    class _Args:
        catalogue = str(refused)
        output = str(tmp_path / "target")
        pack = profile = scope = adapter = skill = None
        all_skills = dry_run = force = False
        yes = True

    Path(_Args.output).mkdir(exist_ok=True)
    install_err = io.StringIO()
    with redirect_stderr(install_err), redirect_stdout(io.StringIO()):
        install_exit = run_direct_install(_Args(), refused)

    assert validate_exit == install_exit == 1
    code = first.diagnostics[0].code
    assert code in validate_err.getvalue(), validate_err.getvalue()
    assert code in install_err.getvalue(), install_err.getvalue()
    assert first.diagnostics[0].message in validate_err.getvalue()
    assert first.diagnostics[0].message in install_err.getvalue()


def test_identity_collision_is_nfc_normalized_and_case_folded(tmp_path: Path):
    # AC11 — collisions compare NFC-normalized, case-folded names, because a
    # case-insensitive filesystem collapses `Alpha` and `alpha` onto one
    # directory and installs one skill over the other silently.
    #
    # The rule is driven directly rather than through an on-disk fixture: on
    # macOS and Windows the colliding pair cannot be created at all — the
    # filesystem merges them before admission ever sees two envelopes — so a
    # tmp_path fixture would pass here by producing one skill and would only
    # exercise the rule on Linux.
    import agentbundle.direct_source as direct_source

    def _skill(name: str) -> direct_source.DirectSkill:
        return direct_source.DirectSkill(
            name=name, envelope=tmp_path / name, files=()
        )

    for first, second in (
        ("alpha", "Alpha"),
        ("alpha", "ALPHA"),
        ("caf\u00e9", "cafe\u0301"),  # NFC vs NFD spelling of the same name
    ):
        with pytest.raises(Exception) as raised:
            direct_source._enforce_unique_skill_names((_skill(first), _skill(second)))
        assert raised.value.diagnostic.code == "CAT-D011", (first, second)

    # Genuinely distinct identities still pass.
    direct_source._enforce_unique_skill_names((_skill("alpha"), _skill("beta")))


def test_recovery_commands_quote_every_interpolated_value():
    # AC11 — a recovery command is text a reader is invited to paste into a
    # shell, and a publisher chooses the skill name inside it.
    from agentbundle.direct_source import recovery_command

    assert recovery_command("agentbundle", "install", "plain") == (
        "agentbundle install plain"
    )
    hostile = recovery_command("agentbundle", "install", "--skill", "a; rm -rf /")
    assert "'a; rm -rf /'" in hostile
    assert hostile.count(";") == 1, "the separator must stay inside the quotes"
    for value in ("with space", "quote'inside", "$(id)", "`id`", "a\nb"):
        assert value not in recovery_command("x", value) or "'" in recovery_command(
            "x", value
        )


def test_entry_budget_accumulates_across_measured_directories(tmp_path: Path):
    # AC33 — the entry allowance is shared across every enumerated
    # directory, not granted afresh per call.
    #
    # This is the fixture no per-directory implementation can pass, and it is
    # built from DIRECTORIES on purpose: 2,800 directories consume 2,800 entries
    # while contributing zero files, so an implementation that threads
    # `len(files)` sees 0 used and hands the full 2,500 to each call. File count
    # deliberately stays under its own 1,000 bound so this can only reach the
    # entry code.
    from agentbundle.direct_source import DIRECT_MAX_ENTRIES, admit_direct_source

    root = tmp_path / "src"
    (root / "scripts").mkdir(parents=True)
    (root / "references").mkdir(parents=True)
    (root / "SKILL.md").write_text("---\nname: root-single\n---\nbody\n")
    for i in range(1_400):
        (root / "scripts" / f"d{i}").mkdir()
        (root / "references" / f"d{i}").mkdir()

    total = 2 * 1_400
    assert total > DIRECT_MAX_ENTRIES, "fixture must exceed the shared entry bound"

    _refusal_code(lambda: admit_direct_source(root), "CAT-D012")


def test_entry_integrity_refusal_names_its_path_and_is_not_a_budget(tmp_path: Path):
    # AC33 — an entry-integrity refusal carries its own registered code
    # and names the offending path, and is never reported as a budget breach.
    from agentbundle.direct_source import admit_direct_source

    root = tmp_path / "src"
    envelope = root / "skills" / "one"
    _write_skill(envelope, "one")
    (envelope / "scripts").mkdir()
    (envelope / "scripts" / "real.py").write_text("print(1)\n")
    (envelope / "scripts" / "link.py").symlink_to("real.py")

    with pytest.raises(Exception) as raised:
        admit_direct_source(root)
    diagnostic = raised.value.diagnostic
    assert diagnostic.code == "CAT-D009", "integrity refusal, never a budget code"
    assert diagnostic.path, "AC33 requires the offending path, carried as data"
    assert "link.py" in diagnostic.path


def test_block_scalar_frontmatter_matches_a_real_yaml_parser():
    # AC16, AC18 — 22% of published skills write `description:` as a YAML block
    # scalar, so the bounded subset parser has to read the literal (`|`) and
    # folded (`>`) styles with every chomping indicator. Both parsers are
    # checked because AC16 pins the direct route's parser as lifted unchanged
    # from catalogue discovery; a fix applied to one and not the other is the
    # drift this asserts against.
    import agentbundle.bounded_metadata as bounded_metadata
    from agentbundle.catalogue_tooling import okf_discovery

    limits = bounded_metadata.MetadataLimits()
    discovery_limits = okf_discovery.DiscoveryLimits()

    # Expected values are YAML's, not ours: folding joins lines with a space,
    # a blank line becomes a newline, and clip keeps a trailing break only when
    # the input actually contains one. The last case has no trailing newline
    # because a closing `---` fence leaves the slice without one.
    cases = [
        ("description: >\n  one two\n  three\n", {"description": "one two three\n"}),
        ("description: >-\n  one two\n  three\n", {"description": "one two three"}),
        ("description: |\n  first\n  second\n", {"description": "first\nsecond\n"}),
        ("description: |-\n  first\n  second\n", {"description": "first\nsecond"}),
        ("description: >\n  para one\n\n  para two\n", {"description": "para one\npara two\n"}),
        ("metadata:\n  summary: >\n    nested folded\n    text\n",
         {"metadata": {"summary": "nested folded text\n"}}),
        ("name: demo\ndescription: >\n  folded\nmodel: opus\n",
         {"name": "demo", "description": "folded\n", "model": "opus"}),
        ("description: >\n  no trailing break", {"description": "no trailing break"}),
    ]
    for raw, expected in cases:
        assert bounded_metadata._parse_subset(raw, "SKILL.md", limits) == expected, raw
        assert okf_discovery.parse_frontmatter_subset(
            raw, "SKILL.md", discovery_limits
        ) == expected, raw

    # An explicit indentation indicator (`>2`) is refused rather than guessed
    # at, because silently mis-reading the indent changes the parsed value.
    for unsupported in ("description: >2\n  text\n", "description: |3\n  text\n"):
        with pytest.raises(bounded_metadata.BoundedMetadataError):
            bounded_metadata._parse_subset(unsupported, "SKILL.md", limits)

    # A block scalar reaches admission through the whole envelope path, not
    # just the parser in isolation. A trailing block gets no final newline:
    # the frontmatter slice stops at the closing `---` fence, so there is no
    # line break for clip chomping to keep. A block followed by another key
    # does keep one, which is why both shapes are asserted here.
    assert bounded_metadata.parse_bounded_metadata(
        b"---\nname: demo\ndescription: >\n  folded across\n  two lines\n---\n# Demo\n"
    ) == {"name": "demo", "description": "folded across two lines"}
    assert bounded_metadata.parse_bounded_metadata(
        b"---\ndescription: >\n  folded across\n  two lines\nmodel: opus\n---\n# Demo\n"
    ) == {"description": "folded across two lines\n", "model": "opus"}


def test_a_remote_root_single_takes_the_repository_name(tmp_path: Path):
    # AC1/E17 — a GitHub archive extracts under a `<repo>-<ref>/` wrapper, so
    # the enclosing directory encodes the commit. Using it would change the
    # installed identity on every upgrade, which is the instability that argued
    # for the frontmatter name before the corpus ruled that out.
    import agentbundle.direct_source as direct_source

    wrapper = tmp_path / "skills-3b3fad96af16a10759d930941b4520ba0c40edae"
    _write_skill(wrapper, "anything")

    # Without the declaration, identity is the wrapper — commit and all.
    assert direct_source.admit_direct_source(wrapper).skills[0].name == wrapper.name

    direct_source.declare_remote_root_identity(wrapper, "skills")
    try:
        assert direct_source.admit_direct_source(wrapper).skills[0].name == "skills"
    finally:
        direct_source._REMOTE_ROOT_IDENTITY.pop(wrapper, None)


def _corpus_fixture() -> dict:
    """Load the committed AC35 corpus verdict table."""
    import json

    return json.loads(
        (
            Path(__file__).resolve().parents[1]
            / "fixtures"
            / "direct"
            / "ac35_corpus_verdicts.json"
        ).read_text(encoding="utf-8")
    )


def test_ac35_corpus_table_pins_the_bound_constants():
    # AC35 — the table is re-asserted whenever a bound or a shape rule changes.
    # A measurement-versus-limit assertion alone is one-directional: it reddens
    # only when a bound is LOWERED past a recorded measurement, and for depth,
    # selected skills, and total bytes this corpus records no attributable
    # refusal, so no raise could ever redden it. Pinning each constant to a
    # committed value makes a change in either direction fail here.
    import agentbundle.direct_source as direct_source

    bounds = _corpus_fixture()["bounds"]
    assert bounds == {
        "entries": direct_source.DIRECT_MAX_ENTRIES,
        "depth": direct_source.DIRECT_MAX_DEPTH,
        "files": direct_source.DIRECT_MAX_FILES,
        "selected_skills": direct_source.DIRECT_MAX_SELECTED_SKILLS,
        "per_file_bytes": direct_source.DIRECT_MAX_FILE_BYTES,
        "total_bytes": direct_source.DIRECT_MAX_TOTAL_BYTES,
    }, "regenerate the corpus table: a Family-2 bound moved"

    # The committed values themselves, so a coordinated change to both the
    # constants and the fixture still has to be deliberate.
    assert bounds == {
        "entries": 2500,
        "depth": 12,
        "files": 1000,
        "selected_skills": 500,
        "per_file_bytes": 1024 * 1024,
        "total_bytes": 25 * 1024 * 1024,
    }


def test_ac35_corpus_table_is_complete_and_attributable():
    # AC35 — at least fifteen real repositories, one recorded verdict each, the
    # measured columns present for REFUSED repositories too, and every refusal
    # attributable to a named shape exclusion or a named budget.
    from agentbundle.catalogue_tooling.diagnostics import DIRECT_CODES

    fixture = _corpus_fixture()
    rows = fixture["repositories"]
    assert len(rows) >= 15, f"AC35 requires at least fifteen repositories, got {len(rows)}"
    assert len({row["repository"] for row in rows}) == len(rows), "duplicate repository"

    measured = ("entries", "depth", "files", "largest_file", "total_bytes")
    registered = {code.value for code in DIRECT_CODES}
    for row in rows:
        for column in measured:
            assert isinstance(row[column], int), (
                f"{row['repository']} is missing the {column} column; AC35 requires "
                f"it for refused repositories too"
            )
        assert row["verdict"] in {"admitted", "refused"}
        if row["verdict"] == "refused":
            # An unclassified or unattributable refusal fails this criterion.
            assert row["code"] in registered, (
                f"{row['repository']} refused with an unregistered code {row['code']}"
            )
            assert row["reason"], f"{row['repository']} refused with no stated reason"
        else:
            assert row["shape"] in {"root-single", "collection", "direct-pack"}
            assert row["selected_skills"] >= 1
        assert row["allowlist_failures"] == [], (
            f"{row['repository']} carries a publisher value that fails the AC18 "
            f"allowlist: {row['allowlist_failures']}"
        )


def test_ac35_recorded_measurements_respect_the_bounds_they_were_measured_against():
    # Every admitted repository's recorded measurement must sit inside the bound
    # it was admitted under. This is the direction that catches a bound being
    # lowered below something the corpus already admits.
    fixture = _corpus_fixture()
    bounds = fixture["bounds"]
    for row in fixture["repositories"]:
        if row["verdict"] != "admitted":
            continue
        assert row["admitted_entries"] <= bounds["entries"], row["repository"]
        assert row["admitted_files"] <= bounds["files"], row["repository"]
        assert row["admitted_total_bytes"] <= bounds["total_bytes"], row["repository"]
        assert row["selected_skills"] <= bounds["selected_skills"], row["repository"]


def test_a_repository_root_may_itself_be_the_collection(tmp_path: Path):
    # RFC-0098 E22 — publishers commonly put skill folders straight at the
    # repository root with no `skills/` wrapper; two of eighteen surveyed
    # repositories do, and refusing them left a real publishing shape
    # unreachable. Still one level: a child holding SKILL.md is an envelope,
    # exactly as it would be under `skills/`.
    import agentbundle.direct_source as direct_source

    root = tmp_path / "posit-style"
    for name in ("alt-text", "brand-yml"):
        _write_skill(root / name, name)
    (root / "README.md").write_text("# repo\n")
    (root / "count.py").write_text("x = 1\n")

    result = direct_source.validate_direct_source(root)
    assert result.ok, result.diagnostics
    assert result.classification is not None
    assert result.classification.shape == "collection"
    assert sorted(s.name for s in result.classification.skills) == ["alt-text", "brand-yml"]


def test_the_root_collection_shape_is_the_last_resort(tmp_path: Path):
    # It is reached only after every other marker is ruled out, so a repository
    # that has `skills/` uses that and a decoy at the root is not discovered.
    import agentbundle.direct_source as direct_source

    root = tmp_path / "has-skills-dir"
    _write_skill(root / "skills" / "inner", "inner")
    _write_skill(root / "decoy", "decoy")

    result = direct_source.validate_direct_source(root)
    assert result.ok, result.diagnostics
    assert result.classification is not None
    assert [s.name for s in result.classification.skills] == ["inner"]

    # A repository with no skills anywhere still refuses.
    empty = tmp_path / "links-only"
    empty.mkdir()
    (empty / "README.md").write_text("# links\n")
    refused = direct_source.validate_direct_source(empty)
    assert refused.ok is False
    assert "no supported shape" in refused.diagnostics[0].message


def test_a_symlinked_root_child_still_refuses(tmp_path: Path):
    # The root-collection shape selects candidates with `is_dir()`, which
    # follows a link. Integrity is not weakened: the confined traversal refuses
    # the link before anything is read.

    import agentbundle.direct_source as direct_source

    root = tmp_path / "linked"
    _write_skill(root / "real", "real")
    Path(root / "alias").symlink_to(root / "real")

    result = direct_source.validate_direct_source(root)
    assert result.ok is False
    assert result.diagnostics[0].code == "CAT-D009"


def test_an_empty_git_placeholder_is_admitted_and_a_full_one_is_not(tmp_path: Path):
    # RFC-0098 E22 — the hidden-entry rule guards against a dotfile carrying
    # instructions, which an empty Git placeholder cannot. Refusing a whole
    # repository over a zero-byte `.gitkeep` rejected real sources for a file
    # with no content.
    import agentbundle.direct_source as direct_source

    def _source(name: str, content: str) -> Path:
        root = tmp_path / f"src-{name.lstrip('.')}-{len(content)}"
        _write_skill(root / "skills" / "a", "a")
        (root / "skills" / "a" / "references").mkdir(parents=True)
        (root / "skills" / "a" / "references" / name).write_text(content)
        return root

    for placeholder in (".gitkeep", ".keep"):
        assert direct_source.validate_direct_source(_source(placeholder, "")).ok, placeholder

    # The relaxation is by name AND emptiness: a placeholder carrying bytes is
    # a hidden file with content, which is the thing the rule exists to refuse.
    full = direct_source.validate_direct_source(_source(".gitkeep", "instructions"))
    assert full.ok is False
    assert "not empty" in full.diagnostics[0].message

    # Every other dotfile still refuses, EMPTY OR NOT: the relaxation is by
    # name and emptiness together, so an empty `.env` must not slip through the
    # emptiness half.
    for content in ("TOKEN=x", ""):
        other = direct_source.validate_direct_source(_source(".env", content))
        assert other.ok is False, f".env with {len(content)} bytes was admitted"
        assert "hidden entry" in other.diagnostics[0].message


def test_the_two_frontmatter_parsers_have_not_drifted():
    # AC16 pins `bounded_metadata`'s parser as lifted from `okf_discovery`, and
    # the block-scalar support added by this spec landed in both. They cannot be
    # merged: `okf_discovery` imports `file_safety` and so has a filesystem API,
    # which `bounded_metadata` deliberately does not — a fresh direct-module
    # import must leave that surface absent.
    #
    # So the duplication stays and is policed instead. Source equality of the
    # shared functions is the check the copies never had: `_sweep_guard` exists
    # because four adapters carried "keep in sync" comments and three drifted
    # anyway, and a comment is not a control.
    import ast
    import inspect
    from pathlib import Path

    import agentbundle.bounded_metadata as bounded_metadata
    from agentbundle.catalogue_tooling import okf_discovery

    shared = ("_is_block_scalar_header", "_consume_block_scalar")

    def _bodies(module) -> dict[str, str]:
        tree = ast.parse(Path(module.__file__).read_text(encoding="utf-8"))
        return {
            node.name: ast.dump(node)
            for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef) and node.name in shared
        }

    direct = _bodies(bounded_metadata)
    catalogue = _bodies(okf_discovery)
    for name in shared:
        assert name in direct, f"{name} missing from bounded_metadata"
        assert name in catalogue, f"{name} missing from okf_discovery"
        assert direct[name] == catalogue[name], (
            f"{name} has drifted between the two parsers; AC16 pins them as the "
            f"same primitive and nothing else compares them"
        )

    # And the behaviour they exist for agrees on the forms that matter.
    limits = bounded_metadata.MetadataLimits()
    discovery_limits = okf_discovery.DiscoveryLimits()
    for raw in (
        "description: >\n  folded one\n  folded two\n",
        "description: |-\n  literal\n  lines\n",
        "metadata:\n  summary: >+\n    kept\n\n",
        "name: plain\ndescription: single line\n",
    ):
        assert bounded_metadata._parse_subset(
            raw, "SKILL.md", limits
        ) == okf_discovery.parse_frontmatter_subset(raw, "SKILL.md", discovery_limits), raw

    assert inspect.getmodule(bounded_metadata) is not inspect.getmodule(okf_discovery)
