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

Open. No owner assigned. Not scheduled. **Reviewed 2026-09-11 and deliberately
parked.**

**Why it stays parked.** It was checked against the one piece of work that could
have forced it. Slice S6 of `sdlc-guide-uplift-and-learning-paths`
(`four-discipline-sequence`) presents four disciplines as an ordered sequence,
which is the kind of content that invites a diagram. Its AC-0016 forbids an
image on either surface precisely so this defect is avoided rather than hit, and
its construction record routes the diagram obligation here by name. So S6 does
not put this on the critical path, and nothing else currently scheduled does.

**What would unpark it.** The first guide that genuinely needs an image. At that
point this is blocking, not deferred, and the blast radius above — one regular
expression governing every link in 209 pages — is why it needs its own contract
rather than being folded into that guide's change.

**What parking costs.** Every guide is silently constrained to text-only. That
constraint is invisible: nothing fails, no linter fires, and an author discovers
it only by shipping a broken image. That cost is accepted here rather than
unnoticed.
