"""Direct state 0.5, provenance ordering, and the content-only digest."""

from __future__ import annotations

from pathlib import Path

import pytest
from agentbundle import config, statelock
from agentbundle.direct_source import admit_direct_source
from agentbundle.direct_source_state import (
    DIGEST_PREFIX,
    DirectStateError,
    build_provenance,
    comparable_digest,
    digest_preimage_entries,
    direct_content_digest,
    direct_source_digest,
    relative_repo_source,
)

# Derived independently from RFC-0098 E2's wording, with a separate
# implementation that never imports the module under test. If these move, the
# stored digest of every installed direct skill has changed meaning.
E2_VECTORS = {
    "empty": "sha256-1:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "single": "sha256-1:81415a00be1c6cf4a7b708c2683eb529e08662e6b5beb01f983f3ade05831cd4",
    "ambiguity_a": "sha256-1:601d5476e2ccfe2c87a2bba7a322659734a05749d5b5aa781f513e4912db0d5f",
    "ambiguity_b": "sha256-1:3fafa1cf2f19a7c1129beb20cf0983f73a489a221fc0dd2f16d1be292d089205",
    "two_entries": "sha256-1:f1760790e1826e35b898b16647ac3f1faa4b0ced229e23558e377044d391dfe4",
    "shared_leaf": "sha256-1:09e3231a628af9bc30773b7d152626ddd66b1768806d03316be51372c8fb58a0",
}


def _write_skill(path: Path, name: str) -> None:
    path.mkdir(parents=True, exist_ok=True)
    (path / "SKILL.md").write_text(f"---\nname: {name}\n---\n# {name}\n")


def test_digest_matches_independently_derived_vectors():
    # AC13 — the preimage is RFC-0098 E2's, byte for byte.
    assert direct_content_digest([]) == E2_VECTORS["empty"]
    assert direct_content_digest([("SKILL.md", b"hello\n")]) == E2_VECTORS["single"]
    assert direct_content_digest(
        [("skills/a/SKILL.md", b"A"), ("skills/b/SKILL.md", b"B")]
    ) == E2_VECTORS["two_entries"]

    # Order of presentation cannot change the digest: entries sort by encoded
    # path bytes, not by argument order or locale collation.
    assert direct_content_digest(
        [("skills/b/SKILL.md", b"B"), ("skills/a/SKILL.md", b"A")]
    ) == E2_VECTORS["two_entries"]


def test_length_prefixes_remove_the_concatenation_ambiguity():
    # AC13 — without the u64be prefixes, ("ab", b"c") and ("a", b"bc") feed
    # SHA-256 the identical byte stream and two different trees share a digest.
    a = direct_content_digest([("ab", b"c")])
    b = direct_content_digest([("a", b"bc")])
    assert a == E2_VECTORS["ambiguity_a"]
    assert b == E2_VECTORS["ambiguity_b"]
    assert a != b, "the length prefixes are what separate these"


def test_a_shared_leaf_name_cannot_collapse_two_envelopes():
    # AC13 — a categorised envelope contributes its full relative path from the
    # source root, never the leaf-normalized identity. Two categories may hold
    # the same leaf name, and digesting the leaf would fold them into one.
    full = direct_content_digest(
        [("skills/x/dup/SKILL.md", b"1"), ("skills/y/dup/SKILL.md", b"2")]
    )
    assert full == E2_VECTORS["shared_leaf"]
    leaf_normalized = direct_content_digest([("dup/SKILL.md", b"1")])
    assert full != leaf_normalized


def test_digest_refuses_non_nfc_and_duplicate_paths():
    # AC13 — a non-NFC path is refused rather than normalized, because
    # normalizing changes what the digest attests to.
    with pytest.raises(DirectStateError):
        direct_content_digest([("café/SKILL.md", b"x")])
    direct_content_digest([("café/SKILL.md", b"x")])  # NFC form is fine
    with pytest.raises(DirectStateError):
        direct_content_digest([("a", b"1"), ("a", b"2")])


def test_digest_is_stable_across_mtime_and_mode(tmp_path: Path):
    # AC13, E2 — mode availability differs by platform, so including it would
    # manufacture updates for a tree whose content never changed.
    source = tmp_path / "stable"
    _write_skill(source, "stable")
    (source / "scripts").mkdir()
    script = source / "scripts" / "run.sh"
    script.write_text("#!/bin/sh\n")

    first = direct_source_digest(admit_direct_source(source))
    import os
    import time

    script.chmod(0o755)
    os.utime(script, (0, 0))
    time.sleep(0.01)
    second = direct_source_digest(admit_direct_source(source))
    assert first == second, "mode and mtime must not participate"

    script.write_text("#!/bin/sh\necho changed\n")
    assert direct_source_digest(admit_direct_source(source)) != first


