# RFC-0079: Optional Code Intelligence through Core Grounding and Exploration

- **Status:** Accepted
- **Author:** eugenelim
- **Approver:** eugenelim
- **Date opened:** 2026-08-03
- **Date closed:** 2026-10-04
- **Decision weight:** heavy
- **Related:** [RFC-0104](0104-code-intelligence-pack.md) (`code-intelligence`
  pack), [RFC-0076](0076-catalogue-contracts-composition-semantics-discovery.md)
  (optional pack integrations),
  [ADR-0037](../adr/0037-grounding-is-adopter-and-org-supplied-and-presence-checked-one-gate-from-infra-to-framework.md)
  (presence-checked grounding),
  [ADR-0097](../adr/0097-knowledge-access-capability-detected-provider-mediated.md)
  (capability-detected knowledge),
  [repository-grounding preservation](../product/briefs/repository-grounding-preservation.md),
  [grounding-probe extensions](../product/intents/grounding-probe-extensions.md),
  [internal repository topology](../product/briefs/internal-repo-topology.md), and
  [code-graph review benchmark](../product/intents/code-graph-review-benchmark.md)

## Reviewer brief

- **Decision:** Whether Core's existing repository-grounding and exploration
  seams may opportunistically use code-intelligence capabilities already
  exposed in the active environment, without depending on a provider or making
  providers conform to a catalogue-defined schema.
- **Recommended outcome:** Accept.
- **Change if accepted:**
  - Repository grounding and exploration become the composition seams for
    optional code intelligence.
  - Core stays complete when no code-intelligence capability is present.
  - The `code-intelligence` pack becomes the golden example, not the provider
    contract or the final catalogue of investigation patterns.
- **Affected surface:** Future Core grounding and exploration guidance, their
  evaluations, and optional integrations that supply repository evidence. This
  RFC changes no shipped skill by itself.
- **Stakes:** The decision shapes several future Core consumers and tool trust
  boundaries, but remains reversible because it introduces no runtime,
  provider protocol, persistent state, or required dependency.
- **Review focus:** Whether the proposed seam is open enough for CLI, MCP,
  language-server, editor-native, indexed, hosted, and future tools while still
  giving Core a safe and testable absence path.
- **Not in scope:** Selecting or installing a provider, standardizing provider
  data, proving that graph-assisted review is better, or prescribing a delivery
  sequence for downstream work.

## The ask

**Recommendation.** Accept repository grounding and exploration as Core's
provider-neutral composition seams. They may use suitable code-intelligence
capabilities already visible in the active environment, through each
provider's native interface. They must remain complete without those
capabilities.

**Why now.** RFC-0104 admitted the opt-in `code-intelligence` pack and proved
that indexed code evidence can answer useful repository questions. Core already
has path-seeded grounding probes and several workflows that explore code, but
there is no decision about how those surfaces should use optional intelligence.
Leaving the relationship undefined pushes provider checks into `work-loop`,
spec authoring, review, and debugging one at a time. That creates the coupling
this RFC is intended to avoid.

| ID | Question | Recommendation | Why | Decide by | Reviewer action |
| --- | --- | --- | --- | --- | --- |
| D1 | Where does optional code-intelligence composition live? | **In existing repository-grounding and exploration seams** | The seams already own how repository evidence is found. Workflow and authoring flows should consume evidence, not acquire provider-specific responsibilities | 2026-10-07 | Accept the ownership boundary or name the existing owner that should replace it |
| D2 | Is code intelligence required when available or absent? | **No. Presence permits an optional improvement; absence, failure, or poor fit preserves Core's repository-native baseline** | Optional tooling must not weaken a standalone Core install or turn availability into a new gate | 2026-10-07 | Confirm that the absence path preserves the baseline outcome and acceptance criteria |
| D3 | How does Core find eligible capabilities? | **Inspect only already-exposed, trusted surfaces and select by semantic task fit** | Active tool metadata, installed skills, effective repository guidance, explicit user selection, and host-native capabilities are discoverable without probing hidden state | 2026-10-07 | Confirm the discovery boundary |
| D4 | What must a provider implement? | **No catalogue-defined provider schema** | Providers come as CLIs, MCP tools, language services, indexes, hosted tools, and shapes not yet known. Core uses their native invocation and result form | 2026-10-07 | Reject any implied common command, transport, storage, request, result, or capability schema |
| D5 | What authority do RFC-0104 and its five investigation patterns have? | **Golden example only; illustrative, non-exhaustive, and expected to evolve** | They prove the seam and supply a first worked integration without freezing future repository questions or provider capabilities | 2026-10-07 | Confirm that this RFC neither subsumes nor canonizes the pack |
| D6 | Does this RFC sequence downstream delivery? | **No. It gives a conceptual composition model and validation boundaries only** | The owning briefs, intents, and future specs must decide what to deliver and in what order from current evidence | 2026-10-07 | Confirm downstream ownership |

