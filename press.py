#!/usr/bin/env python3
"""Dossier de presse Studio BEGA, construit depuis Airtable — la même base que le site.

  Textes   (table « Textes ») : manifeste, communiqué, sujets, chiffres, bios, citations…  colonne « Où » contient Presse
  Projets  (table « Projets », vue « Site ») : les lignes cochées « Presse » ; champs « Site · » + « Presse · Devenu »

Rien n'est écrit ici en dur : changer un texte dans Airtable change le dossier à la publication suivante.
Sortie : dist/presse/Studio-BEGA_Dossier-de-presse.pdf  (publié avec le site : studiobega.be/presse/…)

Usage : AIRTABLE_TOKEN=pat… python3 press.py        (Chrome requis : google-chrome)
        python3 press.py --local press/test.json      (données de test, sans Airtable)
"""
import html, io, json, math, os, re, subprocess, sys, time
from pathlib import Path
from datetime import date

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'dist' / 'presse'; OUT.mkdir(parents=True, exist_ok=True)
WORK = ROOT / 'press' / 'build'; WORK.mkdir(parents=True, exist_ok=True)
BASE, PROJETS, TEXTES = 'app96I5oQRuFkzTbc', 'tbl8SvCW4xtd7LtuT', 'tblbzLNq3B2BUefMe'
F = {'Code': 'code', 'Site · Porte': 'porte', 'Site · Nom': 'nom', 'Site · Lieu': 'lieu', 'Site · Type': 'type',
     'Site · Année': 'annee', 'Site · État': 'etat', 'Site · Demandé': 'dem', 'Site · La clé': 'cle',
     'Site · Sorti / Pistes': 'sorti', 'Site · Paragraphe': 'para', 'Presse · Devenu': 'devenu'}
DOORS = {'Territoires': "Un territoire se lit avant de se dessiner.", 'Activités': "Un lieu d'activité vit de ce qu'il fait ressentir.",
         'Habitat': "Habiter, c'est s'accorder à un lieu."}
MOIS = ['janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre']
e = lambda s: html.escape(s or '')

# ---------- données ----------
def airtable():
    import requests
    tok = os.environ.get('AIRTABLE_TOKEN') or sys.exit('AIRTABLE_TOKEN manquant')
    H = {'Authorization': f'Bearer {tok}'}
    def get(table, params):
        out, off = [], None
        while True:
            p = dict(params, pageSize=100, **({'offset': off} if off else {}))
            r = requests.get(f'https://api.airtable.com/v0/{BASE}/{table}', headers=H, params=p, timeout=60); r.raise_for_status()
            j = r.json(); out += j['records']; off = j.get('offset')
            if not off: return out
            time.sleep(.25)
    tx = get(TEXTES, {'filterByFormula': 'FIND("Presse", ARRAYJOIN({Où}))', 'sort[0][field]': 'Ordre'})
    textes = {r['fields'].get('Nom', ''): r['fields'].get('Texte', '') for r in tx}
    pj = get(PROJETS, {'view': 'Site', 'filterByFormula': '{Presse}', 'fields[]': list(F) + ['Site · Photos']})
    projets = []
    for r in pj:
        f = r['fields']; p = {k: f.get(a, '') for a, k in F.items()}
        p['photos'] = []
        for k, a in enumerate(f.get('Site · Photos', [])[:2]):
            dst = WORK / f"{p['code'].replace('.', '-')}-{k}.jpg"
            if not dst.exists():
                from PIL import Image, ImageOps
                b = requests.get(a['url'], timeout=120); b.raise_for_status()
                im = ImageOps.exif_transpose(Image.open(io.BytesIO(b.content))).convert('RGB')
                if im.width > 2200: im = im.resize((2200, round(im.height * 2200 / im.width)), Image.LANCZOS)
                im.save(dst, 'JPEG', quality=86)
            p['photos'].append(dst.name)
        projets.append(p)
    return textes, projets

if '--local' in sys.argv:
    d = json.load(open(sys.argv[sys.argv.index('--local') + 1])); TX, PJ = d['textes'], d['projets']
else:
    TX, PJ = airtable()

T = lambda k: TX.get(k, '').strip()
def paras(txt, cls=''):   # paragraphes séparés par une ligne vide ; *italique* = la clé surlignée
    out = []
    for b in re.split(r'\n\s*\n', txt.strip()):
        b = e(b).replace('\n', '<br>')
        b = re.sub(r'\*(.+?)\*', r'<span class="k">\1</span>', b)
        out.append(f'<p{f" class={chr(34)}{cls}{chr(34)}" if cls else ""}>{b}</p>')
    return ''.join(out)
