import { ReactNode, useEffect, useState } from "react";
import { NavLink } from "react-router-dom";
import { healthCheck } from "../api/predictionApi";

type AppLayoutProps = {
  children: ReactNode;
};

export default function AppLayout({ children }: AppLayoutProps) {
  const [backendOnline, setBackendOnline] = useState<boolean | null>(null);

  useEffect(() => {
    let ignore = false;

    healthCheck()
      .then(() => {
        if (!ignore) setBackendOnline(true);
      })
      .catch(() => {
        if (!ignore) setBackendOnline(false);
      });

    return () => {
      ignore = true;
    };
  }, []);

  return (
    <div className="app-shell">
      <header className="app-header">
        <NavLink to="/" className="brand-block" aria-label="AI Model Lab - Trang chủ">
          <span className="brand-mark" aria-hidden="true">AI</span>
          <span>
            <span className="eyebrow">Tiểu luận môn học</span>
            <strong>Model Lab</strong>
          </span>
        </NavLink>

        <nav className="nav-links" aria-label="Điều hướng chính">
          <NavLink to="/" end>Trang chủ</NavLink>
          <NavLink to="/ml">ML</NavLink>
          <NavLink to="/cnn">CNN</NavLink>
          <NavLink to="/rnn">RNN</NavLink>
        </nav>

        <div
          className={`status-pill ${
            backendOnline === true
              ? "online"
              : backendOnline === false
                ? "offline"
                : ""
          }`}
          role="status"
        >
          <span className="status-dot" aria-hidden="true" />
          {backendOnline === null
            ? "Đang kiểm tra API"
            : backendOnline
              ? "4 mô hình sẵn sàng"
              : "API chưa kết nối"}
        </div>
      </header>

      <main className="page-wrap">{children}</main>

      <footer className="app-footer">
        <p>AI · Machine Learning · CNN · RNN</p>
        <p>Ứng dụng minh họa học thuật — không thay thế tư vấn chuyên môn.</p>
      </footer>
    </div>
  );
}