## Problem & goals

For this RFC, **Core** means the repository's default `core` pack, which must
remain useful when installed alone. A **repository inquiry seam** is an
existing skill section, reference method, script, or other owned procedure
that decides how to gather evidence for a repository question. **Wicked
Estate** is the code-graph tool wrapped by the optional `code-intelligence`
pack; it is one provider, not a required dependency.

Core already performs two related kinds of repository inquiry.

**Repository grounding** asks what constrains a contemplated change: what owns
or governs a surface, what moves with it, what consumes it, what verifies it,
and what existing behavior must survive. The shipped grounding explorer is
path-seeded, bounded by those paths and their references, and advisory. A probe
reports evidence; it never decides.

**Repository exploration** asks how the software works: where behavior begins,
how it flows, what depends on a symbol or surface, what may be affected, and
which source should be read next. It appears across debugging, review,
authoring, architecture assessment, and ordinary implementation rather than as
one mandatory workflow phase.

Code-intelligence tools can improve both kinds of inquiry. A resolved reference
graph may answer a caller question better than text search. A build graph may
answer dependency reachability better than either. Git history may answer
co-change without understanding symbols. Repository guidance may directly name
an owner that no inferred graph can establish.

The missing decision is not which tool wins. It is where optional evidence
composition belongs and what stays true when tools differ or are absent.

### Goals

- Let Core use relevant code intelligence without depending on a named pack,
  binary, protocol, storage model, or output structure.
- Extend the existing grounding and exploration seams rather than adding
  provider logic to `work-loop`, spec authoring, or every consuming workflow.
- Preserve repository-native reads, searches, history, guidance, and mechanical
  probes as a complete baseline.
- Keep provider results attributed, bounded, and subordinate to governing
  repository authorities and the consuming workflow's scope.
- Allow the questions, starting points, and investigation strategies to evolve
  without amending this RFC.

### Non-goals

- A universal code-intelligence API, provider schema, tool registry, broker, or
  routing service.
- A required repository index, graph, daemon, MCP server, language server, or
  optional pack.
- Automatic provider installation, registration, authentication, indexing, or
  refresh.
- Moving repository-specific topology, ownership, preservation properties, or
  workflow decisions into a code-intelligence provider.
- Adding a code-intelligence phase or gate to `work-loop`, `new-spec`, review,
  or any other main flow.
- Ratifying the current investigation patterns as the complete or preferred
  set.
- Settling whether graph-assisted review produces better findings than
  repository-native targeted exploration.

## Proposal

### D1 — Compose at repository inquiry seams

Core workflows ask repository questions through the grounding or exploration
method that already owns the question. That method chooses how to gather
evidence. A workflow does not gain provider discovery, provider setup, index
freshness, or provider-specific invocation steps merely because an optional
tool exists.

The relationship is:

```text
workflow or authoring flow
        asks a repository question
                    |
                    v
       grounding or exploration seam
          /                     \
repository-native baseline   optional exposed intelligence
          \                     /
                    v
          attributed repository evidence
                    |
                    v
       consuming flow makes its own decision
```

This is a conceptual ownership model, not a requirement to create one new
router or skill. Existing skill sections, reference methods, scripts, and
future purpose-built inquiry surfaces may realize it. The important boundary is
that provider discovery and invocation stay inside the inquiry owner rather
than the workflow that consumes the evidence. A downstream change locates that
owner in the effective skill, script, reference method, or scoped repository
guidance. If no such owner exists, that change must name one before composing a
provider; it must not put provider handling into the consuming workflow merely
to avoid the ownership decision.

