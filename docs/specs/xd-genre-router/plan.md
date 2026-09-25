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

Cross-cutting, after every wave. The sweep is `sweep()` as defined once under
**Verification command map** below — never re-typed, because both earlier
re-typings were wrong in the same direction:

```bash
python3 tools/lint-experience-agnostic.py
python3 -m pytest tests/roster -q -k "experience or handoff or census"
sweep                                   # want no output
```

The completeness grep runs here, not only at closeout: without it a half-swept
tree passes every wave gate. **It binds on the fold branch only.** On the abort
branch the removed-name sweep is not owed, the 21 hits are all correct, and T9b
asserts the pre-fold figures instead — so an operator seeing 21 hits after a
failed gate is looking at a correct residue, not a miss. The selector covers the handoff and census suites,
which a bare `-k experience` deselects.

Two exclusions have to be exactly right, and a draft of this plan got both
wrong. Excluding `\.apm/skills/[a-z]+-design/` matches **every** `*-design`
skill directory, not the six being removed, and so hides three surviving files
that name removed skills today — `content-design/SKILL.md`,
`content-design/references/communication-modes.md`, and
`interaction-design/references/pattern-families.md`. Measured on the pre-fold
tree: the weak form returns **21** files and `sweep_raw` **23**. The canonical
form must additionally exclude `.apm/skills/information-architecture/`, because
after T3 the six surviving references are *named* `<genre>-design.md` and
`SKILL.md` cites them — so a sweep without that carve-out prints seven files on
a perfectly folded tree and reads as failure. That exclusion is why 23 and not
24: `information-architecture/SKILL.md` is a pre-fold hit `sweep_raw` drops. It
is not thereby unchecked — the routing block above reads both of its cells
directly, and the six new references get their own narrower grep.

Three figures are in play and two of them are 21, which is a coincidence worth
naming so nobody reads it as agreement. **Weak form: 21** — wrong, because its
`[a-z]+-design/` exclusion hides three files in surviving skills while keeping
`information-architecture/SKILL.md`. **`sweep_raw`: 23** — every real pre-fold
hit. **`sweep`: 21** — `sweep_raw` minus the two documented exemptions, and the
only one of the three that can reach zero on a correctly folded tree. The two
21s are not the same 21: measured, they share **18** files and differ by three
on each side. Equal totals here are a coincidence, not corroboration.

## Verification command map

**Commands are fenced blocks, never table cells.** A shell pipe inside a
markdown table must be escaped as `\|`, and `\|` is not a pipe — a sweep written
that way matches nothing and exits 0, reporting success while checking nothing.
Every block below that carries a `reads … today` comment was executed against
the pre-fold tree on 2026-09-24 and its present-state output recorded, so a
reviewer can tell a broken command from a failing check. Three blocks carry no
recorded present state and the claim does not extend to them. The rule, rather
than a list that goes stale: **a block asserting a post-change state that does
not exist on the pre-fold tree carries no `reads … today` figure, because there
is nothing to read.** That covers the `cmp` of the relocated shared file, the
description-boundary check, the six-reference existence loop (six `MISSING`
lines today), the method-carry floor (its `new=` column unreadable today), and
the pooled-query assertions. The Astro build is a separate case: it does **not
run on a fresh checkout at all** — see its block.

Set the roots once:

```bash
IA=packs/experience-design/.apm/skills/information-architecture
FE=packs/frontend-engineering/.apm/skills/frontend-engineering
GENRES='(analytical|conversion|documentation|informational|marketplace|workspace)-design'

# The canonical sweep. Every call site uses this function; none re-types it.
# Exclusion 1: the six removed skills' own directories (pre-fold definitions).
# Exclusion 2: the surviving skill, whose six references are named after the
#   genres by contract and whose SKILL.md cites them by name.
# Exclusion 3: the two documented exemptions the spec names. Without them the
#   expression can never return empty, and every wave gate hands the reviewer a
#   non-empty result to adjudicate by eye — the judgement substitution the
#   measured framing exists to prevent. `sweep_raw` keeps the unfiltered view so
#   an exemption can be re-checked rather than taken on trust.
EXEMPT='tools/lint-guidebook-steps\.py|skills/tone-of-voice/references/editorial-quality-gates\.md'
sweep_raw() {
  grep -rlE "$GENRES" packs/ guides/ web/ tools/ tests/ \
    | grep -vE "\.apm/skills/($GENRES|information-architecture)/"
}
sweep() { sweep_raw | grep -vE "$EXEMPT"; }
```

**Routing — all seven genres reach exactly one destination.** Counts *distinct*
genres, and tolerates the table's three-space indentation inside numbered step 1:

