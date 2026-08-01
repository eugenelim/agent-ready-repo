# Expected behavior: anti-pattern detection and steering

Answer key for AC5. The live QA session exercises detection against one of the
three fixture files in `fixtures/antipatterns/`. This document describes the
expected detection output and corrective reshaping for each fixture.

Source authority:
`packs/catalogue-curation/.apm/skills/assimilate-primitive/references/anti-patterns.md`

---

## Pattern 1: skill-triggers-skill (fixture: skill-triggers-skill.md)

### Why this is rejected / steered

The fixture (`run-quality-gate`) contains a procedure step that invokes a
second skill by shelling out to the Claude CLI:

```
claude --print "Run lint-check on the current working tree"
```

This is anti-pattern #1 from `anti-patterns.md`: **a script or hook that
triggers a skill or agent**. The tell is the `claude --print` invocation
embedded in a procedure step; the skill's job is to activate the `lint-check`
skill deterministically, which is not how skill activation works (skills
activate by description, not by being called from another skill).

Because the primitive exists *only* to auto-trigger another primitive
(`lint-check`), the correct disposition is **reject**, not reshape.

### Expected detection message

The assimilation skill should surface a message similar to:

> **Anti-pattern detected: script triggers skill** (anti-patterns.md §1)
>
> `run-quality-gate` step 3 invokes `lint-check` via `claude --print "..."`.
> Skills activate by description — they are not called from other skills or
> scripts. This primitive's sole purpose is to auto-invoke `lint-check`, which
> is the pattern the catalogue forbids.
>
> **Disposition: Reject.** There is no reshapeable form — split the
> deterministic formatting work into a standalone script and let `lint-check`
> activate through its own trigger description.

### Reshaped form

Not applicable — this primitive is rejected. The correct separation is:

- A standalone script `scripts/format.py` (data in / data out: runs ruff format
  and ruff check, exits non-zero on failure, no skill invocation).
- The `lint-check` skill activates independently from its own trigger surface;
  it is never called from `format.py`.

---

## Pattern 2: agent-reviews-own-output (fixture: agent-reviews-own-output.md)

### Why this is rejected / steered

The fixture (`doc-author-agent`) instructs the agent to self-review its own
draft in step 4:

> Self-review your draft: Re-read the document you just authored … Score each
> section … Revise any section scoring "needs revision."

This is anti-pattern #2 from `anti-patterns.md`: **an agent used the wrong way
(self-review)**. Agents don't mark their own homework. A self-review step
doesn't provide an independent perspective and gives the operator false
confidence in the output's quality.

### Expected detection message

> **Anti-pattern detected: agent self-review** (anti-patterns.md §2)
>
> `doc-author-agent` step 4 instructs the agent to re-read and score its own
> output. Self-review provides no independent signal and violates the
> reviewer-after-implementer pattern.
>
> **Disposition: Steer.** Remove the self-review step. The reshaped form
> presents the draft directly to the operator and routes a quality review to a
> separate reviewer subagent or human reviewer — not the authoring agent.

### Reshaped form

Step 4 becomes:

> Present the draft `docs/<topic>.md` to the operator. If a structured quality
> review is needed before sign-off, route it to a reviewer subagent (e.g.
> `design-reviewer` or `experience-reviewer`) — not this agent.

The "self-certification" claim in the Output section is removed.

---

## Pattern 3: flooding-prompt (fixture: flooding-prompt.md)

### Why this is rejected / steered

The fixture (`deploy-microservice`) is a SKILL.md that:
1. Opens with an "IMPORTANT: Read this before starting" meta-instruction.
2. Enumerates 10 environment variables with multi-sentence per-variable
   explanations inline (should be in `references/deployment-vars.md`).
3. Repeats "Do not proceed" and "stop and notify" instructions on nearly every
   line rather than stating them once.
4. Closes with a "REMINDER: Important notes" wall that re-states every rule
   already given in the procedure.

This is anti-pattern #3 from `anti-patterns.md`: **a flooding prompt**. The
SKILL.md dumps a wall of instructions where progressive disclosure (detail →
`references/`, mechanical steps → `scripts/`) should apply.

### Expected detection message

> **Anti-pattern detected: flooding prompt** (anti-patterns.md §3)
>
> `deploy-microservice` repeats identical prohibitions ("Do not proceed", "stop
> and notify") on 14 separate lines, embeds 10 environment variable
> specifications inline, and closes with a 9-item "REMINDER" block that
> duplicates the procedure text. The result is a wall of instructions that
> exhausts context and buries the actual decision points.
>
> **Disposition: Steer.** Reshape using progressive disclosure:
> - Move the 10 env-var specs to `references/deployment-vars.md`.
> - Move the rollback procedure to `references/rollback.md`.
> - State each "stop and notify" rule once in a "Never do" section.
> - Remove the "IMPORTANT" preamble and the "REMINDER" closing block.
> - The SKILL.md body should reference `references/` files, not inline them.

### Reshaped form (outline)

```
# Skill: deploy-microservice
[terse description of when to use and what it does — 2–3 sentences]

## Procedure
1. Validate environment (see references/deployment-vars.md).
2. Validate Git state (clean tree, correct branch, up-to-date with origin).
3. Build and push: docker build + push + manifest verify.
4. Deploy: kubectl rolling update + rollout status.
5. Verify health (see references/health-check.md).
6. On any failure: trigger rollback (see references/rollback.md).

## Never do
- Deploy with IMAGE_TAG=latest.
- Deploy from a feature branch.
- Proceed past a failing step.
```
