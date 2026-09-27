# Plan: One copy-layer skill with three modes

- **Spec:** [`spec.md`](spec.md)
- **Status:** Approved <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `packs/AGENTS.md` (§ Version bump rule; § Authoring or editing a skill); `tests/AGENTS.md` (the three guarded edits a **new** `tests/roster/test_*.py` owes, which this plan avoids by extending an existing suite); `tests/roster/test_experience_design_write_declaration_and_containment.py` — specifically `test_every_containment_copy_is_byte_identical`, which globs `*/references/containment.md` off the filesystem and is the pattern this delivery reuses, and separately `test_every_skill_citing_the_module_ships_its_own_copy`, which is the citation-derived one and runs citation → copy, so neither can fail on a copy that nothing cites; two analogous multi-mode skills — `packs/core/.apm/skills/project-knowledge/` (capture / distill / enquire behind one description) and `packs/core/.apm/skills/author-delivery-brief/` (create / continue); the accepted `xd-genre-router` routing-classification evidence and static-corpus approach. Named uncertainties: the pervasive-versus-localized divergence classification has no repository precedent and is authored here as a judgement with a recorded verdict; the bounded Codex probe is a description-level decision input, so production activation remains unmeasured.

> **Plan contract:** this is the implementation strategy. It may change
> substantively only while its Status is `Drafting`. After approval, `spec.md`
> and `plan.md` are pinned in substance; execution observations belong in
> `notes/verification-ledger.md`.

## Approach

Three registrations become one skill with three modes. Unlike the genre fold,
almost none of the work is moving method — it is **reconciling six pairs of files
that share a name and disagree**, and doing it without silently picking a winner.

Order is forced three ways. The bounded 18-call routing-classification probe
runs first, before any deletion (T1), over the current descriptions and one
exact post-fold candidate. The reconciliations happen before the merge (T3–T4),
because a merged skill built on an unreconciled pair bakes in whichever variant
was pasted first. And the whole slice is blocked behind the genre fold landing
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
  0.13.18` constraint came to be satisfied by an untouched tree, and it reached
  `0.13.19` on `origin/main` before this delivery started, which would have done
  the same to a `0.13.19` literal.
  `frontend-engineering` takes no **bump**: it names neither removed skill. It
  does move in the **projection**, which is a different surface — see the
  inherited-red note under Construction tests.
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

**One gate arrives red, and T10 is what clears it.** This delivery inherits an
out-of-date self-host projection: `.claude-plugin/marketplace.json` reads
`experience-design 2.0.9` against a `pack.toml` of `3.0.0`, and
`frontend-engineering 0.3.2` against `0.3.3`. Neither is this delivery's doing —
the genre fold and the frontend repair both bumped a manifest without committing
a regenerated projection. `agentbundle catalogue verify` therefore fails before
this delivery changes anything, and it keeps failing until T10 regenerates the
projection. Read a pre-T10 `catalogue verify` failure as this inherited state,
not as a defect this slice introduced, and confirm the reported mismatch names
only those two entries before continuing — a third name is a real finding. This
is the same expected-pre-state record the pytest exit-5 note carries below.

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
# "Untouched" is a content claim, not an existence one: an arbitrary rewrite
# passes a `test -f`. Compare against the guarded merge-base.
git diff --quiet "$BASE" -- packs/experience-design/.apm/skills/creative-direction/references/interrogation-sequence.md \
  || echo "creative-direction's interrogation-sequence.md was MODIFIED — the spec refuses to touch it"
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
  -q -k every_editorial_quality_gates_copy_is_byte_identical
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

**The per-surface copy direction keeps its marker and its path.** This block is
the entry the `type: copy-direction` output-contract criterion owed and did not
have: the assets block above tests only that the relocated template exists, and
an empty file passes a `test -f`. Both halves are checked, because the criterion
names both — the `type:` the template emits, and the path the mode writes:

```bash
grep -q 'type: copy-direction' "$CD/assets/copy-direction-template.md" \
  || echo "the relocated copy-direction template no longer emits type: copy-direction"
grep -q '<output_dir>/copy/<surface-slug>.md' "$CD/SKILL.md" \
  || echo "SKILL.md no longer states the per-surface output path"
# The brand register's reserved path is the sibling literal, and the two must not
# collapse into one another:
grep -q '<output_dir>/copy/brand-register.md' "$CD/SKILL.md" \
  || echo "SKILL.md no longer states the reserved brand-register path"
```

**The discriminator survives, by counted occurrence.** `grep -c` counts *lines*;
these are *occurrences*, so the check must use `grep -o`:

**There are TWO discriminators, not one.** `type: copy-direction` is an artifact
marker the output contract requires to survive, exactly as `type: tone-of-voice`
is, and `$REMOVED` matches it — `copy-direction` is a whole word inside it. An
earlier draft carved out only `type: tone-of-voice`, which left two live
contradictions: the surviving skill's own check below would have flagged the two
`type: copy-direction` literals it inherits as registration violations, and the
final sweep's rubric would have read `experience-status/SKILL.md` and
`derive-the-screen-flow.md` as defects. Both counts were measured 2026-09-26.

```bash
check() { n=$(grep -o "$3" "$1" 2>/dev/null | wc -l | tr -d ' '); [ "$n" = "$2" ] || echo "$1: want $2 of '$3', got $n"; }
TOV='type: tone-of-voice'
CDR='type: copy-direction'
check "$CD/SKILL.md" 7 "$TOV"     # 4 inherited from copy-direction + 3 from tone-of-voice
check "$CD/assets/tone-of-voice-template.md" 1 "$TOV"
check "$CD/evals/evals.json" 2 "$TOV"
check packs/experience-design/.apm/skills/experience-status/SKILL.md 1 "$TOV"
check packs/product-engineering/.apm/skills/ux-writing/SKILL.md 3 "$TOV"
check packs/product-engineering/.apm/skills/ux-writing/evals/evals.json 2 "$TOV"
# The second discriminator. Inherited from copy-direction/ as it folds in:
check "$CD/SKILL.md" 2 "$CDR"
check "$CD/assets/copy-direction-template.md" 1 "$CDR"
check "$CD/evals/evals.json" 2 "$CDR"
# And the two that survive outside the surviving skill:
check packs/experience-design/.apm/skills/experience-status/SKILL.md 1 "$CDR"
check guides/experience-design/how-to/derive-the-screen-flow.md 1 "$CDR"
# The same guide quotes the brand-register template rung, so it holds one
# `type: tone-of-voice` too. An earlier draft listed it under $CDR only,
# which left that occurrence in none of the final sweep's four classes.
check guides/experience-design/how-to/derive-the-screen-flow.md 1 "$TOV"
# copy-direction/references/agentbundle-layout.md holds 3 more and is deleted
# with its directory, the same case as tone-of-voice's copy.
# Those three `ux-writing` discriminators sit on ONE physical line — the same
# line that carries the forbidden pointer "surface the same migration prompt as
# `tone-of-voice` step 6". So the file is a required sweep hit whether or not the
# pointer is retargeted, and the registration sweep, which reports filenames,
# cannot decide it. The step-6 criterion therefore gets the same treatment this
# map already gives `$CD`: remove the discriminator OCCURRENCES, then search what
# is left. `grep -v` would drop the whole line and take the pointer with it.
sed -e 's/type: tone-of-voice//g' -e 's/type: copy-direction//g' packs/product-engineering/.apm/skills/ux-writing/SKILL.md \
  | grep -nE "$REMOVED"   # want no output: the pointer names the surviving mode's step
