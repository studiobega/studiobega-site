/* studiobega.be — rideau d'accueil, fiches dépliantes, lightbox. Aucune dépendance. */
(function () {
  'use strict';
  var hero = document.getElementById('hero'), site = document.getElementById('site'), lb = document.getElementById('lb');
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
    closeAll(); history.replaceState(null, '', location.pathname);
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
    history.replaceState(null, '', '#' + r.id);
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
      if (r.classList.contains('open')) { closeAll(); history.replaceState(null, '', location.pathname); } else open(r);
    });
    r.querySelector('.panel').addEventListener('click', function (ev) {
      if (ev.target.hasAttribute('data-zoom')) { ev.stopPropagation(); zoom(ev.target.getAttribute('data-zoom')); return; }
      if (ev.target.closest('a')) return;
      closeAll(); history.replaceState(null, '', location.pathname);
    });
  });
  function openHash() {
    var h = location.hash ? location.hash.slice(1) : '', r0 = h && document.getElementById(h);
    if (r0 && r0.classList.contains('row')) { enter(true); open(r0, true); setTimeout(function () { r0.scrollIntoView({ block: 'start' }); }, 50); }
  }
  openHash();
  window.addEventListener('hashchange', openHash);

  /* ---- lightbox ---- */
  function zoom(src) { if (!lb) return; lb.querySelector('img').src = src; lb.classList.add('on'); lb.setAttribute('aria-hidden', 'false'); }
  function unzoom() { if (!lb) return; lb.classList.remove('on'); lb.setAttribute('aria-hidden', 'true'); }
  if (lb) { lb.addEventListener('click', unzoom); document.addEventListener('keydown', function (ev) { if (ev.key === 'Escape') unzoom(); }); }
})();
