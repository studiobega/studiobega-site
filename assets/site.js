/* studiobega.be — accueil, fiches dans la grille, agrandissement des photos. Aucune dépendance. */
(function () {
  'use strict';

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
      var h = a.getAttribute('href'); if (h === here || (h === '/#accueil' && here === '/')) a.classList.add('on');
    });
  }

  /* ---- accueil : le rideau (la photo) se lève sur la page ---- */
  var hero = document.getElementById('hero'), site = document.getElementById('site');
  if (hero && site) {
    var map = {}; try { map = JSON.parse(hero.getAttribute('data-map') || '{}'); } catch (e) {}
    var h0 = location.hash.slice(1);
    if (h0 && map[h0]) { location.replace('/' + map[h0] + '/#' + h0); return; }   // anciens liens index.html#lieu
    // le rideau accueille chaque arrivée sur le site ; il reste levé quand on revient à l'accueil depuis une autre page
    var seen = !!document.referrer && document.referrer.indexOf(location.origin) === 0;
    /* la voix : un extrait de Benjamin, une forme blanche qui vibre avec lui */
    var vo = document.getElementById('voice'), voice = null;
    if (vo) voice = (function () {
      var btn = vo.querySelector('.vbtn'), cv = vo.querySelector('canvas'), au = vo.querySelector('audio'), cx = cv.getContext('2d');
      var data = null, playing = false, raf = 0, seekTo = -1, t0 = performance.now(), IC = 26;
      var calm = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
      fetch(vo.getAttribute('data-env')).then(function (r) { return r.json(); }).then(function (d) { data = d; start(); }).catch(function () {});
      function fit() {
        var k = window.devicePixelRatio || 1, w = cv.clientWidth, h = cv.clientHeight;
        if (cv.width !== Math.round(w * k)) { cv.width = Math.round(w * k); cv.height = Math.round(h * k); }
        cx.setTransform(k, 0, 0, k, 0, 0);
      }
      function draw() {
        if (!data) return; fit();
        var W = cv.clientWidth, H = cv.clientHeight, n = data.peaks.length, step = (W - IC) / n, bw = Math.max(1.5, step * 0.5);
        var dur = au.duration || data.dur, p = Math.min(1, (au.currentTime || 0) / dur), ph = p * n;
        var lvl = playing ? (data.env[Math.min(data.env.length - 1, Math.floor(au.currentTime * data.fps))] || 0) : 0;
        var br = playing || calm ? 0 : 0.08 * Math.sin((performance.now() - t0) / 650);
        cx.clearRect(0, 0, W, H); cx.fillStyle = '#fff'; cx.globalAlpha = 0.95;
        if (playing) { cx.fillRect(2, H / 2 - 6, 3, 12); cx.fillRect(9, H / 2 - 6, 3, 12); }
        else { cx.beginPath(); cx.moveTo(3, H / 2 - 7); cx.lineTo(14, H / 2); cx.lineTo(3, H / 2 + 7); cx.closePath(); cx.fill(); }
        for (var i = 0; i < n; i++) {
          var d = i + 0.5 - ph, w = Math.exp(-d * d / 5);
          var h = H * (0.14 + 0.42 * data.peaks[i] * (1 + br) + (playing ? 0.5 * lvl * w : 0));
          h = Math.min(H, Math.max(2, h));
          cx.globalAlpha = (p > 0 && i < ph) ? 1 : 0.6;
          cx.fillRect(IC + i * step, (H - h) / 2, bw, h);
        }
        cx.globalAlpha = 1;
      }
      function tick() {
        draw();
        if (hero.classList.contains('up') && !playing) { raf = 0; return; }
        raf = requestAnimationFrame(tick);
      }
      function start() { if (!raf) raf = requestAnimationFrame(tick); }
      function load() { if (!au.getAttribute('src')) { au.src = vo.getAttribute('data-src'); au.load(); } }
      au.addEventListener('loadedmetadata', function () { if (seekTo >= 0) { au.currentTime = seekTo * au.duration; seekTo = -1; } });
      au.addEventListener('play', function () { playing = true; btn.setAttribute('aria-pressed', 'true'); start(); });
      au.addEventListener('pause', function () { playing = false; btn.setAttribute('aria-pressed', 'false'); });
      au.addEventListener('ended', function () { playing = false; au.currentTime = 0; btn.setAttribute('aria-pressed', 'false'); });
      btn.addEventListener('click', function (ev) {
        ev.stopPropagation(); load();
        var r = cv.getBoundingClientRect(), x = ev.clientX - r.left;
        if (ev.detail !== 0 && x > IC && x <= r.width) {          // un clic sur la forme : on y va
          var f = (x - IC) / (r.width - IC);
          if (au.readyState >= 1) au.currentTime = f * au.duration; else seekTo = f;
          au.play().catch(function () {}); return;
        }
        if (playing) au.pause(); else au.play().catch(function () {});
      });
      ['touchstart', 'touchmove'].forEach(function (t) { btn.addEventListener(t, function (ev) { ev.stopPropagation(); }, { passive: true }); });
      window.addEventListener('resize', draw);
      return {
        hush: function () {                                        // le rideau se lève : la voix s'efface
          if (!playing) return;
          var v = 1, iv = setInterval(function () {
            v -= 0.1; try { au.volume = Math.max(0, v); } catch (e) {}
            if (v <= 0) { clearInterval(iv); au.pause(); try { au.volume = 1; } catch (e) {} }
          }, 50);
        },
        wake: start
      };
    })();
    var up = function (instant) {
      if (voice) voice.hush();
      if (hero.classList.contains('up')) return;
      if (instant) hero.classList.add('now');
      window.scrollTo(0, 0);
      hero.classList.add('up'); site.classList.remove('locked');
      if (!instant) {   // pendant que le rideau monte, la page reste calée en haut : on ne saute aucun texte
        document.documentElement.classList.add('lock');
        setTimeout(function () { window.scrollTo(0, 0); document.documentElement.classList.remove('lock'); }, 900);
      }
    };
    if (h0 === 'accueil') { seen = false; history.replaceState(null, '', '/'); }   // le logo rappelle le rideau
    if (h0 === 'studio' || seen) up(true); else site.classList.add('locked');
    window.addEventListener('hashchange', function () {
      if (location.hash !== '#accueil') return;
      history.replaceState(null, '', '/'); window.scrollTo(0, 0);
      hero.classList.remove('now', 'up'); site.classList.add('locked');
      window.scrollTo(0, 0);
      if (voice) voice.wake();
    });
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
