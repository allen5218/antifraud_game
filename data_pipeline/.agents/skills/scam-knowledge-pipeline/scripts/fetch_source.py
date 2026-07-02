#!/usr/bin/env python3
import argparse
import csv
import html
import io
import json
import re
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin
from common import CATEGORY_LABELS, TAXONOMY_CODES, content_hash, clean_text, fetch_url, find_source, write_jsonl

parser = argparse.ArgumentParser(description="Fetch raw records from a configured source using HTTP/API/HTML.")
parser.add_argument("--source", required=True)
parser.add_argument("--sources", default=None)
parser.add_argument("--out", required=True)
parser.add_argument("--source-verification-status", default=None)
parser.add_argument("--max-records", type=int, default=None, help="Override per-endpoint record cap for smoke runs.")
args = parser.parse_args()

KEYWORD_RULES = {
    "investment_fraud": ["假投資", "投資", "股票", "虛擬貨幣", "博弈", "投顧", "LINE群組", "金融保險", "交易群", "市場分析", "操作看法"],
    "fake_online_auction_purchase": ["拍賣", "網路拍賣", "假網拍", "網拍", "賣場", "下標", "商品未到", "電子商務"],
    "general_purchase_fraud": ["網路購物", "購物", "假買家", "買賣", "一頁式", "假客服", "假廣告", "租屋", "租房", "訂金", "匯款", "電子商務", "網域", "涉詐"],
    "romance_fraud": ["假交友", "交友", "愛情", "感情", "戀愛"],
    "atm_installment_cancellation_fraud": ["解除分期", "分期付款", "ATM", "自動櫃員機", "重複扣款"],
}

def text_has_any_keyword(text, keywords):
    lowered = text.lower()
    return any(keyword and keyword.lower() in lowered for keyword in keywords)

def infer_taxonomy(source, endpoint, text):
    if endpoint.get("taxonomy_code") in TAXONOMY_CODES:
        if endpoint.get("require_taxonomy_keyword_match") or source.get("require_taxonomy_keyword_match"):
            if not text_has_any_keyword(text, endpoint.get("keywords", [])):
                return infer_taxonomy_from_keywords(text)
        return endpoint["taxonomy_code"], "source_taxonomy", 0.85
    supported = source.get("supported_taxonomy_codes", [])
    if len(supported) == 1 and supported[0] in TAXONOMY_CODES:
        return supported[0], "source_taxonomy", 0.75
    return infer_taxonomy_from_keywords(text)

def infer_taxonomy_from_keywords(text):
    scores = {}
    for code, keywords in KEYWORD_RULES.items():
        scores[code] = sum(1 for keyword in keywords if keyword.lower() in text.lower())
    code, score = max(scores.items(), key=lambda item: item[1])
    if score > 0:
        return code, "rule", min(0.7, 0.45 + score * 0.08)
    return "general_purchase_fraud", "manual", 0

def matched_keywords_for(code, source, endpoint, text):
    candidates = []
    candidates.extend(endpoint.get("keywords", []))
    candidates.extend(source.get("keywords", []))
    candidates.extend(KEYWORD_RULES.get(code, []))
    seen = []
    lowered = text.lower()
    for keyword in candidates:
        if keyword and keyword not in seen and keyword.lower() in lowered:
            seen.append(keyword)
    return seen

def should_drop_unclassified(source, endpoint, classification_method, confidence):
    if not (endpoint.get("drop_unclassified") or source.get("drop_unclassified")):
        return False
    min_confidence = float(endpoint.get("min_classification_confidence", source.get("min_classification_confidence", 0.01)))
    return classification_method == "manual" or confidence < min_confidence

def quote_snippets(text, keywords, limit=3):
    snippets = []
    for keyword in keywords:
        idx = text.find(keyword)
        if idx < 0:
            continue
        start = max(0, idx - 80)
        end = min(len(text), idx + len(keyword) + 80)
        snippets.append({"text": text[start:end], "field": "clean_text", "confidence": 0.8})
        if len(snippets) >= limit:
            break
    if not snippets and text:
        snippets.append({"text": text[:160], "field": "clean_text", "confidence": 0.4})
    return snippets

