"""Fetch reproducible, candidate-scoped PubMed E-utilities search snapshots."""
from __future__ import annotations

import csv
import hashlib
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REPORTS = ROOT / "reports" / "top10_kg"
FROZEN_PATH = REPORTS / "02_top10_frozen_manifest.json"
RAW_ROOT = ROOT / "data" / "top10_kg" / "raw" / "pubmed" / "top10_review_v1"
OUTPUT = ROOT / "data" / "top10_kg" / "evidence" / "top10_pubmed_search_results.csv"
MANIFEST = ROOT / "data" / "top10_kg" / "evidence" / "top10_pubmed_search_manifest.json"
API_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
USER_AGENT = "ER-DReKG-Top10-literature-audit/1.0 (candidate-scoped evidence retrieval)"

ALIASES = {
    "BRD-K44227013": ["ponatinib", "AP24534"],
    "BRD-K16485616": ["mocetinostat", "MGCD0103"],
    "BRD-K56405753": ["MK-2461", "MK2461"],
    "BRD-K92093830": ["doxorubicin", "Adriamycin"],
    "BRD-K76694128": ["rebastinib", "DCC-2036"],
    "BRD-K50000283": ["PHA-767491", "PHA767491"],
    "BRD-K11153516": ["iniparib", "BSI-201"],
    "BRD-A00147595": ["balaglitazone", "DRF-2593"],
    "BRD-K13094524": ["PFI-1"],
    "BRD-K83837640": ["JNJ-26481585", "quisinostat", "J&J-26481585"],
}

QUERY_GROUPS = {
    "mechanism": '("mechanism of action"[Title/Abstract] OR pharmacology[Title/Abstract] OR inhibitor[Title/Abstract] OR agonist[Title/Abstract])',
    "direct_target": '("direct target"[Title/Abstract] OR target[Title/Abstract] OR binding[Title/Abstract] OR IC50[Title/Abstract])',
    "breast_cancer": '("breast cancer"[Title/Abstract] OR "breast carcinoma"[Title/Abstract] OR "breast neoplasm"[Title/Abstract])',
    "er_positive": '("ER-positive"[Title/Abstract] OR "estrogen receptor-positive"[Title/Abstract] OR "hormone receptor-positive"[Title/Abstract] OR MCF7[Title/Abstract] OR T47D[Title/Abstract])',
    "MCF7": '(MCF7[Title/Abstract] OR "MCF-7"[Title/Abstract])',
    "T47D": '(T47D[Title/Abstract] OR "T-47D"[Title/Abstract])',
    "pathway": '(pathway[Title/Abstract] OR signalling[Title/Abstract] OR signaling[Title/Abstract])',
}


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def request_bytes(endpoint: str, params: dict[str, str]) -> tuple[bytes, int, str]:
    url = f"{API_BASE}/{endpoint}?{urllib.parse.urlencode(params)}"
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json, application/xml"})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(request, timeout=45) as response:
                return response.read(), response.status, url
        except urllib.error.HTTPError as exc:
            if exc.code not in {429, 500, 502, 503, 504} or attempt == 4:
                raise
            time.sleep(min(2 ** attempt, 12))
        except (TimeoutError, urllib.error.URLError):
            if attempt == 4:
                raise
            time.sleep(min(2 ** attempt, 12))
    raise RuntimeError("unreachable retry state")


def request_or_cache(endpoint: str, params: dict[str, str], raw_path: Path) -> tuple[bytes, int | str, str, str]:
    if raw_path.is_file():
        return raw_path.read_bytes(), "cached_snapshot", f"cache://{raw_path.name}", "cache"
    payload, status, url = request_bytes(endpoint, params)
    return payload, status, url, "ncbi_api"


def aliases_query(aliases: list[str]) -> str:
    return "(" + " OR ".join(f'"{alias}"[Title/Abstract]' for alias in aliases) + ")"