def mk(txt): return re.sub(r'\*(.+?)\*', r'<span class="k">\1</span>', e(txt)).replace('\n', '<br>')
def manifeste(txt):   # « la clé » en jaune, comme sur le site
    return paras(txt.replace("Nous l'appelons la clé", "Nous l'appelons *la clé*"))

# ---------- pages ----------
P = []
def page(inner, cls=''): P.append(f'<section class="page {cls}">{inner}</section>')
def hdr(r): return f'<div class="hdr"><span class="logo s">BEGA<i></i></span><span>{e(r)}</span></div>'
today = date.today(); QUAND = f'{MOIS[today.month - 1]} {today.year}'
cover = next((p['photos'][0] for p in PJ if p['photos'] and p['code'] == '23.14'), next((p['photos'][0] for p in PJ if p['photos']), ''))

page(f"""<div class="cover" style="background-image:url('build/{cover}')"></div>
<div class="covtxt"><div class="logo">BEGA<i></i></div><h1>Tout est déjà là.</h1>
<p class="kick">Lire un lieu. Imaginer sa clé. Le réaliser.</p>
<p class="date">Studio BEGA · architectes à Hotton · Dossier de presse, {QUAND}</p></div>""", 'nopad')

chiffres = ''.join(f'<tr><td>{e(a.strip())}</td><td>{e(b.strip())}</td></tr>' for a, b in (l.split('|', 1) for l in T('En chiffres').splitlines() if '|' in l))
page(f"""{hdr('Communiqué · ' + QUAND)}<p class="eyebrow">Communiqué de presse · Hotton, {QUAND}</p>
<h2 class="xl2">{mk(T('Communiqué · titre'))}</h2>
<div class="cols2 com"><div>{paras(T('Communiqué · texte'))}</div>
<div><table class="fiche chiffres"><tr><th colspan="2">En chiffres</th></tr>{chiffres}</table>
{f'<blockquote>« {e(T("Citation · le lieu"))} »<br><small>Benjamin Gaspard</small></blockquote>' if T('Citation · le lieu') else ''}</div></div>""")

ess = re.split(r'\n\s*\n', T("L'essence · la clé puissante"))
page(f"""{hdr('Plus loin que la commande')}<p class="eyebrow">Ce que c'est, BEGA</p>
<h2 class="xl2">{mk(T('Écart · titre'))}</h2>
<p class="lead" style="max-width:150mm">{mk(ess[0] if ess else '')}</p>
<table class="ecart"><tr><th></th><th>Ce qu'on demandait</th><th>Ce que c'est devenu</th></tr>
{''.join(f'<tr><td>{e(p["nom"])}{", " + e(p["lieu"]) if p["lieu"] and p["lieu"] not in p["nom"] else ""}</td><td>{e(re.sub(r"^Par [^.]*\. ", "", p["dem"]))}</td><td>{e(p["devenu"] or p["cle"])}</td></tr>' for p in PJ)}
</table>{f'<p class="lead fin">{mk(ess[1])}</p>' if len(ess) > 1 else ''}""")

suj = [(k.split(' · ', 2), v) for k, v in TX.items() if k.startswith('Sujet · ')]
cit_b = T('Citation · Bouillon')
page(f"""{hdr('Sujets pour la presse')}<p class="eyebrow">Sujets pour la presse</p><h2>{len(suj)} histoires à raconter.</h2>
<div class="suj">{''.join(f'<div><p class="lab">{e(k[1])}</p><h3>{e(k[2])}</h3><p>{e(v)}</p></div>' for k, v in suj)}
{f'<div class="q"><blockquote>« {e(cit_b)} »<br><small>Benjamin Gaspard, à propos de l’esplanade de Bouillon</small></blockquote></div>' if cit_b else ''}</div>
{next((f'<img class="strip" src="build/{p["photos"][0]}"><p class="credit">{e(p["nom"])}, {e(p["lieu"])} · Studio BEGA</p>' for p in PJ if p['code'] == '26.60' and p['photos']), '')}""")

