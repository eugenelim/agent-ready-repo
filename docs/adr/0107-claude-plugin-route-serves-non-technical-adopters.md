# ADR-0107: The Claude-plugin route serves non-technical adopters, as individual per-pack plugins

- **Status:** Accepted <!-- Proposed | Accepted | Rejected | Deprecated | Superseded by ADR-NNNN -->
- **Date:** 2026-09-10
- **Decision-makers:** eugenelim
- **Consulted:** independent shaping review (two rounds; the first returned WRONG ARTIFACT against a meta-plugin framing of this same outcome)
- **Supersedes:** the **"CLI-route only" clause only** of [ADR-0025](0025-pack-profiles-single-scope-cli-manifest.md) — specifically its sentence "Plugin/APM-route surfacing is deferred (it would require coupled meta-plugins)", to the extent it reads as deferring *pack* distribution on the plugin route. ADR-0025's actual decision — that a **profile** is a single-scope, catalogue-owned, CLI-expanded manifest and **not** a meta-pack — stands unchanged, as do its single-scope, catalogue-ownership, thin-orchestration, and no-new-persistent-entity clauses.
- **Related:** [RFC-0034](../rfc/0034-pack-profiles.md) OQ2 (the deferral this revisits), [ADR-0003](0003-credential-broker-contract.md) / [RFC-0013](../rfc/0013-credential-broker-contract.md) option F (the meta-pack rejection, upheld here), [RFC-0092](../rfc/0092-first-class-distribution-routes.md) (the route layer), [ADR-0072](0072-derived-plugin-manifest-mirrors-upstream-schema.md) (schema conformance is not client proof), [`docs/product/research/claude-desktop-distribution-survey.md`](../product/research/claude-desktop-distribution-survey.md) (the evidence base)

## Decision summary

- **Decision:** The Claude-plugin route is a supported distribution surface for adopters who do not use a terminal, reaching the Claude apps — Desktop's Chat tab, web chat, and Cowork — delivered as the per-pack plugins this catalogue already publishes, installed individually.
- **Because:** the people who most need the strategy, research, and design methods are the least able to run a CLI, and the route already reaches them with no new machinery.
- **Applies to:** the published `claude-plugins` route and its adopter documentation. No runtime-adapter, schema, or build change.
- **Tradeoff accepted:** N disciplines means N installs, and the catalogue is registered separately in Claude Code and in the Claude apps because they are separate plugin stores; this route carries no curated bundle, and an organisation wanting one-shot setup scripts it itself.
- **Revisit if:** Anthropic ships a *scope-aware* bundle primitive (not the coupled `dependencies` array), or adopter demand for a curated bundle outweighs the coupling cost that ADR-0003 / RFC-0013 option F rejected.

## Context

ADR-0025 settled what a pack profile is, and in doing so recorded that
"Plugin/APM-route surfacing is deferred (it would require coupled
meta-plugins)". [RFC-0034](../rfc/0034-pack-profiles.md) OQ2 carried the same
deferral with an explicit revisit condition — "only if route parity is demanded
and the coupling/scope cost is judged acceptable", owner `eugenelim`, decide-by
"post-v1, demand-driven".

Route parity is now demanded, for an audience the CLI cannot serve. Four
constraints shape the answer:

- **The audience has no terminal.** Product strategists, researchers, and
  designers are the primary users of `product-strategy`, `desk-research`, and
  `experience-design`. Every route this catalogue documented before this
  decision assumed a filesystem the adopter could write to and a CLI they could
  run.
- **The plugin route already reaches them.** Anthropic documents that "you can
  install and use plugins in chat on the web, the Chat tab in Claude Desktop,
  and Claude Cowork", and that "the skills bundled in a plugin work across all
  three". All four discipline packs are already published to the marketplace,
  because each declares `allowed-scopes` admitting `user`.
- **Registration is per surface, and the two registries do not cross over.**
  Claude Code registers a marketplace with `/plugin marketplace add`; the Claude
  apps register one under **Customize › Plugins › Personal plugins › Add
  marketplace**, which "sync[s] a marketplace from a GitHub repository or git
  URL". An adopter who added this catalogue in Claude Code does **not** see it
  in the Chat tab, and adds it again there. Publishing once serves both, but
  installing once does not.
