# roadmap fixture

A corpus for the roadmap question and the Browse tree: two product strategies,
nested capabilities, a capability under no strategy, a stopped capability with
an open child capability, a capability with nothing beneath, a capability whose
only work is stopped, every delivery band, a brief with specs placed by `Brief:`,
a refused parent edge, a parentless intent with nothing beneath, and a parent
loop with a tail intent that sorts before the loop's first member.

Every value below is stated by hand from each record's own `Status:` and edges.
A test compares them with a reading of the export's payload, so a wrong
definition shows as a disagreement. Delivery bands: a record that is open and
`Implementing` or `Executing` is in progress; any other open record is not
started; a closed record with status word `Fulfilled` or `Shipped` is delivered;
any other closed record is stopped. Display names are the headings without
their label, in the order a reader sees them.

The resolver breaks the loop by refusing the parent edge of `loop-alpha`, the
member with the lowest slug, so that edge is the only refused loop edge.

## Records

| Node id | Delivery band | Roadmap placement |
| --- | --- | --- |
| `intent:atlas-direction` | not started | heads section "Atlas direction" |
| `intent:boreal-direction` | not started | heads section "Boreal direction" |
| `capability:anchor-cap` | not started | section "Atlas direction" |
| `capability:anchor-sub-cap` | in progress | nested under capability:anchor-cap |
| `intent:anchor-sub-feat-a` | delivered | - |
| `intent:anchor-sub-feat-b` | in progress | - |
| `brief:anchor-sub-brief` | in progress | - |
| `spec:anchor-sub-spec-one` | delivered | - |
| `spec:anchor-sub-spec-two` | not started | - |
| `spec:anchor-sub-spec-three` | not started | - |
| `intent:anchor-feat-open` | not started | - |
| `intent:anchor-feat-child` | not started | - |
| `intent:anchor-feat-withdrawn` | stopped | - |
| `spec:anchor-spec-disc` | delivered | - |
| `capability:birch-cap` | delivered | section "Atlas direction" |
| `intent:birch-feat` | delivered | - |
| `capability:cinder-cap` | not started | section "Atlas direction" |
| `capability:dune-cap` | not started | section "Atlas direction" |
| `intent:dune-feat-cancelled` | stopped | - |
| `brief:dune-brief-withdrawn` | stopped | - |
| `capability:ember-cap` | stopped | section "Boreal direction" |
| `capability:ember-child-cap` | not started | nested under capability:ember-cap |
| `intent:ember-child-feat` | in progress | - |
| `capability:fjord-cap` | in progress | section "Boreal direction" |
| `brief:fjord-brief` | not started | - |
| `brief:fjord-brief-shipped` | delivered | - |
| `spec:fjord-spec` | in progress | - |
| `spec:fjord-spec-archived` | stopped | - |
| `capability:gale-cap` | not started | section "Not under a product strategy in this export" |
| `intent:gale-feat` | not started | - |
| `intent:orphan-feat` | not started | - |
| `intent:dangling-feat` | not started | - |
| `intent:loop-alpha` | not started | - |
| `intent:loop-beta` | not started | - |
| `intent:loop-gamma` | not started | - |
| `intent:acorn-tail` | not started | - |

## Progress

Counts are over each node's work beneath. Share is delivered over current work
(delivered, in progress and not started), rounded half up. Cells are the 24-cell
bar as delivered/in progress/not started/empty.

| Node id | Delivered | In progress | Not started | Stopped | Share | Cells |
| --- | --- | --- | --- | --- | --- | --- |
| `intent:atlas-direction` | 5 | 3 | 7 | 3 | 33% | 8/5/11/0 |
| `intent:boreal-direction` | 1 | 3 | 2 | 2 | 17% | 4/12/8/0 |
| `capability:anchor-cap` | 3 | 3 | 4 | 1 | 30% | 7/7/10/0 |
| `capability:anchor-sub-cap` | 2 | 2 | 2 | 0 | 33% | 8/8/8/0 |
| `capability:birch-cap` | 1 | 0 | 0 | 0 | 100% | 24/0/0/0 |
| `capability:cinder-cap` | 0 | 0 | 0 | 0 | - | no bar |
| `capability:dune-cap` | 0 | 0 | 0 | 2 | - | 0/0/0/24 |
| `capability:ember-cap` | 0 | 1 | 1 | 0 | 0% | 0/12/12/0 |
| `capability:ember-child-cap` | 0 | 1 | 0 | 0 | 0% | 0/24/0/0 |
| `capability:fjord-cap` | 1 | 1 | 1 | 1 | 33% | 8/8/8/0 |
| `capability:gale-cap` | 0 | 0 | 1 | 0 | 0% | 0/0/24/0 |

## Tree roots

| Node id | Full hierarchy placement |
| --- | --- |
| `intent:atlas-direction` | root, intents beneath |
| `intent:boreal-direction` | root, intents beneath |
| `intent:dangling-feat` | root, nothing beneath |
| `capability:gale-cap` | root, intents beneath |
| `intent:loop-alpha` | root, intents beneath |
| `intent:orphan-feat` | root, nothing beneath |
