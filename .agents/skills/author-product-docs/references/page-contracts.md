# Page contracts

Each section below is the contract for one artifact type. Load only the section that matches the artifact you are writing or revising. The contract answers four questions: what the first screen must make obvious, what content is required, what to move lower or link out, and what to refuse.

Diátaxis is an authoring contract, not a directory structure. A how-to guide follows the how-to contract wherever the repository keeps it. The file's location does not change what it promises the reader.

## Choosing the right kind

Choose a tutorial, how-to, reference, or explanation by reader posture: what the reader is doing right now, not what topic they are reading about. The same person, on different days, lands in different kinds.

| Reader's posture right now | Kind |
| --- | --- |
| On rails, attentive, wants a guaranteed working result | **Tutorial** |
| Has a named problem, wants the recipe | **How-to** |
| In a hurry, scanning for the authoritative answer | **Reference** |
| Away from the keyboard, wants to understand *why* | **Explanation** |

Choose every other artifact by journey stage: the README, quickstart, installation guide, troubleshooting page, changelog, migration guide, contributing guide, docs landing page, and journey page. [`docs-journey.md`](docs-journey.md) maps each stage to its artifact.

---

## Tutorial

**First screen must answer:** "How do I complete my first real journey?"

**Required content:**
- The exact first request, command, or code sample, copyable and not paraphrased
- The expected result after that first action
- Checkpoints along the way ("you should see…")
- A complete outcome at the end: the reader finishes with something real
- Each step says what to do and what the reader should observe

**Move lower or link out:**
- Alternatives and variations (→ How-to)
- Architecture and design decisions (→ Explanation)
- Exhaustive option lists (→ Reference)
- Prerequisites beyond the minimum needed to start

**Anti-patterns to refuse:**
- Offering the reader a choice mid-tutorial
- Inserting explanation of *why* without linking out
- Steps that produce no observable result
- A result the reader cannot verify

---

## How-to

**First screen must answer:** "How do I accomplish this one goal?"

**Required content:**
- A copyable request, command, or code sample that starts the task
- The scope of what is read and what may change
- A minimal procedure covering the common path
- Common variations the reader is likely to hit
- The most likely follow-up task after this one completes

**Move lower or link out:**
- Theory and background (→ Explanation)
- Exhaustive field-by-field reference (→ Reference)
- Step-by-step setup a beginner needs (→ Tutorial)
- Options the reader will never vary

**Anti-patterns to refuse:**
- A title that names a topic rather than the reader's problem
- Reteaching basics the competent reader already knows
- Covering only the linear happy path with no realistic variations

---

## Reference

**First screen must answer:** "What exactly does this accept and do?"

**Required content:**
- An intent index: what the reader can accomplish
- Inputs: what the reader provides
- Outputs: what the product returns
- Reads: what is accessed without asking
- Writes: what may change
- Limits: caps, timeouts, pagination, rate limits
- One entry per item on the product's surface, shaped the same way. The entry shape per surface type (library, CLI, API, app, service, plugin, agent-context pack) is in [`surface-discovery.md`](surface-discovery.md)

**Move lower or link out:**
- Narrative walkthroughs (→ How-to or Tutorial)
- Explanation of why the design works this way (→ Explanation)
- Getting-started instructions (→ Tutorial)

**Anti-patterns to refuse:**
- Editorializing ("this is the recommended option…")
- Entries of the same kind shaped differently from their siblings
- Skipping an option because it is "rarely used"

**Sync discipline:** Reference rots when behavior drifts. A behavior change → reference update in the same PR is the rule. For auto-generated sections, mark them with a comment pointing to the source data so readers know not to hand-edit the copy.

---

## Explanation

**First screen must answer:** "How do these pieces fit together and why?"

**Required content:**
- A mental model the reader can hold in their head
- How the components compose: what connects to what
- Trade-offs and the reasoning behind key design choices
- Boundaries: what this concept is and is not

**Move lower or link out:**
- Step-by-step procedures (→ How-to)
- Exhaustive parameter lists (→ Reference)
- Guaranteed-outcome walkthroughs (→ Tutorial)

**Anti-patterns to refuse:**
- Step-by-step instructions embedded in the explanation
- Open-ended scope with no "About <topic>" frame
- Refusing to take a position where the design is opinionated

---

## README

**First screen must answer:** "What is this, who is it for, and what can I do with it?"

**Required content:**
- What the product is and what it helps the reader accomplish, in the reader's language and not internal names
- Who it is for, and its limits: what it does not do, supported platforms and versions
- The install command, or a link to the installation guide
- A first runnable example with its expected result: a command, a code sample, or a request
- Where to get help
- How to contribute (a link to the contributing guide) and the license

**Move lower or link out:**
- Long material: full tutorials, option lists, architecture (→ the docs)
- Configuration and setup details (→ How-to or Installation guide)
- The full inventory of commands, flags, components, or endpoints (→ Reference)
- Design rationale (→ Explanation, or the maintainer design record)

**Anti-patterns to refuse:**
- Opening with a flag, skill, or component inventory
- Requiring the reader to know an internal name to begin
- Describing capabilities in abstract terms with no concrete example
- Duplicating machine facts that a manifest already states and that can go stale
- A README that grows into the whole docs set

**Agent-context pack variant:** For a pack of skills, agents, or commands, the first runnable example is a starter prompt in the user's language, with a preview of what comes back. Skill names are not the entry point. Machine facts (version, scope, dependencies) stay in the manifest, and the README links to it.

---

## Quickstart

**First screen must answer:** "How do I get one real result in minutes?"

