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
- Scripted Chrome check that record-ID search finds a record by full, lowercase, and bare-ordinal ID, and that the search box names what it searches (**AC-0027**).

**Manual verification:**

- Offline Chrome review for keyboard access, visible focus, high-zoom reflow, reduced-motion handling, required states, source labelling, support references, and no double-click dependency (**AC-0011–AC-0016, AC-0021, AC-0025, AC-0026**).
- The benchmark schedule named only in **AC-0015**, with thresholds frozen before measurement.
- The owner-run session and acceptance required by **AC-0020**.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| User procedure and product documentation | T5, T7, T9 | Guide examples, link checks, installed documentation | `close-work` confirms current public navigation and no stale operative name |
| Pack promise and journey | T5 | Reviewed README and journey against shipped behavior | Durable surfaces name the same boundaries and workflow |
| Architecture | T5, T7 | Design review against RFC-0105, CAP-0002, `docs/architecture/decision-graph.md`, and implementation controls | Read-only, on-demand, multi-form, checked-lineage, reference-policy, and safe-publication truth remains current |
| Pack registration and generated projections | T4, T7 | Activation evaluation, build, and install results | Installed pack exposes `navigate-decisions` and no operative `rfc-status` |
| Executable proof | T1-T4, T7, T9 | Targeted tests and evaluation fixtures | Every criterion has named passing evidence |
| Verification ledger | T3, T6, T7, T9 | Chrome measurements, interaction review, destination checks, the owner session, and the RFC-0099 cleanup record | Ledger records thresholds, exact version, results, and final representation rule |
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

Malformed records, duplicate identifiers, oversized inputs, unsafe inputs or destinations, budget refusal, existing output, and interrupted publication produce stable fail-closed results. One-sided, contradictory, or missing-endpoint lineage is unresolved evidence, not a failure. Bounded mode is an explicit representation, not a partial-failure fallback. Traces to **AC-0005, AC-0007, AC-0009, AC-0013, AC-0014, AC-0022**.

Owned by: T1, T2, T3

### Quality attributes (NFRs)

Security is proven by hostile-content and confined-filesystem tests; accessibility by keyboard and focus review; portability by offline Chrome review; cross-view integrity by parity and trust-label tests; and scalability by the predeclared measurements in AC-0015. Exact thresholds, parser, renderer, search, graph, styling, and component choices remain implementation-discovered. Traces to **AC-0008, AC-0009, AC-0010, AC-0011, AC-0012, AC-0013, AC-0014, AC-0015, AC-0016, AC-0022, AC-0023**.

Owned by: T1, T3, T6

### Dependencies & integration

The feature uses the repository's blessed confined-filesystem helpers and the existing pack build, install, and evaluation paths. Pack scripts run standalone from their projection, so the skill vendors a byte-identical copy of the blessed `file_safety.py` beside its scripts rather than reusing the pack-local `_record_paths.py`, which has no bounded read or hashing. A roster test, `tests/roster/test_navigate_decisions_file_safety_mirror.py`, pins the copy against `packs/core/.apm/skills/close-work/scripts/file_safety.py`, the declared source of truth, following the `architect-design` pin in `tests/roster/test_architect_design_reviewer_projection.py`. Pack tests may not read outside their pack (`tools/lint-pack-test-boundary.py`), and the `Makefile` test list is the runner that names the pack suite. It adds no external service or runtime dependency. Traces to **AC-0009, AC-0017, AC-0018, AC-0019, AC-0022**.

Owned by: T2, T4

## Tasks

### T1 — Decision contract fixtures fail for the absent capability

**Depends on:** none

**Touches:** `packs/governance-extras/tests/skills/navigate-decisions/**`, `packs/governance-extras/.apm/skills/navigate-decisions/**`, `packs/agent-skill-engineering/tests/fixtures/skill-census.json`

**Verification mode:** TDD — `packs/governance-extras/tests/skills/navigate-decisions/test_query_contract.py` and the mixed fixture corpus.

**Tests:**

