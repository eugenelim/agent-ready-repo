# Your first governance session

In fifteen minutes you'll install the `governance-extras` pack, use `new-adr` to record one architectural decision, and see the preview-confirm write gate in action — the step where you read exactly what will land in your repo and where, before confirming the write.

This is a tutorial — it leads. For the full `new-adr` procedure, see [How to record a decision (ADR)](../how-to/new-adr.md). For `new-rfc`, see [How to propose a change (RFC)](../how-to/new-rfc.md).

## What you need before starting

- `agentbundle` on your PATH. The [install agentbundle](../../_shared/how-to/install-agentbundle-from-clone.md) guide covers the one-time setup.
- A repo you can work in — any project directory where you'd be happy to add a `docs/adr/` folder. The pack writes one file on confirm; you can delete it before committing if you change your mind.
- The `core` pack installed at repo scope. `governance-extras` depends on it; the installer will tell you if it's missing.

## Step 1 — Install governance-extras at repo scope

Open your agent (Claude Code or equivalent) in the repo you'll work in, then run:

```bash
agentbundle install --pack governance-extras --scope repo
```

The pack lands in `.claude/skills/` with four skills: `new-adr`, `new-rfc`, `update-conventions`, and `rfc-status`.

You should see a confirmation that four skills installed. A `docs/adr/README.md` and `docs/rfc/README.md` are seeded if they were absent.

## Step 2 — Verify the install

In your agent, ask:

```
run rfc-status
```

You should see the RFC lifecycle states listed — `Draft`, `Open`, `Final Comment Period`, `Accepted`, `Rejected`, `Withdrawn`, `Experimental`, `Superseded` — and a count of any RFCs in `docs/rfc/`. If `docs/rfc/` is empty, the skill says so cleanly.

If this step fails, see [Recovery](#recovery) below.

## Step 3 — Paste the starter prompt

Copy this prompt exactly and paste it into your agent:

```
Create an ADR for the decision to use TOML as the format for our workspace coordination file.
```

The `new-adr` skill activates. It checks the three preconditions for a valid ADR — architecture-not-feature, decided-not-debated, real-tradeoff — and confirms this decision qualifies.

You should see the skill acknowledge the request and begin framing the decision.

## Step 4 — Read the decision frame

The skill may offer a short decision frame before drafting: the decision restated in one sentence, the problem it resolves, the alternatives considered (YAML, JSON, INI/dotenv), and the driver that made TOML the right choice.

You should see something like:

> **Decision:** Use TOML as the format for the workspace coordination file (`workspace.toml`).
> **Problem:** The workspace coordination file needs a structured format that supports nested sections, comments, and typed values without a schema validator.
> **Driver:** TOML's native support for sections, inline tables, and comments outweighs the marginal familiarity benefit of YAML — which loses comments on round-trip — or JSON — which has no comment syntax.
> **Alternatives:** YAML (comments lost on round-trip), JSON (no comment syntax), INI (no nested structure).

If the frame doesn't match your intent, correct it now. You can say "the driver should say..." or "we also considered XML." The skill reworks the frame before drafting anything.

## Step 5 — Preview the ADR content

The skill presents the full ADR draft before writing anything. You'll see the title, the `Context` section with constraints, the `Decision` section with a single declarative sentence, `Consequences` with honest tradeoffs, and `Alternatives` with rejection reasons.

**This is the content preview.** Read every section before confirming. If anything looks wrong — a hand-wavy Consequences section, an alternative missing its rejection reason — say so and the skill revises.

You should see a complete, structured ADR in your conversation before any file is written to disk.

## Step 6 — See the target path

The skill names the file it will create before it creates it:

> I'll write this to `docs/adr/0001-workspace-coordination-file-format-toml.md` (or the next sequential number if you have existing ADRs) and add a row to `docs/adr/README.md`.

**This is the target path preview.** You know exactly which file will be created and where it will land. If the path is wrong — you wanted a different directory, or the numbering is off — say so now.

## Step 7 — Confirm or stop

You have three options at this point:

**Confirm:** Say "looks good", "write it", "go ahead", or simply "yes".

The skill writes the ADR file and updates `docs/adr/README.md`. Nothing was written until this moment.

---

**Stop:** Say "cancel", "don't write it", "stop", or close the conversation.

Nothing is written. The draft exists only in the conversation history. You can start a new session and try again with a revised prompt.

---

**Revise:** Say what you'd like changed before confirming — "remove the Decision summary", "the Context section should mention our team's YAML fatigue", "change the Revisit if trigger to say...".

The skill updates the draft and shows it to you again. Confirm when you're satisfied.

## Step 8 — Verify the result

After confirming, open the file and check the index:

```bash
cat docs/adr/0001-workspace-coordination-file-format-toml.md
cat docs/adr/README.md
```

You should see the ADR you reviewed in Step 5, at the path named in Step 6, with a new row in the index.

To commit:

```bash
git add docs/adr/
git commit -m "docs(adr): record decision to use TOML for workspace coordination file"
```

## Recovery

**Verification fails in Step 2.** Confirm `governance-extras` is installed at repo scope (`ls .claude/skills/rfc-status/`). If the directory is absent, re-run the install. Also confirm `docs/rfc/` exists — the skill expects it; the seed creates it on install, but if the install was partial you may need to re-run.

**Wrong path shown in Step 6.** Say "cancel" before confirming. The skill stops. Re-run with a corrected prompt if needed.

**You confirmed but want to undo.** The ADR is a plain markdown file. Before committing, delete it and revert the index update:

```bash
rm docs/adr/0001-workspace-coordination-file-format-toml.md
git checkout -- docs/adr/README.md
```

Then start a new session with a revised prompt.

**The skill pushes back on the starter prompt.** The `new-adr` skill enforces three preconditions. If it says the decision is "still being debated," use `new-rfc` instead (see [How to propose a change](../how-to/new-rfc.md)). If it says the prompt describes a feature's internals rather than an architectural call, adjust the framing to name the cross-cutting structural choice.

## What you did

You installed `governance-extras`, verified it, invoked `new-adr` with the starter prompt, read the decision frame, reviewed the full ADR content and target path, and confirmed the write. You now know where the file lands, what it contains, and how to stop the write at any point before confirming.

The pack ships three more skills — `new-rfc` (for proposals still under debate), `update-conventions` (for editing `docs/CONVENTIONS.md`), and `rfc-status` (for scanning the RFC registry).

## See also

- [How to record a decision (ADR)](../how-to/new-adr.md) — all three ADR routes: greenfield, superseding an existing record, and originating from an accepted RFC.
- [How to propose a change (RFC)](../how-to/new-rfc.md) — use this when the decision is still under debate.
- [Governance index](../how-to/governance-index.md) — where ADRs, RFCs, and conventions fit in the wider doc system.
