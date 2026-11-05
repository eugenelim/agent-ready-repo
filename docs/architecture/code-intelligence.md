# Code intelligence

Core answers repository questions from live search by default and can add
evidence from any code-intelligence capability the host already exposes. No
provider is required, no provider is registered, and every provider answer is
labelled and checked against source before it can satisfy a required condition.

The optional `code-intelligence` pack is one such provider: it teaches an agent
to query an index built by the Wicked Estate CLI, read-only. Core and the pack
never depend on each other.[^1]

## 1. Two seams in Core own provider use

Provider handling lives in two Core skills and nowhere else. Consuming
workflows (`work-loop`, spec authoring, review, debugging, implementation) hold
no provider logic.[^2]

| Seam | Question it owns | Baseline without a provider |
| --- | --- | --- |
| `repository-grounding` | "What already governs these paths?" Seed-bounded probes over a change's touched paths | Probes report governing files, references, phrase pins, gates, co-change partners, and dead links, and report without deciding |
| `repository-exploration` | An open question about behavior, dependencies, impact, or context | Repository search, with load-bearing claims checked against source |

Both seams share one posture:

- **Selection.** Consider only capabilities already exposed by the host: host
  metadata, installed skills, effective repository guidance, explicit user
  selection, and native language, editor, or navigation surfaces. Hidden
  configuration, arbitrary local executables, and inferred endpoints are outside
  the set. Select by semantic fit and call the provider in its native shape.
- **No common contract.** Core defines no provider schema, registry, broker,
  transport, capability vocabulary, or lifecycle state.
- **Attribution.** Provider evidence is labelled apart from repository source,
  and every material limit the provider reports (depth cut, staleness,
  truncation) is preserved.
- **Verification.** A load-bearing provider conclusion is checked against the
  governing source, test, contract, or record. Unchecked claims are labelled
  unresolved and cannot be sole proof of a required condition. A provider claim
  that conflicts with a governing source is recorded as a conflict.
- **Fallback.** An absent, poorly fitted, refused, timed-out, or malformed
  provider returns the inquiry to the baseline without surfacing a provider
  error as a grounding failure.
- **Disclosure.** A provider receives only what the bounded question needs.
  Permission to call is not permission to upload the repository or let the
  provider persist content.
- **Locators.** A file locator a provider returns is read only through the
  skill's `read-locator.py`, which takes the locator base64-encoded and refuses
  with one of ten closed reasons. Approved roots come from the user or the
  calling workflow, never from provider output.[^3]

Neither seam installs, authenticates, registers, indexes, or refreshes a
provider, and neither uses a mutating provider action.[^4]

## 2. The `code-intelligence` pack is one read-only provider

The pack ships one skill, two forked-context subagents, and a preflight script.
It owns how to gather evidence well and nothing about what a workflow does with
it.[^5]

| Part | Role |
| --- | --- |
| `code-intelligence` skill | Evidence discipline and investigation patterns over an indexed code graph; preserves confidence, provenance, and unresolved-edge counts |
| `code-investigator` agent | Read-only investigation of a subsystem or behavior in a forked context; labels each claim observed, verified, or unestablished |
| `impact-analyst` agent | Change-impact analysis for one symbol, module, or file; states the graph's limits first |
| `scripts/estate_preflight.py` | Setup check: exit 0 ready, 2 binary missing, 3 no index, 4 binary below the 0.30 floor |

The skill holds one boundary: it describes the software estate (entities,
relationships, dependency structure, blast radius, hotspots, provenance) and never
a job performed on it. Migration phase, bug status, and review verdicts stay with
the calling workflow and are never written into the graph.[^6]

The skill is read-only by default. `annotate`, `semantics`, `index`, `scip`,
`evidence`, `tfstate`, `import-telemetry`, `compact`, and `watch` change the graph
or the working tree, and each needs the user's say-so first. Installation also
needs consent.[^6]

## 3. The provider's dependency is pinned and its limits travel with answers

The Wicked Estate CLI is a `cargo` runtime dependency pinned to 0.30.0
(`>=0.30`), and the adopter builds the index. The pack's preflight detects the
binary first and installs only on explicit consent and only when `cargo` is
already present. The MCP server `wicked-estate-mcp` is optional and off by
default, because it keeps 30 tool schemas resident in the agent's context for the
whole session.[^7]

