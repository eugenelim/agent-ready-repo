# Plan: One copy-layer skill with three modes

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `packs/AGENTS.md` (§ Version bump rule; § Authoring or editing a skill); `tests/AGENTS.md` (the three guarded edits a **new** `tests/roster/test_*.py` owes, which this plan avoids by extending an existing suite); `tests/roster/test_experience_design_write_declaration_and_containment.py` — specifically `test_every_containment_copy_is_byte_identical` and its citation-derived copy set, the pattern this delivery reuses; two analogous multi-mode skills — `packs/core/.apm/skills/project-knowledge/` (capture / distill / enquire behind one description) and `packs/core/.apm/skills/author-delivery-brief/` (create / continue). Named uncertainty: the pervasive-versus-localized divergence classification has no repository precedent and is authored here as a judgement with a recorded verdict.

> **Plan contract:** this is the implementation strategy. It may change
> substantively only while its Status is `Drafting`. After approval, `spec.md`
> and `plan.md` are pinned in substance; execution observations belong in
> `notes/verification-ledger.md`.

## Approach

Three registrations become one skill with three modes. Unlike the genre fold,
almost none of the work is moving method — it is **reconciling six pairs of files
that share a name and disagree**, and doing it without silently picking a winner.

Order is forced three ways. The activation baseline runs first, before any
deletion (T1). The reconciliations happen before the merge (T3–T4), because a
merged skill built on an unreconciled pair bakes in whichever variant was pasted
first. And the whole slice is blocked behind the genre fold landing
`editorial-quality-gates.md` under `information-architecture` — checked as a
precondition in T2, not assumed.

The riskiest part is T3. `copy-arbitration.md` diverges on every paragraph, and
the spec's own rule forbids both concatenation and letting one variant win when
the divergence is scope-borne. The only remaining move is a rewrite with one
named scope parameter, which is authoring rather than merging.

## Constraints

- `packs/AGENTS.md` § Version bump rule — removals are **major**;
  `experience-design` → `4.0.0` (second of two). `product-engineering` takes a
  **patch**, `0.13.17 → 0.13.18`. `frontend-engineering` takes none: it names
  neither removed skill.
- ADR-0038 — alias-free; the sweep completes inside this PR.
- RFC-0062's 2026-08-02 erratum — `tone-of-voice` is brand-level and
  `copy/brand-register.md` is reserved. Both survive.
- RFC-0055 D2 — both errata sections convert to the two-layer form.
- An erratum names no spec and no brief.
- `tests/AGENTS.md` — a new roster suite owes three further guarded edits; this
  plan extends an existing suite to avoid them.
- The surviving name is `content-design`, forced by a suite that hard-codes it.

## Construction tests

Cross-cutting, after every wave:

```bash
python3 tools/lint-experience-agnostic.py
python3 -m pytest tests/roster -q -k "experience or content_design"
```

## Verification command map

**Commands are fenced blocks, never table cells.** A shell pipe inside a markdown
table must be escaped as `\|`, which is not a pipe — the registration sweep
written that way matched nothing and exited 0, reporting success while checking
nothing. Every block below was executed against the pre-fold tree on 2026-09-24
and its present-state reading recorded, so a reviewer can distinguish a broken
command from a failing check.

Set the roots once:

```bash
CD=packs/experience-design/.apm/skills/content-design
REMOVED='\b(copy-direction|tone-of-voice)\b'
```

**The three modes, named literally** so no reader confuses them with the three
`communication_mode` values a roster suite already asserts:

```bash
for m in 'message and narrative structure' 'per-surface acquisition copy goals' 'brand-level register'; do
  grep -q "$m" "$CD/SKILL.md" || echo "MODE MISSING: $m"
done
```

**Each reference exists exactly once, under the surviving skill.** The existence
half is scoped to `$CD` — a pack-wide count of 1 passes even when the file landed
in the wrong skill:

