from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "optimuskg" / "3.2"
DOI = "doi:10.7910/DVN/IYNGEV"
SERVER = "https://dataverse.harvard.edu"
USER_AGENT = "DiseaseGraphLab/0.1 (research data audit)"
FILES = [
    "nodes/drug.parquet",
    "nodes/gene.parquet",
    "nodes/pathway.parquet",
    "edges/drug_gene.parquet",
    "edges/pathway_gene.parquet",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    response = requests.get(
        f"{SERVER}/api/datasets/:persistentId/",
        params={"persistentId": DOI}, headers=headers, timeout=60,
    )
    response.raise_for_status()
    data = response.json()["data"]
    version = data["latestVersion"]
    version_label = f"{version['versionNumber']}.{version['versionMinorNumber']}"
    if version_label != "3.2" or version.get("versionState") != "RELEASED":
        raise RuntimeError(f"Unexpected OptimusKG release: {version_label} {version.get('versionState')}")
    if version.get("license", {}).get("name") != "CC BY-NC-SA 4.0":
        raise RuntimeError("Dataset license differs from audited CC BY-NC-SA 4.0")
    catalog = {}
    for item in version["files"]:
        file = item["dataFile"]
        path = "/".join(x for x in [item.get("directoryLabel", ""), file["filename"]] if x)
        catalog[path] = file
    missing = [name for name in FILES if name not in catalog]
    if missing:
        raise RuntimeError(f"Required files missing from release: {missing}")

    OUT.mkdir(parents=True, exist_ok=True)
    records = []
    for relative in FILES:
        entry = catalog[relative]
        target = OUT / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists() or target.stat().st_size != entry["filesize"]:
            temp = target.with_suffix(target.suffix + ".part")
            url = f"{SERVER}/api/access/datafile/{entry['id']}"
            with requests.get(url, headers=headers, stream=True, timeout=(30, 300)) as resp:
                resp.raise_for_status()
                with temp.open("wb") as handle:
                    for chunk in resp.iter_content(1024 * 1024):
                        if chunk:
                            handle.write(chunk)
            if temp.stat().st_size != entry["filesize"]:
                raise RuntimeError(f"Size mismatch for {relative}: got {temp.stat().st_size}, expected {entry['filesize']}")
            temp.replace(target)
        records.append({
            "path": relative,
            "dataverse_file_id": entry["id"],
            "bytes": target.stat().st_size,
            "dataverse_md5": entry.get("md5"),
            "sha256": sha256(target),
        })
    manifest = {
        "dataset": "OptimusKG",
        "persistent_id": DOI,
        "release": version_label,
        "release_state": version.get("versionState"),
        "license": version["license"]["name"],
        "license_uri": version["license"]["uri"],
        "source_url": "https://doi.org/10.7910/DVN/IYNGEV",
        "downloaded_utc": datetime.now(timezone.utc).isoformat(),
        "user_agent": USER_AGENT,
        "files": records,
        "note": "Only the five listed Parquet tables were downloaded; this is not the complete OptimusKG graph.",
    }
    (OUT / "source_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"release": version_label, "files": records, "bytes_total": sum(x["bytes"] for x in records)}, indent=2))


if __name__ == "__main__":
    main()
