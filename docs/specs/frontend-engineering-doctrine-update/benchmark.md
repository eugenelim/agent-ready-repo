# Frontend Engineering Doctrine Benchmark

- **Feature:** `frontend-engineering-doctrine-update`
- **Benchmark phase:** shipped-evidence baseline and final publication reconciliation
- **Date:** 2026-08-08
- **Scope:** all nine skills named by `packs/frontend-engineering/pack.toml`, the `frontend-reviewer` agent, the frontend-engineering pack eval fixtures, RFC-0071 Area E, and the frontend-owner responsibilities in the Digital Experience Contract.

The opening matrices record the pre-change shipped-evidence baseline; planned
publication prose is not treated as evidence for that baseline. Later sections
reconcile the authored publication claims against shipped sources and record the
final disposition of candidate behavior gaps. After the user approved the two
genuine gaps, the final reconciliation appended their build follow-ons to
`workspace.toml`.

## Source Inventory

| Source | Disposition | Shipped evidence path | Notes |
|---|---|---|---|
| Pack manifest names all user-triggered skills | Pass | `packs/frontend-engineering/pack.toml` | `[pack.evals].skills` lists `frontend-engineering`, `token-architecture`, `a11y-engineering`, `fe-performance`, `rendering-strategy`, `component-contract`, `responsive-layout`, `css-architecture`, and `fe-status`. |
| Pack-local install context | Pass | `packs/frontend-engineering/AGENTS.md` | States the pack installs 9 skills and the `frontend-reviewer` agent; documents the `experience-design` co-install named skip. |
| Canonical frontend-engineering doctrine owner | Pass | `docs/adr/0057-frontend-engineering-pack-promotion-and-resident-deletion.md` | Records promotion of `packs/frontend-engineering/` as the canonical owner after deletion of the core resident skill. Internal decision evidence only; not shipped adopter prose. |
| RFC-0071 Area E obligation set | Pass | `docs/rfc/0071-digital-experience-doctrine.md` | Defines the frontend-engineering doctrine obligations benchmarked below. Internal governance evidence only; not shipped adopter prose. |
| Digital Experience Contract reference | Pass | `packs/frontend-engineering/.apm/skills/frontend-engineering/references/digital-experience-contract.md` | Pack-local shipped DEC copy with `schema-version: "1.0"` and frontend-owner fields. |
| Main frontend implementation skill | Pass | `packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md` | Canonical shipped implementation doctrine source. |
| Atomic skills | Pass | `packs/frontend-engineering/.apm/skills/*/SKILL.md` | Eight supporting skills partition tokens, a11y, performance, rendering, component contracts, responsive layout, CSS architecture, and status. |
| Diff-level reviewer | Pass | `packs/frontend-engineering/.apm/agents/frontend-reviewer.md` | Shipped reviewer for frontend diffs. |
| Activation eval fixtures | Pass | `packs/frontend-engineering/.apm/skills/*/evals/eval_queries.json` | All nine skills have skill-local Tier-A activation/near-miss fixtures. |

## RFC-0071 Area E Obligation Matrix