# Measured 2026-09-26, this returns THREE lines, not one. The step-6 pointer is
# the only one the criteria name; T7 owns all three:
#   :3  the frontmatter description — "(use `tone-of-voice`)"
#   :32 the scope-boundary blockquote and the onboarding tri-point, which name
#       `copy-direction` twice as the skill to use
#   :74 the step-6 migration-prompt pointer, sharing its line with the three
#       required discriminators
# The check is complete even though the prose enumerates a subset, which is why
# it is a command and not a reading.
# tone-of-voice/references/agentbundle-layout.md holds 5 more and is deleted with
# its directory; the Follow-on records that the family shrinks rather than closing
```

**No removed name survives as a registration.** Real alternation. The scope is
the spec's stated scope: the five trees, the repo-root `workspace.toml`, and the
five `docs/` files this delivery edits — **not** `docs/` wholesale. The reason is
what a registration sweep owns, **not** the frozen-record rule: the rest of
`docs/` holds records that *mention* the skills rather than register them. Do
not restore the lifecycle-status justification an earlier draft used here. It
named `xd-genre-router` and `creative-direction-modes` as live counterexamples;
both now read `Shipped`, so a bound resting on their status would have moved
while the bound itself did not. An earlier draft's comment also claimed `docs/`
was in scope while the command omitted it entirely:

```bash
# The five in-scope `docs/` paths are SEPARATE LITERAL ARGUMENTS, and stderr is
# NOT discarded. Both are load-bearing, and an earlier draft got both wrong in a
# way that disarmed this control without failing.
#
# It wrote the five paths as one space-joined scalar and expanded it unquoted.
# bash word-splits that; **zsh does not**, unless SH_WORD_SPLIT is set. So under
# zsh — this repository's shell, and the macOS default — all five paths arrived
# as ONE non-existent argument, `grep` reported `No such file or directory` to
# the stderr that the same line threw away, and the command still exited 0 on
# its `packs/` hits. Measured 2026-09-26 on the same tree: zsh printed 26 files
# and **zero** `docs/` files, bash printed 29 including three `docs/` files, and
# both exited 0. The entire `docs/` half of this delivery's registration scope
# was checked by nothing, including the two RFCs this delivery must amend.
grep -rlE "$REMOVED" packs/ guides/ web/ tools/ tests/ workspace.toml \
  docs/rfc/0062-content-design-and-copy-direction-skills.md \
  docs/rfc/0071-digital-experience-doctrine.md \
  docs/product/briefs/digital-experience-doctrine-completion.md \
  docs/product/intents/xd-state-reviewer-doctrine.md \
  docs/product/changelog.md \
  | grep -vE '\.apm/skills/(copy-direction|tone-of-voice)/' \
  | grep -vF 'web/src/lib/now-highlights.generated.json'
# `now-highlights.generated.json` is excluded: it is generated and gitignored,
# rebuilt from the changelog by every `web/` and `docs-site/` run, so it is not a
# surface this delivery edits and a hit there is noise, not a defect.
# want: only files whose hits are discriminator uses on the counted list above.
# Recorded readings for the five trees + workspace.toml only:
#   27 files pre-genre-fold, 2026-09-25. An earlier draft recorded 28; `git grep`
#   at each of the last five commits also returns 27, so 28 was never a reading
#   and a reviewer comparing against it would chase a phantom one-file delta.
#   26 files post-genre-fold, measured 2026-09-26 once that fold had landed.
#   **26 is this slice's baseline.** An earlier reading of 24 was derived rather
#   than measured, and was wrong in both directions: it assumed the genre fold
#   DELETED conversion-design's SKILL.md, evals/evals.json and
#   editorial-quality-gates.md, when the fold RELOCATED the latter two into
#   `information-architecture`, where they still name a removed skill; and it
#   missed informational-design/evals/evals.json leaving the set entirely.
#   Measured composition of the 26: packs 17, guides 5, web 2, tools 1, tests 0,
#   workspace.toml 1.
#   The `docs/` arm adds THREE more, for 29 printed lines in total, and it needs
#   its own reading for the same reason: without one, a reviewer cannot tell a
#   `docs/` file that stopped matching from an argument list that stopped being
#   passed — which is exactly how the zsh defect above stayed invisible.
#   Reading, 2026-09-26: docs/rfc/0062-… matches, docs/rfc/0071-… matches,
#   docs/product/changelog.md matches; the brief and
#   docs/product/intents/xd-state-reviewer-doctrine.md match nothing yet.
#   NONE of these three is retargeted, and an earlier reading that said T8
#   "retargets" the two RFCs was wrong in a way that made the final sweep
#   unreachable. Both RFCs read `Status: Accepted`, which this spec's `Never do`
#   rule amends by erratum only. T8 ADDS an erratum entry to each; it removes
#   nothing. RFC-0062 cannot stop matching even in principle — its filename and
#   its title line are `content-design and copy-direction skills` — so it matches
#   on 43 lines today and permanently, and RFC-0071 on 36. The changelog is the
#   same shape for a different reason: the 4.0.0 entry is obliged to name both
#   removed skills, and T11 adds adopter-action text naming both retired
#   directories, so its hits grow rather than shrink.
#   The final sweep therefore classifies into FOUR classes, not three:
#     registration hit          -> defect
#     counted discriminator     -> required (`type: tone-of-voice`, `type: copy-direction`)
#     release history           -> expected, permanent (docs/product/changelog.md)
#     frozen decision record    -> expected, permanent (the two RFC paths above)
#   The fourth class exists because a frozen record mentions a skill without
#   registering it, and the only way to make it stop matching is the rewrite the
#   `Never do` rule refuses.
#   Three of the packs hits are the genre fold's new surfaces —
#   information-architecture/references/conversion-design.md,
#   information-architecture/references/editorial-quality-gates.md, and
#   information-architecture/evals/evals.json — which did not exist when this
#   plan was approved and which T7's `Touches:` already owns.
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

There is deliberately no `ls -d … 2>/dev/null | wc -l  # want 0` line here. It
prints the wanted `0` both when the directories are gone and when the path
prefix is wrong or unreadable, so it is the same disarmed shape the sweep block
above was repaired for. The Python block subsumes it and cannot be fooled the
same way: it derives `skills` from `iterdir()`, which raises on a bad prefix
rather than printing zero, and catches a survivor through `extra` and the
twelve-directory count.

