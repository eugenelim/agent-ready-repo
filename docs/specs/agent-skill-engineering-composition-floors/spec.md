# Spec: Agent Skill Engineering Composition Floors

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [`RFC-0097`](../../rfc/0097-agent-skill-engineering.md);
  [`Agent Skill Engineering Corpus`](../agent-skill-engineering-corpus/spec.md);
  [`Agent Skill Engineering Languages and Execution`](../agent-skill-engineering-languages-and-execution/spec.md)
- **Brief:** docs/product/briefs/agent-skill-engineering.md
- **Discovery:** none
- **Contract:** none under `contracts/`. The pack's provider response contract
  gains no field and no status value; `stale-profile` keeps the meaning RFC-0097
  assigns it and gains a second derivation path, which the criteria below
  constrain and distinguish by `diagnostic`.
- **Shape:** mixed

> **Hard dependency.** The corpus and languages slices are Shipped. This slice
> admits four of the eleven taxonomy leaves reserved for runtime composition and
> leaves the remaining seven runtime profiles to its successor.

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

An agent-skill author asking how to compose a skill with subagents, hooks, or a
plugin package gets portable guidance that separates a capability floor from
runtime-specific behavior, and gets it without being told a capability is
supported when nobody checked. The corpus carries three portable composition
floors and one runtime profile — Claude Code — whose every capability row names
a first-party source, the date it was retrieved, the product version that
source exposed where it exposes one, and a lifecycle state that the router
reports rather than averages away. A sourced claim nobody has independently
probed reads as `experimental`; a claim whose verification window elapsed reads
as `stale` and returns provenance instead of guidance; a capability that is
absent, or whose sources conflict so that safe verification cannot be performed,
reads as `unavailable` and is recorded as an enterprise delta rather than a gap.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| User-facing promise | The pack README states which topics are governed and what the pack does not yet cover; both change | `packs/agent-skill-engineering/README.md` | this spec | Shipped-statement agreement test over the admitted set | README states sixteen governed topics and no longer claims composition floors are later-slice work |
| Current product truth | Topology accounting, admitted-versus-absent partition, and retrieval measurement all move | `packs/agent-skill-engineering/tests/fixtures/` | this spec | Partition test; re-measured retrieval and negative records | Every fixture digest matches the tree it describes |
| Current architecture | The planned architecture names composition floors and runtime profiles as unimplemented | `docs/architecture/agent-skill-engineering.md` | this spec | Section names the shipped floors, the pilot profile, and what stays `PLANNED` | Document states which slice-3 surfaces exist and which remain |
| Interface compatibility | `profile_provenance` and `stale-profile` are reached today only through the provider's own contract-version staleness; neither carries a capability-lifecycle meaning | `packs/agent-skill-engineering/tests/fixtures/provider-cases.json` and the provider suite | this spec | Provider case whose expected status the oracle derives from a ledger row rather than echoes | A named case id whose removal reddens a named assertion |
| Spec index | The active-spec table carries one row per spec with its shape and AC/task counts | `docs/specs/README.md` | this spec | Row matches the shipped spec | Row states the shipped shape and the final AC and task counts |
| Release history | Pack behavior changes for installers | `docs/product/changelog.md`, `pack.toml`, `.claude-plugin/plugin.json` | this spec | Version bump in lockstep; topmost pack entry | `0.3.0` to `0.4.0` in both manifests, one changelog entry |
| Maintainer procedure | Slice 3b needs the ledger's field contract and the redirect rule | this spec's `qa.md` | this spec | QA record naming the ledger schema and its probe boundary | `qa.md` records the ledger contract, the residual, and gate results |
| Reusable learning | Capture gates fire at `spec-approved` and `plan-locked` | `project-knowledge` producer profile | work-loop | Capture receipts, or a recorded unavailability | Receipts exist or `project-knowledge unavailable` is recorded |

## Boundaries

### Always do

- Record a capability claim's source identity as the URL that served the content
  after every redirect, together with the date it was retrieved and the product
  version or last-updated date the source exposed, or the literal `none exposed`.