**Required content:**
- The minimum prerequisites, with versions
- One path with no choices: install, run, and see a result
- Copyable commands or code that work as pasted
- The expected output at each step, so the reader knows it worked
- Where to go next: the tutorial, a how-to, or the reference

**Move lower or link out:**
- Alternative install methods (→ Installation guide)
- Configuration options (→ Reference)
- Why it works this way (→ Explanation)

**Anti-patterns to refuse:**
- Branching paths or "choose your own setup" before the first result
- Steps that need knowledge the page never gives
- Samples that fail when pasted
- A quickstart that runs longer than a few minutes without being split

---

## Installation guide

**First screen must answer:** "Can I get this running in my environment?"

**Required content:**
- Prerequisites with versions: runtime, OS, accounts, permissions
- One supported install path first, as copyable commands
- A command that proves the install worked, with its expected output
- Alternative install methods after the first one
- How to upgrade and how to uninstall
- Links to troubleshooting for the failures readers hit most

**Move lower or link out:**
- First-use walkthroughs (→ Quickstart)
- Full configuration options (→ Reference)
- Build-from-source and development setup for contributors (→ Contributing guide)

**Anti-patterns to refuse:**
- Listing five install methods with no recommended one
- Unversioned prerequisites
- No way to confirm the install worked
- Mixing user install steps with contributor setup

---

## Troubleshooting

**First screen must answer:** "I see this problem. What do I check?"

**Required content:**
- Entries organized by symptom the reader can see, with the exact error text quoted so search finds it
- For each symptom: the likely cause, how to confirm it, and the fix
- How to collect diagnostics: a verbose flag, a log location, a version command
- Where to get help when no entry matches, and what to include in the report

**Move lower or link out:**
- Background on why the failure happens (→ Explanation)
- Install and setup steps repeated in full (→ Installation guide)
- Internal incident runbooks (→ the maintainer docs)

**Anti-patterns to refuse:**
- Entries organized by internal component instead of symptom
- A paraphrased error message instead of the exact text
- A fix with no way to confirm the cause
- A standalone FAQ that duplicates these answers

---

## Changelog and release notes

**First screen must answer:** "What changed in each release, and does it affect me?"

**Required content:**
- Releases newest first, each with a version and a date
- Changes grouped as Added, Changed, Deprecated, Removed, Fixed, Security
- Breaking changes marked and linked to the migration guide
- A name for the replacement with every deprecation
- Links to the issue or pull request for each entry where the repository has them

**Move lower or link out:**
- Upgrade steps (→ Migration guide)
- Explanation of design changes (→ Explanation)
- Marketing summaries (cut, or keep to one line in release announcements)

**Anti-patterns to refuse:**
- A dump of commit messages
- Entries written in internal terms the reader cannot map to behavior
- A deprecation with no replacement named
- Unreleased and released changes mixed with no "Unreleased" heading

---

## Migration guide

**First screen must answer:** "I am on version X. What must I change to move to version Y?"

**Required content:**
- One guide per breaking version pair, stating the versions at the top
- A checklist of what to search for in the reader's code or config, and what to change it to
- Before and after samples for each breaking change
- The order to do the steps in, and how to confirm the upgrade worked
- What to do if the reader cannot upgrade yet: support dates or a rollback path

**Move lower or link out:**
- The full list of non-breaking changes (→ Changelog)
- Why the break was made (→ Explanation)
- General installation steps (→ Installation guide)

**Anti-patterns to refuse:**
- A single guide that spans many versions with no per-pair checklist
- Describing a break without the replacement
- Steps with no search term or pattern the reader can look for
- No way to verify the migrated result

---

## Contributing guide

**First screen must answer:** "How can I help, and what do you need from me?"

**Required content:**
- How to report a bug: where, and what to include
- How to set up a development environment
- How to run the tests and the linters
- Which contributions are welcome, and which need discussion first
- How a change moves from branch to review to merge, and the commit or pull-request conventions
- A link to it from the README

**Move lower or link out:**
- Architecture and design rationale (→ the maintainer design record)
- User-facing how-tos (→ the user docs)
- Release procedures (→ the maintainer docs)

**Anti-patterns to refuse:**
- Setup steps that do not run on a clean machine
- Undocumented review or merge expectations
- Mixing user documentation into the contributor guide
- Hiding the guide where the README does not link to it

---

## Docs landing page

**First screen must answer:** "Where do I start?"

**Required content:**
- A single start-here path for a new reader
- Entry points named by reader goal ("Install it", "Fix an error"), not by Diátaxis kind or internal structure
- Links to the reference, the changelog, and where to get help
- One line saying what the product is

**Move lower or link out:**
- Tutorials and how-to content (→ their own pages)
- Long product descriptions (→ README or Explanation)
- Full navigation trees for a larger docs site (→ `information-architecture` if installed)

**Anti-patterns to refuse:**
- Marketing copy and slogans
- Several equal-weight starting points with no recommended one
- Links grouped by internal team or component
- A page that restates the README

---

## Journey

**First screen must answer:** "What happens from start to finish?"

**Required content (one block per stage):**
- **You do** — the request, command, or action the reader takes
- **The product does** — what it reads, fetches, or computes
- **You get** — the concrete result
- **Decision** — what the reader decides or confirms before the next stage

**Move lower or link out:**
- Implementation vocabulary (→ Reference)
- Configuration and permission details (→ How-to)
- Error-handling reference (→ Reference or Troubleshooting)

**Anti-patterns to refuse:**
- Describing what the product does without showing what the reader says and gets
- Stages without a visible decision or outcome
- Mixing implementation vocabulary into the user-facing flow
