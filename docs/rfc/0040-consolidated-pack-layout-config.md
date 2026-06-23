# RFC-0040: A consolidated, namespaced pack-output layout file (`agentbundle-layout.toml`)

- **Status:** Accepted <!-- Draft | Open | Final Comment Period | Accepted | Rejected | Withdrawn | Experimental -->
- **Author:** eugenelim
- **Approver:** eugenelim
- **Date opened:** 2026-06-22
- **Date closed:** 2026-06-22
- **Related:** RFC-0039 / ADR-0029 (research project mode — introduced `research-layout.toml`, the file this generalises; the only existing prompt-only-read layout precedent); RFC-0038 (forward-only migration pattern — considered, then found not to apply); RFC-0035 (`references/sso-config.toml` — namespaced adopter-editable TOML + shipped-placeholder delivery; **note: code-read via `tomllib`, *not* a prompt-only-read precedent**); RFC-0034 (`profiles/<name>.toml` config precedent); ADR-0021 (pack manifest as source of truth — the `[pack.layout]` extension lands here)

## The ask

- **Recommendation (BLUF):** Replace the research-only `research-layout.toml` with one
  namespaced **`agentbundle-layout.toml`** that every output-producing pack reads — one
  `[<pack>]` table each, whose `parent` key names a **base directory under which each unit of
  work gets its own topic-named folder** (e.g. `efforts/research/2026-06-22-oauth-pkce/`,
  `efforts/architecture/billing-rearchitecture/`). Two locations with precedence (a repo-root
  file overrides a user-profile file), per-table override, read prompt-only by skill bodies.
  Wire **three** consumers — `research`, `architect`, `product-engineering` — in one
  implementing spec. Because the file is created/maintained under separate per-pack installs,
  the `agentbundle` installer gains an **append-if-exists, never-overwrite** step.
- **Why now (SCQA):** *Situation* — research project mode just shipped (RFC-0039) with an
  adopter-created `research-layout.toml` resolving where a project corpus lives. *Complication*
  — two more packs carry the same friction (`architect` re-elicits a save location every run;
  `product-engineering` hardcodes `docs/product/…`), and `research 0.4.0` has **not been
  distributed** (it landed after the last release), so the config shape is changeable at zero
  migration cost *right now*. *Question* — do we consolidate into one namespaced contract while
  it's free, or let a `research-layout.toml` / `architect-layout.toml` / … proliferation set in?
- **Decisions requested:**
  1. **Consolidate** the per-pack config into one namespaced `agentbundle-layout.toml`
     (vs keep per-pack files; vs do nothing). · recommended: **consolidate** · default if no
     objection: yes.
  2. **Filename & visibility** `agentbundle-layout.toml` — a *visible* repo-root file (vs a
     `.agentbundle-layout.toml` dotfile). Visible because it's config-as-code an adopter should
     see and commit, like `pyproject.toml`. · recommended: visible, as named · default: yes.
  3. **Precedence** repo-root `./agentbundle-layout.toml` **overrides** user-profile
     `~/.agentbundle/agentbundle-layout.toml`. · recommended: repo wins · default: yes.
  4. **Override granularity** per-table (a higher-precedence file replaces a whole `[<pack>]`
     table; tables only in the lower file survive). · recommended: per-table · default: yes.
  5. **Schema** one `parent` key per `[<pack>]` table — a *base* under which the skill creates a
     topic-named work folder; the skill owns the folder-naming convention. · recommended: as
     stated · default: yes.
  6. **Install-time maintenance** the installer appends a pack's section **if the file already
     exists, never overwriting** an existing section. · recommended: append-if-exists · default:
     yes.
  7. **Append-default source** the per-pack default lives in a new optional **`[pack.layout]`
     table in `pack.toml`** (a manifest/contract extension — ADR-0021), which either declares
     the section inline **or points to a within-pack `agentbundle-layout.toml` template**, and
     may be **scope-keyed** (`[pack.layout.repo]` / `[pack.layout.user]`) so a pack behaves
     differently installed at repo vs user scope (e.g. `product-engineering` at repo scope →
     repo-relative `docs/product`; at user scope → an absolute base). · recommended: as stated
     · default: yes.
  8. **Migration** rename `research-layout.toml` → the `[research]` table outright — **no
     legacy alias** (the file is undistributed). Bump `research` 0.4.0 → 0.5.0. · recommended:
     as stated · default: yes.
  9. **Path anchoring** `parent` is anchored by the layout file's *location*, not blanket
     absolute: a **repo-root** file's `parent` is **repo-root-relative** (portable across
     clones); a **user-profile** file's `parent` **must be an explicit absolute path**
     (`~`-anchored ok) because a user-scope skill has no stable relative base. The skill always
     resolves to and **surfaces the full absolute path before writing**. · recommended: as
     stated · default: yes.

