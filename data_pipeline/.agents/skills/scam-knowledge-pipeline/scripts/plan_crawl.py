#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from common import load_env, load_sources, run_psql, db_args
import subprocess

parser = argparse.ArgumentParser(description="Produce incremental crawl plan from source registry and existing staging URLs.")
parser.add_argument("--env-file")
parser.add_argument("--sources", default=None)
parser.add_argument("--out", required=True)
parser.add_argument("--include-unverified", action="store_true")
parser.add_argument("--allow-empty-existing", action="store_true", help="Allow planning without a reachable DB; marks existing DB state as unknown.")
args = parser.parse_args()
load_env(args.env_file)

sources = load_sources(args.sources)
eligible = [s for s in sources if args.include_unverified or s.get("verification_status") == "verified"]

existing = {}
try:
    proc = subprocess.run(db_args() + ["-t", "-A", "-F", "\t", "-c", "SELECT source_name, source_url, content_hash FROM staging_documents;"], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
except FileNotFoundError as exc:
    if not args.allow_empty_existing:
        raise SystemExit("psql not found; install PostgreSQL client or use --allow-empty-existing for offline source-only planning") from exc
    proc = None
db_state = "loaded"
if proc is None:
    db_state = "unknown"
elif proc.returncode == 0:
    for line in proc.stdout.splitlines():
        if not line.strip():
            continue
        source_name, source_url, content_hash = line.split("\t")
        existing[(source_name, source_url)] = content_hash
elif args.allow_empty_existing:
    db_state = "unknown"
else:
    raise SystemExit("failed to query staging_documents; use --allow-empty-existing only for offline source-only planning")

plan = {"sources": [], "existing_record_count": len(existing), "db_state": db_state}
for source in eligible:
    items = []
    for endpoint in source.get("endpoints", []):
        key = (source["source_name"], endpoint["url"])
        items.append({
            "endpoint": endpoint["name"],
            "method": endpoint.get("method", "GET"),
            "url": endpoint["url"],
            "known_content_hash": existing.get(key),
            "action": "fetch"
        })
    plan["sources"].append({
        "source_name": source["source_name"],
        "crawl_strategy": source["crawl_strategy"],
        "verification_status": source.get("verification_status", "needs_probe"),
        "items": items
    })

out = Path(args.out)
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({"planned_sources": len(plan["sources"]), "existing_record_count": len(existing), "db_state": db_state}, ensure_ascii=False))
