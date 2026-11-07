"""Carte des lieux (page Studio) : la Wallonie, un point par localité où le studio a un projet.

- Le fond (Wallonie + Bruxelles) est figé dans data/carte/fond.json (polygones simplifiés,
  sources : Statbel / mathiasleroy/Belgium-Geographic-Data, WGS84).
- Les points viennent du champ « Site · Lieu » d'Airtable, via la table LIEUX ci-dessous.
  Un lieu inconnu de la table est simplement ignoré (et listé à la construction).
- Hors de la carte (ex. Limoges) : cité en toutes lettres sous la carte.
"""
import json, math, html, unicodedata, re
from pathlib import Path

e = lambda s: html.escape(s or '', quote=True)

def _k(s):
    s = unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z]+', ' ', s).strip()

# localité → (lat, lon, nom affiché) ; le nom affiché regroupe les villages dans leur commune
LIEUX = {
    'bouillon': (49.794, 5.068, 'Bouillon'), 'corbion': (49.797, 5.004, 'Bouillon'),
    'frahan': (49.837, 5.023, 'Bouillon'), 'noirefontaine': (49.810, 5.110, 'Bouillon'),
    'bastogne': (50.000, 5.715, 'Bastogne'),
    'la roche en ardenne': (50.183, 5.576, 'La Roche-en-Ardenne'),
    'martelange': (49.832, 5.738, 'Martelange'),
    'hotton': (50.268, 5.446, 'Hotton'), 'melreux': (50.283, 5.437, 'Hotton'), 'werpin': (50.262, 5.428, 'Hotton'),
    'beauraing': (50.110, 4.956, 'Beauraing'),
    'leglise': (49.800, 5.533, 'Léglise'), 'thibessart': (49.802, 5.485, 'Léglise'),
    'liege': (50.633, 5.575, 'Liège'),
    'somme leuze': (50.336, 5.367, 'Somme-Leuze'),
    'libramont': (49.920, 5.380, 'Libramont'),
    'stavelot': (50.395, 5.930, 'Stavelot'),
    'neufchateau': (49.841, 5.435, 'Neufchâteau'),
    'vaux sur sure': (49.912, 5.578, 'Vaux-sur-Sûre'), 'sibret': (49.971, 5.642, 'Vaux-sur-Sûre'),
    'durbuy': (50.352, 5.456, 'Durbuy'), 'barvaux': (50.350, 5.495, 'Durbuy'), 'weris': (50.328, 5.531, 'Durbuy'),
    'biron': (50.330, 5.430, 'Durbuy'),
    'rendeux': (50.233, 5.500, 'Rendeux'), 'bois d arlogne': (50.222, 5.530, 'Rendeux'), 'concy': (50.240, 5.515, 'Rendeux'),
    'marcourt': (50.208, 5.524, 'Rendeux'),
    'tenneville': (50.095, 5.530, 'Tenneville'), 'journal': (50.077, 5.540, 'Tenneville'),
    'erezee': (50.292, 5.559, 'Érezée'),
    'sainte ode': (50.020, 5.540, 'Sainte-Ode'), 'saint ode': (50.020, 5.540, 'Sainte-Ode'),
    'lavacherie': (50.046, 5.514, 'Sainte-Ode'), 'fosset': (49.995, 5.592, 'Sainte-Ode'),
    'aywaille': (50.474, 5.676, 'Aywaille'),
    'marche en famenne': (50.227, 5.344, 'Marche-en-Famenne'),
}
HORS = {'limoges': 'Limoges'}           # projets hors de la carte, cités sous la carte
REPERES = [('Bruxelles', 50.847, 4.352), ('Namur', 50.467, 4.872), ('Charleroi', 50.411, 4.445),
           ('Mons', 50.454, 3.952), ('Arlon', 49.683, 5.817)]
STUDIO = (50.268, 5.446)

