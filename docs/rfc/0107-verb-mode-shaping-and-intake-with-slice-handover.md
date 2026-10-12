# RFC-0107: Verb-mode shaping and intake skills, with a slice handover across repositories

- **Status:** Accepted
- **Author:** eugenelim
- **Approver:** eugenelim
- **Date opened:** 2026-10-10
- **Date closed:** 2026-10-10
- **Decision weight:** heavy. It retires published skill names, supersedes parts of
  several accepted records, and lets Core read a second repository.
- **Related:** [ADR-0098](../adr/0098-artifact-admission-and-delivery-brief-lifecycle.md),
  [RFC-0099](0099-cut-before-adding-and-artifact-shaping.md),
  [RFC-0083](0083-work-intake-and-artifact-routing.md),
  [ADR-0022](../adr/0022-value-stream-meta-repo-cross-component-layer.md),
  [ADR-0019](../adr/0019-product-intent-ontology-and-brief-projection.md),
  [RFC-0103](0103-cross-artifact-reference-grammar.md),
  [RFC-0105](0105-artifact-derived-navigation-and-workspace-retirement.md),
  [RFC-0106](0106-stop-registering-derivable-work.md),
  [RFC-0067](0067-session-arc-conventions-and-pack-workflow-guide.md),
  [RFC-0053](0053-the-discovery-loop.md),
  [skill-routing survey](../product/findings/pe-skill-routing-survey.md),
  [meta-repo handover audit](../product/findings/meta-repo-handover-audit.md)

## Terms used here

- **Skill listing:** the name and description of every installed skill. A host such as
  Claude Code or Codex preloads it so the model can pick a skill. The body of a skill
  loads only when it is picked.
- **Verb mode:** one named procedure inside a skill, such as `intent de-risk`. Its
  instructions load only when that mode is chosen.
- **The *Shape it* stage:** the stage of the
  [operating model](../../guides/_shared/explanation/the-operating-model.md) where work is
  framed and tested before anyone builds it. It has three routes:
  - the short route: frame, test, and break down one bet;
  - the longer route: six steps for an unclear problem or a large bet;
  - the supervised route: `discovery-loop`, for a new product area.
- **Value-stream meta-repo:** a coordinating repository with no application code. It
  holds feature intents that span several **component repos**, each of which owns one
  part of the system.
- **Delivery brief:** a component repo's plan for one coordinated outcome.
  - It passes a **Ready gate**, an independent review plus one human confirmation.
  - A separate human confirmation then approves cutting it into specs.
  - Each spec selected from a brief is a **delivery slice**.
- **Component slice:** the new artifact this RFC proposes. It states one component
  repo's share of a meta-repo feature intent. It is not a delivery slice.
  - Until now, "per-component slice" in ADR-0019, ADR-0022, and the pack docs meant the
    component repo's delivery brief itself.
  - This RFC redefines the term as the meta-repo artifact the brief is written from (D4).
- **Acquire / refresh:** `work-intake`'s actions for bringing outside work into a repo
  at a recorded revision, and for re-reading it later. Each changed field is kept,
  accepted, or revised, and some fields lock once delivery starts. Tracker items such as
  GitHub issues already use this path.
- **Receipt:** a reviewed record that another repository's artifact reached a stated
  status at a stated revision. [RFC-0083](0083-work-intake-and-artifact-routing.md)
  introduced receipts.
- **Provider pack:** a pack such as `github` that owns access to one hosted service.

## Reviewer brief

- **Decision:** Replace the shaping stage's separate skills with one verb-mode `intent`
  skill. Fold Core's intent and brief authoring into `work-intake`. Hand work from a
  meta-repo to component repos as component slices that each component repo acquires.
- **Recommended outcome:** accept.
- **Change if accepted:**
  - `product-engineering` shrinks from 15 listed skills to 3, and `ux-writing` moves to
    `experience-design`.
  - In Core, `work-intake` absorbs four skills: `intake-intent`,
    `author-delivery-brief`, `author-brief`, and `receive-brief`.
  - A component repo writes its own brief from an acquired component slice. The meta-repo
    learns delivery status from receipts.
- **Affected surface:** skill names in `product-engineering`, `experience-design`, and
  Core; the source rules for delivery briefs; and Core's repository boundary.
