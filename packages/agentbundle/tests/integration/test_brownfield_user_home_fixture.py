"""Quality-engineer Blocker 3 pin: the `brownfield-adapt-user-home`
fixture is consumed by automation so regressions to its shape trip
pytest (not just code review).

The fixture plumbs the synthetic user-scope dot-directory used by
AC4a's user-scope plumbing rows in the manual QA matrix. Before this
test, the fixture was declared but never loaded — a regression
(deletion, malformed TOML, missing `[markers]`-refusal property)
would have shipped silently.
"""

from __future__ import annotations

from pathlib import Path

from agentbundle.config import load_adapt_discovery_typed, load_state


FIXTURE = (
    Path(__file__).parent.parent
    / "fixtures"
    / "brownfield-adapt-user-home"
    / ".agent-ready"
)


def test_user_home_state_file_parses_at_v0_2():
    """The fixture's `state.toml` parses cleanly as v0.2."""
    state = load_state(FIXTURE / "state.toml")
    assert state.schema_version == "0.2"


def test_user_home_discovery_file_parses_at_user_scope():
    """The fixture's `.adapt-discovery.toml` parses with `scope="user"`
    (the loader refuses `[markers]` at user scope per RFC-0004)."""
    d = load_adapt_discovery_typed(
        FIXTURE / ".adapt-discovery.toml", scope="user"
    )
    assert d.schema_version == "0.1"
    assert d.markers == {}, "user-scope file must carry no markers"
    # The seeded `[[findings.declined]]` round-trips.
    assert len(d.findings_declined) == 1
    f = d.findings_declined[0]
    assert f.kind == "restructure"
    assert f.accepted is False
