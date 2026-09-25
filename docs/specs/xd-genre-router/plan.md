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
sweep                                   # decides: exits 0 only when clean
```

The completeness grep runs here, not only at closeout: without it a half-swept
tree passes every wave gate. **It binds on the fold branch only.** On the abort
branch the removed-name sweep is not owed and the hits are all correct — but
there are **two** measurement points and they differ: after T9b, `sweep_raw`
reads 20 and `sweep` 18 (T6 survives and has cleared three frontend files);
after T9a restores those three, both return to the pre-fold 23 and 21. An
operator seeing either figure after a failed gate is looking at a correct
residue, not a miss. The selector covers the handoff and census suites,
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

**Assertion blocks versus reported measurements.** A block that ends in
`sys.exit(...)` on failure **decides** — a `Done when` may say "exits 0" of it.
A block that prints a figure against a `# want` comment **reports**: it exits 0
on any value, and a human reads it. Which is which is a **property of the
block**, not a list to maintain: **a block decides when its exit status is 0 on
exactly the states its criterion calls passing, and non-zero otherwise** — for
a Python block that means a `sys.exit` or an uncaught raise on failure; for a
shell block it means checking the exit status explicitly, because a pipeline
ending in `grep -v` returns 0 when it prints and 1 when it does not, which is
the inverse of a completeness check. `sweep` is a deciding block for that
reason and `sweep_hits` is its reporting twin. A block that prints on every
path and returns 0 regardless reports. Read the block — and read its last
stage, not just its shape. One caveat for the grep-shaped reporting blocks (the
numeral grep, the `docs/` classification): `grep` returns **1** when it matches
nothing, so they exit 1 in their passing state. They are still reporting blocks
— a `Done when` naming one says "returns no output", never "exits 0" — but a
reviewer running the map top-to-bottom under `set -e` will stop on their
success. An
earlier version enumerated four reporting blocks and claimed "everything else
asserts", which was wrong by more than a factor of two — ten blocks exit 0 on
any value, among them the numeral grep, the `docs/` classification grep, the
table-parser readout, the pinned-copy counts and the method-carry floor.
Reporting blocks are legitimate; what is not legitimate is a reporting block
standing as the **sole** control for a criterion, or a `Done when` saying
"exits 0" of one. A `Done when` naming a reporting
block must say "reads N", never "exits 0", or it claims a gate that is not
there. This distinction is stated because three blocks were gated as assertions
while only printing, and one was gated as "exit 0" while returning 1 in its own
passing state.

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
# `sweep_hits` prints the files; `sweep` DECIDES — 0 when clean, 1 when a hit
# remains. A bare `sweep_raw | grep -v` is inverted: `grep -v` exits 0 when it
# prints and 1 when it prints nothing, so it returned 0 on the pre-fold tree's
# 21 hits and 1 on a correctly folded one. Measured both ways. Every other
# block in this map defers to this expression, and it is the sole control for
# the sweep acceptance criterion, so the inversion was load-bearing.
sweep_hits() { sweep_raw | grep -vE "$EXEMPT"; }
sweep() {
  local out; out="$(sweep_hits)"
  if [ -n "$out" ]; then printf '%s\n' "$out"; return 1; fi
  return 0
}
```

**Routing — all seven genres reach exactly one destination.** Counts *distinct*
genres, and tolerates the table's three-space indentation inside numbered step 1:

```bash
# Both cells, not only the key: a row with an empty or two-valued destination
# still contributes one distinct key, so counting keys alone cannot fail on it.
python3 - <<'QQ'
import re, sys
GENRES = ("marketing", "documentation", "informational", "analytical",
          "marketplace", "workspace", "transactional-journey")
text = open("packs/experience-design/.apm/skills/information-architecture/SKILL.md").read()
seen = {}
for m in re.finditer(r"^ *\| *`([a-z-]+)` *\| *([^|]*?) *\|", text, re.M):
    if m.group(1) in GENRES:
        seen.setdefault(m.group(1), m.group(2))
REMOVED = ("analytical-design", "conversion-design", "documentation-design",
           "informational-design", "marketplace-design", "workspace-design")
SURVIVING = ("interaction-design", "content-design", "design-system",
             "design-review", "creative-direction", "user-flow")
missing = [g for g in GENRES if g not in seen]
if missing: sys.exit(f"UNROUTED surface-genre values: {missing}")
bad = []
for g, dest in sorted(seen.items()):
    if not dest.strip():
        bad.append(f"{g}: empty destination"); continue
    # The three permitted outcomes, decided rather than assumed.
    ref = re.search(r"references/([a-z-]+)\.md", dest)
    # Strip the contracted citation forms before scanning for removed names:
    # `references/<genre>-design.md` contains a removed slug by construction,
    # so leaving it in makes a cell that carries BOTH a citation and a bare
    # deleted-skill name fall through to the `elif` and pass.
    scannable = re.sub(r"(references/)?([a-z-]+)-design\.md", "", dest)
    names_removed = [r for r in REMOVED if r in scannable]
    names_surviving = [k for k in SURVIVING if k in dest]
    if names_removed and not ref:
        bad.append(f"{g}: routes to deleted skill(s) {names_removed}")
    elif not (ref or names_surviving or "general" in dest.lower()):
        bad.append(f"{g}: {dest!r} is none of the three outcomes "
                   "(a reference in this skill, a named surviving skill, "
                   "or the general IA path)")
if bad:
    sys.exit("ROUTING RUBRIC:\n  " + "\n  ".join(bad))
