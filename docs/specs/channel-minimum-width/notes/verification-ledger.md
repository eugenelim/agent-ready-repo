# Verification ledger — channel minimum width

## T6 — the step performed against a single-channel surface

A completeness test cannot show that one channel was enough to judge a page.
This is the performed run.

- **Surface:** the marketing site's `/` route, built by `make site-build` at
  18:13 and served under its production base path.
- **Minimum in force:** `1280`.
- **Channel basis:** `fallback` — no breakpoints declared. The minimum composes
  with the basis rather than replacing it.
- **Discarded breakpoints:** none. No breakpoints were declared, so the minimum
  discarded nothing.
- **Required channels:** one, `wide >=1280`, captured at 1280. Without the
  minimum the same surface requires two channels — `narrow <=480` and
  `wide >=1024` — and eight captures per route. With it, four.

### Observations

| Capture | Viewport | Scroll | Scrollable | h1 top | h1 width | Overflow-x | 4xx |
| --- | --- | ---: | --- | ---: | ---: | --- | ---: |
| short-at-rest | 1280×600 | 0 | yes | 169 | 797 | no | 0 |
| short-scrolled | 1280×600 | 400 | yes | −221 | 797 | no | 0 |
| tall-at-rest | 1280×900 | 0 | yes | 169 | 797 | no | 0 |
| tall-scrolled | 1280×900 | 400 | yes | −221 | 797 | no | 0 |

Read from the images, not from the geometry alone. At rest the navigation, the
hero heading, the body copy, both calls to action and the three-column stat row
all render in place, with the measure held at 797px inside a 1280px viewport.
Scrolled, the stat row and the next section boundary enter the frame cleanly and
no element is clipped or overlapped. Nothing is cut off horizontally at either
height: `overflow-x` is false in all four.

### The frame the evidence needed

The first attempt at this run served `build/` at the server root and captured a
page whose stylesheets all 404'd — the site is built under a `/agent-ready-repo/`
base path. Those four captures were discarded unread. An unstyled page is not
the surface, and the geometry proves it: the heading measured 1264px wide
unstyled against 797px styled. The recorded run serves the production base path
and records zero 4xx responses per capture, which is what makes the judgement
about this surface rather than about a broken one.

### Result

- **Result state:** `completed`.
- **Verdict:** `pass`. No blocking finding.

One channel was enough. The surface supports 1280 and up, every required
capture was taken at a width it supports, and the reduced set still exercised
both heights and both scroll positions — which is where this axis expects a
layout to fail. The four captures the minimum removed would all have been below
1280, where this surface makes no claim.