- **Stakes:** costly to reverse. Retired names stop working.
- **Review focus:**
  - Is the case for superseding RFC-0099's exclusions strong enough?
  - Do the cross-repository read controls hold?
  - Is hard retirement acceptable?
- **Not in scope:**
  - mode names, file layout, field names and syntax, and checker changes;
  - schema values, versioning, and release order.

  The delivery brief and its specs own those.

## The ask

**Recommendation:** accept D1–D6.
- **Listing:** the shaping skills' listing falls from 8,401 to about 2,640 description
  characters, about 69%. That counts the 14 shaping skills today against `intent` at the
  1,024-character cap plus today's `discovery-loop` and `align-value-stream`.
  - `ux-writing` (972 characters) moves to `experience-design` and still counts against
    the host budget. Counting it, the installed total falls from 9,373 to about 3,610.
  - The survey's 66% figure differs because it also assumes a shorter `discovery-loop`
    description.
- **Routing:** the route choice gets one owner that runs.
- **Handover:** the meta-repo handover that the guides describe gets a skill that
  performs it.

**Why now.**
- Hosts fit every skill's listing entry into a fixed budget. Codex allows 8,000
  characters when it can't size the context window, and today `product-engineering` alone
  uses 9,373. Over the budget, Codex shortens descriptions and then drops skills.
- The choice between the three shaping routes exists only as prose, copied in five
  places.
- A meta-repo user can get a feature into a component repo only by copying a file by
  hand.

| ID | Question | Recommendation | Why | Decide by | Reviewer action |
| --- | --- | --- | --- | --- | --- |
| D1 | How many shaping entry points? | One verb-mode `intent` skill. `discovery-loop` and `align-value-stream` stay separate. | The listing falls by about 69%, and selection accuracy held in a probe | 2026-11-14 | Confirm, including the RFC-0099 supersession |
| D2 | What does `discovery-loop` become? | The supervised route `intent` hands to, not the router | Routing through a stateful loop charges every request its cost | 2026-11-14 | Confirm |
| D3 | Do Core's intake skills merge? | `intake-intent` and `author-delivery-brief` become `work-intake` modes | Acquire, intent, brief, and refresh are one lifecycle | 2026-11-14 | Confirm the ADR-0098 and RFC-0099 supersessions |
| D4 | Where is per-component delivery authority born? | The meta-repo writes component slices; each component repo acquires one and writes its own brief | One copy of each brief; reuses the acquire lifecycle | 2026-11-14 | Confirm the ADR-0022, RFC-0083, and RFC-0103 amendments |
| D5 | May Core read another repository? | Yes, at an immutable revision, only during acquire, refresh, and a separate status-collection action | Needed for D4; offline reconciliation is kept | 2026-11-14 | Confirm the controls |
| D6 | What happens to retired and moved names? | Hard retire with no alias, after every in-repo caller moves | Follows RFC-0067's clean-retire convention; an alias keeps the listing cost | 2026-11-14 | Confirm the breaking change |

## Problem & goals

### Problem

