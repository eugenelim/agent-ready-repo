"""Executable guards for the direct lifecycle's grounded facts."""

from __future__ import annotations

import ast
from argparse import Namespace
from dataclasses import fields
from pathlib import Path

from tests._direct_acquisition import GitHttpsAcquisitionFake


def _direct_args(source: str, target: Path, **overrides: object):
    """Build the direct-install argument object used by these fact checks."""

    class _Args:
        catalogue = source
        output = str(target)
        pack = profile = scope = adapter = None
        skill = ["alpha"]
        all_skills = dry_run = force = False
        yes = True

    for key, value in overrides.items():
        setattr(_Args, key, value)
    return _Args()


def _skill_tree(root: Path, body: str) -> Path:
    """Stage one admissible skill collection with distinguishable bytes."""

    skill = root / "skills" / "alpha"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text(
        f"---\nname: alpha\n---\n# {body}\n", encoding="utf-8"
    )
    return root


def _capability_skill_tree(root: Path) -> Path:
    """Stage a skill whose source bytes exercise every capability axis."""

    skill = root / "skills" / "alpha"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text(
        "---\n"
        "name: alpha\n"
        "allowed-tools:\n"
        "  - read\n"
        "metadata:\n"
        "  boundaries:\n"
        "    - network\n"
        "  credentialed: true\n"
        "---\n"
        "# alpha\n",
        encoding="utf-8",
    )
    return root


def test_f7_remote_yes_refusal_happens_before_acquisition(
    tmp_path: Path, tmp_path_factory, capsys, monkeypatch
) -> None:
    """A remote wet install without consent cannot claim an unread summary."""

    from agentbundle.direct_install import (
        ADMISSIBILITY_VERDICT,
        PUBLISHER_BLOCK_CLOSE,
        PUBLISHER_BLOCK_OPEN,
        run_direct_install,
    )

    source = "git+https://github.com/example/lifecycle@release-1"
    fake = GitHttpsAcquisitionFake(monkeypatch, tmp_path_factory.mktemp("direct-acquisition"))
    fake.publish("example/lifecycle", "release-1", _skill_tree(tmp_path / "source", "one"))

    assert run_direct_install(_direct_args(source, tmp_path / "target", yes=False), source) == 1

    captured = capsys.readouterr()
    assert fake.calls == []
    assert "requires --yes" in captured.err
    assert PUBLISHER_BLOCK_OPEN not in captured.err
    assert PUBLISHER_BLOCK_CLOSE not in captured.err
    assert ADMISSIBILITY_VERDICT not in captured.err


def test_f7_remote_dry_run_reaches_acquisition_without_yes(
    tmp_path: Path, tmp_path_factory, capsys, monkeypatch
) -> None:
    """A remote dry run acquires and admits bytes without the wet-run consent flag."""

    from agentbundle.direct_install import (
        ADMISSIBILITY_VERDICT,
        PUBLISHER_BLOCK_OPEN,
        run_direct_install,
    )

    source = "git+https://github.com/example/lifecycle@release-1"
    fake = GitHttpsAcquisitionFake(monkeypatch, tmp_path_factory.mktemp("direct-acquisition"))
    fake.publish("example/lifecycle", "release-1", _skill_tree(tmp_path / "source", "one"))

    args = _direct_args(source, tmp_path / "target", yes=False, dry_run=True)
    assert run_direct_install(args, source) == 0

    captured = capsys.readouterr()
    assert fake.calls == [source]
    assert "requires --yes" not in captured.err
    assert ADMISSIBILITY_VERDICT in captured.err
    assert PUBLISHER_BLOCK_OPEN in captured.err


def test_git_https_acquisition_fake_replaces_a_moved_ref(
    tmp_path: Path, tmp_path_factory, capsys, monkeypatch
) -> None:
    """Re-publishing a ref returns fresh bytes and a new deterministic revision."""

    from agentbundle.config import load_state
    from agentbundle.direct_install import run_direct_install

    fake = GitHttpsAcquisitionFake(monkeypatch, tmp_path_factory.mktemp("direct-acquisition"))
    source = "git+https://github.com/example/lifecycle@release-1"
    first_revision = fake.publish(
        "example/lifecycle", "release-1", _skill_tree(tmp_path / "one", "one")
    )
    target = tmp_path / "target"
    target.mkdir()

    assert run_direct_install(_direct_args(source, target), source) == 0
    capsys.readouterr()
    row = load_state(target / ".agentbundle-state.toml").row("alpha", "claude-code")
    assert row is not None and row.source_revision == first_revision
    assert (target / ".claude" / "skills" / "alpha" / "SKILL.md").read_bytes() == (
        b"---\nname: alpha\n---\n# one\n"
    )

    fake.publish("example/lifecycle", "release-1", _skill_tree(tmp_path / "two", "two"))
    second = fake.acquire(source, parent=tmp_path)
    second_bytes = (second.root / "skills" / "alpha" / "SKILL.md").read_bytes()

    assert first_revision != second.revision
    assert second_bytes == b"---\nname: alpha\n---\n# two\n"
    assert fake.calls == [source, source]