```bash
for r in copy-arbitration copy-grounding plain-language-floor copy-jtbd; do
  test -f "$CD/references/$r.md" || echo "MISSING $CD/references/$r.md"
  n=$(find packs/experience-design/.apm/skills -name "$r.md" | wc -l | tr -d ' ')
  [ "$n" = 1 ] || echo "EXPECTED 1 $r.md pack-wide, found $n"
done
# interrogation-sequence survives twice: content-design and creative-direction
[ "$(find packs/experience-design/.apm/skills -name interrogation-sequence.md | wc -l | tr -d ' ')" = 2 ] || echo "interrogation-sequence count wrong"
# editorial-quality-gates survives twice: content-design and information-architecture
[ "$(find packs/experience-design/.apm/skills -name editorial-quality-gates.md | wc -l | tr -d ' ')" = 2 ] || echo "editorial-quality-gates count wrong"
test ! -f "$CD/references/audience-jtbd.md" || echo "merged file must be copy-jtbd.md, not audience-jtbd.md"
```

**The shared editorial file is cited from the surviving `SKILL.md`.** The roster
suite derives its copy set from `SKILL.md` text only, so a citation living in a
reference body leaves the copy an orphan:

```bash
grep -q 'references/editorial-quality-gates.md' "$CD/SKILL.md"
```

**Byte-equality, by the named new assertion** rather than the whole suite. The
file passes 6 tests today, before any extension exists, so running it whole
proves nothing about this delivery:

```bash
python3 -m pytest tests/roster/test_experience_design_write_declaration_and_containment.py \
  -q -k editorial_quality_gates_copies_are_byte_identical
# must be RED before the extension lands and GREEN after;
# the extension carries the existing len(copies) >= 2 vacuity guard
```

**The brand register emits both markers** — with file arguments, which an earlier
draft omitted:

```bash
T="$CD/assets/tone-of-voice-template.md"
grep -q 'type: tone-of-voice' "$T" && grep -q 'scope: brand-level' "$T"
```

**The discriminator survives, by counted occurrence.** `grep -c` counts *lines*;
these are *occurrences*, so the check must use `grep -o`:

```bash
check() { n=$(grep -o 'type: tone-of-voice' "$1" 2>/dev/null | wc -l | tr -d ' '); [ "$n" = "$2" ] || echo "$1: want $2, got $n"; }
check "$CD/SKILL.md" 7            # 4 inherited from copy-direction + 3 from tone-of-voice
check "$CD/assets/tone-of-voice-template.md" 1
check "$CD/evals/evals.json" 2
check packs/experience-design/.apm/skills/experience-status/SKILL.md 1
check packs/product-engineering/.apm/skills/ux-writing/SKILL.md 3
check packs/product-engineering/.apm/skills/ux-writing/evals/evals.json 2
# tone-of-voice/references/agentbundle-layout.md holds 5 more and is deleted with
# its directory; the Follow-on records that the family shrinks rather than closing
```

**No removed name survives as a registration.** Real alternation, and the repo
root and `docs/` are in scope because `workspace.toml` and open records carry
them:

```bash
grep -rlE "$REMOVED" packs/ guides/ web/ tools/ tests/ workspace.toml 2>/dev/null \
  | grep -vE '\.apm/skills/(copy-direction|tone-of-voice)/' \
  | grep -vF 'web/src/lib/now-highlights.generated.json'
# `now-highlights.generated.json` is excluded: it is generated and gitignored,
# rebuilt from the changelog by every `web/` and `docs-site/` run, so it is not a
# surface this delivery edits and a hit there is noise, not a defect.
# want: only files whose hits are discriminator uses on the counted list above.
# 28 files today. Classify each hit registration vs discriminator; a registration
# hit is a defect, a discriminator hit is required.
grep -n 'copy/' packs/experience-design/DESIGN.md
# § 7's artifact row names both skills as registrations and must be retargeted;
# DESIGN.md holds no `type: tone-of-voice` literal, so it carries no carve-out
```

**The removals.**

```bash
ls -d packs/experience-design/.apm/skills/{copy-direction,tone-of-voice} 2>/dev/null | wc -l   # want 0
python3 -c "import tomllib;print(len(tomllib.load(open('packs/experience-design/pack.toml','rb'))['pack']['evals']['skills']))"   # want 12
```

