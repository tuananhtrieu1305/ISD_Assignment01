import { Component, Fragment, type ReactNode } from "react";
import { displayValue, record, safeLink } from "./presentation";
import type { Doc } from "./types";
export function ErrorPanel({
  error,
  retry,
}: {
  error: unknown;
  retry?: () => void;
}) {
  return (
    <div className="v3-alert error" role="alert">
      <strong>Chưa thể tải nội dung</strong>
      <p>{error instanceof Error ? error.message : String(error)}</p>
      {retry && <button onClick={retry}>Thử lại</button>}
    </div>
  );
}
export function Loading({
  text = "Đang đọc artifact đã khóa…",
}: {
  text?: string;
}) {
  return (
    <div className="v3-loading" role="status">
      <span className="v3-spinner" />
      {text}
    </div>
  );
}
export function Note({ children }: { children: ReactNode }) {
  return <div className="v3-note">{children}</div>;
}
export function JsonView({
  value,
  label = "Xem dữ liệu gốc",
}: {
  value: unknown;
  label?: string;
}) {
  return (
    <details className="v3-json">
      <summary>{label}</summary>
      <pre>{JSON.stringify(value, null, 2)}</pre>
    </details>
  );
}
export function Hash({ value }: { value: string | null | undefined }) {
  return value ? (
    <code className="v3-hash" title={value}>
      {value}
    </code>
  ) : (
    <span>Không có số đo</span>
  );
}
export function Definition({ values }: { values: Doc }) {
  return (
    <dl className="v3-definitions">
      {Object.entries(values).map(([key, value]) => (
        <Fragment key={key}>
          <dt>{key}</dt>
          <dd>{displayValue(value)}</dd>
        </Fragment>
      ))}
    </dl>
  );
}
function inline(text: string): ReactNode {
  return text
    .split(/(\[[^\]]+\]\(https?:\/\/[^)]+\)|`[^`]+`|\*\*[^*]+\*\*)/g)
    .map((part, n) => {
      const link = part.match(/^\[([^\]]+)\]\(([^)]+)\)$/);
      if (link)
        return (
          <a key={n} href={safeLink(link[2])} rel="noreferrer" target="_blank">
            {link[1]} ↗
          </a>
        );
      if (part.startsWith("`")) return <code key={n}>{part.slice(1, -1)}</code>;
      if (part.startsWith("**"))
        return <strong key={n}>{part.slice(2, -2)}</strong>;
      return part;
    });
}
export function Markdown({ text }: { text: string }) {
  const lines = text.split("\n");
  const blocks: ReactNode[] = [];
  for (let index = 0; index < lines.length; index++) {
    const line = lines[index].trim();
    if (!line) continue;
    if (line.startsWith("```")) {
      const language = line.slice(3).trim() || "text";
      const code: string[] = [];
      index++;
      while (index < lines.length && !lines[index].trim().startsWith("```")) {
        code.push(lines[index]);
        index++;
      }
      blocks.push(
        <details className="v3-json" key={index}>
          <summary>Ví dụ có cấu trúc · {language}</summary>
          <pre>{code.join("\n")}</pre>
        </details>,
      );
    } else if (line.startsWith("|")) {
      const rows: string[][] = [];
      while (index < lines.length && lines[index].trim().startsWith("|")) {
        const parts = lines[index]
          .trim()
          .split("|")
          .slice(1, -1)
          .map((s) => s.trim());
        if (!parts.every((s) => /^[-: ]+$/.test(s))) rows.push(parts);
        index++;
      }
      index--;
      const [head = [], ...body] = rows;
      blocks.push(
        <div className="v3-table-wrap" key={index}>
          <table>
            <thead>
              <tr>
                {head.map((cell, n) => (
                  <th key={n}>{inline(cell)}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {body.map((row, n) => (
                <tr key={n}>
                  {row.map((cell, j) => (
                    <td key={j}>{inline(cell)}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>,
      );
    } else if (/^#{1,6} /.test(line))
      blocks.push(<h3 key={index}>{inline(line.replace(/^#+ /, ""))}</h3>);
    else
      blocks.push(
        <p key={index} className={/^[-*] /.test(line) ? "v3-list-line" : ""}>
          {inline(line)}
        </p>,
      );
  }
  return <div className="v3-prose">{blocks}</div>;
}
export function DataTable({ rows }: { rows: Doc[] }) {
  if (!rows.length)
    return <Note>Không có dòng phù hợp với dataset/họ mô hình đang chọn.</Note>;
  const columns = [...new Set(rows.flatMap((row) => Object.keys(row)))];
  return (
    <div
      className="v3-table-wrap"
      tabIndex={0}
      role="region"
      aria-label="Bảng dữ liệu có thể cuộn"
    >
      <table>
        <thead>
          <tr>
            {columns.map((key) => (
              <th key={key}>{key}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.slice(0, 60).map((row, n) => (
            <tr key={n}>
              {columns.map((key) => (
                <td key={key}>{displayValue(row[key])}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      {rows.length > 60 && (
        <p>Hiển thị60/{rows.length}dòng; tải artifact để xem toàn bộ.</p>
      )}
    </div>
  );
}
export function BarList({ data, label }: { data: Doc; label: string }) {
  const rows = Object.entries(data).filter(
    ([, value]) =>
      typeof value === "number" && Number.isFinite(value) && value >= 0,
  ) as [string, number][];
  if (!rows.length) return null;
  const max = Math.max(1, ...rows.map(([, n]) => n));
  return (
    <figure className="v3-bars">
      <figcaption>
        {label} · trục từ0 đến{displayValue(max)}
      </figcaption>
      {rows.slice(0, 24).map(([key, n]) => (
        <div className="v3-bar-row" key={key}>
          <span>{key}</span>
          <span className="v3-bar-track">
            <span style={{ width: `${(n / max) * 100}%` }} />
          </span>
          <strong>{displayValue(n)}</strong>
        </div>
      ))}
    </figure>
  );
}
export class Boundary extends Component<
  { children: ReactNode },
  { error: Error | null }
> {
  state = { error: null as Error | null };
  static getDerivedStateFromError(error: Error) {
    return { error };
  }
  render() {
    return this.state.error ? (
      <ErrorPanel
        error={
          new Error(
            "Giao diện gặp lỗi. Hãy tải lại trang; dữ liệu đã khóa không bị thay đổi.",
          )
        }
        retry={() => location.reload()}
      />
    ) : (
      this.props.children
    );
  }
}
export function flatFields(value: unknown): Doc {
  const row = record(value);
  return Object.fromEntries(
    Object.entries(row).filter(
      ([, v]) =>
        v === null || ["number", "string", "boolean"].includes(typeof v),
    ),
  );
}
