# AG02 — đối chiếu đủ 10 câu với bằng chứng

Bản thảo: [manuscript.md](phase 08/manuscript.md). Code/CSV/hình được đọc từ các khóa Phase 1–7;không có train/final mới.

## Q01 — 6.1. Câu 1

Hai policy chọn đồng thời, môi trường/sales/reward/state và MAS qua môi trường chung.

Code: `code/controlled.py:144` MarketEnv.step; `code/controlled.py:132` MarketEnv.states.

Bảng: baseline_train;hình: F01, F02;nguồn: S1, S6.

Artifact: `docs/protocol_v1.json`; `artifacts/runs/controlled/iid/baseline/s0011/trace_sample.json`.

## Q02 — 6.2. Câu 2

Rule không học;RL dùng reward sửaQ;ví dụ hành chính tiểu đường/lọc nhà chỉ minh họa.

Code: `code/controlled.py:167` RuleAgent.act; `code/controlled.py:179` QAgent.act.

Bảng: core_final;hình: F09;nguồn: S1, S4, S6.

Artifact: `artifacts/metrics/phase05/config_summary.json`; `artifacts/metrics/phase05/controls_summary.json`.

## Q03 — 6.3. Câu 3

Hypothetical Q-update 4 → 4,65 và terminal không bootstrap;không dùng số giả định làm empirical reward.

Code: `code/controlled.py:192` QAgent.learn.

Bảng: q_policy;hình: F03;nguồn: S1, S3.

Artifact: `docs/model_core_v1.md`; `evidence/phase02/verification.json`.

## Q04 — 6.4. Câu 4

Epsilon điều khiển khám phá;ba lịch,cảtrain/final;greedy vẫn có randomtie.

Code: `code/controlled.py:179` QAgent.act; `code/controlled.py:69` LearningConfig.epsilon_at.

Bảng: exploration;hình: F06, F07, F12;nguồn: S1, S4.

Artifact: `artifacts/metrics/phase04/config_train_summary.csv`; `artifacts/metrics/phase05/exploration_comparison.csv`.

## Q05 — 6.5. Câu 5

Margin 5/3;sales không thay profit;reward mới chỉ đề xuất,chưa có số đo.

Code: `code/controlled.py:79` margin; `code/controlled.py:74` conversion.

Bảng: baseline_train;hình: F04, F12;nguồn: S1, S3.

Artifact: `docs/protocol_v1.json`; `artifacts/metrics/phase03_train_summary.csv`.

## Q06 — 6.6. Câu 6

Mean đúng mẫu số;REF/native riêng;gộp role trước 5 seed;within-match khác policycontrol.

Code: `code/evaluation/aggregate_v1.py:25` role_average; `code/evaluation/aggregate_v1.py:37` mean_std.

Bảng: baseline_train, baseline_final, core_final;hình: F09, F10, F11;nguồn: S1.

Artifact: `artifacts/metrics/phase05/baseline_reward.csv`; `artifacts/metrics/phase05/config_summary.json`.

## Q07 — 6.7. Câu 7

Ba alpha 0,01/0,10/0,50;std train khác final;không suy hội tụ/tối ưu.

Code: `code/controlled.py:192` QAgent.learn.

Bảng: alpha;hình: F05, F08, F09;nguồn: S1, S4.

Artifact: `artifacts/metrics/phase04/config_train_summary.csv`; `artifacts/metrics/phase05/alpha_comparison.csv`.

## Q08 — 6.8. Câu 8

Non-stationarity khi hai learner;fixed-opponent checkpoint test;pair là replicate,chưa chứng minh nhânquả.

Code: `code/pair_training.py:26` PairSession.run_chunk; `code/evaluation/final_v1.py:29` evaluate_tapes.

Bảng: q 8;hình: F14, F15;nguồn: S1, S5, S6.

Artifact: `artifacts/metrics/phase06/q8_summary.csv`; `artifacts/metrics/phase06/policy_drift.csv`; `evidence/phase06/train_declaration.json`.

## Q09 — 6.9. Câu 9

>=3 hạnchế;kernel persistent/Goldđãcode/train/eval;chỉTRAINprefix;khôngđo cầu vàng.

Code: `phase06.py:43` markets; `code/gold_regime.py:33` estimate_regimes.

Bảng: gold_kernel, variants;hình: F13, F16;nguồn: S1, S7.

Artifact: `data/derived/gold_regime_kernel_v1.json`; `artifacts/metrics/phase06/variant_summary.csv`; `artifacts/metrics/phase06/variant_deltas.csv`.

## Q10 — 6.10. Câu 10

State/action/reward/method/eval,cùngbudget/kernel;320 Qchưa cải thiện mean;oracle không làmnhãntrain.

Code: `code/augmented.py:73` AugmentedAgent.learn; `code/augmented.py:33` observe; `code/market_oracle.py:33` solve.

Bảng: improved, improved_delta, oracle;hình: F17, F18, F19, F20;nguồn: S1.

Artifact: `artifacts/metrics/phase07/policy_summary.csv`; `artifacts/metrics/phase07/delta_summary.csv`; `artifacts/metrics/phase07/model_expectations.csv`; `artifacts/manifests/phase07/reference_index.json`.