| Obligation | Disposition | Shipped evidence path | Evidence summary | Candidate behavior gap |
|---|---|---|---|---|
| Four-mode structure as conditional sections: create / retrofit / audit / verify | Pass | `packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md` | The mode-selection table names create, retrofit, audit, and verify with separate mode sections and outputs. | none |
| Page/screen contract required before significant UI code | Pass | `packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md` | Create mode Step 0 requires the page/screen contract before significant UI code. | none |
| Page/screen contract has 12 fields | Pass | `packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md` | The template lists: target user, primary job, primary action, expected result, next action, first-screen content, product proof, read/write consequence, critical states, responsive behavior, a11y requirements, and measurement event. | none |
| Contract is proportional to risk and scope, not ritualized for trivial changes | Pass | `packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md` | The create-mode contract text distinguishes new routes/key surfaces from a single form field, tooltip, or minor component variant. | none |
| WCAG 2.2 AA is the default accessibility baseline | Pass | `packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md`; `packs/frontend-engineering/.apm/skills/a11y-engineering/SKILL.md` | The main skill declares WCAG 2.2 AA as baseline; the a11y skill covers the two automated-tooling gaps. | none |
| Baseline Widely Available is the default browser policy | Pass | `packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md`; `packs/frontend-engineering/.apm/skills/css-architecture/SKILL.md`; `packs/frontend-engineering/.apm/skills/responsive-layout/SKILL.md` | Main skill sets Baseline Widely Available; atomic CSS/responsive skills cite Baseline status for `@layer`, `inert`, container queries, and `subgrid`. | none |
| Core Web Vitals targets for public production surfaces: LCP <= 2.5s, INP <= 200ms, CLS <= 0.1 at p75 | Pass | `packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md`; `packs/frontend-engineering/.apm/skills/fe-performance/SKILL.md` | The main skill states p75 mobile/desktop evaluation; the performance skill carries the same metric targets and diagnostic model. | none |
| Core Web Vitals evaluated separately for mobile and desktop where field data exists | Pass | `packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md` | Performance targets and audit mode both state mobile and desktop are evaluated separately where field data exists. | none |
| Asset budget requirement covers JS, images, fonts, third-party scripts, hydration, route-level loading, and long tasks | Pass | `packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md`; `packs/frontend-engineering/.apm/skills/fe-performance/SKILL.md` | Main skill names all seven categories; performance skill gives measurement/remediation handles for those categories. | none |
| Brownfield inspection checklist | Pass | `packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md` | Retrofit mode defines six inspection items: what-to-preserve, duplicated-systems, hard-coded values, a11y-debt, responsive-debt, and visual-regression-risk. | none |
| Implementation evidence manifest required as a completion artifact | Pass | `packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md`; `packs/frontend-engineering/.apm/skills/fe-status/SKILL.md` | Main skill refuses completion or passing verify without an 11-field manifest; status skill treats the manifest as the quality-state ground truth. | none |
| Multi-surface shell contract for shared tokens, navigation, and terminology | Pass | `packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md`; `packs/frontend-engineering/.apm/skills/token-architecture/SKILL.md` | Main skill defines shared tokens, navigation patterns, and terminology constraints; token skill defines token architecture and governance. | none |
| Conditional public-surface guidance for metadata, canonical URLs, sitemaps, structured data, and search indexing intent | Pass | `packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md` | Public-surface section applies only to indexable marketing/docs/landing surfaces and lists all five required checks. | none |

## Digital Experience Contract Frontend Responsibilities

