# Plan: ux-writing-rename

- **Spec:** [`spec.md`](spec.md)
- **Status:** In Progress

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

Pure rename-and-sweep, no logic changes. Shape: rename the skill directory in source, update frontmatter + body self-reference, sweep all operative inbound references, add RFC-0066 errata, update changelog and workspace.toml comment, then run `make build-self` to regenerate the projected tree. The lint gate (zero `grep` hits over the operative set) is the hard acceptance criterion; everything else is in service of passing it.

Pack manifests (`pack.toml`, `plugin.json`) require no changes — product-engineering has no skills-array entry for `voice-and-microcopy` and both descriptions already use `ux-writing`.

Order of operations: rename source directory → update frontmatter + body → sweep inbound refs → add errata + changelog + workspace comment → build-self → lint gate + build-check → open PR.

## Constraints

- RFC-0066 D7: no alias; clean retire only; operative/historical classification rules apply.
- ADR-0038: alias-free rename precedent — operative references swept in the same PR.
- RFC-0071 OQ3: grep-verified count recorded in spec before PR opens.
- RFC-0055: errata on Accepted RFC uses `## Errata` (not `## Amendments`); must be Approver-signed.
- CONVENTIONS §2: frozen RFC/ADR/spec bodies are never edited.
- CONVENTIONS §Pack source-of-truth split: `make build-self` must run after source edits; direct edits to projected paths are caught by `make build-check` and rejected.

## Construction tests

**Lint gate (runs at T4):**
```bash
git ls-files | xargs grep -Hn "voice-and-microcopy" \
  | grep -v "docs/rfc/0048-" \
  | grep -v "docs/rfc/0050-" \
  | grep -v "docs/rfc/0053-" \
  | grep -v "docs/rfc/0062-" \
  | grep -v "docs/rfc/0066-" \
  | grep -v "docs/rfc/0071-" \
  | grep -v "docs/adr/" \
  | grep -v "docs/specs/" \
  | grep -v "docs/product/changelog.md" \
  | grep -v "docs/rfc/README.md" \
  | grep -v "docs/rfc/0053-notes/"
# Must return zero hits.
```

**Build gate (runs at T4):**
```bash
make build-check
# Must exit 0.
```

## Tasks

### T1: Rename skill directory and update SKILL.md

**Depends on:** none  
**Touches:** `packs/product-engineering/.apm/skills/voice-and-microcopy/` (renamed), `packs/product-engineering/.apm/skills/ux-writing/SKILL.md`

**Tests:**
- Goal-based (AC1): `ls packs/product-engineering/.apm/skills/ux-writing/` succeeds; `ls packs/product-engineering/.apm/skills/voice-and-microcopy/` fails.
- Goal-based (AC2): `grep "^name: ux-writing" packs/product-engineering/.apm/skills/ux-writing/SKILL.md` returns a hit; `grep "voice-and-microcopy" packs/product-engineering/.apm/skills/ux-writing/SKILL.md` returns zero hits.

**Approach:**
```bash
git mv packs/product-engineering/.apm/skills/voice-and-microcopy \
       packs/product-engineering/.apm/skills/ux-writing
```
Then update `SKILL.md`:
- Frontmatter `name:` field: `voice-and-microcopy` → `ux-writing`
- Scope-boundary note in body: `voice-and-microcopy` → `ux-writing` (the self-reference in the "`voice-and-microcopy` covers product UI copy states" line)

---

### T2: Sweep operative inbound references

**Depends on:** T1  
**Touches:** experience-design pack skills + README, product-engineering discovery-loop + README, product-strategy define-content-strategy, guides (3 files), web content (3 files)

**Tests:**
- Goal-based (AC8): `grep -rl "voice-and-microcopy" packs/ guides/ web/` returns zero operative files after sweep.

**Approach:** Run `git ls-files | xargs grep -Hl "voice-and-microcopy"` to get the exact live list. For each operative file, replace `voice-and-microcopy` → `ux-writing` (exact-string substitution; no logic changes). Known files:

