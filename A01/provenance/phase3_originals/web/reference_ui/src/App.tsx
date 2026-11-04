import { Navigate, Route, Routes } from "react-router-dom";
import AppLayout from "./components/AppLayout";
import DiabetesPage from "./pages/DiabetesPage";
import HomePage from "./pages/HomePage";
import HousePricePage from "./pages/HousePricePage";

export default function App() {
  return (
    <AppLayout>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/diabetes" element={<DiabetesPage />} />
        <Route path="/house" element={<HousePricePage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AppLayout>
  );
}
