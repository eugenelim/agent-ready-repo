"""Tests for text_crosscheck.py — the Tier-1 hallucination guard (AC6).

Pure comparator; run with `python -m pytest` from this directory.
"""
from __future__ import annotations

import text_crosscheck as tc


def test_agreement_above_threshold_does_not_flag():
    vision = "the quick brown fox jumps over the lazy dog"
    layer = "the quick brown fox jumps over the lazy dog"
    review, note = tc.crosscheck(vision, layer)
    assert review is False and note is None


def test_disagreement_below_threshold_flags_with_note():
    vision = "the quick brown fox jumps over the lazy dog"
    layer = "completely different unrelated content nothing shared at all"
    review, note = tc.crosscheck(vision, layer)
    assert review is True
    assert note and "cross-check" in note.lower()


def test_empty_text_layer_is_a_noop():
    """A true scan has no digital text layer — the comparator must not flag."""
    review, note = tc.crosscheck("anything the vision read produced", "")
    assert review is False and note is None


def test_whole_document_concatenation_not_spuriously_flagged():
    """AC6 granularity: a page-by-page vision read, concatenated whole-document,
    is compared against the whole-document layer — high overlap, no false flag."""
    pages = ["page one alpha beta", "page two gamma delta", "page three epsilon"]
    vision = "\n".join(pages)                       # concatenated, as the caller does
    layer = "alpha beta gamma delta epsilon page one page two page three"
    review, _ = tc.crosscheck(vision, layer)
    assert review is False


def test_threshold_is_tunable():
    vision = "alpha beta"
    layer = "alpha gamma"          # Jaccard = 1/3
    assert tc.crosscheck(vision, layer, threshold=0.5)[0] is True
    assert tc.crosscheck(vision, layer, threshold=0.2)[0] is False