def evidence_for(code, keywords, text):
    return {
        "platforms": [kw for kw in keywords if kw in {"LINE", "LINE群組", "臉書", "Facebook", "IG", "Instagram", "蝦皮"}],
        "payment_methods": [kw for kw in keywords if kw in {"ATM", "匯款", "轉帳", "虛擬貨幣"}],
        "impersonated_roles": [kw for kw in keywords if kw in {"假客服", "投顧", "名人", "買家", "賣家"}],
        "transaction_context": CATEGORY_LABELS.get(code),
        "relationship_signals": [kw for kw in keywords if kw in {"假交友", "交友", "愛情", "感情", "戀愛"}],
        "atm_or_installment_signals": [kw for kw in keywords if kw in {"解除分期", "分期付款", "ATM", "重複扣款"}],
        "evidence_quotes": quote_snippets(text, keywords),
    }

def strip_html(value):
    value = re.sub(r"(?is)<script[^>]*>.*?</script>", " ", value)
    value = re.sub(r"(?is)<style[^>]*>.*?</style>", " ", value)
    value = re.sub(r"(?is)<[^>]+>", " ", value)
    return clean_text(html.unescape(value))

def extract_between(value, start_pattern, end_pattern=None):
    match = re.search(start_pattern, value, flags=re.I | re.S)
    if not match:
        return ""
    start = match.start()
    tail = value[start:]
    if end_pattern:
        end = re.search(end_pattern, tail, flags=re.I | re.S)
        if end:
            tail = tail[:end.start()]
    return tail

def parse_json_records(body, source, endpoint):
    payload = json.loads(body)
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        if isinstance(payload.get("body"), list):
            return payload["body"]
        data = payload.get("data")
        if isinstance(data, dict):
            records = []
            for key in ("news", "marquee", "videos", "charts"):
                value = data.get(key)
                if isinstance(value, list):
                    for item in value:
                        records.append({"section": key, **(item if isinstance(item, dict) else {"value": item})})
            if records:
                return records
        return [payload]
    return [{"value": payload}]

def parse_csv_records(body):
    sample = body.lstrip("\ufeff")
    reader = csv.DictReader(io.StringIO(sample))
    rows = []
    for row in reader:
        cleaned = {clean_text(k): clean_text(v) for k, v in row.items() if k is not None}
        if not any(cleaned.values()):
            continue
        # Some government CSV files use the first data row as Chinese field labels.
        if set(cleaned.values()) & {"網站名稱", "網址", "件數", "統計起始日期", "統計結束日期"}:
            continue
        rows.append(cleaned)
    return rows

def pdf_link_for(record, fields):
    if not isinstance(record, dict):
        return ""
    for field in fields:
        value = clean_text(record.get(field))
        if value.startswith("http") and (".pdf" in value.lower() or "mediadl=true" in value.lower()):
            return value
    return ""

def extract_pdf_text(url, timeout=30, max_pages=8, max_chars=20000):
    if not shutil.which("curl") or not shutil.which("pdftotext"):
        return "", "curl or pdftotext not available"
    with tempfile.TemporaryDirectory(prefix="scam-pdf-") as tmpdir:
        pdf_path = Path(tmpdir) / "source.pdf"
        txt_path = Path(tmpdir) / "source.txt"
        curl_cmd = [
            "curl", "-L", "-sS",
            "--max-time", str(timeout),
            "--connect-timeout", str(min(5, timeout)),
            "-A", "Codex scam-knowledge-pipeline/1.0",
            "-o", str(pdf_path),
            url,
        ]
        curl_proc = subprocess.run(curl_cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout + 5)
        if curl_proc.returncode != 0 or not pdf_path.exists() or pdf_path.stat().st_size == 0:
            return "", curl_proc.stderr.strip() or "pdf download failed"
        pdf_cmd = ["pdftotext", "-layout", "-enc", "UTF-8"]
        if max_pages:
            pdf_cmd.extend(["-l", str(max_pages)])
        pdf_cmd.extend([str(pdf_path), str(txt_path)])
        pdf_proc = subprocess.run(pdf_cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout + 10)
        if pdf_proc.returncode != 0 or not txt_path.exists():
            return "", pdf_proc.stderr.strip() or "pdftotext failed"
        text = clean_text(txt_path.read_text(encoding="utf-8", errors="replace"))
        if max_chars and len(text) > max_chars:
            text = text[:max_chars]
        return text, ""

