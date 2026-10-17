  // ---------------------------------------------------------------- detail
  function nextStep(id) {
    if (deliveryUnavailable()) {
      return 'No next step shown: delivery mapping was incomplete, so this snapshot cannot tell what is open.';
    }
    var type = typeOf(id);
    var word = statusWord(id);
    if (!isOpen(id)) { return 'Nothing to do. It is ' + (word !== '' ? word : 'not open') + '.'; }
    if (type === 'spec') {
      if (word === 'Implementing') { return 'Continue building it with the work-loop skill. It is already being built.'; }
      if (word === 'Approved') { return 'Build it with the work-loop skill. It is approved, and work-loop checks readiness before it starts.'; }
      return 'Finish the spec with the new-spec skill. It needs approval before it is built.';
    }
    if (type === 'brief') {
      return 'Work on it with the author-delivery-brief skill in continue mode. Briefs are delivered through their slices.';
    }
    if (word === 'Accepted') {
      if (hasNothingBeneath(id)) {
        return 'Decompose it with the intent skill. It is accepted but has nothing beneath it yet.';
      }
      return openCount(id) > 0 ? 'Pick an item from Open beneath. Its work is already decomposed.' :
        'Close it with the close-work skill if its outcome is met. Everything beneath it is finished.';
    }
    return 'Keep shaping it with the intent skill. It is not accepted yet.';
  }

  function brokenOf(id) {
    var list = (edgesFrom.get(id) || []).filter(function (e) { return e.state; })
      .map(function (e) { return { holder: id, edge: e }; });
    if (!deliveryUnavailable() && rec(id)) {
      arr(rec(id).delivery_diagnostics).forEach(function (d) {
        if (isObj(d)) { list.push({ holder: id, diag: d }); }
      });
    }
    return list.concat(depEntriesOf(id));
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

