# Amendment authority: model-owned page design

## Owner authority

On 2026-09-26, after reviewing the adaptive structured explainer, the scope
owner explicitly approved replacing the structured page-authoring contract with
model-authored HTML. The requested boundary is: let the model own the page's
design, while the shipped skill supplies consistent teaching requirements,
validation, offline safeguards, safe publication, and browser handoff.

## Reason

A controlled comparison used the same model to explain three different change
shapes under two instruction sets: the original prose-led gist and the current
structured skill. The structured path selected fitting archetypes and accurate
content, but every output passed through the same block grammar and the same CSS
system. All three renderer outputs therefore shared one CSS hash and offered no
work-specific interaction beyond the common quiz.

The prose-led path produced three independently composed lessons: a trust-boundary
explainer, a telemetry signal path, and a retirement case file. Their hierarchy,
visual metaphor, and interaction followed the work being explained. This is the
quality the feature is meant to preserve.

The failure begins before rendering. Requiring versioned JSON and closed block
types makes the model translate its teaching idea into the product's vocabulary,
so ideas without a matching field disappear before the renderer sees them. A
larger design schema would recreate HTML while keeping that bottleneck.

## Amended boundary

- Evidence tracing remains bounded and distinguishes observed facts, inference,
  and unknowns during reasoning.
- The model authors one complete self-contained HTML document and owns its visual
  hierarchy, layout, diagrams, metaphor, and responsive CSS.
- A bundled standard-library publisher accepts HTML, not JSON. It rejects active
  or external capabilities, injects one fixed quiz runtime and restrictive CSP,
  confines the output path, and publishes atomically without overwrite.
- Model-authored scripts, event-handler attributes, external or non-fragment
  URLs, network-capable CSS, embedded browsing contexts, forms, SVG, and media
  are rejected. Work-specific teaching may use semantic HTML, CSS, and native
  controls such as `details` without gaining arbitrary JavaScript authority.
- Browser opening remains adopter-specific, explicitly accepted, and outside the
  publisher.

## Plan assumptions

- **Files touched:** amend the spec and unfinished plan tasks; replace the
  structured schema/renderer surface with an HTML authoring guide and guarded
  publisher; update evals, renderer tests, pack-surface tests, README wording,
  verification evidence, and generated projections.
- **Done proof:** TDD covers HTML validation, trusted runtime injection, CSP,
  offline restrictions, path confinement, permissions, and atomic publication;
  three distinct model-authored fixtures pass the real publisher entry point;
  pack tests and local lint/type gates pass; manual visual QA remains
  `skipped-no-browser` in this session.
- **Not changing:** activation boundaries, cross-pack independence, network-free
  generation, the five-question teaching requirement, optional browser handoff,
  or the already selected Core minor release version.

## Declined additions

- **A general-purpose HTML sanitizer:** declined under the standard-library rung.
  Safe rewriting of arbitrary HTML, CSS, and JavaScript is a browser-grade parser
  problem. The publisher instead validates a deliberately capable static subset
  and owns the only script.
- **A larger structured design AST:** declined under the cut-before-adding first
  rung. The benchmark shows that another closed authoring language works against
  the requested model-owned design outcome.
- **A new runtime dependency:** declined under the standard-library rung. A
  bounded `html.parser` validator plus fixed publication code satisfies the
  accepted safeguards without installation or another pack.
