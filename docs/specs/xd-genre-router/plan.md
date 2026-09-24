# Plan: One genre-aware information-architecture skill

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `packs/AGENTS.md` (§ Version bump rule — removals are major; § Authoring or editing a skill); `packs/experience-design/DESIGN.md` §§ 5 and 10 (what the genre skills are and why they were separate); the existing genre routing table at `packs/experience-design/.apm/skills/information-architecture/SKILL.md:61-79`, which is the mechanism this delivery migrates rather than introduces; two analogous reference-bearing skills — `packs/frontend-engineering/.apm/skills/frontend-engineering/` (references loaded per mode) and `packs/experience-design/.apm/skills/design-review/` (five references, one shared cross-skill); their construction path is `tests/roster/test_experience_design_artifact_folder_registry.py`. Named uncertainty: no prior fold has been measured in this catalogue, so the activation comparison is the first of its kind and its statistic is authored here.

> **Plan contract:** this is the implementation strategy. It may change
> substantively only while its Status is `Drafting`. After approval, `spec.md`
> and `plan.md` are pinned in substance; execution observations belong in
> `notes/verification-ledger.md`.

## Approach

Seven registrations become one. The method does not change — six genre bodies
become six references under the skill that already routes to them — so the risk
is not authoring, it is sweep completeness and one measurement.

Order is forced twice. First, the **activation baseline runs before anything is
deleted** (T1): it is the gate, and a baseline taken after the fold measures
nothing. Second, the **references land before the directories go** (T3 before
T4), because a deleted directory takes its method with it.

The sweep is the bulk of the work and spans two packs plus the site content. It
is split by surface — pack internals (T5), cross-pack (T6), docs and site (T7) —
because each has a different completeness test and a different failure mode.

The riskiest single edit is the cross-pack routing table (T6). Its Load cell is
parsed verbatim as a skill name by a suite in the *other* pack, which no
`experience-design` gate runs, so T6 carries that pack's suite as its own test.

## Constraints

- `packs/AGENTS.md` § Version bump rule — removals are **major**;
  `experience-design` → `3.0.0`. Cross-pack content change is **patch**;
  `frontend-engineering` `0.3.2 → 0.3.3`.
- ADR-0038 — alias-free. No shim, no deprecation stub, so the sweep must be
  complete inside this PR.
- RFC-0066 D2 (seven-type taxonomy) and D5(d) (`transactional-journey` →
  `interaction-design`) are untouched.
- RFC-0055 D2 — the errata section converts to the two-layer form.
- An erratum names no spec and no brief.
- RFC-0033 / ADR-0024 — no values in pack content.

## Construction tests

Cross-cutting, after every wave:

```bash
python3 tools/lint-experience-agnostic.py
python3 -m pytest tests/roster -q -k "experience or handoff or census"
grep -rlE '(analytical|conversion|documentation|informational|marketplace|workspace)-design' \
  packs/ guides/ web/ tools/ tests/ | grep -vE '\.apm/skills/[a-z]+-design/'
```

The completeness grep runs here, not only at closeout: without it a half-swept
tree passes every wave gate. The selector covers the handoff and census suites,
which a bare `-k experience` deselects.

## Verification command map

**Commands are fenced blocks, never table cells.** A shell pipe inside a
markdown table must be escaped as `\|`, and `\|` is not a pipe — a sweep written
that way matches nothing and exits 0, reporting success while checking nothing.
Every block below was executed against the pre-fold tree on 2026-09-24 and its
present-state output recorded, so a reviewer can tell a broken command from a
failing check.

Set the roots once:

```bash
IA=packs/experience-design/.apm/skills/information-architecture
FE=packs/frontend-engineering/.apm/skills/frontend-engineering
GENRES='(analytical|conversion|documentation|informational|marketplace|workspace)-design'
```

**Routing — all seven genres reach exactly one destination.** Counts *distinct*
genres, and tolerates the table's three-space indentation inside numbered step 1:

```bash
grep -oE '\| *`(marketing|documentation|informational|analytical|marketplace|workspace|transactional-journey)` *\|' "$IA/SKILL.md" \
  | grep -oE '`[a-z-]+`' | tr -d '`' | sort -u | wc -l     # want 7; reads 7 today
grep -qE '^ *\| *`transactional-journey` *\| *`interaction-design`' "$IA/SKILL.md"  # D5(d) row survives
```

**The six genre references exist, by exact filename.** A brace glob aborts in zsh
on the first non-match, so five-of-six reports the same `0` as none-of-six:

```bash
for r in analytical conversion documentation informational marketplace workspace; do
  test -f "$IA/references/$r-design.md" || echo "MISSING $r-design.md"
done                                                        # want no output
```

**The relocated shared file.** Pinned to the merge-base, not `HEAD`: once T4's
deletion is in `HEAD` a `git show HEAD:` comparison fails with "path does not
exist", which reads as "bytes differ":

```bash
BASE=$(git merge-base HEAD origin/main)
cmp "$IA/references/editorial-quality-gates.md" \
    <(git show "$BASE:packs/experience-design/.apm/skills/conversion-design/references/editorial-quality-gates.md")
grep -q 'references/editorial-quality-gates.md' "$IA/SKILL.md"   # the citation the copy set requires
```

**Authored body ≤ 8,000 bytes.** The strip set is derived from the tool's own
directive table rather than hand-copied — the tool defines nine kinds and an
earlier draft listed five:

```bash
python3 - "$IA/SKILL.md" tools/add-rendering-directives.py <<'PY'
import re, sys
skill, tool = open(sys.argv[1]).read(), open(sys.argv[2]).read()
fm = re.match(r'---\n.*?\n---\n', skill, re.S)
blk = re.search(r'<!-- agentbundle:output-rendering:start -->.*?<!-- agentbundle:output-rendering:end -->', skill, re.S)
if not fm or not blk:
    sys.exit("frontmatter or managed block missing")
body = skill.replace(fm.group(0), '', 1).replace(blk.group(0), '', 1)
leads = re.findall(r'^\s*"([a-z-]+)"\s*:\s*\(?\s*\n?\s*"([^"]{4,}?) — ', tool, re.M)
for _, lead in set(leads):
    body = re.sub(r'(?m)^' + re.escape(lead) + r' — .*\n', '', body)
print(len(body.encode()))
PY
# want <= 8000; reads 7194 today
```

**Description.** Reads the frontmatter block first — a greedy
`description: "(.*)"` with `re.S` swallows the file and reports five figures too
many:

```bash
python3 - "$IA/SKILL.md" <<'PY'
import re, sys
fm = re.match(r'---\n(.*?)\n---\n', open(sys.argv[1]).read(), re.S).group(1)
print(len(re.search(r'^description:\s*"?(.*?)"?\s*$', fm, re.M | re.S).group(1)))
PY
# want <= 1024; reads 762 today, and must absorb seven genres' vocabulary
# plus a `design-system` boundary clause that is absent today
# the boundaries must be in the DESCRIPTION, not merely somewhere in the file.
# A whole-file grep passes for `design-system` today because the string appears
# elsewhere in the body, while the description does not carry that boundary.
python3 - "$IA/SKILL.md" <<'EOF'
import re, sys
fm = re.match(r'---\n(.*?)\n---\n', open(sys.argv[1]).read(), re.S).group(1)
d = re.search(r'^description:\s*"?(.*?)"?\s*$', fm, re.M | re.S).group(1)
for b in ("interaction-design", "design-system", "design-review", "creative-direction"):
    if b not in d:
        print("BOUNDARY MISSING FROM DESCRIPTION:", b)
EOF
```

**The removals.**

```bash
ls -d packs/experience-design/.apm/skills/{analytical,conversion,documentation,informational,marketplace,workspace}-design 2>/dev/null | wc -l   # want 0
python3 -c "import tomllib;print(len(tomllib.load(open('packs/experience-design/pack.toml','rb'))['pack']['evals']['skills']))"                  # want 14; reads 20 today
```

**Sweep completeness.** Real alternation, not an ellipsis placeholder; excludes
the skills' own directories so it measures references rather than definitions:

```bash
grep -rlE "$GENRES" packs/ guides/ web/ tools/ tests/ \
  | grep -vE "\.apm/skills/$GENRES/"        # want no output; 24 files today
