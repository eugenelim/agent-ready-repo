# Plan: One copy-layer skill with three modes

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `packs/AGENTS.md` (§ Version bump rule; § Authoring or editing a skill); `tests/AGENTS.md` (the three guarded edits a **new** `tests/roster/test_*.py` owes, which this plan avoids by extending an existing suite); `tests/roster/test_experience_design_write_declaration_and_containment.py` — specifically `test_every_containment_copy_is_byte_identical`, which globs `*/references/containment.md` off the filesystem and is the pattern this delivery reuses, and separately `test_every_skill_citing_the_module_ships_its_own_copy`, which is the citation-derived one and runs citation → copy, so neither can fail on a copy that nothing cites; two analogous multi-mode skills — `packs/core/.apm/skills/project-knowledge/` (capture / distill / enquire behind one description) and `packs/core/.apm/skills/author-delivery-brief/` (create / continue). Named uncertainty: the pervasive-versus-localized divergence classification has no repository precedent and is authored here as a judgement with a recorded verdict.

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
  `experience-design` → `4.0.0` (second of two) — a fixed contract value.
  `product-engineering` takes a **patch** computed from its value at this
  delivery's merge-base, never a literal copied from here: it reached `0.13.18`
  on its own while this plan was in draft, which is how an earlier `0.13.17 →
  0.13.18` constraint came to be satisfied by an untouched tree.
  `frontend-engineering` takes none: it names neither removed skill.
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
nothing. Every block below was executed against the pre-fold tree and its
present-state reading recorded, so a reviewer can distinguish a broken command
from a failing check. The blocks were first run on 2026-09-24 and re-run on
2026-09-25 after review; every reading below carries the later date.

Set the roots once. `BASE` is derived **once, here**, behind a guard: three
blocks below need it, and an unresolvable revision makes `git diff` write to
stderr and produce empty stdout, which a downstream `grep` reads as "no
violations" rather than as a broken command. The errata scan is the delivery's
only control on the `Never do` rule about naming a spec or a brief, so it must
not disarm quietly:

```bash
CD=packs/experience-design/.apm/skills/content-design
REMOVED='\b(copy-direction|tone-of-voice)\b'
BASE=""
if ! git rev-parse --verify origin/main >/dev/null 2>&1; then
  echo "origin/main not fetched in this worktree — run 'git fetch origin main' first"
else
  BASE=$(git merge-base origin/main HEAD)
fi
[ -n "$BASE" ] || echo "BASE is empty — the diff-based blocks below will refuse to run"
```

This block sets `CD`, `REMOVED` and `BASE` for every block below, so run it in
your own shell, not a subshell. It reports and continues rather than calling
`exit` — an `exit` here closes an interactive session and takes the message
telling you to fetch with it. The blocks that consume `BASE` each refuse
individually when it is empty.

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
# The two that survive in two places still need the $CD-scoped half: a pack-wide
# count of 2 passes when both copies landed in skills other than content-design.
for r in interrogation-sequence editorial-quality-gates; do
  test -f "$CD/references/$r.md" || echo "MISSING $CD/references/$r.md"
  n=$(find packs/experience-design/.apm/skills -name "$r.md" | wc -l | tr -d ' ')
  [ "$n" = 2 ] || echo "EXPECTED 2 $r.md pack-wide, found $n"
done
# and the named second holder in each case:
test -f packs/experience-design/.apm/skills/creative-direction/references/interrogation-sequence.md || echo "creative-direction's variant was touched"
test -f packs/experience-design/.apm/skills/information-architecture/references/editorial-quality-gates.md || echo "the genre fold's relocated copy is missing"
test ! -f "$CD/references/audience-jtbd.md" || echo "merged file must be copy-jtbd.md, not audience-jtbd.md"
```

**The shared editorial file is cited from the surviving `SKILL.md`.** This grep
is the *only* thing that checks the citation — see the anchors line: the suite's
byte-equality test globs the filesystem, and its citation-derived test runs
citation → copy, so neither can fail on a copy that nothing cites. A citation
living in a reference body would leave the copy an orphan with every test green:

```bash
grep -q 'references/editorial-quality-gates.md' "$CD/SKILL.md"
```

**Byte-equality, by the named new assertion** rather than the whole suite. The
file passes 6 tests today, before any extension exists, so running it whole
proves nothing about this delivery:

```bash
python3 -m pytest tests/roster/test_experience_design_write_declaration_and_containment.py \
  -q -k editorial_quality_gates_copies_are_byte_identical
# Before the extension lands the selector matches nothing and pytest exits **5**
# ("no tests ran") — not 1. Exit 5 is the expected pre-state; exit 1 means the
# extension exists and fails; exit 0 means it exists and passes. Treating 5 as
# "RED" conflates a missing test with a failing one.
# The extension carries the existing len(copies) >= 2 vacuity guard.
```

**All three assets survive under the surviving skill.** Two of them live in
directories T6 deletes, so this is a relocation check, not a content check:

```bash
for a in content-brief-template copy-direction-template tone-of-voice-template; do
  test -f "$CD/assets/$a.md" || echo "MISSING $CD/assets/$a.md"
done
ls "$CD/assets/"   # want exactly those three
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

**No removed name survives as a registration.** Real alternation. The scope is
the spec's stated scope: the five trees, the repo-root `workspace.toml`, and the
five `docs/` files this delivery edits — **not** `docs/` wholesale. The reason is
what a registration sweep owns, **not** the frozen-record rule: the rest of
`docs/` holds records that *mention* the skills rather than register them, and
two of them — `xd-genre-router` (Approved) and `creative-direction-modes`
(Implementing) — are live records the frozen-record rule does not cover at all.
An earlier draft's comment claimed `docs/` was in scope while the command omitted
it entirely, and then justified the omission on that rule:

