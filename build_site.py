#!/usr/bin/env python3
"""Génère le site statique studiobega.be depuis data/.

Entrées
  data/projets.json          lignes Airtable (Site ✓), champs normalisés
  data/photos_manifest.json  [{code,k,id,...}] ordre des photos par projet
  data/photos/<attId>.jpg    photos (max 1600 px) rapatriées d'Airtable
  data/mockup/*.jpg          hero, duo, carte de contact, images test plan directeur

Sortie
  dist/   index.html, studio.html, contact.html, assets/, img/, .htaccess

Usage : python3 -I build_site.py
"""
import json, html, os, re, shutil, unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA, DIST = ROOT / 'data', ROOT / 'dist'
IMG = DIST / 'img'
e = lambda s: html.escape(s or '', quote=False)

# ---------- données ----------
P = json.load(open(DATA / 'projets.json'))
MAN = json.load(open(DATA / 'photos_manifest.json')) if (DATA / 'photos_manifest.json').exists() else []
PORTES = [('communes', 'Communes'), ('hotellerie', 'Hôtellerie & commerces'), ('promotion', 'Promotion'), ('maisons', 'Maisons')]
PKEY = {n: k for k, n in PORTES}

def slug(s):
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode()
    s = re.sub(r'[^a-zA-Z0-9]+', '-', s).strip('-').lower()
    return s or 'lieu'

def ph(s):  # placeholder du mockup → vide
    return '' if (not s or s.startswith('[')) else s

for p in P:
    p['id'] = slug(p['nom']) if ph(p['nom']) else slug(p['code'])
    p['pk'] = PKEY.get(p['porte'], 'communes')
# ids uniques
seen = {}
for p in P:
    n = seen.get(p['id'], 0); seen[p['id']] = n + 1
    if n: p['id'] = f"{p['id']}-{n+1}"

# ---------- images ----------
from PIL import Image, ImageOps
FALLBACK = {  # images test du mockup, utilisées seulement si Airtable n'a pas de photo
    'P79': ['6bf52fbbb6c5bd363811c13f9982db33'], 'P98': ['6c72dd911871c2dab9dc1c02ea7ac5d3'],
    'REF.17': ['a105e3318e80effe4ed8582fbc8fba86'],
}
def save(img, dst, w, q=82):
    img = ImageOps.exif_transpose(img).convert('RGB')
    if img.width > w: img = img.resize((w, round(img.height * w / img.width)), Image.LANCZOS)
    dst.parent.mkdir(parents=True, exist_ok=True); img.save(dst, 'JPEG', quality=q, optimize=True, progressive=True)

def photos_for(p):
    """→ liste de (grande, vignette) en chemins relatifs dist/."""
    out = []
    mine = sorted([m for m in MAN if m['code'] == p['code']], key=lambda m: m['k'])
    srcs = [(DATA / 'photos' / f"{m['id']}.jpg") for m in mine]
    srcs = [s for s in srcs if s.exists()]
    if not srcs:
        srcs = [DATA / 'mockup' / f'{b}.jpg' for b in FALLBACK.get(p['code'], []) if (DATA / 'mockup' / f'{b}.jpg').exists()]
    for k, src in enumerate(srcs):
        big, th = IMG / p['id'] / f'{k+1}.jpg', IMG / p['id'] / f'{k+1}-t.jpg'
        if not big.exists() or big.stat().st_mtime < src.stat().st_mtime:
            im = Image.open(src); save(im, big, 1600); save(im, th, 480, 78)
        out.append((f"img/{p['id']}/{k+1}.jpg", f"img/{p['id']}/{k+1}-t.jpg"))
    return out

# ---------- CSS ----------
BASE_CSS = open(ROOT / 'assets' / 'site.css').read()

FONTS = '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n<link href="https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;1,6..72,400&family=Jost:wght@400;500;600&display=swap" rel="stylesheet">'

FOOT = '''    <footer class="foot">
      <div>© 2026 Studio Benjamin Gaspard SRL · TVA BE 0799.818.844</div>
      <div class="grp"><a href="https://www.instagram.com/studio_bega_/">Instagram</a><a href="https://www.facebook.com/studiobenjamingaspard">Facebook</a><a href="https://be.linkedin.com/company/studiobega">LinkedIn</a></div>
    </footer>
'''

def nav(on, home_btn=False):
    links = ''.join(f'<a href="{href}"{" class=\"on\"" if t == on else ""}>{t}</a>' for href, t in [('index.html#lieux', 'Lieux'), ('studio.html', 'Studio'), ('contact.html', 'Contact')])
    logo = '<button type="button" class="logo" id="home" aria-label="Studio BEGA, accueil">BEGA<span class="dot" aria-hidden="true"></span></button>' if home_btn else '<a class="logo" href="index.html" aria-label="Studio BEGA, accueil">BEGA<span class="dot" aria-hidden="true"></span></a>'
    return f'    <nav class="nav" aria-label="Navigation">\n      {logo}\n      <div class="links">{links}</div>\n    </nav>\n'

