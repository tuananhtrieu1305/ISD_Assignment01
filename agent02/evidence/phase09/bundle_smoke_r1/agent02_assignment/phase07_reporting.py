"""Saved-output tables/charts and separate analytic model checks for Phase7."""

import csv
import json
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use('Agg')
import matplotlib.pyplot as plt

from .code.evaluation.phase07_journal import PREFIX
from .code.market_oracle import policy_value, solve
from .code.phase07_analysis import KERNELS, POLICIES, aggregate
from .phase02 import save_csv, save_json
from .phase03 import writer_lock
from .phase07 import assert_proof
from .workspace import sha256_file

BASE=Path(__file__).resolve().parent
MET,FIG='artifacts/metrics/phase07','artifacts/figures/phase07'


def collect():
    completion=json.loads((BASE/'artifacts/evaluation/phase07/completion.json').read_text())
    result=[{'job':e['job'],'result':json.loads((BASE/PREFIX/e['key']/'result.json').read_text())} for e in completion['entries']]
    refs=json.loads((BASE/'artifacts/manifests/phase07/reference_index.json').read_text())['entries']
    for r in refs:
        if sha256_file(BASE/r['result_path'])!=r['result_sha256'] or sha256_file(BASE/r['complete_path'])!=r['complete_sha256']:
            raise ValueError('Saved reference changed')
        result.append({'job':{k:r[k] for k in ('kernel_id','policy_id','seed','role')},
                       'result':json.loads((BASE/r['result_path']).read_text())})
    return result


def baseline_id(kernel,seed):
    return f'controlled/iid/baseline/s{seed:04d}' if kernel=='iid' else f'controlled/{kernel}/retrain/s{seed:04d}'


def supporting_tables(declaration):
    from .code.controlled import MarketConfig

    costs,curve_rows,model_rows,oracle_rows=[],[],[],[]
    for kernel in KERNELS:
        market=MarketConfig(**declaration['market_configs'][kernel])
        exact={gamma:solve(market,gamma=gamma)['reset_expected_return'] for gamma in (1.,.9)}
        oracle_rows.append({'kernel':kernel,'optimal_expected_profit_per_step_gamma1':exact[1.]/20,
                           'optimal_discounted_total_gamma09':exact[.9], 'known_model_fixed_rule':True})
        for policy in ('augmented','baseline'):
            trajectories=[]
            for seed in (11,22,33,44,55):
                run_id=f'controlled/{kernel}/augmented/s{seed:04d}' if policy=='augmented' else baseline_id(kernel,seed)
                folder=BASE/'artifacts/runs'/run_id
                done=json.loads((folder/'complete.json').read_text())
                visits=np.array(json.loads((folder/'visits.json').read_text()))
                q=np.array(json.loads((folder/'q_table.json').read_text()))
                costs.append({'kernel':kernel,'policy':policy,'seed':seed,'train_cpu_seconds':done['train_cpu_seconds'],
                    'train_wall_seconds':done['train_wall_seconds'],'q_entries':int(q.size),'q_payload_bytes_float64':int(q.nbytes),
                    'visited_cells':int(np.count_nonzero(visits)),'theoretical_cells':int(visits.size),
                    'visited_fraction':float(np.count_nonzero(visits)/visits.size), 'train_market_steps':100000})
                with (folder/'episode_rewards.csv').open() as stream:
                    rewards=[float(r['rl_mean_reward_per_step']) for r in csv.DictReader(stream)]
                trajectories.append(np.convolve(rewards,np.ones(100)/100,mode='valid'))
                values={gamma:policy_value(market,q=q,kind='augmented' if policy=='augmented' else 'partial',gamma=gamma)[
                    'reset_expected_return'] for gamma in (1.,.9)}
                model_rows.append({'kernel':kernel,'policy':policy,'seed':seed,'exact_expected_profit_per_step_gamma1':values[1.]/20,
                    'exact_discounted_total_gamma09':values[.9], 'expected_profit_gap_to_oracle_gamma1':(exact[1.]-values[1.])/20,
                    'discounted_gap_to_oracle_gamma09':exact[.9]-values[.9]})
            trajectories=np.array(trajectories)
            for index,(mean,std) in enumerate(zip(trajectories.mean(axis=0),trajectories.std(axis=0,ddof=1),strict=True)):
                curve_rows.append({'kernel':kernel,'policy':policy,'episode':index+100,'mean':float(mean),'std':float(std)})
        rulevalues={g:policy_value(market,kind='rule',gamma=g)['reset_expected_return'] for g in (1.,.9)}
        for seed in (11,22,33,44,55):
            model_rows.append({'kernel':kernel,'policy':'rule','seed':seed,'exact_expected_profit_per_step_gamma1':rulevalues[1.]/20,
                'exact_discounted_total_gamma09':rulevalues[.9],'expected_profit_gap_to_oracle_gamma1':(exact[1.]-rulevalues[1.])/20,
                'discounted_gap_to_oracle_gamma09':exact[.9]-rulevalues[.9]})
    if any(r['expected_profit_gap_to_oracle_gamma1'] < -1e-10 or r['discounted_gap_to_oracle_gamma09'] < -1e-10 for r in model_rows):
        raise ValueError('Analytic oracle bound violated')
    return {'train_curves':curve_rows,'cost_coverage':costs,'model_expectations':model_rows,'oracle_summary':oracle_rows}