## Problem & goals

**Diagnosis.** Three packs each want adopters to control where their durable output lands, and
each solves it differently or not at all:

| Pack | Writes | Where today | Gap |
|---|---|---|---|
| `research` (project mode) | a multi-week project folder (`sources/`, digests, synthesis) | `research-layout.toml` `parent` → out-of-repo scratch → elicit (`research-project-start/SKILL.md:84-109`) | works, but the config is research-shaped and research-only |
| `architect` | `architect-design` design doc | re-scans `docs/design/`→`design/`→`architecture/`→`docs/` and offers the first that exists, else elicits — **every run** (`architect-design/SKILL.md:83-86`) | no way to *fix* the location once; the adopter is asked every time, and output is a loose file, not a per-effort folder |
| `product-engineering` | `frame-intent` → `docs/product/intents/`, `align-value-stream` → `docs/product/rollups/` [^briefs] | hardcoded `docs/product/…` | an adopter who keeps product docs elsewhere must fork the skill |

[^briefs]: `decompose-intent` also writes `docs/product/briefs/<slug>.md` (`decompose-intent/SKILL.md:53`), but a brief is the hand-off point to core's `receive-brief` — it is **not** a `product-engineering`-relocatable output and stays pinned to `docs/product/briefs/` (see Non-goals).

Left alone, each pack grows its own `*-layout.toml`, and an adopter customizing three packs
juggles three files with three schemas. The config *shape* is the cheapest to fix now: the
only existing instance (`research-layout.toml`) ships in an **undistributed** release.

Two nuances the contract must carry:

- **The defaults differ in kind.** `research` defaults *out-of-repo* (a code repo shouldn't
  carry a source corpus); `architect` defaults to its existing *scan-then-elicit* behaviour;
  `product-engineering` defaults to a *committed `docs/product/` subdir*. So "never the
  committed tree" is a **research-specific default**, not a property of the shared file. The
  file supplies a `parent` override; each pack's default and posture stay in its own skill body.
- **`parent` is a base, not the leaf.** `research` already nests each project under
  `<parent>/<YYYY-MM-DD>-<topic-slug>/`. We generalise that: `architect` likewise gives each
  design effort its own `<parent>/<topic-slug>/` folder (a design effort accrues a doc,
  diagrams, notes — a folder, not a loose file). So an adopter who sets
  `[research] parent = "efforts/research"` and `[architect] parent = "efforts/architecture"`
  gets a tidy `efforts/research/<topic>/` + `efforts/architecture/<topic>/` tree; pointing the
  parents independently is equally fine. The topic-folder nesting is the *skill's* job; the
  file only configures the base.

**Goals.**
- One namespaced file, one `[<pack>]` table per consumer, one resolution rule.
- `parent` configures a base; each unit of work lands in its own topic-named folder beneath it.
- Two locations with clear precedence so a team can commit repo-wide config and an individual
  can keep a personal default.
- Reading stays **prompt-only** (a skill body reads it; no engine/index/daemon — ADR-0029 /
  Charter Principle 3 hard boundary).
- The file is **adopter-owned and never shipped as a projected artifact**; it only ever exists
  on an adopter's machine (hand-written, skill-scaffolded on consent, or installer-maintained).
- Adding the next consumer is a table, not a migration.

