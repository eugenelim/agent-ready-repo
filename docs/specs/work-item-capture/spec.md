# Spec: Capture a loop's leftover work as an actionable record

- **Status:** Approved
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Mode:** full
- **Brief:** none
- **Discovery:** docs/product/intents/FEAT-0006-work-item-capture-contract.md
- **Contract:** contracts/jsonschema/knowledge-captured-observation.schema.json
- **Shape:** mixed
- **Constrained by:** docs/product/intents/CAP-0005-work-item-capture-and-disposition.md § Boundary — an item is validated before it is captured, and the owner that runs a stored command is outside this capability. A record written here may carry a command; what that command may contain is § D6's, and what execution still owes is `docs/specs/work-item-promotion-handoff/spec.md`'s.

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Outcome`, `What Changes`, `Durable Outputs`, `Follow-ons` and
> `Assumptions` are working material: they orient a reader and an author
> corrects them in place as the work teaches, without an amendment and without
> a review round. A review finding against working material is advisory — it
> cannot block, because nothing gates the text it cites. Marking the tiers is
> the spec's job; honouring them when a finding is adjudicated is the
> reviewing surface's.

> **Contract tier.** This spec carries three sections the house template does
> not define. `## Decisions this spec makes` is **contract**, on the same
> footing as Acceptance Criteria: criteria dereference § D1, D2, D4, D6, D9,
> D10 for their meaning, so those decisions change only by amendment.
> `## Boundaries` and `## Inherited constraints` are **working material** —
> they restate fences other artifacts own.

## Outcome

A work-loop that finishes with leftover work records it as a typed observation
a later session can act on without re-deriving what the original session knew.
Success is that a cold session reads the record alone and can name both the
finished state and its first edit, and that an item which is not real or not
worth doing is refused before it is written.

## What Changes

- **The capture contract gains a fourth kind, `work-item`** —
  `contracts/jsonschema/knowledge-captured-observation.schema.json`, at
  contract version `knowledge-captured-observation.v2`.
- **A `work_item` object carries the fields the three shapes require** — the
  same schema.
- **`verification_route.command` becomes a bounded argv array** — the same
  schema, in the same v2. A `work-item` `defect` may carry one; the rules it
  must satisfy are § D6's, which this spec settles rather than importing
  (`AC-0046`).
- **The capture kind vocabulary widens at the five sites that pin it** — the
  two schema copies, `project_knowledge.py`'s request validator, and
  `knowledge_store.py`'s partition allowlist and kind enumerator. **Four** other literal sets hold the same three values and are **not**
  widened: the topic synthesis kind, the proposal synthesis kind, the legacy
  row kind in `knowledge_store.py`, and `lint-knowledge.py`'s own
  `ALLOWED_KINDS`. The last two are distinct sets even though both serve
  `patterns.jsonl`. A work item is the complement of generalisable
  practice, so admitting it to those vocabularies would contradict § D1.
- **The v1 validator is retained and selected by a record's own
  `contract_version`** — `project_knowledge.py`.
- **The diagnostic catalog gains the work-item refusal codes** —
  `REQUIRED_DIAGNOSTIC_CODES` in `project_knowledge.py`.
- **The deterministic privacy scan handles a work-item record** —
  `_deterministic_privacy_scan` in `project_knowledge.py`, which today reads
  `lesson` unconditionally and passes `verification_route.command` to a
  string matcher. Both break on a `work-item` record.
- **The close-time admission rule gains a branch for specific blocked work** —
  `packs/core/.apm/skills/work-loop/SKILL.md` § Capture learnings, with its
  detail in a new reference.
- **The close gains the per-item validation dispatch** — the same new
  `work-loop` reference, which dispatches the per-item cold reasoning check
  and supplies the verdict the writer requires (`AC-0068`); a close that
  cannot obtain one writes nothing. Tier
  *ordering* is `docs/specs/work-item-mechanical-tier/spec.md`'s: there is
  one tier until it lands.
- **The packaged schema mirror is re-synced** —
  `packages/agentbundle/agentbundle/_data/knowledge-captured-observation.schema.json`,
  which `make build-check` requires to stay byte-identical to the canonical
  contract.

## Boundaries

This spec settles what may be written and what is refused at write time. It
does not own:

- **What a later session does with a captured record.** Routing, terminal
  dispositions and the treatment of captured content as classifier input are
  `docs/specs/work-item-promotion-handoff/spec.md`'s.
- **Which governance items the governance route accepts once an item is
  written.** `docs/specs/governance-item-record-routing/spec.md`'s, per
  FEAT-0008 § For the spec to decide.
- **Knowledge freshness.** A registered open item with its own owner. This spec
  reads nothing from it and rules nothing about it, per FEAT-0006 § Non-goals.
- **Anything owed at a stored command's execution.**
  `docs/specs/work-item-promotion-handoff/spec.md`'s, under the six residual
  controls § D6 hands it by name. What a stored command may *contain* is § D6's
  own. A record written here may carry a command; this spec settles that it is
  validated against § D6 before it is stored, and nothing about running it.

## Inherited constraints

Not open to this spec. Each is fenced by an artifact above it.

- **A refusal is never silent**, per FEAT-0006 § For the spec to decide. What
  that handling is, is settled below.
- **Capture fails closed when validation cannot run.** FEAT-0006
  § Validation at capture requires a floor — "a guard whose failure is
  silent must not be the only guard". This delivery ships **one** tier, the
  reasoning tier, so the floor cannot be a second tier here: it is
  `AC-0068`, which admits nothing without a well-formed, item-correlated
  verdict — see its own text for what a write-path gate cannot establish, however the verdict failed to arrive. When `docs/specs/work-item-mechanical-tier/spec.md` lands, the
  mechanical tier becomes the structural floor FEAT-0006 describes, and
  `AC-0068` still holds — that spec's `AC-0004` is conditioned on an item
  both its checks admit, so it does not cover unavailability and never
  replaces this one.
- **The reasoning check runs in a context that did not produce the item**, per
  FEAT-0006 § Validation at capture.
- **The necessity test is the repository's own razor, not a new rubric**, per
  FEAT-0006 § Validation at capture. This spec authors none.
- **An item is validated before it is captured**, per CAP-0005 § Outcome.
- **No new store**, per FEAT-0006 § Non-goals. A refusal therefore has no
  durable home.

## Decisions this spec makes

Assigned by
[FEAT-0006](../../product/intents/FEAT-0006-work-item-capture-contract.md)
§ For the spec to decide, which holds the grounds for each. Two are marked
*confirm at gate*: each is a defensible call the owner may prefer to set
differently.

### D1 — one new kind; shape is a field, not a kind *(confirm at gate)*

The kind vocabulary gains exactly one value, `work-item`. The three existing
values all name generalisable practice; a work item is their complement — a
specific, non-generalisable, actionable item. That is one distinct
required-field set, so FEAT-0006's candidate test warrants one kind and no
more.

The taxonomy FEAT-0006 attaches thresholds to becomes a field,
`work_item.shape`, with a closed set of three values. This is what stops the
decision kind over-collecting: a shape is cheap to threshold, and widening the
enum that partitions storage is not.

| Shape | Definition | Threshold |
| --- | --- | --- |
| `defect` | A specific wrong behavior in a named artifact | Carries a `verification_route`, or supplies both `observed` and `intended` |
| `question` | An unresolved question whose deliverable is an answer | Names who or what can answer it |
| `decision` | A question whose deliverable is a durable decision record | At least one of: architecturally significant, expensive to reverse, or constrains work beyond the feature that raised it |

FEAT-0006 asks whether every kind needs a second half or only the decision
kind. Every shape has one, stated in the table's third column. The decision
shape's is the three-ground test; a question failing all three is spec content
and is refused as `decision`, though it remains admissible as `question`.

**The declaration check and the threshold judgement are different things.**
The schema-level field validator checks that `work_item.significance` is a
non-empty subset and nothing more, so an author who declares a ground clears
it; that validator is what `AC-0009` binds to and it ships in this delivery.
Whether the declared ground actually *holds* is a judgement, and judgement is
the reasoning tier's. `AC-0009` is therefore a declaration check by design,
not a weakened threshold check. Neither half is the mechanical tier's, which
is why `AC-0009` is unaffected by that tier's split into
`docs/specs/work-item-mechanical-tier/spec.md`.

### D2 — required fields, per shape

Every `work-item` record carries the base contract fields, less `lesson`
(see D8), plus:

- `work_item.statement` — the item in one line.
- `work_item.shape` — one of the three values above.
- `work_item.blocker` — one of `decision`, `instrument`, `elapsed-time`,
  `dependency`. These are FEAT-0006 § Assumptions' four blockers and the set is
  closed.