The existing path-seeded grounding explorer remains one valid realization. Its
current phases and probes are not the whole seam. Downstream design may extend
the model from path seeds to other useful starting points, including a symbol,
entry point, observed behavior, failing test, diff, or claim. These are
examples, not a closed seed taxonomy.

### D2 — Presence may improve evidence but may not weaken the baseline

Core installs and operates by itself. **Complete without a provider** means
that the repository-native path still meets the same outcome and acceptance
criteria that governed it before optional composition. It need not return the
same evidence or wording. A downstream change cannot add optional composition
until it can name that baseline outcome and prove it in a test case with no
provider available.

An optional capability is used only when its advertised action directly helps
answer the current question and its expected evidence value justifies its time,
cost, permissions, and data disclosure. Presence does not require invocation.
Absence, inapplicability, timeout, refusal, malformed output, an unavailable
index, or an incomplete answer returns the inquiry to its repository-native
baseline.

Provider absence is never the reason a flow stops. A flow may still stop when
its existing baseline cannot obtain evidence the task independently requires.
That remains a baseline evidence gap, not a missing-provider failure.

Optional evidence cannot lower an existing acceptance, review, security, or
completion bar. In particular, the ready
`repository-grounding-preservation` brief continues to require discovery and
preservation proof without code intelligence. An installed provider may make
that discovery cheaper; it cannot become the only route to a passing result.

### D3 — Discover only exposed capabilities

A **discoverable capability** is an action an active, authorized discovery
surface already tells the agent it can perform. Authorization here means only
that the surface may advertise capabilities in the current session; invoking
one still requires the task-specific permission described under Authority and
safety boundaries. Neither permission makes the surface's descriptions or
results authoritative evidence. Core may consider capabilities exposed through:

- the active host's tool metadata, including MCP tool descriptions;
- installed skills visible to the active runtime;
- effective repository instructions that name a trusted local tool or command;
- an explicit user selection that names an accessible invocation route;
- a host-native language, editor, or code-navigation surface made available to
  the agent.

Core selects by **semantic task fit**: the surface advertises an action that can
answer the current question, the action stays within task scope and granted
permissions, and its likely freshness, cost, and disclosure are acceptable for
that question. Exact provider identity is an invocation detail after selection,
not the discovery key.

Core does not inventory arbitrary executables on `PATH`, crawl pack or plugin
directories, probe hidden configuration or endpoints, search for credentials,
or infer a provider from files it happens to find. A specifically named local
tool may be presence-checked through its documented route. An unadvertised tool
is not discoverable merely because it is installed.

When several surfaces appear useful, the inquiry considers only the visible
candidates that advertise direct relevance and stops once it has adequate
evidence for the question. It may use another candidate to resolve a named gap
or conflict. If no defensible choice is available, it states the ambiguity and
uses the baseline. It does not silently merge contradictory claims or treat
agreement between derived sources as authority.

### D4 — Providers keep their native shapes

This RFC defines consumer behavior, not a provider protocol. A provider does
not need to implement common:

- capability names or an enumerated capability set;
- commands, prompts, parameters, or tool identifiers;
- CLI, MCP, LSP, editor, HTTP, file, or process transport;
- index, graph, database, cache, or freshness representation;
- request or result schema;
- provenance, confidence, completeness, or error fields.

The inquiry reads the provider's exposed description, invokes its native
surface, and interprets the returned evidence in that provider's own terms. If
the provider supplies provenance, confidence, unresolved edges, freshness, or
coverage limits, the inquiry preserves material caveats. If it does not, Core
does not invent them or reinterpret a text-search result as a resolved graph.

Whenever provider evidence is used, the inquiry's ordinary evidence-bearing
output — such as a response, report, review, or research note — names the
provider or surface, distinguishes its derived result from source, and preserves
material freshness, coverage, confidence, and unresolved-edge limits that the
provider exposes. The consuming output states any unresolved limit that could
change its conclusion. This creates no separate persistent record or response
envelope for providers.

RFC-0076 `[[pack.integrations]]` entries may document known pack composition and
fallbacks. They remain explanatory delivery metadata: they neither discover
runtime tools nor define the provider contract for this RFC.

