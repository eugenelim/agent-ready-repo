  // ---------------------------------------------------------------- labels
  var GROUP_LABELS = {
    parent: 'Parent',
    children: 'Child intents',
    briefs: 'Briefs',
    specs: 'Specs',
    relations: 'Delivery relations',
    diagnostics: 'Delivery diagnostics',
    relatedHere: 'Related, written here',
    relatedElsewhere: 'Related, written elsewhere',
    dependsHere: 'Depends on, written here',
    dependsElsewhere: 'Depends on, written elsewhere',
    pointers: 'Pointers'
  };
  var GROUP_HELP = {
    parent: 'The intent above this one (the Parent intent field), resolved or refused.',
    children: 'Intents that name this one as their parent (their Parent intent field).',
    briefs: 'Briefs that name this intent as their parent (their Parent intent field).',
    specs: 'Specs that name this intent as their source (their Discovery field).',
    relations: 'Links that show how this node is delivered, through its briefs and specs.',
    diagnostics: 'Problems the delivery resolver found with this intent.',
    relatedHere: 'Other intents this one lists as related (the Related intents field), resolved or refused.',
    relatedElsewhere: 'Other intents that list this one as related (their Related intents field).',
    dependsHere: 'Each value this intent writes in its Depends on field, with how it was written and what it resolved to.',
    dependsElsewhere: 'Other intents whose Depends on field names this one. The view does not decide whether either can start.',
    pointers: 'Every pointer this brief or spec writes. A pointer is a field that names another record. Each is resolved or refused.'
  };
  var GROUP_ORDER = ['parent', 'children', 'briefs', 'specs', 'relations', 'diagnostics',
    'relatedHere', 'relatedElsewhere', 'dependsHere', 'dependsElsewhere', 'pointers'];
  var STATE_HELP = {
    dangling: 'The pointer names no live record.',
    retired_target: 'The pointer names a retired record.',
    kind_mismatch: 'The pointer names a record of a different kind than it declares.',
    out_of_type: 'The pointer names a record of a type this field does not accept.',
    multiple_values: 'The field carries more than one value.',
    cycle: 'The pointers make a loop: a parent loop would make an intent its own ancestor, and a dependency loop leads a Depends on field back to the same intent.',
    outside_scope: 'The value names a brief or a spec, not an intent, so this view does not follow it.',
    unparseable: 'The value is not a pointer the derivation can read.',
    self_reference: 'The pointer names the record that writes it.'
  };
  // How a Depends on value was written, as the navigator's classifier reads it.
  var FORM_HELP = {
    typed: 'A kind and a name joined by a colon, such as intent:example.',
    path: 'A repository path to a file.',
    bare_slug: 'A name alone, with no kind in front of it.',
    markdown_link: 'A link written as [text](target).',
    unrecognized: 'Text that is none of the other forms.'
  };
  var TRUST_HELP = {
    delivery_contract: 'The delivery resolver reports this link from the records\' own contract.',
    pointer_checked: 'A pointer the derivation checked against a live record.',
    pointer_unchecked: 'A pointer written in a field, not checked beyond resolving it.'
  };
  // State marks: the glyph is decoration, the word beside it is what is read.
  var MARKS = {
    active: { glyph: '\u25CF', help: 'In progress: a spec being built or a brief being delivered.' },
    approved: { glyph: '\u25C6', help: 'Approved, accepted, or a brief ready for its slices.' },
    draft: { glyph: '\u25C7', help: 'Open and still being shaped.' },
    broken: { glyph: '\u2715', help: 'A pointer that did not resolve, a parent or dependency loop made of pointers that did resolve, or a delivery problem.' },
    stale: { glyph: '\u25B3', help: 'The linked file may be newer than this snapshot.' },
    done: { glyph: '\u2713', help: 'Finished or closed: not open work.' }
  };
  var MARK_ORDER = ['active', 'approved', 'draft', 'broken', 'stale', 'done'];
  var ACTIVE_WORDS = { Implementing: true, Executing: true };
  var APPROVED_WORDS = { Approved: true, Accepted: true, Ready: true };
  var NAME_LABELS = ['Spec: ', 'Brief: ', 'Intent: ', 'Feature: ', 'Capability: ', 'Outcome: ',
    'Opportunity: '];
  var TYPE_NAMES = { intent: 'Intent', brief: 'Brief', spec: 'Spec' };
  var TYPE_GROUPS = [['intent', 'Intents'], ['brief', 'Briefs'], ['spec', 'Specs']];

  // Each question has a short label for the rail and its full question (`name`), which a list shows
  // above its title and a rail link carries as its description.
  var QUESTIONS = [
    { key: 'next', label: 'Next up', name: 'What can I work on next?', title: 'In a startable stage',
      lead: 'Readiness not checked in this snapshot.', sort: 'By stage, then name',
      empty: 'Nothing is in a startable stage.', noun: ['item', 'items'] },
    { key: 'broken', label: 'Broken', name: 'What is broken?', title: 'Broken pointers and delivery problems',
      lead: 'Pointers that did not resolve, parent or dependency loops made of resolved pointers, and problems the delivery resolver found.',
      sort: 'By name', empty: 'Nothing is broken.', noun: ['entry', 'entries'] },
    { key: 'roadmap', label: 'Capability progress', name: 'How far along is each capability?', title: 'Capability progress',
      lead: 'All work beneath each capability, by delivery stage, grouped under each product strategy.',
      sort: 'By strategy, then name', empty: 'No capability is recorded.',
      noun: ['capability', 'capabilities'] },
    { key: 'capabilities', label: 'Open by capability', name: 'What is still open under a capability?',
      title: 'Capabilities with open work', lead: 'Pick a capability to see the open work beneath it.',
      sort: 'By open count, then name', empty: 'No capability has open work beneath it.',
      noun: ['capability', 'capabilities'] },
    { key: 'noparent', label: 'No parent', name: 'What has no parent?', title: 'Open with no parent',
      lead: 'Open items whose parent pointer is absent or did not resolve.',
      sort: 'By type, then name', empty: 'Every open item has a parent.', noun: ['item', 'items'],
      filters: ['type', 'level'] },
    { key: 'browse', label: 'All intents', name: 'Browse all intents', title: 'All intents',
      lead: 'Every intent in the export, under its parent.', sort: 'Under each parent, by name',
      empty: 'No intents were found.', noun: ['intent', 'intents'],
      filters: ['level', 'kind', 'status'] }
  ];
  // The rail's lists: each is named by its visible label, through aria-labelledby.
  var RAIL_GROUPS = [
    { key: 'work', label: 'Work', questions: ['next', 'broken'] },
    { key: 'progress', label: 'Progress', questions: ['roadmap', 'capabilities'] },
    { key: 'tidy', label: 'Tidy', questions: ['noparent'] },
    { key: 'browse', label: 'Browse', questions: ['browse'] }
  ];
  var FILTER_LABELS = { type: ['Type', 'Any type'], level: ['Level', 'Any level'],
    kind: ['Kind', 'Any kind'], status: ['Status', 'Any status'] };
  var ROUTE_KEYS = ['q', 'node', 'search', 'type', 'level', 'kind', 'status', 'dir', 'steps', 'show',
    'group'];
  // The "Dependencies" controls: the offered choices, with the default first.
  var DIR_CHOICES = [['prerequisites', 'What it waits for'], ['dependents', 'What waits for it'],
    ['both', 'Both']];
  var STEP_CHOICES = [['1', '1'], ['2', '2'], ['3', '3'], ['all', 'All']];
  var FILTER_KEYS = ['type', 'level', 'kind', 'status'];

