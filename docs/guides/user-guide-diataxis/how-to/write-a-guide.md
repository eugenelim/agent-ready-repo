# How to write a guide

This guide is for someone documenting a feature that already ships and who wants the page to land in the right Diátaxis kind the first time. It assumes you've installed the `user-guide-diataxis` pack and that your agent can run the `new-guide` skill.

New to the four kinds? Read [About the Diátaxis framework](../explanation/the-diataxis-framework.md) first — it's the model this procedure rests on.

## Before you start

You need:

- The `user-guide-diataxis` pack installed, so your agent can reach the [`new-guide`](../../../../packs/user-guide-diataxis/.apm/skills/new-guide/SKILL.md) skill.
- A real reader in mind. "Someone might want to know X" isn't a reader; "an adopter who installed `credential-brokers` and needs to rotate a token" is.
- Behavior that already ships. Guides are living docs that match current product behavior. Documenting something you're proposing? You want an RFC or a spec, not a guide.

## Steps

1. **Invoke the skill.** Tell your agent what you're documenting: `write a guide for rotating a credentialed-skill token`. The skill triggers on phrases like "write a guide for X", "new tutorial", "new how-to", "new reference page", "new explanation".

2. **Settle the audience contract.** This is a gated checkpoint — the skill writes no body until you sign off. It surfaces a contract naming the reader's posture, the kind it implies, and a working title:

   ```markdown
   AUDIENCE CONTRACT:

   ## Reader profile
   - Right now they are: <on rails | has a specific problem | scanning for a fact | reflecting>
   - They leave with: <a working artifact | their problem solved | the precise answer | a clearer model>

   ## Quadrant pick
   - Quadrant: <tutorials | how-to | reference | explanation>
   - Why this one (not the adjacent quadrants): <one sentence>

   ## Title (working)
   - Title: <draft>
   - What the reader would have typed into search: <phrase>
   ```

Read it. Accept it, or push back if the kind looks wrong. The contract is the cheapest place to catch a mismatched kind — fixing it once prose is on the page costs far more.

3. **Pick the kind by reader posture, not by topic.** The skill maps posture to kind: on rails wanting a guaranteed result is a tutorial; a named problem wanting the recipe is a how-to; scanning for the authoritative answer is reference; wanting to understand *why* is explanation.

4. **Let the skill scaffold from the matching template.** Each kind has one template carrying its minimal section structure. The skill copies the right one to the per-pack write path:

`docs/guides/<pack>/<quadrant>/<slug>.md`

So a how-to in this pack lands at `docs/guides/user-guide-diataxis/how-to/<slug>.md`. The slug is short and noun-y, matching what the reader would search for — `rotate-credentialed-skill-token`, not `how-to-rotate-your-token-step-by-step`. The quadrant directory already carries the framing; don't repeat it in the filename.

5. **Draft inside the kind's rules, applying link-out.** When you reach for material from an adjacent kind, write a link instead of the material. Tempted to explain *why* mid-tutorial? Link to an explanation. Tempted to list every option mid-how-to? Link to the reference. The link can be a placeholder until the other page exists.

6. **Run the skill's self-check, then cross-link real siblings only.** The skill walks a kind-specific checklist for leaks, then adds a `See also` section. It links a sibling only when the file exists, and surfaces the missing ones as follow-up TODOs rather than writing a broken link.

## Variations

- **The contract splits into two readers or two postures.** That's two guides, not one. Pick the first; the second goes to follow-up. The skill surfaces the split rather than cramming both into one page.
- **You're editing an existing guide, not writing a new one.** The skill is for new pages. Edits are normal PRs against the existing file. The kind's writing rules still apply; the checkpoint and scaffold don't.
- **The page won't sit in one kind.** If a "tutorial" can't actually be run end to end to produce its promised result, it's a how-to or an explanation. Re-open the contract.

## Common pitfalls

- **Writing prose before the contract is signed off** — the body is gated for a reason. Confirm the kind first.
- **Picking the kind by topic** — "authentication" is a topic, not a kind. *Learning* it, *configuring* it, and *understanding* it are three different pages.
- **Narrative voice in reference** — "you'll want to set this to…" is explanation leaking in. Reference says *what*; recommendations live in explanation.
- **Explanation with no *About <X>* frame** — open-ended explanation absorbs adjacent material and sprawls. Name the question the page answers.
- **A tutorial you never ran** — one that doesn't produce its promised result is worse than none. Run the steps end to end.

## See also

- [About the Diátaxis framework](../explanation/the-diataxis-framework.md) — the four kinds and the link-out discipline behind this procedure.
- [`new-guide` skill](../../../../packs/user-guide-diataxis/.apm/skills/new-guide/SKILL.md) — the full procedure the skill runs.
- [The catalogue framework](../../README.md) — how the packs fit together.