1. **Listing cost.** The 15 `product-engineering` skills take 9,373 description
   characters. Codex's fallback budget is 8,000 characters for all installed skills
   ([Codex skills](https://learn.chatgpt.com/docs/build-skills)).
2. **Colliding verbs.** `frame-intent`, `frame-situation`, and `frame-domain` share one
   verb. `explore-options` and `diverge-solutions` differ only by altitude.
3. **The route choice has no owner that runs.** The short, longer, or supervised route is
   chosen from prose in `frame-intent`. The same choice appears in four other documents,
   and nothing keeps them in step.
4. **Core splits one lifecycle across separate skills.** In a component repo these steps
   follow each other, but they have three owners plus two deprecated aliases:
   - acquiring work;
   - recording an intent;
   - creating and continuing a brief;
   - refreshing it from its source.
5. **No meta-repo handover exists.** ADR-0022 slices a feature intent into briefs that
   "cross into" component repos. `author-delivery-brief` writes only inside its own
   repository, so the only route is a hand copy. A hand copy leaves two authorities for
   one brief. RFC-0083 specified closure receipts on the parent intent, but they were never built.

### Goals

- Keep the shaping listing within a budget that leaves room for other packs.
- Give the route choice one owner that runs.
- Give each piece of cross-repository work one authority.
- Return delivery status to the meta-repo as reviewed evidence, not hand edits.

### Non-goals

- **An orchestrator.** `intent` holds no run state, retries, or gate control.
- **Live cross-repository status.** The meta-repo's status stays a snapshot.
- **Changing `discovery-loop`'s gates, reviewers, or saved state.**
- **Structuring a monorepo.**

## Proposal

### D1. One verb-mode `intent` skill

`intent` replaces 12 shaping skills. Its body lists its modes, so the model can choose
one without opening another file. Each mode has one entry condition, and its procedure
loads only when chosen.

With no verb, `intent` runs a read-only route mode:
- It picks the short, longer, or supervised route from observable facts in the request.
- It names the first mode to run.
- It asks one question when the facts conflict.
- It sends requests outside shaping to their owners.

Three skills stay separate:

- `discovery-loop` (D2).
- `align-value-stream`, which coordinates delivery across repositories. That is not
  shaping. When it was a mode, Sonnet chose no skill for 11 queries whose expected
  answer was `align-value-stream`.
- `ux-writing`, which moves to `experience-design` (D6).

**This supersedes part of RFC-0099.** RFC-0099 put a "generic shaping skill" out of
scope. It rejected a "generic shaping orchestrator" because it "recreates the overloaded
work-loop problem at a new altitude". That rationale held when listing cost was not
measured. Two facts change it:

- The listing cost is now measured, and the separate skills exceed a host budget on
  their own.
- Progressive disclosure answers the overload concern. A request loads the mode table
  and one mode's procedure, never every procedure. `intent` also holds no state or
  delivery machinery, which keeps it apart from the overloaded `work-loop`.

In a forced-choice probe, the revised `intent` listing matched today's selection
accuracy (see Evidence).

### D2. `discovery-loop` is the supervised route

`discovery-loop` stays a separate skill that the model can invoke. Requests like "run a
discovery" or "resume the X discovery" still reach it directly. `intent` hands it a raw
whole-product idea. At its gates it calls `intent` modes instead of separate skills, and
its description names its real handoff through `work-intake`.

### D3. `work-intake` absorbs intent and brief authoring

`intake-intent` and `author-delivery-brief` become modes of `work-intake`. Each
artifact's contract stays intact inside its mode.

**ADR-0098's revisit trigger has not fired.** It depends on an adopter routing study
that RFC-0099's errata waived on 2026-08-31. The study was never run, and no run is
scheduled. D3 rests on new evidence instead:

- The handover in D4 makes acquiring, recording, briefing, and refreshing one lifecycle
  in the component repo.
- D1's `intent` would otherwise sit next to `intake-intent`, two names a model could
  confuse.
- The listing cost falls by four entries.

D3 supersedes these clauses:
- ADR-0098's separate-owner decisions for intent and brief authoring (D1, D2, D4, D5);
- ADR-0098 D8's delegation targets. Until `author-brief` and `receive-brief` are removed
  (D6), they delegate to `work-intake`'s brief create and continue modes. ADR-0098 D9
  still applies, so they cannot widen the owner's authority.
- RFC-0099 D1's separate `intake-intent` entry point, and its `author-delivery-brief`
  brief entry point;
- the RFC-0099 §11 erratum to RFC-0083, which moved intent authoring out of
  `work-intake`.

No adopter study validates the merged `work-intake`. This RFC's Experiment section is
its only validation.

Guardrails:

- The default mode behaves read-only. It classifies and routes.
- Every mode that writes needs an explicit switch that names the target and scope. The
  routing step cannot grant it.
- Only the current human request can set that switch. A switch carried in a handoff
  object, a calling skill's output, or acquired content is refused.
- The brief Ready gate keeps its independent review and human confirmation. The
  separate confirmation before cutting specs also stays.
- Core still works without `product-engineering` installed.

### D4. Component slices carry work from a meta-repo to component repos

| Artifact | Lives in | Owns |
| --- | --- | --- |
| Feature intent | meta-repo | the outcome; its affected repos derive from its component slices |
| Component slice | meta-repo | one component's share of the outcome, and every cross-repo link |
| Delivery brief | component repo | how that repo delivers its share, from Ready to specs |
| Receipt | meta-repo | reviewed evidence of a component brief's final status |

The lifecycle:

1. The meta-repo cuts a feature intent into component slices.
2. The component repo acquires one at a pinned revision, under the same lifecycle rules
   Core applies to tracker items.
3. The component repo writes its own brief from it. The meta-repo never writes a delivery
   brief.
4. When the component slice changes, the component repo refreshes it.
5. The meta-repo collects each component brief's status and records receipts. The feature
   intent is fulfilled when every component slice has a shipped receipt.

**Ownership.**
- Core publishes the component-slice contract, so a component repo with only Core
  installed can acquire one.
- `product-engineering` writes component slices and owns status collection through
  `align-value-stream`.
- Core still imports nothing from `product-engineering`.

**Links.** A component slice links the intent tree, the component, shared contracts,
other component slices it depends on, and the component brief. Each cross-repository
link has one authoritative home, on the component slice. The component brief still carries
what ADR-0022 D5 requires: a `contract@version` reference and a read-only snapshot of
the contract. The component slice's pinned revision fixes both, and refresh keeps them
current.
Cross-repository pointers extend RFC-0103's `<kind>:<slug>` pointer grammar with a
repository qualifier. The specs fix the syntax.

**Registry independence.** RFC-0105 and RFC-0106 retire `workspace.toml` registration
step by step. Acquiring, refreshing, and recording receipts keep their facts on the
artifacts themselves, and depend on no registry state those RFCs retire.

D4 amends these records:
- ADR-0022 D3: briefs no longer cross into component repos; component slices are
  acquired instead.
- ADR-0022 D4 and ADR-0019 D9: the brief's parent pointer is now interpreted, as a
  cross-repository link. Interpreting it grants no read on its own (D5).
- ADR-0019 part 2: the product pack no longer writes the per-component brief. It writes
  the component slice, and the component repo writes the brief.
- ADR-0022 D9: status is collected by an explicit, pinned read. It is still never a live
  feed.
- RFC-0083 §4: closure receipts and the list of affected repositories move from the parent
  intent to its component slices.
- RFC-0103: its pointer grammar gains a repository qualifier.

### D5. Core may read a pinned revision of another repository

Two transports are allowed:
- a local checkout, whose path lives in user-scope configuration;
- a host API, through a provider pack.

A read may happen only during acquire, refresh, and the status-collection action in D4.
That action is separate from the offline reconciliation in RFC-0083 and
`workspace-status`. Existing reconcile surfaces gain no access to other repositories.
Dependency evaluation still reads only local receipts, so reconciliation reaches the
same answer offline.

For component-slice sources only, this supersedes the rule that an external locator is
passive provenance and is never read. RFC-0099 §2 owns that rule. Every other external
locator stays opaque. That includes any link found inside acquired content.

The controls the specs must meet:

- **Where a read may point.**
  - The repository and host come only from trusted, human-reviewed records. They never
    come from acquired text.
    - In a component repo, that record is the acquisition record a human started.
    - In the meta-repo, it is the meta-repo's own reviewed list of component
      repositories. That list changes only through a human-reviewed change, never through
      a handoff, a skill's output, or acquired text.
  - Interpreting a parent pointer never grants a read on its own. The pointer must match
    the trusted record, and a mismatch stops the action.
  - Core owns the read capability and these controls. `align-value-stream`'s status
    collection calls that capability and adds no transport of its own.
- **Identity and pinning.**
  - Before any read, Core proves that the target is the named repository.
  - A pin is an immutable commit identity, never a branch or tag.
  - A read returns committed content at that pin, never a working tree. A local read
    applies no replacement refs, grafts, or borrowed object stores, so the pin returns
    the commit's real objects.
  - Core checks that the pinned commit is reachable from the source's designated reviewed
    branch. If it is not, Core records that fact and shows it to the human before any
    acquire goes ahead. No receipt is ever written from an unreachable pin, so offline
    dependency evaluation and intent fulfilment never count one.
  - The designated branch comes from the same trusted record as the repository. It never
    comes from the source's own metadata or from acquired text. For a local checkout, the
    specs name which ref counts as that branch.
- **Confinement.**
  - A local read takes a file from the checkout's commit history at the pin, not from its
    working tree. The blessed confinement helpers cover only working-tree files, so this
    is a new read path.
  - That read path matches the blessed helpers' rejection set:
    - It accepts only a repository-relative path, and refuses traversal.
    - It accepts only regular-file entries, and refuses symbolic-link and submodule
      entries without resolving them.
    - It enforces a size limit.
  - It must not run the checkout's own configuration or hooks.
  - It needs its own security review.
  - An API read is a new provider read surface. It meets the existing adapters' full
    declared boundary:
    - read verbs only;
    - the host and repository from trusted configuration;
    - authentication, redirect, and DNS confinement to that host;
    - size, page, and time limits.
  - The read credential is never sent to any other host.
  - The specs choose between a separately scoped read credential through `credbroker`
    and the user's shared host session. If they choose the shared session, which can
    also write, only the adapter's verb allowlist keeps the path read-only, and the specs
    must say so.
  - Core adds no network transport of its own.
- **Privacy.**
  - Records carry only the repository identity, the revision, and repository-relative
    paths, never a local absolute path.
  - A receipt records only the status fact, the pin, and those locators. Status
    collection never copies component brief text into the meta-repo.
- **Untrusted content, in both directions.**
  - Component-slice text read by a component repo, and brief text read by the meta-repo,
    can never select a route, read target, write destination, tool, lifecycle status,
    Ready, or approval.
  - Component-slice content enters a brief only through the existing source minimization
    path.
  - Text that claims a status is never evidence of it. A receipt's status fact comes
    only from the brief's lifecycle field in a commit on the designated reviewed branch.
    A status from anywhere else stops the action, or is shown to the human as unproven
    and never as fact.
- **Human control of status collection.**
  - Status collection runs only on a current human request.
  - Every receipt write, whatever the status, needs the same human-set switch as a
    `work-intake` write mode.
  - A shipped status also needs current-human review.

### D6. Retired and moved names hard-retire

The retired skill names have no alias. These follow RFC-0067's clean-retire convention,
as RFC-0105 applies it:
- the 12 shaping skills `intent` replaces;
- the four Core skills `work-intake` absorbs;
- `ux-writing`'s place in `product-engineering`.

Every operative reference in this repository moves before a name retires. Frozen
historical records stay as written. Release notes map each retired name to its
replacement.

`author-brief` and `receive-brief` already carry a published removal policy, set out in
RFC-0099 §10. Under it they can retire no earlier than 2026-11-26, which is 90 days after
their 2026-08-28 deprecation. Every §10 removal condition still applies.

## Options considered

### D1, by how many shaping skills the model sees

- **Do nothing:** 15 skills, over Codex's budget on their own.
- **Trim descriptions only:** the colliding verbs and copied route prose remain.
- **Verb-mode `intent` with three separate skills:** recommended.
- **One skill including `discovery-loop`:** the most common request would load a
  stateful loop.

### D3, by which owners merge

- **Do nothing:** keep ADR-0098 as it stands.
- **Fold `intake-intent` only:** the brief lifecycle stays split from acquisition.
- **Fold both:** recommended.

### D4, by who creates the component brief and how it moves

- **Do nothing (hand copy):** two authorities for one brief.
- **The meta-repo writes and pushes briefs:** the meta-repo would own another
  repository's Ready gate.
- **Component slice and acquire:** recommended.
- **The component repo re-shapes from scratch, with only a link back:** contract and
  dependency facts are lost.

### D5, by transport

- **None (paste only):** no refresh is possible.
- **Local checkout only:** excludes setups that have only the remote.
- **Provider API only:** requires a provider pack.
- **Both:** recommended.

### D6, by what an old name does after the change

- **Hard retire:** recommended.
- **Time-limited alias bridge:** this is what RFC-0083 D6 and RFC-0099 D6 chose. It keeps
  14 extra listing entries for the length of the window, so it spends the budget
  D1 exists to save at the moment adopters upgrade.
- **Manual-only alias:** Claude Code (`disable-model-invocation`), Cursor (the same
  flag), and Codex (`allow_implicit_invocation: false`) keep such a skill out of the
  listing. The Gemini CLI and Copilot skill overview pages document no equivalent flag.

## Risks & what would make this wrong

- **A broad description under-triggers.** The probe forced a choice, and it was tuned on
  the queries it scored. *Wrong if:* the activation run in Experiment / validation fails
  its threshold on any required host.
- **Five modes are untested.** Six retired skills ship no trigger evals:
  `frame-situation`, `identify-opportunities`, `diverge-solutions`, `place-bet`,
  `map-capabilities`, and `lean-canvas`. `diverge` is partly covered by
  `explore-options`' evals, which leaves `situate`, `find`, `bet`, `map`, and `canvas`
  with no evidence.
- **`intent` grows into an orchestrator.** *Wrong if:* a later change gives route mode
  state, retries, or gate control. The follow-on ADR records this boundary.
- **A write-capable default.** `work-intake` holds write tools. *Wrong if:* any write mode
  runs without a human-set switch.
- **Hard retirement breaks callers outside this repository.** Adopters' prompts and
  scripts that name an old skill stop resolving. The only mitigation is the release
  notes.
- **The cross-repository read widens Core's trust boundary.** D5 lists the controls.
  The [recorded `security-reviewer` pass](0107-notes/security-review.md) of 2026-10-10
  is clean at proposal depth. It names four questions for the spec-stage security
  review.

## Evidence & prior art

- [Skill-routing survey](../product/findings/pe-skill-routing-survey.md): listing
  measurements, host limits, and a forced-choice selection probe over the 146 distinct
  queries in the pack's nine eval files. The files hold 153 entries, 7 of which repeat
  across files.
  The revised `intent` listing scored 99% on Opus (one run) and 98% on Sonnet (two runs).
  Today's listing scored 98% on Opus (one run) and 99% on Sonnet (two runs).
- [Meta-repo handover audit](../product/findings/meta-repo-handover-audit.md): gaps in
  today's handover with file and line evidence, and a working link model for component
  slices.
- [Claude skill best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices):
  a description says what the skill does and when to use it.
- [Codex skills](https://learn.chatgpt.com/docs/build-skills): the listing budget, one
  job per skill, and `allow_implicit_invocation`.
- [Claude Code skills](https://code.claude.com/docs/en/skills): the 1,536-character
  listing cap per skill, and `disable-model-invocation`.
- [Cursor skills](https://cursor.com/docs/context/skills): `disable-model-invocation`.
- [Agent Skills specification](https://agentskills.io/specification): progressive
  disclosure, and a 1,024-character description cap.
- [Building effective agents](https://www.anthropic.com/engineering/building-effective-agents):
  routing fits distinct categories that are better handled separately; start with the
  simplest solution.

## Experiment / validation

- **Hypothesis:** `intent` and the merged `work-intake` trigger and route as reliably as
  the skills they replace.
- **Measure:** a headless activation run on each supported host, using held-out queries
  plus new queries for the six retired skills that ship no evals. Score the right skill, the right mode,
  and no write without a human-set switch.
- **Hosts:** the run is required on Claude Code. It is also required on Codex once the
  [multi-adapter eval runner](../product/briefs/multi-adapter-eval-runner.md) ships a
  Codex detector. Cursor, Copilot, and Gemini CLI have no runner. They are recorded as
  not measured, never as passed or failed, and the release notes say so.
- **Success:** on every required host, activation and mode accuracy are each within 3
  percentage points of today's skills.
- **Failure:** any required host falls below that. Then split the weakest modes back out
  before release.

## Follow-on artifacts

- **An ADR** recording the D1 router boundary and every supersession and amendment named
  in D1, D3, D4, and D5.
- **Errata entries** on RFC-0099, RFC-0083, and RFC-0103 naming this RFC, as RFC-0099
  §11 did for its own supersessions.
- **Forward pointers** in the metadata of ADR-0098, ADR-0022, and ADR-0019.
- **A delivery brief** that decides the cut, the mode names, the contract fields, the
  checker changes, and the release order.
- **Specs** for each delivery slice the brief confirms.
- **Guide updates**, shipped with each capability.

## Errata

- **2026-10-10 (Approver: eugenelim) — the follow-on ADR is split into three.**
  - Follow-on artifacts named one ADR. It is recorded as three, because each records one
    decision and supersedes a different set of records:
    - [ADR-0140](../adr/0140-shaping-entry-point-one-verb-mode-intent-skill.md)
      covers D1 and D2.
    - [ADR-0141](../adr/0141-core-intake-lifecycle-intent-and-brief-modes-in-work-intake.md)
      covers D3 and D6.
    - [ADR-0142](../adr/0142-meta-repo-handover-component-slices-and-pinned-receipts.md)
      covers D4 and D5.
  - The errata on RFC-0099, RFC-0083, and RFC-0103 and the forward pointers on ADR-0098,
    ADR-0022, and ADR-0019 are in place.
- **2026-10-10 (Approver: eugenelim) — the operating-model guide link is retargeted.**
  - The guide moved from `guides/_shared/explanation/the-three-loops.md` to
    `the-operating-model.md` in #1531.
  - The link under *Terms used here* now points at the new path.
  - Nothing else changes.