- Classify a capability honestly against its evidence. A claim with a source but
  no passing probe is `experimental`, never `verified`.
- Keep the three composition-floor topics free of runtime-specific behavior, and
  keep runtime-specific behavior inside the profile topic.
- Re-measure the retrieval record and the generic-negative record after admission
  moves the binding digests, rather than re-stamping either.
- State degradation wherever the floor names a capability a runtime may lack.

### Ask first

- Before admitting any leaf beyond the four this spec names.
- Before changing the closed set of five unavailable authoring modes.
- Before adding a dependency to make a predicate categorical, including a
  CommonMark parser.
- Before changing the fixed size of the forty-case generic-negative set.
- Before widening the promotion-class restriction that today admits only
  language-specific topics to the `single-ecosystem-contract` class.

### Never do

- Never advertise a capability as supported on evidence weaker than `verified`.
- Never let a profile's roll-up be a declared string that no test recomputes from
  the rows beneath it.
- Never cite this repository's own paths, specs, ADRs, RFCs, acceptance-criterion
  identifiers, or `workspace.toml` inside shipped pack content.
- Never introduce a new top-level directory, a new module boundary, or a new
  runtime dependency for this slice.
- Never write a capability claim for a runtime this slice does not profile, and
  never infer one runtime's behavior from another's.

## Testing Strategy

- **Topic admission, basis fields, and source parity: TDD.** The admission record
  and the shipped projection are two representations of one fact set, so the
  invariant compresses to an equality and a wrong implementation is detectable.
- **Source-identity shape: TDD. Post-redirect provenance: visual / manual QA.**
  That a URL is absolute, non-relative and not repository-internal is a form
  check an offline suite makes. That it is the location serving the content after
  every redirect is not, because establishing it needs a fetch the pack suite
  cannot perform; its evidence is the retrieval record.
- **Lifecycle-state transitions and the profile roll-up: TDD.** The state
  function and the roll-up are pure over `(rows, reference_date)`. Tests drive
  synthetic dates so the suite stays deterministic; a date-dependent assertion
  against the wall clock would redden unrelated work on a timer.
- **Router behavior per lifecycle state: TDD, at integration surface.** Each
  state's router response is observable only across the provider seam, so the
  check drives the contract rather than the state function.
- **Retrieval precision, recall, and the negative set: goal-based check.** The
  existing gate recomputes the measurement from a recorded independent run; this
  slice re-measures and the same thresholds apply unchanged.
- **The Claude Code capability probes: visual / manual QA.** Each probed row
  records the gesture and the observed outcome, because the evidence is runtime
  behavior rather than a value a unit test can assert.
- **Shipped-statement agreement: goal-based check.** A scan over shipped surfaces
  compared against the admitted set.

## Acceptance Criteria

- [ ] **AC1 — The four named leaves are admitted, each on a named basis.**
  `skills-and-subagents-common-floor` and `plugin-package-common-floor` are
  admitted on the `observed-practice` basis; `hooks-common-floor` and
  `claude-code-skills-subagents-hooks-and-plugins` are admitted on the `doctrine`
  basis, the first under the `two-runtime-public-contract` promotion class and
  the second under `single-ecosystem-contract` carrying that class's ecosystem,
  version range with an explicit upper bound, fixture, and non-generalization
  statement. Each topic carries every field its named basis requires.

- [ ] **AC2 — The taxonomy is unchanged and the partition holds.** The taxonomy
  declared at `docs/rfc/0097-agent-skill-engineering.md` D3 stays at 36 leaves.
  Every leaf appears in the admitted set or the absence register, never both and
  never neither. The admitted set holds 16 topics and the register holds 20, and
  the register's size is asserted against a declared expected count rather than
  inferred.

- [ ] **AC3 — Every admitted topic carries the eight required sections.** Each of
  the four new topics carries the same ordered section set every shipped topic
  carries, and every `## Related topics` entry resolves to an admitted topic.

