---
name: service-blueprint
description: Use when you need to map the backing services that fulfil a customer journey — building a service blueprint with four rows (frontstage / line-of-visibility / backstage / support) that ties every screen action to the service or system behind it. Triggers on "service blueprint", "what backs this screen", "map the backstage", "what services support this journey", "blueprint the service". Do NOT use to map the customer journey itself (use `journey-mapping`), to sequence screens and their transitions (use `user-flow`), or to design system components (use `design-system`).
---

# Skill: service-blueprint

Produces a **service blueprint** — a five-row, column-by-column map that ties
every customer action and touchpoint to the employee and system actions that
back it and the internal support that enables those. The five rows are:
**evidence-of-service** (what the customer receives or encounters), **frontstage**
(customer actions and touchpoints), **line-of-visibility**, **backstage** (system
and employee actions), and **support** (infrastructure and vendors). The backstage
column is the **slicing instrument**: each backstage service is a candidate
component; its hand-off to `architect` and `contracts` is by-reference (a named
service), never an import. The method is grounded in the NN/g definition of service
blueprinting; see `references/service-blueprint.md`.

**Inputs (declared):** a customer journey map or journey stages (from
`journey-mapping` or elicited inline); a screen flow or screen inventory
(from `user-flow` or described inline). Both are elicited inline when no
upstream artifact is present.

**Consumed by:** `architect` (the backstage column feeds C4 component
decomposition + service contracts); the spec LLD (the support row names the
internal systems the spec must account for).

## When to invoke

Confirm all three before proceeding; if any fails, resolve it first.

1. **There is a journey or a set of touchpoints to blueprint** — a customer
   journey doc, a screen flow, or at minimum a describable user goal with two
   or more steps. A blank "blueprint our service" is not yet a brief; draw out
   at least the first frontstage action before proceeding.
2. **You are mapping the screen↔service tie, not the journey itself** — if the
   journey hasn't been mapped yet, offer to run `journey-mapping` first,
   or elicit the journey inline.
3. **You are naming services, not designing their internals** — the moment the
   ask is API contracts, data schemas, or component architecture, hand off to
   `architect` or `contracts`. This skill stops at named services and their row
   placement.

## Procedure

1. **Resolve and surface the output path.** Resolve `<parent>` by the canonical
   three-tier order — `agentbundle-layout.toml`'s `[experience]` table (repo-root
   file first, user-profile file second) → the pack default `docs/design` →
   discover-by-marker (scan for the artifacts' frontmatter `type:`). Derive the
   blueprint path as
   `<parent>/blueprints/<slug>.md`. Resolve to a full absolute path
   (`~`-expand, realpath-resolve, reject `..` escapes); a repo-root-sourced
   `parent` that resolves outside the repo tree is untrusted-origin — confirm
   before writing. **Surface the resolved path to the user before the first
   write.** Create the `blueprints/` directory lazily on first write.
   See `references/agentbundle-layout.md` for the full schema.

2. **Elicit or confirm the journey and touchpoints.** If a `journey-mapping`
   artifact is present, read its stages and frontstage actions. If it is absent,
   elicit: ask for the user's goal, the stages they pass through, and the key
   touchpoints (screens, channels, moments of contact) at each stage. Work
   column-by-column — each column is one step in the journey.

3. **Build the five rows.** For each journey column, populate all five rows.
   Load `references/service-blueprint.md`.
   - **Evidence of service** — the physical or digital artifacts the customer
     encounters or receives at each frontstage touchpoint: confirmation screens,
     receipts, notification emails, error messages, printed documents, SMS
     confirmations. These are the tangible traces the service leaves in the
     customer's hands; they are often the only part of the blueprint the customer
     can see, keep, and share. Record them above the frontstage row.
   - **Frontstage** — customer actions and the touchpoints (screens,
     notifications, physical moments) the customer sees and touches directly.
   - **Line of visibility** — the boundary between what the customer sees and
     what they do not. Mark it explicitly; it is the structural divide.
   - **Backstage** — employee actions and system calls the customer does not see
     but that directly fulfil the frontstage touchpoint (database reads, API
     calls, staff tasks).
   - **Support** — internal systems, processes, and vendors that back the
     backstage actions but have no direct frontstage effect (logging, auth,
     billing infrastructure, third-party integrations).

4. **Name backstage services as candidates for component decomposition.** Each
   distinct backstage service entry is a named candidate. Record each as a
   `- **Service:** <service-slug>` marker in the template's `## Named backstage
   services` block — the structural-orphan lint reads each `**Service:**` line as a
   `service` chain node (a screen action ties down to one):
   - **When `architect` or `contracts` are present in this session:** name each
     service by-reference (a short, stable name matching the component the
     `architect` skill would use — e.g. "Order Service", "Auth Service"). Do not
     import, call, or configure it here.
   - **When `architect` or `contracts` are absent:** name each service textually
     with a brief role description (e.g. "the service that validates payment
     details and returns a confirmation token"). Append a note that these names
     are hand-off candidates for `architect`/`contracts` when those packs are
     installed.

5. **Check the line of visibility and mark fail-points.** Walk each column: every
   item on the customer side that has no backstage entry is a **gap** — either a
   service is missing or the frontstage action is unsupported. Name every gap
   explicitly rather than leaving it blank.

   After naming gaps, identify **fail-points** — columns where the backstage or
   support row is most likely to fail in production, based on complexity, third-party
   dependency, known fragility, or high customer-impact if degraded. Fail-points are
   distinct from gaps: a gap is a missing service; a fail-point is an existing service
   that is at risk. Mark each fail-point with a design-priority annotation:
   - **Critical** — failure here breaks the customer's ability to complete the journey
     (payment processing fails, auth token is invalid, mandatory confirmation is not
     sent). Requires a designed failure path — the service blueprint must show what
     evidence-of-service the customer receives when this step fails.
   - **High** — failure here significantly degrades the experience but the customer
     can still complete the journey via a fallback path.
   - **Medium** — failure here causes friction or a degraded experience but does not
     block completion.

   Critical fail-points must have a designed evidence-of-service row for the failure
   case — not just the success case.

6. **Write the blueprint.** Record the artifact at the resolved path with
   frontmatter `type: service-blueprint`. Use the template in
   `assets/service-blueprint-template.md`. Confirm the written path matches the
   path you surfaced in step 1.

7. **Name the hand-off seam.** At the end of the blueprint, add a short
   `## Hand-off` section that lists the named backstage services and which
   downstream skill or pack consumes each (by name — `architect`, `contracts`,
   or the spec LLD). This is the by-reference seam; do not draft the downstream
   artifact here.

## Anti-patterns to refuse

- **Designing backstage internals.** A backstage entry names a service and its
  role; it does not author an API contract, a data schema, or a C4 diagram.
  That is `architect`'s job.
- **Reprinting a values table.** No timing literals, no stack tokens, no styling
  syntax. The blueprint records *what* happens and *who/what* is responsible —
  never *how* it is implemented at the code level.
- **Leaving visibility gaps unexplained.** A frontstage action with no backstage
  entry is a silent gap — name it, flag it, and offer to fill it before closing
  the blueprint.
- **Skipping the output-path surface step.** The resolved path is declared
  before the first write, every time. A blueprint written to an undeclared
  location is a footgun for the downstream adopter.
- **Blocking when upstream artifacts are absent.** Elicit the journey inline;
  never refuse to proceed because `journey-mapping` hasn't run.