**The merged description clears a hard gate.** `skill_spec_lint.py` raises an
error above 1024, not a warning, and the three sources total 2,273 characters:

```bash
python3 - "$CD/SKILL.md" <<'PY'
import re, sys
fm = re.match(r'---\n(.*?)\n---\n', open(sys.argv[1]).read(), re.S).group(1)
print(len(re.search(r'^description:\s*"?(.*?)"?\s*$', fm, re.M | re.S).group(1)))
PY
# want <= 1024; sources are 769 + 732 + 772 = 2273
```

**No removed name survives inside the surviving skill itself.** Five lines of
`content-design/SKILL.md` and one of `references/communication-modes.md` name
them today:

```bash
grep -nE "$REMOVED" "$CD/SKILL.md" "$CD/references/communication-modes.md"   # want no output
```

**Skill counts — negative and positive, cardinal and ordinal:**

```bash
grep -rnoE '\b(14|fourteen|fifteenth)\b' \
  packs/experience-design/docs/index.md \
  guides/experience-design/reference/experience-design.md \
  web/src/content/packs/experience-design.md          # want no output after the fold
grep -q '12 skills' packs/experience-design/docs/index.md
grep -q '12 pure-Markdown skills' guides/experience-design/reference/experience-design.md
grep -q 'thirteenth skill' web/src/content/packs/experience-design.md
```

**The sibling brief's rows are restated, not merely absent.** An absence check
cannot distinguish a full restatement from a deletion:

```bash
B=docs/product/briefs/digital-experience-doctrine-completion.md
grep -q '31 files' "$B" && echo "stale headline still present"      # want silence
grep -q 'eight duplicate-basename families' "$B" && echo "stale family count"
grep -q 'five duplicate-basename families' "$B"                     # the new count
grep -qE 'editorial gates 2/1' "$B"
grep -qE 'interrogation 2' "$B"
```

**Versions — pack-scoped and labelled.** `grep -h version` is unusable: it strips
filenames, matches the adapter-contract stanza, and matches the substring inside
`conversion-design`:

```bash
for m in packs/experience-design packs/product-engineering; do
  printf '%-34s %s\n' "$m" "$(python3 -c "import tomllib;print(tomllib.load(open('$m/pack.toml','rb'))['pack']['version'])")"
done                                    # want 4.0.0 and 0.13.18; reads 2.0.9 and 0.13.17
grep -q '\"version\": \"4.0.0\"' packs/experience-design/.claude-plugin/plugin.json
grep -q '\"version\": \"0.13.18\"' packs/product-engineering/.claude-plugin/plugin.json
grep -rlE "$REMOVED" packs/frontend-engineering/ ; echo "want empty — that pack takes no bump"
```

**Suites and gates.** The selector includes the census suite, which a narrower
`-k "experience or content_design"` deselects:

```bash
python3 -m pytest tests/roster -q -k "experience or content_design or census or handoff"
python3 -m pytest packs/agent-skill-engineering/tests -q
python3 tools/lint-experience-agnostic.py
python3 packs/core/.apm/skills/work-loop/scripts/lint-spec-status.py --root .
agentbundle catalogue lint --root . --deep
agentbundle catalogue verify --root .
make lint-ruff lint-mypy
```

**Guides — spelled out with arguments**, because `lint-guidebook-steps.py` aborts
without a pack:

```bash
python3 tools/validate_guides.py
python3 tools/check-guide-index.py
python3 tools/lint-guide-titles.py
python3 tools/lint-guidebook-steps.py guides/experience-design
python3 tools/build-site.py
```

**The Astro content** the docs-site build never reads:

```bash
cd web && npm run build
```

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Activation baseline + abort path | `notes/activation-baseline.md` | T1, T9 |
| Reconciliation record | `notes/reference-reconciliation.md` | T3, T4 |
| Merged skill | `CD/` | T5 |
| Two directories removed | `packs/experience-design/.apm/skills/` | T6 |
| Reviewer + cross-pack | `.apm/agents/experience-reviewer.md`, `packs/product-engineering/**` | T7 |
| Two errata | RFC-0062, RFC-0071 | T8 |
| Sibling brief rows | `docs/product/briefs/digital-experience-doctrine-completion.md` | T7 |
| Versions + changelog | manifests, changelog | T10 |
| Manual-QA verdicts | `notes/verification-ledger.md` | T11 |

## Design (LLD)

### Design decisions

**Three modes, three artifacts.** The brief settles this twice. Merging the
outputs would change `frontend-engineering`'s handoff read and the reviewer's
marketing-clarity lens, and belongs to a different spec.

**The merged JTBD file is `copy-jtbd.md`.** `creative-direction` holds a third
`audience-jtbd.md`, pinned by the standalone slice as reachable from `frame`.
Reusing that basename opens a new two-copy family instead of closing one.

**One shared file keeps two copies, held by a test.** `editorial-quality-gates.md`
is needed by both the surviving copy skill and `information-architecture`. The
pack's own precedent for a shared file is duplication plus byte-equality — five
`containment.md` copies, one hash, no drift — and that precedent derives its copy
set from **citation**, so both `SKILL.md` files must cite it or the suite fails on
an uncited copy.

**Scope-borne divergence gets a scope parameter, not a winner.** Where two
variants restate the same rule for different scopes, letting one win deletes the
other mode's scope. The rewrite names the scope once and parameterises it.

### Failure, edge cases & resilience

- Genre fold aborted or landed without the relocation → T2 fails and the slice
  stops; it does not create the shared file itself.
- Activation gate fails → nothing in this slice ships; there is no separable
  repair, unlike the genre fold.
- A reconciliation cannot be classified → the verdict is recorded as unresolved
  and the pair escalates rather than being merged on a guess.

## Tasks

### T1: The pre-fold activation baseline exists

**Depends on:** none

**Tests:**
- Command, date, CLI version and model recorded; three runs per side, lowest
  reported; the statistic is total passing over total, pooled.
- Positive and negative pooled sets both recorded, the negatives including one
  `ux-writing` and one `creative-direction` query.
- The abort path is stated as a **revert, not a prevention**: T6 deletes the
  directories and T9 measures afterwards, so the fold must happen before it can
  be measured. The revert set is T3–T8, plus T10's manifest and changelog edits
  when the window-elapsed trigger fires after T10 has run.
- It names both triggers, the no-partial-fold residue, and `eugenelim`.

**Done when:** the file carries both sets and the abort path.

**Touches:** docs/specs/xd-copy-router/notes/activation-baseline.md

### T2: The genre fold's post-condition is verified, not assumed

**Depends on:** `spec:xd-genre-router/T3` — the cross-spec marker, so
`loop-cohort schedule` can see the sequencing. `none` hid it.

**Tests:**
- `information-architecture/references/editorial-quality-gates.md` exists and is
  byte-identical to the `conversion-design` original **at the merge-base**, not
  at `HEAD`: by the time this slice runs the genre fold has deleted that
  directory, so a `git show HEAD:` comparison fails with "path does not exist"
  and reads as "bytes differ".
- `information-architecture/SKILL.md` cites it.

**Approach:** a precondition gate, run before any reconciliation. If either fails
the slice stops and the genre fold is amended — this slice does not create the
file, because a second author of a shared file is how the drift started.

**Done when:** both checks pass. A task that is "done" on either branch is not a
gate; a failure stops the slice and is recorded, but that is the failure path,
not completion.

**Touches:** docs/specs/xd-copy-router/notes/verification-ledger.md

### T3: The pervasive divergences are rewritten, not merged

**Depends on:** T1, T2

**Tests:**
- Each pair classified pervasive or localized, with the verdict recorded.
- No reconciled file is the concatenation of both variants (manual QA).
- For each scope-borne pervasive file, one body with one named scope parameter;
  no variant deleted outright.
- `copy-arbitration.md` is handled by this rule and the record says so.

