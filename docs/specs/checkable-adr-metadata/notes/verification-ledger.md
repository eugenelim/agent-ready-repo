# Verification ledger — checkable-adr-metadata

Execution observations. The spec holds the contract and the plan holds the
strategy; neither is edited to record what happened here.

## T6 — goal-based checks, run 2026-09-17

T6's `Tests` are goal-based and name this file as their home.

| Check | Verifies | Observed |
| --- | --- | --- |
| The write gate surfaces the `Areas` tokens in use in the target directory and requires an explicit answer before an unused token is coined | AC-0025 | present at `new-adr/SKILL.md:208-214`, step 7 "Preview and confirm — the write gate"; the scan and the explicit-answer requirement both run *before* the general preview, so coining does not ride the preview confirmation |
| `new-adr`'s SKILL.md defines the `## Errata` convention; `new-rfc`'s sole-home sentence names RFCs | AC-0026 | `## Recording corrections (Errata)` present; `new-rfc/SKILL.md` sole-home sentence narrowed to RFCs |
| `new-adr` SKILL.md body lines under 500, measured after the six-line YAML frontmatter | — | **365** (371 total − 6). Command: `F=…/new-adr/SKILL.md; echo $(( $(wc -l < $F) - $(awk 'NR>1 && /^---$/{print NR; exit}' $F) ))`. The plan's "It is 335 today" was the pre-T6 baseline, not a target; CAT-S003 warns above 500 and errors above 1000, so the criterion holds with 135 lines of headroom |

