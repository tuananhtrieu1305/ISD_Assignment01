"""Claim before forward; reuse complete results; never replay a consumed partial claim."""

import json
from datetime import UTC, datetime

from ...phase02 import save_csv, save_json
from ...workspace import inside, sha256_file
from ..training import digest

PREFIX = 'artifacts/evaluation/phase05/journal'


class ConsumedClaimError(RuntimeError):
    pass


def job_key(job):
    return digest([job['study_id'], job['policy_sha256'], job['scenario_sha256'], job['role']])


def read_complete(base, job, proof_sha256):
    prefix = PREFIX+'/'+job_key(job)
    saved = json.loads(inside(base, prefix+'/complete.json').read_text())
    if saved['proof_sha256'] != proof_sha256 or saved['key'] != job_key(job):
        raise ValueError('Completed claim belongs to a different proof/key')
    for item in saved['files']:
        if sha256_file(inside(base, item['path'])) != item['sha256']:
            raise ValueError('Saved evaluation artifact hash mismatch')
    return saved


def claim_evaluate(base, job, proof_sha256, callback):
    prefix = PREFIX+'/'+job_key(job)
    if inside(base, prefix+'/complete.json').exists():
        return read_complete(base, job, proof_sha256)
    claim = inside(base, prefix+'/claim.json')
    if claim.exists():
        raise ConsumedClaimError('Claim consumed without completion; preserve evidence, never forward again')
    # x mode at the OS level is the final race guard; no identical-claim reuse.
    claim.parent.mkdir(parents=True, exist_ok=True)
    with claim.open('x', encoding='utf-8') as stream:
        json.dump({'job': job, 'key': job_key(job), 'proof_sha256': proof_sha256,
                   'claimed_utc': datetime.now(UTC).isoformat()}, stream, indent=2)
    try:
        result = callback()
        save_json(base, prefix+'/result.json', result)
        save_csv(base, prefix+'/episodes.csv', result['rows'])
        paths = [claim, inside(base, prefix+'/result.json'), inside(base, prefix+'/episodes.csv')]
        complete = {'status': 'EVALUATED', 'key': job_key(job), 'proof_sha256': proof_sha256,
                    'evaluation_count': 1, 'files': [{'path': path.relative_to(base).as_posix(),
                        'sha256': sha256_file(path)} for path in paths]}
        save_json(base, prefix+'/complete.json', complete)
    except BaseException as error:
        save_json(base, prefix+'/failure.json', {'status': 'FAILED_SEALED', 'key': job_key(job),
            'error': type(error).__name__+': '+str(error), 'evaluation_count': 1})
        raise
    return read_complete(base, job, proof_sha256)
