"""Declared job matrix, held-out scenario namespaces and gate source binding."""

import json

import pytest

from agent02_assignment.code.evaluation.journal_v1 import job_key
from agent02_assignment.phase05 import assert_declaration, build_jobs
from agent02_assignment.workspace import sha256_file


def test_final_plan_has_50_core_20_controls_one_separate_native_reference():
    jobs = build_jobs()
    assert len(jobs) == len({job_key(job) for job in jobs}) == 71
    assert sum(job['group'] == 'core' for job in jobs) == 50
    assert sum(job['group'] == 'control' for job in jobs) == 20
    assert sum(job['group'] == 'reference_native' for job in jobs) == 1
    assert all(job['episodes'] == 500 and job['steps_per_episode'] == 20 for job in jobs)
    assert sum(job['episodes']*job['steps_per_episode'] for job in jobs) == 710000


def test_core_configs_share_scenarios_by_training_seed_and_both_roles():
    jobs = [job for job in build_jobs() if job['group'] == 'core']
    for seed in (11, 22, 33, 44, 55):
        group = [job for job in jobs if job['train_seed'] == seed]
        assert len(group) == 10 and {job['role'] for job in group} == {0, 1}
        assert {job['scenario_seed'] for job in group} == {2000000+seed}
        assert len({job['scenario_sha256'] for job in group}) == 1


def test_gate_rejects_missing_or_modified_inputs(tmp_path):
    source = tmp_path/'fixture.py'
    source.write_text('x=1')
    path = tmp_path/'evidence/phase05/declaration.json'
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({'files': [{'path': 'fixture.py', 'sha256': sha256_file(source)}]}))
    assert assert_declaration(tmp_path)['files'][0]['path'] == 'fixture.py'
    source.write_text('x=2')
    with pytest.raises(ValueError):
        assert_declaration(tmp_path)
