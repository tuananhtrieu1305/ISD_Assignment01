"""Phase7 exclusive claim ledger; prior final journals remain immutable."""

import json
from datetime import UTC, datetime

from ...phase02 import save_csv, save_json
from ...workspace import inside, sha256_file
from ..training import digest

PREFIX = 'artifacts/evaluation/phase07/journal'


def key_for(job):
    return digest([job['study_id'],job['policy_sha256'],job['scenario_sha256'],job['role']])


def read_claim(base, job, proof):
    prefix = PREFIX+'/'+key_for(job)
    saved = json.loads(inside(base,prefix+'/complete.json').read_text())
    if saved['key']!=key_for(job) or saved['proof_sha256']!=proof or saved['evaluation_count']!=1:
        raise ValueError('Completed claim identity/count mismatch')
    for item in saved['files']:
        if sha256_file(inside(base,item['path']))!=item['sha256']:
            raise ValueError('Evaluation artifact hash mismatch')
    return saved


def claim_once(base, job, proof, callback):
    prefix = PREFIX+'/'+key_for(job)
    if inside(base,prefix+'/complete.json').exists():
        return read_claim(base,job,proof)
    claim = inside(base,prefix+'/claim.json')
    if claim.exists():
        raise RuntimeError('Claim consumed without completion; never replay')
    claim.parent.mkdir(parents=True,exist_ok=True)
    with claim.open('x',encoding='utf-8') as stream:
        json.dump({'job':job,'key':key_for(job),'proof_sha256':proof,'claimed_utc':datetime.now(UTC).isoformat()},stream,indent=2)
    try:
        result = callback()
        save_json(base,prefix+'/result.json',result)
        save_csv(base,prefix+'/episodes.csv',result['rows'])
        paths = [claim,inside(base,prefix+'/result.json'),inside(base,prefix+'/episodes.csv')]
        save_json(base,prefix+'/complete.json',{'status':'EVALUATED','key':key_for(job),'proof_sha256':proof,
            'evaluation_count':1,'files':[{'path':p.relative_to(base).as_posix(),'sha256':sha256_file(p)} for p in paths]})
    except BaseException as error:
        save_json(base,prefix+'/failure.json',{'status':'FAILED_SEALED','evaluation_count':1,'error':str(error)})
        raise
    return read_claim(base,job,proof)