- Freeze positive fixtures for the admitted population defined by the spec's Corpus and query contract, mixed ADR/RFC records, full and partial supersession, exact and qualified statuses, contextual references, caller-supplied guidance direction, neutral navigation groupings, supporting references, constraints, and snapshot/latest provenance (**AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0006, AC-0007, AC-0008, AC-0011, AC-0021, AC-0023**).
- Freeze negative fixtures for candidate-shaped malformed files, duplicate kind-plus-ordinal identities, unsupported or missing query selectors, every query bound, one-sided or contradictory lineage, missing endpoints, false guidance direction, active content, instruction-shaped agent data, bidirectional and non-printing visual spoofing, traversal, links, special files, duplicate identity, and identity change (**AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0006, AC-0007, AC-0009, AC-0010**).
- Prove the first targeted run is red because query behavior is absent, not because the fixture is empty or broken.

**Approach:** Use a checked-in mixed fixture root and a minimal executable seam. The first compilable red assertion is:

```python
import importlib.util
import pathlib
import sys

sys.dont_write_bytecode = True
HERE = pathlib.Path(__file__).resolve().parent
SCRIPTS = HERE.parents[2] / ".apm/skills/navigate-decisions/scripts"
FIXTURE = HERE / "fixtures/mixed"
SPEC = importlib.util.spec_from_file_location(
    "governance_extras_navigate_decisions", SCRIPTS / "navigate_decisions.py"
)
NAV = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(NAV)


def test_record_returns_body_and_checked_partial_lineage() -> None:
    payload = NAV.run_query(FIXTURE, {"operation": "record", "id": "ADR-0001"})

    assert payload["schema"] == "decision-navigation.query.v1"
    assert payload["status"] == "ok"
    record = payload["records"][0]
    assert record["id"] == "ADR-0001"
    assert record["body"]["available"] is True
    expected = {
        "from": "ADR-0020",
        "relation": "supersedes_in_part",
        "to": "ADR-0001",
        "scope": ["D3"],
        "trust_class": "checked",
        "resolution_state": "resolved",
    }
    assert any(expected.items() <= r.items() for r in payload["relationships"])
```

**Done when:** The positive fixture validates, every negative fixture reaches its intended boundary, and the contract test fails only on the absent query behavior.

### T2 — Bounded query proves exact facts and checked lineage

**Depends on:** T1

**Touches:** `packs/governance-extras/.apm/skills/navigate-decisions/**`, `packs/governance-extras/tests/skills/navigate-decisions/**`, `tools/repo/build_gate_chain.py`, `Makefile`, `tests/roster/test_navigate_decisions_file_safety_mirror.py`, `.github/workflows/build-check.yml`, `tools/lint-ci-parity.py`

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

**Touches:** `packs/governance-extras/pack.toml`, `packs/governance-extras/.claude-plugin/plugin.json`, `packs/governance-extras/.apm/skills/navigate-decisions/evals/eval_queries.json`, `packs/governance-extras/.apm/skills/rfc-status/**`, `packs/agent-skill-engineering/tests/fixtures/skill-census.json`, `tools/add-rendering-directives.py`, `tests/roster/test_conventions_retirement.py`, `packs/iac-terraform/pack.toml`, `packs/iac-terraform/.claude-plugin/plugin.json`, owned generated projections

**Verification mode:** TDD and goal-based build/install checks — `packs/governance-extras/.apm/skills/navigate-decisions/evals/eval_queries.json` and owned build outputs.

**Tests:**

- Route migrated `rfc-status` prompts and new landscape, lineage, broader-or-narrower guidance, provenance, constraint, and explorer prompts to `navigate-decisions` (**AC-0017**).
- Keep creation and revision prompts routed to `new-adr` and `new-rfc` (**AC-0018**).
- Keep intent-hierarchy and intent-status prompts out of `navigate-decisions` (**AC-0024**).
- Build and install the pack with `navigate-decisions` and no operative `rfc-status` surface (**AC-0019**).

**Done when:** Activation evaluations, pack build, and installed-surface checks are green before the predecessor skill is removed.

### T5 — Durable product, architecture, guide, and release truth matches the capability

