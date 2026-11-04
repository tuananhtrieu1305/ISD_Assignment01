import type { Dataset, Overview } from "./types";
import { displayValue, record, safeLink } from "./presentation";
import { BarList, Definition, Hash, JsonView, Markdown, Note } from "./ui";
export default function DataCard({
  dataset,
  overview,
}: {
  dataset: Dataset;
  overview: Overview;
}) {
  const distribution = record(overview.eda_summary.distribution_summary);
  const counts = record(
    distribution.class_counts ??
      distribution.target_counts ??
      distribution.label_counts,
  );
  const sample = overview.sample;
  const bytes = dataset.files.reduce(
    (n, file) => n + (file.size_bytes ?? 0),
    0,
  );
  return (
    <section className="v3-surface" data-testid="data-card">
      <div className="v3-section-heading">
        <div>
          <span className="v3-kicker">DATASET CARD</span>
          <h2>Dữ liệu & nguồn gốc</h2>
        </div>
        <a
          className="v3-button secondary"
          href={safeLink(dataset.source.url)}
          target="_blank"
          rel="noreferrer"
        >
          Nguồn chính thức ↗
        </a>
      </div>
      <div className="v3-stat-strip">
        <div>
          <span>Kích cỡ logic</span>
          <strong>
            {displayValue(
              dataset.logical_size.records ??
                dataset.logical_size.entities ??
                dataset.logical_size.tasks,
            )}
          </strong>
        </div>
        <div>
          <span>Dung lượng file nguồn</span>
          <strong>{displayValue(bytes)} byte</strong>
        </div>
        <div>
          <span>Phạm vi</span>
          <strong>{overview.scope}</strong>
        </div>
      </div>
      <p className="v3-muted">{dataset.source.citation}</p>
      <details>
        <summary>Giấy phép, phiên bản & hash</summary>
        <Definition
          values={{
            "License status": dataset.source.license_status,
            "Điều khoản": dataset.source.license_note,
            "Phiên bản": dataset.source.version,
          }}
        />
        <Hash value={overview.data_card.sha256} />
      </details>
      <BarList data={counts} label="Phân bố nhãn · snapshot EDA đã lưu" />
      {sample && (
        <div className="v3-sample">
          <h3>Mẫu input minh họa</h3>
          <p>
            {sample.sample_id} · <strong>{sample.input_split}</strong> · mẫu
            demo, không phải TEST mới
          </p>
          {sample.request.input.kind === "image" && (
            <img
              className="v3-sample-image"
              src={`data:${String(sample.request.input.media_type)};base64,${String(sample.request.input.data)}`}
              alt={`Mẫu TRAIN của ${overview.dataset_id}`}
            />
          )}
          <JsonView value={sample.request.input} label="Input có cấu trúc" />
        </div>
      )}
      <details className="v3-card-details" open>
        <summary>Thẻ dữ liệu đầy đủ · mẫu/output, phân bố, nhận xét</summary>
        <Markdown text={overview.data_card_text} />
      </details>
      <JsonView
        value={overview.eda_summary}
        label="EDA gốc: size/schema, phân bố, missing và giới hạn"
      />
      <Note>
        Không nhập bệnh án hoặc dữ liệu nhạy cảm. Nguồn là snapshot học thuật,
        không dữ liệu thị trường hiện tại.
      </Note>
    </section>
  );
}
