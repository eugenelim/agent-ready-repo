# A new team can walk the whole SDLC from the guides

- **Status:** Draft
- **Level:** feature

## Outcome

A team adopting this catalogue can go from install to a shipped, governed change
by following the guides alone: every skill they must invoke shows what to type,
what to supply, what comes back, and what they hold at the end, and the guides
are grouped into ordered paths that name their prerequisites.

## Opportunity

The catalogue publishes 22 packs and 135 skills behind 203 guide files, and a
newcomer cannot act from them. Measured over the whole guide tree by
`tools/audit-guide-affordances.py`: 21% show a literal chat input, 4%
demonstrate what the user supplies into a workflow, and 10% state what the
reader ends up with. Forty-eight guides name a skill in prose without ever
showing what to type, and 66 of 203 files carry none of the five affordances.
Exactly one file carries all five.

The corpus is also missing the route this repository's own owner uses.
Shaping runs on `desk-research`, `product-engineering`, and `architect`;
handover to build runs on `intake-intent`. That skill is named in zero guides
under those three packs. The upstream packs write durable artifacts and the
guide set never closes the loop into repository scope.

Two facts make this cheap rather than large. Three of the five affordances are
already authored and validated one level up: all 14 packs that ship a
`JOURNEY.md` carry a complete `contract:` block — `useItWhen`, `youProvide`,
`youReceive`, `yourDecisions` — and the contract has no slot at all for the
literal chat input. And the chat inputs already exist in a third place: 56 of
135 skills carry a quoted example utterance in their SKILL.md description, with
coverage highest exactly where the guides are weakest (`product-strategy` 9/9
skills against 0/7 guides; `product-engineering` 13/15 against 1/18).
Thirty-three guides can gain a correct chat input by lifting a phrase that
already exists in the skill they document.

## Assumptions

- The 56 existing SKILL.md phrases are correct invocations, so lifting them
  into guides projects fact rather than inventing phrasing. This is the
  load-bearing assumption: if the phrases are wrong, the bulk passes become
  authoring work and the appetite does not hold.
- A guide can gain a path grouping without moving on disk, so generated pack
  navigation and every published URL survive. Whether it needs a new
  frontmatter key is open: `contracts/guide.schema.json` sets
  `additionalProperties: false`, and its existing optional `journey` and `order`
  keys may already be able to carry a path.
- `experience-design` (20 skills) and `frontend-engineering` (9 skills) have
  no invocation phrasing anywhere and therefore need authored content, not
  projection.

## What the decision requires

- Document the handover the owner actually uses: a finished intent entering
  `intake-intent`, and which of spec, brief, or RFC follows.
- Give every skill on the shaping and build spine a literal chat input and a
  stated outcome in its owning guide.
- Add a chat-input slot to the journey contract as an optional field, before the
  bulk guide passes, so the affordance cannot be dropped again. The contract is
  closed — `journey_validator.py` rejects unknown fields — so this is a
  validator, standard, generator, and test change, and a *required* field would
  break packs authored outside this repository. It is a regression gate, not a
  content source: one pack-level utterance cannot supply distinct inputs to 30
  skill-specific guides.
- Make the owner's repo-first tracker position reachable from `guides/`, with
  the projection table promoted out of a skill reference and the missing GitHub
  and Jira Software columns added.
- Name shaping artifacts as inputs to `new-rfc` and `new-adr`.
- Group the guides into ordered paths that state prerequisites, audience, and a
  first-value moment.
- Correct the seven verified defects that hand a newcomer a command or a name
  that does not exist.

## Decisions taken

- **Multiple tracker modes are supported** (owner, 2026-09-03). Repo-first
  projection and tracker-authoritative write-back are both first-class. The
  guides must name which mode a reader is in and how to choose; neither is
  removed.
- **Light intents are the primary shaping path** (owner, 2026-09-03). The robust
  path — situation, opportunities, options, bet, capability map, and the gated
  discovery loop — stays supported and must be surfaced as the alternative for
  higher-uncertainty work.

## Risks

- Two supported tracker modes double the surface a reader must disambiguate. If
  a guide does not state its mode, a team will mix repo-first projection with
  tracker write-back and corrupt both.
- Naming the light path "primary" risks stranding the robust path. It needs a
  visible entry point and a stated trigger for reaching past light, or the
  higher-uncertainty route becomes invisible.

## Source

- Mode: repo-origin
- Locator: docs/product/findings/new-team-sdlc-guide-uplift-audit.md
- Revision: sha256-bytes-v1:63105bfff844b1a878104d27e295794235fc608c59cd20b81a4a8f93c8b7a96c

## Supporting artifacts

- [New-team SDLC adoption — journey map and guide uplift audit](../findings/new-team-sdlc-guide-uplift-audit.md)
  — the measured audit behind every count above: the six-phase journey, the
  five-affordance measurement over 203 guides, the 15-row uplift table, the
  proposed path structure, and the seven verified defects.
