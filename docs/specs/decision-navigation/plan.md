# Plan: Decision navigation

- **Spec:** [`spec.md`](spec.md)
- **Status:** Approved
- **Repository anchors:** `packs/governance-extras/DESIGN.md`; `packs/governance-extras/.apm/skills/rfc-status/`; `packs/core/.apm/skills/explain-diff/references/html-authoring.md`; `packs/governance-extras/pack.toml`; divergence: decision navigation covers a corpus and two output modes, so `explain-diff` is a safety precedent rather than a required renderer or page structure.

> **Plan contract:** this is the implementation strategy. It may change
> substantively only while its Status is `Drafting`, before approval records its
> baseline. After approval, `spec.md` and `plan.md` are pinned in substance;
> execution observations belong in
> `docs/specs/decision-navigation/notes/verification-ledger.md`.
>
> **Not every field is contract.** `Touches`, `Tests` and `Done when` are what a
> completion gate reads. `Design`, `Approach`, `Grounding` and `Risks` are
> working material before approval. Internal renderer, parser, payload, search,
> graph, styling, and module choices remain with the implementation team unless
> they change an accepted behavior, add a dependency, or cross an ask-first
> boundary in the spec.

## Approach

Build one read-only `navigate-decisions` capability inside Governance Extras with two observable modes: a bounded, versioned query for agents and a self-contained HTML explorer for people. The explorer offers peer list, lifecycle-graph, guidance-context, and record-detail views over one corpus. Start with mixed-corpus and trust-boundary tests, implement confined record discovery and checked lineage, prove cross-view fact parity, add safe offline publication and measured representation selection, then replace activation and documentation only after the new behavior is proven.

A read-only probe on 2026-10-02 measured 1,668 KiB allocated under `docs/adr/` and 6,512 KiB under `docs/rfc/`. That keeps a current-corpus full artifact credible but does not justify a growth claim, so the representation rule remains gated by the Chrome schedule in **AC-0015**.

## Constraints

- Implementation dispatch remains gated until RFC-0105 and the reshaped CAP-0002 are accepted. The approved spec and plan may be reviewed and registered before that dispatch gate closes.
- `new-adr` and `new-rfc` remain separate authoring skills. `navigate-decisions` is read-only and cannot claim to select complete applicable policy.
- List, lifecycle-graph, guidance-context, and record-detail views are projections over the same facts. Visual hierarchy, contextual references, and navigation grouping never become checked lineage or require a new core record shape.
- Every record, support reference, measured input, source target, destination, and temporary sibling crosses the blessed confined-filesystem boundary.
- The HTML is one disposable offline file with embedded data and no runtime file or network reads.
- Unsafe or malformed admitted records fail the whole operation; partial truth is not published.
- Initial browser performance evidence targets desktop Chrome only and records its exact version.
- No runtime dependency, durable index, hosted service, background process, or top-level directory is added without approval.

## Construction tests

**Integration tests:**

- Query/HTML differential proof over the same corpus for membership, exact status, checked lineage, unresolved counts, provenance, and policy-boundary copy (**AC-0008, AC-0021**).
- Built and installed pack proof for replacement activation and removal of operative `rfc-status` surfaces (**AC-0017–AC-0019**).

**Manual verification:**

- Offline Chrome review for keyboard access, visible focus, high-zoom reflow, reduced-motion handling, required states, source labelling, support references, and no double-click dependency (**AC-0011–AC-0016, AC-0021**).
- The benchmark schedule named only in **AC-0015**, with thresholds frozen before measurement.
- The frozen comparative evidence required by **AC-0020**.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| User procedure and product documentation | T5 | Guide examples, link checks, installed documentation | `close-work` confirms current public navigation and no stale operative name |
| Pack promise and journey | T5 | Reviewed README and journey against shipped behavior | Durable surfaces name the same boundaries and workflow |
| Architecture | T5 | Design review against RFC-0105, CAP-0002, `docs/architecture/decision-graph.md`, and implementation controls | Read-only, on-demand, multi-form, checked-lineage, reference-policy, and safe-publication truth remains current |
| Pack registration and generated projections | T4 | Activation evaluation, build, and install results | Installed pack exposes `navigate-decisions` and no operative `rfc-status` |
| Executable proof | T1-T4 | Targeted tests and evaluation fixtures | Every criterion has named passing evidence |
| Verification ledger | T3, T6 | Chrome measurements, interaction review, destination checks, and task-panel results | Ledger records thresholds, exact version, results, and final representation rule |
| Release history | T5 | Owning changelog or release note | Shipped version and compatibility change are discoverable |

