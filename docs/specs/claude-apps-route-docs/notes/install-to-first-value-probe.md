# Claude-apps install-to-first-value probe

**Status: NOT RUN.** This file is the prepared record, not a result. Every
result cell below is empty on purpose. Do not cite this document as evidence
until it carries a date and an observer.

## Why this probe gates the spec

[`claude-apps-first-value-entry`](../../../product/intents/claude-apps-first-value-entry.md)
§ Projection requires one dated probe before a consumer-documentation spec is
scoped. The reason is that the load-bearing premise is **third-party
behaviour**, which no repository gate can observe:

- Marketplace presence is not installability. All four packs appear in
  `.claude-plugin/marketplace.json`, which proves publication eligibility only.
- Whether the Claude apps install this marketplace at all is unverified.
- Whether a **filesystem-oriented skill completes** on a surface that reads
  nothing from disk is unverified. ADR-0107 records that the chat surface reads
  nothing from disk, while current first-value records expect artifacts written
  to repository paths. That tension is unresolved and is the most likely thing
  this probe fails on.
- The distribution survey states plainly that **no claim in it is
  runtime-verified**.

`claude-apps-route-docs`'s AC12 fences the spec off from any first-value or
install-success claim precisely because this is outstanding. The spec's
recommendation of Desktop's **Code tab** is partly a consequence of this being
unrun: the probe either confirms that recommendation or changes it.

## Who runs it

**A human, on a real Claude app account.** An agent cannot run this: it requires
a paid plan, the Customize > Plugins UI, and observation of what the app does.

## Which pack to probe, and why

**Recommended: `product-strategy`.**

It is the only one of the four discipline packs that ships **zero** agents —
`product-engineering` ships 3, `desk-research` 2, `experience-design` 1. Probing
a pack with agents would confound two separate questions: whether the install
and invoke path works at all, and whether the known present-but-unrunnable
sub-agent defect fires. `product-strategy` isolates the first.

Its skills are also analysis-and-authoring shaped rather than
repository-mutation shaped, which makes the filesystem question above a clean
observation instead of an immediate hard failure.

**If `product-strategy` passes, that is not a general pass.** It establishes the
route for a zero-agent, authoring-shaped pack only. A second probe on a pack
that ships agents is a separate question with a separate owner.

## Steps, and what to capture at each

Record the date, the app (Claude Desktop / web / mobile), the surface (chat tab
or Code tab), and the plan tier before starting. Registration is **per surface**
— an install in one store does not appear in the other — so state which surface
each row was performed on.

| # | Step | What counts as a pass | Result | Evidence captured |
| --- | --- | --- | --- | --- |
| 1 | Reach Customize > Plugins > Personal plugins | The menu exists on this plan and is not admin-restricted | | |
| 2 | Register the marketplace | The catalogue is accepted and its packs are listed | | |
| 3 | Install `product-strategy` | Install completes and reports success | | |
| 4 | Skill discovery | At least one of the pack's skills is listed and named correctly | | |
| 5 | Invoke one skill | The skill runs rather than being merely listed | | |
| 6 | A visible result | The reader can see an artifact or answer, and can say what they now hold | | |
| 7 | Filesystem behaviour | Record what the skill did about writing anything to disk. **This is the question most likely to fail** | | |
| 8 | Recovery | A wrong or absent input produces a recoverable, legible failure rather than a dead end | | |

## Routing on the result

- **All eight pass.** Scope the smallest consumer-documentation spec. The Code
  tab recommendation stands, and AC12's fence can be revisited by the spec's
  owner — it does not lift automatically.
- **Step 7 fails or is degraded.** The deviation routes to the **first-value
  contract** (`portfolio-pack-first-value-contract`), not to the documentation.
  A surface that cannot hold the artifact a first-value record expects is a
  contract question.
- **Steps 1–3 fail.** The deviation routes to the **owning pack** or to ADR-0107
  itself, and no navigation may be specified until it is settled.
- **Any step is partial.** Record it as partial, not as a pass. A partial result
  here is what would let an unsupported install-success claim reach the site.

## What this probe does not settle

- Whether any pack that **ships agents** works on the chat surface. That is the
  separate, still-open defect at
  [`subagent-present-but-unrunnable`](../../claude-plugin-route-scope/notes/subagent-present-but-unrunnable.md).
- Whether a reader reaches first value on the **Agent Plugins** route. Agent
  Plugins 1.0.0 defines no agent component type; that route is a different
  question with a different refusal set.
