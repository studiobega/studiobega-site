#!/usr/bin/env python3
"""Génère le site statique studiobega.be depuis data/.

Entrées
  data/projets.json          lignes Airtable (Site ✓), champs normalisés
  data/photos_manifest.json  [{code,k,id,...}] ordre des photos par projet
  data/photos/<attId>.jpg    photos (max 1600 px) rapatriées d'Airtable
  data/mockup/*.jpg          hero, duo, carte de contact, images test plan directeur

Sortie
  dist/   index.html (accueil), territoires/ activites/ habitat/ (une page par porte),
          (chaque lieu s'ouvre en fiche dans sa porte, /porte/#id), contact.html ; le studio est sur l'accueil (/#studio), assets/, img/, .htaccess

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
PORTES = [('territoires', 'Territoires'), ('activites', 'Activités'), ('habitat', 'Habitat')]
PKEY = {n: k for k, n in PORTES}
# anciennes valeurs de « Site · Porte », au cas où une ligne n'a pas été rebasculée
PKEY.update({'Communes': 'territoires', 'Hôtellerie & commerces': 'activites', 'Promotion': 'habitat', 'Maisons': 'habitat'})

def slug(s):
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode()
    s = re.sub(r'[^a-zA-Z0-9]+', '-', s).strip('-').lower()
    return s or 'lieu'

def ph(s):  # placeholder du mockup → vide
    return '' if (not s or s.startswith('[')) else s

for p in P:
    p['id'] = slug(p['nom']) if ph(p['nom']) else slug(p['code'])
    p['pk'] = PKEY.get(p['porte'], 'territoires')
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

# ---------- gabarit ----------
FONTS = '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n<link href="https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;1,6..72,400&family=Jost:wght@400;500;600&display=swap" rel="stylesheet">'

FOOT = """    <footer class="foot">
      <div>© 2026 Studio Benjamin Gaspard SRL · TVA BE 0799.818.844</div>
      <div class="grp"><a href="https://www.instagram.com/studio_bega_/">Instagram</a><a href="https://www.facebook.com/studiobenjamingaspard">Facebook</a><a href="https://be.linkedin.com/company/studiobega">LinkedIn</a></div>
    </footer>
"""
MENU = [('/territoires/', 'Territoires'), ('/activites/', 'Activités'), ('/habitat/', 'Habitat'), ('/#studio', 'Studio'), ('/contact.html', 'Contact')]
LOGO = '<a class="logo" href="/#accueil" aria-label="Studio BEGA, accueil">BEGA<span class="dot" aria-hidden="true"></span></a>'

def nav(on):
    links = ''.join(f'<a href="{h}"{" class=\"on\"" if t == on else ""}>{t}</a>' for h, t in MENU)
    return f'    <nav class="nav" aria-label="Navigation">\n      {LOGO}\n      <div class="links">{links}</div>\n    </nav>\n'

def page(title, body, desc, img='/img/hero.jpg'):
    return f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}"><meta property="og:image" content="https://studiobega.be{img}"><meta property="og:type" content="website">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
{FONTS}
<link rel="stylesheet" href="/assets/site.css">
</head>
<body>
{body}
<script src="/assets/site.js" defer></script>
</body>
</html>
"""

def write(path, html_):
    f = DIST / path
    f.parent.mkdir(parents=True, exist_ok=True); f.write_text(html_)

DIST.mkdir(exist_ok=True)
PICS = {p['id']: photos_for(p) for p in P}
abs_ = lambda r: '/' + r

