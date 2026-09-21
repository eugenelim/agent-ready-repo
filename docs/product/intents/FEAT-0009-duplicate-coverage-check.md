# Intent: promotion stops creating an artifact that already exists

- **Slug:** `duplicate-coverage-check` <!-- canonical identity; independent of the filename ordinal -->
- **Status:** Accepted
- **Level:** `feature`
- **Owner:** eugenelim
- **Kind:** `opportunity`
- **Scale:** `app`
- **Maturity:** `brownfield`
- **Parent intent:** work-item-capture-and-disposition — [Work-item capture and disposition](CAP-0005-work-item-capture-and-disposition.md)
- **Depends on:** docs/product/intents/FEAT-0007-work-item-promotion-routing.md <!-- stated for a reader; the enforceable edge is a typed `needs` entry on the workspace registration, which does not exist yet -->

## Outcome

Promoting a captured item does not create a second artifact for an outcome an
existing one already covers.

**How we will know.** Two measures, because one alone can be satisfied by doing
nothing useful.

- **The result.** The share of promotions that create an artifact duplicating
  one that already existed, judged by a reader after the fact.
- **The guardrail.** The share of promotions that wrongly attach an item to an
  existing artifact, or that a human abandons because reviewing the offered
  alternatives cost more than creating the artifact.

An earlier draft measured only whether a covering artifact appeared among
surfaced candidates. That measures a mechanism's recall, not this outcome, and
returning the whole corpus would have satisfied it.

## Opportunity

Promotion that creates by default grows the artifact corpus faster than it
drains the store. Any repository running this already holds artifacts with
near-duplicates among them, and a router that always creates makes that worse at
machine speed — faster the larger the corpus already is.

The failure is quiet, which is why it needs a measure of its own. If nothing
useful is offered, the human creates anyway; the store still drains, so the
promotion feature reads green while doing the thing this exists to prevent.

**One mechanism is already refuted, and the refutation is the useful part.** A
match on the paths a captured observation carries was probed against this
repository's own backlog and fired its kill line. The probe is one command, so a
reader re-derives it rather than trusting a figure here:

```
python3 -c "
import tomllib,collections,os
o=tomllib.load(open('workspace.toml','rb'))['backlog']['open']
b=collections.Counter(os.path.dirname(x['path']) for x in o if x.get('path'))
n=sum(b.values()); top=b.most_common(1)[0]
print(n,'entries;',len(b),'directories; largest',top[1],'in',top[0],
      '; singletons',sum(1 for v in b.values() if v==1))"
```

It reports a corpus where most entries share one directory and most directories
hold exactly one entry. Path proximity is therefore near-constant across the
bulk and absent elsewhere: a match returns most of the corpus or none of it,
with no middle where a short list exists. Running it on two days a fortnight
apart already gave different counts and the same shape — which is the argument
for the command over the number.

The reason is not a namespace mismatch — observations may carry documentation
paths as readily as code paths, and in the existing corpus the documentation
root is the most common. The reason is that an artifact's path does not encode
what it covers, and the artifact corpus is concentrated in one directory. So
path proximity is nearly constant across it and carries almost no signal.

What survives is the outcome, not the mechanism. Whether coverage is discoverable
at all depends on what artifacts happen to record about the territory they
concern, and no field carries that — it appears in body prose where it appears,
which varies by repository and by adopter.

## What exists today

**Snapshot taken 2026-09-19.** These are locations, not contents. Each names a
file and why this intent cares about it, and deliberately reproduces no value,
status, field content or count from it — a copy would be a second home for
another artifact's state, and the date would record only when the copy was made,
not whether it still holds. Open them.

- **Where artifacts live.** `docs/` holds the intent, spec, decision-record and
  proposal trees, plus the registers under `docs/product/findings/`. Which of
  them a check searches is a spec decision, not settled here.
- **What an intent records about its territory.**
  `packs/product-engineering/.apm/skills/frame-intent/assets/intent-template.md`.
  Read its field list against the question of whether coverage is machine-findable.
- **What a captured item records about scope.** `_validate_project_scope` in
  `packs/core/.apm/skills/project-knowledge/scripts/project_knowledge.py`.
- **Where the refuted probe was taken.** The `[backlog].open` array in
  `workspace.toml`.
## Upstream state, 2026-09-21

The capture contract ships. Two facts bear on this child's measure:

**A necessity razor already runs at capture.** Every `work-item` carries a
`necessity_rationale` and is refused unless a cold reasoning check admits
it. That check is asked whether the item clears the razor, not whether an
artifact already covers it, so this child's question is still open — but
the volume reaching it is smaller than an unfiltered capture stream.