```bash
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
# Each of the FOUR source items gets its own evidenced disposition. Destination
# existence cannot supply it: both sources merge into one `content-design/evals/`,
# so `(cd / "evals.json").exists()` is the same boolean for both and one survivor
# would mark both carried. An earlier repair introduced exactly that.
import re as _re
import subprocess as _sp

if not BASE:
    sys.exit("BASE empty — refusing to judge the harness disposition against an unknown base")

ledger = pathlib.Path("docs/specs/xd-copy-router/notes/verification-ledger.md")
ledger_text = ledger.read_text() if ledger.exists() else ""

def disposition(token):
    """Return ('carried'|'dropped', detail) for a source item, or None.

    Both branches are recorded per source and both need >= 20 characters after
    the dash: `carried` says where that source's content landed, `dropped` says
    why. The match is bounded to the token's OWN LINE — a pattern running to
    end-of-file would let a later section supply the character count while the
    detail itself is empty. The separator may be an em-dash, `--` or `-`.
    """
    pattern = _re.compile(
        r"^.*" + _re.escape(token) + r":\s*(?P<verb>carried|dropped)\s*(?:\u2014|--|-)\s*(?P<detail>.+)$",
        _re.M,
    )
    hit = pattern.search(ledger_text)
    if hit is None or len(hit.group("detail").strip()) < 20:
        return None
    return hit.group("verb"), hit.group("detail").strip()

def existed_at_base(src, leaf):
    """Was this source item present at the merge-base? T6 deletes it, so HEAD cannot say."""
    if leaf == "files":
        r = _sp.run(["git", "ls-tree", "--name-only", f"{BASE}:{src}"],
                    capture_output=True, text=True)
        return "files" in r.stdout.split()
    return _sp.run(["git", "cat-file", "-e", f"{BASE}:{src}/{leaf}"],
                   capture_output=True).returncode == 0

problems = []
for gone in ("copy-direction", "tone-of-voice"):
    src = f"packs/experience-design/.apm/skills/{gone}/evals"
    for leaf in ("evals.json", "files"):
        if not existed_at_base(src, leaf):
            continue  # nothing to dispose of
        token = f"{gone}/evals/{leaf}"
        d = disposition(token)
        if d is None:
            problems.append(
                f"{token} has no recorded disposition; verification-ledger.md needs "
                f"'{token}: carried - <where it landed>' or '{token}: dropped - <why>', "
                f"20+ characters either way"
            )
            continue
        verb, _detail = d
        if verb == "carried":
            # A carried claim is checkable at the destination: the file or tree
            # must actually be there. A dropped claim rests on its reason.
            dest = cd / ("evals.json" if leaf == "evals.json" else "files")
            if not (dest.exists() if leaf == "evals.json" else dest.is_dir()):
                problems.append(f"{token} recorded as carried, but {dest} does not exist")
if problems:
    sys.exit("EVAL HARNESS DISPOSITION\n  " + "\n  ".join(problems))
print("eval harness: all four source items carried or dropped, each recorded per source")
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
# Then remove the discriminator OCCURRENCES and search what is left. `grep -v`
# would drop the whole line, so `route to tone-of-voice when type: tone-of-voice`
# would pass while still naming a routing target.
sed -e 's/type: tone-of-voice//g' -e 's/type: copy-direction//g' "$CD/SKILL.md" | grep -nE "$REMOVED"   # want no output
sed -e 's/type: tone-of-voice//g' -e 's/type: copy-direction//g' "$CD/references/communication-modes.md" | grep -nE "$REMOVED"   # want no output
# The eval corpus is a third surface inside the surviving skill, and an earlier
# draft read only the two above. `content-design/evals/evals.json` names
# `copy-direction` as a downstream consumer on three lines today; those are
# routing targets, not `type:` literals, so the counted-occurrence check cannot
# see them and they would surface at T11 as class-1 hits nothing had required
# anyone to remove.
sed -e 's/type: tone-of-voice//g' -e 's/type: copy-direction//g' "$CD/evals/evals.json" | grep -nE "$REMOVED"   # want no output
```

**Skill counts — negative and positive, cardinal and ordinal:**

Four numerals across three files, in three different constructs. `docs/index.md`
carries **two** — a prose line and a heading — so a single `grep -q '12 skills'`
leaves the heading stale. `README.md` and `JOURNEY.md` carry no skill-count
numeral at all, so the positive check is replaced there by a negative one:

```bash
# Reject EVERY stale form, not only the genre fold's intermediate 14: the
# pre-genre-fold 20/twenty-first text can survive beside a correct new string.
grep -rnoE '\b(14|fourteen|fifteenth|20|twenty|twentieth|twenty-first)\b' \
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
# Both word orders and both forms — `12 skills`, `twelve skills`, `Skills (13)`,
# `thirteen skills`. An earlier draft matched only number-then-noun.
! grep -rnoiE '(\b(1[0-9]|2[0-9]|ten|eleven|twelve|thirteen|fourteen|twenty)\b[^.]{0,12}\bskills?\b)|(\bskills?\b[^.]{0,4}\(?\b(1[0-9]|2[0-9]|ten|eleven|twelve|thirteen|fourteen|twenty)\b)' \
  packs/experience-design/README.md packs/experience-design/JOURNEY.md
# Readings, 2026-09-26, after the genre fold landed — this is the form this
# delivery actually edits: "pack of 14 skills" (index.md:3),
# "**Skills (14) in two families:**" (index.md:11), "14 pure-Markdown skills"
# (guides:17), "fifteenth skill" (web:63). The pre-genre-fold readings were
# 20/20/20/twenty-first; the ordinal counts the reviewer agent last, so it lands
# on "thirteenth" for a 12-skill pack, never on "12".
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
# ONE regenerator, one consumer. An earlier draft had two independent
# implementations of the same measurement — a validator that rebuilt the
# inventory and a separate "single home" block that rebuilt it again — which is
# the drift this block exists to prevent, reintroduced by the repair that
# claimed to remove it. The block below emits the inventory as JSON and
# validates the brief against that same object.
python3 - "$B" <<'QQ'
import collections, hashlib, json, pathlib, re, sys

SKILLS = pathlib.Path("packs/experience-design/.apm/skills")
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


def inventory():
    """The single measurement. Everything below reads this."""
    fam = collections.defaultdict(list)
    for path in sorted(SKILLS.glob("*/references/*.md")):
        fam[path.name].append(path)
    fam = {n: ps for n, ps in fam.items() if len(ps) > 1}
    rows = {}
    for name, paths in sorted(fam.items()):
        digests = {hashlib.sha256(q.read_bytes()).hexdigest() for q in paths}
        rows[name] = {
            "label": LABEL.get(name, name[:-3]),
            "files": len(paths),
            "hashes": len(digests),
            "skills": [q.relative_to(SKILLS).parts[0] for q in paths],
        }
    return {
        "families": len(rows),
        "files": sum(r["files"] for r in rows.values()),
        "hashes": sum(r["hashes"] for r in rows.values()),
        "rows": rows,
    }


def row_text(brief, needle):
    """The single table row containing `needle`, flattened. Bounded deliberately:
    flattening the WHOLE brief lets figures anywhere satisfy the check while the
    required row is deleted or left incomplete."""
    for line in brief.splitlines():
        if needle in line and line.lstrip().startswith("|"):
            return re.sub(r"\s+", " ", line)
    return None


inv = inventory()
print(json.dumps({k: v for k, v in inv.items() if k != "rows"}))
for name, r in inv["rows"].items():
    print(f"  {r['label']:<22} {r['files']:>2} files / {r['hashes']} hashes  " + ", ".join(r["skills"]))

if len(sys.argv) < 2:
    sys.exit(0)  # inventory-only mode: no brief argument, nothing to validate

brief = pathlib.Path(sys.argv[1]).read_text()
recheck = row_text(brief, "S8a reference deduplication")
adjacent = row_text(brief, "experience-design-reference-reconciliation")
fail = []
if recheck is None:
    fail.append("the S8a re-check row is missing entirely")
if adjacent is None:
    fail.append("the Adjacent-work row is missing entirely")

if recheck:
    # The re-check row carries the full regenerated summary: both totals and
    # every surviving sub-count.
    for want in [f"{inv['files']} files", f"{inv['hashes']} hashes"]:
        if want not in recheck:
            fail.append(f"re-check row does not state '{want}'")
    for r in inv["rows"].values():
        if f"{r['label']} {r['files']}/{r['hashes']}" not in recheck:
            fail.append(f"re-check row does not state '{r['label']} {r['files']}/{r['hashes']}'")
if adjacent:
    n = inv["families"]
    if (f"{n} duplicate-basename families" not in adjacent
            and f"{WORDS.get(n, n)} duplicate-basename families" not in adjacent):
        fail.append(f"Adjacent-work row does not state the family count ({n} / {WORDS.get(n, n)})")
    if f"{inv['files']}/{inv['hashes']}" not in adjacent:
        fail.append(f"Adjacent-work row does not state the {inv['files']}/{inv['hashes']} measurement")
# Stale figures must be GONE, not merely accompanied by the new ones: a row that
# states both passes every positive check above while still contradicting itself.
# Scoped to the two rows, because the brief legitimately discusses other numbers.
for label, row in (("re-check", recheck), ("Adjacent-work", adjacent)):
    if not row:
        continue
    for stale in ("31 files", "24 hashes", "31/24", "eight duplicate-basename families"):
        if stale in row:
            fail.append(f"{label} row still carries the stale figure '{stale}'")
if fail:
    sys.exit("BRIEF ROWS\n  " + "\n  ".join(fail))
print("brief rows agree with the regenerator, and carry no stale figure")
QQ
```