# ---------- les trois portes ----------
# Chaque porte : une phrase, quelques lignes qui posent la démarche pour ce public, puis la grille d'images.
DOORS = {
    'territoires': ("Un territoire se lit avant de se dessiner.",
                    "Une place, une rue, une rivière, un massif. Chaque territoire porte déjà sa logique : le relief, l'eau, les usages, ceux qui le traversent. BEGA la lit sur place, trouve la clé, et dessine à partir d'elle, du plan directeur à l'espace public."),
    'activites':   ("Un lieu d'activité vit de ce qu'il fait ressentir.",
                    "Un hôtel, un café, un commerce, un cinéma, un bureau. Le lieu porte le projet de celui qui l'exploite : ce qu'il veut offrir, à qui, et comment on y arrive. La clé réconcilie ce programme avec ce que le lieu sait déjà faire."),
    'habitat':     ("Habiter, c'est s'accorder à un lieu.",
                    "Une maison neuve, une ferme à rénover de fond en comble, des logements, un intérieur. Chaque projet part de ce qui est déjà là : le terrain, les murs, la vue, la lumière. La clé fait le lien entre ce qui existe et la façon dont on veut y vivre. Héloïse la prolonge à l'intérieur."),
}
NAMES = dict(PORTES)
bykey = {k: sorted([p for p in P if p['pk'] == k and ph(p['nom'])], key=lambda p: (p['ordre'] or 999, p['nom'])) for k, _ in PORTES}

def card(p):
    """Vignette : l'image, la clé en titre, puis le nom réel du lieu."""
    pics = PICS.get(p['id'])
    if not pics: return ''
    cle, nom = ph(p['cle']), ph(p['nom'])
    sub = ' · '.join(x for x in (nom if cle else '', ph(p['lieu'])) if x)
    return (f'      <a class="card" href="#{p["id"]}" data-open="{p["id"]}"><span class="im"><img src="{abs_(pics[0][2])}" alt="{e(nom)}" loading="lazy"></span>'
            f'<span class="cap"><span class="ck">{e(cle or nom)}</span><span class="cm">{e(sub)}</span></span></a>\n')

def fiche(p):
    """Contenu de la fiche qui s'ouvre dans la grille (caché jusqu'au clic)."""
    pics = PICS.get(p['id']) or []
    nom = ph(p['nom'])
    meta = ' · '.join(x for x in (ph(p['lieu']), p['type'], ph(p['annee']), ph(p['etat'])) if x)
    dem, cle, sorti, para = ph(p['dem']), ph(p['cle']), ph(p['sorti']), ph(p['para'])
    multi = '\n' in sorti
    sorti_h = ''.join(f'<span class="ln">{e(x.strip())}</span>' for x in sorti.split('\n') if x.strip()) if multi else e(sorti)
    dl = ''
    if dem:   dl += f'<div><dt class="lab">Demandé</dt><dd>{e(dem)}</dd></div>'
    if cle:   dl += f'<div><dt class="lab">La clé</dt><dd class="cle"><span class="key">{e(cle)}</span></dd></div>'
    if sorti: dl += f'<div><dt class="lab">{"Pistes" if multi else "Sorti"}</dt><dd>{sorti_h}</dd></div>'
    liens = [l.split('|', 1) for l in (p['liens'] or '').split('\n') if '|' in l]
    lk = ''.join(f'<a href="{u.strip()}">{e(t.strip())}</a>' for t, u in liens if u.strip() and u.strip() != '#')
    n = len(pics)
    wide = lambda j: j == 0 or (j == n - 1 and (n - 1) % 2 == 1)  # 1re pleine largeur, puis par deux, dernière impaire pleine largeur
    imgs = ''.join(f'<img{" class=\"w\"" if wide(j) else ""} src="{abs_(b)}" alt="{e(nom)}" loading="lazy" data-zoom="{abs_(b)}">' for j, (b, t, m) in enumerate(pics))
    return f"""    <template id="f-{p['id']}">
      <div class="fh"><div><h2 class="nm">{e(nom)}</h2><div class="meta">{e(meta)}</div></div><button type="button" class="fx-x">Fermer</button></div>
      <div class="fb"><div class="pics">{imgs}</div><div class="tx"><dl>{dl}</dl>{f'<p class="para">{e(para)}</p>' if para else ''}{f'<div class="links">{lk}</div>' if lk else ''}</div></div>
    </template>
"""