**Non-goals.**
- **Not** making every pack's output configurable. Specs (`docs/specs/`), ADRs, RFCs,
  contracts (`contracts/<type>/`), and packages (`packages/`) are deliberately fixed —
  discovery and governance depend on those locations. This RFC touches only the three packs
  whose output an adopter genuinely relocates.
- **Not** relocating `receive-brief` or the brief output. `receive-brief` (core) and
  `decompose-intent` both write `docs/product/briefs/`; that stays pinned even when
  `product-engineering` relocates its `intents/` and `rollups/`. **Decided** (Approver: leave
  it) — core can opt in as a `[core]` consumer in a later RFC if a need appears.
- **Not** a runtime config engine. The installer's append step is install-time code (peer to
  the existing install-marker writer), not a thing that runs while a skill operates.
- **Not** prescribing whether an adopter commits their file. The repo-level layer is
  config-as-code; committing it is encouraged but theirs to decide.

## Proposal

### The file

A namespaced TOML, one table per consuming pack, single `parent` key naming a **base**:

```toml
# agentbundle-layout.toml  (adopter-owned; never shipped)
# repo-root form shown — parents are repo-relative (Decision 9);
# in the user-profile file they must be absolute, e.g. parent = "~/efforts/research"
[research]
parent = "efforts/research"        # base; each project → <parent>/<YYYY-MM-DD>-<topic-slug>/
                                   # (default: out-of-repo scratch)
[architect]
parent = "efforts/architecture"    # base; each design effort → <parent>/<topic-slug>/
                                   # (default: existing scan docs/design/→design/→architecture/→docs/, else elicit)
[product-engineering]
parent = "docs/product"            # base for intents/ + rollups/ (default: docs/product)
```

### What `parent` means — a base, with a topic-named folder per work unit

`parent` is the directory the pack writes *under*, never the leaf the work lands *in*. The
skill creates a topic-named child folder per unit of work, using its own naming convention:

| Pack | Folder per unit of work | Inside |
|---|---|---|
| `research` | `<parent>/<YYYY-MM-DD>-<topic-slug>/` (unchanged) | `overview.md`, `sources/`, digests, synthesis, brief |
| `architect` | `<parent>/<topic-slug>/` (new — was a loose file) | the design doc, diagrams, notes for that effort |
| `product-engineering` | `<parent>/{intents,rollups}/<slug>.md` (file-per-slug, not a folder) | a single intent/rollup file each |

`product-engineering` is the deliberate exception: its outputs are single per-slug files handed
downstream, so a per-topic *folder* buys nothing — it keeps its file-per-slug-under-subdir
shape. Each pack's `references/` schema doc (below) states which shape it uses; the shared
contract only standardises `parent`.

### Anchoring — what `parent` is relative *to* (Decision 9)

`parent` is anchored by the **layout file's own location**, never by the ambient working
directory:

- **Repo-root file** (`./agentbundle-layout.toml`): `parent` is **repo-root-relative**
  (`docs/architecture`, `efforts/research`). This is the config-as-code case — a committed file
  must be portable across clones, so relative-to-repo is correct (the same rule `tsconfig`/
  `.editorconfig` use). An absolute value is permitted but warned (non-portable). A relative
  value with no `..` is naturally confined to the repo; an absolute or `..`-escaping value is
  the surfaced, Ask-first, untrusted-origin case (see Risks).
- **User-profile file** (`~/.agentbundle/agentbundle-layout.toml`): `parent` **must be an
  explicit absolute path** (`~`-anchored, e.g. `~/research-projects`, expands to absolute). A
  user-scope skill runs from arbitrary working directories across many repos, so a *relative*
  `parent` here has no stable base and would silently resolve against the wrong cwd — a
  relative value is an Ask-first deviation, not a silent guess.

Regardless of anchor, the skill **resolves to and surfaces the full absolute path before the
first write** (security AC, below) — so the adopter always sees the explicit full path.
Install-time append (Decision 6) writes the default in the *form* its target file expects: a
repo-file append uses the pack's repo-relative default; a user-file append uses an absolute /
`~`-anchored default (or a commented placeholder when no sensible absolute default exists, so
the installer never writes a wrong-anchor value — the spec settles the exact form).

