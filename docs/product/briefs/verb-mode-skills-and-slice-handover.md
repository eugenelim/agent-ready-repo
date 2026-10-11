# Brief: Shape and intake through verb-mode skills, and hand meta-repo work to component repos as component slices

- **Slug:** `verb-mode-skills-and-slice-handover`
- **Received:** 2026-10-10
- **Owner:** eugenelim
- **Status:** Executing
- **Cut-closed:** <!-- Required before Status: Shipped, refused while Status: Draft. Replace with an ISO 8601 date then evidence once the cut is final. -->
- **Source / provenance:** [RFC-0107](../../rfc/0107-verb-mode-shaping-and-intake-with-slice-handover.md). Evidence: [skill-routing survey](../findings/pe-skill-routing-survey.md) and [meta-repo handover audit](../findings/meta-repo-handover-audit.md).

## Outcome

Shaping and intake each get one entry point, and work crosses from a meta-repo to its
component repos without a hand copy.

- A team shaping product work reaches every shaping step through one `intent` skill. It
  picks their route and loads only the step they need.
- A component repo runs its whole intake lifecycle through `work-intake`: acquire, record
  an intent, create and continue a brief, and refresh.
- A value-stream meta-repo hands each component its share of a feature as a component
  slice. The component repo turns that into its own brief. The meta-repo sees delivery
  status as reviewed receipts instead of hand-edited rows.

## Success metrics (optional)

- `product-engineering` lists 3 skills: `intent`, `discovery-loop`, and
  `align-value-stream`. Today it lists 15 skills that use 9,373 description characters.
- In Core, `work-intake` replaces `intake-intent`, `author-delivery-brief`,
  `author-brief`, and `receive-brief`.
