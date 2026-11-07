/* studiobega.be — accueil, fiches dans la grille, agrandissement des photos. Aucune dépendance. */
(function () {
  'use strict';
  var B = document.documentElement.getAttribute('data-base') || '';   // aperçu : /apercu ; site : rien

  /* ---- menu téléphone : trois barres → menu plein écran ---- */
  var mnav = document.getElementById('mnav');
  if (mnav) {
    var setM = function (on) {
      mnav.classList.toggle('on', on); mnav.setAttribute('aria-hidden', on ? 'false' : 'true');
      document.documentElement.classList.toggle('lock', on);
      Array.prototype.forEach.call(document.querySelectorAll('.burger'), function (b) { b.setAttribute('aria-expanded', on ? 'true' : 'false'); });
    };
    Array.prototype.forEach.call(document.querySelectorAll('.burger'), function (b) { b.addEventListener('click', function (ev) { ev.stopPropagation(); setM(true); }); });
    mnav.querySelector('.mnav-x').addEventListener('click', function () { setM(false); });
    Array.prototype.forEach.call(mnav.querySelectorAll('a'), function (a) { a.addEventListener('click', function () { setM(false); }); });
    var here = location.pathname;
    Array.prototype.forEach.call(mnav.querySelectorAll('a'), function (a) {
      var h = a.getAttribute('href'); if (h === here || (h === B + '/#accueil' && here === B + '/')) a.classList.add('on');
    });
  }

  /* ---- accueil : le rideau (la photo) se lève sur la page ---- */
  var hero = document.getElementById('hero'), site = document.getElementById('site');
  if (hero && site) {
    var tint = function (c) { var m = document.querySelector('meta[name=theme-color]'); if (m) m.setAttribute('content', c); };   // barres Safari iOS : sombres sur le rideau, blanches sur la page
    var map = {}; try { map = JSON.parse(hero.getAttribute('data-map') || '{}'); } catch (e) {}
    var h0 = location.hash.slice(1);
    if (h0 && map[h0]) { location.replace(B + '/' + map[h0] + '/#' + h0); return; }   // anciens liens index.html#lieu
    // le rideau accueille chaque arrivée sur le site ; il reste levé quand on revient à l'accueil depuis une autre page
    var seen = !!document.referrer && document.referrer.indexOf(location.origin) === 0;
    var up = function (instant) {
      if (hero.classList.contains('up')) return;
      if (instant) hero.classList.add('now');
      window.scrollTo(0, 0);
      hero.classList.add('up'); site.classList.remove('locked'); upAt = Date.now(); tint('#ffffff');
      if (!instant) {   // pendant que le rideau monte, la page reste calée en haut : on ne saute aucun texte
        document.documentElement.classList.add('lock');
        setTimeout(function () { window.scrollTo(0, 0); document.documentElement.classList.remove('lock'); }, 900);
      }
    };
    if (h0 === 'accueil') { seen = false; history.replaceState(null, '', B + '/'); }   // le logo rappelle le rideau
    if (h0 === 'studio' || h0 === 'projets' || seen) up(true); else { site.classList.add('locked'); tint('#2a2a28'); }
    var upAt = 0;
    var down = function () {                                         // le rideau redescend
      if (!hero.classList.contains('up')) return;
      history.replaceState(null, '', B + '/'); window.scrollTo(0, 0);
      hero.classList.remove('now', 'up'); site.classList.add('locked'); tint('#2a2a28');
    };
    window.addEventListener('hashchange', function () { if (location.hash === '#accueil') down(); });
    // on remonte tout en haut de l'accueil et on continue de remonter : le rideau revient
    var calmNow = function () { return Date.now() - upAt > 1000 && window.scrollY <= 0 && !document.documentElement.classList.contains('lock'); };
    window.addEventListener('wheel', function (ev) { if (ev.deltaY < -8 && hero.classList.contains('up') && calmNow()) down(); }, { passive: true });
    var sy = null;
    window.addEventListener('touchstart', function (ev) { sy = hero.classList.contains('up') && window.scrollY <= 0 ? ev.touches[0].clientY : null; }, { passive: true });
    window.addEventListener('touchmove', function (ev) { if (sy !== null && ev.touches[0].clientY - sy > 70 && calmNow()) { sy = null; down(); } }, { passive: true });
    document.getElementById('enter').addEventListener('click', function () { up(); });
    hero.addEventListener('wheel', function (ev) { if (ev.deltaY > 8) up(); }, { passive: true });
    var ty = 0;
    hero.addEventListener('touchstart', function (ev) { ty = ev.touches[0].clientY; }, { passive: true });
    hero.addEventListener('touchmove', function (ev) { if (ty - ev.touches[0].clientY > 24) up(); }, { passive: true });
    return;
  }

  /* ---- agrandissement : on fait défiler toutes les images du lieu ---- */
  var lb = document.getElementById('lb'), set = [], cur = 0;
  function show(i) {
    if (!set.length) return;
    cur = (i + set.length) % set.length;
    lb.querySelector('img').src = set[cur];
    lb.querySelector('.lb-c').textContent = set.length > 1 ? (cur + 1) + ' / ' + set.length : '';
    lb.classList.toggle('one', set.length < 2);
  }
  function zoom(src, all) { if (!lb) return; set = all && all.length ? all : [src]; show(set.indexOf(src)); lb.classList.add('on'); lb.setAttribute('aria-hidden', 'false'); }
  function unzoom() { if (!lb) return; lb.classList.remove('on'); lb.setAttribute('aria-hidden', 'true'); }
  if (lb) {
    lb.addEventListener('click', function (ev) {
      if (ev.target.closest('.lb-p')) { show(cur - 1); return; }
      if (ev.target.closest('.lb-n') || ev.target.tagName === 'IMG') { show(cur + 1); return; }
      unzoom();
    });
    var sx = 0;
    lb.addEventListener('touchstart', function (ev) { sx = ev.touches[0].clientX; }, { passive: true });
    lb.addEventListener('touchend', function (ev) { var d = ev.changedTouches[0].clientX - sx; if (Math.abs(d) > 40) show(cur + (d < 0 ? 1 : -1)); }, { passive: true });
    document.addEventListener('keydown', function (ev) {
      if (!lb.classList.contains('on')) return;
      if (ev.key === 'ArrowRight') show(cur + 1); else if (ev.key === 'ArrowLeft') show(cur - 1);
    });
  }

  /* ---- fiches : une fenêtre qui vient se poser devant la page ---- */
  var grid = document.querySelector('.grid'), modal = document.getElementById('modal');
  if (!grid || !modal) return;
  var box = modal.querySelector('.mbox'), lastFocus = null;
  function open(id) {
    var t = document.getElementById('f-' + id); if (!t) return;
    box.innerHTML = ''; box.appendChild(t.content.cloneNode(true)); box.scrollTop = 0;
    lastFocus = document.activeElement;
    modal.classList.add('on'); modal.setAttribute('aria-hidden', 'false');
    document.documentElement.classList.add('lock');
    history.replaceState(null, '', '#' + id);
    var x = box.querySelector('.fx-x'); if (x) x.focus({ preventScroll: true });
  }
  function close() {
    if (!modal.classList.contains('on')) return;
    modal.classList.remove('on'); modal.setAttribute('aria-hidden', 'true');
    document.documentElement.classList.remove('lock');
    history.replaceState(null, '', location.pathname);
    if (lastFocus) lastFocus.focus({ preventScroll: true });
  }
  modal.addEventListener('click', function (ev) {
    var z = ev.target.closest('[data-zoom]');
    if (z) { zoom(z.getAttribute('data-zoom'), Array.prototype.map.call(box.querySelectorAll('[data-zoom]'), function (x) { return x.getAttribute('data-zoom'); })); return; }
    if (ev.target.closest('a')) return;
    close();   // la croix, à côté, ou sur la fiche : elle se ferme
  });
  Array.prototype.forEach.call(grid.querySelectorAll('.card'), function (c) {
    c.addEventListener('click', function (ev) { ev.preventDefault(); open(c.getAttribute('data-open')); });
  });
  document.addEventListener('keydown', function (ev) {
    if (ev.key !== 'Escape') return;
    if (lb && lb.classList.contains('on')) unzoom(); else close();
  });
  var h = location.hash.slice(1);
  if (h) open(h);
})();

