"""T1 skeleton check: the package installs and imports.

Goal-based (spec task T1): proves `pip install -e ./packages/credbroker`
produced an importable `credbroker` with a version. The public-API and
resolution tests arrive with the core lift (T2).
"""

from __future__ import annotations


def test_credbroker_imports() -> None:
    import credbroker

    assert credbroker.__version__


def test_base_all_is_present() -> None:
    import credbroker

    # T2 populated the public surface; the detailed contract lives in
    # test_public_surface.py — here we just smoke that __all__ is a non-empty list.
    assert isinstance(credbroker.__all__, list)
    assert credbroker.__all__
