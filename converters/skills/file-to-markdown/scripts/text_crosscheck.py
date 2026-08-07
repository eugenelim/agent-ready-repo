#!/usr/bin/env python3
"""
text_crosscheck.py — bound Tier-1 vision-read hallucination against a text layer.

A Tier-1 (agent-vision) read of a rasterized PDF can hallucinate or drop content
(survey F5 / C12). When the *same* PDF also has an extractable digital text layer
(the ``pypdf`` text the Tier-0 floor produces), that layer is an independent,
deterministic reference: if the vision read and the text layer disagree
substantially, the read is suspect and the output is flagged ``requires-review``.

The comparison is **whole-document on both sides** — the page-by-page vision reads
concatenated, versus the text layer's whole-document blob — so a per-page read is
never spuriously flagged against a document-wide layer.

Pure function, no I/O, no network, no ML. The metric is **Jaccard token-set
overlap** with a pinned threshold; below it the read is flagged. Calibrated the way
the floor pinned ``SPARSE_WORD_THRESHOLD`` — a coarse, adopter-tunable bar, not a
precision instrument.
"""
from __future__ import annotations

import re

# Below this Jaccard token-set overlap, the vision read and the text layer are
# judged to disagree substantially and the output is flagged for review. Pinned
# coarse (0.5 = "at least half the token vocabulary is shared"); a true scan has
# no text layer and never reaches this comparator.
CROSSCHECK_THRESHOLD = 0.5


def _tokens(s: str) -> set[str]:
    """Lowercased word-token set — the comparison vocabulary of a text blob."""
    return set(re.findall(r"\w+", (s or "").lower()))


def crosscheck(
    vision_text: str,
    layer_text: str,
    *,
    threshold: float = CROSSCHECK_THRESHOLD,
) -> tuple[bool, str | None]:
    """Compare a whole-document vision read against a whole-document text layer.

    Returns ``(requires_review, discrepancy_note)``. When the text layer is empty
    (a true scan with no digital text), the comparator is a **no-op** — it returns
    ``(False, None)`` and the read stands on its own confidence signal.
    """
    layer_tokens = _tokens(layer_text)
    if not layer_tokens:
        return False, None
    vision_tokens = _tokens(vision_text)
    union = vision_tokens | layer_tokens
    jaccard = (len(vision_tokens & layer_tokens) / len(union)) if union else 1.0
    if jaccard < threshold:
        return True, (
            f"Text-layer cross-check: the agent-vision read overlaps the PDF's "
            f"digital text layer by only {jaccard:.0%} (below the {threshold:.0%} "
            f"threshold). The read may have hallucinated or missed content — "
            f"review against the source before trusting this extraction."
        )
    return False, None
