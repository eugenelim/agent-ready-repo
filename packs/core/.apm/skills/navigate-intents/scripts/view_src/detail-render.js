  var STAGE_NOUNS = [['Implementing spec', 'Implementing specs'], ['Approved spec', 'Approved specs'],
    ['Executing brief', 'Executing briefs'], ['Ready brief', 'Ready briefs'],
    ['Accepted intent with nothing beneath', 'Accepted intents with nothing beneath']];
  // Counts with their nouns, leaving out any that are zero.
  function nonZero(pairs) {
    return pairs.filter(function (p) { return p[0] > 0; })
      .map(function (p) { return plural(p[0], p[1]); }).join(', ');
  }
  // A plain count of what the list holds, from fixed words and numbers only.
  function listSummary(route) {
    if (shownCount === null || emptyCorpus()) { return ''; }
    if (route.search === '' && route.q === 'next') {
      var per = STAGES.map(function () { return 0; });
      startableIds().forEach(function (id) { per[stageOf(id)] += 1; });
      var parts = [];
      per.forEach(function (n, i) { if (n > 0) { parts.push(plural(n, STAGE_NOUNS[i])); } });
      return parts.length ? 'In this list: ' + parts.join(', ') + '.' : '';
    }
    if (shownCount === 0 || route.search !== '') { return ''; }
    if (route.q === 'broken') {
      var entries = brokenEntries();
      var pointers = entries.filter(function (b) { return b.edge || b.dep || b.cycle; }).length;
      if (deliveryUnavailable()) {
        return 'In this list: ' + plural(pointers, ['broken pointer', 'broken pointers']) +
          '. Delivery diagnostics were unavailable.';
      }
      return 'In this list: ' + nonZero([[pointers, ['broken pointer', 'broken pointers']],
        [entries.length - pointers, ['delivery diagnostic', 'delivery diagnostics']]]) + '.';
    }
    if (route.q === 'noparent') {
      return 'In this list: ' + nonZero(TYPE_GROUPS.map(function (pair) {
        return [noParentIds().filter(function (id) { return typeOf(id) === pair[0]; }).length,
          [pair[1].toLowerCase().replace(/s$/, ''), pair[1].toLowerCase()]];
      })) + '.';
    }
    if (route.q === 'capabilities') {
      var open = capabilityIds().reduce(function (sum, id) { return sum + openCount(id); }, 0);
      return 'In this list: ' + plural(open, ['open item', 'open items']) +
        ' in total across these capabilities; an item under two capabilities counts twice.';
    }
    return '';
  }

  function renderDetail(route) {
    clear(dom.detailBody);
    dom.depBody = null;
    var id = route.node;
    dom.main.toggleAttribute('data-picked', id !== '' && nodes.has(id));
    if (!id) {
      dom.detailHeading.textContent = 'Details';
      add(dom.detailBody, el('p', 'note', 'Pick an item to see its next step.'));
      var summary = listSummary(route);
      if (summary !== '') { add(dom.detailBody, el('p', 'list-summary', summary)); }
      return;
    }
    if (!nodes.has(id)) {
      dom.detailHeading.textContent = 'Details';
      add(dom.detailBody, el('p', 'note', 'That item is not in this snapshot.'));
      return;
    }
    dom.detailHeading.textContent = escapeDisplay(displayName(id));
    var back = add(dom.detailBody, button('action back-link', 'Back to list'));
    back.addEventListener('click', function () { backToList(id); });
    add(dom.detailBody, stateLine(id));

    add(part('Next step'), el('p', 'next-step', nextStep(id)));

    var openSec = part('Open beneath');
    var under = deliveryUnavailable() ? null : (beneath.get(id) || []);
    if (under === null) {
      add(openSec, el('p', 'empty', 'Open work unknown: delivery mapping incomplete.'));
    } else if (!under.length) {
      add(openSec, el('p', 'empty', 'Nothing open beneath.'));
    } else {
      TYPE_GROUPS.forEach(function (pair) {
        var these = under.filter(function (u) { return typeOf(u) === pair[0]; }).sort(byName);
        if (!these.length) { return; }
        add(openSec, el('h4', 'group-label', pair[1]));
        var ul = add(openSec, el('ul', 'plain'));
        these.forEach(function (u) {
          var li = add(ul, el('li', 'beneath-row'));
          add(li, nodeLink(u, 'node-link'));
          add(li, stateMark(u));
        });
      });
    }

    var brokenSec = part('What is broken');
    var broken = brokenOf(id);
    if (deliveryUnavailable()) { add(brokenSec, el('p', 'note', 'Delivery diagnostics were unavailable.')); }
    if (!broken.length) {
      add(brokenSec, el('p', 'empty', 'Nothing broken here.'));
    } else {
      var bl = add(brokenSec, el('ul', 'plain'));
      broken.forEach(function (b) {
        var li = add(bl, el('li', 'edge'));
        if (b.edge) {
          add(li, edgeItem(b.edge, false).firstChild);
          if (own(STATE_HELP, b.edge.state) !== undefined) {
            add(li, el('p', 'meaning', own(STATE_HELP, b.edge.state)));
          }
        } else if (b.dep || b.cycle) {
          dependencyBroken(li, id, b);
        } else {
          var line = add(li, el('div', 'edge-line'));
          add(line, el('span', 'field', 'Delivery diagnostic'));
          add(line, el('span', 'value', isStr(b.diag.code) ? b.diag.code : 'unknown'));
          add(li, el('p', 'meaning', describe(b.diag)));
        }
      });
    }

    var sits = part('Where it sits');
    var lists = ancestorLists(id);
    if (!lists.length) {
      add(sits, el('p', 'empty', 'No parent.'));
    } else {
      lists.forEach(function (list, n) {
        add(sits, el('p', 'trail-label', lists.length > 1 ?
          'Path ' + (n + 1) + ' of ' + lists.length + ', from the top:' : 'From the top:'));
        var trail = add(sits, el('ol', 'trail'));
        list.slice().reverse().forEach(function (a) {
          if (!isObj(a) || !isStr(a.id)) { return; }
          var step = add(trail, el('li', 'trail-step'));
          add(step, nodeRef(a.id, 'node-link'));
          if (nodes.has(a.id)) { text(step, ' '); add(step, stateMark(a.id)); }
        });
      });
    }

    if (typeOf(id) === 'intent') { dependenciesPart(id, route); }

    add(part('Open the file'), sourceBlock(id));
    recordDetails(id);
  }

  function rowLinkFor(id) {
    var links = dom.list.querySelectorAll('a.row-link');
    for (var i = 0; i < links.length; i++) {
      if (links[i].getAttribute('data-node') === id) { return links[i]; }
    }
    return null;
  }

  function backToList(id) {
    location.hash = hashFor({ node: '' });
    // The list is hidden while a row is picked; show it now so the row can take focus.
    dom.main.removeAttribute('data-picked');
    window.scrollTo(0, listScroll);
    var target = rowLinkFor(id);
    (target || dom.listTitle).focus();
  }

