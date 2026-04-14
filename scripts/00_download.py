#!/usr/bin/env python3 -u
"""
Usage:
    python -u scripts/00_download.py
"""

import hashlib
import json
import re
import sys
import time
import zipfile
import gzip
import shutil
from pathlib import Path
from urllib.parse import urlparse, urljoin

import requests
from bs4 import BeautifulSoup

sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

# Configuration
BASE_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
MANIFEST_PATH = BASE_DIR / "manifest.json"

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "EPSI-MSPR-I1-2627/1.0 (educational project)"})

MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds
TIMEOUT = 120  # seconds


# Datasets configuration
# Each entry:
#   "id": unique identifier
#   "folder": target subfolder under data/raw/
#   "source_type": "datagouv" | "direct" | "insee_page"
#   "url": URL (API slug for datagouv, direct URL, or INSEE page)
#   "description": human-readable description
#   "filter": optional function to filter resources (datagouv only)

DATASETS = [
    # Référentiels
    {
        "id": "ref_cog_2024",
        "folder": "referentiels",
        "source_type": "insee_page",
        "url": "https://www.insee.fr/fr/information/8377162",
        "description": "COG 2024 - Code Officiel Géographique",
        "link_patterns": [r"v_commune.*\.csv", r"v_commune.*\.zip"],
    },
    {
        "id": "ref_passage_communes",
        "folder": "referentiels",
        "source_type": "insee_page",
        "url": "https://www.insee.fr/fr/information/7766585",
        "description": "Table de passage communes historique",
        "link_patterns": [r"table.*passage", r"historique.*commune"],
    },
    {
        "id": "ref_communes_ze",
        "folder": "referentiels",
        "source_type": "insee_page",
        "url": "https://www.insee.fr/fr/information/4652957",
        "description": "Table communes vers zones d'emploi",
        "link_patterns": [r"zone.*emploi", r"table.*appartenances?"],
    },
    {
        "id": "ref_grille_densite",
        "folder": "referentiels",
        "source_type": "insee_page",
        "url": "https://www.insee.fr/fr/information/8571524",
        "description": "Grille de densité communale INSEE",
        "link_patterns": [r"grille.*densit", r"\.xlsx?$", r"\.csv$"],
    },
    # Élections
    {
        "id": "elections_agregees",
        "folder": "elections",
        "source_type": "datagouv",
        "url": "donnees-des-elections-agregees",
        "description": "Élections agrégées (data.gouv.fr - Etalab)",
    },
    {
        "id": "presidentielle_2002",
        "folder": "elections",
        "source_type": "datagouv",
        "url": "election-presidentielle-2002-resultats-par-bureaux-de-vote",
        "description": "Présidentielle 2002 par bureau de vote",
    },
    # Diplômes (recensement 2021)
    {
        "id": "diplome_2021",
        "folder": "recensement",
        "source_type": "insee_page",
        "url": "https://www.insee.fr/fr/statistiques/8581488?sommaire=8582771",
        "description": "Diplômes-Formation RP 2021",
        "link_patterns": [r"base.*cc.*diplomes?", r"diplom", r"\.zip$"],
    },
    # CSP (recensement 2021)
    {
        "id": "csp_2021",
        "folder": "recensement",
        "source_type": "insee_page",
        "url": "https://www.insee.fr/fr/statistiques/8581444",
        "description": "Emploi-Population active RP 2021",
        "link_patterns": [r"base.*cc.*act", r"emploi.*pop", r"\.zip$"],
    },
    # Chômage
    {
        "id": "chomage_ze",
        "folder": "chomage",
        "source_type": "insee_page",
        "url": "https://www.insee.fr/fr/statistiques/2012804",
        "description": "Taux de chômage localisés par zone d'emploi",
        "link_patterns": [r"taux.*chom", r"zone.*emploi", r"\.xlsx?$"],
    },
    {
        "id": "france_travail",
        "folder": "chomage",
        "source_type": "datagouv",
        "url": "inscrits-a-france-travail-donnees-communales-trimestrielles-brutes",
        "description": "Inscrits France Travail données communales",
    },
    # Filosofi (téléchargement direct)
    {
        "id": "filosofi_2021",
        "folder": "filosofi",
        "source_type": "direct",
        "url": "https://www.insee.fr/fr/statistiques/fichier/7756855/indic-struct-distrib-revenu-2021-COMMUNES_csv.zip",
        "filename": "indic-struct-distrib-revenu-2021-COMMUNES_csv.zip",
        "description": "Filosofi 2021 revenus et pauvreté communaux",
    },
    {
        "id": "filosofi_2017",
        "folder": "filosofi",
        "source_type": "direct",
        "url": "https://www.insee.fr/fr/statistiques/fichier/4291712/indic-struct-distrib-revenu-2017-COMMUNES.zip",
        "filename": "indic-struct-distrib-revenu-2017-COMMUNES.zip",
        "description": "Filosofi 2017 revenus et pauvreté communaux",
    },
    # Population historique
    {
        "id": "population_historique",
        "folder": "recensement",
        "source_type": "insee_page",
        "url": "https://www.insee.fr/fr/statistiques/3698339",
        "description": "Série historique population communale",
        "link_patterns": [r"pop.*communal", r"historique", r"\.xlsx?$"],
    },
    # Structure par âge
    {
        "id": "age_2021",
        "folder": "recensement",
        "source_type": "insee_page",
        "url": "https://www.insee.fr/fr/statistiques/8581696?sommaire=8581933",
        "description": "Évolution et structure de la population RP 2021",
        "link_patterns": [r"base.*cc.*pop", r"evol.*struct", r"\.zip$"],
    },
    # Criminalité
    {
        "id": "criminalite",
        "folder": "criminalite",
        "source_type": "datagouv",
        "url": "bases-statistiques-communale-departementale-et-regionale-de-la-delinquance-enregistree-par-la-police-et-la-gendarmerie-nationales",
        "description": "SSMSI criminalité communale et départementale",
    },
    # Logement
    {
        "id": "logement_2021",
        "folder": "recensement",
        "source_type": "insee_page",
        "url": "https://www.insee.fr/fr/statistiques/8647012",
        "description": "Logement RP 2021",
        "link_patterns": [r"base.*cc.*log", r"logement", r"\.zip$"],
    },
    # Immigration (téléchargements directs)
    {
        "id": "immigres_img1a",
        "folder": "recensement",
        "source_type": "direct",
        "url": "https://www.insee.fr/fr/statistiques/fichier/8582054/TD_IMG1A_2022_csv.zip",
        "filename": "TD_IMG1A_2022_csv.zip",
        "description": "Immigrés par sexe, âge et pays de naissance RP 2022",
    },
    {
        "id": "immigres_img2a",
        "folder": "recensement",
        "source_type": "direct",
        "url": "https://www.insee.fr/fr/statistiques/fichier/8582054/TD_IMG2A_2022_csv.zip",
        "filename": "TD_IMG2A_2022_csv.zip",
        "description": "Immigrés par sexe, âge et ancienneté d'arrivée RP 2022",
    },
    {
        "id": "immigres_img3a",
        "folder": "recensement",
        "source_type": "direct",
        "url": "https://www.insee.fr/fr/statistiques/fichier/8582054/TD_IMG3A_2022_csv.zip",
        "filename": "TD_IMG3A_2022_csv.zip",
        "description": "Immigrés par sexe, diplôme et pays de naissance RP 2022",
    },
    {
        "id": "etrangers_nat1",
        "folder": "recensement",
        "source_type": "direct",
        "url": "https://www.insee.fr/fr/statistiques/fichier/8582032/TD_NAT1_2022_csv.zip",
        "filename": "TD_NAT1_2022_csv.zip",
        "description": "Étrangers par sexe, âge et nationalité RP 2022",
    },
    # Emploi public/privé
    {
        "id": "emploi_2021",
        "folder": "recensement",
        "source_type": "insee_page",
        "url": "https://www.insee.fr/fr/statistiques/8581559?sommaire=8581612",
        "description": "Caractéristiques de l'emploi RP 2021",
        "link_patterns": [r"base.*cc.*caract", r"emploi", r"\.zip$"],
    },
    # RNA (dernier snapshot uniquement)
    {
        "id": "rna",
        "folder": "associations",
        "source_type": "datagouv",
        "url": "repertoire-national-des-associations",
        "description": "Répertoire National des Associations (RNA)",
        "filter_title": "waldec",
        "max_resources": 1,
    },
    # Recensement Dossier Complet (2021)
    {
        "id": "rp_dossier_complet_2021",
        "folder": "recensement",
        "source_type": "direct",
        "url": "https://www.insee.fr/fr/statistiques/fichier/5359146/dossier_complet.zip",
        "filename": "dossier_complet.zip",
        "description": "Base du Dossier Complet RP 2021",
    },
]


