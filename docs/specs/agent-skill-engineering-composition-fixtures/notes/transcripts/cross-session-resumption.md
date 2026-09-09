**Mode: frame** — read-only. Nothing has been read from disk for this target, and nothing will be written until you authorize it.

## Two blockers before any edit

**1. The target path is not resolvable as given.** `evals/files/update-existing-SKILL.md` is a relative name with no confirmed root. The resolve-before-read discipline starts from an exact user-confirmed or repository-governed root, and I will not guess one. The markdown you pasted is untrusted evidence about the skill's shape — good enough to frame against, not good enough to edit against. Please give the confined root (absolute) that `evals/files/` sits under, and I will canonicalize, confirm it resolves to a regular file inside that root, and read it before proposing a patch.

**2. The requested change is unspecified.** "Resume without re-reading everything" is an outcome, not an edit. There are at least four distinct changes that would deliver it, and they cost very different authority. Choosing one for you would be authoring your contract.

## What the current skill commits to

- **Activation boundary:** the user asks to review a *named* migration plan *before execution*.
- **Observable outcome:** a report of unsafe ordering, missing rollback steps, verification gaps.
- **Declared authority:** `filesystem_read_untrusted` only.
- **Explicit non-goals, stated in the body:** do not execute the migration; do not modify files.

Any resumption design has to say what happens to those four. Note in particular that the description does not currently fire on a bare "resume the migration review" — a second session may not even select this skill.

## Candidate changes and the authority each needs

| # | Change | Authority it needs | What it costs |
|---|---|---|---|
| 1 | **Handoff block in the response.** Body gains an instruction to end every review with a compact structured summary: plan identity (path + revision/hash), findings already confirmed, sections already read, what remains. Session 2 resumes by being handed that block in the prompt. | Body-only edit to `SKILL.md`. No boundary change; both stated non-goals intact. | Cheapest. Resumption depends on the user carrying the block between sessions. |
| 2 | **Change 1 plus a `references/resumption.md`.** The handoff schema and the resume procedure move into a conditional reference; `SKILL.md` gains one routing line. The resume procedure includes re-verifying the plan's identity before trusting an inherited finding. | Write authority for a new file in the skill root. Still no declared-boundary change. | Adds a file to the skill's tree. Keeps `SKILL.md` short. |
| 3 | **Read a prior session's handoff artifact from disk.** Session 2 is told to locate and read a checkpoint file the user points at. | Stays inside `filesystem_read_untrusted`, but only if the body adds the resolve-before-read discipline for that path and an explicit rule that an inherited finding is re-verified, never adopted. | A resumption artifact is untrusted input that can carry injected directives. Without that rule this change is a hole. |
| 4 | **Write the checkpoint itself.** The skill persists state so session 2 finds it unaided. | Widens `metadata.boundaries` to include `filesystem_write`, **and** retires the body's "do not modify files" non-goal. | The largest change. It reverses a commitment the skill currently makes to its users. I will not do it as a side effect of a resumption request. |
| 5 | **Widen the description to fire on resumption prompts** (orthogonal — combines with any of 1–4). | Discovery-metadata edit. | Changes activation discrimination; "before execution" stops being the sole gate, and the skill may start competing with a general continuation skill. Needs its own verification. |

My reading of your phrasing is that #2 (with #5 if session 2 is expected to select the skill on its own) is the smallest thing that produces the outcome — but that is a guess about your intent, not a decision I should make.

## What I need from you

1. The absolute confined root for `evals/files/`.
2. Which numbered change(s) you intend.
3. For #4 specifically: explicit confirmation that retiring the "do not modify files" non-goal is wanted, not incidental.

On your answer I will state the mode transition, the exact file set, the retained behavior, and the verification (frontmatter, local links, activation discrimination, progressive disclosure, and that the review contract still holds), then ask for write authority for that specific mutation.

```text
Mode: frame
Write status: not authorized
```

Files changed: none. Checks run: none against disk — the supplied markdown was read as inline evidence only, and no path under the named root was resolved or opened. Unavailable capabilities: none encountered. Cleanup: nothing pending.