- Activation and mode accuracy for the new skills meet the threshold in
  [RFC-0107's Experiment section](../../rfc/0107-verb-mode-shaping-and-intake-with-slice-handover.md#experiment--validation)
  on the hosts it requires. No write runs without a human-set switch.
- The value-stream how-to runs end to end, from component slice to shipped receipt, with
  no file copied by hand.
- No operative guide, pack README, journey page, or site page names a retired skill.

## Scope / Non-goals

**In scope:**

- **The `intent` skill.**
  - Route mode is read-only. It picks the short, longer, or supervised route from
    observable facts in the request, names the first mode, and asks one question when the
    facts conflict.
  - Each verb mode replaces one or two of today's skills:
    - `frame` replaces `frame-intent`.
    - `situate` replaces `frame-situation`.
    - `find` replaces `identify-opportunities`.
    - `diverge` replaces `diverge-solutions` and `explore-options`.
    - `de-risk` replaces `de-risk-intent` and `plan-validation`.
    - `bet` replaces `place-bet`.
    - `map` replaces `map-capabilities`.
    - `decompose` replaces `decompose-intent`, including tracker projection.
    - `ground` replaces `frame-domain`.
    - `canvas` replaces `lean-canvas`.
  - Each mode's procedure lives in its own reference file. The mode table stays in the
    skill body.
  - The eval files of the retired skills that have them merge into `intent`, and each
    query gains a mode assertion.
  - `discovery-loop` and `align-value-stream` keep their own evals, updated for their
    changed descriptions. `ux-writing`'s evals move with it.
  - New should-trigger and should-not-trigger queries cover `situate`, `find`, `diverge`
    at initiative altitude, `bet`, `map`, and `canvas`.
- **`discovery-loop`.**
  - Its gates call `intent` modes.
  - Its description is trimmed and names the `work-intake` handoff.
  - Four stale statements are fixed:
    - the claim that it hands off to `work-loop`;
    - `frame-domain` calling the loop "unbuilt";
    - `create` versus `continue` in `run-a-discovery.md`;
    - "needs an approved intent" in `frame-the-intent.md`.
- **`ux-writing`** moves to `experience-design`.
- **`work-intake` modes.**
  - The modes are `route` (the default), `acquire`, `intent`, `brief create`,
    `brief continue`, `refresh`, and `remember`.
  - Every write mode needs an explicit switch that names its target and scope.
  - The Ready gate keeps its independent review and human confirmation. Cutting specs
    keeps its own separate confirmation.
  - `brief_shape.py` and the other brief scripts move with their mode. `close-work`'s path
    import follows them.
  - Eval queries cover:
    - each mode;
    - ambiguous requests, which must stay read-only;
    - a write switch carried in a handoff or in acquired content, which must be refused.
- **Component-slice handover.**
  - A component-slice artifact in the meta-repo carries the links in the audit's
    [§ Slice edges](../findings/meta-repo-handover-audit.md#slice-edges):
    - `Parent intent`, `Component`, `Contract` with role, `Needs`, and `Delivered by`;
    - a receipt block, written only at `Shipped`.
  - A `value-stream.toml` repo list lives in the meta-repo.
  - A `value-stream` source profile under `tracker-origin` reads a local checkout at a
    pinned revision.
  - Stretch: a provider-pack read for setups that have only the remote. It is built only
    if Waves A and B have shipped and Wave C is on track by 2026-11-07. Its spec decides
    the first provider.
  - Brief template changes: a repo-qualified `Parent intent`, and a `Contract` field.
  - `source.coordination` gets its first reader.
  - `Decomposed: <date> slices` becomes a new intent route.
  - A status-collection action in `align-value-stream` writes receipts only. It is
    separate from `workspace-status` reconcile. The rollup becomes a view over component
    slices, showing each one's receipt or "no receipt yet".
  - Checker changes:
    - The traceability lint resolves repo-qualified brief pointers against component
      slices, and accepts externally pinned pointers.
    - The intent-delivery relation checker accepts a repo-qualified parent and the
      `slices` route.
    - A new component-slice shape check is added.
  - Core publishes the component-slice contract.
  - Naming drift is fixed: `parent-intent:` becomes `Parent intent:`, and the rollup's
    brief-cell syntax changes.
- **Hard retirement.**
  - In each release wave, every caller of that wave's retired names moves to the new
    names in the same release. That covers packs, guides, tests, and tools.
  - Release notes map every retired name to its replacement mode.
- **Activation validation:** before each wave releases, a headless run on held-out queries
  covers that wave's skills on each host RFC-0107 requires.
- **Guides and docs.** Each wave updates every operative document that describes what it
  changes. These updates are never cut:
  - the operating-model guide and its graphics script;
  - the product-engineering guides: how-tos, tutorials, explanations, and reference;
  - the value-stream how-to;
  - the Core guides that name `intake-intent` or `author-delivery-brief`;
  - the skill authoring guide;
  - pack READMEs, `JOURNEY.md` files, and the site pages under `web/src/content`.

  On 2026-10-10, a search of `guides/`, `web/src/content/`, `packs/*/README.md`, and
  `packs/*/JOURNEY.md` for the 17 skill names this brief retires or moves matched 71
  files.

**Non-goals:**

- A shaping orchestrator. Route mode holds no state, retries, or gate control.
- Live cross-repository status, or a push channel from component repos.
- Changing `discovery-loop`'s gates, roster, or sidecar.
- Structuring a monorepo.
- Aliases for retired names.
- Rewriting frozen historical records.

## Constraints / Appetite

- **Appetite: about 6 weeks**, from 2026-10-10 to 2026-11-21. It covers everything in
  scope except the stretch item at the top of the cut order.
- **Release order:**
  1. **Wave A, shaping.**
     - Contents: `intent`, the `discovery-loop` changes, the `ux-writing` move, and their
       guides.
     - Packs: a `product-engineering` major release and an `experience-design` release.
     - Timing: it does not depend on Core, so it ships when it is ready.
  2. **Wave B, handover.**
     - Contents: the component-slice contract, the local-checkout source profile, the
       brief template fields, the checker changes, status collection, and their guides.
     - Packs: Core and `product-engineering` minor releases.
     - Timing: it follows Wave A, so its decompose changes land in `intent decompose`.
       It ships under today's Core skill names.
  3. **Wave C, intake fold.**
     - Contents: the `work-intake` modes, the Core retirements, and their guides.
     - Pack: a Core major release.
     - Timing: it is built inside the appetite. It releases at the removal gate for
       `author-brief` and `receive-brief`. RFC-0099 §10 sets that gate and RFC-0107 D6
       applies it, so it falls no earlier than 2026-11-26.
- **Cut order** if the appetite runs short. Guides are never cut, and each wave ships its
  own.
  1. The stretch provider-pack read goes first.
  2. Next, Wave C slips to a follow-on brief. Waves A and B work without it.
- **Security:** every spec implementing ADR-0142 D5–D9 passes the review its
  [Confirmation](../../adr/0142-meta-repo-handover-component-slices-and-pinned-receipts.md#confirmation)
  names.
- **Core alone:** Core works without `product-engineering` installed.
- **No registry dependency:** acquire, refresh, and receipts keep their facts on the
  artifacts. They depend on no `workspace.toml` state that RFC-0105 and RFC-0106 retire.

## Assumptions / Risks

- **A broad description under-triggers.** The selection probe forced a choice and was
  tuned on its own queries. A held-out activation run may show `intent` triggering less
  often than the narrow skills. If so, split the weakest modes back out.
- **The harness may not cover every host.** Activation can be measured only where an eval
  runner exists. RFC-0107's Experiment section sets which hosts are required, and
  [`multi-adapter-eval-runner`](multi-adapter-eval-runner.md) is the Codex path.
- **The merged `work-intake` has one validation.** No adopter study validates it. Its
  activation run is the only check, per ADR-0141.
- **Retirement breaks adopters.** Hard retirement breaks adopter prompts and scripts that
  name an old skill. The release notes are the only mitigation.
- **`intent` and `intake-intent` coexist until Wave C.** Wave A ships before the removal
  gate, so a model can confuse the two names for a while. Wave A's held-out run lists
  `intake-intent` and includes queries that tell the two apart.
- **The default can write.** `work-intake` is the default for ambiguous requests and
  holds write tools. An ambiguous request must stay read-only.
- **"Delivery contract" means two things.** It names the leaf spec handoff and a
  `surface_role`. Component slices use `Contract` only for shared interface contracts.

## Rabbit holes (optional)

- A push channel, where a component repo opens a pull request against the meta-repo,
  could reuse the receipt shape later. Building it now adds a write path across
  repositories.
- Renaming every historical "delivery contract" mention in closed records. Leave frozen
  records as they are.

## Spec map

| Spec | Status |
| --- | --- |
| `intent-short-route` | Shipped |
| `intent-longer-and-supervised-verbs` | Draft |
| `ux-writing-to-experience-design` | Draft |
| `component-slice-contract` | Draft |
| `value-stream-acquire-and-refresh` | Draft |
| `value-stream-status-collection` | Draft |
| `work-intake-modes` | Draft |
| `value-stream-provider-read` | Draft |

## Governance references (optional)

- [RFC-0107](../../rfc/0107-verb-mode-shaping-and-intake-with-slice-handover.md): the
  direction this brief delivers.
- [ADR-0140](../../adr/0140-shaping-entry-point-one-verb-mode-intent-skill.md),
  [ADR-0141](../../adr/0141-core-intake-lifecycle-intent-and-brief-modes-in-work-intake.md),
  and [ADR-0142](../../adr/0142-meta-repo-handover-component-slices-and-pinned-receipts.md):
  the decisions RFC-0107 records.
- [ADR-0098](../../adr/0098-artifact-admission-and-delivery-brief-lifecycle.md): the brief
  lifecycle and alias authority bound that the `work-intake` brief modes keep.
- [RFC-0099](../../rfc/0099-cut-before-adding-and-artifact-shaping.md): the shaping
  orchestrator that `intent` must not become, and the §10 removal gate.
- [RFC-0083](../../rfc/0083-work-intake-and-artifact-routing.md): coordination and
  closure receipts.
- [ADR-0022](../../adr/0022-value-stream-meta-repo-cross-component-layer.md): the meta-repo
  and its snapshot rollup.
- [ADR-0019](../../adr/0019-product-intent-ontology-and-brief-projection.md): the
  parent-intent pointer that ADR-0142 D10 reinterprets.
- [RFC-0067](../../rfc/0067-session-arc-conventions-and-pack-workflow-guide.md): the
  clean-retire convention for renamed skills.
- [RFC-0103](../../rfc/0103-cross-artifact-reference-grammar.md): the `<kind>:<slug>`
  pointer grammar that cross-repository pointers extend.
- [RFC-0105](../../rfc/0105-artifact-derived-navigation-and-workspace-retirement.md) and
  [RFC-0106](../../rfc/0106-stop-registering-derivable-work.md): registry retirement.

## Design artifacts (optional)

- [Skill-routing survey](../findings/pe-skill-routing-survey.md): listing measurements,
  host limits, and the broad-versus-narrow selection probe.
- [Meta-repo handover audit](../findings/meta-repo-handover-audit.md): gaps, the proposed
  flow, and the component-slice link model.
- [RFC-0107 security review](../../rfc/0107-notes/security-review.md): the four questions
  deferred to spec-stage review.