for g, d in sorted(seen.items()): print(f"  {g} -> {d}")
QQ
# This is the PRIMARY control on the rubric's destination cell; the
# genre-reference scan, which now opens SKILL.md, is the backstop. `sweep` excludes
# `.apm/skills/information-architecture/` by carve-out (a), the genre-reference
# scan globs `references/*.md` and never opens `SKILL.md`, and no roster or
# frontend suite reads this table — so a post-fold SKILL.md that collapsed
# nothing would otherwise pass every gate. An earlier version asserted only
# that each destination was non-empty, which is true today of a table whose
# every destination names a skill this fold deletes.
grep -qE '^ *\| *`transactional-journey` *\| *`interaction-design`' "$IA/SKILL.md"  # D5(d) row survives
```

**The six genre references exist, by exact filename.** A brace glob aborts in zsh
on the first non-match, so five-of-six reports the same `0` as none-of-six:

```bash
python3 - <<'QQ'
import pathlib, sys
refs = pathlib.Path("packs/experience-design/.apm/skills/information-architecture/references")
want = [f"{g}-design.md" for g in ("analytical", "conversion", "documentation",
                                   "informational", "marketplace", "workspace")]
missing = [w for w in want if not (refs / w).exists()]
if missing: sys.exit(f"MISSING genre references: {missing}")
print("all six genre references present")
QQ
# Decided by filename, and it exits non-zero. The earlier shell loop printed
# MISSING lines and returned 0 — reporting five-of-six exactly as the brace
# glob it replaced did, which is the failure its own preamble describes. The
# `len(refs) < 11` guard elsewhere counts files, so five correct genre files
# plus one stray reaches 11 and reads clean; only this check names names.
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
n = len(body.encode())
print(n)
if n > 8000:
    sys.exit(f"AUTHORED BODY {n} B exceeds the 8,000 B ceiling — a genre's "
             "method was pasted in rather than referenced")
PY
# reads 7194 today. This block DECIDES: nothing else in the repository measures
# a SKILL.md body size — not `skill_spec_lint`, not the roster suites, not any
# `tools/` gate — so a print-and-exit-0 left the criterion with the largest
# blast radius uncontrolled. The whole point of the fold is that genre method
# loads on selection; a body that swallowed it passes every other check.
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
absent = [b for b in ("interaction-design", "design-system", "design-review",
                      "creative-direction") if b not in d]
if absent:
    sys.exit(f"BOUNDARY MISSING FROM DESCRIPTION: {absent}")
print("all four boundaries present in the description")
EOF
# Exits 1 today — `design-system` is the one absent, and the plan flags it as
# the boundary most likely to be missed. An earlier version printed that fact
# and exited 0, so the sole control for the criterion could not fail.
```

**The removals.**

No-stub is a directory-contents claim, which the Testing-Strategy rule routes
to this map. Counting the six original names cannot see a stub shipped under a
different one, which is exactly the case ADR-0038 forbids:

```bash
python3 - <<'QQ'
import pathlib, sys, tomllib
skills = {p.name for p in pathlib.Path("packs/experience-design/.apm/skills").iterdir() if p.is_dir()}
declared = set(tomllib.load(open("packs/experience-design/pack.toml","rb"))["pack"]["evals"]["skills"])
extra = skills - declared
if extra: sys.exit(f"UNDECLARED skill directories (alias or stub?): {sorted(extra)}")
if len(skills) != 14: sys.exit(f"{len(skills)} skill directories, want 14")
# The surviving skill must ship both harness files, because it absorbed seven
# skills' worth of each. Scoped to `information-architecture` deliberately:
# asserting it of every skill fails on `experience-status`, which ships no
# `evals.json` today for reasons unrelated to this fold.
ia = pathlib.Path("packs/experience-design/.apm/skills/information-architecture/evals")
for f in ("eval_queries.json", "evals.json"):
    if not (ia / f).exists():
        sys.exit(f"information-architecture is missing evals/{f}")
print(f"{len(skills)} skills, all declared, surviving skill ships both harness files")
QQ
# exits 1 today (20 directories) — and catches a stub under any name, which a
# fixed-list `ls` of the six removed names cannot.
```

```bash
ls -d packs/experience-design/.apm/skills/{analytical,conversion,documentation,informational,marketplace,workspace}-design 2>/dev/null | wc -l   # want 0
python3 -c "import tomllib;print(len(tomllib.load(open('packs/experience-design/pack.toml','rb'))['pack']['evals']['skills']))"                  # want 14; reads 20 today
```

**Sweep completeness.** Real alternation, not an ellipsis placeholder; excludes
the skills' own directories so it measures references rather than definitions:

```bash
sweep                                       # exits 0 only when clean; 1 + 21 lines pre-fold
sweep_hits | wc -l                          # 21 pre-fold (reports; does not decide)
sweep_raw | wc -l                           # 23 pre-fold (sweep_hits + the 2 exemptions)

# Carve-out (a) excludes the surviving skill, so the new references are not
# swept. Read them directly. This must be done in Python, not as a grep pipe:
# `grep -n` over a multi-file glob prefixes every output line with the matching
# file's own path, so a `grep -v "references/<genre>-design.md"` filter drops
# *every* line rather than only self-references — a file containing exactly the
# failing sentence this check exists to catch prints "clean". Verified.
python3 - <<'QQ'
import pathlib, re, sys
GENRES = r"(analytical|conversion|documentation|informational|marketplace|workspace)-design"
IA = pathlib.Path("packs/experience-design/.apm/skills/information-architecture")
refs = sorted(IA.glob("references/*.md"))
# SKILL.md is inside the carve-out too and no other control reads its prose.
scanned = refs + [IA / "SKILL.md"]
# 4 files today (agentbundle-layout, containment, reading-patterns,
# wayfinding-concepts) + 6 genre references + editorial-quality-gates = 11.
# A `< 7` threshold passed a fold that shipped only two of the six.
if len(refs) < 11:
    sys.exit(f"REFERENCE SET INCOMPLETE: {len(refs)} files, want 11 — absence must fail, not read clean")
