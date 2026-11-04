"""Three-kernel, three-policy role-first aggregates from saved final outputs."""

from .evaluation.aggregate_v1 import SEEDS, mean_std, role_average, validate_result

KERNELS=('iid','persistent','gold')
POLICIES=('augmented','baseline','rule')


def aggregate(records):
    if len(records)!=90:
        raise ValueError('Require30new+60reused final claims')
    indexed={}
    for record in records:
        validate_result(record['result'])
        j=record['job']
        key=(j['kernel_id'],j['policy_id'],j['seed'],j['role'])
        if key in indexed or j['kernel_id'] not in KERNELS or j['policy_id'] not in POLICIES or j['seed'] not in SEEDS:
            raise ValueError('Duplicate/unknown final identity')
        indexed[key]=record
    def pair(kernel,policy,seed):
        try:
            return role_average([indexed[kernel,policy,seed,role] for role in (0,1)])
        except KeyError as error:
            raise ValueError('Missing paired role/policy/seed') from error
    seedrows,summary,deltas,delta_summary=[],[],[],[]
    for kernel in KERNELS:
        for policy in POLICIES:
            for seed in SEEDS:
                seedrows.append({'kernel':kernel,'policy':policy,'seed':seed,**pair(kernel,policy,seed)})
            selected=[r for r in seedrows if r['kernel']==kernel and r['policy']==policy]
            mean,std=mean_std([r['target_mean'] for r in selected])
            rate_mean,rate_std=mean_std([r['discount_rate'] for r in selected])
            summary.append({'kernel':kernel,'policy':policy,'profit_mean':mean,'profit_std':std,
                'discount_rate_mean':rate_mean,'discount_rate_std':rate_std,'n_seed_or_panels':5,
                'trained_replicates':policy!='rule','std_ddof':1})
        for seed in SEEDS:
            new=pair(kernel,'augmented',seed)['target_mean']
            deltas.append({'kernel':kernel,'seed':seed,'delta_vs_baseline':new-pair(kernel,'baseline',seed)['target_mean'],
                          'delta_vs_rule':new-pair(kernel,'rule',seed)['target_mean']})
        row={'kernel':kernel,'n_training_seeds':5,'roles_averaged_first':True,'std_ddof':1}
        for field in ('delta_vs_baseline','delta_vs_rule'):
            mean,std=mean_std([r[field] for r in deltas if r['kernel']==kernel])
            row[field+'_mean'],row[field+'_std']=mean,std
        delta_summary.append(row)
    return {'seed_comparison':seedrows,'policy_summary':summary,'paired_deltas':deltas,'delta_summary':delta_summary}
