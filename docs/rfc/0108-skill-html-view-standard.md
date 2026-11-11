# RFC-0108: One usability-first standard and shared style for skill-emitted HTML views

- **Status:** Accepted
- **Author:** eugenelim
- **Approver:** Platform Core maintainer
- **Date opened:** 2026-10-12
- **Date closed:** 2026-10-12
- **Decision weight:** standard
- **Related:** [RFC-0105](0105-artifact-derived-navigation-and-workspace-retirement.md) (D3 and D4 each receive an errata exception), [RFC-0106](0106-stop-registering-derivable-work.md), [CAP-0001](../product/intents/CAP-0001-repository-work-graph.md), [FEAT-0002](../product/intents/FEAT-0002-intent-graph-navigation.md), [FEAT-0034](../product/intents/FEAT-0034-workspace-registry-retirement.md), [`intent-navigation-export` spec](../specs/intent-navigation-export/spec.md)

## Reviewer brief

- **Decision:** Skills that emit HTML follow one usability-first standard. The four that emit a view for a maintainer share one visual style. The intent navigator may show `workspace-status`'s readiness through a temporary, read-only bridge, and hands a picked item over only through a fixed-template prompt.
- **Recommended outcome:** Accept.
- **Change if accepted:**
  - Five HTML-emitting skills in three packs share one rule set. Four maintainer views also share one stylesheet, kept byte-identical by a build-check gate.
  - RFC-0105 D3 and D4 each gain one errata exception. D3's: `navigate-intents` may embed a validated, allowlisted projection of `workspace-status`'s canonical output, piped to it at export, until `work-loop` stops dispatching from `workspace-status`.
  - D4's: a picked item hands over through a prompt built from a closed template set and a grammar-checked path. Every launching mechanism, including custom-scheme links, needs its own security-reviewed decision.
- **Affected surface:**
  - core: `navigate-intents` and `explain-diff`;
  - governance-extras: `navigate-decisions`;
  - converters: `render-proof` and `markdown-to-html`;
  - `build_gate_chain.py`, which gains one parity gate.
- **Stakes:** The standard and the style are cheap to revise. The bridge is reversible by design and ends on a named condition. D4 deliberately leaves the page with no authority to launch anything.
- **Review focus:** whether the bridge reopens the drift RFC-0105 D3 guards against; whether the prompt rule closes the path from repository text to agent instructions; whether model-written `explain-diff` pages can meet the content security policy floor.
- **Not in scope:**
  - retiring `workspace.toml` or `workspace-status`;
  - a loopback server, a launcher or a terminal-host integration;
  - a shared renderer or data model;
  - the visual style of documents an author publishes with `markdown-to-html`.

## Terms used here

- **`workspace.toml` and `workspace-status`.** `workspace.toml` is this repository's work registry file. `workspace-status` is the skill that reads it and reports the work queue.
- **Canonical ready, active and blocked sets.** The lists in `workspace-status`'s status output of specs that `work-loop` may start now, that are in progress, or that a dependency or finding stops. "Canonical" means these are the lists `work-loop` itself dispatches from.
- **Argless `work-loop`.** Starting the `work-loop` skill without naming a spec, so it chooses one from those sets.
- **First-in-list selection.** `work-loop`'s current rule of choosing the first ready item in registry order.
- **Adapter projection.** The rewritten copy of each skill that the build installs for each agent host (Claude Code, Codex, Cursor, Copilot, Gemini CLI). Folder layouts differ between hosts, so one skill cannot rely on a path to another.
- **Parity gate.** A build check that fails when copies of a file stop being byte-identical.
- **Data block.** The JSON embedded in an exported page. The shipped export escapes it so record text can never run as code (its acceptance criteria AC-0031, AC-0034 and AC-0035).
- **RFC-0105.** The accepted decision that the intent navigator derives everything from the files themselves. Its D3 makes retiring `workspace.toml` a target reached through four gates, and it forbids new navigation work from depending on `workspace-status`. The first gate is a consumer inventory: every reader of `workspace.toml` or `workspace-status` must be listed and given a replacement. Its D4 says a generated view never becomes an input to another workflow.
- **RFC-0106 D1.** The accepted rule that a spec's readiness will come from its own headers (its `Status:`, a sibling plan and its `Depends on:` line) instead of the registry. It also removes first-in-list selection.
- **Intents.** Records of an intended outcome. CAP-0001 is the capability for navigating repository work. FEAT-0002 is the feature intent for the intent navigator. FEAT-0034 retires `workspace.toml` once every reader has a replacement.
- **Errata entry.** A dated correction appended to an accepted RFC and signed by its Approver.
- **Worklist and document density.** The style's two spacing and type settings: tight rows for lists, a readable line length for prose. The values are in the token file D2 names.

