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
import json, html, os, re, shutil, unicodedata, hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / 'data'
DIST = Path(os.environ.get('OUT') or ROOT / 'dist')
# V2=1 : la refonte (accueil en trois portes, page Studio avec la carte), construite à part pour l'aperçu /apercu/
V2 = os.environ.get('V2') == '1'
BASE = os.environ.get('BASE', '')
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
FONTS = '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n<link href="https://fonts.googleapis.com/css2?family=Jost:ital,wght@0,400;0,500;0,600;0,700;1,400;1,500&family=Newsreader:ital,opsz,wght@1,6..72,400&display=swap" rel="stylesheet">'

FOOT = """    <footer class="foot">
      <div class="grp"><a href="https://www.instagram.com/studio_bega_/">Instagram</a><a href="https://www.facebook.com/studiobenjamingaspard">Facebook</a><a href="https://be.linkedin.com/company/studiobega">LinkedIn</a></div>
      <div>Studio BEGA, architectes · Rue Simon 43, 6990 Hotton, Belgique · © Studio Benjamin Gaspard SRL · TVA BE 0799.818.844</div>
    </footer>
"""
MENU = ([('/#projets', 'Projets'), ('/studio/', 'Studio')] if V2 else
        [('/territoires/', 'Territoires'), ('/activites/', 'Activités'), ('/habitat/', 'Habitat'), ('/contact.html', 'Contact')])
CT = ('Contact', 'Studio')
LOGO = '<a class="logo" href="/#accueil" aria-label="Studio BEGA, accueil">BEGA<span class="dot" aria-hidden="true"></span></a>'

# téléphone : les trois petites barres ouvrent le menu plein écran, comme l'ancien site
BURGER = '<button type="button" class="burger" aria-label="Menu" aria-expanded="false"><span></span><span></span><span></span></button>'
def mobile_menu():
    items = ''.join(f'<a href="{h}"{" class=\"ct\"" if t in CT else ""}>{t}</a>' for h, t in ([] if V2 else [('/#accueil', 'Accueil')]) + MENU)
    return f'<div class="mnav" id="mnav" aria-hidden="true"><button type="button" class="mnav-x" aria-label="Fermer le menu">×</button><nav>{items}</nav></div>'

def nav(on):
    links = ''.join(f'<a href="{h}" class="{"on " if t == on else ""}{"ct" if t in CT else ""}">{t}</a>' for h, t in MENU)
    return f'    <nav class="nav" aria-label="Navigation">\n      {LOGO}\n      <div class="links">{links}</div>\n      {BURGER}\n    </nav>\n'

# version des feuilles : change dès que le CSS ou le JS change, les navigateurs reprennent alors la nouvelle version
VER = hashlib.sha1(b''.join((ROOT / 'assets' / x).read_bytes() for x in ('site.css', 'site.js'))).hexdigest()[:8]

def page(title, body, desc, img='/img/hero.jpg', canon=None, ld=''):
    return f"""<!doctype html>
<html lang="fr"{f' data-base="{BASE}"' if BASE else ''}>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light">
<meta name="theme-color" content="#ffffff">{'<meta name="robots" content="noindex, nofollow">' if BASE else ''}
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}"><meta property="og:image" content="https://studiobega.be{img.split('?')[0]}"><meta property="og:type" content="website"><meta property="og:site_name" content="Studio BEGA"><meta property="og:locale" content="fr_BE">{f'<link rel="canonical" href="https://studiobega.be{canon}">' if canon and not BASE else ''}
<link rel="icon" href="/favicon.png" type="image/png"><link rel="apple-touch-icon" href="/apple-touch-icon.png">
{FONTS}
<link rel="stylesheet" href="/assets/site.css?v={VER}">{ld}
</head>
<body>
{body}
{mobile_menu()}
<script src="/assets/site.js?v={VER}" defer></script>
</body>
</html>
"""

def write(path, html_):
    f = DIST / path
    f.parent.mkdir(parents=True, exist_ok=True); f.write_text(html_)