**Depends on:** T3, T4

**Touches:** `packs/governance-extras/README.md`, `packs/governance-extras/DESIGN.md`, `packs/governance-extras/JOURNEY.md`, `packs/governance-extras/docs/index.md`, `guides/governance-extras/**`, `web/src/content/journeys/governance-extras.md`, `docs/architecture/decision-graph.md`, `docs/product/changelog.md`

**Verification mode:** Goal-based documentation review — `guides/governance-extras/how-to/navigate-decisions.md`, pack build output, and operative-surface search results.

**Tests:**

- Resolve all changed links and examples and prove public surfaces use the current capability name (**AC-0017, AC-0019**).
- Review durable text for ADR/RFC separation, on-demand derivation, multi-form views, checked versus contextual relationships, offline and bounded behavior, snapshot/latest source handoff, safe publication, and the complete-policy warning (**AC-0008, AC-0009, AC-0010, AC-0011, AC-0012, AC-0013, AC-0014, AC-0018, AC-0021, AC-0022, AC-0023**).

**Done when:** Every durable output mapped to T5 matches shipped behavior, the owning release surface records the replacement, and operative-surface search finds no stale `rfc-status` guidance outside allowed history.

### T7 — Explorer redesign and post-gates review corrections

**Depends on:** T1-T5

**Touches:** `packs/governance-extras/.apm/skills/navigate-decisions/**`, `packs/governance-extras/tests/skills/navigate-decisions/**`, `packs/governance-extras/pack.toml`, `packs/governance-extras/DESIGN.md`, `guides/governance-extras/how-to/navigate-decisions.md`, `docs/specs/decision-navigation/notes/verification-ledger.md`, owned generated projections

**Verification mode:** TDD for query and publication corrections; visual/manual QA for the redesign — `test_query_contract.py`, `test_html_publication.py`, and scripted desktop Chrome evidence in the verification ledger.

**Tests:**

- Close every finding in the T7 corrections table of `docs/specs/decision-navigation/notes/verification-ledger.md` by its listed mode (**AC-0001–AC-0014, AC-0016, AC-0019, AC-0021–AC-0023**).
- Closure modes and their pass conditions:
  - failing test: a test fails on the defect and passes after the fix.
  - scripted Chrome check: a check in the scripted desktop-Chrome evidence run fails on the defect and passes after the fix.
  - document change: the corrected text is re-read against shipped behaviour and agrees with it.
  - mutation red: the new or strengthened test fails against a recorded mutation that reintroduces the defect and passes on the fixed code.
  - lint or search: a named lint or search command finds the item before the fix and nothing after it.
  - ledger deviation: the correction to a completed task's text is recorded in the ledger's deviations section.
- The T7 corrections table in the ledger holds exactly these 58 findings, each closed by the mode named here. Within that table only each row's Status may change; any change to this set, a mode, or a pass condition needs a controlled amendment. The rest of the ledger stays open for evidence:
  - failing test (30): ADV-1, ADV-2, ADV-3, ADV-4, ADV-5, ADV-6, ADV-7, ADV-8, ADV-9, ADV-10, ADV-13, ADV-17, ADV-18, ADV-19, SEC-1, SEC-2, SEC-3, SEC-4, SEC-5, SEC-7, SEC-8, QE-1, QE-2, QE-3, QE-4, QE-6, QE-7, QE-12, QE-13, QE-20
  - document change (7): ADV-11, ADV-12, ADV-14, ADV-20, SEC-6, QE-15, QE-17
  - mutation red (8): ADV-15, QE-5, QE-8, QE-9, QE-10, QE-11, QE-16, QE-21
  - ledger deviation (1): ADV-16
  - scripted Chrome check (10): QE-14, FE-F1, FE-F4, FE-F2, FE-F3, FE-F5, FE-F6, FE-F9, FE-F10, FE-F11
  - lint or search (2): QE-18, QE-19
