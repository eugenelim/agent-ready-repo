# Reaching a Claude Desktop user with the four-discipline toolkit

> Discipline: applied (practitioner-pattern survey)

Commissioned 2026-09-10 to ground a shaping decision: how a non-CLI Claude
Desktop user installs and runs the catalogue's `product-strategy`,
`product-engineering`, `experience-design`, and `desk-research` packs, and what
a team- or organisation-level standard operating procedure over them would
require. Independent desk research; every finding is cited and labelled by
evidence class. Retained so intents and briefs can cite it rather than restate
it.

---

## Bottom line

There are **two** viable routes to a Claude Desktop user, not one, and they are
governed by different systems with different formats and different plan gates.

1. **Plugins** — a plugin bundles skills, connectors, and sub-agents, installs
   into Claude Desktop's Chat tab, web chat, and Cowork, and is available on
   every paid plan. An organisation marketplace is a **private or internal**
   GitHub repository synced by Anthropic's GitHub App, carrying a
   `marketplace.json`. This route carries a whole pack in one action and is the
   only route with group-scoped distribution.
2. **Skills** — a `.zip` per skill, uploaded through Settings by an individual,
   or provisioned org-wide by an Owner. **One skill per archive, always**, with
   no bulk form, so the upload count scales with the number of skills in the
   toolkit. That disqualifies it as the primary route for a multi-skill pack.

The plugin route is in use today, and self-service. Any paid user adds a
marketplace in the Claude apps under **Customize › Plugins › Personal plugins ›
"+"** — which also accepts an uploaded plugin, or one created in place — with no
administrator involved. Separately, an admin can push packs to a fleet through
**Organization settings › Plugins** on Team and Enterprise, with group-scoped
assignment.

**The two plugin registries do not cross over.** Claude Code and the Claude apps
keep separate stores: a marketplace added with `/plugin marketplace add` does not
appear in the chat tab, and is added again under Personal plugins. Publishing
once serves both surfaces; installing once does not. This is the single most
load-bearing mechanic for guidance, and the easiest to get wrong.

Reach is still conditional rather than universal, because administrators can
restrict what a group installs for itself — but the default is self-service, not
gated.

That makes two publication constraints load-bearing for this repository. An
organisation marketplace repository must be private or internal — public
repositories are refused — so the catalogue's published marketplace cannot serve
as an org marketplace for an adopting enterprise. And Anthropic's GitHub sync
reads the repository's **default branch**, while this catalogue publishes its
marketplace to a non-default branch. Those two facts do not currently meet.

---

## Findings

### F1. Plugins reach Claude Desktop; the plugin surface is not Claude-Code-only [high]

A plugin "bundles skills, connectors, and sub-agents into a single package."
Plugins appear "in both chat (on the web and the Chat tab in Claude Desktop)
and Claude Cowork", and "the skills bundled in a plugin work across all three".
**Hooks and sub-agents** are carried but run only in Cowork — "so they appear
grayed out in chat". Local MCP servers are also carried. Skills are invoked by
typing "/" or using the "+" button.

Plugins are "available to all paid plans (Pro, Max, Team, Enterprise)."
Mobile and Claude Code are not named on the end-user page; Claude Code has its
own separate marketplace system (F6).