## The ask

**Recommendation:** accept D1 to D5.

**Why now.** The `navigate-intents` export shipped on 2026-10-11 (core 3.1.0). It is safe and meets WCAG 2.2 AA, but its owner found it hard to use:
- it opens on 6 counts, 4 tabs, 4 filters and a 168-row tree;
- each row leads with a machine id;
- a 15-row legend fills the detail panel;
- its 202 open items have no order.

The other HTML-emitting skills each look and behave differently, so nothing learned in one carries to the next. The owner also wants this view to become where a maintainer starts each session. RFC-0105 D3 currently forbids it from using the only source that knows what is ready.

| ID | Question | Recommendation | Why | Decide by | Reviewer action |
| --- | --- | --- | --- | --- | --- |
| D1 | Should skill-emitted HTML follow one usability-first standard? | Yes: a normative standard, binding each view from its adoption | The views already diverge; only a standard gives reviewers a bar | 2026-10-19 | Accept or amend the rules |
| D2 | How does one style reach the four maintainer views? | One canonical stylesheet in `navigate-intents`, byte-copied into each adopter, with a build-check parity gate | Skills stay self-contained, each hash is computed from a file inside the skill, and the mirror-check pattern exists | 2026-10-19 | Accept or name another mechanism |
| D3 | May the navigator show `workspace-status` readiness? | Yes, as a validated projection of piped `workspace-status` output, ending when `work-loop` stops dispatching from it | The page must never disagree with `work-loop` about what is ready | 2026-10-19 | Accept the RFC-0105 D3 exception and its end condition |
| D4 | How does a picked item reach a skill? | A prompt from a closed template set with one grammar-checked path, copied on click; nothing that launches | Repository text must never become agent instructions; the file stays inert | 2026-10-19 | Accept the RFC-0105 D4 exception |
| D5 | In what order do the skills adopt? | `navigate-intents`, `navigate-decisions`, `explain-diff`, `render-proof`, then the `markdown-to-html` floor | The first adopter is already designed and de-risked | 2026-10-19 | Accept |

## Problem & goals

**Problem.** Each skill that emits HTML designed its view around its data. None sets out what a reader should get from the first screen.
- Two views share a palette by copy.
- `explain-diff` has no house style by design.
- `render-proof` has a distinct palette.
- `markdown-to-html` has no dark mode and no content security policy, and it loads Mermaid from a CDN.

Reviews of the intent view checked 1280×900 and 320px, never wider. At 1680 and 2560px the page leaves empty bands on both sides.

**Goals.**
- A reader of any skill-emitted view answers that view's main questions from its first screen.
- What a maintainer learns in one view (state marks, keys, focus, layout zones) works the same in every other.
- A maintainer can start a session from the intent view, pick work, and hand it to the right skill, without the view and `work-loop` ever disagreeing about what is ready.

**Non-goals.**
- One renderer or one data model for all views; FEAT-0002 keeps "sharing a renderer with `navigate-decisions`" as a non-goal.
- Readiness, dependency or repair logic inside the navigator, now or after the bridge ends.
- Giving any view authority to launch, write or reach the network.
- Imposing a house style on documents an author publishes for their own readers.

## Proposal

### D1 — A usability-first standard for skill-emitted HTML

**Scope.** The standard covers every skill that writes an HTML file for a person to read. Today that is five skills:
- maintainer views: `navigate-intents`, `navigate-decisions`, `explain-diff` and `render-proof`;
- a publication tool: `markdown-to-html`, whose output an author ships to their own readers.

Rules 1 to 7 cover the maintainer views. Rules 8 to 10 cover all five.