- `work_item.finished_state` — what done looks like. This is the field whose
  absence FEAT-0006 § Opportunity measures: each observed record named a
  location and omitted a finished state.
- `work_item.necessity_rationale` — what was considered and rejected as
  sufficient.

Per shape, additionally:

- `defect` — `verification_route`, or both `work_item.observed` and
  `work_item.intended`.
- `question` — `work_item.answered_by`.
- `decision` — `work_item.significance`, a non-empty subset of
  `architecturally-significant`, `expensive-to-reverse`, `constrains-beyond`.

A shape that cannot carry a reproduction command supplies the substitute named
on its row: the `observed`/`intended` pair for a defect, and `answered_by` or
`significance` for the other two, which never require a command.

### D3 — validation runs per item, in a cold context, capped at 12 *(confirm at gate)*

Per item, not once over the batch: FEAT-0006 records that a batch check may
miss an item-specific error, and the dispatch cost it trades against is small
because a close declines few items.

The cap is **12 declined items per close**; above it the close refuses rather
than dispatching validation. The value is borrowed, not derived: 12 is what
`_MAX_DISTILL_CANDIDATES` and `_MAX_NAMED_SOURCES` use in `knowledge_store.py`,
but those bound candidates and sources inside one distillation request, not the
size of a declined set, so this is a chosen provisional bound rather than a
coupling to an existing ceiling. Its revision trigger is the first close that
the cap actually refuses: no work item has ever been captured, so real close
sizes are unobserved. Enforcement is that the close counts the declined set
before it dispatches any validation, so the cap fires before the first dispatch
rather than partway through.

### D4 — a refusal tells the author, is not stored, and admits one correction

**The declined set** is the close's specific, non-generalisable leftover work:
rows two, three and four of § D9's table. Generalisable practice is not a
member — it takes the existing `project-knowledge` route and is not leftover
work. The outcome vocabulary is closed at three values, but it is not a
per-row lookup: a row-two item that fails validation receives
`refused`, which is also row four's outcome. Row membership defines the
declined set `AC-0001` needs; it does not determine the outcome.

**Item identity within one close.** D3 has the close enumerate the declined set
before it dispatches any validation, so each member carries a position-stable
ordinal from that enumeration. That ordinal is the identity a refusal, a
correction and a re-submission share. It is session-local and never stored,
which is consistent with a refused item receiving no capture id.

- **The author is told.** The close output lists every declined item with
  exactly one outcome: `captured` with its capture id, `refused` with its
  reason code, or `dispatched-in-session`.
- **The refusal is not retained durably.** CAP-0005 admits no new store, and an
  append-only observation store is not the home for a record that was refused.
  The refusal lives in the close's own output.
- **One correction is admitted.** A refused item may be corrected and
  re-submitted once within the same close. A second refusal of the same item is
  terminal for that close.

Reason codes come from the closed diagnostic catalog in
`REQUIRED_DIAGNOSTIC_CODES`. This spec is the single home for that catalog's
baseline size — fifteen values today — and adds **eleven**: four record-shaped
and seven command-shaped. The seven command codes are exactly the distinct
verdict column of § D6 cases.

| Added code | Refuses |
| --- | --- |
| `work_item_incomplete` | A field the item's shape requires is absent |
| `work_item_not_blocked` | `blocker` is present but outside the four |
| `work_item_unnecessary` | The necessity razor refuses the item |
| `work_item_threshold` | A shape's § D1 threshold is not met |
| `work_item_command_shape` | Not an array, or an element that is not a string |
| `work_item_command_size` | Element count, aggregate length, or element length |
| `work_item_command_option` | An element beginning `-` |
| `work_item_command_tool` | `argv[0]` outside the four |
| `work_item_command_operand` | Fewer operands than the tool requires |
| `work_item_command_charset` | An element outside the character class |
| `work_item_command_path` | `repositoryPath` |

The diagnostic carries no free-text field — `SAFE_DIAGNOSTIC_FIELDS` is closed
— so the code is the whole signal an author gets, which is why there is one per
action an author can take rather than one per rule.

### D5 — operational definitions

- **Can act on** — a second session, given the record alone, states the
  finished state and names the first edit it would make, without the
  originating session's transcript, scratch notes, or working tree.
- **Cold session** — a process with no access to the originating session's
  transcript or scratch, and no working tree beyond the committed tree at the
  record's `freshness_anchor` digest.
- **False-or-already-fixed count** — **not defined here.** Both available
  instruments are closed to this spec: an exit-code signal needs a stored
  command to *run*, and execution is outside this capability by CAP-0005
  § Boundary, and an anchor-versus-bytes
  comparison is the registered freshness item's, which
  `docs/specs/work-item-mechanical-tier/spec.md` § D1 excludes and
  FEAT-0006 § Non-goals assumes no answer to. Defining the count therefore
  needs an amendment to that Non-goal, which this spec does not have, so the
  operational definition is withdrawn to the freshness owner and carried in
  § Follow-ons.

### D6 — the trust boundary on a stored command

Today `_validate_verification_route` enforces an exact key set of `command` and
`path`, validates `path` through `_expect_repo_path`, and bounds `command` to a
500-character string. Everything below is new, and all of it is settled at
write time.

**Read-only is a property of the whole argv, not of its first element.** A
command whose first element is an allowlisted tool can still write or execute
through its options: `find -delete`, `find -fprint`, `git log --output`,
`rg --pre`, and `git -c diff.external=` all do. So the option surface is closed
by refusing options outright rather than by enumerating the dangerous ones,
which is a negative list and cannot converge.

The rules below were not written and then asserted. They were implemented as a
throwaway validator and run against a case table built from every escape the
security reviews demonstrated; the table is reproduced under § D6 cases and its
verdicts are the contract. Two rules in an earlier draft admitted cases this
spec claimed they refused, and running it is what found them.

- **Structure.** The command is stored as an argv array, never a shell string.
  A string-valued `command` is refused.
- **Every element is a string.** A number, `null`, a nested array or an object
  is refused with a catalog code, rather than raising when a later rule calls
  a string method on it.
- **Size.** Between 1 and 20 elements; at most 500 characters per element; at
  most 2,000 characters in total. The element cap matches the schema's
  existing largest array bound, `project_scope.paths` `maxItems: 20`, whose
  `minItems: 1` supplies the floor; the per-element cap is the 500 the string
  form already carried; the aggregate is 4 × 500, because no admitted command
  needs more than a tool, a pattern and two paths — `grep` is the widest
  admitted shape and `AC-0053` requires at least one operand after its
  pattern. The order is count, then element type, then the two length checks — the
  order the derivation runs. Two rows pin it: the 21-non-string row pins
  count before type, and `[1, 2]` pins type before length. The aggregate and
  per-element checks both return `work_item_command_size`, so their relative
  order is unobservable and is left unspecified rather than stated as a rule
  nothing can fail.
- **No options.** Any element beginning with `-` is refused. This is the rule
  that makes an argv read-only, and it is what refuses `find -delete`,
  `find -fprint`, `git log --output`, `rg --pre` and `git -c`.
- **argv[0] allowlist.** A closed set of four: `cat`, `wc`, `grep`, `ls`.

  `git` is excluded, and that exclusion is load-bearing. Under the no-options
  rule `git`'s remaining surface is its ref and object-id arguments, which are
  not paths and which no path rule reaches: `git cat-file blob <oid>` and
  `git show <oid>` read a blob that is no longer in the working tree — a
  credential scrubbed from the tree but still in the object database.
  Bounding that means naming a closed ref shape and the commits it may reach,
  a second trust boundary this spec would have to author and test. `find` and
  `rg` are excluded too: neither has a useful option-free invocation.

  The cost is that no admitted command reads a file at an anchored revision. A
  `defect` needing one supplies `work_item.observed` and `work_item.intended`,
  which § D2 already admits for exactly this case.
- **An operand is required.** `cat`, `wc` and `ls` need at least two elements;
  `grep` needs at least three. Without this, `["cat"]` is admitted and blocks
  on standard input at execution.
