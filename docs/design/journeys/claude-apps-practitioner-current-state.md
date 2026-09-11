---
type: customer-journey
slug: claude-apps-practitioner-current-state
persona: non-technical-practitioner
outcome: produce-a-first-artifact-without-a-terminal
surface: cross-platform
genre: documentation
state: current
evidence-level: assumption-based
evidence_note: >-
  No primary research exists on this persona. The platform mechanics are
  documentation-verified against Anthropic Help Centre pages fetched
  2026-09-10 and confirmed by the repository owner for the registration path;
  none is runtime-verified, consistent with ADR-0107. The repository-side
  facts — which pages mention which surface, and what the site home offers —
  are observational, from direct reads of the working tree on 2026-09-10. The
  emotional arc is inferred, not measured, and is the weakest part of this map.
---

# Journey: the practitioner reaches a discipline method without a terminal

**Relationship to the standing journey.** This is not a competing map. The
gate-approved
[team-orientation future-state map](team-orientation-future-state.md) owns the
adoption lifecycle end to end; this one zooms into the single step where that
map's Stage 2 assumes a terminal, and follows the reader for whom that
assumption fails. Read it as the evidence behind that map's 2026-09-10
amendment, not as a second spine.

**Persona:** A product strategist, researcher, or designer. They use Claude
every day, in the desktop app or the web app. They are not hostile to a
terminal; they simply do not have one open, and a shell command is a signal
about who a thing is for. They are the primary intended user of
`product-strategy`, `desk-research`, and `experience-design`.

**Outcome:** Run one discipline method to a finished artifact — a SWOT, a
journey map, a research survey — inside the Claude surface they already have
open.

