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
      hero.classList.add('up'); site.classList.remove('locked'); tint('#ffffff');
      if (!instant) {   // pendant que le rideau monte, la page reste calée en haut : on ne saute aucun texte
        document.documentElement.classList.add('lock');
        setTimeout(function () { window.scrollTo(0, 0); document.documentElement.classList.remove('lock'); }, 900);
      }
    };
    if (h0 === 'accueil') { seen = false; history.replaceState(null, '', B + '/'); }   // le logo rappelle le rideau
    if (h0 === 'studio' || h0 === 'projets' || seen) up(true); else { site.classList.add('locked'); tint('#2a2a28'); }
    var down = function () {                                         // le rideau redescend
      if (!hero.classList.contains('up')) return;
      history.replaceState(null, '', B + '/'); window.scrollTo(0, 0);
      hero.classList.remove('now', 'up'); site.classList.add('locked'); tint('#2a2a28');
    };
    window.addEventListener('hashchange', function () { if (location.hash === '#accueil') down(); });
    // le rideau ne revient jamais en remontant la page : seulement à l'arrivée sur le site, ou par le logo (#accueil)
    document.getElementById('enter').addEventListener('click', function () { up(); });
    hero.addEventListener('wheel', function (ev) { if (ev.deltaY > 8) up(); }, { passive: true });
    var ty = 0;
    hero.addEventListener('touchstart', function (ev) { ty = ev.touches[0].clientY; }, { passive: true });
    hero.addEventListener('touchmove', function (ev) { if (ty - ev.touches[0].clientY > 24) up(); }, { passive: true });
    // (la suite — agrandissement, fiches — sert aussi à l'accueil quand il porte les projets)
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
  // page d'un projet (référencement) : les photos s'agrandissent aussi
  var pp = document.querySelector('.pp-box');
  if (pp) pp.addEventListener('click', function (ev) {
    var z = ev.target.closest('[data-zoom]'); if (!z) return;
    zoom(z.getAttribute('data-zoom'), Array.prototype.map.call(pp.querySelectorAll('[data-zoom]'), function (x) { return x.getAttribute('data-zoom'); }));
  });
  var grid = document.querySelector('.grid') || document.getElementById('projets'), modal = document.getElementById('modal');
  if (!grid || !modal) return;
  var box = modal.querySelector('.mbox'), lastFocus = null, pushed = false, fromLoad = false;
  function open(id) {
    var t = document.getElementById('f-' + id); if (!t) return;
    box.innerHTML = ''; box.appendChild(t.content.cloneNode(true)); box.scrollTop = 0;
    lastFocus = document.activeElement;
    modal.classList.add('on'); modal.setAttribute('aria-hidden', 'false');
    document.documentElement.classList.add('lock');
    box.style.transform = ''; box.style.opacity = '';
    if (fromLoad) history.replaceState(null, '', '#' + id); else { history.pushState({ fiche: id }, '', '#' + id); pushed = true; }
    var x = box.querySelector('.fx-x'); if (x) x.focus({ preventScroll: true });
  }
  function shut() {
    if (!modal.classList.contains('on')) return;
    modal.classList.remove('on'); modal.setAttribute('aria-hidden', 'true');
    document.documentElement.classList.remove('lock');
    if (lastFocus) lastFocus.focus({ preventScroll: true });
  }
  function close() {   // la fiche s'est ouverte en avançant d'un pas dans l'historique : on recule d'un pas
    if (!modal.classList.contains('on')) return;
    if (pushed) { pushed = false; history.back(); } else { history.replaceState(null, '', location.pathname + location.search); shut(); }
  }
  window.addEventListener('popstate', function () { pushed = false; shut(); });   // geste ou bouton « retour »
  // téléphone : on glisse la fiche de côté pour la retirer, comme une carte
  var sx = null, sy0 = 0, dx = 0, swiping = false, swiped = false;
  modal.addEventListener('touchstart', function (ev) { if (ev.touches.length !== 1) return; sx = ev.touches[0].clientX; sy0 = ev.touches[0].clientY; dx = 0; swiping = false; }, { passive: true });
  modal.addEventListener('touchmove', function (ev) {
    if (sx === null) return;
    var x = ev.touches[0].clientX - sx, y = ev.touches[0].clientY - sy0;
    if (!swiping) { if (Math.abs(x) > 12 && Math.abs(x) > Math.abs(y) * 1.4) { swiping = true; box.style.transition = 'none'; } else if (Math.abs(y) > 12) { sx = null; return; } else return; }
    dx = x; box.style.transform = 'translateX(' + dx + 'px) rotate(' + (dx / 40) + 'deg)'; box.style.opacity = String(1 - Math.min(Math.abs(dx) / 500, .5));
  }, { passive: true });
  modal.addEventListener('touchend', function () {
    if (sx === null) return; sx = null;
    if (!swiping) return;
    box.style.transition = '';
    if (Math.abs(dx) > 90) {
      swiped = true; setTimeout(function () { swiped = false; }, 400);
      box.style.transform = 'translateX(' + (dx > 0 ? 120 : -120) + 'vw) rotate(' + (dx > 0 ? 6 : -6) + 'deg)'; box.style.opacity = '0';
      setTimeout(close, 220);
    } else { box.style.transform = ''; box.style.opacity = ''; }
    swiping = false;
  });
  modal.addEventListener('click', function (ev) {
    var z = ev.target.closest('[data-zoom]');
    if (z) { zoom(z.getAttribute('data-zoom'), Array.prototype.map.call(box.querySelectorAll('[data-zoom]'), function (x) { return x.getAttribute('data-zoom'); })); return; }
    if (ev.target.closest('a') || swiped) return;
    close();   // la croix, à côté, ou sur la fiche : elle se ferme
  });
  grid.addEventListener('click', function (ev) {   // vignettes, lignes de liste, cartes de visite de la carte
    var c = ev.target.closest('[data-open]'); if (!c || !grid.contains(c)) return;
    ev.preventDefault(); open(c.getAttribute('data-open'));
  });
  document.addEventListener('keydown', function (ev) {
    if (ev.key !== 'Escape') return;
    if (lb && lb.classList.contains('on')) unzoom(); else close();
  });
  var h = location.hash.slice(1);
  if (h) { fromLoad = true; open(h); fromLoad = false; }
})();