- **A positive character class over every element after argv[0].** Each must
  match `\A[A-Za-z0-9_/.,:@#%+=-]{1,500}\Z`.

  **The anchors are `\A` and `\Z`, not `^` and `$`.** This is the rule the
  anchoring matters for. It does **not** matter for the `repositoryPath` rule
  below: the class runs first and admits no newline, so every element reaching
  the path rule is newline-free, where the two anchor forms are equivalent.
  Re-anchoring the `repositoryPath` copy is defence in depth against the
  character class being **removed or narrowed**, not against a reordering:
  admission is a conjunction of every check, so reordering can change which
  code an element returns but never whether it is admitted. Enumerating every
  string of length 1-3 over the ten symbols `a`, `b`, `/`, `.`, newline,
  carriage return, backslash, `:`, `-` and the space character finds 33 that
  the raw and re-anchored patterns judge differently and **none** that clears
  the character class, in any order. (Without the space the count is 29; the
  zero is the load-bearing half and holds either way.) It is therefore **unreachable while the
  class covers every element**, including `grep`'s exempt index-1 pattern,
  which the § D6 case row `["grep", "AKIA\n", "src/a.py"]` witnesses. Narrowing
  the class is what would make this defence load-bearing; no separate
  criterion states that, because that row already fails on it. The copy is produced by
  rewriting the pattern's **trailing** anchor only; a whole-string substitution
  would also rewrite the three `$` inside its lookaheads, which is correct by
  accident today and wrong the first time a `$` appears as a literal — a mutation replacing it
  with the raw schema pattern changes no verdict in § D6 cases. In Python — and in JS,
  Java and PCRE without `D` — `$` matches immediately before a terminal
  newline, so a `^…$` form admits `["cat", "src/a.py\n"]` while refusing
  `["cat", "a\nb"]`. An earlier draft of this spec carried `^…$` and claimed
  the class "subsumes the newline case"; running the derivation showed it did
  not. The same defect is in the schema's own `repositoryPath` pattern, which
  ends `.+$`, so the rule below is enforced with an explicitly re-anchored
  copy rather than by trusting that pattern's anchoring.

  This replaces the metacharacter blocklist an earlier draft carried. The
  blocklist did not do the job claimed for it: running the case table showed
  `["cat", "a' '-delete"]` admitted, because a quote and a space are not
  members, yet naive shell re-serialisation splits it into two words with an
  option. A positive class has no such gap, and with `\A`/`\Z` anchoring it
  subsumes the newline and glob cases in one rule rather than three.
- **Every element after argv[0] satisfies `repositoryPath`,** re-anchored as
  above, except `grep`'s pattern at index 1, for which the character class is
  the whole rule. The exemption is load-bearing: `repositoryPath` forbids a
  colon, so without it the admitted row `["grep", "TODO:fix", "docs/x.md"]`
  could not hold.
  This is the decidable form of argument confinement — not "path-shaped
  elements", which no validator can decide. It refuses absolute paths, `..`
  segments, backslashes and colons.

  **The stored-path set, defined once here.** A `verification_route`'s stored
  paths are: every argv element after `argv[0]` except `grep`'s pattern at
  index 1, **plus `verification_route.path`**. Every rule in this section that
  says "path" means this set. It is the single home for the membership
  question, and `docs/specs/work-item-promotion-handoff/spec.md`'s
  `AC-0013` dereferences it rather than
  restating it.
  **These rules confine; they do not classify.** Every member of the
  stored-path set just defined is held inside the repository. Membership is
  the whole of the claim, and two things fall outside it. `grep`'s pattern at
  index 1 is not a member, so `["grep", "/etc/passwd", "docs"]` and
  `["grep", "../../etc/passwd", "docs"]` are **admitted** — the character
  class is the only rule reaching that slot. And `verification_route.path`
  is confined by `_expect_repo_path`, which folds a backslash to `/` before
  testing, so `a\b` is admitted as `a/b` rather than refused; that helper is
  shared with twenty other call sites and this spec does not change it.

  Nothing in this section decides whether an in-repository file is
  *sensitive*. A path inside the repository is admitted whatever it is
  called, so `credentials.json`, `keys/id_rsa`, `config/prod.env` and `.env`
  alike pass every write-time check. An earlier draft carried a
  dot-leading-component rule here; amendment 008 removed it, because a
  filename-convention denylist is the documented antipattern for path
  security, it added nothing to confinement, and it caught `.env` while
  missing the other three. See `notes/amendment-008.md`.

  In-repository sensitivity is therefore **disclosed and unowned**. It is
  *not* `docs/specs/work-item-promotion-handoff/spec.md`'s obligation 1:
  post-resolution repository confinement refuses a path resolving *outside*
  the repository, and an in-repository file never does. Round 4 routed it
  there, found it had zero homes rather than one, and withdrew the routing;
  amendment 008 does not reinstate it.


### D6 cases

Every row below is **emitted** by the derivation, not transcribed: run, **from the repository
root**, `python3 docs/specs/work-item-capture/notes/spike-argv-boundary.py
--markdown` and the output is this table. The script resolves the schema
relative to the working directory, so it only reproduces from the root. Its `_cell` renderer asserts each rendered case parses back as JSON — which
catches a renderer swap but **not** markdown corruption: an element containing
a pipe would still emit a malformed row, and a duplicated case would still
render twice. The guard is narrower than the corruption class, so T3
re-driving every row remains the only control that catches those. Two
earlier drafts lacked that: one mangled the rows carrying shell quotes, and
one mixed two renderers so a case appeared twice under different spellings.
T3 re-drives every row regardless — the table is evidence, not authority. `notes/spike-argv-boundary.py` is that derivation: it
is not shipping code, and T3 reimplements the rules against these rows. The
table is the whole run, not a selection — an earlier draft carried a subset and
the omitted rows were where two defects hid.

A row whose verdict changes is a contract change, not a test fix. The table
carries **44 rows**, one per case the derivation runs; the count is
stated so a dropped row is detectable, which is how an earlier draft lost the
row that pins the check order.

| argv | Verdict | Why this case exists |
| --- | --- | --- |
| `["cat", "src/a.py"]` | **admit** | baseline admission |
| `["wc", "docs/x.md"]` | **admit** | baseline admission |
| `["ls", "docs"]` | **admit** | baseline admission |
| `["grep", "AKIA", "src/a.py"]` | **admit** | baseline admission, fixed-string pattern |
| `"cat src/a.py"` | `work_item_command_shape` | R1: string command |
| `["find", ".", "-delete"]` | `work_item_command_option` | R1 sec: find -delete destroyed a file |
| `["find", "d", "-maxdepth", "0", "-fprint", "o"]` | `work_item_command_option` | R1 sec: find -fprint wrote a file |
| `["git", "log", "--output=o"]` | `work_item_command_option` | R1 sec: git --output wrote a file |
| `["rg", "--pre", "./pre.sh", "q", "a.txt"]` | `work_item_command_option` | R1 sec: rg --pre executed a script |
| `["git", "-c", "diff.external=tee p", "diff"]` | `work_item_command_option` | R2 sec: git -c reached execution |
| `["cat", "-n", "src/a.py"]` | `work_item_command_option` | R4 adv 12: option on an ADMITTED tool — the only rows above use tools the allowlist refuses anyway, so scoping the option rule to non-allowlisted tools reproduced every verdict |
| `["ls", "-la", "docs"]` | `work_item_command_option` | R4 adv 12: second admitted tool with an option, so the case is not one tool's quirk |
| `["grep", "-i", "x", "docs"]` | `work_item_command_option` | R4 adv 12: option ahead of grep's exempt pattern slot |
| `["git", "cat-file", "blob", "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"]` | `work_item_command_tool` | R2 sec: reads a deleted blob |
| `["git", "show", "HEAD:docs/x.md"]` | `work_item_command_tool` | R2 sec: anchored read, now excluded |
| `["cat", ".git/config"]` | **admit** | amendment 008: admitted -- an in-repo dot path is an ordinary path |
| `["cat", ".env"]` | **admit** | amendment 008: admitted -- confinement does not classify sensitivity |
| `["cat"]` | `work_item_command_operand` | R3 sec F4: blocks on stdin |
| `[]` | `work_item_command_size` | R3 sec F4: argv[0] undefined |
| `["grep", "pattern"]` | `work_item_command_operand` | R3 sec F4: grep with no operand |
| `[1, 2]` | `work_item_command_shape` | R3 sec F5: non-string elements |
| `[null]` | `work_item_command_shape` | R3 sec F5: null element |
| `[["cat"]]` | `work_item_command_shape` | R3 sec F5: nested list |
| `["grep", "a*", "docs"]` | `work_item_command_charset` | R3 sec F6: glob survives re-serialisation |
| `["cat", "a' '-delete"]` | `work_item_command_charset` | R3 sec F6: quote-split survives wrapping |
| `["cat", "docs\\x.md"]` | `work_item_command_charset` | R3 sec F7: backslash, enforcers disagreed |
| `["cat", "../etc/passwd"]` | `work_item_command_path` | traversal |
| `["cat", "/etc/passwd"]` | `work_item_command_path` | absolute path |
| `["cat", "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"]` | `work_item_command_size` | element length |
| `["cat", "x", "x", "x", "x", "x", "x", "x", "x", "x", "x", "x", "x", "x", "x", "x", "x", "x", "x", "x", "x"]` | `work_item_command_size` | element count |
| `["cat", "yyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy", "yyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy", "yyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy", "yyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy", "yyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy", "yyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy"]` | `work_item_command_size` | aggregate length |
| `["cat", "a\nb"]` | `work_item_command_charset` | newline in element |
| `["cat", "a;b"]` | `work_item_command_charset` | shell metacharacter |
| `["grep", "foo.*", "docs"]` | `work_item_command_charset` | iter2: BRE metachar in pattern |
| `["cat", "a b"]` | `work_item_command_charset` | iter2: space element |
| `["cat", "a\"b"]` | `work_item_command_charset` | iter2: double quote |
| `["cat", "docs/a-b_c.py"]` | **admit** | iter2: ordinary path must survive |
| `["grep", "TODO:fix", "docs/x.md"]` | **admit** | iter2: ordinary pattern must survive |
| `["cat", "src/a.py\n"]` | `work_item_command_charset` | R4 sec B1: TRAILING newline, $ admitted it |
| `["grep", "AKIA\n", "src/a.py"]` | `work_item_command_charset` | R4 sec B1: trailing newline in a pattern |
| `["grep", "a", "b\n"]` | `work_item_command_charset` | R4 sec B1: trailing newline in a later path |
| `["grep", ".env", "docs"]` | **admit** | grep pattern slot, admitted before and after amendment 008 |
| `["grep", "../../etc/passwd", "docs"]` | **admit** | R4 sec C4: pattern exempt from repositoryPath |
| `["cat", 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]` | `work_item_command_size` | R5 sec C6: pins count-before-type ordering |

