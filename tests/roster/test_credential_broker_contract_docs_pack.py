"""Repository roster assertion spanning a pack and its published guide."""

from __future__ import annotations

import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


def test_ac43_guide_walks_broker_first():
    """The full walkthrough makes broker choice the first step.

    The short how-to leads with the promise; the step-by-step walkthrough moved
    to the reference page (spec/docs-job-pages), so the ordering is checked there.
    """
    guide = (
        REPO_ROOT
        / "guides"
        / "credential-brokers"
        / "reference"
        / "credentialed-skill-walkthrough.md"
    ).read_text(encoding="utf-8")
    pick_broker_idx = guide.find("## Pick a broker")
    assert pick_broker_idx > 0, "guide does not start with 'Pick a broker'"
    pick_class_idx = guide.find("Pick a primitive class")
    assert pick_class_idx > pick_broker_idx
    for broker in ("`env`", "`cli`", "`creds`", "`sso-cookie`"):
        assert broker in guide