def page(title, body, desc, extra_head=''):
    return f'''<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}"><meta property="og:image" content="https://studiobega.be/img/hero.jpg"><meta property="og:type" content="website">
<link rel="icon" href="favicon.svg" type="image/svg+xml">
{FONTS}
<link rel="stylesheet" href="assets/site.css">
{extra_head}</head>
<body>
{body}
</body>
</html>
'''

# ---------- LIEUX ----------
def row(p):
    pics = photos_for(p)
    thumb = f'<img class="th" src="{pics[0][1]}" alt="" loading="lazy">' if pics else '<span class="th" aria-hidden="true"></span>'
    nom = ph(p['nom']) or '[Nom du lieu]'
    lieu, typ, an, etat = ph(p['lieu']), p['type'], ph(p['annee']), ph(p['etat'])
    dem, cle, sorti, para = ph(p['dem']), ph(p['cle']), ph(p['sorti']), ph(p['para'])
    picsh = ''.join(f'<img src="{b}" alt="{e(nom)}" loading="lazy" data-zoom="{b}">' for b, t in pics) if pics else '<span class="ph" aria-hidden="true"></span>'
    two = ' two' if len(pics) >= 2 else ''
    liens = [l.split('|', 1) for l in (p['liens'] or '').split('\n') if '|' in l]
    more = ''
    if para or liens:
        lk = ''.join(f'<a href="{u.strip()}">{e(t.strip())}</a>' for t, u in liens if u.strip() and u.strip() != '#')
        more = f'<div class="more">{f"<p>{e(para)}</p>" if para else ""}{f"<div class=\"links\">{lk}</div>" if lk else ""}</div>'
    multi = '\n' in sorti
    sorti_h = ''.join(f'<span style="display:block">{e(x.strip())}</span>' for x in sorti.split('\n') if x.strip()) if multi else e(sorti)
    dl = ''
    if dem:   dl += f'<div><dt class="lab">Demandé</dt><dd>{e(dem)}</dd></div>'
    if cle:   dl += f'<div><dt class="lab">La clé</dt><dd class="cle"><span class="key">{e(cle)}</span></dd></div>'
    if sorti: dl += f'<div><dt class="lab">{"Pistes" if multi else "Sorti"}</dt><dd>{sorti_h}</dd></div>'
    return f'''      <article class="row" id="{p['id']}">
        <button type="button" class="line" aria-expanded="false" aria-controls="p-{p['id']}">{thumb}<span class="nm">{e(nom)}</span><span class="md"><span class="pl">{e(lieu)}</span><span class="tp">{e(typ)}</span><span class="yr">{e(an)}</span></span><span class="st">{e(etat)}</span></button>
        <div class="pw" id="p-{p['id']}"><div class="pi"><div class="panel">
            <div class="pics{two}">{picsh}</div>
            <div class="tx"><dl>{dl}</dl>{more}</div>
        </div></div></div>
      </article>
'''

bykey = {k: sorted([p for p in P if p['pk'] == k], key=lambda p: (p['ordre'] or 999, p['nom'])) for k, _ in PORTES}
doors = ''.join(f'<a href="#{k}">{e(n)}<span class="n">{len(bykey[k])}</span></a>' for k, n in PORTES)
lieux = f'''    <header id="lieux" class="lieux-head"><div class="doors">{doors}</div></header>
'''
for k, n in PORTES:
    lieux += f'    <h2 class="lab sec" id="{k}">{e(n)}</h2>\n    <div>\n' + ''.join(row(p) for p in bykey[k]) + '    </div>\n'

# hero & images fixes
for src, dst in [('7d27646bb9e84d280aaa51552a3d6afb', 'hero'), ('ec894847fb1cdd2dc482462924bcd351', 'duo'), ('18732aa0aa56be5aeb1bb35760702fa6', 'contact')]:
    s = DATA / 'mockup' / f'{src}.jpg'
    if s.exists():
        save(Image.open(s), IMG / f'{dst}.jpg', 2000 if dst == 'hero' else 1600, 84)

index_body = f'''<section class="hero" id="hero">
  <img class="bg" src="img/hero.jpg" alt="Bouillon vu du ciel : l'esplanade, le château, la Semois">
  <div class="veil" aria-hidden="true"></div>
  <button type="button" class="go" id="enter" aria-label="Voir les lieux"></button>
  <div class="nav" aria-hidden="true"><span class="logo">BEGA<span class="dot"></span></span></div>
  <div class="txt">
    <h1>Tout est déjà là.</h1>
    <p>Lire un lieu. Écouter un programme. Trouver ce qui fait basculer le projet.</p>
  </div>
</section>
<div class="site locked" id="site"><div class="page"><div class="wrap">
{nav('Lieux', home_btn=True)}{lieux}{FOOT}</div></div></div>
<div class="lb" id="lb" aria-hidden="true"><img src="" alt=""></div>
<script src="assets/site.js" defer></script>'''
DIST.mkdir(exist_ok=True)
(DIST / 'index.html').write_text(page('Studio BEGA — Architecture & stratégie de lieu, Ardenne', index_body,
    "Studio BEGA lit les lieux avant de dessiner : communes, hôtellerie, promotion, maisons. Architecture et plans directeurs en Wallonie, à Bruxelles et au Luxembourg."))

