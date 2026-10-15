import { defineRouteMiddleware } from '@astrojs/starlight/route-data';
import { hasCurrent, tabs, type Entry } from './components/rail';

type Link = Extract<Entry, { type: 'link' }>;

function links(entry: Entry): Link[] {
  return entry.type === 'link' ? [entry] : entry.entries.flatMap(links);
}

/**
 * Keep previous/next inside the current tab, so paging never jumps from Docs
 * into the CLI tab. A page outside every tab gets no pagination.
 */
export const onRequest = defineRouteMiddleware((context) => {
  const route = context.locals.starlightRoute;
  const tab = tabs(route.sidebar as Entry[]).find(hasCurrent);
  const ordered = tab ? links(tab) : [];
  const index = ordered.findIndex((link) => link.isCurrent);
  route.pagination = {
    prev: index > 0 ? (ordered[index - 1] as typeof route.pagination.prev) : undefined,
    next: index >= 0 ? (ordered[index + 1] as typeof route.pagination.next) : undefined,
  };
});
