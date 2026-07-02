#!/usr/bin/env python3
"""既有 documents 回填 case_stance/content_kind(以來源為準,spec §3.1)。"""
import argparse
import json
from common import load_env, ensure_relational_schema, psql_scalar, run_psql

SOURCE_STANCE = {
    "tw_judicial_fraud_judgments": ("scam", "case_narrative"),
    "tw_165_article_search": ("scam", "case_narrative"),
    "tw_165_dashboard_cases": ("scam", "case_narrative"),
    "tw_165_structured_query": ("scam", "case_narrative"),
    "fraudbuster_digiat_accessibility": ("scam", "case_narrative"),
    "tw_165_fraud_domains_blocked": ("scam", "domain_list"),
    "tw_moda_ecommerce_fraud_domains": ("scam", "domain_list"),
    "tw_165_fake_investment_sites": ("scam", "domain_list"),
    "tw_165_scam_rumor_busting": ("advisory", "advisory"),
    "tw_moj_anti_fraud_legal_education": ("advisory", "advisory"),
    "tw_chiayi_fraud_channel_methods": ("advisory", "advisory"),
    "tw_twse_tpex_anti_fraud": ("advisory", "advisory"),
}

parser = argparse.ArgumentParser(description="Backfill documents.case_stance/content_kind by source.")
parser.add_argument("--env-file")
parser.add_argument("--apply", action="store_true")
args = parser.parse_args()
load_env(args.env_file)

if args.apply:
    ensure_relational_schema()

plan = {
    name: {
        "docs": int(psql_scalar(f"SELECT count(*) FROM documents WHERE source_name = '{name}';") or "0"),
        "stance": stance,
        "kind": kind,
    }
    for name, (stance, kind) in SOURCE_STANCE.items()
}
print(json.dumps({"apply": args.apply, "plan": plan}, ensure_ascii=False, indent=2))
if not args.apply:
    raise SystemExit(0)

values = ", ".join(f"('{n}','{s}','{k}')" for n, (s, k) in SOURCE_STANCE.items())
run_psql(
    f"UPDATE documents d SET case_stance = m.stance, content_kind = m.kind "
    f"FROM (VALUES {values}) AS m(source_name, stance, kind) WHERE d.source_name = m.source_name;"
)
print(psql_scalar("SELECT count(*) FROM documents WHERE case_stance IS NULL OR content_kind IS NULL;"))