Run with no argument it prints the inventory alone; run with the brief it also
validates the two rows. Against the pre-fold tree on 2026-09-25 the inventory
reads **8 duplicate-basename families, 31 files, 24 hashes**, reproducing the
figure the sibling brief records — which is what establishes it measures the
thing the brief measured. The post-fold run is what the amended rows must
restate. The expected post-fold shape, derived from what this delivery does
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
import json, pathlib, subprocess, sys, tomllib
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
# Projection-wide, not just the two packs this delivery bumps. The regeneration
# is a whole-file rewrite, so it necessarily carries corrections this delivery
# did not author: it arrived with `experience-design` at 2.0.9 against a
# pack.toml of 3.0.0 and `frontend-engineering` at 0.3.2 against 0.3.3, both left
# by earlier deliveries. Asserting only the two named entries lets a hand edit
# fix those two, leave `frontend-engineering` stale, print "versions agree", and
# still fail `catalogue verify`. Every pack's projection entry must equal its
# own pack.toml.
for pack_toml in sorted(pathlib.Path("packs").glob("*/pack.toml")):
    name = pack_toml.parent.name
    want_any = tomllib.load(open(pack_toml, "rb"))["pack"]["version"]
    if name in proj and proj[name] != want_any:
        fail.append(f"marketplace.json[{name}]: projection {proj[name]} != pack.toml {want_any}")
if fail:
    sys.exit("VERSION MISMATCH\n  " + "\n  ".join(fail))
print("versions agree:", targets)
QQ
```

Pre-state readings, 2026-09-26, after the genre fold landed and this branch was
rebased onto `origin/main`: `experience-design` `3.0.0`, `product-engineering`
`0.13.19`, so the derived `product-engineering` target is `0.13.20`. Earlier
readings were `2.0.10` / `0.13.18` on 2026-09-25 and `2.0.9` / `0.13.17` before
that. The `4.0.0` arithmetic is unaffected — it counts major bumps, not the
base — but a stale reading defeats the stated
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
# Refuse an empty base: `git show ":<path>"` resolves to the INDEX, so the
# derived product-engineering target would come from staged content and the
# block would report agreement against a base it never read.
if not base:
    sys.exit("BASE empty — refusing to derive a version from an unknown base")
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
    # Free-standing, not nested — NOT adjacency. The position directly beneath
    # [Unreleased] is owned by test_the_core_release_heading_sits_directly_beneath_unreleased,
    # which requires [core] there, so requiring it here was unsatisfiable. What
    # matters is that the entry is a top-level `## ` heading rather than nested
    # inside the [Unreleased] section, because build-site.py withholds a nested
    # entry as unreleased and still exits 0.
    if n_xd <= unrel:
        fail.append("the experience-design entry is not below [Unreleased]")
    if not lines[i_xd].startswith("## "):
        fail.append("the experience-design entry is nested, not free-standing at ##")
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
# BASE comes from the guarded derivation at the top of this map. Refuse here too:
# an empty BASE makes `git diff` write to stderr and produce EMPTY STDOUT, which
# the pipeline below reads as "no violations" — a clean pass on the delivery's
# only control over the rule that an erratum names no spec or brief.
[ -n "$BASE" ] || { echo "BASE empty — refusing to run the errata scan"; return 1 2>/dev/null || exit 1; }
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
# A real OR. Running both sequentially means the edited-but-no-ledger-entry
# branch — which the criterion allows — still exits 1 on the trailing grep.
if [ -n "$(git diff --name-only "$BASE" -- docs/product/intents/xd-state-reviewer-doctrine.md)" ]; then
  echo "doctrine intent was updated in this delivery — criterion satisfied"
elif grep -q 'xd-state-reviewer-doctrine.*confirmed unaffected' docs/specs/xd-copy-router/notes/verification-ledger.md 2>/dev/null; then
  echo "doctrine intent recorded confirmed unaffected — criterion satisfied"
else
  echo "FAIL: doctrine intent neither updated nor recorded confirmed unaffected"
fi
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
| `DESIGN.md` records the supersession | `packs/experience-design/DESIGN.md`: an explicit statement that the byte-equality test supersedes the "Skill autonomy beats DRY at this scale" note. Owned by **T8**, the only task whose `Touches:` names that file. The reference-side check only sees the note disappear from the two copies; nothing else requires the positive statement |
| Autonomy-note removal has an owning `Touches:` | T3's `Touches:` names `information-architecture/references/editorial-quality-gates.md`; grep that the note is absent from both surviving copies |
| Routing-classification evidence | `notes/routing-classification-evidence.md`: nine fixed pre-fold and nine fixed post-fold rows; all 18 expected selections at high confidence; exact prompts and descriptions; zero retries; the proxy limits, abort path, and owner decision |
| Pooled `eval_queries.json` corpus | `$CD/evals/eval_queries.json`: 29 distinct positives and 32 distinct negatives; no query appears with both `should_trigger` values; every source positive is present; the negative set retains cases owned by `ux-writing` and `creative-direction`. Compare source membership against the guarded merge-base because T6 deletes two source files |
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
| Routing-classification evidence + abort path | `notes/routing-classification-evidence.md` | T1, T9 | Nine pre-fold and nine post-fold classifications; 18/18 expected selections at high confidence; exact tested post-fold description; proxy limits; all three abort triggers and `eugenelim` |
| Genre-fold precondition | `notes/verification-ledger.md` | T2 | The relocated file exists, is byte-identical at the merge-base, and is cited |
| Reconciliation record | `notes/reference-reconciliation.md` | T3, T4 | Six files, each with a winner, a clause, or a recorded drop and its reason |
| Shared-reference integrity | `content-design/` + `information-architecture/` | T3, T5, T6 | T3 lands the byte-equality extension with its vacuity guard; T5 lands the citation in `content-design/SKILL.md`, the only side this delivery installs; **T2 verifies** the `information-architecture` side, which is a genre-fold post-condition in no task's `Touches:`; **T6 is where it goes GREEN**, because the glob sees the two doomed copies until T6 deletes them |
| Merged skill (current product truth) | `CD/` | T5 | Three modes, three assets, all output contracts; `lint-experience-agnostic` exits 0 |
| Eval harness | `content-design/evals/` + `notes/verification-ledger.md` | T5, T6 | Pooled positives and negatives. **T6 writes the four per-source disposition lines** into the ledger, which is in its `Touches:`; T5 reads the sources at the merge-base and edits neither |
| Two directories removed | `packs/experience-design/.apm/skills/` | T6 | Directory count 12, every directory declared, no undeclared stub |
| Reviewer + cross-pack | `.apm/agents/experience-reviewer.md`, `packs/product-engineering/**` | T7 | The sync citation resolves; the exclusion clause names an artifact `type:` |
| Sibling brief rows | `docs/product/briefs/digital-experience-doctrine-completion.md` | T7 | Both stale occurrences gone; 4 families / 19 files / 11 hashes present |
| Two errata (decision rationale) | RFC-0062, RFC-0071, `DESIGN.md` §§ 4 and 7 | T8 | Two-layer form; neither new entry names a spec or a brief. **T8 is the sole editor of `DESIGN.md`**, including the supersession statement |
| User promise | `guides/experience-design/` | T7a | Guide-agreement test passes and a named reviewer judges the guide sufficient |
| Registry + projection surfaces | `workspace.toml`, `skill-census.json`, `tools/add-rendering-directives.py` | T7a | Census suite passes; no removed name in any of the three |
| Public site truth | `web/src/content/` | T7 | Frontmatter, `whatChanges` and stage prose updated; the **ordinal reads `thirteenth skill`**; `npm run build` exits 0 |
| Versions + release history | manifests, `.claude-plugin/marketplace.json`, changelog | T10 | All three surfaces agree per pack; both catalogue commands exit 0 |
| Manual-QA verdicts + final sweep | `notes/verification-ledger.md` | T11 | All four verdicts with reviewer and date, the `brand-register` refusal verdict as a fifth entry, the install observation, and the **delivery-wide registration sweep**, which only this last task can reach |

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