- [ ] **AC4 — The composition floors carry no runtime-specific behavior.** No
  floor topic names an event name, matcher token, configuration scope, output
  protocol, or file path belonging to any runtime the corpus profiles. The
  forbidden subject set is fixed by a stated rule — the runtimes named in
  RFC-0097 D3's profile table together with the runtimes carrying ledger rows —
  rather than by a list written into this criterion, because a runtime release
  adds identifiers and a written list would be defeated by the next one.

- [ ] **AC5 — Each floor covers the subjects its authority assigns it.** The
  skills-and-subagents floor answers each of the eight capability questions
  RFC-0097 D3 states and carries the conservative default it names. The hooks
  floor draws each of the six distinctions D3 states. The plugin floor covers
  each of the seven concerns D3 states. A floor omitting one of its subjects
  fails.

- [ ] **AC6 — Every Claude Code capability row the authority requires exists.**
  The ledger carries a row for each of the seven capabilities RFC-0097 D3's
  profile table assigns Claude Code. The required-capability set names the
  authority it transcribes and its expected count of 7, and that transcription is
  checked before completeness is evaluated, so deleting a capability from both the
  rows and the required set fails rather than passing.

- [ ] **AC7 — Every capability row carries its provenance set.** Each row names at
  least one source with a non-empty title and an absolute URL that is neither
  relative nor repository-internal; that source's `retrieved_at` date; the
  source's exposed version or last-updated date, or the literal `none exposed`;
  the runtime, the surface the claim applies to, and the operating system it was
  observed on; the row's claim scope; its last verification date; and its
  revalidation trigger. A row missing any of these is rejected rather than
  defaulted.

- [ ] **AC8 — Each recorded source identity is the post-redirect location.** For
  every source the ledger names, the retrieval record shows the URL that served
  the content after every redirect was followed, and the recorded identity is
  that URL rather than a location that redirects to it.

- [ ] **AC9 — Each of the four lifecycle states is produced by a distinct named
  input.** `verified`, `experimental`, `stale`, and `unavailable` are each
  produced by an input the record names. Where two entry conditions co-occur —
  an absent capability whose window has also elapsed — the resolution order is
  stated, so the outcome is determined rather than left to evaluation order.

- [ ] **AC10 — A shipped row's recorded state equals its computed state.** For
  every row in the ledger, the state recorded on the row equals the state computed
  from that row's own fields at the ledger's stated reference date. A row whose
  recorded state is edited away from its computed state fails.

- [ ] **AC11 — Verified rows rest on a recorded probe.** At least three Claude
  Code rows carry a probe record naming the gesture performed and the outcome
  observed, and no row anywhere in the ledger carries the `verified` state without
  such a record. The classification each probe supports follows from its evidence
  and is not fixed in advance.

- [ ] **AC12 — Window elapse is computed from stated values.** The Claude Code
  profile declares a verification window of 90 days, which is also the maximum
  RFC-0097 D3 permits any profile to declare; a profile declaring more than 90 is
  rejected. Holding a row's fields fixed and advancing only the reference date past
  the declared window changes that row's state from `verified` to `stale`. Because
  the declared window and the permitted maximum are equal here, the declared window
  is the limit that fires on the staleness route and the 90-day maximum binds only
  the validation route. RFC-0097 D3's two other `stale` entry conditions — a
  relevant release landing, and a source changing without revalidation — are
  operator-driven through each row's revalidation trigger and are not computed.

- [ ] **AC13 — The shipped projection is validated at a stated date.** The state
  each topic body projects is the state computed at the ledger's recorded
  `evaluated_at` date, and that date lies inside every row's declared window. A
  projected state disagreeing with the state computed at that date fails.

- [ ] **AC14 — The roll-up maps required rows to a profile state.** A profile
  resolves `complete-current` when every required row is present and no required
  row is `stale`; `needs-revalidation` when a required row is `stale`; and
  `incomplete` when a required row is absent. A row recorded `unavailable` does
  not prevent `complete-current`.

