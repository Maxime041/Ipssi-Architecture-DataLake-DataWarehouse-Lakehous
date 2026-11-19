# Jour 3 - UC-06 : transformation, qualité et zones Silver / Gold

Team **MaxMag** : Maxime DANINO - Awadi BEDJA - Gurvan Godin

Chaîne PySpark qui lit les données TPCx-BB de la zone Bronze (HDFS, Jour 2), les nettoie, les
transforme et produit les zones Silver et Gold en Parquet, avec des contrôles qualité.

## Prérequis

| Élément | Version observée |
|---|---|
| Système | Ubuntu 24.04.5 LTS sous WSL 2 |
| Python | 3.12.3, environnement virtuel `~/retail-intelligence/tp3/.venv` |
| PySpark / Spark | 4.3.0 (mode `local[*]`, 16 cœurs, 4 Go pour le driver) |
| Java utilisé par Spark | OpenJDK 21 |
| Hadoop / HDFS | 3.5.0, pseudo-distribué, `hdfs://localhost:9000` |
| JupyterLab | 4.6.6, noyau « Python (TP3 Retail) » |

Installation (une seule fois) : `UC06_traitements/installation/installer_environnement.sh`
(après `sudo apt install python3-venv python3-pip`). Les versions exactes de tous les paquets
sont dans `UC06_preuves/etape1/requirements_observes.txt`.

Le dossier de travail `~/retail-intelligence/tp3` contient deux liens vers ce dépôt :
`scripts -> J3/UC06_traitements` et `notebooks -> J3/UC06_notebooks`
(script `installation/lier_dossiers_depot.sh`).

## Emplacement des données

| Zone | Chemin HDFS | Contenu |
|---|---|---|
| Bronze (entrée) | `/retail-lake/bronze/tpcxbb/<table>/lot=initial\|refresh/` | Fichiers `.dat` déposés au Jour 2, en lecture seule pour ce TP |
| Silver | `/retail-lake/silver/` | `store_sales`, `item`, `store`, `date_dim`, `ventes_detaillees` |
| Gold | `/retail-lake/gold/` | `fait_ventes`, `dim_date`, `dim_produit`, `dim_magasin`, `kpi_ventes_magasin_mois`, `kpi_ventes_categorie_mois` |
| Rejets | `/retail-lake/quality/rejets/<table>/` | Lignes écartées avec leurs motifs |
| Contrôles | `/retail-lake/quality/controles/` | Rapports de contrôle qualité |
| Journaux | `/retail-lake/logs/traitements/` | Un journal JSON par exécution Silver et Gold |

Repli si HDFS est indisponible : `KIT_LOCAL` (`~/kit_tpcxbb`, lien vers le kit local).

## Paramètres

Tous les chemins et réglages sont dans `UC06_traitements/config.py` : racine HDFS, zones,
mémoire du driver, fuseau horaire, réplication HDFS (1, notre HDFS n'a qu'un DataNode).
`UC06_ESSAI=1` envoie les sorties Gold, contrôles et preuves dans un espace d'essai
(`hdfs:///tmp/uc06_essai`) pour mettre un traitement au point sans toucher aux zones officielles.

## Organisation du code

| Fichier | Rôle |
|---|---|
| `config.py` | Paramètres, chemins, session Spark |
| `schemas.py` | Noms de colonnes (pas d'en-tête dans les `.dat`) et types cibles des 4 sources |
| `nettoyage.py` | Les 17 règles de nettoyage (N01 à N17) : rejets avec motifs, conservation des valeurs atypiques |
| `transformations.py` | Renommage, colonnes calculées, jointures vérifiées, agrégations |
| `gold.py` | Définition et documentation des jeux Gold |
| `dictionnaire.py` | Description des colonnes Silver |
| `01_` à `10_*.py` | Une étape du TP chacun (voir ci-dessous) |
| `test_nettoyage.py` | Test des règles de rejet sur 11 lignes synthétiques |
| `run.sh` | Lance un script dans le venv (démarre HDFS si besoin et attend la fin du mode sans échec) |
| `run_pipeline.sh` | Enchaîne les étapes dans l'ordre et range chaque journal dans `UC06_preuves/etapeN` |
| `run_notebook.sh` | Exécute un notebook avec le noyau du TP |

## Ordre d'exécution

```bash
cd ~/retail-intelligence/tp3/scripts
./run_pipeline.sh            # toutes les étapes, dans l'ordre
./run_pipeline.sh 6 7        # ou seulement certaines
./run_notebook.sh 01_exploration.ipynb   # étape 3 (notebook)
```

| Ordre | Script | Lit | Écrit |
|---|---|---|---|
| 1 | `01_verif_environnement.py` | Bronze (store) | test local et HDFS (supprimé) |
| 2 | `02_inventaire_sources.py` | Bronze | preuves uniquement |
| 3 | `notebooks/01_exploration.ipynb` | Bronze | notebook exécuté |
| 4 | `04_appliquer_nettoyage.py`, `test_nettoyage.py` | Bronze | preuves uniquement |
| 5 | `05_transformations.py` | Bronze | preuves uniquement |
| 6 | `06_produire_silver.py` | Bronze | Silver, rejets, journal |
| 7 | `07_produire_gold.py` | Silver | Gold, journal |
| 8 | `08_formats_parquet.py` | Silver, Gold | dossier temporaire (supprimé) |
| 9 | `09_controles_qualite.py` | Silver, Gold, rejets | quality/controles |
| 10 | `10_verifier_chaine.py` | toutes les zones | preuves uniquement |

Les étapes 6 et 7 sont relançables : chaque sortie est remplacée dans son propre dossier
(`overwrite`), jamais dans Bronze.

## Sorties produites

- Silver : 5 tables, 10 fichiers Parquet, 177,8 Mo (`UC06_preuves/etape6`).
- Gold : 6 jeux, dont 2 jeux d'indicateurs (magasin x mois, catégorie x mois) (`UC06_preuves/etape7`).
- Documents : une fiche par étape (`UC06_etapeN_*.pdf`), les questions de recul
  (`UC06_questions_de_recul.pdf`) et le notebook d'exploration.

## Contrôles disponibles

- Après chaque écriture (étapes 6 et 7) : lignes relues, schéma, clé unique, cohérence du chiffre d'affaires.
- Étape 9 : 49 contrôles (complétude, unicité, types, cohérence, volumes, clés, intégrité) avec statut OK / ALERTE / KO.
- Étape 10 : présence de toutes les sorties et des journaux, test des règles de rejet.

## Limites connues

- Mode local sur un seul PC : pas de traitement distribué, temps non représentatifs d'un cluster.
- HDFS mono-nœud, une seule copie des blocs ; WSL arrête HDFS quand Ubuntu s'éteint (`run.sh` le relance).
- Périmètre : ventes en magasin et 3 dimensions ; ventes web, retours et stocks non traités.
- Données synthétiques : marges négatives (74 %), panier moyen très élevé, marques et noms de produits aléatoires.
- Parquet seul n'est pas une table transactionnelle : une écriture interrompue peut laisser un dossier incomplet.
- Spark 4 est en mode ANSI : les conversions utilisent `try_cast`, les sommes risquant un dépassement sont évitées.
