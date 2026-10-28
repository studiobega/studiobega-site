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

  /* ---- survol : la première image suit la souris (ordi seulement) ---- */
  var peek = document.getElementById('peek');
  if (peek && window.matchMedia && window.matchMedia('(hover: hover) and (min-width: 900px)').matches) {
    var pimg = peek.querySelector('img'), mx = 0, my = 0, raf = 0;
    var place = function () {
      raf = 0;
      var w = peek.offsetWidth, h = peek.offsetHeight || w * 0.66;
      var x = mx + 28, y = my - h / 2;
      if (x + w > window.innerWidth - 16) x = mx - w - 28;
      y = Math.max(16, Math.min(y, window.innerHeight - h - 16));
      peek.style.transform = 'translate(' + x + 'px,' + y + 'px)';
    };
    var hide = function () { peek.classList.remove('on'); };
    rows.forEach(function (r) {
      var line = r.querySelector('.line'), src = line.getAttribute('data-peek');
      if (!src) return;
      line.addEventListener('mouseenter', function () {
        if (r.classList.contains('open')) return;
        if (pimg.getAttribute('src') !== src) pimg.src = src;
        peek.classList.add('on');
      });
      line.addEventListener('mouseleave', hide);
      line.addEventListener('click', hide);
    });
    document.addEventListener('mousemove', function (ev) { mx = ev.clientX; my = ev.clientY; if (!raf) raf = requestAnimationFrame(place); }, { passive: true });
  }

  /* ---- lightbox ---- */
  function zoom(src) { if (!lb) return; lb.querySelector('img').src = src; lb.classList.add('on'); lb.setAttribute('aria-hidden', 'false'); }
  function unzoom() { if (!lb) return; lb.classList.remove('on'); lb.setAttribute('aria-hidden', 'true'); }
  if (lb) { lb.addEventListener('click', unzoom); document.addEventListener('keydown', function (ev) { if (ev.key === 'Escape') unzoom(); }); }
})();
