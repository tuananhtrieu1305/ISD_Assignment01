import { Link } from "react-router-dom";

export default function HomePipelinePage() {
  return (
    <section className="home-page">
      <div className="page-intro">
        <p className="eyebrow">Assignment 02</p>
        <h2>Intelligent Systems</h2>
        <p>Chọn một chức năng để nhập thông tin và xem kết quả dự đoán theo schema mới.</p>
      </div>

      <div className="system-grid">
        <Link to="/diabetes" className="system-card">
          <span className="card-kicker">Thông tin sức khỏe</span>
          <h3>Dự đoán tiểu đường</h3>
          <p>Nhập 21 chỉ số CDC/BRFSS theo từng nhóm sức khỏe và thói quen.</p>
        </Link>
        <Link to="/house" className="system-card">
          <span className="card-kicker">Thông tin căn nhà</span>
          <h3>Dự đoán giá nhà</h3>
          <p>Nhập 12 feature gồm thông số nhà, vị trí, pháp lý, nội thất và hướng.</p>
        </Link>
        <Link to="/customer-behavior" className="system-card">
          <span className="card-kicker">Hành vi khách hàng</span>
          <h3>Dự đoán churn</h3>
          <p>Nhập feature customer-level theo giao dịch, session, review và sở thích.</p>
        </Link>
      </div>
    </section>
  );
}