- [ ] **AC15 — The recorded roll-up equals the recomputed roll-up.** The roll-up
  stored on each profile equals the value recomputed from that profile's rows. A
  roll-up edited away from its recomputed value fails.

- [ ] **AC16 — A stale selection returns provenance without guidance.** A request
  selecting a row whose computed state is `stale` returns status `stale-profile`
  with `profile_provenance` populated, `guidance` empty, and a `diagnostic` that
  distinguishes an elapsed capability window from the provider's own stale
  contract version. The status is derived from the selected row's computed state,
  not echoed from the request.

- [ ] **AC17 — An experimental selection returns sourced facts and a warning.** A
  request selecting a row whose computed state is `experimental` returns
  `profile_provenance` populated, a non-empty `warnings` entry naming the
  unprobed status, and no statement that the capability is supported.

- [ ] **AC18 — An unavailable selection returns the limit and its provenance.** A
  request selecting a row whose computed state is `unavailable` returns
  `profile_provenance` populated, `guidance` limited to the recorded limit, and no
  behavior inferred from another runtime.

- [ ] **AC19 — A mixed-state request reports each state separately.** A request
  selecting rows of differing states reports each selected row's own state and the
  profile roll-up as separate values, rather than one aggregate state standing for
  all of them.

- [ ] **AC20 — The unavailable authoring modes stay a closed set of five.**
  `runtime-package`, `runtime-profile`, `plugin`, `hook`, and `subagent` remain
  the five unavailable authoring modes, each returning the versioned unavailable
  result.

- [ ] **AC21 — The recorded activation observation stays in force.** Both
  user-facing workflow `SKILL.md` files and both eval query fixtures are unchanged
  from their shipped bytes, so the digests the recorded activation observation
  pins still match the tree.

- [ ] **AC22 — Every admitted topic has at least two declared solo cases.** The
  retrieval case set declares at least two cases whose expected topic set is
  exactly that topic, for each of the 16 admitted topics.

- [ ] **AC23 — Every admitted topic is measured as selected alone at least
  twice.** In the recorded independent measurement, each of the 16 admitted topics
  is the sole selected topic for at least two prompts. This is a different
  population from AC22: declaring a solo case does not make the measurement
  return it alone.

- [ ] **AC24 — The measurement meets its thresholds.** On the re-measured record,
  precision is at least 0.90, recall is at least 0.90, the exact-selection rate is
  at least 0.90, the share of cases returning at most three topics is at least
  0.90, and every case declaring no topic returns none.

- [ ] **AC25 — The generic-negative set is unchanged in size and answered no more
  than twice.** The negative set holds exactly 40 prompts, and at most 2 of them
  return any topic.

- [ ] **AC26 — Inherited foundation pins hold, and any re-take is accounted.**
  Every pin recorded in
  `packs/agent-skill-engineering/tests/fixtures/foundation-retrieval-pins.json`,
  whose content at this spec's approval is
  `sha256:837a08ce8d8a93f1406890000ded3ea0974e8ae2cd499a74447905ac0cf410cc`, holds
  at its recorded value; or each pin whose value differs is recorded in `qa.md`
  with its prior and current value, and the count of recorded re-takes equals the
  count of pins whose value differs.

- [ ] **AC27 — Shipped statements agree with the admitted set.** No shipped
  surface states that the corpus lacks composition floors or a Claude Code
  profile, and every shipped statement of a topic count states 16. The surfaces
  bound by this criterion are every file under the pack's published tree plus the
  pack's marketing page at `web/src/content/packs/agent-skill-engineering.md`, and
  the check enumerates that set by walking those trees rather than from a
  hand-maintained list.

- [ ] **AC28 — The milestone string names this slice.** The initiative's milestone
  string names the composition-floors slice.

- [ ] **AC29 — The workspace records this spec's delivery state.** This spec is
  registered under `ini-009` shipped work with `repo-origin` provenance naming the
  brief as its parent.

- [ ] **AC30 — Both pack manifests carry the same new version.** `pack.toml` and
  `.claude-plugin/plugin.json` both state `0.4.0`.