def test_preimage_paths_are_relative_to_the_source_root(tmp_path: Path):
    # AC13 — full relative paths from the source root, POSIX-spelled.
    source = tmp_path / "collection"
    _write_skill(source / "skills" / "category" / "alpha", "alpha")
    entries = dict(digest_preimage_entries(admit_direct_source(source)))
    assert set(entries) == {"skills/category/alpha/SKILL.md"}


def test_digest_version_prefix_refuses():
    # AC13 — lifecycle comparison refuses another prefix and directs the reader
    # to reinstall, rather than recomputing (which would re-baseline silently).
    good = E2_VECTORS["single"]
    assert comparable_digest(good) == good
    for foreign in ("sha256-2:" + "a" * 64, "blake3-1:" + "a" * 64, "a" * 64):
        with pytest.raises(DirectStateError) as raised:
            comparable_digest(foreign)
        assert "Reinstall" in str(raised.value) or "malformed" in str(raised.value)
    for malformed in (DIGEST_PREFIX + "a" * 63, DIGEST_PREFIX + "A" * 64):
        with pytest.raises(DirectStateError):
            comparable_digest(malformed)


def test_provenance_shape_by_source_kind():
    # AC12 — a direct pack has no source-path; a manifestless row requires a
    # validated relative POSIX one that is never empty.
    digest = E2_VECTORS["single"]
    pack = build_provenance(
        source="git+https://github.com/o/r@v1",
        source_revision="0" * 40,
        source_kind="pack",
        source_path=None,
        source_digest=digest,
    )
    assert pack.source_path is None

    skill = build_provenance(
        source="git+https://github.com/o/r@v1",
        source_revision="0" * 40,
        source_kind="skill",
        source_path="skills/alpha",
        source_digest=digest,
    )
    assert skill.source_path == "skills/alpha"

    for kind, path in [
        ("pack", "skills/alpha"),   # a pack may not carry one
        ("skill", None),            # a manifestless row must
        ("skill", ""),              # never empty
        ("skill", "/absolute"),
        ("skill", "../escape"),
        ("skill", "windows\\sep"),
        ("catalogue", None),        # unknown kind
    ]:
        with pytest.raises(DirectStateError):
            build_provenance(
                source="git+https://github.com/o/r@v1",
                source_revision=None,
                source_kind=kind,
                source_path=path,
                source_digest=digest,
            )

    with pytest.raises(DirectStateError):
        build_provenance(
            source="",
            source_revision=None,
            source_kind="skill",
            source_path="skills/a",
            source_digest=digest,
        )


def test_repo_scope_sources_are_stored_relatively(tmp_path: Path):
    # AC12 — an absolute path in repository state breaks for every other clone.
    repo = tmp_path / "repo"
    (repo / "vendor" / "skills").mkdir(parents=True)
    assert relative_repo_source(repo / "vendor" / "skills", repo) == "vendor/skills"
    with pytest.raises(DirectStateError):
        relative_repo_source(tmp_path / "elsewhere", repo)


def test_state_reads_both_versions_and_never_downgrades(tmp_path: Path):
    # AC12, E3 — readers accept 0.4 and 0.5; a write raises to 0.5 only when a
    # direct row is present, and an existing 0.5 file is never downgraded.
    assert {"0.4", "0.5"} == config.SUPPORTED_STATE_SCHEMA_VERSIONS

    for version in ("0.4", "0.5"):
        path = tmp_path / f"state-{version}.toml"
        path.write_text(f'schema-version = "{version}"\n')
        assert config.load_state(path).schema_version == version

    unknown = tmp_path / "state-future.toml"
    unknown.write_text('schema-version = "0.6"\n')
    with pytest.raises(config.StateFileLegacy):
        config.load_state(unknown)

    # A catalogue-only mutation leaves a 0.4 file at 0.4.
    catalogue_only = config.State(schema_version="0.4")
    assert statelock.direct_state_floor("0.4", catalogue_only) == "0.4"

    # Adding a direct row raises the floor.
    with_direct = config.State(schema_version="0.4")
    with_direct.packs[("alpha", "claude-code")] = config.PackState(
        installed_version="0.0.0",
        source="git+https://github.com/o/r@v1",
        scope="repo",
        adapter="claude-code",
        source_kind="skill",
        source_path="skills/alpha",
        source_digest=E2_VECTORS["single"],
    )
    assert statelock.direct_state_floor("0.4", with_direct) == "0.5"
    # And an existing 0.5 file stays 0.5 even for a catalogue-only mutation:
    # the direct provenance an earlier install wrote does not stop existing.
    assert statelock.direct_state_floor("0.5", catalogue_only) == "0.5"


