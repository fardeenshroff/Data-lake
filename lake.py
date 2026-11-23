"""Local object-store style data lake: immutable, idempotent CSV ingestion."""
import argparse
import csv
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

REQUIRED={'order_id','order_date','customer_id','product_id','quantity','unit_price'}

def ingest(source, root, dataset='sales_orders'):
    source,root=Path(source),Path(root)
    if not source.is_file(): raise FileNotFoundError(source)
    if not dataset.replace('_','').replace('-','').isalnum(): raise ValueError('Invalid dataset name')
    with source.open(newline='',encoding='utf-8-sig') as f:
        reader=csv.DictReader(f)
        if not REQUIRED.issubset(reader.fieldnames or []): raise ValueError('Missing required CSV columns')
        rows=list(reader)
    if not rows: raise ValueError('Empty dataset')
    # Idempotency follows content identity, not filenames or run timestamps.
    payload=source.read_bytes()
    digest=hashlib.sha256(payload).hexdigest()
    destination=root/'raw'/dataset/f'sha256={digest}'/'data.csv'
    destination.parent.mkdir(parents=True,exist_ok=True)
    if destination.exists():
        if hashlib.sha256(destination.read_bytes()).hexdigest()!=digest:
            raise RuntimeError('Object collision or altered existing file')
        status='already_present'
    else:
        # Atomic rename avoids partially written objects on interrupted ingestion.
        tmp=destination.with_suffix('.tmp')
        tmp.write_bytes(payload)
        tmp.replace(destination)
        status='ingested'
    manifest={'dataset':dataset,'sha256':digest,'rows':len(rows),
              'file':'data.csv','size_bytes':len(payload),'schema':list(reader.fieldnames),
              'source_kind':'synthetic_reference_dataset'}
    metadata=destination.parent/'manifest.json'
    metadata.write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    return {'status':status,'object':str(destination),'manifest':manifest}

def verify(root):
    root=Path(root)
    manifests=sorted(root.glob('raw/*/sha256=*/manifest.json'))
    if not manifests: raise ValueError('No ingested objects')
    report=[]
    for m in manifests:
        data=m.parent/'data.csv';metadata=json.loads(m.read_text())
        valid=data.is_file() and hashlib.sha256(data.read_bytes()).hexdigest()==metadata['sha256']
        report.append({'object':str(data),'integrity_ok':valid})
    if not all(x['integrity_ok'] for x in report): raise RuntimeError('Data integrity failure')
    return report

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('command',choices=['ingest','verify'])
    parser.add_argument('--input',default='data/sample_orders.csv')
    parser.add_argument('--root',default='out/lake')
    a=parser.parse_args()
    print(json.dumps(ingest(a.input,a.root) if a.command=='ingest' else verify(a.root),indent=2))