### Two locations, repo overrides user

- **User profile:** `~/.agentbundle/agentbundle-layout.toml` — an individual's default across
  repos.
- **Repo root:** `./agentbundle-layout.toml` — the project's checked-in config.
- **Repo wins, per table.** When both define `[<pack>]`, the repo file's table is used whole;
  a table present only in the user file survives. (This mirrors npm's `project > user` and
  Cargo's deeper-directory precedence; because each table is single-key today, per-table
  override coincides exactly with the per-key merge those tools document — we take the simpler
  per-table rule, which a prompt-only reader executes without deep-merge bookkeeping.)

### Resolution tail (per pack, unchanged in shape)

1. Read `agentbundle-layout.toml` — repo file's `[<pack>]` table, else user file's — to get
   `parent`, then **anchor it** (Decision 9): a repo-file value is repo-root-relative, a
   user-file value must be absolute.
2. Fall back to the **pack's own default** base (research → out-of-repo scratch; architect →
   its existing scan-then-elicit; product-engineering → `docs/product`).
3. **Elicit** — and the elicitation is now a first-class bootstrap step (below).
4. Resolve to the **full absolute path** (realpath, `~`-expanded, `..` rejected), **surface it**
   to the adopter, then create the topic-named work folder under it.

### How a `[<pack>]` section comes to exist — three paths (create vs maintain)

The file is adopter-owned and never shipped. It comes into being one of three ways:

1. **Skill elicitation, on consent (create).** When a skill resolves no section and the
   adopter declines the default, the skill offers to **scaffold** the file — at repo root or
   user profile (adopter picks) — writing only its own `[<pack>]` section. This is the path
   that creates the file when absent. Adopter-*initiated*, skill-*written*: still
   adopter-owned, still never shipped.
2. **Installer append-if-exists (maintain).** `agentbundle install <pack>` adds an
   `_append_layout_section` step (modelled on the existing `_append_install_marker` upsert,
   `install.py:2026-2228`, called from the Step-11 per-scope loop, `install.py:1109-1123`):
   *if* a layout file exists at the install scope's location, ensure `[<pack>]` is present —
   append the pack's default if missing, **never overwrite** an existing section. It does
   **not** create the file from nothing, so installing a pack never litters a config file an
   adopter didn't ask for; once the file exists, every later pack install keeps it current.
   The append default is sourced from the pack's `[pack.layout]` manifest table (Decision 7) —
   inline, or a within-pack `agentbundle-layout.toml` template, **selected by the install
   scope** (`[pack.layout.repo]` vs `[pack.layout.user]`) so the appended default already
   matches the target file's anchor (repo-relative for the repo file, absolute for the user
   file). It is serialised through the existing injection-safe `config._emit_basic_string`
   emitter (`config.py:383`) and written via the path-jailed atomic `safety.write_jailed`
   (`safety.py:264`).
3. **Hand-authored.** The adopter writes it directly, guided by the `references/` schema doc.

The within-pack `[pack.layout]` template/declaration is **shipped pack metadata** (the
*default source*, like the `sso-config.toml` placeholder) — distinct from the active
`agentbundle-layout.toml`, which is adopter-owned and never shipped.

### Per-pack schema doc (shipped) vs the file (not shipped)

Each consuming pack ships `references/agentbundle-layout.md` — a normal projected pack file
(the same *delivery* path as RFC-0035's `sso-config.toml` placeholder, which rides into the
installed skill tree as an ordinary in-skill file) documenting its own `[<pack>]` section: the
`parent` key, the default base, the per-unit folder shape, and the posture (committed-docs vs
out-of-repo). The skill body reads it to both **parse** an existing section and **scaffold** a
correct one. The schema doc and the within-pack `[pack.layout]` template default are the
shipped artifacts; the **active** `agentbundle-layout.toml` is never shipped and never lives
under `packs/`.

