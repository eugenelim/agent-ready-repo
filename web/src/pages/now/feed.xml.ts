// The complete shipped history as an Atom feed.
//
// WHY THIS EXISTS. `/now/` renders every released highlight on one page, which
// grows monotonically and is already 120 viewport heights at the supported 320
// minimum. The survey behind that finding
// (docs/product/research/release-feed-length-survey.md) found that the products
// keeping full history navigable all publish a complete feed alongside the HTML
// page — Sentry and Simon Willison's archive both do — and that the feed is
// what lets the HTML page be a display and navigation layer rather than also
// being the exhaustive machine-readable record. It is the one mechanism the
// survey found with no identified downside.
//
// NO NEW DEPENDENCY. `@astrojs/rss` would do this, but a static endpoint
// returning a string does it with the standard library and nothing else, and
// the repository asks for the smallest sufficient option. The cost is that the
// XML escaping below is ours to get right, which is why it is one function used
// at every interpolation and why `test_now_feed` asserts against a real parser
// rather than a regex.
//
// ATOM, NOT RSS. Atom 1.0 specifies its date format (RFC 3339) and entry
// identity (`<id>` must be a permanent, unique IRI); RSS 2.0 leaves both to
// convention. A feed whose entries are release records wants stable identity
// most of all, because a reader that re-shows every entry on each fetch is
// worse than no feed.
import projection from '../../lib/now-highlights.generated.json';
import type { NowGroup } from '../../components/now/NowHighlights.astro';

// Same contract the page enforces, for the same reason: a renamed or
// restructured field should fail the build rather than publish a feed that is
// silently empty or half-populated. Duplicated deliberately — this endpoint is
// a second consumer of the projection, and a guard that lives only in the
// other consumer does not protect this one.
if (projection.schemaVersion !== 1) {
  throw new Error(
    `now-highlights.generated.json is schemaVersion ${projection.schemaVersion}, ` +
      'but the Atom feed renders version 1 — regenerate or update the endpoint.'
  );
}

const SITE = 'https://eugenelim.github.io/agent-ready-repo';
const FEED_URL = `${SITE}/now/feed.xml`;
const PAGE_URL = `${SITE}/now/`;

/**
 * Escape text for both XML text nodes and double-quoted attribute values.
 *
 * `&` must be replaced FIRST or it re-escapes the ampersands the later
 * replacements introduce, turning `<` into `&amp;lt;`. Apostrophe is escaped
 * too so the one function is safe in single-quoted attributes as well; it is
 * not required in a text node, and escaping it there is harmless.
 */
export function xmlEscape(value: string): string {
  return value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;');
}

/** A date-only ISO string as the RFC 3339 instant Atom requires. */
function rfc3339(isoDate: string): string {
  return `${isoDate}T00:00:00Z`;
}

/**
 * One highlight as an HTML fragment, preserving the emphasis and code spans the
 * page renders. Built from the typed segments rather than from `highlight.source`,
 * which is raw Markdown — a feed reader would show the asterisks and backticks.
 */
function highlightHtml(segments: NowGroup['highlights'][number]['segments']): string {
  return segments
    .map((segment) => {
      const text = xmlEscape(segment.value);
      if (segment.type === 'strong') return `<strong>${text}</strong>`;
      if (segment.type === 'code') return `<code>${text}</code>`;
      return text;
    })
    .join('');
}

const groups = projection.groups as readonly NowGroup[];

const releaseLabel = (group: NowGroup) =>
  group.packages.map((pkg) => `${pkg.name} ${pkg.version}`).join(' · ');

function entry(group: NowGroup): string {
  // The entry URL is the release's anchor on /now/, which the page has carried
  // as a stable `id` since the navigability change. `<id>` and the alternate
  // link are the same IRI: it is permanent, and minting a separate identity
  // scheme would give a reader two ways to refer to one release.
  const url = `${PAGE_URL}#${group.changelogAnchor}`;
  const body = group.highlights
    .map((highlight) => `<li>${highlightHtml(highlight.segments)}</li>`)
    .join('');
  return [
    '  <entry>',
    `    <title>${xmlEscape(group.heading)}</title>`,
    `    <id>${xmlEscape(url)}</id>`,
    `    <link rel="alternate" type="text/html" href="${xmlEscape(url)}"/>`,
    `    <updated>${rfc3339(group.date)}</updated>`,
    `    <summary>${xmlEscape(`Released highlights for ${releaseLabel(group)}.`)}</summary>`,
    `    <content type="html">${xmlEscape(`<ul>${body}</ul>`)}</content>`,
    '  </entry>',
  ].join('\n');
}

export function GET(): Response {
  // Groups arrive newest-first, which is the page's contract, so the feed's
  // own `<updated>` is the first entry's date. An empty projection is a real
  // state — an adopter fork with no released highlights — so it falls back to
  // the epoch rather than throwing: an empty feed is valid Atom and a build
  // failure here would be worse than a feed with no entries.
  const updated = groups.length > 0 ? rfc3339(groups[0].date) : '1970-01-01T00:00:00Z';

  const body = [
    '<?xml version="1.0" encoding="utf-8"?>',
    '<feed xmlns="http://www.w3.org/2005/Atom">',
    '  <title>agent-ready-repo — Now</title>',
    '  <subtitle>Outcomes that have shipped in a released version, newest first.</subtitle>',
    `  <id>${xmlEscape(FEED_URL)}</id>`,
    `  <link rel="self" type="application/atom+xml" href="${xmlEscape(FEED_URL)}"/>`,
    `  <link rel="alternate" type="text/html" href="${xmlEscape(PAGE_URL)}"/>`,
    `  <updated>${updated}</updated>`,
    ...groups.map(entry),
    '</feed>',
    '',
  ].join('\n');

  return new Response(body, {
    headers: { 'Content-Type': 'application/atom+xml; charset=utf-8' },
  });
}
