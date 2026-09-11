# Defect: a guide cannot carry an image that works on both surfaces

Found 2026-09-10 while probing whether the operating-model canvas can render on
GitHub and the docs site from one source. Recorded here because this spec owns
the guide-to-Starlight build boundary.

## Why it matters

`guides/**` is dual-purpose by design: the same Markdown is browsed on GitHub
and projected by `tools/build-site.py` into the Starlight docs site. An image
must therefore resolve under two different renderers from one source file.
Today neither image syntax does.

## Measured behaviour

`tools/build-site.py` contains no handling of `svg`, `png`, `image`, or
`asset` — assets are never copied to the site. Its guide rewriter applies one
regular expression to the body:

```
(\]\()([^)#"'\s]+)(#[^)]+)?\)
```

Run against each construct:

| Construct | Treatment | Result on the site |
| --- | --- | --- |
| `![alt](./assets/x.svg)` | **rewritten** — the pattern cannot distinguish an image from a link | the path becomes a Starlight page URL or a GitHub blob URL; both are HTML pages, so the image is broken |
| `<img src="./assets/x.svg">` | untouched | relative path with no asset copied to the destination; broken |
| `<picture><source srcset="./assets/x.svg">` | untouched | same |

Both syntaxes fail, in opposite directions.

## What is not the problem

The GitHub half works. Probed 2026-09-10 against GitHub's own renderer
(`gh api --method POST /markdown`, `gfm` mode with repository context):
`<picture>` with `prefers-color-scheme` sources survives intact, `<img>` with a
relative path survives and gains `style="max-width: 100%;"`, and a Markdown
image survives. Only inline `<svg>` is removed outright.

So a single `<picture>` block is acceptable to both renderers. The gap is
entirely in projection.

## Why nothing caught it

No guide carries an image today — the one grep hit in `guides/` is prose inside
a code sample — so the path has never been exercised. `validate_guides.py` does
not check image targets, and the emitted-link audit checks links rather than
image sources.

## The shape of a fix

The dual-purpose mechanism already exists: `_rewrite_guide` deliberately lets
the source and the projection differ, so a relative link that is correct on
GitHub is rewritten for the site. Extending that to assets means teaching the
rewriter to recognise image syntax — Markdown image paths and HTML `src` and
`srcset` — as a distinct case from page links, and adding the asset copy the
build currently lacks.

**Blast radius is the reason this needs its own contract rather than a quick
patch.** That one regular expression governs every link in 209 guide pages, so
a change to it is small in code and wide in consequence.

## Status

Open. No owner assigned. Not scheduled.