grep -rlE "$GENRES" docs/ | sort            # classify each: frozen, dated output, or open
```

**Skill counts — negative *and* positive.** An absence check alone passes on a
file that lost its numeral or gained a wrong one; the ordinal form on the web
page matches neither `14` nor `fourteen`:

```bash
grep -rnoE '\b(20|twenty|twenty-first)\b' \
  packs/experience-design/docs/index.md \
  guides/experience-design/reference/experience-design.md \
  web/src/content/packs/experience-design.md      # want no output; 4 hits today
grep -q '14 skills' packs/experience-design/docs/index.md
grep -q '14 pure-Markdown skills' guides/experience-design/reference/experience-design.md
grep -q 'fifteenth skill' web/src/content/packs/experience-design.md
```

**The frontend table, read by the suite's own parser** rather than a hand-rolled
approximation. Requires the test directory on `sys.path`:

```bash
python3 - <<'PY'
import importlib.util, sys
d = "packs/frontend-engineering/tests/skills/frontend-engineering"
sys.path.insert(0, d)
spec = importlib.util.spec_from_file_location("t", f"{d}/test_public_claims_match_shipped_behaviour.py")
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
rows = m.genre_routing_table(open("packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md").read())
print(len(rows), "rows"); [print(" ", r) for r in rows]
PY
# want 4 rows; every Load cell a bare slug; reads 7 today
```

**The four byte-pinned contract copies stay pinned.** A negative criterion with
no positive control cannot fail, and T6 edits the same pack:

```bash
find packs -name digital-experience-contract.md -exec md5 -q {} \; | sort -u | wc -l   # want 1
```

**Versions — pack-scoped and labelled.** `grep -h version` is unusable here: it
strips filenames, matches the adapter-contract stanza, and matches the substring
inside `conversion-design`:

```bash
for m in packs/experience-design packs/frontend-engineering; do
  printf '%-32s %s\n' "$m" "$(python3 -c "import tomllib;print(tomllib.load(open('$m/pack.toml','rb'))['pack']['version'])")"