**Approach:** the classification is the decision, so it is recorded per file
before the rewrite rather than inferred from the result. `copy-arbitration.md`
diverges on every paragraph and carries an extra section on one side; it is the
case the rule exists for.

**Done when:** every pervasive pair has a scope-parameterised body and a recorded
verdict.

**Touches:** packs/experience-design/.apm/skills/content-design/references/, packs/experience-design/.apm/skills/information-architecture/references/editorial-quality-gates.md, docs/specs/xd-copy-router/notes/reference-reconciliation.md

### T4: The localized divergences and the two-name pair are reconciled

**Depends on:** T3

**Tests:**
- Per-mode differences are named clauses inside one file.
- The JTBD pair merges into `copy-jtbd.md`; the reconciliation note enumerates
  **every** substantive difference, not a subset, and classifies each.
- The brand-naming convention is decided and recorded; both `SKILL.md` bodies are
  in the evidence set.
- No rule present in either variant is silently dropped (manual QA).

**Done when:** all six reconciliations are recorded with a winner, a clause, or a
recorded drop with its reason.

**Touches:** packs/experience-design/.apm/skills/content-design/references/, docs/specs/xd-copy-router/notes/reference-reconciliation.md

### T5: One skill carries three modes and every output contract

**Depends on:** T3, T4

**Tests:**
- Three modes named literally; a mode-selection rubric decidable without loading
  a reference.
- All three output paths and `type:` values unchanged; the brand register emits
  `type: tone-of-voice` **and** `scope: brand-level`.
- The `brand-register` slug refusal survives (manual QA, ledger).
- The three legacy-1.x migration prompts and the three `type:`-collision branches
  survive.
- `content-design/SKILL.md` cites `references/editorial-quality-gates.md`.
- Neither removed name survives inside the surviving skill: five lines of
  `content-design/SKILL.md` and one of `references/communication-modes.md` name
  them today, and this is the task that edits both.

**Done when:** every mechanical test passes and `lint-experience-agnostic` exits 0.