def enrich_pdf_records(records, source, endpoint):
    if not (endpoint.get("expand_pdf_links") or source.get("expand_pdf_links")):
        return records
    fields = endpoint.get("pdf_link_fields", source.get("pdf_link_fields", ["檔案連結", "file_url", "url"]))
    timeout = endpoint.get("pdf_timeout_seconds", source.get("pdf_timeout_seconds", source.get("timeout_seconds", 30)))
    max_pages = endpoint.get("pdf_max_pages", source.get("pdf_max_pages", 8))
    max_chars = endpoint.get("pdf_max_chars", source.get("pdf_max_chars", 20000))
    enriched = []
    for record in records:
        if not isinstance(record, dict):
            enriched.append(record)
            continue
        link = pdf_link_for(record, fields)
        if not link:
            enriched.append(record)
            continue
        pdf_text, pdf_error = extract_pdf_text(link, timeout=timeout, max_pages=max_pages, max_chars=max_chars)
        enriched_record = {
            **record,
            "pdf_url": link,
            "pdf_text": pdf_text,
            "pdf_fetch_error": pdf_error,
        }
        enriched.append(enriched_record)
    return enriched

def extract_fraudbuster_detail_links(body, base_url):
    links = re.findall(r'href=["\']([^"\']*/accessibility/detail\?[^"\']+)["\']', body, flags=re.I)
    return list(dict.fromkeys(urljoin(base_url, html.unescape(link)) for link in links))

def extract_judicial_detail_links(body, base_url):
    links = re.findall(r'href=["\']([^"\']*(?:/LAW_Mobile_FJUD/FJUD/)?data\.aspx\?[^"\']+)["\']', body, flags=re.I)
    return list(dict.fromkeys(urljoin(base_url, html.unescape(link)) for link in links))

def parse_html_records(body, source, endpoint):
    url = endpoint["url"]
    source_name = source["source_name"]
    max_details = endpoint.get("max_detail_records", source.get("max_detail_records", 5))
    if source_name == "fraudbuster_digiat_accessibility":
        records = []
        for detail_url in extract_fraudbuster_detail_links(body, url)[:max_details]:
            detail = fetch_url(detail_url, timeout=endpoint.get("timeout_seconds", source.get("timeout_seconds", 30)))
            detail_body = detail.get("body", "")
            main = extract_between(detail_body, r'<main\b[^>]*id=["\']aC["\'][^>]*>', r"</main>")
            text = strip_html(main or detail_body)
            records.append({
                "detail_url": detail_url,
                "html_text": text,
                "http_status": detail.get("status"),
                "content_type": detail.get("content_type", "")
            })
        return records
    if source_name == "tw_judicial_fraud_judgments":
        records = []
        for detail_url in extract_judicial_detail_links(body, url)[:max_details]:
            detail = fetch_url(detail_url, timeout=endpoint.get("timeout_seconds", source.get("timeout_seconds", 30)))
            detail_body = detail.get("body", "")
            content = extract_between(detail_body, r'<div\b[^>]*class=["\'][^"\']*htmlcontent[^"\']*["\'][^>]*>', r"</div>")
            text = strip_html(content or detail_body)
            records.append({
                "detail_url": detail_url,
                "html_text": text,
                "http_status": detail.get("status"),
                "content_type": detail.get("content_type", "")
            })
        return records
    return [{"html_text": strip_html(body), "source_url": url}]

