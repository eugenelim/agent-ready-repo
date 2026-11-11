# Digital Experience Doctrine current-standards survey

Research date: 2026-10-01

## Question and method

This survey asks whether the seven Digital Experience Doctrine feature intents
still describe current outcomes, whether fast-moving agent adapters or external
standards change their boundaries, and whether each intent remains one
feature-sized spec and plan.

Retrieval used built-in web search and three focused research agents. Sources
were limited to standards bodies, protocol projects, official product
documentation, and first-party research. No MCP or script retriever was used.
Material claims were checked against at least three independent sources when
the evidence surface allowed it. Standards controlled by one body are rated
below `high` and name that limitation.

## Findings

### Strategy remains outcome-led, but its measurement contract needs more precision

- The adoption hypothesis, user-visible first success, and causal metric tree
  remain sound. Google HEART ties product goals to signals and metrics, ISO
  9241-11 defines usability around specified users achieving specified goals in
  context, and Microsoft experimentation guidance requires falsifiable
  hypotheses plus outcome, guardrail, and data-quality metrics.
  [Google HEART](https://research.google.com/pubs/archive/36299.pdf),
  [ISO 9241-11:2018](https://www.iso.org/standard/63500.html),
  [Microsoft pre-experiment guidance](https://www.microsoft.com/en-us/research/?p=680556),
  [Microsoft metric-pitfall paper](https://www.microsoft.com/en-us/research/publication/a-dirty-dozen-twelve-common-metric-interpretation-pitfalls-in-online-controlled-experiments/).
  [high]

- The strategy contract should treat its named fields as required semantics,
  not as a form-filling count. It should allow an evidence-backed `not
  applicable`, and it should define first success as a completed user goal or
  accepted result rather than a tool call or task creation. [moderate]
  Downgrade: `indirectness`; the sources support contextual measurement but do
  not validate this repository's exact field count.

### Product-engineering shaping remains one feature, with portable evidence and capability semantics

- A thin slice remains a usable end-to-end learning unit rather than a smaller
  implementation ticket. The Agile principles call for early, frequent
  delivery of valuable software, Scrum requires a usable and valuable
  Increment, and DORA ties small batches to shorter feedback and safer
  AI-assisted delivery.
  [Agile principles](https://agilemanifesto.org/principles),
  [Scrum Guide 2020](https://scrumguides.org/scrum-guide.html),
  [DORA small batches](https://dora.dev/capabilities/working-in-small-batches/).
  [high]

- The five-level evidence ladder needs a provenance envelope and an event
  identity contract. W3C PROV covers entities, activities, agents, derivation,
  responsibility, time, and primary sources. CloudEvents standardizes event
  identity, source, type, version, time, and schema. OpenTelemetry provides
  shared semantic conventions across telemetry signals.
  [W3C PROV-O](https://www.w3.org/TR/prov-o/),
  [CloudEvents 1.0](https://github.com/cloudevents/spec/blob/main/cloudevents/spec.md),
  [OpenTelemetry semantic conventions](https://opentelemetry.io/docs/specs/semconv/).
  [moderate]
  Downgrade: `indirectness`; the sources define provenance and telemetry
  envelopes, not this repository's five labels.

- Current agent protocols converge on declared versions, negotiated
  capabilities, explicit fallbacks, and resumable or asynchronous behavior.
  MCP 2026-07-28 uses a stateless core, per-request capability metadata, and
  extensions. A2A 1.0 uses protocol versions and Agent Card capability
  declarations. Agent Skills defines portable skill packages but leaves some
  frontmatter and runtime support optional.
  [MCP 2026-07-28](https://modelcontextprotocol.io/specification/2026-07-28),
  [A2A 1.0](https://a2a-protocol.org/v1.0.0/specification/),
  [Agent Skills specification](https://agentskills.io/specification).
  [high]

- These protocols do not belong wholesale inside the shaping intent. The
  intent should own host-neutral capability, consent, fallback, retry,
  cancellation, and recovery semantics. Adapter and protocol implementations
  remain in the repository's adapter layer, and the cross-pack evaluation
  should prove their projections. [synthesis] [high]

### The delivered design-system outcome stays closed, with an explicit interchange seam

- DTCG 2025.10 is the current stable format, resolver, and color baseline. It
  is a Final Community Group Report intended for implementation, but it is not
  a W3C Standard or Recommendation. Later editor drafts are not authoritative.
  [Format Module 2025.10](https://www.designtokens.org/tr/2025.10/format/),
  [Resolver Module 2025.10](https://www.designtokens.org/tr/2025.10/resolver/),
  [Color Module 2025.10](https://www.designtokens.org/tr/2025.10/color/).
  [moderate]
  Downgrade: `single source`; all three modules come from one standards body.

- Tool support remains uneven. Style Dictionary reports partial DTCG support,
  Tokens Studio has a DTCG mode with type gaps, Penpot documents current token
  limits, and Figma exposes a proprietary Variables API.
  [Style Dictionary](https://styledictionary.com/info/dtcg/),
  [Tokens Studio](https://docs.tokens.studio/manage-settings/token-format),
  [Penpot](https://help.penpot.app/user-guide/design-systems/design-tokens/),
  [Figma Variables API](https://developers.figma.com/docs/rest-api/variables-endpoints/).
  [high]

- ADR-0128 and `design-system-values` intentionally deliver project value
  resolution in a technology-neutral Markdown artifact. DTCG serialization and
  target-tool round trips are therefore a post-fulfilment interoperability
  seam, not grounds to reopen the feature intent. [synthesis] [moderate]
  Downgrade: `indirectness`; this is a repository-governance inference from the
  external interoperability evidence.

### Archetypes, objects, and authorization need separate axes

- No standard defines a canonical page-archetype count. WAI defines semantic
  regions and landmarks, GOV.UK organizes patterns around user tasks, and
  USWDS describes templates as adaptable starting points. The RFC's twelve
  archetypes should remain a local seed catalogue, not an industry claim.
  [WAI page structure](https://www.w3.org/WAI/tutorials/page-structure/),
  [GOV.UK patterns](https://design-system.service.gov.uk/patterns/),
  [USWDS templates](https://designsystem.digital.gov/templates/).
  [high]

- A read/write permission pair is too narrow. Current authorization models
  bind a subject or role to actions over resources, sometimes with contextual
  attributes and structured authorization details.
  [NIST RBAC](https://csrc.nist.gov/projects/role-based-access-control),
  [NIST ABAC SP 800-162](https://csrc.nist.gov/pubs/sp/800/162/upd2/final),
  [RFC 9396](https://www.rfc-editor.org/rfc/rfc9396.html).
  [high]

- The intent should distinguish surface genre, task/page archetype, semantic
  regions, and product object plus authorized action. UI guidance may present
  policy, but it is not the security enforcement boundary. [synthesis] [high]

### Eighteen experience states are a local baseline, not a standards taxonomy

- WCAG and ARIA do not define a closed eighteen-state model. WCAG 2.2 defines
  conformance requirements, ARIA 1.2 defines role-specific states and
  properties, and APG applies different state contracts to different widgets.
  ARIA 1.3 remained a Working Draft on the research date.
  [WCAG 2.2](https://www.w3.org/TR/WCAG22/),
  [WAI-ARIA 1.2](https://www.w3.org/TR/wai-aria-1.2/),
  [ARIA Authoring Practices](https://www.w3.org/WAI/ARIA/apg/patterns/),
  [WAI-ARIA 1.3 draft](https://www.w3.org/TR/wai-aria-1.3/).
  [moderate]
  Downgrade: `single source`; these documents belong to one standards family.

- WCAG-EM 2.0 supports review across representative views, state-specific
  views, complete processes, critical branches, interaction, errors, feedback,
  settings, devices, and preferences. Rendered proof should combine visual
  state, task or keyboard trace, and accessible role/name/state evidence;
  screenshots alone are insufficient.
  [WCAG-EM 2.0](https://www.w3.org/TR/WCAG-EM/),
  [Chrome accessibility inspection](https://developer.chrome.com/docs/devtools/accessibility/reference),
  [Playwright ARIA snapshots](https://playwright.dev/docs/aria-snapshots),
  [WAI evaluation overview](https://www.w3.org/WAI/test-evaluate/).
  [high]

### Cross-pack evaluation must prove adapter behavior, not source-file sameness

- Agent Skills standardizes a package shape, not equivalent host behavior.
  Official host documentation differs on discovery, loading, inheritance,
  consent, runtime access, and synchronization.
  [Agent Skills specification](https://agentskills.io/specification),
  [Claude Agent Skills](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview),
  [Copilot custom skills](https://docs.github.com/en/copilot/how-tos/copilot-sdk/features/skills),
  [Cursor Agent Skills](https://prod.cursor.com/docs/skills),
  [Gemini CLI Agent Skills](https://github.com/google-gemini/gemini-cli/blob/main/docs/cli/using-agent-skills.md),
  [Kiro Agent Skills](https://kiro.dev/docs/skills/).
  [high]

- Current CLIs expose structured headless execution, so a bounded host matrix
  is practical rather than aspirational.
  [Cursor CLI](https://prod.cursor.com/docs/cli/overview),
  [Gemini CLI headless mode](https://github.com/google-gemini/gemini-cli/blob/main/docs/cli/headless.md),
  [Copilot CLI programmatic reference](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-programmatic-reference),
  [Kiro headless mode](https://kiro.dev/docs/cli/headless/),
  [OpenAI skill-eval guidance](https://developers.openai.com/blog/eval-skills).
  [high]

- A useful evaluation separates activation, outcome, process, style,
  efficiency, and comparison with a no-skill or prior-version baseline. It
  should deterministically inspect every supported projection, run a small
  positive/negative activation suite on headless hosts, rotate full journeys,
  and record explicit manual or not-measured rows for other surfaces.
  [OpenAI skill-eval guidance](https://developers.openai.com/blog/eval-skills),
  [Agent Skills evaluation guidance](https://github.com/agentskills/agentskills/blob/main/docs/skill-creation/evaluating-skills.mdx),
  [CursorBench report](https://cursor.com/resources/Composer2.pdf).
  [high]

- Blanket MCP or A2A conformance is out of scope. Agent Skills packages local
  procedural context, MCP connects hosts to tools and data, and A2A connects
  independent remote agents. A fixture that actually crosses one of those
  boundaries should pin the applicable revision and conformance suite.
  [Agent Skills specification](https://agentskills.io/specification),
  [MCP 2026-07-28](https://modelcontextprotocol.io/specification/2026-07-28),
  [A2A 1.0](https://a2a-protocol.org/v1.0.0/specification/).
  [high]

### Guides need generated freshness signals and host overlays

- Static intent indexes and a host-neutral end-to-end tutorial remain useful,
  but they do not prove current adapter behavior. The guide feature should add
  mechanically verified indexes, short host-specific overlays, a compatibility
  matrix, adapter-contract and host-version stamps, and links to the M5
  evaluation receipts. [synthesis] [moderate]
  Downgrade: `indirectness`; this follows from independently documented host
  differences rather than from one normative guide standard.

- The guide must distinguish filesystem Agent Skills, host-specific plugins
  and hooks, Skills over MCP, and A2A `AgentSkill`; the names overlap but the
  contracts do not. [synthesis] [high]

## Feature-size pressure test

Each intent still reduces to one feature-sized spec and one implementation
plan. The boundary is the independently useful outcome, while tests, guides,
release evidence, and adapter checks are acceptance surfaces of that outcome.
[synthesis] [moderate]
Downgrade: `indirectness`; external standards pressure-test the content but do
not determine this repository's delivery units.

| Intent | One-spec outcome | Split trigger |
| --- | --- | --- |
| `product-strategy-adoption-doctrine` | One portable strategy-to-adoption contract | Growth-program operations or a runtime-specific telemetry implementation enters scope |
| `product-engineering-shaping-doctrine` | One observable, learning-oriented shaping contract | Protocol transport or adapter implementation, rather than capability assumptions and fallbacks, enters scope |
| `xd-design-system-foundations` | One delivered project-value-resolution contract | Already delivered; DTCG serialization is a separate interoperability seam |
| `xd-ia-archetypes-objects` | One IA method joining archetype, object, action, attention, and navigation | Security-policy enforcement or a standalone authorization engine enters scope |
| `xd-state-reviewer-doctrine` | One review contract joining applicable states, three passes, severity, and evidence | A browser automation runtime becomes a product of the spec rather than a proving fixture |
| `cross-pack-experience-eval` | One layered source, projection, activation, handoff, and journey evaluation | A new general-purpose eval platform or remote-agent protocol implementation enters scope |
| `digital-product-guides-update` | One adoption surface joining verified indexes, a host-neutral tutorial, and host overlays | A docs-generation platform becomes required rather than bounded verification |

The six open intents should stay in `workspace.toml` as intent records until
their de-risking, shaping review, and acceptance evidence exists. A projected
spec path must not be registered before the spec exists and the intent is ready
for that transition. The fulfilled design-system intent needs no new spec.

## Known unknowns

- **Known-unknown:** Which headless hosts expose a reliable skill-activation
  event rather than only tool and final-output events. Close with one bounded
  probe per supported host.
- **Known-unknown:** Which host, model, and version combinations are affordable
  and licensed for scheduled evaluation. Close with an execution-budget
  decision before M5 spec authoring.
- **Known-unknown:** Which DTCG fields survive round trips through the exact
  Figma, Penpot, Tokens Studio, and Style Dictionary versions adopters use.
  Close with a shared fixture and loss matrix.
- **Known-unknown:** Which twelve archetypes cover the repository's real adopter
  products. Close with a representative surface and journey corpus.
- **Known-unknown:** Which browser, assistive-technology, device, and platform
  set each adopting product must support. The product owner must choose that
  baseline.
- **Known-unknown:** Whether the local `allowed-tools` schema still rejects the
  Agent Skills standard's space-separated scalar against real shipped files.
  Close with a confined real-file schema test and route any repair through the
  schema owner, outside this doctrine capability.
- **Unknowable:** Future optional agent extensions and host semantics. Mitigate
  with version-stamped receipts and a recurring adapter-freshness check rather
  than a claim of permanent parity.
