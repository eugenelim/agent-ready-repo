# Spec: Self-host Inter and JetBrains Mono

Mode: light (user-directed; note — the "new dependency" risk trigger would
normally route to full mode, but the change is a boring, well-understood
self-hosting swap and the user explicitly chose light mode)

Status: Shipped

## Objective

Remove the runtime dependency on `fonts.googleapis.com` / `fonts.gstatic.com`
in the Astro marketing site (`web/`) by self-hosting Inter and JetBrains Mono
via Fontsource. Every page currently makes an external network call for fonts;
after this change fonts are bundled into the build and served from the same
origin.

## Acceptance Criteria

- [x] `@fontsource-variable/inter` and `@fontsource/jetbrains-mono` are added
      to `web/package.json` dependencies.
- [x] `web/src/styles/global.css` imports the variable Inter `wght` axis and
      the JetBrains Mono weights the components actually use (400/500/600/700/800)
      from Fontsource.
- [x] The `<link rel="preconnect">` (×2) and the `<link rel="stylesheet">` to
      Google Fonts are removed from `web/src/components/layout/SiteLayout.astro`.
- [x] `--ds-font-sans` in `tokens.css` resolves Inter from the local variable
      family (`'Inter Variable'` — the family name Fontsource registers for the
      variable package, distinct from the static `'Inter'`); `--ds-font-mono`
      resolves JetBrains Mono locally. System fallbacks remain as backup.
- [x] `npm run build` (from `web/`) passes and self-hosted font `.woff2` files
      appear in the build output.
- [x] The two new dependencies are recorded in `web/AGENTS.md` per the repo
      convention (§ "Check before acting").

## Boundaries

- No visual redesign — same two typefaces, same weights the site already used.
- No CSS framework introduced (platform-site spec Boundaries hold).
- `web/` only.

## Assumptions declined / temptations

- Tempted to also self-host with `font-display` tuning or subsetting config;
  declining — Fontsource ships all subsets (latin, latin-ext, cyrillic, greek,
  vietnamese), each `@font-face` gated by `unicode-range`, so an English visitor
  still only fetches the latin `.woff2` at runtime — equivalent to the prior
  Google Fonts `css2` behavior. `font-display: swap` also matches the prior
  `display=swap`. Boring is correct here. (Trimming the committed subset set is
  possible via Fontsource subset imports if deployed asset count ever matters,
  but runtime fetch cost is already minimal.)
- Tempted to drop the static `'Inter'` from the fallback stack; declining —
  harmless and cheap insurance if a static Inter is ever present.
