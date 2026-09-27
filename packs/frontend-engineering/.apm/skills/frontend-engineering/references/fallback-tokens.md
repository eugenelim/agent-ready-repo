# Fallback token block

Load this only when the visual-authority precedence reaches its lowest rung —
no token taxonomy resolved from the adopter's design tree, and no incumbent
token system in the repository to inherit. On any higher rung the values come
from there, and seeding this block instead forks the product's visual identity.

The block is a starting point for a greenfield surface with no design authority
of its own. It is not a house style, and nothing here outranks a taxonomy or an
existing system.

Provide a CSS custom properties block before writing any HTML. Selecting from
`var(--ds-color-primary)` beats fabricating a fresh hex per session —
token-seeding is the single strongest lever for visual consistency.

**The accent below is deliberately not a brand colour.** A greenfield surface's
accent is a decision to make, not a value to inherit: shipping a saturated
default here would hand every surface that reaches this rung the same look, which
is the failure the AI-aesthetic rules name. Replace `--ds-color-primary` with the
accent this product actually wants before writing components against it.

**Three-tier architecture (one-way dependency):**
```
Primitive  →  Semantic  →  Component
(raw hex)      (role)       (usage)
```
Only the semantic layer goes in the seed block; primitives are defined once
at the top of the CSS file and referenced by semantics.

**Minimum viable property set** (`--ds-` prefix for namespace clarity):

```css
:root {
  /* Color roles — semantic, not raw hex */
  --ds-color-surface:      #ffffff;
  --ds-color-surface-alt:  #f8fafc;
  --ds-color-on-surface:   #1a202c;
  --ds-color-on-surface-2: rgba(0, 0, 0, 0.60);
  --ds-color-primary:      #1f2933;  /* placeholder ink — replace, do not ship */
  --ds-color-on-primary:   #ffffff;
  --ds-color-error:        #dc2626;
  --ds-color-on-error:     #ffffff;
  --ds-color-outline:      rgba(0, 0, 0, 0.12);

  /* Spacing — 4 px base, 8-step scale */
  --ds-space-px: 2px;
  --ds-space-1:  4px;
  --ds-space-2:  8px;
  --ds-space-3:  12px;
  --ds-space-4:  16px;
  --ds-space-5:  24px;
  --ds-space-6:  32px;
  --ds-space-7:  48px;
  --ds-space-8:  64px;

  /* Type scale */
  --ds-text-sm:   0.75rem;
  --ds-text-base: 0.875rem;
  --ds-text-lg:   1rem;
  --ds-text-xl:   1.125rem;
  --ds-text-2xl:  1.25rem;
  --ds-font-regular: 400;
  --ds-font-medium:  500;
  --ds-font-bold:    600;
  --ds-leading-tight:  1.25;
  --ds-leading-normal: 1.5;
  --ds-leading-loose:  1.75;

  /* Radius */
  --ds-radius-sm: 4px;
  --ds-radius-md: 8px;
  --ds-radius-lg: 12px;
  --ds-radius-full: 9999px;

  /* Shadow */
  --ds-shadow-sm: 0 1px 2px rgba(0,0,0,0.06);
  --ds-shadow-md: 0 4px 8px rgba(0,0,0,0.08);
  --ds-shadow-lg: 0 8px 24px rgba(0,0,0,0.10);

  /* Motion */
  --ds-duration-quick:    120ms;
  --ds-duration-moderate: 200ms;
  --ds-duration-gentle:   300ms;
  --ds-ease-standard:     cubic-bezier(0.4, 0, 0.2, 1);
  --ds-ease-decelerate:   cubic-bezier(0, 0, 0.2, 1);
}
```
