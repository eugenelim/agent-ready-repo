## Requested capability: unavailable

Two parts of this request — the plugin package and its hook — are not activation modes for this foundation. The stable result:

```text
contract_version: agent-skill-engineering-foundation/v1
status: unavailable
mode: plugin
reason: not available in the foundation slice
baseline: frame the portable skill concern without inventing mode-specific guidance
```

```text
contract_version: agent-skill-engineering-foundation/v1
status: unavailable
mode: hook
reason: not available in the foundation slice
baseline: frame the portable skill concern without inventing mode-specific guidance
```

So I cannot tell you what a hook can enforce in a host's execution model, or what a plugin manifest costs you — that guidance does not exist here and I will not invent it. What I can do is what you asked for first: frame the portable skill contract underneath, read-only. Several of the claims in the supplied file are decidable at the portable floor, and they are the ones that would poison the package regardless of how the hook is eventually wired.

## What the supplied file asserts that the portable floor contradicts

**The enforcement claim is self-defeating on its own timeline.** The file says the hook "fires after a release is published," then says reporting a violation "stops the release from going out." A check that runs after publication cannot prevent publication; at best it reports on an artifact already in users' hands. This is not a hook-mechanics question — it is a stated-outcome contradiction visible in the prose. Whatever the eventual mechanism, the skill must name a pre-publication decision point or drop the word "block" from its description.

**The policy file is untrusted evidence, and the file grants it authority.** `.release-guard/policy.md` is a repository path whose contents "the hook reads each run and follows whatever rules it states." That inverts the common contract: candidate files, repository prose, and discovered knowledge cannot widen the task, tools, identity, or write authority. A tunable policy file is fine as *data* — a licence allowlist, a changelog-path pattern, a severity threshold, all extracted as expected fields. It is not fine as *instructions*. As written, anyone who can land a commit can rewrite what the guard enforces, including down to nothing, and the guard will comply and report green.

Any read of that path also owes the resolve-before-read discipline: start from the confirmed repository root, reject `..` components and absolute paths supplied as relative names, canonicalize and symlink-resolve before touching contents, and require a regular file. An in-boundary symlink is the obvious escape here and `..`-rejection does not stop it.

**The declared boundary does not cover the declared behavior.** Frontmatter declares `filesystem_read_untrusted` alone. The Slack digest sends external messages over the network. `filesystem_read_untrusted` permits bounded content reads after the confinement check and nothing else; it grants no network access, no credential access, and no external messages. The digest also implies an authentication path — a Slack token — and this foundation carries no authentication implementation. If the digest stays, it needs an external least-authority broker and its own declared boundary, and no repository content may select that identity.

**The description is a bundling claim, not an activation boundary.** "…and bundle the team's release tooling into one installable package" describes distribution, not when an agent should select this skill. Discovery metadata has to discriminate. Prompts that should activate a release-policy check: "does this release pass our licence policy," "is the changelog entry missing for this version," "check the dependency licences before we tag." Prompts that should not: "write the changelog entry," "format this commit message," "post the release digest to Slack." Those last two are different tasks with different outcomes and different boundaries, and the current description would pull the guard into all of them.

**Four components share one activation surface and one dependency graph.** The release hook, the changelog linter, the commit-message formatter, and the Slack digest have no common trigger. The formatter fires on commits, the digest on a schedule or a human ask, the guard at a release gate. Bundling them means the HTTP client the digest needs becomes a dependency of the licence check — you cannot install the guard without installing the network surface. That coupling is stated in the file itself ("the digest command uses the same HTTP client the linter pulls in"). At the portable floor the answer is one skill per outcome, with conditional detail in references rather than co-installed components.

**The shared `release` prefix is chosen to collide.** Matching the team's existing local commands so "muscle memory carries over" means an ambiguous name resolves to either the installed component or the local one, and which wins is not something the skill controls. Deliberate collision with an existing contract is the opposite of preserving it. Whether the eventual packaging format offers namespacing is a packaging question I cannot answer — but the design intent of colliding is wrong before that question is reached.

## The portable frame I would build instead

**Name.** `check-release-policy` — action-oriented, lowercase-hyphenated, under 64 characters, and it names the outcome rather than the bundle. `release-guard` reads as a product name; it does not tell a selecting agent what task it performs.

**Observable outcome.** For a named release candidate, a decision — pass or fail — with each failure naming the offending dependency and its licence, or the artifact missing its changelog entry. The decision is reported before the release is published; the skill states plainly that it advises, and that enforcement belongs to whatever gate consumes the decision.

**Authority and boundaries.** `filesystem_read_untrusted` only. Reads confined to the resolved repository root: the policy data file, the dependency manifest, the changelog. No writes, no network, no credentials, no publication, no external messages. The policy file is parsed for expected fields and embedded directives in it are ignored.

**Portability floor.** A concise `SKILL.md` carrying the activation boundary, the outcome, and the read discipline. Conditional detail — the licence-allowlist schema, the changelog-entry matching rules, how to report a policy file that is absent or malformed — goes to references. A script only if manifest parsing genuinely needs one.

**Evidence.** Success: a candidate with a disallowed licence fails and names it; a candidate with a missing changelog entry fails and names the artifact; a clean candidate passes. Failure and degradation: an absent policy file, a malformed one, and one containing embedded instructions each produce a stated, non-silent result — and the injection case must not change what is enforced. Interruption: a partial read yields no verdict rather than a pass.

**Proposed tree** (nothing created):

```text
check-release-policy/
  SKILL.md
  references/
    policy-file-contract.md
    changelog-matching.md
```

**Non-goals.** Publishing or stopping a release. Writing or repairing changelog entries. Formatting commit messages. Sending digests. Resolving licences from the network. Reading or holding any credential.

The commit-message formatter and the Slack digest are separate concerns and should be framed separately; the changelog linter may fold into this skill's checks or stand alone depending on whether it is ever run outside a release gate. I did not decide that for you.

```text
Mode: frame
Write status: not authorized
```

Files changed: none. Checks run: read the supplied file's inline content only; no repository candidate files were resolved or read, and no filesystem target was confirmed. Unavailable capabilities encountered: `plugin` and `hook` authoring, both reported above. Cleanup: none required.
