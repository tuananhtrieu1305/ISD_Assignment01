"""Acquire pinned public MedQuAD XML; select diabetes text without running any QA model."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib
import json
import re
import tarfile
import urllib.request
import xml.etree.ElementTree as ET

PROJECT=Path(__file__).resolve().parents[2]
DATA=PROJECT/'datasets/llm_v2'
COMMIT='577bd37b96c02d1833b2c9eed2de9f96964e96cb'
URL=f'https://codeload.github.com/abachaa/MedQuAD/tar.gz/{COMMIT}'

def text(node):return ' '.join(''.join(node.itertext()).split()) if node is not None else ''
def sha(data):return hashlib.sha256(data).hexdigest()
def save(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def main():
    raw=DATA/'raw';raw.mkdir(parents=True,exist_ok=True)
    archive=raw/'medquad-pinned.tar.gz'
    if not archive.exists():
        temp=archive.with_suffix('.partial')
        with urllib.request.urlopen(urllib.request.Request(URL,headers={'User-Agent':'Project01 academic source acquisition'}),timeout=60) as response,temp.open('wb') as output:
            size=0
            while block:=response.read(1024*1024):
                size+=len(block)
                if size>64*1024*1024:raise RuntimeError('Source exceeds 64 MiB acquisition budget')
                output.write(block)
        temp.rename(archive)
    documents=[];xml_count=0
    with tarfile.open(archive,'r:gz') as bundle:
        for member in bundle:
            if member.name.endswith('LICENSE.txt'):
                (raw/'MedQuAD_LICENSE.txt').write_bytes(bundle.extractfile(member).read())
            if not member.isfile() or not member.name.endswith('.xml'):continue
            xml_count+=1;payload=bundle.extractfile(member).read()
            root=ET.fromstring(payload)
            focus=text(root.find('Focus'))
            title=text(root.find('Title')) or focus
            if not re.search(r'diabet',focus+' '+title,re.I):continue
            original='/'.join(member.name.split('/')[1:])
            url=root.attrib.get('url','')
            pairs=[]
            for pair in root.findall('.//QAPair'):
                question=text(pair.find('Question'));answer=text(pair.find('Answer'))
                if answer:pairs.append({'qa_id':pair.attrib.get('pid',''),'question':question,'answer':answer})
            if not pairs:continue
            document_id='mq-'+sha(original.encode())[:16]
            documents.append({'document_id':document_id,'title':title,'focus':focus,'source_url':url,
                'snapshot_url':f'https://github.com/abachaa/MedQuAD/blob/{COMMIT}/{original}',
                'source_xml_path':original,'source_xml_sha256':sha(payload),'language':'en',
                'qa_pairs':pairs,'license':'MedQuAD CC BY 4.0; original website terms remain applicable',
                'source_version':COMMIT,'is_current_clinical_guideline':False})
            target=raw/'xml'/original;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(payload)
    documents.sort(key=lambda row:row['document_id'])
    path=DATA/'documents.jsonl'
    if path.exists():raise RuntimeError('Corpus already exists; do not overwrite')
    path.write_text(''.join(json.dumps(row,ensure_ascii=False)+'\n' for row in documents),encoding='utf-8')
    receipt={'source':URL,'commit':COMMIT,'acquired_at':datetime.now(timezone.utc).isoformat(),
      'archive_bytes':archive.stat().st_size,'archive_sha256':sha(archive.read_bytes()),
      'xml_scanned':xml_count,'documents':len(documents),'qa_pairs':sum(len(r['qa_pairs']) for r in documents),
      'with_original_url':sum(bool(r['source_url']) for r in documents),'selection':'Focus/Title contains diabet, no rank/model/held-out tuning',
      'old_corpus_modified':False,'historical_TEST_read':False}
    save(PROJECT/'artifacts/llm_v2/phase1/acquisition.json',receipt)
    print(json.dumps(receipt))

if __name__=='__main__':main()
