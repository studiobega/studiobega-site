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
HORS = {'limoges': ('Limoges', 49.77, 4.72)}   # projets hors de la carte : un point posé en Ardenne française, une flèche vers le sud-ouest
REPERES = [('Bruxelles', 50.847, 4.352), ('Liège', 50.633, 5.575), ('Namur', 50.467, 4.872), ('Charleroi', 50.411, 4.445),
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
        hk = next((v[0] for k, v in HORS.items() if k in _k(p['lieu'])), None)
        if hk: hors.setdefault(hk, []).append(p)
        else: inconnus.append(p['lieu'])

    # un point par commune, tous de la même taille ; Hotton (le studio) en jaune.
    # Aucun point ne touche un autre, et aucun n'est exactement à l'aplomb ou à l'horizontale d'un autre (léger décalage).
    R_PT, GAP, OFF = 5, 6, 3
    pts = []
    for name, g in groups.items():
        lat = sum(a for a, _ in g['pts']) / len(g['pts']); lon = sum(b for _, b in g['pts']) / len(g['pts'])
        pts.append([X(lon), Y(lat), name, g['items']])
    for name, items in hors.items():
        la, lo = next((v[1], v[2]) for v in HORS.values() if v[0] == name)
        pts.append([X(lo), Y(la), name, items])
    for _ in range(2000):
        moved = False
        for i in range(len(pts)):
            for j in range(i + 1, len(pts)):
                a_, b_ = pts[i], pts[j]
                dx, dy = b_[0] - a_[0], b_[1] - a_[1]; d = math.hypot(dx, dy) or .01
                if d < 2 * R_PT + GAP:                       # trop proches : on écarte les deux
                    k = (2 * R_PT + GAP - d) / 2 / d
                    a_[0] -= dx * k; a_[1] -= dy * k; b_[0] += dx * k; b_[1] += dy * k; moved = True
                if abs(dx) < OFF: s = OFF + .3 - abs(dx); sg = 1 if dx >= 0 else -1; a_[0] -= sg * s / 2; b_[0] += sg * s / 2; moved = True
                if abs(dy) < OFF: s = OFF + .3 - abs(dy); sg = 1 if dy >= 0 else -1; a_[1] -= sg * s / 2; b_[1] += sg * s / 2; moved = True
        if not moved: break
    def point(x, y, items, place):
        x, y = round(x, 1), round(y, 1)
        lst = '|'.join('§'.join([q['nom']] + (href(q).split('~') + ['', ''])[0:3:2]) for q in items)   # nom§id§porte
        n = len(items); lab = f"{place} · {n} lieu{'x' if n > 1 else ''}"
        return (f'<g class="{"pt st" if place == "Hotton" else "pt"}" tabindex="0" role="button" data-n="{e(place)}" data-l="{e(lst)}" aria-label="{e(lab)}">'
                f'<circle cx="{x}" cy="{y}" r="{R_PT}"/><circle class="hit" cx="{x}" cy="{y}" r="12"/></g>')
    dots = [point(x, y, items, name) for x, y, name, items in pts]
    hx, hy = next((p[0], p[1]) for p in pts if p[2] == 'Hotton') if any(p[2] == 'Hotton' for p in pts) else (X(STUDIO[1]), Y(STUDIO[0]))
    def smooth(pts):   # tracé lissé (Catmull-Rom → Bézier) pour des rivières souples
        P = [(X(a), Y(b)) for a, b in pts]
        if len(P) < 3: return 'M' + 'L'.join(f'{x},{y}' for x, y in P)
        d = f'M{P[0][0]},{P[0][1]}'
        for i in range(len(P) - 1):
            p0, p1, p2 = P[max(i - 1, 0)], P[i], P[i + 1]; p3 = P[min(i + 2, len(P) - 1)]
            c1 = (round(p1[0] + (p2[0] - p0[0]) / 6, 1), round(p1[1] + (p2[1] - p0[1]) / 6, 1))
            c2 = (round(p2[0] - (p3[0] - p1[0]) / 6, 1), round(p2[1] - (p3[1] - p1[1]) / 6, 1))
            d += f'C{c1[0]},{c1[1]} {c2[0]},{c2[1]} {p2[0]},{p2[1]}'
        return d
    riv = ''.join(f'<path class="rv" d="{smooth(r)}"/>' for r in fond.get('rivieres', []))
    for name, items in hors.items():   # hors carte : une flèche vers le lieu, son nom au bout
        x, y = next((p[0], p[1]) for p in pts if p[2] == name)
        dots.append(f'<g class="far" aria-hidden="true"><line class="ar" x1="{x - 8}" y1="{y + 8}" x2="{x - 36}" y2="{y + 36}"/>'
                    f'<path class="ah" d="M{x - 36},{y + 28} L{x - 36},{y + 36} L{x - 28},{y + 36}"/><text class="nm" x="{x - 42}" y="{y + 52}" text-anchor="end">{e(name)}</text></g>')
    LAB = {'Liège': (-12, -4, 'end'), 'Namur': (0, -10, 'middle'), 'Charleroi': (4, 26, 'start'), 'Mons': (0, -10, 'middle'),
           'Bruxelles': (0, -12, 'middle'), 'Arlon': (-12, -8, 'end')}
    rep = ''.join(f'<text class="nm{" out" if n == "Bruxelles" else ""}" x="{X(lo) + LAB.get(n, (8, 4, "start"))[0]}" y="{Y(la) + LAB.get(n, (8, 4, "start"))[1]}" text-anchor="{LAB.get(n, (8, 4, "start"))[2]}">{n}</text>'
                  for n, la, lo in REPERES)
    studio = f'<text class="nm stl" x="{hx - 40}" y="{hy - 26}" text-anchor="end">le studio</text><line class="stk" x1="{hx - 36}" y1="{hy - 30}" x2="{hx - 7}" y2="{hy - 4}"/>'
    svg = (f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Carte des lieux du studio en Wallonie">'
           f'<g class="zm"><path class="bx" d="{path(fond["bruxelles"])}"/><path class="wa" d="{path(fond["wallonie"])}"/><g class="rvs">{riv}</g>'
           f'{"".join(dots)}<g class="lbs">{rep}{studio}</g></g></svg>')
    total = sum(len(g['items']) for g in groups.values()) + sum(len(v) for v in hors.values())
    html_ = (f'<section class="lieux"><h2 class="h">Les lieux.</h2></section>'
             f'<figure class="carte" id="carte">{svg}<div class="zb"><button type="button" class="zi" aria-label="Zoomer">+</button><button type="button" class="zo" aria-label="Dézoomer">−</button></div>'
             '</figure>')
    return html_, inconnus

