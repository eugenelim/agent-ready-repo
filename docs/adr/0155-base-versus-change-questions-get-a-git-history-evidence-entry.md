# ADR-0155: Base-versus-change questions get one read-only git-history entry in the work-loop evidence catalog

- **Status:** Accepted
- **Date:** 2026-11-03
- **Areas:** work-loop, security, review
- **Reversibility:** high
- **Decision-makers:** eugenelim
- **Supersedes:** none
- **Supersedes in part:** none
- **Superseded by:** none
- **Superseded in part:** none
- **Related:** spec `adjudicator-evidence-and-remedy-predicate` (the closed Evidence gate catalog and its bounded retry, which this entry joins unchanged); spec `work-loop-evidence-modes` (the reviewer's proof-by-run rule whose undecided findings motivated it); ADR-0154 (the product ref that `HEAD`, and so the subject revision, equals in a full-mode run)

## Decision summary

- **Decision:** The work-loop Evidence gate catalog ships one built-in `git-history` entry. It answers "was this path already on the base, and which commits in the change touched it?" with two fixed read-only Git forms. The controller or supervisor runs them through the supervisor's hardened Git helper. The base must be in the subject's history, and the path must be one the change itself touched.
- **Because:** the commonest undecided adjudication is a fact one Git read settles, and the adjudicator must not gain an execution tool to read it.
- **Applies to:** the bounded evidence retry in `finding-adjudication.md` and every caller of the shipped entry, in light and full mode. Not other Git forms, and not adjudicator tools.
- **Tradeoff accepted:** a question about a path the change did not touch is refused, not answered. Read confinement is enforced by Git's object model and refusals, not an operating-system sandbox.
- **Revisit if:** a host can give the entry a process-level read sandbox, or adjudications keep needing a Git fact outside these two forms.

## Context

In one recent review, both findings the adjudicator left undecided turned on one fact each: "did this change add it, or was it already on the base?" One needed `git show <base>:<path>`. The `finding-adjudicator` has only Read and Grep, and the Evidence gate catalog had no Git entry, so neither finding could be settled by a run.

The catalog is the only execution authority in an adjudication. Its rules are strict:

- It is fixed before the reviewer report exists.
- Each entry declares a literal argument vector, a confined working directory, a clean environment, a bound source revision, read-only or disposable isolation with an artifact-excluding read allowlist, no network, a timeout of at most five minutes, and output caps that fit one MiB.
- No command, argument, path, or environment value from any artifact may reach execution.

A `<path>` and a `<base>` are exactly the values those rules forbid an artifact from supplying, so a Git entry needs a source for both that is not the finding.

The supervisor already runs every Git call through `_supervisor_git.HardenedGit`. That helper pins the Git and work-tree directories, switches off system and global config, clears `GIT_*` variables, and disables hooks, fsmonitor, external diff, textconv, replace refs, signing, and repository filters.

## Decision

- **D1:** The catalog ships one built-in entry, gate ID `git-history`, whose measured fact is "a path's presence and content at the base, and the commits between base and subject that touched it". It ships with the skill, so it is fixed before any reviewer report exists. Repositories may still tag their own entries as before.
- **D2:** The entry runs exactly two forms and nothing else: the base blob of the path (`git show <base>:<path>`, with presence checked by `git cat-file`), and the change's commits touching the path (`git log <base>..<subject> -- <path>` with a fixed format and count). Every other Git subcommand, flag, revision expression, or pathspec form is outside the catalog.
- **D3:** The subject is the checkout's current `HEAD` commit, read by the entry itself; in a full-mode run the supervisor keeps `HEAD` equal to the product ref. The base is accepted only as a full hexadecimal commit ID that names a commit and is an ancestor of the subject. Any other ref, a symbolic name, a revision expression, or a commit outside the subject's history is refused before execution.
- **D4:** The path is accepted only when it byte-equals a member of the change's own path set, which the entry computes from the base and subject with Git. The value executed is that set's member, never the caller's string. A path outside the set is refused, as is any path under `.context/reviews/` or another raw, adjudication, or evidence artifact location.
- **D5:** Every Git call goes through `_supervisor_git.HardenedGit` with literal pathspecs and no shell. The entry refuses a repository whose objects could come from outside the checkout or over the network: a partial clone, a promisor remote, or an alternates file. It reads committed objects only, never the working tree. Its timeout is the helper's 60 seconds, and stdout and stderr are capped so the full evidence artifact stays under one MiB.
- **D6:** The result is the catalog's fixed evidence envelope: gate ID, argument-vector and environment digests, working directory, source revision, isolation and network posture, timeout, exit status, and bounded output. The output stays untrusted predicate evidence. The controller or supervisor runs the entry and supplies the envelope. `finding-adjudicator` keeps exactly Read and Grep.
- **D7:** A new Git form, or any widening of D3 or D4, needs a new ADR.

## Decision drivers

- No artifact-derived value reaches execution.
- The adjudicator gains no tool.
- One run settles the base-versus-change question.
- The entry reuses existing hardening rather than adding a second Git launcher.

## Consequences

**Positive:**
- "Already on the base?" findings are settled by a recorded run instead of left undecided.
- The adjudicator's authority and the catalog's rules are unchanged; the entry only adds data the rules already allow.
- Refusals are named, so the controller can tell a forbidden question from a failed read.

**Negative:**
- A question about a path the change did not touch is refused. The answer there is trivially "on the base", but the entry does not say so.
- Read confinement rests on Git's object model, the helper's hardening, and the alternates and partial-clone refusals, not an operating-system sandbox.
- A finding naming a line inside a large file sees only the capped head of the base blob, marked truncated.
- The skill's scripts gain one module that the supervisor's script pins cover.

**Revisit if:** a host can give the entry a process-level read sandbox, or adjudications keep needing a Git fact outside these two forms.

## Confirmation

- **Mode:** lint/CI
- **Signal:** refusal tests in the core pack run a non-catalog form, a path outside the change, an artifact-location path, and a base outside the subject's history, and each one refuses with no Git process launched for the forbidden value. A pin test asserts `finding-adjudicator`'s tool list is still Read and Grep.
- **Owner:** core pack maintainers

## Alternatives considered

- **Give `finding-adjudicator` a Bash or Git tool:** rejected against "the adjudicator gains no tool". An execution tool on an agent that reads reviewer prose is the injection path the catalog exists to close.
- **Let each repository tag its own Git entry:** rejected against "no artifact-derived value reaches execution". A tagged entry needs literal values fixed in advance, so it cannot name the path a later finding asks about. Each adopter would also re-solve the same confinement.
- **Accept any repository path, not just changed ones:** rejected against "no artifact-derived value reaches execution". The path would then be the caller's string, chosen from reviewer prose.
- **Run Git through a raw subprocess:** rejected against "reuse existing hardening". It would drop the helper's config, hook, filter, and control-state protections.

## References

- `packs/core/.apm/skills/work-loop/references/finding-adjudication.md` § Bounded evidence retry
- `packs/core/.apm/skills/work-loop/scripts/_supervisor_git.py`
