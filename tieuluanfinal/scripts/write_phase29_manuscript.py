"""Build a new combined Ch4 manuscript, preserving frozen Phase28 text/artifacts."""

import argparse
import re

from scripts.summarize_phase29 import LABELS, UNITS, aggregate_rows, collect, diagnostics_rows, paired_deltas
from src.ch04_rnn_lstm.phase29.protocol import BASE, DATASETS, IMPLEMENTATIONS, checked, ref
from src.common.artifact_core import write_once
from src.common.contracts import ROOT, read_json


def fmt(row, decimals=3, show_n=False):
    if row["mean"] is None:
        return "không xác định"
    result = f"{row['mean']:.{decimals}f}".replace(".", ",")
    if row["sample_std"] is not None:
        result += " ± " + f"{row['sample_std']:.{decimals}f}".replace(".", ",")
    if show_n or row["n"] == 1:
        result += f" (n={row['n']})"
    return result


def table(headers, rows):
    return (
        "\n".join(
            [
                "| " + " | ".join(headers) + " |",
                "|" + "---|" * len(headers),
                *["| " + " | ".join(map(str, row)) + " |" for row in rows],
            ]
        )
        + "\n"
    )


def image(name, caption):
    return f"\n![{caption}](../../../artifacts/figures/phase29/{name}.png)\n"