page(f"""{hdr('Le studio')}<p class="eyebrow">Le studio</p><h2>Chaque lieu a sa clé.</h2>
<figure class="duo1"><img src="static/duo.jpg"><figcaption>Héloïse Collin et Benjamin Gaspard</figcaption></figure>
<div class="cols2"><div><h3>Benjamin Gaspard · architecte, fondateur</h3><p>{e(T('Bio · Benjamin Gaspard'))}</p></div>
<div><h3>Héloïse Collin · architecte d'intérieur</h3><p>{e(T('Bio · Héloïse Collin'))}</p><p>Studio BEGA travaille en Wallonie, à Bruxelles et au Luxembourg, de l'espace public à la maison.</p></div></div>""")

if T('Manifeste'):
    page(f"""{hdr('Le manifeste')}<p class="eyebrow">Le manifeste</p><h2 class="xl">Chaque lieu a sa clé.</h2>
<div class="manif2">{manifeste(T('Manifeste'))}</div>""")

for p in PJ:
    sorti = [x.strip() for x in (p['sorti'] or '').split('\n') if x.strip()]
    lieu_cle = next((v for k, v in TX.items() if k.startswith('Citation · ') and k[11:] and k[11:] in (p['lieu'] or '')), '')
    meta = ' · '.join(x for x in (p['lieu'], (p['type'] or '').capitalize(), p['annee'], p['etat']) if x)
    ph = p['photos']
    page(f"""<div class="hero" style="background-image:url('build/{ph[0] if ph else ''}')"></div><div class="pin">
{hdr(f"{p['porte']} · {DOORS.get(p['porte'], '')}")}<p class="eyebrow">{e(meta)}</p><h2>{e(p['nom'])}</h2>
<p class="clebig"><span class="cle">{e(p['cle'])}</span></p>
<div class="cols2 proj"><div><p class="lab">Demandé</p><p>{e(p['dem'])}</p>
{f'<p class="lab">{"Pistes" if len(sorti) > 1 else "Sorti"}</p><p>{"<br>".join(e(x) for x in sorti)}</p>' if sorti else ''}
{f'<blockquote>« {e(lieu_cle)} »<br><small>Benjamin Gaspard</small></blockquote>' if lieu_cle else ''}</div>
<div>{f'<p class="lab">En détail</p><p>{e(p["para"])}</p>' if p['para'] else ''}{f'<img class="img2" src="build/{ph[1]}">' if len(ph) > 1 else ''}</div></div></div>""", 'nopad')

# ---------- carte : le fond du site (Wallonie, rivières), un point par commune ----------
sys.path.insert(0, str(ROOT)); import carte as C
fond = json.load(open(ROOT / 'data' / 'carte' / 'fond.json'))
W = 680; lon0, lon1, lat0, lat1 = fond['bbox']; kx = math.cos(math.radians((lat0 + lat1) / 2)); sc = W / ((lon1 - lon0) * kx); H = round((lat1 - lat0) * sc)
X = lambda lon: round((lon - lon0) * kx * sc, 1); Y = lambda lat: round((lat1 - lat) * sc, 1)
path = lambda rings: ' '.join('M' + 'L'.join(f'{X(a)},{Y(b)}' for a, b in r) + 'Z' for r in rings)
def smooth(pts):
    Q = [(X(a), Y(b)) for a, b in pts]; d = f'M{Q[0][0]},{Q[0][1]}'
    for i in range(len(Q) - 1):
        p0, p1, p2, p3 = Q[max(i - 1, 0)], Q[i], Q[i + 1], Q[min(i + 2, len(Q) - 1)]
        d += f'C{p1[0]+(p2[0]-p0[0])/6:.1f},{p1[1]+(p2[1]-p0[1])/6:.1f} {p2[0]-(p3[0]-p1[0])/6:.1f},{p2[1]-(p3[1]-p1[1])/6:.1f} {p2[0]},{p2[1]}'
    return d
# tous les lieux publiés sur le site (data/projets.json), un point noir chacun ; le studio en jaune
try: TOUS = json.load(open(ROOT / 'data' / 'projets.json'))
except Exception: TOUS = PJ
pts, communes = [], {}
for p in TOUS:
    g = C._find(p.get('lieu') or '')
    if not g: continue
    pts.append((g[0], g[1])); communes.setdefault(g[2], (g[0], g[1]))