1. **Questions first.** The view names the questions it answers, and its first screen answers them without search. Counts appear only as answers to a named question.
2. **Ranked by the job.** Content is ordered by what the reader is trying to do, not by how the data is stored.
3. **Names lead.** A row or heading leads with the human name. Ids, paths and slugs are secondary: searchable, and shown in detail.
4. **State is a word plus a shape.** Colour may reinforce state but never carries it alone, per WCAG 2.2 SC 1.4.1.
5. **Reference on demand.** Keys, legends and field definitions open on request and never fill space before the reader asks.
6. **Detail leads with action.** A detail pane opens with the item's state, its next step, what is open beneath it and what is broken. Raw fields come last, collapsed.
7. **Honest order.** Every list names its sort key. No view presents a priority its source records do not hold.
8. **Every width checked.** Layout adapts to the width and is checked at 320, 1280, 1680 and 2560 CSS px, in light and dark. The 320px check uses a true 320px viewport, per SC 1.4.10, not a cropped wider window.
9. **Accessible floor.** WCAG 2.2 AA throughout. That includes SC 2.4.11 (a focused control is never fully hidden by author content) and SC 2.5.8 (targets at least 24 by 24 CSS px). Every action works by keyboard. There is no motion.
10. **Inert and offline, under a stated policy floor.** The view is one self-contained file that makes no network requests and runs no record text as code. Its content security policy is at least:
    - `default-src 'none'`;
    - scripts and styles allowed only by hash, with no `'unsafe-inline'` and no `'unsafe-eval'`;
    - `base-uri 'none'` and `form-action 'none'`;
    - no `url(` or `@import` in any stylesheet;
    - no inline `style` attributes;
    - images only when a view embeds them, either as `data:` URIs under `img-src data:`, or as inline SVG that passes an allowlist of elements and attributes. The view's spec names the allowed set, and anything not named is removed. Whatever the set:
      - `script`, `foreignObject`, `set`, `animate`, `animateMotion`, `animateTransform` and `iframe` are never kept;
      - `use` and `image` are kept only with a same-document fragment target;
      - every `href` and `xlink:href` must pass the view's link allowlist;
      - SVG `<style>` content is joined into the one hashed style element under the `url(` and `@import` ban, or removed.

    A link a person clicks may go only to schemes and hosts on an allowlist that the view's spec names. A vendored renderer, such as an offline Mermaid build, is pinned, verified by hash, and recorded under the repository's dependency rule, and it runs under the same floor. An exception to any part of rule 10 is recorded as an Approver-signed errata entry on this RFC, never taken in a spec alone.

**When it binds.** An existing view is bound from the release that adopts it under D5, not from this RFC's acceptance. A new HTML-emitting skill is bound from its first release.

**Where authors find it.** A shared reference guide, `guides/_shared/reference/html-view-standard.md`, states rules 1 to 10 without citing this RFC, so shipped pack content may point to it. Each adopting skill's own authoring reference restates the rules it relies on, so the skill stays whole on its own.

### D2 — One shared style for the four maintainer views

The style is the owner-selected direction in [`docs/design/direction/skill-html-views.md`](../design/direction/skill-html-views.md), selected on 2026-10-12. Its values are in [`docs/design/tokens/skill-html-views.md`](../design/tokens/skill-html-views.md). It has two densities:
- worklist, for `navigate-intents` and `navigate-decisions`;
- document, for `explain-diff` and `render-proof`.

**How the bytes travel.**
- **Canonical file.** The canonical file is `packs/core/.apm/skills/navigate-intents/scripts/view_assets/view-base.css`. It ships with the first adopter.
- **Byte copies.** Each other adopter carries a byte-identical copy inside its own skill tree.
- **Parity gate.** A gate in `build_gate_chain.py` fails when any copy differs from the canonical file. It follows the byte-mirror pattern of the roster test that checks `navigate-decisions`' copy of `file_safety`.
- **Changing the style.** A change edits the canonical file and every copy in one change, and bumps each affected pack's version.

**How it reaches each policy.**
- A view's own layout rules live in a second file inside its skill. That file never overrides a shared colour, type or state-mark rule.
- At build time the two files are joined into the single `<style>` element whose hash the policy names. That keeps the shipped export rule of one style element and one style hash (`intent-navigation-export` AC-0029).
- For `explain-diff`, the publisher injects the shared base as trusted bytes, joins it with the page's own `<style>`, and hashes the result. The publisher refuses `style` attributes. This replaces its current `style-src 'unsafe-inline'`.

`render-proof` keeps its proof chrome distinct from a published document. `markdown-to-html` does not adopt this style, and its author-chosen themes stand.

### D3 — A gated read-only readiness bridge (errata exception to RFC-0105 D3)