ADR-0097 remains the stricter owner for its governed knowledge-corpus providers.
For code intelligence, this RFC states the applicable rules in full: discover
only actively exposed capabilities, keep their claims subordinate to repository
authority, treat absence as normal, do not inspect hidden configuration or
credentials, and surface material ambiguity. ADR-0097 is precedent for those
rules, not required reading to apply them here. Its portable skill, request,
result, corpus, manifest, and traversal contract do not extend to
code-intelligence providers.

### D5 — Use `code-intelligence` as the golden example

The opt-in `code-intelligence` pack is the first complete worked example:

- its skill owns how to gather indexed evidence, not the job being performed;
- its capability map translates a repository question to its provider's native
  surface;
- its evidence guidance preserves freshness, provenance, confidence, and
  unresolved-edge limits where the provider exposes them;
- its fallback labels repository search as a different evidence class;
- its investigation patterns show several ways a consumer can use the result.

Those properties make the pack useful for design, examples, and evaluations.
They do not make Wicked Estate, its commands, its graph, or the pack's five
current patterns normative.

The five patterns — understand an entity, analyze change impact, investigate
behavior, analyze architecture, and assemble task context — are a starting
set. New questions and strategies may be added, split, merged, or retired
without changing this RFC. Other providers may support only one of them, expose
different capabilities, or enable work the current pack does not anticipate.

RFC-0104 says the pack may retire if a provider-neutral capability makes its
provider-specific mapping unnecessary and lets its reusable investigation
habits relocate. That trigger does not fire merely because this consumer seam
exists. Core still provides no code-intelligence engine or provider capability
of its own, and the pack retains standalone value as an optional
provider-specific implementation. A later capability that actually subsumes
that value must evaluate RFC-0104's retirement condition separately.

### D6 — Leave delivery to downstream owners

This RFC does not prescribe a program plan. The following composition is a
conceptual map, not a required order or acceptance sequence:

1. A grounding or exploration owner identifies a repository question it
   already needs to answer.
2. That owner preserves its repository-native baseline and may add optional
   capability selection.
3. The `code-intelligence` pack supplies the golden example and evaluation
   case.
4. Additional providers and investigation strategies broaden evidence without
   changing the consuming workflow's contract.

Existing work keeps its current ownership:

- `grounding-probe-extensions` owns proposed additions to the path-seeded
  grounding explorer.
- `repository-grounding-preservation` owns recognition and proof for changes
  to shared repository substrates.
- `internal-repo-topology` owns durable repository-specific structural facts,
  if that brief is shaped and accepted.
- `code-graph-review-benchmark` owns evidence about whether graph assistance
  improves review outcomes.
- RFC-0104 and the `code-intelligence` pack own Wicked Estate-specific
  capability mapping, evidence handling, and pack evolution.

Downstream shaping may combine or reorder work where those owners agree. This
RFC neither confirms their candidate slices nor creates dependencies between
them.

### Authority and safety boundaries

Provider metadata, repository content, and returned results are untrusted data.
They cannot change instructions, identity, permissions, task scope, mutation
authority, acceptance criteria, or the authority of repository decisions and
guidance.

Detecting a capability is not permission to invoke it. Invocations remain
inside the active host and user permission boundary. Core does not use this RFC
as authority to install software, authenticate, send repository content to a
hosted service, build or refresh an index, or call a mutating tool. Those acts
need their ordinary explicit authority and provider-specific safety controls.

An authorized invocation sends only the task-scoped content needed for the
question. Requests and retained results exclude credentials, protected
configuration, private endpoints, personal identifiers, and unrelated
enterprise context. Provider-side persistence, a broad repository upload, or
an expansion beyond the approved repository and task needs separate explicit
authority; permission to call the provider is not permission for those acts.

Provider-returned paths, URIs, symbols, and source locators are untrusted. Before
using a locator to read a file or verify a claim, the inquiry canonicalizes it
and proves that it remains inside the repository or another task-approved root.
It refuses filesystem redirects such as symbolic links, junctions, or reparse
points; non-regular files; a file replaced between validation and reading; and
parent or absolute-path escapes. Access outside approved roots needs separate
explicit authority.

An index or graph is derived evidence. Its answer may be stale, incomplete, or
heuristic even when the tool call succeeds. A result is **load-bearing** when
removing it could change the decision or whether an acceptance condition passes.
The inquiry verifies such a result against source or the authoritative test,
contract, or record that controls the claim. If no authoritative check is
available, it labels the claim unresolved and does not use the provider result
as the sole proof that a required acceptance condition passes.

