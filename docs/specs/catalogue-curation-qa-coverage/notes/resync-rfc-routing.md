# Expected-behavior transcript: resync-rfc-routing

This document captures the three re-sync routing cases that `assimilate-repo`
must handle when a previously-assimilated source RFC is re-pointed. It defines
the example inputs, the routing decision logic, and the expected skill output for
each case. Use this as the reference document when running AC4's live QA session.

## Background

RFC-0055 defines two forms for updating a frozen RFC:
- **Erratum** — a genuine correction to an existing decision. Added in-place to
  the Frozen RFC's Errata section.
- **Amendment** — used only while the RFC is Open (not yet frozen). Applied in-
  place to the RFC body.
- **New RFC (superseding)** — when a Frozen RFC needs new decisions (not
  corrections), a new RFC is authored. The prior Frozen RFC gains an Erratum entry
  naming the superseding RFC.

The `assimilate-repo` skill must classify re-sync changes into these three forms
and route accordingly — never appending new decisions to a Frozen RFC's Errata.

The source RFC used in AC4's QA session is `agent-commander` RFC-0001, produced
in the 2026-07-22 `assimilate-repo` QA session.

---

## Case 1 — Open RFC → Amendment

### Input

- **Prior assimilation:** `assimilate-repo` previously produced RFC-0001 in the
  `agent-commander` repo. The RFC recorded verdicts for 57 candidates from
  `llm-wiki-kit`. RFC-0001's Status is `Open` (not yet accepted or frozen).
- **Re-sync trigger:** The operator re-points `assimilate-repo` at the same
  `llm-wiki-kit` source. The skill detects the durable `last-synced.toml` marker
  and compares content hashes. It finds that 4 candidates have changed (updated
  content in `llm-wiki-kit`) and 2 new candidates have appeared.

### Expected routing decision

The source RFC (RFC-0001) is **Open**. New or changed candidates are fresh
information appended to an ongoing proposal. RFC-0055 allows in-place Amendments
to Open RFCs. The correct form is an **Amendment** — update RFC-0001 in-place with:
- Revised verdicts for the 4 changed candidates.
- New verdicts for the 2 new candidates.
- An `## Amendment` section noting the re-sync date and what changed.

### Expected skill output

```
Re-sync complete against llm-wiki-kit (prior run: 2026-07-22).

Changes detected:
  - 4 candidates updated (content hash changed)
  - 2 new candidates

RFC-0001 is Open — applying as Amendment.

Proposed RFC-0001 amendment written to:
  agent-commander/docs/rfc/0001-llm-wiki-kit-assimilation.md

Amendment adds:
  ## Amendment — 2026-07-24

  Re-sync against llm-wiki-kit at <commit-sha>.

  Updated verdicts:
    - shared/parser: verdict unchanged; content revision noted.
    - shared/formatter: verdict revised to `reject` (now duplicates existing core/format).
    - tools/extractor: content update; verdict remains `assimilate` (destination: converters).
    - tools/validator: verdict revised to `needs-new-pack` (validator scope exceeds core).

  New candidates:
    - shared/embedder: verdict `assimilate` (destination: research pack).
    - tools/indexer: verdict `reject` (overlaps existing search tooling).

  No candidates were removed from the source since the prior run.

Review and accept RFC-0001 to proceed with the updated verdicts.
```

---

## Case 2 — Frozen RFC + genuine correction → Erratum

### Input

- **Prior state:** RFC-0001 is now **Frozen** (accepted). Verdicts were acted on;
  several candidates were assimilated.
- **Re-sync trigger:** On re-pointing at `llm-wiki-kit`, the skill detects that
  one prior verdict is now known to be incorrect: `shared/formatter` was assigned
  verdict `assimilate` (destination: core) but the operator has since confirmed it
  duplicates an existing core skill and should have been `reject`.
- **Nature of change:** A correction to an existing decision — not a new decision.
  The candidate was in the prior run and its verdict was wrong.

### Expected routing decision