- Prove safe Markdown rendering with the scripted Chrome check on a hostile-fixture export: allowlisted elements only, text nodes only, inert links, unloaded images, literal raw HTML, visible escaping of link targets and image alt text, the 32-level nesting fallback, the 2 MiB pathological-body render within 2 seconds without a stack error, the computed-style separation of the record-content container and its headings from trust cues, and a test that reads the emitted content security policy (**AC-0010**).
- Prove superseded-by markers in list and detail and their links (**AC-0025**), and the SVG lineage diagram, folded contextual edges, chain atlas, keyboard focus, and text equivalent (**AC-0026**).
- Re-run the AC-0015 and AC-0016 Chrome scripts from any checkout with no personal path, and record the export command and captured output.

**Approach:** The visual direction follows the supplied review-pack reference: a centred column, a header with an eyebrow label and gradient title, stat cards, pill filters, and card rows; trust classes carry an evidence rail of solid, dashed, dotted, and double left borders with written labels. CSS and JavaScript live as files beside the explorer and are inlined at export, with the script hash computed from the inlined bytes. The lineage diagram layers only checked supersession relationships with longest-path layering after collapsing cycles into one layer, orders each layer by barycenter, and builds SVG with `createElementNS`.

**Done when:** Every row of the T7 corrections table is closed by its listed mode and marked closed, the Chrome evidence is re-recorded, and the T3 and T5 gates still pass.

### T8 — Round-4 review corrections and the header and selector amendment

**Depends on:** T7

**Touches:** `packs/governance-extras/.apm/skills/navigate-decisions/**`, `packs/governance-extras/tests/skills/navigate-decisions/**`, `guides/governance-extras/how-to/navigate-decisions.md`, `docs/specs/decision-navigation/notes/verification-ledger.md`, owned generated projections

**Verification mode:** TDD for query, parsing and publication; scripted desktop Chrome checks for the explorer — `test_query_contract.py`, `test_html_publication.py`, `browser_checks.py`, and the verification ledger.

**Tests:**

- Close each of the 20 findings sustained by the fourth post-gates review by the mode below, using the pass conditions defined under T7, and record each closure in the ledger's "Round-4 review corrections" section, a table with the T7 table's columns (ID, Severity, Finding, Closes by, Status). Within that section only each row's Status may change; any change to this set, a mode, or a pass condition needs a controlled amendment.
  - R4-ADV-1 (document change): the spec and the guide state that a selector whose only key is a caller grouping is refused with `invalid_selector`, matching the shipped refusal.
  - R4-ADV-2 (scripted Chrome check): detail shows the Status header field's row when its carried value, with one trailing HTML comment and trailing whitespace removed, differs from the lifecycle `raw_value`, as for a wrapped Status; a one-line Status shows a single Status row.
  - R4-ADV-3 (failing test): a wrapped supersession field yields an entry for every identity in its whole extent.
  - R4-ADV-4 (scripted Chrome check): see R4-FE-1 and R4-FE-2.
  - R4-ADV-5 (document change): the QE-11 row records the round-3 closure, and the R2-EXP-1 row names only the links a check measures.
  - R4-ADV-6 (failing test): a bounded export keeps a multi-line header value exactly; the swap-test docstring describes both phases.
  - R4-SEC-1 (failing test): the AC-0001 admission-time condition holds.
  - R4-FE-1 (scripted Chrome check): no two `in part` label plates intersect, and no plate intersects a node box or an arrowhead box, in the focused graph and the atlas, on a fixture where four partial edges enter one node.
  - R4-FE-2 (scripted Chrome check): full and partial edge arrowheads have the same rendered size.
  - R4-FE-3 (scripted Chrome check): a caller-asserted edge between two chain members in one column with a node between them has no point inside any other node's box, and its `asserted` label plate intersects no node box, arrowhead box or other label plate.
  - R4-FE-4 (scripted Chrome check): on a view without sections, activating Expand all leaves its label unchanged.
  - R4-FE-5 (scripted Chrome check): text-list node buttons align to the top of their list item.
  - R4-QE-1 (failing test): after a refused publication at either phase, neither the validated nor the swapped-in directory holds a file of any name.
  - R4-QE-2 (failing test): a swap before the link is refused even when the link would otherwise succeed, so the case fails when the pre-link check is a no-op; the ADV-7 row states what each swap case proves.
  - R4-QE-3 (document change): see R4-ADV-5.
  - R4-QE-4 (scripted Chrome check): partial edges carry the hollow inner stroke and an `in part` label in both views, and differ from full edges.
  - R4-EXP-1 (scripted Chrome check): the node focus indicator reaches 3:1 against the canvas in both themes and does not touch the supersession ring.
  - R4-EXP-2 (scripted Chrome check): with scripts disabled and a dark system preference, the banner, info panel, form controls and title use their dark styles.
  - R4-EXP-3 (scripted Chrome check): see R4-FE-1.
  - R4-EXP-4 (scripted Chrome check): the partially superseded ID uses one underline style in the list, focused graph and atlas.
