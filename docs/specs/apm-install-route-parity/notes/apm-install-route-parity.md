# APM install-route parity evidence

This packet preserves the deferred live-install evidence identified by
`apm-install-route-parity`. The implementation contract remains in the frozen
specification; the recording surface is
[`manual-qa-matrix.md`](../../adapt-to-project/notes/manual-qa-matrix.md).

## Evidence request

Use a development environment with the named adapters and complete rows 32–34
of the existing manual-QA matrix:

- row 32: APM core project-scope marker, nudge, and class-1 behavior;
- row 33: APM converters user-scope marker, nudge, and classes 1–4; and
- row 34: first-firing characterization for Copilot, Cursor, and Gemini.

For each row, record the tested revision, adapter and version, clean install
scope, command or user gesture, observable result, and exit status where one
exists. Preserve redactions and do not infer parity from generated artifacts
alone. The packet is complete when every cell required by rows 32–34 has a
passing receipt or a separately owned defect.