## Design (LLD)

### Design decisions

Query and HTML derive from the same confined canonical reads and are compared at the fact boundary. Output adapters may use different internal representations and do not have to share rendering code. Traces to **AC-0008, AC-0012, AC-0014**.

Owned by: T2, T3

### Data & schema

`decision-navigation.query.v1` is the only versioned public payload fixed by the contract. The spec's Corpus and query contract owns its exact operations, selectors, bounds, ordering, success and refusal envelopes, oversized-body behavior, and projection fields. Implementation tasks verify that contract without restating its values here. Exact raw source values remain separate from safely escaped human display values. The ephemeral internal model and HTML-internal data shape remain implementation choices. Traces to **AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0006, AC-0007, AC-0008**.

Owned by: T2, T3

### State & control flow

The observable flow is discover every candidate matching the spec's exact roots and basename rules, validate the whole admitted corpus, build checked facts, answer a bounded query or estimate an export, validate the final publication boundary, write a temporary sibling, and publish atomically. Any unsafe, duplicate, identity-changing, or malformed candidate stops before a success payload or destination is produced. Traces to **AC-0001, AC-0007, AC-0009, AC-0013, AC-0022**.

Owned by: T2, T3

### Behavior & rules

Only reciprocal explicit supersession metadata creates checked lineage. Guidance direction requires an admitted directional fact or explicit caller assertion; caller assertions remain non-authoritative navigation inputs, and other similarities stay neutral. Query and HTML preserve record kind and exact lifecycle values, keep weaker evidence unresolved, label snapshot versus latest source handoff, and state that recorded constraints are not complete applicable policy. Traces to **AC-0004, AC-0005, AC-0006, AC-0011, AC-0021, AC-0023**.

Owned by: T2, T3

### Failure, edge cases & resilience

Malformed records, duplicate identifiers, contradictory or missing endpoints, unsafe inputs or destinations, budget refusal, existing output, and interrupted publication produce stable fail-closed results. Bounded mode is an explicit representation, not a partial-failure fallback. Traces to **AC-0005, AC-0007, AC-0009, AC-0013, AC-0014, AC-0022**.

Owned by: T1, T2, T3

### Quality attributes (NFRs)

Security is proven by hostile-content and confined-filesystem tests; accessibility by keyboard and focus review; portability by offline Chrome review; cross-view integrity by parity and trust-label tests; and scalability by the predeclared measurements in AC-0015. Exact thresholds, parser, renderer, search, graph, styling, and component choices remain implementation-discovered. Traces to **AC-0008, AC-0009, AC-0010, AC-0011, AC-0012, AC-0013, AC-0014, AC-0015, AC-0016, AC-0022, AC-0023**.

Owned by: T1, T3, T6

### Dependencies & integration

The feature uses the repository's blessed confined-filesystem helpers and the existing pack build, install, and evaluation paths. It adds no external service or runtime dependency. Traces to **AC-0009, AC-0017, AC-0018, AC-0019, AC-0022**.

Owned by: T2, T4

## Tasks

### T1 — Decision contract fixtures fail for the absent capability

**Depends on:** none

**Touches:** `packs/governance-extras/tests/skills/navigate-decisions/**`, `packs/governance-extras/.apm/skills/navigate-decisions/**`

**Verification mode:** TDD — `packs/governance-extras/tests/skills/navigate-decisions/test_query_contract.py` and the mixed fixture corpus.

**Tests:**

- Freeze positive fixtures for the admitted population defined by the spec's Corpus and query contract, mixed ADR/RFC records, full and partial supersession, exact and qualified statuses, contextual references, caller-supplied guidance direction, neutral navigation groupings, supporting references, constraints, and snapshot/latest provenance (**AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0006, AC-0007, AC-0008, AC-0011, AC-0021, AC-0023**).
- Freeze negative fixtures for candidate-shaped malformed files, duplicate kind-plus-ordinal identities, unsupported or missing query selectors, every query bound, one-sided or contradictory lineage, missing endpoints, false guidance direction, active content, instruction-shaped agent data, bidirectional and non-printing visual spoofing, traversal, links, special files, duplicate identity, and identity change (**AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0006, AC-0007, AC-0009, AC-0010**).
- Prove the first targeted run is red because query behavior is absent, not because the fixture is empty or broken.