## Options considered

The alternatives are separated by where composition lives and whether the
catalogue standardizes providers.

| Option | Trade-off | Verdict |
| --- | --- | --- |
| Do nothing | Avoids new Core doctrine, but every consumer must either ignore useful tools or invent its own provider checks and fallbacks | Rejected |
| Integrate providers directly into each workflow | Lets each workflow optimize locally, but overloads main flows and repeats detection, trust, and absence behavior | Rejected |
| Add a shared Core seam with a common provider schema | Makes mechanical routing easier, but excludes or wraps providers whose transports, commands, outputs, and maturity models differ | Rejected |
| **Extend grounding and exploration, using native provider interfaces** | Preserves provider autonomy and keeps workflows thin; selection remains judgment-based and needs heterogeneous evaluations | **Recommended** |

A new central broker or tool registry was also rejected. It would turn a habit
of using available evidence into infrastructure, duplicate the active runtime's
tool surface, and create a mandatory availability and trust boundary.

## Risks & what would make this wrong

| Risk | Mitigation | What would change the answer |
| --- | --- | --- |
| Capability descriptions are too inconsistent for reliable semantic selection | Limit discovery to exposed surfaces, keep selection bounded, and test deliberately different provider shapes | Repeated evaluations show useful tools are routinely missed or unsuitable tools are invoked despite clear metadata |
| Optional intelligence becomes a hidden requirement | Preserve an explicit test case with no provider available and the pre-existing repository-native result for every evolved seam | A Core inquiry cannot complete without an optional provider |
| Main flows acquire provider ceremony through the back door | Keep discovery and invocation in grounding or exploration owners; review direct provider references in main workflow procedures | Multiple consumers need provider-specific lifecycle state that cannot be owned below them |
| A stale or incomplete graph produces confident but wrong evidence | Preserve provider caveats, distinguish evidence classes, and verify load-bearing conclusions against source or the authoritative test, contract, or record | Providers cannot expose enough limits for consumers to avoid systematically worse answers |
| The current five patterns freeze future inquiry | Mark every list illustrative and evaluate new questions without RFC amendment | Downstream governance treats the examples as a closed enum |
| Tool output changes agent authority or injects instructions | Treat descriptions and results as untrusted data and retain the consumer's instruction, permission, and scope boundary | A host cannot isolate tool data from instruction authority well enough to enforce that boundary |
| The design assumes graph assistance is beneficial without evidence | Keep use optional and preserve the separate controlled benchmark | The RFC begins requiring or preferring graphs before that benchmark supports the claim |

The principal drawback is that provider-neutral composition remains partly a
reasoning discipline. Without a common schema, some providers will be easier to
select and interpret than others. That cost is accepted because imposing a
schema would move interoperability work onto every provider and prematurely
freeze the capability space.

## Evidence & prior art

### Repository evidence

- The [grounding-probes survey](../product/research/repository-grounding-probes-survey.md)
  establishes the current seed-bounded, report-never-decide baseline and records
  why a whole-repository map is the wrong default for that grounding job. This
  RFC permits a bounded query to an existing index; it does not replace that
  baseline with a map.