```bash
DOCS_IN_SCOPE="docs/rfc/0062-content-design-and-copy-direction-skills.md \
docs/rfc/0071-digital-experience-doctrine.md \
docs/product/briefs/digital-experience-doctrine-completion.md \
docs/product/intents/xd-state-reviewer-doctrine.md \
docs/product/changelog.md"
grep -rlE "$REMOVED" packs/ guides/ web/ tools/ tests/ workspace.toml $DOCS_IN_SCOPE 2>/dev/null \
  | grep -vE '\.apm/skills/(copy-direction|tone-of-voice)/' \
  | grep -vF 'web/src/lib/now-highlights.generated.json'
# `now-highlights.generated.json` is excluded: it is generated and gitignored,
# rebuilt from the changelog by every `web/` and `docs-site/` run, so it is not a
# surface this delivery edits and a hit there is noise, not a defect.
# want: only files whose hits are discriminator uses on the counted list above.
# Recorded readings, 2026-09-25, for the five trees + workspace.toml only:
#   27 files pre-genre-fold. An earlier draft recorded 28; `git grep` at each of
#   the last five commits also returns 27, so 28 was never a reading and a
#   reviewer comparing against it would chase a phantom one-file delta.
#   24 files post-genre-fold — that fold deletes conversion-design/SKILL.md, its
#   evals/evals.json and its editorial-quality-gates.md. **24 is this slice's
#   baseline**, because the genre fold lands first.
# Classify each hit registration vs discriminator; a registration hit is a
# defect, a discriminator hit is required.
grep -n 'copy/' packs/experience-design/DESIGN.md
# § 7's artifact row names both skills as registrations and must be retargeted;
# DESIGN.md holds no `type: tone-of-voice` literal, so it carries no carve-out
```

**The removals.**

No-stub is a directory-contents claim: counting the two removed names cannot see
a stub shipped as `copy-direction-legacy`, which is the case ADR-0038 forbids.
And `pack.evals.skills` needs membership, not length — a list that dropped an
unrelated skill and kept `tone-of-voice` has length twelve:

```bash
ls -d packs/experience-design/.apm/skills/{copy-direction,tone-of-voice} 2>/dev/null | wc -l   # want 0
python3 - <<'QQ'
import pathlib, sys, tomllib
root = pathlib.Path("packs/experience-design")
skills = {p.name for p in (root / ".apm/skills").iterdir() if p.is_dir()}
declared = set(tomllib.load(open(root / "pack.toml", "rb"))["pack"]["evals"]["skills"])
extra = skills - declared
if extra: sys.exit(f"UNDECLARED skill directories (alias or stub?): {sorted(extra)}")
if skills != declared: sys.exit(f"declared but absent: {sorted(declared - skills)}")
if len(skills) != 12: sys.exit(f"{len(skills)} skill directories, want 12")
for gone in ("copy-direction", "tone-of-voice"):
    if gone in declared: sys.exit(f"{gone} still declared in pack.evals.skills")
if "content-design" not in declared: sys.exit("content-design is not declared")
# The surviving skill absorbed two skills' worth of eval harness, so it must
# ship both harness files and the fixture tree the folded skills carried.
cd = root / ".apm/skills/content-design/evals"
# eval_queries.json is NOT optional: skill_spec_lint cross-checks
# pack.evals.skills against it, so its absence breaks the catalogue gate.
if not (cd / "eval_queries.json").exists():
    sys.exit("content-design is missing evals/eval_queries.json")
# evals.json and the fixture trees ARE the carried-or-dropped set. Each source
# gets its own disposition; one surviving directory does not prove both source
# fixture trees were handled. Read the sources at the merge-base, since T6
# deletes them.
import subprocess
base = subprocess.run(["git", "rev-parse", "--verify", "origin/main"],
                      capture_output=True, text=True).returncode == 0
if not base:
    sys.exit("origin/main not fetched — cannot read the source harnesses")
BASE = subprocess.run(["git", "merge-base", "origin/main", "HEAD"],
                      capture_output=True, text=True, check=True).stdout.strip()
if not BASE:
    sys.exit("merge-base empty — refusing to judge the harness disposition")
# Each source harness file gets its own disposition. `evals.json` and
# `evals/files/` may be carried OR dropped with a recorded reason; the reason is
# recorded per source, because one surviving `files/` directory does not prove
# both source trees were handled.
import re as _re
import subprocess as _sp

ledger = pathlib.Path("docs/specs/xd-copy-router/notes/verification-ledger.md")
ledger_text = ledger.read_text() if ledger.exists() else ""

def dropped_with_reason(token):
    """A recorded drop: the token, a dash, and >= 20 characters of reason ON ITS OWN LINE.

    Bounding to the line matters: a match that ran to end-of-file would let any
    later section supply the character count while the reason itself is empty.
    The separator may be an em-dash, `--` or `-`; none is load-bearing.
    """
    pattern = _re.compile(
        r"^.*" + _re.escape(token) + r":\s*dropped\s*(?:\u2014|--|-)\s*(?P<reason>.+)$", _re.M
    )
    hit = pattern.search(ledger_text)
    return hit is not None and len(hit.group("reason").strip()) >= 20

def existed_at_base(path):
    return _sp.run(["git", "cat-file", "-e", f"{BASE}:{path}"],
                   capture_output=True).returncode == 0

problems = []
for gone in ("copy-direction", "tone-of-voice"):
    src = f"packs/experience-design/.apm/skills/{gone}/evals"
    for leaf, carried in (("evals.json", (cd / "evals.json").exists()),
                          ("files", (cd / "files").is_dir())):
        if not existed_at_base(f"{src}/{leaf}" if leaf != "files" else f"{src}/files/.gitkeep") \
           and leaf == "files":
            # `git cat-file` cannot test a directory; fall back to a tree probe.
            r = _sp.run(["git", "ls-tree", "--name-only", f"{BASE}:{src}"],
                        capture_output=True, text=True)
            if "files" not in r.stdout.split():
                continue
        if carried:
            continue
        token = f"{gone}/evals/{leaf}"
        if not dropped_with_reason(token):
            problems.append(
                f"{token} neither carried into content-design/evals/ nor dropped with a reason; "
                f"verification-ledger.md needs a line '{token}: dropped - <reason, 20+ chars>'"
            )
if problems:
    sys.exit("EVAL HARNESS DISPOSITION\n  " + "\n  ".join(problems))
print("eval harness: every source file carried or dropped with a recorded reason")
QQ
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

**No removed name survives inside the surviving skill — as a registration or a
path, never as the `type:` literal.** A bare `grep -nE "$REMOVED"` over
`$CD/SKILL.md` is **mutually exclusive** with the discriminator block above,
which requires seven `type: tone-of-voice` occurrences in that same file: the
literal contains the bare name, so "want no output" and "want 7" cannot both
hold. Match registration and path position only:

```bash
grep -nE '(skills/(copy-direction|tone-of-voice))|(`(copy-direction|tone-of-voice)`[^:])|((copy-direction|tone-of-voice) skill)' \
  "$CD/SKILL.md" "$CD/references/communication-modes.md"   # want no output
