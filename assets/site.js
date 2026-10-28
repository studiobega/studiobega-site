/* studiobega.be — rideau d'accueil, vues Images / Liste, fiches, lightbox. Aucune dépendance. */
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

  /* ---- fiche plein écran (depuis la grille) ---- */
  var sheet = document.getElementById('sheet'), lastScroll = 0;
  function openSheet(id) {
    var r = document.getElementById(id); if (!r || !sheet) return;
    var line = r.querySelector('.line');
    var meta = Array.prototype.map.call(line.querySelectorAll('.pl,.tp,.yr,.st'), function (x) { return x.textContent; }).filter(Boolean).join(' · ');
    sheet.querySelector('.sheet-h').innerHTML = '';
    var nm = document.createElement('span'); nm.className = 'nm'; nm.textContent = line.querySelector('.nm').textContent;
    var cm = document.createElement('span'); cm.className = 'cm'; cm.textContent = meta;
    sheet.querySelector('.sheet-h').appendChild(nm); sheet.querySelector('.sheet-h').appendChild(cm);
    var b = sheet.querySelector('.sheet-b'); b.innerHTML = ''; b.appendChild(r.querySelector('.panel').cloneNode(true));
    lastScroll = window.pageYOffset;
    sheet.scrollTop = 0; sheet.classList.add('on'); sheet.setAttribute('aria-hidden', 'false');
    document.documentElement.style.overflow = 'hidden';
    history.replaceState(null, '', '#' + id);
    sheet.querySelector('.sheet-x').focus({ preventScroll: true });
  }
  function closeSheet() {
    if (!sheet || !sheet.classList.contains('on')) return false;
    sheet.classList.remove('on'); sheet.setAttribute('aria-hidden', 'true');
    document.documentElement.style.overflow = '';
    history.replaceState(null, '', location.pathname);
    window.scrollTo(0, lastScroll);
    return true;
  }
  if (sheet) {
    sheet.querySelector('.sheet-x').addEventListener('click', closeSheet);
    sheet.addEventListener('click', function (ev) {
      var z = ev.target.closest('[data-zoom]'); if (z) { zoom(z.getAttribute('data-zoom')); }
    });
  }
  Array.prototype.forEach.call(document.querySelectorAll('.card'), function (c) {
    c.addEventListener('click', function (ev) { ev.preventDefault(); openSheet(c.getAttribute('data-open')); });
  });

  function openHash() {
    var h = location.hash ? location.hash.slice(1) : '', r0 = h && document.getElementById(h);
    if (!(r0 && r0.classList.contains('row'))) return;
    enter(true);
    if (view === 'img' && document.querySelector('.card[data-open="' + h + '"]')) { openSheet(h); return; }
    setView('list'); open(r0, true); setTimeout(function () { r0.scrollIntoView({ block: 'start' }); }, 50);
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
    closeSheet();
  });
})();