# Utility functions
def sha256_file(filepath: Path) -> str:
    """Compute SHA256 hash of a file."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def download_file(url: str, dest: Path) -> bool:
    """Download a file with retries. Returns True if successful."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            print(f"  Téléchargement: {url}")
            print(f"  -> {dest}")
            resp = SESSION.get(url, stream=True, timeout=TIMEOUT, allow_redirects=True)
            resp.raise_for_status()

            dest.parent.mkdir(parents=True, exist_ok=True)
            with open(dest, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)

            size = dest.stat().st_size
            if size == 0:
                print("  ATTENTION: fichier vide, nouvel essai...")
                dest.unlink()
                continue

            print(f"  OK ({size:,} bytes)")
            return True

        except (requests.RequestException, IOError) as e:
            print(f"  Tentative {attempt}/{MAX_RETRIES} échouée: {e}")
            if attempt < MAX_RETRIES:
                print(f"  Nouvel essai dans {RETRY_DELAY}s...")
                time.sleep(RETRY_DELAY)
    return False


def extract_archive(filepath: Path):
    """Extract ZIP or GZ archives in place."""
    if filepath.suffix.lower() == ".zip":
        extract_dir = filepath.parent / filepath.stem
        if extract_dir.exists() and any(extract_dir.iterdir()):
            print(f"  Déjà extrait: {extract_dir}")
            return
        print(f"  Extraction ZIP: {filepath.name}")
        try:
            with zipfile.ZipFile(filepath, "r") as zf:
                zf.extractall(extract_dir)
            print(f"  Extrait dans: {extract_dir}")
        except zipfile.BadZipFile:
            print(f"  ATTENTION: fichier ZIP corrompu: {filepath}")

    elif filepath.suffix.lower() == ".gz" and filepath.stem.endswith(
        (".csv", ".parquet", ".json", ".txt")
    ):
        out_path = filepath.parent / filepath.stem
        if out_path.exists():
            print(f"  Déjà extrait: {out_path}")
            return
        print(f"  Extraction GZ: {filepath.name}")
        with gzip.open(filepath, "rb") as f_in, open(out_path, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)
        print(f"  Extrait dans: {out_path}")