| DEC responsibility | Disposition | Shipped evidence path | Evidence summary | Candidate behavior gap |
|---|---|---|---|---|
| Skills may read all DEC areas but must not silently rewrite another discipline's section | Pass | `packs/frontend-engineering/.apm/skills/frontend-engineering/references/digital-experience-contract.md`; `packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md` | DEC comment states read-only cross-discipline rule and provisional fallback; main skill's genre-routing step records named skips when `experience-design` is absent. | none |
| Prototype or representation at explore tier | Pass | `packs/frontend-engineering/.apm/skills/frontend-engineering/references/digital-experience-contract.md`; `packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md` | DEC requires earliest rendered evidence; main skill requires screenshots/visual QA and evidence manifest fields for rendered states. | none |
| Implemented behavior at production tier | Pass | `packs/frontend-engineering/.apm/skills/frontend-engineering/references/digital-experience-contract.md`; `packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md` | DEC names implemented behavior; main skill's gates require structural validation, accessibility audit, token enforcement, and visual state checks. | none |
| Semantic structure | Pass | `packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md` | HTML rules cover interactive elements, landmarks, heading hierarchy, forms, images/media, and content semantics. | none |
| Design-system realization | Pass | `packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md`; `packs/frontend-engineering/.apm/skills/token-architecture/SKILL.md`; `packs/frontend-engineering/.apm/skills/css-architecture/SKILL.md` | Main skill requires token seed and token gate; token/css skills cover architecture, cascade layers, specificity, and token compliance audit. | none |
| Responsive implementation | Pass | `packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md`; `packs/frontend-engineering/.apm/skills/responsive-layout/SKILL.md` | Main skill includes responsive behavior in the page contract; responsive-layout covers primitive selection, container/media queries, fluid type, breakpoints, grid patterns, and no-JS responsive rules. | none |
| State implementation | Pass | `packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md`; `packs/frontend-engineering/.apm/agents/frontend-reviewer.md`; `packs/frontend-engineering/.apm/skills/fe-status/SKILL.md` | Main skill requires 18-state matrix enumeration and visual QA; reviewer checks state coverage regression; status skill reports missing states from the manifest. | none |
| Accessibility evidence | Pass | `packs/frontend-engineering/.apm/skills/frontend-engineering/references/digital-experience-contract.md`; `packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md`; `packs/frontend-engineering/.apm/skills/a11y-engineering/SKILL.md`; `packs/frontend-engineering/.apm/agents/frontend-reviewer.md` | DEC requires accessibility evidence; main/a11y skill cover WCAG 2.2 AA and manual criteria; reviewer flags Focus Appearance and Target Size gaps. | none |
| Browser behavior | Pass | `packs/frontend-engineering/.apm/skills/frontend-engineering/references/digital-experience-contract.md`; `packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md` | DEC requires browser behavior; main skill requires browsers/rendering engines in the evidence manifest and Baseline Widely Available policy. | none |
| Performance | Pass | `packs/frontend-engineering/.apm/skills/frontend-engineering/references/digital-experience-contract.md`; `packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md`; `packs/frontend-engineering/.apm/skills/fe-performance/SKILL.md`; `packs/frontend-engineering/.apm/agents/frontend-reviewer.md` | DEC requires CWV/asset-budget evidence; main/performance skills define targets and budgets; reviewer scans CWV regression signals. | none |
| Security and privacy | Gap | `packs/frontend-engineering/.apm/skills/frontend-engineering/references/digital-experience-contract.md`; `packs/frontend-engineering/.apm/agents/frontend-reviewer.md` | DEC includes a production FE-owned field for data handled, privacy controls, and security review status. The reviewer explicitly routes auth/secrets/input boundaries to `security-reviewer`; the main FE skill does not require recording this DEC field in the evidence manifest. | Candidate behavior gap: decide whether the FE evidence manifest or public-surface guidance should require a security/privacy DEC entry, or whether this remains owned by security review outside FE doctrine. |
| Reliability | Gap | `packs/frontend-engineering/.apm/skills/frontend-engineering/references/digital-experience-contract.md`; `packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md` | DEC requires error rates, SLOs, monitoring/alerting, and recovery path. Main skill checks console/network result and known exceptions, but does not require reliability/SLO evidence. | Candidate behavior gap: decide whether FE verify mode should require a reliability/recovery manifest field for production surfaces. |
| Instrumentation | Pass | `packs/frontend-engineering/.apm/skills/frontend-engineering/references/digital-experience-contract.md`; `packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md` | DEC requires events/dashboards; main skill includes measurement event in the page contract and analytics events in the evidence manifest. | none |
| Rendered evidence | Pass | `packs/frontend-engineering/.apm/skills/frontend-engineering/references/digital-experience-contract.md`; `packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md` | DEC requires screenshot/recording/live URL; main skill requires screenshots and visual QA evidence. | none |

## Primitive Coverage Matrix

| Primitive | Disposition | Shipped evidence path | Doctrine coverage | Candidate behavior gap |
|---|---|---|---|---|
| `frontend-engineering` | Pass | `packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md` | Owns the four-mode workflow, page/screen contract, state matrix, craft rules, gates, CWV targets, asset budgets, evidence manifest, public-surface guidance, and multi-surface shell. | Security/privacy and reliability DEC production fields are present in the DEC but not fully represented in the main skill's manifest. |
| `token-architecture` | Pass | `packs/frontend-engineering/.apm/skills/token-architecture/SKILL.md` | Covers design-system realization through a three-tier token architecture, `--ds-` namespace, semantic aliases, theming, component tokens, DTCG export, audit, and governance. | none |
| `a11y-engineering` | Pass | `packs/frontend-engineering/.apm/skills/a11y-engineering/SKILL.md` | Covers WCAG 2.2 AA manual gaps, focus management, dynamic ARIA mutation, live regions, keyboard contracts, complex patterns, and remediation priority. | none |
| `fe-performance` | Pass | `packs/frontend-engineering/.apm/skills/fe-performance/SKILL.md` | Covers CWV diagnosis, p75 LCP/INP/CLS targets, structured profiling, remediation, asset-budget enforcement, code splitting, image optimization, and PR regression signals. | none |
| `rendering-strategy` | Pass | `packs/frontend-engineering/.apm/skills/rendering-strategy/SKILL.md` | Covers CSR/SSR/SSG/ISR/RSC route decisions against data access, performance targets, personalization, SEO, and hydration cost. | none |
| `component-contract` | Pass | `packs/frontend-engineering/.apm/skills/component-contract/SKILL.md` | Covers component public interfaces, controlled/uncontrolled ownership, props, slots, events, lifecycle, usage docs, and component accessibility contract. | none |
| `responsive-layout` | Pass | `packs/frontend-engineering/.apm/skills/responsive-layout/SKILL.md` | Covers layout primitive choice, container/media queries, fluid typography, breakpoints, grid patterns, no-JS responsive patterns, and common responsive failures. | none |
| `css-architecture` | Pass | `packs/frontend-engineering/.apm/skills/css-architecture/SKILL.md` | Covers cascade layers, scoping, specificity budgets, deletion safety, token compliance audit, custom property gotchas, and naming systems. | none |
| `fe-status` | Pass | `packs/frontend-engineering/.apm/skills/fe-status/SKILL.md` | Reads evidence manifest, known exceptions, missing states, accessibility status, CWV status, console/network status, and open unverified items. | none |
| `frontend-reviewer` | Pass | `packs/frontend-engineering/.apm/agents/frontend-reviewer.md` | Diff-level lens for CSS token drift, ARIA mutation completeness, 18-state regression, WCAG 2.2 manual items, and CWV regression signals; routes other reviewer concerns out of scope. | none |

