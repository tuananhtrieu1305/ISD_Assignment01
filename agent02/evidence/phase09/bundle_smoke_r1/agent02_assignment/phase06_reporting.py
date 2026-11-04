"""Read completed Phase6 outputs to build tables, grayscale figures and Vietnamese notes."""

import csv
import json
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use('Agg')
import matplotlib.pyplot as plt

from .code.evaluation.phase06_journal import PREFIX
from .code.phase06_analysis import aggregate
from .phase02 import save_csv, save_json
from .phase03 import writer_lock
from .phase06 import assert_proof
from .workspace import sha256_file

BASE = Path(__file__).resolve().parent
FIG, MET = 'artifacts/figures/phase06', 'artifacts/metrics/phase06'


def load_records():
    completion = json.loads((BASE/'artifacts/evaluation/phase06/completion.json').read_text())
    return [{'job': entry['job'], 'result': json.loads((BASE/PREFIX/entry['key']/'result.json').read_text())}
            for entry in completion['entries']]


def rows_for(spec):
    with (BASE/'artifacts/runs'/spec['run_id']/'episode_rewards.csv').open() as stream:
        return [{k: json.loads(v) for k, v in row.items()} for row in csv.DictReader(stream)]


def train_diagnostics(matrix):
    summaries, curves, drift = [], [], []
    for spec in matrix:
        rows = rows_for(spec)
        pair = spec['learners']==2
        fields = ['agent0_mean_reward_per_step', 'agent1_mean_reward_per_step'] if pair else [
            'rl_mean_reward_per_step', 'rule_mean_reward_per_step']
        for learner, field in enumerate(fields):
            values = np.array([r[field] for r in rows])
            summaries.append({'run_id': spec['run_id'], 'kernel': spec['kernel_id'], 'seed': spec['seed'],
                'learners': spec['learners'], 'agent': learner, 'train_mean': float(values.mean()),
                'episode_std_ddof1': float(values.std(ddof=1)), 'first100_mean': float(values[:100].mean()),
                'last100_mean': float(values[-100:].mean()), 'last100_std_ddof1': float(values[-100:].std(ddof=1))})
            if pair:
                smoothed = np.convolve(values, np.ones(100)/100, mode='valid')
                curves.append({'seed': spec['seed'], 'learner': learner, 'values': smoothed})
        if pair:
            previous = None
            for episode in range(0, 5001, 100):
                checkpoint = json.loads((BASE/'artifacts/runs'/spec['run_id']/f'checkpoint_e{episode:06d}.json').read_text())
                q = np.array(checkpoint['q'])
                if previous is not None:
                    for learner in (0, 1):
                        best = np.isclose(q[learner], q[learner].max(axis=-1, keepdims=True))
                        oldbest = np.isclose(previous[learner], previous[learner].max(axis=-1, keepdims=True))
                        drift.append({'seed': spec['seed'], 'learner': learner, 'end_episode': episode,
                            'q_l2_change': float(np.linalg.norm(q[learner]-previous[learner])),
                            'greedy_action_sets_changed_of4': int(np.any(best != oldbest, axis=-1).sum())})
                previous = q
    curve_rows = []
    for learner in (0, 1):
        values = np.array([r['values'] for r in curves if r['learner']==learner])
        for index, (mean, std) in enumerate(zip(values.mean(axis=0), values.std(axis=0, ddof=1), strict=True)):
            curve_rows.append({'learner': learner, 'episode': index+100, 'mean': float(mean), 'std': float(std)})
    return summaries, curve_rows, drift


