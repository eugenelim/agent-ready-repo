  // ---------------------------------------------------------------- detail
  // The ten next-step rules, in the session-start order; one table holds every sentence.
  var NEXT_STEP_SENTENCES = [
    '',
    'No next step shown: delivery mapping was incomplete, so this snapshot cannot tell what is open.',
    null,
    'Continue building it with the work-loop skill. It is already being built.',
    'Build it with the work-loop skill. It is approved, and work-loop checks readiness before it starts.',
    'Finish the spec with the new-spec skill. It needs approval before it is built.',
    'Work on it with the author-delivery-brief skill in continue mode. Briefs are delivered through their slices.',
    'Decompose it with the intent skill. It is accepted but has nothing beneath it yet.',
    'Pick an item from Open beneath. Its work is already decomposed.',
    'Close it with the close-work skill if its outcome is met. Everything beneath it is finished.',
    'Keep shaping it with the intent skill. It is not accepted yet.'
  ];

  // The first session-start rule (1 to 10) that matches the record.
  function nextStepRule(id) {
    if (deliveryUnavailable()) { return 1; }
    if (!isOpen(id)) { return 2; }
    var type = typeOf(id);
    var word = statusWord(id);
    if (type === 'spec') { return word === 'Implementing' ? 3 : (word === 'Approved' ? 4 : 5); }
    if (type === 'brief') { return 6; }
    if (word === 'Accepted') {
      if (hasNothingBeneath(id)) { return 7; }
      return openCount(id) > 0 ? 8 : 9;
    }
    return 10;
  }

  function nextStep(id) {
    var rule = nextStepRule(id);
    if (rule === 2) {
      var word = statusWord(id);
      return 'Nothing to do. It is ' + (word !== '' ? word : 'not open') + '.';
    }
    return NEXT_STEP_SENTENCES[rule];
  }

  function brokenOf(id) {
    var list = (edgesFrom.get(id) || []).filter(function (e) { return e.state; })
      .map(function (e) { return { holder: id, edge: e }; });
    if (!deliveryUnavailable() && rec(id)) {
      arr(rec(id).delivery_diagnostics).forEach(function (d) {
        if (isObj(d)) { list.push({ holder: id, diag: d }); }
      });
    }
    return list.concat(depEntriesOf(id), workspaceEntriesOf(id));
  }

  // A work-loop dispatch finding: a known one reads with its action; one this view does not know
  // keeps the action under a label saying where it came from.  Both are text only.
  function workspaceBroken(li, w) {
    if (w.known) {
      add(li, el('p', 'meaning diag-raw', 'Workspace finding ' + w.code + ': ' + w.next_action));
      return;
    }
    add(li, el('p', 'meaning diag-raw', 'Workspace finding ' + w.code + '.'));
    var note = add(li, el('div', 'edge-line'));
    add(note, el('span', 'field', 'Note from work-loop\'s dispatch:'));
    add(note, el('span', 'value diag-raw', w.next_action));
  }

  // A dependency broken entry in the holder's "What is broken" part: the field, the Key's meaning
  // of its state, then the value written (a fault) or the other members (a cycle).
  function dependencyBroken(li, id, b) {
    var state = b.cycle ? 'cycle' : b.dep.state;
    var line = add(li, el('div', 'edge-line'));
    add(line, el('span', 'field', 'Depends on:'));
    var chip = stateChip(state);
    add(line, chip || el('span', 'value', String(state)));
    if (own(STATE_HELP, state) !== undefined) { add(li, el('p', 'meaning', own(STATE_HELP, state))); }
    var detail = add(li, el('div', 'edge-line'));
    if (b.dep) {
      add(detail, el('code', 'value', b.dep.value));
      return;
    }
    var others = b.cycle.members.filter(function (m) { return m !== id; });
    if (!others.length) {
      add(detail, el('span', 'note', 'It names itself.'));
    }
    others.forEach(function (m) { add(detail, namedIntent(m)); });
  }

