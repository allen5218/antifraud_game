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
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin
from common import (
    CATEGORY_LABELS,
    TAXONOMY_CODES,
    content_hash,
    clean_text,
    fetch_url,
    find_source,
    write_jsonl,
)

parser = argparse.ArgumentParser(
    description="Fetch raw records from a configured source using HTTP/API/HTML."
)
parser.add_argument("--source", required=True)
parser.add_argument("--sources", default=None)
parser.add_argument("--out", required=True)
parser.add_argument("--source-verification-status", default=None)
parser.add_argument(
    "--max-records",
    type=int,
    default=None,
    help="Override per-endpoint record cap for smoke runs.",
)
parser.add_argument(
    "--since",
    default=None,
    help="Only keep Cofacts records newer than this ISO-8601 timestamp.",
)
parser.add_argument(
    "--known-id",
    action="append",
    default=[],
    help="Cofacts article ID already seen at the --since timestamp; repeatable.",
)
args = parser.parse_args()

KEYWORD_RULES = {
    "investment_fraud": [
        "假投資",
        "投資",
        "股票",
        "虛擬貨幣",
        "博弈",
        "投顧",
        "LINE群組",
        "金融保險",
        "交易群",
        "市場分析",
        "操作看法",
    ],
    "fake_online_auction_purchase": [
        "拍賣",
        "網路拍賣",
        "假網拍",
        "網拍",
        "賣場",
        "下標",
        "商品未到",
        "電子商務",
    ],
    "general_purchase_fraud": [
        "網路購物",
        "購物",
        "假買家",
        "買賣",
        "一頁式",
        "假客服",
        "假廣告",
        "租屋",
        "租房",
        "訂金",
        "匯款",
        "電子商務",
        "網域",
        "涉詐",
    ],
    "romance_fraud": ["假交友", "交友", "愛情", "感情", "戀愛"],
    "atm_installment_cancellation_fraud": [
        "解除分期",
        "分期付款",
        "ATM",
        "自動櫃員機",
        "重複扣款",
    ],
}

COFACTS_REPLIES_LICENSE = {
    "license": "CC BY-SA 4.0",
    "attribution_required": True,
    "verbatim_in_seed": False,
}

FRAUDBUSTER_CATEGORY_TAXONOMY = {
    "金融投資": "investment_fraud",
    "產品服務": "general_purchase_fraud",
    "愛情交友": "romance_fraud",
    "工作求職": None,
    "其他詐騙": None,
}

FRAUDBUSTER_STATUS_PATTERNS = [
    r"經內政部確認[，,]\s*非詐騙訊息",
    r"本訊息缺乏足夠資訊辨識詐騙與否",
    r"高風險訊息[，,]\s*請謹慎評估",
    r"疑似詐騙訊息",
    r"詐騙訊息[，,]\s*已通知[^\n]*?移除",
    r"網頁已消失",
]


def text_has_any_keyword(text, keywords):
    lowered = text.lower()
    return any(keyword and keyword.lower() in lowered for keyword in keywords)


def infer_taxonomy(source, endpoint, text, record=None):
    if isinstance(record, dict) and record.get("_taxonomy_locked"):
        taxonomy_code = record.get("_taxonomy_code")
        confidence = 0.95 if taxonomy_code in TAXONOMY_CODES else 0
        return taxonomy_code, "source_taxonomy", confidence
    if endpoint.get("taxonomy_code") in TAXONOMY_CODES:
        if endpoint.get("require_taxonomy_keyword_match") or source.get(
            "require_taxonomy_keyword_match"
        ):
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
    min_confidence = float(
        endpoint.get(
            "min_classification_confidence",
            source.get("min_classification_confidence", 0.01),
        )
    )
    return classification_method == "manual" or confidence < min_confidence


def allows_empty_taxonomy(
    source, case_stance, content_kind, classification_method, confidence
):
    unclassified = (
        classification_method in {"manual", "source_taxonomy"} and confidence == 0
    )
    return unclassified and (
        (
            source.get("allow_unclassified_advisory")
            and case_stance == "advisory"
            and content_kind == "advisory"
        )
        or (
            source.get("allow_unclassified_message_sample")
            and case_stance in {"scam", "legit"}
            and content_kind == "message_sample"
        )
    )


def quote_snippets(text, keywords, limit=3):
    snippets = []
    for keyword in keywords:
        idx = text.find(keyword)
        if idx < 0:
            continue
        start = max(0, idx - 80)
        end = min(len(text), idx + len(keyword) + 80)
        snippets.append(
            {"text": text[start:end], "field": "clean_text", "confidence": 0.8}
        )
        if len(snippets) >= limit:
            break
    if not snippets and text:
        snippets.append({"text": text[:160], "field": "clean_text", "confidence": 0.4})
    return snippets


def evidence_for(code, keywords, text):
    return {
        "platforms": [
            kw
            for kw in keywords
            if kw in {"LINE", "LINE群組", "臉書", "Facebook", "IG", "Instagram", "蝦皮"}
        ],
        "payment_methods": [
            kw for kw in keywords if kw in {"ATM", "匯款", "轉帳", "虛擬貨幣"}
        ],
        "impersonated_roles": [
            kw for kw in keywords if kw in {"假客服", "投顧", "名人", "買家", "賣家"}
        ],
        "transaction_context": CATEGORY_LABELS.get(code),
        "relationship_signals": [
            kw for kw in keywords if kw in {"假交友", "交友", "愛情", "感情", "戀愛"}
        ],
        "atm_or_installment_signals": [
            kw for kw in keywords if kw in {"解除分期", "分期付款", "ATM", "重複扣款"}
        ],
        "evidence_quotes": quote_snippets(text, keywords),
    }


def strip_html(value):
    return clean_text(value)