**What RFC-0105 D3 says.**
- "`navigate-intents` must derive navigation from canonical artifact metadata. It must not read `workspace.toml` as its inventory, lifecycle authority, or graph source."
- "Until all four gates pass, `workspace-status` and `workspace.toml` remain supported compatibility surfaces. New navigation work must not add further dependencies on them."

This RFC adds one exception, to the second sentence only.

**How readiness arrives.**
- `navigate-intents` never runs `workspace-status`, never locates its script, and never reads `workspace.toml`.
- The skill's instructions tell the agent to pipe `workspace-status`'s read-only status command into the export, as `export --readiness -`. Both skills are installed and run by the agent through its normal tools, so nothing depends on where an adapter projection puts a sibling skill.
- When `workspace-status` is not installed, or the agent does not pipe it, the page says readiness was not checked and calls nothing ready.

**How the export treats that input.** The piped bytes are untrusted data. The export:
- caps the input by size;
- requires a status payload with the expected schema version, mode and repository-relative root, and typed lists;
- keeps only an allowlisted projection: a repository-relative path, the set it belongs to (ready, active or blocked), a finding `code`, `dispatchable`, and `next_action`;
- drops locators, absolute or unconfined paths, and every other field;
- shows a `next_action` outside the known vocabulary as inert text under a generic label;
- passes the projection through the shipped data-block escape and hostile-fixture criteria (AC-0031, AC-0034 and AC-0035), plus a hostile `workspace.toml` fixture.

Bridge data can only add a readiness mark to a record the navigator has already loaded from the files. It never adds a row, a link or a prompt of its own. Any failed check leaves readiness unchecked; the export still succeeds.

**What the page may say.** The page says "ready" only for an item in the canonical ready set. Where it says which item an argless `work-loop` starts, it follows `work-loop`'s own order:
- with exactly one active item, that item is the one `work-loop` resumes;
- with more than one, `work-loop` asks, and no item is marked;
- with none, the first ready item is the one it starts.

Those marks state dispatch behaviour, not priority. They go when RFC-0106 removes first-in-list selection.

**Why the exception leaves the first sentence intact.** Readiness says whether `work-loop` may start an item now. Lifecycle authority says what state the item itself is in. The bridge supplies only the first. Every record's lifecycle status still comes from the record's own `Status:`. The navigator still reads no inventory, lifecycle or graph from `workspace.toml`. RFC-0105 D3's four retirement gates, and its rule that priority and human selection are never presented as graph derivation, are unchanged.

**End condition and owner.** The bridge ends in the release where `work-loop` stops dispatching from `workspace-status`, under RFC-0106 D1. From then on the page takes readiness from the read-only output of whatever owner `work-loop` then dispatches from, through the same validated projection. The navigator never derives readiness itself. The bridge reads `workspace-status`'s output, so it must appear in RFC-0105 D3's consumer inventory. That gate therefore cannot pass until the bridge is moved. The FEAT-0034 dispatch specification lists it there, and the `navigate-intents` owner moves it in that release.

### D4 — Hand-over by fixed-template prompt only

**The prompt.**
- For a picked item, the page may show a prompt that starts a skill on it. The prompt comes from a closed set of fixed templates, chosen by the item's recorded state. Each template names a skill and mode from a closed vocabulary, for example: "Use the work-loop skill to implement `<path>`."
- The only slot filled in is the item's repository-relative path. It must match a strict grammar: at most 200 characters, under `docs/specs/`, `docs/product/briefs/` or `docs/product/intents/`, ending in `.md`, with every `/`-separated segment matching `[A-Za-z0-9][A-Za-z0-9._-]{0,99}` and no segment equal to `..`. It must also name a record the navigator loaded under its confinement helper.
- A record that fails the grammar gets no prompt and a plain reason. It never gets a cleaned-up prompt.
- Headings, titles, `next_action` and other free text never enter a prompt.

**Copying.** Copying uses the browser clipboard on that click. The copied string equals the visible prompt byte for byte. When copying fails, the visible prompt is selected for manual copy. A hostile-fixture test covers paths carrying whitespace, a newline, a bidirectional control, an instruction phrase, a backtick, `$(`, `|` and `;`, and shows that none produces a prompt.

**What counts as a launcher.** The page launches nothing. A loopback server, a launcher, a terminal-host integration, and any link with a non-`https` scheme or that starts a local program all count as launchers. Each needs its own security-reviewed decision.

This is a narrow, reviewed exception to RFC-0105 D4's rule that generated HTML never becomes an input to another workflow. The only thing that crosses is a fixed template and one validated path, and a person chooses to paste it.

