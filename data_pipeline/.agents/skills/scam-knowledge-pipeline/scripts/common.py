#!/usr/bin/env python3
import csv
import hashlib
import html
import io
import json
import os
import re
import shlex
import shutil
import ssl
import subprocess
import sys
import tempfile
from pathlib import Path
from html.parser import HTMLParser
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from urllib.parse import urlencode

ROOT = Path(__file__).resolve().parents[1]
TAXONOMY_CODES = {
    "investment_fraud",
    "fake_online_auction_purchase",
    "general_purchase_fraud",
    "romance_fraud",
    "atm_installment_cancellation_fraud",
}

CATEGORY_LABELS = {
    "investment_fraud": "投資詐欺",
    "fake_online_auction_purchase": "假網路拍賣（購物）",
    "general_purchase_fraud": "一般購物詐欺（偽稱買賣）",
    "romance_fraud": "假愛情交友",
    "atm_installment_cancellation_fraud": "解除分期付款詐欺（ATM）",
}

STANCE_VALUES = {"scam", "legit", "advisory"}
CONTENT_KINDS = {
    "case_narrative",
    "message_sample",
    "domain_list",
    "advisory",
    "statute",
}
WEAKNESS_TAGS = {
    "time_pressure",
    "authority",
    "greed",
    "social_proof",
    "trust_building",
}
GAME_FRAUD_TYPES = {
    "investment_fraud": "investment",
    "fake_online_auction_purchase": "fake-sale",
    "general_purchase_fraud": "shopping",
    "romance_fraud": "romance",
    "atm_installment_cancellation_fraud": "atm",
}


def load_env(path=None):
    if not path:
        return
    env_path = Path(path)
    if not env_path.exists():
        raise SystemExit(f"env file not found: {env_path}")
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def load_sources(path=None):
    source_path = Path(path) if path else ROOT / "references" / "sources.yaml"
    data = json.loads(source_path.read_text(encoding="utf-8"))
    return data["sources"]


def find_source(name, path=None):
    for src in load_sources(path):
        if src["source_name"] == name:
            return src
    raise SystemExit(f"unknown source: {name}")