**The routing proxy uses fixed inputs.** T1 classifies these prompts once in
each world. The expected post-fold route for C1–C6 is `content-design`; the
expected pre-fold route is the source named in the third column. C7–C9 keep the
same neighboring route in both worlds.

| Case | Prompt | Expected pre-fold |
| --- | --- | --- |
| C1 | Before wireframes, decide what our onboarding page must say and how the story should unfold | `content-design` |
| C2 | What does our API quickstart page need to communicate to developers? | `content-design` |
| C3 | Name the copy goals for this pricing-page hero before anyone writes the lines | `copy-direction` |
| C4 | Before we write the tagline for this surface, we need to name what it should feel like | `copy-direction` |
| C5 | Our teams sound inconsistent; define the brand voice every channel should share | `tone-of-voice` |
| C6 | What's the copy arbitration rule when urgency and warmth conflict across our communications? | `tone-of-voice` |
| C7 | Write the error message for when login fails | `ux-writing` |
| C8 | What's the visual aesthetic direction for the landing page? | `creative-direction` |
| C9 | Order the content on this settings screen by priority | `information-architecture` |

The exact post-fold candidate is:

> Use when someone asks what a surface should communicate or how its copy
> should feel before final words are written, or when a team needs a
> cross-surface brand register. Runs in three modes: message and narrative
> structure for a content brief; per-surface acquisition copy goals for a
> copy-direction record; brand-level register for named, ranked voice goals and
> arbitration rules. Use `ux-writing` for final product UI strings and state
> microcopy, `creative-direction` for visual mood, and
> `information-architecture` for page hierarchy. Organization-level content
> strategy belongs to `define-content-strategy`; product positioning and growth
> strategy stay upstream; implementation belongs to `frontend-engineering`.
> Triggers on "shape the message hierarchy before we wireframe", "set ranked
> copy goals for this landing page", and "define how our brand should sound
> across product and marketing".

The candidate is 895 **characters** when joined as one frontmatter scalar. T1
recomputes the character count from the exact joined text rather than trusting
this illustrative reading. The unit matters: `skill_spec_lint.py` raises on
`len(desc)`, which counts characters, so a non-ASCII candidate measured in bytes
would be checked against a limit that does not run. This candidate is ASCII, so
its two counts coincide at 895 today. The 1024-**character** cap and byte
identity are the gates.

### Failure, edge cases & resilience

- Genre fold aborted or landed without the relocation → T2 fails and the slice
  stops; it does not create the shared file itself.
- The bounded classifier returns a mismatch or less than high confidence → T1
  stops before any skill edit, and nothing in this slice ships. The evidence is
  directional only, so this delivery makes no production-activation claim.
- A reconciliation cannot be classified → the verdict is recorded as unresolved
  and the pair escalates rather than being merged on a guess.

## Tasks

### The ownership rule these tasks obey

**A task may only assert what it can reach.** An assertion belongs to a task
when the thing asserted is inside that task's own `Touches:`, or is installed by
one of its ancestors in the graph. An assertion that depends on a
non-ancestor — a descendant, or an unordered sibling — cannot be satisfied at
that task's position, and the only way to "pass" it is to declare done against a
check that is still failing.

This rule is written down because the task list violated it repeatedly and
each violation read as reasonable in isolation: a delivery-wide sweep asserted
at the task that deletes the directories, a shared-file equality test closed out
before the duplicate copies are gone, a ledger entry required from a task whose
`Touches:` does not include the ledger. Three consequences follow, and the task
sections below are written to them:

1. **`Touches:` is precise, never a convenient prefix.** A prefix such as
   `packs/experience-design/` silently claims another task's files and makes two
   unordered siblings co-owners of the same surface. Each task lists what it
   actually edits.
2. **A whole-scope assertion lands on the last task that can reach the whole
   scope**, not on the task whose subject matter it resembles.
3. **Every obligation is owned by exactly one task.** Where an obligation moved
   during this reconciliation, the task that gave it up says so, so the move is
   visible rather than inferred from an absence.

### T1: The bounded routing-classification evidence is durable

**Depends on:** none

**Tests:**
- `notes/routing-classification-evidence.md` records 18 cold
  `fork_turns: "none"` Codex classifications: nine fixed prompts, once against
  the pre-fold descriptions and once against one exact post-fold candidate,
  with descriptions only and no retries.
- The six copy-layer prompts cover message and narrative structure,
  per-surface acquisition copy goals, and brand-level register twice each. The
  three boundary prompts belong to `ux-writing`, `creative-direction`, and
  `information-architecture`.
- The pre-fold results select `content-design`, `copy-direction`, and
  `tone-of-voice` twice each; the post-fold results select `content-design` for
  all six copy-layer prompts; the three boundaries retain their route in both
  worlds. Every result matches at high confidence.
- The note carries the exact prompts, every candidate description, expected and
  actual selections, confidence, owner authorization, date, zero-retry count,
  and the exact tested post-fold description. That candidate is at most 1024
  characters.
- The post-fold candidate set states the **post-fold** `ux-writing` description,
  not today's. Today's ends "or to establish the brand-level copy register (use
  `tone-of-voice`)", which T7 must retarget; T1 runs first, so testing today's
  text would classify a boundary candidate that does not ship. Author the
  retargeted description here, test it, and let T7 install it and T9 check it.
- The note states the limits: this is a classification proxy, not a Claude
  `Skill` activation event; Codex retains platform system context; one sample
  per case and world does not establish broad recall, false-positive rates,
  repeated-sampling stability, or production behavior.
- The abort path is prevention, not reversion: a mismatch or less than high
  confidence stops before T3. The other triggers are an explicit owner stop and
  the brief's approximately three-week window elapsing. On any trigger nothing
  in this slice ships, and `eugenelim` decides.

**Approach:** run the same bounded external description-classification protocol
accepted for `xd-genre-router`, with this fold's fixed copy-layer cases and
neighbor set. Persist the evidence before any pack edit.

