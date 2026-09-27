# HTML authoring contract

Author a complete static HTML lesson directly. The publisher supplies validation,
the restrictive CSP, the fixed quiz runtime, and atomic publication. The model
owns the page's teaching concept, semantic structure, CSS, visual hierarchy, and
composition within this contract.

## Design the Lesson

Before drafting, choose four things from the local evidence:

- Teaching concept: the plain-language idea that makes the change click.
- Audience: the reader's likely familiarity with the code and domain.
- Central visual: the main comparison, map, flow, state story, annotated excerpt,
  timeline, or other semantic treatment that fits the evidence.
- Reading sequence: the order in which the reader should meet context, idea,
  implementation, and quiz.

Use those choices to shape the page. The four teaching roles are mandatory, but
their surrounding structure, order, density, layout, and visual treatment should
fit the work. Do not force every page into cards, a two-column article, a purple
gradient, or a generic dashboard shell. Favor quiet hierarchy, exact labels, and
controls that teach the change.

Put the literal technical claim before its metaphor. A metaphor should compress
one hard relationship, not decorate the page or replace exact terms. If a
metaphor helps, choose one dominant analogy and reuse it consistently; do not
make the reader translate among a uniform, a mold, a press, and a gate to
understand one boundary.

### Choose a visual system for this change

Choose palette, typography, density, contrast, spacing rhythm, and diagram
language from the subject, audience, and teaching task. A state-heavy runtime
change, a visual interface adjustment, and a data transformation should not
automatically look alike. No sample output establishes a cream editorial theme,
dark studio theme, font stack, or other house style.

Use only system-local font stacks because the artifact must remain offline, but
vary their role and combination when that improves comprehension: prose may be
serif or sans; labels may be sans or monospace; source code remains clearly
distinct. Compose for the whole fallback stack, not only its first named face:
different local fonts have different glyph widths, so tight tracking or a
single-font assumption must not make headings collide or labels clip. Choose
light, dark, muted, vivid, monochrome, or mixed palettes only when they support
the explanation, and preserve readable contrast and non-color cues. Build one
coherent visual system inside the page; variability between pages is not an
excuse for inconsistency within one page.

Do not copy CSS from a previous explainer unless the user asks for continuity.
Start from the current evidence and explain why the chosen visual character
fits the change.

Give an experienced reviewer a fast path near the start: state the prior
behavior, the new behavior, and why the difference matters. Express that thesis
with whatever compact comparison, flow, state, map, or prose treatment fits the
evidence; a status card is not a universal requirement. If the named audience
spans newcomers and maintainers, put prerequisite background in a short
`details` disclosure or another clearly skippable semantic region.

## Ground the Diff

The Code role must connect the mental model back to inspectable source. Group
changes by behavior or execution flow, then name the repository-relative file
and the relevant symbol. Add a line reference only when it will remain useful in
the named diff or revision. Include at least one minimal before/after excerpt or
worked input, transition, and outcome. Keep excerpts small enough that the
relationship is easier to see than in the raw diff.

## Required HTML

The draft must:

- Start with `<!doctype html>`.
- Contain one `html` with `lang`, one `head`, one non-empty `title`, one `body`,
  one `main`, and one `h1`.
- Put `<!-- EXPLAIN_DIFF_CSP -->` as the first meaningful child of `head`.
- Put `<!-- EXPLAIN_DIFF_RUNTIME -->` as the final meaningful child of `body`.
- Mark exactly one region for each role with
  `data-explain-role="background"`, `data-explain-role="intuition"`,
  `data-explain-role="code"`, and `data-explain-role="quiz"`.
- Include a table of contents with fragment links to all four role regions.
- Use unique IDs, resolved fragment links, and headings that do not skip levels.
- Preserve code excerpts in `pre > code`.
- Label evidence with `data-evidence="observed"`, `"inference"`, or `"unknown"`
  where the page depends on a fact, reasoning step, or gap.

Allowed markup is semantic and native: document landmarks, headings, paragraphs,
lists, tables, details/summary, inline text, fragment links, `pre`, `code`, and
the quiz controls below. Do not include `script`, event-handler attributes,
inline `style` attributes, external links, forms, SVG, images, media, frames,
plugins, `base`, active metadata, or a CSP meta tag.

## CSS Floor

Use one or more local `style` blocks for the complete composition. Required
floors:

- Narrow layouts work at small widths without horizontal page scroll.
- Grid and flex children can shrink. Inline `code`, file paths, and identifiers
  may wrap or break inside their own region rather than widening the page.
  `pre` and `pre > code` preserve source or diagram whitespace and use contained
  horizontal scrolling when wrapping would destroy meaning. Short illustrative
  snippets may wrap or be shortened instead of clipping.
- Tables keep short headers and labels readable instead of breaking words into
  fragments. When the columns cannot reflow cleanly, the table scrolls as one
  contained region rather than widening the page. Navigation deliberately
  wraps, collapses, or scrolls at narrow widths.
- Native inputs and their selected, unselected, focus, and disabled states stay
  visually distinct against the chosen color scheme.
- Quiz feedback is neutral before evaluation. Correct, incorrect, and
  unanswered results remain distinct in text; if semantic color is used, CSS
  styles the runtime's `data-state="correct"` and
  `data-state="incorrect"` separately and never presents an incorrect or
  unanswered result in the success treatment.
- Visible `:focus-visible` is present for interactive elements.
- `prefers-reduced-motion` is present if any transition, animation, or scroll
  behavior appears.
- The unstyled document order remains useful.

If the named audience is likely to print the lesson or paste its pages into a
light document, add a suitable `@media print` treatment. This is an audience
decision, not a rule that every on-screen explainer must use a light palette.

CSS may express the full page concept, but it may not load resources or hide
execution surfaces. Avoid backslash escapes, `url()`, `@import`, `@font-face`,
`image-set()`, `expression()`, and `-moz-binding`.

## Quiz Contract

Create exactly five quiz questions. Each question is one `fieldset` with
`data-quiz-question`, a non-empty `data-quiz-rationale`, a `legend`, four
labelled radio inputs sharing one non-empty name unique to that question, one option with
`data-correct="true"`, one `button type="button" data-quiz-check`, and one
feedback element with `data-quiz-feedback` and `aria-live="polite"`.

The model writes no script. The publisher injects the only runtime. The runtime
sets textual feedback and `data-state`; the page may style those states, but
must not rely on color or motion alone. The rationale is question-specific
teaching text: it explains the governing behavior after either a correct or
incorrect choice and does not merely say which option was right.

## Sensitive Values

Minimize source excerpts. Replace credential-shaped values, bearer tokens, email
addresses, private hostnames, personal names, user-home paths, and unexplained
high-entropy strings before drafting. Use generic placeholders such as
`<TOKEN>`, `<EMAIL>`, `<PRIVATE_HOST>`, `<PERSON>`, and `<USER_HOME>` while
preserving the surrounding code shape that explains the change.

## Publish

Write the draft under the workspace or operating system temporary directory, then
invoke `scripts/publish_explanation.py`. The publisher validates the safe subset,
injects the CSP and quiz runtime, writes exactly one HTML file on success, and
prints its absolute path. On refusal, revise the draft inside this contract; do
not bypass the publisher.
