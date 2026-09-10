import { Navigate, Route, Routes } from "react-router-dom";
import AppLayout from "./components/AppLayout";
import CustomerBehaviorPage from "./pages/CustomerBehaviorPipelinePage";
import DiabetesPage from "./pages/DiabetesPipelinePage";
import HomePage from "./pages/HomePipelinePage";
import HousePricePage from "./pages/HousePricePipelinePage";

export default function App() {
  return (
    <AppLayout>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/diabetes" element={<DiabetesPage />} />
        <Route path="/house" element={<HousePricePage />} />
        <Route path="/customer-behavior" element={<CustomerBehaviorPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AppLayout>
  );
}
