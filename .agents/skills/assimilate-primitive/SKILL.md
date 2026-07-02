---
name: assimilate-primitive
description: Use to bring a single external agent primitive — one skill, subagent, hook, or command (or a small connected bundle) — from a local path or URL into this catalogue. Fetches it, diagnoses the destination pack and lifecycle from the local charter, and migrates it to pack convention, or rejects it with a reason. Triggers on "assimilate this skill from <path/url>", "bring in this agent", "adopt this hook into a pack". Do NOT use to survey a whole repo (use assimilate-repo) or to justify a new pack (use propose-catalogue-pack).
---

# Skill: assimilate-primitive

Bring **one** external primitive into the catalogue, migrated to this repo's
convention and craft — or reject it. A *primitive* is one skill, subagent, hook,
or command (or a small connected bundle, e.g. a skill + its hook).

Run in **two phases**: judge the untrusted content **safe** first, then shape it
to our target state. Never merge the two — you inspect raw, then transform.

## Phase 1 — fetch and make it safe (before you trust a byte)

1. **Fetch, SSRF-guarded.** A local path is read as-is. A **URL** is fetched
   only over an allowlisted scheme — `https`, or `git`/`ssh` for a repo clone
   (`git clone` / `gh`, which avoids raw-fetch `file://` reads). **Reject**
   `file:`, `ftp:`, `gopher:`, and any host resolving to a private, link-local,
   or cloud-metadata range (`169.254.0.0/16`, `10/8`, `127/8`, `192.168/16`, …);
   revalidate redirects against the allowlist. See
   [`references/ingest-safety.md`](references/ingest-safety.md).
2. **Show the raw body verbatim** for the operator to read. Do not reformat
   first — an assimilated skill/agent is instruction prose that will project into
   this operator's *and downstream users'* agents (prompt-injection surface); a
   hook or script is code that runs on their machine. The operator judges the
   raw content before it is trusted.
3. **Confirm on code.** If the primitive is (or contains) a **hook or script**
   — executable code, not prose — flag it as a higher-scrutiny class and require
   an explicit "yes, land this code" before proceeding.
4. **Run the repo's own gates on the candidate.** Before it lands, run the
   internal lints that apply to the artifact kind (`lint-skill-spec`,
   `lint-agent-artifacts`) and the SAST/SCA scanners (`.snyk` / dependency scan
   where runnable; CodeQL runs on the PR this opens). A failure **blocks the
   landing** or is surfaced for an explicit confirm — ingestion never bypasses
   the gates the repo runs on its own code.

## Phase 2 — shape to our target state (only after Phase 1 clears)

5. **Diagnose the destination.** Read the local `docs/CHARTER.md` coverage model
   and the existing packs; pick the destination pack + lifecycle. When the fit,
   naming, or bundle-split is a genuine judgment, **prepare the elicitation
   context** — what you found, the options, your recommendation — and offer it;
   never dump a bare question.
6. **Steer away from anti-patterns.** Detect and correct — or reject — known
   misuse before it lands: a **script or hook that triggers a skill or agent**,
   an **agent used the wrong way** (self-review, over-broad tool grant,
   skill-vs-agent confusion), a **flooding-prompt "skill"**. Cite the specific
   convention you steer toward. Full catalogue:
   [`references/anti-patterns.md`](references/anti-patterns.md).
7. **Reshape to craft** (not just reformat). Rewrite the `description` terse and
   activation-optimized, and **collision-check it against every existing skill**
   (surface any overlap, naming the colliding skill). Apply progressive
   disclosure (detail → `references/`, mechanical steps → `scripts/`), gloss
   coined terms for a cold reader, and turn in-skill decision points into guided
   offers. The craft authority is the repo's skill-authoring conventions (its
   *Authoring skills* guidance).
   Checklist: [`references/craft-checklist.md`](references/craft-checklist.md).
8. **Present the shaped target for approval, then write** — through the engine's
   blessed jail, `agentbundle.safety.write_jailed` / `assert_under` (resolve →
   verify-prefix → symlinks resolved first), so a traversing/absolute path or an
   in-source symlink cannot escape `packs/`. Never roll your own path handling.
9. **Prompt `make build-self`** so the projection tracks the new source, and
   purge the fetched-but-rejected working copy.

## Never do

- Write under this repo's `packages/agentbundle/**` or `packs/credential-brokers/**`
  — those trees change only through a separate, human-authored RFC, never through
  this skill (RFC-0059 D6). This refusal is scoped to *this* repo's engine tree.
- Land ingested content without the raw-body review (Phase 1) or, for code/hooks,
  the explicit confirm.
- Fetch a URL over a non-allowlisted scheme or reach a private/metadata address.
- Write outside `agentbundle.safety.write_jailed`, or launder an anti-pattern
  (step 6) into the catalogue unshaped.

_Depends on `core` + `governance-extras`. Repo-scope; not in any default profile._