DIST.mkdir(exist_ok=True)
PICS = {p['id']: photos_for(p) for p in P}
def abs_(r):
    """chemin absolu + empreinte du contenu (?v=…) : une photo remplacée change d'URL, le navigateur ne garde pas l'ancienne."""
    f = DIST / r
    return '/' + r + (f"?v={hashlib.sha1(f.read_bytes()).hexdigest()[:8]}" if f.exists() else '')

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
if V2:   # textes de secteur resserrés : ils s'affichent sur l'accueil quand on filtre, et en tête de chaque galerie
    DOORS = {
        'territoires': ("Un territoire se lit avant de se dessiner.",
                        "Une place, une rue, une rivière, un massif. Le relief, l'eau, les usages et ceux qui le traversent donnent au lieu sa logique. Du plan directeur à l'espace public, tout se dessine à partir de sa clé."),
        'activites':   ("Un lieu d'activité vit de ce qu'il fait ressentir.",
                        "Un hôtel, un café, un commerce, un cinéma, un bureau. La clé réconcilie ce que l'exploitant veut offrir avec ce que le lieu sait déjà faire."),
        'habitat':     ("Habiter, c'est s'accorder à un lieu.",
                        "Une maison neuve, une ferme à rénover, des logements, un intérieur. Tout part de ce qui est là : le terrain, les murs, la vue, la lumière. Héloïse prolonge la clé à l'intérieur."),
    }
NAMES = dict(PORTES)
bykey = {k: sorted([p for p in P if p['pk'] == k and ph(p['nom'])], key=lambda p: (p['ordre'] or 999, p['nom'])) for k, _ in PORTES}

def card(p):
    """Vignette : l'image, le nom, puis la fonction et le lieu. La clé se lit dans la fiche."""
    pics = PICS.get(p['id'])
    if not pics: return ''
    cle, nom = ph(p['cle']), ph(p['nom'])
    # dessous : deux mots, la fonction et le lieu ; la clé parle
    typ = (p['type'] or '').strip()
    sub = ' · '.join(x for x in ((typ[:1].upper() + typ[1:]) if typ else '', ph(p['lieu'])) if x)
    return (f'      <a class="card" href="#{p["id"]}" data-open="{p["id"]}"><span class="im"><img src="{abs_(pics[0][2])}" alt="{e(nom)}" loading="lazy"></span>'
            f'<span class="cap"><span class="nm">{e(nom)}</span><span class="cm">{e(sub)}</span></span></a>\n')

def fiche(p):
    """Contenu de la fiche qui s'ouvre dans la grille (caché jusqu'au clic)."""
    pics = PICS.get(p['id']) or []
    nom = ph(p['nom'])
    meta = ' · '.join(x for x in (ph(p['lieu']), p['type'], ph(p['annee']), ph(p['etat'])) if x)
    dem, cle, sorti, para = ph(p['dem']), ph(p['cle']), ph(p['sorti']), ph(p['para'])
    multi = '\n' in sorti
    sorti_h = ''.join(f'<span class="ln">{e(x.strip())}</span>' for x in sorti.split('\n') if x.strip()) if multi else e(sorti)
    dl = ''
    if dem:   dl += f'<div><dt class="lab">Demandé</dt><dd class="v">{e(dem)}</dd></div>'
    if sorti: dl += f'<div><dt class="lab">{"Pistes" if multi else "Sorti"}</dt><dd class="v">{sorti_h}</dd></div>'
    liens = [l.split('|', 1) for l in (p['liens'] or '').split('\n') if '|' in l]
    lk = ''.join(f'<a href="{u.strip()}">{e(t.strip())}</a>' for t, u in liens if u.strip() and u.strip() != '#')
    n = len(pics)
    wide = lambda j: j == 0 or (j == n - 1 and (n - 1) % 2 == 1)  # 1re pleine largeur, puis par deux, dernière impaire pleine largeur
    imgs = ''.join(f'<img src="{abs_(b)}" alt="{e(nom)}" loading="lazy" data-zoom="{abs_(b)}">' for j, (b, t, m) in enumerate(pics))
    f1 = f'<figure class="f1"><img src="{abs_(pics[0][0])}" alt="{e(nom)}" data-zoom="{abs_(pics[0][0])}"></figure>' if pics else ''
    return f"""    <template id="f-{p['id']}">
      {f1}<div class="fh"><div><h2 class="nm">{e(nom)}</h2><div class="meta">{e(meta)}</div></div><button type="button" class="fx-x" aria-label="Fermer">×</button></div>
      {f'<p class="fcle"><span class="key">{e(cle)}</span></p>' if cle else ''}
      <div class="tx{' two' if para else ''}">{f'<dl>{dl}</dl>' if dl else ''}{f'<div class="det"><div class="lab">En détail</div><p class="para">{e(para)}</p>{f'<div class="links">{lk}</div>' if lk else ''}</div>' if para else (f'<div class="links">{lk}</div>' if lk else '')}</div>
      <div class="pics">{imgs}</div>
    </template>
"""

