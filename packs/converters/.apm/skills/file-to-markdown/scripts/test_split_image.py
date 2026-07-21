"""Tests for split_image.py — pixel-bomb guard and module-level ceiling.

Run with `python -m pytest` from this directory.
"""
from __future__ import annotations

from pathlib import Path

import pytest

import split_image


def test_pixel_ceiling_is_bounded():
    """_MAX_IMAGE_PIXELS must be set to a finite value at import time."""
    from PIL import Image

    assert split_image._MAX_IMAGE_PIXELS is not None
    assert split_image._MAX_IMAGE_PIXELS == split_image.DEFAULT_MAX_SOURCE ** 2 * 8
    assert Image.MAX_IMAGE_PIXELS == split_image._MAX_IMAGE_PIXELS


def test_validate_image_pixel_bomb_refused(tmp_path, monkeypatch):
    """_validate_image must propagate DecompressionBombError for over-ceiling images.

    Setting PIL's ceiling to 1 turns a 10×10 PNG (100 pixels) into a
    "bomb", exercising the guard without needing a genuinely huge file.
    """
    PIL_Image = pytest.importorskip("PIL.Image")
    DecompressionBombError = getattr(PIL_Image, "DecompressionBombError", None)
    if DecompressionBombError is None:
        pytest.skip("DecompressionBombError not present in this Pillow version")

    img = PIL_Image.new("RGB", (10, 10))
    img_path = tmp_path / "tiny.png"
    img.save(str(img_path))
    img.close()

    # Register current ceiling for teardown so this test's side-effect on
    # PIL.Image.MAX_IMAGE_PIXELS is undone after the test.
    monkeypatch.setattr(PIL_Image, "MAX_IMAGE_PIXELS", PIL_Image.MAX_IMAGE_PIXELS)
    PIL_Image.MAX_IMAGE_PIXELS = 1
    with pytest.raises(DecompressionBombError):
        split_image._validate_image(img_path)