**Instruction-shaped item prose is refused before the reasoning dispatch.** A
captured item's own text reaches a cold reasoning check, and § Assumptions
concedes that text may have been copied from untrusted prose. The existing
`_INSTRUCTION_SHAPE` pattern already recognises the shape, so the item is
refused at write time rather than delimited downstream, and the reasoning
dispatch presents item content as data rather than as instructions.

**Provenance is not established at write time.** An earlier draft claimed an
`authorship` constant refused a command copied from an issue body or a fetched
document. It cannot: the constant is supplied by the same workflow whose
provenance is in question, so an honest record and a copied one are identical.
The field carries no refusal and no acceptance criterion. Attribution comes
from git history instead, which records every stored line against its
introducing commit.

**Residual obligation at execution.** These controls bound what is written.
They cannot resolve a symlink, fix `PATH`, or bound a runtime's resources —
properties of the moment a command runs. Ambient `git` configuration and
`.gitattributes` textconv drivers affect only `git` subprocesses, which the
allowlist no longer admits; they are named in the sibling against a future
widening rather than as a reachable case today. **Six obligations remain owed at execution**, and this is where their members
are fixed; § D10 separately discloses an accepted, unowned residual on the
record's own prose, which is not one of them.
`docs/specs/work-item-promotion-handoff/spec.md` § Boundaries restates these
six. Every other mention cites the count and points here:

1. Post-resolution repository confinement.
2. Environment neutralisation.
3. A resource cap.
4. A re-check of the stored command against these § D6 rules immediately
   before it runs, using the same validator the write path uses.
