import { getCollection } from 'astro:content';

export interface WalkStep {
  step: number;
  title: string;
  href: string;
  current: boolean;
}

export interface Walk {
  name: string;
  step: number;
  steps: number;
  items: WalkStep[];
}

/**
 * The guidebook walk for one page, or null when the page is not a step.
 *
 * `step` / `steps` are projected by tools/build-site.py from the page body's
 * own "**Step N of M**" declaration, so every surface that names a position --
 * this panel, the numbered sidebar entry, the page text -- derives from one
 * statement and they cannot disagree.
 *
 * Siblings are scoped by directory rather than by pack, so a pack that grows a
 * second guidebook keeps the two walks apart.
 */
export async function guidebookWalk(entry: {
  id: string;
  data: { step?: number; steps?: number; title: string };
}): Promise<Walk | null> {
  const { step, steps } = entry.data;
  if (!step || !steps) return null;

  const directory = entry.id.split('/').slice(0, -1).join('/');
  const siblings = await getCollection(
    'docs',
    (other: { id: string; data: { step?: number } }) =>
      other.data.step !== undefined &&
      other.id.split('/').slice(0, -1).join('/') === directory,
  );
  if (siblings.length < 2) return null;

  const base = import.meta.env.BASE_URL.replace(/\/$/, '');
  return {
    // The pack segment of the route, which is the guidebook's own name. Taken
    // from the path rather than a title so the rail names the same thing the
    // reader clicked in the sidebar.
    name: directory.split('/')[1] ?? '',
    step,
    steps,
    items: siblings
      .sort((a, b) => (a.data.step ?? 0) - (b.data.step ?? 0))
      .map((item) => ({
        step: item.data.step as number,
        title: item.data.title,
        href: `${base}/${item.id}/`,
        current: item.id === entry.id,
      })),
  };
}
