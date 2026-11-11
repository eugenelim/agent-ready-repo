  // ---------------------------------------------------------- dependencies
  // Breadth-first step counts from start along one direction's neighbour lists; start is 0.
  function walkSteps(start, adj, limit) {
    var seen = new Map([[start, 0]]);
    var frontier = [start];
    for (var d = 1; d <= limit && frontier.length; d++) {
      var next = [];
      frontier.forEach(function (at) {
        (adj.get(at) || []).forEach(function (to) {
          if (!seen.has(to)) { seen.set(to, d); next.push(to); }
        });
      });
      frontier = next;
    }
    return seen;
  }

  // What the query returns for the same choices: the intents within `limit` steps, every edge
  // with both ends among them, their pointer diagnostics and the cycle groups they touch.
  function dependencyResult(id, dir, limit) {
    var counts = new Map();
    if (dir !== 'dependents') { counts = walkSteps(id, depOut, limit); }
    if (dir !== 'prerequisites') {
      walkSteps(id, depIn, limit).forEach(function (n, at) {
        if (!counts.has(at) || n < counts.get(at)) { counts.set(at, n); }
      });
    }
    var edges = [];
    var pointers = [];
    var cycles = new Set();
    counts.forEach(function (_n, at) {
      (depEdgesFrom.get(at) || []).forEach(function (e) {
        if (counts.has(e.to)) { edges.push({ edge: e, step: Math.max(counts.get(e.from), counts.get(e.to)) }); }
      });
      (depPointers.get(at) || []).forEach(function (d) { pointers.push(d); });
      (depCycles.get(at) || []).forEach(function (c) { cycles.add(c); });
    });
    edges.sort(function (a, b) {
      return (a.step - b.step) || byName(a.edge.from, b.edge.from) || byName(a.edge.to, b.edge.to);
    });
    // Source name order, then written order (the lists are already in written order).
    pointers.sort(function (a, b) { return byName(a.from, b.from) || (posOf(a) - posOf(b)); });
    var ordered = Array.from(cycles).sort(function (a, b) { return byName(a.members[0], b.members[0]); });
    return { counts: counts, edges: edges, pointers: pointers, cycles: ordered };
  }

  // One line reads waiting end, then "waits for" with the prerequisite end, so the
  // connector stays with the name it points to; the picked intent's end is marked.
  function dependencyEnd(id, picked, cls) {
    var end = el('span', id === picked ? cls + ' dep-self' : cls);
    add(end, namedIntent(id));
    if (id === picked) {
      var self = end.querySelector('a');
      if (self) { self.setAttribute('aria-current', 'true'); }
    }
    return end;
  }
  function dependencyLine(entry, picked) {
    var li = el('li', 'edge dep-line');
    var row = add(li, el('div', 'dep-row'));
    add(row, dependencyEnd(entry.edge.from, picked, 'dep-waiting'));
    var to = add(row, el('span', 'dep-to'));
    add(to, el('span', 'dep-word', 'waits for'));
    add(to, dependencyEnd(entry.edge.to, picked, 'dep-prereq'));
    return li;
  }

  // The value in a code element with a <wbr> after each slash, backslash or colon so a long path breaks at a separator;
  // the element's text is the value itself.
  function breakableValue(value) {
    var code = el('code', 'value');
    String(value).split(/([\/\\:])/).forEach(function (piece, i) {
      if (i % 2) { text(code, piece); add(code, document.createElement('wbr')); } else if (piece) { text(code, piece); }
    });
    return code;
  }

  function dependencyFault(d) {
    var li = el('li', 'edge dep-diag');
    var line = add(li, el('div', 'edge-line'));
    var outside = d.state === 'outside_scope';
    if (!outside) {
      add(line, markEl('broken', 'Broken'));
      var chip = stateChip(d.state);
      add(line, chip || el('span', 'value', String(d.state)));
    }
    add(add(line, el('span', 'dep-source')), namedIntent(d.from));
    add(line, breakableValue(isStr(d.value) ? d.value : ''));
    if (outside) { add(line, el('span', 'note-inline', 'not an intent, outside this view')); }
    return li;
  }

  function dependencyCycle(c) {
    var li = el('li', 'edge dep-diag');
    var line = add(li, el('div', 'edge-line'));
    add(line, markEl('broken', 'Broken'));
    add(line, stateChip('cycle'));
    var members = add(line, el('span', 'dep-members'));
    c.members.forEach(function (m) { add(members, namedIntent(m)); });
    return li;
  }

  var EMPTY_LINES = { prerequisites: 'It waits for nothing in its Depends on: header.',
    dependents: 'No intent\'s Depends on: header names it.', both: 'No dependencies recorded.' };

  function fillDependencies(id, route) {
    var dir = route.dir || 'prerequisites';
    var limit = route.steps === 'all' ? Infinity : parseInt(route.steps || '1', 10);
    dom.depDir.value = dir;
    dom.depSteps.value = route.steps || '1';
    clear(dom.depBody);
    var res = dependencyResult(id, dir, limit);
    var has = res.pointers.length + res.cycles.length > 0;
    if (res.edges.length) {
      add(dom.depBody, el('p', 'note dep-sort', 'Nearest first, then by name'));
      var ul = add(dom.depBody, el('ul', 'plain dep-lines'));
      res.edges.forEach(function (entry) { add(ul, dependencyLine(entry, id)); });
    } else {
      add(dom.depBody, el('p', 'empty', has ? 'No line to show. Its Depends on: values are listed below.' :
        EMPTY_LINES[dir]));
    }
    if (has) {
      var dl = add(dom.depBody, el('ul', 'plain dep-diags'));
      res.pointers.forEach(function (d) { add(dl, dependencyFault(d)); });
      res.cycles.forEach(function (c) { add(dl, dependencyCycle(c)); });
    }
  }

  function dependencySelect(key, label, choices) {
    var field = add(dom.depControls, el('div', 'field'));
    var selectId = 'dep-' + key;
    var lab = add(field, el('label', '', label));
    lab.setAttribute('for', selectId);
    var select = add(field, el('select', 'control'));
    select.setAttribute('id', selectId);
    choices.forEach(function (c) {
      var o = add(select, el('option', '', c[1]));
      o.setAttribute('value', c[0]);
    });
    select.addEventListener('change', function () {
      var over = {};
      over[key] = select.value === choices[0][0] ? '' : select.value;
      replaceRoute(over);
    });
    return select;
  }

  function dependenciesPart(id, route) {
    var sec = part('Dependencies');
    add(sec, el('p', 'lead', 'From Depends on: headers only. This does not check whether work can start.'));
    dom.depControls = add(sec, el('div', 'dep-controls'));
    dom.depDir = dependencySelect('dir', 'Show', DIR_CHOICES);
    dom.depSteps = dependencySelect('steps', 'Steps', STEP_CHOICES);
    dom.depBody = add(sec, el('div', 'dep-body'));
    fillDependencies(id, route);
  }

