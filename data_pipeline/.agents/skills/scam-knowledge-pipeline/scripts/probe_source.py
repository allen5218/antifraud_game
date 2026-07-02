#!/usr/bin/env python3
import argparse
import csv
import io
import json
import re
from common import fetch_url, find_source

parser = argparse.ArgumentParser(description="Probe source availability and shape.")
parser.add_argument("--source", required=True)
parser.add_argument("--sources", default=None)
parser.add_argument("--out", required=True)
args = parser.parse_args()

source = find_source(args.source, args.sources)
results = []

def parsed_record_count(body, content_type, parser_type, source_name):
    try:
        if parser_type == "json_endpoint" or "json" in content_type:
            payload = json.loads(body)
            if isinstance(payload, list):
                return len(payload)
            if isinstance(payload, dict) and isinstance(payload.get("body"), list):
                return len(payload["body"])
            if isinstance(payload, dict) and isinstance(payload.get("data"), dict):
                return sum(len(payload["data"].get(key) or []) for key in ("news", "marquee", "videos", "charts") if isinstance(payload["data"].get(key), list)) or 1
            return 1
        if parser_type == "csv_resource" or "csv" in content_type:
            reader = csv.DictReader(io.StringIO(body.lstrip("\ufeff")))
            return sum(1 for row in reader if any(row.values()))
        if parser_type == "html_selector":
            if source_name == "fraudbuster_digiat_accessibility":
                return len(set(re.findall(r'/accessibility/detail\?', body)))
            if source_name == "tw_judicial_fraud_judgments":
                return len(set(re.findall(r'(?:/LAW_Mobile_FJUD/FJUD/)?data\.aspx\?', body)))
            return 1 if body.strip() else 0
        return 1 if body.strip() else 0
    except Exception:
        return 0

for endpoint in source.get("endpoints", []):
    result = fetch_url(
        endpoint["url"],
        endpoint.get("method", "GET"),
        endpoint.get("json"),
        timeout=endpoint.get("timeout_seconds", source.get("timeout_seconds", 30)),
        verify_tls=endpoint.get("verify_tls", source.get("verify_tls", True)),
        max_bytes=endpoint.get("probe_max_bytes", source.get("probe_max_bytes")),
    )
    body = result.get("body") or ""
    parser_type = endpoint.get("parser_type", source.get("parser_type"))
    is_csv = parser_type == "csv_resource" or "csv" in result.get("content_type", "")
    parse_count = parsed_record_count(body, result.get("content_type", ""), parser_type, source["source_name"]) if result["ok"] and (is_csv or not result.get("truncated")) else 0
    results.append({
        "endpoint": endpoint["name"],
        "url": endpoint["url"],
        "method": endpoint.get("method", "GET"),
        "ok": result["ok"],
        "status": result["status"],
        "content_type": result.get("content_type", ""),
        "body_size": len(body.encode("utf-8")),
        "truncated": result.get("truncated", False),
        "transport": result.get("transport"),
        "error": result.get("error", ""),
        "taxonomy_code": endpoint.get("taxonomy_code"),
        "parser_type": parser_type,
        "parsed_record_count": parse_count,
        "preview": body[:500]
    })

ok_results = [
    r for r in results
    if r["ok"]
    and r["body_size"] > 0
    and (not r["truncated"] or r["parser_type"] == "csv_resource" or "csv" in r.get("content_type", ""))
    and r["parsed_record_count"] > 0
]
policy = source.get("verification_policy", "any_success")
min_success = int(source.get("min_successful_endpoints", 1))
if policy == "all_endpoints":
    verified = bool(results) and len(ok_results) == len(results)
elif policy == "min_successful_endpoints":
    verified = len(ok_results) >= min_success
else:
    verified = bool(ok_results)
report = {
    "source_name": source["source_name"],
    "verification_status": "verified" if verified else "failed",
    "crawl_strategy": source["crawl_strategy"],
    "supported_taxonomy_codes": source.get("supported_taxonomy_codes", []),
    "verification_policy": policy,
    "successful_endpoints": len(ok_results),
    "parsed_records": sum(r["parsed_record_count"] for r in ok_results),
    "endpoint_count": len(results),
    "results": results
}

from pathlib import Path
out = Path(args.out)
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({
    "source_name": source["source_name"],
    "verification_status": report["verification_status"],
    "successful_endpoints": report["successful_endpoints"],
    "endpoint_count": len(results)
}, ensure_ascii=False))
