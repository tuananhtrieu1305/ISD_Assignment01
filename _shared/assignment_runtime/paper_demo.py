"""Post-migration demo revision using the pinned serving registry, never TEST gates.

Historical experiment demos require their training-time Git HEAD. That guard remains
unchanged in provenance. These notebook entry points instead use Registry's exact
artifact/source checks and the existing CPU serving implementation (default seed42).
"""
from functools import lru_cache


@lru_cache(maxsize=1)
def registry():
    from apps.api.v3.registry import Registry
    return Registry()


def sample_request(dataset, family=None):
    if dataset.startswith('ch3_'):
        if family not in {None,'cnn'}:
            raise ValueError('Require CNN family')
        from scripts.demo_phase27 import sample_request as original
        return original(dataset)
    if dataset.startswith('ch4_'):
        if family not in {None,'rnn','lstm'}:
            raise ValueError('Require RNN/LSTM family')
        from scripts.demo_phase29 import sample_request as original
        return original(dataset,family or 'rnn')
    raise ValueError('Require a declared Chapter3/4 dataset')


def infer(request, seed=42):
    if seed != 42:
        raise ValueError('This serving-registry revision exposes only pinned seed42')
    if request.get('chapter') not in {3,4}:
        raise ValueError('Require a Chapter3/4 request')
    from apps.api.v3.inference import compare
    job, _ = compare(registry(),request,'job_00000000000000000000000000000000','cpu')
    return job
