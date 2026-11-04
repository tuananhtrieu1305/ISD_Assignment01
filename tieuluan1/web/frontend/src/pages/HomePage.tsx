import { Link } from "react-router-dom";

export default function HomePage() {
  return (
    <section className="home-page">
      <div className="page-intro">
        <p className="eyebrow">Assignment 02</p>
        <h2>Intelligent Systems</h2>
        <p>
          Chọn một chức năng bên dưới để nhập thông tin và xem kết quả dự đoán
          theo cách dễ hiểu.
        </p>
      </div>

      <div className="system-grid">
        <Link to="/diabetes" className="system-card">
          <span className="card-kicker">Thông tin sức khỏe</span>
          <h3>Dự đoán tiểu đường</h3>
          <p>Nhập 6 chỉ số sức khỏe để xem nhóm kết quả mô hình dự đoán.</p>
        </Link>
        <Link to="/house" className="system-card">
          <span className="card-kicker">Thông tin căn nhà</span>
          <h3>Dự đoán giá nhà</h3>
          <p>Nhập 6 đặc điểm căn nhà để nhận mức giá ước tính từ mô hình.</p>
        </Link>
        <Link to="/customer-behavior" className="system-card">
          <span className="card-kicker">Hành vi khách hàng</span>
          <h3>Dự đoán churn</h3>
          <p>
            Nhập dữ liệu giao dịch, phiên truy cập và review để dự đoán nguy cơ
            khách hàng rời bỏ.
          </p>
        </Link>
      </div>
    </section>
  );
}