```bash
# Both cells, not only the key: a row with an empty or two-valued destination
# still contributes one distinct key, so counting keys alone cannot fail on it.
grep -oE '^ *\| *`(marketing|documentation|informational|analytical|marketplace|workspace|transactional-journey)` *\| *[^|]+\|' "$IA/SKILL.md" \
  | sed -E 's/^ *\| *`([a-z-]+)` *\| *(.*[^ ]) *\|$/\1 -> \2/' | sort -u
# want exactly 7 lines, one per genre, each with a non-empty single destination
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
sweep                                       # want no output post-fold; 21 pre-fold
sweep_raw | wc -l                           # 23 pre-fold (sweep + the 2 exemptions)

# Carve-out (a) excludes the surviving skill, so the new references are not
# swept. Read them directly. This must be done in Python, not as a grep pipe:
# `grep -n` over a multi-file glob prefixes every output line with the matching
# file's own path, so a `grep -v "references/<genre>-design.md"` filter drops
# *every* line rather than only self-references — a file containing exactly the
# failing sentence this check exists to catch prints "clean". Verified.
python3 - <<'QQ'
import pathlib, re, sys
GENRES = r"(analytical|conversion|documentation|informational|marketplace|workspace)-design"
refs = sorted(pathlib.Path("packs/experience-design/.apm/skills/information-architecture/references").glob("*.md"))
if len(refs) < 7:   # six genre references + editorial-quality-gates.md
    sys.exit(f"REFERENCE SET INCOMPLETE: {len(refs)} files — absence must fail, not read clean")
bad = []
for f in refs:
    for n, line in enumerate(f.read_text().splitlines(), 1):
        # Strip the legitimate forms first: this file's own slug in its own
        # name, and a citation path to a sibling reference.
        # Both citation forms are legitimate between siblings in one directory:
        # the `references/`-prefixed path and the bare filename.
        stripped = re.sub(rf"(references/)?{GENRES}\.md", "", line)
        # Strip only this file's own slug from a heading, not everything up to
        # the last genre match: a greedy `^#.*{GENRES}` would swallow
        # "# marketplace-design — bridges to conversion-design" whole.
        stripped = re.sub(rf"^(#+\s*){re.escape(f.stem)}", r"\1", stripped)
        for m in re.finditer(GENRES, stripped, re.I):
            if m.group(0) == f.stem:
                continue     # the file naming its own genre is expected
            bad.append(f"{f.name}:{n}: {line.strip()}")
if bad:
    sys.exit("GENRE REFERENCE NAMES A REMOVED SKILL:\n  " + "\n  ".join(bad))
print(f"{len(refs)} references clean")
QQ
grep -rlE "$GENRES" docs/ | sort            # classify each by the spec's class rule
```

The `docs/` hits are classified by the spec's **class** rule, not against a list
of filenames. On the pre-fold tree the classes resolve as: exempt-by-class —
the RFC-0066 erratum, `docs/product/changelog.md`, the delivery brief, the
in-flight `docs/specs/xd-copy-router/` and `docs/specs/xd-genre-router/` spec
and plan pairs, everything under `docs/design/`, and everything under
`docs/product/research/` (which covers both the consolidation analysis and
`aesthetic-style-survey.md`); frozen — by lifecycle class, per the spec; open —
everything else, each owed an edit. An earlier four-filename list had no
admissible class for four current hits.

**Skill counts — negative *and* positive.** An absence check alone passes on a
file that lost its numeral or gained a wrong one; the ordinal form on the web
page matches neither `14` nor `fourteen`:

```bash
# Re-derived, not enumerated. The earlier three-path list missed
# guides/experience-design/README.md, whose numeral carries no removed skill
# name and so is invisible to the sweep too — so the set is discovered by
# search over the trees that describe this pack, and the four known paths are
# the expected *result*, not the input.
# Matched on count-*shaped* phrases, not on a bare `20`. A bare-numeral sweep
# returns three "20 minutes" lines in unrelated skill bodies, and a check whose
# expected output includes known false positives stops being readable.
grep -rnoiE '(20|twenty)[- ]?(skills?|pure-Markdown|skill inventory)|Skills \(20\)|pack of 20|twenty-first skill' \
  packs/experience-design/ guides/experience-design/ \
  web/src/content/packs/experience-design.md --include='*.md'
# want no output post-fold. Today: 5 hits across 4 files —
#   packs/experience-design/docs/index.md:3   "pack of 20"
#   packs/experience-design/docs/index.md:11  "Skills (20)"
#   guides/experience-design/README.md:83     "20-skill inventory"
#   guides/experience-design/reference/experience-design.md:17 "20 pure-Markdown"
#   web/src/content/packs/experience-design.md:69 "twenty-first skill"
# A hit in a path outside those four means a fifth numeral landed and needs an
# owning task — which is what this expression exists to discover, since a
# numeral carries no removed skill name and `sweep` is blind to it.
grep -q '14 skills' packs/experience-design/docs/index.md          # covers index.md:3 only
grep -q 'Skills (14)' packs/experience-design/docs/index.md        # covers index.md:11, the second numeral
grep -q '14 pure-Markdown skills' guides/experience-design/reference/experience-design.md
grep -q 'fifteenth skill' web/src/content/packs/experience-design.md
grep -q '14-skill' guides/experience-design/README.md                 # covers README.md:83
```

`docs/index.md` carries **two** numerals — line 3 ("pack of 20 skills") and
line 11 ("**Skills (20) in two families:**"). One positive control reaches only
the first; the second is otherwise guarded solely by the negative `\b20\b`
grep, which passes on a file that lost its numeral entirely.

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

# Row count and bare slugs cannot see the gap this change exists to close. The
# parser returns (surface_type, skill_name) and the surface-type cells are
# prose, not `surface-genre:` tokens, so a correct-looking four-row table can
# still omit marketplace and workspace while every gate stays green.
python3 - <<'QQ'
import importlib.util, sys
d = "packs/frontend-engineering/tests/skills/frontend-engineering"
sys.path.insert(0, d)
sp = importlib.util.spec_from_file_location("t", f"{d}/test_public_claims_match_shipped_behaviour.py")
m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m)
rows = m.genre_routing_table(open("packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md").read())
collapsed = [st for st, k in rows if k == "information-architecture"]
assert len(collapsed) == 1, f"expected one collapsed row, got {len(collapsed)}"
missing = [g for g in ("marketing", "documentation", "informational",
                       "analytical", "marketplace", "workspace")
           if g not in collapsed[0].lower()]
assert not missing, f"collapsed row omits: {missing}"
assert any(k == "interaction-design" for _, k in rows), "no row loads interaction-design"
print("six genres enumerated; transactional-journey still routes to interaction-design")
QQ
```