def test_git_https_acquisition_fake_snapshots_published_bytes(
    tmp_path: Path, tmp_path_factory, monkeypatch
) -> None:
    """Mutating a caller tree does not alter an already-published revision."""

    fake = GitHttpsAcquisitionFake(monkeypatch, tmp_path_factory.mktemp("direct-acquisition"))
    source = "git+https://github.com/example/lifecycle@release-1"
    tree = _skill_tree(tmp_path / "source", "published")
    fake.publish("example/lifecycle", "release-1", tree)
    (tree / "skills" / "alpha" / "SKILL.md").write_text(
        "---\nname: alpha\n---\n# changed after publication\n", encoding="utf-8"
    )

    acquired = fake.acquire(source, parent=tmp_path)
    assert (acquired.root / "skills" / "alpha" / "SKILL.md").read_bytes() == (
        b"---\nname: alpha\n---\n# published\n"
    )


def test_git_https_acquisition_fake_refuses_links(
    tmp_path: Path, tmp_path_factory, monkeypatch
) -> None:
    """A fixture source carrying a link fails before it can become an archive."""

    import pytest
    from agentbundle.catalogue_tooling.diagnostics import DiagnosticCode
    from agentbundle.direct_source_acquisition import DirectAcquisitionError

    fake = GitHttpsAcquisitionFake(monkeypatch, tmp_path_factory.mktemp("direct-acquisition"))
    tree = _skill_tree(tmp_path / "source", "published")
    link = tree / "linked-skill"
    try:
        link.symlink_to(tree / "skills")
    except OSError:
        pytest.skip("symlinks are unavailable on this platform")

    with pytest.raises(DirectAcquisitionError) as refused:
        fake.publish("example/lifecycle", "release-1", tree)
    assert refused.value.diagnostic.code == DiagnosticCode.CAT_D007


def test_f1_direct_source_grammar_and_ref_classification() -> None:
    """The parser owns ref kinds, default-ref refusal, and request normalization."""

    import pytest
    from agentbundle.catalogue_tooling.diagnostics import DiagnosticCode
    from agentbundle.direct_source_acquisition import (
        DirectAcquisitionError,
        archive_url,
        parse_direct_source,
    )

    prefix = "git+https://github.com/owner/repository@"
    assert parse_direct_source(prefix + ("a" * 40)).ref_kind == "sha"
    assert parse_direct_source(prefix + "abcdef1").ref_kind == "abbreviated-sha"
    assert parse_direct_source(prefix + ("a" * 39)).ref_kind == "abbreviated-sha"
    assert parse_direct_source(prefix + "release/v1.0").ref_kind == "ref"

    with pytest.raises(DirectAcquisitionError) as hexadecimal:
        parse_direct_source(prefix + ("a" * 41))
    assert hexadecimal.value.diagnostic.code == DiagnosticCode.CAT_D003

    with pytest.raises(DirectAcquisitionError) as too_short:
        parse_direct_source(prefix + ("a" * 6))
    assert too_short.value.diagnostic.code == DiagnosticCode.CAT_D003

    for default_ref in ("main", "master", "HEAD"):
        with pytest.raises(DirectAcquisitionError) as defaulted:
            parse_direct_source(prefix + default_ref)
        assert defaulted.value.diagnostic.code == DiagnosticCode.CAT_D002

    with pytest.raises(DirectAcquisitionError) as path_component:
        parse_direct_source("git+https://github.com/owner/repository/path@v1")
    assert path_component.value.diagnostic.code == DiagnosticCode.CAT_D001

    plain = parse_direct_source("git+https://github.com/owner/repository@v1")
    dotted = parse_direct_source("git+https://github.com/owner/repository.git@v1")
    assert archive_url(plain) == archive_url(dotted)


