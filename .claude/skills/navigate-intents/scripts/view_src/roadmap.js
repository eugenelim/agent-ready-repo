  // ----------------------------------------------------------- roadmap
  // Capabilities under their product strategies, each with how much of the work beneath it is
  // delivered, in progress or not started. Every number is read from the payload's records, edges
  // and open items; the view states no health, only counts.
  var BAR_CELLS = 24;
  var DELIVERED_WORDS = { Fulfilled: true, Shipped: true };
  var BAND_LABELS = [['delivered', 'delivered'], ['active', 'in progress'],
    ['waiting', 'not started']];
  var NO_STRATEGY_HEADING = 'Not under a product strategy in this export';
  var UNKNOWN_PROGRESS = 'Progress unknown: delivery mapping incomplete.';

  // A band reads the shipped open-item index and status word: an open item is in progress when its
  // status word is active, else not started; a closed one is delivered or stopped by its word.
  function bandOf(id) {
    var word = statusWord(id);
    if (isOpen(id)) { return own(ACTIVE_WORDS, word) ? 'active' : 'waiting'; }
    return own(DELIVERED_WORDS, word) ? 'delivered' : 'stopped';
  }

  // Specs of each brief, from the resolved Brief: edges; indexed once.
  var specsOfBrief = null;
  function briefSpecs(id) {
    if (specsOfBrief === null) {
      specsOfBrief = new Map();
      data.edges.forEach(function (e) {
        if (e.field === 'Brief' && !e.state && isStr(e.to)) { addTo(specsOfBrief, e.to, e.from); }
      });
    }
    return specsOfBrief.get(id) || [];
  }

  // Every intent, brief and spec reached from a node through children, briefs, specs and their
  // briefs' specs; the node itself is left out and each reached node counts once.
  function workBeneath(id) {
    var reached = new Set();
    var todo = [id];
    while (todo.length) {
      var at = todo.pop();
      var r = rec(at);
      var found = r ? arr(r.children).concat(arr(r.briefs), arr(r.specs)) : briefSpecs(at);
      found.forEach(function (next) {
        if (isStr(next) && nodes.has(next) && !reached.has(next)) { reached.add(next); todo.push(next); }
      });
    }
    reached.delete(id);
    return reached;
  }

  // Largest-remainder apportionment of the bar's cells over the three live bands: each band takes
  // the integer part of its share, and each leftover cell goes to the largest remainder, ties to
  // the earlier band.
  function apportion(counts, current) {
    var cells = counts.map(function (n) { return Math.floor(BAR_CELLS * n / current); });
    var spare = BAR_CELLS - cells.reduce(function (a, b) { return a + b; }, 0);
    counts.map(function (n, i) { return { i: i, rem: (BAR_CELLS * n) % current }; })
      .sort(function (a, b) { return (b.rem - a.rem) || (a.i - b.i); })
      .slice(0, spare)
      .forEach(function (x) { cells[x.i] += 1; });
    return cells;
  }

  var progressCache = new Map();
  function progressOf(id) {
    var p = progressCache.get(id);
    if (p === undefined) {
      var beneath = workBeneath(id);
      var counts = { delivered: 0, active: 0, waiting: 0, stopped: 0 };
      beneath.forEach(function (x) { counts[bandOf(x)] += 1; });
      var current = counts.delivered + counts.active + counts.waiting;
      p = { counts: counts, current: current, nothing: beneath.size === 0,
        share: current ? Math.floor((200 * counts.delivered + current) / (2 * current)) : null };
      progressCache.set(id, p);
    }
    return p;
  }

  function barCells(p) {
    var bar = el('span', 'rm-bar');
    bar.setAttribute('aria-hidden', 'true');
    var classes = [];
    if (p.current) {
      var live = apportion([p.counts.delivered, p.counts.active, p.counts.waiting], p.current);
      ['rm-delivered', 'rm-inprogress', 'rm-notstarted'].forEach(function (cls, i) {
        for (var k = 0; k < live[i]; k++) { classes.push(cls); }
      });
    } else {
      for (var e = 0; e < BAR_CELLS; e++) { classes.push('rm-empty'); }
    }
    classes.forEach(function (cls) { add(bar, el('span', 'rm-cell ' + cls)); });
    return bar;
  }

  function progressEl(id) {
    var box = el('span', 'rm-progress');
    if (deliveryUnavailable()) { add(box, el('span', 'rm-unknown', UNKNOWN_PROGRESS)); return box; }
    var p = progressOf(id);
    if (p.nothing) { add(box, el('span', 'rm-none', 'Nothing beneath yet')); return box; }
    add(box, barCells(p));
    if (p.share !== null) { add(box, el('span', 'rm-pct', p.share + '%')); }
    var words = add(box, el('span', 'rm-words'));
    BAND_LABELS.forEach(function (pair) {
      var n = p.counts[pair[0]];
      if (n || pair[0] === 'delivered') { add(words, el('span', 'rm-w', n + ' ' + pair[1])); }
    });
    if (p.counts.stopped) { add(words, el('span', 'rm-w', p.counts.stopped + ' stopped')); }
    return box;
  }

  // The first intent of a level met walking resolved parent edges upward, within the export.
  function nearestUp(id, level) {
    var seen = new Set([id]);
    var at = resolvedParent(rec(id));
    while (at !== null && rec(at) !== null && !seen.has(at)) {
      if ((rec(at).level || '') === level) { return at; }
      seen.add(at);
      at = resolvedParent(rec(at));
    }
    return null;
  }

  function capabilityRow(id, nested) {
    var li = el('li', 'row rm-row');
    var a = add(li, el('a', 'row-link rm-link'));
    a.setAttribute('href', hashFor({ node: id }));
    a.setAttribute('data-node', id);
    add(a, el('span', 'c-name', displayName(id)));
    add(add(a, el('span', 'c-state')), stateMark(id));
    add(a, progressEl(id));
    if (current !== null && current.node === id) { a.setAttribute('aria-current', 'true'); }
    var inside = (nested.get(id) || []).sort(byName);
    if (inside.length) {
      var sub = add(li, el('ul', 'rows rm-sub'));
      inside.forEach(function (c) { add(sub, capabilityRow(c, nested)); });
    }
    return li;
  }

  function bodyRoadmap() {
    var ids = capabilityRecordIds();
    if (!ids.length) { add(dom.list, emptyLine(question('roadmap').empty)); return 0; }
    var nested = new Map();
    var sections = new Map();
    ids.forEach(function (id) {
      var above = nearestUp(id, 'capability');
      if (above !== null) { addTo(nested, above, id); return; }
      addTo(sections, nearestUp(id, 'product-strategy') || '', id);
    });
    var strategies = Array.from(sections.keys()).filter(function (k) { return k !== ''; }).sort(byName);
    if (sections.has('')) { strategies.push(''); }
    strategies.forEach(function (strategy) {
      var section = add(dom.list, el('section', 'rm-section'));
      var head = add(section, el('div', 'rm-head'));
      add(head, el('h3', 'group-head rm-title',
        strategy === '' ? NO_STRATEGY_HEADING : displayName(strategy)));
      if (strategy !== '') { add(head, progressEl(strategy)); }
      var ul = add(section, el('ul', 'rows'));
      sections.get(strategy).sort(byName).forEach(function (c) { add(ul, capabilityRow(c, nested)); });
    });
    return ids.length;
  }
