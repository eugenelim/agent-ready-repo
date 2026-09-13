# Rendered-page inspection rules

The tables below are the rule layer for the rendered-page inspection step. They
are data, not prose: the step reads them, and so does anything that checks the
step. Wording around a table may change freely; a table's columns and row keys
may not.

## Severity by finding class

A finding's severity comes from its class. Every class has exactly one severity.

| Finding class | Severity | Reader-visible failure |
| --- | --- | --- |
| occlusion | Blocker | One element covers another so the covered text or control cannot be read or used. |
| clipped-at-rest-top | Blocker | Content is cut off or covered at the top of the content area in an at-rest capture, so a reader who never scrolls never sees it. |
| clipped | Major | Content is cut off at a container or viewport edge, away from the at-rest top of the content area. |
| overflow | Major | Content runs outside the visible bounds of the container meant to hold it. |
| target-undersized | Major | An interactive control is rendered too small to hit reliably. |
| illegible | Major | Text cannot be read as rendered — too small, or too close in tone to what sits behind it. |
| crowding | Minor | Elements sit close enough that the grouping is hard to read, without any content being covered or cut off. |

`clipped-at-rest-top` is the one class whose severity does not follow from the
image alone. Whether a capture is at rest is a property of the capture, not of
the picture, which is why the capture record carries the scroll position and why
a capture without one yields no finding at all. A capture taken after scrolling
shows content above the fold leaving the viewport, which is what scrolling is;
that is not this class.

## Severity resolution

| Rule | Value |
| --- | --- |
| severity-source | finding-class |
| judge-supplied-severity | discarded |

A judge may return a severity label. It does not reach the result. Look the class
up in the table above and carry that severity, including when the two disagree.
The judge's job is to say what it sees and where; the severity is the rule's.

## Required captures

Every inspected route needs all four of these. Heights are the browser viewport's
height in CSS pixels; scroll position is the vertical offset the capture was
taken at, in the same units.

| Capture | Viewport height | Scroll position |
| --- | --- | --- |
| short-at-rest | <=600 | 0 |
| short-scrolled | <=600 | >0 |
| tall-at-rest | >=900 | 0 |
| tall-scrolled | >=900 | >0 |

Two heights, because a layout that holds at one often fails at the other, and a
reader on a laptop and a reader on a phone are both readers. Two scroll positions
per height, because the at-rest view is the one nobody scrolls to reach and the
scrolled view is where sticky and overlay elements land on top of content.

A capture set missing any of the four is **incomplete**. An incomplete set cannot
satisfy a completed inspection — it is not a pass with a gap, and no number of
findings from the captures that are present makes it one. Further heights are
welcome and none are required.

## Capture record

Every capture carries all four fields. They describe the browser state the image
was taken in, which the image itself does not show.

| Field | Required |
| --- | --- |
| route | yes |
| viewport-width | yes |
| viewport-height | yes |
| scroll-position | yes |

A capture missing any required field is **unusable**: it yields no finding, and
it is reported as unusable rather than passed over in silence. A judge cannot
recover this state by looking harder — an image of a page at rest and the same
page scrolled to the same pixel are the same picture.

## Judgement request

The request that goes to the judge restates the same four fields recorded with
the capture, so the judgement is made about a known browser state.

| Field | Required |
| --- | --- |
| route | yes |
| viewport-width | yes |
| viewport-height | yes |
| scroll-position | yes |

## Step separation

Capture and judgement are two steps. Keeping them apart is what lets an adopter
keep the capture and route the images to whatever judge they already use.

| Rule | Value |
| --- | --- |
| capture-step-invokes-judge | no |
| capture-step-produces | capture-set |
| judgement-step-input | capture-set |
| judgement-step-produces-captures | no |

The capture step finishes on its own and hands over a capture set plus its
records. The judgement step reads a capture set it did not produce, and never
opens a browser.

## Result states

Every run of the step ends in exactly one of these. Only `completed` is a
completed inspection; the rest are distinct states, not one "unverified" bucket,
because what a reader should do next differs for each.

| Result state | Completed inspection | What it says |
| --- | --- | --- |
| completed | yes | Every required capture was taken, judged, and the observations recorded. |
| incomplete | no | A required capture is missing from the set. |
| unusable-capture | no | A capture arrived without every required field, so nothing could be judged from it. |
| skipped-no-browser | no | No browser was reachable. Names the missing capability. |
| failed-navigation | no | The route could not be reached. |
| failed-capture | no | The browser was reached but the image could not be taken. |
| failed-judgement | no | Captures exist but the judge returned nothing usable. |

Collapsing these would cost the distinction that matters most:
`unusable-capture` is a defect in how the step was run, while
`skipped-no-browser` is a fact about the environment. One "unverified" label
makes the first read as the second.

## Result surfaces

The result state reaches three places, and it is the same state in all three. A
skipped or failed run stays visibly different from a completed one in each.

| Surface | Carries the result state |
| --- | --- |
| evidence-manifest | yes |
| step-output | yes |
| acceptance-gate-input | yes |

## Observations field

| Rule | Value |
| --- | --- |
| field-name | inspection observations |
| distinct-from | screenshots |
| filenames-only | rejected |

`screenshots` records that images exist. `inspection observations` records what
was seen in them, plus the result state. A value naming only filenames is
rejected: a list of names is what the step already had before anyone looked, and
accepting it is exactly how a green signal ends up sitting on an unexamined page.