LSTM_CODE = """
### 4.4.6. Code cốt lõi ở ba cách viết

Đoạn scratch dưới đây minh họa forward của một tầng. Hai lần đầu trả cả chuỗi,
lần thứ ba lấy trạng thái cuối, rồi nối Dense16/ReLU → Dense8/ReLU → Dense3.
Backward/BPTT của cả h và c, cache các bước và Adam nằm trong source đã kiểm gradient;
không thay chúng bằng autograd trong bản scratch.

```python
def lstm_layer(x, W, U, b, return_sequences=True):
    h = np.zeros((len(x), U.shape[0]), dtype=x.dtype)
    c = np.zeros_like(h)
    sequence = []
    for t in range(x.shape[1]):
        zi, zf, zg, zo = np.split(x[:, t] @ W + h @ U + b, 4, axis=1)
        i, f, o = sigmoid(zi), sigmoid(zf), sigmoid(zo)
        g = np.tanh(zg)
        c = f * c + i * g
        h = o * np.tanh(c)
        sequence.append(h)
    return np.stack(sequence, axis=1) if return_sequences else h
```

Keras biểu diễn sáu lớp có tham số trên ví dụ vàng như sau. Code train thật gán
canonical weights, forget bias và dùng NativeAdam đã chuẩn hóa, không gọi stock
Keras Adam để thay quy ước update.

```python
model = keras.Sequential([
    keras.Input(shape=(24, 4)),
    keras.layers.LSTM(32, return_sequences=True),
    keras.layers.LSTM(32, return_sequences=True),
    keras.layers.LSTM(32),
    keras.layers.Dense(16, activation="relu"),
    keras.layers.Dense(8, activation="relu"),
    keras.layers.Dense(3),
])
```

PyTorch cũng dùng ba LSTM riêng và ba Linear; tuple trạng thái (h,c) không được
truyền sang window khác. Bias recurrent thứ hai giữ0/frozen để khớp số tham số.

```python
class LSTM6(nn.Module):
    def __init__(self, features=4):
        super().__init__()
        self.layers = nn.ModuleList([
            nn.LSTM(d, 32, batch_first=True) for d in (features, 32, 32)
        ])
        self.head = nn.Sequential(nn.Linear(32, 16), nn.ReLU(),
                                  nn.Linear(16, 8), nn.ReLU(), nn.Linear(8, 3))
        for layer in self.layers:
            with torch.no_grad():
                layer.bias_hh_l0.zero_()
            layer.bias_hh_l0.requires_grad_(False)
    def forward(self, x):
        for layer in self.layers:
            x, _ = layer(x)
        return self.head(x[:, -1])
```

Các đoạn trên tập trung vào phép tính/shape, không phải runner thay thế hoặc một
lượt train mới. Runner dùng LstmKerasTrainer/LstmTorchTrainer và gán đúng canonical
initial weights trước update. Mỗi native engine chạy process/venv riêng.

"""


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    output = BASE / "manuscript_generation.json"
    if output.exists():
        result = read_json(output)
        checked(result["manuscript"])
        print({"status": "PASS", "mode": "reused_verified"})
        return
    statistics = read_json(BASE / "report_statistics.json")
    audit = read_json(BASE / "test_verification.json")
    if statistics["status"] != "PASS" or audit["status"] != "PASS":
        raise ValueError("Final saved-output audit/statistics required")
    records, horizons, _, selections = collect()
    aggregate = aggregate_rows(records)
    horizon_summary = aggregate_rows(horizons, fields=("rmse", "mae", "smape"), extra_keys=("horizon",))
    deltas, diagnostic = paired_deltas(records), diagnostics_rows(selections)

    def value(dataset, family, method, metric, split="test", **extra):
        return next(
            r
            for r in aggregate
            if r["dataset_id"] == dataset
            and r["family"] == family
            and r["method"] == method
            and r["metric"] == metric
            and r["split"] == split
            and r["fold"] is None
            and all(r[k] == v for k, v in extra.items())
        )

    rnn_source = ROOT / "report/sections/v3/ch04_rnn.md"
    lstm_source = ROOT / "report/sections/v3/ch04_lstm_theory.md"
    rnn = "## 4.1." + rnn_source.read_text(encoding="utf-8").split("## 4.1.", 1)[1].split("## 4.4.", 1)[0]
    rnn = rnn.replace("TEST giữ niêm phong", "TEST giữ kín đến chốt mô hình")
    rnn = rnn.replace("LSTM ở Phase 29\nsẽ được so sánh", "LSTM trong phần tiếp theo\nđược so sánh")
    lstm = (
        "## Vì sao"
        + lstm_source.read_text(encoding="utf-8").split("## Vì sao", 1)[1].split("## Đánh giá", 1)[0]
    )
    counter = iter(range(1, 10))
    lstm = re.sub(r"^## (.+)$", lambda m: f"### 4.4.{next(counter)}. {m.group(1)}", lstm, flags=re.MULTILINE)
    parts = [
        (
            "# CHƯƠNG 4. RNN–LSTM VÀ DỰ ĐOÁN CHUỖI THỜI GIAN\n\n"
            "Chương này xét cùng ba bài toán vàng, chỉ số nhà và điện năng bằng RNN, LSTM và hai baseline nhân quả. "
            "Mỗi họ mạng có ba bản scratch, Keras/TensorFlow và PyTorch, cùng sáu lớp học được. "
            "Phần thực nghiệm phân biệt rõ validation dùng chọn checkpoint với TEST chung chỉ đánh giá một lần.\n\n"
        ),
        rnn,
        "\n## 4.4. LSTM: đường bộ nhớ và các cổng\n\n",
        lstm,
        LSTM_CODE,
        (
            "\n## 4.5. Giao thức so sánh và ý nghĩa số đo\n\n"
            "RNN và LSTM dùng cùng split, windows, scaler, seed17/42/73 và ngân sách đã nêu. "
            "Mỗi họ có27 lượt main và81 lượt rolling, tổng216 lượt mạng;24 baseline validation ở Phase28 được dùng lại, "
            "không train lại. Hai họ dùng cùng hidden width nhưng LSTM có nhiều tham số hơn, vì vậy đây không phải "
            "so sánh cùng parameter budget.\n\n"
            "Sau khi đủ108 lựa chọn LSTM,108 native-CPU receipts và audit183.159 dòng validation PASS, "
            "330 test/0skip cùng coverage88,02% được khóa trước TEST. Cả hai họ,60 approved main run IDs và evaluator "
            "được niêm phong; rolling checkpoint không vào TEST. Mỗi dataset đánh giá9 RNN+9 LSTM+2 baseline, "
            "mỗi window đúng một lần cho mỗi model, không update optimizer hoặc chạy timing lặp trên TEST. "
            "Gold/BIS có seal evaluated/count1. Power giữ nguyên seal failed_sealed/count1 vì lỗi schema phục hồi chỉ cho validation; "
            "revision được người dùng duyệt hoàn tất bản ghi orphan từ4.911 output đã có rồi chạy đúng17 run chưa claim. "
            "Không lặp43 claim hoặc dựng lại cache; continuation journal riêng công khai sự cố thay vì reset seal. "
            "Revision có21 test và coverage93,50% phần schema/journal PASS trước khi chạy tiếp. "
            "Audit hợp nhất111.900 dòng prediction, mỗi dòng có ba horizon, chỉ đọc output đã lưu. "
            "Timestamp tạo metric orphan là thời điểm phục hồi record, không giả làm thời điểm inference đã mất.\n\n"
            "RMSE là căn của trung bình bình phương sai số, nên phạt sai số lớn; MAE là sai số tuyệt đối trung bình. "
            "Hai số cùng đơn vị với target và càng thấp càng tốt. sMAPE thể hiện sai số tương đối đối xứng theo phần trăm; "
            "giá trị gần0 có thể làm tỷ lệ nhạy hơn. BIS dùng macro-series RMSE làm metric chính: tính RMSE từng "
            "nền kinh tế rồi lấy trung bình ngang49 chuỗi. Không cộng USD, điểm chỉ số và kW thành một điểm chung.\n\n"
            "Bảng mạng ghi mean ± sample SD qua ba seed, không phải khoảng tin cậy hoặc bằng chứng hơn hẳn. "
            "Baseline là quy tắc cố định với n=1, không dựng SD=0 để giả độ ổn định. Delta ghép theo dataset/method/seed, "
            "không chọn seed tốt nhất theo TEST. Các rolling fold chồng lịch nên không coi là mẫu độc lập.\n\n"
        ),
    ]
    parameter_rows = []
    for dataset in DATASETS:
        a = value(dataset, "rnn", "scratch", "parameter_count")["mean"]
        b = value(dataset, "lstm", "scratch", "parameter_count")["mean"]
        parameter_rows.append((LABELS[dataset], int(a), int(b), f"{b / a:.2f}"))
    parts += [
        table(("Dataset", "RNN /6 lớp", "LSTM /6 lớp", "Tỷ số tham số LSTM/RNN"), parameter_rows),
        (
            "\n## 4.6. Kết quả: LSTM không mặc định tốt hơn RNN\n\n"
            "### 4.6.1. Chất lượng trên TEST chung\n\n"
            "Metric chính là macro-series RMSE cho BIS và RMSE cho hai dataset còn lại. MAE có cùng đơn vị target; "
            "sMAPE tính theo%. Bảng dùng full TEST116/568/4.911 windows, không cắt TEST theo matched train.\n\n"
        ),
    ]
    quality_rows = []
    for dataset in DATASETS:
        metric = "macro_series_rmse" if dataset == DATASETS[1] else "rmse"
        for family in ("rnn", "lstm", "classical"):
            for method in IMPLEMENTATIONS if family != "classical" else ("last_value", "seasonal_naive"):
                quality_rows.append(
                    (
                        LABELS[dataset],
                        family.upper(),
                        method,
                        fmt(value(dataset, family, method, metric)),
                        fmt(value(dataset, family, method, "mae")),
                        fmt(value(dataset, family, method, "smape")),
                    )
                )
    parts += [
        table(("Dataset", "Họ", "Cách viết/quy tắc", "Metric chính", "MAE", "sMAPE%"), quality_rows),
        image(
            "main_test_comparison",
            "Hình 4.1. TEST chung, sai số chính theo từng dataset; trục log, đơn vị riêng. Error bar là sample SD ba seed, đường baseline n=1.",
        ),
        (
            "\nDấu dương ở cột cải thiện nghĩa là LSTM có sai số trung bình thấp hơn RNN; dấu âm nghĩa là kém hơn. "
            "Tỷ lệ được tính bằng100×(mean RNN−mean LSTM)/mean RNN trên cùng nhóm, không phải lợi nhuận.\n\n"
        ),
    ]
    main_deltas = [r for r in deltas if r["split"] == "test" and r["fold"] is None]
    parts.append(
        table(
            ("Dataset", "Cách viết", "RNN−LSTM (đơn vị target)", "Cải thiện tương đối%"),
            [
                (
                    LABELS[r["dataset_id"]],
                    r["method"],
                    fmt({"mean": r["rnn_minus_lstm_mean"], "sample_std": r["sample_std"], "n": r["n"]}),
                    f"{r['relative_improvement_percent']:.2f}",
                )
                for r in main_deltas
            ],
        )
    )
    for dataset in DATASETS:
        group = [r for r in main_deltas if r["dataset_id"] == dataset]
        better = sum(r["rnn_minus_lstm_mean"] > 0 for r in group)
        primary = "macro_series_rmse" if dataset == DATASETS[1] else "rmse"
        naive = value(dataset, "classical", "last_value", primary)
        rnn_over_naive = sum(value(dataset, "rnn", m, primary)["mean"] < naive["mean"] for m in IMPLEMENTATIONS)
        lstm_over_naive = sum(value(dataset, "lstm", m, primary)["mean"] < naive["mean"] for m in IMPLEMENTATIONS)
        parts.append(
            f"\n**{LABELS[dataset]}:** LSTM giảm metric chính ở{better}/3 implementation trên TEST. "
            "Kết quả này mô tả đúng kiến trúc và ngân sách đã khóa, không chứng minh ưu thế của mọi LSTM/RNN.\n"
        )
        parts.append(f"\nLast-value có metric chính {fmt(naive)} {UNITS[dataset]}; "
                     f"RNN thấp hơn baseline này ở{rnn_over_naive}/3 cách viết, LSTM ở{lstm_over_naive}/3. "
                     "Đây là so sánh với quy tắc đã khai báo, không chọn lại mô hình triển khai bằng TEST.\n")
    parts += [
        (
            "\n### 4.6.2. Horizon dài và biến động giai đoạn\n\n"
            "Bảng sau xét horizon xa nhất bằng RMSE theo toàn window. Riêng BIS, bảng này là pooled RMSE, "
            "khác metric chính macro-series RMSE ở bảng trước; không đổi tên hai cách tính cho nhau.\n\n"
        )
    ]
    far_rows = []
    for dataset in DATASETS:
        h = max(r["horizon"] for r in horizons if r["dataset_id"] == dataset)
        for method in IMPLEMENTATIONS:
            pair = [
                next(
                    r
                    for r in horizon_summary
                    if r["dataset_id"] == dataset
                    and r["method"] == method
                    and r["family"] == family
                    and r["horizon"] == h
                    and r["metric"] == "rmse"
                    and r["split"] == "test"
                    and r["fold"] is None
                )
                for family in ("rnn", "lstm")
            ]
            far_rows.append((LABELS[dataset], h, method, fmt(pair[0]), fmt(pair[1])))
    parts += [
        table(("Dataset", "Horizon xa", "Cách viết", "RNN RMSE", "LSTM RMSE"), far_rows),
        image(
            "horizon_test",
            "Hình 4.2. TEST theo cả ba horizon, mean ± sample SD; tháng/quý/giờ theo dataset, không đồng nhất về thời lượng.",
        ),
        image(
            "rolling_validation",
            "Hình 4.3. Ba expanding rolling VALIDATION; scaler riêng từng prefix. Đây là development, không phải ba lượt TEST hoặc ba mẫu độc lập.",
        ),
        (
            "\n### 4.6.3. Ví dụ dự đoán và khác biệt giữa nền kinh tế\n\n"
            "Ví dụ forecast dùng scratch seed42 đã định trước, horizon gần nhất và chuỗi đầu theo ID. "
            "Power hiển thị thưa nếu quá500 điểm để đọc hình; metric vẫn tính trên mọi window. "
            "Đường sát nhau không đồng nghĩa có giá trị giao dịch hay mô hình nhận ra đúng cơ chế kinh tế.\n"
        ),
        image(
            "saved_test_forecasts",
            "Hình 4.4. Nhãn thật và dự đoán TEST đã lưu, một chuỗi/dataset; không phát sinh inference TEST để vẽ.",
        ),
        image(
            "bis_country_errors",
            "Hình 4.5. BIS TEST: RMSE từng nền kinh tế, trung bình ba seed, màu log10 cùng thang cho sáu cách triển khai.",
        ),
        (
            "\n## 4.7. Quá trình học, cổng và gradient\n\n"
            "Đường loss dùng seed42 main của cả hai họ và cả ba framework, không lấy seed có đường đẹp nhất. "
            "Early stopping chọn minimum validation thật, không chọn theo TEST. Sai khác giữa các framework có thể "
            "tích lũy qua update và làm epoch dừng khác nhau, dù khởi tạo và quy ước Adam giống nhau.\n"
        ),
        image(
            "learning_curves",
            "Hình 4.6. Validation MSE chuẩn hóa theo epoch, seed42 main; không so giá trị loss giữa dataset như cùng đơn vị vật lý.",
        ),
        (
            "\nCổng sigmoid có giá trị0–1: gần1 cho phép giữ/ghi/xuất nhiều hơn tại thành phần đó. "
            "Hình lấy trung bình trên4 TRAIN windows và hidden dimensions của scratch seed42, không phải tỷ lệ dự đoán đúng. "
            "Cổng quên cao không tự chứng minh rằng mô hình đã học được quan hệ dài hạn hữu ích.\n"
        ),
        image(
            "lstm_gate_profiles",
            "Hình 4.7. Input/forget/output gates theo bước thời gian, ba tầng LSTM, chỉ dùng TRAIN.",
        ),
        image(
            "train_gradient_profiles",
            "Hình 4.8. Input-gradient RMS của4 TRAIN windows cố định; floor1e−30 chỉ để hiển thị log nếu bằng0, không dùng cho metric/parity.",
        ),
        (
            "\nĐộ lớn gradient mô tả độ nhạy cục bộ của loss tại checkpoint và mẫu đã chọn, không phải causal importance. "
            "Không kết luận LSTM khắc phục mọi vanishing/exploding gradient chỉ từ một đường cong. "
            "Các tỷ lệ oldest/newest và clipping của toàn216 lượt mạng nằm trong `train_diagnostics.csv`.\n\n"
        ),
        table(
            ("Dataset", "Họ /scratch seed42", "Gradient oldest/newest", "Tỷ lệ batch bị clip, TB epoch"),
            [
                (
                    LABELS[r["dataset_id"]],
                    r["family"].upper(),
                    "không xác định"
                    if r["oldest_to_newest_ratio"] is None
                    else f"{r['oldest_to_newest_ratio']:.4g}",
                    f"{r['epoch_mean_clip_fraction']:.4f}",
                )
                for r in diagnostic
                if r["fold"] is None and r["seed"] == 42 and r["method"] == "scratch"
            ],
        ),
        (
            "\n## 4.8. Chi phí, sai lệch đo và giới hạn\n\n"
            "Scratch chạy NumPy CPU; Keras và PyTorch train GPU trong hai venv độc lập. "
            "RNN Keras dùng XLA, LSTM Keras graph không XLA; PyTorch eager. Vì vậy thời gian phản ánh cả engine, "
            "dispatch/compile và implementation, không đo riêng độ phức tạp lý thuyết. "
            "Các unit test nhẹ đã chạy khi queue hoạt động nên không gọi đây là benchmark máy cô lập.\n\n"
            "Trong Phase29, distro/runtime cũ không còn nên được khôi phục đúng lock ở Ubuntu/user mới. "
            "Bốn process torch/TF ×GPU/CPU và shared-package parity đã PASS; năm selection cũ được giữ nguyên. "
            "Không mô tả RNN và LSTM là hai lượt đo liên tiếp trong một phiên runtime không gián đoạn.\n\n"
            "Train wall là thời gian đoạn fit, có thể bao gồm validation/compile trong timer; RSS là high-water "
            "process, VRAM là peak allocator, không phải bộ nhớ toàn máy/GPU. Timing p50/p95 lưu từ5warmup+30repeat "
            "trên một TRAIN input, không phải end-to-end HTTP hoặc đo lại TEST. "
            "TEST metric giữ bản sao chi phí train gốc; không cộng thành chi phí train thứ hai.\n\n"
            "RNN Power/PyTorch seed17 có original train/RAM/VRAM bị mất khi export lỗi. "
            "Giữ null, giữ FAIL GPU→CPU gốc và bản phục hồi không thêm update; quality dùng3 seed nhưng nhóm chi phí dùng2. "
            "Không thay bằng0 hoặc peak của process recovery.\n\n"
        ),
    ]
    cost_rows = []
    for dataset in DATASETS:
        for family in ("rnn", "lstm"):
            for method in IMPLEMENTATIONS:
                seconds = value(dataset, family, method, "train_seconds", "validation")
                ram = value(dataset, family, method, "peak_ram_bytes", "validation")
                vram = value(dataset, family, method, "peak_vram_bytes", "validation")

                def scale(r):
                    return {
                        **r,
                        "mean": r["mean"] / 1024**2 if r["mean"] is not None else None,
                        "sample_std": r["sample_std"] / 1024**2 if r["sample_std"] is not None else None,
                    }

                cost_rows.append(
                    (
                        LABELS[dataset],
                        family.upper(),
                        method,
                        fmt(seconds, show_n=True),
                        fmt(scale(ram), 1),
                        fmt(scale(vram), 1),
                    )
                )
    parts += [
        table(
            ("Dataset", "Họ", "Cách viết", "Train giây", "Peak RSS MiB", "Peak allocator VRAM MiB"), cost_rows
        ),
        image(
            "training_cost",
            "Hình 4.9. Train wall chính, mean ± sample SD trên số seed có telemetry; n=2 được ghi riêng, không phải latency TEST.",
        ),
        (
            "\nSnapshot vàng/BIS có thể đã được chỉnh sửa hồi tố; không có vintage và lịch công bố đầy đủ. "
            "Power chỉ một hộ và timezone/DST chưa xác minh. Các mô hình sâu có thể kém baseline khi dữ liệu ít, "
            "trend đổi hoặc target vượt vùng train. Không tuning lại sau TEST để che các kết quả âm; "
            "không suy rộng thành hệ dự báo giá hay điện thương mại.\n\n"
            "## 4.9. Triển khai ngắn: checkpoint CPU và notebook\n\n"
            "Mỗi dataset có notebook RNN–LSTM với hai nhóm ba checkpoint main seed42, cùng TRAIN input và scaler. "
            "Model train độc lập bằng scratch/Keras/PyTorch nhưng serving thực tế bằng NumPy CPU portable, "
            "không giả vờ gọi ba native framework lúc demo. Strict native-CPU round-trip giữ ngưỡng rtol1e−4/atol1e−5.\n\n"
            "```powershell\n.\\scripts\\run_experiment.ps1 -Distribution Ubuntu -Framework torch -Module scripts.demo_phase29 -ModuleArguments @('--dataset','ch4_gold_pink_sheet','--family','lstm')\n```\n\n"
            "Đổi family thành `rnn`, hoặc chọn `ch4_bis_house_prices`/`ch4_household_power`; mỗi lần trả ba kết quả. "
            "Notebook ở `experiments/notebooks/v3/ch04_rnn_lstm/`; request/job bám API schema đã khóa, input finite "
            "đúng shape/canonical order và checkpoint được kiểm hash trước nạp. Demo không cập nhật weights hoặc mở TEST. "
            "Đây là CLI/notebook học thuật, chưa phải HTTP/React/Render live. Tích hợp API/UI thuộc Phase32–33, "
            "DOCX/render cuối thuộc Phase34–35. Deployment chỉ là mục cuối chương, không thêm chương riêng.\n\n"
            "### Nguồn bằng chứng của chương\n\n"
            "Dữ liệu: data cards Phase24 tại `report/references/dataset_cards/v3_eda/ch4_*.md`. "
            "RNN: Phase28 experiment_lock; LSTM: Phase29 release/selection/receipts; "
            "TEST: Phase29 pretest_verification/test_seals/test_verification. "
            "Bảy CSV và chín hình PNG300dpi/SVG sinh bởi `scripts.summarize_phase29`, không lấy số từ initialized registry Phase25. "
            "Source code và function contracts cung cấp chi tiết BPTT/Adam và từng hàm để đối chiếu, "
            "không đưa khai triển vi phân dài vào chương chính.\n"
        ),
    ]
    path = ROOT / "report/sections/v3/ch04_rnn_lstm.md"
    with path.open("x", encoding="utf-8") as stream:
        stream.write("".join(parts))
    write_once(
        output,
        {
            "phase": 29,
            "status": "PASS",
            "manuscript": ref(path),
            "source_text": [ref(rnn_source), ref(lstm_source)],
            "statistics": ref(BASE / "report_statistics.json"),
            "test_audit": ref(BASE / "test_verification.json"),
            "new_test_forward_executed": False,
        },
    )
    print({"status": "PASS", "manuscript": path.relative_to(ROOT).as_posix()})


if __name__ == "__main__":
    main()
