# Why curation is its own pack

`catalogue-curation` sits one meta-level above the rest of the catalogue. Where
`governance-extras` governs *this* repo's decisions, `catalogue-curation` governs
the catalogue's *growth and reproduction* — adding packs, adopting skills,
forking the whole thing. A few design choices explain its shape.

## It's a catalogue-operator pack, not an adopter pack

Most packs earn their place by being a habit a *builder* reaches for. This one's
user is a *catalogue operator* — you, and anyone who forks the catalogue. That's
a narrower audience, which is why the pack is opt-in, repo-scope, and off every
default profile. It cleared the charter's bar as a **forward bet**: the manual
cost of curation suppressed the practice, and lowering it (plus the
ecosystem-growth angle of attributed forks) should make curation routine.

## Single authoritative source, no merge-back

Forking follows the model that keeps confidential-and-public mirrors sane: one
repo is **authoritative**, the derivative is read-only-derived. There is no
"sync my fork's edits back upstream" flow — the only inbound path is a fresh,
reviewed assimilation of a specific unit. This is deliberate: bidirectional sync
between a catalogue and its forks is how divergence and leak accidents happen.

## Fail-closed, because leaking is the worse error

Export scrubbing has two possible mistakes: *omit* a file that was actually safe,
or *ship* one that leaked identity. The pack always prefers the first. The verify
gate hard-fails on any surviving anchor rather than trusting the strip step —
you'd rather re-add an over-omitted file than discover an org's name in a public
fork after the fact.

## Assimilation shapes, it doesn't paste

Bringing a skill in isn't copy-and-reformat. External work carries other
projects' conventions and anti-patterns; assimilation judges the raw content for
safety, then *reshapes* it to this repo's craft — activation, progressive
disclosure, anti-pattern steering — or rejects it. The same craft discipline
applies whether you're adopting a skill or authoring a new one from scratch,
which is why the pack is framed as the operator's toolkit rather than an
import-only tool.

## No new engine

Every part of the pack is skills plus declarative manifests and one lint — no
scheduler, no service, no daemon. That's consistent with the catalogue's other
"loops," and it keeps the pack something a maintainer can read and trust rather
than a black box.
