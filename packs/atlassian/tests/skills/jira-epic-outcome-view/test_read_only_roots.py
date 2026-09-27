"""Two named roots come out of a run byte-identical.

The roots are the invocation working directory tree and the installed pack
tree. Naming them is what makes the comparison runnable: "the filesystem"
names no comparison, and "creates no new file" would pass a run that
rewrote a cache entry or unlinked a stale temporary.

The working directory is seeded with a populated flow cache including a
`*.tmp` older than an hour before the run, because an empty directory
cannot discriminate. The flow skill's plain bypass flag unlinks exactly
that file, from a directory relative to wherever it was run, before the
flag's own branch is reached -- so this seed is what separates a view
composed through the inert mode from one composed through the bypass.
"""

from __future__ import annotations

import atlassian_jira_epic_outcome_view_guarantees as guarantees
import pytest


@pytest.fixture
def transport(tmp_path):
    return guarantees.build_recording_transport(tmp_path)


@pytest.fixture
def working_dir(tmp_path):
    """A non-repository working directory, cache pre-populated."""
    cwd = tmp_path / "team-working-directory"
    cwd.mkdir()
    guarantees.seed_flow_cache(cwd)
    return cwd


def _run(monkeypatch, load_module, transport, working_dir, capsys):
    cli = load_module("")
    guarantees.apply_environment(monkeypatch, guarantees.view_environment(transport))
    monkeypatch.chdir(working_dir)
    with guarantees.recording_spawns(monkeypatch) as spawns:
        exit_code = cli.main(list(guarantees.VIEW_ARGV))
    stdout = capsys.readouterr().out
    assert exit_code == 0, f"the view did not complete: {stdout}"
    document = guarantees.parse_stdout_document(stdout)
    guarantees.assert_answer_is_correct_and_non_empty(document)
    return document, spawns


def test_the_working_directory_tree_is_byte_identical_across_a_run(
    monkeypatch, load_module, transport, working_dir, capsys
):
    """Including the seeded cache: an unlinked stale temporary is a write."""
    before = guarantees.hash_tree(working_dir)
    assert any(name.endswith(".tmp") for name in before), "the stale temporary was not seeded"

    _run(monkeypatch, load_module, transport, working_dir, capsys)

    after = guarantees.hash_tree(working_dir)
    assert after == before, (
        "the working directory tree changed across the run; differing paths: "
        f"{sorted(set(before) ^ set(after)) or [k for k in before if before[k] != after.get(k)]}"
    )


def test_the_installed_pack_tree_is_byte_identical_across_a_run(
    monkeypatch, load_module, transport, working_dir, capsys, pack_root
):
    """The second named root. The run imports and executes the pack's own
    shipped code, which is the path that would otherwise leave bytecode
    caches behind inside the tree the view promises not to change.

    The package is imported before the fingerprint is taken, so the
    comparison is about what the run does and not about which test
    happened to import first. Taking it afterwards makes this pass on a
    warm tree and fail on a cold one for the same code, and the run's own
    writes are then invisible either way. The compilation this harness
    itself causes is asserted separately, against the documented command,
    in `test_documented_invocation_writes_no_bytecode.py`.
    """
    load_module("")
    before = guarantees.hash_tree(pack_root)

    _run(monkeypatch, load_module, transport, working_dir, capsys)

    after = guarantees.hash_tree(pack_root)
    changed = sorted(
        set(before) ^ set(after)
    ) or sorted(k for k in before if before[k] != after.get(k))
    assert after == before, f"the installed pack tree changed across the run: {changed}"


def test_the_seeded_stale_temporary_survives_the_run(
    monkeypatch, load_module, transport, working_dir, capsys
):
    """Named on its own because it is the one mutation the bypass flag does
    not suppress. A hash comparison that happened to be seeded without it
    would be green against a view composed the wrong way."""
    stale = working_dir / guarantees.CACHE_RELATIVE_DIR / "9f86d081.jsonl.4242.tmp"
    assert stale.exists()

    _run(monkeypatch, load_module, transport, working_dir, capsys)

    assert stale.exists(), (
        "the stale temporary was unlinked, so the flow skill was reached through "
        "the bypass flag rather than the inert cache mode"
    )


def test_the_flow_skill_is_composed_only_through_the_inert_cache_mode(
    monkeypatch, load_module, transport, working_dir, capsys
):
    """Observed on the real spawn the run made, not on the argv builder.

    The builder is asserted elsewhere; this is the whole-run statement, so a
    second call site added later that reached the flow skill another way
    would be caught here even though the builder stayed correct.
    """
    _, spawns = _run(monkeypatch, load_module, transport, working_dir, capsys)

    flow_spawns = [spawn for spawn in spawns.spawns if "flow_metrics" in spawn.argv]
    assert flow_spawns, "the run never reached the flow skill, so it composed nothing"
    for spawn in flow_spawns:
        assert "--inert-cache" in spawn.argv
        assert "--no-cache" not in spawn.argv
    assert len(flow_spawns) == 1, "the flow reading is one run, not one per Epic"
