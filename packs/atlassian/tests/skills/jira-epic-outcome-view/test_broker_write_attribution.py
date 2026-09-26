"""Every write under the broker's own root is the broker's.

The credential broker's root sits outside the two roots a run leaves
byte-identical, and it has to: the broker resolves a sign-on session into an
on-disk cookie jar there, so an authenticated read can legitimately change
it. Holding the view to byte-identity there would fail on a path the view
neither owns nor controls.

Excluding a root and stopping there would let the view write anything it
liked under it. So the view is held to the narrower statement it can
actually honour -- it issues no write there itself -- and that is asserted
by attribution: the broker seam records the paths it writes, the root is
compared across the run, and any changed path the seam did not record has
no attribution and fails.
"""

from __future__ import annotations

import atlassian_jira_epic_outcome_view_guarantees as guarantees
import pytest


@pytest.fixture
def home(tmp_path):
    """A throwaway home directory, so no real broker state is touched."""
    home_dir = tmp_path / "home"
    home_dir.mkdir()
    return home_dir


@pytest.fixture
def broker_root(home):
    """The broker's root, seeded as an established install would leave it."""
    root = home / ".agentbundle"
    (root / "bin").mkdir(parents=True)
    (root / "bin" / "sso-broker.py").write_text("# the broker, already installed\n", "utf-8")
    (root / "credentials.env").write_text("JIRA_BASE_URL=https://example.invalid\n", "utf-8")
    return root


@pytest.fixture
def transport(tmp_path):
    return guarantees.build_recording_transport(tmp_path)


def _run(monkeypatch, load_module, transport, tmp_path, home, broker_root, capsys):
    cli = load_module("")
    env = guarantees.view_environment(transport, broker_root=broker_root)
    env["HOME"] = str(home)
    guarantees.apply_environment(monkeypatch, env)
    working_dir = tmp_path / "team-working-directory"
    working_dir.mkdir()
    monkeypatch.chdir(working_dir)

    before = guarantees.hash_tree(broker_root)
    exit_code = cli.main(list(guarantees.VIEW_ARGV))
    stdout = capsys.readouterr().out
    assert exit_code == 0, f"the view did not complete: {stdout}"
    guarantees.assert_answer_is_correct_and_non_empty(
        guarantees.parse_stdout_document(stdout)
    )
    after = guarantees.hash_tree(broker_root)
    return before, after


def _changed_paths(broker_root, before, after):
    names = set(before) | set(after)
    return {
        str((broker_root / name).resolve())
        for name in names
        if before.get(name) != after.get(name)
    }


def test_the_broker_seam_really_writes_under_its_own_root(
    monkeypatch, load_module, transport, tmp_path, home, broker_root, capsys
):
    """Liveness first. Attribution over a root nothing wrote to is vacuous:
    it would pass against a run that never authenticated at all, and against
    a view that had been changed to write there."""
    before, after = _run(
        monkeypatch, load_module, transport, tmp_path, home, broker_root, capsys
    )

    assert transport.broker_writes(), "the broker seam was never reached"
    assert _changed_paths(broker_root, before, after), (
        "nothing under the broker root changed, so this run cannot tell an "
        "attributed write from an absent one"
    )


def test_every_write_under_the_broker_root_is_attributed_to_the_broker(
    monkeypatch, load_module, transport, tmp_path, home, broker_root, capsys
):
    """The guarantee itself: a changed path the broker seam did not record
    is a write the view made, and there is no such thing."""
    before, after = _run(
        monkeypatch, load_module, transport, tmp_path, home, broker_root, capsys
    )

    unattributed = _changed_paths(broker_root, before, after) - transport.broker_writes()

    assert not unattributed, (
        "these paths under the broker root changed with no broker attribution, "
        f"so the view wrote them itself: {sorted(unattributed)}"
    )
