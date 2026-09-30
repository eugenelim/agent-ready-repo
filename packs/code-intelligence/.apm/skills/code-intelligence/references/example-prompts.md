# Example prompts

Five workflows, each showing the same thing: the workflow supplies the goal,
this skill supplies the evidence, and the two stay separate.

In every example the skill answers *what is true*. It never decides whether to
migrate, whether the bug is fixed, or whether the refactor is worth doing.

---

## 1. Debugging

> "Orders occasionally get charged twice. Where does the charge actually happen
> and what could call it more than once?"

**Pattern:** Investigate behavior (3).

```bash
wicked-estate resolve charge --json                  # which `charge`?
wicked-estate source ChargeProcessor.charge --json   # read it before theorising
wicked-estate blast-radius ChargeProcessor.charge --json
wicked-estate graph-view --focus ChargeProcessor --limit 30
```

**A good answer looks like:**

> The charge is issued at `billing/charge_processor.rs:142`. Six resolved call
> sites reach it. Two are retry paths — `RetryQueue::drain` and
> `WebhookHandler::replay` — and neither checks an idempotency key before
> calling, which I confirmed by reading both.
>
> `blast-radius` also reports 3 unresolved call sites. They are probably the
> dynamic handler registration in `plugins/`, which the indexer cannot bind, so
> there may be a seventh caller I have not seen.

**What the skill did not do:** decide that the missing idempotency check is the
bug, or write a fix. The `bug-fix` workflow owns the diagnosis and the change.

---

## 2. Feature impact analysis

> "We want to add a currency field to `Money`. What does that touch?"

**Pattern:** Analyze change impact (2).

```bash
wicked-estate stats                                  # freshness, before anything else
wicked-estate resolve Money --json
wicked-estate blast-radius Money --json
wicked-estate source --symbols <chosen-ids> --json   # read the ones you picked
```

**A good answer looks like:**

> 47 resolved dependents, 0 unresolved, no truncation. Two caveats on that:
> the CLI traverses to a fixed depth of 12 and does not tell you whether it hit
> that limit, and `stats` reports the graph is current with the working tree.
>
> I picked five to read — `Invoice`, `LedgerEntry`, `PaymentGateway`,
> `RefundCalculator`, and the `Money` serde implementation — chosen because
> they are public constructors or serialization paths, **not because the tool
> ranked them**. The CLI cannot rank a supplied set. Four construct `Money`
> positionally and will fail to compile with a new field; `RefundCalculator`
> only reads `.amount` and is unaffected.
>
> I could not separate direct from transitive dependents: the CLI blast radius
> is a flat list with no depth. Registering the MCP server would give per-
> dependent depth and a PageRank ranking over exactly these 47.

**What the skill did not do:** estimate effort, propose a migration order, or
decide whether the field should be optional.

---

## 3. Architecture understanding

> "I have just joined this team. How is this codebase organized?"

**Pattern:** Analyze architecture (4).

```bash
wicked-estate stats
wicked-estate clusters --json
wicked-estate rank
wicked-estate entrypoints --json
wicked-estate source --cluster 3 --json --signatures-only
```

**A good answer looks like:**

> **Observed.** 8,412 symbols, 31,006 edges. Louvain finds 12 communities above
> size 2. The three largest are cluster 1 (1,204 symbols, mostly
> `ingest/`), cluster 3 (890, spanning `billing/` and `invoicing/`), and
> cluster 7 (455, `api/`). The highest-PageRank symbol overall is
> `EventBus::publish`. There are 34 entry points, 29 of them HTTP route
> handlers in `api/`.
>
> **Interpretation.** Cluster 3 spanning two directories suggests billing and
> invoicing are one domain split by folder rather than by responsibility.
> `EventBus::publish` topping the ranking suggests the system is
> event-driven at its core, so changes there will be unusually wide-reaching.
> Both of these are my reading of the structure, not something the graph
> asserts.

**What the skill did not do:** recommend a re-architecture, or grade the design.

---

## 4. Refactoring

> "Is `LegacyAuthAdapter` safe to delete?"

**Pattern:** Understand an entity (1), then analyze change impact (2).

```bash
wicked-estate resolve LegacyAuthAdapter --json
wicked-estate blast-radius LegacyAuthAdapter --json
wicked-estate annotations --symbol <symbol_id> --json
wicked-estate dead-code --json | grep LegacyAuthAdapter
```

**A good answer looks like:**

> `blast-radius` returns 0 resolved dependents, and `dead-code` lists it — so
> nothing in the graph references it.
>
> That is not sufficient to call it safe. `blast-radius` also reports 2
> unresolved references, and edgeless does not mean unused: anything reached by
> reflection, dynamic dispatch, or framework registration looks exactly like
> this. `dead-code` is a wide net — on this catalogue it returns 65% of all
> nodes. I checked its annotations — it carries `deprecated=true`, author
> `platform-team`, confidence 0.9, recorded 2025-11-03. That is a timestamp
> (`ts`), not a verification date; the JSON carries no `last_verified`.
>
> The graph says nothing references it. Confirming it is dead needs a check the
> index cannot perform: a search for string-based references to the class name,
> and whoever owns the auth config.

**What the skill did not do:** delete it, or pronounce it safe. It separated
"the graph shows no references" from "this is unused", which are different
claims.

---

## 5. Migration and modernization

> "We are moving the COBOL batch layer to services. Which COBOL programs carry
> the most downstream dependency weight?"

**Pattern:** Analyze architecture (4), then analyze change impact (2) per
candidate.

```bash
wicked-estate rank
wicked-estate clusters --json
wicked-estate blast-radius CALCINT --json
wicked-estate source CALCINT --json
wicked-estate by-requirement REQ-441          # only if requirements were annotated
```

**A good answer looks like:**

> In the global top-25 by PageRank, the three heaviest batch programs are
> `CALCINT` (interest
> calculation), `POSTGL` (general-ledger posting), and `VALACCT`. `CALCINT`
> has 61 resolved dependents with 14 unresolved call sites — the highest
> unresolved count in the graph, which for COBOL usually means dynamic `CALL`
> targets the indexer could not bind. Its true dependency weight is therefore
> higher than 61.
>
> `clusters` puts `CALCINT` and `POSTGL` in the same community with 23 shared
> members, so they are tightly coupled to each other.
>
> Nothing in the graph records requirements for these programs —
> `by-requirement` returns empty because no one has annotated them, not because
> no requirements exist.

**What the skill did not do — and this is the point of the example:** it did not
assign a migration phase, a wave, a cutover order, or a readiness score. It did
not create a `MIGRATES_TO` relationship. It reported dependency weight,
coupling, and resolution completeness, and handed those to whichever
modernization workflow asked.

A migration pack consuming this skill needs to know nothing about migration to
get that answer, and this skill needs to know nothing about migration to give
it.

---

## The shape all five share

| Layer | Owns | Example |
| --- | --- | --- |
| Wicked Estate | What is true about this estate | 61 dependents, 14 unresolved |
| This skill | How to gather that well and report its limits | Which verb, which stop condition, which caveat |
| The workflow skill | What we are trying to accomplish | Whether to migrate `CALCINT` first |

If an answer from this skill contains a phase, a status, a readiness verdict, or
an approval, the boundary has been crossed.
