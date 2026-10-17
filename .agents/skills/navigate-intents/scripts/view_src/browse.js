  // ------------------------------------------------------------ browse tree
  // "Browse all intents": a tree in sections, a Show choice (all, open or done), a Group choice
  // (full hierarchy or by capability) and expand controls. Show and Group live in the route, so a
  // change replaces the fragment and a reload restores it.
  var LEVEL_WORDS = { 'product-vision': 'Vision', 'product-strategy': 'Strategy',
    capability: 'Capability', feature: 'Feature' };
  var SHOW_CHOICES = [['', 'All'], ['open', 'Open'], ['done', 'Done']];
  var GROUP_CHOICES = [['', 'Full hierarchy'], ['capability', 'By capability']];
  var FILTER_HINT = 'Grouping and expanding are off while a filter is set.';
  var OPEN_UNKNOWN = 'Open and done are unknown: delivery mapping incomplete.';

  function levelWord(id) {
    var level = rec(id) ? (rec(id).level || '') : '';
    return level === '' ? 'Unrecorded' : (own(LEVEL_WORDS, level) || level);
  }

  // Tree roots: intents whose parent edge is absent, refused or outside the export, then, of the
  // intents no root reaches, each member of a parent loop in name order that no earlier root has
  // reached. An intent hanging beneath a loop is reached through it. A scoped export has one root.
  function treeRoots() {
    var scope = data.scope.from;
    if (isStr(scope) && rec(scope) !== null) { return [scope]; }
    var roots = recordIds.filter(function (id) {
      var parent = resolvedParent(rec(id));
      return parent === null || own(data.records, parent) === undefined;
    });
    var reach = new Set();
    function reachFrom(starts) {
      var stack = starts.slice();
      while (stack.length) {
        var at = stack.pop();
        if (reach.has(at)) { continue; }
        reach.add(at);
        (kidsOf.get(at) || []).forEach(function (k) { stack.push(k); });
      }
    }
    function onLoop(id) {
      var path = [];
      var at = id;
      while (at !== null && path.indexOf(at) === -1) {
        path.push(at);
        at = resolvedParent(rec(at));
      }
      return at !== null && path.indexOf(id) >= path.indexOf(at);
    }
    reachFrom(roots);
    recordIds.slice().sort(byName).forEach(function (id) {
      if (!reach.has(id) && onLoop(id)) { roots.push(id); reachFrom([id]); }
    });
    return roots.sort(byName);
  }

  // Each grouping gives its sections' ids and every row's children, so an intent appears once.
  function hierarchyTree() {
    var kids = new Map();
    var claimed = new Set();
    var roots = treeRoots();
    roots.forEach(function (id) { claimed.add(id); });
    var stack = roots.slice();
    while (stack.length) {
      var id = stack.pop();
      var mine = (kidsOf.get(id) || []).filter(function (k) { return !claimed.has(k); });
      mine.forEach(function (k) { claimed.add(k); stack.push(k); });
      kids.set(id, mine);
    }
    var scoped = isStr(data.scope.from);
    var parents = roots.filter(function (r) { return scoped || kids.get(r).length > 0; });
    return { kids: kids, main: ['Hierarchy roots', parents],
      rest: ['No parent and nothing beneath', roots.filter(function (r) { return parents.indexOf(r) === -1; })] };
  }
  function capabilityTree() {
    var kids = new Map();
    var tops = [];
    var loose = [];
    recordIds.forEach(function (id) {
      var anchor = nearestUp(id, 'capability');
      if (anchor !== null) { addTo(kids, anchor, id); }
      else if ((rec(id).level || '') === 'capability') { tops.push(id); }
      else { loose.push(id); }
    });
    kids.forEach(function (list) { list.sort(byName); });
    return { kids: kids, main: ['Top-level capabilities', tops.sort(byName)],
      rest: ['Not under a capability', loose.sort(byName)] };
  }

  // The count of intents beneath a row in the current grouping, and how many of them are closed.
  function tally(id, ctx) {
    var t = ctx.tally.get(id);
    if (t === undefined) {
      t = { total: 0, closed: 0 };
      (ctx.kids.get(id) || []).forEach(function (k) {
        var s = tally(k, ctx);
        t.total += 1 + s.total;
        t.closed += (isOpen(k) ? 0 : 1) + s.closed;
      });
      ctx.tally.set(id, t);
    }
    return t;
  }

  function treeContext(id, ctx, context) {
    var box = el('span', 'tree-ctx');
    if (context) {
      add(box, el('span', 'ctx-tag', 'context')).setAttribute('aria-hidden', 'true');
      add(box, el('span', 'visually-hidden', 'shown for context'));
    }
    // The shipped context stays, so a refused parent and an outside parent still show.
    add(box, el('span', 'tree-where', contextText(id)));
    if (ctx.counts) {
      var t = tally(id, ctx);
      if (t.total) { add(box, el('span', 'tree-roll', t.closed + '/' + t.total + ' closed')); }
      var open = openCount(id);
      if (open) { add(box, el('span', 'tree-open', open + ' open items')); }
    }
    return box;
  }

  function treeRow(id, ctx, section) {
    var li = el('li', 'row tree-row');
    var context = !ctx.match(id);
    if (context) { li.classList.add('context-only'); }
    var kids = (ctx.kids.get(id) || []).filter(ctx.shown);
    var sub = null;
    var toggle = null;
    if (kids.length) {
      toggle = add(li, button('toggle'));
      toggle.setAttribute('aria-expanded', 'false');
      add(toggle, el('span', 'toggle-g', '\u25B8')).setAttribute('aria-hidden', 'true');
      add(toggle, el('span', 'visually-hidden', 'Show ' + kids.length + ' beneath ' + displayName(id)));
    } else {
      add(li, el('span', 'toggle-spacer')).setAttribute('aria-hidden', 'true');
    }
    var link = add(li, rowLink(id, stateMark(id), treeContext(id, ctx, context)));
    // The name cell keeps the display name alone; the tag follows it inside one first cell.
    var title = el('span', 'c-title');
    link.insertBefore(title, link.firstChild);
    add(title, link.querySelector('.c-name'));
    text(title, ' ');
    var tag = add(title, el('span', 'level-tag', levelWord(id)));
    tag.setAttribute('data-level', rec(id) ? (rec(id).level || '') : '');
    if (toggle) {
      // A reader's own choice is remembered across renders; a Show choice opens what it shows.
      var setOpen = function (open, remember) {
        if (open && sub === null) {
          sub = el('ul', 'rows subtree');
          kids.forEach(function (kid) { add(sub, treeRow(kid, ctx, section)); });
          li.appendChild(sub);
        }
        if (sub !== null) { sub.hidden = !open; }
        toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
        toggle.firstChild.textContent = open ? '\u25BE' : '\u25B8';
        if (remember) { if (open) { expanded.add(id); } else { expanded.delete(id); } }
      };
      ctx.openers.push({ section: section, set: setOpen });
      toggle.addEventListener('click', function () {
        setOpen(toggle.getAttribute('aria-expanded') !== 'true', true);
      });
      if (ctx.auto || expanded.has(id)) { setOpen(true, false); }
    }
    return li;
  }

  // One-line summary the list header shows: it follows the Show and Group choices.
  function browseSummary(route) {
    var show = deliveryUnavailable() ? '' : route.show;
    var prefix = show === 'open' ? 'Open work only. ' : (show === 'done' ? 'Done work only. ' : '');
    var under = route.group === 'capability' ? 'its nearest capability' : 'its parent';
    return { lead: prefix + 'Every intent in the export, under ' + under + '.',
      sort: route.group === 'capability' ? 'Under each capability, by name' : 'Under each parent, by name' };
  }

  // A segment is one labelled group of buttons; isOff says which of its buttons are disabled.
  function choiceGroup(label, key, choices, pressed, isOff) {
    var group = el('div', 'seg');
    group.setAttribute('role', 'group');
    var head = add(group, el('span', 'seg-label', label));
    head.setAttribute('id', 'seg-' + key);
    group.setAttribute('aria-labelledby', 'seg-' + key);
    choices.forEach(function (choice) {
      var b = add(group, button('seg-btn', choice[1]));
      b.setAttribute('aria-pressed', choice[0] === pressed ? 'true' : 'false');
      b.setAttribute('data-ctl', key + '-' + (choice[0] || 'default'));
      if (isOff(choice[0])) { b.setAttribute('disabled', ''); }
      b.addEventListener('click', function () {
        var over = {};
        over[key] = choice[0];
        replaceRoute(over);
      });
    });
    return group;
  }

  // The first section's rows are the ones the expand controls act on; a section's disclosure is
  // never opened or closed by them. While a filter is set the list is flat, so grouping and
  // expanding have nothing to act on.
  function browseBar(show, group, ctx, filtered) {
    var bar = el('div', 'tree-bar');
    var unknown = deliveryUnavailable();
    add(bar, choiceGroup('Show', 'show', SHOW_CHOICES, show, function (v) { return unknown && v !== ''; }));
    add(bar, choiceGroup('Group', 'group', GROUP_CHOICES, group, function () { return filtered; }));
    var tools = add(bar, el('div', 'tree-actions'));
    [['Expand all', true], ['Collapse all', false]].forEach(function (pair) {
      var b = add(tools, button('seg-btn', pair[0]));
      if (filtered) { b.setAttribute('disabled', ''); }
      b.addEventListener('click', function () {
        for (var i = 0; i < ctx.openers.length; i++) {
          if (ctx.openers[i].section === 0) { ctx.openers[i].set(pair[1], true); }
        }
      });
    });
    if (unknown) { add(bar, el('p', 'note tree-note', OPEN_UNKNOWN)); }
    if (filtered) { add(bar, el('p', 'note tree-note', FILTER_HINT)); }
    return bar;
  }

  function bodyBrowse(route) {
    var q = question('browse');
    buildFilters(q, route, recordIds);
    if (!recordIds.length) { add(dom.list, emptyLine(q.empty)); return 0; }
    var show = deliveryUnavailable() ? '' : route.show;
    var group = route.group;
    var match = function (id) {
      return show === '' || (show === 'open') === isOpen(id);
    };
    var keys = activeFilters(route, q);
    var ctx = { kids: null, match: match, shown: null, auto: show !== '', counts: !deliveryUnavailable(),
      openers: [], tally: new Map() };
    add(dom.tools, browseBar(show, group, ctx, keys.length > 0));
    var matching = recordIds.filter(function (id) { return passes(id, route) && match(id); });
    if (keys.length) {
      if (!matching.length) { add(dom.list, filteredEmpty(route, keys, show)); return 0; }
      add(dom.list, rows(matching.sort(byName)));
      return matching.length;
    }
    if (!matching.length) {
      add(dom.list, emptyLine(show === 'open' ? 'No intent is an open item.' : 'No intent is done.'));
      return 0;
    }
    var tree = group === 'capability' ? capabilityTree() : hierarchyTree();
    ctx.kids = tree.kids;
    // A row is shown when it matches or a row beneath it in the grouping is shown.
    var memo = new Map();
    ctx.shown = function (id) {
      var known = memo.get(id);
      if (known === undefined) {
        memo.set(id, false);
        known = match(id) || (ctx.kids.get(id) || []).some(ctx.shown);
        memo.set(id, known);
      }
      return known;
    };
    var sectionsShown = 0;
    [tree.main, tree.rest].forEach(function (pair, index) {
      var ids = pair[1].filter(ctx.shown);
      if (!ids.length) { return; }
      var wrap = index === 1 ? add(dom.list, el('details', 'loose')) : dom.list;
      add(wrap, el(index === 1 ? 'summary' : 'h3', 'group-head tree-head', pair[0]));
      var ul = add(wrap, el('ul', 'rows tree'));
      ids.forEach(function (id) { add(ul, treeRow(id, ctx, sectionsShown)); });
      sectionsShown += 1;
    });
    return matching.length;
  }
