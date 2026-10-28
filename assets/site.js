/* studiobega.be — rideau d'accueil, vues Images / Liste, fiches, lightbox. Aucune dépendance. */
(function () {
  'use strict';
  var hero = document.getElementById('hero'), site = document.getElementById('site'), lb = document.getElementById('lb');
  /* le surligneur : chaque clé se surligne quand elle arrive à l'écran */
  var mks = document.querySelectorAll('.mk');
  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (es) {
      es.forEach(function (x) { if (x.isIntersecting) { x.target.classList.add('in'); io.unobserve(x.target); } });
    }, { rootMargin: '0px 0px -12% 0px' });
    Array.prototype.forEach.call(mks, function (m) { io.observe(m); });
  } else Array.prototype.forEach.call(mks, function (m) { m.classList.add('in'); });
  if (!site) return;
  var phone = function () { return window.innerWidth <= 640; };
  var top = function () { try { window.scrollTo(0, 0); document.documentElement.scrollTop = 0; document.body.scrollTop = 0; } catch (e) {} };
  var seen = false; try { seen = sessionStorage.getItem('bega_in') === '1'; } catch (e) {}
  var hash = location.hash ? location.hash.slice(1) : '';

  /* ---- rideau ---- */
  function enter(instant) {
    if (!hero || hero.classList.contains('up')) return;
    try { sessionStorage.setItem('bega_in', '1'); } catch (e) {}
    hero.classList.add('up');
    site.classList.remove('locked');
    if (instant) return;
    site.classList.add('hold'); top();
    setTimeout(function () { site.classList.remove('hold'); top(); }, 900);
  }
  function home() {
    try { sessionStorage.removeItem('bega_in'); } catch (e) {}
    closeGrid(); closeAll(); syncFx(); history.replaceState(null, '', location.pathname);
    hero.classList.remove('up'); site.classList.add('locked'); top();
  }
  if (hero) {
    if (hash || seen) enter(true); else site.classList.add('locked');
    document.getElementById('enter').addEventListener('click', function () { enter(); });
    hero.addEventListener('wheel', function (ev) { if (ev.deltaY > 8) enter(); }, { passive: true });
    var ty = 0;
    hero.addEventListener('touchstart', function (ev) { ty = ev.touches[0].clientY; }, { passive: true });
    hero.addEventListener('touchmove', function (ev) { if (ty - ev.touches[0].clientY > 24) enter(); }, { passive: true });
    var hb = document.getElementById('home'); if (hb) hb.addEventListener('click', home);
  }

  /* ---- fiches ---- */
  var rows = Array.prototype.slice.call(document.querySelectorAll('.row'));
  function closeAll() {
    rows.forEach(function (r) { r.classList.remove('open'); r.querySelector('.line').setAttribute('aria-expanded', 'false'); });
  }
  function open(r, noScroll) {
    closeAll();
    r.classList.add('open'); r.querySelector('.line').setAttribute('aria-expanded', 'true');
    setHash(r.id); syncFx();
    if (phone() && !noScroll) {
      site.classList.add('nt');
      requestAnimationFrame(function () { requestAnimationFrame(function () {
        var nav = site.querySelector('.nav'); var nh = nav ? nav.getBoundingClientRect().height : 56;
        var y = r.getBoundingClientRect().top + window.pageYOffset - nh - 12;
        window.scrollTo(0, Math.max(0, y));
        setTimeout(function () { site.classList.remove('nt'); }, 80);
      }); });
    }
  }
  rows.forEach(function (r) {
    r.querySelector('.line').addEventListener('click', function () {
      if (r.classList.contains('open')) shut(); else open(r);
    });
    r.querySelector('.panel').addEventListener('click', function (ev) {
      if (ev.target.hasAttribute('data-zoom')) { ev.stopPropagation(); zoom(ev.target.getAttribute('data-zoom')); return; }
      if (ev.target.closest('a')) return;
      shut();
    });
  });
  /* ---- Images / Liste ---- */
  var view = 'img'; try { view = sessionStorage.getItem('bega_view') || 'img'; } catch (e) {}
  var vbtns = Array.prototype.slice.call(document.querySelectorAll('.views button'));
  function setView(v) {
    view = v; try { sessionStorage.setItem('bega_view', v); } catch (e) {}
    site.classList.toggle('v-img', v === 'img'); site.classList.toggle('v-list', v === 'list');
    vbtns.forEach(function (b) { b.setAttribute('aria-pressed', b.getAttribute('data-v') === v ? 'true' : 'false'); });
  }
  vbtns.forEach(function (b) { b.addEventListener('click', function () { setView(b.getAttribute('data-v')); }); });
  setView(view);

  /* ---- fiche dépliée dans la grille ---- */
  var gp = null, fx = document.getElementById('fx'), pushed = false;
  try { history.scrollRestoration = 'manual'; } catch (e) {}
  function navH() { var n = site.querySelector('.nav'); return n ? n.getBoundingClientRect().height : 56; }
  function closeGrid() {
    if (!gp) return false;
    var c = gp._card; gp.parentNode.classList.remove('has-open'); c.classList.remove('on'); gp.remove(); gp = null;
    return c;
  }
  function anyOpen() { return !!gp || rows.some(function (r) { return r.classList.contains('open'); }); }
  function syncFx() { if (fx) fx.classList.toggle('on', anyOpen()); }
  function openGrid(id, noScroll) {
    var c = document.querySelector('.card[data-open="' + id + '"]'), r = document.getElementById(id);
    if (!c || !r) return;
    closeGrid();
    var grid = c.parentNode, cards = Array.prototype.slice.call(grid.querySelectorAll('.card')), first = c;
    for (var i = cards.length - 1; i >= 0; i--) if (Math.abs(cards[i].offsetTop - c.offsetTop) < 4) first = cards[i];
    var line = r.querySelector('.line');
    var meta = Array.prototype.map.call(line.querySelectorAll('.pl,.tp,.yr,.st'), function (x) { return x.textContent; }).filter(Boolean).join(' · ');
    gp = document.createElement('div'); gp.className = 'gpanel'; gp._card = c;
    var h = document.createElement('div'); h.className = 'gp-h';
    var t = document.createElement('div');
    var nm = document.createElement('span'); nm.className = 'nm'; nm.textContent = line.querySelector('.nm').textContent;
    var cm = document.createElement('span'); cm.className = 'cm'; cm.textContent = meta;
    t.appendChild(nm); t.appendChild(cm); h.appendChild(t);
    var x = document.createElement('button'); x.type = 'button'; x.className = 'gp-x'; x.textContent = 'Fermer'; h.appendChild(x);
    gp.appendChild(h); gp.appendChild(r.querySelector('.panel').cloneNode(true));
    first.before(gp); grid.classList.add('has-open'); c.classList.add('on');
    x.addEventListener('click', function () { shut(); });
    gp.addEventListener('click', function (ev) {
      var z = ev.target.closest('[data-zoom]'); if (z) { zoom(z.getAttribute('data-zoom')); return; }
      if (ev.target.closest('a')) return;
      shut();
    });
    if (!noScroll) {
      var y = gp.getBoundingClientRect().top + window.pageYOffset - navH() - 24;
      window.scrollTo({ top: Math.max(0, y), behavior: 'instant' });
    }
    syncFx();
  }
  function setHash(id) {
    if (id) { if (pushed) history.replaceState({ f: 1 }, '', '#' + id); else { history.pushState({ f: 1 }, '', '#' + id); pushed = true; } }
    else { if (pushed) { pushed = false; history.back(); } else history.replaceState(null, '', location.pathname); }
  }
  /* ferme ce qui est ouvert (grille ou liste) et revient à la vignette / ligne */
  function shut(fromPop) {
    var back = closeGrid(), openRow = rows.filter(function (r) { return r.classList.contains('open'); })[0];
    if (openRow) { closeAll(); back = back || openRow; }
    if (!fromPop) setHash(null);
    syncFx();
    if (back && back.getBoundingClientRect().top < navH()) window.scrollTo(0, back.getBoundingClientRect().top + window.pageYOffset - navH() - 16);
  }
  Array.prototype.forEach.call(document.querySelectorAll('.card'), function (c) {
    c.addEventListener('click', function (ev) {
      ev.preventDefault();
      if (c.classList.contains('on')) { shut(); return; }
      openGrid(c.getAttribute('data-open')); setHash(c.getAttribute('data-open'));
    });
  });
  if (fx) fx.addEventListener('click', function () { shut(); });
  window.addEventListener('popstate', function () { pushed = false; if (anyOpen() && !location.hash) shut(true); });
  var rw = window.innerWidth;
  window.addEventListener('resize', function () {
    if (!gp || window.innerWidth === rw) return; rw = window.innerWidth;
    openGrid(gp._card.getAttribute('data-open'), true);
  });
  /* la fiche se referme d'elle-même quand on la dépasse en scrollant */
  var ticking = false;
  window.addEventListener('scroll', function () {
    if (!gp || ticking) return; ticking = true;
    requestAnimationFrame(function () {
      ticking = false; if (!gp) return;
      var b = gp.getBoundingClientRect();
      if (b.bottom < navH() - 40) {
        var g = gp.parentNode, before = g.getBoundingClientRect().bottom;
        closeGrid(); setHash(null); syncFx();
        window.scrollTo(0, window.pageYOffset + (g.getBoundingClientRect().bottom - before));
      } else if (b.top > window.innerHeight + 40) { closeGrid(); setHash(null); syncFx(); }
    });
  }, { passive: true });

  function openHash() {
    var h = location.hash ? location.hash.slice(1) : '', r0 = h && document.getElementById(h);
    if (!(r0 && r0.classList.contains('row'))) return;
    enter(true);
    if (view === 'img' && document.querySelector('.card[data-open="' + h + '"]')) { openGrid(h); return; }
    setView('list'); open(r0, true); syncFx(); setTimeout(function () { r0.scrollIntoView({ block: 'start' }); }, 50);
  }
  openHash();
  window.addEventListener('hashchange', openHash);

  /* ---- lightbox ---- */
  function zoom(src) { if (!lb) return; lb.querySelector('img').src = src; lb.classList.add('on'); lb.setAttribute('aria-hidden', 'false'); }
  function unzoom() { if (!lb) return; lb.classList.remove('on'); lb.setAttribute('aria-hidden', 'true'); }
  if (lb) lb.addEventListener('click', unzoom);
  document.addEventListener('keydown', function (ev) {
    if (ev.key !== 'Escape') return;
    if (lb && lb.classList.contains('on')) { unzoom(); return; }
    if (anyOpen()) shut();
  });
})();