// carte des lieux : un point → le nom de la localité et ses lieux, chacun mène à sa fiche
(function () {
  var c = document.getElementById('carte'); if (!c) return;
  var out = c.querySelector('.cl'), cur = null;
  function esc(s) { var d = document.createElement('div'); d.textContent = s; return d.innerHTML; }
  function show(g) {
    if (cur) cur.classList.remove('on'); cur = g; g.classList.add('on');
    out.innerHTML = '<b>' + esc(g.getAttribute('data-n')) + '</b>' + g.getAttribute('data-l').split('|').map(function (x) {
      var a = x.split('§'); return '<a href="' + esc(a[1]) + '">' + esc(a[0]) + '</a>';
    }).join('');
  }
  Array.prototype.forEach.call(c.querySelectorAll('.pt'), function (g) {
    g.addEventListener('click', function () { show(g); });
    g.addEventListener('mouseenter', function () { show(g); });
    g.addEventListener('keydown', function (ev) { if (ev.key === 'Enter' || ev.key === ' ') { ev.preventDefault(); show(g); } });
  });
  var first = c.querySelector('.pt'); if (first) show(first);
})();

// projets (accueil) : filtres par porte et vues Images · Liste · Carte ; le défilé 1 · 2 · 3 se recompose à chaque filtre
(function () {
  var pj = document.getElementById('projets'); if (!pj) return;
  var flow = pj.querySelector('.flow'), tiles = Array.prototype.slice.call(flow.querySelectorAll('.sq')), f = '', v = 'img';
  function rows() {
    var L = tiles.filter(function (t) { return !f || t.getAttribute('data-k') === f; }), i = 0, n = 0;
    flow.innerHTML = '';
    while (i < L.length) {
      var size = [1, 2, 3][n % 3], g = L.slice(i, i + size), r = document.createElement('div');
      r.className = 'rw r' + g.length;
      g.forEach(function (t) { var im = t.querySelector('img'); im.src = im.getAttribute(g.length === 1 ? 'data-b' : 'data-m'); r.appendChild(t); });
      flow.appendChild(r); i += size; n++;
    }
  }
  function apply() {
    Array.prototype.forEach.call(pj.querySelectorAll('.flt button'), function (b) { b.classList.toggle('on', b.getAttribute('data-f') === f); });
    Array.prototype.forEach.call(pj.querySelectorAll('.vws button'), function (b) { b.classList.toggle('on', b.getAttribute('data-v') === v); });
    Array.prototype.forEach.call(pj.querySelectorAll('.sec'), function (s) { s.hidden = s.getAttribute('data-for') !== f; });
    Array.prototype.forEach.call(pj.querySelectorAll('.v'), function (x) { x.hidden = x.getAttribute('data-v') !== v; });
    Array.prototype.forEach.call(pj.querySelectorAll('.li'), function (x) { x.hidden = !!f && x.getAttribute('data-k') !== f; });
    rows();
  }
  pj.querySelector('.flt').addEventListener('click', function (ev) { var b = ev.target.closest('button'); if (b) { f = b.getAttribute('data-f'); apply(); } });
  pj.querySelector('.vws').addEventListener('click', function (ev) { var b = ev.target.closest('button'); if (b) { v = b.getAttribute('data-v'); apply(); } });
})();