# Then read the remaining bare-name hits and classify them; the count of
# `type: tone-of-voice` occurrences is asserted separately above.
grep -nE "$REMOVED" "$CD/SKILL.md" "$CD/references/communication-modes.md" \
  | grep -v 'type: tone-of-voice'   # want no output
```

**Skill counts — negative and positive, cardinal and ordinal:**

Four numerals across three files, in three different constructs. `docs/index.md`
carries **two** — a prose line and a heading — so a single `grep -q '12 skills'`
leaves the heading stale. `README.md` and `JOURNEY.md` carry no skill-count
numeral at all, so the positive check is replaced there by a negative one:

```bash
grep -rnoE '\b(14|fourteen|fifteenth)\b' \
  packs/experience-design/docs/index.md \
  guides/experience-design/reference/experience-design.md \
  web/src/content/packs/experience-design.md          # want no output after the fold
grep -q 'pack of 12 skills' packs/experience-design/docs/index.md
grep -qF '**Skills (12) in two families:**' packs/experience-design/docs/index.md
# The literal is the whole line: the closing `**` follows `families:`, not the
# parenthesised count, so `'**Skills (12)**'` matches nothing in a correct file.
grep -q '12 pure-Markdown skills' guides/experience-design/reference/experience-design.md
grep -q 'thirteenth skill' web/src/content/packs/experience-design.md   # ordinal: counts the reviewer agent last
# README and JOURNEY hold no count today and must not acquire a stale one:
! grep -rnoE '\b(1[0-9]|20|twelve|fourteen|twenty)\b.{0,12}skills?\b' \
  packs/experience-design/README.md packs/experience-design/JOURNEY.md
# Readings, 2026-09-25 (pre-genre-fold): "pack of 20 skills" (index.md:3),
# "**Skills (20) in two families:**" (index.md:11), "20 pure-Markdown skills"
# (guides:17), "twenty-first skill" (web:69). The genre fold lands first and
# takes each to its 14-skill form; this delivery edits that form.
```

**The sibling brief's rows are restated, not merely absent.** An absence check
cannot distinguish a full restatement from a deletion:

The absence half must be written `! grep -q`: a bare `grep -q` returns exit 1 on
the *wanted* outcome, so under `set -e` or any harness reading the block's exit
status the passing path reports failure and the positive checks below never run.
The stale figure also appears **twice** in the brief — line 68's re-check row and
line 81's "the 31/24 measurement" — so both are checked:

```bash
B=docs/product/briefs/digital-experience-doctrine-completion.md
! grep -q '31 files' "$B"                       # line 68's headline
! grep -q '31/24' "$B"                          # line 81's second occurrence
! grep -q 'eight duplicate-basename families' "$B"
# The positive half reads the regenerator, not a literal. Every figure the brief
# now states must appear in the post-fold run's output, and the headline count
# must match it exactly:
python3 - "$B" <<'QQ'
import collections, hashlib, pathlib, re, sys
SKILLS = pathlib.Path("packs/experience-design/.apm/skills")
fam = collections.defaultdict(list)
for path in sorted(SKILLS.glob("*/references/*.md")):
    fam[path.name].append(path)
fam = {n: ps for n, ps in fam.items() if len(ps) > 1}
files = sum(len(ps) for ps in fam.values())
hashes = sum(len({hashlib.sha256(p.read_bytes()).hexdigest() for p in ps}) for ps in fam.values())
brief = pathlib.Path(sys.argv[1]).read_text()
# The brief writes short labels, not basenames. One canonical mapping, here, so a
# semantically correct restatement in the brief's own vocabulary passes.
# Run POST-fold. Pre-fold it reports the four pairs as missing, because the brief
# summarises them as "four other pairs 2/2" rather than naming each; post-fold
# those four families have left the inventory, so `want` holds only the surviving
# rows — layout, containment, editorial gates, interrogation — plus the totals.
LABEL = {
    "containment.md": "containment",
    "agentbundle-layout.md": "layout",
    "editorial-quality-gates.md": "editorial gates",
    "interrogation-sequence.md": "interrogation",
    "copy-arbitration.md": "copy arbitration",
    "copy-grounding.md": "copy grounding",
    "plain-language-floor.md": "plain-language floor",
    "audience-jtbd.md": "audience jtbd",
    "copy-jtbd.md": "copy jtbd",
}
WORDS = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five",
         6: "six", 7: "seven", 8: "eight", 9: "nine", 10: "ten"}
flat = re.sub(r"\s+", " ", brief)
want = [f"{files} files", f"{hashes} hashes"]
for name, ps in sorted(fam.items()):
    h = len({hashlib.sha256(q.read_bytes()).hexdigest() for q in ps})
    label = LABEL.get(name, name[:-3])
    want.append(f"{label} {len(ps)}/{h}")