- **The chat surface reads nothing from disk.** Custom skills reach chat by ZIP
  upload through Settings; no local folder or profile path is documented for it,
  and one skill per archive with no bulk form. Desktop's **Code tab is Claude
  Code** and does read `~/.claude/`, which is a different surface with a
  different mechanism. Plugins are therefore the only route that delivers a
  whole pack to the chat surface without per-skill upload.
- **Self-service by default, restrictable by an admin.** The personal
  marketplace path is generally available on any paid plan. An organisation's
  administrators can restrict what a group installs for itself, and can push
  packs instead, so reach is conditional at the margin rather than gated by
  default. Guidance names the self-service path first and the administrator as
  the fallback question.

The coupling question that drove the original deferral is no longer load-bearing,
because the requirement is no longer one-shot installation. Individual per-pack
installs are accepted as sufficient.

## Decision drivers

- **Reach the non-technical adopter at all.** A route that requires a terminal
  fails the audience this decision exists for.
- **No new runtime infrastructure.** Charter Principle 3 and
  [RFC-0031](../rfc/0031-catalogue-package-manager-posture.md)'s "distribution
  hygiene, not package-manager infrastructure" posture bound what may be added.
- **Preserve the meta-pack rejection.** ADR-0003 / RFC-0013 option F rejected
  coupled meta-packs on portability grounds; a convenience gain does not buy
  that back.
- **Honest support claims.** RFC-0092 admits no claim above
  `documentation-verified` without a dated per-client record. Note what that
  does and does not gate: it gates a *declaration*, not this route's use. The
  route works and is documented; the record is owed only if and when something
  consumes the claim.

## Decision

> The Claude-plugin route is a supported distribution surface for adopters who
> do not use a terminal, reaching the Claude apps — Desktop's Chat tab, web
> chat, and Cowork. Distribution is by **individually installed per-pack
> plugins**, which the catalogue already publishes. No meta-plugin is created,
> and profiles are not surfaced on this route.

Specifically:

- **Two registration paths, both first-class.** Any paid user can self-register
  this catalogue in the Claude apps under **Customize › Plugins › Personal
  plugins › Add marketplace**, from a GitHub repository or git URL; the same
  menu also accepts an uploaded plugin, or one created in place. That is
  generally available, not an enterprise feature. An admin can additionally push
  it through **Organization settings › Plugins**, which requires a private or
  internal repository and adds group-scoped assignment. Adopter documentation
  names the personal path first, because it needs nobody's permission, and the
  organisation path second, for fleets.
- **Registration is per surface.** The same marketplace is added separately in
  Claude Code and in the Claude apps; an install on one does not appear on the
  other. Documentation must not imply a single install reaches both.
- **Per-pack, not bundled.** Each discipline installs as its own plugin. The
  catalogue ships no aggregate plugin and adds no `dependencies` field to any
  generated manifest. An organisation that wants one-shot setup scripts the
  installs itself; that is a local convenience, not a catalogue artifact.
- **Profiles stay CLI-only.** `profiles/<name>.toml` remains what ADR-0025 says
  it is, read only by `agentbundle`. A profile is not projected onto this route,
  because doing so is the meta-plugin shape that remains rejected.
- **Skills are the carried primitive; sub-agents degrade by surface.** Anthropic
  documents that "hooks and sub-agents run only in Cowork, so they appear grayed
  out in chat". Three of the four packs ship sub-agents — `product-engineering`
  (3), `desk-research` (2), `experience-design` (1) — so those are available in
  Cowork and inert in chat. None of the four ships commands or hooks, so no
  other primitive is affected. Documentation states this per surface rather than
  claiming uniform parity.
- **The claim stays documentation-verified.** This ADR records a supported
  *route and audience*; it does not promote a runtime-verified support claim.
  The dated per-client observation is owed by
  [`live-adapter-and-client-smoke-evidence`](../product/intents/live-adapter-and-client-smoke-evidence.md),
  consistent with ADR-0072.

## Consequences

**Positive**

- The audience the four discipline packs were written for can install and use
  them with no terminal, on a route that already exists.
- Zero engine work. All four packs are already present in the published
  marketplace, so this decision changes documentation and posture, not code.
- The meta-pack rejection is intact, so no portability coupling is introduced
  and no schema on a protected engine path is touched.

**Negative / accepted**

- **N installs for N disciplines.** There is no curated "digital product
  toolkit" entry point on this route, and a first-time adopter cannot tell from
  the marketplace which packs constitute a complete practice. The CLI profile
  route remains the only place that curation is expressed.
