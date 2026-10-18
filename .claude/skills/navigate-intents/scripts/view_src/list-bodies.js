  // ------------------------------------------------------------- list bodies
  function unavailableStatement() {
    var p = el('p', 'notice');
    text(p, 'Can\'t list open work: delivery mapping incomplete. Reason: ');
    add(p, el('span', 'value', isStr(data.outstanding.reason) ? data.outstanding.reason : 'unknown'));
    if (data.outstanding.limit !== undefined && data.outstanding.limit !== null) {
      text(p, ', limit ');
      add(p, el('span', 'value', String(data.outstanding.limit)));
    }
    text(p, '.');
    return p;
  }
  function emptyLine(message) { return el('p', 'empty', message); }

  function grouped(ids) {
    var frag = document.createDocumentFragment();
    TYPE_GROUPS.forEach(function (pair) {
      var these = ids.filter(function (id) { return typeOf(id) === pair[0]; }).sort(byName);
      if (!these.length) { return; }
      add(frag, el('h3', 'group-head', pair[1]));
      add(frag, rows(these));
    });
    return frag;
  }

  function filterOptions(key, ids) {
    var values = new Set();
    ids.forEach(function (id) {
      var r = rec(id);
      if (key === 'type') { values.add(typeOf(id)); }
      if (key === 'level' && r) { values.add(r.level || 'unrecorded'); }
      if (key === 'kind' && r && r.kind) { values.add(r.kind); }
      if (key === 'status' && r) { values.add(r.status || ''); }
    });
    return Array.from(values).sort(cmp);
  }
  function passes(id, route) {
    var r = rec(id);
    if (route.type && typeOf(id) !== route.type) { return false; }
    if (route.level && (!r || (r.level || 'unrecorded').toLowerCase() !== route.level.toLowerCase())) {
      return false;
    }
    if (route.kind && (!r || (r.kind || '').toLowerCase() !== route.kind.toLowerCase())) { return false; }
    if (route.status && (!r || (r.status || '') !== route.status)) { return false; }
    return true;
  }
  function activeFilters(route, q) {
    return (q.filters || []).filter(function (k) { return route[k] !== ''; });
  }
  function describeFilters(route, keys) {
    return keys.map(function (k) { return FILTER_LABELS[k][0].toLowerCase() + ' "' + route[k] + '"'; })
      .join(', ');
  }
  // The control is removed by the render its click causes, so focus is placed on a target that
  // stays: the list title (it takes focus), or the search field.
  function clearControl(label, over, focusTarget) {
    var b = button('action', label);
    b.addEventListener('click', function () {
      replaceRoute(over);
      focusTarget().focus();
    });
    return b;
  }
  function filteredEmpty(route, keys, show) {
    var box = el('div', 'empty');
    add(box, el('p', '', 'Nothing matches ' + describeFilters(route, keys) +
      (show ? ' among ' + show + ' items' : '') + '.'));
    var over = {};
    FILTER_KEYS.forEach(function (k) { over[k] = ''; });
    add(box, clearControl('Clear filters', over, function () { return dom.listTitle; }));
    return box;
  }

  function buildFilters(q, route, pool) {
    clear(dom.filters);
    var keys = q.filters || [];
    dom.filters.hidden = keys.length === 0 || route.search !== '';
    keys.forEach(function (key) {
      var field = add(dom.filters, el('div', 'field'));
      var id = 'filter-' + key;
      var label = add(field, el('label', '', FILTER_LABELS[key][0]));
      label.setAttribute('for', id);
      var select = add(field, el('select', 'control'));
      select.setAttribute('id', id);
      var first = add(select, el('option', '', FILTER_LABELS[key][1]));
      first.setAttribute('value', '');
      filterOptions(key, pool).forEach(function (v) {
        var o = add(select, el('option', '', key === 'type' ? (own(TYPE_NAMES, v) || v) : v));
        o.setAttribute('value', v);
      });
      select.value = route[key];
      select.addEventListener('change', function () {
        var over = {};
        over[key] = select.value;
        replaceRoute(over);
      });
    });
  }

  function brokenRow(entry) {
    var li = el('li', 'row');
    var context;
    if (entry.edge) {
      context = (isStr(entry.edge.field) ? entry.edge.field : 'Pointer') + ': ' +
        (own(STATE_HELP, entry.edge.state) !== undefined ? entry.edge.state : 'refused');
    } else if (entry.dep || entry.cycle) {
      var depState = entry.cycle ? 'cycle' : entry.dep.state;
      context = 'Depends on: ' + (own(STATE_HELP, depState) !== undefined ? depState : 'refused');
    } else {
      context = el('span');
      text(context, 'Delivery diagnostic: ');
      add(context, el('span', 'value', isStr(entry.diag.code) ? entry.diag.code : 'unknown'));
    }
    add(li, rowLink(entry.holder, markEl('broken', 'Broken'), context));
    return li;
  }

  // Each body builder fills dom.list and returns the count it shows.
  function bodyNext() {
    if (deliveryUnavailable()) { add(dom.list, unavailableStatement()); return null; }
    var ids = startableIds();
    if (!ids.length) { add(dom.list, emptyLine(question('next').empty)); return 0; }
    add(dom.list, rows(ids));
    return ids.length;
  }
  function bodyCapabilities() {
    if (deliveryUnavailable()) { add(dom.list, unavailableStatement()); return null; }
    var ids = capabilityIds();
    if (!ids.length) { add(dom.list, emptyLine(question('capabilities').empty)); return 0; }
    var ul = add(dom.list, el('ul', 'rows'));
    ids.forEach(function (id) {
      var li = add(ul, el('li', 'row'));
      add(li, rowLink(id, stateMark(id), contextText(id) + ' \u00B7 ' + openCount(id) + ' open'));
    });
    return ids.length;
  }
  function bodyNoParent(route) {
    if (deliveryUnavailable()) { add(dom.list, unavailableStatement()); return null; }
    var base = noParentIds();
    buildFilters(question('noparent'), route, base);
    if (!base.length) { add(dom.list, emptyLine(question('noparent').empty)); return 0; }
    var ids = base.filter(function (id) { return passes(id, route); });
    var keys = activeFilters(route, question('noparent'));
    if (!ids.length) { add(dom.list, filteredEmpty(route, keys)); return 0; }
    add(dom.list, grouped(ids));
    return ids.length;
  }
  function bodyBroken() {
    var entries = brokenEntries();
    if (deliveryUnavailable()) {
      add(dom.list, el('p', 'notice', 'Delivery diagnostics were unavailable: delivery mapping incomplete. Broken pointers are listed below.'));
    }
    if (!entries.length) { add(dom.list, emptyLine(question('broken').empty)); return 0; }
    var ul = add(dom.list, el('ul', 'rows'));
    entries.forEach(function (entry) { add(ul, brokenRow(entry)); });
    return entries.length;
  }
  function bodySearch(route) {
    var want = route.search.toLowerCase();
    var ids = searchIndex().filter(function (entry) {
      return entry.slug.indexOf(want) !== -1 || entry.heading.indexOf(want) !== -1;
    }).map(function (entry) { return entry.id; });
    if (!ids.length) {
      var box = add(dom.list, el('div', 'empty'));
      add(box, el('p', '', 'Nothing matches the search "' + route.search + '".'));
      add(box, clearControl('Clear search', { search: '' }, function () { return dom.search; }));
      return 0;
    }
    add(dom.list, rows(ids));
    return ids.length;
  }
  // Every node once, already in name order, with its lowercased slug and heading.
  var searchEntries = null;
  function searchIndex() {
    if (searchEntries === null) {
      searchEntries = data.nodes.map(function (n) {
        return { id: n.id, slug: slugOf(n).toLowerCase(),
          heading: (isStr(n.heading) ? n.heading : '').toLowerCase() };
      }).sort(function (a, b) { return byName(a.id, b.id); });
    }
    return searchEntries;
  }
  var BODIES = { next: bodyNext, capabilities: bodyCapabilities, noparent: bodyNoParent,
    broken: bodyBroken, browse: bodyBrowse, roadmap: bodyRoadmap };

  function emptyCorpus() { return data.nodes.length === 0; }

  function renderList(route, announce) {
    var q = question(route.q);
    listGeneration += 1;
    clear(dom.list);
    clear(dom.tools);
    clear(dom.filters);
    dom.filters.hidden = true;
    var count;
    if (route.search !== '') {
      dom.listQuestion.textContent = '';
      dom.listTitle.textContent = escapeDisplay('Search results for "' + route.search + '"');
      dom.listLead.textContent = 'Intents, briefs and specs whose name or id contains the search.';
      dom.listSort.textContent = 'By name';
      count = bodySearch(route);
    } else if (emptyCorpus()) {
      dom.listQuestion.textContent = q.name;
      dom.listTitle.textContent = q.title;
      dom.listLead.textContent = q.key === 'next' ? q.lead : '';
      dom.listSort.textContent = q.sort;
      var box = add(dom.list, el('div', 'empty'));
      add(box, el('p', '', 'No intents, briefs or specs found under this root.'));
      add(box, el('p', 'note', 'The export reads docs/product/intents, docs/product/briefs and docs/specs.'));
      count = 0;
    } else {
      var summary = q.key === 'browse' ? browseSummary(route) : q;
      dom.listQuestion.textContent = q.name;
      dom.listTitle.textContent = q.title;
      dom.listLead.textContent = summary.lead;
      dom.listSort.textContent = summary.sort;
      count = BODIES[q.key](route);
    }
    shownCount = count;
    var noun = route.search !== '' ? ['result', 'results'] : q.noun;
    dom.listCount.textContent = count === null ? 'Count unavailable' : plural(count, noun);
    if (announce) {
      dom.live.textContent = escapeDisplay(dom.listTitle.textContent + ', ' + dom.listCount.textContent);
    }
    performance.mark('list-updated');
  }

  function markSelected(route) {
    var links = dom.list.querySelectorAll('a.row-link');
    for (var i = 0; i < links.length; i++) {
      if (links[i].getAttribute('data-node') === route.node) {
        links[i].setAttribute('aria-current', 'true');
      } else {
        links[i].removeAttribute('aria-current');
      }
    }
  }