HALO = 'stroke="#fff" stroke-width="3.5" paint-order="stroke" stroke-linejoin="round"'
svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" font-family="Inter">'
svg += f'<path d="{path(fond["bruxelles"])}" fill="none" stroke="#111" stroke-width=".8"/><path d="{path(fond["wallonie"])}" fill="none" stroke="#111" stroke-width=".8" stroke-linejoin="round"/>'
svg += ''.join(f'<path d="{smooth(r)}" fill="none" stroke="#b9cdd9" stroke-width="1"/>' for r in fond.get('rivieres', []))
seen = {}
for la, lo in pts:   # points superposés dans une même commune : léger décalage pour les voir tous
    k = (round(la, 3), round(lo, 3)); i = seen.get(k, 0); seen[k] = i + 1
    ang = i * 2.4; r = 0 if i == 0 else 4 + 2 * (i // 6)
    svg += f'<circle cx="{X(lo) + r * math.cos(ang):.1f}" cy="{Y(la) + r * math.sin(ang):.1f}" r="3.2" fill="#111"/>'
svg += f'<circle cx="{X(C.STUDIO[1])}" cy="{Y(C.STUDIO[0])}" r="6" fill="#F2B705" stroke="#111" stroke-width="1"/>'
svg += f'<text x="{X(C.STUDIO[1]) - 10}" y="{Y(C.STUDIO[0]) - 10}" text-anchor="end" font-size="12" font-weight="600" fill="#111" {HALO}>Hotton · le studio</text>'
svg += '</svg>'
page(f"""{hdr('Les lieux')}<p class="eyebrow">Les lieux</p><h2>Le studio est à Hotton, au bord de l'Ourthe.<br>Les lieux, eux, sont partout.</h2><p class="credit">Chaque point : un lieu publié sur studiobega.be.</p>
<div class="map2">{svg}</div>
<div class="cols3 refs"><div><p class="lab">Contact</p><p><b>Studio BEGA</b><br>Rue Simon 43, 6990 Hotton<br>+32 474 63 43 09<br>contact@studiobega.be<br>studiobega.be</p></div>
<div><p class="lab">Sur demande</p><p>Photos haute définition, plans, entretien sur place.</p></div>
<div><p class="lab">Ce dossier</p><p>Toujours à jour : studiobega.be/presse</p>{f'<p class="credit">{e(T("Crédits photos"))}</p>' if T('Crédits photos') else ''}</div></div>""")

Y_ = '#F2B705'
fonts = ''.join(f"@font-face{{font-family:Inter;src:url('fonts/Inter-{n}.otf');font-weight:{w};font-style:{s}}}"
                for n, w, s in [('Regular', 400, 'normal'), ('Medium', 500, 'normal'), ('SemiBold', 600, 'normal'), ('Bold', 700, 'normal'), ('ExtraBold', 800, 'normal'), ('Italic', 400, 'italic')])
CSS = fonts + f"""
@page{{size:A4;margin:0}}*{{box-sizing:border-box}}
body{{margin:0;font-family:Inter,sans-serif;color:#111;font-size:10pt;line-height:1.45}}
.page{{width:210mm;height:297mm;padding:16mm 16mm 14mm;position:relative;overflow:hidden;page-break-after:always}}.page.nopad{{padding:0}}
b{{font-weight:600}}.logo{{font-weight:800;font-size:22pt;letter-spacing:-.01em}}.logo i{{display:inline-block;width:.28em;height:.28em;border-radius:50%;background:{Y_};margin-left:.08em}}.logo.s{{font-size:11pt}}
.hdr{{display:flex;justify-content:space-between;align-items:baseline;font-size:8pt;color:#777;border-bottom:1px solid #e3e3e3;padding-bottom:2.5mm;margin-bottom:9mm}}
.eyebrow{{font-size:8pt;text-transform:uppercase;letter-spacing:.12em;color:#888;margin:0 0 2mm}}
h1{{font-size:46pt;line-height:1.02;font-weight:700;margin:10mm 0 6mm;letter-spacing:-.02em}}
h2{{font-size:22pt;line-height:1.12;font-weight:700;margin:0 0 8mm;letter-spacing:-.01em}}h2.xl{{font-size:40pt;line-height:1.02;margin-bottom:10mm}}h2.xl2{{font-size:30pt;line-height:1.05;margin-bottom:9mm}}
h3{{font-size:11pt;margin:0 0 2mm}}p{{margin:0 0 3mm}}.lead{{font-size:12pt;line-height:1.4}}.lead.fin{{margin-top:12mm;font-weight:600;font-size:15pt;line-height:1.3}}
.k,.cle{{box-shadow:inset 0 -.45em {Y_}}}.cle{{font-size:17pt;font-weight:600;line-height:1.3;display:inline}}.clebig{{margin:-4mm 0 6mm}}
.cols2{{display:grid;grid-template-columns:1fr 1fr;gap:10mm}}.cols3{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:7mm}}
.fiche{{width:100%;border-collapse:collapse;font-size:9pt;margin-bottom:8mm}}.fiche th{{text-align:left;font-size:8pt;text-transform:uppercase;letter-spacing:.1em;color:#888;font-weight:500;border-bottom:1.5px solid #111;padding:0 0 2mm}}
.fiche td{{border-bottom:1px solid #e3e3e3;padding:2mm 3mm 2mm 0;vertical-align:top}}.chiffres td:first-child{{width:22mm;font-size:13pt;font-weight:700}}
blockquote{{margin:4mm 0;padding-left:4mm;border-left:3px solid {Y_};font-size:12pt;line-height:1.35}}blockquote small{{font-size:8pt;color:#888}}
.com p{{font-size:10.5pt}}.manif2{{columns:2;column-gap:10mm;font-size:11pt;line-height:1.5}}.manif2 p{{margin:0 0 4mm;break-inside:avoid}}.manif2 p:last-child{{font-weight:600}}
.cover{{position:absolute;inset:0;background-size:cover;background-position:center}}.covtxt{{position:absolute;left:0;right:0;bottom:0;background:#fff;padding:12mm 16mm 16mm}}
.kick{{font-size:11pt}}.date{{font-size:9pt;color:#777;margin-top:6mm}}
.duo1{{margin:0 0 8mm}}.duo1 img{{width:100%;height:118mm;object-fit:cover;object-position:50% 35%}}figure{{margin:0}}figcaption{{font-size:8pt;color:#777;margin-top:1.5mm}}
.hero{{height:138mm;background-size:cover;background-position:center}}.pin{{padding:10mm 16mm 12mm}}.pin .hdr{{margin-bottom:6mm}}
.lab{{font-size:7.5pt;text-transform:uppercase;letter-spacing:.12em;color:#888;margin:4mm 0 1mm}}.lab:first-child{{margin-top:0}}
.img2{{width:100%;height:46mm;object-fit:cover;margin-top:2mm}}.credit{{font-size:7.5pt;color:#888;margin-top:2mm}}
.ecart{{width:100%;border-collapse:collapse;margin-top:8mm;font-size:10pt}}.ecart th{{text-align:left;font-size:7.5pt;text-transform:uppercase;letter-spacing:.12em;color:#888;font-weight:500;border-bottom:1.5px solid #111;padding:0 4mm 2mm 0}}
.ecart td{{border-bottom:1px solid #e3e3e3;padding:4.5mm 4mm 4.5mm 0;vertical-align:top;line-height:1.4}}.ecart td:first-child{{width:42mm;font-weight:600}}.ecart td:nth-child(2){{width:50mm;color:#666}}.ecart td:nth-child(3){{font-weight:500}}
.suj{{display:grid;grid-template-columns:1fr 1fr;gap:8mm 10mm}}.suj h3{{font-size:13pt}}.suj p{{margin:0 0 2mm}}.suj .lab{{margin:0 0 1mm}}.suj .q blockquote{{margin:0}}
.strip{{display:block;width:100%;height:78mm;object-fit:cover;margin-top:9mm}}
.map2{{margin:2mm 0 8mm}}.map2 svg{{width:100%;height:auto;display:block}}.refs{{font-size:9pt;line-height:1.45}}
"""
doc = f'<!doctype html><html lang="fr"><head><meta charset="utf-8"><title>Studio BEGA · Dossier de presse</title><style>{CSS}</style></head><body>{"".join(P)}</body></html>'
src = ROOT / 'press' / 'dossier.html'; src.write_text(doc)
pdf = OUT / 'Studio-BEGA_Dossier-de-presse.pdf'
chrome = next((c for c in ('google-chrome', 'google-chrome-stable', 'chromium', 'chromium-browser') if subprocess.run(['which', c], capture_output=True).returncode == 0), 'google-chrome')
subprocess.run([chrome, '--headless=new', '--no-sandbox', '--disable-gpu', '--no-pdf-header-footer', '--allow-file-access-from-files',
                f'--print-to-pdf={pdf}', src.as_uri()], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
(OUT / 'index.html').write_text('<!doctype html><meta charset="utf-8"><meta name="robots" content="noindex">'
                                 '<meta http-equiv="refresh" content="0;url=Studio-BEGA_Dossier-de-presse.pdf">')
print(f'dossier de presse : {len(P)} pages, {len(PJ)} lieux → {pdf}')