**The four byte-pinned contract copies stay pinned.** A negative criterion with
no positive control cannot fail, and T6 edits the same pack:

```bash
# `md5` is macOS-only; on Linux it is absent, the pipeline hashes nothing, and
# `wc -l` prints 0 — loud rather than silent, but still not the check.
find packs -name digital-experience-contract.md -print0 \
  | xargs -0 shasum -a 256 | awk '{print $1}' | sort -u | wc -l   # want 1; reads 1 today
find packs -name digital-experience-contract.md | wc -l           # want 4; the positive control
```

**Versions — pack-scoped and labelled.** `grep -h version` is unusable here: it
strips filenames, matches the adapter-contract stanza, and matches the substring
inside `conversion-design`:

```bash
for m in packs/experience-design packs/frontend-engineering; do
  printf '%-32s %s\n' "$m" "$(python3 -c "import tomllib;print(tomllib.load(open('$m/pack.toml','rb'))['pack']['version'])")"
done                  # want 3.0.0 and 0.3.3; reads 2.0.10 and 0.3.2 on 2026-09-24
# 2.0.10, not 2.0.9: the sibling `creative-direction-modes` landed its bump in
# the working tree. Re-read this rather than trusting the figure — it is the one
# number in this map another in-flight slice moves.
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
cd web && npm ci && npm run build      # `npm ci` is not optional — see below
```

`web/node_modules` is absent on a fresh checkout. Without the install step the
block exits **127** with `sh: astro: command not found`, which is indistinguishable
at a glance from a schema rejection. Read the outcome as: exit 127 with
`astro: command not found` means *toolchain absent, criterion unsettled*; a
non-zero exit carrying a Zod or collection error means *schema rejected,
criterion failed*; exit 0 settles it. This is the only control on the `skills:`
frontmatter list, so an unsettled run is not a pass.

**Method-carry floor — the mechanical half of manual-QA judgement 1.** The
judgement ("each genre reference carries its source skill's method") is
uncomputable in substance, but its stated failure mode — a reference shorter
than the method it replaced — is arithmetic, and a human should not be spending
the judgement on detecting truncation:

```bash
git fetch origin main --quiet     # BASE is only as current as the local ref
BASE=$(git merge-base HEAD origin/main)
for r in analytical conversion documentation informational marketplace workspace; do
  if [ ! -f "$IA/references/$r-design.md" ]; then printf '%-16s MISSING\n' "$r"; continue; fi
  new=$(wc -c < "$IA/references/$r-design.md")
  old=$(git show "$BASE:packs/experience-design/.apm/skills/$r-design/SKILL.md" | wc -c)
  printf '%-16s new=%6d  old-SKILL=%6d\n' "$r" "$new" "$old"
done
# A reference materially smaller than its source skill's body is a truncation
# signal, not a verdict: de-duplication against the shared body legitimately
# shrinks it. The reviewer explains any shortfall in the ledger rather than
# discovering it by eye.
```

**Pooled activation queries.**

A bare tally cannot fail: the **unpooled** file reads `11 positive, 11 negative`
today and would satisfy any check that only prints a number. The expected counts
are stated, and the two named negatives are asserted by content rather than
counted:

```bash
python3 - <<'QQ'
import json, sys
q = json.load(open("packs/experience-design/.apm/skills/information-architecture/evals/eval_queries.json"))
pos = {x["query"].strip() for x in q if x["should_trigger"]}
neg = {x["query"].strip() for x in q if not x["should_trigger"]}
fail = []
# Counts are assertions, not prints: a block that only prints exits 0 on a file
# that pooled nothing, which is the failing state the criterion names.
if len(pos) != 71: fail.append(f"positives {len(pos)}, want 71")
if len(neg) != 67: fail.append(f"negatives {len(neg)}, want 67")
# Only an opposite-should_trigger collision is a defect. A string repeated on
# the same side is a benign cross-file duplicate the pooling rule dedupes.
clash = pos & neg
if clash: fail.append(f"contradictory queries kept on both sides: {sorted(clash)}")
# The two named negatives, by exact text. A keyword proxy cannot settle this:
# within the pooled 67, "interaction" matches exactly one string and "design
# system" exactly one, so a substring test proves only that some query contains
# a word — not that the boundary case the criterion names was pooled. Six of
# the 67 carry "token", which is why that word is not used at all.
# Verbatim strings that are already inside the 67, so the count assertion and
# the content assertion can hold at once. Taking them from `interaction-design`'s
# or `design-system`'s own eval files instead would add two queries the 67 does
# not contain and red the count — those two skills are not among the seven
# pooled here.
REQUIRED_NEGATIVES = [
    "Design the individual component interactions for the workspace toolbar",
    "Derive the token taxonomy for the marketplace design system",
]
for want in REQUIRED_NEGATIVES:
    if want not in neg: fail.append(f"required negative absent: {want!r}")
if fail:
    sys.exit("POOLED QUERY SET FAILED:\n  " + "\n  ".join(fail))
print(f"{len(pos)} positive, {len(neg)} negative, no contradictions, both named negatives present")
QQ
```

