---
title: split-image pixel-bomb guard
slug: split-image-pixel-bomb-guard
status: Shipped
source: backlog:split-image-pixel-bomb-guard
---

- **Status:** Shipped

## Objective

`split_image.py` sets `Image.MAX_IMAGE_PIXELS = None` at module load time (line 63),
disabling PIL's decompression-bomb guard for the entire process lifetime. This is the
same vulnerability class as `extraction-image-pixel-bomb-guard` (fixed in `convert.py`),
but with a wider blast radius because the assignment happens at import, before any
user-supplied path is opened. A pixel-flood image would fully decode before any
dimension ceiling can limit it.

## Acceptance Criteria

- [x] `Image.MAX_IMAGE_PIXELS` is never set to `None` in `split_image.py`.
- [x] A module-level `_MAX_IMAGE_PIXELS` constant is defined as
      `DEFAULT_MAX_SOURCE * DEFAULT_MAX_SOURCE * 8` = 512 MP. PIL raises
      `DecompressionBombError` at 2× the constant, so the hard error fires at 1024 MP —
      generous enough for Miro/FigJam exports while refusing genuine pixel-flood attacks.
- [x] `Image.MAX_IMAGE_PIXELS = _MAX_IMAGE_PIXELS` is assigned immediately after
      `_MAX_IMAGE_PIXELS` is defined, replacing the old `None` assignment.
- [x] `test_split_image.py` contains a structural test verifying `_MAX_IMAGE_PIXELS`
      equals `DEFAULT_MAX_SOURCE ** 2 * 8` and a behavioral test verifying
      `DecompressionBombError` propagates from `_validate_image` when the ceiling
      is exceeded.
- [x] Existing tests continue to pass.

## Testing Strategy

Two tests in `test_split_image.py`:

1. **`test_pixel_ceiling_is_bounded`** — structural: asserts `_MAX_IMAGE_PIXELS` is not
   None and equals the expected formula value; asserts `Image.MAX_IMAGE_PIXELS` matches
   at import time.
2. **`test_validate_image_pixel_bomb_refused`** — behavioral: monkeypatches
   `PIL.Image.MAX_IMAGE_PIXELS = 1`, calls `_validate_image` with a real 10×10 PNG;
   asserts `DecompressionBombError` propagates.