**Path proximity is refuted** as a coverage signal; the surviving question
is whether coverage is discoverable at all.

This child remains blocked on `docs/specs/work-item-promotion-handoff/spec.md`,
which is not built.

## Non-goals

- **Deciding.** Whatever is offered, a human accepts or rejects it.
- **The augmenting write.** Editing, appending to, and linking an existing
  artifact are three different contracts; none is settled here.
- **The governance route.** Independent — the corpus to search is the same
  whichever record types exist.

## Assumptions

- A human is present at the point this matters. An unattended promotion has
  nobody to offer alternatives to.
- The corpus to search is the artifacts the repository already holds, whatever
  their kinds and lifecycle states.

## Decomposition

None. One outcome, measured on both sides.

## De-risk

**Reversibility: mixed.** The check writes nothing and can be switched off. Its
errors are not reversible in the same way: a miss lets promotion create a
duplicate artifact, and a wrong offer can attach an item to the wrong artifact.
Turning the check off restores future behaviour and undoes neither.

**Riskiest assumption, revised after the first probe killed its predecessor.**
*Coverage is discoverable at all from what a captured item carries and what the
corpus records.*

The original assumption was that a path match would surface it. That was
predeclared with a kill line, and the probe fired it. The assumption moves up a
level rather than being restated at a lower one.

If nothing discoverable exists, this check is decoration: it adds a step,
changes no outcome, and the duplication persists behind a control that reads as
present.

**Kill condition, with its basis and a bound on both sides.** Over ten captured
items whose covering artifact is known, either half fails:

- **Reach.** The covering artifact is not offered for seven of the ten.
- **Precision.** Across those ten, the offers a reader has to read through to
  find it are more numerous than the artifacts they would have created by hand.

Capping the list length was the earlier draft's attempt at the second half and
does not achieve it: a short list of consistently wrong entries still costs a
reader more than it saves. Precision is about what is in the list, not how long
it is.

Neither threshold is derived from an observation. Seven of ten is a placeholder
for "often enough to be worth opening", and the precision half has no number at
all — both need a basis before this is a test rather than a gesture.

**Deriving them is this intent's, not its spec's.** A kill line is the
instrument this intent uses to decide whether its own bet survives, so a spec
cannot replace it without replacing the bet. The spec derives its own
acceptance thresholds, which answer a different question — whether the built
mechanism is good enough to ship — and the two pairs of numbers are not
interchangeable. Until this intent derives its pair, the kill line stays a
gesture and this artifact says so rather than delegating it.

**The next probe draws unseen items, and this is a requirement rather than a
preference.** The ten used for the path probe are now contaminated: their
coverage is known to whoever ran it, so a mechanism developed against them can
be tuned to them without anyone intending it. The next test draws ten that
have not been inspected. If ten with independently known coverage cannot be
found, that is itself a finding — it means ground truth is scarce, and a
measure built on scarce ground truth will not survive contact.

```
validation_hook:
  assumption: coverage is discoverable at all from what a captured item carries
    and what the corpus records
  kill_condition: over 10 items with known coverage, no available mechanism
    offers the covering artifact within a list of 5 for at least 7. The 5
    bounds what a probe run shows a reader and is not a precision threshold:
    the prose above records that capping length does not achieve precision.
    It does not bind the delivered offer contract, whose list size is the
    spec's
  activity: try body-text search over the artifact corpus on ten previously
    uninspected items; have the owner judge each result as correct offer,
    correct no-offer, or wrong
  scope: this tests one mechanism. A failure refutes body-text search, not the
    assumption — the assumption survives until no available mechanism reaches
    the line, and each candidate is refuted on its own evidence
  known_weakness: a single adjudicator, so the judgement is not reproducible
    across readers
  refuted:
    - path matching. Kill line fired against this repository's backlog: an
      artifact's path does not encode what it covers, and the corpus is
      concentrated in one directory, so path proximity is near-constant.
```

## For the spec to decide

- **What "covers" means**, and how ground truth is established for measuring it.
- **The candidate universe** — which artifact kinds and lifecycle states are
  searched, and whether a retired or superseded artifact can cover an item.
- **The offer contract** — maximum list size, ordering, the minimum evidence an
  entry needs to be worth showing, and what is shown when nothing qualifies.
- **What happens on acceptance.** Attaching an item to an existing artifact is a
  write with a review path, and it is not specified anywhere yet.
- **Multiple valid covering artifacts**, and which one an offer should prefer.
- **Portability.** Repositories differ in artifact kinds, paths and prose
  conventions, so any mechanism that works here needs a stated reason to work
  elsewhere.