def parse_article(article: ET.Element) -> dict[str, str]:
    def first_text(*paths: str) -> str:
        for path in paths:
            node = article.find(path)
            if node is not None:
                value = " ".join("".join(node.itertext()).split())
                if value:
                    return value
        return ""

    is_book_article = article.tag == "PubmedBookArticle"
    pmid = first_text("./BookDocument/PMID", "./MedlineCitation/PMID")
    title = first_text(
        "./BookDocument/ArticleTitle", "./MedlineCitation/Article/ArticleTitle",
    )
    journal = first_text(
        "./MedlineCitation/Article/Journal/Title", "./BookDocument/Book/BookTitle",
    )
    year = first_text(
        "./MedlineCitation/Article/Journal/JournalIssue/PubDate/Year",
        "./BookDocument/Book/PubDate/Year", "./BookDocument/Book/PubDate",
    )
    if not year:
        year = first_text("./MedlineCitation/Article/Journal/JournalIssue/PubDate/MedlineDate")
    abstract_parts = []
    abstract_nodes = article.findall("./MedlineCitation/Article/Abstract/AbstractText")
    if not abstract_nodes:
        abstract_nodes = article.findall("./BookDocument/Abstract/AbstractText")
    for part in abstract_nodes:
        label = part.attrib.get("Label") or part.attrib.get("NlmCategory") or ""
        value = " ".join("".join(part.itertext()).split())
        abstract_parts.append(f"{label}: {value}" if label else value)
    dois = [node.text or "" for node in article.findall("./PubmedData/ArticleIdList/ArticleId[@IdType='doi']")]
    dois.extend(node.text or "" for node in article.findall("./BookDocument/ArticleIdList/ArticleId[@IdType='doi']"))
    pubtypes = [" ".join("".join(node.itertext()).split()) for node in article.findall("./MedlineCitation/Article/PublicationTypeList/PublicationType")]
    if is_book_article:
        pubtypes.extend(" ".join("".join(node.itertext()).split()) for node in article.findall("./BookDocument/PublicationType"))
        pubtypes.insert(0, "Book")
    return {
        "pmid": pmid,
        "title": title,
        "journal": journal,
        "year": year,
        "doi": "; ".join(filter(None, dois)),
        "publication_types": "; ".join(filter(None, pubtypes)),
        "abstract": "\n".join(abstract_parts),
        "pubmed_url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else "",
    }


def parse_records(root: ET.Element) -> list[dict[str, str]]:
    records = [*root.findall(".//PubmedArticle"), *root.findall(".//PubmedBookArticle")]
    return [parsed for record in records if (parsed := parse_article(record))["pmid"]]