- A wrapped Status keeps its label-line lifecycle value and its whole header extent, a header whose only Status line is `- **Status**: Accepted` yields the lifecycle `raw_value` `Accepted` and never the missing-state marker, and a header holding both `**Status:**` and `**Status**:` is malformed, pinned in query tests (**AC-0001, AC-0006**).

**Done when:** All 20 round-4 findings are closed by their modes and marked closed in the ledger, the AC-0016 evidence and the AC-0022 case-variant run are recorded on a commit containing T8's final code, and the T3 and T5 gates still pass.

### T9 — Record-ID search and the owner session's source cleanup

**Depends on:** T8

**Touches:** `packs/governance-extras/.apm/skills/navigate-decisions/scripts/explorer.py`, `packs/governance-extras/.apm/skills/navigate-decisions/scripts/explorer_assets/explorer.js`, `packs/governance-extras/tests/skills/navigate-decisions/browser_checks.py`, `guides/governance-extras/how-to/navigate-decisions.md`, `docs/rfc/0099-cut-before-adding-and-artifact-shaping.md`, `docs/specs/decision-navigation/notes/verification-ledger.md`, owned generated projections

**Verification mode:** Scripted desktop Chrome check for the search; record-index check for the RFC edit — `browser_checks.py`, `index-records.py --check docs/rfc`, and the verification ledger.

**Tests:**

- A scripted Chrome check types `ADR-0098`, `adr-0098`, `98`, and `0098` in turn on an export holding ADR-0098 and RFC-0098, and each leaves ADR-0098 in the results; `0098` and `98` also leave RFC-0098. A title-only term still matches as before, and a term that matches no ID, title, or status shows the no-result state (**AC-0027**).
- The same check reads the search box's visible label or hint and its accessible name, and both name IDs, titles, and statuses (**AC-0027**).
- Owner-directed source cleanup, outside any criterion: RFC-0099's Status reads exactly `Accepted`. Its `Related` list gains one last item, a link to ADR-0111 followed by "supersedes in part § 5's intent-mode rubric and its single `Clean` | `Findings` result vocabulary; everything else stands", with that quoted text kept word for word; the list's closing "and" moves before the new item. `index-records.py --check docs/rfc` passes.
- The ledger records the RFC-0099 Status line and the new `Related` item as read back from the file after the edit, and notes beside the frozen AC-0020 panel, without editing it, that the task-2 key applies only to commits before this cleanup.

**Done when:** The search check passes, the RFC index check passes, and the ledger records the search result, the read-back RFC-0099 Status and `Related` item, and the task-2 key note.

### T6 — Owner-accepted outcome evidence and completion gates pass

**Depends on:** T3-T5, T7, T8, T9

**Touches:** `docs/specs/decision-navigation/notes/verification-ledger.md`; a correction outside the T1–T5 Touches returns through controlled plan amendment

**Verification mode:** Goal-based owner-session evidence — `docs/specs/decision-navigation/notes/verification-ledger.md`.

**Tests:**

- Record the owner-run session against the frozen panel, each usability finding with its disposition, and the owner's acceptance, exactly as **AC-0020** defines.
- Confirm the ledger, targeted tests, activation evaluations, documentation checks, build/install proof, repository lint, and contract-item alignment cover every open criterion named by the preceding tasks.