bad = []
for f in scanned:
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
every file under `docs/specs/<delivery>/`, classified by **its owning
delivery's lifecycle, not its own file type** — so a closed delivery's notes,
benchmarks and test-results are frozen, and a live delivery's belong to that
delivery. Read the owning `spec.md`'s Status to classify; do not infer from the
filename — and the three **dated-output** directories — everything under
`docs/design/`, everything under `docs/product/research/` (covering both the
consolidation analysis and `aesthetic-style-survey.md`), and everything under
`docs/product/findings/`, which holds two live hits today
(`experience-design-thread-pressure-test.md` and `s7-walkability-handoff.md`);
frozen — by lifecycle class, per the spec; open — everything else, each owed an
edit. `findings/` is named here because this paragraph is what a T7 implementer
actually runs the classification against, and an earlier version of it listed
only two dated-output directories while the spec listed three — so the default
branch, "open, owed an edit", would have sent T7 to rewrite two dated
measurement records to remove the names of the skills they measured. The spec
owns the canonical list; this paragraph must not drift from it.

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
# The row COUNT is contract (`spec.md`: "the spec states that shape rather
# than leaving it to be inferred"), and the frontend suite asserts nothing
# about it — only that exactly one Surface-type cell contains `interaction`.
# A five-row table with a leftover row naming a *surviving* skill satisfies
# every other check here and is invisible to `sweep`, since no removed name
# remains in it.
WANT_ROWS = 4      # fold branch; the abort branch's T9a asserts 9
assert len(rows) == WANT_ROWS, f"table has {len(rows)} rows, want {WANT_ROWS}"
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

**The README's offered route set — the positive half.** The frontend suite
checks offered ⊆ routable in one direction only, so a list that dropped the
three removed names and stopped would stay green while offering no skill for
the six genres this delivery routes:

```bash
BRANCH=fold   # or: BRANCH=abort
python3 - "$BRANCH" <<'QQ'
import importlib.util, sys
branch = sys.argv[1]
d = "packs/frontend-engineering/tests/skills/frontend-engineering"
sys.path.insert(0, d)
sp = importlib.util.spec_from_file_location("t", f"{d}/test_public_claims_match_shipped_behaviour.py")
m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m)
offered = m.readme_offered_genre_skills(open("packs/frontend-engineering/README.md").read())
removed = {"analytical-design", "conversion-design", "documentation-design",
           "informational-design", "marketplace-design", "workspace-design"}
# Set **equality**, not presence: a subset check passes on a list that dropped
# the removed names and stopped, which is the defect this block exists to close.
# `test_every_route_the_readme_offers_is_one_the_skill_routes_to` checks
# offered ⊆ routable in one direction only, so it cannot catch a short list.
if branch == "fold":
    # Exactly the post-fold routable set.
    want = {"information-architecture", "interaction-design",
            "content-design", "design-system"}
else:
    # Abort: the genre skills still ship and still route, so the README is
    # unchanged from today — three genre names plus the example's route.
    want = {"conversion-design", "documentation-design",
            "analytical-design", "interaction-design"}
if offered != want:
    sys.exit(f"README ROUTE LIST ({branch}): offers {sorted(offered)}, "
             f"want exactly {sorted(want)} "
             f"(missing {sorted(want - offered)}, extra {sorted(offered - want)})")
print(branch, "branch — offered exactly:", sorted(offered))
QQ
# Fold: exactly {information-architecture, interaction-design, content-design,
#   design-system} — the post-fold routable set. A two-name answer would leave
#   the pre-flight with no route for content strategy or token foundation.
# Abort: exactly {conversion-design, documentation-design, analytical-design,
#   interaction-design} — unchanged from today, which is why that branch needs
#   no README edit.
```

**The `recommended` floor, including the field that fails silently.** Nothing
else reads it: the versions block reads only `pack['version']`, no test in
`packs/frontend-engineering/tests` opens `pack.toml`, and `catalogue verify`
*skips* an entry whose catalogue does not match rather than failing it:

```bash
python3 - <<'QQ'
import sys, tomllib
sys.path.insert(0, "packages/agentbundle")
from agentbundle.catalogue_tooling.version_ranges import parse_version_range
pack = tomllib.load(open("packs/frontend-engineering/pack.toml", "rb"))["pack"]
entries = pack.get("dependencies", {}).get("recommended", [])
xd = [e for e in entries if e.get("pack") == "experience-design"]
if not xd: sys.exit("no recommended entry for experience-design")
e = xd[0]
fail = []
if e.get("catalogue") != "agent-ready-repo":
    fail.append(f"catalogue is {e.get('catalogue')!r}, want 'agent-ready-repo' "
                "— a mismatch makes verify.py skip the entry and exit 0")
if not parse_version_range(e.get("version", "")):
    fail.append(f"version {e.get('version')!r} does not parse — no space after the operator")
if fail: sys.exit("RECOMMENDED FLOOR: " + "; ".join(fail))
print("recommended floor OK:", e)
QQ
# fold branch wants version '>=3.0.0'; abort branch the highest released
# experience-design version when the task runs (2.0.10 as of 2026-09-24).
```

**The surviving rendering-directive entry.** The spec certifies that no gate
reads this map, and deleting the six keys clears the sweep hit — so a map still
reading `["table"]` passes everything else:

```bash
python3 - <<'QQ'
import ast, re, sys
src = open("tools/add-rendering-directives.py").read()
m = re.search(r'"information-architecture":\s*(\[[^]]*\])', src)
if not m: sys.exit("information-architecture is absent from the directive map")
got = ast.literal_eval(m.group(1))
want = ["table", "narrative"]
if sorted(got) != sorted(want):
    sys.exit(f"DIRECTIVE MAP: information-architecture reads {got}, want {want}")
removed = [k for k in ("analytical-design", "conversion-design", "documentation-design",
                       "informational-design", "marketplace-design", "workspace-design")
           if f'"{k}"' in src]
if removed: sys.exit(f"DIRECTIVE MAP still registers: {removed}")
print("directive map correct")
QQ
# exits 1 today (reads ['table'] and all six keys present) — printing the wrong
# value and exiting 0 is exactly the "check that only reports a number" defect
```

