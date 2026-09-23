// Paging for the `/now/` index. Shared by the two routes that render it, so
// they cannot disagree about where a page starts or how many there are.
//
// Page 1 is `/now/`, not `/now/page/1/`. Google's pagination guidance asks for
// consistent URL conventions, and two URLs for the same first page is the
// inconsistency it warns about. `/now/page/1/` is deliberately never emitted.

/**
 * Releases per index page.
 *
 * 20 is the low end of what the surveyed products use — GitHub Releases shows
 * 10, Twilio 8 or 9, Sentry enough to reach 32 pages over 3.5 years. It is
 * chosen against page WEIGHT rather than against a target page count: at 156
 * releases the unpaginated page was 235 KB, so a 20-release page lands near
 * 30 KB, which is the number that mattered. The page count is allowed to grow
 * instead; that is what pagination is for, and every surveyed product has
 * accepted the same trade.
 */
export const PAGE_SIZE = 20;

export function pageCount(total: number): number {
  return Math.max(1, Math.ceil(total / PAGE_SIZE));
}

/** The slice of `groups` shown on 1-based page `page`. */
export function sliceForPage<T>(groups: readonly T[], page: number): readonly T[] {
  const start = (page - 1) * PAGE_SIZE;
  return groups.slice(start, start + PAGE_SIZE);
}

/**
 * The internal path for a 1-based page number, BEFORE `withBase`.
 *
 * Page 1 collapses to `/now/` so the canonical first page has exactly one URL.
 */
export function pagePath(page: number): string {
  return page <= 1 ? '/now/' : `/now/page/${page}/`;
}