class _SelectorTextParser(HTMLParser):
    """擷取單一簡易 CSS selector（tag、.class、#id）的文字。"""

    BLOCK_TAGS = {
        "br",
        "div",
        "h1",
        "h2",
        "h3",
        "h4",
        "li",
        "p",
        "section",
        "td",
        "th",
        "tr",
    }
    VOID_TAGS = {
        "area",
        "base",
        "br",
        "col",
        "embed",
        "hr",
        "img",
        "input",
        "link",
        "meta",
        "param",
        "source",
        "track",
        "wbr",
    }

    def __init__(self, selector):
        super().__init__(convert_charrefs=True)
        match = re.fullmatch(
            r"(?:(?P<tag>[A-Za-z][\w-]*))?(?:\.(?P<class>[\w-]+)|#(?P<id>[\w-]+))?",
            selector.strip(),
        )
        if not match:
            raise ValueError(f"不支援的 detail_content selector: {selector}")
        self.tag = (match.group("tag") or "").lower()
        self.class_name = match.group("class") or ""
        self.element_id = match.group("id") or ""
        self.depth = 0
        self.parts = []

    def _matches(self, tag, attrs):
        values = dict(attrs)
        classes = values.get("class", "").split()
        return (
            (not self.tag or tag.lower() == self.tag)
            and (not self.class_name or self.class_name in classes)
            and (not self.element_id or values.get("id") == self.element_id)
        )

    def _newline(self):
        if self.parts and self.parts[-1] != "\n":
            self.parts.append("\n")

    def handle_starttag(self, tag, attrs):
        if self.depth:
            if tag.lower() in self.BLOCK_TAGS:
                self._newline()
            if tag.lower() not in self.VOID_TAGS:
                self.depth += 1
        elif self._matches(tag, attrs):
            self.depth = 1

    def handle_startendtag(self, tag, attrs):
        if self.depth and tag.lower() in self.BLOCK_TAGS:
            self._newline()

    def handle_endtag(self, tag):
        if self.depth:
            if tag.lower() in self.BLOCK_TAGS:
                self._newline()
            self.depth -= 1

    def handle_data(self, data):
        if self.depth:
            self.parts.append(data)


def extract_selector_text(value, selectors):
    if isinstance(selectors, str):
        selectors = [selectors]
    for selector in selectors or []:
        parser = _SelectorTextParser(selector)
        parser.feed(value)
        parser.close()
        text = clean_text("".join(parser.parts))
        if text:
            return text, selector
    return "", None


