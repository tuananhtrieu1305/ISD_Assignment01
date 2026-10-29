"""Grayscale alpha/exploration train curves; reads completed logs, never evaluates."""

import json
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use('Agg')
import matplotlib.pyplot as plt

from .code.baseline_runs import verify_run
from .code.controlled import LearningConfig
from .code.sweep_analysis import CONFIG_IDS
from .code.sweep_summary import summarize_matrix
from .phase02 import save_csv, save_json
from .phase03_reporting import read_rows
from .phase04 import assert_declaration
from .workspace import sha256_file

BASE = Path(__file__).resolve().parent
FIG = 'artifacts/figures/phase04'
METRIC = 'artifacts/metrics/phase04'
LABELS = {'baseline': 'Baseline: α=0,10; ε giảm', 'alpha_low': 'α=0,01; ε giảm',
          'alpha_high': 'α=0,50; ε giảm', 'epsilon_low_fixed': 'ε cố định 0,05; α=0,10',
          'epsilon_high_fixed': 'ε cố định 0,30; α=0,10'}


def collect():
    declaration = assert_declaration()
    records, sources = [], []
    for spec in declaration['matrix']:
        result = verify_run(BASE, spec['run_id'])
        path = BASE/'artifacts/runs'/spec['run_id']/'episode_rewards.csv'
        records.append({'spec': spec, 'rows': read_rows(path), 'result': result})
        sources.append({'run_id': spec['run_id'], 'path': path.relative_to(BASE).as_posix(),
                        'sha256': sha256_file(path)})
    return summarize_matrix(records), sources


def export(summary, sources):
    save_csv(BASE, METRIC+'/seed_train_summary.csv', summary['seed_summary'])
    save_csv(BASE, METRIC+'/config_train_summary.csv', summary['config_summary'])
    save_csv(BASE, METRIC+'/curves_mean_std.csv', summary['curve_rows'])
    save_json(BASE, METRIC+'/paired_train_deltas.json', summary['paired'])
    save_json(BASE, METRIC+'/source_index.json', sources)
    save_json(BASE, METRIC+'/aggregation.json', {'window': 100, 'n_training_seeds': 5, 'ddof': 1,
        'unit': 'simulated profit per market step', 'partition': 'training',
        'bands': 'Mean +/- one sample std across five smoothed training-seed trajectories; not CI',
        'final_evaluation': False})


def make_curves(summary, configs, filename, title):
    figure, axes = plt.subplots(3, 1, figsize=(10.5, 9.8), sharex=True, sharey=True, layout='constrained')
    for axis, config in zip(axes, configs, strict=True):
        rows = [row for row in summary['curve_rows'] if row['config_id'] == config]
        x = [row['episode'] for row in rows]
        for agent, color, style, label in [('rl', 'black', '-', 'Q-learning'), ('rule', '.5', '--', 'Agent luật')]:
            mean = np.array([row[agent+'_mean'] for row in rows])
            std = np.array([row[agent+'_std'] for row in rows])
            axis.fill_between(x, mean-std, mean+std, color=color, alpha=.13)
            axis.plot(x, mean, color=color, linestyle=style, linewidth=1.1, label=label)
        axis.set_title(LABELS[config])
        axis.set_ylabel('Lợi nhuận giả lập / bước')
        axis.grid(alpha=.15)
        axis.legend(loc='lower right', ncol=2)
    axes[-1].set_xlabel('Episode train (mỗi đường đã làm mượt 100 episode)')
    figure.suptitle(title+'\nMean ± 1 sample std giữa 5 seed; đây là train, không phải final evaluation', fontsize=12)
    figure.savefig(BASE/FIG/filename, dpi=180)
    plt.close(figure)