- **Two homes for the same need.** `profiles/digital-product.toml` (once it
  ships) and the per-pack plugins serve the same outcome by different means on
  different surfaces. Guidance must route by surface, not present them as
  interchangeable.
- **The same marketplace is registered twice.** An adopter who works in both
  Claude Code and the Claude apps adds this catalogue in each, and upgrades it
  in each. That is a per-surface chore the catalogue cannot remove, and a
  plausible source of version skew between one person's two surfaces.
- **Conditional reach.** The personal path is generally available, but an
  organisation's administrators can restrict what a group may install, so
  "supported" still does not mean "available to everyone".
- **A degraded surface is now a supported surface, and the degradation is not
  currently handled.** Sub-agents ship in the plugin — the route declares
  `agent = native` and the Claude Code adapter projects `agent →
  .claude/agents/` — so on the chat surface they are **present, listed and
  unrunnable**, not absent. Every pack that ships them degrades only on
  *absence*, so no fallback fires in that state:
  `experience-reviewer-work-loop-gate` (Shipped) guarantees a missing reviewer
  is "a named skip, not a silent pass", and on this surface the trigger never
  fires. Accepting this surface therefore accepts a state in which a shipped
  contract can pass silently. Tracked as a defect at
  `docs/specs/claude-plugin-route-scope/notes/subagent-present-but-unrunnable.md`
  and not repairable by documentation, which can disclose the difference but
  does not own the contract.

  *Amended 2026-09-10, before publication.* The original wording called this
  "degradation accepted because skills carry the method". That was too
  comfortable: it described the capability gap and missed that the handling for
  it never triggers. The decision is unchanged — the surface is still
  supported — but the cost is larger than first recorded.
- **Revisit if:** Anthropic ships a scope-aware bundle primitive (not the
  coupled `dependencies` array), or adopter demand for a curated bundle
  outweighs the coupling cost ADR-0003 / RFC-0013 option F rejected.

## Alternatives considered

1. **An aggregate meta-plugin using the `dependencies` array.** Rejected. It
   reverses ADR-0003 / RFC-0013 option F's meta-pack rejection for a convenience
   gain; plugin dependencies install at one scope with no notion of this
   catalogue's user/repo pack scope; and a fifth published artifact has no
   canonical source under RFC-0092 P4, which requires every route manifest to
   project from `pack.toml`. Once individual installs are accepted as
   sufficient, it buys nothing that justifies that cost.
2. **Surface profiles on the plugin route.** Rejected — this *is* alternative 1
   under another name, which is precisely what RFC-0034 OQ2 recorded.
3. **The skills-upload route.** Rejected as a primary route. One skill per ZIP
   with no bulk form means the upload count scales with the toolkit, and there
   is no per-pack update path; a plugin carries a whole pack and updates with
   it.
4. **Status quo — CLI only.** Rejected. It excludes the audience this decision
   exists to serve, and leaves the adopter documentation asserting the plugin
   route is for Claude Code alone, which was factually wrong.

## Confirmation

- **Mode:** reviewer-checked
- **Signal:** `guides/_shared/explanation/install-routes.md` names the Claude-apps
  surface, its per-group availability caveat, and the chat/Cowork sub-agent
  difference; and no published support claim rises above
  `documentation-verified` without a dated per-client record.
- **Owner:** eugenelim

A lint is deliberately not proposed. The claim this decision could get wrong is
a prose accuracy claim about a third-party client's surfaces, which no
repository-local check can evaluate; `tools/lint-plugin-route-docs.py` pins the
scope precondition's wording in that guide but cannot judge whether a surface
statement is true.

## References

- [RFC-0034](../rfc/0034-pack-profiles.md) — OQ2, the deferral and its revisit condition
- [ADR-0025](0025-pack-profiles-single-scope-cli-manifest.md) — the decision partially superseded here
- [`docs/product/research/claude-desktop-distribution-survey.md`](../product/research/claude-desktop-distribution-survey.md)
  — the evidence base, including the two Anthropic surfaces that disagreed on
  org-wide skill distribution and how that was dated and resolved
- Anthropic, "Use plugins in Claude" and "Use skills in Claude" (Help Centre),
  fetched 2026-09-10 — the supported-surface and per-component sentences quoted
  above