# Source-specific fetchers
def fetch_datagouv_resources(slug: str) -> list[dict]:
    """Fetch resource list from data.gouv.fr API.

    Prefers Parquet over CSV when both exist for the same data,
    since Parquet is much smaller and faster to read.
    """
    api_url = f"https://www.data.gouv.fr/api/1/datasets/{slug}/"
    print(f"  Requête API data.gouv.fr: {slug}")
    resp = SESSION.get(api_url, timeout=TIMEOUT)
    resp.raise_for_status()
    data = resp.json()

    resources = []
    for r in data.get("resources", []):
        url = r.get("url", "")
        title = r.get("title", "")
        fmt = r.get("format", "").lower()
        size = r.get("filesize") or 0

        ext = Path(urlparse(url).path).suffix.lower()
        if ext in (".csv", ".parquet", ".xlsx", ".xls", ".zip", ".txt", ".gz", ".7z"):
            resources.append(
                {
                    "url": url,
                    "title": title,
                    "format": fmt or ext.lstrip("."),
                    "size": size,
                }
            )
        elif fmt in ("csv", "parquet", "xlsx", "xls", "zip", "txt"):
            resources.append(
                {
                    "url": url,
                    "title": title,
                    "format": fmt,
                    "size": size,
                }
            )

    # Prefer Parquet over CSV when both exist for the same content
    parquet_titles = {r["title"] for r in resources if r["format"] == "parquet"}
    if parquet_titles:
        filtered = []
        for r in resources:
            if r["format"] == "csv" and r["title"] in parquet_titles:
                print(f"  SKIP CSV (Parquet disponible): {r['title']}")
                continue
            filtered.append(r)
        resources = filtered

    print(f"  {len(resources)} ressources téléchargeables trouvées")
    return resources