done                                        # want 3.0.0 and 0.3.3; reads 2.0.9 and 0.3.2
python3 -c "import json;print({p['name']:p['version'] for p in json.load(open('.claude-plugin/marketplace.json'))['plugins'] if p['name'] in ('experience-design','frontend-engineering')})"
grep -q '\"version\": \"3.0.0\"' packs/experience-design/.claude-plugin/plugin.json
grep -q '\"version\": \"0.3.3\"' packs/frontend-engineering/.claude-plugin/plugin.json
```

**Suites and gates.**

```bash
python3 -m pytest tests/roster -q -k "experience or handoff or census"
python3 -m pytest packs/frontend-engineering/tests -q          # 355 pass today
python3 -m pytest packs/agent-skill-engineering/tests -q       # 267 pass today
python3 tools/lint-experience-agnostic.py
python3 packs/core/.apm/skills/work-loop/scripts/lint-spec-status.py --root .
agentbundle catalogue lint --root . --deep
agentbundle catalogue verify --root .
make lint-ruff lint-mypy
```

**Guides — the five commands spelled out with their arguments.** The pointer form
is not runnable: `lint-guidebook-steps.py` aborts without a pack argument:

```bash
python3 tools/validate_guides.py
python3 tools/check-guide-index.py
python3 tools/lint-guide-titles.py
python3 tools/lint-guidebook-steps.py guides/experience-design
python3 tools/build-site.py
```

**The site content the Astro schema validates.** `tools/build-site.py` builds the
docs site and never reads `web/src/content/`, so it cannot catch a malformed
`skills:` frontmatter list:

```bash
cd web && npm run build
```

**Pooled activation queries.**

```bash
python3 -c "import json;q=json.load(open('$IA/evals/eval_queries.json'));print(sum(1 for x in q if x['should_trigger']), 'positive,', sum(1 for x in q if not x['should_trigger']), 'negative')"
# the positives pool all seven skills'; the negatives include one interaction-design and one design-system query
```

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Activation baseline | `notes/activation-baseline.md` | T1, T9 |
| Six genre references + relocated shared file | `IA/references/` | T3 |
| Rewritten rubric | `IA/SKILL.md` | T3 |
| Six directories removed | `packs/experience-design/.apm/skills/` | T4 |
| Pack internals swept | `pack.toml`, `DESIGN.md`, `JOURNEY.md`, `README.md`, `docs/index.md` | T5 |
| Cross-pack | `packs/frontend-engineering/**` | T6 |
| Docs, site, census | `docs/`, `web/src/content/`, census fixture | T7 |
| RFC-0066 erratum | `docs/rfc/0066-…md` § Errata | T8 |
| Versions + changelog | three manifests, changelog | T10 |
| Manual-QA verdicts | `notes/verification-ledger.md` | T11 |

## Design (LLD)

### Design decisions

**The surviving skill keeps the name `information-architecture`.** It already
holds the routing table, `frontend-engineering` and the guide tree already name
it, and ADR-0038 forbids aliases — so a rename multiplies a sweep that is already
the bulk of this work.

**Genre goes in the Surface-type cell, never the Load cell.** The frontend
suite's `genre_routing_table()` takes the Load cell verbatim as a routable skill
name. A cell reading `information-architecture <genre>` makes every README shape
fail its cross-check, so the argument travels in the human-readable column and
the Load cell stays a bare slug.

**Six references, not one parameterised file.** `DESIGN.md` §10 rejected a
`genre:` flag because it would bury genre logic in a conditional tree. A
per-genre file loaded on selection keeps each genre's logic first-class and
separately reviewable, which is the objection's substance rather than its letter.

**The relocated shared file is moved, not edited.** `editorial-quality-gates.md`
travels byte-identical, stale internal note included. Editing a file this slice
only relocates would make two authors of one shared file, which is how the pack's
drift started.

### Failure, edge cases & resilience

- Activation gate fails → abort path (T2 records it), six directories stay, the
  cross-pack repair ships alone at `0.3.3`.
- `claude` CLI unavailable → T1 cannot run and the fold stalls at its gate rather
  than proceeding unmeasured.
- A genre reference is shorter than its source skill's method section → manual-QA
  judgement 1 fails and T3 reopens.

## Tasks

### T1: The pre-fold activation baseline exists and is reproducible

**Depends on:** none

**Tests:**
- `notes/activation-baseline.md` records the command, date, CLI version and model
  identifier.
- Three runs recorded per side; the reported figure is the lowest.
- The statistic is total passing queries over total queries, over the pooled set.
- Both a positive and a negative pooled set are recorded.

**Approach:** first, and before any edit. A baseline taken after the fold
measures the thing it is supposed to be the control for. It also fixes the
pre-fold resident-description figure at this branch point rather than inheriting
the `2.0.9` number, which predates the sibling slice.

**Done when:** the file records both sets, three runs each, with the environment
named.

**Touches:** docs/specs/xd-genre-router/notes/activation-baseline.md

### T2: The abort path is written down before it can be needed

**Depends on:** T1

**Tests:**
- `notes/activation-baseline.md` names both triggers — failing gate, or the
  window from `Approved` elapsing.
- It names the residue: six directories stay, cross-pack repair ships alone.
- It names `eugenelim` as deciding owner.

**Done when:** all three are present.

**Touches:** docs/specs/xd-genre-router/notes/activation-baseline.md

### T3: One skill routes seven genres, with every method preserved

**Depends on:** T1

**Tests:**
- Rubric maps all seven genres; `transactional-journey → interaction-design`
  survives.
- Six genre references exist; each carries its source's method, grounding
  citations and scope boundaries (manual QA).
- `editorial-quality-gates.md` is byte-identical to the `conversion-design` copy
  and cited from `SKILL.md`.
- Authored body ≤ 8,000 B.
- Description ≤ 1024 chars, naming seven genres' trigger vocabulary and the four
  boundary skills — including the `design-system` boundary, which is absent from
  the description today.
- `evals/eval_queries.json` pools the seven skills' positives and carries the two
  named negatives. `packs/AGENTS.md` obliges an eval-harness update on any
  non-cosmetic pack change.

**Approach:** references land before the directories are removed, so no method is
deleted before its new home exists. The relocated shared file is copied with
`cp` and verified with `cmp` rather than retyped.

**Done when:** every mechanical test passes and `lint-experience-agnostic` exits 0.

**Touches:** packs/experience-design/.apm/skills/information-architecture/**

### T4: The six registrations are gone

**Depends on:** T3

**Tests:**
- Six directories absent.
- `pack.evals.skills` lists fourteen.
- No alias, shim or stub exists.

**Done when:** the directory count is zero and the evals list is fourteen.

**Touches:** packs/experience-design/.apm/skills/, packs/experience-design/pack.toml

### T5: The pack's own surfaces name only surviving skills

**Depends on:** T4

**Tests:**
- No removed name anywhere under `packs/experience-design/`.
- `DESIGN.md` names no removed slug **and** describes one genre-aware skill at
  lines 41, 61, 179, 249 and 187–198.
- `DESIGN.md` §10 carries the amended rationale entry with approver and date.
- Skill-count numerals read 14 in the three files that carry one.

**Done when:** the grep is empty and the five `DESIGN.md` locations describe the
new shape.

**Touches:** packs/experience-design/**

### T6: The frontend pre-flight routes every genre, and its own suite is green

**Depends on:** T4

**Tests:**
- The genre table is four rows; the collapsed row's Load cell is the bare slug.
- All six genres reachable; `transactional-journey` still reaches
  `interaction-design`.
- `design-system-foundations` corrected to `design-system` in the table, the
  README route list, and the cross-check test.
- The availability sentinel no longer probes a deleted skill.
- A `[[pack.dependencies.recommended]]` floor is declared.
- `python3 -m pytest packs/frontend-engineering/tests -q` passes.
- That pack's `evals/eval_queries.json` is updated, per the eval-harness
  obligation on any non-cosmetic pack change.
- `frontend-engineering` reads `0.3.3` in both manifests.

**Approach:** this pack's suite reads both the table and the README and is run by
no `experience-design` gate, so it is named here as a task test rather than left
to the cross-cutting sweep.

**Done when:** the frontend suite passes and all six genres are reachable.

**Touches:** packs/frontend-engineering/**

### T7: Docs, site and census tell the truth

**Depends on:** T4

**Tests:**
- Every **open** `docs/` record naming a removed skill is updated, starting with
  `docs/product/intents/skill-sequence-wayfinding.md`; frozen records and dated
  outputs are exempt and the classification is recorded.
- `docs/product/journeys/designer-designs-surface.md` describes the surviving set.
- `xd-ia-archetypes-objects.md`'s observed-state table is re-measured, re-dated,
  and its verdict corrected for the new reference structure.
- The Astro `skills:` frontmatter, `whatChanges` and stage prose are updated;
  `cd web && npm run build` exits 0.
- The census fixture matches.

**Done when:** the classification lands in
`docs/specs/xd-genre-router/notes/verification-ledger.md`, naming every `docs/`
file that matched and its class; the site builds; the census suite passes.

**Touches:** docs/**, web/src/content/**, packs/agent-skill-engineering/tests/fixtures/skill-census.json, docs/specs/xd-genre-router/notes/verification-ledger.md

### T7a: `tools/` and the guide tree name only surviving skills

**Depends on:** T4

**Tests:**
- `tools/add-rendering-directives.py`'s per-skill map carries none of the six
  removed names; it registers all six today at lines 224–235.
- The four `guides/experience-design/` files naming a removed skill are
  rewritten: `README.md`, `reference/experience-design.md`,
  `how-to/design-each-screen.md`, `explanation/the-experience-thread.md`.
- `guides/frontend-engineering/how-to/read-the-design-handoff.md` names the
  surviving routing target.
- The five guide commands each exit 0, `lint-guidebook-steps.py` with its pack
  argument.

**Approach:** split from T5 and T7 because neither owned these trees, while the
sweep-completeness grep covers both — a gap that would have surfaced only at
closeout.

**Done when:** the sweep grep returns no hit under `tools/` or `guides/`.

**Touches:** tools/add-rendering-directives.py, guides/experience-design/**, guides/frontend-engineering/**

### T8: RFC-0066 records what no longer holds

**Depends on:** T4

**Tests:**
- A dated, approver-signed entry names D4, the retirement, the preserved method,
  and that D2 and D5(d) are unchanged.
- It names no spec and no brief.
- The Errata section is in RFC-0055 D2's two-layer form.

**Done when:** the entry exists in two-layer form and cites no delivery artifact.

**Touches:** docs/rfc/0066-experience-pack-surface-genre-and-skill-uplift.md

### T9: The post-fold activation figure clears the gate

**Depends on:** T2, T3, T4 — T2 explicitly, so the abort path exists before the
trigger that invokes it can fire

**Tests:**
- Post-fold runs recorded under the same command, CLI version and model.
- Positive figure ≥ baseline; negative figure ≥ baseline.
- Post-fold resident description bytes recorded with the delta.

**Done when:** both figures clear and the delta is recorded.

On failure the abort path from T2 executes, and its revert set is **T3, T4, T5,
T7, T7a and T8** — note T3 is *in* and T6 is *out*. An earlier draft had this
backwards: it reverted T6, which is the cross-pack repair the residue promises
will ship alone, and preserved T3, which would leave six new genre references
under `information-architecture` and a rewritten rubric pointing at them while
the six source skills still exist. T6 survives the abort with its post-state
restated against the still-present genre skills.

**Touches:** docs/specs/xd-genre-router/notes/activation-baseline.md

### T10: The release is registered

**Depends on:** T5, T6, T7, T8, T9

**Tests:**
- `experience-design` reads `3.0.0` in both manifests and the marketplace
  projection, regenerated by `make build-self`.
- Two changelog entries — `experience-design` `3.0.0` naming the six removed
  skills, and `frontend-engineering` `0.3.3`.
- Both catalogue commands exit 0.

**Done when:** every version surface agrees and catalogue passes.

**Touches:** packs/experience-design/pack.toml, packs/experience-design/.claude-plugin/plugin.json, packs/frontend-engineering/pack.toml, packs/frontend-engineering/.claude-plugin/plugin.json, .claude-plugin/marketplace.json, docs/product/changelog.md

### T11: Adopter hygiene and the three judgements are recorded

**Depends on:** T10

**Tests:**
- The ledger records observed `agentbundle` install/update behaviour against a
  fixture install carrying the six skills.
- If stale directories are not pruned, the changelog states the manual step.
- Three manual-QA verdicts recorded with reviewer and date.

**Done when:** the ledger carries the install observation and all three verdicts.

**Touches:** docs/specs/xd-genre-router/notes/verification-ledger.md, docs/product/changelog.md

## Rollout

Single PR, major bump. Breaking for any adopter naming a removed skill directly;
the changelog names all six so a changelog-only reader learns which disappeared.

No shim by ADR-0038, so there is no deprecation window — the names stop resolving
at upgrade. Rollback is `git revert` of the PR: nothing outside the repository
holds state, and the removed directories return with their content.

## Risks

- **The activation gate fails.** Most likely risk and the one the whole T1/T2/T9
  structure exists for. Cost is the fold, not the slice: the cross-pack repair
  still ships.
- **The sweep misses an open `docs/` record.** No alias means a miss is a broken
  reference. T7's classification step is the control; the risk is that a record
  is misclassified frozen when it is open.
- **The frontend suite reds late.** T6 runs it as a task test precisely because no
  `experience-design` gate does.
- **RFC-0071 is wrong on the skill count between slices.** Accepted knowingly; if
  the sibling fold aborts, this slice's owner files the count erratum.

## Changelog

<!-- Approvals only. Drafting history does not belong here. -->