- [ ] **AC31 — The changelog carries one entry for this pack.** `docs/product/changelog.md`
  carries exactly one new entry for the `agent-skill-engineering` pack, and it is
  the topmost entry for that pack.

- [ ] **AC32 — The architecture document states what exists.** `docs/architecture/agent-skill-engineering.md`
  names the three shipped composition floors and the Claude Code profile as
  implemented, names the seven remaining profiles as not implemented, and remains
  `PLANNED`.

- [ ] **AC33 — The spec index row matches this spec.** `docs/specs/README.md`
  carries a row for this spec stating its shape and its final AC and task counts.

## Follow-ons

- INI-009 slice 3b owner, via the slice 3b row in
  `docs/product/briefs/agent-skill-engineering.md`: the seven remaining runtime
  profiles — Codex, GitHub Copilot, Cursor, Kiro IDE, Kiro CLI, Gemini CLI, and
  Google Antigravity — which fill the ledger this slice establishes and complete
  RFC-0097's eight-profile M2 roll-up condition.
- INI-009 slice 3b owner, same row: the two behavior fixtures
  `docs/specs/agent-skill-engineering-corpus/spec.md` assigns to slice 3 —
  subagent composition, and hook/plugin design — which RFC-0097's Gate 2 M2
  measure also names. This slice ships neither.
- INI-009 slice 3b owner, same row: the `runtime-package` authoring mode, which
  the corpus slice also assigns to slice 3 and which stays unavailable here by
  owner decision, together with the
  `compatibility-and-runtime-package-patterns` leaf whose recorded admission
  condition is the runtime profiles that make packaging claims verifiable.
- INI-009 slice 6 owner, via the slice 6 row in
  `docs/product/briefs/agent-skill-engineering.md`, which already owns freshness
  policy: a wall-clock freshness check reporting elapsed verification windows
  across profiles. This slice makes window elapse computable and validates the
  shipped projection at the ledger's recorded evaluation date; a gate reading the
  wall clock would redden unrelated work on a timer, which is why it is not
  built here.

## Assumptions

