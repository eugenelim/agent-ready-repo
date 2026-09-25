# converge — selection, commitment, and the doc

`converge` is the only operation that writes a file. `explore` holds candidate sheets in the session; `visualize` writes nothing. Presenting candidates, the standing exit and selection produce the selection. Every act from grounding onward consumes it and cannot run before it.

## Presenting candidates

Present surviving candidates at equal salience. The comparison is limited to the axes on which they differ; axes where all candidates agree are omitted. Show each candidate by its axis tokens, not by adjective or mood word.

## The standing exit

In every divergence round, offer the standing exit alongside the derived candidates: the category standard played straight — the arrangement the audience expects from any product in this space, executed without modification.

- The standing exit is offered in every divergence round, not once and then assumed.
- It is never recommended by the agent; the agent presents it at equal salience and does not weight the choice.
- It is executed at full commitment when chosen: the direction sheet is filled as seriously as any derived candidate, the counterfactual check runs, and the floor applies.
- Presenting it does not require comment or qualification. The name is enough.
- On a route where `visualize` ran, the standing exit is visualised on the same terms as the derived candidates, or none of them are. An unvisualised option beside visualised ones weights the choice.

## Selection

The agent does not choose among materially different directions. A delegated choice is recorded as delegated.

## Ground each goal in stable referents

On a surface with a declared genre, start the precedent referent from the genre tier in `references/referents.md`. For each named goal in the selected direction, name what grounds it: the persona it serves, any precedent that carries the quality, the standards it respects, and the platform conventions for the target surface. A goal with no stable referent is still a fresh opinion — ground it, or push it back to `frame` to be renamed. Load `references/grounding.md`.

## Rank the goals

Order the goals so a tie can break. The dominant goal wins when goals conflict. Load `references/coherence-arbitration.md`.

## Record arbitration

For each likely conflict between goals, name which goal wins and why. The build does not re-litigate a recorded conflict.

## Fill the direction sheet

Fill the direction sheet across all fifteen axes for the selected direction. Each cell opens with its tokens from that axis's vocabulary, then the prose saying what it means here; the audit compares the tokens, not the prose. Grid grammar, alignment and equilibrium, and section and scroll rhythm take exactly two ordered tokens; every other axis takes exactly one. Undecided is `[platform-default]`, never blank.

The first seven axes are structural. Do not leave them at `[platform-default]` by default — decide them.

## Run the counterfactual check

Name a comparator — a similar brief you could plausibly have been given — and work it through. Any part of the direction that matches what you would produce for that brief is a default, not a choice. Revise it. Record the comparator, what it produced, and what changed and why in the doc's `## Counterfactual check` table. That table is a required field of the direction doc: an empty table means the check has not run, not that nothing needed revision.

## Hold the floor

The selected direction must not fight the quality floor at `../design-review/references/quality-floor.md`. Accessibility is not negotiable against aesthetics. If a goal pulls against the floor, the floor wins; record that as an open question, not a trade-off.

## Capture the doc

Resolve `output_dir` by reading `references/agentbundle-layout.md`, then apply every control in `references/containment.md` in the order stated there:

1. **Output-directory approval** — approve the resolved `output_dir` and state it to the operator before composing any path.
2. **Slug validation** — validate the slug before composing any path; refuse and do not repair a non-conforming slug.
3. **Final-target confinement** — execute the real-path resolution immediately before writing; do not reason the path.
4. **Intermediate-directory confinement** — re-establish confinement at each intermediate directory as it is created.
5. **Existing-artifact checks** — check type, surface a matching type to the user, and confirm product belonging when `output_dir` came from user-profile configuration.

The target is `<output_dir>/direction/<slug>.md`. When the target does not exist, copy `assets/creative-direction-template.md` to it. When an approved visual target exists, write the selected direction's compositional commitments into the doc here. `visualize` forms them and writes nothing itself, and on `originate` it may have produced one per candidate: only the selected direction's reaches the doc, the rest are discarded with their candidates. Fill it with: the surface, the ranked goals with their referents, what each goal means and what would violate it, the dominant goal, and the open questions — including any the floor hold above raised.

## Signature device

Record the signature device: the single visual decision that makes the direction recognisable. `refine` holds it fixed, so a direction without one has nothing to hold.

## Borrowed-discipline record

After selection, record the borrowed-discipline field in the direction doc. Write one named discipline taken from a rejected candidate — the technique, structural principle, or visual logic carried forward — or the explicit statement that none was. This field is required; it cannot be left empty.

## Hand off

Once the direction doc is captured, hand to `design-system` to derive the tokens and scales that express the direction.

---

**References:** `references/visualize.md`, `references/grounding.md`, `references/referents.md`, `references/coherence-arbitration.md`, `references/containment.md`, `references/agentbundle-layout.md`, `references/refusals.md`
