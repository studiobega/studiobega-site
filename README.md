# studiobega.be

Site statique de Studio BEGA, construit depuis Airtable.

## Comment ça marche

```
Airtable (BEGA BASE › Projets, vue « Site »)
        │  fetch_airtable.py   lit les lignes cochées Site + les photos
        ▼
data/   projets.json · photos_manifest.json · photos/*.jpg
        │  build_site.py      génère le HTML, redimensionne les images
        ▼
dist/   index.html (accueil) · territoires/ · activites/ · habitat/ · studio.html · contact.html · assets/ · img/ · .htaccess
        │  GitHub Action      dépose dist/ chez Infomaniak par SFTP
        ▼
https://new.studiobega.be  (puis studiobega.be)
```

## Publier

1. Dans Airtable, coche **Site** sur le projet, choisis sa **Porte** (Territoires · Activités · Habitat : ce qu'est le lieu), remplis la ligne (la colonne *Site · À compléter* dit ce qui manque), glisse les photos dans l'ordre (la première = vignette).
2. Attends la nuit, **ou** GitHub → Actions → *Publier le site* → *Run workflow*.

Rien d'autre. Pas de code à toucher pour un projet.

## Secrets du dépôt (Settings → Secrets and variables → Actions)

| Secret           | Contenu                                                        |
|------------------|----------------------------------------------------------------|
| `AIRTABLE_TOKEN` | jeton Airtable lecture seule (`data.records:read`, `schema.bases:read`, base BEGA BASE) |
| `FTP_USER`       | utilisateur FTP/SSH Infomaniak (`kx5isg_…`)                    |
| `FTP_PASSWORD`   | son mot de passe                                               |

Variables optionnelles : `FTP_HOST` (défaut `kx5isg.ftp.infomaniak.com`), `SITE_DIR` (défaut `sites/new.studiobega.be` ; passer à `sites/studiobega.be` au moment de la bascule).

## Règles de contenu (côté Airtable)

- *Site · Année* vide = non affichée. Tout champ qui commence par `[` est un placeholder : ignoré à la publication.
- *Site · Sorti / Pistes* : une ligne = « Sorti » ; plusieurs lignes = « Pistes ».
- *Site · Liens* : une ligne par lien, `Titre | https://…`.
- Les noms de clients privés ne vont jamais dans *Site · Nom*.

## En local

```
pip install requests pillow
AIRTABLE_TOKEN=pat… python3 fetch_airtable.py   # optionnel : sinon data/ sert tel quel
python3 build_site.py                           # → dist/
```

`data/old_slugs.json` : anciennes adresses Adobe Portfolio → code projet, pour les redirections 301 du `.htaccess`.