### D5 — Adoption order

Each adoption is its own spec and its own pack version bump. A maintainer view counts as adopted when it meets D1 and carries D2's stylesheet under the parity gate. `markdown-to-html` counts as adopted when it meets rules 8 to 10.

1. **`navigate-intents`.** The redesign is designed and de-risked. It lands as new slices of the [`intent-navigation-delivery`](../product/briefs/intent-navigation-delivery.md) brief, with the shared stylesheet and its parity gate. The brief's queued dependency-graph slice is re-fitted to the new layout before it is built.
2. **`navigate-decisions`.** It moves from `style-src 'unsafe-inline'` to one hashed style element.
3. **`explain-diff`.** Its authoring reference takes rules 1 to 10. Its publisher injects the shared base and hashes styles, as D2 describes.
4. **`render-proof`.** It takes the document density and keeps its proof chrome distinct. To meet rule 10 it gains a content security policy, moves code highlighting from inline `style` attributes to class-based output, and stops its sanitizer keeping `style` attributes and `url()` values. Document content that relied on inline styles renders without them.
5. **`markdown-to-html`.** It gains a policy that meets rule 10 and dark-mode support within its own themes. Its diagrams come from the `mermaid-renderer` skill in place of the CDN, embedded in the single file as `data:` images under rule 10's image clause. Mermaid draws flowchart labels inside `foreignObject`, which the inline-SVG allowlist removes, so inline SVG is not used for diagrams. Its spec adds a hostile-diagram fixture covering an `xlink:href`, an animated `href` change and a `foreignObject` link, and shows that no link survives in the page.

## Options considered

- **D1, where the rule lives.**
  - *Do nothing:* the views keep diverging, and nothing tells a reviewer what a new view must meet.
  - *An advisory guide:* RFC-0105 D5 already makes design advice non-binding, and that is how the current view shipped hard to use.
  - *A normative standard (chosen).*
- **D2, how the bytes travel.**
  - *Do nothing:* hand copies have already drifted.
  - *A runtime import from another skill:* not portable across adapter projections, and skills must be self-contained.
  - *`.apm/shared-libs/`:* this works within one pack only. It would still need copies in governance-extras and converters, and it puts the hashed file outside the skill that hashes it.
  - *A pack dependency on core for converters:* it couples a converter pack to core for one stylesheet.
  - *Byte copy plus parity gate (chosen).*
- **D3, where the view gets "ready" from.**
  - *Do nothing:* the view cannot answer "what can I work on next", so it never replaces session-start orientation.
  - *Derive readiness from headers now:* RFC-0106 D1's rule is accepted but is not yet what `work-loop` dispatches from, so the page and `work-loop` could disagree.
  - *The export runs `workspace-status` itself:* it needs a path to a sibling skill that adapter projections do not guarantee, and it adds the export's first non-Git subprocess.
  - *Piped, validated bridge (chosen).*
- **D4, how much authority the page gets.** Clearly dominant: a fixed-template prompt keeps the page inert. Every other option moves a security boundary, and no host contract exists to integrate with.

## Risks & what would make this wrong

- **The bridge outlives its purpose.** It ends on a named condition, and RFC-0105 D3's consumer-inventory gate cannot pass while it remains. A stale snapshot shows its generation time, so it never reads as live.
- **The bridge disagrees with `work-loop`.** The page shows `workspace-status`'s own sets and `work-loop`'s own order, and never re-derives either. A snapshot can still go stale between export and use. `work-loop` re-checks readiness before it starts.
- **A prompt carries hostile text.** Only a fixed template and a grammar-checked, loaded path reach a prompt. A record that fails gets no prompt. A hostile fixture proves both.
- **Model-written pages cannot meet rule 10.** If `explain-diff` cannot reach the floor through D2's publisher route, its adoption stops. The exception is proposed as Approver-signed errata on this RFC.
- **One style fits no view well.** The density split exists for that reason. If a view still fights the style, a refinement of the direction changes the canonical file for all adopters.
- **The redesign does not beat search.** De-risk passed on a prototype (owner, 2026-10-12). FEAT-0002's 4-of-6-session comparison against repository search runs on the shipped build. If it fails, the view is reworked.

## Evidence & prior art

