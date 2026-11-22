#!/usr/bin/env python3
"""Empreinte de la vue « Site » : identifiants des lignes dans l'ordre de la vue + date de dernière
modification de leurs champs publiés. Change dès qu'une ligne est modifiée, ajoutée, retirée ou déplacée.

Deux vues Airtable, deux ordres distincts : « Site » (l'ordre dans chaque catégorie) et « Site · Tous »
(l'ordre de « Tous » sur l'accueil). Lues par leur identifiant : les renommer dans Airtable ne casse rien.

Usage : AIRTABLE_TOKEN=pat… python3 empreinte.py   →  affiche l'empreinte (sha256)
Importé par fetch_airtable.py pour l'écrire dans data/empreinte.txt.
"""
import hashlib, os, sys, time
import requests

BASE, TABLE = 'app96I5oQRuFkzTbc', 'tbl8SvCW4xtd7LtuT'
VIEW = 'viwsgVmDFTzHZL38Z'   # vue « Site » : l'ordre dans chaque catégorie (Territoires, Activités, Habitat)
TOUS = 'viwX0XYIX1xTmzT16'   # vue « Site · Tous » : l'ordre de « Tous » sur l'accueil, toutes catégories confondues
MOD = 'Site · Modifié'
# Les faits du projet ne portent plus le préfixe « Site · » dans Airtable (22/11/2026) : nom actuel → ancien nom.
# Tant qu'Airtable n'est pas renommé, on retombe sur l'ancien nom ; les deux marchent.
ANCIENS = {'Nom': 'Site · Nom', 'Lieu': 'Site · Lieu', 'Type': 'Site · Type', 'Année': 'Site · Année',
           'État public': 'Site · État', 'Demandé': 'Site · Demandé', 'La clé': 'Site · La clé',
           'Sorti / Pistes': 'Site · Sorti / Pistes', 'Paragraphe': 'Site · Paragraphe'}

def lignes(token, fields, view=VIEW, extra=None):
    """Les lignes de la vue, dans l'ordre de la vue. Si un champ n'existe pas sous son nom actuel
    (Airtable pas encore renommé), on relit avec les anciens noms et on rend les clés sous les noms actuels."""
    url = f'https://api.airtable.com/v0/{BASE}/{TABLE}'
    def lire(noms):
        params = dict(extra or {}, view=view, pageSize=100); params['fields[]'] = noms
        out, off = [], None
        while True:
            if off: params['offset'] = off
            r = requests.get(url, headers={'Authorization': f'Bearer {token}'}, params=params, timeout=60)
            if r.status_code == 422: return None
            r.raise_for_status()
            j = r.json(); out += j['records']; off = j.get('offset')
            if not off: return out
            time.sleep(0.25)
    out = lire(list(fields))
    if out is not None: return out
    vieux = [ANCIENS.get(f, f) for f in fields]
    out = lire(vieux)
    if out is None: sys.exit('Airtable : champ introuvable parmi ' + ', '.join(fields))
    retour = {v: k for k, v in ANCIENS.items()}
    for rec in out: rec['fields'] = {retour.get(k, k): v for k, v in rec['fields'].items()}
    return out

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
