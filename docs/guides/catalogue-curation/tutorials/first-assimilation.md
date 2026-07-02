# Your first assimilation

**Goal:** bring one external skill into the catalogue — safely, and shaped to
our craft — end to end. By the end you'll have adopted a skill from a URL and
seen where every guardrail fires.

You need the `catalogue-curation` pack installed (it requires `core` +
`governance-extras`).

## 1. Point the skill at the source

In your agent, say what you want in plain language:

> Assimilate the skill at `https://github.com/some-org/their-repo` (the
> `summarize-thread` skill) into our catalogue.

`assimilate-primitive` activates. It fetches over an allowlisted scheme only
(`https`/`git`) — a `file:` URL or a private/metadata address is refused before
anything is read.

## 2. Read the raw content (this is the security gate)

The skill shows you the **raw fetched body, verbatim** — not reformatted. This
is deliberate: an external skill is instruction prose that will run in your
agents and, if you ever fork, your users' agents. Read it as untrusted input.
If the unit is (or contains) a **hook or script**, you'll be asked to explicitly
confirm the code before it can land.

Behind the scenes the skill also runs the repo's own lints and SAST/SCA over the
candidate — the same gates your own code passes. A failure stops the landing.

## 3. Watch it shape to our craft

Once you've accepted the content as safe, the skill reshapes it to convention —
it doesn't just reformat:

- rewrites the `description` for activation and **checks it for collision** with
  every existing skill (you'll be told if it clashes);
- moves detail into `references/` and mechanical steps into `scripts/`;
- glosses jargon for a cold reader;
- **steers anti-patterns** — if the skill triggered another skill from a script,
  or misused an agent, it's corrected to our shape or the assimilation is
  rejected, with the reason named.

Where a real judgment is needed (which pack, what to name it), the skill offers
you the options and its recommendation — it guides, it doesn't dump.

## 4. Approve and land

You see the shaped target before it's written. Approve, and it's written into the
destination pack through the engine's path-jail (nothing escapes `packs/`). The
skill prompts you to run `make build-self` so the projection tracks the new
source.

## What you just relied on

Every step had a guardrail: scheme allowlist, raw-content review, code confirm,
repo lints/scanners, collision check, anti-pattern steering, path-jail. That's
the difference between *adopting* a skill and *pasting* one. Next: survey a whole
repo at once — see [Survey a repo](../how-to/survey-a-repo.md).