for k, n in PORTES:
    t, intro = DOORS[k]
    cards = ''.join(card(p) for p in bykey[k])
    fiches = ''.join(fiche(p) for p in bykey[k] if PICS.get(p['id']))
    body = f"""<div class="page"><div class="wrap">
{nav(n)}    <header class="ph-head"><h1 class="t1">{e(t)}</h1><p class="t3">{e(intro)}</p></header>
    <div class="grid">
{cards}    </div>
{fiches}{FOOT}</div></div>
<div class="lb" id="lb" aria-hidden="true"><img src="" alt=""></div>
<button type="button" class="fx" id="fx" aria-label="Fermer la fiche">Fermer</button>"""
    write(f'{k}/index.html', page(f'{n} — Studio BEGA', body, intro))

# ---------- images fixes ----------
for src, dst in [('7d27646bb9e84d280aaa51552a3d6afb', 'hero'), ('ec894847fb1cdd2dc482462924bcd351', 'duo'), ('18732aa0aa56be5aeb1bb35760702fa6', 'contact')]:
    s_ = DATA / 'mockup' / f'{src}.jpg'
    if s_.exists():
        save(Image.open(s_), IMG / f'{dst}.jpg', 2000 if dst == 'hero' else 1600, 84)

# ---------- accueil : la photo, puis BEGA se présente, puis les trois portes ----------
def first_pic(k, code=None):
    L = [p for p in bykey[k] if PICS.get(p['id'])]
    if code: L = [p for p in L if p['code'] == code] or L
    return abs_(PICS[L[0]['id']][0][2]) if L else '/img/hero.jpg'
tiles = ''.join(f"""      <a class="door" href="/{k}/"><span class="im"><img src="{first_pic(k, '23.14' if k == 'territoires' else None)}" alt="" loading="lazy"></span><span class="dn">{e(n)}</span><span class="dt">{e(DOORS[k][0])}</span></a>
""" for k, n in PORTES)
IDMAP = json.dumps({p['id']: p['pk'] for p in P}, ensure_ascii=False).replace('"', '&quot;')
hero_links = ''.join(f'<a href="{h}">{t}</a>' for h, t in MENU)
index_body = f"""<section class="hero" id="hero" data-map="{IDMAP}">
  <img class="bg" src="/img/hero.jpg" alt="Bouillon vu du ciel : l'esplanade, le château, la Semois">
  <div class="veil" aria-hidden="true"></div>
  <button type="button" class="go" id="enter" aria-label="Entrer"></button>
  <nav class="nav" aria-label="Navigation">{LOGO}<div class="links">{hero_links}</div></nav>
  <div class="txt">
    <h1>Tout est déjà là.</h1>
    <p>Lire un lieu. Imaginer sa clé. Le réaliser.</p>
  </div>
</section>
<div class="page site" id="site"><div class="wrap">
{nav('')}    <section class="studio" id="studio">
      <h2 class="t1">Revaloriser ce qui existe.<br>Construire quand le terrain le demande.</h2>
      <div class="essay">
        <p>Une maison, un gîte, un commerce, un lieu de travail, un espace public.<br>Studio BEGA accompagne les particuliers, les investisseurs, les entreprises et les communes, quand un lieu demande à être transformé, valorisé ou repensé.</p>
        <p>Un projet commence par une lecture.<br>Ce que le lieu permet. Ce qu'il impose. Ce qu'il peut devenir.<br>Et ce que vous voulez en faire.</p>
        <p>Entre les deux, il y a une clé : ce qui rend le lieu singulier.<br>Elle se trouve sur place, et le projet se dessine à partir d'elle, du territoire à l'intérieur.</p>
      </div>
      <div class="temps">
        <div><h3>Lire</h3><p>Sur place, avant de dessiner.</p></div>
        <div><h3>Imaginer</h3><p>Trouver la clé, puis dessiner le projet à partir d'elle.</p></div>
        <div><h3>Réaliser</h3><p>Le permis, le chantier, jusqu'au dernier détail.</p></div>
      </div>
      <figure class="duo">
        <img src="/img/duo.jpg" alt="Benjamin Gaspard et Héloïse Collin" loading="lazy">
        <div class="two">
          <div><h3>Benjamin Gaspard</h3><div class="lab">Architecte</div><p>Trouve la clé sur place.</p></div>
          <div><h3>Héloïse Collin</h3><div class="lab">Architecte d'intérieur</div><p>La prolonge à l'intérieur.</p></div>
        </div>
        <figcaption class="t3">Un studio d'architecture à Hotton, en Wallonie, à Bruxelles et au Luxembourg.<br>Des projets qui restent. Dans leur usage, dans le temps, dans ce qu'ils changent.</figcaption>
      </figure>
    </section>
    <section class="doors" aria-label="Les lieux">
{tiles}    </section>
{FOOT}</div></div>"""
write('index.html', page('Studio BEGA — Architecture & stratégie de lieu, Ardenne', index_body,
    "Studio BEGA lit les lieux avant de dessiner : territoires, lieux d'activité, habitat. Architecture et plans directeurs en Wallonie, à Bruxelles et au Luxembourg."))