**Approach:** Use a checked-in mixed fixture root and a minimal executable seam. The first compilable red assertion is:

```python
import json
import subprocess
import sys
from pathlib import Path


SCRIPT = Path(
    "packs/governance-extras/.apm/skills/navigate-decisions/"
    "scripts/navigate_decisions.py"
)
FIXTURE = Path(
    "packs/governance-extras/tests/skills/navigate-decisions/fixtures/mixed"
)


def test_query_keeps_partial_lineage_checked_and_bodies_bounded() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "query",
            "--root",
            str(FIXTURE),
            "--record",
            "ADR-0001",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["schema"] == "decision-navigation.query.v1"
    assert payload["records"][0]["id"] == "ADR-0001"
    assert payload["records"][0]["body"] is None
    assert payload["records"][0]["checked_lineage"] == [
        {
            "relation": "superseded-in-part-by",
            "target": "ADR-0020",
            "scope": "D3",
        }
    ]
```

**Done when:** The positive fixture validates, every negative fixture reaches its intended boundary, and the contract test fails only on the absent query behavior.

### T2 — Bounded query proves exact facts and checked lineage

**Depends on:** T1

**Touches:** `packs/governance-extras/.apm/skills/navigate-decisions/**`, `packs/governance-extras/tests/skills/navigate-decisions/**`

**Verification mode:** TDD — `packs/governance-extras/tests/skills/navigate-decisions/test_query_contract.py` and `test_filesystem_safety.py`.

**Tests:**

- Prove exact candidate admission and every operation, selector, ordering rule, bound, refusal, oversized-body behavior, and envelope owned by the spec's Corpus and query contract; also prove raw-versus-display lifecycle fidelity, explicit detail, stable errors, checked full and partial edges, contextual and unresolved evidence, provenance, trust classes, and reference-policy-boundary output (**AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0006, AC-0007, AC-0021, AC-0023**).
- Prove all reads are confined, hostile values remain schema-safe untrusted data in the serialized query, and the owned skill-consumption seam cannot let instruction-shaped fixture values change scope, workflow, permissions, or tool use (**AC-0009–AC-0010**).

**Approach:** Resolve parser and module boundaries from established Governance Extras conventions during implementation. The seam must add no runtime dependency, must preserve exact source bodies separately from parsed navigation facts, and is killed if it cannot fail the whole operation on an unsafe or malformed admitted record.

**Done when:** The T1 contract suite is green; every success and refusal variant is covered; and no accepted query path reads outside the confined canonical corpus, silently truncates, obeys record-controlled instructions, or claims complete applicable policy.

### T3 — Offline publication is safe, reviewable, and evidence-sized

**Depends on:** T2

**Touches:** `packs/governance-extras/.apm/skills/navigate-decisions/**`, `packs/governance-extras/tests/skills/navigate-decisions/**`, `docs/specs/decision-navigation/notes/verification-ledger.md`

**Verification mode:** TDD plus goal-based and visual/manual QA — `test_html_publication.py` and `docs/specs/decision-navigation/notes/verification-ledger.md`.

**Tests:**

- Compare normalized record facts and complete relationship tuples across query, list, lifecycle-graph, guidance-context, and record-detail views and prove hostile record content cannot enter active sinks (**AC-0008, AC-0010, AC-0023**).
- Refuse unsafe sources and destinations, untrusted or non-allowlisted remote mappings, existing outputs, interruption, and over-budget publication without partial output (**AC-0009, AC-0011, AC-0013, AC-0022**).
- Prove full and bounded self-containment, disclosed omissions, and snapshot-versus-latest source labelling (**AC-0011, AC-0012, AC-0013, AC-0014**).
- Record the Chrome evidence required by **AC-0015** and inspect every state, view transition, trust label, and interaction required by **AC-0016** and **AC-0023**, including their zoom and motion-preference requirements.

**Approach:** Select renderer, Markdown handling, graph, search, CSS, and HTML-internal data shape during implementation from established dependencies and browser evidence. Reject any design that needs a network or adjacent-file read, cannot keep record content inert, or cannot validate and publish atomically inside the approved destination boundary.

