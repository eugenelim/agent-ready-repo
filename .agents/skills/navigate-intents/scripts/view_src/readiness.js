  // -------------------------------------------------------------- readiness
  // The payload's readiness member is work-loop's dispatch view of the work, read once when the
  // snapshot was made.  It holds ids of loaded records, finding codes and plain sentences; every
  // string is shown as text through the element helpers and never reaches a link or a prompt.
  var START_PHRASE = 'work-loop with no spec named';
  // One sentence for each reason a check can fail; not_requested is the quiet default.
  var REASON_TEXT = {
    unreadable: 'standard input could not be read',
    timed_out: 'nothing finished arriving within 60 seconds',
    too_large: 'the piped input was larger than 4 MiB',
    empty: 'nothing was piped in',
    not_json: 'the piped input was not valid JSON',
    wrong_schema: 'the piped input was not argless work-loop dispatch output this view reads',
    bad_workspace: 'work-loop\'s dispatch could not use workspace.toml',
    page_too_big: 'the page would have been too large with it'
  };
  var START_RULES = { resume: true, start: true, ask: true, none: true };
  var READINESS_GROUPS = [['active', 'Active'], ['ready', 'Ready'], ['blocked', 'Blocked']];
  // "What is broken?" while it holds workspace findings: the shipped lead, naming that source too.
  var BROKEN_WITH_FINDINGS = 'Pointers that did not resolve, parent or dependency loops made of resolved ' +
    'pointers, problems the delivery resolver found, and findings work-loop\'s dispatch reported.';
  var CHECKED_NEXT = { title: 'Active, ready and blocked',
    lead: 'Readiness from work-loop\'s dispatch, read when this snapshot was made.',
    sort: 'Active, then ready, then blocked, in dispatch order',
    empty: 'work-loop\'s dispatch lists nothing active, ready or blocked in this export.' };

  function readinessChecked() { return readiness !== null && readiness.checked === true; }

  // The rows of each group, in payload order; a group with no row is left out.
  function readinessGroups(owner) {
    var found = [];
    READINESS_GROUPS.forEach(function (pair) {
      var key = pair[0];
      var ids = key === 'blocked' ? readiness.blocked.map(function (b) { return b.id; }) : readiness[key];
      ids = ownerOnly(ids.filter(function (id) { return nodes.has(id); }), owner || '');
      if (ids.length) { found.push({ key: key, head: pair[1], ids: ids }); }
    });
    return found;
  }
  function readinessRowCount(owner) {
    return readinessGroups(owner).reduce(function (sum, g) { return sum + g.ids.length; }, 0);
  }
  // Each code of a blocked item is one broken entry, held by that item.  The finding's
  // own path never holds anything: only the blocked item's id does.
  function workspaceEntries() {
    var list = [];
    if (!readinessChecked()) { return list; }
    readiness.blocked.forEach(function (b) {
      if (!nodes.has(b.id)) { return; }
      b.findings.forEach(function (f) {
        list.push({ holder: b.id, workspace: { code: f.code, next_action: f.next_action, known: f.known } });
      });
    });
    return list;
  }
  function workspaceEntriesOf(id) {
    return workspaceEntries().filter(function (entry) { return entry.holder === id; });
  }
  function blockedCodes(id) {
    for (var i = 0; i < readiness.blocked.length; i++) {
      if (readiness.blocked[i].id === id) {
        return readiness.blocked[i].findings.map(function (f) { return f.code; });
      }
    }
    return [];
  }
  // A group's row: the readiness mark, then the usual context, and a blocked row ends with its
  // codes, each set as a code the way "What is broken?" sets it.
  function readinessRow(group) {
    return function (id) {
      var li = el('li', 'row');
      var context = contextText(id);
      var codes = group === 'blocked' ? blockedCodes(id) : [];
      if (codes.length) {
        var cell = el('span');
        text(cell, context + ' \u00B7 ');
        codes.forEach(function (code, i) {
          if (i > 0) { text(cell, ', '); }
          add(cell, el('span', 'value wrap', code));
        });
        context = cell;
      }
      var word = group.charAt(0).toUpperCase() + group.slice(1);
      add(li, rowLink(id, markEl(group, word), context, startTagText(id)));
      return li;
    };
  }

  function startTagText(id) {
    if (!readinessChecked() || readiness.start.id !== id) { return ''; }
    return START_PHRASE + (readiness.start.rule === 'resume' ? ' resumes this' : ' starts this');
  }
  // Why no row carries the start tag, when none does.
  function startLine() {
    var s = readiness.start;
    if (!readinessChecked() || s.id !== null) { return ''; }
    var verb = s.rule === 'resume' ? 'resume' : 'start';
    if (s.rule === 'ask') {
      return START_PHRASE + (s.active_count > 0
        ? ' asks which of the ' + s.active_count + ' active items to resume, so none is marked.'
        : ' asks which ready item to start, so none is marked.');
    }
    if (s.rule === 'none') { return START_PHRASE + ' finds nothing to start or resume.'; }
    return START_PHRASE + ' would ' + verb + ' an item outside this export, so none is marked.';
  }
  // The notice or the start line that sits above the first list.
  function readinessPreface() {
    var frag = document.createDocumentFragment();
    if (readinessChecked()) {
      var line = startLine();
      if (line !== '') { add(frag, el('p', 'note', line)); }
    } else if (readiness !== null && readiness.reason !== 'not_requested') {
      add(frag, el('p', 'notice', 'Readiness could not be checked: ' + own(REASON_TEXT, readiness.reason) +
        '. Run work-loop\'s dispatch to see what is ready.'));
    }
    return frag;
  }
  // The question with its title, lead and sort key replaced while readiness is checked.
  function checkedQuestion(q) {
    if (!readinessChecked()) { return q; }
    if (q.key === 'broken' && workspaceEntries().length) { return Object.assign({}, q, { lead: BROKEN_WITH_FINDINGS }); }
    if (q.key !== 'next') { return q; }
    return Object.assign({}, q, { title: CHECKED_NEXT.title, lead: CHECKED_NEXT.lead, sort: CHECKED_NEXT.sort });
  }

