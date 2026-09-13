import { defineCollection, z } from 'astro:content';
import { docsLoader } from '@astrojs/starlight/loaders';
import { docsSchema } from '@astrojs/starlight/schema';

export const collections = {
  docs: defineCollection({
    loader: docsLoader(),
    // `step` / `steps` are projected by tools/build-site.py from a guidebook
    // step's own "**Step N of M**" declaration. TableOfContents.astro uses them
    // to name the reader's position instead of repeating "On this page".
    schema: docsSchema({
      extend: z.object({
        step: z.number().int().positive().optional(),
        steps: z.number().int().positive().optional(),
      }),
    }),
  }),
};