missing = [w for w in want if w not in flat]
# The family count itself, in either cardinal or word form — the brief writes
# "eight duplicate-basename families" today, so the word form is the likely one.
n = len(fam)
if f"{n} duplicate-basename families" not in flat and f"{WORDS.get(n, n)} duplicate-basename families" not in flat:
    missing.append(f"the family count ({n} / {WORDS.get(n, n)})")
if missing:
    sys.exit("brief does not restate the regenerated figures: " + "; ".join(missing))
print(f"brief agrees with the regenerator: {n} families, {files} files, {hashes} hashes")
QQ
```

**The family figures come from a regenerator, not a pinned table.** An inventory
of what a change invalidates cannot be a snapshot: deleting the two skill
directories is exactly what makes such a table stale, and this one was wrong once
already — an earlier draft counted three of the four pairs as leaving and
reported five surviving families instead of four. The block below is the single
home for the *measurement*. Run it before the fold and after; the brief's rows
are checked against its output. The spec's criterion does restate the figures so
it reads on its own — that is a contract value, not a second measurement — and
the regenerator is what decides a disagreement between them. Saying the spec
"carries no literal" would be the overclaim this block exists to prevent.

```bash
python3 - <<'QQ'
import collections, hashlib, pathlib
SKILLS = pathlib.Path("packs/experience-design/.apm/skills")
fam = collections.defaultdict(list)
for path in sorted(SKILLS.glob("*/references/*.md")):
    fam[path.name].append(path)