for k, n in PORTES:
    t, intro = DOORS[k]
    cards = ''.join(card(p) for p in bykey[k])
    fiches = ''.join(fiche(p) for p in bykey[k] if PICS.get(p['id']))
    body = f"""<div class="page"><div class="wrap">
{nav(n)}    <header class="col"><h1 class="h">{e(t)}</h1><p>{e(intro)}</p></header>
    <div class="grid">
{cards}    </div>
{fiches}{FOOT}</div></div>
<div class="modal" id="modal" aria-hidden="true"><div class="mbox" role="dialog" aria-modal="true"></div></div>
<div class="lb" id="lb" aria-hidden="true"><button type="button" class="lb-p" aria-label="Image précédente">‹</button><img src="" alt=""><button type="button" class="lb-n" aria-label="Image suivante">›</button><span class="lb-c"></span></div>"""
    write(f'{k}/index.html', page(f'{n} — Studio BEGA', body, intro, canon=f'/{k}/'))

# ---------- images fixes ----------
for src, dst in [('7d27646bb9e84d280aaa51552a3d6afb', 'hero'), ('ec894847fb1cdd2dc482462924bcd351', 'duo'), ('18732aa0aa56be5aeb1bb35760702fa6', 'contact')]:
    s_ = DATA / 'mockup' / f'{src}.jpg'
    if s_.exists():
        save(Image.open(s_), IMG / f'{dst}.jpg', 2000 if dst == 'hero' else 1600, 84)

# ---------- accueil : le rideau, puis le discours en colonne, comme l'ancien site ----------
def pic(code, k=0):
    q = next((p for p in P if p['code'] == code and PICS.get(p['id'])), None)
    return abs_(PICS[q['id']][min(k, len(PICS[q['id']]) - 1)][0]) if q else ''
def lines(*xs): return ''.join(f'<p>{e(x)}</p>' for x in xs)
IMG_COL = pic('REF.04')
# le schéma de l'ancien accueil (lire → la clé → le projet), gardé tel quel
shutil.copy(DATA / 'adobe' / 'schema-lire.png', IMG / 'schema-lire.png'); IMG_BANDEAU = '/img/schema-lire.png'
# « lire un lieu » : Benjamin sur place, la photo entière, en grand
_l1 = Image.open(DATA / 'accueil' / 'lire-1.jpg'); _l1 = _l1.crop((0, int(_l1.height * .30), _l1.width, _l1.height))  # ciel blanc rogné : il se fondait dans la page
save(_l1, IMG / 'lire-1.jpg', 2000, 84)
IDMAP = json.dumps({p['id']: p['pk'] for p in P}, ensure_ascii=False).replace('"', '&quot;')
def first_pic(k, code=None):
    L = [q for q in bykey[k] if PICS.get(q['id'])]
    if code: L = [q for q in L if q['code'] == code] or L
    return abs_(PICS[L[0]['id']][0][2]) if L else '/img/hero.jpg'
# une seule vraie clé sur l'accueil : Bouillon, lue dans Airtable, lien vers sa fiche
_ex = next((p for p in P if p['code'] == '23.14' and ph(p['cle'])), None)
EX = (f'<a class="ex" href="/{_ex["pk"]}/#{_ex["id"]}"><span class="exk"><span class="key">{e(ph(_ex["cle"]))}</span></span>'
      f'<span class="cm">{e(ph(_ex["nom"]))} · {e(ph(_ex["lieu"]))}</span></a>') if _ex else ''
