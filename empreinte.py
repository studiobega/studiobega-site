#!/usr/bin/env python3
"""Empreinte de la vue « Site » : identifiants des lignes dans l'ordre de la vue + date de dernière
modification de leurs champs « Site · ». Change dès qu'une ligne est modifiée, ajoutée, retirée ou déplacée.

Usage : AIRTABLE_TOKEN=pat… python3 empreinte.py   →  affiche l'empreinte (sha256)
Importé par fetch_airtable.py pour l'écrire dans data/empreinte.txt.
"""
import hashlib, os, sys, time
import requests

BASE, TABLE, VIEW = 'app96I5oQRuFkzTbc', 'tbl8SvCW4xtd7LtuT', 'Site'
TOUS = 'viwX0XYIX1xTmzT16'   # vue « Site · Tous » : l'ordre de « Tous » sur l'accueil, toutes catégories confondues
MOD = 'Site · Modifié'

def lignes(token, fields, view=VIEW):
    url = f'https://api.airtable.com/v0/{BASE}/{TABLE}'
    params = {'view': view, 'pageSize': 100, 'fields[]': fields}
    out, off = [], None
    while True:
        if off: params['offset'] = off
        r = requests.get(url, headers={'Authorization': f'Bearer {token}'}, params=params, timeout=60); r.raise_for_status()
        j = r.json(); out += j['records']; off = j.get('offset')
        if not off: return out
        time.sleep(0.25)

def empreinte(token):
    recs = lignes(token, [MOD])
    txt = '\n'.join(f"{r['id']} {r['fields'].get(MOD, '')}" for r in recs)
    txt += '\nTOUS ' + ' '.join(r['id'] for r in lignes(token, [MOD], TOUS))   # déplacer une ligne dans « Site · Tous » republie aussi
    # la table « Textes » (manifeste, dossier de presse) : un texte modifié republie aussi
    r = requests.get(f'https://api.airtable.com/v0/{BASE}/tblbzLNq3B2BUefMe', headers={'Authorization': f'Bearer {token}'},
                     params={'fields[]': ['Modifié'], 'pageSize': 100}, timeout=60)
    if r.ok: txt += '\nTEXTES ' + ' '.join(sorted(f"{x['id']}:{x['fields'].get('Modifié', '')}" for x in r.json()['records']))
    return hashlib.sha256(txt.encode()).hexdigest()

if __name__ == '__main__':
    tok = os.environ.get('AIRTABLE_TOKEN') or sys.exit('AIRTABLE_TOKEN manquant')
    print(empreinte(tok))
