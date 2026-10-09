# Affectations SSA : carte et base de données

Outil d'aide au choix d'affectation pour un médecin des armées. Il recense les centres médicaux des armées (CMA), leurs antennes médicales et les hôpitaux d'instruction des armées (HIA), en métropole, outre-mer et à l'étranger. Chaque lieu est enrichi de critères de vie mesurés dans un rayon de **30 minutes à vélo** (cercle vert) et **30 minutes en voiture** (cercle jaune).

**Application en ligne : https://eliotpechdi-wq.github.io/affectations** (téléphone ou ordinateur, rien à installer).
Sur iPhone : Safari → Partager → « Sur l'écran d'accueil » pour l'avoir comme une application.

## Ce qu'il y a à ouvrir

| Fichier | Pour qui | Contenu |
|---|---|---|
| `output/carte_affectations.html` | tout le monde | Carte interactive : double-cliquer pour l'ouvrir dans un navigateur. |
| `output/affectations.xlsx` | Excel | 3 onglets : lieux (filtrables, colonne « Ma sélection »), employeurs proches, méthode et sources. |
| `data/affectations.db` | Python / SQL | Base SQLite : tables `sites`, `employeurs`, `ref_gares_tgv`, `ref_aeroports`, `ref_grandes_villes`, vue `v_synthese`. |

## Utiliser la carte

- **Cliquer un point** (ou un nom dans la liste) ouvre sa fiche : accès, logement, crèches et écoles, culture, emploi ingénieur.
- **Filtres** à gauche : armée, zone, type, temps max jusqu'au TGV / aéroport / grande ville, prix du m², nombre minimal de crèches, cinémas, employeurs.
- **Retenir / Écarter** un lieu et ajouter des notes. Le filtre « Ma sélection → Retenus » n'affiche plus que la liste courte.
- **Tableau comparatif** (en haut à droite) : tous les lieux affichés côte à côte, triables par colonne.
- **Profils** : au premier lancement, chacun choisit ou crée son profil (un prénom, sans mot de passe). Chaque profil garde ses propres choix et notes, enregistrés en ligne dans Supabase : on les retrouve sur tous ses appareils. Le bouton en haut à droite change de profil.
- Pas de mot de passe : n'écrivez rien de confidentiel dans les notes.

## Critères et sources

| Critère | Source | Remarque |
|---|---|---|
| Lieux d'affectation | defense.gouv.fr, sites des unités, Wikipédia | « à confirmer » = antenne déduite de la présence d'une unité |
| Habitants | Insee via geo.api.gouv.fr | zone = communes dont le centre est dans le cercle |
| Grande ville | communes > 80 000 hab. (+ agglomérations outre-mer) | |
| TGV | GTFS SNCF Voyageurs (TGV INOUI / OUIGO) | |
| Aéroports | OurAirports (vols réguliers) | « Hub » = grand aéroport international |
| Prix m² | DVF Etalab, médiane des ventes | absent en Alsace-Moselle et à Mayotte |
| Crèches | Sirene, NAF 88.91A | les crèches municipales en régie peuvent manquer |
| Écoles, collèges, lycées | Annuaire de l'Éducation nationale | |
| Culture | Basilic (ministère de la Culture), Panorama des festivals | |
| Industrie / emploi ingénieur | Sirene géolocalisé, établissements ≥ 50 salariés | emplois estimés au milieu de la tranche d'effectif |

Les temps de trajet sont des ordres de grandeur (distance à vol d'oiseau × 1,3, vitesse moyenne selon la distance), pas des itinéraires.

## Mettre à jour ou compléter

```bash
uv venv .venv --python 3.12 && uv pip install --python .venv/bin/python pandas openpyxl requests duckdb pyarrow shapely pillow
.venv/bin/python scripts/download.py     # télécharge les sources (~4 Go, une seule fois)
.venv/bin/python scripts/build.py        # calcule la base, l'Excel et les données de la carte
.venv/bin/python scripts/build_map.py    # régénère la carte
```

Pour ajouter, corriger ou supprimer un lieu, modifier `data/raw/sites_ssa.csv` (une ligne par lieu, coordonnées GPS comprises) puis relancer les deux derniers scripts. Les rayons vélo / voiture se règlent en haut de `scripts/build.py` (`R_VELO_KM`, `R_VOITURE_KM`).

## Mise en ligne et base des choix

- `docs/` est le site publié par GitHub Pages ; il est régénéré par `scripts/build_map.py`. Publier une mise à jour = reconstruire, puis `git commit` et `git push`.
- Les choix et notes sont dans Supabase (projet `affectations-ssa`, région Paris, offre gratuite) : tables `profils` et `choix`, définies dans `supabase/migrations/`. L'adresse et la clé publique sont dans `config.json` (clé faite pour être dans une page web). Le mot de passe de la base est dans `.env.local`, jamais publié.
- L'offre gratuite de Supabase met la base en pause après 7 jours sans activité : `.github/workflows/supabase-anti-veille.yml` l'interroge deux fois par semaine.