def fetch_insee_page_links(url: str, patterns: list[str]) -> list[str]:
    """Scrape an INSEE page for download links matching patterns."""
    print(f"  Récupération page INSEE: {url}")
    resp = SESSION.get(url, timeout=TIMEOUT)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "lxml")

    download_links = []
    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]
        text = a_tag.get_text(strip=True).lower()
        href_lower = href.lower()

        # Look for download links (files)
        is_file = any(
            href_lower.endswith(ext)
            for ext in (".csv", ".xlsx", ".xls", ".zip", ".gz", ".parquet", ".txt")
        )
        if not is_file:
            # Also check for links containing "télécharg" or "download"
            if "télécharg" not in text and "télécharge" not in href_lower:
                continue

        # Make absolute URL
        full_url = urljoin(url, href)
        download_links.append(full_url)

    # Deduplicate
    download_links = list(dict.fromkeys(download_links))

    # Filter by patterns if provided
    if patterns and download_links:
        filtered = []
        for link in download_links:
            link_lower = link.lower()
            if any(re.search(p, link_lower) for p in patterns):
                filtered.append(link)
        if filtered:
            print(
                f"  Filtrage {len(download_links)} liens → {len(filtered)} correspondant aux patterns"
            )
            download_links = filtered
        else:
            print(
                f"  ATTENTION: aucun lien ne correspond aux patterns {patterns}, conservation des {len(download_links)} liens"
            )

    if not download_links:
        print(f"  ATTENTION: aucun lien de téléchargement trouvé sur {url}")
        print(
            "  Téléchargement manuel peut-être nécessaire. URL sauvegardée dans le manifest."
        )

    print(f"  {len(download_links)} liens de téléchargement trouvés")
    return download_links


def safe_filename(url: str, title: str = "") -> str:
    """Generate a safe filename from URL or title."""
    parsed = urlparse(url)
    name = Path(parsed.path).name
    if name and len(name) > 3:
        # Clean up query params from filename
        return re.sub(r"[^\w\-_\.]", "_", name)
    if title:
        safe = re.sub(r"[^\w\-_\.]", "_", title)
        return safe[:100]
    return hashlib.md5(url.encode()).hexdigest()[:12]


# Manifest management
def load_manifest() -> dict:
    """Load existing manifest or return empty dict."""
    if MANIFEST_PATH.exists():
        with open(MANIFEST_PATH) as f:
            return json.load(f)
    return {}


def save_manifest(manifest: dict):
    """Save manifest to disk."""
    with open(MANIFEST_PATH, "w") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)


def is_already_downloaded(
    manifest: dict, dataset_id: str, filename: str, filepath: Path
) -> bool:
    """Check if a file is already downloaded and matches the manifest hash."""
    key = f"{dataset_id}/{filename}"
    if key not in manifest:
        return False
    if not filepath.exists():
        return False
    expected_hash = manifest[key].get("sha256")
    if not expected_hash:
        return False
    actual_hash = sha256_file(filepath)
    return actual_hash == expected_hash