def build():
    folder = BASE/FIG
    if (folder/'manifest.json').exists():
        result = json.loads((folder/'manifest.json').read_text())
        for item in result['files']:
            if sha256_file(BASE/item['path']) != item['sha256']:
                raise ValueError('Presentation hash mismatch; preserve and revise')
        return result
    folder.mkdir(parents=True, exist_ok=True)
    if list(folder.iterdir()):
        raise FileExistsError('Partial presentation exists; preserve and use a revision')
    summary, sources = collect()
    export(summary, sources)
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10, 'text.color': 'black',
                         'axes.labelcolor': 'black', 'savefig.facecolor': 'white'})
    make_curves(summary, ['alpha_low', 'baseline', 'alpha_high'], 'alpha_curves.png', 'C — Ảnh hưởng learning rate α')
    make_curves(summary, ['epsilon_low_fixed', 'baseline', 'epsilon_high_fixed'],
                'exploration_curves.png', 'D — So sánh lịch khám phá ε')
    data = json.loads((BASE/'docs/protocol_v1.json').read_text())
    figure, axis = plt.subplots(figsize=(10, 4.5), layout='constrained')
    schedule_rows = []
    floor_episode = None
    for config, style, color in [('baseline', '-', 'black'), ('epsilon_low_fixed', '--', '.4'),
                                 ('epsilon_high_fixed', ':', '.65')]:
        learning = LearningConfig(**data['controlled_configs'][config])
        values = [learning.epsilon_at(i) for i in range(5000)]
        axis.plot(range(1, 5001), values, color=color, linestyle=style, linewidth=1.8, label=LABELS[config])
        schedule_rows.extend({'config_id': config, 'episode': i+1, 'epsilon': value} for i, value in enumerate(values))
        if config == 'baseline':
            floor_episode = next(i+1 for i, value in enumerate(values) if value == .02)
    axis.set(xlabel='Episode train', ylabel='Xác suất khám phá ε', ylim=(0, .33),
             title='Lịch ε đã đăng ký trước train (không phải reward)')
    axis.legend(loc='upper right')
    axis.grid(alpha=.15)
    figure.savefig(folder/'epsilon_schedules.png', dpi=180)
    plt.close(figure)
    save_csv(BASE, METRIC+'/epsilon_schedules.csv', schedule_rows)
    figure, axes = plt.subplots(1, 2, figsize=(11, 5.1), sharey=True, layout='constrained')
    short_labels = ['Baseline', 'α=0,01', 'α=0,50', 'ε=0,05', 'ε=0,30']
    for axis, agent, label in zip(axes, ['rl', 'rule'], ['Q-learning', 'Agent luật'], strict=True):
        means = [row[agent+'_train_mean'] for row in summary['config_summary']]
        stds = [row[agent+'_train_std'] for row in summary['config_summary']]
        axis.bar(range(5), means, yerr=stds, capsize=5, color='.72', edgecolor='black')
        axis.set_xticks(range(5), short_labels, rotation=25)
        axis.set_title(label+' — trung bình toàn train')
        axis.set_xlabel('Cấu hình (mỗi nhóm 5 seed)')
    axes[0].set_ylabel('Lợi nhuận giả lập / bước')
    figure.suptitle('Mean ± sample std giữa 5 mean/run; không phải chất lượng final policy', fontsize=12)
    figure.savefig(folder/'train_summary.png', dpi=180)
    plt.close(figure)
    tables = {row['config_id']: row for row in summary['config_summary']}
    notes = []
    for figure_id, configs, purpose in [
        ('alpha_curves', ['alpha_low', 'baseline', 'alpha_high'], 'C/Q7: chỉ đổi α=0,01/0,10/0,50'),
        ('exploration_curves', ['epsilon_low_fixed', 'baseline', 'epsilon_high_fixed'], 'D/Q4: đổi lịch ε, giữ α=0,10')]:
        observations = '; '.join(f"{LABELS[config]}: RL cửa sổ đầu {tables[config]['rl_first_window_mean']:.4f}, "
            f"cuối {tables[config]['rl_last_window_mean']:.4f} ± {tables[config]['rl_last_window_std']:.4f}"
            for config in configs)
        notes.append({'figure_id': figure_id, 'path': FIG+'/'+figure_id+'.png', 'purpose': purpose,
            'data_source': METRIC+'/curves_mean_std.csv; raw source index '+METRIC+'/source_index.json',
            'explanation': 'Mỗi panel là một cấu hình. Trục x: episode 100–5.000; trục y: lợi nhuận giả lập/bước. '
            'Đường đen liền là RL, xám đứt là rule; mỗi seed được làm mượt bằng 100 episode trước, '
            'rồi lấy mean qua 5 seed (11/22/33/44/55). Vùng mờ là ±1 sample std giữa 5 đường đã làm mượt '
            '(ddof=1), không phải CI, không phải biến động từng timestep. '+observations+'. '
            'So sánh giữ cùng ngân sách 5.000×20, gamma, reward, kernel và bộ seed; chỉ đổi yếu tố đã nêu. '
            'Các cửa sổ kế tiếp chồng lấp nên không độc lập. Reward còn chịu exploration, đối thủ và nhiễu thị trường; '
            'không suy ra hội tụ/tối ưu hoặc thứ hạng final policy từ đường train. '
            'Rule không học vẫn đổi reward vì learner và tình huống đổi; phase5 mới đánh giá Q đóng băng.'})
    notes.append({'figure_id': 'epsilon_schedules', 'path': FIG+'/epsilon_schedules.png', 'purpose': 'Giải thích D/Q4',
        'data_source': 'docs/protocol_v1.json; '+METRIC+'/epsilon_schedules.csv',
        'explanation': 'Trục x là episode 1–5.000, trục y là xác suất khám phá ε (không đơn vị). '
        f'Baseline đen liền từ 0,20 xuống sàn 0,02 lần đầu ở episode {floor_episode}; '
        'xám đứt giữ 0,05, xám chấm giữ 0,30. Đây là lịch định trước, trùng ở cả 5 seed; '
        'không có vùng sai số, không phải đường reward đo được. Ngẫu nhiên do exploration khác '
        'ngẫu nhiên phá đồng hạng Q; ε=0 vẫn có thể phá đồng hạng ngẫu nhiên. '
        'Khám phá nhiều giúp thử action nhưng có thể giảm profit khi train; không mặc định lịch nào tốt nhất.'})
    means_words = '; '.join(f"{LABELS[config]}: RL {tables[config]['rl_train_mean']:.5f} ± "
                           f"{tables[config]['rl_train_std']:.5f}, rule {tables[config]['rule_train_mean']:.5f} ± "
                           f"{tables[config]['rule_train_std']:.5f}" for config in CONFIG_IDS)
    notes.append({'figure_id': 'train_summary', 'path': FIG+'/train_summary.png', 'purpose': 'Tổng hợp C/D train',
        'data_source': METRIC+'/config_train_summary.csv',
        'explanation': 'Hai panel tách RL và rule. Trục ngang là 5 cấu hình; trục dọc là lợi nhuận giả lập/bước '
        'trung bình trên toàn 100.000 bước/run. Chiều cao cột là mean của 5 mean/run; whisker là sample std '
        '(ddof=1) của 5 mean/run, không phải std episode và không phải CI. '+means_words+'. '
        'Baseline được tái dùng trong hai sweep; tổng là 25 run, không phải 30. '
        'Đây là lợi nhuận trong lúc học, có exploration và opponent phản ứng, chưa so sánh final policy '
        'trước cùng opponent/tape. Không chọn lại cấu hình/seed từ biểu đồ này, không coi overlap whisker là kiểm định.'})
    save_json(BASE, FIG+'/figure_notes.json', notes)
    paragraphs = ['# Giải thích bốn biểu đồ phase 4\n\nDữ liệu synthetic từ simulator, chỉ kết quả train.']
    for note in notes:
        paragraphs.append(f"## {note['figure_id']}\n\n![{note['figure_id']}]({note['figure_id']}.png)\n\n"
                          f"Mục đích: {note['purpose']}. Nguồn: `{note['data_source']}`.\n\n{note['explanation']}\n")
    (folder/'figure_notes.md').write_text('\n\n'.join(paragraphs), encoding='utf-8')
    manuscript = BASE/'report/sections/phase04_sweeps.md'
    content = ['# C–D: learning rate và exploration\n',
        ('Ma trận 5 cấu hình × 5 training seed, mỗi run 5.000 episode × 20 bước. '
        'CONTROLLED baseline seed11 tái dùng từ phase3. REF42 không thuộc nhóm n=5. '
        'Lý thuyết đủ dùng: α quyết định mức sửa Q sau reward mới; ε quyết định xác suất thử action ngẫu nhiên. '
        'Alpha sweep giữ lịch ε baseline; exploration sweep giữ α=0,10.\n'),
        '| Cấu hình | RL mean ± std/bước train | Rule mean ± std/bước train |\n|---|---:|---:|']
    for row in summary['config_summary']:
        content.append(f"| {LABELS[row['config_id']]} | {row['rl_train_mean']:.5f} ± {row['rl_train_std']:.5f} | "
                       f"{row['rule_train_mean']:.5f} ± {row['rule_train_std']:.5f} |")
    content.append('\nMẫu số: 100.000 market step/run, n=5 training seed, sample std ddof=1. '
        'Không gọi 125.000 episode là 125.000 learner độc lập. Ghép seed trong train giúp giữ comparable '
        'khởi tạo RNG/nhu cầu; sales/policy draw vẫn có thể khác khi hành động khác, '
        'không thay cho matched exogenous tapes ở final evaluation.\n')
    for note in notes:
        content.append(f"\n## Hình {note['figure_id']}\n\n{note['explanation']}\n\nHình: `{note['path']}`.\n")
    content.append('\n## Chênh lệch train ghép seed so với baseline\n\n'
        '| Cấu hình | Mean delta RL/bước ± std giữa 5 cặp seed |\n|---|---:|')
    for config, row in summary['paired'].items():
        content.append(f"| {LABELS[config]} | {row['mean']:.5f} ± {row['std']:.5f} |")
    content.append('\nDelta là mean reward lúc học của cấu hình trừ baseline cùng seed, '
        'không phải chênh lệch final policy. Đã báo đủ mọi cấu hình đăng ký, không tuning lại. '
        'Nhu cầu/doanh số là mô phỏng, số seed nhỏ; không khẳng định cấu hình tốt nhất ở thị trường thật. '
        'Phase5 mới chạy đánh giá riêng đóng băng Q, 500 episode/vai và mean/std qua 5 seed.\n')
    manuscript.write_text('\n'.join(content), encoding='utf-8')
    paths = list(folder.iterdir()) + list((BASE/METRIC).iterdir()) + [manuscript]
    result = {'status': 'GENERATED_PENDING_VISUAL_QA', 'charts': 4, 'matrix_cells': 25,
        'curve_csv_rows': len(summary['curve_rows']), 'source_index': sources,
        'generator_sha256': sha256_file(Path(__file__)),
        'files': [{'path': path.relative_to(BASE).as_posix(), 'sha256': sha256_file(path)} for path in sorted(paths)]}
    save_json(BASE, FIG+'/manifest.json', result)
    return result


if __name__ == '__main__':
    print(json.dumps(build(), ensure_ascii=False, indent=2))