**Done when:** Publisher tests pass and the ledger supports one explicit representation rule with complete Chrome, multi-form interaction, trust-label, source-link, reference-policy-boundary, and destination-safety evidence.

### T4 — Replacement activation and installed pack remain correctly separated

**Depends on:** T2

**Touches:** `packs/governance-extras/pack.toml`, `packs/governance-extras/.apm/skills/navigate-decisions/evals/eval_queries.json`, `packs/governance-extras/.apm/skills/rfc-status/**`, owned generated projections

**Verification mode:** TDD and goal-based build/install checks — `packs/governance-extras/.apm/skills/navigate-decisions/evals/eval_queries.json` and owned build outputs.

**Tests:**

- Route migrated `rfc-status` prompts and new landscape, lineage, broader-or-narrower guidance, provenance, constraint, and explorer prompts to `navigate-decisions` (**AC-0017**).
- Keep creation and revision prompts routed to `new-adr` and `new-rfc` (**AC-0018**).
- Build and install the pack with `navigate-decisions` and no operative `rfc-status` surface (**AC-0019**).

**Done when:** Activation evaluations, pack build, and installed-surface checks are green before the predecessor skill is removed.

### T5 — Durable product, architecture, guide, and release truth matches the capability

**Depends on:** T3, T4

**Touches:** `packs/governance-extras/README.md`, `packs/governance-extras/DESIGN.md`, `packs/governance-extras/JOURNEY.md`, `packs/governance-extras/docs/index.md`, `guides/governance-extras/**`, owning release surface

**Verification mode:** Goal-based documentation review — `guides/governance-extras/how-to/navigate-decisions.md`, pack build output, and operative-surface search results.

**Tests:**

- Resolve all changed links and examples and prove public surfaces use the current capability name (**AC-0017, AC-0019**).
- Review durable text for ADR/RFC separation, on-demand derivation, multi-form views, checked versus contextual relationships, offline and bounded behavior, snapshot/latest source handoff, safe publication, and the complete-policy warning (**AC-0008, AC-0009, AC-0010, AC-0011, AC-0012, AC-0013, AC-0014, AC-0018, AC-0021, AC-0022, AC-0023**).

**Done when:** Every durable output mapped to T5 matches shipped behavior, the owning release surface records the replacement, and operative-surface search finds no stale `rfc-status` guidance outside allowed history.

### T6 — Measured outcome evidence and completion gates pass

**Depends on:** T3-T5

**Touches:** `docs/specs/decision-navigation/notes/verification-ledger.md`, corrections required by observed failures

**Verification mode:** Goal-based and manual comparative evidence — `docs/specs/decision-navigation/notes/verification-ledger.md`.

**Tests:**

- Freeze the comparison tasks and measurement rules before sessions, then run the session mix and score the outcome exactly as **AC-0020** defines.
- Confirm the ledger, targeted tests, activation evaluations, documentation checks, build/install proof, repository lint, and contract-item alignment cover every open criterion named by the preceding tasks.

**Done when:** The comparative thresholds in **AC-0020** pass, every accepted criterion has named evidence, and every required gate passes.

## Rollout

- **Delivery:** Ship the new capability and its positive/negative activation coverage before removing `rfc-status`. Rollback restores the prior pack registration and documentation; generated HTML is disposable and needs no migration.
- **Infrastructure:** None.
- **External-system integration:** None. Source links depend only on a reviewed repository-to-HTTPS mapping and degrade to inert repository-relative provenance.
- **Deployment sequencing:** Do not dispatch implementation until RFC-0105 and the reshaped CAP-0002 are accepted. During implementation, T4 proves the replacement before removal, T5 aligns durable truth, and T6 closes evidence.

## Risks

- Dense graph presentation can imply certainty beyond the checked records; contradictory fixtures and unresolved-evidence styling are reviewed before graph prominence is accepted.
- Browser scale can invalidate a preferred full representation; thresholds are fixed before measurement and bounded mode remains a first-class result.
- Record text can cross active browser or agent sinks; hostile fixtures cover both output modes before publication is accepted.
- A latest-branch source link can drift from the export; snapshot links are preferred and any latest link carries an explicit warning.
- Replacing a familiar skill name can divert authoring prompts; migration positives and authoring negatives land before retirement.

## Changelog

- 2026-10-03 — Spec approved (scope decision) by the repository owner.
- 2026-10-03 — Plan approved (build-strategy decision) by the repository owner.
