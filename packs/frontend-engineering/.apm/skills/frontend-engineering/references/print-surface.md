# Print and slide surfaces

Load this whenever the output targets a PPT slide or a PDF export, **whatever
rung supplied the token values**. This is medium-specific CSS, not a fallback:
a surface that inherited its tokens from a taxonomy or from the repository's
existing system still needs the page box, the colour-adjust rule and the
page-break behaviour, and the visual QA checklist still asks whether print
output is correct.

Use `pt` for typographic values here.

When the output targets a PPT slide or PDF export, add this block and use
`pt` for typographic values:

```css
@page {
  size: 960px 540px; /* 16:9 slide — standard widescreen */
  margin: 0;
}

* {
  -webkit-print-color-adjust: exact;
  print-color-adjust: exact; /* preserve background fills */
}

@media print {
  :root {
    --ds-color-surface:    #ffffff;
    --ds-color-on-surface: #000000;
    --ds-shadow-sm: none;
    --ds-shadow-md: none;
    --ds-shadow-lg: none;
  }

  .slide            { page-break-after: always; }
  h2, h3, figure,
  table, blockquote { page-break-inside: avoid; }
}
```

**Print safety:** `box-shadow` and `text-shadow` are unreliable across
renderers (Chrome/WeasyPrint differ) — use `--ds-shadow-*: none` in the
print override and rely on borders for separation instead. Avoid Tailwind
responsive variants (`sm:`, `md:`) for fixed-dimension artifacts.
