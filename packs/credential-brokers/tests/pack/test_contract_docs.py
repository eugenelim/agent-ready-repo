"""Pack-owned credential-brokers guide assertion pending relocation."""

from __future__ import annotations

import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]  # pack tests -> repository root


def test_ac43_guide_walks_broker_first():
    """The guide makes broker choice the first step."""
    guide = (
        REPO_ROOT
        / "guides"
        / "credential-brokers"
        / "how-to"
        / "add-a-credentialed-skill.md"
    ).read_text(encoding="utf-8")
    pick_broker_idx = guide.find("## Step 1 — Pick a broker")
    assert pick_broker_idx > 0, "guide does not start with 'Pick a broker'"
    pick_class_idx = guide.find("Pick a primitive class")
    assert pick_class_idx > pick_broker_idx
    for broker in ("`env`", "`cli`", "`creds`", "`sso-cookie`"):
        assert broker in guide