A blast radius is never presented as complete when `unresolved` is non-zero or a
cursor remains. A heuristic edge is confirmed by repository search before it is
treated as fact. With no index, the agent falls back to repository search and
labels the result as search.[^6]

## 4. The composition has two proofs and one open trial

Core shows it completes alone, and the pack shows one provider shape working
through the seams.

- The no-provider path is the shipped default of both seams.[^2]
- The pack's `composition-example.md` walks one inquiry (which call sites must
  change before the signature of `parse_config` changes, and which could not be
  established) through the provider-fit path and the fallback path. The example
  is illustrative, not a contract.[^8]
- A six-question construction exercise covered two provider shapes (a graph CLI
  and editor language-server capabilities) without a shared schema.
  **STATUS: PLANNED** — guided real-world use of the pack on authorized legacy-app
  repositories, with a self-serve worksheet ([CAP-0011](../product/intents/CAP-0011-optional-code-intelligence-composition.md)).
  Blind selection and live generalization across provider shapes are not
  validated.[^9]

Whether graph assistance improves code review is unmeasured. The deferred
benchmark in `code-graph-review-benchmark` owns that question, and this page
makes no claim about it.[^10]

## 5. Governing records

- [RFC-0079 — Optional code intelligence through Core grounding and exploration](../rfc/0079-codebase-context-pack.md)
- [RFC-0104 — The `code-intelligence` pack](../rfc/0104-code-intelligence-pack.md)
- [ADR-0037 — Grounding is adopter- and org-supplied and presence-checked](../adr/0037-grounding-is-adopter-and-org-supplied-and-presence-checked-one-gate-from-infra-to-framework.md)
- [ADR-0097 — Knowledge access is capability-detected and provider-mediated](../adr/0097-knowledge-access-capability-detected-provider-mediated.md)
- Intents [CAP-0011](../product/intents/CAP-0011-optional-code-intelligence-composition.md) and [FEAT-0032](../product/intents/FEAT-0032-native-provider-selection-validation.md) own the open validation.

## 6. Last verified against commit

`3fe5f2760`, whole page, against `packs/core/.apm/skills/repository-grounding/`,
`packs/core/.apm/skills/repository-exploration/`, and `packs/code-intelligence/`
at version 0.1.10.

[^1]: `packs/core/pack.toml` carries no reference to `code-intelligence`; `packs/code-intelligence/README.md` ("Works with").

[^2]: `packs/core/.apm/skills/repository-grounding/SKILL.md` (Optional provider evidence); `packs/core/.apm/skills/repository-exploration/SKILL.md` (Exposed surfaces; Disclosure minimization; Never do).

[^3]: `packs/core/.apm/skills/repository-exploration/scripts/read-locator.py` and `.../repository-grounding/scripts/read-locator.py`; reasons listed under "Reading a provider-returned file locator" in `repository-exploration/SKILL.md`.

[^4]: `repository-exploration/SKILL.md` (Ask first before any of the following; Never do).

[^5]: `packs/code-intelligence/.apm/skills/code-intelligence/SKILL.md`; `packs/code-intelligence/.apm/agents/code-investigator.md` and `impact-analyst.md`.

[^6]: `packs/code-intelligence/.apm/skills/code-intelligence/SKILL.md` (The boundary this skill holds; Writes; Never do; Degrading without the graph).

[^7]: `packs/code-intelligence/pack.toml` (`[[pack.runtime-dependencies]]`); `scripts/estate_preflight.py`.

[^8]: `packs/code-intelligence/.apm/skills/code-intelligence/references/composition-example.md`; `packs/code-intelligence/tests/pack/test_composition_example.py`.

[^9]: [CAP-0011](../product/intents/CAP-0011-optional-code-intelligence-composition.md) (De-risking, validation hook); `docs/product/research/native-provider-selection-validation/instrument.md`; `guides/code-intelligence/tutorials/first-session.md`.

[^10]: [`code-graph-review-benchmark`](../product/intents/code-graph-review-benchmark.md).
