"""Six final tables and four explained grayscale figures from saved claims only."""

import csv
import json
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use('Agg')
import matplotlib.pyplot as plt

from .code.evaluation.aggregate_v1 import aggregate_evaluations
from .code.evaluation.journal_v1 import PREFIX, read_complete
from .code.sweep_analysis import CONFIG_IDS
from .phase02 import save_csv, save_json
from .phase05 import assert_declaration
from .workspace import sha256_file

BASE = Path(__file__).resolve().parent
METRIC, FIG = 'artifacts/metrics/phase05', 'artifacts/figures/phase05'
LABELS = ['Baseline', 'α=0,01', 'α=0,50', 'ε=0,05', 'ε=0,30']


def collect():
    declaration = assert_declaration()
    proof = sha256_file(BASE/'evidence/phase05/declaration.json')
    records, sources = [], []
    for job in declaration['jobs']:
        receipt = read_complete(BASE, job, proof)
        relative = PREFIX+'/'+receipt['key']+'/result.json'
        result = json.loads((BASE/relative).read_text())
        records.append({'job': job, 'result': result})
        sources.append({'job_id': job['job_id'], 'path': relative, 'sha256': sha256_file(BASE/relative)})
    return records, aggregate_evaluations(records), sources


def build():
    folder = BASE/FIG
    if (folder/'manifest.json').exists():
        saved = json.loads((folder/'manifest.json').read_text())
        for item in saved['files']:
            if sha256_file(BASE/item['path']) != item['sha256']:
                raise ValueError('Presentation changed; preserve and revise')
        return saved
    folder.mkdir(parents=True, exist_ok=True)
    if list(folder.iterdir()):
        raise FileExistsError('Keep partial presentation; use a revision')
    records, aggregate, sources = collect()
    configs = aggregate['config_summary']
    baseline = [{'track': 'CONTROLLED', 'train_seed': row['train_seed'], 'roles': 2,
                 'target_mean': row['target_mean'], 'opponent_mean': row['opponent_mean'],
                 'target_total': row['target_total_sum_roles'], 'opponent_total': row['opponent_total_sum_roles'],
                 'steps': row['steps_sum_roles'], 'scope': 'matched tapes, role average; one trained seed'}
                for row in aggregate['multi_seed'] if row['config_id'] == 'baseline']
    native = aggregate['reference_native']
    baseline.append({'track': 'REF_NATIVE', 'train_seed': 42, 'roles': 1,
        'target_mean': native['target_mean'], 'opponent_mean': native['opponent_mean'],
        'target_total': native['target_total'], 'opponent_total': native['opponent_total'], 'steps': native['steps'],
        'scope': 'native teacher RNG, role0 only; excluded from CONTROLLED n5'})
    q_rows, seen = [], set()
    for record in records:
        job = record['job']
        if 'run_id' not in job or job['run_id'] in seen:
            continue
        seen.add(job['run_id'])
        q = np.array(json.loads((BASE/job['q_path']).read_text()))
        for d in (0, 1):
            for previous in (0, 1):
                q_rows.append({'run_id': job['run_id'], 'config_id': job['config_id'], 'seed': job['train_seed'],
                    'demand': d, 'competitor_previous': previous, 'q_no_discount': float(q[d, previous, 0]),
                    'q_discount': float(q[d, previous, 1]),
                    'greedy_actions': np.flatnonzero(np.isclose(q[d, previous], q[d, previous].max())).tolist(),
                    'q_sha256': job['policy_sha256']})
    for filename, rows in [('baseline_reward.csv', baseline), ('q_policy.csv', q_rows),
        ('alpha_comparison.csv', [row for row in configs if row['config_id'] in ('alpha_low', 'baseline', 'alpha_high')]),
        ('exploration_comparison.csv', [row for row in configs if row['config_id'] in
            ('epsilon_low_fixed', 'baseline', 'epsilon_high_fixed')]),
        ('multi_seed.csv', aggregate['multi_seed']), ('paired_comparison.csv', aggregate['paired_rows'])]:
        save_csv(BASE, METRIC+'/'+filename, rows)
    save_json(BASE, METRIC+'/config_summary.json', configs)
    save_json(BASE, METRIC+'/controls_summary.json', aggregate['controls'])
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10, 'text.color': 'black',
                         'axes.labelcolor': 'black', 'savefig.facecolor': 'white'})
    means, stds = [row['target_mean'] for row in configs], [row['target_std'] for row in configs]
    controls = aggregate['controls']
    control_mean = float(np.mean([row['target_mean'] for row in controls if row['kind'] == 'rule']))
    figure, axis = plt.subplots(figsize=(10.4, 5.4), layout='constrained')
    axis.bar(range(5), means, yerr=stds, capsize=5, color='.7', edgecolor='black', label='Q: mean ± std giữa 5 training seed')
    axis.axhline(control_mean, color='black', linestyle='--', label='Rule-vs-rule: mean qua 5 kịch bản')
    axis.set_xticks(range(5), LABELS)
    axis.set(xlabel='Cấu hình đã train', ylabel='Lợi nhuận giả lập / bước',
             title='Final: Q đóng băng trước cùng fixed-rule opponent\nHai vai được lấy trung bình trước khi tổng hợp 5 seed')
    axis.legend(loc='lower left', fontsize=9)
    figure.savefig(folder/'final_profit.png', dpi=190)
    plt.close(figure)
    figure, axes = plt.subplots(1, 2, figsize=(11, 5.1), layout='constrained')
    for axis, stem, title in [(axes[0], 'paired_delta_baseline', 'Chênh policy so với Q baseline cùng seed/tape'),
                               (axes[1], 'within_match_delta', 'Q trừ đối thủ rule trong cùng cuộc đối đầu')]:
        axis.errorbar(range(5), [row[stem+'_mean'] for row in configs], yerr=[row[stem+'_std'] for row in configs],
                      fmt='o', color='black', capsize=5)
        axis.axhline(0, color='.5', linestyle='--')
        axis.set_xticks(range(5), LABELS, rotation=25)
        axis.set(title=title, xlabel='Cấu hình', ylabel='Chênh lợi nhuận giả lập / bước')
        axis.grid(alpha=.15)
    figure.suptitle('Hai câu hỏi khác nhau; whisker = sample std giữa 5 giá trị seed, không phải CI', fontsize=11)
    figure.savefig(folder/'paired_and_match.png', dpi=190)
    plt.close(figure)
    with (BASE/'artifacts/metrics/phase04/config_train_summary.csv').open(encoding='utf-8') as stream:
        train = {row['config_id']: row for row in csv.DictReader(stream)}
    with (BASE/'artifacts/metrics/phase04/seed_train_summary.csv').open(encoding='utf-8') as stream:
        train_seeds = list(csv.DictReader(stream))
    x, width = np.arange(5), .36
    for filename, title, ylabel, train_mean, train_std, final_mean, final_std in [
        ('train_vs_final.png', 'Reward khi học khác reward của policy cuối', 'Lợi nhuận giả lập / bước',
         [float(train[c]['rl_train_mean']) for c in CONFIG_IDS], [float(train[c]['rl_train_std']) for c in CONFIG_IDS], means, stds),
        ('discount_rates.png', 'Tần suất giảm giá lúc train và khi Q đóng băng', 'Action giảm giá (%)',
         [100*np.mean([json.loads(row['rl_action_counts'])[1]/100000 for row in train_seeds if row['config_id']==c]) for c in CONFIG_IDS],
         [100*np.std([json.loads(row['rl_action_counts'])[1]/100000 for row in train_seeds if row['config_id']==c], ddof=1) for c in CONFIG_IDS],
         [100*row['discount_rate_mean'] for row in configs], [100*row['discount_rate_std'] for row in configs])]:
        figure, axis = plt.subplots(figsize=(10.4, 5.4), layout='constrained')
        axis.bar(x-width/2, train_mean, width, yerr=train_std, capsize=4, color='.78', edgecolor='black', label='Train: 5 mean/run')
        axis.bar(x+width/2, final_mean, width, yerr=final_std, capsize=4, color='.3', edgecolor='black', label='Final: 5 mean/seed sau gộp vai')
        axis.set_xticks(x, LABELS)
        axis.set(title=title+'\nWhisker = sample std giữa 5 seed (ddof=1)', xlabel='Cấu hình', ylabel=ylabel)
        axis.legend(fontsize=9, loc='lower left' if filename == 'train_vs_final.png' else 'upper right')
        figure.savefig(folder/filename, dpi=190)
        plt.close(figure)
    numbers = '; '.join(f"{LABELS[i]}: {row['target_mean']:.5f} ± {row['target_std']:.5f}" for i, row in enumerate(configs))
    deltas = '; '.join(f"{LABELS[i]}: {row['paired_delta_baseline_mean']:.5f} ± {row['paired_delta_baseline_std']:.5f}"
                       for i, row in enumerate(configs))
    rates = '; '.join(f"{LABELS[i]}: {100*row['discount_rate_mean']:.3f}% ± {100*row['discount_rate_std']:.3f} điểm %"
                      for i, row in enumerate(configs))
    common = ('Mỗi final claim có 500 episode×20 bước, mỗi Q chạy hai vai. Lấy mean hai vai trước, '
              'sau đó mean/sample std ddof=1 giữa 5 training seed. Không gộp 10 vai hoặc 5.000 episode '
              'thành learner độc lập. Không có CI/kiểm định ý nghĩa từ whisker; đây là mô phỏng, chỉ 5 seed. ')
    notes = [
        {'figure_id': 'final_profit', 'path': FIG+'/final_profit.png', 'source': METRIC+'/config_summary.json',
         'explanation': 'Trục x: 5 cấu hình; y: profit giả lập/bước trước fixed-rule opponent. Cột xám là Q '
         'đóng băng, whisker là std giữa training seed; đường đứt là mean Rule-vs-rule qua5 kịch bản, '
         'không phải đối chứng đã train. '+common+numbers+'. Mean đối chứng '+f'{control_mean:.5f}. '
         'Reward giữa các config được đo trên cùng tape theo seed và role. Không dùng final để tuning/chọn lại seed. '
         'Nếu hai policy cho cùng score, chỉ kết luận trên các trajectory này, không chứng minh tương đương mọi state.'},
        {'figure_id': 'paired_and_match', 'path': FIG+'/paired_and_match.png', 'source': METRIC+'/paired_comparison.csv',
         'explanation': 'Hai panel cùng trục x cấu hình, trục y chênh profit/bước; mốc đứt0 là bằng nhau. '
         'Trái ghép Q cấu hình trừ Q baseline cùng training seed, tape và fixed opponent; phải so chất lượng policy theo panel này. '
         'Panel phải là Q trừ reward của rule trong chính cuộc đối đầu, có thể chịu phản ứng của rule với learner. '
         'Chấm là mean, whisker sample std giữa5 delta seed, không phải CI. '+common+'Delta so baseline: '+deltas+'. '
         'Không đánh đồng lợi thế trong trận với hơn một policy khác trước cùng opponent.'},
        {'figure_id': 'train_vs_final', 'path': FIG+'/train_vs_final.png',
         'source': 'artifacts/metrics/phase04/config_train_summary.csv; '+METRIC+'/config_summary.json',
         'explanation': 'Trục x cấu hình, y profit/bước. Cột sáng lấy reward toàn giai đoạn học (còn exploration và Q đang đổi), '
         'cột tối lấy policy cuối đóng băng, tắt exploration và dùng final scenarios riêng. Hai loại whisker đều giữa5 seed, '
         'nhưng đo hai đại lượng khác nhau; không coi reward train thấp là final policy kém. '+common+
         'Final: '+numbers+'. Chênh train/final có cả thay đổi policy, exploration và tập scenario, '
         'không quy toàn bộ tác dụng cho riêng việc tắt epsilon. Không gọi score tăng là chứng minh hội tụ.'},
        {'figure_id': 'discount_rates', 'path': FIG+'/discount_rates.png', 'source': METRIC+'/multi_seed.csv; phase04/seed_train_summary.csv',
         'explanation': 'Trục x cấu hình; y tỷ lệ action giảm giá (%), không phải epsilon hay xác suất chuyển đổi mua hàng. '
         'Cột sáng toàn100.000 bước train/run, cột tối20.000 bước final/seed (hai vai); whisker sample std giữa5 seed, đơn vị điểm %. '
         'Final: '+rates+'. '+common+'Giảm giá làm lãi mỗi món từ5 còn3; giảm giá nhiều không tự chứng minh profit tốt. '
         'Policy có thể khác ở state không đạt tới sau reset0. Tần suất là hành vi thực đo, không chỉ đọc argmax toàn bảng Q.'}]
    save_json(BASE, FIG+'/figure_notes.json', notes)
    text = ['# Giải thích biểu đồ final phase5\n\nSố đo synthetic; không chọn tham số từ kết quả cuối.']
    for note in notes:
        text.append(f"## {note['figure_id']}\n\n![{note['figure_id']}]({note['figure_id']}.png)\n\n"
                    f"Nguồn: `{note['source']}`.\n\n{note['explanation']}\n")
    (folder/'figure_notes.md').write_text('\n\n'.join(text), encoding='utf-8')
    manuscript = BASE/'report/sections/phase05_final_evaluation.md'
    body = ['# E — đánh giá riêng, Q đóng băng\n', common,
        ('\n71 claim: 50 core +20 đối chứng +1 REF native riêng, mỗi claim chạy đúng1 lần. '
        'Không train/tuning, Q hash trước/sau giữ nguyên, seed final tách khỏi train/DEV. '
        'Đối chứng rule-vs-rule và no-discount đều bắt đầu lịch sử0; trong mô hình này hai cách có thể '
        'giữ giá mãi trên reachable states, nên không coi chúng là hai policy độc lập về hành vi.\n'),
        '| Cấu hình | Final Q profit/bước ±std | Q−rule trong trận | Q−Rule control (cùng tape) |\n|---|---:|---:|---:|']
    for i, row in enumerate(configs):
        body.append(f"| {LABELS[i]} | {row['target_mean']:.5f} ± {row['target_std']:.5f} | "
                    f"{row['within_match_delta_mean']:.5f} | {row['delta_vs_rule_policy_mean']:.5f} |")
    body.append(f"\nREF native seed42, role0,500 episode: RL {native['target_mean']:.5f}, rule "
                f"{native['opponent_mean']:.5f}/bước. Đây là hàm evaluate_pair gốc với env seed500042 và "
                'RNG policy clone từ checkpoint; không gộp vào CONTROLLED n5 hoặc gọi là paired role-swap.\n')
    for note in notes:
        body.append(f"\n## Hình {note['figure_id']}\n\n{note['explanation']}\n\nHình: `{note['path']}`.\n")
    body.append('\nSáu bảng CSV baseline_reward, q_policy, alpha_comparison, exploration_comparison, '
        'multi_seed, paired_comparison nằm trong artifacts/metrics/phase05/. Q/policy có đủ104 state rows '
        'của26 checkpoint; không dùng giá trị Q như trực tiếp profit final. Phân tích mới chỉ đọc output đã lưu. '
        'Giữ cả kết quả không thắng rule, không đổi hyperparameter/seed sau final.\n')
    manuscript.write_text('\n'.join(body), encoding='utf-8')
    paths = list(folder.iterdir())+list((BASE/METRIC).iterdir())+[manuscript]
    manifest = {'status': 'GENERATED_PENDING_VISUAL_QA', 'charts': 4, 'tables_csv': 6, 'source_results': sources,
        'generator_sha256': sha256_file(Path(__file__)),
        'files': [{'path': path.relative_to(BASE).as_posix(), 'sha256': sha256_file(path)} for path in sorted(paths)]}
    save_json(BASE, FIG+'/manifest.json', manifest)
    return manifest


if __name__ == '__main__':
    print(json.dumps(build(), ensure_ascii=False, indent=2))