def test_direct_row_serializes_in_the_pinned_order(tmp_path: Path):
    # AC12 pins the order after `source-revision`: source-kind, source-path
    # when present, source-digest, then install-route.
    state = config.State(schema_version="0.5")
    state.packs[("alpha", "claude-code")] = config.PackState(
        installed_version="0.0.0",
        source="git+https://github.com/o/r@v1",
        scope="repo",
        adapter="claude-code",
        source_revision="0" * 40,
        source_kind="skill",
        source_path="skills/alpha",
        source_digest=E2_VECTORS["single"],
    )
    dumped = config.dump_state(state)
    keys = [
        line.split(" = ")[0]
        for line in dumped.splitlines()
        if " = " in line and not line.startswith("schema-version")
    ]
    ordered = [
        key
        for key in keys
        if key in {"source-revision", "source-kind", "source-path", "source-digest", "install-route"}
    ]
    assert ordered == [
        "source-revision", "source-kind", "source-path", "source-digest", "install-route"
    ], ordered

    # The row round-trips through the parser unchanged.
    path = tmp_path / "state.toml"
    path.write_text(dumped)
    row = config.load_state(path).row("alpha", "claude-code")
    assert row is not None
    assert row.source_kind == "skill"
    assert row.source_path == "skills/alpha"
    assert row.source_digest == E2_VECTORS["single"]


def test_interrupted_install_leaves_unowned_projection(tmp_path: Path, capsys):
    # AC28 — a hard interruption after projection and before the direct-row
    # state write leaves projection files with no owning row. That is the
    # accepted post-condition, not a bug to repair: the criterion forbids any
    # transaction, staging, rollback, or reconcile extension.
    #
    # This drives the REAL install with the state write made to fail. The
    # previous version hand-built the post-condition it claimed to observe —
    # `projection.mkdir()` then asserting the projection existed, and asserting
    # no row after writing no state — so every assertion mirrored its own setup
    # and it stayed green no matter what order `run_direct_install` used.
    import agentbundle.direct_install as direct_install
    from agentbundle.direct_source_state import DirectStateError

    source = tmp_path / "alpha"
    source.mkdir()
    (source / "SKILL.md").write_text("---\nname: alpha\n---\n# alpha\n")
    target = tmp_path / "target"
    target.mkdir()

    def _die(**_kwargs):
        raise DirectStateError("state write interrupted")

    class _Args:
        catalogue = str(source)
        output = str(target)
        pack = profile = scope = adapter = skill = None
        all_skills = dry_run = force = False
        yes = True

    original = direct_install._record_direct_rows
    direct_install._record_direct_rows = _die
    try:
        exit_code = direct_install.run_direct_install(_Args(), source)
    finally:
        direct_install._record_direct_rows = original
    capsys.readouterr()

    assert exit_code == 1, "an interrupted state write must not report success"

    # The post-condition AC28 accepts: the projection is on disk and owns
    # nothing. If the row were written BEFORE projecting — the ordering AC28
    # and `run_direct_install`'s docstring forbid — the row would exist here.
    projected = target / ".claude" / "skills" / "alpha" / "SKILL.md"
    assert projected.exists(), "the projection landed before the state write"
    state = config.load_state(target / ".agentbundle-state.toml")
    assert state.row("alpha", "claude-code") is None, (
        "the state row must not exist; the write is what failed"
    )


def test_golden_state_file_pins_row_key_order(tmp_path: Path):
    # AC12 — a committed golden asserts the whole row shape, not only the
    # direct keys. Key order is part of the contract because a reader diffing
    # two state files across versions should see content changes, not
    # reshuffled keys.
    golden = (
        Path(__file__).resolve().parents[1]
        / "fixtures"
        / "direct"
        / "golden_state_0_5.toml"
    )
    expected = golden.read_text(encoding="utf-8")

    state = config.State(schema_version="0.5")
    state.packs[("alpha", "claude-code")] = config.PackState(
        installed_version="0.0.0",
        source="git+https://github.com/example/skills@v1.2.3",
        scope="repo",
        adapter="claude-code",
        source_revision="0" * 40,
        source_kind="skill",
        source_path="skills/alpha",
        source_digest="sha256-1:" + "ab" * 32,
        files={".claude/skills/alpha/SKILL.md": {"sha": "cd" * 32}},
    )
    state.packs[("bravo", "claude-code")] = config.PackState(
        installed_version="2.1.0",
        source="git+https://github.com/example/pack@v2.1.0",
        scope="repo",
        adapter="claude-code",
        source_revision="1" * 40,
        source_kind="pack",
        source_path=None,
        source_digest="sha256-1:" + "ef" * 32,
    )
    assert config.dump_state(state) == expected

    # The golden is also a read fixture: this build must load what it writes,
    # and a direct pack must round-trip with no `source-path` at all.
    path = tmp_path / "golden.toml"
    path.write_text(expected, encoding="utf-8")
    loaded = config.load_state(path)
    assert loaded.schema_version == "0.5"
    manifestless = loaded.row("alpha", "claude-code")
    direct_pack = loaded.row("bravo", "claude-code")
    assert manifestless is not None and direct_pack is not None
    assert manifestless.source_kind == "skill"
    assert manifestless.source_path == "skills/alpha"
    assert direct_pack.source_kind == "pack"
    assert direct_pack.source_path is None
    assert "source-path" not in expected.split("[pack.bravo")[1]
