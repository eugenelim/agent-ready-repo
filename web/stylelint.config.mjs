/**
 * Gate 3 — CSS token enforcement for the marketing site.
 *
 * Requires a semantic `var(--ds-*)` token for the four properties below in
 * every `src/` stylesheet and every `.astro` `<style>` block.
 */
export default {
  plugins: ['stylelint-declaration-strict-value'],

  rules: {
    'scale-unlimited/declaration-strict-value': [
      ['color', 'background-color', 'border-color', 'font-size'],
      {
        // These are keywords, not colours. `inherit`, `transparent` and
        // `currentColor` take their value from elsewhere, so there is nothing
        // to tokenise. `Canvas`, `CanvasText` and `LinkText` are CSS system
        // colours used only inside `@media (forced-colors: active)`: Windows
        // High Contrast substitutes the user's own theme for them, so pinning
        // one to a token would defeat the mode. `SiteNav.astro` carries the
        // comment for the repair that introduced them.
        ignoreValues: [
          'inherit',
          'transparent',
          'currentColor',
          'Canvas',
          'CanvasText',
          'LinkText',
        ],
        disableFix: true,
        message:
          'Use a semantic design token (var(--ds-*)) for "${property}", not ' +
          'the literal "${value}". Tokens live in src/styles/tokens.css.',
      },
    ],
  },

  // Component CSS lives in `.astro` `<style>` blocks. Without this override
  // stylelint reads only the four files under `src/styles/` and reports a
  // pass while every component goes unchecked.
  overrides: [{ files: ['**/*.astro'], customSyntax: 'postcss-html' }],

  ignoreFiles: ['**/node_modules/**', '**/*.generated.*'],
};