| File | Nature of reference |
|------|---------------------|
| `packs/experience-design/.apm/skills/tone-of-voice/SKILL.md` | skill reference |
| `packs/experience-design/.apm/skills/user-flow/SKILL.md` | skill reference |
| `packs/experience-design/.apm/skills/user-flow/assets/design-tool-handover-template.md` | skill reference |
| `packs/experience-design/.apm/skills/user-flow/assets/screen-brief-template.md` | skill reference |
| `packs/experience-design/.apm/skills/user-flow/references/screen-flow.md` | skill reference |
| `packs/experience-design/.apm/skills/design-review/references/quality-floor.md` | skill reference |
| `packs/experience-design/.apm/skills/content-design/SKILL.md` | skill reference |
| `packs/experience-design/README.md` | skill listing |
| `packs/product-engineering/.apm/skills/discovery-loop/SKILL.md` | cross-skill reference |
| `packs/product-engineering/README.md` | skill listing |
| `packs/product-strategy/.apm/skills/define-content-strategy/SKILL.md` | cross-skill reference |
| `guides/README.md` | guide listing |
| `guides/experience-design/reference/experience-design.md` | skill listing |
| `guides/product-engineering/README.md` | guide listing |
| `guides/product-engineering/how-to/write-product-microcopy.md` | how-to guide prose |
| `web/src/components/marketing/PackCatalogue.astro` | marketing catalogue |
| `web/src/content/journeys/discovery.md` | journey content |
| `web/src/content/packs/product-engineering.md` | pack page |

---

### T3: Add RFC-0066 errata, update changelog and workspace.toml

**Depends on:** T2  
**Touches:** `docs/rfc/0066-experience-pack-surface-genre-and-skill-uplift.md`, `docs/product/changelog.md`, `workspace.toml`

**Tests:**
- Goal-based (AC5): `grep "## Errata" docs/rfc/0066-experience-pack-surface-genre-and-skill-uplift.md` returns a hit.
- Goal-based (AC6): `grep "\[Unreleased\]" docs/product/changelog.md` returns a hit referencing `ux-writing`.
- Goal-based (AC9/workspace.toml): `grep "voice-and-microcopy rename" workspace.toml` returns zero hits.

**Approach:**

Add `## Errata` section at the end of RFC-0066 (after `## Follow-on artifacts`):

```markdown
## Errata

| # | Date | Topic | Effect |
|---|------|-------|--------|
| 1 | 2026-07-27 | `voice-and-microcopy → ux-writing` rename governance | D7 required "a separate product-engineering RFC" for this rename. That separate RFC was not written. The rename was implemented via `docs/specs/ux-writing-rename/`, citing RFC-0066 D7 + ADR-0038 as the governing decisions. RFC-0071 OQ3's grep-verified count requirement was honored in that spec. This errata discharges the "separate product-engineering RFC" requirement from D7. |

eugenelim, 2026-07-27
```

Add `[Unreleased]` entry to `docs/product/changelog.md`:
```
**Renamed:** `voice-and-microcopy` → `ux-writing` in `product-engineering` pack (RFC-0066 D7 / spec: `ux-writing-rename`).
```

Update `workspace.toml`: in the `product-engineering-shaping-doctrine` queue entry comment, remove the sentence(s) that note the `voice-and-microcopy → ux-writing` rename as deferred/included, since the rename now ships standalone.

---

### T4: Build gates and lint

**Depends on:** T3  
**Touches:** projected paths (read-only; `make build-self` regenerates)

**Tests:**
- Goal-based (AC4): `make build-self FORCE=1` exits 0 (`product-engineering` skills are core-only in `.apm/`; not projected to `.claude/skills/` or `.agents/skills/`).
- Goal-based (AC3): lint gate returns zero hits.
- Goal-based (AC7): `make build-check` exits 0.

**Approach:**
```bash
make build-self
# Then run lint gate and build-check (see Construction tests above).
```

Record grep-verified count in `spec.md` (RFC-0071 OQ3):
```bash
git ls-files | xargs grep -l "voice-and-microcopy" \
  | grep -v "docs/rfc/0048-" | grep -v "docs/rfc/0050-" \
  | grep -v "docs/rfc/0053-" | grep -v "docs/rfc/0062-" \
  | grep -v "docs/rfc/0066-" | grep -v "docs/rfc/0071-" \
  | grep -v "docs/adr/" | grep -v "docs/specs/" \
  | grep -v "docs/product/changelog.md" | grep -v "docs/rfc/README.md" \
  | wc -l
```
Record the pre-sweep count in `spec.md`'s `<!-- Grep-verified count: TBD -->` comment.