def test_f2_capability_surface_and_delta_semantics() -> None:
    """Capability absence and content drift remain observable to lifecycle code."""

    from agentbundle.direct_install import _normalised_allowed_tools
    from agentbundle.direct_source_state import (
        UNDECLARED_TOOLS,
        Capabilities,
        CapabilityDelta,
        _normalised_credentialed,
        _tool_display,
        compare_capabilities,
    )

    assert _tool_display(None) == frozenset({UNDECLARED_TOOLS})
    assert _normalised_credentialed(None) == "undeclared"
    assert _normalised_credentialed(True) == "true"
    assert _normalised_credentialed(False) == "false"
    assert _normalised_credentialed("yes") == "yes"
    for metadata in ({}, {"allowed-tools": []}, {"allowed-tools": ""}):
        assert _normalised_allowed_tools(metadata, source="fixture") == []

    assert not CapabilityDelta((), unknown=False).requires_reconsent
    assert CapabilityDelta((), unknown=True).requires_reconsent
    assert CapabilityDelta(("anything",), unknown=False).requires_reconsent

    original = Capabilities(
        allowed_tools=frozenset({"read"}),
        skill_digest="skill-one",
        skill_identities=frozenset({"alpha"}),
        payload_digests={"references/guide.md": "payload-one"},
        boundaries=frozenset({"network"}),
        credentialed=False,
    )
    unknown = compare_capabilities(None, original)
    assert unknown.unknown is True
    assert unknown.differences == ()

    skill_changed = Capabilities(
        allowed_tools=original.allowed_tools,
        skill_digest="skill-two",
        skill_identities=original.skill_identities,
        payload_digests=original.payload_digests,
        boundaries=original.boundaries,
        credentialed=original.credentialed,
    )
    payload_changed = Capabilities(
        allowed_tools=original.allowed_tools,
        skill_digest=original.skill_digest,
        skill_identities=original.skill_identities,
        payload_digests={"references/guide.md": "payload-two"},
        boundaries=original.boundaries,
        credentialed=original.credentialed,
    )
    for candidate in (skill_changed, payload_changed):
        delta = compare_capabilities(original, candidate)
        assert len(delta.differences) == 1
        assert delta.requires_reconsent is True


def test_f3_direct_state_fields_and_constructor_defaults(
    tmp_path: Path, capsys, monkeypatch
) -> None:
    """A direct row is equivalent to a reconstruction from its nine written fields."""

    import agentbundle.config as config
    from agentbundle.config import PackState, State, dump_state, load_state
    from agentbundle.direct_install import run_direct_install
    from agentbundle.direct_source import MANIFESTLESS_VERSION_SENTINEL

    all_fields = {
        "installed_version",
        "source",
        "install_route",
        "scope",
        "primitives",
        "files",
        "primitive_versions",
        "adapter",
        "target_file",
        "hook_wiring_owned",
        "user_root",
        "artifact_uri",
        "archive_sha256",
        "source_revision",
        "source_kind",
        "source_path",
        "source_digest",
    }
    written = {
        "installed_version",
        "source",
        "scope",
        "adapter",
        "source_revision",
        "source_kind",
        "source_path",
        "source_digest",
        "files",
    }
    never_written = {
        "archive_sha256",
        "artifact_uri",
        "install_route",
        "primitives",
        "primitive_versions",
        "target_file",
        "hook_wiring_owned",
        "user_root",
    }
    assert {state_field.name for state_field in fields(PackState)} == all_fields
    assert written.isdisjoint(never_written)
    assert written | never_written == all_fields

    source = _skill_tree(tmp_path / "source", "one")
    loaded_rows = {}
    for adapter in ("claude-code", "codex"):
        target = tmp_path / adapter
        target.mkdir()
        actual_pack_state = config.PackState
        constructor_calls = []

        def record_pack_state(
            *args,
            _calls=constructor_calls,
            _pack_state=actual_pack_state,
            **kwargs,
        ):
            _calls.append((args, kwargs))
            return _pack_state(*args, **kwargs)

        with monkeypatch.context() as patch:
            patch.setattr(config, "PackState", record_pack_state)
            assert run_direct_install(_direct_args(str(source), target, adapter=adapter), source) == 0
        capsys.readouterr()
        assert len(constructor_calls) == 1
        arguments, keywords = constructor_calls[0]
        assert arguments == ()
        assert set(keywords) == written
        row = load_state(target / ".agentbundle-state.toml").row("alpha", adapter)
        assert row is not None
        assert row.install_route == "cli"
        assert row.user_root == "~/.agentbundle"
        assert row.primitives == []
        reconstructed = PackState(**{name: getattr(row, name) for name in written})
        reconstruction_path = target / "reconstructed-state.toml"
        reconstruction_path.write_text(
            dump_state(State(packs={("alpha", adapter): reconstructed})), encoding="utf-8"
        )
        round_tripped = load_state(reconstruction_path).row("alpha", adapter)
        assert round_tripped == row
        loaded_rows[adapter] = row

    assert loaded_rows["codex"].installed_version == MANIFESTLESS_VERSION_SENTINEL
    assert loaded_rows["codex"].adapter == "codex"


