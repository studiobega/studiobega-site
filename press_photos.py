"""Télécharge les photos des lieux pour le dossier de presse (artefact GitHub)."""
import os, io, requests
from PIL import Image
T = os.environ['AIRTABLE_TOKEN']; B = 'app96I5oQRuFkzTbc'; TB = 'tbl8SvCW4xtd7LtuT'
RECS = {'bastogne': 'reckeiMDHObyilc4I', 'laroche-centre': 'recAlXHK2iq1RKgyZ', 'laroche-ourthe': 'rec9fDw9d8iAT4fFe',
        'plaza': 'reclmo4ejDuyRgYiS', 'bouillon': 'receHRecHhgwqR1aY', 'tour-a-tour': 'recWyKc5vNj06z9mx'}
os.makedirs('press/hd', exist_ok=True); os.makedirs('press/web', exist_ok=True)
for name, rid in RECS.items():
    r = requests.get(f'https://api.airtable.com/v0/{B}/{TB}/{rid}', headers={'Authorization': f'Bearer {T}'}, timeout=60).json()
    for i, a in enumerate(r['fields'].get('Site · Photos', []), 1):
        url = a.get('thumbnails', {}).get('full', {}).get('url') or a['url']
        im = Image.open(io.BytesIO(requests.get(url, timeout=180).content)).convert('RGB')
        base = f'{name}-{i:02d}'
        h = im.copy(); h.thumbnail((2400, 2400)); h.save(f'press/hd/{base}.jpg', quality=88)
        w = im.copy(); w.thumbnail((1400, 1400)); w.save(f'press/web/{base}.jpg', quality=82)
        print(base, im.size)
