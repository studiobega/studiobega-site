/* studiobega.be — accueil, fiches dans la grille, agrandissement des photos. Aucune dépendance. */
(function () {
  'use strict';

  /* ---- accueil : un plein écran ; on entre en cliquant ou en faisant défiler ---- */
  var hero = document.getElementById('hero');
  if (hero) {
    var map = {}; try { map = JSON.parse(hero.getAttribute('data-map') || '{}'); } catch (e) {}
    var h0 = location.hash.slice(1);
    if (h0 && map[h0]) { location.replace('/' + map[h0] + '/#' + h0); return; }   // anciens liens index.html#lieu
    var go = function () { location.href = '/territoires/'; };
    hero.addEventListener('wheel', function (ev) { if (ev.deltaY > 8) go(); }, { passive: true });
    var ty = 0;
    hero.addEventListener('touchstart', function (ev) { ty = ev.touches[0].clientY; }, { passive: true });
    hero.addEventListener('touchmove', function (ev) { if (ty - ev.touches[0].clientY > 24) go(); }, { passive: true });
    return;
  }

  /* ---- agrandissement ---- */
  var lb = document.getElementById('lb');
  function zoom(src) { if (!lb) return; lb.querySelector('img').src = src; lb.classList.add('on'); lb.setAttribute('aria-hidden', 'false'); }
  function unzoom() { if (!lb) return; lb.classList.remove('on'); lb.setAttribute('aria-hidden', 'true'); }
  if (lb) lb.addEventListener('click', unzoom);

  /* ---- fiches : elles s'ouvrent dans la grille, à la place de la rangée cliquée ---- */
  var grid = document.querySelector('.grid');
  if (!grid) return;
  var gp = null, fx = document.getElementById('fx');
  try { history.scrollRestoration = 'manual'; } catch (e) {}
  function navH() { var n = document.querySelector('.nav'); return n ? n.getBoundingClientRect().height : 56; }
  function top(el) { return el.getBoundingClientRect().top + window.pageYOffset; }

  function close(quiet) {
    if (!gp) return null;
    var c = gp._card;
    c.classList.remove('on'); gp.remove(); gp = null;
    if (fx) fx.classList.remove('on');
    history.replaceState(null, '', location.pathname);
    if (!quiet && c.getBoundingClientRect().top < navH()) window.scrollTo(0, top(c) - navH() - 16);
    return c;
  }
  function open(id, noScroll) {
    var c = grid.querySelector('.card[data-open="' + id + '"]'), t = document.getElementById('f-' + id);
    if (!c || !t) return;
    close(true);
    var cards = Array.prototype.slice.call(grid.querySelectorAll('.card')), first = c;
    for (var i = cards.length - 1; i >= 0; i--) if (Math.abs(cards[i].offsetTop - c.offsetTop) < 4) first = cards[i];
    gp = document.createElement('div'); gp.className = 'gpanel'; gp._card = c;
    gp.appendChild(t.content.cloneNode(true));
    first.parentNode.insertBefore(gp, first); c.classList.add('on');
    gp.addEventListener('click', function (ev) {
      var z = ev.target.closest('[data-zoom]'); if (z) { zoom(z.getAttribute('data-zoom')); return; }
      if (ev.target.closest('a')) return;
      close();
    });
    history.replaceState(null, '', '#' + id);
    if (fx) fx.classList.add('on');
    if (!noScroll) window.scrollTo(0, Math.max(0, top(gp) - navH() - 24));
  }
  Array.prototype.forEach.call(grid.querySelectorAll('.card'), function (c) {
    c.addEventListener('click', function (ev) { ev.preventDefault(); open(c.getAttribute('data-open')); });
  });
  if (fx) fx.addEventListener('click', function () { close(); });
  document.addEventListener('keydown', function (ev) {
    if (ev.key !== 'Escape') return;
    if (lb && lb.classList.contains('on')) unzoom(); else close();
  });
  /* la fiche se referme d'elle-même quand on la dépasse en faisant défiler */
  var ticking = false;
  window.addEventListener('scroll', function () {
    if (!gp || ticking) return; ticking = true;
    requestAnimationFrame(function () {
      ticking = false; if (!gp) return;
      var b = gp.getBoundingClientRect();
      if (b.bottom < navH() - 40) {
        var before = grid.getBoundingClientRect().bottom;
        close(true);
        window.scrollTo(0, window.pageYOffset + (grid.getBoundingClientRect().bottom - before));
      } else if (b.top > window.innerHeight + 40) close(true);
    });
  }, { passive: true });
  var rw = window.innerWidth;
  window.addEventListener('resize', function () {
    if (!gp || window.innerWidth === rw) return; rw = window.innerWidth;
    open(gp._card.getAttribute('data-open'), true);
  });
  var h = location.hash.slice(1);
  if (h) window.addEventListener('load', function () { open(h); });
})();
