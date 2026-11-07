#!/usr/bin/env python3
"""Range la refonte (construite par V2=1 BASE=/apercu OUT=dist_apercu) dans dist/apercu/.

Les images sont celles du site (/img/…, mêmes fichiers) : on ne les recopie pas.
Les liens internes reçoivent le préfixe /apercu ; l'aperçu est fermé aux moteurs de recherche.
Usage : python3 -I apercu.py
"""
import re, shutil
from pathlib import Path
ROOT = Path(__file__).resolve().parent
SRC, DST = ROOT / 'dist_apercu', ROOT / 'dist' / 'apercu'
BASE = '/apercu'
for x in ('img', '.htaccess', 'build.json', 'favicon.png', 'apple-touch-icon.png'):
    p = SRC / x
    if p.is_dir(): shutil.rmtree(p)
    elif p.exists(): p.unlink()
for f in SRC.rglob('*.html'):
    s = f.read_text()
    # liens et scripts internes → /apercu/… ; images et icônes restent celles du site
    s = re.sub(r'(href|src)="/(?!/|img/|favicon|apple-touch)', rf'\1="{BASE}/', s)
    f.write_text(s)
(SRC / 'robots.txt').write_text('User-agent: *\nDisallow: /\n')
if DST.exists(): shutil.rmtree(DST)
shutil.move(str(SRC), str(DST))
print('aperçu prêt →', DST)
