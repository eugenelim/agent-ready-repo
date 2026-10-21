  // ------------------------------------------------------------ page chrome
  // The time to the minute in UTC; any other form is shown as written.
  function generatedText(value) {
    if (!isStr(value) || value === '') { return 'at an unknown time'; }
    var m = /^(\d{4}-\d{2}-\d{2})T(\d{2}:\d{2})(?::\d{2}(?:\.\d+)?)?(?:Z|[+-]00:00)$/.exec(value);
    return m === null ? value : m[1] + ' ' + m[2] + ' UTC';
  }
  function sumValues(obj) {
    var total = 0;
    if (!isObj(obj)) { return total; }
    Object.keys(obj).forEach(function (k) { if (typeof obj[k] === 'number') { total += obj[k]; } });
    return total;
  }

  function renderMeta() {
    var s = data.summary;
    var scoped = isStr(data.scope.from);
    dom.meta.textContent = escapeDisplay('Read-only snapshot generated ' +
      generatedText(data.provenance.generated_at) + '. ' + sumValues(s.intents_by_level) +
      ' intents, ' + s.briefs + ' briefs and ' + s.specs + ' specs' +
      (scoped ? ' in the whole corpus' : '') +
      '. Record text is shown as plain text and never run.');
    if (scoped) {
      dom.banner.hidden = false;
      clear(dom.banner);
      text(dom.banner, 'Scoped export: the questions cover ');
      add(dom.banner, nodeRef(data.scope.from, 'node-link'));
      text(dom.banner, ' and everything beneath it. The totals above cover the whole corpus.');
    }
  }

  // The links are built once, so a link that has focus keeps it across routes; a route only
  // moves aria-current.  The counts come from the data, which never changes, so they are set here.
  function buildNav() {
    RAIL_GROUPS.forEach(function (group) {
      var head = add(dom.questions, el('h2', 'rail-group', group.label));
      head.setAttribute('id', 'rail-' + group.key);
      var ul = add(dom.questions, el('ul', 'question-list'));
      ul.setAttribute('aria-labelledby', head.id);
      group.questions.forEach(function (key) {
        var q = question(key);
        var li = add(ul, el('li', 'question'));
        var a = add(li, el('a', 'question-link'));
        a.setAttribute('href', questionHash(q.key));
        a.setAttribute('data-q', q.key);
        add(a, el('span', 'q-name', q.label));
        if (q.key !== 'browse') {
          var count = emptyCorpus() ? 0 : questionCount(q.key);
          add(a, el('span', 'q-count', count === null ? 'unknown' : String(count)));
        }
        // The full question is the link's description; it sits beside the link so the name stays short.
        var why = add(li, el('span', 'visually-hidden', q.name));
        why.setAttribute('id', 'q-desc-' + q.key);
        a.setAttribute('aria-describedby', why.id);
      });
    });
  }
  function markNav(route) {
    var links = dom.questions.querySelectorAll('a.question-link');
    for (var i = 0; i < links.length; i++) {
      links[i].setAttribute('href', questionHash(links[i].getAttribute('data-q'), route.owner));
      if (links[i].getAttribute('data-q') === route.q) {
        links[i].setAttribute('aria-current', 'page');
      } else {
        links[i].removeAttribute('aria-current');
      }
    }
  }

  function renderKey() {
    var dl = add(dom.keyBody, el('dl', 'key-list'));
    function row(term, def, id) {
      var r = add(dl, el('div', 'fact'));
      var dt = add(r, el('dt', 'fact-name'));
      add(dt, term);
      var dd = add(r, el('dd', 'fact-value', def));
      if (id) { dd.setAttribute('id', id); }
    }
    MARK_ORDER.forEach(function (key) {
      var words = { active: 'Implementing, Executing', approved: 'Approved, Accepted, Ready',
        draft: 'Draft and other open states', broken: 'Broken', stale: 'Stale', done: 'Closed states' };
      row(markEl(key, words[key]), MARKS[key].help);
    });
    if (readinessChecked()) {
      READINESS_KEY.forEach(function (t) { row(markEl(t[0], t[1]), t[2]); });
      row(el('span', 'label-group', 'Workspace finding'), FINDING_HELP);
    }
    GROUP_ORDER.forEach(function (key) {
      row(el('span', 'label-group', own(GROUP_LABELS, key)), own(GROUP_HELP, key));
    });
    [['state', STATE_HELP], ['trust', TRUST_HELP], ['form', FORM_HELP]].forEach(function (pair) {
      Object.keys(pair[1]).forEach(function (key) {
        row(el('span', 'chip label-' + pair[0], key), own(pair[1], key), helpId(pair[0], key));
      });
    });
    row(el('span', 'dep-word', 'waits for'), 'The first intent\'s Depends on: header names the second. ' +
      'The view does not decide whether either can start.');
  }

  function handleRoute() {
    var next = parseRoute();
    var prev = current;
    current = next;
    var listChanged = prev === null || ['q', 'search', 'show', 'group', 'owner'].concat(FILTER_KEYS).some(function (k) {
      return prev[k] !== next[k];
    });
    var nodeChanged = prev === null || prev.node !== next.node;
    if (dom.search.value !== next.search) { dom.search.value = next.search; }
    markNav(next);
    syncOwnerControl(next);
    // A filter select is rebuilt with the list; keep the reader on the one they were using.
    var held = document.activeElement;
    var heldFilter = held && held.closest && held.closest('#filters, #owner-pick') ? held.id : '';
    var heldChoice = held && held.closest && held.closest('#list, #tools') ? held.getAttribute('data-ctl') || '' : '';
    if (listChanged) {
      renderList(next, prev !== null);
      if (heldFilter !== '') {
        var again = byIdEl(heldFilter);
        if (again) { again.focus(); }
      }
      if (heldChoice !== '') {
        var choice = document.querySelector('#tools [data-ctl="' + heldChoice + '"]');
        if (choice) { choice.focus(); }
      }
    } else if (nodeChanged) {
      markSelected(next);
    }
    if (nodeChanged || listChanged) {
      renderDetail(next);
    } else if (prev !== null && dom.depBody && (prev.dir !== next.dir || prev.steps !== next.steps)) {
      // Only the part's own result changes, so the control in use keeps focus and the zone its scroll.
      fillDependencies(next.node, next);
    }
    if (prev !== null && nodeChanged && !listChanged && next.node !== '' && nodes.has(next.node)) {
      var fromDetail = followedDetailLink;
      followedDetailLink = false;
      if (wide.matches && !fromDetail) {
        dom.live.textContent = escapeDisplay('Showing ' + displayName(next.node));
      } else {
        dom.detailHeading.focus();
      }
    } else if (prev !== null && prev.node !== '' && next.node === '' && !wide.matches) {
      // The detail that held focus is gone (browser Back, for one): return to the picked row.
      var active = document.activeElement;
      // Focus inside the detail is about to be lost: the zone is hidden by this very render.
      if (!active || active === document.body || (active.closest && active.closest('.detail'))) {
        window.scrollTo(0, listScroll);
        (rowLinkFor(prev.node) || dom.listTitle).focus();
      }
    }
  }

  function showDamaged() {
    var main = byIdEl('main');
    var alertBox = el('div', 'alert', 'This file is damaged and cannot be shown. Export it again.');
    alertBox.setAttribute('role', 'alert');
    main.replaceChildren(alertBox);
    byIdEl('app').hidden = false;
    byIdEl('questions-nav').hidden = true;
    var field = byIdEl('search').parentNode;
    field.parentNode.removeChild(field);
    var pick = byIdEl('owner-pick');
    pick.parentNode.removeChild(pick);
  }

  function start() {
    var block = byIdEl('intent-data');
    try {
      data = JSON.parse(block.textContent);
    } catch (err) {
      data = null;
    }
    if (!validData(data)) { showDamaged(); return; }
    try {
      dom = {
        live: byIdEl('live'), meta: byIdEl('meta'), banner: byIdEl('scope-banner'),
        search: byIdEl('search'), questions: byIdEl('question-list'), main: byIdEl('main'),
        listQuestion: byIdEl('list-question'), listTitle: byIdEl('list-title'), listLead: byIdEl('list-lead'),
        listCount: byIdEl('list-count'), listSort: byIdEl('list-sort'),
        tools: byIdEl('tools'), filters: byIdEl('filters'), keyBody: byIdEl('key-body'), list: byIdEl('list'),
        detailHeading: byIdEl('detail-heading'), detailBody: byIdEl('detail-body'),
        skip: byIdEl('skip-details'), owner: byIdEl('owner-pick')
      };
      wide = window.matchMedia('(min-width: 40rem)');
      buildIndexes();
      renderMeta();
      renderKey();
      buildNav();
      buildOwnerControl();
      dom.search.addEventListener('input', function () {
        // Below 40rem a picked item hides the list, so a search drops the pick to show its results.
        var over = { search: dom.search.value };
        if (!wide.matches && dom.search.value !== '') { over.node = ''; }
        replaceRoute(over);
      });
      dom.search.addEventListener('keydown', function (ev) {
        if (ev.key === 'Escape' && dom.search.value !== '') {
          ev.preventDefault();
          replaceRoute({ search: '' });
        }
      });
      dom.skip.addEventListener('click', function () { dom.detailHeading.focus(); });
      dom.detailBody.addEventListener('click', function (ev) {
        var link = ev.target.closest ? ev.target.closest('a.node-link') : null;
        // A link to the item already shown changes no route, so it must not mark the next one.
        if (link && link.getAttribute('href') !== location.hash) { followedDetailLink = true; }
      });
      dom.list.addEventListener('click', function (ev) {
        var link = ev.target.closest ? ev.target.closest('a.row-link') : null;
        if (link) { followedDetailLink = false; listScroll = window.scrollY; }
      });
      byIdEl('app').hidden = false;
      handleRoute();
      window.addEventListener('hashchange', handleRoute);
      performance.mark('view-ready');
    } catch (err) {
      showDamaged();
      // The alert is the reader's message; the error stays visible to whoever debugs the page.
      console.error('Intent view could not render:', err);
    }
  }

  start();
