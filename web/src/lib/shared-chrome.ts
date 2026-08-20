// Marketing-local consumption rules for the generated shared-chrome projection.
// Renderer-local by design: docs consumes the same canonical contract through
// its own renderer-native code. Nothing here is shared with docs-site.
import { withBase } from './paths';
import marketingChrome from './shared-chrome.generated.json';

export type ChromeLink = (typeof marketingChrome.header)[number];

/** The header's call-to-action, selected by its stable ID rather than position. */
export const CTA_ID = 'try-the-build-loop';

/**
 * Resolve a destination's href from its DECLARED kind.
 *
 * `withBase` branches on the target's scheme, which would make internal/external
 * handling hostname-derived. The spec requires kind to come from canonical data,
 * so the branch is made here on `link.kind` and `withBase` only ever sees a target
 * already known to be internal.
 */
export function chromeHref(link: ChromeLink): string {
  return link.kind === 'internal' ? withBase(link.target) : link.target;
}

/**
 * Split the header into its ordered plain destinations and its CTA.
 *
 * Selecting the CTA by ID keeps an approved reordering of the header from
 * silently promoting whichever destination happens to land last.
 */
export function splitHeader(header: readonly ChromeLink[]): {
  links: ChromeLink[];
  cta: ChromeLink;
} {
  const cta = header.find((link) => link.id === CTA_ID);
  if (!cta) {
    throw new Error(
      `shared-chrome header is missing its '${CTA_ID}' call-to-action destination`
    );
  }
  return { links: header.filter((link) => link.id !== CTA_ID), cta };
}

/**
 * Current-location state for a destination on the page at `pathname`.
 *
 * Homepage fragment destinations never claim current state: a fragment needs
 * client-side route evidence the static build does not have.
 */
export function currentState(
  link: ChromeLink,
  pathname: string,
  baseUrl: string
): 'page' | 'location' | undefined {
  if (link.kind !== 'internal' || link.target.includes('#')) return undefined;

  const basePath = baseUrl.replace(/\/$/, '');
  const routePath = pathname.startsWith(basePath)
    ? pathname.slice(basePath.length) || '/'
    : pathname;

  if (routePath === link.target) return 'page';
  if (
    link.id === 'catalogue' &&
    (routePath.startsWith('/packs/') || routePath.startsWith('/journeys/'))
  ) {
    return 'location';
  }
  return undefined;
}