Pack suite `packs/governance-extras/tests/skills/new-adr/test_lint_adr_shape.py`:
49 passed, 0.53s. `make lint-packs`: ok, 1 pre-existing INFO finding
(`CAT-L032`, an unsatisfied optional runtime dependency in `packs/core`, not
this delivery's). `make lint-ruff lint-mypy`: clean, 148 source files.

## Two repairs landing outside any task's pinned `Touches`

Both were found by reading AC-0023 and AC-0024 against their own surface sets
rather than against the task that happened to be running. Recorded here because
`Touches` is pinned (`plan.md:29-32`) and neither repair is inside the task that
owns the criterion.

**`new-adr/SKILL.md` stated the retired rule in two places T6's `Approach` did
not name.** T6's `Approach` named two line locations; AC-0023's predicate is
file-wide. The surviving text was the "Reversing a decision" bullet ("flip the
old ADR's status to `Superseded by ADR-NNNN` — status line only") and the
anti-pattern entry ("ADRs are immutable … never an edit"). The first also
carried the compound `Superseded by ADR-NNNN` status value that RFC-0102 § 2
splits into a bare `Status` token plus a `Superseded by:` field, so it was
teaching a shape the new lint rejects. AC-0023 is T7's to close, but T7's
`Touches` does not admit this file, so T7 could not have repaired the surface
its own search reads. Repaired under T6, whose `Touches` does admit it; T7's
pinned search is now satisfiable within T7's own `Touches`.

**The template's zone block was a different taxonomy from the one it names.**
`assets/adr.md` (T5, already committed) headed the block "Lifecycle zones" and
keyed all four names to `Status` values — "Frozen — Status is Deprecated or
Superseded: body **and metadata** are stable". RFC-0102 § 4 divides a record by
content, not by lifecycle: all four zones apply to every ADR at once, and the
scope paragraph states there is no grandfathered set and no format threshold.
The template's reading froze `Status` and the supersession fields on exactly the
records that still need them writable — the superseded ones — which contradicts
the `Live` zone and would have taught an author not to record a supersession
discovered later. Re-derived from the § 4 table, including the `Consulted` /
`Informed` no-zone carve-out. No task's live `Touches` admits `assets/adr.md`.

Neither repair changes a criterion; both make an existing criterion hold on a
surface it already named.

## T9 — the closing corpus observation, run 2026-09-17

The corpus went from 8 finding lines over 4 record paths to 0. Command, run
against the projected copy the `check-adr-shape` chain step invokes:

    python3 .claude/skills/new-adr/scripts/lint-adr-shape.py docs/adr
    read: 116  refused: 0  unreadable: 0      exit 0

Only two records were edited. `ADR-S010` is a mirror rule that reports from both
sides, so ADR-0042 and ADR-0109 each contributed a finding line without needing
a change; bare-tokening ADR-0023 and ADR-0050 and giving each a `Superseded by:`
field cleared all four `ADR-S010` lines along with both `ADR-S001` and both
`ADR-S007`. `check-adr-index` (`index-records.py --check docs/adr`) exits 0.

`tools/test_build_gate_chain.py`: 40 passed, 28 subtests, 21.8s — this is what
pins the step's presence and its `docs/adr` argv. The step body was also read
directly at `tools/repo/build_gate_chain.py:286-289` and matches the invocation
above, so the exit code recorded here is the step's own, not a proxy for it.

### `docs/adr/README.md` did not change, and that is the finding

AC-0013 asks that a supersession pointer render in the generated index. It
already did: rows 27 and 54 read `Superseded by ADR-0042` and `Superseded by
ADR-0109` both before and after, because `_status_token` stripped the link
markup out of the old compound `Status` value and arrived at the same text the
new field composition produces. The file has not been committed since an
unrelated change, and regenerating it is a no-op.

So the artifact cannot distinguish the two mechanisms, and AC-0013 is not
observable in it. The generator suite is the only thing pinning the new path.
Confirmed differentially rather than by reading the code: copying ADR-0023 into
a scratch directory and running the generator renders `Superseded by ADR-0042`;
deleting only its `Superseded by:` line and re-running renders a bare
`Superseded`. The field drives the cell.

Generator suite `tests/roster/test_index_records.py`: 48 passed, 2.46s, up from
44. The four added cases cover the composition, the missing-field fallback, the
`none` sentinel, and AC-0032's escaping. `cmp` confirms the two shipped
generator copies stay byte-identical, and both `.claude/` and `.agents/`
projections match their `packs/` source.

## T10 — the new record and ADR-0027's erratum, run 2026-09-17

### The new record: `docs/adr/0117-adr-shape-lint-ships-blocking-not-advisory.md`

Authored by walking `new-adr`'s procedure by hand against the projected
`.claude/skills/new-adr/SKILL.md` step order, rather than through the live
skill dispatcher (no interactive session here to hold the step-7 confirmation
gate open). `python3 .claude/skills/new-adr/scripts/next-ordinal.py docs/adr`
printed `0117`, and `--check docs/adr` reported "no duplicate ordinals" both
before and after the write. **Recording the allocated ordinal here, per the
task's instruction — the spec names this record by role
("the one new-format decision record"), not by number.**

Step 7's confirm-before-coining check was run, not skipped: scanning every
sibling record's `Areas` field (`grep -h "Areas:" docs/adr/*.md`) turned up 24
tokens already in use, including `governance` and `tooling`, so the drafted
`Areas: governance, tooling` value coined nothing and the explicit-confirmation
branch never fires. That is a true negative on the check, not an unexercised
one — the scan ran, found the value already covered, and the record proceeded
without asking. Exercising the branch where a real answer must be given (a
genuinely novel token) would need a separate fixture case in
`test_lint_adr_shape.py`, not a real corpus record — this repository's `Areas`
vocabulary is broad enough that a real, honest decision under governance/tooling
was never going to need one.

Subject, corrected: AC-0015 asks for "the ADR format decision," and RFC-0102's
own Follow-on artifacts list names this record by role — "An ADR recording
this format decision, authored in the new format, shipping with the lint as
its first fixture." The first draft of this record instead headlined the
blocking-vs-advisory rollout posture, which is a genuine and separately
settled decision but not RFC-0102's own format decision, and AC-0015 asks for
**one** record, not a second. Rewritten in place, same ordinal, to record
RFC-0102's actual decision — the metadata block is mechanically checkable
(RFC-0102 §§ 2–3) and acceptance's freeze binds prose, not metadata
(§ 4) — sourced from RFC-0102 §§ 2–5 directly rather than from memory. The
blocking-vs-advisory reasoning is kept, folded in as a Consequence and an
Alternative rather than the headline `Decision`. Renamed with `git mv` to
`0117-adr-metadata-is-mechanically-checkable-and-the-freeze-binds-prose.md` to
match; `git status --short` after the move showed only the rename (`R`), no
lingering empty directory.

**Pinned test — isolated single-record invocation (AC-0015), re-run against the corrected, renamed record:**

    mkdir -p <scratch>/adr-t10-isolated
    cp docs/adr/0117-adr-metadata-is-mechanically-checkable-and-the-freeze-binds-prose.md <scratch>/adr-t10-isolated/
    python3 .claude/skills/new-adr/scripts/lint-adr-shape.py <scratch>/adr-t10-isolated
    read: 1  refused: 0  unreadable: 0      exit 0

**What this isolated run proves, and what it does not.** All four supersession
fields on the new record are the `none` sentinel, so every per-record check
(`ADR-S001`–`ADR-S008`, `ADR-S011`–`ADR-S015`) ran against the record's own
content and is a real pass. The two mirror rules, `ADR-S009` (a cited D-ID
exists in the record it names) and `ADR-S010` (a supersession entry has its
mirrored counterpart), had nothing to pair against: with one record and no
non-`none` supersession field, both rules are vacuously satisfied rather than
exercised. A single-record directory cannot exercise either mirror rule
regardless of the record's content, unless the record cites a sibling that is
absent from the same directory — which would itself only prove the *absent*
branch, not the paired-mirror branch. That branch is what T2's and T3's fixture
suites cover; this run is the manual-QA instance the spec's Testing Strategy
asks for, over the real shipped lint and the real new record, not a substitute
for the fixture coverage of the mirror rules.

**Full-corpus re-run after the new record joined `docs/adr`:**

    python3 .claude/skills/new-adr/scripts/lint-adr-shape.py docs/adr
    read: 117  refused: 0  unreadable: 0      exit 0

Up by exactly 1 from the 116 pre-T10 baseline (confirmed by re-running the
lint before making any change), all attributed to the new record; no other
corpus record's outcome changed.

### ADR-0027's erratum (AC-0016)

One dated `## Errata` entry appended after `## References`, at the position
every one of the eight pre-existing corpus records using `## Errata` already
uses (`0002`, `0013`, `0020`, `0022`, `0036`, `0061`, `0072`, `0079`). It
covers both facts the task names in one entry, dated 2026-09-17: that the
mechanical ADR-status lint this ADR's own `Confirmation` section deferred has
now shipped (citing RFC-0102 and the new ADR-0117 record of that decision),
and that `D5`'s forward-only-migration clause is overridden on RFC-0102's
authority, because the corpus — including this ADR's own frontmatter, which
already carried `Areas`, `Reversibility`, and all four supersession fields —
was migrated ahead of the lint shipping blocking.

**Was the convention usable, as the first real exercise of it?** Yes, and the
part expected to be awkward — picking the heading and deciding whether a
correction needs its own new supersession chain rather than an in-place
entry — was not. `new-adr/SKILL.md`'s "## Recording corrections (Errata)"
section fixes the heading to exactly `## Errata` and states plainly that a
changed decision is a new ADR, never an edit here; that left no judgment call
about *which* mechanism this correction needed. The corpus's eight pre-existing
`## Errata` sections (all predating this delivery, so the heading and the
dated-bold-headline entry shape were already established practice, not
something this delivery had to invent from the SKILL.md prose alone) gave a
real precedent for entry shape and placement, which is why the new entry above
matches their `**YYYY-MM-DD — headline.**` form.

One genuine ambiguity did surface, worth naming rather than papering over: the
convention states entries are "append-only" and a later entry supersedes an
earlier one "by being later," but says nothing about whether an erratum
entry may itself cite metadata-block fields that the `Live` zone still permits
to change after the entry is written (here, `Superseded by:` on a *different*
record, not this one). This record's erratum does not need that — it corrects
meaning, not a supersession pointer — so the gap did not block this task, but a
future erratum that does need to reference a still-mutable field would have no
stated rule for whether the erratum text itself must be treated as frozen
prose the moment it lands, or whether it may be read against the record's
current metadata. Left for whoever writes that erratum; not a defect in this
task's `Done when:`.

**Index regeneration (goal-based check), re-run after the ADR-0117 rewrite and rename:**

    python3 .claude/skills/new-adr/scripts/index-records.py --check docs/adr
    # exit 1 first: line 121 differed (old title/filename still on disk vs.
    # the corrected title/filename), naming exactly that mismatch
    python3 .claude/skills/new-adr/scripts/index-records.py docs/adr
    # exit 0
    python3 .claude/skills/new-adr/scripts/index-records.py --check docs/adr
    # exit 0

`docs/adr/README.md`'s `0117` row now reads the corrected title and links the
renamed file; no other row changed. `next-ordinal.py --check docs/adr` exits
0 (no duplicate ordinals) after the rename — the ordinal did not change, only
the filename and title did.

`tests/roster/test_index_records.py`: 48 passed (unchanged from T9 — T10 adds
no generator case). `tests/roster/test_lint_adr_shape_corpus.py`: 2 passed —
its partition assertion is computed from the live directory listing at run
time, so the new record is absorbed without a code or fixture change.

## T11 — release 0.11.0, changelog, and evals, run 2026-09-17

**Path note.** T11's `Touches` does not admit this file, but its `Tests`
name it as the home for the live-model record (AC-0030). Recorded here per
that instruction; flagging the mismatch rather than silently reaching outside
`Touches`.

### AC-0027 — version strings

    grep -rn "0\.10\.7" --include="*.toml" --include="*.json" --include="*.md" --include="*.yml" . \
      --exclude-dir=.git --exclude-dir=node_modules --exclude-dir=build --exclude-dir=dist

Three hits before the edit: `packs/governance-extras/pack.toml:3`,
`packs/governance-extras/.claude-plugin/plugin.json:3`, and the changelog's
previous release heading (a fourth home would be a discovery, not a
justification to skip it — the search came back exactly three). Both
non-changelog files now read `0.11.0`; the changelog's own heading for this
release also reads `0.11.0` (that's AC-0028, not a fourth version-string
home). Minor: the shipped shape lint and the shared confinement helper are
new primitives, not a content-only patch.

### AC-0028 — heading pattern and placement

New heading `## [governance-extras][0.11.0] — 2026-09-17` sits immediately
after the `[Unreleased]` block's HTML comment and before `## [core][2.26.11]`
— free-standing, at top level, not nested. `python3 -m pytest
tools/test_build_site_routing.py -q`: **94 passed, 1 skipped, 4.40s.** That
suite checks heading level (free-standing vs. nested-under-Unreleased),
exactly-one-blank-line separation above and below every heading, and that
every `### Highlights` child projects into the real `/now/` payload with
matching date and bullet text. It does **not** read whether a released entry
without Highlights recorded a reason — that's AC-0029, checked directly below
because the suite is silent on it by design (per the spec's own note on this
AC).

### AC-0029 — the Highlights decision

Recorded as "yes" — a `### Highlights` subsection is present, four bullets. I
judged by the nature of the change per `packs/AGENTS.local.md`'s question
("does this change what a consumer of the pack can do?"): yes — the template
now requires `Areas` and `Reversibility`, coining an `Areas` token needs
explicit confirmation, superseding a decision is now a two-field pointer
instead of a `Status` edit, and `## Errata` is a new, load-bearing authoring
convention. All four bullets are outcome-led (what an adopter can now do),
none names a plan, a queue, a commit, or a PR, matching the public `/now/`
constraint in `docs/product/AGENTS.md`.

### AC-0030 — eval content

Added eval `id: 15` to `evals.json` (a decision-reversal prompt) and its
matching query to `eval_queries.json` (`should_trigger: true`), per
`packs/AGENTS.md`'s "a non-cosmetic pack update also updates that pack's
eval harness."

**Areas / Reversibility / the mirrored half.** Eval 15's `expected_output`
and `assertions` name `Areas` (the write-gate confirmation check),
`Reversibility` (recorded as a judgement at authoring time), and
`Supersedes:` — read from `new-adr/SKILL.md`'s "Reversing a decision" bullet
(`:315-319`) as the field a *newly authored* record sets on itself. The
mirrored field, `Superseded by:`, lands on the *pre-existing* record being
superseded — an edit to a different file, not something authoring a new
record does — so `Supersedes:` is the half a single authored record can
carry, and eval 15 says so explicitly rather than asserting both halves.

**No eval asserts body immutability — the search and its blind spot.**
Predicate used: case-insensitive substring search over the JSON-serialized
text of both files for `immutab`, `frozen`, `never edited`, `never edit`,
`status-only`, `only edit`, `body is`, `cannot be changed/edited/modified`,
`read-only`/`readonly`, `no edits`, `never rewritten`, `never changed`,
`edit permitted`, `sole normative`, and `rewrite an accepted`. Zero hits
before this task's edit (confirmed by parsing the JSON and counting, not by
reading prose) and zero after — eval 15 uses `frozen` only to describe the
correct, narrower claim (prose freezes except `## Errata`; `Status`,
supersession fields, and `Areas` stay writable), never the retired blanket
claim. Before this task, `git log -p` on `evals.json` located the actual
retired sentence T6 removed: `"After Accepted the body is immutable — a
reversal is a new superseding ADR, never an edit."` (commit `e8e6548de`) —
confirming the concept this AC forbids is exactly that sentence, not merely
its literal words. **What the predicate would miss:** a paraphrase using none
of the listed phrasings and no morphological variant of them — e.g. "the
decision text is settled the moment it's accepted" or "nothing in an accepted
record moves again" — would not match any listed term and would need a human
read or a different predicate to catch. The phrase list is drawn from the
concept's known real phrasing (the retired sentence itself, RFC-0102's own
zone vocabulary, and this delivery's other governing-surface edits in T6/T7),
not from an exhaustive grammar of ways to say "immutable."

**JSON validity:**

    python3 -c "import json; json.load(open('packs/governance-extras/.apm/skills/new-adr/evals/evals.json'))"
    python3 -c "import json; json.load(open('packs/governance-extras/.apm/skills/new-adr/evals/eval_queries.json'))"

Both exit 0. No suite under `packages/agentbundle/tests/` or
`packs/governance-extras/tests/` reads this skill's eval content directly
(searched `eval_queries\|evals.json` across both trees); `make lint-packs`
is the structural oracle that does (see below).

### The live-model run (advisory)

The pinned `Tests` do not make this a gate; recorded here as the spec
requires. `claude` is on `PATH` (2.1.274) and authenticated in this
environment, so a live model **is** reachable from here — this is not the
"cannot run" case.

Ran exactly one bounded, real live-model call, scoped to the query this task
added, rather than the full `agentbundle pack evals run --pack
governance-extras` pipeline (which would run all three of the pack's covered
skills' full `eval_queries.json` sets at the default 3 runs each — dozens of
live calls, minutes of wall time, real API spend — and which the pack's own
`pack.toml` and `pack-evals.yml` commit to a scheduled/dispatch-only,
`continue-on-error` workflow precisely so it never runs ad hoc on the PR
path). Running that full pipeline was outside what this task should spend
without separate authorization; the bounded single-query run below is honest
evidence of capability and of this task's specific addition, not a
substitute for the harness's own scheduled run.

Command, from the repo root (the self-hosted `.claude/skills/new-adr/`
projection makes the skill discoverable here):

    claude -p "We're reversing an earlier architecture decision — record the new choice as a new ADR that supersedes the old one" \
      --output-format stream-json --verbose --allowed-tools Skill

Result: the model's first tool call was `Skill` with `input: {"skill":
"new-adr"}` — the query fired the skill, matching this eval's
`should_trigger: true`. `total_cost_usd: 0.2300236`, `num_turns: 4`,
`duration_ms: 32466`. Full transcript saved at
`/Users/<user>/.claude/projects/-Users-<user>-orca-workspaces-agent-ready-repo-decisions/9e4d45ee-a142-421c-96e7-c5ba934922c2/tool-results/bmfhgtk9t.txt`.

**Out-of-scope observation, not fixed here.** After the `Skill` activation,
the transcript shows a second tool call, `Bash` (`ls docs/adr/`), which
executed and returned real output despite `--allowed-tools Skill`. The
runner's own docstring
(`packages/agentbundle/agentbundle/commands/pack_evals.py:27-30`) states that
restricting `--allowed-tools` to `Skill` keeps the activated skill's body
tools ungranted, "so author-influenced query strings cannot drive side
effects." This single run contradicts that claim on this CLI version
(2.1.274) — worth a follow-on look at the harness's trust boundary, but nested
inside a different, already-shipped file this task's `Touches` does not
admit, and orthogonal to what T11 is scored on.

### Gates

- `make lint-ruff lint-mypy`: both clean (148 source files, no findings).
- `make lint-packs` (`agentbundle catalogue lint --root .`): 1 finding, the
  pre-existing `CAT-L032` INFO on `packs/core` named in this task's brief as
  not this delivery's; nothing new from `governance-extras`.
- `python3 -m pytest tools/test_build_site_routing.py -q`: 94 passed, 1
  skipped, 4.40s.
- `make build-self`, run from the committed T11 content-change state: synced
  the `evals.json`/`eval_queries.json` edits into `.claude/skills/new-adr/
  evals/` and `.agents/skills/new-adr/evals/`; `cmp` confirms both
  projections are byte-identical to the `packs/` source after the sync.

## Round 6 — post-execute implementation review (Codex), 2026-09-17

Reviewer: `codex exec --model gpt-5.6-sol --sandbox read-only`, scoped to the
six implementation files and a pre-extracted diff. Raw report:
`.context/reviews/c1120540-bd0d-4741-8bd6-8421a07557fa/6-post-execute-code-adversarial-codex-raw.md`
(103 lines, 7 findings: 3 Blocker, 4 Concern, 0 Nit). The reviewer could not
run pytest — no writable temp dir under its sandbox — so every finding is
static. Each was reproduced here before being acted on.

### Reproduced and fixed (5)

| Finding | Probe | Before | After |
| --- | --- | --- | --- |
| B1 `ADR-S010` compares ordinals, not D-IDs | pair where A says it superseded B's `D1` and B records its `D2` superseded | exit 0 | exit 1, both records named |
| B1b reverse-only partial attributed to one record | `Superseded in part` with no counterpart | one path | both paths |
| B3 CR in `Superseded by:` reaches the cell | value `ADR-0109\rINJECTED` | `^M` raw in the status cell | value refused, bare `Superseded` |
| C5 `## Corrections` evades `ADR-S015` | correction section under an unobserved spelling | exit 0, no finding | exit 1, `ADR-S015` |
| C5 renaming `## Consequences` retires `ADR-S012` | section renamed `## Outcome` | exit 0 | exit 1, `ADR-S012` |
| C6 oversized D-ID aborts the scan | 5000-digit D-ID | `ValueError` traceback, record in no bucket, no summary | `ADR-S011`, `read: 1`, exit 1 |

