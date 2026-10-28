#!/usr/bin/env python3
"""Lit Airtable (BEGA BASE › Projets, lignes cochées « Site ») et écrit data/.

  data/projets.json          champs normalisés, dans l'ordre du site
  data/photos_manifest.json  ordre des photos par projet
  data/photos/<attId>.jpg    photos, réduites à 1600 px (une seule fois : cache par id)

Variables : AIRTABLE_TOKEN (lecture seule : data.records:read + schema.bases:read).
Usage : AIRTABLE_TOKEN=pat… python3 fetch_airtable.py
"""
import io, json, os, sys, time
from pathlib import Path
import requests
from PIL import Image, ImageOps

BASE, TABLE, VIEW = 'app96I5oQRuFkzTbc', 'tbl8SvCW4xtd7LtuT', 'Site'
TOKEN = os.environ.get('AIRTABLE_TOKEN')
if not TOKEN:
    sys.exit('AIRTABLE_TOKEN manquant')
H = {'Authorization': f'Bearer {TOKEN}'}
DATA = Path(__file__).resolve().parent / 'data'
PH = DATA / 'photos'; PH.mkdir(parents=True, exist_ok=True)

F = {  # nom de champ Airtable → clé JSON
    'Code': 'code', 'Site · Porte': 'porte', 'Site · Ordre': 'ordre', 'Site · Nom': 'nom', 'Site · Lieu': 'lieu',
    'Site · Type': 'type', 'Site · Année': 'annee', 'Site · État': 'etat', 'Site · Demandé': 'dem',
    'Site · La clé': 'cle', 'Site · Sorti / Pistes': 'sorti', 'Site · Paragraphe': 'para', 'Site · Liens': 'liens',
}

def records():
    url = f'https://api.airtable.com/v0/{BASE}/{TABLE}'
    params = {'view': VIEW, 'pageSize': 100, 'fields[]': list(F) + ['Site · Photos']}
    out, off = [], None
    while True:
        if off: params['offset'] = off
        r = requests.get(url, headers=H, params=params, timeout=60); r.raise_for_status()
        j = r.json(); out += j['records']; off = j.get('offset')
        if not off: return out
        time.sleep(0.25)

rows, manifest, fresh = [], [], 0
for rec in records():
    f = rec['fields']
    row = {k: f.get(a, '') for a, k in F.items()}
    row['ordre'] = row['ordre'] or 999
    rows.append(row)
    for k, a in enumerate(f.get('Site · Photos', [])):
        manifest.append({'code': row['code'], 'k': k, 'id': a['id'], 'fn': a.get('filename')})
        dst = PH / f"{a['id']}.jpg"
        if dst.exists(): continue
        r = requests.get(a['url'], timeout=120); r.raise_for_status()
        im = ImageOps.exif_transpose(Image.open(io.BytesIO(r.content))).convert('RGB')
        if im.width > 1600: im = im.resize((1600, round(im.height * 1600 / im.width)), Image.LANCZOS)
        im.save(dst, 'JPEG', quality=86, optimize=True); fresh += 1

rows.sort(key=lambda r: (r['porte'], r['ordre'], r['nom']))
json.dump(rows, open(DATA / 'projets.json', 'w'), ensure_ascii=False, indent=0)
json.dump(manifest, open(DATA / 'photos_manifest.json', 'w'), ensure_ascii=False, indent=0)
# photos retirées d'Airtable → retirées du cache
keep = {m['id'] for m in manifest}
for p in PH.glob('*.jpg'):
    if p.stem not in keep: p.unlink()
print(f'{len(rows)} lieux, {len(manifest)} photos ({fresh} nouvelles)')