portes = ''.join(f'<a class="door" href="/{k}/"><span class="im"><img src="{first_pic(k, "23.14" if k == "territoires" else None)}" alt="" loading="lazy"></span><span class="dn">{e(n)} <span class="ar" aria-hidden="true">→</span></span><span class="dt">{e(DOORS[k][0])}</span></a>' for k, n in PORTES)
index_body = f"""<section class="hero" id="hero" data-map="{IDMAP}">
  <img class="bg" src="/img/hero.jpg" alt="Bouillon vu du ciel : l'esplanade, le château, la Semois">
  <div class="veil" aria-hidden="true"></div>
  <button type="button" class="go" id="enter" aria-label="Entrer"></button>
  <nav class="nav" aria-label="Studio BEGA">{LOGO}</nav>
  <div class="txt"><h1>Tout est déjà là.</h1><p>Lire un lieu. Imaginer sa clé. Le réaliser.</p></div>
</section>
<div class="page site" id="site"><div class="wrap">
{nav('')}    <div class="col">
      <section><h2 class="h">Des lieux singuliers.</h2>{lines("Une place, un hôtel, une ferme, une maison.", "Chacun a déjà ce qu'il faut pour devenir unique.")}</section>
      <img class="wide" src="/img/lire-1.jpg" alt="Benjamin Gaspard sur place, face au paysage" loading="lazy">
      <section><h2 class="h">Un projet commence par une lecture.</h2>{lines("Ce que le lieu permet.", "Ce qu'il impose.", "Ce qu'il peut devenir.", "Et ce que vous voulez en faire.")}</section>
      <section><h2 class="h">Puis vient la clé.</h2>{lines("Ce qui rend le lieu singulier.", "Elle se trouve sur place, entre le lieu et votre projet.")}{EX}</section>
      <section><h2 class="h">Et le lieu se transforme.</h2>{lines("D'une vallée entière à une seule pièce.", "Dessiné à partir de la clé, construit jusqu'au dernier détail.")}</section>
      <img class="band" src="{IMG_BANDEAU}" alt="Lire le lieu, trouver la clé, faire le projet" loading="lazy">
      <section><h2 class="h">Des projets qui restent.</h2>{lines("Dans leur usage.", "Dans le temps.", "Dans ce qu'ils changent.")}<div class="doors">{portes}</div></section>
      <section id="studio"><h2 class="h">Le Studio.</h2>{lines("Architecture & stratégie de lieu.", "Benjamin Gaspard, architecte, trouve la clé sur place.", "Héloïse Collin, architecte d'intérieur, la prolonge à l'intérieur.", "Revaloriser ce qui existe. Construire quand le terrain le demande.", "Installé à Hotton. Projets en Wallonie, à Bruxelles et au Luxembourg.")}</section>
      <img class="ill" src="/img/duo.jpg" alt="Benjamin Gaspard et Héloïse Collin" loading="lazy">
    </div>
{FOOT}</div></div>"""
write('index.html', page('Studio BEGA — Architecture & stratégie de lieu, Ardenne', index_body,
    "Studio BEGA lit les lieux avant de dessiner : territoires, lieux d'activité, habitat. Architecture et plans directeurs en Wallonie, à Bruxelles et au Luxembourg."))

# ---------- CONTACT ----------
contact = f"""<div class="page"><div class="wrap">
{nav('Contact')}    <header class="col"><h1 class="h">Un lieu à imaginer.</h1><p>Le studio est à Hotton, au bord de l'Ourthe. Les lieux, eux, sont partout.</p></header>
    <div class="map">
      <img src="/img/contact.jpg" alt="Hotton vu du ciel : l'Ourthe, le pont, et le studio rue Simon">
      <span class="pin" aria-hidden="true"></span>
    </div>
    <dl class="addr">
      <div><span class="k">Mail</span><span class="v"><a href="mailto:contact@studiobega.be">contact@studiobega.be</a></span></div>
      <div><span class="k">Téléphone</span><span class="v"><a href="tel:+32474634309">+32 474 63 43 09</a></span></div>
      <div><span class="k">Studio</span><span class="v">Rue Simon 43<br>6990 Hotton, Belgique</span></div>
    </dl>
{FOOT}</div></div>"""
write('contact.html', page('Contact — Studio BEGA', contact, 'Studio BEGA, rue Simon 43, 6990 Hotton. contact@studiobega.be · +32 474 63 43 09'))

