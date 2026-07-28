# Test architecture notes

## Container API

Astro 7.1.0 exports `experimental_AstroContainer` (not `AstroContainer`) from
`astro/dist/container/index.js`. The stable `AstroContainer` export does not
exist in this version.

**Test environment requirement:** Container API tests must use `// @vitest-environment node`
per-file directive. The jsdom environment breaks esbuild's `TextEncoder instanceof Uint8Array`
invariant, which prevents the Container API from initialising.

**axe-core with JSDOM in node environment:** To run axe-core against rendered HTML
in a node-environment test, import `JSDOM` from `jsdom` directly and pass a DOM element:

```typescript
import { JSDOM } from 'jsdom';

const dom = new JSDOM(`<main>${html}</main>`);
const main = dom.window.document.querySelector('main') as Element;
const results = await axe.run(main as any);
```

Wrap the component HTML in `<main>` to satisfy axe-core's `region` landmark rule,
which would otherwise report a false positive.

**Pattern established in:** `web/src/test/StatusChip.test.ts`

## Axe-core direct usage

`@axe-core/vitest` does not exist on npm (verified 2026-07-28). Use `axe-core` directly.

Import: `import axe from 'axe-core'`
Run: `const results = await axe.run(element)`
Assert: `expect(results.violations).toHaveLength(0)`
