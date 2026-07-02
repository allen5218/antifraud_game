# JSON Schema Contract

The classified JSONL contract is `schemas/scam_case.schema.json`.

Each line must be one complete classified case object. The validator rejects records that miss required source, content, taxonomy, evidence, or audit fields.

Minimum command:

```bash
python scripts/validate_cases.py \
  --input data/classified/cases.jsonl \
  --valid-output data/validated/cases.valid.jsonl \
  --reject-output data/rejected/cases.rejected.jsonl
```

Only valid JSONL may be passed to `scripts/ingest_jsonb.py`.