### Migration

`research-layout.toml`'s top-level `parent` becomes the `[research]` table's `parent`. Because
`research 0.4.0` landed (2026-06-22) **after** the last release `agentbundle-v0.6.0`
(2026-06-21), no distributed artifact reads `research-layout.toml` and no adopter holds one —
so this is a **clean rename with no legacy alias** (the RFC-0038 one-release-alias pattern was
considered and found not to apply: there is nothing in the wild to be backward-compatible
*with*). Update `research-project-start`'s body, the research reference and how-to guides, the
`docs/product/changelog.md` `[Unreleased]` entry (which names `research-layout.toml` at
`changelog.md:35`), and bump `research` 0.4.0 → 0.5.0.

### Self-host housekeeping

Add `agentbundle-layout.toml` to *this* repo's `.gitignore` (alongside the existing
`.adapt-install-marker.toml` entry) so a contributor exercising a consumer skill in the
catalogue can't trip the self-host drift gate. This is a one-repo decision; we ship adopters
**no** gitignore rule — their repo-level file is config-as-code and theirs to commit.

## Options considered

**Axis: how adopter-relocatable output configuration is filed and namespaced** — the space is
exhausted by *number of files × namespacing style*, plus the do-nothing baseline.

| Option | Shape | Prior art | Trade-offs |
|---|---|---|---|
| **0. Do nothing** | research keeps `research-layout.toml`; architect keeps re-eliciting; product-engineering stays hardcoded | — | No work now. But the *next* pack repeats the question, the proliferation it invites is the expensive path, and the free-migration window (research undistributed) closes at the next release. |
| **1. Per-pack files** | `research-layout.toml`, `architect-layout.toml`, … one schema each | git's many dotfiles; eslint's per-tool configs | Each pack self-contained. But an adopter customizing N packs juggles N files/schemas, and there's no shared precedence story. |
| **2. One shared file, flat prefixed keys** | one file, `research_parent` / `architect_parent` / … no tables | `.npmrc` flat keys; `.editorconfig` sections-but-flat | One file, but the namespace lives in a key-name convention rather than structure; harder for a skill to scope "read only my section," and per-table override has no natural unit. |
| **★ 3. One shared file, `[<pack>]` tables** | `agentbundle-layout.toml`, table per pack, repo>user | `pyproject.toml` `[tool.*]`; Cargo `[profile.*]`; RFC-0035 `sso-config.toml` namespacing | One file, one rule, one precedence; the table is the natural per-pack scope and override unit; next consumer is a table. Costs: a shared contract to govern, an installer append step, a small `pack.toml` extension. **Recommended.** |

Option 3 wins on the namespacing-style sub-axis (a structural table beats a key-prefix
convention for "read/scaffold only my section" and for per-table override), and one-shared
beats per-pack on the file-count axis once the consumer count is ≥2.

## Risks & what would make this wrong

**Pre-mortem.**
- *The installer step violates the prompt-only boundary.* — It doesn't: **reading** stays in
  the skill body (prompt-only); **writing** is install-time code, peer to the install-marker
  writer that already upserts TOML on the adopter's machine. No engine runs while a skill
  operates. Mitigation: the implementing spec's ACs forbid any runtime reader/engine, and the
  adversarial + security pass checks for it.
- *Per-table override surprises an adopter who set `parent` at user level and a different key
  at repo level.* — Tables are single-key today, so the surprise can't arise yet; the
  references doc states the rule. If a table ever grows a second key, revisit (per-key merge is
  the documented fallback).
- *`pack.toml` `[pack.layout]` is a manifest/contract extension (now scope-keyed).* — Adding
  `[pack.layout]` (with optional `.repo`/`.user` sub-tables and a within-pack template
  reference, Decision 7) will bump the manifest contract version and touch the manifest
  validator. Mitigation: keep it one additive optional table with optional scope sub-tables;
  the spec carries the contract-bump test traps (lexical version-compare, CI-ungated test
  roots) called out in repo memory, and the manifest schema/validator update is an explicit
  spec task, not an afterthought.
