"""Role-first seed-level comparisons with saved baseline references, no new forwards."""

import copy

import pytest

from agent02_assignment.code.phase07_analysis import aggregate


def fixtures():
    records=[]
    for kernel in ('iid','persistent','gold'):
        for seed in (11,22,33,44,55):
            for policy,value in [('augmented',33.),('baseline',32.),('rule',35.)]:
                for role in (0,1):
                    mean=value+role
                    result={'episodes':1,'steps':20,'total_reward':mean*20,'mean_reward':mean,
                        'opponent_total_reward':200.,'opponent_mean_reward':10.,
                        'learner_action_counts':[20,0],'opponent_action_counts':[20,0],
                        'rows':[{'learner_reward':mean*20,'opponent_reward':200.,
                                 'learner_action_counts':[20,0],'opponent_action_counts':[20,0]}]}
                    records.append({'job':{'kernel_id':kernel,'policy_id':policy,'seed':seed,'role':role},'result':result})
    return records


def test_compare_three_policies_role_average_then_five_seeds():
    result=aggregate(fixtures())
    assert len(result['seed_comparison'])==45 and len(result['policy_summary'])==9
    assert len(result['paired_deltas'])==15 and len(result['delta_summary'])==3
    assert result['policy_summary'][0]['profit_mean']==33.5
    assert result['delta_summary'][0]['delta_vs_baseline_mean']==1.
    assert result['delta_summary'][0]['delta_vs_rule_mean']==-2.
    assert result['delta_summary'][0]['n_training_seeds']==5


@pytest.mark.parametrize('kind',['missing','duplicate','totals','policy'])
def test_bad_comparison_inputs(kind):
    records=copy.deepcopy(fixtures())
    if kind=='missing':
        records.pop()
    elif kind=='duplicate':
        records[-1]=records[0]
    elif kind=='totals':
        records[0]['result']['total_reward']+=1
    else:
        records[0]['job']['policy_id']='other'
    with pytest.raises(ValueError):
        aggregate(records)
