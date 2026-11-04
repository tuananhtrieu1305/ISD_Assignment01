import { useState } from "react";
import type { Doc } from "./types";
import { displayValue, record, records } from "./presentation";
import { Definition, Hash, JsonView, Note } from "./ui";
export default function AgentTrace({ details }: { details: Doc }) {
  const traces = record(details.traces);
  const [selected, select] = useState("");
  const entries = Object.entries(traces);
  const [id, raw] = entries.find(([key]) => key === selected) ??
    entries[entries.length - 1] ?? ["", {}];
  const trace = record(raw);
  const nodes = records(trace.nodes);
  const variant = String(trace.variant ?? "A2");
  const output = record(record(record(details.agent_outputs).outputs)[variant]);
  if (!entries.length)
    return (
      <Note>Chưa có agent trace; chỉ xuất hiện sau khi job đã xử lý.</Note>
    );
  return (
    <section className="v3-surface v3-trace" data-testid="agent-trace">
      <span className="v3-kicker">QUAN SÁT ORCHESTRATION</span>
      <h2>Agent trace & bằng chứng</h2>
      <label className="v3-field">
        Chọn trace
        <select value={id} onChange={(event) => select(event.target.value)}>
          {entries.map(([key, value]) => (
            <option key={key} value={key}>
              {displayValue(record(value).variant)} ·{" "}
              {displayValue(record(value).status)}
            </option>
          ))}
        </select>
      </label>
      <div
        className="v3-trace-flow"
        role="group"
        aria-label="Đồ thị các bước thực thi"
      >
        {nodes.map((node, n) => (
          <div className="v3-trace-node" key={n}>
            <small>{displayValue(node.node_id ?? node.id)}</small>
            <strong>
              {displayValue(node.role ?? node.agent ?? node.name)}
            </strong>
            <span>{displayValue(node.status ?? node.outcome)}</span>
            <span aria-hidden="true">→</span>
          </div>
        ))}
      </div>
      <Definition
        values={{
          "Biến thể": trace.variant,
          "Định tuyến": output.route,
          "Kiểm chứng": output.verification,
          "Tool call": output.tool_calls,
          "Số message": output.message_count,
          "Wall latency (ms)": trace.latency_ms,
        }}
      />
      <Note>
        Message là input/output công cụ, không chain-of-thought. Node duration0
        chưa instrument không phải số đo0ms. Hệ xác định, ID-bound; không LLM
        hoặc tác tử tự chủ tổng quát.
      </Note>
      <ol className="v3-timeline">
        {nodes.map((node, n) => (
          <li key={n}>
            <strong>
              {displayValue(node.role ?? node.agent ?? node.name)}
            </strong>
            <Definition
              values={{
                "Phụ thuộc": node.depends_on ?? node.parents ?? node.parent_ids,
                "Kết quả": node.status ?? node.outcome,
                "Thời gian node":
                  node.duration_ms === 0
                    ? "Chưa instrument riêng (giá trị mặc định0)"
                    : node.duration_ms,
              }}
            />
            <JsonView value={node} label="Node và artifact refs" />
          </li>
        ))}
      </ol>
      <h3>Thông điệp công cụ</h3>
      {records(output.messages).map((message, n) => (
        <JsonView
          key={n}
          value={message}
          label={`Message${n + 1} · ${displayValue(message.node_id)}`}
        />
      ))}
      <p>{displayValue(trace.answer)}</p>
      <Hash value={String(trace.task_set_sha256 ?? "")} />
      <JsonView value={trace.citations} label="Citation / provenance" />
      <p className="v3-muted">{displayValue(trace.limitations)}</p>
    </section>
  );
}