- The [loop contract](../architecture/loop-contract.md#5-grounding-which-probes-run-when)
  stages grounding by the paths each stage knows and makes degraded inputs
  visible instead of silently clean.
- [ADR-0037](../adr/0037-grounding-is-adopter-and-org-supplied-and-presence-checked-one-gate-from-infra-to-framework.md)
  already requires optional grounding to be presence-checked, never mandated,
  and added by extending an existing gate rather than creating a parallel
  front door.
- [ADR-0097](../adr/0097-knowledge-access-capability-detected-provider-mediated.md)
  demonstrates capability-based selection, external authority anchoring,
  expected absence, bounded ambiguity, and refusal to probe hidden surfaces.
- [RFC-0104](0104-code-intelligence-pack.md) separates the provider, the habit
  of using its evidence, and the consuming workflow. Its current skill and
  investigation patterns provide the golden example for this RFC.
- The [repository-grounding preservation brief](../product/briefs/repository-grounding-preservation.md)
  states the compatibility invariant directly: optional capabilities may
  accelerate discovery, but their absence cannot weaken acceptance, review, or
  completion.
- The [code-graph review benchmark](../product/intents/code-graph-review-benchmark.md)
  records that current evidence does not establish improved review
  effectiveness and does not authorize requiring a graph provider.
- The [agent-authoring input-quality brief](../product/briefs/agent-authoring-input-quality.md#repository-grounding-is-a-developed-field-and-this-is-where-the-survey-competes)
  distinguishes retrieval from recognition and ownership. Code intelligence
  can supply evidence; it does not become an ownership declaration.

No open item in `docs/backlog.md` names this capability. Related queued work is
represented as intents or briefs in `workspace.toml`, not by a duplicate
backlog entry.

### External prior art

- The [Model Context Protocol tool specification](https://modelcontextprotocol.io/specification/2025-06-18/server/tools)
  lets clients discover native tools from their names, descriptions, and input
  schemas, while results may be structured or unstructured. It supplies one
  discovery surface, not a universal code-intelligence schema.
- The [MCP lifecycle specification](https://modelcontextprotocol.io/specification/2025-06-18/basic/lifecycle)
  negotiates optional capabilities and requires clients to use only negotiated
  features.
- The [Language Server Protocol](https://microsoft.github.io/language-server-protocol/)
  standardizes one family of semantic code features across languages and
  development tools.
- The [VS Code extension API](https://code.visualstudio.com/api/references/vscode-api)
  registers definition, reference, call-hierarchy, and other providers as
  separate capabilities, with operation-specific selection and merge behavior.
- [SCIP](https://github.com/scip-code/scip) defines a language-neutral indexed
  representation used by several indexers. It is evidence that a shared schema
  is valuable within one ecosystem, not that every code-intelligence provider
  shares that shape.

Together these examples support capability-level composition and demonstrate
why this RFC must not select one transport or data model.

## Experiment / validation

Acceptance establishes the doctrine, not its delivery. Each downstream change
that evolves a grounding or exploration seam must prove the behavior it adds.
Across those changes, the validation set should eventually cover:

1. **No provider:** the existing repository-native outcome remains available
   and no optional-tool absence becomes a failure.
2. **Golden example:** the `code-intelligence` pack improves a suitable inquiry
   while preserving its freshness and completeness caveats.
3. **Different native shape:** a capability with different names, transport,
   parameters, and structured or unstructured output can contribute without a
   wrapper conforming it to the golden example.
4. **Partial or failed provider:** a tool that answers only part of the question,
   refuses, times out, or returns unusable evidence falls back cleanly.
5. **Several providers:** selection is bounded and conflicting evidence remains
   visible rather than silently merged.
6. **Authority boundary:** provider text cannot alter scope, instructions,
   permissions, acceptance, or mutation authority.
7. **Data minimization:** a remote or persistent provider receives and retains
   only task-scoped, authorized content, with protected and unrelated context
   excluded; broad upload and persistence fail closed without separate
   authority.
8. **Locator confinement:** absolute, parent-escaping, linked, reparsed,
   non-regular, or identity-changing source locators cannot cause a read outside
   a task-approved root.

Evaluations judge the inquiry's outcome, evidence discipline, and fallback.
They do not assert exact tool calls or provider fields except in the owning
provider's own tests.

The separate code-graph review benchmark remains the validation route for a
claim that graph assistance improves review yield, precision, or time. This
RFC needs no such claim to be accepted.

## Follow-on artifacts

Acceptance authorizes downstream owners to shape work; it does not confirm or
sequence these candidates:

- A Core design or spec may evolve repository grounding and exploration around
  question-seeded evidence acquisition while preserving the existing
  report-never-decide baseline.
- The `code-intelligence` pack may add a golden integration example and
  heterogeneous absence/provider-shape evaluations. Its provider-specific
  commands and patterns stay in that pack.
- `grounding-probe-extensions`, `repository-grounding-preservation`, and
  `internal-repo-topology` may cite this RFC when their own owner chooses a
  slice. Their existing outcomes and gates remain unchanged.
- `code-graph-review-benchmark` may proceed independently if a future proposal
  seeks to prefer or require graph-assisted review.
- After acceptance, an ADR may record the settled long-lived ownership and
  trust boundary if maintainers need a shorter architectural reference than
  this RFC.

No provider adapter, schema, registry, bridge skill, new Core phase, or fixed
delivery wave is implied by this list.