## Eval Baseline

| Eval source | Disposition | Shipped evidence path | Evidence summary | Candidate behavior gap |
|---|---|---|---|---|
| All nine manifest-listed skills have eval files | Pass | `packs/frontend-engineering/.apm/skills/*/evals/eval_queries.json` | Each skill has skill-local activation and near-miss queries. | none |
| Main skill covers create, audit, and verify activation language | Pass | `packs/frontend-engineering/.apm/skills/frontend-engineering/evals/eval_queries.json` | True queries include building new pages/components/surfaces and running the full gate suite/evidence manifest; near-misses route atomic concerns away. | none |
| Main skill covers retrofit activation language | Gap | `packs/frontend-engineering/.apm/skills/frontend-engineering/evals/eval_queries.json` | The main eval set includes create, audit, and verify phrasings but no direct true query using `retrofit`, improving an existing surface, or brownfield inspection language. | Candidate eval gap for T5/T6: add benchmark-derived retrofit activation coverage. |
| Main skill covers page/screen-contract activation language | Gap | `packs/frontend-engineering/.apm/skills/frontend-engineering/evals/eval_queries.json` | The shipped skill requires the contract, but the main eval set has no direct true query for writing or applying the page/screen contract. | Candidate eval gap for T5/T6: add benchmark-derived page/screen-contract activation coverage. |
| Main skill covers project-specific asset-budget language | Gap | `packs/frontend-engineering/.apm/skills/frontend-engineering/evals/eval_queries.json` | Performance budget language activates `fe-performance`, but the main skill's eval set does not cover project-specific asset-budget language used during full-surface create/verify work. | Candidate eval gap for T5/T6: add benchmark-derived project-specific asset-budget coverage without changing skill behavior. |
| Main skill has documentation-authoring near miss | Gap | `packs/frontend-engineering/.apm/skills/frontend-engineering/evals/eval_queries.json` | Existing near-misses cover token, a11y, CWV, rendering, component API, breakpoints, CSS architecture, and status, but not documentation-authoring requests. | Candidate eval gap for T5/T6: add a false query for writing a guide or docs page. |

## Candidate Behavior Gaps For Final Disposition

| Gap id | Source obligation | Disposition now | Evidence | Final disposition needed |
|---|---|---|---|---|
| `candidate-security-privacy-dec-field` | DEC production `Security and Privacy` field | Gap | `packs/frontend-engineering/.apm/skills/frontend-engineering/references/digital-experience-contract.md`; `packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md`; `packs/frontend-engineering/.apm/agents/frontend-reviewer.md` | Decide after claim authoring whether this is a genuine FE behavior gap needing `workspace.toml [backlog].open`, or an out-of-scope security-review handoff not claimed by adopter-facing FE materials. |
| `candidate-reliability-dec-field` | DEC production `Reliability` field | Gap | `packs/frontend-engineering/.apm/skills/frontend-engineering/references/digital-experience-contract.md`; `packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md` | Decide after claim authoring whether production FE verify should record reliability/recovery evidence, or whether publication prose must avoid implying reliability coverage. |
| `candidate-main-eval-retrofit` | Main skill activation coverage | Gap | `packs/frontend-engineering/.apm/skills/frontend-engineering/evals/eval_queries.json` | Add or defer benchmark-derived retrofit activation eval coverage in the authorized eval-only `.apm` task. |
| `candidate-main-eval-page-screen-contract` | Main skill activation coverage | Gap | `packs/frontend-engineering/.apm/skills/frontend-engineering/evals/eval_queries.json` | Add or defer benchmark-derived page/screen-contract activation eval coverage in the authorized eval-only `.apm` task. |
| `candidate-main-eval-project-asset-budget` | Main skill activation coverage | Gap | `packs/frontend-engineering/.apm/skills/frontend-engineering/evals/eval_queries.json` | Add or defer benchmark-derived project-specific asset-budget activation eval coverage in the authorized eval-only `.apm` task. |
| `candidate-main-eval-doc-authoring-near-miss` | Main skill near-miss coverage | Gap | `packs/frontend-engineering/.apm/skills/frontend-engineering/evals/eval_queries.json` | Add or defer benchmark-derived documentation-authoring near-miss coverage in the authorized eval-only `.apm` task. |