fam = {n: ps for n, ps in fam.items() if len(ps) > 1}
files = hashes = 0
for name, paths in sorted(fam.items()):
    h = {hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    files += len(paths); hashes += len(h)
    print(f"{name[:-3]:<28} {len(paths):>2} files / {len(h)} hashes  "
          + ", ".join(p.relative_to(SKILLS).parts[0] for p in paths))
print(f"\n{len(fam)} duplicate-basename families, {files} files, {hashes} hashes")
QQ
```

Run against the pre-fold tree on 2026-09-25 it prints **8 duplicate-basename
families, 31 files, 24 hashes**, reproducing the figure the sibling brief records
— which is what establishes the block measures the thing the brief measured. The
post-fold run is what the brief's amended rows must restate, sub-count by
sub-count. The expected post-fold shape, derived from what this delivery does
rather than pinned as a target: `containment` untouched; `agentbundle-layout`
loses the two deleted directories; `editorial-quality-gates` and
`interrogation-sequence` each reconcile two copies into one; and all four pairs
— `copy-arbitration`, `copy-grounding`, `plain-language-floor` and
`audience-jtbd` — drop to a single copy and leave the inventory entirely.
`audience-jtbd` is the one an earlier draft missed: `copy-direction`'s instance
merges into `copy-jtbd.md`, so only `creative-direction`'s keeps the basename.

**Versions — pack-scoped and labelled.** `grep -h version` is unusable: it strips
filenames, matches the adapter-contract stanza, and matches the substring inside
`conversion-design`:

`product-engineering`'s target is **derived from the merge-base, not literal.**
An earlier draft wrote `0.13.17 → 0.13.18`; the pack reached `0.13.18` on its own
before approval, so both the criterion and this check passed against an untouched
tree and the obliged bump could have been skipped in silence. Read the base and
compute:

The block **computes and asserts**; it does not print two numbers and leave the
comparison to the reader. It covers all three surfaces per pack — `pack.toml`,
`.claude-plugin/plugin.json` and the projection — because the Agent Rule requires
the first two to move in one edit and an earlier draft checked
`product-engineering`'s `plugin.json` nowhere at all:

```bash
# BASE comes from the guarded derivation at the top of this map — it carries the
# emptiness check, which this block needs more than any other: it is the only one
# that computes a number from BASE. With BASE empty, `git show ":<path>"` resolves
# to the INDEX, not the merge-base, so the target would be derived from staged
# content and the block would print "versions agree" against a base it never read.
[ -n "$BASE" ] || { echo "BASE unset — run the roots block first"; return 1 2>/dev/null || exit 1; }
python3 - "$BASE" <<'QQ'
import json, subprocess, sys, tomllib
base = sys.argv[1]
def toml_at(rev, path):
    out = subprocess.run(["git", "show", f"{rev}:{path}"], capture_output=True, text=True, check=True).stdout
    return tomllib.loads(out)["pack"]["version"]
def toml_now(path):
    return tomllib.load(open(path, "rb"))["pack"]["version"]
def plugin(path):
    return json.load(open(path))["version"]

targets = {}
# experience-design is a fixed contract value: 2.0.10 -> genre 3.0.0 -> 4.0.0.
targets["packs/experience-design"] = "4.0.0"
# product-engineering is derived: exactly one patch above the merge-base.
was = toml_at(base, "packs/product-engineering/pack.toml")
a, b, c = (int(x) for x in was.split("."))
targets["packs/product-engineering"] = f"{a}.{b}.{c + 1}"

fail = []
for m, want in targets.items():
    for label, got in (("pack.toml", toml_now(f"{m}/pack.toml")),
                       ("plugin.json", plugin(f"{m}/.claude-plugin/plugin.json"))):
        if got != want:
            fail.append(f"{m}/{label}: want {want}, got {got}")
proj = {p["name"]: p["version"] for p in json.load(open(".claude-plugin/marketplace.json"))["plugins"]}
for m, want in targets.items():
    name = m.split("/")[-1]
    if proj.get(name) != want:
        fail.append(f"marketplace.json[{name}]: want {want}, got {proj.get(name)}")
if fail:
    sys.exit("VERSION MISMATCH\n  " + "\n  ".join(fail))
print("versions agree:", targets)
QQ
```

Pre-state readings, 2026-09-25: `experience-design` `2.0.10`,
`product-engineering` `0.13.18`. An earlier draft recorded `2.0.9` and `0.13.17`.
The `4.0.0` arithmetic is unaffected, but a stale reading defeats the stated
purpose of recording readings at all — telling a broken command from a failing
check.

**The remaining goal-based criteria**, which an earlier draft left with no entry
in this map at all. The last two are structural reads rather than greps; the map
still names what the read must show, so a reviewer can execute them:

```bash
! grep -nE "$REMOVED" workspace.toml
! grep -nE "$REMOVED" tools/add-rendering-directives.py
! grep -nE "$REMOVED" packs/agent-skill-engineering/tests/fixtures/skill-census.json
python3 -m pytest tests/roster/test_skill_census.py -q

# The changelog entry: a free-standing `##` heading directly beneath the
# `[Unreleased]` section rather than nested inside it, naming both removed skills.
# `tools/build-site.py` fails closed on a nested entry — it withholds it as
# unreleased and still exits 0 — so the site build cannot serve as this check.
grep -n '^## \[experience-design\]\[4\.0\.0\]' docs/product/changelog.md
# A `/start/,/^## /` range is WRONG here: awk tests the end pattern against the
# record that opened the range, the heading matches `^## ` itself, and the range
# collapses to that one line — so a correct entry scores 0. Skip the opener, then
# stop at the next `## `:
# Parse once and assert placement, date and BOTH entries. An earlier draft found
# the heading anywhere, checked no date, and had no product-engineering check at
# all, while T10 promises two entries.
python3 - "$BASE" <<'QQ'
import json, pathlib, re, subprocess, sys, tomllib
base = sys.argv[1]
lines = pathlib.Path("docs/product/changelog.md").read_text().splitlines()
heads = [(i, l) for i, l in enumerate(lines) if l.startswith("## ")]
want_pe = None
out = subprocess.run(["git","show",f"{base}:packs/product-engineering/pack.toml"],
                     capture_output=True, text=True, check=True).stdout
a, b, c = (int(x) for x in tomllib.loads(out)["pack"]["version"].split("."))
want_pe = f"{a}.{b}.{c+1}"
fail = []
idx = {}
for n, (i, l) in enumerate(heads):
    m = re.match(r"## \[(?P<pack>[a-z-]+)\]\[(?P<ver>[0-9.]+)\] — (?P<date>\d{4}-\d{2}-\d{2})\s*$", l)
    if m:
        idx[(m.group("pack"), m.group("ver"))] = (n, i, m.group("date"))
unrel = next((n for n, (i, l) in enumerate(heads) if l.startswith("## [Unreleased]")), None)
if unrel is None:
    fail.append("no [Unreleased] heading")
for pack, ver in (("experience-design", "4.0.0"), ("product-engineering", want_pe)):
    if (pack, ver) not in idx:
        fail.append(f"no well-formed dated heading '## [{pack}][{ver}] — YYYY-MM-DD'")
if not fail:
    n_xd, i_xd, _ = idx[("experience-design", "4.0.0")]
    if n_xd != unrel + 1:
        fail.append("the experience-design entry is not the heading directly beneath [Unreleased]")
    end = heads[n_xd + 1][0] if n_xd + 1 < len(heads) else len(lines)
    body = "\n".join(lines[i_xd + 1:end])
    for name in ("copy-direction", "tone-of-voice"):
        if name not in body:
            fail.append(f"the experience-design entry does not name {name}")
if fail:
    sys.exit("CHANGELOG\n  " + "\n  ".join(fail))
print("changelog: both dated entries present, experience-design directly beneath [Unreleased], both removed skills named")
QQ

# The two errata: present, dated, approver-signed, naming no spec and no brief.
# Layer cannot separate the new entry from the inherited one. RFC-0055 D2 makes
# `### Current state` the authoritative TABLE of corrections in force and
# `### History / audit trail` the DATED ENTRIES — so the entry this delivery
# writes and RFC-0062's inherited 2026-08-02 entry both live in History. The
# separator is the diff: scan only the lines this delivery ADDS.
# BASE comes from the guarded derivation at the top of this map.
for R in docs/rfc/0062-content-design-and-copy-direction-skills.md \
         docs/rfc/0071-digital-experience-doctrine.md; do
  # Two-layer presence, bounded to the `## Errata` section — RFC-0071 carries
  # `### Area A`–`### Area F` under `## Proposal`, so a whole-file grep passes
  # on headings that are not errata layers at all.
  err() { awk -v f=0 '/^## Errata/{f=1;next} f&&/^## /{exit} f' "$1"; }
  err "$R" | grep -q '^### Current state' && err "$R" | grep -q '^### History' \
    || echo "$R: Errata section not in RFC-0055 D2 two-layer form"
  # Delivery artifacts, in every form the Never-do rule forbids: path, `brief:`
  # prefix, and bare slug.
  # Two tiers, because a bare slug is ambiguous. RFC-0071's `## Implementation
  # sequence` lists its items as `spec/xd-copy-direction`, `spec/xd-skill-
  # boundaries` and so on, and the criterion obliges an erratum to correct that
  # ordering dependency — which means naming the item it amends. A scan that
  # hard-fails on any `xd-*` slug would fail the line the spec requires.
  #
  # Tier 1, hard failure: citation forms — a path into the spec or brief tree, or
  # a reference-grammar prefix. These cite a delivery artifact as authority,
  # which is what the rule forbids.
  git diff "$BASE" -- "$R" | grep '^+' | grep -vE '^\+\+\+' \
    | grep -nE 'docs/specs/|docs/product/briefs/|brief:[a-z-]|spec:[a-z-]' \
    && echo "$R: FAIL — a new erratum line cites a delivery artifact"
  # Tier 2, report for classification: a bare slug, which may be a legitimate
  # reference to a sequence item this erratum corrects, or may be a citation
  # wearing no prefix. The bounded-reads row for the errata is where the verdict
  # is recorded; this prints the candidates rather than judging them.
  git diff "$BASE" -- "$R" | grep '^+' | grep -vE '^\+\+\+' \
    | grep -nE '\bxd-[a-z-]+\b|creative-direction-modes|experience-design-skill-consolidation' \
    && echo "$R: CLASSIFY — bare slugs above; a sequence item being corrected is allowed, a citation is not"
done
# The inherited 2026-08-02 entry cites a spec path twice and moves into
# `### History` unchanged; it is not an added line, so the diff scan never sees
# it. The rule binds what this delivery writes, not what it inherits.

# DESIGN.md § 4 and `xd-state-reviewer-doctrine.md` are read, not grepped.
# § 4 must read as mode selection within one skill plus the one surviving
# cross-pack boundary; the doctrine intent must either carry an edit in this
# delivery's diff or a ledger line recording it confirmed unaffected.
! grep -nE "$REMOVED" packs/experience-design/DESIGN.md packs/product-engineering/DESIGN.md
git diff --name-only "$BASE" -- docs/product/intents/xd-state-reviewer-doctrine.md
grep -n 'xd-state-reviewer-doctrine' docs/specs/xd-copy-router/notes/verification-ledger.md
# want: a hit from one of the two, not neither.
```

**The criteria whose check is a bounded read, not a grep.** Each is goal-based
and each had no map entry at all in an earlier draft, which the Testing Strategy
claim then declared a spec defect. The check is stated as what the read must
show, so a reviewer can execute it and record a verdict:

| Criterion | The read, and what it must show |
| --- | --- |
| Mode-selection rubric decidable without loading a reference | `$CD/SKILL.md`: the rubric cites no `references/` path, and each branch names one of the three literal mode names |
| Each mode states what it produces, where it lands, what it must not do | `$CD/SKILL.md`: three mode sections, each with all three statements present |
| Content brief keeps its path and `type: content-brief` | `grep -q 'type: content-brief' "$CD/assets/content-brief-template.md"` and the path literal in `SKILL.md` |
| Three legacy-1.x migration prompts survive | `$CD/SKILL.md`, owned by **T5**, which edits that file — T4 reaches only `references/` and the note. The three conditions, each matched by its own string carried over from the folded body: `type: tone-of-voice` found at a per-surface slug; `type: tone-of-voice` without `scope: brand-level`; and user-profile `output_dir` cross-brand confirmation |
| Three-branch `type:`-collision handling survives | `$CD/SKILL.md`: three branches, each naming its condition and its action |
| JTBD pair's full difference enumeration | `notes/reference-reconciliation.md`: a row per substantive difference, each classified clause / winner / drop. The unit is neither the line nor, strictly, the hunk. The pre-fold `diff` has **10 hunks** (`1c1 7c7 13c13 15c15 19c19 21c21 23,24d22 27c25 30,31c28,29 40c38`) across **22 changed lines** counting both sides. Counting rows against 22 fails a correct note and passes a padded one. Ten hunks is the **enumeration's starting point, not a minimum**: adjacency is textual, so `13c13`/`15c15` may be one substantive difference and `30,31c28,29` plainly is, and a correct note may hold fewer than ten rows. The reviewer's obligation is to account for each of the ten hunks — folded into a row, or named as not substantive — not to hit a count |
| Per-file reconciliation record | `notes/reference-reconciliation.md`: six named files, each with winner, differences, reason |
| Brand-naming verdict | the same note: which convention wins, `[example service]` or real company names |
| Three-way editorial verdict | the same note: which gating condition survives, `conversion-design`'s or `copy-direction`'s upstream-`communication_mode` form |
| Autonomy-note removal has an owning `Touches:` | T3's `Touches:` names `information-architecture/references/editorial-quality-gates.md`; grep that the note is absent from both surviving copies |
| Pooled `eval_queries.json` negatives | `$CD/evals/eval_queries.json`: every folded positive present, plus ≥ 1 `ux-writing` and ≥ 1 `creative-direction` negative. Compare against `git show "$BASE:…/copy-direction/evals/eval_queries.json"` and the `tone-of-voice` equivalent — **at the merge-base**, as T2 does: T6 deletes both files, so a `HEAD` comparison has nothing to read and passes vacuously |
| Install/update observation and adopter action | `notes/verification-ledger.md` carries the observed behaviour; the changelog carries the manual step if stale directories persist |
| Two errata's content requirements | RFC-0062: three registrations → one, three output contracts unchanged, the 2026-08-02 reservation survives. RFC-0071: its own entry, the post-fold skill count stated as **12**, and an explicit clause recording that it **supersedes** the 2026-08-02 erratum that set the same count to 20. An entry that restates the number without the supersession fails this read |
| The three `experience-reviewer.md` criteria | that file: the sync citation resolves to a path that exists; the exclusion clause names an artifact `type:`; `Does NOT fire on` names only surviving skills or types |
| Four manual-QA verdicts | `notes/verification-ledger.md`: four verdicts, each with reviewer name and date |

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

Every Durable Output in `spec.md` has a row, and every task has at least one.
An earlier draft's body carried three cells against this four-column header, left
`Closeout evidence` empty throughout, omitted four of the spec's Durable Outputs,
and named neither T2 nor T7a.

| Durable output | Destination | Tasks | Closeout evidence |
| --- | --- | --- | --- |
| Activation baseline + abort path | `notes/activation-baseline.md` | T1, T9 | Both figures ≥ baseline; the abort path names both triggers and `eugenelim` |
| Genre-fold precondition | `notes/verification-ledger.md` | T2 | The relocated file exists, is byte-identical at the merge-base, and is cited |
| Reconciliation record | `notes/reference-reconciliation.md` | T3, T4 | Six files, each with a winner, a clause, or a recorded drop and its reason |
| Shared-reference integrity | `content-design/` + `information-architecture/` | T3, T5 | The byte-equality extension is GREEN and both `SKILL.md` files cite the file |
| Merged skill (current product truth) | `CD/` | T5 | Three modes, three assets, all output contracts; `lint-experience-agnostic` exits 0 |
| Eval harness | `content-design/evals/` | T5, T6 | Pooled positives and negatives; `evals.json` and `files/` carried or the drop recorded |
| Two directories removed | `packs/experience-design/.apm/skills/` | T6 | Directory count 12, every directory declared, no undeclared stub |
| Reviewer + cross-pack | `.apm/agents/experience-reviewer.md`, `packs/product-engineering/**` | T7 | The sync citation resolves; the exclusion clause names an artifact `type:` |
| Sibling brief rows | `docs/product/briefs/digital-experience-doctrine-completion.md` | T7 | Both stale occurrences gone; 4 families / 19 files / 11 hashes present |
| Two errata (decision rationale) | RFC-0062, RFC-0071, `DESIGN.md` § 4 | T8 | Two-layer form; neither new entry names a spec or a brief |
| User promise | `guides/experience-design/` | T7a | Guide-agreement test passes and a named reviewer judges the guide sufficient |
| Registry + projection surfaces | `workspace.toml`, `skill-census.json`, `tools/add-rendering-directives.py` | T7a | Census suite passes; no removed name in any of the three |
| Public site truth | `web/src/content/` | T7 | Frontmatter, `whatChanges` and stage prose updated; `npm run build` exits 0 |
| Versions + release history | manifests, `.claude-plugin/marketplace.json`, changelog | T10 | All three surfaces agree per pack; both catalogue commands exit 0 |
| Manual-QA verdicts | `notes/verification-ledger.md` | T11 | All four verdicts with reviewer and date, plus the install observation |

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
set from **citation** in a *different* test than the one this delivery extends —
and that test runs citation → copy, so it cannot fail on a copy nothing cites.
Both `SKILL.md` files must therefore cite the file as a stated obligation held by
a grep, not as something the suite would catch.

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
  be measured. The revert set is T3–T8 **including T7a**, plus T10's manifest
  and changelog edits when the window-elapsed trigger fires after T10 has run.
- It names both triggers, the no-partial-fold residue, and `eugenelim`.

**Done when:** the file carries both sets and the abort path.

**Touches:** docs/specs/xd-copy-router/notes/activation-baseline.md

### T2: The genre fold's post-condition is verified, not assumed

**Depends on:** spec:xd-genre-router/T3

**Tests:**
- `information-architecture/references/editorial-quality-gates.md` exists and is
  byte-identical to the `conversion-design` original **at the merge-base**, not
  at `HEAD`: by the time this slice runs the genre fold has deleted that
  directory, so a `git show HEAD:` comparison fails with "path does not exist"
  and reads as "bytes differ".
- `information-architecture/SKILL.md` cites it.

**Approach:** the `Depends on:` value is the cross-spec marker
`spec:xd-genre-router/T3`, kept to a bare single-line value so `loop-cohort`
parses it — `TOUCHES_LINE_RE` and `DEPENDS_LINE_RE` are `^\*\*Field:\*\*\s*(.+)$`
under `re.MULTILINE`, so a wrapped field silently drops everything after its
first line and still prints a clean DAG. An earlier draft wrapped this one and
an earlier draft before that said `none`, which hid the sequencing entirely.

This is a precondition gate, run before any reconciliation. If either fails
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
- The byte-equality extension lands in
  `tests/roster/test_experience_design_write_declaration_and_containment.py` as a
  new `test_every_editorial_quality_gates_copy_is_byte_identical`, carrying the
  existing `len(copies) >= 2` vacuity guard. Extending the existing suite avoids
  the three further guarded edits `tests/AGENTS.md` obliges for a new
  `tests/roster/test_*.py`.

**Approach:** the classification is the decision, so it is recorded per file
before the rewrite rather than inferred from the result. `copy-arbitration.md`
diverges on every paragraph and carries an extra section on one side; it is the
case the rule exists for.

**Done when:** every pervasive pair has a scope-parameterised body and a recorded
verdict.

**Touches:** packs/experience-design/.apm/skills/content-design/references/, packs/experience-design/.apm/skills/information-architecture/references/editorial-quality-gates.md, tests/roster/test_experience_design_write_declaration_and_containment.py, docs/specs/xd-copy-router/notes/reference-reconciliation.md

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
- The merged `description` is **at most 1024 characters**. `skill_spec_lint.py`
  raises an error above that, not a warning, and the three sources total 2,273
  (769 + 732 + 772), so roughly 55% must compress away. This is the delivery's
  one hard-gated numeric constraint and an earlier draft of this plan left it
  owned by no task.
- All three assets land under `content-design/assets/`:
  `content-brief-template.md` stays, `copy-direction-template.md` and
  `tone-of-voice-template.md` move here from the directories T6 deletes. Each
  mode writes through its template, so a template lost with its directory breaks
  the output contract while every name-based check stays green.
- All three output paths and `type:` values unchanged; the brand register emits
  `type: tone-of-voice` **and** `scope: brand-level`.
- The pooled `evals/` harness carries `eval_queries.json`, `evals.json` and the
  `evals/files/` fixture tree, or the drop is recorded with its reason.
- The `brand-register` slug refusal survives (manual QA, ledger).
- The three legacy-1.x migration prompts and the three `type:`-collision branches
  survive.
- `content-design/SKILL.md` cites `references/editorial-quality-gates.md`.
- Neither removed name survives inside the surviving skill: five lines of
  `content-design/SKILL.md` and one of `references/communication-modes.md` name
  them today, and this is the task that edits both.

**Done when:** every mechanical test passes and `lint-experience-agnostic` exits 0.

**Touches:** packs/experience-design/.apm/skills/content-design/**, packs/experience-design/.apm/skills/copy-direction/assets/copy-direction-template.md, packs/experience-design/.apm/skills/tone-of-voice/assets/tone-of-voice-template.md

### T6: The two registrations are gone

**Depends on:** T5

**Tests:**
- Both directories absent; every surviving `.apm/skills/` directory is declared
  in `pack.evals.skills` and the two sets are equal at **twelve** — membership,
  not length, and a check that a stub under a third name fails.
- Neither removed name is declared; `content-design` is.
- No removed name survives **as a registration** within the stated scope — the
  five trees, `workspace.toml`, and the five `docs/` files this delivery edits.
  Every surviving hit is a discriminator use on the protected list.
- The two directories' `evals/evals.json` and `evals/files/` are carried into
  `content-design/evals/` or their drop is recorded with a reason in
  `notes/verification-ledger.md`. Neither asset dies unremarked with its
  directory.
- Both templates have already moved under T5; this task confirms nothing under
  `assets/` is lost with the deletion.

**Done when:** the two sets are equal at twelve, the registration grep is empty,
and the harness disposition is recorded.

**Approach:** `packs/AGENTS.md` § Security and authoring rules obliges a
non-cosmetic pack update to update the pack's eval harness, and `skill_spec_lint`
cross-checks `pack.evals.skills` against `eval_queries.json` only — so a vanished
`evals.json` leaves `catalogue lint --deep` green. The disposition is therefore
stated here rather than inferred from a passing gate.

**Touches:** packs/experience-design/.apm/skills/, packs/experience-design/pack.toml

### T7: Reviewer, cross-pack and sibling-brief surfaces are consistent

**Depends on:** T6

**Tests:**
- `experience-reviewer.md`'s sync citation resolves; its `Does NOT fire on` list
  names surviving skills or artifact types.
- `xd-state-reviewer-doctrine.md` is updated or recorded confirmed unaffected.
- `ux-writing/SKILL.md`'s `tone-of-voice step 6` pointer is retargeted while its
  **three** discriminator literals stay — the measured count, all on one line;
  `product-engineering/DESIGN.md` updated.
- `digital-experience-doctrine-completion.md`'s re-check and Adjacent-work rows
  carry the **full** post-fold row — every sub-count, new file/hash totals, and
  eight families becoming **four**: 19 files / 11 hashes, containment 5/1, layout
  10/7, editorial gates 2/1, interrogation 2/2. Both stale occurrences of the
  31/24 figure are amended, line 68's and line 81's.
- `DESIGN.md` §4 rewritten as mode selection; no removed slug pack-wide.
- Astro build exits 0; census fixture matches.

**Done when:** the sibling row reads post-fold and the site builds.

**Touches:** packs/experience-design/**, packs/product-engineering/**, docs/product/briefs/digital-experience-doctrine-completion.md, docs/product/intents/xd-state-reviewer-doctrine.md, web/src/content/**

### T7a: The guide tree and the three registry surfaces are consistent

**Depends on:** T6

**Tests:**
- `guides/experience-design/how-to/copy-boundary.md` describes mode selection
  within one skill.
- Every skill-count numeral reads its post-fold form, checked **per numeral**:
  `guides/…/reference/experience-design.md` "12 pure-Markdown skills" (reads "20"
  today, 14 after the genre fold), and `packs/experience-design/docs/index.md`'s
  **two** numerals — the prose line and the `**Skills (N)**` heading. Checking
  only the prose line leaves the heading stale.
- `README.md` and `JOURNEY.md` carry no skill-count numeral today and acquire
  none; their obligation is naming the surviving skill set, not a count.
- `workspace.toml` carries no removed skill name.
- `packs/agent-skill-engineering/tests/fixtures/skill-census.json` matches, and
  `tests/roster/test_skill_census.py` passes.
- `tools/add-rendering-directives.py`'s per-skill map carries neither removed
  name.

**Approach:** split out because T7's `Touches:` covered neither `tools/`, nor
`packs/agent-skill-engineering/**`, nor the repo-root `workspace.toml`, while
three acceptance criteria name them.

**Done when:** the census suite passes and the guide count is correct.

**Touches:** guides/experience-design/**, packs/experience-design/docs/index.md, packs/experience-design/README.md, packs/experience-design/JOURNEY.md, workspace.toml, tools/add-rendering-directives.py, packs/agent-skill-engineering/tests/fixtures/skill-census.json

### T8: RFC-0062 and RFC-0071 record what no longer holds

**Depends on:** T6

**Tests:**
- RFC-0062: a dated, approver-signed entry recording three registrations becoming
  one, all three output contracts unchanged, and the 2026-08-02 reservation
  surviving.
- RFC-0071: its own entry, stating the post-fold skill count as **12** and
  recording explicitly that it **supersedes** the 2026-08-02 erratum, which
  set that same count to 20. Restating the number without the supersession
  leaves two errata asserting different counts with nothing ranking them.
- Neither **new** entry names a spec or a brief; RFC-0062's frozen 2026-08-02
  entry keeps its spec path and moves to `### History` unchanged.
- Both sections in RFC-0055 D2's two-layer form.

**Done when:** both entries exist in two-layer form and cite no delivery artifact.

**Touches:** docs/rfc/0062-content-design-and-copy-direction-skills.md, docs/rfc/0071-digital-experience-doctrine.md, packs/experience-design/DESIGN.md

### T9: The post-fold activation figure clears the gate

**Depends on:** T5, T6

**Tests:**
- Same command, CLI version and model as T1; positive and negative figures both
  ≥ baseline.

**Done when:** both clear. If either fails, nothing in this slice ships and
T3–T8 revert.

**Touches:** docs/specs/xd-copy-router/notes/activation-baseline.md

### T10: The release is registered

**Depends on:** T7, T7a, T8, T9

**Tests:**
- `experience-design` reads `4.0.0` in both manifests **and** in the regenerated
  `.claude-plugin/marketplace.json` entry, read as JSON — the projection is a
  third surface and an earlier draft checked only the two source manifests.
- `product-engineering` reads exactly **one patch above its merge-base value** in both, and in the projection. The 2026-09-25 reading is `0.13.18`, so the target is `0.13.19` unless the base has moved; the target is derived at execution time, never copied from here.
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