def prioritize_judgment_text(text, max_chars=20000):
    """短判決保留全文；長判決將犯罪事實移到前段並限制策展文字長度。"""
    text = clean_text(text)
    if len(text) <= max_chars:
        return text
    start = text.find("犯罪事實")
    facts = ""
    if start >= 0:
        endings = [
            text.find(marker, start + 4)
            for marker in ("理由", "證據並所犯法條", "論罪科刑")
        ]
        endings = [position for position in endings if position > start]
        end = min(endings) if endings else min(len(text), start + max_chars // 2)
        facts = text[start:end]
    prioritized = f"{facts}\n\n{text}" if facts else text
    return prioritized[:max_chars].rstrip()


def infer_content_kind(source, record, title, text):
    if isinstance(record, dict) and record.get("_content_kind"):
        return record["_content_kind"]
    default = source.get("default_content_kind", "case_narrative")
    for rule in source.get("content_kind_structure_rules", []):
        title_patterns = rule.get("title_patterns", [])
        if title_patterns and not any(
            re.search(pattern, clean_text(title), flags=re.I)
            for pattern in title_patterns
        ):
            continue
        item_pattern = rule.get("item_pattern")
        if item_pattern and len(
            re.findall(item_pattern, clean_text(text), flags=re.I | re.M)
        ) >= int(rule.get("min_matches", 1)):
            return rule["content_kind"]
    pattern_groups = source.get("content_kind_patterns", {})
    for kind in ("domain_list", "advisory", "message_sample", "case_narrative"):
        configured = pattern_groups.get(kind, {})
        for field_name, value in (("title", title), ("content", text)):
            patterns = (
                configured.get(field_name, []) if isinstance(configured, dict) else []
            )
            if any(
                re.search(pattern, clean_text(value), flags=re.I | re.S)
                for pattern in patterns
            ):
                return kind
    return default


def infer_case_stance(source, record):
    if isinstance(record, dict) and record.get("_case_stance"):
        return record["_case_stance"]
    return source.get("default_case_stance", "scam")


def record_metadata(record):
    if isinstance(record, dict) and isinstance(record.get("_metadata"), dict):
        return record["_metadata"]
    return None


def clean_cofacts_message(value):
    """移除手機截圖 OCR 常見的狀態列／聊天介面雜訊。"""
    text = clean_text(value)
    noise_line = re.compile(
        r"^(?:(?:(?:[01]?\d|2[0-3]):[0-5]\d|5G|4G|LTE|Wi-?Fi|已讀|未讀|上午|下午)(?:\s+|$))+$",
        flags=re.I,
    )
    lines = [
        line for line in text.splitlines() if not noise_line.fullmatch(line.strip())
    ]
    return clean_text("\n".join(lines))


def is_url_heavy_message(text):
    urls = re.findall(r"https?://\S+|www\.\S+", text, flags=re.I)
    if not urls:
        return False
    without_urls = re.sub(r"https?://\S+|www\.\S+", "", text, flags=re.I)
    meaningful = re.sub(r"[\W_]+", "", without_urls, flags=re.UNICODE)
    return (
        len(meaningful) < 20 or sum(len(url) for url in urls) / max(1, len(text)) >= 0.7
    )


def is_cofacts_advisory(text, source):
    return any(
        re.search(pattern, text, flags=re.I | re.S)
        for pattern in source.get("advisory_patterns", [])
    )


def prepare_record(source, endpoint, record):
    if not isinstance(record, dict):
        return record
    source_name = source.get("source_name")
    prepared = dict(record)
    if source_name == "tw_165_dashboard_cases" and record.get("Description"):
        title = clean_text(record.get("Title") or record.get("CaseTitle"))
        description = clean_text(record.get("Description"))
        prepared["clean_text"] = clean_text(
            f"{title}\n{description}" if title else description
        )
        prepared["body_text"] = prepared["clean_text"]
        if len(re.findall(r"(?m)^\s*\d+[、.]", description)) >= 2:
            prepared["_content_kind"] = "advisory"
    if source_name in {"tw_cofacts_scam_messages", "tw_cofacts_legit_lookalikes"}:
        message = clean_cofacts_message(record.get("text"))
        prepared["clean_text"] = message
        prepared["body_text"] = clean_text(record.get("text"))
        prepared["source_url"] = f"https://cofacts.tw/article/{record.get('id', '')}"
        metadata = dict(prepared.get("_metadata") or {})
        if isinstance(record.get("cofacts_replies"), dict):
            metadata["cofacts_replies"] = record["cofacts_replies"]
        if source_name == "tw_cofacts_legit_lookalikes":
            prepared["_case_stance"] = "advisory"
            prepared["_content_kind"] = "advisory"
            metadata.update(
                {
                    "candidate_for": "legit_lookalike",
                    "review_required": True,
                }
            )
        if metadata:
            prepared["_metadata"] = metadata
    return prepared


def extract_between(value, start_pattern, end_pattern=None):
    match = re.search(start_pattern, value, flags=re.I | re.S)
    if not match:
        return ""
    start = match.start()
    tail = value[start:]
    if end_pattern:
        end = re.search(end_pattern, tail, flags=re.I | re.S)
        if end:
            tail = tail[: end.start()]
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
            article_list = data.get("ListArticles")
            if isinstance(article_list, dict):
                records = []
                for edge in article_list.get("edges") or []:
                    if not isinstance(edge, dict) or not isinstance(
                        edge.get("node"), dict
                    ):
                        continue
                    node = dict(edge["node"])
                    article_replies = node.pop("articleReplies", None)
                    if isinstance(article_replies, list):
                        replies = [
                            dict(item["reply"])
                            for item in article_replies
                            if isinstance(item, dict)
                            and isinstance(item.get("reply"), dict)
                        ]
                        node["cofacts_replies"] = {
                            "items": replies,
                            "license": dict(COFACTS_REPLIES_LICENSE),
                        }
                    records.append({**node, "_cofacts_cursor": edge.get("cursor")})
                return records
            records = []
            for key in ("news", "marquee", "videos", "charts"):
                value = data.get(key)
                if isinstance(value, list):
                    for item in value:
                        records.append(
                            {
                                "section": key,
                                **(item if isinstance(item, dict) else {"value": item}),
                            }
                        )
            if records:
                return records
        return [payload]
    return [{"value": payload}]


def parse_csv_records(body):
    sample = body.lstrip("\ufeff")
    reader = csv.DictReader(io.StringIO(sample))
    rows = []
    for row in reader:
        cleaned = {
            clean_text(k): clean_text(v) for k, v in row.items() if k is not None
        }
        if not any(cleaned.values()):
            continue
        # Some government CSV files use the first data row as Chinese field labels.
        if set(cleaned.values()) & {
            "網站名稱",
            "網址",
            "件數",
            "統計起始日期",
            "統計結束日期",
        }:
            continue
        rows.append(cleaned)
    return rows


def pdf_link_for(record, fields):
    if not isinstance(record, dict):
        return ""
    for field in fields:
        value = clean_text(record.get(field))
        if value.startswith("http") and (
            ".pdf" in value.lower() or "mediadl=true" in value.lower()
        ):
            return value
    return ""


def extract_pdf_text(url, timeout=30, max_pages=8, max_chars=20000):
    if not shutil.which("curl") or not shutil.which("pdftotext"):
        return "", "curl or pdftotext not available"
    with tempfile.TemporaryDirectory(prefix="scam-pdf-") as tmpdir:
        pdf_path = Path(tmpdir) / "source.pdf"
        txt_path = Path(tmpdir) / "source.txt"
        curl_cmd = [
            "curl",
            "-L",
            "-sS",
            "--max-time",
            str(timeout),
            "--connect-timeout",
            str(min(5, timeout)),
            "-A",
            "Codex scam-knowledge-pipeline/1.0",
            "-o",
            str(pdf_path),
            url,
        ]
        curl_proc = subprocess.run(
            curl_cmd,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout + 5,
        )
        if (
            curl_proc.returncode != 0
            or not pdf_path.exists()
            or pdf_path.stat().st_size == 0
        ):
            return "", curl_proc.stderr.strip() or "pdf download failed"
        pdf_cmd = ["pdftotext", "-layout", "-enc", "UTF-8"]
        if max_pages:
            pdf_cmd.extend(["-l", str(max_pages)])
        pdf_cmd.extend([str(pdf_path), str(txt_path)])
        pdf_proc = subprocess.run(
            pdf_cmd,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout + 10,
        )
        if pdf_proc.returncode != 0 or not txt_path.exists():
            return "", pdf_proc.stderr.strip() or "pdftotext failed"
        text = clean_text(txt_path.read_text(encoding="utf-8", errors="replace"))
        if max_chars and len(text) > max_chars:
            text = text[:max_chars]
        return text, ""


def enrich_pdf_records(records, source, endpoint):
    if not (endpoint.get("expand_pdf_links") or source.get("expand_pdf_links")):
        return records
    fields = endpoint.get(
        "pdf_link_fields",
        source.get("pdf_link_fields", ["檔案連結", "file_url", "url"]),
    )
    timeout = endpoint.get(
        "pdf_timeout_seconds",
        source.get("pdf_timeout_seconds", source.get("timeout_seconds", 30)),
    )
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
        pdf_text, pdf_error = extract_pdf_text(
            link, timeout=timeout, max_pages=max_pages, max_chars=max_chars
        )
        enriched_record = {
            **record,
            "pdf_url": link,
            "pdf_text": pdf_text,
            "pdf_fetch_error": pdf_error,
        }
        enriched.append(enriched_record)
    return enriched


def extract_fraudbuster_detail_links(body, base_url):
    links = re.findall(
        r'href=["\']([^"\']*/accessibility/detail\?[^"\']+)["\']', body, flags=re.I
    )
    return list(dict.fromkeys(urljoin(base_url, html.unescape(link)) for link in links))


def extract_fraudbuster_list_items(body, base_url):
    items = []
    anchor_pattern = re.compile(
        r"<a\b(?P<attrs>[^>]*)>(?P<body>.*?)</a>", flags=re.I | re.S
    )
    for match in anchor_pattern.finditer(body):
        href_match = re.search(
            r'href=["\']([^"\']*/accessibility/detail\?[^"\']+)["\']',
            match.group("attrs"),
            flags=re.I,
        )
        if not href_match:
            continue
        item_body = match.group("body")
        image_alts = [
            clean_text(html.unescape(value))
            for value in re.findall(
                r'<img\b[^>]*\balt=["\']([^"\']*)["\']', item_body, re.I
            )
        ]
        category = next(
            (alt for alt in image_alts if alt in FRAUDBUSTER_CATEGORY_TAXONOMY),
            None,
        )
        item_text = strip_html(item_body)
        status = None
        for pattern in FRAUDBUSTER_STATUS_PATTERNS:
            status_match = re.search(pattern, item_text, flags=re.I)
            if status_match:
                status = clean_text(status_match.group(0))
                break
        items.append(
            {
                "detail_url": urljoin(base_url, html.unescape(href_match.group(1))),
                "source_category_alt": category,
                "source_case_status": status,
            }
        )
    return items


def fraudbuster_status_outcome(status):
    if not status:
        return {}
    if re.fullmatch(r"詐騙訊息[，,]\s*已通知.*移除", status):
        return {"case_stance": "scam"}
    if "疑似詐騙訊息" in status or "高風險訊息" in status:
        return {"case_stance": "scam", "review_required": True}
    if re.fullmatch(r"經內政部確認[，,]\s*非詐騙訊息", status):
        return {"case_stance": "legit", "review_required": True}
    if "缺乏足夠資訊辨識詐騙與否" in status:
        return {"drop_reason": "insufficient_evidence"}
    if status == "網頁已消失":
        return {"drop_reason": "page_gone"}
    return {}


def is_fraudbuster_meta_description(text):
    return bool(
        re.fullmatch(
            r"\d[\d,]*\s+Followers\s*[•·]\s*\d[\d,]*\s+Threads?\.?\s*"
            r"See the latest conversations with\s+@\S+?\.?",
            clean_text(text),
            flags=re.I,
        )
    )


def is_configured_message_placeholder(text, patterns):
    cleaned = clean_text(text)
    return any(re.fullmatch(pattern, cleaned, flags=re.I) for pattern in patterns)


def extract_judicial_detail_links(body, base_url):
    links = re.findall(
        r'href=["\']([^"\']*(?:/LAW_Mobile_FJUD/FJUD/)?data\.aspx\?[^"\']+)["\']',
        body,
        flags=re.I,
    )
    return list(dict.fromkeys(urljoin(base_url, html.unescape(link)) for link in links))


def extract_fsc_press_links(body, base_url, title_patterns):
    links = []
    anchor_pattern = re.compile(
        r"<a\b(?P<attrs>[^>]*)>(?P<label>.*?)</a>", flags=re.I | re.S
    )
    for match in anchor_pattern.finditer(body):
        attrs = match.group("attrs")
        href_match = re.search(r'href=["\']([^"\']+)["\']', attrs, flags=re.I)
        if not href_match:
            continue
        href = html.unescape(href_match.group(1))
        if "mcustomize=news_view.jsp" not in href or "dataserno=" not in href:
            continue
        title_match = re.search(r'title=["\']([^"\']+)["\']', attrs, flags=re.I)
        title = clean_text(
            title_match.group(1) if title_match else strip_html(match.group("label"))
        )
        title = re.sub(r"[（(]開啟新視窗[)）]\s*$", "", title).strip()
        if not any(re.search(pattern, title, flags=re.I) for pattern in title_patterns):
            continue
        links.append((urljoin(base_url, href), title))
    return list(dict.fromkeys(links))


def extract_configured_page_links(body, base_url, pagination):
    param = pagination.get("param", "page")
    links = re.findall(r'href=["\']([^"\']+)["\']', body, flags=re.I)
    return list(
        dict.fromkeys(
            urljoin(base_url, html.unescape(link))
            for link in links
            if re.search(rf"(?:[?&]){re.escape(param)}=\d+", html.unescape(link))
        )
    )


def parse_html_records(body, source, endpoint, max_records=None):
    url = endpoint["url"]
    source_name = source["source_name"]
    max_details = endpoint.get(
        "max_detail_records", source.get("max_detail_records", 5)
    )
    if source_name == "fraudbuster_digiat_accessibility":
        records = []
        list_items = extract_fraudbuster_list_items(body, url)
        if not list_items:
            list_items = [
                {
                    "detail_url": detail_url,
                    "source_category_alt": None,
                    "source_case_status": None,
                }
                for detail_url in extract_fraudbuster_detail_links(body, url)
            ]
        for item in list_items[:max_details]:
            detail_url = item["detail_url"]
            category = item.get("source_category_alt")
            status = item.get("source_case_status")
            status_outcome = fraudbuster_status_outcome(status)
            metadata = {}
            if category:
                metadata["source_category_alt"] = category
            if status:
                metadata["source_case_status"] = status
            if status_outcome.get("review_required"):
                metadata["review_required"] = True
            common_fields = {
                "detail_url": detail_url,
                "_metadata": metadata,
                **(
                    {
                        "_taxonomy_locked": True,
                        "_taxonomy_code": FRAUDBUSTER_CATEGORY_TAXONOMY[category],
                        "_source_category_label": category,
                    }
                    if category in FRAUDBUSTER_CATEGORY_TAXONOMY
                    else {}
                ),
                **(
                    {"_case_stance": status_outcome["case_stance"]}
                    if status_outcome.get("case_stance")
                    else {}
                ),
            }
            if status_outcome.get("drop_reason"):
                records.append(
                    {
                        **common_fields,
                        "_drop_reason": status_outcome["drop_reason"],
                    }
                )
                continue
            detail = fetch_url(
                detail_url,
                timeout=endpoint.get(
                    "timeout_seconds", source.get("timeout_seconds", 30)
                ),
            )
            detail_body = detail.get("body", "")
            main = extract_between(
                detail_body, r'<main\b[^>]*id=["\']aC["\'][^>]*>', r"</main>"
            )
            text = strip_html(main or detail_body)
            summary_match = re.search(
                r"(?:內容摘要|內容摘錄)\s*(.*)", text, flags=re.I | re.S
            )
            if summary_match:
                text = clean_text(summary_match.group(1))
            for pattern in source.get("detail_end_patterns", []):
                end_match = re.search(pattern, text, flags=re.I | re.S)
                if end_match:
                    text = clean_text(text[: end_match.start()])
                    break
            min_message_chars = int(source.get("min_message_chars", 0))
            drop_reason = (
                "no_message_body"
                if (
                    not text
                    or len(text) < min_message_chars
                    or is_fraudbuster_meta_description(text)
                    or is_configured_message_placeholder(
                        text, source.get("message_placeholder_patterns", [])
                    )
                )
                else None
            )
            records.append(
                {
                    **common_fields,
                    "html_text": text,
                    "http_status": detail.get("status"),
                    "content_type": detail.get("content_type", ""),
                    **({"_drop_reason": drop_reason} if drop_reason else {}),
                }
            )
        return records
    if source_name == "tw_fsc_antifraud_press":
        records = []
        title_patterns = source.get(
            "title_include_patterns", ["詐", "盜刷", "假冒", "冒用", "防範"]
        )
        pagination = source.get("pagination", {})
        max_pages = int(pagination.get("max_pages", 3))
        press_links = []
        page_bodies = [(url, body)]
        if pagination.get("type") == "post_form":
            first_page = int(pagination.get("first_page", 1))
            page_field = pagination.get("page_field", "page")
            for page_number in range(first_page + 1, first_page + max_pages):
                form_body = dict(endpoint.get("form") or {})
                form_body[page_field] = page_number
                page_result = fetch_url(
                    url,
                    method=endpoint.get("method", "POST"),
                    timeout=endpoint.get(
                        "timeout_seconds", source.get("timeout_seconds", 30)
                    ),
                    verify_tls=endpoint.get(
                        "verify_tls", source.get("verify_tls", True)
                    ),
                    max_bytes=endpoint.get(
                        "fetch_max_bytes", source.get("fetch_max_bytes")
                    ),
                    headers=endpoint.get("headers", source.get("headers")),
                    form_body=form_body,
                )
                if not page_result.get("ok") or page_result.get("truncated"):
                    break
                page_bodies.append((url, page_result.get("body", "")))
        else:
            pending_pages = [(url, body)]
            seen_pages = {url}
            while pending_pages and len(seen_pages) <= max_pages:
                page_url, page_body = pending_pages.pop(0)
                page_bodies.append((page_url, page_body)) if page_url != url else None
                for next_url in extract_configured_page_links(
                    page_body, page_url, pagination
                ):
                    if next_url in seen_pages or len(seen_pages) >= max_pages:
                        continue
                    page_result = fetch_url(
                        next_url,
                        timeout=endpoint.get(
                            "timeout_seconds", source.get("timeout_seconds", 30)
                        ),
                        verify_tls=endpoint.get(
                            "verify_tls", source.get("verify_tls", True)
                        ),
                        max_bytes=endpoint.get(
                            "fetch_max_bytes", source.get("fetch_max_bytes")
                        ),
                    )
                    seen_pages.add(next_url)
                    if page_result.get("ok") and not page_result.get("truncated"):
                        pending_pages.append((next_url, page_result.get("body", "")))
        excluded_ids = source.get("excluded_dataserno_patterns", [])
        for page_url, page_body in page_bodies:
            press_links.extend(
                extract_fsc_press_links(page_body, page_url, title_patterns)
            )
        press_links = [
            item
            for item in press_links
            if not any(
                re.search(pattern, item[0], flags=re.I) for pattern in excluded_ids
            )
        ]
        configured_selectors = source.get("selectors", {}).get(
            "detail_content", ["div#content", "main"]
        )
        record_limit = max_records or endpoint.get(
            "max_records", source.get("max_records", 30)
        )
        for detail_url, title in list(dict.fromkeys(press_links))[: int(record_limit)]:
            detail = fetch_url(
                detail_url,
                timeout=endpoint.get(
                    "timeout_seconds", source.get("timeout_seconds", 30)
                ),
                verify_tls=endpoint.get("verify_tls", source.get("verify_tls", True)),
                max_bytes=endpoint.get(
                    "fetch_max_bytes", source.get("fetch_max_bytes")
                ),
            )
            detail_body = detail.get("body", "")
            text, matched_selector = extract_selector_text(
                detail_body, configured_selectors
            )
            records.append(
                {
                    "detail_url": detail_url,
                    "title": title,
                    "html_text": text,
                    "body_text": text,
                    "clean_text": text,
                    "detail_html": detail_body,
                    "detail_selector": matched_selector,
                    "http_status": detail.get("status"),
                    "content_type": detail.get("content_type", ""),
                    **(
                        {
                            "fetch_error": detail.get("error")
                            or "金管會新聞稿內頁擷取失敗"
                        }
                        if not detail.get("ok") or detail.get("truncated")
                        else {}
                    ),
                    **(
                        {"parse_error": "找不到設定的新聞稿全文 selector"}
                        if not matched_selector
                        else {}
                    ),
                }
            )
        return records
    if source_name == "tw_judicial_fraud_judgments":
        records = []
        configured_selectors = source.get("selectors", {}).get(
            "detail_content", "div.htmlcontent"
        )
        for detail_url in extract_judicial_detail_links(body, url)[:max_details]:
            detail = fetch_url(
                detail_url,
                timeout=endpoint.get(
                    "timeout_seconds", source.get("timeout_seconds", 30)
                ),
                verify_tls=endpoint.get("verify_tls", source.get("verify_tls", True)),
                max_bytes=endpoint.get(
                    "fetch_max_bytes", source.get("fetch_max_bytes")
                ),
            )
            detail_body = detail.get("body", "")
            text, matched_selector = extract_selector_text(
                detail_body, configured_selectors
            )
            if not text:
                text = strip_html(detail_body)
            records.append(
                {
                    "detail_url": detail_url,
                    "html_text": text,
                    "body_text": text,
                    "clean_text": prioritize_judgment_text(text),
                    "detail_html": detail_body,
                    "detail_selector": matched_selector,
                    "http_status": detail.get("status"),
                    "content_type": detail.get("content_type", ""),
                    "detail_truncated": detail.get("truncated", False),
                    **(
                        {
                            "fetch_error": detail.get("error")
                            or "判決內頁擷取失敗或內容遭截斷"
                        }
                        if not detail.get("ok") or detail.get("truncated")
                        else {}
                    ),
                    **(
                        {"parse_error": "找不到設定的判決全文 selector"}
                        if not matched_selector
                        else {}
                    ),
                }
            )
        return records
    return [{"html_text": strip_html(body), "source_url": url}]


def record_text(record):
    if isinstance(record, str):
        return clean_text(record)
    if not isinstance(record, dict):
        return clean_text(record)
    fields = [
        "clean_text",
        "body_text",
        "CaseTitle",
        "Title",
        "Description",
        "CaseContent",
        "TacticAnalysis",
        "PreventionTips",
        "FraudMethod",
        "title",
        "content",
        "page_title",
        "html_text",
        "pdf_text",
        "WEBSITE_NM",
        "WEBURL",
        "網站性質",
        "網域",
        "一頁式詐騙購物網站",
        "偽冒網址",
        "網域名稱",
        "標題",
        "發佈內容",
        "詐騙管道",
        "詐騙手法",
        "檔案名稱",
        "檔案連結",
        "webSiteName",
        "webUrl",
    ]
    parts = [clean_text(record.get(field)) for field in fields if record.get(field)]
    if not parts:
        parts = [clean_text(record)]
    return clean_text("\n".join(parts))


def record_title(record, endpoint, source):
    if isinstance(record, dict):
        for field in (
            "CaseTitle",
            "Title",
            "title",
            "標題",
            "WEBSITE_NM",
            "webSiteName",
            "詐騙手法",
            "檔案名稱",
        ):
            if record.get(field):
                return clean_text(record[field])[:240]
    return endpoint.get("display_name") or source.get("display_name")


def record_url(record, endpoint):
    if isinstance(record, dict):
        for field in (
            "detail_url",
            "source_url",
            "webUrl",
            "WEBURL",
            "偽冒網址",
            "檔案連結",
        ):
            if record.get(field):
                value = clean_text(record[field])
                if value.startswith("http"):
                    return value
                if field in {"WEBURL", "webUrl"}:
                    return "https://" + value.lstrip("/")
    return endpoint["url"]


def record_key(source, endpoint, record, index):
    if isinstance(record, dict):
        if source.get("source_name") in {
            "tw_cofacts_scam_messages",
            "tw_cofacts_legit_lookalikes",
        }:
            return f"{source['source_name']}:content:{content_hash({'text': record.get('clean_text', '')})}"
        csv_identity_fields = [
            "編號",
            "CNT",
            "民國年月",
            "STA_SDATE",
            "STA_EDATE",
            "statisticsStartDate",
            "statisticsEndDate",
            "接獲通報日期",
            "停止解析日期",
            "詐騙網站創建日期",
            "WEBURL",
            "webUrl",
            "偽冒網址",
            "網域",
            "網域名稱",
            "一頁式詐騙購物網站",
        ]
        csv_parts = [
            clean_text(record.get(field))
            for field in csv_identity_fields
            if record.get(field)
        ]
        if csv_parts:
            return f"{source['source_name']}:{endpoint['name']}:{'|'.join(csv_parts)}:row{index}"
        for field in (
            "Id",
            "id",
            "編號",
            "detail_url",
            "WEBURL",
            "webUrl",
            "網域",
            "網域名稱",
        ):
            if record.get(field):
                return f"{source['source_name']}:{endpoint['name']}:{clean_text(record[field])}"
    return f"{source['source_name']}:{endpoint['name']}:{index}"


def parse_records(result, source, endpoint, max_records=None):
    body = result.get("body", "")
    parser_type = endpoint.get("parser_type", source.get("parser_type", "raw_endpoint"))
    content_type = result.get("content_type", "")
    if parser_type == "json_endpoint" or "json" in content_type:
        return parse_json_records(body, source, endpoint)
    if parser_type == "csv_resource" or "csv" in content_type:
        return enrich_pdf_records(parse_csv_records(body), source, endpoint)
    if parser_type == "html_selector":
        return parse_html_records(body, source, endpoint, max_records=max_records)
    return [{"body": body}]


def can_use_truncated_records(source, endpoint, result, records):
    parser_type = endpoint.get("parser_type", source.get("parser_type", "raw_endpoint"))
    if parser_type != "csv_resource" and "csv" not in result.get("content_type", ""):
        return False
    return bool(records) and not (
        isinstance(records[0], dict) and records[0].get("parse_error")
    )


def timestamp_after(value, boundary):
    if not boundary or not value:
        return True
    try:
        parsed_value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        parsed_boundary = datetime.fromisoformat(boundary.replace("Z", "+00:00"))
    except (AttributeError, ValueError):
        return True
    return parsed_value >= parsed_boundary


def timestamps_equal(left, right):
    if not left or not right:
        return False
    try:
        return datetime.fromisoformat(
            left.replace("Z", "+00:00")
        ) == datetime.fromisoformat(right.replace("Z", "+00:00"))
    except (AttributeError, ValueError):
        return left == right


def cofacts_filter_reason(source, endpoint, record, seen_hashes):
    original = clean_text(record.get("text"))
    prepared = prepare_record(source, endpoint, record)
    text = clean_text(prepared.get("clean_text"))
    if len(original) < 40 or len(original) > 1500:
        return None, "length"
    if len(text) < 40:
        return None, "ocr_too_short"
    if is_url_heavy_message(text):
        return None, "url_heavy"
    message_hash = content_hash({"text": text})
    if message_hash in seen_hashes:
        return None, "duplicate"
    _, classification_method, confidence = infer_taxonomy(source, endpoint, text)
    if should_drop_unclassified(source, endpoint, classification_method, confidence):
        return None, "unclassified"
    seen_hashes.add(message_hash)
    return prepared, None


def fetch_cofacts_records(source, endpoint, max_records, since=None, known_ids=None):
    records = []
    drop_counts = Counter(
        {
            "length": 0,
            "ocr_too_short": 0,
            "url_heavy": 0,
            "duplicate": 0,
            "unclassified": 0,
        }
    )
    seen_hashes = set()
    cursor = None
    seen_cursors = set()
    last_result = None
    last_success_result = None
    pagination_error = ""
    using_fallback = False
    known_ids = set(known_ids or [])
    max_pages = int(endpoint.get("max_pages", source.get("max_pages", 20)))
    pages_fetched = 0
    # Initial crawls honor max_records. Incremental crawls must cross the prior
    # timestamp boundary even when a burst contains more than the nominal cap,
    # otherwise the overflow can never be discovered on the next run.
    while pages_fetched < max_pages and (len(records) < max_records or since):
        request_body = deepcopy(
            endpoint.get("fallback_json")
            if using_fallback
            else endpoint.get("json") or {}
        )
        if not using_fallback:
            variables = dict(request_body.get("variables") or {})
            variables["cursor"] = cursor
            request_body["variables"] = variables
        last_result = fetch_url(
            endpoint["url"],
            endpoint.get("method", "POST"),
            request_body,
            timeout=endpoint.get("timeout_seconds", source.get("timeout_seconds", 30)),
            verify_tls=endpoint.get("verify_tls", source.get("verify_tls", True)),
            max_bytes=endpoint.get("fetch_max_bytes", source.get("fetch_max_bytes")),
            headers=endpoint.get("headers", source.get("headers")),
        )
        if not last_result.get("ok") or last_result.get("truncated"):
            pagination_error = last_result.get("error") or (
                "response truncated by fetch_max_bytes"
                if last_result.get("truncated")
                else "request failed"
            )
            break
        pages_fetched += 1
        try:
            payload = json.loads(last_result.get("body", ""))
        except json.JSONDecodeError as exc:
            if last_success_result is not None:
                pagination_error = f"invalid JSON on a later Cofacts page: {exc}"
                break
            raise
        if payload.get("errors"):
            if endpoint.get("fallback_json") and not using_fallback:
                using_fallback = True
                cursor = None
                continue
            if last_success_result is not None:
                pagination_error = (
                    f"GraphQL errors on a later Cofacts page: {payload['errors']}"
                )
                break
            raise ValueError(f"Cofacts GraphQL errors: {payload['errors']}")
        article_list = (payload.get("data") or {}).get("ListArticles") or {}
        if using_fallback:
            last_result = {
                **last_result,
                "degraded": True,
                "degraded_reason": "Cofacts GraphQL fallback query has no cursor pagination",
            }
        last_success_result = last_result
        page_records = parse_json_records(last_result.get("body", ""), source, endpoint)
        reached_boundary = False
        for record in page_records:
            record_timestamp = record.get("lastRequestedAt") or record.get("createdAt")
            if timestamp_after(record_timestamp, since):
                if (
                    timestamps_equal(record_timestamp, since)
                    and record.get("id") in known_ids
                ):
                    continue
                prepared, reason = cofacts_filter_reason(
                    source, endpoint, record, seen_hashes
                )
                if reason:
                    drop_counts[reason] += 1
                elif prepared is not None:
                    records.append(prepared)
            elif record_timestamp:
                reached_boundary = True
        page_info = article_list.get("pageInfo") or {}
        edges = article_list.get("edges") or []
        if not edges:
            break
        if page_info.get("endCursor"):
            next_cursor = page_info.get("endCursor")
        else:
            next_cursor = (
                edges[-1].get("cursor")
                if edges and isinstance(edges[-1], dict)
                else None
            )
        has_next = page_info.get("hasNextPage")
        if (
            using_fallback
            or reached_boundary
            or not next_cursor
            or next_cursor == cursor
            or next_cursor in seen_cursors
            or has_next is False
        ):
            break
        seen_cursors.add(next_cursor)
        cursor = next_cursor
    result = (
        last_success_result
        or last_result
        or {
            "ok": False,
            "status": None,
            "content_type": "",
            "body": "",
            "truncated": False,
            "transport": None,
            "error": "no Cofacts response",
        }
    )
    if pagination_error and last_success_result is not None:
        result = {
            **last_success_result,
            "degraded": True,
            "degraded_reason": f"Cofacts pagination stopped after a later-page failure: {pagination_error}",
        }
    return (
        result,
        records if since else records[:max_records],
        {
            "pages_fetched": pages_fetched,
            "filter_drop_counts": dict(sorted(drop_counts.items())),
            "pagination_error": pagination_error,
        },
    )


source = find_source(args.source, args.sources)
verification_status = args.source_verification_status or source.get(
    "verification_status", "needs_probe"
)
rows = []
seen_content_hashes = set()
fetch_stats = {
    "pages_fetched": 0,
    "filter_drop_counts": Counter(),
    "pagination_errors": [],
}
for endpoint in source.get("endpoints", []):
    max_records = args.max_records or endpoint.get(
        "max_records", source.get("max_records")
    )
    prefetched_records = None
    try:
        if source.get("source_name") in {
            "tw_cofacts_scam_messages",
            "tw_cofacts_legit_lookalikes",
        }:
            result, prefetched_records, cofacts_stats = fetch_cofacts_records(
                source,
                endpoint,
                int(max_records or 100),
                since=args.since,
                known_ids=args.known_id,
            )
            fetch_stats["pages_fetched"] += cofacts_stats["pages_fetched"]
            fetch_stats["filter_drop_counts"].update(
                cofacts_stats["filter_drop_counts"]
            )
            if cofacts_stats["pagination_error"]:
                fetch_stats["pagination_errors"].append(
                    cofacts_stats["pagination_error"]
                )
        else:
            result = fetch_url(
                endpoint["url"],
                endpoint.get("method", "GET"),
                endpoint.get("json"),
                timeout=endpoint.get(
                    "timeout_seconds", source.get("timeout_seconds", 30)
                ),
                verify_tls=endpoint.get("verify_tls", source.get("verify_tls", True)),
                max_bytes=endpoint.get(
                    "fetch_max_bytes", source.get("fetch_max_bytes")
                ),
                headers=endpoint.get("headers", source.get("headers")),
                form_body=endpoint.get("form"),
            )
    except Exception as exc:
        result = {
            "ok": False,
            "status": None,
            "content_type": "",
            "body": "",
            "truncated": False,
            "transport": None,
            "error": str(exc),
        }
    endpoint_payload = {
        "endpoint": endpoint,
        "http_status": result["status"],
        "content_type": result.get("content_type", ""),
        "truncated": result.get("truncated", False),
        "transport": result.get("transport"),
        "error": result.get("error", ""),
        "degraded": result.get("degraded", False),
        "degraded_reason": result.get("degraded_reason", ""),
        "body": result.get("body", ""),
    }
    try:
        if (
            prefetched_records is not None
            and result.get("ok")
            and not result.get("truncated")
        ):
            records = prefetched_records
        elif result.get("ok") and not result.get("truncated"):
            records = parse_records(result, source, endpoint, max_records=max_records)
        elif result.get("ok") and result.get("truncated"):
            parsed_records = parse_records(
                result, source, endpoint, max_records=max_records
            )
            if can_use_truncated_records(source, endpoint, result, parsed_records):
                records = parsed_records
            else:
                records = [
                    {
                        "fetch_error": "response truncated by fetch_max_bytes",
                        "http_status": result.get("status"),
                        "transport": result.get("transport"),
                        "body_preview": result.get("body", "")[:2000],
                    }
                ]
        else:
            reason = result.get("error") or result.get("body") or "fetch failed"
            records = [
                {
                    "fetch_error": reason,
                    "http_status": result.get("status"),
                    "transport": result.get("transport"),
                    "body_preview": result.get("body", "")[:2000],
                }
            ]
    except Exception as exc:
        records = [{"parse_error": str(exc), "body": result.get("body", "")[:2000]}]
    if max_records and not (
        args.since
        and source.get("source_name")
        in {"tw_cofacts_scam_messages", "tw_cofacts_legit_lookalikes"}
    ):
        records = records[: int(max_records)]
    for index, record in enumerate(records):
        record = prepare_record(source, endpoint, record)
        if isinstance(record, dict) and record.get("_drop_reason"):
            fetch_stats["filter_drop_counts"][record["_drop_reason"]] += 1
            continue
        is_cofacts = source.get("source_name") in {
            "tw_cofacts_scam_messages",
            "tw_cofacts_legit_lookalikes",
        }
        is_diagnostic = isinstance(record, dict) and bool(
            record.get("parse_error") or record.get("fetch_error")
        )
        text = (
            clean_text(record.get("clean_text"))
            if is_cofacts and not is_diagnostic
            else record_text(record)
        )
        if is_cofacts and not is_diagnostic:
            if not (40 <= len(text) <= 1500) or is_url_heavy_message(text):
                continue
            message_hash = content_hash({"text": text})
            if message_hash in seen_content_hashes:
                continue
            seen_content_hashes.add(message_hash)
        body_text = (
            clean_text(record.get("body_text")) if isinstance(record, dict) else text
        )
        clean_record_text = (
            clean_text(record.get("clean_text")) if isinstance(record, dict) else text
        )
        body_text = body_text or text
        clean_record_text = clean_record_text or text
        raw_payload = {
            **endpoint_payload,
            "body": None,
            "record_index": index,
            "record": record,
        }
        ok_for_apply = (
            bool(result.get("ok"))
            and bool(text)
            and not result.get("degraded")
            and (
                not result.get("truncated")
                or can_use_truncated_records(source, endpoint, result, records)
            )
            and not (
                isinstance(record, dict)
                and (record.get("parse_error") or record.get("fetch_error"))
            )
        )
        taxonomy_code, classification_method, confidence = infer_taxonomy(
            source, endpoint, text, record=record
        )
        if not is_diagnostic and should_drop_unclassified(
            source, endpoint, classification_method, confidence
        ):
            fetch_stats["filter_drop_counts"]["unclassified"] += 1
            continue
        case_stance = infer_case_stance(source, record)
        content_kind = infer_content_kind(
            source, record, record_title(record, endpoint, source), clean_record_text
        )
        allow_empty_taxonomy = allows_empty_taxonomy(
            source,
            case_stance,
            content_kind,
            classification_method,
            confidence,
        )
        if allow_empty_taxonomy:
            taxonomy_code = None
        matched_keywords = matched_keywords_for(taxonomy_code, source, endpoint, text)
        record_verification_status = (
            verification_status if ok_for_apply else "candidate"
        )
        validation_status = (
            "valid"
            if ok_for_apply and (confidence > 0 or allow_empty_taxonomy)
            else "needs_review"
        )
        source_url = record_url(record, endpoint)
        row = {
            "source_name": source["source_name"],
            "source_type": source["source_type"],
            "source_url": source_url,
            "canonical_url": source_url,
            "case_key": record_key(source, endpoint, record, index),
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "content_hash": (
                content_hash({"text": clean_record_text})
                if is_cofacts
                else content_hash(raw_payload)
            ),
            "page_title": record_title(record, endpoint, source),
            "body_text": body_text,
            "clean_text": clean_record_text,
            "raw_payload": raw_payload,
            "taxonomy_code": taxonomy_code,
            "source_category_label": (
                record.get("_source_category_label")
                if isinstance(record, dict)
                else None
            )
            or endpoint.get("source_category_label")
            or CATEGORY_LABELS.get(taxonomy_code),
            "matched_keywords": matched_keywords,
            "classification_confidence": confidence,
            "classification_method": classification_method,
            "category_evidence": evidence_for(taxonomy_code, matched_keywords, text),
            "extraction_notes": [
                f"Fetched endpoint {endpoint['name']} with parser_type={endpoint.get('parser_type', source.get('parser_type', 'raw_endpoint'))}.",
                f"http_status={result.get('status')}; truncated={result.get('truncated', False)}; record_index={index}.",
            ],
            "classification_notes": [
                f"Classified by {classification_method}; endpoint taxonomy takes precedence over keyword rules."
            ],
            "validation_status": validation_status,
            "source_verification_status": record_verification_status,
            "case_stance": case_stance,
            "content_kind": content_kind,
        }
        metadata = record_metadata(record)
        if metadata is not None:
            row["metadata"] = metadata
        rows.append(row)

write_jsonl(args.out, rows)
print(
    json.dumps(
        {
            "source_name": source["source_name"],
            "fetched_records": len(rows),
            "valid_records": sum(
                1 for row in rows if row.get("validation_status") == "valid"
            ),
            "verified_records": sum(
                1 for row in rows if row.get("source_verification_status") == "verified"
            ),
            "pages_fetched": fetch_stats["pages_fetched"],
            "filter_drop_counts": dict(
                sorted(fetch_stats["filter_drop_counts"].items())
            ),
            "pagination_errors": fetch_stats["pagination_errors"],
            "out": args.out,
        },
        ensure_ascii=False,
    )
)
