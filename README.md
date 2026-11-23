# Data Lake — Immutable Ingestion and Integrity Validation

I built this project to demonstrate how I organize raw analytical data into an auditable, content-addressed storage layer. The implementation is intentionally lightweight: it uses Python's standard library and the local filesystem to model object storage principles before introducing S3, Azure Data Lake Storage, or distributed compute.

## Architecture

`CSV source → schema checks → SHA-256 object key → immutable raw storage → manifest → integrity validation`

## Run

```bash
python lake.py ingest --input data/sample_orders.csv --root out/lake
python lake.py verify --root out/lake
python -m pip install pytest
python -m pytest -q
```

Run ingestion twice to see idempotence (`ingested` then `already_present`). An altered object fails the integrity audit. Output data is ignored by Git; only the small synthetic sample is included.

## Engineering decisions

The object path contains the source checksum, preventing accidental overwrites and making repeat ingestions deterministic. A manifest captures row count, schema, byte size and digest. I deliberately keep raw records unchanged rather than performing business transformations during ingestion. That separation supports later bronze/silver/gold pipelines.

## Scope

This is a **functional local reference**, not a deployed cloud lake. It does not implement IAM, encryption-at-rest, object version retention or distributed ingestion. Those are the next platform-level concerns for a production implementation. See [project status](PROJECT_STATUS.md).