## Initial Publication Claim Guardrails

Use these constraints when authoring T2-T4 and reconciling claims in T5-T6:

- Claims about four jobs may say the shipped main skill supports create, retrofit, audit, and verify.
- Claims about page/screen contracts must preserve the 12 canonical field names and the proportional-to-risk rule.
- Claims about accessibility may say WCAG 2.2 AA is the baseline, with manual verification required for Focus Appearance and Target Size Minimum.
- Claims about browser support may say Baseline Widely Available is the default browser policy.
- Claims about performance may state the three CWV p75 targets and the seven asset-budget categories; they must not invent universal numeric byte ceilings.
- Claims about completion may say create/retrofit/verify require an evidence manifest.
- Claims about security/privacy or reliability must be narrowed unless T5 records shipped evidence or opens a follow-on behavior gap.
- Claims about eval coverage must account for the four candidate eval gaps above until T5 updates or defers them.

## Final Publication Claim Inventory

### Pre-integration inventory

This inventory was extracted from the completed T2-T6 publication surfaces before
any final claim narrowing. It treats shipped pack sources as evidence, not future
backlog intent.

| Publication source | Claim | Disposition | Shipped evidence path | Reconciliation |
|---|---|---|---|---|
| `web/src/content/packs/frontend-engineering.md` | The pack serves teams and agents building web surfaces in HTML, CSS, and JS; its example request asks for frontend evidence for release review. | Pass | `packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md`; `packs/frontend-engineering/AGENTS.md` | Main skill activation says primary output is HTML, CSS, or JS and requires gate results plus an evidence manifest; pack AGENTS states the pack installs FE primitives for HTML/CSS/JS work. |
| `web/src/content/packs/frontend-engineering.md` | The pack routes work by four jobs: create, retrofit, audit, and verify. | Pass | `packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md` | Mode-selection table and mode sections name all four jobs. |
| `web/src/content/packs/frontend-engineering.md` | Create drafts a proportional page/screen contract, plans states and tokens, implements, runs gates, and returns an evidence manifest. | Pass | `packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md` | Create mode requires the contract, shared pre-flight, state matrix, EXECUTE/GATES, and evidence manifest. |
| `web/src/content/packs/frontend-engineering.md` | Retrofit starts with brownfield inspection covering what-to-preserve, duplicated systems, hard-coded values, a11y debt, responsive debt, and visual-regression risk. | Pass | `packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md` | Retrofit mode defines the same six-item checklist before code changes. |
| `web/src/content/packs/frontend-engineering.md` | Audit is read-only and reports applicable states, WCAG 2.2 AA, CWV targets, asset-budget categories, and brownfield risks. | Pass | `packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md` | Audit procedure is report-only and includes state, accessibility, CWV, and brownfield checks. |
| `web/src/content/packs/frontend-engineering.md` | Verify runs structural HTML validation, accessibility audit, CSS token enforcement when configured, visual QA, and performance checks against p75 CWV targets. | Pass | `packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md` | Verify mode and GATES define these checks; performance targets state p75 CWV evaluation. |
| `web/src/content/packs/frontend-engineering.md` | The evidence manifest separates pass, fail, known exception, and unverified items. | Pass | `packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md` | Evidence manifest requires known exceptions and unverified items; gates require actual results. |
| `web/src/content/packs/frontend-engineering.md` | The journey exposes contract, implementation or audit, gates, manifest, and independent frontend review as the workflow. | Pass | `packs/frontend-engineering/JOURNEY.md`; `packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md`; `packs/frontend-engineering/.apm/agents/frontend-reviewer.md` | Journey is shipped pack content and matches main skill plus reviewer responsibilities. |
| `web/src/content/packs/frontend-engineering.md` | The skill inventory installs nine named skills and a frontend reviewer. | Pass | `packs/frontend-engineering/pack.toml`; `packs/frontend-engineering/AGENTS.md`; `packs/frontend-engineering/.apm/agents/frontend-reviewer.md` | Manifest and pack AGENTS name the nine skills and reviewer. |
| `web/src/content/packs/frontend-engineering.md` | `experience-design` co-install supplies full genre routing; absence is a named skip, not a failure. | Pass | `packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md`; `packs/frontend-engineering/AGENTS.md` | Shared pre-flight Step 1b checks for `experience-design` skills and records the named skip when absent. |
| `packs/frontend-engineering/JOURNEY.md` | The journey starts read-only and ends confirmed-write. | Not applicable | `packs/frontend-engineering/JOURNEY.md` | Journey state metadata describes the published journey surface; it is not a skill-behavior capability claim. |
| `packs/frontend-engineering/JOURNEY.md` | The user receives a proportional page/screen contract, implementation or audit path, gate results, evidence manifest, and independent frontend review. | Pass | `packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md`; `packs/frontend-engineering/.apm/agents/frontend-reviewer.md` | Main skill owns the contract/path/gates/manifest; reviewer owns independent diff review. |
| `packs/frontend-engineering/JOURNEY.md` | Human gates are mode choice, contract approval, evidence acceptance, and independent review. | Pass | `packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md`; `packs/frontend-engineering/.apm/agents/frontend-reviewer.md` | These are surfaced from mode selection, contract approval, manifest acceptance, and reviewer run requirements. |
| `packs/frontend-engineering/JOURNEY.md` | Security, reliability, and broader product-design concerns route to appropriate reviewers instead of being claimed as covered by frontend review. | Pass | `packs/frontend-engineering/.apm/agents/frontend-reviewer.md`; `packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md` | Reviewer explicitly routes security and reliability out of scope; main skill records named skips for unavailable design routing. |
| `packs/frontend-engineering/JOURNEY.md` | The evidence manifest includes routes, viewports, browsers, states, screenshots, a11y result, perf result, console/network result, analytics events, known exceptions, and unverified items. | Pass | `packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md` | Evidence manifest table lists the same 11 required fields. |
| `guides/frontend-engineering/how-to/page-screen-contract.md` | The result is a full 12-field contract, a proportional subset, or a no-contract decision for trivial work. | Pass | `packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md` | Create mode states the contract is proportional; full contract is required only for new routes/key surfaces/significant surfaces. |
| `guides/frontend-engineering/how-to/page-screen-contract.md` | The guide preserves the 12 canonical contract field names. | Pass | `packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md` | Guide table matches the main skill's contract template field names exactly. |
| `guides/frontend-engineering/how-to/page-screen-contract.md` | Smaller changes use only fields that settle user intent, consequence, states, and accessibility; trivial changes record an explicit no-contract decision. | Pass | `packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md` | Main skill exempts a single new form field, tooltip, or minor component variant from the full contract while preserving proportionality. |
| `guides/frontend-engineering/reference/performance-targets.md` | Fixed CWV targets are LCP <= 2.5 seconds, INP <= 200 milliseconds, and CLS <= 0.1 at p75, evaluated separately for mobile and desktop where field data exists. | Pass | `packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md`; `packs/frontend-engineering/.apm/skills/fe-performance/SKILL.md` | Main and performance skills state the same thresholds and p75/mobile/desktop rule. |
| `guides/frontend-engineering/reference/performance-targets.md` | Numeric asset ceilings are project-specific; no universal byte ceiling applies across unrelated surfaces. | Pass | `packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md`; `packs/frontend-engineering/.apm/skills/fe-performance/SKILL.md` | Shipped skills require per-route asset budgets and remediation categories without publishing universal byte ceilings. |
| `guides/frontend-engineering/reference/performance-targets.md` | Asset-budget categories are JS, images, fonts, third-party scripts, hydration, route-level loading, and long tasks. | Pass | `packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md`; `packs/frontend-engineering/.apm/skills/fe-performance/SKILL.md` | Main skill names all seven categories; performance skill maps category measurement and remediation. |
| `guides/frontend-engineering/reference/performance-targets.md` | Marketing, documentation, product/workspace, analytical/internal, and transactional surfaces prioritize different performance categories and measurements. | Pass | `packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md`; `packs/frontend-engineering/.apm/skills/fe-performance/SKILL.md` | Shipped skills provide CWV and asset-budget policy; surface-type prioritization is explanatory guide guidance derived from those categories. |
| `guides/frontend-engineering/README.md` | The guide index routes readers from an example request for frontend release-review evidence through the pack overview to the frontend engineering journey. | Pass | `packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md`; `web/src/content/packs/frontend-engineering.md`; `packs/frontend-engineering/JOURNEY.md`; `web/src/content/journeys/frontend-engineering.md`; `guides/frontend-engineering/README.md` | The main skill requires gate results and an evidence manifest; navigation claims cite the overview, canonical journey, generated journey route, and index link. |
| `guides/frontend-engineering/README.md` | The guide index registers the page/screen-contract how-to and says it yields a full 12-field contract, proportional subset, or explicit no-contract decision. | Pass | `guides/frontend-engineering/how-to/page-screen-contract.md`; `packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md` | The linked guide and main skill both support the proportional contract outcomes and canonical field set. |
| `guides/frontend-engineering/README.md` | The guide index registers the performance reference and says it yields fixed CWV targets, prioritized asset-budget categories, and project-specific numeric-ceiling decisions. | Pass | `guides/frontend-engineering/reference/performance-targets.md`; `packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md`; `packs/frontend-engineering/.apm/skills/fe-performance/SKILL.md` | The linked reference and shipped skills support the CWV targets, seven asset categories, and project-specific ceiling rule. |
| `guides/frontend-engineering/README.md` | The guide index routes to the existing audit how-to, tutorial, and skill/reviewer reference. | Not applicable | `guides/frontend-engineering/how-to/run-an-audit.md`; `guides/frontend-engineering/tutorials/scaffold-a-component.md`; `guides/frontend-engineering/reference/frontend-engineering.md`; `guides/frontend-engineering/README.md` | Navigation claims cite existing guide files rather than skill behavior. |
| `guides/frontend-engineering/README.md` | The shared frontend quality floor is state coverage, WCAG 2.2 AA, token discipline, and an evidence manifest for completed create, retrofit, or verify work. | Pass | `packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md`; `packs/frontend-engineering/.apm/skills/a11y-engineering/SKILL.md`; `packs/frontend-engineering/.apm/skills/token-architecture/SKILL.md`; `packs/frontend-engineering/.apm/skills/fe-status/SKILL.md` | Main and atomic skills support the quality-floor elements without adding broader security or reliability coverage. |
| `guides/frontend-engineering/README.md` | The pack does not replace security or reliability review; frontend review routes those concerns to the appropriate reviewer or owner. | Pass | `packs/frontend-engineering/.apm/agents/frontend-reviewer.md`; `packs/frontend-engineering/.apm/skills/frontend-engineering/evals/eval_queries.json`; `docs/specs/frontend-engineering-doctrine-update/benchmark.md`; `workspace.toml` | Reviewer scope routes security and reliability out of frontend review; false activation near misses cover security and reliability handoff prompts; recorded behavior gaps point to approved backlog slugs `frontend-engineering-security-privacy-manifest-field` and `frontend-engineering-reliability-manifest-field`. |

