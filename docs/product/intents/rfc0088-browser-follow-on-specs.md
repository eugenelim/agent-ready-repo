# RFC-0088 browser pilot follow-on specifications are ready to author

- **Status:** Draft
- **Level:** capability
- **Authority:** [RFC-0088 follow-on release gates](../../rfc/0088-web-pilot-foundation.md)

## Outcome

The RFC-0088 browser pilot has a complete set of three separately scoped follow-on specifications for foundation delivery, behavior results, and repair tooling.

## Opportunity

RFC-0088 defines three mandatory implementation specifications before its foundation packs, behavior results or downloads, and repair tooling may ship.

## What this absorbs

### rfc0088-spec-1-foundation-provider-vertical

Author the synthetic foundation and provider vertical specification. It covers a pinned-container fixture, current-rail runtime delivery, browser lifecycle, authorization-order fixtures, an install/admit/activate/upgrade/rollback/repair gate, and a user guide for login handoff and recovery. It carries Q5's per-destination credential-exposure declaration. RFC-0088 labels this “Spec 1 — foundation delivery and lifecycle” at `docs/rfc/0088-web-pilot-foundation.md:798`; it must pass before the first foundation pack can merge.

### rfc0088-spec-2-result-policy-contracts

Author the generic results and policy contracts specification. It covers result and artifact contracts, downloads, retention and quotas, diagnostics, redaction, authorization, and network and filesystem policy. RFC-0088 labels this “Spec 2 — results, files, policy, and diagnostics” at `docs/rfc/0088-web-pilot-foundation.md:800`; it must pass before behavior results or downloads ship.

### rfc0088-spec-3-developer-workbench

Author the developer workbench specification for supervised probes, packaging and provenance review, and the repair workflow. RFC-0088 labels this “Spec 3 — developer workbench” at `docs/rfc/0088-web-pilot-foundation.md:801`; it must pass before repair tooling ships.

## Assumptions

- Each follow-on remains a separate future specification because RFC-0088 assigns distinct release gates to the three slices.

## Source

- Mode: repo-origin
- Locator: workspace.toml
- Revision: 581dd8b7aefba04f566e4ea9a3213da8c6afb55d
