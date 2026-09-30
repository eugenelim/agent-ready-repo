# Amendment authority: adaptive structured explainers

## Owner authority

On 2026-09-25, the scope owner explicitly approved amending and reworking the
accepted `explain-diff` delivery after observing that the fixed composition
could produce an unimaginative, text-led explanation. The approved direction is
to let the language model design the most useful explainer for the kind of code
change while retaining the structured-data-only renderer boundary.

## Reason

The first implementation lets the model author content and select a small set
of blocks, but the renderer fixes the overall teaching shape. That is not enough
for changes best explained as an execution trace, data flow, state transition,
before/after comparison, architecture map, API contract, or annotated code
walkthrough.

The amended contract will add bounded explainer archetypes, composition choices,
and richer semantic visual primitives. It will continue to prohibit raw HTML,
CSS, and JavaScript input; remain offline and deterministic; use only the Python
standard library; stay independent of other packs; and keep browser opening in
the adopter-specific handoff.