Ten tests added, each paired with its discriminating negative, because a
control that has never been observed failing is indistinguishable from one
that cannot fail. The negatives are load-bearing: matching D-IDs must still
pass, a CRLF record must still read its field, and a content section merely
beginning with "Corrected" must not be flagged.

**Two fixes of mine were wrong on first attempt, and the corpus caught both.**
Excluding every control character from the field read also excluded the
trailing CR of a CRLF line ending, which would have made every field
unreadable on a Windows checkout — the repository supports those. And matching
correction headings by word stem plus trailing words flagged ADR-0105's
`## Corrected transition table`, a content section, reddening the real corpus
on first run. Both were caught by running against the corpus rather than
against fixtures alone.

### Two criteria were ticked before they held

AC-0004 and AC-0032 were ticked against passing tests whose fixtures did not
reach the defect: AC-0032's escaping fixture used an ordinary space where the
criterion's own wording names line breaks as the load-bearing case, and
AC-0004's attribution test exercised only the forward direction. Both criteria
hold now. The tick was the error, not the criterion.

### Open, not fixed

- **B2 — check-then-act window in `_record_paths.py`.** The supplied directory
  is tested with `is_symlink()` and then separately opened by `os.scandir`, and
  a candidate classified by `classify_entry` is opened later in
  `read_confined`. `(st_dev, st_ino)` equality proves identity at two instants,
  not across the gap. Closing it means opening the directory once with
  `O_DIRECTORY | O_NOFOLLOW` and resolving every candidate relative to that
  descriptor — a rewrite of the helper, which is byte-identity pinned to the
  `new-rfc` copy. Not attempted; owner decision.
- **C7 — the mutation suite proves one example per class, not every clause.**
  Deleting `ADR-S005`'s duplicate-token loop, `ADR-S011`'s duplicate branch, or
  `ADR-S013`'s Signal/Owner checks would leave the suite green. The hostile
  bucket test asserts `>= 1` per bucket, so double-counting one entry passes.
  `tests/roster/test_lint_adr_shape_corpus.py:74` already names that blind spot.
- **C5's third limb — `<!-- TODO -->` satisfies `ADR-S014`.** A comment-only
  section is non-empty as bytes. The accepted narrowing for S014 was
  "present-and-non-empty", so this matches the criterion as written; recorded
  rather than changed.
