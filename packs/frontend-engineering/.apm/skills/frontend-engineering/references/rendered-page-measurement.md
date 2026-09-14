# Measuring the rendered-page inspection in your own environment

How often this step reports a page that is actually fine is a property of *your*
setup — your judge, your browser, your viewport sizes — not of the step. It was
measured to move between viewer configurations, and the cause was not isolated
between the model and the environment. So this pack publishes no number. It ships
the fixtures and the procedure instead, and you measure yours.

Run this when you adopt the step, and again whenever you change the judge.

## What ships

Both sets live in `inspection-fixtures/`, next to this file. Every fixture is a
self-contained HTML file with no network requests and no build step: open it from
disk.

Each fixture declares what it is in its own `<meta>` tags —
`inspection-fixture` (`defect` or `clean`), `inspection-fixture-class` on a
defect, and `inspection-fixture-defect` describing the failure in words.

### Defect fixtures — 4

Each carries exactly one reader-visible failure.

| Fixture | Finding class | The failure a reader meets |
| --- | --- | --- |
| defect-occlusion.html | occlusion | The announcement bar sits on top of the page heading and the first line of body text. |
| defect-overflow.html | overflow | The account identifier runs outside the right edge of its card and the end is unreadable. |
| defect-clipped-at-rest-top.html | clipped-at-rest-top | The confirmation heading and order number are cut off above the top of the content area at rest. |
| defect-target-undersized.html | target-undersized | The dismiss control is about ten CSS pixels square. |

### Known-clean fixtures — 4

These are the input set the false-positive rate is measured over. Each is an
ordinary page with nothing reader-visible wrong at any required capture state.

| Fixture | What it is |
| --- | --- |
| clean-article.html | A long-form article with a constrained measure |
| clean-card-grid.html | A responsive pricing grid that reflows rather than overflowing |
| clean-form.html | A form with full-width inputs and a 44px submit control |
| clean-nav.html | A sticky header whose content area is offset by the header's own height |

## The procedure

1. Capture every fixture in both sets at all four required capture states — two
   viewport heights, each at rest and scrolled. That is **up to 4 captures per
   fixture, so at most 8 fixtures × 4 = 32 captures**. Several of these fixtures
   are shorter than a 900px viewport and do not scroll there, so they produce
   fewer: record `page-scrollable: no` on that height's at-rest capture and the
   scrolled requirement for that height is met. Record all five fields with each
   capture, as always.
2. Judge each capture with the judge you actually intend to use, asking only what
   the failure is and where it appears. Derive severity from the finding class;
   discard any severity the judge volunteers.
3. For each **defect** fixture, check whether the run produced a finding naming
   that fixture's recorded defect. A run that names no defect fixture's failure is
   not usable as an inspection step, whatever it reports elsewhere.
4. For each **known-clean** fixture, count it as a false positive if the run
   reported any finding against it.
5. Compute the rate:

   ```
   false-positive rate = (known-clean fixtures with at least one finding)
                         / (known-clean fixtures measured)
   ```

   The denominator is the number of known-clean fixtures you measured — **4** if
   you ran the shipped set unchanged. It is not the total number of fixtures, and
   not the number of captures: a rate measured over defect fixtures too answers a
   different question than the one you asked.

6. Write the result down where your team will find it again, next to the judge
   and viewport sizes it was measured with. It does not transfer to a different
   judge, and it is not a property of this pack.

## Reading your result

There is no threshold here to pass. A rate you can live with is the one where
your team still reads the findings. If every clean page produces a finding,
people stop looking, and the step is worse than not having it.

If the rate is higher than you want, change one thing at a time — the judge, or
the viewport heights — and measure again with the same fixtures.

## Rate vocabulary

These are the terms this pack uses for the measurement. No shipped pack content
states a number against any of them, and none should: a rate written down here
would be read as a property of the step, which is the thing that was measured not
to be true.

| Term |
| --- |
| false-positive rate |
| false positive |
| detection rate |
| detected |
| missed |
| precision |
| recall |
| accuracy |