**Touches:** packs/experience-design/.apm/skills/content-design/**

### T6: The two registrations are gone

**Depends on:** T5

**Tests:**
- Both directories absent; `pack.evals.skills` lists twelve; no alias or stub.
- No removed name survives **as a registration**; every surviving hit is a
  discriminator use on the protected list.

**Done when:** the directory count is zero and the registration grep is empty.

**Approach:** the two deleted directories carry `evals/evals.json` and an
`evals/files/` fixture directory that `content-design/evals/` does not have. This
task states their disposition — merged into the surviving harness or recorded as
intentionally dropped — rather than deleting them silently with the directory.

**Touches:** packs/experience-design/.apm/skills/, packs/experience-design/pack.toml

### T7: Reviewer, cross-pack and sibling-brief surfaces are consistent

**Depends on:** T6

**Tests:**
- `experience-reviewer.md`'s sync citation resolves; its `Does NOT fire on` list
  names surviving skills or artifact types.
- `xd-state-reviewer-doctrine.md` is updated or recorded confirmed unaffected.
- `ux-writing/SKILL.md`'s `tone-of-voice step 6` pointer is retargeted while its
  four discriminator literals stay; `product-engineering/DESIGN.md` updated.
- `digital-experience-doctrine-completion.md`'s re-check and Adjacent-work rows
  carry the **full** post-fold row — every sub-count, new file/hash totals, and
  eight families becoming five.
- `DESIGN.md` §4 rewritten as mode selection; no removed slug pack-wide.
- Astro build exits 0; census fixture matches.

**Done when:** the sibling row reads post-fold and the site builds.

**Touches:** packs/experience-design/**, packs/product-engineering/**, docs/product/briefs/digital-experience-doctrine-completion.md, docs/product/intents/xd-state-reviewer-doctrine.md, web/src/content/**

### T7a: The guide tree and the three registry surfaces are consistent

**Depends on:** T6

**Tests:**
- `guides/experience-design/how-to/copy-boundary.md` describes mode selection
  within one skill.
- `guides/experience-design/reference/experience-design.md`'s skill count reads
  the post-fold value; it reads "20 pure-Markdown skills" today.
- `workspace.toml` carries no removed skill name.
- `packs/agent-skill-engineering/tests/fixtures/skill-census.json` matches, and
  `tests/roster/test_skill_census.py` passes.
- `tools/add-rendering-directives.py`'s per-skill map carries neither removed
  name.

**Approach:** split out because T7's `Touches:` covered neither `tools/`, nor
`packs/agent-skill-engineering/**`, nor the repo-root `workspace.toml`, while
three acceptance criteria name them.

**Done when:** the census suite passes and the guide count is correct.

**Touches:** guides/experience-design/**, workspace.toml, tools/add-rendering-directives.py, packs/agent-skill-engineering/tests/fixtures/skill-census.json

### T8: RFC-0062 and RFC-0071 record what no longer holds

**Depends on:** T6

**Tests:**
- RFC-0062: a dated, approver-signed entry recording three registrations becoming
  one, all three output contracts unchanged, and the 2026-08-02 reservation
  surviving.
- RFC-0071: its own entry, including the skill-count correction.
- Neither **new** entry names a spec or a brief; RFC-0062's frozen 2026-08-02
  entry keeps its spec path and moves to `### History` unchanged.
- Both sections in RFC-0055 D2's two-layer form.

**Done when:** both entries exist in two-layer form and cite no delivery artifact.

**Touches:** docs/rfc/0062-content-design-and-copy-direction-skills.md, docs/rfc/0071-digital-experience-doctrine.md

### T9: The post-fold activation figure clears the gate

**Depends on:** T5, T6

**Tests:**
- Same command, CLI version and model as T1; positive and negative figures both
  ≥ baseline.

**Done when:** both clear. If either fails, nothing in this slice ships and
T3–T8 revert.

**Touches:** docs/specs/xd-copy-router/notes/activation-baseline.md

### T10: The release is registered

**Depends on:** T7, T8, T9

**Tests:**
- `experience-design` reads `4.0.0` in both manifests and the regenerated
  marketplace projection.
- `product-engineering` reads `0.13.18` in both.
- Two changelog entries; the `experience-design` one names both removed skills.
- Both catalogue commands exit 0.

**Done when:** every version surface agrees and catalogue passes.

**Touches:** packs/experience-design/pack.toml, packs/experience-design/.claude-plugin/plugin.json, packs/product-engineering/pack.toml, packs/product-engineering/.claude-plugin/plugin.json, .claude-plugin/marketplace.json, docs/product/changelog.md

### T11: Adopter hygiene and the four judgements are recorded

**Depends on:** T10

**Tests:**
- Observed `agentbundle` install/update behaviour for a removed directory
  recorded; the changelog states the manual step if stale directories persist.
- Four manual-QA verdicts recorded with reviewer and date.

**Done when:** the ledger carries the install observation and all four verdicts.

**Touches:** docs/specs/xd-copy-router/notes/verification-ledger.md, docs/product/changelog.md

## Rollout

Single PR, second major. Breaking for any adopter naming `copy-direction` or
`tone-of-voice` directly; the changelog names both. No shim by ADR-0038.

Artifacts are untouched: an existing `copy/<slug>.md` or `copy/brand-register.md`
keeps its path and `type:`, so no adopter content migrates. Rollback is
`git revert`.

## Risks

- **A reconciliation silently changes a rule.** The highest-consequence risk,
  because it is invisible to every mechanical check. Controlled by a per-file
  recorded verdict plus two manual-QA judgements.
- **The genre fold never lands the relocation.** T2 catches it as a precondition
  rather than letting T5 build on a missing file.
- **The sweep removes a discriminator.** `type: tone-of-voice` is both a skill
  name and an artifact marker; the carve-out list is the control, and it is
  enumerated rather than described.
- **The activation gate fails.** Nothing ships — no separable repair exists here.

## Changelog

<!-- Approvals only. Drafting history does not belong here. -->