def record_text(record):
    if isinstance(record, str):
        return clean_text(record)
    if not isinstance(record, dict):
        return clean_text(record)
    fields = [
        "CaseTitle", "CaseContent", "TacticAnalysis", "PreventionTips", "FraudMethod",
        "title", "content", "page_title", "html_text",
        "pdf_text",
        "WEBSITE_NM", "WEBURL", "網站性質", "網域", "一頁式詐騙購物網站", "偽冒網址", "網域名稱",
        "標題", "發佈內容", "詐騙管道", "詐騙手法", "檔案名稱", "檔案連結",
        "webSiteName", "webUrl"
    ]
    parts = [clean_text(record.get(field)) for field in fields if record.get(field)]
    if not parts:
        parts = [clean_text(record)]
    return clean_text("\n".join(parts))

def record_title(record, endpoint, source):
    if isinstance(record, dict):
        for field in ("CaseTitle", "title", "標題", "WEBSITE_NM", "webSiteName", "詐騙手法", "檔案名稱"):
            if record.get(field):
                return clean_text(record[field])[:240]
    return endpoint.get("display_name") or source.get("display_name")

def record_url(record, endpoint):
    if isinstance(record, dict):
        for field in ("detail_url", "source_url", "webUrl", "WEBURL", "偽冒網址", "檔案連結"):
            if record.get(field):
                value = clean_text(record[field])
                if value.startswith("http"):
                    return value
                if field in {"WEBURL", "webUrl"}:
                    return "https://" + value.lstrip("/")
    return endpoint["url"]

def record_key(source, endpoint, record, index):
    if isinstance(record, dict):
        csv_identity_fields = [
            "編號", "CNT", "民國年月", "STA_SDATE", "STA_EDATE", "statisticsStartDate", "statisticsEndDate",
            "接獲通報日期", "停止解析日期", "詐騙網站創建日期",
            "WEBURL", "webUrl", "偽冒網址", "網域", "網域名稱", "一頁式詐騙購物網站",
        ]
        csv_parts = [clean_text(record.get(field)) for field in csv_identity_fields if record.get(field)]
        if csv_parts:
            return f"{source['source_name']}:{endpoint['name']}:{'|'.join(csv_parts)}:row{index}"
        for field in ("Id", "id", "編號", "detail_url", "WEBURL", "webUrl", "網域", "網域名稱"):
            if record.get(field):
                return f"{source['source_name']}:{endpoint['name']}:{clean_text(record[field])}"
    return f"{source['source_name']}:{endpoint['name']}:{index}"

def parse_records(result, source, endpoint):
    body = result.get("body", "")
    parser_type = endpoint.get("parser_type", source.get("parser_type", "raw_endpoint"))
    content_type = result.get("content_type", "")
    if parser_type == "json_endpoint" or "json" in content_type:
        return parse_json_records(body, source, endpoint)
    if parser_type == "csv_resource" or "csv" in content_type:
        return enrich_pdf_records(parse_csv_records(body), source, endpoint)
    if parser_type == "html_selector":
        return parse_html_records(body, source, endpoint)
    return [{"body": body}]

def can_use_truncated_records(source, endpoint, result, records):
    parser_type = endpoint.get("parser_type", source.get("parser_type", "raw_endpoint"))
    if parser_type != "csv_resource" and "csv" not in result.get("content_type", ""):
        return False
    return bool(records) and not (isinstance(records[0], dict) and records[0].get("parse_error"))