def main() -> None:
    frozen = json.loads(FROZEN_PATH.read_text(encoding="utf-8"))
    if len(frozen.get("items", [])) != 10:
        raise SystemExit("Expected the frozen formal Top 10")
    if {item["pert_id"] for item in frozen["items"]} != set(ALIASES):
        raise SystemExit("Alias map must exactly cover the frozen Top 10 pert_id values")
    snapshot_time = datetime.now(timezone.utc).isoformat()
    (RAW_ROOT / "esearch").mkdir(parents=True, exist_ok=True)
    (RAW_ROOT / "efetch").mkdir(parents=True, exist_ok=True)
    calls: list[dict[str, object]] = []
    ids_by_drug: dict[str, dict[str, set[str]]] = {}
    all_raw_files: dict[str, str] = {}

    for item in frozen["items"]:
        pert_id = item["pert_id"]
        aliases = ALIASES[pert_id]
        drug_term = aliases_query(aliases)
        ids_by_drug[pert_id] = {}
        for group, topic_term in QUERY_GROUPS.items():
            query = f"{drug_term} AND {topic_term}"
            raw_name = f"{pert_id}__{group}.json"
            raw_path = RAW_ROOT / "esearch" / raw_name
            payload, status, url, response_source = request_or_cache("esearch.fcgi", {
                "db": "pubmed", "term": query, "retmode": "json", "retmax": "100", "sort": "relevance",
            }, raw_path)
            if response_source == "ncbi_api":
                raw_path.write_bytes(payload)
            raw_hash = sha256_bytes(payload)
            all_raw_files[f"esearch/{raw_name}"] = raw_hash
            result = json.loads(payload.decode("utf-8"))["esearchresult"]
            ids = set(result.get("idlist", []))
            ids_by_drug[pert_id][group] = ids
            calls.append({
                "stage": "esearch", "pert_id": pert_id, "drug_name": item["pert_iname"], "query_group": group,
                "aliases": aliases, "query": query, "request_url": url, "http_status": status, "response_source": response_source,
                "result_count": int(result.get("count", 0)), "returned_count": len(ids),
                "result_ids": sorted(ids), "response_file": f"esearch/{raw_name}", "response_sha256": raw_hash,
            })
            if response_source == "ncbi_api":
                time.sleep(0.36)  # stay below the NCBI 3 requests/second guidance without an API key

    curated_refs_by_pert: dict[str, set[str]] = {item["pert_id"]: set() for item in frozen["items"]}
    with (REPORTS / "external_disease_evidence.csv").open(encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            curated_refs_by_pert[row["pert_id"]].update(re.findall(r"\b\d{7,9}\b", row.get("source_id", "")))
    mechanism_path = ROOT / "data" / "top10_kg" / "evidence" / "chembl_mechanisms.csv"
    if mechanism_path.is_file():
        with mechanism_path.open(encoding="utf-8-sig", newline="") as stream:
            for row in csv.DictReader(stream):
                refs = json.loads(row.get("mechanism_refs", "[]") or "[]")
                curated_refs_by_pert[row["pert_id"]].update(str(ref["ref_id"]) for ref in refs if ref.get("ref_type") == "PubMed" and str(ref.get("ref_id", "")).isdigit())
    external_claim_path = REPORTS / "external_identity_and_mechanism_evidence.csv"
    if external_claim_path.is_file():
        with external_claim_path.open(encoding="utf-8-sig", newline="") as stream:
            for row in csv.DictReader(stream):
                curated_refs_by_pert[row["pert_id"]].update(re.findall(r"PMID\s+(\d{7,9})", row.get("evidence_source", "")))

    result_rows: list[dict[str, str]] = []
    for item in frozen["items"]:
        pert_id = item["pert_id"]
        ids_by_group = ids_by_drug[pert_id]
        union_ids = set().union(*ids_by_group.values())
        id_frequency: dict[str, int] = {}
        for ids in ids_by_group.values():
            for pmid in ids:
                id_frequency[pmid] = id_frequency.get(pmid, 0) + 1
        # Fetch every returned unique record for this candidate, chunked to 100 IDs per API call.
        ordered_ids = sorted(union_ids, key=lambda pmid: (-id_frequency[pmid], -int(pmid)))
        articles: dict[str, dict[str, str]] = {}
        for chunk_index in range(0, len(ordered_ids), 100):
            chunk = ordered_ids[chunk_index:chunk_index + 100]
            raw_name = f"{pert_id}__{chunk_index // 100:03d}.xml"
            raw_path = RAW_ROOT / "efetch" / raw_name
            payload, status, url, response_source = request_or_cache("efetch.fcgi", {
                "db": "pubmed", "id": ",".join(chunk), "retmode": "xml", "rettype": "abstract",
            }, raw_path)
            if response_source == "ncbi_api":
                raw_path.write_bytes(payload)
            raw_hash = sha256_bytes(payload)
            all_raw_files[f"efetch/{raw_name}"] = raw_hash
            root = ET.fromstring(payload)
            parsed_records = parse_records(root)
            for parsed in parsed_records:
                articles[parsed["pmid"]] = parsed
            calls.append({
                "stage": "efetch", "pert_id": pert_id, "drug_name": item["pert_iname"],
                "requested_pmids": chunk, "returned_articles": len(parsed_records),
                "request_url": url, "http_status": status, "response_source": response_source, "response_file": f"efetch/{raw_name}", "response_sha256": raw_hash,
            })
            if response_source == "ncbi_api":
                time.sleep(0.36)
        for pmid in ordered_ids:
            parsed = articles.get(pmid, {"pmid": pmid, "title": "", "journal": "", "year": "", "doi": "", "publication_types": "", "abstract": "", "pubmed_url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"})
            matching_groups = [group for group, ids in ids_by_group.items() if pmid in ids]
            result_rows.append({
                "rank": str(item["rank"]), "pert_id": pert_id, "drug_name": item["pert_iname"],
                "pmid": pmid, **parsed, "matched_query_groups": ";".join(matching_groups),
                "query_match_count": str(id_frequency[pmid]), "screening_status": "not_manually_screened",
                "review_note": "PubMed search result only; not a curated mechanism or disease claim.",
            })

    rows_by_pert_pmid = {(row["pert_id"], row["pmid"]): row for row in result_rows}
    missing_reference_ids: set[str] = set()
    for pert_id, pmids in curated_refs_by_pert.items():
        for pmid in pmids:
            row = rows_by_pert_pmid.get((pert_id, pmid))
            if row:
                if "curated_source_reference" not in row["matched_query_groups"].split(";"):
                    row["matched_query_groups"] += ";curated_source_reference"
                row["review_note"] = "Also cited by an existing manually curated source record; this search cache does not create or upgrade the claim."
            else:
                missing_reference_ids.add(pmid)
    fetched_curated: dict[str, dict[str, str]] = {}
    missing_ordered = sorted(missing_reference_ids)
    for chunk_index in range(0, len(missing_ordered), 100):
        chunk = missing_ordered[chunk_index:chunk_index + 100]
        request_ids_sha256 = sha256_bytes(",".join(chunk).encode("ascii"))
        raw_name = f"direct_curated_references__{chunk_index // 100:03d}_{request_ids_sha256[:12]}.xml"
        raw_path = RAW_ROOT / "efetch" / raw_name
        payload, status, url, response_source = request_or_cache("efetch.fcgi", {
            "db": "pubmed", "id": ",".join(chunk), "retmode": "xml", "rettype": "abstract",
        }, raw_path)
        if response_source == "ncbi_api":
            raw_path.write_bytes(payload)
        raw_hash = sha256_bytes(payload)
        all_raw_files[f"efetch/{raw_name}"] = raw_hash
        root = ET.fromstring(payload)
        parsed_records = parse_records(root)
        for parsed in parsed_records:
            fetched_curated[parsed["pmid"]] = parsed
        calls.append({"stage": "efetch_curated_reference", "requested_pmids": chunk,
                      "returned_articles": len(parsed_records), "request_url": url,
                      "http_status": status, "response_source": response_source, "request_ids_sha256": request_ids_sha256,
                      "response_file": f"efetch/{raw_name}", "response_sha256": raw_hash})
        if response_source == "ncbi_api":
            time.sleep(0.36)
    by_pert = {item["pert_id"]: item for item in frozen["items"]}
    for pert_id, pmids in curated_refs_by_pert.items():
        for pmid in sorted(pmids):
            if (pert_id, pmid) in rows_by_pert_pmid:
                continue
            parsed = fetched_curated.get(pmid, {"pmid": pmid, "title": "", "journal": "", "year": "", "doi": "", "publication_types": "", "abstract": "", "pubmed_url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"})
            item = by_pert[pert_id]
            row = {"rank": str(item["rank"]), "pert_id": pert_id, "drug_name": item["pert_iname"],
                   **parsed, "matched_query_groups": "curated_source_reference", "query_match_count": "0",
                   "screening_status": "curated_reference_cached_not_newly_screened",
                   "review_note": "Direct PubMed metadata fetch because the manually cited PMID was absent from the candidate-scoped title/abstract query hits; retain the original manual claim and audit why search did not retrieve it."}
            result_rows.append(row)
            rows_by_pert_pmid[(pert_id, pmid)] = row

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    fields = ["rank", "pert_id", "drug_name", "pmid", "title", "journal", "year", "doi", "publication_types", "abstract", "pubmed_url", "matched_query_groups", "query_match_count", "screening_status", "review_note"]
    with OUTPUT.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(result_rows)
    calls_path = RAW_ROOT / "pubmed_api_calls.json"
    calls_path.write_text(json.dumps({"retrieved_at_utc": snapshot_time, "frozen_top10_sha256": frozen["source_sha256"], "calls": calls}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    all_raw_files["pubmed_api_calls.json"] = sha256_file(calls_path)
    manifest = {
        "manifest_version": 1,
        "status": "retrieved_candidate_scoped_pubmed_search_with_existing_curated_reference_cache_not_manually_screened",
        "retrieved_at_utc": snapshot_time,
        "api": "NCBI PubMed E-utilities esearch.fcgi + efetch.fcgi",
        "api_base": API_BASE,
        "frozen_top10_sha256": frozen["source_sha256"],
        "candidate_count": 10,
        "query_groups": list(QUERY_GROUPS),
        "alias_map": ALIASES,
        "search_count": sum(call["stage"] == "esearch" for call in calls),
        "esearch_retmax_per_query": 100,
        "truncated_search_groups": [
            {"pert_id": call["pert_id"], "query_group": call["query_group"],
             "total_matching_records": call["result_count"], "records_returned": call["returned_count"]}
            for call in calls if call["stage"] == "esearch" and call["returned_count"] < call["result_count"]
        ],
        "live_search_call_count": sum(call["stage"] == "esearch" and call.get("response_source") == "ncbi_api" for call in calls),
        "cached_response_count": sum(call.get("response_source") == "cache" for call in calls),
        "api_call_count": sum(call.get("response_source") == "ncbi_api" for call in calls),
        "request_record_count": len(calls),
        "search_result_count": len(result_rows),
        "metadata_coverage": {
            "records_with_title": sum(bool(row["title"]) for row in result_rows),
            "records_without_title": sum(not row["title"] for row in result_rows),
            "records_with_abstract": sum(bool(row["abstract"]) for row in result_rows),
            "records_without_abstract": sum(not row["abstract"] for row in result_rows),
            "pubmed_book_articles": sum("Book" in row["publication_types"].split("; ") for row in result_rows),
        },
        "existing_curated_pmids_by_pert_id": {pert_id: sorted(pmids) for pert_id, pmids in curated_refs_by_pert.items()},
        "curated_reference_pmids_fetched_outside_query_hits": sorted(missing_reference_ids),
        "unique_pmids_by_pert_id": {pert_id: len(set().union(*groups.values())) for pert_id, groups in ids_by_drug.items()},
        "output_file": "data/top10_kg/evidence/top10_pubmed_search_results.csv",
        "output_sha256": sha256_file(OUTPUT),
        "api_calls_file": str(calls_path.relative_to(ROOT)).replace("\\", "/"),
        "api_calls_sha256": sha256_file(calls_path),
        "raw_snapshots_sha256": all_raw_files,
        "screening_policy": "Search result retrieval is not manual study screening. Do not convert search hits into graph assertions without source review.",
        "limitations": ["Each of the seven title/abstract query groups returns at most 100 ranked PMID IDs; groups with more matches are listed in truncated_search_groups, so retrieval is not exhaustive.", "Title/abstract query aliases may miss records using unindexed names or full text only.", "Searches are candidate-scoped and reproducible but are not a registered systematic review.", "Results are not manually screened and do not imply support or contradiction."],
    }
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"candidate_count": 10, "search_count": manifest["search_count"], "api_call_count": manifest["api_call_count"], "unique_pmids_by_pert_id": manifest["unique_pmids_by_pert_id"], "results_csv": str(OUTPUT)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
