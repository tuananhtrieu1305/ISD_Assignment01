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
        <div>
          <p className="eyebrow">Intelligent Systems Development</p>
          <h1>Assignment 02</h1>
        </div>
        <nav className="nav-links" aria-label="Primary navigation">
          <NavLink to="/" end>
            Home
          </NavLink>
          <NavLink to="/diabetes">Tiểu đường</NavLink>
          <NavLink to="/house">Giá nhà</NavLink>
          <NavLink to="/customer-behavior">Khách hàng</NavLink>
        </nav>
        <div
          className={`status-pill ${
            backendOnline === true
              ? "online"
              : backendOnline === false
                ? "offline"
                : ""
          }`}
        >
          {backendOnline === null
            ? "Đang kiểm tra"
            : backendOnline
              ? "Hệ thống sẵn sàng"
              : "Không thể kết nối hệ thống"}
        </div>
      </header>
      <main className="page-wrap">{children}</main>
    </div>
  );
}
