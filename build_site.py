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

# Schémas dont le jaune est ramené au jaune BEGA (#FFD400), id de pièce jointe Airtable.
RECOLOR = {'att0sJfbGVF6vDiiV'}
def bega_yellow(im):
    """Remplace un jaune terne par #FFD400 en gardant l'anticrénelage (mélange avec le blanc)."""
    im = im.convert('RGB'); px = im.load(); w, h = im.size
    for y in range(h):
        for x in range(w):
            r, g, b = px[x, y]
            a = (min(r, g) - b) / 152
            if a <= 0.04: continue
            a = min(a, 1.0)
            px[x, y] = (min(255, round(r + 31 * a)), min(255, round(g + 4 * a)), max(0, round(b - 56 * a)))
    return im

def photos_for(p):
    """→ liste de (grande 1600, vignette 480, moyenne 900) en chemins relatifs dist/."""
    out = []
    mine = sorted([m for m in MAN if m['code'] == p['code']], key=lambda m: m['k'])
    srcs = [(DATA / 'photos' / f"{m['id']}.jpg") for m in mine]
    srcs = [s for s in srcs if s.exists()]
    if not srcs:
        srcs = [DATA / 'mockup' / f'{b}.jpg' for b in FALLBACK.get(p['code'], []) if (DATA / 'mockup' / f'{b}.jpg').exists()]
    for k, src in enumerate(srcs):
        big, th, mid = (IMG / p['id'] / f'{k+1}{x}.jpg' for x in ('', '-t', '-m'))
        if not (big.exists() and mid.exists()) or big.stat().st_mtime < src.stat().st_mtime or src.stem in RECOLOR:
            im = Image.open(src)
            if src.stem in RECOLOR: im = bega_yellow(im)
            save(im, big, 1600); save(im, th, 480, 78); save(im, mid, 900, 80)
        r = f"img/{p['id']}/{k+1}"
        out.append((r + '.jpg', r + '-t.jpg', r + '-m.jpg'))
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
    links = ''.join(f'<a href="{href}"{" class=\"on\"" if t == on else ""}>{t}</a>' for href, t in [('index.html', 'Lieux'), ('studio.html', 'Studio'), ('contact.html', 'Contact')])
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
PICS = {}
def row(p):
    pics = PICS[p['id']] = photos_for(p)
    thumb = f'<img class="th" src="{pics[0][1]}" alt="" loading="lazy">' if pics else '<span class="th" aria-hidden="true"></span>'
    nom = ph(p['nom']) or '[Nom du lieu]'
    lieu, typ, an, etat = ph(p['lieu']), p['type'], ph(p['annee']), ph(p['etat'])
    dem, cle, sorti, para = ph(p['dem']), ph(p['cle']), ph(p['sorti']), ph(p['para'])
    # 1re photo pleine largeur, les suivantes par deux ; si elles sont en nombre impair, la dernière repasse pleine largeur
    n = len(pics)
    wide = lambda k: k == 0 or (k == n - 1 and (n - 1) % 2 == 1)
    picsh = ''.join(f'<img{" class=\"w\"" if wide(k) else ""} src="{b}" alt="{e(nom)}" loading="lazy" data-zoom="{b}">' for k, (b, t, m) in enumerate(pics)) if pics else '<span class="ph w" aria-hidden="true"></span>'
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

def card(p):
    """Vignette : l'image, la clé en grand, puis nom · lieu."""
    pics = PICS.get(p['id'])
    if not pics or not ph(p['nom']): return ''
    meta = ' · '.join(x for x in (ph(p['nom']), ph(p['lieu'])) if x)
    head = f'<span class="ck">{e(ph(p["cle"]))}</span>' if ph(p['cle']) else f'<span class="ck nk">{e(ph(p["nom"]))}</span>'
    return (f'      <a class="card" href="#{p["id"]}" data-open="{p["id"]}"><span class="im"><img src="{pics[0][2]}" alt="" loading="lazy"></span>'
            f'{head}<span class="cm">{e(meta)}</span></a>\n')