def main():
    with writer_lock(BASE):
        declaration=assert_proof('evidence/phase07/train_declaration.json')
        assert_proof('evidence/phase07/eval_declaration.json')
        aggregate_data=aggregate(collect())
        support=supporting_tables(declaration)
        for name,rows in {**aggregate_data,**support}.items():
            save_csv(BASE,MET+'/'+name+'.csv',rows)
        save_json(BASE,MET+'/summary.json',{k:aggregate_data[k] for k in ('policy_summary','delta_summary')})
        plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'text.color':'black','axes.labelcolor':'black',
                             'xtick.color':'black','ytick.color':'black','axes.edgecolor':'black'})
        (BASE/FIG).mkdir(parents=True,exist_ok=True)
        notes,figures=[],[]
        def finish(fig,name,purpose,axes,legend,aggregation,observations,limits,sources):
            target=BASE/FIG/(name+'.png')
            fig.savefig(target,dpi=180,facecolor='white')
            plt.close(fig)
            figures.append({'path':target.relative_to(BASE).as_posix(),'sha256':sha256_file(target)})
            notes.append({'figure':target.relative_to(BASE).as_posix(),'purpose':purpose,'axes_and_units':axes,'legend':legend,
                'aggregation_and_n':aggregation,'observations':observations,'quantitative_comparison':observations,
                'limitations':limits,'data_source':sources})
        fig,axes=plt.subplots(3,1,figsize=(10.8,9),sharex=True,layout='constrained')
        curve=support['train_curves']
        curve_obs=[]
        for axis,kernel in zip(axes,KERNELS,strict=True):
            for policy,color,style,label in [('augmented','black','-','State memory/time'),('baseline','.5','--','State cũ, cùng kernel')]:
                rows=[r for r in curve if r['kernel']==kernel and r['policy']==policy]
                x,y,s=np.array([[r[k] for r in rows] for k in ('episode','mean','std')])
                axis.plot(x,y,color=color,linestyle=style,label=label)
                axis.fill_between(x,y-s,y+s,color=color,alpha=.12)
                curve_obs.append(f'{kernel}/{policy}:MA100 đầu={y[0]:.5f},cuối={y[-1]:.5f}')
            axis.set(title=f'Train trên {kernel}',ylabel='Lợi nhuận giả lập / bước')
            axis.legend(fontsize=8)
        axes[-1].set_xlabel('Episode train (5.000/run)')
        finish(fig,'augmented_training','Đọc diễn biến train khi chỉ thay state.',
            'X:episode train;Y:lợi nhuận giả lập/bước.','Đen liền:augmented;xám đứt:baseline cùngkernel;dải±sample std.',
            'MA100 riêng từng seed trước,rồi mean/std ddof1 qua5seed;khôngCI.', '; '.join(curve_obs),
            'Q đang thay đổi và cònepsilon;traincurve không chứng minh policy cuối tốt hơn/hội tụ. Baseline đọc logcũ,khôngtrain lại.', MET+'/train_curves.csv')
        summary=aggregate_data['policy_summary']
        fig,axes=plt.subplots(1,3,figsize=(12,4.5),layout='constrained')
        for axis,kernel in zip(axes,KERNELS,strict=True):
            rows=[next(r for r in summary if r['kernel']==kernel and r['policy']==p) for p in POLICIES]
            axis.bar(np.arange(3),[r['profit_mean'] for r in rows],yerr=[r['profit_std'] for r in rows],
                     color=['.25','.55','.85'],edgecolor='black',capsize=3)
            axis.set_xticks(np.arange(3),['Memory/time','State cũ','Rule'],rotation=20)
            axis.set(title=kernel,ylabel='Lợi nhuận giả lập / bước')
        observations='; '.join(f'{r["kernel"]}/{r["policy"]}={r["profit_mean"]:.5f}±{r["profit_std"]:.5f}' for r in summary)
        finish(fig,'augmented_final_profit','So chất lượng policy cuối trước cùng fixedrule/scenario.',
            'X:3policy;Y:profit/bước;ba panelkernel.','Cột mean;whisker±sample std.',
            '500episode/vai,gộp2vai trước rồi5seed/kernel.Rule n5 làscenario panel.30claim mới+60reference reuse.',observations,
            'Không so rawprofit xuyênkernel như cùng phân phối;n5 nhỏ,whiskerkhôngCI/kiểmđịnh;khôngtuning từfinal.',
            MET+'/policy_summary.csv và seed_comparison.csv')
        delta=aggregate_data['delta_summary']
        fig,axis=plt.subplots(figsize=(9.5,4.8),layout='constrained')
        x=np.arange(3)
        for field,offset,marker,color,label in [('delta_vs_baseline',-.08,'o','black','Augmented − baseline'),
            ('delta_vs_rule',.08,'s','.5','Augmented − rule')]:
            axis.errorbar(x+offset,[r[field+'_mean'] for r in delta],yerr=[r[field+'_std'] for r in delta],
                          linestyle='none',marker=marker,color=color,capsize=4,label=label)
        axis.axhline(0,color='.7',linestyle='--')
        axis.set_xticks(x,KERNELS)
        axis.set(xlabel='Kernel nhu cầu',ylabel='Chênh lợi nhuận giả lập / bước',title='Chênh ghép cặp theo seed, cùng tape/opponent')
        axis.legend(fontsize=9)
        observations='; '.join(f'{r["kernel"]}:Δbaseline={r["delta_vs_baseline_mean"]:.5f}±{r["delta_vs_baseline_std"]:.5f},'
            f'Δrule={r["delta_vs_rule_mean"]:.5f}±{r["delta_vs_rule_std"]:.5f}' for r in delta)
        finish(fig,'augmented_paired_delta','Trả lời state mới có cải thiện mean trên cả3kernel hay không.',
            'X:kernel;Y:profit augmented trừ đối chứng/bước.','Tròn đen:trừbaseline;vuôngxám:trừrule;đứtngang:mốc0.',
            'Tính delta saugộp role cho từngseed,rồi mean±sample std qua5seed;khôngCI.',observations,
            'Mean dương không tự chứng minh cóýnghĩathốngkê;giữmọiseed,kểcảbấtlợi.Không đổi budget đểđảo kếtquả.',
            MET+'/paired_deltas.csv và delta_summary.csv')
        costs=support['cost_coverage']
        fig,axes=plt.subplots(1,2,figsize=(11.5,4.5),layout='constrained')
        cost_obs=[]
        for policy,offset,color,label in [('augmented',-.18,'.3','Memory/time'),('baseline',.18,'.75','State cũ')]:
            fractions,cpu,cpu_std=[],[],[]
            for kernel in KERNELS:
                rows=[r for r in costs if r['kernel']==kernel and r['policy']==policy]
                fractions.append(100*np.mean([r['visited_fraction'] for r in rows]))
                cpu.append(np.mean([r['train_cpu_seconds'] for r in rows]))
                cpu_std.append(np.std([r['train_cpu_seconds'] for r in rows],ddof=1))
                cost_obs.append(f'{kernel}/{policy}:visited={fractions[-1]:.2f}%,CPUmean={cpu[-1]:.4f}s')
            axes[0].bar(x+offset,fractions,width=.36,color=color,edgecolor='black',label=label)
            axes[1].bar(x+offset,cpu,yerr=cpu_std,capsize=3,width=.36,color=color,edgecolor='black',label=label)
        for axis in axes:
            axis.set_xticks(x,KERNELS)
            axis.legend(fontsize=8)
        axes[0].set(ylabel='Ô state-action đã thăm / tổng ô (%)',ylim=(0,105),title='Coverage bảng lý thuyết: 320 so với 8 ô')
        axes[1].set(ylabel='CPU giây / 100.000 train market step',title='Chi phí loop train có instrumentation')
        finish(fig,'augmented_coverage_cost','Đối chiếu kích cỡ bảng,visitation và chi phí.',
            'X:kernel;tráiY:%ôQ đãthăm;phảiY:CPUgiây/run.','Xámđậm:augmented;nhạt:baseline;phảiwhiskerstd5seed.',
            'Mean qua5run/kernel/model,CPUstd ddof1;coverage dùngmẫusố320/8ô,bảngfloat642.560/64byte.', '; '.join(cost_obs),
            'Một sốô fullstate không thểđạt từreset/horizon;coverage thấp khôngtựlàlỗi. CPUkhônggồmcheckpointI/O,khôngpeakRAM/benchmarkmáy.',
            MET+'/cost_coverage.csv')
        save_json(BASE,FIG+'/figure_notes.json',notes)
        text='# Giải thích hình Phase7\n\n'+'\n\n'.join('## '+Path(n['figure']).stem+'\n\n'+
            '\n\n'.join(f'**{k}**: {v}' for k,v in n.items() if k!='figure') for n in notes)+'\n'
        (BASE/FIG/'figure_notes.md').write_text(text,encoding='utf-8')
        manuscript=('# Câu10 — state có memory và thời gian\n\n'
            'State=(nhu cầu,hành động trước của mình,hành động trước của đối thủ,số bước còn lại). '
            'Action/reward vẫn giữ giá hoặc giảm giá/lợi nhuận. Q-learning bảng với320giá trị,không deepRL. '
            'Mỗi kernel train5seed với cùngbudget5.000×20;đo500episode/vai,Qđóngbăng. '
            'Baseline cũ train trên cùngkernel vàrule đọc từ savedfinal,cùngtape/opponent.\n\n')
        manuscript+='|Kernel|Policy|Mean profit/bước|Sample std|\n|---|---|---:|---:|\n'+''.join(
            f'|{r["kernel"]}|{r["policy"]}|{r["profit_mean"]:.5f}|{r["profit_std"]:.5f}|\n' for r in summary)
        manuscript+='\nOracle tính kỳ vọng bằng simulator đãbiết/fixedrule;không dùng nhãn train. '
        manuscript+='Gapγ1 dùngprofitkhôngchiếtkhấu;γ0,9 làtargetQ,táchđơnvị. Không gọi oracle làmodel-free đãhọc.\n\n'+text
        target=BASE/'report/sections/phase07_improved_agent.md'
        target.write_text(manuscript,encoding='utf-8')
        paths=[p for folder in (BASE/MET,BASE/FIG) for p in folder.glob('*') if p.is_file()]+[target]
        save_json(BASE,FIG+'/manifest.json',{'status':'GENERATED_PENDING_VISUAL_QA','generator_sha256':sha256_file(Path(__file__)),
            'figures':figures,'files':[{'path':p.relative_to(BASE).as_posix(),'sha256':sha256_file(p)} for p in sorted(paths)]})
        print(json.dumps({'status':'GENERATED','figures':4,'tables_csv':8,'summary':summary,'deltas':delta,
                          'oracle':support['oracle_summary']},indent=2))


if __name__=='__main__':
    main()
