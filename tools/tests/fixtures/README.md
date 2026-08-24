# Test fixtures

`external-catalogue-smoke/` is the shared source for the local
`external-catalogue-smoke` target and CI Gate B. Both consumers create an empty
`AGENTS.md` after copying it: catalogue archives exclude `catalogue.toml`, and
the archive verifier requires a catalogue marker such as `AGENTS.md`.

Its sample pack is user-capable so the smoke build exercises both the
claude-plugins and APM routes. A repo-only pack yields a valid empty marketplace
but does not exercise marketplace aggregation.
