# Library or SDK documentation

Evidence narrow: six popular open-source docs sets (Python and JavaScript tools, one Rust book chapter), mostly tutorials and quickstarts. No commercial SDK docs were opened. Read each rule as a default plus the condition that changes it.

Load this file only when surface discovery names a library or SDK. Rules marked **Default** apply; items marked **Option** apply only under the stated condition.

## First screen

**Default:** open with one sentence on what the reader gets, then a short sample that shows a call and its result.[^1][^2]

**Option:** on a tutorial page, add a prerequisite list and the supported version pair before the first step. Four of six sets opened do this, but Rust and Python open with reading conventions or install, so the pattern fits tutorials more than landing pages.[^4][^6]

## First reader action

**Default:** a runnable sample with expected output early, where the code produces output. FastAPI shows a 5-line file (about 8 with blanks), one run command, and the expected result.[^3]

**Do not resolve:** a pure library with no one-call output has no "run and see" step. Name the condition: does one call print something the reader can compare? If yes, show it. If not, show the call and what it returns, and say so.

## Sample style

- **Default:** mark omitted code with the language's own marker. Google's guide asks for a comment in the language's syntax, not an ellipsis.[^9]
- **Option:** truncated real output with `...`, as Requests does for long JSON.[^2] This conflicts with the Google rule for code; use `...` only inside output blocks.
- **Option:** text over screenshots when the product is not visual. FastAPI uses two screenshots only because the product renders a UI.[^3]
- Input and output go in separate blocks. Explain every placeholder.

## Reference shape

**Default:** hand-written tutorial or quickstart material beside the reference. Never ship generated reference as the only docs.[^10][^11]

**Option:** one entry per function with Parameters, Returns, and Caveats lists, as React's `useState` page does.[^8] The evidence is one hand-written page; the layout is not shown to beat other layouts. Generate the reference where doc comments exist and are maintained; hand-write only what they miss.

## Troubleshooting

**Default:** word each heading as the reader's symptom. React uses "I've updated the state, but the screen doesn't update".[^8]

**Option:** put the note at the failing step (Django does this) rather than at the page foot (React does this).[^7][^8] Two of six sets have no troubleshooting on the first page or defer it to another section, so state which you chose.[^3][^5]

## Failures to refuse

- **Reference offered as the only docs.** Jacob Kaplan-Moss wrote in 2009 that auto-generated docs are "worse than useless" and that reference is "not in any way a substitute" for tutorials and guides.[^10] The post says it may be out of date, so the narrow rule is "do not offer reference alone", not "generated reference fails".
- **Named example:** the next-drupal issue "Improve Utility of Typedoc API Docs" (opened 2025-01-21) says a move to generated API docs lost detail and is "a jarring transition from the main docs".[^11] One project, one issue, no maintainer reply seen.
- A reference entry with no example. Support is thin (search snippets only); treat it as a check, not a verdict.

## Sources

Confidence rates what the source supports here.

[^1]: Requests: HTTP for Humans, https://requests.readthedocs.io/en/latest/, accessed 2026-11-06. Confidence: medium (one of six independent sets).
[^2]: Requests Quickstart, https://requests.readthedocs.io/en/latest/user/quickstart/, accessed 2026-11-06. Confidence: medium.
[^3]: FastAPI first steps, https://fastapi.tiangolo.com/tutorial/first-steps/, accessed 2026-11-06 and re-opened by a reviewer. Confidence: high for sample size and absence of troubleshooting.
[^4]: React Quick Start, https://react.dev/learn, accessed 2026-11-06. Confidence: medium.
[^5]: The Rust Programming Language, Hello, World!, https://doc.rust-lang.org/book/ch01-02-hello-world.html, accessed 2026-11-06 and re-opened. Confidence: high for the sample and the deferral sentence.
[^6]: The Python Tutorial, https://docs.python.org/3/tutorial/introduction.html, accessed 2026-11-06. Confidence: medium.
[^7]: Writing your first Django app, part 1, https://docs.djangoproject.com/en/stable/intro/tutorial01/, accessed 2026-11-06. Confidence: medium.
[^8]: React reference, useState, https://react.dev/reference/react/useState, accessed 2026-11-06 and re-opened. Confidence: high for layout and the symptom heading; low as proof of a best layout.
[^9]: Google developer documentation style guide, Code samples, https://developers.google.com/style/code-samples, accessed 2026-11-06. Confidence: medium; it sets no sample-length limit and does not rule on output.
[^10]: Jacob Kaplan-Moss, "What to write", 2009-11-10, https://jacobian.org/2009/nov/10/what-to-write/, accessed 2026-11-06 and re-opened. Confidence: low (one author, 16 years old by the post's own note).
[^11]: next-drupal issue 829, https://github.com/chapter-three/next-drupal/issues/829, accessed 2026-11-06. Confidence: low (one issue).