def _find(lieu):
    k = _k(lieu)
    if not k: return None
    if k in LIEUX: return LIEUX[k]
    for part in reversed([_k(x) for x in (lieu or '').split(',')]):   # « Journal, Tenneville »
        if part in LIEUX: return LIEUX[part]
    for key in sorted(LIEUX, key=len, reverse=True):                   # « Vallée … à Durbuy »
        if re.search(rf'\b{key}\b', k): return LIEUX[key]
    return None

def build(projets, href, fond_path):
    """projets : liste de dicts (nom, lieu) ; href(p) → lien vers la fiche. Renvoie le HTML."""
    fond = json.load(open(fond_path))
    W = 680
    lon0, lon1, lat0, lat1 = fond['bbox']
    kx = math.cos(math.radians((lat0 + lat1) / 2))
    sc = W / ((lon1 - lon0) * kx)
    H = round((lat1 - lat0) * sc)
    X = lambda lon: round((lon - lon0) * kx * sc, 1)
    Y = lambda lat: round((lat1 - lat) * sc, 1)
    path = lambda rings: ' '.join('M' + 'L'.join(f'{X(a)},{Y(b)}' for a, b in r) + 'Z' for r in rings)

    groups, hors, inconnus = {}, {}, []
    for p in projets:
        g = _find(p['lieu'])
        if g:
            groups.setdefault(g[2], {'pts': [], 'items': []})
            groups[g[2]]['pts'].append(g[:2]); groups[g[2]]['items'].append(p)
            continue
        hk = next((v for k, v in HORS.items() if k in _k(p['lieu'])), None)
        if hk: hors.setdefault(hk, []).append(p)
        else: inconnus.append(p['lieu'])

    dots = []
    for name, g in sorted(groups.items(), key=lambda kv: -len(kv[1]['items'])):
        lat = sum(a for a, _ in g['pts']) / len(g['pts']); lon = sum(b for _, b in g['pts']) / len(g['pts'])
        n = len(g['items']); r = round(4.5 + 1.6 * math.sqrt(n - 1), 1)
        lst = '|'.join(f"{x['nom']}§{href(x)}" for x in g['items'])
        dots.append(f'<g class="pt" tabindex="0" role="button" aria-label="{e(name)} : {n} lieu{"x" if n > 1 else ""}" '
                    f'data-n="{e(name)}" data-l="{e(lst)}"><circle cx="{X(lon)}" cy="{Y(lat)}" r="{r}"/>'
                    f'<circle class="hit" cx="{X(lon)}" cy="{Y(lat)}" r="{max(r, 16)}"/></g>')
    rep = ''.join(f'<g class="rep"><circle cx="{X(lo)}" cy="{Y(la)}" r="1.6"/><text x="{X(lo) + 6}" y="{Y(la) + 4}">{n}</text></g>'
                  for n, la, lo in REPERES)
    sx, sy = X(STUDIO[1]), Y(STUDIO[0])
    studio = f'<circle class="st" cx="{sx}" cy="{sy}" r="13"/>'

    svg = (f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Carte des lieux du studio en Wallonie">'
           f'<path class="bx" d="{path(fond["bruxelles"])}"/><path class="wa" d="{path(fond["wallonie"])}"/>'
           f'{rep}{"".join(dots)}{studio}</svg>')
    noms = sorted(groups, key=lambda s: _k(s)) + sorted(hors, key=_k)
    total = sum(len(g['items']) for g in groups.values()) + sum(len(v) for v in hors.values())
    html_ = (f'<section class="lieux"><h2 class="h">Les lieux.</h2><p>Le studio est à Hotton. Les lieux, eux, sont partout.</p></section>'
             f'<figure class="carte" id="carte">{svg}'
             f'<figcaption><p class="cl" aria-live="polite"></p>'
             f'<p class="cn"><span class="leg" aria-hidden="true"></span>le studio · {total} lieux · {" · ".join(e(n) for n in noms)}</p></figcaption></figure>')
    return html_, inconnus
