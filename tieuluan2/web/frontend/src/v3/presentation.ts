import type { Doc } from "./types";
export function displayValue(value: unknown): string {
  if (value === null || value === undefined) return "Không có số đo";
  if (typeof value === "boolean") return value ? "Có" : "Không";
  if (typeof value === "number")
    return Number.isFinite(value)
      ? new Intl.NumberFormat("vi-VN", { maximumFractionDigits: 6 }).format(
          value,
        )
      : "Không có số đo";
  if (typeof value === "string") return value;
  return JSON.stringify(value, null, 2);
}
export function safeLink(value: string): string | undefined {
  try {
    const url = new URL(value);
    return ["https:", "http:"].includes(url.protocol) &&
      !url.username &&
      !url.password
      ? url.href
      : undefined;
  } catch {
    return undefined;
  }
}
export function probabilityWidth(value: number): string {
  return `${Math.max(0, Math.min(1, Number.isFinite(value) ? value : 0)) * 100}%`;
}
export function csvRows(text: string): Doc[] {
  const lines: string[][] = [];
  let row: string[] = [],
    cell = "",
    quote = false;
  for (let n = 0; n < text.length; n++) {
    const c = text[n];
    if (c === '"') {
      if (quote && text[n + 1] === '"') {
        cell += '"';
        n++;
      } else quote = !quote;
    } else if (c === "," && !quote) {
      row.push(cell);
      cell = "";
    } else if ((c === "\n" || c === "\r") && !quote) {
      if (c === "\r" && text[n + 1] === "\n") n++;
      row.push(cell);
      if (row.some(Boolean)) lines.push(row);
      row = [];
      cell = "";
    } else cell += c;
  }
  if (cell || row.length) {
    row.push(cell);
    lines.push(row);
  }
  if (quote) throw new Error("CSV không hoàn chỉnh");
  const [header = [], ...body] = lines;
  return body.map((values) =>
    Object.fromEntries(header.map((name, n) => [name, values[n] ?? ""])),
  );
}
export function filteredRows(
  rows: Doc[],
  dataset: string,
  family: string,
  hint: Record<string, string>,
): Doc[] {
  return rows.filter(
    (row) =>
      (row.dataset_id === undefined || row.dataset_id === dataset) &&
      (row.family === undefined || row.family === family) &&
      Object.entries(hint).every(
        ([key, value]) => row[key] === undefined || String(row[key]) === value,
      ),
  );
}
export function record(value: unknown): Doc {
  return value && typeof value === "object" && !Array.isArray(value)
    ? (value as Doc)
    : {};
}
export function records(value: unknown): Doc[] {
  return Array.isArray(value) ? value.map(record) : [];
}