The figures, measured rather than derived by subtraction. The seven source
files hold 71 positive entries, all 71 distinct — so pooling keeps **71**
positives. They hold 71 negative entries but only **69 distinct**, because two
negative strings appear in two files each: `Design the landing page to convert
trial visitors` (`analytical-design` + `informational-design`) and `Design the
article page layout for our editorial blog` (`conversion-design` +
`documentation-design`). From those 69 the contradiction rule drops the two
strings that are positive elsewhere — `Design the article page layout for our
editorial blog` and `Design the workspace UI for our collaborative editing
tool` — leaving **67**. Note the first is both a cross-file duplicate and a
contradiction, which is why an entry-count and a string-count disagree; the
spec fixes the string count as the one that governs. An earlier draft said 69
by subtracting two from the negative entry tally, a figure no correct file
could reach.

## Durable-output map

Every row carries four cells. An earlier draft was column-shifted — the
destination landed in `Tasks`, the task IDs landed in `Implementation
evidence`, and `Closeout evidence` was empty for all ten rows, which is the one
column closeout actually reads.

| Durable output | Destination | Tasks | Closeout evidence |
| --- | --- | --- | --- |
| Activation baseline | `notes/activation-baseline.md` | T1, T2, T9 | Both runs recorded, three each, positive and negative figures clearing |
| Pooled trigger queries | `IA/evals/eval_queries.json` | T1, T3 | 71 positives / 67 negatives asserted, no opposite-trigger collision, both named negatives present by exact text, and the set identical to the one T1 graded |
| Six genre references + relocated shared file | `IA/references/` | T3 | Six files present; `cmp` clean on the relocated file; judgement 1 recorded |
| Rewritten rubric | `IA/SKILL.md` | T3 | Seven genres each reaching one destination; authored body ≤ 8,000 B; judgement 2 recorded |
| Six directories removed | `packs/experience-design/.apm/skills/` | T4 | Directory count 0; `pack.evals.skills` reads 14 |
| Pack internals swept | `pack.toml`, `DESIGN.md`, `JOURNEY.md`, `README.md`, `docs/index.md` | T5 | `sweep` empty under `packs/experience-design/`; six `DESIGN.md` locations restated; § 10 entry signed and dated |
| Cross-pack (fold branch) | `packs/frontend-engineering/**` | T6, T10a | Four-row table enumerating the six `surface-genre:` tokens; `AGENTS.md:11` repointed; `packs/frontend-engineering/tests` green; `0.3.3` in both manifests and the projection |
| Cross-pack (abort branch) | `packs/frontend-engineering/**` | T9a, T10a | **Nine**-row table with `marketplace-design` and `workspace-design` added; sentinel still probing `conversion-design`; `AGENTS.md:11` naming the six again; `recommended` reading `>=2.0.10`; same suite green; same `0.3.3` release surface |
| Fold work reverted (abort branch only) | `packs/experience-design/**`, `docs/**`, `web/src/content/**`, `tools/`, `guides/**`, census fixture | T9b | `sweep_raw` back to **20** and `sweep` to **18** — not the pre-fold 23/21, because T6 survives the abort; `pack.evals.skills` back to 20; every T3 output reverted including `evals/eval_queries.json` and the frontmatter `description`; roster suites green |
| Docs, site, census | `docs/`, `web/src/content/`, census fixture | T7 | Class record for every `docs/` hit in the ledger; `npm ci && npm run build` exit 0; census suite green |
| Guide tree and `tools/` | `guides/**`, `tools/add-rendering-directives.py` | T7a | `sweep` empty under `guides/` and `tools/`; five guide commands exit 0 |
| User promise — the guide a reader follows | `guides/experience-design/` | T7a | Guide-agreement suite green; judgement 3 recorded with reviewer and date |
| RFC-0066 erratum | `docs/rfc/0066-…md` § Errata | T8 | Two-layer section; new entry names D4 and no delivery artifact; prior entry verbatim |
| Versions + changelog (fold branch) | three manifests, changelog | T10, T10a | All three surfaces agree at `3.0.0`/`0.3.3`; both changelog entries free-standing; catalogue lint and verify exit 0 |
| Versions + changelog (abort branch) | `frontend-engineering` manifests, projection, changelog | T10a | `0.3.3` on all three `frontend-engineering` surfaces and its changelog entry; `experience-design` untouched at its pre-fold version, which is correct here rather than a miss |
| Manual-QA verdicts + adopter hygiene | `notes/verification-ledger.md` | T11 | Three verdicts with reviewer and date; install/update prune behaviour observed |

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
- The statistic is total passing queries over total queries, over the pooled
  set, with "passing" defined for the pre-fold world in the terms the spec
  states, so T9 reproduces it unchanged.
- Both a positive and a negative pooled set are recorded, and the two
  contradictory queries are resolved and the resolution written down.