# ---------- V2 : la refonte (aperçu) ----------
# Accueil : le rideau, puis une porte par type de projet (un lieu la représente, avec sa clé).
# Studio : qui, la méthode, le duo, la carte des lieux, les coordonnées. Contact y est fondu.
if V2:
    import sys; sys.path.insert(0, str(ROOT)); import carte

    # Accueil = Projets (modèle OFFICE KGDVS / Carmody Groarke) : filtres en mots (Tout · portes), vues Images · Liste · Carte.
    # Images : défilé rythmé 1 · 2 · 3, la clé en phrase sous chaque projet. Le filtre affiche le texte du secteur.
    # Ordre : la vue Airtable « Site · Tous » (glisser une ligne = la déplacer dans « Tous ») ; dans chaque porte, la vue « Site ». Un clic ouvre la fiche dans sa galerie.
    from itertools import zip_longest
    rows = [[q for q in bykey[k] if PICS.get(q['id'])] for k, _ in PORTES]
    tous = [q for trio in zip_longest(*rows) for q in trio if q]
    # l'ordre de la vue Airtable « Site · Tous » quand il existe ; une ligne absente garde sa place à tour de rôle, en fin de liste
    tous = sorted(tous, key=lambda q: q.get('tous') or 9999)
    def tile(q, big):
        cle = ph(q['cle']); B, M = abs_(PICS[q['id']][0][0]), abs_(PICS[q['id']][0][2])
        return (f'<a class="sq" data-k="{q["pk"]}" data-open="{q["id"]}" href="/{q["pk"]}/#{q["id"]}"><span class="im"><img src="{B if big else M}" data-b="{B}" data-m="{M}" alt="{e(ph(q["nom"]))}, {e(ph(q["lieu"]))}" loading="lazy"></span>'
                f'{f"<span class=\"ck\">{e(cle)}</span>" if cle else ""}<span class="cm">{e(ph(q["nom"]))} · {e(ph(q["lieu"]))}</span></a>')
    seq, i, n = [], 0, 0
    while i < len(tous):
        size = (1, 2, 3)[n % 3]; grp = tous[i:i + size]; i += size; n += 1
        seq.append(f'<div class="rw r{len(grp)}">' + ''.join(tile(q, len(grp) == 1) for q in grp) + '</div>')
    flt = f'<button type="button" class="on" data-f="">Tous<sup>{len(tous)}</sup></button>' + ''.join(
        f'<button type="button" data-f="{k}">{e(n)}<sup>{len(r)}</sup></button>' for (k, n), r in zip(PORTES, rows))
    vws = '<button type="button" class="on" data-v="img">Images</button><button type="button" data-v="list">Liste</button><button type="button" data-v="map">Carte</button>'
    TOUT = ("Des lieux singuliers, à toutes les échelles.",
            "Une vallée, une place, un musée, un café, une maison, une pièce. Chaque projet part de ce qui est déjà là et se dessine à partir de sa clé.")
    intros = f'<div class="sec" data-for=""><p class="sp">{e(TOUT[0])}</p><p>{e(TOUT[1])}</p></div>' + ''.join(
        f'<div class="sec" data-for="{k}" hidden><p class="sp">{e(DOORS[k][0])}</p><p>{e(DOORS[k][1])}</p></div>' for k, _ in PORTES)
    # Liste : en-têtes cliquables (petite flèche à droite de chaque colonne), tri alphabétique par nom par défaut
    import unicodedata
    _k = lambda t: unicodedata.normalize('NFD', ph(t)).encode('ascii', 'ignore').decode().lower()
    lhd = '<div class="lh">' + ''.join(f'<button type="button" data-c="{c}"{" class=\"on\"" if c == 0 else ""}>{t}<span class="ar" aria-hidden="true"></span></button>'
                                     for c, t in enumerate(('Projet', 'Lieu', 'Type', 'Année'))) + '</div>'
    lst = lhd + ''.join(f'<a class="li" data-k="{q["pk"]}" data-open="{q["id"]}" href="/{q["pk"]}/#{q["id"]}"><span class="ln">{e(ph(q["nom"]))}</span><span>{e(ph(q["lieu"]))}</span>'
                  f'<span>{e(NAMES[q["pk"]])}</span><span>{e(ph(q["annee"]))}</span></a>' for q in sorted(tous, key=lambda q: _k(q['nom'])))
    # la carte : chaque lieu porte son identifiant, sa vignette et sa porte (le clic ouvre une carte de visite du lieu, puis sa fiche)
    CARTE, _inc = carte.build([q for q in tous if ph(q['lieu'])], lambda q: f"{q['id']}~{abs_(PICS[q['id']][0][1])}~{q['pk']}", DATA / 'carte' / 'fond.json')
    if _inc: print('carte : lieux sans coordonnées →', sorted(set(_inc)))
    CARTE = re.sub(r'<section class="lieux">.*?</section>', '', CARTE)
    moments = (f'<section class="pj" id="projets"><div class="bar"><div class="flt">{flt}</div><div class="vws">{vws}</div></div>{intros}'
               f'<div class="v" data-v="img"><div class="flow">{"".join(seq)}</div></div>'
               f'<div class="v" data-v="list" hidden><div class="lst">{lst}</div></div>'
               f'<div class="v" data-v="map" hidden>{CARTE}</div></section>\n'
               + ''.join(fiche(q) for q in tous) +
               '<div class="modal" id="modal" aria-hidden="true"><div class="mbox" role="dialog" aria-modal="true"></div></div>'
               '<div class="lb" id="lb" aria-hidden="true"><button type="button" class="lb-p" aria-label="Image précédente">‹</button><img src="" alt=""><button type="button" class="lb-n" aria-label="Image suivante">›</button><span class="lb-c"></span></div>\n')
    index2 = f"""<section class="hero" id="hero" data-map="{IDMAP}">
  <img class="bg" src="/img/hero.jpg" alt="Bouillon vu du ciel : l'esplanade, le château, la Semois">
  <div class="veil" aria-hidden="true"></div>
  <button type="button" class="go" id="enter" aria-label="Entrer"></button>
  <nav class="nav" aria-label="Studio BEGA">{LOGO}</nav>
  <div class="txt"><h1>Tout est déjà là.</h1><p>Lire un lieu. Imaginer sa clé. Le réaliser.</p></div>
</section>
<div class="page site" id="site"><div class="wrap">
{nav('Projets')}{moments}
{FOOT}</div></div>"""
    # fiche d'entreprise lue par Google (adresse, téléphone, zone) : sur l'accueil et sur Studio
    LD = '<script type="application/ld+json">' + json.dumps([{
        "@context": "https://schema.org", "@type": "WebSite", "@id": "https://studiobega.be/#site", "url": "https://studiobega.be/",
        "name": "Studio BEGA", "alternateName": ["Studio Bega", "BEGA architectes", "Studio Benjamin Gaspard"], "inLanguage": "fr-BE",
        "publisher": {"@id": "https://studiobega.be/#studio"}}, {
        "@context": "https://schema.org", "@type": "ProfessionalService", "@id": "https://studiobega.be/#studio",
        "name": "Studio BEGA", "alternateName": ["Studio Bega", "BEGA architectes"], "legalName": "Studio Benjamin Gaspard SRL", "url": "https://studiobega.be/",
        "description": "Studio d'architecture à Hotton, en Belgique : plans directeurs, espaces publics, lieux d'activité, maisons et intérieurs, partout en Belgique et au Luxembourg.",
        "image": "https://studiobega.be/img/hero.jpg", "logo": "https://studiobega.be/apple-touch-icon.png",
        "telephone": "+32474634309", "email": "contact@studiobega.be", "vatID": "BE0799818844",
        "address": {"@type": "PostalAddress", "streetAddress": "Rue Simon 43", "postalCode": "6990", "addressLocality": "Hotton", "addressRegion": "Luxembourg", "addressCountry": "BE"},
        "areaServed": [{"@type": "Country", "name": "Belgique"}, {"@type": "Country", "name": "Luxembourg"}],
        "geo": {"@type": "GeoCoordinates", "latitude": 50.2681, "longitude": 5.4466}, "hasMap": "https://maps.google.com/?q=Studio+BEGA,+Rue+Simon+43,+6990+Hotton",
        "founder": {"@type": "Person", "name": "Benjamin Gaspard", "jobTitle": "Architecte"},
        "employee": [{"@type": "Person", "name": "Héloïse Collin", "jobTitle": "Architecte d'intérieur"}],
        "knowsAbout": ["architecture", "plan directeur", "espace public", "rénovation", "architecture d'intérieur", "scénographie"],
        "sameAs": ["https://www.instagram.com/studio_bega_/", "https://www.facebook.com/studiobenjamingaspard", "https://be.linkedin.com/company/studiobega"]
    }], ensure_ascii=False) + '</script>'
    write('index.html', page('Studio BEGA — Architectes à Hotton, Belgique', index2,
        "Studio BEGA, architectes à Hotton (Belgique) : lire un lieu, imaginer sa clé, le réaliser. Plans directeurs, espaces publics, lieux d'activité, maisons et intérieurs, partout en Belgique.", canon='/', ld=LD))

    # Studio, sur le modèle des pages « Office » des bureaux d'auteur : une phrase forte, la photo du duo en grand,
    # puis une grille éditoriale — rubrique à gauche, contenu à droite, filets fins — alignée sur le logo.
    # Une seule taille de texte pour tout le corps de page, deux couleurs (noir, gris) : net sur ordinateur comme sur téléphone.
    # Studio : un seul fil, aéré, sans grille ni filets — la phrase, le duo, qui on est, comment on travaille, où l'on est, comment appeler.
    studio = f"""<div class="page"><div class="wrap">
{nav('Studio')}    <article class="sf">
      <h1 class="sf-h">Le studio est à Hotton. Les lieux, eux, sont partout.</h1>
      <figure class="sf-duo"><img src="/img/duo.jpg" alt="Héloïse Collin et Benjamin Gaspard" loading="lazy">
        <figcaption>Héloïse Collin, architecte d'intérieur — Benjamin Gaspard, architecte</figcaption></figure>
      <div class="sf-t" id="contact">
        <p>Un lieu se lit avant de se dessiner. Le relief, l'eau, les usages, ceux qui le traversent, et ce que vous voulez en faire : de cette lecture sort <span class="key">la clé</span>, l'idée qui rend le lieu singulier.</p>
        <p>Puis le projet entier, de la clé au chantier. Plans directeurs, espaces publics, lieux d'activité, maisons et intérieurs, en Wallonie, à Bruxelles et au-delà.</p>
      </div>
      <div class="sf-dl">
        <a href="tel:+32474634309"><span class="k">Téléphone</span><span class="v">+32 474 63 43 09</span><span class="ar" aria-hidden="true">→</span></a>
        <a href="mailto:contact@studiobega.be"><span class="k">E-mail</span><span class="v">contact@studiobega.be</span><span class="ar" aria-hidden="true">→</span></a>
        <a href="https://maps.google.com/?q=Rue+Simon+43,+6990+Hotton" target="_blank" rel="noopener"><span class="k">Studio</span><span class="v">Rue Simon 43, 6990 Hotton</span><span class="ar" aria-hidden="true">↗</span></a>
      </div>
    </article>
{FOOT}</div></div>"""
    write('studio/index.html', page('Studio — Studio BEGA, architectes à Hotton', studio,
        "Studio BEGA, Hotton : Benjamin Gaspard, architecte, et Héloïse Collin, architecte d'intérieur. Plans directeurs, espaces publics, lieux d'activité, maisons. Rue Simon 43, 6990 Hotton · +32 474 63 43 09", canon='/studio/', ld=LD))
    # une page par projet, pour Google : /projets/<id>/ — la fiche en pleine page, titre et description propres ; le site, lui, ouvre les fiches sur place
    for q in tous:
        inner = re.search(r'<template id="f-[^"]+">(.*)</template>', fiche(q), re.S).group(1)
        inner = re.sub(r'<button type="button" class="fx-x"[^>]*>×</button>', '', inner).replace('<h2 class="nm">', '<h1 class="nm">').replace('</h2>', '</h1>', 1)
        nom, lieu, cle = ph(q['nom']), ph(q['lieu']), ph(q['cle'])
        desc = ' '.join(x for x in (cle, ph(q['dem']), f"{NAMES[q['pk']]} · {lieu} · Studio BEGA, architecture et plans directeurs en Wallonie.") if x)
        body_p = f"""<div class="page"><div class="wrap">
{nav('Projets')}    <article class="pp"><a class="pp-back" href="/#projets">← Tous les projets</a>
      <div class="mbox pp-box">{inner}</div></article>
{FOOT}</div></div>
<div class="lb" id="lb" aria-hidden="true"><button type="button" class="lb-p" aria-label="Image précédente">‹</button><img src="" alt=""><button type="button" class="lb-n" aria-label="Image suivante">›</button><span class="lb-c"></span></div>"""
        write(f'projets/{q["id"]}/index.html', page(f'{nom} — {lieu} · Studio BEGA', body_p, desc[:300], abs_(PICS[q['id']][0][0]), f'/projets/{q["id"]}/'))
    # plan du site pour Google
    urls = ['/', '/studio/', '/territoires/', '/activites/', '/habitat/'] + [f'/projets/{q["id"]}/' for q in tous]
    (DIST / 'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + ''.join(f'  <url><loc>https://studiobega.be{u}</loc></url>\n' for u in urls) + '</urlset>\n')
    # Google Search Console : fichier de vérification du site (ne pas supprimer, sinon la propriété est perdue)
    (DIST / 'googleabd13bafbcc1a0b9.html').write_text('google-site-verification: googleabd13bafbcc1a0b9.html')
    (DIST / 'robots.txt').write_text('User-agent: *\nAllow: /\nSitemap: https://studiobega.be/sitemap.xml\n')
    # l'ancienne page Contact mène au bas de Studio
    write('contact.html', f'<!doctype html><meta charset="utf-8"><meta name="robots" content="noindex"><meta http-equiv="refresh" content="0;url={BASE}/studio/#contact"><link rel="canonical" href="{BASE}/studio/#contact">')

# ---------- assets, redirections, favicon ----------
(DIST / 'assets').mkdir(exist_ok=True)
shutil.copy(ROOT / 'assets' / 'site.css', DIST / 'assets' / 'site.css')
shutil.copy(ROOT / 'assets' / 'site.js', DIST / 'assets' / 'site.js')
emp = DATA / 'empreinte.txt'
(DIST / 'build.json').write_text(json.dumps({'empreinte': emp.read_text().strip() if emp.exists() else ''}))
# favicon : le gros rond jaune, seul, sans fond (PNG : Safari ignore les SVG)
shutil.copy(ROOT / 'assets' / 'favicon.png', DIST / 'favicon.png'); shutil.copy(ROOT / 'assets' / 'apple-touch-icon.png', DIST / 'apple-touch-icon.png')

# anciennes adresses Adobe Portfolio → fiche dans sa porte. RewriteRule [NE] : le « # » de l'ancre passe tel quel
# (Redirect/RedirectMatch l'encoderaient en %23). Correspondance exacte, sans quoi /studio attraperait /studio.html.
redir = ['RewriteEngine On', 'RewriteCond %{HTTPS} off', 'RewriteRule ^ https://%{HTTP_HOST}%{REQUEST_URI} [L,R=301]',
         'ErrorDocument 404 /index.html', 'AddDefaultCharset UTF-8',
         # les pages se revérifient à chaque visite ; style, script et images versionnés restent en cache
         '<IfModule mod_headers.c>', '<FilesMatch "\\.(html|json)$">', 'Header set Cache-Control "no-cache"', '</FilesMatch>',
         '<FilesMatch "\\.(css|js)$">', 'Header set Cache-Control "public, max-age=31536000"', '</FilesMatch>', '</IfModule>']
R = lambda src, dst: redir.append(f'RewriteRule ^{src}/?$ {dst} [R=301,L,NE]')
old = json.load(open(DATA / 'old_slugs.json')) if (DATA / 'old_slugs.json').exists() else {}
# anciennes adresses Adobe → la page du projet (Google y transfère son référencement), sinon la fiche dans sa galerie
bycode = {p['code']: (f"/projets/{p['id']}/" if V2 and PICS.get(p['id']) else f"/{p['pk']}/#{p['id']}") for p in P}
for s_, code in old.items():
    if code in bycode: R(re.escape(s_.lstrip('/')), bycode[code])
if V2:   # la refonte : /studio/ est une vraie page ; l'ancienne page Contact et l'aperçu y mènent
    R(r'studio\.html', '/studio/'); R(r'contact(\.html)?', '/studio/#contact'); R('accueil', '/'); R('apercu(/.*)?', '/')
else:
    R(r'studio(\.html)?', '/#studio'); R('contact', '/contact.html'); R('accueil', '/')
R('sites', '/territoires/'); R('maisons', '/habitat/')
(DIST / '.htaccess').write_text('\n'.join(redir) + '\n')

n_img = sum(1 for _ in IMG.rglob('*.jpg'))
print(f"ok — {len(P)} lieux, {n_img} images, dist/ = {sum(f.stat().st_size for f in DIST.rglob('*') if f.is_file())//1024} Ko")
