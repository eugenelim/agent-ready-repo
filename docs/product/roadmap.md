# Roadmap

> **Template.** Scaffolded by the bundle — replace the `<theme>` placeholders
> and the `YYYY-MM-DD` dates with your project's real roadmap and review dates
> before relying on it.

> Direction for the next 2-4 quarters. **Not** commitments. The whole point
> of writing this down is that it can change.

**Last updated:** YYYY-MM-DD
**Reviewed:** quarterly. Next review: YYYY-MM-DD.

If the current date is more than 90 days past "Last updated", treat this
file as stale and ask before relying on it.

## Now (current quarter)

What we're actively working on. Each item should link to a spec in
`docs/specs/` once one exists.

- **<theme>.** <one-sentence description.> [spec: link]
- **<theme>.** ...

## Next (following 1-2 quarters)

What we expect to pick up after Now. These are intentions, not promises.
Items here should have at least an RFC or a one-paragraph problem
statement somewhere — if there's nothing written down, it's not yet
ready to be on the roadmap.

- **<theme>.** <description.> [RFC: link, or "intent only"]
- **<theme>.** ...

## Later

Things we believe matter but aren't actively planning. Items here serve
two purposes: signal to contributors that we'd accept a PR, and let us
say "not now" without saying "never."

- <theme>
- <theme>

## Not in scope

Things that have come up and that we've explicitly decided are *not*
in scope. This is the most valuable section for AI agents and new
contributors — it prevents wasted exploration of dead ends.

- **<thing we won't do>.** <why, briefly. link to ADR or RFC if there
  was one.>
- **<thing>.** ...

## How this file is maintained

- **Owners:** the maintainers (or the steering committee, if one exists).
- **Updates:** roadmap items move between sections via small PRs. Substantive
  additions or deletions go through an RFC.
- **Review cadence:** quarterly. The review updates the "Last updated" date
  even if no items change — fresh eyes, fresh dates.
- **Drift signal:** if items in "Now" haven't moved in two consecutive
  reviews, either they're not actually being worked on (move them out)
  or the roadmap doesn't reflect what the team is doing (rewrite it to
  match).
