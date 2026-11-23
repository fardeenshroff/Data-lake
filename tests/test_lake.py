import csv
import json
from pathlib import Path
import pytest
from lake import ingest,verify

def test_idempotence_and_integrity(tmp_path):
    src=Path(__file__).resolve().parents[1]/'data/sample_orders.csv'
    assert ingest(src,tmp_path)['status']=='ingested'
    assert ingest(src,tmp_path)['status']=='already_present'
    result=verify(tmp_path)
    assert len(result)==1 and result[0]['integrity_ok']
    data=Path(result[0]['object'])
    data.write_text('tampered')
    with pytest.raises(RuntimeError): verify(tmp_path)

def test_missing_schema(tmp_path):
    p=tmp_path/'x.csv';p.write_text('name\nabc\n')
    with pytest.raises(ValueError): ingest(p,tmp_path/'lake')