### Final inventory after T6 reconciliation

| Reconciliation item | Disposition | Shipped evidence path | Final result |
|---|---|---|---|
| Unsupported publication claims | Pass | Sources inventoried above | No unsupported adopter-facing claims were found across the marketing page, journey, two new guides, and guide index. Security/privacy and reliability are not marketed as frontend-owned coverage; the journey and guide index explicitly route them to appropriate reviewers or owners. |
| `candidate-security-privacy-dec-field` | Gap | `packs/frontend-engineering/.apm/skills/frontend-engineering/references/digital-experience-contract.md`; `packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md`; `packs/frontend-engineering/.apm/agents/frontend-reviewer.md` | Genuine behavior gap remains: the DEC has a production frontend security/privacy field, but the main FE evidence manifest does not require data-handled, privacy-controls, or security-review-status evidence. Publication claims are narrowed; `workspace.toml [backlog].open` tracks `frontend-engineering-security-privacy-manifest-field`. |
| `candidate-reliability-dec-field` | Gap | `packs/frontend-engineering/.apm/skills/frontend-engineering/references/digital-experience-contract.md`; `packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md` | Genuine behavior gap remains: the DEC has a production frontend reliability field, but the main FE evidence manifest does not require error-rate, SLO, monitoring/alerting, or recovery-path evidence. Publication claims are narrowed; `workspace.toml [backlog].open` tracks `frontend-engineering-reliability-manifest-field`. |
| `candidate-main-eval-retrofit` | Pass | `packs/frontend-engineering/.apm/skills/frontend-engineering/evals/eval_queries.json` | T5 adds a true activation query containing `retrofit`. |
| `candidate-main-eval-page-screen-contract` | Pass | `packs/frontend-engineering/.apm/skills/frontend-engineering/evals/eval_queries.json` | T5 adds a true activation query containing `page/screen contract`. |
| `candidate-main-eval-project-asset-budget` | Pass | `packs/frontend-engineering/.apm/skills/frontend-engineering/evals/eval_queries.json` | T5 adds a true activation query containing `project-specific asset budget`. |
| `candidate-main-eval-doc-authoring-near-miss` | Pass | `packs/frontend-engineering/.apm/skills/frontend-engineering/evals/eval_queries.json` | T5 adds a false near-miss query containing `write a guide`. |
| `review-security-handoff-near-miss` | Pass | `packs/frontend-engineering/.apm/skills/frontend-engineering/evals/eval_queries.json` | Final security review adds a false near miss for authentication, session-handling, and secrets-review language so the frontend-only skill does not claim that boundary. |
| `review-reliability-handoff-near-miss` | Pass | `packs/frontend-engineering/.apm/skills/frontend-engineering/evals/eval_queries.json` | Final security review adds a false near miss for error-budget, SLO-alerting, and recovery-procedure language so the frontend-only skill does not claim that boundary. |

