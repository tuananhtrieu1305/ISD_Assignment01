"""Expose the eight original paper1 datasets without substituting V3 datasets/splits."""
from pathlib import Path
import csv
import json

ROOT=Path(__file__).resolve().parents[1]
def load(path): return json.loads(path.read_text(encoding='utf-8-sig'))
def group(project,prefix):
    doc=load(ROOT/project/'datasets/catalog.json')
    return [file for dataset in doc['datasets'] for file in dataset.get('files',[]) if file['path'].startswith(prefix)]

summaries={}
for chapter in [2,3,4]:
    with (ROOT/f'tieuluan1/artifacts/metrics/ch{chapter}_dataset_summary.csv').open(encoding='utf-8-sig',newline='') as stream:
        summaries.update({r['dataset_id']:r for r in csv.DictReader(stream)})
specs=[
    ('ch2_diabetes_binary','CDC diabetes binary','A03','A03/datasets/diabetes/','ch2_diabetes_binary.md'),
    ('ch2_vietnam_housing','Vietnam housing','A03','A03/datasets/housing_price/','ch2_vietnam_housing.md'),
    ('ch2_ecommerce_behavior','E-commerce customer behavior','A03','A03/datasets/customer_behavior/','ch2_ecommerce_behavior.md'),
    ('ch3_eurosat','EuroSAT RGB','A05','A05/datasets/eurosat/','ch3_eurosat_rgb.md'),
    ('ch3_oxford_pets','Oxford-IIIT Pet','A05','A05/datasets/oxford_pets/','ch3_oxford_pets.md'),
    ('ch3_diabetes_012','CDC diabetes three-class','A05','A05/datasets/diabetes/','ch3_diabetes_012.md'),
    ('ch4_online_retail_customer_week','Online Retail II customer-week','A06','A06/datasets/customer/','ch4_online_retail_ii.md'),
    ('ch4_aapl_next_close','AAPL next Close','A06','A06/datasets/stock/','ch4_aapl.md'),
]
rows=[]
for dataset,name,project,prefix,card in specs:
    files=group(project,prefix)
    assert files,(dataset,prefix)
    card_path=f'tieuluan1/sources/dataset_cards/{card}'
    rows.append({'dataset_id':dataset,'name':name,'status':'available','files':files,'source_card':card_path,'source':card_path,'summary':summaries[dataset],'schema':{'read_original_card':card_path},'split_policy':'paper1 matched splits/subsets from its own artifacts; original A05/A06 ablations separately labeled; never use V3 splits','note':'Files borrowed only at identical raw snapshot identity. Canonical AAPL Git LF differs only in line endings from Windows CRLF expected in the source card; declared representation adapter supplies the exact original hash in the runtime view.' if project=='A06' and 'stock/' in prefix else 'Existing image/CSV payload; no regeneration or new split.'})
path=ROOT/'tieuluan1/datasets/catalog.json'
temporary=path.with_name(path.name+'.migration-tmp')
temporary.write_text(json.dumps({'project':'tieuluan1','datasets':rows,'physical_path_base':'repository root','resolver':'scripts/datasets.py','raw_modified':False,'derived_from':'eight original source cards and saved chapter dataset summaries'},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
temporary.replace(path)
print('Paper1 catalog:8dataset identities;',sum(len(r['files']) for r in rows),'physical references')