5. **Which matcher `grep` runs.** The character class admits exactly two
   characters that are metacharacters under some candidate matcher: `.`,
   which is one under BRE, ERE and PCRE alike, and `+`, which is one under
   ERE and PCRE but a literal under BRE. No other ERE metacharacter —
   `[ ] ( ) { } * ? | ^ $ \` — is in the class. `grep`'s pattern is exempt
   from the path rules, so `["grep", "a.b", "docs"]` and
   `["grep", "a+b", "docs"]` are both admitted and each denotes a different
   line set under a different matcher. Write-time validation cannot settle
   which one executes.

   **The choice is already narrowed to one.** The sibling's `docs/specs/work-item-promotion-handoff/spec.md` `AC-0022`
   requires an admitted pattern to denote the same line set the author wrote.
   For `a.b` that holds only under `-F`, so the class and `AC-0022` together
   admit `-F` and nothing else. The sibling may relax `docs/specs/work-item-promotion-handoff/spec.md` `AC-0022` instead, but
   it cannot name BRE, ERE or PCRE while keeping it.
6. The treatment of the command's output — which sinks it may reach, that it
   carries no instruction authority at a reasoning step, and that it is
   privacy-scanned before any durable write. The bytes are
   attacker-influenced whenever the record is.

All six are `docs/specs/work-item-promotion-handoff/spec.md`'s.

**The merge path § D10 discloses reaches a stored command.** § D10 owns that
disclosure and states it once; what follows is only what it means here.

Obligations 1 to 3 above do not cover such a record: they bound resolution,
environment and resources, and none inspects `argv[0]` or the option rule.
Obligation 4 — the pre-execution re-check — is what does, and the sibling's
criteria carry it. Without it an unvalidated record carrying a string
`command`, or argv `["bash", "-c", …]`, would satisfy every other stated
control and run.

The merge path itself is disclosed by
§ D10, which owns what a stored record
must be; this section states only what it means for a command.

### D7 — the rationale travels with the item and is printed at the close

`work_item.necessity_rationale` is required on every written record, so the
rationale is in the store. The close output prints it beside each captured
item, so the owner confirms a judgement they can see rather than a list already
filtered by reasoning they cannot. One source, two surfaces.

### D8 — a new `work_item` object, not a reused `lesson`

FEAT-0006 offers reuse as the cheaper option because the schema forbids unknown
properties. Measurement refutes the premise: the kind enum is pinned at many
sites, `additionalProperties` is `false`, and `contract_version` is a `const`,
so admitting any work item at all is already a new contract version. Reuse
therefore saves nothing and costs one field carrying two meanings.

§ What Changes names the five sites in prose. The enumeration that governs
is the plan's T4 check, which parses the `kind` enum at every site and
compares them: it fails on a site the prose misses, so the prose cannot
silently go stale against it. One of them is the packaged mirror
`packages/agentbundle/agentbundle/_data/knowledge-captured-observation.schema.json`,
which `tools/catalogue/check_contract_parity.py` requires to be byte-identical
to the canonical file and which `make build-check` runs. The mirror is a copy, so it is synced by copying. The packaged inventory
`public-contracts.txt` does list this contract, but it is keyed on filenames
and this change adds no file, so the inventory is unaffected. A future change
that adds a second `contracts/jsonschema/knowledge-*.schema.json` would have to
regenerate it.

`lesson` stays required for the three existing kinds and is not required for
`work-item`, which carries `work_item.statement` instead.

### D9 — the close-time rule gains a branch, not a loosening

`work-loop`'s § Capture learnings currently keeps generalisable practice and
discards the rest. It gains one branch:

| What the note is | Where it goes |
| --- | --- |
| Generalisable practice | The existing `project-knowledge` route, unchanged |
| Specific, real, blocked | Captured as a `work-item` |
| Specific, real, ready now | Dispatched in-session, not captured |
| Specific, failing the razor | Refused, non-silently, per D4 |

### D10 — existing records stay readable and are never rewritten

Re-derived from the store during PLAN: the observation files hold records of
two different kinds carrying two different contracts, and the spec must not
conflate them. No count appears here — the store is append-only and grows on
every capture, including this feature's own close, so a figure recorded here
would be stale before the work lands.

| Layer | Field | Which records carry it |
| --- | --- | --- |
| Event envelope | `schema_version` | `observation-event.v1` on every record |
| Capture payload | `request.contract_version` | `knowledge-captured-observation.v1` on the `observation.captured` records |
| — | — | The `observation.dispositioned` records carry no `request` object and so no `contract_version` at all |

**A record entering the store by any path other than the capture API is not
re-checked.** The store is committed repository content, so a record can
arrive in a merge or a contributor branch having been validated elsewhere or
not at all, and this spec adds no ingest gate. **No write-time prose control is re-established at execution — a disclosed,
unowned residual.** Three controls run on a record's own prose at the write
path and nowhere else: `assert_persistable_text`'s eight patterns, `AC-0035`'s
instruction-shape refusal, and `AC-0036`'s framing of item content as data. A
record reaching the store by merge carries prose none of them ever saw, and
the sibling runs a classifier and a reasoning step over it. So a merged record
may carry an email address, a bearer token, a `/Users/<name>` path, a tenant
identifier or instruction-shaped text into a reasoning context and into a
durable artifact.

This is **not** assigned to an obligation here. An earlier draft handed the
sibling a single obligation covering `AC-0035` alone, which re-established one
of the eight patterns while reading as coverage of the class — worse than the
disclosure it replaced, because a partial control invites the reader to stop.
Closing it needs a decision this spec does not own: which controls a read path
re-runs, and against what. That decision is the sibling's
§ Decisions this spec owes entry on the trust boundary for captured content,
and until it is made this residual is accepted and unmitigated.

Note the asymmetry it leaves: the sibling's `docs/specs/work-item-promotion-handoff/spec.md` `AC-0021` privacy-scans the
*command's output* before a durable write, so output carries a control the
record's own prose does not, on the same merge threat. That is a consequence
of this residual, not an independent gap.

This disclosure is this spec's,
because this spec owns what a stored record must be; § D6 and
`docs/specs/work-item-promotion-handoff/spec.md` reference it rather than
restating it, and the handoff spec's pre-execution re-check is what stands
between such a record and a command running.

Version selection therefore binds to the **capture payload only**. A record
carrying a `request.contract_version` is validated by the validator that field
selects. A disposition event has no capture payload, is not a capture-contract
record, and is outside version selection entirely — it is read through its
envelope, which this spec does not change. No stored record of either kind is
rewritten.

### D11 — the version boundary

The writer emits capture payloads at `knowledge-captured-observation.v2` only.
`v1` becomes a read-only legacy version: readable, never written.

**Version selection is the Python validator's, not the schema document's.**
The contract file describes the writable version only, so its
`contract_version` `const` becomes v2 and no second schema document is
created — which is why the packaged inventory needs no regeneration.
The document carries **two** version sites — a top-level
`contract_version` key and `properties.contract_version.const` — and both move
together; `tests/roster/test_project_knowledge_capture_contract.py` pins the
top-level one and validates a fixture against it, so that suite moves with the
bump. `project_knowledge.py` holds a version-to-validator map and dispatches on the
record's own `request.contract_version`, so a stored v1 record is validated by
the v1 rules in code. That is how `AC-0015` and `AC-0017` hold across the bump.

**A `request` object with no `contract_version` is refused too.** Absence and
an unknown value are the same hazard once selection is a lookup: the schema
previously closed absence by making the field `required`, and the map does
not. The read-path partition therefore keys on whether a record carries a
capture payload at all, not on whether the version field is present.

**A `contract_version` that selects no validator is refused.** Moving
selection into a map turns a `const` mismatch — previously a failure by
construction — into a lookup on a field the record supplies, and § D10 admits
records this spec never validated. The map therefore has no default and no
fallback: an unknown version returns a code from `REQUIRED_DIAGNOSTIC_CODES`,
never `None`, never the oldest validator, never an uncaught `KeyError`.

**Selection is the read path's rule.** The write path validates under the
writable version unconditionally; a submission tagged with any other version
is refused rather than validated under legacy rules and re-stamped, which
would produce a record carrying a version whose validator never ran.

**v2 is one schema and lands in one delivery.** The `work-item` kind and the
`verification_route.command` argv change are both v2, and § D6 settles the
argv rules in this spec rather than a sibling. `contract_version` is a
`const`, so a v2 that later changes shape would leave every record written in
between failing the validator its own field selects — against a store § Never
do forbids rewriting. An earlier draft split the argv rules into their own
spec; the two halves proved to be one seam, because the schema, the validator
and the reason-code table are single artifacts that both halves edit. The
`observation-event.v1` envelope is unchanged by this spec and is not versioned
by it.


## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Interface compatibility | Applicable: the capture contract gains a version | `contracts/jsonschema/knowledge-captured-observation.schema.json` | project-knowledge | `AC-0015`, `AC-0016`, `AC-0017`, `AC-0018`, `AC-0047`, `AC-0048`, `AC-0062` green | Each payload version validates its own records and the envelope-only records never reach version selection |
| Current architecture | Applicable: the store gains a record class that is not generalisable practice | `docs/architecture/` knowledge-capture entry | work-loop | The `work-item` kind, and its validation as delivered: **the reasoning tier only**, with the mechanical tier named as not built and pointed at `docs/specs/work-item-mechanical-tier/spec.md` | A reader finds the record class and the tier state it ships with. The gap list lives in the security row below; this row makes no claim about it |
| Maintainer procedure | Applicable: the close-time rule branches | `packs/core/.apm/skills/work-loop/SKILL.md` and its new reference | work-loop | AC-0001, AC-0002 green | The branch is readable without the spec |
| Interface compatibility | Applicable: `verification_route.command` changes type and gains a trust boundary | `contracts/jsonschema/knowledge-captured-observation.schema.json` and the § D6 validator | project-knowledge | `AC-0049`–`AC-0061` green | A stored command is an argv array every element of which cleared § D6 |
| Current product truth | Applicable: adopters write captures | `docs/guides/reference/` entry for the work-item kind | maintainers | Guide names the three shapes and their thresholds | A cold adopter can write a valid record |
| Current architecture (security) | Applicable: the delivery ships accepted, unmitigated residuals | `docs/architecture/security.md` | work-loop | **The single home for the gap list.** The write-time argv rules, then every gap: unestablished provenance, the unchecked merge path, § D10's prose residual, **§ D6's stored-path rules confine but do not classify** — every member of that set is held inside the repository, while `grep`'s pattern at index 1 is not a member and is admitted, and no rule decides whether an in-repository file is sensitive, so `credentials.json`, `keys/id_rsa`, `config/prod.env` and `.env` are all admitted; the residual is **unowned**, obligation 1 having been refuted for it in round 4, and amendment 008 removed the dot-leading-component rule that read as a credential control and was not one — **the caller-asserted verdict** — § D3 puts the cold check at the close, so the agent dispatches it and hands the writer the result; `AC-0068` can require a well-formed, item-correlated verdict but cannot establish that one was obtained, because no in-process gate can verify a caller consulted an oracle the caller controls. It catches omission, garbling and stale reuse, not a deliberate assertion — the late-ordering residual `AC-0069` records — § D6's argv rules run at write time, after the per-item reasoning dispatch under § D3's ordering, so an attacker-influenced `verification_route.command` element reaches the cold reasoning context screened only by `AC-0036`'s framing — and the absent mechanical tier, which `docs/specs/work-item-mechanical-tier/spec.md` owns — stated as its **consequence**, not as a missing artifact: validation is one tier deep, so an unavailable reasoning tier is the whole of validation being unavailable, and `AC-0068` refusing to write is what stands in for the floor. **That spec's settlement amends this list**: its **catalog-code** and **residual-bit** points each move it. The six residual runner obligations are the sibling's and are listed as handed over, not as gaps | The list is complete against this spec's disclosures. No count appears anywhere: a literal falsifies silently when a disclosure is added, so the list is the assertion |
| Release history | Applicable: a published contract changes version | The core pack changelog | maintainers | Entry leads the release | The version bump is recorded |
| Decision rationale | Applicable: the mechanical tier is split out rather than settled here | This spec § Follow-ons and `docs/specs/work-item-mechanical-tier/spec.md` | eugenelim | The gate approval | The approved spec records that the tier is a separate spec and why, and ships no criterion that depends on it |
| Reusable learning | Not applicable | — | — | — | The work-loop capture gate already owns it |

## Agent Rules

### Always do

- Select a record's validator from that record's own `contract_version`.
- Emit exactly one outcome for every declined item at a close.
- Widen the kind vocabulary at every site that pins it, in one change.
- Drive a change to the § D6 rules from the § D6 case table, so the table
  and the validator move together.

### Ask first

- Adding a value to `work_item.shape` or `work_item.blocker`. Each is a closed
  set this spec fixes.
- Adding a tool to § D6's `argv[0]` allowlist, or loosening its character
  class. Both are trust-boundary widenings, and the derivation in
  `notes/spike-argv-boundary.py` is what shows the effect of a change.
- Raising the 12-item cap, which is a chosen provisional bound with no
  observed traffic behind it.
- Any edit taking `work-loop/SKILL.md` above 1000 body lines as
  `skill_spec_lint` measures them — the threshold at which `CAT-S003` becomes
  an error. Read the count from the linter; this spec states no figure,
  because the task this rail governs edits that file.

### Never do

- Rewrite, migrate, or delete a record already in the store.
- Widen any of the four non-capture kind sets — topic synthesis, proposal
  synthesis, `knowledge_store.py`'s legacy row kind, or `lint-knowledge.py`'s
  `ALLOWED_KINDS`. A work item is the complement of generalisable practice.
- Write an item for which the tier returned no recognized verdict — whether
  it was unreachable, unrecognized, raised, expired, unconfigured, or never
  asked. There is no second tier to fall back to in this delivery, so
  anything short of a recognized verdict is a refusal (`AC-0068`).
- Create a second store for refusals.
- Treat a stored command as executable here. § D6 bounds what may be
  written; running one is `docs/specs/work-item-promotion-handoff/spec.md`'s
  and needs the six residual controls § D6 hands it.
- Scan a command element with `assert_persistable_paths`. It carries four
  patterns where `assert_persistable_text` carries eight.

## Testing Strategy

The parent's own bet test — one loop's close, a cold session, the author
interview — is FEAT-0006 § De-risk's and runs there. These verify this spec's
criteria, cited by stable id throughout.

| Criteria | Mode | Surface | Why |
| --- | --- | --- | --- |
| `AC-0003`–`AC-0009`, `AC-0013`, `AC-0018`, `AC-0031`, `AC-0032`, `AC-0034`, `AC-0037` | TDD | unit | Each is a pure function over a record with a compressible invariant |
| `AC-0047`, `AC-0048` | TDD | unit, over the version map | An unknown version and a non-writable submission are both driven directly at the selector |
| `AC-0069` | Goal-based check | the dispatch's parameter set, derived and compared against the refusals ahead of it | Both bins are total by construction, so the check is the domain's completeness: derived by nested walk over the **schema document** — not a record instance, which drops unset optional fields — widened by the non-schema inputs `AC-0041` shows the dispatch also receives, and pinned to a minimum yield |
| `AC-0035`, `AC-0036` | TDD | unit, with a dispatch spy | Instruction-shape refusal and the dispatch's data framing, driven one field at a time |
| `AC-0068` | TDD | unit, **at the writer in `project_knowledge.py`**, four cases | The gate is a write-path refusal, not a spy over skill prose: every way of failing to validate reduces to "no recognized verdict for this item" at one seam a test can drive. The four cases are absent, unrecognized, mismatched identity, and a stale verdict on a corrected re-submission |
| `AC-0044`, `AC-0045` | TDD | **reasoning-tier dispatch**, not a pure function | The razor and the shape threshold are the reasoning tier's calls, matching T5 |
| `AC-0046` | TDD | unit, at the kind-agnostic validation seam | The binding is an invocation, so the test asserts the § D6 validator was called for a non-`work-item` kind too and its refusal propagated |
| `AC-0015`, `AC-0016`, `AC-0017` | Goal-based check | **integration replay** over the whole store | These only prove out across the validator and the widened enum together, so the surface is named rather than implied |
| `AC-0038`–`AC-0041` | TDD | unit, with a dispatch spy | The correction path, its terminal path, the cap and the cold-context property are driven assertions, not observations of a real close |
| `AC-0050`–`AC-0060` | TDD | unit, driven from the § D6 case table | Each refusal class is one row of that table, so a row added there is a case here and the table cannot drift from the validator |
| `AC-0049` | TDD | unit, **round-trip through the writer and reader** | The admit direction is the one a refusal-only suite never reaches, and element-for-element equality is what catches a writer that flattens the array |
| `AC-0061` | TDD | unit, with the scan spied per element | The claim is which scan function each element reaches, so the assertion is on the call. A refusal assertion would pass with the wrong scan wired, because § D6 refuses most discriminating strings before any scan runs |
| `AC-0062` | TDD | unit, at the version selector | A `request` with no `contract_version` is the case the schema used to close and the version map reopened |
| `AC-0001`, `AC-0002`, `AC-0014` | Visual / manual QA | the real close | The declined set, its outcome accounting and the printed rationale are what an author reads |

The vocabulary sweep and the packaged-mirror parity are goal-based checks the
plan owns; they carry no criterion.

- Decline an item during close and suppress its outcome; assert the close
  fails (`AC-0001`, `AC-0002`).
- For each shape, construct a record missing one required field; assert each
  is refused, and that a complete record of that shape is written (`AC-0003`,
  `AC-0004`).
- Submit a `defect` with no command but both `observed` and `intended`, and a
  `question` and a `decision` with no `verification_route`; assert all three
  are written (`AC-0005`, `AC-0006`).
- Submit a record with an absent `blocker` and one with an out-of-set
  `blocker`; assert the two refusals carry different codes (`AC-0007`,
  `AC-0008`).
- Submit a `decision` with an empty `significance`; assert it is refused
  (`AC-0009`).
- Assert a written record carries a non-empty `necessity_rationale`, and that
  the close output prints it (`AC-0013`, `AC-0014`).
- **Replay every record in the store**, partitioned on whether
  `request.contract_version` is present: assert the present partition reads
  under the validator that field selects, the absent partition reads through
  the `observation-event.v1` envelope without reaching version selection, and
  every file's bytes are unchanged (`AC-0015`, `AC-0016`, `AC-0017`). The
  partition is the assertion; the store grows on every capture, including
  this feature's own, so no record count appears in this spec or the plan.
- Submit a payload tagged `knowledge-captured-observation.v3`, and one tagged
  v1 at the write path; assert the first is refused with a catalog code and
  nothing is stored, and the second is refused rather than re-stamped
  (`AC-0047`, `AC-0048`). Drive the unknown version through the replay too,
  since § D10 admits records this spec never validated.
- Write a record through the writer and assert the emitted payload's
  `contract_version` — the write path, not the read path (`AC-0018`).
- Submit a `work-item` record populating each of the six free-text fields in
  turn with a known privacy-violating string; assert each is caught
  (`AC-0031`). Separately assert the scanned set equals **the set `AC-0031`
  derives**, computed from the schema at test time — the rule is stated once,
  in that criterion, and is not restated here. That comparison, not the
  per-field loop, is what makes a field added later fail the suite, and the
  partition assertion is what catches a non-string addition.
- Submit a record with no `lesson`; assert the scan runs without error
  (`AC-0032`).
- Induce a scan failure; assert it returns a catalog code (`AC-0034`).
- Submit an item with instruction-shaped prose in each of the six fields in
  turn; assert each is refused before any reasoning dispatch, proven by a
  dispatch spy recording zero calls (`AC-0035`). `significance` is not among
  them: it is a closed enum, so its refusal comes from the enum check and the
  case would pass with no instruction-shape scan at all.
- Derive the domain from the **dispatch's own parameter set**, with the
  schema document as one contributing source walked to nested depth, and
  assert each member is either refused deterministically beforehand or
  listed as unscreened; assert `verification_route.command` is in the
  unscreened list, since § D6 runs after the dispatch (`AC-0069`).
- Assert the reasoning dispatch wraps item content in its data delimiter and
  that no item field is interpolated into instruction position (`AC-0036`).
- Assert every refusal path returns a code from the closed catalog
  (`AC-0037`).
- Submit a record carrying a `verification_route` whose command violates § D6
  — one case per refusal class in § D6 cases — and assert each is refused with
  the matching § D4 code and nothing is stored (`AC-0046`). Drive it for a
  `work-item` and for a non-`work-item` kind, since the field is kind-agnostic.
- Drive **every row of the § D6 case table** through the write path: assert
  each refused row returns its table verdict as the stored reason code and
  nothing is written, and that each admitted row is written
  (`AC-0050`–`AC-0060`). The table is the fixture, so a row added to § D6
  without a validator change fails the suite. Include at minimum a string
  command, a non-string element, a 0- and a 21-element command, a `grep`
  with no pattern, an element beginning `-`, a `find` in `argv[0]`, an
  element carrying a character outside the class, an element failing
  `repositoryPath`, an element with a `.`-leading component, a command
  totalling over 2,000 characters, and a single element over 500.

- Write `["grep", "pattern", "src/a.py"]` and read it back; assert the
  array is equal element-for-element to what was submitted (`AC-0049`).
- Assert, per element, that the scan function each element was passed to is
  `assert_persistable_text` and not `assert_persistable_paths` (`AC-0061`).
  The assertion is the call, because a refusal assertion passes with the
  wrong scan wired: `_URL` and `_NON_HTTP_LOCATOR` strings both need a colon,
  which the re-anchored `repositoryPath` refuses before any scan runs. Add
  one end-to-end case that does discriminate — `["cat", "example.com"]`,
  which clears every § D6 rule and is refused by `assert_persistable_text`
  alone — and one using `grep`'s exempt index-1 slot,
  `["grep", "https://evil.example.com/x", "docs"]`, which is the only slot a
  colon-bearing string can occupy.
- Submit a payload whose `request` object carries no `contract_version`;
  assert it is refused with a catalog code and is not read as an
  envelope-only event (`AC-0062`).
- At the writer, submit a record with **no verdict**, then with a verdict
  outside the recognized set, then with a verdict whose item identity does
  not match the record, then a corrected re-submission carrying its
  pre-correction verdict; assert each is refused and the store's bytes are
  unchanged (`AC-0068`). All four are driven at `project_knowledge.py`, not
  through skill prose: an unreachable endpoint, an unconfigured tier and an
  agent that never dispatched all reduce to case 1 at this seam. Asserting a
  refusal code alone would pass on an implementation that appends and then
  reports.

- Submit an item the razor refuses — one an existing artifact already covers,
  which is rung 2 of the root `AGENTS.md` § Coding conventions ladder —
  "make one bounded search for an adequate repository solution; reuse a hit"
  — the rung FEAT-0006 § Validation at capture routes the razor to — and assert it is not written
  and the refusal returns `work_item_unnecessary` (`AC-0044`).
- Submit a `decision`-shaped item whose declared grounds do not hold under the
  § D1 three-ground test; assert it is not written and the refusal returns
  `work_item_threshold` (`AC-0045`). This is the reasoning tier's judgement,
  not the schema-level declaration check `AC-0009` binds to, per § D1.
- Refuse an item, correct it so its statement text changes, re-submit it, and
  refuse it again; assert the ordinal still matches it, the first
  re-submission is admitted, and the second refusal ends the close
  (`AC-0038`, `AC-0039`).
- Drive a close declining 13 items; assert it refuses before the first
  validation dispatch, proven by a dispatch spy recording zero calls
  (`AC-0040`).
- Assert the reasoning check's input set excludes the transcript path
  (`AC-0041`).

## Acceptance Criteria

> **Stable identifiers.** Each criterion carries an `AC-NNNN` id that is
> assigned once within **this document** and never reused or renumbered.
> Numbering is per-spec, so the same id names a different criterion in the
> sibling handoff spec; every cross-spec citation therefore carries its spec
> path, as the plan's cross-spec references do. A criterion inserted later
> takes the next free number wherever it sits in the list, and a criterion
> removed leaves its number retired. Every citation in this spec, the plan and
> the sibling uses the id, never a list position — positional citation is what
> silently broke most of the plan's references when this list was renumbered.

- [ ] `AC-0001` A loop's close emits the set of items it declined, whose
      membership is rows two, three and four of § D9's table.
- [ ] `AC-0002` Every member of that emitted set carries exactly one outcome
      from `captured`, `refused`, `dispatched-in-session`; a member with no
      outcome fails the close.
- [ ] `AC-0003` A `work-item` record missing any field its shape requires, per
      § D2, is refused.
- [ ] `AC-0004` A complete `work-item` record of each of the three shapes is
      written.
- [ ] `AC-0005` A `defect`-shaped item carrying no `verification_route` but
      both `work_item.observed` and `work_item.intended` is written.
- [ ] `AC-0006` A `question`- or `decision`-shaped item carrying no
      `verification_route` is written.
- [ ] `AC-0046` **Any** record carrying a `verification_route` is validated
      against § D6 at write time, whatever its kind, and one whose command fails
      those rules is refused with the matching § D4 code. `verification_route` is a
      kind-agnostic top-level property validated by one shared function, so
      scoping the binding to `work-item` would leave a v2 `gotcha` record's
      command unbound. This is the enforcing home for a command-bearing
      capture: without it the argv rules exist in a spec nothing on this path
      invokes.
- [ ] `AC-0007` A capture whose `work_item.blocker` is absent is refused with
      `work_item_incomplete`.
- [ ] `AC-0008` A capture whose `work_item.blocker` is present but outside
      `decision`, `instrument`, `elapsed-time`, `dependency` is refused with
      `work_item_not_blocked`.
- [ ] `AC-0009` A `decision`-shaped item whose `work_item.significance` is
      empty is refused. Per § D1 this checks declaration only.
- [ ] `AC-0013` Every written `work-item` record carries a non-empty
      `work_item.necessity_rationale`.
- [ ] `AC-0014` The close output prints each captured item's
      `necessity_rationale` beside that item.
- [ ] `AC-0015` Every record in the store carrying a
      `request.contract_version` reads under the validator that field selects.
- [ ] `AC-0016` Every record in the store carrying **no `request` object**
      reads under the `observation-event.v1` envelope and is not passed to
      capture version selection. The partition keys on capture-payload
      presence, per § D10, not on whether the version field happens to be
      there.
- [ ] `AC-0062` A record carrying a `request` object with no
      `contract_version` is refused with a code from
      `REQUIRED_DIAGNOSTIC_CODES`, not admitted as an envelope-only event.
      The schema made an absent field fail by construction; moving selection
      into a map removed that, so absence is closed here as explicitly as an
      unknown value is by `AC-0047`.
- [ ] `AC-0017` Replaying the store rewrites no record: every file's bytes are
      unchanged.
- [ ] `AC-0047` A capture payload whose `request.contract_version` names no
      known validator is refused with a code drawn from
      `REQUIRED_DIAGNOSTIC_CODES`, and nothing is stored. It is never
      validated by a default, by the oldest validator, or not at all.
- [ ] `AC-0048` A submission whose `request.contract_version` is not the
      writable version is refused at the write path, rather than validated
      under that version's rules and emitted at the writable one.
- [ ] `AC-0018` A payload the writer emits carries
      `knowledge-captured-observation.v2` and no other version, asserted over
      the write path.
- [ ] `AC-0031` Every free-text field a `work-item` record carries —
      `work_item`'s `statement`, `finished_state`, `necessity_rationale`,
      `observed`, `intended` and `answered_by` — is passed to the
      deterministic privacy scan. The scanned set is **derived from the
      schema** — every `work_item` property that is string-typed and carries
      no `enum` — not from a second hand-written list, and that derivation
      yields exactly the six named above.

      **Every `work_item` property reaches a scan or is excluded on a stated
      ground**, and the test asserts that partition is total. Without it a
      property added later as an array of free text is excluded by
      "string-typed", reaches no scan, and the derived-set comparison still
      passes — the string case fails loudly and the array case does not. `shape` and `blocker` are
      string-typed but enumerated, and `significance` is an array of
      enumerated values; all three are excluded because a violating value in
      a closed set is refused by the enum before any scan runs, so the case
      could not fail. Repository paths in the record are excluded too, on the
      different ground that they reach `assert_persistable_paths`.
- [ ] `AC-0032` A `work-item` record whose `lesson` is absent is
      privacy-scanned without error.
- [ ] `AC-0034` A privacy-scan failure on a `work-item` record returns a
      reason code drawn from `REQUIRED_DIAGNOSTIC_CODES`, and the store's
      bytes are unchanged. The scan raises rather than returns, so without the
      second half an implementation that appends, catches and reports
      satisfies the criterion while committing the string the scan refuses.
- [ ] `AC-0035` An item any of whose six free-text fields — the set
      `AC-0031` derives — matches the existing instruction-shape pattern is
      refused before the reasoning dispatch.
- [ ] `AC-0036` The reasoning dispatch presents item content as delimited
      data, and an item's prose never reaches it as instruction text.
- [ ] `AC-0069` **Every input the reasoning dispatch can receive is
      enumerated and placed in exactly one bin** — deterministically refused
      before the dispatch, or recorded as unscreened.

      **The domain is the dispatch's own parameter set**, not the record
      schema. The schema is one contributing source and does not cover the
      whole input: `AC-0041` exists because the dispatch also receives
      close-level context, and an input the schema cannot supply must still
      be enumerated and placed.

      **The schema-sourced part is derived, not authored**: every property
      reachable by walking nested objects of the **schema document** — not
      of a record instance, which drops every unset optional field — so
      `verification_route.command` — one level down — is a member. A walk
      that stops at top-level properties yields `verification_route` as one
      opaque member and misses it, which is the escape this clause closes.
      The derivation must yield at least the six `AC-0031` names plus
      `verification_route.command`, `verification_route.path`,
      `friction.summary`, **and at least one input the schema cannot
      supply** — the close-level context `AC-0041` names. Without that last
      member every pinned name is schema-sourced, so a derivation
      enumerating zero non-schema inputs meets the floor and the widened
      half of the domain has no failing case. A derivation returning fewer
      fails, so a partial or empty set cannot pass.

      Both bins are total by construction, so the domain's completeness is
      the whole of this criterion: a hand-written list on both sides
      satisfies every word and catches nothing. **Adding an input to the
      dispatch without placing it must fail** — that is the binding
      mechanism, stated here and not only in a Testing Strategy bullet.

      `verification_route.command` is in the **unscreened** bin — § D6's
      argv rules run at write time, after the per-item dispatch under
      § D3's ordering, so only `AC-0036`'s framing is ahead of it.
- [ ] `AC-0037` A refused capture returns a reason code drawn from
      `REQUIRED_DIAGNOSTIC_CODES`.
- [ ] `AC-0068` **The write path refuses any submission that does not carry
      a well-formed, recognized, item-correlated verdict.** The gate is in
      `project_knowledge.py`, at the write, not in the skill prose that
      obtains the verdict — prose is enforced by source-text assertions,
      and a source-text assertion over a reference is the hand-written list
      `AC-0069` names as catching nothing.

      **What this catches:** a verdict absent, a verdict outside the
      recognized set, and a verdict computed for a different item —
      including a corrected re-submission reusing its pre-correction
      verdict, whose content yields a different correlation key. Omission,
      garbling and stale reuse.

      **What it cannot catch, and why no write-path check could.** § D3
      puts the cold check at the *close*: the agent dispatches it and passes
      the result to the writer. The verdict therefore reaches the writer
      through the party that produced it, so an agent can assert one it
      never obtained — the correlation key is computed from the submitted
      request, so whoever holds the request can compute it, and a
      writer-issued nonce would simply be relayed. This is a property of
      where the check runs, not a weakness in the check: **no in-process
      gate can verify that a caller consulted an oracle the caller
      controls.** An earlier draft of this criterion claimed the opposite.
      The residual is disclosed in the security gap list.

      This is the floor FEAT-0006 § Validation at capture requires, and in
      this delivery it is the **only** floor, because the mechanical tier is
      `docs/specs/work-item-mechanical-tier/spec.md`'s and does not ship
      here.

      Driven at the writer, each case separately:

      1. No verdict supplied at all — the shape an unreachable endpoint, an
         unconfigured tier, a raise, or an agent that never dispatched all
         reduce to. The writer cannot distinguish them and does not need to.
      2. A verdict outside the recognized set — a well-formed value from a
         tier version change or a truncated body. This is what "degraded"
         means; against `if verdict == refuse: refuse else: admit` it is a
         fail-open default.
      3. A verdict whose item identity does not match the item being
         written — the aliasing case, where one item was validated and a
         different one written. A count of verdicts cannot catch this; the
         binding is per-item correspondence.
      4. A **corrected re-submission** under `AC-0038` carrying the verdict
         from its pre-correction dispatch. `AC-0038` admits the
         re-submission; without this case an implementation treats the
         ordinal match as the admission and reuses a stale verdict, which is
         the adversary's retry loop: refuse, edit, land permanently.

      Expiry is the caller's, not the writer's: the skill prose states a
      bound and treats expiry as "no verdict", which case 1 then refuses.
      The bound is not a criterion here, because the writer cannot observe
      it — stating it as one would put an assertion on a surface no test can
      drive, which is what an earlier draft of this criterion did.

      The store is append-only and § Never do forbids rewriting, so an item
      admitted here is permanent. This criterion does **not** retire when
      the mechanical tier lands: that spec's `AC-0004` is conditioned on an
      item both its checks admit, so it never covers unavailability.
- [ ] `AC-0044` An item the necessity razor refuses is not written, and the
      refusal returns `work_item_unnecessary`. This is the razor FEAT-0006
      § Validation at capture calls the test that keeps the well a well rather
      than a heap; without it a validator that admits every syntactically
      valid record satisfies every other criterion in this spec.
- [ ] `AC-0045` An item whose shape's § D1 threshold is not met is not
      written, and the refusal returns `work_item_threshold`.
- [ ] `AC-0038` A refused item corrected and re-submitted once within the same
      close is admitted, matched by the declined-set ordinal § D4 defines.
- [ ] `AC-0039` A second refusal of that same item ends that close.
- [ ] `AC-0040` A close declining more than 12 items refuses before it
      dispatches the first validation.
- [ ] `AC-0041` Each item's reasoning check runs in a context with no access
      to the originating session's transcript.

- [ ] `AC-0049` A well-formed read-only argv — `["grep", "pattern",
      "src/a.py"]` — is written and read back element-for-element unchanged.
- [ ] `AC-0050` A `verification_route.command` that is a string rather than an
      array is refused at write time and nothing is stored.
- [ ] `AC-0051` A stored command any of whose elements is not a string is
      refused at write time with a catalog code, and nothing is stored.
- [ ] `AC-0052` A stored command of fewer than 1 or more than 20 elements is
      refused at write time and nothing is stored.
- [ ] `AC-0053` A stored command carrying fewer operands than § D6 requires
      for its `argv[0]` is refused at write time and nothing is stored.
- [ ] `AC-0054` A stored command any of whose elements begins with `-` is
      refused at write time and nothing is stored.
- [ ] `AC-0055` A stored command whose `argv[0]` is outside `cat`, `wc`,
      `grep`, `ls` is refused at write time and nothing is stored.
- [ ] `AC-0056` A stored command any of whose elements after `argv[0]` fails
      § D6's character class is refused at write time and nothing is stored.
- [ ] `AC-0057` A stored command any of whose elements after `argv[0]`, other
      than `grep`'s pattern, fails the **re-anchored** `repositoryPath` rule
      § D6 defines — the schema's pattern with its trailing `$` rewritten to
      `\Z` — is refused at write time and nothing is stored. The re-anchoring
      is **unfalsifiable by the § D6 case table**: substituting the raw
      published pattern changes none of the 46 verdicts, because the
      character class admits no newline. It is carried as defence in depth
      against that class being narrowed, and only a narrowing would make it
      detectable — no criterion pins it, because none can.

- [ ] `AC-0058` A stored command any of whose elements after `argv[0]`, other
      than `grep`'s pattern, has a component beginning `.` is refused at write
      time and nothing is stored.
- [ ] `AC-0059` A stored command whose elements total more than 2,000
      characters is refused at write time and nothing is stored.
- [ ] `AC-0060` A stored command any of whose elements exceeds 500 characters
      is refused at write time and nothing is stored.
- [ ] `AC-0061` Every element of a stored command **after `argv[0]`** is
      passed to `assert_persistable_text`, the eight-pattern scan the string `command`
      is scanned against today — not `assert_persistable_paths`, which carries
      four and would drop `_URL`, `_NON_HTTP_LOCATOR` and `_BARE_HOSTNAME` from a
      surface that has them now. (`_INSTRUCTION_SHAPE` is in the same
      symmetric difference but cannot fire on an admitted element — every
      alternative needs a space or an angle bracket, and the character class
      admits none — so it is carried for surface uniformity, not as a
      reachable control.) No element loses
      a pattern in this change. `argv[0]` is outside the quantifier because
      the four-member allowlist refuses anything else before the scan runs,
      so an index-0 case could not fail.

## Follow-ons

- knowledge-freshness owner: `workspace.toml` `[backlog].open`, slug
  `knowledge-freshness-pins-bytes-and-the-pins-do-not-hold` — the
  false-or-already-fixed count. FEAT-0006 § De-risk names it as a signal but
  both instruments that could derive it are closed to this spec, so it is
  withdrawn here rather than defined without authority.
- work-item-mechanical-tier: `docs/specs/work-item-mechanical-tier/spec.md`
  — the deterministic validation tier, split out of this spec's § D12
  because it did not converge: nine review rounds, and its owed list grew at
  every one of them, ending with one point that is irreducible by
  construction. That spec's own § Decisions is the single home for the list;
  no count appears here. Five criteria moved with it, renumbered
  there: `AC-0010`→`AC-0001`, `AC-0011`→`AC-0002`, `AC-0012`→`AC-0003`,
  `AC-0043`→`AC-0004`, `AC-0067`→`AC-0005`. **This spec ships without a
  mechanical tier**, so the reasoning tier is the whole of validation
  until that spec lands, and `docs/architecture/security.md` says so.
- work-item-promotion-handoff: `docs/specs/work-item-promotion-handoff/spec.md`
  — what a later session does with a captured record.
- governance-item-record-routing:
  `docs/specs/governance-item-record-routing/spec.md` — which governance items
  the governance route accepts.
- duplicate-coverage-offer: `docs/specs/duplicate-coverage-offer/spec.md` —
  offering an artifact that already covers a captured item.

## Assumptions

<!-- Settled during PLAN by running the write path, not by reading it
(recorded in `notes/verification-ledger.md`). Two facts, and an earlier draft drew the wrong conclusion from the
first: the partition parse is version-blind, so a v2 and a v1 record may share
one month file and no versioned partition is needed — but the same validator
allowlists the kind DIRECTORY, so `observations/work-item/<YYYY-MM>.jsonl` is
refused with `confinement` until that set is widened. The partition change is
real and T4 owns it. -->

- Product: the 12-item cap was a chosen provisional bound with no traffic
  behind it. **First measurement, 2026-09-21:** this spec's own delivery —
  eight tasks, six contract amendments, three reviewer lenses, roughly thirty
  sustained findings — would have captured **one** work item under this
  contract, possibly two. The cap is therefore comfortable and is not the
  binding constraint. It stays at 12 rather than being tuned to a single
  observation, and its revision trigger is unchanged: the first close the cap
  actually refuses.

  The same measurement moves a larger question than the cap, recorded in
  `docs/product/intents/FEAT-0006-work-item-capture-contract.md`
  § Observed demand: the work-loop contract now forbids shipping a deferred
  acceptance criterion, which closes the route by which most leftover work
  used to arise, and the three specs downstream of this one are sized for a
  flow of captured items that may not arrive. That is a product question for
  their owners, not a change to this contract.
- Technical: command provenance is not established at write time and no
  mechanism here establishes it — a command copied from untrusted prose by an
  honest-looking producer is indistinguishable from one the workflow authored
  (settled by: nothing in this delivery; git history attributes the line, not
  the command's origin).
