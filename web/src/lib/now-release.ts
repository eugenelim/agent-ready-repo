// Formatting shared by everything that renders a release: the `/now/` list,
// the per-release permalink, and the Atom feed.
//
// Lifted out when the permalink route arrived and made this the THIRD caller.
// Two copies of a date formatter is a smell; three is a drift bug waiting for
// someone to fix one of them.

/** One release's packages as "governance-extras 0.9.7", or both names when an entry released two. */
export function releaseLabel(
  packages: readonly { readonly name: string; readonly version: string }[]
): string {
  return packages.map((pkg) => `${pkg.name} ${pkg.version}`).join(' · ');
}

const MONTHS = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December',
];

/**
 * 2026-08-16 → "16 August 2026".
 *
 * Built from the ISO parts rather than `new Date(iso)`: parsing a bare date
 * string is UTC while formatting is local, so a timezone behind UTC renders
 * the previous day.
 */
export function readableDate(iso: string): string {
  const [year, month, day] = iso.split('-').map(Number);
  return `${day} ${MONTHS[month - 1]} ${year}`;
}
