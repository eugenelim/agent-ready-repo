// Prefix an internal absolute path with the configured base (`import.meta.env.BASE_URL`,
// e.g. '/agent-ready-repo/' in production, '/' in a root-served build). Astro
// auto-prefixes its own bundled assets, but hardcoded hrefs in markup are not
// rewritten — route every internal link through here. External URLs pass through.
const base = import.meta.env.BASE_URL;

export function withBase(path: string): string {
  if (/^https?:\/\//.test(path) || path.startsWith('mailto:')) return path;
  const b = base.endsWith('/') ? base.slice(0, -1) : base;
  return b + (path.startsWith('/') ? path : `/${path}`);
}