**Surface:** cross-platform, documentation genre. Four consuming surfaces that
are *not* interchangeable: Claude Desktop's chat tab, web chat, Cowork, and
Claude Code (including Desktop's Code tab). Claude Code and the Claude apps
keep **separate plugin stores**; registering in one does nothing for the other.
Sub-agents and hooks run only in Cowork. The chat surface reads nothing from
the filesystem.

**Trigger:** A colleague's recommendation, a link to the tech site, or a search
that lands on the repository.

**End state:** A finished artifact the practitioner can show someone, produced
by a named method, in the app they already had open.

---

## Stage 1: Discovering `[observational]` — **negative peak**

| Row | Content |
|-----|---------|
| **Actions** | Lands on the tech site home. Scans for how to get it. Finds a terminal block. Concludes the project is for engineers and leaves — or asks an engineer to "set it up," which converts a self-serve action into a request that may never be made. |
| **Emotions** | Interested, then quietly excluded. This is the deepest dip in the journey, and it happens before any capability is ever exercised. |
| **Pains** | The home page's only install affordance is a terminal component (`InstallTerminal` in `web/src/pages/index.astro`). Across the four other route-documentation surfaces — `README.md`, `docs-site/.../getting-started/install.md`, `guides/_shared/explanation/pack-catalogue.md`, `guides/core/how-to/adapt-to-project.md` — the strings "Claude Desktop", "Claude apps", and "Cowork" appear **zero times**. Nothing anywhere tells this reader the route exists. |
| **Opportunities** | Put a no-terminal route where the terminal currently is. The capability is already shipped and the packs are already published; only the signpost is missing. This is the single highest-value documentation change in the journey. |

The failure is not that the practitioner tries and struggles. They never start.
Everything downstream in this map is unreachable for most of this persona today.

## Stage 2: Orienting `[observational]`

| Row | Content |
|-----|---------|
| **Actions** | If they persist, they look for install instructions. They meet a table of four routes: Claude plugins, APM, Reference CLI, Local clone. They try to work out which one is theirs. |
| **Emotions** | Uncertain. Willing, but unsure whether they are in the right place or about to waste twenty minutes. |
| **Pains** | Every route is named by its **packaging mechanism**, not by **where the reader works**. "Claude plugins" is only meaningful if you already know plugins reach your app. The one page that now explains the Claude-apps path — `guides/_shared/explanation/install-routes.md` — is a `_shared/explanation` page, the kind a reader reaches after they know what they are looking for, not before. |
| **Opportunities** | Offer a route named by surface: "I work in the Claude app" versus "I work in a terminal." Let the packaging mechanism be an implementation detail the reader never has to learn. |

## Stage 3: First value (TTFV) `[assumption-based]` — **second dip, and the highest positive peak**

| Row | Content |
|-----|---------|
| **Actions** | Opens Customize › Plugins › Personal plugins › "+", adds the marketplace from the repository, installs a discipline pack, types `/` and sees the method appear. Runs it. |
| **Emotions** | The registration itself is unremarkable. Seeing their own method appear under `/` is the **highest positive moment in the journey** — the point where the thing becomes theirs. Then, for three of four packs, a fall. |
| **Pains** | Three distinct cliffs, in likelihood order. **(1) Wrong-store registration:** someone who registered in Claude Code finds nothing in the chat tab and reasonably concludes it is broken; nothing warns them the stores are separate. **(2) Silent degradation:** sub-agents are inert in chat, so `desk-research`'s two retrievers, `experience-design`'s reviewer, and `product-engineering`'s three agents do not run — the method still produces *something*, and nothing tells the user it was the thinner version. **(3) Nowhere to land:** the chat surface reads nothing from disk, while these methods are written to end in a committed artifact at a repository path. |
| **Opportunities** | State register-once-per-surface **at the moment of registration**, not in a caveat further down. Publish a plain capability table — skills everywhere, sub-agents and hooks in Cowork only. Say honestly where an artifact goes on each surface, and name the surface to move to when the method needs a filesystem. |

Cliff (3) is the one documentation can least repair, and the most important to
state plainly rather than discover. A practitioner who completes a SWOT and
cannot save it has had a demo, not a first value.

## Stage 4: Recurring reference `[assumption-based]`

| Row | Content |
|-----|---------|
| **Actions** | Comes back for a second method. Later updates the packs. If they also use the Code tab, does all of it a second time, separately. |
| **Emotions** | Mild friction, accepted. Not a dip so much as a tax. |
| **Pains** | Two registrations to maintain, updated independently, with no surface showing what is installed where. Version skew between one person's own two surfaces is possible and invisible. |
| **Opportunities** | Say that upgrades are per surface too. Nothing here needs building; it needs stating once, where the reader already is. |

## Stage 5: Mastery `[assumption-based]`

| Row | Content |
|-----|---------|
| **Actions** | Chooses surface by method: Cowork when the method dispatches sub-agents, the Code tab when the output must land in a repository, chat for everything else. |
| **Emotions** | Fluent. The surface split has stopped being a trap and become a tool. |
| **Pains** | The mapping from method to best surface is currently folklore. Nobody has written it down. |
| **Opportunities** | One short "which surface for which method" table converts the journey's biggest structural weakness into a described capability. |

---

## Frontstage actions

- **Action:** land-on-the-site-home
- **Action:** scan-for-how-to-get-it
- **Action:** meet-a-terminal-block
- **Action:** ask-an-engineer-instead
- **Action:** look-for-install-instructions
- **Action:** compare-four-named-routes
- **Action:** open-customize-plugins
- **Action:** add-a-marketplace-from-a-repository
- **Action:** install-a-discipline-pack
- **Action:** type-slash-and-see-the-method
- **Action:** run-the-method
- **Action:** look-for-the-artifact
- **Action:** register-again-on-a-second-surface
- **Action:** update-packs-per-surface
- **Action:** choose-a-surface-for-a-method

## Emotional arc

Interested → **excluded (deepest dip, Stage 1)** → uncertain → **delighted
(highest peak, Stage 3, at first `/` invocation)** → dropped (Stage 3 cliffs) →
mildly taxed → fluent.

The arc's defining feature is that its deepest negative moment comes **first**,
before any capability is exercised, and its highest positive moment comes only
a few steps later. The distance between them is almost entirely documentation.

## Peak moments

| Moment | Stage | Why it ranks |
|---|---|---|
| **Negative peak** | Stage 1, Discovering | The reader self-selects out at the terminal block. Everything downstream is unreachable, so no other improvement pays off until this one lands. |
| **Second dip** | Stage 3, First value | Three cliffs — wrong store, silent degradation, nowhere to save. Each is survivable if stated in advance and damaging if discovered. |
| **Positive peak** | Stage 3, first `/` invocation | The method appears inside the user's own tool. Design should protect this moment and place it as early as possible. |

## Handoff notes

**Highest-opportunity pains, ranked.** (1) No no-terminal route exists at the
point of discovery. (2) Routes are named by packaging mechanism, not by where
the reader works. (3) Register-once-per-surface is unstated at the moment it
matters. (4) Sub-agent degradation is silent. (5) Artifact destination per
surface is unstated.

**What documentation can and cannot fix.** Pains 1–3 and 5 are pure
documentation and are fully addressable. Pain 4 is only *disclosable* here —
the underlying behaviour is owned per pack (`research-pack/spec.md` specifies
inline fallback; `experience-reviewer-work-loop-gate/spec.md` makes reviewer
absence a named skip), so documentation states it and any deviation is a defect
against the owning spec.

**Scope boundary this map must not cross.** Nothing here may assert that a given
pack *delivers first value* on the Claude apps. `[pack.first-value].surfaces`
must be a subset of `[pack.install].allowed-adapters`, and all four discipline
packs declare `["claude-code"]`, so that claim is unavailable until the
contract's owner decides the vocabulary. This journey describes reaching and
running a method; it does not certify a first-value surface.

**Next step.** `documentation-design` owns the surface design for a
documentation-genre journey — it decides what content type belongs where and
what the first-value moment is per type. The two decisions it must make are
whether the Stage 1 fix is a new page or a home-page entry, and whether the
Stage 3 cliffs belong in one page with the registration steps or in a separate
capability reference.

**Backstage services implied.** None new. The published marketplace, the
per-pack plugin packages, and the publish workflow all exist and are unchanged
by anything in this map.