- *Installer writes a repo file that trips the self-host drift gate.* — Mitigated by the
  `.gitignore` entry; the gate diffs only build-projected paths and honours gitignore.
- *Changing `architect`'s output from a loose file to a per-effort folder surprises current
  users.* — A deliberate, Approver-required change, not gold-plating: a platform has **many
  architecture topics** and no single doc can carry them all, so each topic gets its own
  `<parent>/<topic-slug>/` folder (matching research's project-folder shape). It is *additive*
  (a folder around what was a file), `architect` is user-scope, and the spec documents the
  shift. The behavior change rides in this spec by design (it's the same per-topic-folder
  generalization the shared contract is about), not as unrelated scope.
- *A hostile `agentbundle-layout.toml` in a cloned untrusted repo redirects a skill's writes.*
  — Making the repo-root file the **higher-precedence** source (Decision 3) crosses a real
  boundary: an adopter who clones an untrusted repo and runs a consumer skill has the skill
  read an attacker-authored `./agentbundle-layout.toml` whose `parent` points anywhere
  (`~/.ssh`, `../sibling-repo`, an absolute path). Because the reader is **prompt-only**
  (Charter Principle 3 forecloses a code path-validator), the control must be **prose-enforced
  acceptance criteria in the spec**, not a code jail: each consumer's skill body must (a)
  resolve `parent` (realpath, expanding `~`, rejecting `..` escapes), (b) **surface the
  resolved absolute path before the first write**, and (c) treat a repo-root-sourced `parent`
  that resolves outside the repo tree as an **Ask-first deviation** — the same prose-rail
  posture `research-project-start/SKILL.md:103-109` already takes, generalised to the two new
  consumers (whose research-specific "never the committed tree" default does not transfer).
  The user-profile file is foot-gun-only (the adopter is the author); the repo-root layer is
  the untrusted-origin case. Verification is goal-based / manual-QA by construction, not a unit
  test — the spec's Testing Strategy must say so.

**Key assumptions (falsifiable).**
- *A skill body can reliably read a two-location namespaced TOML and apply repo-overrides-user.*
  — Already shipped: `research-project-start` reads `research-layout.toml` at two locations
  prompt-only today. Adding a table namespace is a same-shape increment.
- *`research 0.4.0` is undistributed, so no alias is needed.* — Verified against tag dates
  (research 0.4.0 commit 2026-06-22 > `agentbundle-v0.6.0` 2026-06-21). If a release cut
  between draft and merge includes research 0.4.0, decision 8 reverts to a one-release alias.
- *Architect and product-engineering are genuine relocation needs, not just research.* — This
  is the load-bearing assumption, and the **Approver confirms it as a real need** (not a
  build-the-seam hedge): the original code survey found only research with an *existing*
  config, but the friction is real and named — architect's every-run re-elicit can't scale to
  a platform's **many architecture topics** (one design doc can't hold them; each topic needs
  its own folder, hence the file→folder change), and product-engineering's hardcoded
  `docs/product/` blocks adopters who file product docs elsewhere. All three land in one spec
  (Approver's explicit call). Residual exposure if the demand read is softer than stated: the
  contract still degrades gracefully — a pack with no adopter section just uses its default —
  so over-fitting risk is low.

**Drawbacks.** A shared contract is one more governed surface; the installer gains a step and
`pack.toml` gains a table; three packs' skill bodies and one installer change in a single spec.
These are real costs, accepted because the alternative (per-pack proliferation) is worse and
the migration is free only this release.

## Evidence & prior art

- **Spike / de-risk.** No new spike needed — the riskiest assumption (prompt-only two-location
  read) is *already shipped* behaviour in `research-project-start` (`SKILL.md:84-109`). The
  installer's append-if-exists upsert is the established `_append_install_marker` pattern
  (`packages/agentbundle/agentbundle/commands/install.py:2026-2228`); the injection-safe
  emitter (`config._emit_basic_string`, `config.py:383`) and the path-jailed atomic write
  (`safety.write_jailed`, `safety.py:264`) are reused as-is. The drift-gate interaction was
  traced in `build/self_host.py`: the gate diffs only build-projected paths and both its
  dirty-tree and unclassified-path checks honour `.gitignore`.
- **Repo precedent.** `research-layout.toml` (RFC-0039 / ADR-0029 — adopter-created,
  never-shipped, **prompt-only-read**; the generalised case, including the `<parent>/<topic>/`
  nesting this RFC extends to `architect` — and the *only* prompt-only-read layout precedent
  in the repo); `references/sso-config.toml` (RFC-0035 — namespaced adopter-editable TOML
  shipped as an in-skill placeholder; precedent for the **namespacing + placeholder-delivery**
  of `references/agentbundle-layout.md`, **not** for prompt-only reading — `sso-config.toml`
  is parsed by a Python script via `tomllib`); RFC-0034 (`profiles/<name>.toml` config
  precedent); ADR-0021 (manifest as source of truth — home for `[pack.layout]`); ADR-0029 /
  Charter Principle 3 (prompt-only hard boundary the reader must respect).
- **External prior art.**
  [Cargo config](https://doc.rust-lang.org/cargo/reference/config.html) merges per key with
  deeper directories taking precedence over `$HOME`; [npm `.npmrc`](https://docs.npmjs.com/cli/v11/configuring-npm/npmrc/)
  resolves per key with `project > user > global`. Both confirm **more-specific (repo/project)
  overrides less-specific (user/global)** — we adopt the precedence and take the simpler
  per-table override (equivalent while tables are single-key), because our reader is a prompt,
  not code. `pyproject.toml`'s `[tool.<name>]` convention is the direct prior art for one
  shared file namespaced by consumer table.

## Open questions

None remain — every decision above is settled by the Approver. For the record, the one prior
open edge is now **decided**: install **never creates** the file when absent; it only
append-maintains an existing file (Decision 6). Creation happens solely when a **skill or pack
elicits it for an explicit user decision** (path 1 above) or by hand-authoring — installing a
pack never imposes a config file.

## Follow-on artifacts

Filled on acceptance:

- **ADR** — record the consolidated layout contract (one namespaced file, repo>user per-table,
  `parent`-as-base with per-unit topic folders, prompt-only read + install-time append,
  adopter-owned/never-shipped) and that it generalises ADR-0029's `research-layout.toml`.
- **Spec** — `docs/specs/consolidated-pack-layout/` — one spec covering: the file contract and
  resolution rule; `research` migration (rename, no alias, 0.4.0→0.5.0) + body/guide/changelog
  updates; `architect` (new consumer + per-effort folder) and `product-engineering` (new
  consumer, file-per-slug) skill-body reads + `references/` schema docs; the installer
  `_append_layout_section` step (append-only, **never creates**) + the scope-keyed
  `pack.toml` `[pack.layout]` (`.repo`/`.user` sub-tables and/or a within-pack template) and
  its manifest-schema/validator + contract-version update; the `.gitignore` entry.
  Implemented via `/work-loop`. **Security ACs the spec must carry** (from the spec-stage
  review; the prompt-only boundary makes the first three prose-enforced / goal-based, not unit
  tests): (1) each consumer confines the resolved `parent`+folder to the pack's intended root,
  rejecting `..` escapes and surfacing the resolved absolute path before the first write;
  (2) the resolved path is realpath-resolved so a symlinked `parent`/ancestor is visible and
  not silently followed out of tree; (3) a repo-root-sourced `parent` resolving outside the
  repo is treated as untrusted-origin and confirmed before writing; (4) the installer append
  serialises every pack-sourced string through `config._emit_basic_string` and writes via
  `safety.write_jailed`, pinned by a construction test that round-trips a `[pack.layout]`
  default containing `"`, `]`, newline, and `../` through `tomllib`, plus a never-overwrite
  test guarding an existing `[<pack>]` section against clobber.
- **Convention** — note the `agentbundle-layout.toml` contract in `docs/CONVENTIONS.md` (the
  adopter-owned-config surface) if the Approver wants it discoverable there.