def main():
    with writer_lock(BASE):
        declaration = assert_proof('evidence/phase06/train_declaration.json')
        assert_proof('evidence/phase06/eval_declaration.json')
        data = aggregate(load_records())
        train, curves, drift = train_diagnostics(declaration['matrix'])
        for key, value in {**data, 'train_summary': train, 'pair_train_curves': curves, 'policy_drift': drift}.items():
            save_csv(BASE, MET+'/'+key+'.csv', value)
        save_json(BASE, MET+'/summary.json', {k: data[k] for k in ('variant_summary', 'q8_summary')})
        gold = json.loads((BASE/'data/derived/gold_regime_kernel_v1.json').read_text())
        plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10, 'text.color': 'black',
            'axes.labelcolor': 'black', 'axes.edgecolor': 'black', 'xtick.color': 'black', 'ytick.color': 'black'})
        (BASE/FIG).mkdir(parents=True, exist_ok=True)
        files, notes = [], []
        def finish(fig, name, purpose, axes, legend, aggregation, observations, limitations, source):
            path = BASE/FIG/(name+'.png')
            fig.savefig(path, dpi=180, facecolor='white')
            plt.close(fig)
            files.append({'path': path.relative_to(BASE).as_posix(), 'sha256': sha256_file(path)})
            notes.append({'figure': path.relative_to(BASE).as_posix(), 'purpose': purpose, 'axes_and_units': axes,
                'legend': legend, 'aggregation_and_n': aggregation, 'observations': observations,
                'quantitative_comparison': observations, 'limitations': limitations, 'data_source': source})
        fig, ax = plt.subplots(1, 2, figsize=(11.5, 4), layout='constrained')
        prices = [r['gold_usd_per_troy_ounce'] for r in gold['records']]
        ax[0].plot(np.arange(len(prices)), prices, color='black', lw=1)
        ticks = np.linspace(0, len(prices)-1, 5, dtype=int)
        ax[0].set_xticks(ticks, [gold['records'][i]['month'] for i in ticks], rotation=25)
        ax[0].set(xlabel='Tháng (chỉ prefix TRAIN)', ylabel='USD / troy ounce', title='Giá vàng lịch sử dùng hiệu chỉnh')
        matrix = np.array(gold['kernel'])
        ax[1].imshow(matrix, cmap='Greys', vmin=0, vmax=1)
        for i in (0, 1):
            for j in (0, 1):
                ax[1].text(j, i, f'{matrix[i,j]:.4f}', ha='center', va='center', color='black',
                           bbox={'facecolor': 'white', 'edgecolor': 'none', 'alpha': .85})
        ax[1].set(xticks=[0, 1], yticks=[0, 1], xlabel='Chế độ tháng sau', ylabel='Chế độ hiện tại', title='Kernel đã cộng Laplace +1')
        finish(fig, 'gold_calibration', 'Mô tả dữ liệu thực dùng tạo kịch bản, không phải đo demand.',
            'Trái:X tháng,Y USD/troy ounce;phải:hàng regime hiện tại,cột regime kế;ô xác suất0–1.',
            'Đường đen:giá tháng;ô xám/xác suất:kernel.', '560giá tháng,559regime,558transition;không smoothing giá.',
            f'01/1960–08/2006;min{min(prices):.2f},max{max(prices):.2f};counts{gold["transition_counts"]};'
            f'P00={matrix[0,0]:.4f},P11={matrix[1,1]:.4f};persistent giữ0,9,còn IID0,5.',
            'Regime1 là giá tăng,0 gồm giảm/không đổi;giá không đo demand. Vintage sửa hồi tố;không backtest đầu tư.',
            'data/derived/gold_regime_kernel_v1.json và gold_train_prefix_v1.csv')
        fig, ax = plt.subplots(2, 1, figsize=(10.5, 6.5), sharex=True, layout='constrained')
        for learner in (0, 1):
            selected = [r for r in curves if r['learner']==learner]
            x, y, s = np.array([[r[k] for r in selected] for k in ('episode', 'mean', 'std')])
            ax[learner].plot(x, y, color='black', label=f'Learner {learner}, MA100')
            ax[learner].fill_between(x, y-s, y+s, color='.8', label='±1 sample std giữa5 pair seed')
            ax[learner].set(ylabel='Lợi nhuận giả lập / bước', title=f'Hai agent cùng học: learner {learner}')
            ax[learner].legend(fontsize=8)
        ax[-1].set_xlabel('Episode train (5.000/run)')
        selected = [r for r in train if r['learners']==2]
        observations = ';'.join(f'learner{i}:mean train={np.mean([r["train_mean"] for r in selected if r["agent"]==i]):.5f},'
            f'std100episode cuối trung bình={np.mean([r["last100_std_ddof1"] for r in selected if r["agent"]==i]):.5f}' for i in (0, 1))
        finish(fig, 'two_learner_training', 'Quan sát reward và độ biến động khi đối thủ cũng thay đổi.',
            'X:episode train;Y:lợi nhuận giả lập/bước.', 'Mỗi panel một learner;đen meanMA100,xám±std.',
            'Làm mượt riêng mỗi trajectory100episode rồi mean/std ddof1 qua5pair seed;không phảiCI.', observations,
            'Hai learner trong một pair phụ thuộc;vùng mờ chứa cả khác biệt seed và quá trình học. Không chứng minh hội tụ/nhân quả.',
            MET+'/pair_train_curves.csv và train_summary.csv')
        fig, ax = plt.subplots(1, 2, figsize=(11.5, 4.2), layout='constrained')
        q8 = data['q8_summary']
        ax[0].errorbar([r['checkpoint_episode'] for r in q8], [r['target_mean'] for r in q8],
            yerr=[r['target_std'] for r in q8], color='black', marker='o', capsize=4)
        ax[0].set(xlabel='Checkpoint episode', ylabel='Lợi nhuận / bước (Q đóng băng)', title='Đo trước cùng fixed rule / tapes')
        ends = sorted({r['end_episode'] for r in drift})
        changed = [np.mean([r['greedy_action_sets_changed_of4'] for r in drift if r['end_episode']==e]) for e in ends]
        ax[1].plot(ends, changed, color='black')
        ax[1].set(xlabel='Cuối khoảng100episode train', ylabel='Số state đổi tập greedy (trên4)', title='Policy drift giữa checkpoint liền kề')
        totalchanges = sum(r['greedy_action_sets_changed_of4'] for r in drift)
        finish(fig, 'checkpoint_drift', 'Tách đo policy cố định khỏi reward khi cùng học.',
            'Trái:X checkpoint,Y profit/bước;phải:X cuối100episode,Y số state đổi tập greedy/4.',
            'Đen mean;whisker trái±std;đường phải mean sốstate đổi.',
            'Trái:gộp2vai,rồi2learner trong pair,rồi5pair seed;500episode/vai. Phải:mean10learner thuộc5pair,khôngCI.',
            ';'.join(f'e{r["checkpoint_episode"]}:{r["target_mean"]:.5f}±{r["target_std"]:.5f}' for r in q8)+
            f';tổng{totalchanges}state-change trên500learner-interval;Q-L2 cũng lưuCSV.',
            'Bốn điểm repeated measures,không chọn checkpoint tốt nhất;drift ở state không gặp có thể không đổi return. Không chứng minh nguyên nhân từ opponent.',
            MET+'/q8_summary.csv và policy_drift.csv')
        fig, ax = plt.subplots(1, 2, figsize=(11.5, 4.5), layout='constrained')
        policies = ('baseline_iid', 'retrained', 'rule', 'no_discount')
        summary = data['variant_summary']
        for index, kernel in enumerate(('persistent', 'gold')):
            selected = [next(r for r in summary if r['kernel']==kernel and r['policy']==p) for p in policies]
            x = np.arange(4)
            ax[index].bar(x, [r['target_mean'] for r in selected], color=['.3', '.5', '.7', '.9'], edgecolor='black',
                yerr=[r['target_std'] for r in selected], capsize=3)
            ax[index].set_xticks(x, ['Q IID cũ', 'Q train lại', 'Rule', 'Giữ giá'], rotation=15)
            ax[index].set(ylabel='Lợi nhuận giả lập / bước', title=f'Kernel {kernel}: cùng opponent/tape')
        differences = []
        for kernel in ('persistent', 'gold'):
            values = [r['retrained_minus_baseline'] for r in data['variant_deltas'] if r['kernel']==kernel]
            differences.append(f'{kernel}:retrain−baseline={np.mean(values):.5f}±{np.std(values,ddof=1):.5f}')
        finish(fig, 'variant_robustness', 'So policy cũ với retrain khi chỉ đổi kernel nhu cầu.',
            'X:4policy,Y:lợi nhuận giả lập/bước;hai panel kernel khác.',
            'Cột xám mean;whisker±sample std qua5seed/panel.',
            '500episode/vai,gộp vai trước;5trainingseed choQ,5scenario panel cho controls;paired delta cùngseed/tape.',
            ';'.join(differences), 'Không so rawreturn giữa kernel như cùng phân phối;controls có thể trùng hành vi. Không bảo đảm retrain thắng;n5 nhỏ,khôngCI/kiểm định.',
            MET+'/variant_seed.csv,variant_summary.csv,variant_deltas.csv')
        save_json(BASE, FIG+'/figure_notes.json', notes)
        text = '# Giải thích hình Phase6\n\n'+'\n\n'.join('## '+Path(n['figure']).stem+'\n\n'+
            '\n\n'.join(f'**{k}**: {v}' for k, v in n.items() if k!='figure') for n in notes)+'\n'
        (BASE/FIG/'figure_notes.md').write_text(text, encoding='utf-8')
        manuscript = '# Câu8–9: tương tác và sửa môi trường\n\n'+(
            'Khi cả hai Q-learning cùng cập nhật, cùng state/action có thể dẫn tới kết quả khác vì policy đối thủ đổi. '
            'Đó là khó khăn non-stationarity. Thí nghiệm5pair độc lập giữ nguyên learning budget; '
            'fixed-opponent evaluation ở4checkpoint giúp đo learner trước cùng chuẩn. Không tự kết luận hội tụ.\n\n'
            'Chỉ sửa kernel demand:IID→persistent0,9 hoặc kernelGold TRAIN. Giá/reward/action/rule không đổi. '
            'Gold là proxy mô phỏng từ biến động giá, không phải dataset cầu vàng hoặc chứng minh kinh doanh.\n\n')
        manuscript += '|Kernel|Policy|Mean profit/bước|Sample std|n|\n|---|---|---:|---:|---:|\n'
        manuscript += ''.join(f'|{r["kernel"]}|{r["policy"]}|{r["target_mean"]:.5f}|{r["target_std"]:.5f}|5|\n' for r in summary)
        manuscript += '\nPaired delta retrain−baseline: '+'; '.join(differences)+'.\n\n'
        manuscript += ('Hạn chế:conversion minh họa chưa hiệu chỉnh khách hàng;demand đơn giản vàGoldkhông đo nhu cầu;'
            'state cũ thiếu own_previous/time;không inventory/dị biệt khách;hai shop có thể cùng bán cho mô phỏng riêng,không thị phần zero-sum. '
            'Thay kernel giải quyết độ bền demand giả lập, chưa xử lý hết các hạn chế này.\n\n'+text)
        path = BASE/'report/sections/phase06_robustness.md'
        path.write_text(manuscript, encoding='utf-8')
        paths = [p for folder in (BASE/MET, BASE/FIG) for p in folder.glob('*') if p.is_file()]+[path]
        save_json(BASE, FIG+'/manifest.json', {'status': 'GENERATED_PENDING_VISUAL_QA',
            'generator_sha256': sha256_file(Path(__file__)), 'figures': files,
            'files': [{'path': p.relative_to(BASE).as_posix(), 'sha256': sha256_file(p)} for p in sorted(paths)]})
        print(json.dumps({'status': 'GENERATED', 'figures': 4, 'csv': 9, 'variant_summary': summary, 'q8_summary': q8}, indent=2))


if __name__ == '__main__':
    main()
