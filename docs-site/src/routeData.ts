import { defineRouteMiddleware } from '@astrojs/starlight/route-data';
import { hasCurrent, tabs, type Entry } from './components/rail';

type Link = Extract<Entry, { type: 'link' }>;

function links(entry: Entry): Link[] {
  if (entry.type === 'link') return entry.href.includes('#') ? [] : [entry];
  return entry.entries.flatMap(links);
}

/**
 * Starlight appends the trailing slash to a fragment link too
 * (`/page/#section/`), which no longer names the anchor. Drop it.
 */
function trimFragmentSlash(entries: Entry[]): void {
  for (const entry of entries) {
    if (entry.type === 'group') trimFragmentSlash(entry.entries);
    else if (/#[^/]*\/$/.test(entry.href)) entry.href = entry.href.slice(0, -1);
  }
}

/**
 * Keep previous/next inside the current tab, so paging never jumps from Docs
 * into the CLI tab. A page outside every tab gets no pagination. A page that
 * sets `prev` or `next` in its frontmatter keeps Starlight's result. Fragment
 * links are not pages, so paging skips them.
 */
export const onRequest = defineRouteMiddleware((context) => {
  const route = context.locals.starlightRoute;
  trimFragmentSlash(route.sidebar as Entry[]);
  if (route.entry.data.prev !== undefined || route.entry.data.next !== undefined) return;
  const tab = tabs(route.sidebar as Entry[]).find(hasCurrent);
  const ordered = tab ? links(tab) : [];
  const index = ordered.findIndex((link) => link.isCurrent);
  route.pagination = {
    prev: index > 0 ? (ordered[index - 1] as typeof route.pagination.prev) : undefined,
    next: index >= 0 ? (ordered[index + 1] as typeof route.pagination.next) : undefined,
  };
});