def read_jsonl(path):
    with open(path, "r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                yield line_no, json.loads(line)
            except json.JSONDecodeError as exc:
                yield (
                    line_no,
                    {"__json_error__": str(exc), "__raw_line__": line.rstrip("\n")},
                )


def write_jsonl(path, rows):
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def content_hash(obj):
    payload = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


class _TextHTMLParser(HTMLParser):
    """將 HTML 轉成保留段落邊界的純文字。"""

    BLOCK_TAGS = {
        "address",
        "article",
        "aside",
        "blockquote",
        "br",
        "dd",
        "div",
        "dl",
        "dt",
        "figcaption",
        "figure",
        "footer",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "header",
        "hr",
        "li",
        "main",
        "nav",
        "ol",
        "p",
        "pre",
        "section",
        "table",
        "tbody",
        "td",
        "tfoot",
        "th",
        "thead",
        "tr",
        "ul",
    }
    SKIP_TAGS = {"script", "style", "noscript", "template"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.skip_depth = 0

    def _newline(self):
        if self.parts and self.parts[-1] != "\n":
            self.parts.append("\n")

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag in self.SKIP_TAGS:
            self.skip_depth += 1
        elif not self.skip_depth and tag in self.BLOCK_TAGS:
            self._newline()

    def handle_startendtag(self, tag, attrs):
        if not self.skip_depth and tag.lower() in self.BLOCK_TAGS:
            self._newline()

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag in self.SKIP_TAGS:
            self.skip_depth = max(0, self.skip_depth - 1)
        elif not self.skip_depth and tag in self.BLOCK_TAGS:
            self._newline()

    def handle_data(self, data):
        if not self.skip_depth:
            self.parts.append(data)


def _html_to_text(value):
    parser = _TextHTMLParser()
    parser.feed(value)
    parser.close()
    return "".join(parser.parts)


def clean_text(value):
    """正規化純文字；若輸入含 HTML，移除標籤、還原實體並保留段落換行。"""
    if value is None:
        return ""
    if not isinstance(value, str):
        value = json.dumps(value, ensure_ascii=False, sort_keys=True)
    if re.search(r"</?[A-Za-z][^>]*>", value):
        value = _html_to_text(value)
    else:
        value = html.unescape(value)
    return "\n".join(
        " ".join(part.split())
        for part in value.replace("\r", "\n").split("\n")
        if part.strip()
    )


def _fetch_url_with_curl(
    url,
    method="GET",
    json_body=None,
    timeout=30,
    verify_tls=True,
    max_bytes=None,
    headers=None,
    form_body=None,
):
    header_fd, header_path = tempfile.mkstemp(prefix="scam-fetch-", suffix=".headers")
    body_fd, body_path = tempfile.mkstemp(prefix="scam-fetch-", suffix=".body")
    os.close(header_fd)
    os.close(body_fd)
    data_path = None
    try:
        cmd = [
            "curl",
            "-L",
            "-sS",
            "--max-time",
            str(timeout),
            "--connect-timeout",
            str(min(5, timeout)),
            "-A",
            "Codex scam-knowledge-pipeline/1.0",
            "-D",
            header_path,
            "-o",
            body_path,
            "-w",
            "%{http_code}",
        ]
        if not verify_tls:
            cmd.append("-k")
        if method.upper() != "GET":
            cmd.extend(["-X", method.upper()])
        for name, value in (headers or {}).items():
            cmd.extend(["-H", f"{name}: {value}"])
        if json_body is not None:
            data_fd, data_path = tempfile.mkstemp(prefix="scam-fetch-", suffix=".json")
            os.close(data_fd)
            Path(data_path).write_text(
                json.dumps(json_body, ensure_ascii=False), encoding="utf-8"
            )
            cmd.extend(
                [
                    "-H",
                    "Content-Type: application/json",
                    "--data-binary",
                    f"@{data_path}",
                ]
            )
        elif form_body is not None:
            cmd.extend(["-H", "Content-Type: application/x-www-form-urlencoded"])
            for name, value in form_body.items():
                cmd.extend(["--data-urlencode", f"{name}={value}"])
        cmd.append(url)

        proc = subprocess.run(
            cmd,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout + 5,
        )
        body_bytes = Path(body_path).read_bytes()
        truncated = False
        if max_bytes and len(body_bytes) > max_bytes:
            body_bytes = body_bytes[:max_bytes]
            truncated = True
        headers = Path(header_path).read_text(encoding="utf-8", errors="replace")
        content_type = ""
        for line in headers.splitlines():
            if line.lower().startswith("content-type:"):
                content_type = line.split(":", 1)[1].strip()
        status = None
        if proc.stdout.strip().isdigit() and proc.stdout.strip() != "000":
            status = int(proc.stdout.strip())
        ok = proc.returncode == 0 and status is not None and 200 <= status < 400
        if proc.returncode != 0 and not body_bytes:
            body = proc.stderr.strip()
        else:
            body = body_bytes.decode("utf-8", errors="replace")
        return {
            "ok": ok,
            "status": status,
            "content_type": content_type,
            "body": body,
            "truncated": truncated,
            "transport": "curl",
            "error": proc.stderr.strip() if proc.returncode != 0 else "",
        }
    except subprocess.TimeoutExpired:
        return {
            "ok": False,
            "status": None,
            "content_type": "",
            "body": f"timeout after {timeout}s",
            "truncated": False,
            "transport": "curl",
            "error": "timeout",
        }
    finally:
        for path in [header_path, body_path, data_path]:
            if path:
                try:
                    Path(path).unlink()
                except FileNotFoundError:
                    pass


def _fetch_url_with_urllib(
    url,
    method="GET",
    json_body=None,
    timeout=30,
    verify_tls=True,
    max_bytes=None,
    headers=None,
    form_body=None,
):
    request_headers = {
        "User-Agent": "Codex scam-knowledge-pipeline/1.0",
        **(headers or {}),
    }
    data = None
    if json_body is not None:
        data = json.dumps(json_body, ensure_ascii=False).encode("utf-8")
        request_headers.setdefault("Content-Type", "application/json")
    elif form_body is not None:
        data = urlencode(form_body).encode("utf-8")
        request_headers.setdefault("Content-Type", "application/x-www-form-urlencoded")
    req = Request(url, data=data, method=method.upper(), headers=request_headers)
    context = None if verify_tls else ssl._create_unverified_context()
    try:
        with urlopen(req, timeout=timeout, context=context) as resp:
            if max_bytes:
                body = resp.read(max_bytes + 1)
                truncated = len(body) > max_bytes
                body = body[:max_bytes]
            else:
                body = resp.read()
                truncated = False
            return {
                "ok": 200 <= resp.status < 400,
                "status": resp.status,
                "content_type": resp.headers.get("content-type", ""),
                "body": body.decode("utf-8", errors="replace"),
                "truncated": truncated,
                "transport": "urllib",
                "error": "",
            }
    except HTTPError as exc:
        return {
            "ok": False,
            "status": exc.code,
            "content_type": exc.headers.get("content-type", ""),
            "body": exc.read().decode("utf-8", errors="replace"),
            "truncated": False,
            "transport": "urllib",
            "error": str(exc),
        }
    except URLError as exc:
        return {
            "ok": False,
            "status": None,
            "content_type": "",
            "body": str(exc),
            "truncated": False,
            "transport": "urllib",
            "error": str(exc),
        }


def fetch_url(
    url,
    method="GET",
    json_body=None,
    timeout=30,
    verify_tls=True,
    max_bytes=None,
    headers=None,
    form_body=None,
):
    if shutil.which("curl"):
        return _fetch_url_with_curl(
            url, method, json_body, timeout, verify_tls, max_bytes, headers, form_body
        )
    return _fetch_url_with_urllib(
        url, method, json_body, timeout, verify_tls, max_bytes, headers, form_body
    )


def _database_url():
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise SystemExit(
            "未設定 DATABASE_URL；請用 --env-file 指定環境檔，或先設定 DATABASE_URL 環境變數"
        )
    return url


def _command_from_env(name, default):
    value = os.environ.get(name, default)
    command = shlex.split(value)
    if not command:
        raise SystemExit(f"{name} 不可為空字串")
    return command


def db_args():
    return _command_from_env("PSQL_BIN", "psql") + [
        "-v",
        "ON_ERROR_STOP=1",
        "-X",
        _database_url(),
    ]


def pg_dump_args(*options):
    return _command_from_env("PG_DUMP_BIN", "pg_dump") + [
        *options,
        _database_url(),
    ]


def run_psql(sql, quiet=False):
    args = db_args()
    if quiet:
        args.insert(len(args) - 1, "-q")
    args += ["-c", sql]
    proc = subprocess.run(
        args, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr)
        raise SystemExit(proc.returncode)
    return proc.stdout


def run_psql_file(path):
    sql = Path(path).read_text(encoding="utf-8")
    proc = subprocess.run(
        db_args(),
        text=True,
        input=sql,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr)
        raise SystemExit(proc.returncode)
    return proc.stdout


def run_pg_dump(*options):
    proc = subprocess.run(
        pg_dump_args(*options),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr)
        raise SystemExit(proc.returncode)
    return proc.stdout


def psql_copy_stdout(sql):
    args = db_args()
    args.insert(len(args) - 1, "-q")
    proc = subprocess.run(
        args + ["-c", sql],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr)
        raise SystemExit(proc.returncode)
    return proc.stdout


def psql_scalar(sql):
    proc = subprocess.run(
        db_args() + ["-t", "-A", "-c", sql],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr)
        raise SystemExit(proc.returncode)
    return proc.stdout.strip()


def ensure_vector_extension_available():
    available = psql_scalar(
        "SELECT EXISTS (SELECT 1 FROM pg_available_extensions WHERE name = 'vector');"
    )
    installed = psql_scalar(
        "SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector');"
    )
    return available == "t", installed == "t"


def ensure_staging_schema():
    run_psql(
        """
CREATE TABLE IF NOT EXISTS staging_documents (
    id bigserial PRIMARY KEY,
    source_name text NOT NULL,
    source_type text NOT NULL,
    source_url text NOT NULL,
    canonical_url text,
    case_key text,
    content_hash text NOT NULL,
    raw_json jsonb NOT NULL,
    validation_status text NOT NULL DEFAULT 'valid',
    source_verification_status text NOT NULL DEFAULT 'needs_probe',
    ingest_status text NOT NULL DEFAULT 'stored',
    fetched_at timestamptz,
    validated_at timestamptz DEFAULT now(),
    ingested_at timestamptz DEFAULT now()
);
ALTER TABLE staging_documents
  DROP CONSTRAINT IF EXISTS staging_documents_source_name_source_url_key;
ALTER TABLE staging_documents
  DROP CONSTRAINT IF EXISTS staging_documents_source_name_case_key_key;
CREATE UNIQUE INDEX IF NOT EXISTS staging_documents_source_name_case_key_uidx
  ON staging_documents (source_name, case_key);
CREATE INDEX IF NOT EXISTS staging_documents_validation_status_idx
  ON staging_documents (validation_status);
CREATE INDEX IF NOT EXISTS staging_documents_source_name_idx
  ON staging_documents (source_name);
CREATE INDEX IF NOT EXISTS staging_documents_taxonomy_idx
  ON staging_documents ((raw_json->>'taxonomy_code'))
  WHERE validation_status = 'valid';
""",
        quiet=True,
    )


def ensure_relational_schema():
    ensure_staging_schema()
    run_psql(
        """
CREATE TABLE IF NOT EXISTS documents (
    id bigserial PRIMARY KEY,
    staging_id bigint UNIQUE REFERENCES staging_documents(id) ON DELETE CASCADE,
    source_name text NOT NULL,
    source_type text NOT NULL,
    source_url text NOT NULL,
    canonical_url text,
    page_title text,
    body_text text,
    clean_text text,
    content_hash text NOT NULL,
    raw_payload jsonb,
    fetched_at timestamptz,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    normalize_status text NOT NULL DEFAULT 'normalized',
    normalized_at timestamptz
);
CREATE TABLE IF NOT EXISTS fraud_categories (
    code text PRIMARY KEY,
    label_zh text NOT NULL
);
CREATE TABLE IF NOT EXISTS document_categories (
    document_id bigint REFERENCES documents(id) ON DELETE CASCADE,
    category_code text REFERENCES fraud_categories(code),
    source_category_label text,
    matched_keywords text[],
    classification_confidence numeric,
    classification_method text,
    classification_notes text[],
    PRIMARY KEY (document_id, category_code)
);
CREATE TABLE IF NOT EXISTS category_evidence (
    document_id bigint REFERENCES documents(id) ON DELETE CASCADE,
    category_code text REFERENCES fraud_categories(code),
    platforms text[],
    payment_methods text[],
    impersonated_roles text[],
    transaction_context text,
    relationship_signals text[],
    atm_or_installment_signals text[],
    evidence_quotes jsonb,
    evidence_json jsonb NOT NULL DEFAULT '{}'::jsonb,
    PRIMARY KEY (document_id, category_code)
);
ALTER TABLE documents ADD COLUMN IF NOT EXISTS case_stance text NOT NULL DEFAULT 'scam';
ALTER TABLE documents ADD COLUMN IF NOT EXISTS content_kind text NOT NULL DEFAULT 'case_narrative';
ALTER TABLE fraud_categories ADD COLUMN IF NOT EXISTS game_fraud_type text;
CREATE INDEX IF NOT EXISTS documents_source_name_idx
  ON documents (source_name);
CREATE INDEX IF NOT EXISTS documents_content_hash_idx
  ON documents (content_hash);
CREATE INDEX IF NOT EXISTS document_categories_category_code_idx
  ON document_categories (category_code);
CREATE INDEX IF NOT EXISTS category_evidence_category_code_idx
  ON category_evidence (category_code);
""",
        quiet=True,
    )
    values = ", ".join(
        "('%s','%s')" % (code, label.replace("'", "''"))
        for code, label in CATEGORY_LABELS.items()
    )
    run_psql(
        f"INSERT INTO fraud_categories (code, label_zh) VALUES {values} ON CONFLICT (code) DO UPDATE SET label_zh = EXCLUDED.label_zh;",
        quiet=True,
    )
    mappings = ", ".join(
        f"('{code}','{game}')" for code, game in GAME_FRAUD_TYPES.items()
    )
    run_psql(
        f"UPDATE fraud_categories fc SET game_fraud_type = m.game FROM (VALUES {mappings}) AS m(code, game) WHERE fc.code = m.code;",
        quiet=True,
    )


def json_array_to_pg_array_sql(json_path):
    return (
        f"ARRAY(SELECT jsonb_array_elements_text(COALESCE({json_path}, '[]'::jsonb)))"
    )


def copy_from_rows_sql(table, columns, rows):
    """建立可直接從 psql stdin 執行的 COPY 區塊，不依賴 client 本機路徑。"""
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(
        buffer,
        fieldnames=columns,
        delimiter="\t",
        extrasaction="ignore",
        lineterminator="\n",
    )
    writer.writeheader()
    writer.writerows(rows)
    column_sql = ", ".join(columns)
    return (
        f"COPY {table} ({column_sql}) FROM STDIN "
        "WITH (FORMAT csv, HEADER true, DELIMITER E'\\t');\n"
        f"{buffer.getvalue()}\\.\n"
    )


def ensure_game_cases_schema():
    ensure_relational_schema()
    run_psql(
        """
CREATE TABLE IF NOT EXISTS game_cases (
    id bigserial PRIMARY KEY,
    case_key text UNIQUE NOT NULL,
    fraud_type text NOT NULL,
    is_scam boolean NOT NULL,
    title text NOT NULL,
    narrative text NOT NULL,
    red_flags jsonb NOT NULL DEFAULT '[]'::jsonb,
    difficulty int NOT NULL DEFAULT 2,
    source_document_ids bigint[] NOT NULL DEFAULT '{}',
    provenance text NOT NULL,
    mirror_of bigint REFERENCES game_cases(id),
    status text NOT NULL DEFAULT 'draft',
    review_notes text,
    created_at timestamptz NOT NULL DEFAULT now(),
    published_at timestamptz
);
CREATE INDEX IF NOT EXISTS game_cases_published_idx
  ON game_cases (fraud_type, is_scam)
  WHERE status = 'published';

-- 查證題子表：一個母案例可掛多題（問「下一步查什麼」與「證據代表什麼」）。
-- 子題有自己的 status，母案例 published 不代表子題已審核。
CREATE TABLE IF NOT EXISTS game_case_questions (
    id bigserial PRIMARY KEY,
    question_key text NOT NULL,
    version int NOT NULL DEFAULT 1,
    case_id bigint NOT NULL REFERENCES game_cases(id) ON DELETE CASCADE,
    question_kind text NOT NULL,
    question text NOT NULL,
    options jsonb NOT NULL,
    correct_key text NOT NULL,
    explanation text NOT NULL,
    weakness_tag text,
    difficulty int NOT NULL DEFAULT 2,
    source_document_ids bigint[] NOT NULL DEFAULT '{}',
    provenance text,
    status text NOT NULL DEFAULT 'draft',
    review_notes text,
    created_at timestamptz NOT NULL DEFAULT now(),
    published_at timestamptz,
    UNIQUE (question_key, version)
);
CREATE INDEX IF NOT EXISTS game_case_questions_published_idx
  ON game_case_questions (case_id)
  WHERE status = 'published';
""",
        quiet=True,
    )
