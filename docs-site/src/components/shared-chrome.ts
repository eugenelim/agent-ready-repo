import sharedChrome from '../shared-chrome.generated.json' with { type: 'json' };

export type DocsChromeLink =
  | (typeof sharedChrome.product_orientation_band)[number]
  | (typeof sharedChrome.product_navigation)[number]
  | (typeof sharedChrome.footer)[number]['destinations'][number];

/** Resolve only declared internal targets against the combined-site base. */
export function docsChromeHref(link: DocsChromeLink, docsBase: string): string {
  return link.kind === 'internal' ? `${docsBase}${link.target}` : link.target;
}

/** Apply the docs root/location rule without claiming fragment current state. */
export function docsChromeCurrent(
  link: DocsChromeLink,
  pathname: string
): 'page' | 'location' | undefined {
  if (link.kind !== 'internal' || link.target.includes('#')) return undefined;
  if (pathname === link.target) return 'page';
  if (link.target === '/docs/' && pathname.startsWith('/docs/')) return 'location';
  return undefined;
}
