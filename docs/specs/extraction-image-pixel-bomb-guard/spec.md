---
title: extraction image pixel-bomb guard
slug: extraction-image-pixel-bomb-guard
status: Shipped
source: backlog:extraction-image-pixel-bomb-guard
---

- **Status:** Shipped

## Objective

`_prescale_image` in `file-to-markdown/scripts/convert.py` sets
`Image.MAX_IMAGE_PIXELS = None` unconditionally, disabling PIL's decompression-bomb
guard before `Image.open()`. A pixel-flood image is fully decoded before the
`MAX_IMAGE_DIM` downscale ceiling can limit it. This fix enforces a hard pixel
ceiling so the guard fires before any decode begins.

## Acceptance Criteria

- [x] `Image.MAX_IMAGE_PIXELS` is never set to `None` in `_prescale_image`.
- [x] A module-level `_MAX_IMAGE_PIXELS` constant defines the ceiling
      (`MAX_IMAGE_DIM * MAX_IMAGE_DIM * 8` = 128 MP). PIL raises `DecompressionBombError`
      at 2× the constant, so the hard error fires at 256 MP.
- [x] `_prescale_image` sets `Image.MAX_IMAGE_PIXELS = _MAX_IMAGE_PIXELS` before
      `Image.open()`, so PIL's bomb check fires for over-ceiling images.
- [x] `test_convert.py` contains a test that verifies `DecompressionBombError`
      propagates from `_prescale_image` when the ceiling is exceeded.
- [x] Existing tests continue to pass.

## Testing Strategy

TDD — add `test_prescale_image_respects_pixel_ceiling` in `test_convert.py`.
Monkeypatches `_MAX_IMAGE_PIXELS` to 1, then calls `_prescale_image` with a real
10×10 PNG; expects `DecompressionBombError` to propagate.
