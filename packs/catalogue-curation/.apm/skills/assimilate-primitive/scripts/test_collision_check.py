"""Tests for collision_check.py (activation-collision screen)."""

from __future__ import annotations

import collision_check as c


def test_near_duplicate_flags() -> None:
    existing = {
        "summarize-thread": "Use to summarize a long email thread into a short digest of decisions and action items.",
        "export-catalogue": "Use to produce a redistributable derivative of the catalogue at a target path.",
    }
    new = "Use to summarize a long email thread into a brief digest of the decisions and action items."
    hits = c.collisions(new, existing, threshold=0.5)
    assert hits and hits[0][0] == "summarize-thread"


def test_distinct_description_no_collision() -> None:
    existing = {
        "summarize-thread": "Use to summarize a long email thread into a short digest of decisions.",
    }
    new = "Use to render a Mermaid deployment diagram from a Terraform plan file."
    assert c.collisions(new, existing, threshold=0.5) == []


def test_similarity_bounds() -> None:
    assert c.similarity("alpha beta gamma", "alpha beta gamma") == 1.0
    assert c.similarity("alpha beta", "gamma delta") == 0.0


def test_empty_existing() -> None:
    assert c.collisions("anything here", {}) == []
