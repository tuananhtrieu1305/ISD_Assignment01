"""Guarded import of the exact local teacher snapshot; never call its main driver."""

import importlib.util
import json
import sys
import time
from pathlib import Path

from ..workspace import sha256_file
from .controlled import integer

BASE = Path(__file__).resolve().parents[1]


def load_reference(path=None):
    expected_path = BASE / 'code/agent02_experiment.py'
    source = expected_path if path is None else Path(path)
    lock = json.loads((BASE / 'evidence/phase01/input_lock.json').read_text())
    expected_hash = next(row['sha256'] for row in lock['files'] if row['path'] == 'code/agent02_experiment.py')
    if source.resolve() != expected_path.resolve() or sha256_file(source) != expected_hash:
        raise ValueError('Only the unchanged Phase 1 reference snapshot may be imported')
    module_name = '_ag02_teacher_reference_v1'
    spec = importlib.util.spec_from_file_location(module_name, source)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def reference_smoke(*, episodes=100, seed=730042):
    integer(episodes, 'episodes', 1)
    integer(seed, 'seed')
    if episodes > 100:
        raise ValueError('Reference smoke is limited to 100 episodes; full runs belong to Phase 3')
    reference = load_reference()
    config = reference.Config(episodes=episodes)
    started = time.perf_counter()
    learner, rows = reference.train_rl_against_rule(config, seed=seed)
    return {'purpose': 'smoke_only_not_experimental_result', 'seed': seed,
            'episodes': episodes, 'market_steps': episodes * config.steps_per_episode,
            'wall_seconds': time.perf_counter() - started,
            'q': learner.q.tolist(), 'rows': rows,
            'reference_sha256': sha256_file(BASE / 'code/agent02_experiment.py'),
            'main_called': False, 'evaluation_performed': False}