**The `design-system-foundations` correction, both sites.** The frontend suite
passes with either slug because the README offers neither, so only a grep
distinguishes "corrected" from "missed"; the second command is the positive
control that the four byte-pinned copies were *not* edited instead:

A bare `grep | grep -v` is **inverted** against a gate phrased as "exit 0": a
pipeline whose last stage matches nothing returns 1, so the block would exit 0
today (2 hits) and 1 once corrected. Written as an assertion instead, so pass
means exit 0:

```bash
python3 - <<'QQ'
import pathlib, re, sys
root = pathlib.Path("packs/frontend-engineering")
# Skip __pycache__ and any non-text artifact. `grep -r` skips binaries by
# default and Python does not: reading .pyc with errors="ignore" surfaces the
# docstring compiled into it, so a corrected tree still reported two stale
# sites until the cache was cleared — a check that fails on a correct tree.
live = [f"{p}:{n}" for p in root.rglob("*")
        if p.is_file() and p.name != "digital-experience-contract.md"
        and "__pycache__" not in p.parts and p.suffix in {".md", ".py", ".toml", ".json", ".yaml", ".yml", ".txt"}
        for n, line in enumerate(p.read_text(errors="ignore").splitlines(), 1)
        if "design-system-foundations" in line]
if live:
    sys.exit("STALE SLUG REMAINS:\n  " + "\n  ".join(live))
# Positive control: the four byte-pinned copies must still carry it. If this
# reads anything but 4, the correction was applied to a pinned copy instead.
pinned = [p for p in pathlib.Path("packs").rglob("digital-experience-contract.md")
          if "design-system-foundations" in p.read_text()]
if len(pinned) != 4:
    sys.exit(f"PINNED COPIES: {len(pinned)} carry the slug, want 4")
print("slug clear in frontend-engineering; 4 pinned copies intact")
QQ
# exits 1 today (the 2 live sites), 0 when corrected — the direction the gate
# wants. Verified both ways.
```

**The four byte-pinned contract copies stay pinned.** A negative criterion with
no positive control cannot fail, and T6 edits the same pack:

```bash
# `md5` is macOS-only; on Linux it is absent, the pipeline hashes nothing, and
# `wc -l` prints 0 — loud rather than silent, but still not the check.
python3 - <<'QQ'
import hashlib, pathlib, sys
copies = sorted(pathlib.Path("packs").rglob("digital-experience-contract.md"))
if len(copies) != 4: sys.exit(f"{len(copies)} copies, want 4")
digests = {hashlib.sha256(p.read_bytes()).hexdigest() for p in copies}
if len(digests) != 1:
    sys.exit(f"the four copies have drifted: {len(digests)} distinct hashes")
print("4 copies, 1 hash — still byte-pinned")
QQ
# Decides. `shasum | sort -u | wc -l  # want 1` exits 0 whatever it prints, and
# byte-identity is what the criterion contracts — the slug-count control in the
# correction block catches an edit that removes the slug, but not one that
# leaves it in place while changing other bytes.
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
(cd web && npm ci && npm run build)    # subshell: every other block in this
                                       # map uses repository-relative paths, so
                                       # a bare `cd web` breaks each one after
                                       # it for a reviewer running top-to-bottom
# `npm ci` is not optional — see below
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

**The six genre quality-eval sets.** Existence is not the check: the surviving
skill already ships an `evals.json` carrying its own case set, so a fold that
carried nothing across satisfies a file-exists assertion. `skill_spec_lint`
cross-checks `[pack.evals].skills` against the skill directory and
`eval_queries.json` **only**, never `evals.json`, so six vanished case sets
leave `catalogue lint --deep` green:

```bash
python3 - <<'QQ'
import json, pathlib, sys
BASE_CASES = 1   # information-architecture's own pre-fold case count
ia = json.load(open("packs/experience-design/.apm/skills/information-architecture/evals/evals.json"))
cases = ia.get("evals", [])
dropped = pathlib.Path("docs/specs/xd-genre-router/notes/verification-ledger.md")
recorded = dropped.exists() and "evals.json" in dropped.read_text()
if len(cases) <= BASE_CASES and not recorded:
    sys.exit(f"evals.json carries {len(cases)} case(s) — the pre-fold count. "
             "Either the six genre quality-eval sets were not carried across, "
             "or the ledger must record which were knowingly dropped and why.")
print(f"evals.json carries {len(cases)} cases"
      + ("; ledger records a drop decision" if recorded else ""))
QQ
# exits 1 today (1 case, no ledger entry). Satisfied either by carrying the
# genre case sets or by recording the drop — the criterion's two branches.
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
| Activation baseline | `notes/activation-baseline.md` | T1, T2, T9 | Both runs recorded, three each, positive and negative figures clearing; the grading rule recorded in the spec's words and reproduced unchanged by T9; the pre-fold description control recorded with its method |
| Genre quality-eval sets | `IA/evals/evals.json` | T3, T11 | Case count above the pre-fold baseline with the six genre sets carried, **or** the ledger naming which were dropped and why — existence alone passes on an untouched file, and `skill_spec_lint` never reads this file |
| Pooled trigger queries | `IA/evals/eval_queries.json` | T1, T3 | 71 positives / 67 negatives asserted, no opposite-trigger collision, both named negatives present by exact text, and the set identical to the one T1 graded |
| Six genre references + relocated shared file | `IA/references/` | T3 | Six files present; `cmp` clean on the relocated file; judgement 1 recorded |
| Rewritten rubric | `IA/SKILL.md` | T3, T11 | Seven genres each reaching one of the three permitted destinations — asserted, not merely non-empty; authored body ≤ 8,000 B; all four description boundaries present; judgement 2 recorded with reviewer and date (**T11** — T3 records judgement 1 only) |
| Six directories removed | `packs/experience-design/.apm/skills/` | T4 | Directory count 0; `pack.evals.skills` reads 14 |
| Pack internals swept | `pack.toml`, `DESIGN.md`, `JOURNEY.md`, `README.md`, `docs/index.md` | T5, T11 | `sweep` empty under `packs/experience-design/`; six `DESIGN.md` locations restated; § 10 entry signed and dated (T5); the sibling's non-edit criterion cited in the ledger (**T11** — T5 cannot write it); `docs/index.md`'s two numerals reading 14 |
| Cross-pack (fold branch) | `packs/frontend-engineering/**` | T6, T10a | Four-row table enumerating the six `surface-genre:` tokens, exactly one Surface-type cell containing `interaction`; `AGENTS.md:11` repointed; README offering the post-fold routable set including `information-architecture`; `recommended` declared with `catalogue = "agent-ready-repo"` and `>=3.0.0` — absent and correct are indistinguishable to every other gate; `design-system-foundations` gone from both live sites; `packs/frontend-engineering/tests` green; `0.3.3` in both manifests and the projection |
| Cross-pack (abort branch) | `packs/frontend-engineering/**` | T9a, T10a | **Nine**-row table with `marketplace-design` and `workspace-design` added; sentinel still probing `conversion-design`; `AGENTS.md:11` naming the six again; `recommended` reading `>=2.0.10`; same suite green; same `0.3.3` release surface |
| Fold work reverted (abort branch only) | `packs/experience-design/**`, `docs/**`, `web/src/content/**`, `tools/`, `guides/**`, census fixture | T9b | `sweep_raw` back to **20** and `sweep` to **18** — not the pre-fold 23/21, because T6 survives the abort; `pack.evals.skills` back to 20; every T3 output reverted including `evals/eval_queries.json` and the frontmatter `description`; roster suites green |
| Docs, site, census | `docs/`, `web/src/content/`, census fixture | T7 | Class record for every `docs/` hit in the ledger, against the spec's three-directory dated-output class; the count-shaped numeral grep clean across all four files; `web/src/content/packs/frontend-engineering.md` naming the table's target; `npm ci && npm run build` exit 0; census suite green |
| Guide tree and `tools/` | `guides/**`, `tools/add-rendering-directives.py` | T7a | `sweep` empty under `guides/` and `tools/`; five guide commands exit 0; `information-architecture`'s rendering-directive entry asserts `["table", "narrative"]` — no gate reads this map, so nothing else can catch it; the two guide numerals read 14; the `lint-guidebook-steps.py` exemption reason in the ledger; the `read-the-design-handoff.md` zero-occurrence confirmation in the ledger |
| User promise — the guide a reader follows | `guides/experience-design/` | T7a, T11 | Guide-agreement suite green and the five guide commands exit 0 (T7a); judgement 3 recorded with reviewer and date (**T11** — T7a does not record verdicts) |
| RFC-0066 erratum | `docs/rfc/0066-…md` § Errata | T8 | Two-layer section; new entry names D4 and no delivery artifact; prior entry verbatim |
| Versions + changelog (fold branch) | three manifests, changelog | T10, T10a | All three surfaces agree at `3.0.0`/`0.3.3`; both changelog entries free-standing; catalogue lint and verify exit 0 |
| Versions + changelog (abort branch) | `frontend-engineering` manifests, projection, changelog | T10a | `0.3.3` on all three `frontend-engineering` surfaces and its changelog entry; `experience-design` untouched at its pre-fold version, which is correct here rather than a miss |
| Closeout (fold branch) | `notes/verification-ledger.md` | T11 | All five `Done when` items: install/update prune behaviour observed; the `docs/` classification; **both** sweep-exemption reasons, the `tone-of-voice` one included; the `xd-state-reviewer-doctrine` hand-off confirmation; three verdicts with reviewer and date |
| Closeout (abort branch) | `notes/verification-ledger.md` | T11 | Exactly three: the abort decision naming `eugenelim` as deciding owner; the `read-the-design-handoff.md` zero-occurrence confirmation; judgement 1 if T3 was authored before the gate failed. The prune observation and judgements 2 and 3 are **not** owed — a closeout reviewer reading this column must not go looking for them |

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

**Done when:** the file records both pooled sets with three runs each and the
environment named, the graded query set verbatim, **the grading rule in the
spec's own words** — a pre-fold positive passes when the query activates any one
of the seven, a negative when it activates none — **and** the pre-fold resident
description measurement with its method. The grading rule is what makes the two
runs comparable at all, and a note recording both sets, three runs and the
environment satisfies every other clause while grading pre-fold positives
against a single expected skill. That would depress the baseline by a rule no
criterion checked, let the post-fold figure clear it trivially, and leave the
one objection that can defeat this fold never actually tested. That last one is easy to drop — it
reads as unrelated to the activation runs — but T9's own `Done when` requires a
recorded *delta*, which is not computable without the control T1 owns. Omitting
it leaves the implementer inheriting the `2.0.9` figure this task exists to
displace, crediting this fold with the sibling slice's description rewrite.

**Touches:** docs/specs/xd-genre-router/notes/activation-baseline.md

### T2: The abort path is written down before it can be needed

**Depends on:** T1

**Tests:**
- `notes/activation-baseline.md` names both triggers — failing gate, or the
  window from `Approved` elapsing.
- It names the residue in full — **five** items, not a summary: the six
  directories stay; the `frontend-engineering` table repair; its
  `design-system-foundations` slug correction; that pack's version bump; **and**
  its regenerated marketplace entry and changelog entry. The last two are the
  point: a `pack.toml` reading `0.3.3` against a projection reading `0.3.2`
  reds `agentbundle catalogue verify`, so a residue that ships the bump without
  them is not shippable at all.
- It names `eugenelim` as deciding owner.

**Done when:** both triggers, all five residue items, and the named owner are
present. "Cross-pack repair ships alone" as a summary line does not discharge
the enumeration — the two items most easily dropped are the two that make the
residue shippable.

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
- The **narrower genre-reference name scan** exits 0. This is T3's to run, and
  nothing else can: `sweep` excludes `.apm/skills/information-architecture/` by
  construction, so a reference carrying across a sentence like
  `interaction-design/references/pattern-families.md:219`'s "`analytical-design`
  covers the full widget hierarchy" is invisible to every wave gate.
- `evals/eval_queries.json` pools the seven skills' positives and carries the two
  named negatives.
- `evals/evals.json` carries the six genre quality-eval sets, or the ledger
  records which were knowingly dropped and why. `skill_spec_lint` cross-checks
  `pack.evals.skills` against `eval_queries.json` alone, so six vanished
  quality-eval sets leave `catalogue lint --deep` green. `packs/AGENTS.md` obliges an eval-harness update on any
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

**Done when:** every mechanical test passes — including the authored-body block,
which now decides, and the genre quality-eval block, which distinguishes
"carried" from "untouched" — the narrower genre-reference name scan exits 0, `lint-experience-agnostic` exits 0, and judgement 1 is recorded
with reviewer and date.

**Touches:** packs/experience-design/.apm/skills/information-architecture/**, docs/specs/xd-genre-router/notes/verification-ledger.md

### T4: The six registrations are gone

**Depends on:** T3

**Tests:**
- Six directories absent — and their `evals/evals.json` quality-eval sets have
  already been carried into the surviving skill by T3, or the drop is recorded.
  Each removed skill ships two harness files and only `eval_queries.json` was
  ever named; deleting the directory takes the other with it.
- `pack.evals.skills` lists fourteen.
- No alias, shim or stub exists.

**Done when:** the directory count is zero, the evals list is fourteen, and
`.apm/skills/` holds no alias, shim or deprecation stub for a removed name —
checked by listing the directory and comparing against the fourteen the evals
list names, since a stub under a *different* name satisfies both other clauses
(directory absence covers only the six original names, and the evals list
counts entries).

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

**Done when:** `docs/index.md`'s two numerals both read 14 — no wave gate can
see a numeral, so this is the only thing standing between the pack and shipping
"pack of 20 skills" at fourteen skills — `sweep` is empty under
`packs/experience-design/`, the four
stated-post-state files above read as stated, all **six** `DESIGN.md` locations
— including the line-185 section heading — describe the new shape, and § 10
carries its amended rationale entry with approver and date, and the sibling's
non-edit criterion is **read** — recorded in the ledger, not written into
`DESIGN.md`, which would put a delivery-time citation into shipped pack
content. **T11 owns the recording and its fold `Done when` lists it**; T5's
`Touches` reaches only `packs/experience-design/**` and cannot write the
ledger. An earlier revision credited T5's map row with that evidence while
deferring the write to a T11 condition that did not mention it, leaving the
closeout column demanding evidence from a task that cannot produce it. Nothing else can see a missing § 10 entry: no slug
check, no location check and no `sweep` hit reaches it.

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
  `(pick …)` route list becomes **exactly the post-fold routable set** —
  `information-architecture`, `interaction-design`, `content-design`,
  `design-system` — and stays a parenthetical that splits into exactly three
  em-dash-delimited parts. Stating only the negative half ("drops the three
  removed names, keeps `interaction-design`") describes a list that offers one
  route for a table routing six genres, and both README guards stay green on
  it: the suite checks offered ⊆ routable in one direction only. The map's
  `BRANCH=fold` block asserts the positive half.
- The availability sentinel probes for **`information-architecture`** — stated
  positively, because "no longer probes a deleted skill" is satisfied by
  deleting the paragraph outright, which `sweep` reads as clean, the frontend
  suite never opens, and `Done when` would accept. That would leave step 1b
  loading an XD skill with no probe and no named-skip path, which this delivery
  claims to preserve. The paragraph is
  `packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md:174-177`.
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
  that resolves to nothing. Copy the shape from `packs/atlassian/pack.toml:20-23`;
  only the `recommended` sub-key is new here. No count is given — the spec
  records that an earlier "four" was wrong (the tree holds eight such files,
  nine entries) and that the figure is not load-bearing. `parse_version_range` splits on whitespace, so `>= 3.0.0` becomes
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

**Done when:** the frontend suite passes, all six genres are reachable, the
sentinel probes for `information-architecture` and the named-skip text beside
it names the same skill, `AGENTS.md:11` names the surviving skill and the genre
set, the `guides/frontend-engineering/how-to/read-the-design-handoff.md`
zero-occurrence confirmation is recorded in the ledger — moved here from T7a
because T6 is outside the abort revert set and that confirmation is one of the
abort branch's three closeout obligations — and the three map blocks this task
owns each exit 0 — the README offered-route set
(which must include `information-architecture`, not merely exclude the removed
names), the `recommended` floor (whose `catalogue` field fails silently), and
the two-site `design-system-foundations` correction. The frontend suite reaches
none of these: it checks offered ⊆ routable in one direction only, opens no
`pack.toml`, and passes with either slug in the table because the README offers
neither. The three **positive** post-states are named in this condition because
`sweep` reads deletion and repointing identically — the only genre-name
occurrences in those two files are the sentinel at `SKILL.md:175`, the table at
`183-186`, and `AGENTS.md:11`, so deleting each clears the sweep exactly as
repointing does, and nothing else opens them.

**Touches:** packs/frontend-engineering/**, docs/specs/xd-genre-router/notes/verification-ledger.md

### T7: Docs, site and census tell the truth

**Depends on:** T4

**Tests:**
- Every **open** `docs/` record naming a removed skill is updated, starting with
  `docs/product/intents/skill-sequence-wayfinding.md`; frozen records and dated
  outputs are exempt and the classification is recorded.
- `docs/product/journeys/designer-designs-surface.md` describes the surviving set.
- `xd-ia-archetypes-objects.md`'s observed-state table is re-measured, re-dated,
  and its verdict corrected for the new reference structure. This file is
  invisible to **both** automatic controls — it carries zero removed-skill names
  (verified), so `sweep` never returns it and the `docs/` classification never
  enumerates it. Its line-range citations to
  `information-architecture/SKILL.md:69-77` and
  `frontend-engineering/SKILL.md:357-374` both move, and its
  "no file of that name anywhere" verdict about `references/page-archetypes.md`
  stops being true once this fold puts six files in that directory.
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

**Done when:** the post-edit `docs/` grep returns **only** files in the exempt,
dated-output and frozen classes — the **open class empty** — not merely that
every hit carries a label. `sweep`'s roots are `packs/ guides/ web/ tools/
tests/` and do **not** include `docs/` (48 files match there today), so the
classification grep is the only `docs/` instrument and it reports rather than
decides: a tree where every open record is correctly labelled "open, owed an
edit" and then left unedited satisfies a labelling-only condition verbatim.
That covers `docs/product/intents/skill-sequence-wayfinding.md` and
`docs/product/journeys/designer-designs-surface.md`, and it is this plan's
second-ranked risk — whose stated control was the step that does not decide.
Also: the count-shaped numeral grep returns no output across all four
files — T7 runs it as the wave gate, so its clean result gates here rather than
in each task that owns one numeral — `grep -q 'fifteenth skill'` on
`web/src/content/packs/experience-design.md` exits 0, since a negative grep
alone passes on a line whose ordinal was deleted rather than rewritten,
`web/src/content/packs/frontend-engineering.md` names the table's routing
target, both `xd-ia-archetypes-objects.md` halves are done — the re-measured,
re-dated table and the corrected `page-archetypes.md` verdict — the
`xd-state-reviewer-doctrine` hand-off confirmation is in the ledger, the
classification lands in
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
  `experience-design`, or the word "genre"). **T6** records that confirmation
  in the ledger, not T7a — T6 is outside T9b's revert set, so the record
  survives an abort, and this file's content does not depend on the fold. Writing a routing target into it would fail the spec criterion by
  construction — an earlier draft of this task ordered exactly that.
- The five guide commands each exit 0, `lint-guidebook-steps.py` with its pack
  argument.

**Approach:** split from T5 and T7 because neither owned these trees, while the
sweep-completeness grep covers both — a gap that would have surfaced only at
closeout.

**Done when:** `sweep` returns no hit under `guides/` or `tools/` — it filters
the exemption by construction — `sweep_raw`'s only remaining `tools/` hit is
`lint-guidebook-steps.py` with the exemption's reason recorded in the ledger,
`information-architecture`'s rendering-directive entry reads
`["table", "narrative"]` — deleting the six keys clears the sweep hit, so a map
still reading `["table"]` passes every other check, and the spec itself
certifies no gate reads this file — the two guide-tree numerals read 14, the
five guide commands each exit 0 (the map row claims them as T7a's closeout
evidence, so they belong in its completion condition), and the
`read-the-design-handoff.md` zero-occurrence confirmation is in the ledger. That
last one appeared only in T11's *abort*-branch condition, so on the fold branch
the one criterion whose whole obligation is a ledger line was gated by nothing.

**Touches:** tools/add-rendering-directives.py, guides/experience-design/**, guides/frontend-engineering/**, docs/specs/xd-genre-router/notes/verification-ledger.md

The ledger is in this list because T7a's `Done when` reads it: the
`lint-guidebook-steps.py` exemption reason and the `read-the-design-handoff.md`
zero-occurrence confirmation are both T7a's to write. This is the same
`Touches`-cannot-reach defect already fixed for the `web/` page, which moved
from T6 to T7.

### T8: RFC-0066 records what no longer holds

**Depends on:** T4

**Tests:**
- A dated, approver-signed entry names D4, the retirement, the preserved method,
  and that D2 and D5(d) are unchanged.
- **The entry this delivery authors** names no spec and no brief. The rule is
  scoped to the new entry, not to the section: the existing 2026-07-27 entry
  names `docs/specs/ux-writing-rename/` and travels into
  `### History / audit trail` **byte-unchanged**. RFC-0055 D3 makes correction
  sections append-only, so rewording a prior entry to satisfy a rule written
  later is the larger violation. An unscoped reading of this test would have an
  implementer strip that reference and still pass every stated test.
- The Errata section is in RFC-0055 D2's two-layer form, headed
  `### Current state` and `### History / audit trail`.

**Done when:** the new entry **names D4** and states all three of its content
obligations — the six registrations are retired, the genre method is preserved
as references under `information-architecture`, and D2's taxonomy and D5(d)'s
route are unchanged — the section is in two-layer form, the new entry cites no
delivery artifact, and the 2026-07-27 entry is byte-identical to its pre-change
form, verifiable with `git diff` on that hunk. The three shape obligations were
gated and the content one was not, so an erratum saying nothing about D4 closed
this task green.

**Touches:** docs/rfc/0066-experience-pack-surface-genre-and-skill-uplift.md

### T9: The post-fold activation figure clears the gate

**Depends on:** T2, T3, T4, **T6** — T2 explicitly, so the abort path exists
before the trigger that invokes it can fire; and T6 explicitly, so the
cross-pack wave has landed before the gate fires. T6 was previously unordered
against T9, which made T9b's completion figures indeterminate: run
T1→T2→T3→T4→T9 and a failed gate leaves `sweep_raw`/`sweep` at 23/21 rather
than the 20/18 T9b demands, telling the operator the revert is incomplete —
the round-5 misreading, inverted. T6 does not depend on the fold, so ordering
it first costs nothing and makes one figure determinate.

An earlier revision also made T9 depend on T7a, because T7a was then the only
producer of the `read-the-design-handoff.md` zero-occurrence confirmation that
T11's abort `Done when` requires. That edge bought one ledger line at the cost
of running T7a's whole guide-tree rewrite, its two numerals and its
`add-rendering-directives.py` edit ahead of the gate — all inside T9b's revert
set, so all undone on abort. The confirmation moved to **T6** instead, which
sits outside the revert set: the file it concerns carries no genre skill, no
`information-architecture`, no `experience-design` and not the word "genre",
so the confirmation does not depend on the fold at all.

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
  T9a then restores **all three** of those files, not just `AGENTS.md`: its tests
  require the nine-row table whose four genre rows name their own skills and the
  sentinel still probing `conversion-design` (both in `SKILL.md`), the README
  route list keeping its three genre names, and `AGENTS.md` naming the six
  again. So the abort **end** state is `sweep_raw` 20 + 3 = **23** and `sweep`
  18 + 3 = **21** — the pre-fold figures, reached at T9a rather than at T9b.
  There are two distinct measurement points and they differ; stating one figure
  for both is what produced this error.
- `python3 -m pytest tests/roster -q -k "experience or handoff or census"` passes.

**Approach:** the revert set was stated as narrative inside T9's body with no
task ID, no tests and no completion condition, while being the largest single
piece of abort-branch work. Without it T9a and T10a can both close green while
six new genre references sit under `information-architecture` alongside the six
skills they were meant to replace.

**Done when:** `sweep_raw` reads **20** and `sweep` reads **18** — the
post-T9b figures its tests state, *not* the pre-fold 23/21, which are only
reached after T9a — and the roster suites pass. A completion condition demanding
the pre-fold figures here would tell the operator the revert was incomplete and
send them to re-add the three names T6 correctly deleted.

**Touches:** packs/experience-design/**, docs/** *except* `docs/specs/xd-genre-router/notes/`, web/src/content/**, tools/add-rendering-directives.py, guides/**, packs/agent-skill-engineering/tests/fixtures/skill-census.json, docs/rfc/0066-experience-pack-surface-genre-and-skill-uplift.md

**Explicitly out of scope:** `docs/specs/xd-genre-router/notes/` **and
`docs/product/changelog.md`**. T10a depends on T6 alone, so it may legitimately
land the `frontend-engineering` `0.3.3` bump and its changelog entry before the
gate fires; that entry is a condition of the residue being shippable at all.
T9b reverts only the `experience-design` `3.0.0` entry if T10 had already
written one. The rest of the carve-out reasoning: The revert set
is defined task-wise, but the path scope is `docs/**`, and this spec's own
`activation-baseline.md` (the abort decision and its deciding owner) and
`verification-ledger.md` (judgement 1, the `read-the-design-handoff.md`
confirmation) live inside it — T7's `Touches` reaches the ledger, so "carry no
edit from T7" would otherwise sweep it away. Reverting them would delete the
three records T11's abort `Done when` then requires.

### T9a: The abort-branch cross-pack post-state (runs only if T9 fails)

**Depends on:** T9b — the restatement targets a tree where the six skills exist
again, so the revert lands first

**Tests:**
- The genre table reads **nine** rows — asserted with the same parser block T6
  uses, with `WANT_ROWS = 9`, because the row count is contract on this branch
  too and the frontend suite asserts nothing about it: today's seven, plus
  `marketplace-design` and `workspace-design` added as their own rows — which closes the routing gap
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

**Done when:** all nine rows route, `packs/frontend-engineering/tests` passes,
`sweep_raw` is back to 23 and `sweep` to 21, and the same three map blocks T6
owns each exit 0 against this branch's post-state — the README offered-route
set run as `BRANCH=abort`, where the three genre names plus
`interaction-design` is the correct answer and no README edit is owed — the
block's `information-architecture` assertion is fold-branch only — the
`recommended` floor at the abort-branch value, and the `design-system-foundations` correction, which
never depended on the fold. T9a does **not** write the abort-decision record — T11 owns it, with the
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
- `make lint-ruff lint-mypy` exits 0. It is an acceptance criterion under Gates
  and appeared in this plan only inside a map block, named by no task — the
  cross-cutting Construction tests run `lint-experience-agnostic.py`, the roster
  selector and `sweep`, not the repository lint. T10 owns it as the last task
  before closeout on the fold branch.

**Done when:** every `experience-design` version surface agrees, catalogue
passes, and `make lint-ruff lint-mypy` exits 0.

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
`xd-state-reviewer-doctrine` hand-off confirmation, the **§ 10 sole-editor
citation** naming the sibling spec's non-edit criterion, and all three
verdicts — **and**, if any of the six genre quality-eval sets was knowingly dropped rather
than carried into `evals.json`, the ledger names which and why. The enumeration
is stated as closed ("all five"), so a criterion discharged by a ledger entry
needs a slot in it or the entry has nowhere to land — **and**, if the install
observation showed `agentbundle` does **not** prune a
directory the pack no longer declares, the changelog states the manual step.
That branch is the whole reason the observation is taken: an unpruned stale
`SKILL.md` stays in an adopter's skill index and keeps activating against a
method the pack no longer ships. T10's changelog test requires only that the
entry name the six removed skills, so nothing else reaches it.

**Done when (abort branch):** the ledger carries the three obligations named
above — the abort decision and its deciding owner, the
`read-the-design-handoff.md` zero-occurrence confirmation, and judgement 1 if
T3 was authored before the gate failed.

**Touches:** docs/specs/xd-genre-router/notes/verification-ledger.md, docs/product/changelog.md

All three abort-branch obligations land in the **ledger**, which is the one
file T11 is scoped to edit. An earlier map row also named
`notes/activation-baseline.md` as a closeout destination; T11 cannot reach it,
and an implementer reading the map rather than the task would have written the
abort decision into a file outside this task's scope — the same
`Touches`-cannot-reach shape already repaired for the `web/` page and for
T7a's ledger.

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