- The pooled query set T1 grades is **written to the baseline note verbatim**,
  so T3's shipped `eval_queries.json` can be compared against it rather than
  merely resembling it. The gate's whole validity is "computed identically on
  both sides over the **same** pooled set", and T3 — which authors the shipped
  file — runs after T1. Without a comparison the two figures can be computed
  over different denominators and the ≥-baseline gate clears on an artefact.
  The command map's pooled-query block is run against both, and T9 does not
  report a figure until they match.
- The **pre-fold resident description cost is measured here** and recorded with
  its method, so T9's delta has a control. T1's Approach promised this and its
  test list omitted it; the 14,966-byte figure in the discovery note was taken
  at `2.0.9` — two bumps ago now that the sibling landed `2.0.10` — and carries
  no stated computation, so it cannot be inherited. The
  method is: sum the `description` field bytes across the pack's shipped
  `SKILL.md` frontmatter, using the description reader in the command map.

**Approach:** first, and before any edit. A baseline taken after the fold
measures the thing it is supposed to be the control for. It also fixes the
pre-fold resident-description figure at this branch point rather than inheriting
the `2.0.9` number, which predates the sibling slice (the tree reads `2.0.10`
as of 2026-09-24).

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

**Approach (recording):** manual-QA judgement 1 — whether each genre reference
carries its source's method — is recorded **here**, in
`notes/verification-ledger.md`, not at T11. The resilience note says a failed
judgement 1 reopens T3; scheduling it after T10 would mean unwinding the
deletions, the sweeps, the erratum and both version bumps to act on it. The
method-carry floor in the command map runs first so the reviewer spends the
judgement on substance rather than on spotting truncation.

**Done when:** every mechanical test passes, `lint-experience-agnostic` exits 0,
and judgement 1 is recorded with reviewer and date.

