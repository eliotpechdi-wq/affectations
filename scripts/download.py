"""Télécharge les jeux de données publics utilisés par build.py (idempotent).

Usage : .venv/bin/python scripts/download.py
"""
import gzip
import shutil
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
SIRENE = ROOT / "data" / "cache" / "sirene"

SOURCES = {
    RAW / "communes.json": "https://geo.api.gouv.fr/communes?fields=nom,code,population,centre,codeDepartement,codeRegion,codesPostaux&format=json",
    RAW / "airports.csv": "https://davidmegginson.github.io/ourairports-data/airports.csv",
    RAW / "gtfs_tgv.zip": "https://eu.ftp.opendatasoft.com/sncf/gtfs/export_gtfs_voyages.zip",
    RAW / "basilic.csv": "https://static.data.gouv.fr/resources/base-des-lieux-et-equipements-culturels-basilic/20260218-084338/base-des-lieux-et-des-equipements-culturels.csv",
    RAW / "festivals.csv": "https://static.data.gouv.fr/resources/panorama-des-festivals/20250827-130609/panorama-des-festivals.csv",
    RAW / "dvf_stats.csv": "https://data-pipeline-open.s3.sbg.io.cloud.ovh.net/dvf/stats_whole_period.csv",
    RAW / "education.csv": "https://data.education.gouv.fr/api/explore/v2.1/catalog/datasets/fr-en-annuaire-education/exports/csv?delimiter=%3B",
    SIRENE / "etab.parquet": "https://static.data.gouv.fr/resources/base-sirene-des-entreprises-et-de-leurs-etablissements-siren-siret/20261001-073823/stock-stocketablissement-parquet.parquet",
    SIRENE / "geoloc.parquet": "https://static.data.gouv.fr/resources/geolocalisation-des-etablissements-du-repertoire-sirene-pour-les-etudes-statistiques/20260921-065930/geoloc-geolocalisationetablissement-sirene-pour-etudes-statistiques-parquet.parquet",
    SIRENE / "ul.parquet": "https://static.data.gouv.fr/resources/base-sirene-des-entreprises-et-de-leurs-etablissements-siren-siret/20261001-073325/stock-stockunitelegale-parquet.parquet",
}


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    SIRENE.mkdir(parents=True, exist_ok=True)
    for dest, url in SOURCES.items():
        if dest.exists() and dest.stat().st_size > 0:
            print(f"déjà présent : {dest.name}")
            continue
        print(f"téléchargement : {dest.name}")
        subprocess.run(["curl", "-sL", "-o", str(dest), url], check=True)

    # L'export de l'annuaire de l'éducation arrive compressé en gzip.
    plain = RAW / "education_plain.csv"
    if not plain.exists():
        with open(RAW / "education.csv", "rb") as f:
            magic = f.read(2)
        opener = gzip.open if magic == b"\x1f\x8b" else open
        with opener(RAW / "education.csv", "rb") as src, open(plain, "wb") as dst:
            shutil.copyfileobj(src, dst)

    gtfs_dir = RAW / "gtfs_tgv"
    if not gtfs_dir.exists():
        zipfile.ZipFile(RAW / "gtfs_tgv.zip").extractall(gtfs_dir)


if __name__ == "__main__":
    main()
