> Discipline: applied (practitioner-pattern survey)

# Safe write-back into existing tracker records

**Question.** How should an agent write drafted content into a tracker record that already holds human-authored text, across Jira, Jira Align, Linear, and GitHub Issues?

**Result.** No tracker documents a server-side check that blocks a stale write. The safe pattern is therefore client-side: read, compare, preview, ask for a disposition, re-read, write, and keep the prior value. Section 6 turns this into one contract.

Retrieval was shallow: standard searches and a few fetches. Findings marked `[moderate]` or lower need a vendor-doc check before they become a requirement.

## Findings

### 1. Field writes are partial; the text inside a field is not
- Jira `PUT /issue/{key}` merges at field level. `fields` sets only the listed fields, and `update` takes explicit set/add/remove verbs. A `description` that is set replaces the whole text of that field. `[high]` for the merge rule on Server/DC (primary: Atlassian REST guide); `[moderate]` for Cloud ADF replacement, because the Cloud page did not load.
- GitHub `PATCH /issues/{n}` replaces `body`, `labels`, and `assignees` as whole values. `[moderate]`
- Linear `issueUpdate` takes a partial input, so omitted fields stay. `[moderate]` (integration guides only).
- Jira Align `PUT` and `PATCH` both returned 204 and cleared custom fields the request did not include (JIRAALIGN-2709, fixed in 10.88). Other reports show PATCH changing fields it did not name (JIRAALIGN-8402, JIRAALIGN-7859). No official text says `PUT` replaces the record. `[low]` on the rule, `[high]` that the reports exist. Treat both verbs as able to lose data.

### 2. No tracker offers a stale-write check on issue update
- Jira has no `If-Match` or version check on issue update; requests for one were closed or left open (JRACLOUD-26005, JRASERVER-10170). Concurrent PUTs both returned 204 with values lost (JRASERVER-78256). `[moderate]`
- GitHub documents no ETag, `If-Match`, 304, or 412 on update. `[high]` that none is documented.
- Linear and Jira Align: none found. `[uncertain]`
- Practice is a hand-made compare-and-swap: record `updated` (Jira, GitHub) or `updatedAt` (Linear) at read, re-read just before the write, and refuse if it moved. A small race window remains. `[inference]`; Linear's `updatedAt` may skip trivial edits, so also compare the field value or a hash of it.

### 3. Prior values are recoverable only partly, so capture them
- Jira keeps `changelog` with `fromString` and `toString`. `[moderate]`
- GitHub's web page keeps a body edit history; no documented API read. `[low]`
- Linear has `Issue.history`; whether it stores description text is unconfirmed. `[low]`
- Jira Align: audit log only, no API history found. `[low]`
- Conclusion: save the full prior value, and its revision marker, before every write rather than rely on tracker history. `[inference]`

### 4. Preserving existing text
- Bots on GitHub wrap their output in a hidden marker pair, replace only what sits between the markers, and append the block when the markers are missing. Reruns do not duplicate. Several unrelated tools use this one convention, so it counts as one pattern with many adopters. `[moderate]` (secondary sources). Put the marker inside visible content, since a bare comment can render empty.
- Jira ADF has no comment node, and conversion through plain text or wiki markup is lossy. Panels, tables, mentions, and media collapse to text, and a generated client once wrote `{}` back over an ADF field. `[moderate]` (one primary Atlassian page, the rest community). Conclusion: edit the ADF document directly, touch only the agent's own block, and leave every other node as read. `[inference]` A node-level marker (an identifying panel or entity property) is unverified.
- A three-way comparison of the last-synced value, the current remote value, and the new local value separates "remote changed", "local changed", and "both changed". No tracker-specific source found. `[uncertain]`; the shared refresh path in this repository already uses this shape (keep-local, accept-source, revise-both).

### 5. Approval design
- Approval fatigue is real: one vendor reports users accept 93% of manual prompts. `[moderate]` (single vendor's data).
- OWASP LLM06 (Excessive Agency) says to require human approval for high-impact actions, enforce authorization in the downstream system, and use least privilege. `[high]`
- Practitioner posts say to approve the resolved payload (diff, destination, reversibility), not a bare "Approve?", and to tier approval by risk. The three posts likely share one discourse, so they count as one line. `[moderate]`
- Suggested-edit tools (document suggestions, pull-request suggested changes) show a diff on the human's text and keep the original until accepted. From background knowledge, not fetched. `[moderate]`
- Tension, not resolved: fatigue research favors fewer prompts; payload approval favors one prompt per item. The middle path is risk tiers. An edit to human-written text is lossy, so it sits in the top tier. A new comment or an append inside the agent's own block is lower. `[inference]`

## Anti-patterns
- Silent overwrite of a field the human wrote.
- Approving a summary ("improve description") instead of the resulting payload.
- Bulk approval across items.
- Using `PUT` to change one field on Jira Align.
- Round-tripping ADF through a string.

## Known unknowns
- **Known-unknown:** Does Jira Cloud v3 accept any concurrency header on issue update? Would be closed by: the live Cloud REST v3 reference and one test against a sandbox site.
- **Known-unknown:** Does Linear `Issue.history` hold prior description text? Would be closed by: schema introspection against the public GraphQL endpoint.
- **Known-unknown:** Does a node-level marker survive an ADF edit made in the Jira editor? Would be closed by: a sandbox test.
- **Known-unknown:** Which Jira Align resources support `PATCH`, and does this install run a build with the 10.88 fix? Would be closed by: the instance's API docs page and version string.
- **Unknowable:** Whether payload preview beats summary approval in measured error rates. Why not: no controlled study was found, and results would vary with the reviewer.

## What changes our design
1. Treat every field-level text write as lossy unless it appends to a block the agent owns.
2. The agent must do its own stale-write check, because the trackers do not.
3. Capture the prior value ourselves.
4. Approve the exact resolved payload, one item at a time, for edits to human text.

## Sources
- Atlassian: Updating an issue via the Jira REST APIs (Server/DC); ADF wiki-conversion notes; Jira issues JRACLOUD-26005, JRASERVER-10170, JRASERVER-78256.
- Jira Align issues JIRAALIGN-2709, JIRAALIGN-8402, JIRAALIGN-7859; Jira Align KB articles on PATCH.
- GitHub REST docs: update an issue.
- OWASP LLM06:2025 Excessive Agency; Anthropic engineering post on auto mode.
- Practitioner posts on tool-approval patterns; bot marker-block conventions in open-source PR tools.