Sources: [Use plugins in Claude](https://support.claude.com/en/articles/13837440-use-plugins-in-claude)
(primary); [Cowork and plugins for teams across the enterprise](https://claude.com/blog/cowork-plugins-across-enterprise)
(primary).

> Correction to an earlier reading: Claude Code's own
> [plugin-marketplaces page](https://code.claude.com/docs/en/plugin-marketplaces)
> never mentions Claude Desktop, which makes the plugin route look
> Claude-Code-exclusive if that page is read alone. It is not. The Claude apps
> have a parallel plugin system documented in the Help Centre.

### F2. An organisation marketplace must be a private or internal GitHub repository [high]

Admin path: **Organization settings › Plugins › "Add plugins"**, with two
methods:

| Method | Input | Update trigger |
| --- | --- | --- |
| Manual upload | marketplace name + `.zip` files under 50 MB | re-upload a ZIP with the same plugin name; the new version overwrites automatically |
| GitHub sync | repository in `owner/repo` form | automatic sync "when a pull request that includes a plugin version bump is merged to the repository's **default branch**" |

Verbatim restriction: "Your repository must be **private or internal** — public
repos aren't allowed for organization marketplaces." Authentication: "Your
personal GitHub token is verified to confirm you have access, then Cowork uses
its GitHub App installation token for sync operations."

Stated limits: 50 MB per plugin ZIP; 100 plugins per manual marketplace; 500
per GitHub-synced marketplace; 64-character plugin names; 30-minute sync
timeout. Team and Enterprise plans only.

Source: [Manage plugins for your organization](https://support.claude.com/en/articles/13837433-manage-plugins-for-your-organization)
(primary).

### F3. Org marketplaces accept `marketplace.json` but a narrowed source-type set [high]

The org marketplace path references `marketplace.json` for repository structure
and delegates the schema to the plugin reference docs. Supported plugin source
types are **relative paths** (e.g. `"./plugins/my-plugin"`, "fully supported"),
`github`, `url`, and `git-subdir`. Explicitly **not** supported for
organisation marketplaces: `npm`, `archive`, and `command`.

This matters because the full Claude Code marketplace schema admits all seven
source types. A manifest valid for Claude Code is therefore not automatically
valid as an org marketplace.

Source: [Manage plugins for your organization](https://support.claude.com/en/articles/13837433-manage-plugins-for-your-organization)
(primary).

### F4. Group-scoped distribution exists, and is the mechanism a team-level SOP needs [high]

Four per-plugin installation preferences: **Required** (auto-installed, no
removal), **Installed by default** (auto-installed, removable), **Available for
install** (self-service catalogue), **Not available** (hidden). Group-level
overrides are Enterprise-only, for Admins and above, and work with SCIM groups.
Conflict resolution is documented: "If a member belongs to two or more groups
with different settings for the same plugin, the **most permissive** setting
applies," ordered Required > Installed by default > Available for install > Not
available.

The documented pattern for scoping a toolkit to one team is explicit: "To give
a skill to only some users, bundle your skills into a plugin and assign that
plugin to a group."

Sources: [Manage plugins for your organization](https://support.claude.com/en/articles/13837433-manage-plugins-for-your-organization)
(primary); [Cowork and plugins for teams across the enterprise](https://claude.com/blog/cowork-plugins-across-enterprise)
(primary).

### F5. The skills route is one skill per archive — no bulk form exists [high]

`POST /v1/skills` accepts individual files via multipart/form-data or a single
ZIP, and in both cases the upload is exactly one skill, with `SKILL.md` at the
root of a single enclosing folder. There is no bulk-upload endpoint and no
multi-skill archive variant. Size limit under 30 MB uncompressed per skill
\[moderate — primary source, but read through a page summary; verify against the
raw API reference before treating as a hard bound].

Org-wide skill provisioning is real and GA: **Organization settings › Skills**
at `claude.ai/admin-settings/skills`, **Owners only**, same `.zip` format,
"immediately provisioned to all organization members." Updates propagate — "When
an owner saves a new version of a shared skill, everyone it's shared with gets
the update automatically at next use." Users may toggle a provisioned skill off
but cannot delete it. Team and Enterprise only; not marked beta.

A contradiction in Anthropic's own docs resolves as documentation lag, not a
real conflict: `platform.claude.com`'s Agent Skills overview still states that
claude.ai "does not support centralized admin management or org-wide
distribution of custom Skills," but org provisioning shipped 2025-12-18. The
Help Centre and product blog are authoritative on current state.

Sources: [Using Agent Skills with the API](https://platform.claude.com/docs/en/build-with-claude/skills-guide),
[How to create custom skills](https://support.claude.com/en/articles/12512198-how-to-create-custom-skills),
[Provision and manage skills for your organization](https://support.claude.com/en/articles/13119606-provision-and-manage-skills-for-your-organization),
[Skills for organizations, partners, the ecosystem](https://claude.com/blog/organization-skills-and-directory)
(all primary).

### F6. Claude Code's marketplace system is separate, and richer [high]

Claude Code (terminal, VS Code, JetBrains, Desktop's Code tab, Agent SDK) reads
`.claude-plugin/marketplace.json` with all seven source types, and is governed
by `managed-settings.json` keys that the Claude apps' admin console does not
share: `extraKnownMarketplaces` and `enabledPlugins` (any scope), plus
managed-only `strictKnownMarketplaces`, `blockedMarketplaces`,
`disableCommandPluginSources`, and `disableSideloadFlags`.

Two systems, two governance surfaces, one manifest filename. An enterprise
standardising on both surfaces configures each separately.

Sources: [Create and distribute a plugin marketplace](https://code.claude.com/docs/en/plugin-marketplaces),
[Settings reference](https://code.claude.com/docs/en/settings-reference),
[Deploy managed settings](https://code.claude.com/docs/en/managed-settings)
(all primary).

### F7. Programmatic install by a third-party CLI is not a supported surface [moderate]

No `--yes`, no JSON output mode, and no documented exit codes for
`claude plugin install`. The on-disk layout under `~/.claude/plugins/cache/` is
observable but not specified; `~/.claude.json` is internal, and the docs say
"you don't need to edit it." Two settings keys — `extraKnownMarketplaces` and
`enabledPlugins` — **are** documented and writable at user or project scope, so
a third-party tool can legitimately register a marketplace and enable a plugin
for **Claude Code**. Nothing equivalent exists for the Claude apps, whose
plugin state lives server-side behind the admin console.

Anthropic publishes no explicit position permitting or discouraging direct
writes. Practitioner consensus favours shelling out to the CLI over mutating
settings files. Downgrade reason: absence of a documented flag is not proof of
absence, and the cache layout claim rests on observation plus one secondary
source.

Sources: [Settings reference](https://code.claude.com/docs/en/settings-reference)
(primary); [Claude Code Plugins: From Personal Setup to Org Standard](https://claudefa.st/blog/tools/mcp-extensions/plugins-distribution)
(secondary).

### F8. There is no approval workflow on org-wide skill sharing [high]

Anthropic's own documentation states it plainly: "There's no approval workflow
for org-wide sharing. If you enable Share with organization, any user can
publish a skill to the directory without review." Three independent sharing
toggles exist — "Skill sharing" (default on for Team and standard Enterprise,
off for HIPAA-ready orgs), "Share with organization" (default off), and "Share
with groups" (default off). Enterprise plans can additionally enable "Skill and
plugin security scanning" for malicious content. Sharing events land in the
audit log and Compliance API as `role_assignment` events.

For an adopting organisation this is the governance gap a curated catalogue
answers: the platform supplies distribution and scanning, not curation or
review.

Sources: [Provision and manage skills for your organization](https://support.claude.com/en/articles/13119606-provision-and-manage-skills-for-your-organization),
[Use skills in Claude](https://support.claude.com/en/articles/12512180-use-skills-in-claude)
(both primary).

### F9. Mirror rot is the dominant failure mode of the enterprise-clone pattern [moderate]

Across npm/Artifactory pull-through caches, Open VSX mirrors for VS Code forks,
and Backstage software templates, four causes recur:

1. No named owner per item — "a team" rather than a person.
2. No automated test firing when upstream changes; the mirror updates silently
   or not at all.
3. Large surface area — more items means lower average quality, and users
   bypass a mirror they distrust.
4. Distribution decoupled from consumption — the mirror ships, nobody verifies
   what users actually run.

Specific mechanics worth carrying: Artifactory defaults to a 30-minute npm
metadata TTL with artifacts cached indefinitely, so a tag can drift to a new
SHA unnoticed; upstream yanks do not propagate. Anthropic's official marketplace
SHA-pins every entry and its community marketplace auto-bumps pins via CI —
pinning plus a rename map (`renames`) is the published answer to identity drift,
with no cryptographic signing beyond SHA comparison.

Practitioner heuristic from the Backstage corpus: keep three to five golden-path
templates; "a broken template erodes trust faster than no template."

Survivorship bias is explicit and unresolved — no enterprise has published a
post-mortem of a failed internal template or skill registry.

Sources: [What Is a Package Registry Mirror?](https://safeguard.sh/resources/blog/what-is-a-package-registry-mirror)
(secondary); [anthropics/claude-plugins-official](https://github.com/anthropics/claude-plugins-official)
(primary); [Build your first Software Template for Backstage](https://developers.redhat.com/articles/2025/08/12/build-your-first-software-template-backstage)
(primary); [Where the GitHub Copilot extension points break governance](https://devopsjournal.io/blog/2026/05/01/Copilot-extension-governance-concerns)
(secondary).

### F10. CLI prerequisites are the documented adoption blocker for non-technical users [moderate]

Any distribution requiring a CLI install, a git clone, or hand-editing a config
file is a hard stop for a non-technical audience. The prompt-library literature
names the abandonment sequence directly: leave the working tool, open a wiki,
search an index, copy text, paste into the model.

The closest ecosystem analogue is Microsoft 365 Copilot's Prompt Gallery,
described by practitioners as "one of the most underused features" at
enterprise scale, because org-wide enablement requires configuration most teams
skip. Evidence class is qualitative practitioner observation, not measurement.

Sources: [Prompt Library Burnout](https://almcorp.com/blog/prompt-library-burnout-contextual-role-specific-ai-workflows/)
(secondary); [Unlock the Full Power of Microsoft 365 Copilot](https://www.visualsp.com/blog/unlock-the-full-power-of-microsoft-365-copilot-from-the-prompt-gallery-to-complete-team-training/)
(secondary).

---

## What this means for this catalogue

Read against the repository as it stands on 2026-09-10:

| Repository fact | Consequence |
| --- | --- |
| `.github/workflows/publish-claude-plugins.yml` publishes per-pack plugin packages plus a root `marketplace.json` to the **`claude-plugins-dist`** branch | Anthropic's org GitHub sync reads the **default** branch (F2). The two do not meet as configured. |
| `catalogue.toml` sets `claude-plugin-branch = "claude-plugins-dist"` | The branch is already a declared, single-sourced value — the knob an enterprise mirror would repoint. |
| The published catalogue repository is public | It cannot be an **organisation** marketplace (F2). A private or internal mirror is mandatory for the org route. |
| `contracts/distribution-routes.toml` declares three routes (`apm`, `agent-plugin`, `claude-plugins`), each with a nine-component capability map | A Claude-apps route is expressible in the existing contract shape; `command` has no counterpart on that surface and `hook-body` is Cowork-only, so both would declare honestly rather than claim parity. |
| `route_lookup.py` hard-imports the three route modules | Phase 2b of the distribution-routes programme ("route set opening") removes the per-route pins. A fourth route landing before it pays that tax. |
| `product-strategy`, `product-engineering`, `experience-design`, `desk-research` are all `default-scope = "user"`; `core` is `["repo"]` | All four disciplines are already plugin-route-eligible and already published. `core`'s absence is correct, not a gap. |
| `guides/_shared/explanation/install-routes.md:14` scopes the plugin route to "You're on Claude Code" | Stale as written. The route reaches Claude Desktop chat and Cowork too (F1). |

---

## Known unknowns

- **Resolved 2026-09-10, documentation plus owner confirmation:** any paid user
  can self-register a marketplace in the Claude apps under **Customize ›
  Plugins › Personal plugins › "+"**, which offers add-a-marketplace (GitHub
  repository or git URL), upload-a-plugin, or create-a-plugin. This is generally
  available and needs no administrator; the organisation path under
  **Organization settings › Plugins** is a separate, admin-only mechanism
  requiring a private or internal repository. Administrators can restrict what a
  group may install for itself, so reach stays conditional.
- **Resolved 2026-09-10 — the two registries do not cross over.** Claude Code
  and the Claude apps keep separate plugin stores. A marketplace added with
  `/plugin marketplace add` does **not** appear in the chat tab; it is added
  again under Personal plugins. Anthropic's plugin pages never mention Claude
  Code, and document no cross-surface sync. Publishing once serves both
  surfaces; installing once does not. Confirmed by the owner against observed
  behaviour, and the load-bearing correction to any "one install reaches
  everything" reading of this survey's earlier drafts.
- **Known-unknown:** Whether a `marketplace.json` generated for Claude Code
  validates unchanged as an org marketplace manifest, given the narrowed
  source-type set (F3) and the absence of a published org-marketplace schema.
  Would be closed by: pointing a private test repository at Organization
  settings › Plugins and recording the sync result.
- **Known-unknown:** Whether slash **commands** — a canonical primitive in this
  catalogue — have any counterpart on the Claude apps' plugin surface. The
  end-user page names skills, connectors, sub-agents, hooks, and local MCP
  servers, and describes skills as invoked with "/". Commands may be absorbed,
  dropped, or unlisted. Would be closed by: the plugin reference schema, or one
  observed install of a command-bearing plugin.
- **Known-unknown:** The exact per-skill size bound (30 MB is cited from a page
  summary, not read verbatim). Would be closed by: the raw `/v1/skills` API
  reference.
- **Known-unknown:** Whether org-provisioned **plugins** propagate updates the
  way org-provisioned **skills** do ("automatically at next use"). The plugin
  page documents overwrite-on-reupload and PR-merge sync, but not client-side
  refresh timing. Would be closed by: a dated observation on a Team workspace.
- **Unknowable:** Whether a non-technical team actually adopts and retains an
  agent-skill toolkit. No published case study reports measured adoption, week-4
  retention, or failure-to-launch for a named skill toolkit delivered to a
  non-technical audience. Why not: the data is not published — successes appear
  as vendor narratives without denominators, and abandonment is never written
  up. Any adoption target this repository sets is a hypothesis to instrument,
  not a benchmark to match.
- **Unknowable:** Whether the enterprise-clone pattern rots here specifically.
  The four named causes (F9) are drawn from adjacent ecosystems; no Claude
  marketplace mirror has run long enough for a post-mortem to exist.

---

## Evidence-class notes

- Every claim about current Anthropic behaviour is sourced to a primary page
  fetched on 2026-09-10. Two Anthropic surfaces disagreed once (F5); the
  disagreement is dated and resolved rather than averaged.
- Applied-mode independence was enforced: the Cowork blog post and the two Help
  Centre articles are all Anthropic and count as **one** vendor source.
  Findings resting on them alone (F1–F5, F8) are vendor-documentation claims —
  strong evidence of intent and specification, and not a substitute for one
  observed install. No claim here is runtime-verified, which is the same
  posture [RFC-0092](../../rfc/0092-first-class-distribution-routes.md) takes
  toward external-client behaviour.
- F9 and F10 carry the `survivorship bias` downgrade factor. F10 additionally
  carries no quantitative support at all.
