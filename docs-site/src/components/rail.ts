/**
 * Tab and stage lookups over Starlight's resolved sidebar.
 *
 * The sidebar config's top level is the set of top-bar tabs (Docs, CLI,
 * Packs, Build a Catalogue). Inside the Docs tab, groups whose label is an
 * operating-model stage carry that stage's line colour. Both facts come from
 * the one sidebar array, so the header, sidebar, and page title cannot drift.
 */

type Link = { type: 'link'; label: string; href: string; isCurrent: boolean };
type Group = { type: 'group'; label: string; entries: Entry[]; collapsed?: boolean };
export type Entry = Link | Group;

export const STAGES: Record<string, string> = {
  'Set up a repository': 'setup',
  'Decide what to build': 'decide',
  'Shape it': 'shape',
  'Build it': 'build',
  'Ship it': 'ship',
};

/** True when the entry is, or contains, the current page. */
export function hasCurrent(entry: Entry): boolean {
  return entry.type === 'link' ? entry.isCurrent : entry.entries.some(hasCurrent);
}

/** First link inside an entry, depth-first: the landing page of a tab. */
export function firstHref(entry: Entry): string | undefined {
  if (entry.type === 'link') return entry.href;
  for (const child of entry.entries) {
    const href = firstHref(child);
    if (href) return href;
  }
  return undefined;
}

/** The top-level tab groups. */
export function tabs(sidebar: Entry[]): Group[] {
  return sidebar.filter((entry): entry is Group => entry.type === 'group');
}

/** The tab holding the current page; pages outside every tab fall back to the first tab. */
export function currentTab(sidebar: Entry[]): Group | undefined {
  const all = tabs(sidebar);
  return all.find(hasCurrent) ?? all[0];
}

/** The operating-model stage of the current page, if it sits in a stage group. */
export function currentStage(sidebar: Entry[]): { label: string; key: string } | undefined {
  const tab = currentTab(sidebar);
  const group = tab?.entries.find(
    (entry): entry is Group => entry.type === 'group' && entry.label in STAGES && hasCurrent(entry)
  );
  return group ? { label: group.label, key: STAGES[group.label] } : undefined;
}
