# State token contrast checks

Verified 2026-07-28 against WCAG 2.2 SC 1.4.3 (AA, 4.5:1 for normal text).
Background: `--prim-neutral-50` (#fafaf9), relative luminance ≈ 0.956.

| Role    | fg token              | fg hex  | L(fg)  | Contrast | WCAG AA |
|---------|-----------------------|---------|--------|----------|---------|
| success | `--prim-green-700`    | #15803d | 0.1617 | 4.75:1   | ✓       |
| danger  | `--prim-red-700`      | #b91c1c | 0.1250 | 5.75:1   | ✓       |
| warn    | `--prim-orange-700`   | #c2410c | 0.1710 | 4.55:1   | ✓       |
| info    | `--prim-blue-700`     | #1d4ed8 | 0.1230 | 5.82:1   | ✓       |
| neutral | `--prim-neutral-800`  | #2e2c28 | 0.0270 | 14.20:1  | ✓       |

**Formula used:** WCAG 2.1 relative luminance + contrast ratio.
Contrast = (L_lighter + 0.05) / (L_darker + 0.05).

**bg/border pairs** are decorative surfaces only — the fg token carries the
accessible contrast; bg is never used as the sole color signal.
