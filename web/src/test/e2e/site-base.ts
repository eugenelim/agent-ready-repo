/**
 * The deployment base, derived from configuration rather than restated.
 *
 * `site-browser-quality-gate` AC3 requires every route to be base-qualified from
 * configuration, not from a repository-name literal. Before this module the
 * literal `/agent-ready-repo/` appeared in seven places — `playwright.config.ts`
 * twice and five route constants across three spec files — so changing the
 * deployment base would have left the browser suite testing paths the site no
 * longer serves, and it would have failed in a way no test predicted.
 *
 * `web/astro.config.ts` is the single source of truth: it is what the build reads,
 * so a base the tests derive from it cannot disagree with the emitted site.
 */
import webConfig from '../../../astro.config';

/** `/agent-ready-repo`, with any trailing slash removed. `''` when served at root. */
export const SITE_BASE: string = String(webConfig.base ?? '').replace(/\/+$/, '');

/** The docs subtree lives beneath the marketing base (docs-site sets `base` to it). */
export const DOCS_BASE: string = `${SITE_BASE}/docs`;

function previewPortFromEnvironment(value: string | undefined): number {
  if (value === undefined || value === '') {
    return 4321;
  }

  const requirement = 'ARR_PREVIEW_PORT must be an integer from 1 to 65535';
  if (!/^\d+$/.test(value)) {
    throw new Error(`${requirement}; received ${JSON.stringify(value)}`);
  }

  const port = Number(value);
  if (!Number.isSafeInteger(port) || port <= 0 || port > 65535) {
    throw new Error(`${requirement}; received ${JSON.stringify(value)}`);
  }
  return port;
}

/** Port the preview server binds; shared with `playwright.config.ts`'s webServer. */
export const PREVIEW_PORT = previewPortFromEnvironment(process.env.ARR_PREVIEW_PORT);

export const PREVIEW_ORIGIN = `http://localhost:${PREVIEW_PORT}`;

/** What Playwright polls to decide the preview server is up. */
export const PREVIEW_READY_URL = `${PREVIEW_ORIGIN}${SITE_BASE}/`;

/** Qualify a logical marketing path: `/now/` → `/agent-ready-repo/now/`. */
export function withBase(path: string): string {
  return `${SITE_BASE}${path.startsWith('/') ? path : `/${path}`}`;
}

/** Qualify a logical docs path: `/` → `/agent-ready-repo/docs/`. */
export function withDocsBase(path: string): string {
  return `${DOCS_BASE}${path.startsWith('/') ? path : `/${path}`}`;
}
