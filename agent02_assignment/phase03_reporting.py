"""Build grayscale Phase3 figures and Vietnamese explanations from saved logs only."""

import csv
import json
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap

from .code.baseline_analysis import analyze_rows, moving_average, validate_rows
from .code.baseline_runs import verify_run
from .phase02 import save_csv, save_json
from .phase03 import phase3_specs
from .workspace import sha256_file

BASE = Path(__file__).resolve().parent
OUTPUT = 'artifacts/figures/phase03'


def read_rows(path):
    with path.open(newline='', encoding='utf-8') as stream:
        rows = list(csv.DictReader(stream))
    return [{key: json.loads(value) if key == 'action_counts' else int(value) if key == 'episode'
             else float(value) for key, value in row.items()} for row in rows]


def build(base=BASE):
    folder = base / OUTPUT
    if (folder / 'manifest.json').exists():
        old = json.loads((folder / 'manifest.json').read_text())
        for item in old['files']:
            if sha256_file(base / item['path']) != item['sha256']:
                raise ValueError('Report output changed; retain and create presentation revision')
        return old
    folder.mkdir(parents=True, exist_ok=True)
    if list(folder.iterdir()):
        raise FileExistsError('Partial report output: preserve it and use a versioned presentation attempt')
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10, 'text.color': 'black',
                         'axes.labelcolor': 'black', 'axes.titleweight': 'bold', 'savefig.facecolor': 'white'})
    specs = phase3_specs()
    data, analyses, summaries, figure_notes, source_records = [], [], [], [], []
    for spec in specs:
        result = verify_run(base, spec['run_id'])
        run_dir = base / 'artifacts/runs' / spec['run_id']
        csv_path = run_dir / 'episode_rewards.csv'
        rows = read_rows(csv_path)
        validate_rows(rows, episodes=5000, steps=20)
        analysis = analyze_rows(rows)
        analysis.update({'run_id': spec['run_id'], 'track': spec['track']})
        analyses.append(analysis)
        source_records.append({'path': csv_path.relative_to(base).as_posix(), 'sha256': sha256_file(csv_path)})
        summaries.append({'track': spec['track'], 'seed': spec['seed'], **result['summary'],
                          'train_cpu_seconds': result['train_cpu_seconds'],
                          'train_wall_seconds': result['train_wall_seconds']})
        q = np.array(json.loads((run_dir / 'q_table.json').read_text())).reshape(4, 2)
        policy = json.loads((run_dir / 'policy.json').read_text())
        data.append({'spec': spec, 'rows': rows, 'q': q, 'policy': policy, 'summary': result['summary']})
        figure, axes = plt.subplots(2, 1, figsize=(10.4, 6.4), sharex=True, layout='constrained')
        x = np.arange(1, len(rows)+1)
        for name, label, color, style in [('rl', 'Q-learning', 'black', '-'),
                                           ('rule', 'Agent luật', '.55', '--')]:
            values = [row[name+'_mean_reward_per_step'] for row in rows]
            axes[0].plot(x, values, color=color, alpha=.55, linewidth=.45, linestyle=style, label=label)
            axes[1].plot(x[99:], moving_average(values, 100), color=color, linewidth=1.2,
                         linestyle=style, label=label)
        axes[0].set_title(f'{spec["track"]}, seed {spec["seed"]}: reward train từng episode (chưa làm mượt)')
        axes[1].set_title('Trung bình trượt 100 episode; không có vùng sai số giữa seed')
        for axis in axes:
            axis.set_ylabel('Lợi nhuận giả lập / bước')
            axis.grid(alpha=.18)
            axis.legend(loc='lower right', ncol=2)
        axes[1].set_xlabel('Episode huấn luyện')
        relative = OUTPUT + '/' + spec['track'].lower() + '_learning_curve.png'
        figure.savefig(base / relative, dpi=200)
        plt.close(figure)
        stats = analysis
        paragraph = (f"{spec['track']} seed {spec['seed']}: mỗi điểm ở phần trên là reward cả episode chia 20 bước; "
            'trục ngang là episode 1–5.000, trục dọc là lợi nhuận giả lập/bước. Đen liền là RL, xám đứt là rule. '
            'Phần dưới gộp cửa sổ 100 episode liên tiếp (2.000 bước), điểm đầu ở episode100; không đệm 0, '
            'không dùng dữ liệu tương lai. Mỗi track chỉ một seed, không có error band. '
            f"RL: 100 episode đầu {stats['rl']['first_window_mean']:.4f}, cuối {stats['rl']['last_window_mean']:.4f}; "
            f"rule: {stats['rule']['first_window_mean']:.4f} → {stats['rule']['last_window_mean']:.4f}. "
            f"Độ lệch chuẩn reward trung bình/bước giữa 5.000 episode: RL {stats['rl']['raw_episode_mean_std_ddof1']:.4f}, "
            f"rule {stats['rule']['raw_episode_mean_std_ddof1']:.4f} (ddof1, không phải std giữa training seed). "
            f"Đường trượt RL vẫn dao động trong [{stats['rl']['window_min']:.4f}, {stats['rl']['window_max']:.4f}]. "
            'Nhu cầu và doanh số ngẫu nhiên tạo nhiễu; epsilon giảm cũng làm đổi hành vi train. '
            'Rule cố định vẫn có reward đổi vì đối thủ RL và tình huống thị trường đổi. '
            'Làm mượt giúp đọc xu hướng, không chứng minh hội tụ/tối ưu hay hơn ngoài mẫu.')
        figure_notes.append({'figure_id': spec['track'].lower()+'_learning_curve', 'path': relative,
                             'source': source_records[-1], 'question': 'A/B; Q4/Q6/Q7 train context',
                             'explanation': paragraph})
    figure, axes = plt.subplots(1, 2, figsize=(10.2, 4.5), layout='constrained', sharey=True)
    vmin, vmax = min(item['q'].min() for item in data), max(item['q'].max() for item in data)
    for axis, item in zip(axes, data, strict=True):
        light_greys = ListedColormap(plt.get_cmap('Greys')(np.linspace(0, .5, 256)))
        image = axis.imshow(item['q'], cmap=light_greys, vmin=vmin, vmax=vmax, aspect='auto')
        axis.set_xticks([0, 1], ['0: Giữ giá', '1: Giảm giá'])
        axis.set_yticks(range(4), ['Thấp / 0', 'Thấp / 1', 'Cao / 0', 'Cao / 1'])
        axis.set_title(f"{item['spec']['track']} — seed {item['spec']['seed']}")
        for row in range(4):
            for col in range(2):
                value = item['q'][row, col]
                axis.text(col, row, f'{value:.2f}', ha='center', va='center', color='black')
        axis.set_xlabel('Hành động của learner')
    axes[0].set_ylabel('Nhu cầu / hành động trước của đối thủ')
    figure.colorbar(image, ax=axes, shrink=.8, label='Q ước lượng (lợi nhuận chiết khấu)')
    figure.savefig(folder / 'q_tables.png', dpi=200)
    plt.close(figure)
    policy_words = '; '.join(f"{item['spec']['track']}: " + ', '.join(
        f"{tuple(row['state'])}→{row['greedy_action_set']}" for row in item['policy']) for item in data)
    figure_notes.append({'figure_id': 'q_tables', 'path': OUTPUT+'/q_tables.png',
        'source': 'q_table.json and policy.json in both saved run directories', 'question': 'A/Q3/Q10 baseline',
        'explanation': 'Hai ô hình là Q cuối train của hai run, mỗi run một seed, không lấy trung bình. '
        'Trục dọc có 4 state (nhu cầu/hành động trước của đối thủ), trục ngang 2 action. '
        'Thang xám chung: tối hơn là Q lớn hơn; số trong ô là Q, không phải profit/bước DEV. '
        + policy_words + '. Hai track khác RNG và seed nên không dùng chênh Q để xếp hạng phương pháp. '
        'Q là ước lượng chịu chiết khấu, nhiễu và cập nhật terminal; bảng cuối không chứng minh policy tối ưu. '
        'Tập greedy giữ toàn bộ action đồng hạng theo isclose; Q và policy đầy đủ được lưu riêng.'})
    figure, axes = plt.subplots(1, 2, figsize=(10.2, 4.5), layout='constrained', sharey=True)
    count_words = []
    for axis, item in zip(axes, data, strict=True):
        counts = item['summary']['rl_action_counts'] + item['summary']['rule_action_counts']
        bars = axis.bar(range(4), counts, color=['.2', '.7', '.2', '.7'], edgecolor='black')
        axis.bar_label(bars, padding=3, fontsize=9)
        axis.set_xticks(range(4), ['RL:0', 'RL:1', 'Rule:0', 'Rule:1'])
        axis.set_title(item['spec']['track']+' — đếm hành động train')
        axis.set_xlabel('Agent : action (0 giữ giá, 1 giảm giá)')
        axis.set_ylim(0, 108000)
        count_words.append(f"{item['spec']['track']}: RL giảm {counts[1]:,}/100.000 "
                           f"({counts[1]/1000:.3f}%), rule giảm {counts[3]:,}/100.000 ({counts[3]/1000:.3f}%)")
    axes[0].set_ylabel('Số lần chọn hành động')
    figure.savefig(folder / 'action_counts.png', dpi=200)
    plt.close(figure)
    figure_notes.append({'figure_id': 'action_counts', 'path': OUTPUT+'/action_counts.png',
        'source': 'episode_rewards.csv action_counts, both runs', 'question': 'A/Q4/Q5',
        'explanation': 'Trục ngang là 4 cặp agent/action; trục dọc là tổng lượt chọn trên 5.000×20 bước. '
        'Cột tối giữ giá, cột sáng giảm giá, số trên cột là count; mỗi cặp 0+1 của một agent bằng100.000. '
        + '; '.join(count_words) + '. Không gộp hai track thành n2, không có error bar. '
        'Đây là hành động lúc train còn exploration, không phải tần suất policy greedy DEV. '
        'Giảm giá nhiều hơn không tự chứng minh tốt hơn: lãi mỗi món từ5 còn3. '
        'Không thể quy khác biệt cho framework khi seed/RNG đã khác.'})
    save_csv(base, 'artifacts/metrics/phase03_train_summary.csv', summaries)
    save_json(base, 'artifacts/metrics/phase03_curve_analysis.json', analyses)
    q_rows = [{'track': item['spec']['track'], 'state': row['state'], **row} for item in data for row in item['policy']]
    save_csv(base, 'artifacts/metrics/phase03_q_policy.csv', q_rows)
    dev_rows = []
    for item in data:
        for role in (0, 1):
            saved = json.loads((base / f'artifacts/metrics/phase03_dev/{item["spec"]["track"].lower()}_role{role}.json').read_text())
            dev_rows.append({'track': item['spec']['track'], 'role': role, 'episodes': saved['episodes'],
                'mean_profit_per_step': saved['mean_reward'],
                'rule_mean_profit_per_step': saved['rule_total_reward']/saved['steps'],
                'rl_action_counts': saved['learner_action_counts'], 'q_unchanged': saved['q_hash_before']==saved['q_hash_after']})
    save_csv(base, 'artifacts/metrics/phase03_dev_summary.csv', dev_rows)
    save_json(base, OUTPUT+'/figure_notes.json', figure_notes)
    paragraphs = ['# Diễn giải hình phase 3\n\nDữ liệu mô phỏng synthetic; chưa phải final evaluation.']
    for note in figure_notes:
        paragraphs += [f"## {note['figure_id']}\n\n![{note['figure_id']}]({Path(note['path']).name})\n",
                       f"Nguồn: `{note['source']}`.\n\n{note['explanation']}\n"]
    (folder / 'figure_notes.md').write_text('\n\n'.join(paragraphs), encoding='utf-8')
    sections = ['# Baseline A–B — bản thảo từ số đo phase 3\n',
        ('Mỗi track có một training seed, 5.000 episode × 20 bước. REF dùng các class gốc của thầy '
         'với loop instrument đã kiểm parity; CONTROLLED dùng core phase2 tách RNG. Không gộp hai run thành n=2.\n'),
        '| Track | RL profit/bước train | Rule profit/bước train | Chênh lệch trong đối đầu |\n|---|---:|---:|---:|']
    for summary in summaries:
        sections.append(f"| {summary['track']} | {summary['rl_mean_reward_per_step']:.5f} | "
                        f"{summary['rule_mean_reward_per_step']:.5f} | "
                        f"{summary['rl_mean_reward_per_step']-summary['rule_mean_reward_per_step']:.5f} |")
    sections += [('\nMean là tổng reward chia 100.000 market step cho từng shop. Chênh lệch train '
                  'mô tả cùng cuộc đối đầu, chưa là so sánh frozen policy trước cùng opponent.\n')]
    for note in figure_notes:
        sections.append(f"\n## Hình {note['figure_id']}\n\n{note['explanation']}\n\n"
                        f"Nguồn hình: `{note['path']}`; số liệu ở `artifacts/metrics/phase03_*`.\n")
    sections += ['\n## DEV riêng, chưa là kết quả cuối\n',
                 '| Track | Vai learner | RL profit/bước | Rule profit/bước |\n|---|---:|---:|---:|']
    for row in dev_rows:
        sections.append(f"| {row['track']} | {row['role']} | {row['mean_profit_per_step']:.5f} | "
                        f"{row['rule_mean_profit_per_step']:.5f} |")
    sections.append('\nDEV dùng100 episode mỗi vai, scenario seed1000011/tape chung cho cả hai Q, '
        'Q đóng băng và exploration tắt; không dùng để chỉnh cấu hình. Mỗi vai2.000 bước, '
        'không gọi200 episode là200 training seed. Hai Q có thể khác ở state không gặp '
        'trong trajectory greedy: khi cả hai bắt đầu giữ giá và learner tiếp tục giữ giá '
        'ở observation đối thủ0, rule luôn giữ giá và observation đối thủ1 không xuất hiện. '
        'Nếu DEV trùng, đó là cùng hành vi đạt tới trên kịch bản này, không phải Q bằng nhau '
        'hoặc chứng minh mọi môi trường tương đương. Final500 episode/vai và đa seed thuộc phase5.\n')
    manuscript = base / 'report/sections/phase03_baseline.md'
    manuscript.parent.mkdir(parents=True, exist_ok=True)
    manuscript.write_text('\n'.join(sections), encoding='utf-8')
    paths = list(folder.iterdir()) + [base/'artifacts/metrics'/name for name in
             ('phase03_train_summary.csv', 'phase03_curve_analysis.json', 'phase03_q_policy.csv', 'phase03_dev_summary.csv')]
    paths.append(manuscript)
    manifest = {'status': 'GENERATED_PENDING_VISUAL_QA', 'charts': len(figure_notes), 'source_csvs': source_records,
                'generator_sha256': sha256_file(Path(__file__)),
                'files': [{'path': path.relative_to(base).as_posix(), 'sha256': sha256_file(path)} for path in paths]}
    save_json(base, OUTPUT+'/manifest.json', manifest)
    return manifest


if __name__ == '__main__':
    print(json.dumps(build(), ensure_ascii=False, indent=2))
