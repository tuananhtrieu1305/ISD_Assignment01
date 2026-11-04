import { chapters } from "./catalog";
export const sections = [
  "data",
  "theory",
  "run",
  "results",
  "deployment",
] as const;
export type Section = (typeof sections)[number];
export type Selection = {
  route: string;
  chapter: number;
  dataset: string;
  family: string;
  section: Section;
  error: string | null;
};
export function resolveSelection(
  route: string,
  query: URLSearchParams,
): Selection {
  const chapter = chapters.find((c) => c.route === route) ?? chapters[0];
  const dataset = query.get("dataset") ?? chapter.datasets[0];
  const family = query.get("family") ?? chapter.family;
  const section = query.get("section") ?? "data";
  const validDataset = (chapter.datasets as readonly string[]).includes(
    dataset,
  );
  const validFamily =
    chapter.chapter === 4
      ? ["rnn", "lstm"].includes(family)
      : family === chapter.family;
  const validSection =
    (sections as readonly string[]).includes(section) &&
    (chapter.chapter > 1 || ["data", "theory"].includes(section));
  const repeated = [...new Set(query.keys())].some(
    (k) => query.getAll(k).length !== 1,
  );
  return {
    route: chapter.route,
    chapter: chapter.chapter,
    dataset,
    family,
    section: section as Section,
    error:
      !validDataset ||
      !validFamily ||
      !validSection ||
      repeated ||
      !chapters.some((c) => c.route === route)
        ? "Đường dẫn không hợp lệ: dataset, họ mô hình hoặc mục nội dung không thuộc chương này."
        : null,
  };
}
export function selectionUrl(
  current: Selection,
  change: Partial<Selection>,
): string {
  const next = { ...current, ...change };
  return `${next.route}?${new URLSearchParams({ dataset: next.dataset, family: next.family, section: next.section })}`;
}