def test_f6_stored_source_preserves_remote_and_non_repo_spellings(tmp_path: Path) -> None:
    """Only a repo-scope, in-repository local source is stored relatively."""

    from agentbundle.direct_install import stored_source_for

    root = tmp_path / "repository"
    inside = root / "vendor" / "skill"
    outside = tmp_path / "external" / "skill"
    inside.mkdir(parents=True)
    outside.mkdir(parents=True)
    remote = "git+https://github.com/Owner/Repository.git@v1"

    assert stored_source_for(str(inside), "repo", root) == "vendor/skill"
    assert stored_source_for(remote, "repo", root) == remote
    assert stored_source_for(str(outside), "repo", root) == str(outside)
    assert stored_source_for(str(inside), "user", root) == str(inside)


def test_f8_uninstall_removes_a_clean_manifestless_row(tmp_path: Path, capsys) -> None:
    """The existing uninstall route removes every still-owned direct file."""

    from agentbundle.commands.uninstall import run as uninstall
    from agentbundle.config import load_state
    from agentbundle.direct_install import run_direct_install

    source = _skill_tree(tmp_path / "source", "one")
    target = tmp_path / "target"
    target.mkdir()
    assert run_direct_install(_direct_args(str(source), target), source) == 0
    capsys.readouterr()
    state_path = target / ".agentbundle-state.toml"
    row = load_state(state_path).row("alpha", "claude-code")
    assert row is not None
    owned = set(row.files)

    args = Namespace(
        pack="alpha",
        root=str(target),
        scope="repo",
        adapter=None,
        yes=True,
        dry_run=False,
    )
    assert uninstall(args) == 0
    captured = capsys.readouterr()
    assert captured.out == "uninstall: 1 removed, 0 kept\n"
    assert load_state(state_path).row("alpha", "claude-code") is None
    assert all(not (target / relpath).exists() for relpath in owned)


def test_f9_capability_helpers_have_no_production_callers_and_skills_copy_bytes(
    tmp_path: Path, capsys
) -> None:
    """Capability comparison is dormant and every skill adapter preserves bytes."""

    import agentbundle
    from agentbundle.commands.validate import _load_adapter_contract
    from agentbundle.direct_install import run_direct_install
    from agentbundle.direct_source_state import CAPABILITY_FIELDS, Capabilities

    module_root = Path(agentbundle.__file__).parent
    references: set[tuple[Path, str]] = set()
    for module in module_root.rglob("*.py"):
        if "__pycache__" in module.parts:
            continue
        tree = ast.parse(module.read_text(encoding="utf-8"), filename=str(module))
        if module.name == "direct_source_state.py":
            calls = {
                call.func.id
                for call in ast.walk(tree)
                if isinstance(call, ast.Call)
                and isinstance(call.func, ast.Name)
                and call.func.id in {"Capabilities", "compare_capabilities"}
            }
            assert calls == set()
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and node.id in {"Capabilities", "compare_capabilities"}:
                references.add((module, node.id))
            elif isinstance(node, ast.Attribute) and node.attr in {
                "Capabilities",
                "compare_capabilities",
            }:
                references.add((module, node.attr))
            elif isinstance(node, ast.alias):
                names = {node.name.rsplit(".", 1)[-1], node.asname}
                for name in names & {"Capabilities", "compare_capabilities"}:
                    references.add((module, name))
    assert references == set()
    assert len(fields(Capabilities)) == 6
    assert {state_field.name for state_field in fields(Capabilities)} == {
        "allowed_tools",
        "skill_digest",
        "skill_identities",
        "payload_digests",
        "boundaries",
        "credentialed",
    }
    assert {state_field.name for state_field in fields(Capabilities)} == set(CAPABILITY_FIELDS)

    contract = _load_adapter_contract()
    adapter_targets = {
        adapter: projection["target-path"].rstrip("/")
        for adapter, definition in contract["adapter"].items()
        for projection in definition.get("projection", [])
        if projection.get("primitive") == "skill"
        and projection.get("mode") == "direct-directory"
    }
    adapters = set(adapter_targets)
    assert len(adapters) == 8

    source = _capability_skill_tree(tmp_path / "source")
    source_bytes = (source / "skills" / "alpha" / "SKILL.md").read_bytes()
    targets = set(adapter_targets.values())
    assert len(targets) == 3
    for adapter in sorted(adapters):
        target = tmp_path / adapter
        target.mkdir()
        assert run_direct_install(_direct_args(str(source), target, adapter=adapter), source) == 0
        capsys.readouterr()
        projected = target / adapter_targets[adapter] / "alpha" / "SKILL.md"
        assert projected.read_bytes() == source_bytes