# ---------- CONTACT ----------
contact = f"""<div class="page"><div class="wrap">
{nav('Contact')}    <h1 class="t1">Un lieu à imaginer.</h1>
    <p class="t3 ct-sub">Le studio est à Hotton, au bord de l'Ourthe. Les lieux, eux, sont partout.</p>
    <div class="map">
      <img src="/img/contact.jpg" alt="Hotton vu du ciel : l'Ourthe, le pont, et le studio rue Simon">
      <span class="pin" aria-hidden="true"></span>
    </div>
    <div class="addr"><a href="mailto:contact@studiobega.be">contact@studiobega.be</a><a href="tel:+32474634309">+32 474 63 43 09</a><div>Studio BEGA<br>Rue Simon 43<br>6990 Hotton, Belgique</div></div>
{FOOT}</div></div>"""
write('contact.html', page('Contact — Studio BEGA', contact, 'Studio BEGA, rue Simon 43, 6990 Hotton. contact@studiobega.be · +32 474 63 43 09'))

# ---------- assets, redirections, favicon ----------
(DIST / 'assets').mkdir(exist_ok=True)
shutil.copy(ROOT / 'assets' / 'site.css', DIST / 'assets' / 'site.css')
shutil.copy(ROOT / 'assets' / 'site.js', DIST / 'assets' / 'site.js')
(DIST / 'favicon.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><rect width="32" height="32" fill="#141413"/><circle cx="16" cy="16" r="7" fill="#FFD400"/></svg>')

# anciennes adresses Adobe Portfolio → fiche dans sa porte. RewriteRule [NE] : le « # » de l'ancre passe tel quel
# (Redirect/RedirectMatch l'encoderaient en %23). Correspondance exacte, sans quoi /studio attraperait /studio.html.
redir = ['RewriteEngine On', 'RewriteCond %{HTTPS} off', 'RewriteRule ^ https://%{HTTP_HOST}%{REQUEST_URI} [L,R=301]',
         'ErrorDocument 404 /index.html', 'AddDefaultCharset UTF-8']
R = lambda src, dst: redir.append(f'RewriteRule ^{src}/?$ {dst} [R=301,L,NE]')
old = json.load(open(DATA / 'old_slugs.json')) if (DATA / 'old_slugs.json').exists() else {}
bycode = {p['code']: f"/{p['pk']}/#{p['id']}" for p in P}
for s_, code in old.items():
    if code in bycode: R(re.escape(s_.lstrip('/')), bycode[code])
R(r'studio(\.html)?', '/#studio'); R('contact', '/contact.html'); R('accueil', '/')
R('sites', '/territoires/'); R('maisons', '/habitat/')
(DIST / '.htaccess').write_text('\n'.join(redir) + '\n')

n_img = sum(1 for _ in IMG.rglob('*.jpg'))
print(f"ok — {len(P)} lieux, {n_img} images, dist/ = {sum(f.stat().st_size for f in DIST.rglob('*') if f.is_file())//1024} Ko")
