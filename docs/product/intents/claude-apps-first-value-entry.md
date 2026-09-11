# A non-technical adopter reaches first value from the site home, without a terminal

- **Status:** Draft
- **Level:** feature
- **Scale:** app
- **Parent:** [`nontechnical-pack-first-value-rollout`](nontechnical-pack-first-value-rollout.md)

## Outcome

Someone who lands on the public site, works in the Claude apps, and has no
terminal can choose and install at least one of the four discipline packs and
complete one method end to end.

**Steerable input:** the number of terminal-only prerequisites on the shortest
existing public route to a verified Claude-apps first-value path. The baseline is
established by the probe below, not asserted here, and the target is zero.

**Lagging outcome:** an adopter arriving from a public entry point installs a
discipline pack in the Claude apps and produces that discipline's first
artifact in the same session.

**Guardrail:** a terminal adopter can still reach and complete the existing CLI
route in no more steps than the baseline recorded before this work starts.

## Direction 2026-09-10 — recommend Desktop's Code tab first

**Owner decision, amended 2026-09-10.** The starting point we *recommend* is
**Claude Desktop's Code tab**. Both surfaces are **admitted now** — the Code
tab and the Claude apps — rather than the chat surface being deferred to a
later decision.

*What the earlier version said, and why it changed.* It deferred the chat
surface entirely, on the reasoning that it is "worth having only if the
degradation is repaired first". That set the bar in the wrong place. Claude
plugins carry **skills on all three surfaces**, and skills are what carry the
method; the degradation is confined to sub-agents, affecting five of fifteen
published packs. Deferring a surface where the primary primitive works in
order to wait on a secondary one costs more than it protects.

*What admitting it trades, stated plainly.* On the chat surface a reader using
`desk-research`, `experience-design`, `product-engineering`, `architect` or
`frontend-engineering` gets the thinner method and nothing tells them at the
point of use. The mitigation is disclosure — the capability reference — not
repair. **Admitting the surface does not close the defect**; it stays open and
separately owned at
`docs/specs/claude-plugin-route-scope/notes/subagent-present-but-unrunnable.md`,
and a reader who never opens the reference still gets a silent pass.

**Why it dissolves most of this intent's difficulty.** The Code tab *is* Claude
Code. So on that surface: sub-agents run, the filesystem is readable and
writable so a method's artifact lands where the pack's layout says, there is no
second plugin store to register in, and no capability differs from the route
the catalogue was built for. It is also genuinely no-terminal — Claude Desktop
is a GUI application and `/plugin marketplace add` is a slash command in the
app, not a shell command.

**And it needs no contract change at all.** `surfaces = ["claude-code"]`, which
all four discipline packs already declare, is *already true* for the Code tab.
The vocabulary question that this intent recorded as a hard predecessor is not
merely narrowed — for this direction it does not arise.

**The honest caveat.** Claude Code works against a local directory, so an
adopter needs a folder to work in. That is a smaller ask than a terminal, and
it is what makes artifacts persist.

### Sub-agent audit, 2026-09-10

Seven packs ship sub-agents. Five of them are published as plugins, carrying
eight sub-agents onto the plugin route:

| Pack | Sub-agents | Scopes | Published as a plugin |
| --- | --- | --- | --- |
| `product-engineering` | 3 | user, repo | yes |
| `desk-research` | 2 | user, repo | yes |
| `architect` | 1 | user, repo | yes |
| `experience-design` | 1 | user, repo | yes |
| `frontend-engineering` | 1 | user, repo | yes |
| `core` | 6 | repo | no — repo-scope, so the route never carries it |
| `release-engineering` | 1 | repo | no — same |

**Impact by surface:**

| Surface | Sub-agents | Filesystem | Consequence |
| --- | --- | --- | --- |
| Claude Code, incl. Desktop's **Code tab** | run | yes | no degradation; this is the recommended start |
| Cowork | run | — | sub-agents work; artifact destination unestablished |
| Desktop **chat** tab, web chat | present, listed, **unrunnable** | no | 8 sub-agents across 5 published packs are inert, and no pack's fallback fires because all are keyed on *absence* |

The chat-surface row is the defect at
`docs/specs/claude-plugin-route-scope/notes/subagent-present-but-unrunnable.md`.
Recommending the Code tab does not repair it — the packs still ship into a
surface where it bites — but it means no adopter we point at a route meets it.

**Decided 2026-09-10: we want both surfaces.** The chat surface is admitted
with its cost disclosed rather than repaired. What remains open is the defect
itself, which is a packs-level contract problem and not a reason to withhold a
route whose skills work.

## Boundary

- The marketing home's start zone: **two equal links**, one to the existing
  terminal route and one to the no-terminal route; and the no-terminal route's
  copy through a submitted install. Ceded here from
  [`cohort-orientation-surfaces`](cohort-orientation-surfaces.md) on 2026-09-10,
  because this repository resolves ownership by outcome and the doors serve
  reaching a route, not comprehension.
- **The two entry links and the install how-to may be specified before
  `[pack.first-value].surfaces` is resolved**, but they must not claim completed
  first value. That contract question gates only the method-to-artifact tutorial
  and the lagging outcome.
- **This intent is a consumer of each pack's `[pack.first-value]` contract, not
  a second owner of it.** Supported surfaces, prerequisites, install
  verification, recovery, starter task, expected result, and safety behaviour
  remain owned in `packs/<pack>/pack.toml` under
  [`portfolio-pack-first-value-contract`](../../specs/portfolio-pack-first-value-contract/spec.md),
  and must be updated or parity-checked there before any public copy ships.