- **De-risk.** On 2026-10-12, the owner tried a prototype built from that day's real export and `workspace-status` output. They answered all four session-start questions from the first screen. It was checked at 320, 1280, 1680 and 2560px in both themes. See [`session-start-orientation-ia.md`](../design/screens/session-start-orientation-ia.md) § De-risk result.
- **Bridge cost.** `workspace-status`'s status command took 0.5 s on this repository on 2026-10-12. It returned 4 ready, 0 active, 29 blocked and 65 findings.
- **Security review.** A spec-stage secure-design review of D3 and D4 on 2026-10-12 found two blockers and three concerns, then confirmed the revision clean:
  - repository text could reach an agent through the prompt, resolved by D4's fixed templates, per-segment path grammar and hostile fixture;
  - an export-time subprocess had no stated controls, resolved by D3's piped input, so the export starts no process;
  - bridge output was not treated as untrusted, resolved by D3's validated, allowlisted projection;
  - rule 10 named no policy floor, resolved by the floor it now states;
  - custom-scheme links escaped the launcher boundary, resolved by D4's launcher definition.
- **In-repo precedent.**
  - [RFC-0106](0106-stop-registering-derivable-work.md) changed a sibling RFC's decision through an errata entry on RFC-0103; this RFC does the same for RFC-0105. RFC-0106 D1 is the readiness rule the bridge's end condition names.
  - The roster test "navigate-decisions file_safety mirror", registered in `tools/lint-ci-parity.py`, checks a byte copy against its source: the mirror pattern D2 reuses.
- **External standard.** [WCAG 2.2](https://www.w3.org/TR/WCAG22/) SC 1.4.1 Use of Color (A), 1.4.10 Reflow (AA), 2.4.11 Focus Not Obscured (Minimum) (AA), and [2.5.8 Target Size (Minimum)](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html) (AA).

## Follow-on artifacts

- **RFC-0105 errata entry**, pointing its D3 at this RFC's D3 and its D4 at D4's narrow exception.
- **`guides/_shared/reference/html-view-standard.md`**, carrying D1's rules for reviewers and skill authors.
- **Specs, one per adopter, in D5's order.**
  - The first is the `navigate-intents` redesign, as a new slice of the `intent-navigation-delivery` brief. It amends the shipped `intent-navigation-export` spec's view criteria. Among them are AC-0035 (closed label set), AC-0037 to AC-0044 (summary, views, detail and legend), and AC-0056 to AC-0061 (keyboard, viewports and landmarks), and it ships the shared stylesheet and parity gate.
  - The readiness bridge and the hand-over prompt are a second `navigate-intents` slice. It amends that spec's agent rule "Never let the export or view code read `workspace.toml`" to admit the piped projection, and it carries D3's and D4's acceptance criteria.
- **FEAT-0034 dispatch specification**, listing the bridge in its consumer inventory and removing or re-pointing it in the release where `work-loop` stops dispatching from `workspace-status`.
- **Not follow-on work here:** moving `work-loop` Step 0 and the session-start activation boundary to the view belongs to FEAT-0034, after parity.

## Errata

- 2026-10-16, signed by eugenelim as Approver: D1 rule 9's last sentence, "There is no motion.", is replaced with "Motion is limited to colour, border, shadow and opacity transitions and a fade of at most 4px, each at most 200ms, only under `prefers-reduced-motion: no-preference`, and never on scroll." Under reduced motion the page stays still, so WCAG 2.2 SC 2.3.3 holds, and no motion carries information. The same day the owner refined D2's direction, [`skill-html-views`](../design/direction/skill-html-views.md), to soft zones, tinted state pills and these fades after reviewing a prototype; its [token file](../design/tokens/skill-html-views.md) carries the values. The [`intent-view-source-and-style`](../specs/intent-view-source-and-style/spec.md) spec applies both to `navigate-intents`; every other rule is unchanged.
- 2026-10-17, signed by eugenelim as Approver: D1 rule 1 is met by a view whose navigation links show short labels, provided the list on screen names its full question above its title and every navigation link carries its full question as its accessible description. The [`intent-view-tree-and-roadmap`](../specs/intent-view-tree-and-roadmap/spec.md) spec applies this to `navigate-intents` (its AC-0051 and AC-0054); every other rule is unchanged.
- 2026-10-29, signed by eugenelim as Approver: D3's bridge reads `work-loop`'s argless `dispatch.py` output in place of `workspace-status`'s status, under [RFC-0106](0106-stop-registering-derivable-work.md) D1. The argless mark copies dispatch's decision, so it marks nothing when several specs are ready or active.