**Done when:** the tracked note contains the fixed input, 18/18 expected
high-confidence result, exact shippable candidate, limits, owner decision, and
abort path. Any other result stops the slice.

**Touches:** docs/specs/xd-copy-router/notes/routing-classification-evidence.md

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
  `tests/roster/test_*.py`. **This task owns the extension's existence, not its
  passing.** The assertion globs every
  `*/references/editorial-quality-gates.md`, and three copies exist until T6
  deletes `copy-direction/` and `tone-of-voice/` — so it is legitimately red
  from here until T6, which owns its GREEN. Expecting green at this position
  would force either a premature deletion outside this `Touches:` or a weakened
  assertion.

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
  `evals/files/` fixture tree, **or a source is deliberately dropped** — the
  criterion admits either, and T6's disposition script accepts a `dropped`
  verb, so an assertion that only admits carrying fails a legitimate drop
  before the task that records it runs. The **recording** branch is not this
  task's:
  the per-source disposition lines go in `notes/verification-ledger.md`, which
  is in T6's `Touches:` and not in this one. T5 carries; T6 records.
- The `brand-register` slug refusal survives. This task implements the
  behaviour; **T11 records the verdict**, because the ledger is in T11's
  `Touches:` and not in this one. It is a fifth ledger entry, not one of the
  four manual-QA judgements the Testing Strategy enumerates.
- The three legacy-1.x migration prompts and the three `type:`-collision branches
  survive.
- `content-design/SKILL.md` cites `references/editorial-quality-gates.md`.
- Neither removed name survives inside the surviving skill **in registration,
  routing-target or path position**. The `type: tone-of-voice` discriminator
  literals are required to survive — **seven** `type: tone-of-voice` and **two**
  `type: copy-direction` in `SKILL.md` — so an
  unqualified "neither name survives" contradicts the carve-out. Five lines of
  `content-design/SKILL.md`, one of `references/communication-modes.md` and
  **three of `evals/evals.json`** name them in the forbidden positions today,
  and this is the task that edits all three.

**Done when:** every mechanical test passes and `lint-experience-agnostic` exits 0.