The source RFC is **Frozen**. The change is a correction to an existing verdict
(not a new candidate or a reversed decision based on new evidence — strictly a
factual error in the prior run). RFC-0055 allows Errata for corrections to Frozen
RFCs. The correct form is an **Erratum** entry added to RFC-0001's Errata section.

### Expected skill output

```
Re-sync complete against llm-wiki-kit (prior run: 2026-07-22).

RFC-0001 is Frozen.

Detected correction to a prior verdict:
  - shared/formatter: prior verdict was `assimilate` (destination: core)
    New verdict: `reject` (duplicates existing core/format skill)
    Nature: correction to a factual error — the prior verdict was wrong, not superseded.

Routing as Erratum to RFC-0001 (RFC-0055 form for corrections to Frozen RFCs).

Proposed Erratum added to:
  agent-commander/docs/rfc/0001-llm-wiki-kit-assimilation.md

Erratum entry:
  ## Errata

  ### E1 — 2026-07-24 — Correction: shared/formatter verdict

  Prior verdict: `assimilate` (destination: core).
  Correct verdict: `reject`. `shared/formatter` duplicates the existing
  `core/format` skill; it was incorrectly assessed as non-overlapping in the
  original run.

  If `shared/formatter` was already assimilated under the prior verdict, remove it
  from core and run `make build-self` to propagate the removal.

Review the Erratum, then update the assimilation ledger to reflect the correction.
```

---

## Case 3 — Frozen RFC + new candidates/reversed verdicts → new RFC

### Input

- **Prior state:** RFC-0001 is **Frozen** (accepted). Verdicts were acted on.
- **Re-sync trigger:** On re-pointing at `llm-wiki-kit`, the skill detects:
  - 5 new candidates not present in the prior run.
  - 1 prior candidate (`tools/extractor`) whose verdict is now reversed based on
    new evidence (the operator has a new use case that makes it additive).
- **Nature of change:** Fresh decisions — new verdicts for new candidates, and a
  reversed verdict based on new information (not a factual error in the original).

### Expected routing decision

The source RFC is **Frozen**. The changes are fresh decisions, not corrections.
RFC-0055 does not allow appending new decisions to a Frozen RFC's Errata. The
correct form is a **new RFC** (RFC-0002) for the new decisions, plus an Erratum
entry on the Frozen RFC-0001 naming RFC-0002 as the superseding document for these
new decisions.

### Expected skill output

```
Re-sync complete against llm-wiki-kit (prior run: 2026-07-22).

RFC-0001 is Frozen.

Detected new decisions:
  - 5 new candidates (not in prior run): fresh verdicts required.
  - 1 reversed verdict (tools/extractor): prior `reject` → new `assimilate` based
    on new operator use case. This is a new decision, not a correction.

Routing as new RFC (RFC-0055: new decisions on a Frozen RFC require a fresh RFC,
not an Erratum — Errata are for corrections only).

New RFC drafted:
  agent-commander/docs/rfc/0002-llm-wiki-kit-assimilation-resync.md

  RFC-0002 covers:
    New candidates (5): shared/tokenizer, shared/chunker, tools/embedder,
      tools/reranker, tools/cache — verdicts below.
    Reversed verdict: tools/extractor — prior RFC-0001 rejected; RFC-0002 assimilates
      (destination: converters). Reversal noted explicitly with rationale.

RFC-0001 updated with Erratum referencing RFC-0002:
  agent-commander/docs/rfc/0001-llm-wiki-kit-assimilation.md → Errata section:

  ### E1 — 2026-07-24 — Superseded for new candidates by RFC-0002

  RFC-0001 recorded verdicts for the initial survey (2026-07-22). New candidates
  discovered in a 2026-07-24 re-sync, and a reversed verdict for tools/extractor,
  are recorded in RFC-0002 (agent-commander/docs/rfc/0002-llm-wiki-kit-assimilation-resync.md).
  RFC-0001 verdicts remain authoritative for the candidates it covers.

Review RFC-0002 and the RFC-0001 Erratum before proceeding.
```