// carte des lieux : un point par commune. Un lieu : sa fiche s'ouvre. Plusieurs : une courte liste, puis la fiche.
// En fermant la fiche, on retrouve la carte (la liste s'est déjà refermée). Les communes hors du filtre restent en gris.
(function () {
  var c = document.getElementById('carte'); if (!c) return;
  var pop = document.createElement('div'); pop.className = 'pop'; pop.hidden = true; c.appendChild(pop);
  var f = '', cur = null;
  function items(g) { return g.getAttribute('data-l').split('|').map(function (x) { var a = x.split('§'); return { n: a[0], id: a[1], k: a[2] }; }); }
  function esc(s) { var d = document.createElement('div'); d.textContent = s; return d.innerHTML; }
  function hide() { pop.hidden = true; if (cur) cur.classList.remove('on'); cur = null; }
  function openId(id) { var a = document.createElement('a'); a.setAttribute('data-open', id); a.href = '#' + id; a.hidden = true; c.appendChild(a); a.click(); c.removeChild(a); }
  function pick(g) {
    var L = items(g).filter(function (i) { return !f || i.k === f; }); if (!L.length) return;
    if (L.length === 1) { hide(); openId(L[0].id); return; }
    if (cur) cur.classList.remove('on'); cur = g; g.classList.add('on');
    pop.innerHTML = '<div class="pop-h">' + esc(g.getAttribute('data-n')) + '</div>' +
      L.map(function (i) { return '<a href="#' + esc(i.id) + '" data-open="' + esc(i.id) + '">' + esc(i.n) + '</a>'; }).join('');
    pop.hidden = false;
    var r = g.querySelector('circle').getBoundingClientRect(), R = c.getBoundingClientRect(), w = pop.offsetWidth;
    pop.style.left = Math.min(Math.max(r.left + r.width / 2 - R.left - w / 2, 0), R.width - w) + 'px';
    pop.style.top = (r.bottom - R.top + 8) + 'px';
  }
  pop.addEventListener('click', function () { hide(); });   // le choix fait, la liste disparaît ; la fiche s'ouvre par-dessus la carte
  Array.prototype.forEach.call(c.querySelectorAll('.pt'), function (g) {
    g.addEventListener('click', function (ev) { ev.stopPropagation(); if (g.classList.contains('off')) return; if (cur === g) hide(); else pick(g); });
    g.addEventListener('keydown', function (ev) { if (ev.key === 'Enter' || ev.key === ' ') { ev.preventDefault(); pick(g); } });
  });
  document.addEventListener('click', function (ev) { if (!pop.hidden && !ev.target.closest('.pop') && !ev.target.closest('.pt')) hide(); });
  c.filtre = function (x) {   // filtre des portes : les communes sans lieu de la porte choisie passent en gris
    f = x || ''; hide();
    Array.prototype.forEach.call(c.querySelectorAll('.pt'), function (g) { g.classList.toggle('off', !!f && !items(g).some(function (i) { return i.k === f; })); });
  };
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
    var ca = document.getElementById('carte'); if (ca && ca.filtre) ca.filtre(f);
  }
  // la barre des filtres se colle exactement sous le bandeau du haut (sa hauteur varie selon l'écran)
  var nav = document.querySelector('.site .nav'), bar = pj.querySelector('.bar');
  function stick() { var h = nav ? nav.getBoundingClientRect().height : 0; bar.style.top = Math.floor(h) + 'px'; return h; }
  stick(); window.addEventListener('resize', stick);
  // changer de filtre ou de vue ramène au début de la liste, juste sous les barres
  function haut() {
    var y = pj.getBoundingClientRect().top + window.pageYOffset - stick();
    if (window.pageYOffset > y + 2) window.scrollTo({ top: y, behavior: 'smooth' });
  }
  pj.querySelector('.flt').addEventListener('click', function (ev) { var b = ev.target.closest('button'); if (b) { f = b.getAttribute('data-f'); apply(); haut(); } });
  pj.querySelector('.vws').addEventListener('click', function (ev) { var b = ev.target.closest('button'); if (b) { v = b.getAttribute('data-v'); apply(); haut(); } });
})();