source = find_source(args.source, args.sources)
verification_status = args.source_verification_status or source.get("verification_status", "needs_probe")
rows = []
for endpoint in source.get("endpoints", []):
    result = fetch_url(
        endpoint["url"],
        endpoint.get("method", "GET"),
        endpoint.get("json"),
        timeout=endpoint.get("timeout_seconds", source.get("timeout_seconds", 30)),
        verify_tls=endpoint.get("verify_tls", source.get("verify_tls", True)),
        max_bytes=endpoint.get("fetch_max_bytes", source.get("fetch_max_bytes")),
    )
    endpoint_payload = {
        "endpoint": endpoint,
        "http_status": result["status"],
        "content_type": result.get("content_type", ""),
        "truncated": result.get("truncated", False),
        "transport": result.get("transport"),
        "error": result.get("error", ""),
        "body": result.get("body", "")
    }
    try:
        if result.get("ok") and not result.get("truncated"):
            records = parse_records(result, source, endpoint)
        elif result.get("ok") and result.get("truncated"):
            parsed_records = parse_records(result, source, endpoint)
            if can_use_truncated_records(source, endpoint, result, parsed_records):
                records = parsed_records
            else:
                records = [{
                    "fetch_error": "response truncated by fetch_max_bytes",
                    "http_status": result.get("status"),
                    "transport": result.get("transport"),
                    "body_preview": result.get("body", "")[:2000],
                }]
        else:
            reason = result.get("error") or result.get("body") or "fetch failed"
            records = [{
                "fetch_error": reason,
                "http_status": result.get("status"),
                "transport": result.get("transport"),
                "body_preview": result.get("body", "")[:2000],
            }]
    except Exception as exc:
        records = [{"parse_error": str(exc), "body": result.get("body", "")[:2000]}]
    max_records = args.max_records or endpoint.get("max_records", source.get("max_records"))
    if max_records:
        records = records[:int(max_records)]
    for index, record in enumerate(records):
        text = record_text(record)
        raw_payload = {
            **endpoint_payload,
            "body": None,
            "record_index": index,
            "record": record
        }
        ok_for_apply = (
            bool(result.get("ok"))
            and bool(text)
            and (not result.get("truncated") or can_use_truncated_records(source, endpoint, result, records))
            and not (isinstance(record, dict) and (record.get("parse_error") or record.get("fetch_error")))
        )
        taxonomy_code, classification_method, confidence = infer_taxonomy(source, endpoint, text)
        if should_drop_unclassified(source, endpoint, classification_method, confidence):
            continue
        matched_keywords = matched_keywords_for(taxonomy_code, source, endpoint, text)
        record_verification_status = verification_status if ok_for_apply else "candidate"
        validation_status = "valid" if ok_for_apply and confidence > 0 else "needs_review"
        source_url = record_url(record, endpoint)
        row = {
            "source_name": source["source_name"],
            "source_type": source["source_type"],
            "source_url": source_url,
            "canonical_url": source_url,
            "case_key": record_key(source, endpoint, record, index),
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "content_hash": content_hash(raw_payload),
            "page_title": record_title(record, endpoint, source),
            "body_text": text,
            "clean_text": text,
            "raw_payload": raw_payload,
            "taxonomy_code": taxonomy_code,
            "source_category_label": endpoint.get("source_category_label") or CATEGORY_LABELS.get(taxonomy_code),
            "matched_keywords": matched_keywords,
            "classification_confidence": confidence,
            "classification_method": classification_method,
            "category_evidence": evidence_for(taxonomy_code, matched_keywords, text),
            "extraction_notes": [
                f"Fetched endpoint {endpoint['name']} with parser_type={endpoint.get('parser_type', source.get('parser_type', 'raw_endpoint'))}.",
                f"http_status={result.get('status')}; truncated={result.get('truncated', False)}; record_index={index}."
            ],
            "classification_notes": [
                f"Classified by {classification_method}; endpoint taxonomy takes precedence over keyword rules."
            ],
            "validation_status": validation_status,
            "source_verification_status": record_verification_status
        }
        rows.append(row)

write_jsonl(args.out, rows)
print(json.dumps({
    "source_name": source["source_name"],
    "fetched_records": len(rows),
    "valid_records": sum(1 for row in rows if row.get("validation_status") == "valid"),
    "verified_records": sum(1 for row in rows if row.get("source_verification_status") == "verified"),
    "out": args.out
}, ensure_ascii=False))