- Technical: exactly 11 taxonomy leaves are reserved for runtime composition, of which 3 are composition floors (source: `packs/agent-skill-engineering/okf/agent-skill-engineering-foundation/concepts/declared-absent/unpopulated-leaves.md`, 24 `##` blocks of which 11 read "Reserved for the later slice that covers runtime composition")
- Technical: topic frontmatter is a closed five-key set carrying no provenance, which lives in the body's `## Provenance and lifecycle` section (source: `packs/agent-skill-engineering/okf/agent-skill-engineering-foundation/concepts/trust-boundaries-and-instruction-provenance.md:1-7`)
- Technical: the provider contract declares `runtime`, `profile_provenance` and `stale-profile`, and shipped cases already reach all three — `runtime` 5 times, `profile_provenance` 8, `stale-profile` 2. What is absent is a capability-lifecycle meaning for them, not their reachability. An earlier draft of this spec asserted they were unreached; that assertion was checked against the file declaring the fields rather than the file exercising them, and was false (source: `packs/agent-skill-engineering/tests/fixtures/provider-cases.json`, counted 2026-08-31; declaration at `packs/agent-skill-engineering/tests/fixtures/provider-contract.json:4,8,10,12`)
- Technical: `stale-profile` today means every candidate provider's `contract_version` is stale, and the oracle returns an eligible provider's declared status verbatim, so a case can assert the status it declares. A capability-lifecycle meaning must therefore be derived, and the two conditions distinguished by `diagnostic` (source: `packs/agent-skill-engineering/tests/integration/test_provider_contract.py:241-242`, `:266-271`, `:292-296`)
- Technical: all five composition authoring modes are `unavailable` today (source: `packs/agent-skill-engineering/tests/fixtures/unsupported-mode-cases.json`)
- Technical: admitting a topic moves binding digests on both recorded runs. The retrieval record's four all change value; on the negative record three change, because its `case_fixture_digest` binds `generic-negatives.json`, which this slice does not edit. Both records assert four digests each (source: `packs/agent-skill-engineering/tests/pack/test_foundation_corpus.py:278-292` and `:491-502`)
- Technical: an admitted topic must have at least two *declared* solo cases and at least two *measured* solo selections, and these are different populations (source: `packs/agent-skill-engineering/tests/pack/test_foundation_corpus.py:253-259` and `packs/agent-skill-engineering/tests/pack/test_corpus_admission.py:816-831`)
- Technical: the recorded activation observation pins digests over the two workflow skills only, not the router, so leaving those two `SKILL.md` files and their eval query fixtures unedited keeps it in force (source: `packs/agent-skill-engineering/tests/pack/test_pack_boundary.py:175-190`)
- Technical: `observed-practice` requires observations from at least two distinct packs. Seven packs ship agents and 23 ship a plugin manifest, but only `packs/core` ships hooks, so `hooks-common-floor` cannot take that basis honestly and takes `doctrine` instead (source: probe — `find packs -type d -name hooks -path '*.apm*'` returned one pack on 2026-08-31; rule at `packs/agent-skill-engineering/tests/pack/test_corpus_admission.py:297-298`)
- Technical: the `single-ecosystem-contract` promotion class is today restricted to language-specific topics, so admitting a runtime-profile topic under it requires widening that restriction — a change this slice makes deliberately rather than discovering mid-build (source: `packs/agent-skill-engineering/tests/pack/test_corpus_admission.py:140-144`)
- Technical: Claude Code's first-party documentation states the isolated-context, nesting-depth and tool-inheritance claims, and exposes product version v2.1.251 (source: probe — `https://code.claude.com/docs/en/sub-agents` retrieved 2026-08-31)
- Technical: Claude Code documentation URLs under `docs.claude.com/en/docs/claude-code/` 301-redirect to `code.claude.com/docs/en/`, so a pre-redirect URL is not a durable source identity (source: probe — WebFetch of `https://docs.claude.com/en/docs/claude-code/sub-agents` returned `301 Moved Permanently` on 2026-08-31)
- Process: splitting one RFC follow-on into two brief slices needs no RFC amendment; follow-on 3 became brief slices 2a and 2b (source: `docs/rfc/0097-agent-skill-engineering.md:620` compared against `docs/product/briefs/agent-skill-engineering.md:172-173`)
- Process: the basis judgment for all four leaves — which claims stand as doctrine and which as observed practice — was made by the spec author and adversarially reviewed at the spec stage, as RFC-0097's Errata requires each slice to name (source: `docs/rfc/0097-agent-skill-engineering.md:685-691`; review artifacts under `.context/reviews/`)
- Process: two `tools/test_guide_typed_asides.py` failures reproduce on `origin/main` and are owned elsewhere (source: probe — `python3 -m pytest tools/test_guide_typed_asides.py -q` returned 2 failed, 2 passed; `workspace.toml:284`)
- Product: slice 3 is cut into 3a and 3b, this spec being 3a (source: user confirmation 2026-08-31)
- Product: `runtime-package` stays deferred and its package-lifecycle rows are out of scope (source: user confirmation 2026-08-31)
- Product: slice 3a carries the Claude Code profile as a pilot so the ledger schema has a consumer that can fail (source: user confirmation 2026-08-31)
- Product: the `subagent`, `hook` and `plugin` authoring modes stay `unavailable` until profile data supports stating degradation (source: user confirmation 2026-08-31)
- Product: `runtime-profile` also stays `unavailable` as an authoring mode even though this slice ships a runtime profile. A profile is retrievable knowledge; the mode would author one, and authoring guidance needs more than one profile's worth of evidence to state what varies. It becomes available no earlier than the slice that completes the eight (source: user confirmation 2026-08-31)
- Product: the ledger carries `surface` and `os` per row because the brief's verification record requires them and four of the eight profiles have surface-dependent behavior; omitting them in 3a would make them un-backfillable in 3b without re-probing (source: `docs/product/briefs/agent-skill-engineering.md:145-146`; RFC-0097:323-326)
