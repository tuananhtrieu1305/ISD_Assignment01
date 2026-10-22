import { useEffect, useMemo, useRef } from "react";
import { Link, NavLink, useLocation, useNavigate } from "react-router-dom";
import { ApiClient } from "./client";
import { chapters, datasetNames } from "./catalog";
import { resolveSelection, selectionUrl, sections } from "./routing";
import type { Dataset, Envelope, Model, Overview } from "./types";
import { useResource } from "./hooks";
import { Boundary, ErrorPanel, Loading } from "./ui";
import DataCard from "./DataCard";
import FunctionComposition from "./FunctionComposition";
import ModelRunner from "./ModelRunner";
import HistoricalResults from "./HistoricalResults";
import Deployment from "./Deployment";
import "./lab.css";
const labels = {
  data: "Dữ liệu",
  theory: "Hợp hàm & lý thuyết",
  run: "Chạy so sánh",
  results: "Kết quả đã lưu",
  deployment: "Triển khai",
};
export default function App() {
  return (
    <Boundary>
      <Lab />
    </Boundary>
  );
}
function Lab() {
  const location = useLocation();
  const navigate = useNavigate();
  const selection = resolveSelection(
    location.pathname,
    new URLSearchParams(location.search),
  );
  const chapter = chapters.find((row) => row.chapter === selection.chapter)!;
  const mainNavigation = useRef<HTMLElement>(null);
  const datasetNavigation = useRef<HTMLElement>(null);
  useEffect(() => {
    for (const ref of [mainNavigation, datasetNavigation]) {
      const nav = ref.current;
      const active = nav?.querySelector<HTMLElement>('[aria-current="page"]');
      if (nav && active && nav.scrollWidth > nav.clientWidth)
        nav.scrollLeft = Math.max(0, active.offsetLeft - nav.offsetLeft - 8);
    }
  }, [selection.route, selection.dataset]);
  const api = useMemo(
    () =>
      new ApiClient(
        import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:5000",
      ),
    [],
  );
  const health = useResource(api.base + "/ready", (signal) =>
    api.get<{ status: string }>("/ready", signal),
  );
  const data = useResource(
    api.base + "/" + selection.dataset + "/" + (selection.error ?? "valid"),
    async (signal) => {
      if (selection.error) return null;
      const [dataset, overview, models] = await Promise.all([
        api.get<Envelope<Dataset>>(
          `/api/v3/datasets/${selection.dataset}`,
          signal,
        ),
        api.get<Envelope<Overview>>(
          `/api/v3/datasets/${selection.dataset}/overview`,
          signal,
        ),
        selection.chapter > 1
          ? api.get<Envelope<Model[]>>(
              `/api/v3/models?dataset_id=${selection.dataset}&page_size=100`,
              signal,
            )
          : Promise.resolve({ data: [] }),
      ]);
      return {
        dataset: dataset.data,
        overview: overview.data,
        models: models.data,
      };
    },
  );
  const models =
    data.value?.models.filter((row) => row.family === selection.family) ?? [];
  return (
    <div className="v3-shell">
      <a className="v3-skip" href="#lab-content">
        Đến nội dung chính
      </a>
      <header className="v3-header">
        <Link to="/" className="v3-brand" aria-label="Model Lab — Tổng quan">
          <span aria-hidden="true">
            M<span>↗</span>
          </span>
          <span>
            <small>TIỂU LUẬN TRÍ TUỆ NHÂN TẠO</small>
            <strong>
              Model Lab<span className="v3-version">/ 03</span>
            </strong>
          </span>
        </Link>
        <span
          className={`v3-api-status ${health.value?.status === "ready" ? "online" : ""}`}
          role="status"
        >
          <i />
          {health.loading
            ? "Kiểm tra API…"
            : health.error
              ? "API chưa kết nối"
              : `API ${health.value?.status}`}
        </span>
      </header>
      <nav
        ref={mainNavigation}
        className="v3-main-nav"
        aria-label="Điều hướng chính"
      >
        {chapters.map((row) => (
          <NavLink to={row.route} end key={row.route}>
            {row.label}
            <span aria-hidden="true">
              {String(row.chapter).padStart(2, "0")}
            </span>
          </NavLink>
        ))}
      </nav>
      <main id="lab-content" className="v3-content">
        <section className="v3-hero">
          <div>
            <p className="v3-kicker">
              CHƯƠNG {String(chapter.chapter).padStart(2, "0")} / PHÒNG THÍ
              NGHIỆM TƯƠNG TÁC
            </p>
            <h1>
              {chapter.chapter === 1
                ? "Từ dữ liệu đến quyết định."
                : chapter.title}
            </h1>
            <p>{chapter.intro}</p>
            <div className="v3-hero-tags">
              <span>3 dataset / chương</span>
              <span>Checkpoint đã khóa</span>
              <span>Không train trên web</span>
            </div>
          </div>
          <div className="v3-hero-number" aria-hidden="true">
            {String(chapter.chapter).padStart(2, "0")}
            <span>LEARN / COMPARE / TRACE</span>
          </div>
        </section>
        {chapter.chapter === 1 && (
          <section className="v3-directory">
            <p className="v3-kicker">MỘT HÀNH TRÌNH · SÁU CHƯƠNG</p>
            <div>
              {chapters.slice(1).map((row) => (
                <Link to={row.route} key={row.route}>
                  <span>{String(row.chapter).padStart(2, "0")}</span>
                  <strong>{row.label}</strong>
                  <small>{row.datasets.length}dataset</small>
                  <b aria-hidden="true">↗</b>
                </Link>
              ))}
            </div>
            <p>
              Lịch sử AI qua ba case study bên dưới; các chương2–6 có dữ liệu,
              hợp hàm, demo và kết quả truy nguồn.
            </p>
          </section>
        )}
        <nav
          ref={datasetNavigation}
          className="v3-dataset-nav"
          aria-label="Chọn dataset"
        >
          {chapter.datasets.map((id, n) => (
            <Link
              key={id}
              to={selectionUrl(
                { ...selection, error: null },
                {
                  dataset: id,
                  family:
                    chapter.chapter === 4 &&
                    ["rnn", "lstm"].includes(selection.family)
                      ? selection.family
                      : chapter.family,
                },
              )}
              aria-current={id === selection.dataset ? "page" : undefined}
            >
              <span>{String(n + 1).padStart(2, "0")}</span>
              {datasetNames[id]}
            </Link>
          ))}
        </nav>
        {selection.error ? (
          <ErrorPanel
            error={selection.error}
            retry={() => navigate(chapter.route)}
          />
        ) : (
          <>
            <div className="v3-workspace-heading">
              <h2>{datasetNames[selection.dataset]}</h2>
              {chapter.chapter === 4 && (
                <div className="v3-family" role="group" aria-label="Họ mô hình">
                  {["rnn", "lstm"].map((family) => (
                    <button
                      key={family}
                      aria-pressed={selection.family === family}
                      onClick={() =>
                        navigate(selectionUrl(selection, { family }))
                      }
                    >
                      {family.toUpperCase()}
                    </button>
                  ))}
                </div>
              )}
            </div>
            <nav className="v3-section-nav" aria-label="Nội dung dataset">
              {sections
                .filter(
                  (section) =>
                    chapter.chapter > 1 || ["data", "theory"].includes(section),
                )
                .map((section) => (
                  <Link
                    key={section}
                    to={selectionUrl(selection, { section })}
                    aria-current={
                      selection.section === section ? "page" : undefined
                    }
                  >
                    {labels[section]}
                  </Link>
                ))}
            </nav>
            {data.loading && <Loading />}
            {data.error && <ErrorPanel error={data.error} retry={data.retry} />}
            {data.value && (
              <div
                key={`${selection.dataset}/${selection.family}`}
                className="v3-panel"
              >
                {selection.section === "data" && (
                  <DataCard
                    dataset={data.value.dataset}
                    overview={data.value.overview}
                  />
                )}
                {selection.section === "theory" && (
                  <FunctionComposition
                    api={api}
                    models={models}
                    family={selection.family}
                    intro={chapter.intro}
                  />
                )}
                {selection.section === "run" && (
                  <ModelRunner
                    api={api}
                    overview={data.value.overview}
                    family={selection.family}
                  />
                )}
                {selection.section === "results" && (
                  <HistoricalResults
                    api={api}
                    dataset={selection.dataset}
                    family={selection.family}
                    chapter={chapter.chapter}
                  />
                )}
                {selection.section === "deployment" && (
                  <Deployment api={api} models={models} />
                )}
              </div>
            )}
          </>
        )}
        <div className="v3-academic-note">
          <strong>Học thuật, không lời khuyên chuyên môn.</strong>
          <p>
            Không nhập bệnh án hoặc secret. Dự đoán trên snapshot không dùng để
            chẩn đoán, định giá hiện tại hay đầu tư. TEST đã niêm phong không
            được chạy lại từ giao diện.
          </p>
        </div>
      </main>
      <footer className="v3-footer">
        <span>MODEL LAB / AI TERM PAPER V3</span>
        <span>React UI · Python API · provenance first</span>
      </footer>
    </div>
  );
}