**Touches:** packs/experience-design/.apm/skills/information-architecture/**, docs/specs/xd-genre-router/notes/verification-ledger.md

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
- No removed name anywhere under `packs/experience-design/` — `sweep` is the
  completeness check on a stated edit, not the specification of it. **Four**
  files carry **ownership and grounding statements**, not slug mentions, and
  their post-state is named here so the grep is not satisfied by deletion:
  `journey-mapping/references/surface-genre-journeys.md` (lines 20, 36, 52, 69,
  103, 119) says "`<genre>-design` owns the surface design for this journey" six
  times and is repointed at `information-architecture` plus the genre;
  `interaction-design/references/pattern-families.md` (lines 78, 219) cites
  `marketplace-design`'s transaction bridge and `analytical-design`'s widget
  hierarchy as substantive cross-references and is repointed at the new
  reference paths; `content-design/SKILL.md` and
  `content-design/references/communication-modes.md` route to
  `conversion-design` and are repointed at the collapsed route. Deleting the
  slug in any of these loses the referent instead of moving it.
- `DESIGN.md` names no removed slug **and** describes one genre-aware skill at
  its **six** checked locations: lines 41, 61, 179, **185** (the section heading
  `### The genre-direct skills`, slugless and outside the 187–198 range), 249
  and 187–198.
- `DESIGN.md` §10 carries the amended rationale entry with approver and date.
- The sole-editor claim is settled by reading the sibling's criterion:
  `docs/specs/creative-direction-modes/spec.md` requires that delivery not to
  edit § 10. T5 records that citation rather than asserting a negative about
  edits it cannot observe.
- Skill-count numerals: within T5's scope exactly **one** file carries them —
  `packs/experience-design/docs/index.md`, with **two**, at lines 3 and 11. The
  other three numerals sit outside `packs/experience-design/` and belong to T7a
  (`guides/experience-design/reference/experience-design.md:17` and
  `guides/experience-design/README.md:83`) and T7
  (`web/src/content/packs/experience-design.md:69`). An earlier draft said
  "the three files that carry one" here, which was wrong twice: the count, and
  the assumption that T5 could reach them.

**Done when:** `sweep` is empty under `packs/experience-design/`, the four
stated-post-state files above read as stated, and all **six** `DESIGN.md`
locations — including the line-185 section heading — describe the new shape.

**Touches:** packs/experience-design/**

### T6: The frontend pre-flight routes every genre, and its own suite is green

**Depends on:** T2 — the **decision**, not the deletion. Nothing T6 edits reads
the six directories, so declaring `T4` put the one repair that is promised to
survive an abort downstream of the abort trigger. T6 authors the fold-branch
post-state; if T9 fails, T6 re-runs against the abort-branch post-state the
spec now states in full, which is why that post-state is a criterion rather
than a note.

**Tests:**
- The genre table is four rows; the collapsed row's Load cell is the bare slug.
- All six genres reachable; `transactional-journey` still reaches
  `interaction-design`.
- **Exactly one** row's Surface-type cell contains the substring `interaction`
  (case-insensitive). `test_the_example_genre_route_is_the_one_the_table_names`
  asserts that count and routes the notification-panel example to that row, so
  the collapsed row's prose must avoid the word even though none of its six
  tokens contains it.
- `design-system-foundations` corrected to `design-system` in the **two** live
  locations: `.apm/skills/frontend-engineering/SKILL.md:189` and the
  `readme_offered_genre_skills` docstring at
  `tests/skills/frontend-engineering/test_public_claims_match_shipped_behaviour.py:419`.
  **Not the README** — it carries no occurrence, and an earlier draft naming it
  as a third site would have sent an implementer to introduce the slug in order
  to correct it.
- The README's own obligation is separate and is about names, not the slug: its
  `(pick …)` route list drops the three removed genre names, keeps
  `interaction-design` (the worked example's route), and stays a parenthetical
  that splits into exactly three em-dash-delimited parts.
- The availability sentinel no longer probes a deleted skill.
- `packs/frontend-engineering/AGENTS.md:11` — "that supplies
  `conversion-design`, `documentation-design`, `analytical-design`, and the
  other XD genre skills" — names the surviving skill and the genre set instead.
  It is an **ownership statement**, so it is repointed, not deleted, by the same
  rule T5 applies to its own tree. It is neither the sentinel nor the named-skip
  text, so no other cross-pack test reaches it and only the cross-cutting sweep
  would have caught it — and the plan's own doctrine is that `sweep` is a
  completeness check on a stated edit, not the specification of one.
- A `[[pack.dependencies.recommended]]` floor is declared with all three fields
  `verify.py` requires — `catalogue = "agent-ready-repo"` (from
  `catalogue.toml:7`), `pack`, `version` — and a space-free range `>=3.0.0`.
  `catalogue` is the field that fails **silently**: `verify.py` skips an entry
  whose catalogue does not match, so a wrong value exits 0 and leaves a floor
  that resolves to nothing. Copy the shape from `packs/atlassian/pack.toml:20-23`,
  one of four `dependencies.required` entries already in the tree — only the
  `recommended` sub-key is new here. `parse_version_range` splits on whitespace, so `>= 3.0.0` becomes
  two atoms and reds `catalogue verify` with `CAT-V-007`; measured both ways
  against the repository's own parser.
- `python3 -m pytest packs/frontend-engineering/tests -q` passes.
- That pack's `evals/eval_queries.json` is updated, per the eval-harness
  obligation on any non-cosmetic pack change.
- The `0.3.3` bump is **T10a's** to assert and to gate; T6 does not restate it.
  Stating it in both left it in neither `Done when`.

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
- `xd-state-reviewer-doctrine.md` is **not** edited here. T7 confirms that
  `docs/specs/xd-copy-router/spec.md` carries a criterion naming that file, and
  records the confirmation in the ledger — the hand-off is this delivery's
  obligation, the update is the sibling's.
- The Astro `skills:` frontmatter, `whatChanges` and stage prose are updated;
  `cd web && npm ci && npm run build` exits 0.
- `web/src/content/packs/experience-design.md:69` reads "a fifteenth skill", not
  "a twenty-first".
- `web/src/content/packs/frontend-engineering.md` names the same routing target
  as the table — the **positive** half, which `sweep` cannot settle because it
  is a presence claim. T7 owns it because T7 holds `web/src/content/**`; an
  earlier draft assigned it to T6, whose `Touches` cannot reach the file. On the
  abort branch the routing target named is the pre-fold one.
- The numeral grep in the command map is run here, covering all five numerals
  across the four files, so one wave gate reads the whole set rather than each
  task checking only its own.
- The census fixture matches.

**Done when:** the classification lands in
`docs/specs/xd-genre-router/notes/verification-ledger.md`, naming every `docs/`
file that matched and its class; the site builds; the census suite passes.

**Touches:** docs/**, web/src/content/**, packs/agent-skill-engineering/tests/fixtures/skill-census.json, docs/specs/xd-genre-router/notes/verification-ledger.md

### T7a: `tools/` and the guide tree name only surviving skills

**Depends on:** T4

**Tests:**
- `tools/add-rendering-directives.py`'s per-skill map carries none of the six
  removed **keys** — `analytical-design`, `conversion-design`,
  `documentation-design`, `marketplace-design`, `workspace-design` and
  `informational-design`. Named as keys, not as a line span: the six are not
  contiguous (five sit at 224–228, `informational-design` at 235), and the
  224–235 span also contains `information-architecture`, `design-review`,
  `devils-advocate` and `design-principles`. Deleting the stated range would
  strip the surviving skill's own directives plus three unrelated ones, and the
  authored-body command cannot see it because it strips directive lines before
  counting.
- `information-architecture`'s entry reads `["table", "narrative"]` — the union
  of the seven folded entries. It reads `["table"]` today while
  `informational-design` reads `["table", "narrative"]`, so a key-deletion-only
  edit ships the informational genre's method without the narrative directive
  it depends on. No gate reads this map.
- `tools/lint-guidebook-steps.py:406` is the **second** `tools/` file the sweep
  returns. Its hit is an explanatory comment — `# "analytical-design SKILL.md",
  which names a file without locating it.` — naming a file without referencing
  the skill. It is a **documented exemption**, recorded in the ledger, not an
  edit: rewriting an unrelated tool's comment to silence a completeness check is
  the failure this entry prevents.
- The four `guides/experience-design/` files naming a removed skill are
  rewritten: `README.md`, `reference/experience-design.md`,
  `how-to/design-each-screen.md`, `explanation/the-experience-thread.md`.
- The two guide-tree numerals read 14:
  `guides/experience-design/reference/experience-design.md:17` and
  `guides/experience-design/README.md:83` ("the complete 20-skill inventory" →
  14). Neither `sweep` nor any wave gate can see a numeral — it carries no
  removed skill name — so without this test they ship stale, which is the miss
  that already happened once to `README.md:83`.
- `guides/frontend-engineering/how-to/read-the-design-handoff.md` is **not
  edited**. It carries no routing target and no genre-skill name today (grep:
  zero occurrences of any genre skill, `information-architecture`,
  `experience-design`, or the word "genre"). T7a records that confirmation in
  the ledger. Writing a routing target into it would fail the spec criterion by
  construction — an earlier draft of this task ordered exactly that.
- The five guide commands each exit 0, `lint-guidebook-steps.py` with its pack
  argument.

**Approach:** split from T5 and T7 because neither owned these trees, while the
sweep-completeness grep covers both — a gap that would have surfaced only at
closeout.

**Done when:** `sweep` returns no hit under `guides/` or `tools/` — it filters
the exemption by construction — `sweep_raw`'s only remaining `tools/` hit is
`lint-guidebook-steps.py` with the exemption's reason recorded in the ledger,
the two guide-tree numerals read 14, and the
`read-the-design-handoff.md` zero-occurrence confirmation is in the ledger. That
last one appeared only in T11's *abort*-branch condition, so on the fold branch
the one criterion whose whole obligation is a ledger line was gated by nothing.

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
- The shipped `$IA/evals/eval_queries.json` is **the same query set T1 graded**,
  compared against the verbatim copy T1 wrote into the baseline note. This is
  T9's test, not only T1's prose: a T9 implementer reading T9 alone would
  otherwise compute post-fold over T3's file and pre-fold over T1's, and the
  ≥-baseline gate would clear on two different denominators.
- Post-fold runs recorded under the same command, CLI version and model.
- Positive figure ≥ baseline; negative figure ≥ baseline.
- Post-fold resident description bytes recorded with the delta.

**Done when:** both figures clear and the delta is recorded.

On failure the abort path from T2 executes. Its revert set is **T3, T4, T5, T7,
T7a and T8** — note T3 is *in*, and T6 and T10a are *out* — and **T9b owns
executing it**, with its own tests and completion condition. Stating the set
here without an owning task left the largest piece of abort-branch work
unassigned. An earlier draft had this
backwards: it reverted T6, which is the cross-pack repair the residue promises
will ship alone, and preserved T3, which would leave six new genre references
under `information-architecture` and a rewritten rubric pointing at them while
the six source skills still exist. T6 survives the abort with its post-state
restated against the still-present genre skills.

**Touches:** docs/specs/xd-genre-router/notes/activation-baseline.md

### T9b: The fold-branch work is reverted (runs only if T9 fails)

**Depends on:** T9 failing

**Tests:**
- **All four T3 outputs** are reverted, enumerated rather than gestured at:
  (1) the six genre references and the relocated `editorial-quality-gates.md`
  are gone from `$IA/references/`; (2) the pre-fold rubric is restored in
  `$IA/SKILL.md`; (3) `$IA/evals/eval_queries.json` is back to its 11/11
  pre-fold form; and (4) the frontmatter `description` is back to its pre-fold
  762 characters. Outputs 3 and 4 were previously unnamed, and no roster suite
  reads either — so a revert that stopped at the references would ship six
  restored genre skills beside an `information-architecture` whose description
  is tuned to out-trigger all of them and whose negative set has dropped the two
  contradiction queries that existed precisely to separate registrations now
  competing again. That is the over-triggering failure mode the spec names.
- The six skill directories are present again and `pack.evals.skills` reads 20
  (T4 reverted).
- `packs/experience-design/` carries no edit from T5; `docs/`, `web/src/content/`
  and the census fixture carry none from T7; `tools/add-rendering-directives.py`
  and the guide tree carry none from T7a; RFC-0066 § Errata carries none from T8.
- `sweep_raw` reads **20** and `sweep` reads **18** — *not* the pre-fold 23/21.
  T6 is deliberately outside the revert set, and its fold-branch post-state
  clears every removed-skill name from the three `packs/frontend-engineering/`
  files the sweep counts (`README.md`, `AGENTS.md`,
  `.apm/skills/frontend-engineering/SKILL.md`); the fourth frontend member,
  `web/src/content/packs/frontend-engineering.md`, is T7's and does come back.
  23 − 3 = 20 and 21 − 3 = 18. Asserting the pre-fold figures here would tell an
  operator the revert was incomplete and invite them to re-add names T6
  correctly deleted — undoing the one repair the residue promises will ship.
  T9a then restores `AGENTS.md`, taking `sweep_raw` to 21 and `sweep` to 19.
- `python3 -m pytest tests/roster -q -k "experience or handoff or census"` passes.

**Approach:** the revert set was stated as narrative inside T9's body with no
task ID, no tests and no completion condition, while being the largest single
piece of abort-branch work. Without it T9a and T10a can both close green while
six new genre references sit under `information-architecture` alongside the six
skills they were meant to replace.

**Done when:** the pre-fold sweep figures are restored and the roster suites pass.

**Touches:** packs/experience-design/**, docs/**, web/src/content/**, tools/add-rendering-directives.py, guides/**, packs/agent-skill-engineering/tests/fixtures/skill-census.json, docs/rfc/0066-experience-pack-surface-genre-and-skill-uplift.md

### T9a: The abort-branch cross-pack post-state (runs only if T9 fails)

**Depends on:** T9b — the restatement targets a tree where the six skills exist
again, so the revert lands first

**Tests:**
- The genre table reads **nine** rows: today's seven, plus `marketplace-design`
  and `workspace-design` added as their own rows — which closes the routing gap
  on this branch too. Seven-plus-two is nine; an earlier draft said "seven rows"
  and "add two" in consecutive tests, which no table could satisfy.
- The availability sentinel keeps probing `conversion-design`, which is correct
  while that skill ships.
- **Exactly one** row's Surface-type cell contains `interaction`. This binds
  hardest here: the new `workspace-design` row's natural prose ("collaborative
  editing, real-time interaction surfaces") would make two rows match and red
  the suite with a message about a notification panel.
- The `design-system-foundations` → `design-system` correction stands; it never
  depended on the fold.
- `packs/frontend-engineering/AGENTS.md:11` names the six genre skills again.
  T6 removed them on the fold branch; on this branch those skills still ship, so
  a residue that no longer names three skills the pack supplies is wrong. This
  is the one T6 edit the abort branch undoes rather than keeps.
- The README route list keeps its three genre names and `interaction-design`.
- `[[pack.dependencies.recommended]]` carries all three fields `verify.py`
  requires — `catalogue`, `pack`, `version` — and its range is written without a
  space (`>=2.0.10`, not `>= 2.0.10`, which `parse_version_range` rejects). The
  value is the highest **released** `experience-design` version when T9a runs,
  read from `packs/experience-design/pack.toml` rather than assumed; it is
  `2.0.10` as of 2026-09-24. Not `3.0.0` — the abort branch never publishes it.
- `python3 -m pytest packs/frontend-engineering/tests -q` passes.

**Approach:** T6 authors the **fold-branch** post-state. The abort residue
promises the cross-pack repair ships alone, but the fold-branch table routes six
genres at a slug whose references do not exist once T3 is reverted, and its
sentinel no longer probes a skill that still ships. That restatement is real
work and had no owner — the same shape as the stranded-release finding T10a
fixes, on the content half rather than the release half.

**Done when:** all nine rows route and `packs/frontend-engineering/tests`
passes. T9a does **not** write the abort-decision record — T11 owns it, with the
deciding owner named. Two tasks writing it let T9a's bare "abort taken" line
satisfy T11's read, dropping the owner the spec requires.

**Touches:** packs/frontend-engineering/**

### T10a: The cross-pack release is registered, on either branch

**Depends on:** T6, or T9a when the gate fails

**Tests:**
- `frontend-engineering` reads `0.3.3` in `pack.toml`, in
  `.claude-plugin/plugin.json`, and in the regenerated
  `.claude-plugin/marketplace.json`.
- `docs/product/changelog.md` carries a free-standing `frontend-engineering`
  `0.3.3` entry.
- `agentbundle catalogue verify --root .` exits 0.

**Approach:** split out of T10 because T10 sits behind the activation gate and
asserts `experience-design` reads `3.0.0` — which the abort branch forbids. The
abort residue promises the cross-pack repair ships alone, but a `pack.toml`
reading `0.3.3` against a projection reading `0.3.2` reds `catalogue verify`,
so without this split the residue is unshippable and no task owns the fix.

**Done when:** the three `frontend-engineering` version surfaces agree and the
changelog entry exists, whichever branch the fold takes.

**Touches:** packs/frontend-engineering/pack.toml, packs/frontend-engineering/.claude-plugin/plugin.json, .claude-plugin/marketplace.json, docs/product/changelog.md

### T10: The `experience-design` release is registered

**Depends on:** T5, T7, T7a, T8, T9, T10a — **T7a explicitly**, because it
rewrites `tools/add-rendering-directives.py`'s per-skill map and `make build-self`
reads that map. Nothing depended on T7a before, so a projection could be
regenerated against a map still registering all six removed skills, and the
guide suites could close having never run against the swept tree.

**Tests:**
- `experience-design` reads `3.0.0` in both manifests and the marketplace
  projection, regenerated by the unforced `make build-self`.
- `docs/product/changelog.md` carries a free-standing `experience-design`
  `3.0.0` entry naming the six removed skills.
- Both catalogue commands exit 0.

**Done when:** every `experience-design` version surface agrees and catalogue passes.

**Touches:** packs/experience-design/pack.toml, packs/experience-design/.claude-plugin/plugin.json, .claude-plugin/marketplace.json, docs/product/changelog.md

### T11: Adopter hygiene and the three judgements are recorded

**Depends on:** T10 **and** T10a on the fold branch; **T10a alone** on the abort
branch, where T10 is forbidden because it asserts `experience-design` reads
`3.0.0`. T10a already encodes its own branch and T11 did not, which left the
abort branch ending at a closeout task whose dependency could never be
satisfied. Splitting only `Done when` was not enough: an unreachable task does
not reach its completion condition either.

**Tests:**
- The ledger records observed `agentbundle` install/update behaviour against a
  fixture install carrying the six skills.
- If stale directories are not pruned, the changelog states the manual step.
- Judgements 2 and 3 recorded with reviewer and date. Judgement 1 was recorded
  at T3, where its failure costs T3 alone.

**Done when (fold branch):** the ledger carries the install observation, the
`docs/` classification, both sweep-exemption reasons, the
`xd-state-reviewer-doctrine` hand-off confirmation, and all three verdicts.

**Done when (abort branch):** the ledger carries the three obligations named
above — the abort decision and its deciding owner, the
`read-the-design-handoff.md` zero-occurrence confirmation, and judgement 1 if
T3 was authored before the gate failed.

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
