"""Unit tests for small helpers introduced by the round-2 robustness pass.

Covers:

- ``_is_credentialed_true`` — YAML-truthy normalisation for the
  ``credentialed:`` frontmatter scalar (Security Nit #9).
"""

from __future__ import annotations

import pytest

from agentbundle.commands.creds import _is_credentialed_true


@pytest.mark.parametrize(
    "raw",
    [
        "true",
        "True",
        "TRUE",
        '"true"',  # quotes are stripped by _parse_frontmatter, value reaches here as bare
        "yes",
        "Yes",
        "YES",
        "1",
        "on",
        "ON",
    ],
)
def test_is_credentialed_true_accepts_yaml_truthy_forms(raw):
    """Per Security Nit #9, an author writing ``credentialed: True``
    (Python-style) or ``credentialed: yes`` (YAML 1.1) MUST be picked
    up by the ``creds setup`` walker — silent skipping of valid skills
    is confusing and could mask a credentialed-primitive entirely.
    The frontmatter parser strips balanced quotes, so quoted forms
    arrive here as bare strings; the trimmed/lowered comparison handles
    the rest."""
    # Strip the YAML-style outer quotes the same way _parse_frontmatter
    # does, then pass to the helper.
    if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in ('"', "'"):
        raw = raw[1:-1]
    assert _is_credentialed_true(raw) is True


@pytest.mark.parametrize(
    "raw",
    [
        None,
        "",
        "false",
        "False",
        "no",
        "0",
        "off",
        "credentialed",  # the key name, not a value
        "maybe",
    ],
)
def test_is_credentialed_true_rejects_non_truthy(raw):
    """Unset, falsey, and unrecognised values all fall through to False
    so a typo doesn't silently get treated as truthy."""
    assert _is_credentialed_true(raw) is False