**Touches:** packs/experience-design/.apm/skills/content-design/**, packs/experience-design/.apm/skills/copy-direction/assets/copy-direction-template.md, packs/experience-design/.apm/skills/tone-of-voice/assets/tone-of-voice-template.md

### T6: The two registrations are gone

**Depends on:** T5

**Tests:**
- Both directories absent; every surviving `.apm/skills/` directory is declared
  in `pack.evals.skills` and the two sets are equal at **twelve** — membership,
  not length, and a check that a stub under a third name fails.
- Neither removed name is declared; `content-design` is.
- No removed name survives **as a registration inside
  `packs/experience-design/.apm/skills/`**. This `Touches:` is four explicit
  paths rather than the tree, so the assertion rests on the rule's second
  clause — a task may assert what an **ancestor** installed. Measured
  2026-09-26, exactly seven files under that tree match outside the two deleted
  directories, and each is reachable: `content-design/SKILL.md`,
  `content-design/references/communication-modes.md` and
  `content-design/evals/evals.json` are T5's work; the relocated
  `information-architecture/references/editorial-quality-gates.md` is T3's;
  `information-architecture/references/conversion-design.md` and
  `information-architecture/evals/evals.json` are this task's own; and
  `experience-status/SKILL.md` is **this task's**, and its `Touches:` now names
  it. An earlier enumeration called it "edited by nobody, because both of its
  hits are counted discriminators" and was wrong twice: the file carries four
  hits, not two, and the fourth is a registration — its "What to run next"
  suggestion list names both removed skills as routing targets. The two
  `type:` literals on lines 67-68 stay at their counted occurrences; the
  suggestion line is retargeted to the surviving skill. That includes the genre
  fold's three new surfaces, which are this task's work and nobody else's:
  `information-architecture/references/conversion-design.md` names both removed
  skills in routing-target position, and `information-architecture/evals/evals.json`
  names them in bare-name position. Neither is a `type:` literal, so neither is
  carved out. The **delivery-wide** sweep is deliberately not asserted here:
  its remaining hits live in `guides/`, `web/`, `tools/`, `workspace.toml`, the
  two RFCs and the changelog, which T7, T7a, T8, T10 and T11 clean — and all of
  them depend on T6, so no ordering can put them before it. T11 owns that
  assertion, as the last task in the graph.
- The two directories' `evals/evals.json` and `evals/files/` are carried into
  `content-design/evals/` or their drop is recorded with a reason in
  `notes/verification-ledger.md`, which this `Touches:` now reaches. It did not,
  while this task was obliged to write that record.
- **The byte-equality assertion goes GREEN here, not at T3.** T3 lands the
  extension; it cannot be green there. The new test globs
  `*/references/editorial-quality-gates.md` exactly as the containment precedent
  globs its own module, and three copies exist until this task deletes two of
  them — so between T3 and T6 the glob sees copies that legitimately differ.
  T3 owns the extension's existence and its vacuity guard; this task owns its
  passing.
- Both templates have already moved under T5; this task confirms nothing under
  `assets/` is lost with the deletion.

**Done when:** the two sets are equal at twelve, the registration grep is empty
**within `.apm/skills/`**, the byte-equality assertion passes, and the harness
disposition is recorded in the ledger.

**Approach:** `packs/AGENTS.md` § Security and authoring rules obliges a
non-cosmetic pack update to update the pack's eval harness, and `skill_spec_lint`
cross-checks `pack.evals.skills` against `eval_queries.json` only — so a vanished
`evals.json` leaves `catalogue lint --deep` green. The disposition is therefore
stated here rather than inferred from a passing gate.

**Touches:** packs/experience-design/.apm/skills/copy-direction/, packs/experience-design/.apm/skills/tone-of-voice/, packs/experience-design/.apm/skills/experience-status/SKILL.md, packs/experience-design/.apm/skills/information-architecture/references/conversion-design.md, packs/experience-design/.apm/skills/information-architecture/evals/evals.json, packs/experience-design/pack.toml, tests/roster/test_experience_design_write_declaration_and_containment.py, docs/specs/xd-copy-router/notes/verification-ledger.md

### T7: Reviewer, cross-pack and sibling-brief surfaces are consistent

**Depends on:** T6

**Tests:**
- `experience-reviewer.md`'s sync citation resolves; its `Does NOT fire on` list
  names surviving skills or artifact types.
- `xd-state-reviewer-doctrine.md` is updated against this delivery's
  `experience-reviewer.md` edits, **or** recorded confirmed unaffected in
  `notes/verification-ledger.md`. Both branches are available to this task
  because both files are in its `Touches:`; while the ledger was absent from it,
  an executor finding the intent genuinely unaffected had to either make a
  pointless edit or write outside its authority.
- `ux-writing/SKILL.md`'s `tone-of-voice step 6` pointer is retargeted while its
  **three** discriminator literals stay — the measured count, all on one line;
  `product-engineering/DESIGN.md` updated.
- `digital-experience-doctrine-completion.md`'s re-check and Adjacent-work rows
  carry the **full** post-fold row — every sub-count, new file/hash totals, and
  eight families becoming **four**: 19 files / 11 hashes, containment 5/1, layout
  10/7, editorial gates 2/1, interrogation 2/2. Both stale occurrences of the
  31/24 figure are amended, line 68's and line 81's.
- `web/src/content/packs/experience-design.md`'s **ordinal** reads
  `thirteenth skill`. This task owns that numeral because `web/src/content/**`
  is in this `Touches:` and in no other task's; T7a owns the two `docs/index.md`
  numerals and the guides numeral, which sit in its own. Neither task asserts
  "every" numeral, because neither can reach them all.
- `web/src/content/{journeys,packs}/experience-design.md` name the surviving
  skill only, including the journey page's `skills:` frontmatter list.
- Astro build exits 0.
- **Not this task's, and moved deliberately:** `packs/experience-design/DESIGN.md`
  — both its § 4 rewrite and its supersession statement — is **T8's**. T8's
  `Touches:` names that file and this task's no longer does, so one task edits
  it. The census fixture is **T7a's**, for the same reason. Both clauses lived
  here while this task's `Touches:` was the prefix `packs/experience-design/`,
  which claimed files four other tasks edit.

**Done when:** the sibling brief row reads post-fold, the `web/` ordinal reads
`thirteenth skill`, and the site builds.

**Touches:** packs/experience-design/.apm/agents/experience-reviewer.md, packs/product-engineering/.apm/skills/ux-writing/**, packs/product-engineering/DESIGN.md, docs/product/briefs/digital-experience-doctrine-completion.md, docs/product/intents/xd-state-reviewer-doctrine.md, web/src/content/**, docs/specs/xd-copy-router/notes/verification-ledger.md

### T7a: The guide tree and the three registry surfaces are consistent

**Depends on:** T6

**Tests:**
- `guides/experience-design/how-to/copy-boundary.md` describes mode selection
  within one skill.
- **The three skill-count numerals in this task's own `Touches:`** read their
  post-fold form, checked per numeral: `guides/…/reference/experience-design.md`
  "12 pure-Markdown skills" (reads `14` today, on the 2026-09-26
  post-genre-fold reading this pair records throughout), and
  `packs/experience-design/docs/index.md`'s **two** numerals — the prose line
  and the `**Skills (N)**` heading. Checking only the prose line leaves the
  heading stale. The word "every" is deliberately not used: the fourth
  numeral is the `web/` ordinal, which lives in T7's `Touches:` and is
  asserted there.
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
- **`packs/experience-design/DESIGN.md`, in full — moved here from T7.** § 4's
  "Content-design vs. tone-of-voice vs. copy-direction vs. ux-writing" section
  is rewritten as mode selection within one skill plus the one surviving
  cross-pack boundary. § 7's artifact table `copy/` row is retargeted. The file
  records that the byte-equality test supersedes the "Skill autonomy beats DRY
  at this scale" note, which this fold reverses. No removed name survives in
  this file in registration position; `DESIGN.md` holds no `type:` literal of
  either kind, so it carries no discriminator carve-out. This task's `Touches:`
  is the only one naming the file.

**Done when:** both entries exist in two-layer form, cite no delivery artifact,
and `DESIGN.md` carries the rewritten § 4, the retargeted § 7 row and the
supersession statement.

**Touches:** docs/rfc/0062-content-design-and-copy-direction-skills.md, docs/rfc/0071-digital-experience-doctrine.md, packs/experience-design/DESIGN.md

### T9: The shipped routing controls match the accepted evidence

**Depends on:** T5, T6, T7

**Tests:**
- The shipped `content-design` frontmatter description is byte-identical to
  T1's tested post-fold candidate and is at most 1024 characters.
- The shipped `ux-writing` description is byte-identical to the post-fold
  `ux-writing` description T1 put in its candidate set, or the divergence is
  recorded as immaterial with its reason. T7 edits that description and T1 runs
  first, so without this check the probe's boundary candidate is not the one
  that ships.
- The evidence note still records all nine pre-fold and nine post-fold rows,
  18/18 expected high-confidence selections, zero retries, and every stated
  proxy limit.
- `content-design/evals/eval_queries.json` contains 29 distinct positive and 32
  distinct negative queries, with no query carrying both `should_trigger`
  values. Its negative set retains cases owned by `ux-writing` and
  `creative-direction`.
- No live Claude activation run or repeated classifier sampling occurs.

**Done when:** the shipped description is the accepted candidate and the static
evidence and corpus checks pass. A material description change reopens T1 or
stops the slice.

**Touches:** docs/specs/xd-copy-router/notes/routing-classification-evidence.md

### T10: The release is registered

**Depends on:** T7, T7a, T8, T9

**Tests:**
- `experience-design` reads `4.0.0` in both manifests **and** in the regenerated
  `.claude-plugin/marketplace.json` entry, read as JSON — the projection is a
  third surface and an earlier draft checked only the two source manifests.
- `product-engineering` reads exactly **one patch above its merge-base value** in both, and in the projection. The 2026-09-26 reading, after the rebase onto `origin/main`, is `0.13.19`, so the target is `0.13.20` unless the base has moved again; the target is derived at execution time, never copied from here.
- Two changelog entries; the `experience-design` one names both removed skills.
- **The delivery-wide registration sweep is not asserted here either.** This
  task writes the changelog, and T11 writes it again — its adopter-action text
  names both removed directories, which are sweep hits this task cannot see. The
  assertion belongs to the last task in the graph, which is T11.
- Every pack's `.claude-plugin/marketplace.json` entry equals its own
  `pack.toml`, not only the two this delivery bumps. The regeneration clears the
  inherited `experience-design 2.0.9` and `frontend-engineering 0.3.2` entries
  recorded under Construction tests; this is the task that clears them.
- Both catalogue commands exit 0. Before this task they do not, for that
  inherited reason.

**Done when:** every version surface agrees and catalogue passes.

**Touches:** packs/experience-design/pack.toml, packs/experience-design/.claude-plugin/plugin.json, packs/product-engineering/pack.toml, packs/product-engineering/.claude-plugin/plugin.json, .claude-plugin/marketplace.json, docs/product/changelog.md

### T11: Adopter hygiene and the four judgements are recorded

**Depends on:** T10

**Tests:**
- Observed `agentbundle` install/update behaviour for a removed directory
  recorded; the changelog states the manual step if stale directories persist.
- Four manual-QA verdicts recorded with reviewer and date, plus the
  `brand-register` slug-refusal verdict, which is a fifth ledger entry rather
  than one of the four: `spec.md`'s Testing Strategy enumerates four judgements
  and the refusal is not among them, so recording it as one of the four would
  displace a judgement the contract names.
- **The delivery-wide registration sweep carries no unclassified hit.** This is
  the last task in the graph and the only position from which the whole scope is
  reachable: T6 cleans `.apm/skills/`, T7 the reviewer and cross-pack surfaces,
  T7a the guides and registry surfaces, T8 amends the two RFCs, T10 the release
  surfaces, and this task writes the changelog last. Run the sweep block from
  the verification command map and place every surviving hit in one of four
  classes:
  1. **Registration** — a roster, routing target, availability probe or install
     list. A defect. Must be zero.
  2. **Counted discriminator** — `type: tone-of-voice` or `type: copy-direction`
     at an occurrence count the carve-out tables record. Required to survive;
     a missing one fails a number.
  3. **Release history** — `docs/product/changelog.md`. Permanent and expected:
     the `4.0.0` entry is obliged to name both removed skills, and this task
     adds adopter-action text naming both retired directories.
  4. **Frozen decision record** — `docs/rfc/0062-…md` and `docs/rfc/0071-…md`.
     Permanent and expected. Both are `Status: Accepted`, which the spec amends
     by erratum only, so T8 adds entries and removes nothing; RFC-0062 cannot
     stop matching at all, because its filename and title name the skill. The
     assertion is **not** that these files stop matching — that would require
     the rewrite the `Never do` rule refuses.

**Done when:** the ledger carries the install observation, all four verdicts and
the refusal verdict, and every sweep hit falls in one of the four classes with
class 1 empty.

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
- **The bounded classification proxy may not predict production activation.**
  The contract makes no production-rate claim. Static corpus checks protect the
  shipped routing surface, and any mismatch or low-confidence proxy result
  stops the slice before pack edits begin.

## Changelog

<!-- Approvals only. Drafting history does not belong here. -->

- 2026-09-25 — Scope approved by eugenelim. Three registrations become one
  skill with three modes; all three output contracts, their paths and their
  `type:` values are unchanged, and the `brand-register` slug reservation
  survives. The boundary against `product-engineering`'s `ux-writing` stays.
  What is explicitly out: `creative-direction`'s `interrogation-sequence.md`
  variant, which the brief settles flat and this delivery refuses rather than
  asks about, and any merge of the three output artifacts, which the brief
  settles twice and which would change `frontend-engineering`'s handoff read.

- 2026-09-25 — Build strategy approved by eugenelim. Twelve tasks. The
  activation baseline runs before any deletion; the six reference
  reconciliations run before the merge, because a merged skill built on an
  unreconciled pair bakes in whichever variant was pasted first; and the slice
  is blocked behind the genre fold landing `editorial-quality-gates.md` under
  `information-architecture`, checked as a precondition in T2 rather than
  assumed. Scope-borne divergence is rewritten with one named scope parameter
  rather than resolved by letting one variant win — `copy-arbitration.md` is
  the case that forces it. The duplicate-basename measurement is owned by a
  regenerator in this plan, not by a pinned table, because an inventory of what
  a change invalidates cannot be a snapshot.

- 2026-09-25 — Residual accepted by eugenelim. Six review rounds ran before
  this gate, raising 75 findings and 7 proposed deletions; every one was checked
  against the tree before being applied, and rounds one to four ran on Claude
  subagents before the loop moved to Codex for rounds five and six. Blockers
  fell 10 → 9 → 5 → 2 across rounds one to four. Round six's ten findings were
  applied but **not re-reviewed**, so no reviewer has confirmed the pair clean
  against `d0edb5ca1`. The residual is bounded: round six's own verdict line
  read `Remaining findings are drift from recent repairs: YES`, and six of its
  ten findings were explicitly attributed to round five's repairs rather than to
  the artifact — which is the documented stop signal for an iterative review,
  not a convergence failure. A confirmatory review runs before T3, the first
  task that authors pack content.

- 2026-09-26 — **Amendment: replace the live Claude activation experiment with
  bounded routing-classification evidence.** The owner directed this delivery
  to use the approach accepted for `xd-genre-router`: nine fixed cold Codex
  cases classified once in each world from descriptions alone, with no retries,
  plus static corpus and description checks. T1 now runs and records the probe
  before any pack edit; T9 verifies that the shipped description is the exact
  tested candidate and that the pooled corpus remains 29 positive / 32 negative
  with no opposite-trigger collision. The proxy's limits are explicit, and the
  delivery makes no production-activation claim. Scope and repository outcomes
  are unchanged.

- 2026-09-26 — Amended scope approved by eugenelim. The live Claude
  activation-rate gate is replaced by bounded description-classification
  evidence and static corpus checks. The fold's outcome, boundaries, durable
  outputs, and no-partial-shipment rule are unchanged.

- 2026-09-26 — Amended build strategy approved by eugenelim after independent
  shaping review and adversarial spec-mode review returned clean. T1 records
  the fixed 18-call proxy before any pack edit; T9 verifies the exact tested
  description and the 29-positive / 32-negative corpus without another live
  activation run.

- 2026-09-26 — **Amended scope re-approved by eugenelim after six confirmatory
  review rounds.** The pair was re-reviewed against a tree the approval had not
  seen: the sibling genre fold had landed and the branch had been rebased onto
  `origin/main`. Six rounds raised 46 findings and sustained 40. Three
  acceptance criteria change. `type: copy-direction` becomes a second
  discriminator carve-out with its own measured occurrence counts, because the
  sweep pattern matches it as a whole word and carving out only
  `type: tone-of-voice` made the surviving skill's own check contradict the
  output contract. The routing probe must test the post-fold `ux-writing`
  description rather than today's, because this delivery edits that description
  and T1 runs before T7 installs it. The final registration sweep classifies
  into four classes rather than asserting emptiness, because two `Accepted`
  RFCs match the pattern permanently — RFC-0062 by its own filename — and the
  only way to make them stop is the rewrite the `Never do` rule refuses.

- 2026-09-26 — **Amended build strategy re-approved by eugenelim.** The task
  list is reconciled against one rule, now stated at the head of `## Tasks`: a
  task may only assert what its own `Touches:` reaches or an ancestor installs.
  The list violated it throughout, and each violation read as reasonable alone —
  a delivery-wide sweep asserted at the task that deletes the directories, a
  shared-file equality test closed out before the duplicate copies are gone, a
  ledger record required from a task that may not write the ledger. `Touches:`
  is now precise edit authority rather than a convenient prefix, six assertions
  moved to the task that can reach them, and no two unordered tasks share edit
  authority over any path. The verification map's registration sweep was also
  repaired: it passed its five in-scope `docs/` paths as one unquoted scalar,
  which `zsh` does not word-split, so under this repository's shell it scanned
  none of them and still exited 0.

  **Residual accepted.** Round six's four findings were applied but not
  re-reviewed, so no reviewer has confirmed the pair clean against the final
  state. The residual is bounded: every factual claim in those four was
  verified directly against the tree before repair, and all nine carve-out
  occurrence counts were re-measured afterwards. This follows the stop rule this
  delivery's earlier round six already set.

- 2026-09-27 — **Amendment: two checks corrected so each can observe what it
  names. Authorized by eugenelim after post-gates review.** Neither correction
  changes what the delivery must achieve; both change a stated check that could
  not run.

  The changelog placement criterion required the `[experience-design][4.0.0]`
  entry **directly beneath `[Unreleased]`**. That position is owned by
  `tests/roster/test_verification_ledger_contract.py::test_the_core_release_heading_sits_directly_beneath_unreleased`,
  which requires `[core]` at its shipped version there, and the position admits
  one heading — so the criterion and an enforced test could not both hold. The
  conflict is not hypothetical on this branch: commit `e1164adeb` exists only to
  undo the same mistake in a sibling delivery after CI caught it. The criterion,
  its Durable Outputs row, and this plan's changelog validator now require what
  the obligation actually is: a **free-standing** `##` entry, **never nested**
  under `[Unreleased]`, because `tools/build-site.py` withholds a nested entry as
  unreleased and still exits 0, so only nesting stops it publishing. The amended
  validator and the enforced test now pass together.

  The byte-equality criterion's named verification selected
  `-k editorial_quality_gates_copies_are_byte_identical` while the mandated and
  shipped test is `test_every_editorial_quality_gates_copy_is_byte_identical` —
  "copy_is", not "copies_are". The selector matched nothing and exited 5, which
  the block reads as "the extension has not landed yet", so the delivery's named
  check for that criterion reported the pre-state permanently. The selector is
  corrected and now runs the assertion.

- 2026-09-27 — Amended scope and build strategy re-approved by eugenelim. The
  eleven completed tasks and their evidence are preserved by the amendment
  event; no acceptance criterion is removed, narrowed in substance, or deferred,
  and no scope moves to a follow-on.