## Backlog Follow-ons Captured

The user approved these two build entries and their order. T5 appended them to
repo-level `workspace.toml [backlog].open`. They are independent and have no
explicit `needs`.

1. Classification: `[build]`
   Slug: `frontend-engineering-security-privacy-manifest-field`
   Source: `spec/frontend-engineering-doctrine-update AC2`
   Order: first
   Needs: none
   Comment:
   ```
   # Problem: the shipped Digital Experience Contract includes a production
   # Frontend Engineering Security and Privacy field for data handled, privacy
   # controls, and security review status, but the frontend-engineering evidence
   # manifest does not require that evidence. The frontend-reviewer correctly
   # routes security findings to security-reviewer, so adopter-facing publication
   # prose was narrowed instead of claiming coverage.
   # Fix: update the frontend-engineering skill's evidence-manifest requirements
   # and related create/retrofit/verify guidance to record security/privacy review
   # status for production surfaces without making the FE skill perform security
   # review.
   # Affected skill/file: packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md
   # Decisions already taken: security-reviewer remains the reviewer for auth,
   # secrets, and user-input boundaries; FE should record status/handoff evidence,
   # not duplicate security-reviewer.
   # Unblocks: now; there is no tracked prerequisite. Completion requires the
   # skill behavior and any projected/eval/docs updates to ship together, with
   # adopter-facing claims still narrowed to recorded status/handoff.
   ```
2. Classification: `[build]`
   Slug: `frontend-engineering-reliability-manifest-field`
   Source: `spec/frontend-engineering-doctrine-update AC2`
   Order: second
   Needs: none
   Comment:
   ```
   # Problem: the shipped Digital Experience Contract includes a production
   # Frontend Engineering Reliability field for error rates, SLOs, monitoring and
   # alerting, and recovery path, but the frontend-engineering evidence manifest
   # only records console/network result, known exceptions, and unverified items.
   # Publication prose was narrowed so FE does not claim full reliability coverage.
   # Fix: update the frontend-engineering skill's create/retrofit/verify evidence
   # manifest guidance to require reliability/recovery status for production
   # surfaces, with explicit handoff when quality-engineer or platform ownership
   # is needed.
   # Affected skill/file: packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md
   # Decisions already taken: reliability is not a frontend-reviewer lens today;
   # the FE skill should record status and recovery evidence rather than silently
   # claiming a broader reliability review.
   # Unblocks: now; there is no tracked prerequisite. Completion requires the
   # skill behavior and any projected/eval/docs updates to ship together, with
   # adopter-facing claims still narrowed to recorded status/handoff.
   ```