# ---------- STUDIO ----------
studio = f'''<div class="page"><div class="wrap">
{nav('Studio')}    <p class="intro">BEGA est un studio d'architecture fondé à Hotton en 2025 par Benjamin Gaspard, architecte depuis 2013, avec Héloïse Collin, architecte d'intérieur. Il lit les lieux avant qu'on le lui demande : une place de village, un hôtel, une friche, une maison. Il dit ce qu'il y voit, et ce qui les ferait basculer. Certains deviennent des projets, en Wallonie, à Bruxelles et au Luxembourg.</p>

    <div class="blk st"><div class="lab">Lire</div><div class="txt"><p>Sur place, avant de dessiner. Le relief, l'eau, les murs, les passages, ce que les gens en font. Et ce que vous voulez en faire : le programme compte autant que le lieu.</p></div></div>
    <div class="blk st"><div class="lab">Imaginer</div><div class="txt"><p>Entre le lieu et le programme, il y a presque toujours une phrase qui fait basculer le projet. C'est la clé. À partir d'elle, le projet se dessine : un plan directeur, ou le projet lui-même, pour un espace public, un bâtiment, une maison. Le programme y trouve sa place.</p><p class="ex"><span class="key">Un musée commence à son parking. Une salle se retourne vers la rivière. Une grange devient une maison.</span></p></div></div>
    <div class="blk st"><div class="lab">Réaliser</div><div class="txt"><p>Le permis, le chantier, jusqu'au dernier détail. Transformer ce qui existe quand c'est possible, construire quand le terrain le demande.</p></div></div>

    <div class="blk">
      <div class="lab">Deux regards</div>
      <div class="duo">
        <img src="img/duo.jpg" alt="Benjamin Gaspard et Héloïse Collin">
        <div class="two">
          <div><h3>Benjamin Gaspard</h3><div class="lab">Architecte</div><p>Trouve la clé sur place. Lit les lieux depuis l'enfance, les dessine depuis 2013.</p></div>
          <div><h3>Héloïse Collin</h3><div class="lab">Architecte d'intérieur</div><p>Prolonge la clé à l'intérieur, jusqu'au dernier détail.</p></div>
        </div>
      </div>
    </div>
{FOOT}</div></div>'''
(DIST / 'studio.html').write_text(page('Studio — Studio BEGA', studio, "Benjamin Gaspard, architecte, et Héloïse Collin, architecte d'intérieur. Lire, imaginer, réaliser."))

# ---------- CONTACT ----------
contact = f'''<div class="page"><div class="wrap">
{nav('Contact')}    <div class="map">
      <img src="img/contact.jpg" alt="Hotton vu du ciel : l'Ourthe, le pont, et le studio rue Simon">
      <span class="pin" aria-hidden="true"></span>
    </div>
    <div class="addr"><a href="mailto:contact@studiobega.be">contact@studiobega.be</a><a href="tel:+32474634309">+32 474 63 43 09</a><div>Studio BEGA<br>Rue Simon 43<br>6990 Hotton, Belgique</div></div>
{FOOT}</div></div>'''
(DIST / 'contact.html').write_text(page('Contact — Studio BEGA', contact, 'Studio BEGA, rue Simon 43, 6990 Hotton. contact@studiobega.be · +32 474 63 43 09'))

# ---------- assets, redirections, favicon ----------
(DIST / 'assets').mkdir(exist_ok=True)
shutil.copy(ROOT / 'assets' / 'site.css', DIST / 'assets' / 'site.css')
shutil.copy(ROOT / 'assets' / 'site.js', DIST / 'assets' / 'site.js')
(DIST / 'favicon.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><rect width="32" height="32" fill="#141413"/><circle cx="16" cy="16" r="7" fill="#FFD400"/></svg>')

# anciennes adresses Adobe Portfolio → nouvelle fiche
redir = ['RewriteEngine On', 'RewriteCond %{HTTPS} off', 'RewriteRule ^ https://%{HTTP_HOST}%{REQUEST_URI} [L,R=301]',
         'ErrorDocument 404 /index.html', 'AddDefaultCharset UTF-8']
old = json.load(open(DATA / 'old_slugs.json')) if (DATA / 'old_slugs.json').exists() else {}
bycode = {p['code']: p['id'] for p in P}
for s, code in old.items():
    if code in bycode: redir.append(f'Redirect 301 {s} /index.html#{bycode[code]}')
redir.append('Redirect 301 /studio /studio.html'); redir.append('Redirect 301 /contact /contact.html')
(DIST / '.htaccess').write_text('\n'.join(redir) + '\n')

n_img = sum(1 for _ in IMG.rglob('*.jpg'))
print(f"ok — {len(P)} lieux, {n_img} images, dist/ = {sum(f.stat().st_size for f in DIST.rglob('*') if f.is_file())//1024} Ko")