- If the contract's `surfaces` vocabulary cannot represent the Claude apps, that
  contract change routes to its owner first — see Unresolved questions.
- Entry-point precedent:
  [`install-to-ship-walkthrough`](../../specs/install-to-ship-walkthrough/spec.md)
  used four — the marketing landing page at `/` (`web/src/pages/index.astro`),
  the documentation home (`docs-site/src/content/docs/index.mdx`),
  getting-started (`docs-site/src/content/docs/getting-started/index.mdx`), and
  the guide hub (`guides/README.md`). How many this slice needs is a scoping
  decision.
- Outside this intent: the `digital-product` CLI profile and its persona journey
  page (owned by [`digital-product-maker-profile`](digital-product-maker-profile.md),
  blocked on `ini-003`); sub-agent degradation policy, which is already owned
  per pack (see Assumptions); and any change to the published plugin packages.

## Owner

- Platform Core (`ini-002`). No individual owner is recorded.

## Unresolved questions

- **Resolved — the `surfaces` vocabulary is not a blocker.**
  **Narrowed 2026-09-10.** An earlier reading made the `surfaces` vocabulary a
  hard predecessor for this whole intent. It is not, and the field was never the
  right place to look. Plugin reach is already declared: `claude-plugin-route-scope`
  (Shipped) settles that the Claude-plugin route is a **user-scope channel**, the
  route's admission policy is `user-publishable-with-consent`, and the publish
  workflow ships every pack whose `[pack.install] allowed-scopes` admits `user`.
  ADR-0107 then establishes that plugins reach the Claude apps. Claude-apps reach
  is therefore **derivable from fields we already declare**, and storing it again
  in `surfaces` would recreate the drift `[pack.first-value]` exists to prevent.
  
  `surfaces` means *verified* first-value surfaces. No pack could honestly
  declare the Claude apps there today regardless of vocabulary, because no dated
  observation exists. **What actually remains blocked is one thing: a verified
  first-value claim, which needs the observation — not a contract change.**
- Which discipline supplies the walkthrough. `product-strategy` is the only one
  of the four that ships no sub-agents, so it is the only one whose method is
  unaffected by the chat surface's sub-agent gap — which makes it the cheapest
  honest choice and avoids a dependency on degradation work.
- How many of the four entry points this slice needs. One home-page link may
  satisfy the outcome; four is precedent, not obligation.
- Whether the route is a new guide or a section of the existing install-routes
  explanation, which already carries the mechanics after ADR-0107. Duplicating
  them decays.
- What "evaluation evidence" means for a documentation slice, given the parent
  requires it of every slice.

## Projection

- **Probe before spec.** Run one dated Claude-apps install-to-first-value probe
  for one chosen pack, covering marketplace registration, installation, skill
  discovery, invocation, a visible result, and recovery. If it succeeds, scope
  the smallest consumer-documentation spec. If it fails, the deviation routes to
  the owning pack or to the first-value contract before any navigation is
  specified. This is `new-spec` step 5a's cheapest-disconfirming-evidence gate,
  and it is required because the load-bearing premise is third-party behaviour.

## Opportunity

**Functional job.** Get a working product-strategy, research, or design method
running in the Claude app I already have open, starting from whatever page I
first landed on.

**Emotional job.** To feel invited rather than filtered — for the first
instruction I meet to be one I can actually follow.

**Social job.** To bring a practice to my team without asking an engineer to set
it up for me.

**Struggling moment.** The site home's install affordance is a terminal
component (`InstallTerminal` in `web/src/pages/index.astro`). A strategist or
designer reading that page sees a shell command as the way in and concludes the
project is not for them — even though ADR-0107 established that their surface is
supported. The capability and the signpost point in opposite directions.

The second trap is subtler. An adopter who does find the plugin route can
register it in Claude Code and reasonably assume they are done, because nothing
tells them the Claude apps keep a separate plugin store. They then look for the
skills in the chat tab and find nothing.

## Assumptions

- ADR-0107 is Accepted, so the route and audience are settled and this slice
  does not reopen them.
- **Marketplace presence is not installability.** All four packs appear in
  `.claude-plugin/marketplace.json`, which proves publication eligibility only.
  Whether the Claude apps install this marketplace, and whether a
  filesystem-oriented skill completes there, is unverified — the survey states
  that no claim in it is runtime-verified. The probe above exists to settle it.
- ADR-0107 records that the chat surface reads nothing from disk, while current
  first-value records expect artifacts written to repository paths. That tension
  is unresolved and may be what the probe fails on.
- Registration is per surface, and adopters will not infer it.
- **Sub-agent degradation is already owned per pack, not by this intent.**
  `research-pack/spec.md` specifies that "on hosts without subagents the skills
  run inline"; `experience-reviewer-work-loop-gate/spec.md` makes reviewer
  absence "a named skip, not a silent pass". Any observed deviation from those
  is a defect against the owning spec. Choosing `product-strategy` avoids the
  question for this slice entirely.
- The parent capability's outcome is unchanged by ADR-0107, but the
  supported-surface contract it depends on is not — see the parent's Derived
  work section.

## Decomposition

*(empty — `decompose-intent` owns this)*

## Source

- Mode: repo-origin
- Locator: docs/adr/0107-claude-plugin-route-serves-non-technical-adopters.md
- Revision: local-2026-09-10 (the cited ADR is uncommitted; replace with its
  committed revision once it lands)
- Authority: repo-origin
