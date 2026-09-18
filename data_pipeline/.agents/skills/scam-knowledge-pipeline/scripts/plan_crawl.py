#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from common import load_env, load_sources, db_args
import subprocess

parser = argparse.ArgumentParser(
    description="Produce incremental crawl plan from source registry and existing staging URLs."
)
parser.add_argument("--env-file")
parser.add_argument("--sources", default=None)
parser.add_argument("--out", required=True)
parser.add_argument("--include-unverified", action="store_true")
parser.add_argument(
    "--allow-empty-existing",
    action="store_true",
    help="Allow planning without a reachable DB; marks existing DB state as unknown.",
)
args = parser.parse_args()
load_env(args.env_file)

sources = load_sources(args.sources)
eligible = [
    s
    for s in sources
    if args.include_unverified or s.get("verification_status") == "verified"
]

existing = {}
latest_timestamps = {}
latest_ids = {}
try:
    proc = subprocess.run(
        db_args()
        + [
            "-t",
            "-A",
            "-F",
            "\t",
            "-c",
            "SELECT source_name, source_url, content_hash, COALESCE(raw_json->'raw_payload'->'record'->>'lastRequestedAt', raw_json->'raw_payload'->'record'->>'createdAt', ''), COALESCE(raw_json->'raw_payload'->'record'->>'id', '') FROM staging_documents;",
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
except FileNotFoundError as exc:
    if not args.allow_empty_existing:
        raise SystemExit(
            "psql not found; install PostgreSQL client or use --allow-empty-existing for offline source-only planning"
        ) from exc
    proc = None
db_state = "loaded"
if proc is None:
    db_state = "unknown"
elif proc.returncode == 0:
    for line in proc.stdout.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        source_name, source_url, content_hash = parts[:3]
        updated_at = parts[3] if len(parts) > 3 else ""
        record_id = parts[4] if len(parts) > 4 else ""
        existing[(source_name, source_url)] = content_hash
        if updated_at and updated_at > latest_timestamps.get(source_name, ""):
            latest_timestamps[source_name] = updated_at
            latest_ids[source_name] = {record_id} if record_id else set()
        elif (
            updated_at
            and updated_at == latest_timestamps.get(source_name)
            and record_id
        ):
            latest_ids.setdefault(source_name, set()).add(record_id)
elif args.allow_empty_existing:
    db_state = "unknown"
else:
    raise SystemExit(
        "failed to query staging_documents; use --allow-empty-existing only for offline source-only planning"
    )

plan = {"sources": [], "existing_record_count": len(existing), "db_state": db_state}
for source in eligible:
    items = []
    for endpoint in source.get("endpoints", []):
        key = (source["source_name"], endpoint["url"])
        item = {
            "endpoint": endpoint["name"],
            "method": endpoint.get("method", "GET"),
            "url": endpoint["url"],
            "known_content_hash": existing.get(key),
            "action": "fetch",
        }
        since = latest_timestamps.get(source["source_name"])
        if source.get("incremental", {}).get("updated_at_fields") and since:
            item["since"] = since
            item["fetch_args"] = ["--since", since]
            for record_id in sorted(latest_ids.get(source["source_name"], set())):
                item["fetch_args"].extend(["--known-id", record_id])
        items.append(item)
    plan["sources"].append(
        {
            "source_name": source["source_name"],
            "crawl_strategy": source["crawl_strategy"],
            "verification_status": source.get("verification_status", "needs_probe"),
            "items": items,
        }
    )

out = Path(args.out)
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
print(
    json.dumps(
        {
            "planned_sources": len(plan["sources"]),
            "existing_record_count": len(existing),
            "db_state": db_state,
        },
        ensure_ascii=False,
    )
)