**Done when:** The ledger records the owner's accepted session for **AC-0020**, every accepted criterion has named evidence, and every required gate passes.

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
- 2026-10-03 — Amended before implementation from pre-EXECUTE review: RFC shape, status-comment rule, summary aggregates and findings-register counts, export destination, link encoding, caller-value inertness, input bound, AC-0020 scoring, AC-0024, history navigation, and complete Touches; then minimal shared ADR/RFC admission shape, register row rule, AC-0020 run unit, export mode and provenance controls, the RFC-0102 supersession grammar, `Related` field and reference grammar, unparseable-entry and unresolved-count rules, scope serialization, commit-bound case-insensitive evidence, the closed relationship value table, per-operation relationship sets, lineage directions, total relationship order with scope comparison, duplicate-entry and trimmed `raw_value` rules, and bounded canonical D-IDs, and decisive AC-0022 proofs. Owner decisions recorded in-session the same day.
- 2026-10-03 — Amended spec approved (scope decision) by the repository owner, including at most one Status field per header region.
- 2026-10-03 — Amended plan approved (build-strategy decision) by the repository owner.
- 2026-10-03 — Controlled amendment during T2: T2 Touches add `Makefile` and `tests/roster/test_navigate_decisions_file_safety_mirror.py`, because `lint-pack-test-boundary` requires a recognized runner and forbids pack tests that read outside their pack; and `.github/workflows/build-check.yml` and `tools/lint-ci-parity.py`, because `tests/AGENTS.md` requires a named roster step and its `STEP_DISPOSITION` entry. The roster test names no `docs/specs/` literal, so `.workspace-prune-protected.toml` does not apply. Owner authorized in-session.
- 2026-10-03 — Spec re-approved unchanged (scope decision) by the repository owner after the T2 amendment.
- 2026-10-03 — Amended plan approved (build-strategy decision) by the repository owner.
- 2026-10-04 — Controlled amendment during T4: T4 Touches add `packs/iac-terraform/pack.toml` and its `.claude-plugin/plugin.json`, because removing `rfc-status` makes governance-extras 1.0.0 and iac-terraform's `^0.11` dependency then fails `catalogue verify` (CAT-V-007). Owner authorized in-session.
- 2026-10-04 — Spec re-approved unchanged (scope decision) by the repository owner after the T4 amendment.
- 2026-10-04 — Amended plan approved (build-strategy decision) by the repository owner.
- 2026-10-04 — Controlled amendment after post-gates review: added T7 for the explorer redesign and all sustained review corrections; AC-0010 now admits safe Markdown rendering with parse, styling, escaping, and content-security-policy limits; added AC-0025 (supersession markers) and AC-0026 (visual lineage, chains, and cycles); T7 closes the tracked corrections table in the ledger. Owner authorized in-session.
- 2026-10-04 — Amended spec approved (scope decision) by the repository owner: Markdown in AC-0010, AC-0025, and AC-0026.
- 2026-10-04 — Amended plan approved (build-strategy decision) by the repository owner: T7 and its 58 pinned corrections.
- 2026-10-05 — Controlled amendment during review round 4 (`owner-session-2026-10-05-grouping-and-header-extent-amendment`): the spec states one extent for every header field's value and reads supersession entries from it, and refuses a selector whose only key is a caller grouping (owner decision the same day). T8 is added for the round-4 corrections; T6 now depends on T8.
- 2026-10-05 — Amended spec approved (scope decision) by the repository owner.
- 2026-10-05 — Amended plan approved (build-strategy decision) by the repository owner.
- 2026-10-07 — Controlled amendment after the owner's session: AC-0020 now takes the owner's recorded acceptance of an owner-run session on the frozen panel in place of the comparative effort thresholds; AC-0027 adds record-ID search; T9 adds that search and trims RFC-0099's Status to `Accepted`, with its partial-supersession note moved to `Related`; T6 depends on T9. Owner authorized in-session.
- 2026-10-07 — Amended spec approved (scope decision) by the repository owner.
- 2026-10-07 — Amended plan approved (build-strategy decision) by the repository owner.