# Main download logic
def process_dataset(ds: dict, manifest: dict) -> list[dict]:
    """Process a single dataset config entry. Returns list of downloaded file infos."""
    dataset_id = ds["id"]
    folder = BASE_DIR / ds["folder"]
    source_type = ds["source_type"]
    description = ds["description"]

    print(f"\n{'=' * 60}")
    print(f"[{dataset_id}] {description}")
    print(f"{'=' * 60}")

    folder.mkdir(parents=True, exist_ok=True)
    downloaded = []

    if source_type == "datagouv":
        try:
            resources = fetch_datagouv_resources(ds["url"])
        except requests.RequestException as e:
            print(f"  ERREUR requête API: {e}")
            return downloaded

        # Filter resources by title keyword if specified
        filter_title = ds.get("filter_title")
        if filter_title:
            filtered = [
                r for r in resources if filter_title.lower() in r["title"].lower()
            ]
            if filtered:
                print(
                    f"  Filtrage par titre '{filter_title}': {len(resources)} → {len(filtered)} ressources"
                )
                resources = filtered
            else:
                print(
                    f"  ATTENTION: aucune ressource ne correspond au filtre '{filter_title}', conservation de toutes"
                )

        max_res = ds.get("max_resources")
        successful = 0

        for res in resources:
            if max_res and successful >= max_res:
                break
            url = res["url"]
            filename = safe_filename(url, res.get("title", ""))
            filepath = folder / filename
            manifest_key = f"{dataset_id}/{filename}"

            if is_already_downloaded(manifest, dataset_id, filename, filepath):
                print(f"  SKIP (déjà téléchargé): {filename}")
                successful += 1
                continue

            if download_file(url, filepath):
                file_hash = sha256_file(filepath)
                info = {
                    "dataset_id": dataset_id,
                    "source_url": url,
                    "source_page": f"https://www.data.gouv.fr/datasets/{ds['url']}",
                    "title": res.get("title", ""),
                    "format": res.get("format", ""),
                    "filename": filename,
                    "path": str(filepath.relative_to(BASE_DIR)),
                    "sha256": file_hash,
                    "size": filepath.stat().st_size,
                    "download_date": time.strftime("%Y-%m-%d %H:%M:%S"),
                }
                manifest[manifest_key] = info
                downloaded.append(info)
                extract_archive(filepath)
                successful += 1

    elif source_type == "insee_page":
        url = ds["url"]
        patterns = ds.get("link_patterns", [])

        try:
            links = fetch_insee_page_links(url, patterns)
        except requests.RequestException as e:
            print(f"  ERREUR récupération page: {e}")
            # Still record the page URL in manifest for manual download
            manifest[f"{dataset_id}/_page"] = {
                "dataset_id": dataset_id,
                "source_url": url,
                "description": description,
                "status": "error",
                "error": str(e),
                "download_date": time.strftime("%Y-%m-%d %H:%M:%S"),
            }
            return downloaded

        if not links:
            manifest[f"{dataset_id}/_page"] = {
                "dataset_id": dataset_id,
                "source_url": url,
                "description": description,
                "status": "no_links_found",
                "note": "Téléchargement manuel peut-être nécessaire",
                "download_date": time.strftime("%Y-%m-%d %H:%M:%S"),
            }
            return downloaded

        for link_url in links:
            filename = safe_filename(link_url)
            filepath = folder / filename
            manifest_key = f"{dataset_id}/{filename}"

            if is_already_downloaded(manifest, dataset_id, filename, filepath):
                print(f"  SKIP (déjà téléchargé): {filename}")
                continue

            if download_file(link_url, filepath):
                file_hash = sha256_file(filepath)
                info = {
                    "dataset_id": dataset_id,
                    "source_url": link_url,
                    "source_page": url,
                    "description": description,
                    "filename": filename,
                    "path": str(filepath.relative_to(BASE_DIR)),
                    "sha256": file_hash,
                    "size": filepath.stat().st_size,
                    "download_date": time.strftime("%Y-%m-%d %H:%M:%S"),
                }
                manifest[manifest_key] = info
                downloaded.append(info)
                extract_archive(filepath)

    elif source_type == "direct":
        url = ds["url"]
        filename = ds.get("filename") or safe_filename(url)
        filepath = folder / filename
        manifest_key = f"{dataset_id}/{filename}"

        if is_already_downloaded(manifest, dataset_id, filename, filepath):
            print(f"  SKIP (déjà téléchargé): {filename}")
            return downloaded

        if download_file(url, filepath):
            file_hash = sha256_file(filepath)
            info = {
                "dataset_id": dataset_id,
                "source_url": url,
                "description": description,
                "filename": filename,
                "path": str(filepath.relative_to(BASE_DIR)),
                "sha256": file_hash,
                "size": filepath.stat().st_size,
                "download_date": time.strftime("%Y-%m-%d %H:%M:%S"),
            }
            manifest[manifest_key] = info
            downloaded.append(info)
            extract_archive(filepath)

    return downloaded


def main():
    print("=" * 60)
    print("Téléchargement des données")
    print("=" * 60)
    print(f"Répertoire cible: {BASE_DIR}")
    print(f"Manifeste: {MANIFEST_PATH}")

    manifest = load_manifest()
    total_downloaded = 0
    total_errors = 0

    for ds in DATASETS:
        try:
            results = process_dataset(ds, manifest)
            total_downloaded += len(results)
        except Exception as e:
            print(f"  ERREUR CRITIQUE sur {ds['id']}: {e}")
            total_errors += 1

        # Save manifest after each dataset (crash recovery)
        save_manifest(manifest)

    # Final summary
    print(f"\n{'=' * 60}")
    print("RESUME")
    print(f"{'=' * 60}")
    print(f"Datasets traités: {len(DATASETS)}")
    print(f"Fichiers téléchargés: {total_downloaded}")
    print(f"Erreurs critiques: {total_errors}")
    print(f"Manifeste: {MANIFEST_PATH}")

    # List files that need manual download
    manual = [
        k
        for k, v in manifest.items()
        if isinstance(v, dict) and v.get("status") in ("no_links_found", "error")
    ]
    if manual:
        print(
            f"\nATTENTION: {len(manual)} datasets nécessitent un téléchargement manuel:"
        )
        for k in manual:
            info = manifest[k]
            print(f"  - {info.get('dataset_id')}: {info.get('source_url')}")
            print(
                f"    -> Télécharger dans: {BASE_DIR / info.get('dataset_id', '').split('/')[0] if '/' in info.get('dataset_id', '') else ''}"
            )

    # List all downloaded files
    print(f"\nFichiers dans {BASE_DIR}:")
    for folder in sorted(BASE_DIR.iterdir()):
        if folder.is_dir():
            files = list(folder.rglob("*"))
            file_count = sum(1 for f in files if f.is_file())
            print(f"  {folder.name}/: {file_count} fichiers")


if __name__ == "__main__":
    main()
