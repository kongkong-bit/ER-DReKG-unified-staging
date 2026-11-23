"""Collect small warm-cache API latency samples from the acceptance database."""
from __future__ import annotations

import json
import statistics
import time
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

ROOT = Path(__file__).resolve().parents[2]
PROJECT_ID = "3f18f4c1-713d-58c5-8a53-38eca5a5aaf9"


def percentile(values: list[float], p: float) -> float:
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, int((len(ordered) - 1) * p + 0.999999)))
    return ordered[index]


def main() -> None:
    evidence = json.loads((ROOT / "reports/integration/cross_store_e2e.json").read_text(encoding="utf-8"))
    build_id = evidence["graph_build_id"]
    pert_id = evidence["top10_first_pert_id"]
    routes = {
        "top10_api": ("GET", f"/api/v1/projects/{PROJECT_ID}/top10/mechanisms", {}),
        "kg_subgraph_api": ("GET", f"/api/v1/projects/{PROJECT_ID}/graph/summary", {"graph_build_id": build_id}),
        "kg06_evidence_package_api": ("GET", f"/api/v1/projects/{PROJECT_ID}/kg06/evidence-package/{pert_id}", {"graph_build_id": build_id}),
        "kg07_rule_api": ("POST", f"/api/v1/projects/{PROJECT_ID}/kg07/interpret/{pert_id}", {"graph_build_id": build_id, "mode": "kg_rule"}),
    }
    rows = []
    with TestClient(app) as client:
        for feature, (method, path, params) in routes.items():
            values = []
            for sample in range(6):
                start = time.perf_counter()
                response = client.request(method, path, params=params)
                elapsed_ms = (time.perf_counter() - start) * 1000
                response.raise_for_status()
                if sample > 0:  # warm-up excluded; five timed warm-cache requests remain
                    values.append(elapsed_ms)
            rows.append({
                "feature": feature,
                "environment": "isolated PostgreSQL 17 + Neo4j 5; FastAPI TestClient; warm cache",
                "samples": len(values),
                "p50_ms": round(statistics.median(values), 2),
                "p95_ms": round(percentile(values, 0.95), 2),
                "status": "measured",
                "notes": "Five sequential warm-cache API requests; local same-process TestClient, not browser/network latency or a load test.",
            })
    target = ROOT / "reports/integration/07_api_latency_samples.json"
    target.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(rows, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