bykey = {k: sorted([p for p in P if p['pk'] == k and ph(p['nom'])], key=lambda p: (p['ordre'] or 999, p['nom'])) for k, _ in PORTES}
doors = ''.join(f'<a href="#{k}">{e(n)}<span class="n">{len(bykey[k])}</span></a>' for k, n in PORTES)
views = '<div class="views" role="group" aria-label="Affichage"><button type="button" data-v="img" aria-pressed="true">Images</button><button type="button" data-v="list" aria-pressed="false">Liste</button></div>'
lieux = f'''    <p class="lead" id="lieux">Chaque lieu a sa clé.</p>
    <header class="lieux-head"><div class="doors">{doors}</div>{views}</header>
'''
for k, n in PORTES:
    rows_h = ''.join(row(p) for p in bykey[k])
    cards_h = ''.join(card(p) for p in bykey[k])
    lieux += (f'    <h2 class="lab sec" id="{k}">{e(n)}</h2>\n'
              f'    <div class="grid">\n{cards_h}    </div>\n'
              f'    <div class="lst">\n{rows_h}    </div>\n')

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
<div class="site locked v-img" id="site"><div class="page"><div class="wrap">
{nav('Lieux', home_btn=True)}{lieux}{FOOT}</div></div></div>
<div class="lb" id="lb" aria-hidden="true"><img src="" alt=""></div>
<button type="button" class="fx" id="fx" aria-label="Fermer la fiche">Fermer</button>
<script src="assets/site.js" defer></script>'''
DIST.mkdir(exist_ok=True)
(DIST / 'index.html').write_text(page('Studio BEGA — Architecture & stratégie de lieu, Ardenne', index_body,
    "Studio BEGA lit les lieux avant de dessiner : communes, hôtellerie, promotion, maisons. Architecture et plans directeurs en Wallonie, à Bruxelles et au Luxembourg."))

# ---------- STUDIO ----------
# Une position, puis la démonstration sur un lieu (Bouillon), puis les échelles, puis les deux regards.
FIL_CODE = '23.14'
FIL_SRC = [('lire', 'Lire', 'attRCS6nTI0fJ9dtW', "Sur place, avant de dessiner : le relief, l'eau, les passages, ce que les gens en font. Et le programme, qui compte autant que le lieu."),
           ('imaginer', 'Imaginer', 'att0sJfbGVF6vDiiV', None),
           ('realiser', 'Réaliser', 'attN9EId6PPtfGRFu', "Le permis, le chantier, jusqu'au dernier détail. Transformer ce qui existe, construire quand le terrain le demande.")]
# Échelles : (libellé, code projet) — liens vers des lieux, sans leurs clés.
ECHELLES = [('Maison', '25.24'), ('Bâtiment', '26.51'), ('Plan directeur', 'REF.01'), ('Territoire', 'REF.02')]
BYCODE = {p['code']: p for p in P}
fp = BYCODE.get(FIL_CODE)
mine = sorted([m for m in MAN if m['code'] == FIL_CODE], key=lambda m: m['k'])
fpics = PICS.get(fp['id']) if fp else None
fcle = ph(fp['cle']) if fp else ''
steps = ''
for cls, lab, aid, txt in FIL_SRC:
    ks = [i for i, m in enumerate(mine) if m['id'] == aid]
    img = f'<img src="{fpics[ks[0]][2]}" alt="" loading="lazy">' if (fpics and ks and ks[0] < len(fpics)) else '<span class="ph"></span>'
    body = f'<span><span class="key">{e(fcle)}</span></span>' if txt is None else f'<span>{e(txt)}</span>'
    steps += f'      <figure class="step {cls}">{img}<figcaption><span class="lab">{lab}</span>{body}</figcaption></figure>\n'
fil_link = f' · <a href="index.html#{fp["id"]}">{e(ph(fp["nom"]))}, {e(ph(fp["lieu"]))}</a>' if fp else ''
ech = ''
for lab, c in ECHELLES:
    q = BYCODE.get(c)
    if q: ech += f'<a href="index.html#{q["id"]}"><span class="lab">{lab}</span><span class="en">{e(ph(q["nom"]))}</span><span class="el">{e(ph(q["lieu"]))}</span></a>'
studio = f'''<div class="page"><div class="wrap">
{nav('Studio')}    <h1 class="manif">Revaloriser ce qui existe. Construire quand le terrain le demande.</h1>
    <div class="essay">
      <p>Une place de village, un hôtel, une ferme, une maison, un site entier. Chaque lieu a déjà tout : le relief, l'eau, les murs, ce que les gens en font, et l'envie de celui qui porte le projet.</p>
      <p>Dans chaque lieu, il y a une clé. C'est ce qui le rend singulier, ce qui réconcilie ce que le lieu peut donner et ce que vous voulez en faire. Elle se trouve sur place. Le projet se dessine à partir d'elle.</p>
      <p>Demain, on construira moins et on revalorisera ce qui existe. BEGA y travaille de la maison au territoire, en Wallonie, à Bruxelles et au Luxembourg.</p>
      <p>BEGA est un studio d'architecture installé à Hotton, porté par Benjamin Gaspard, architecte, et Héloïse Collin, architecte d'intérieur.</p>
    </div>

    <section class="temps">
      <div><h2>Lire</h2><p>Sur place, avant de dessiner.</p></div>
      <div><h2>Imaginer</h2><p>Trouver la clé, puis dessiner le projet à partir d'elle.</p></div>
      <div><h2>Réaliser</h2><p>Le permis, le chantier, jusqu'au dernier détail.</p></div>
    </section>

    <figure class="duo-f">
      <img src="img/duo.jpg" alt="Benjamin Gaspard et Héloïse Collin">
      <div class="two">
        <div><h3>Benjamin Gaspard</h3><div class="lab">Architecte</div><p>Trouve la clé sur place.</p></div>
        <div><h3>Héloïse Collin</h3><div class="lab">Architecte d'intérieur</div><p>La prolonge à l'intérieur.</p></div>
      </div>
    </figure>
{FOOT}</div></div>
<script src="assets/site.js" defer></script>'''
(DIST / 'studio.html').write_text(page('Studio — Studio BEGA', studio, "Benjamin Gaspard, architecte, et Héloïse Collin, architecte d'intérieur. Lire, imaginer, réaliser."))

# ---------- CONTACT ----------
contact = f'''<div class="page"><div class="wrap">
{nav('Contact')}    <h1 class="manif">Un lieu à imaginer.</h1>
    <p class="ct-sub">Le studio est à Hotton, au bord de l'Ourthe. Les lieux, eux, sont partout.</p>
    <div class="map">
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
