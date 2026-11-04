import { Navigate, Route, Routes } from "react-router-dom";
import AppLayout from "./components/AppLayout";
import RnnModelPage from "./pages/CustomerBehaviorPipelinePage";
import DiabetesModelPage from "./pages/DiabetesPipelinePage";
import HomePage from "./pages/HomePipelinePage";
import EuroSatModelPage from "./pages/HousePricePipelinePage";

export default function App() {
  return (
    <AppLayout>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/ml" element={<DiabetesModelPage />} />
        <Route path="/cnn" element={<EuroSatModelPage />} />
        <Route path="/rnn" element={<RnnModelPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AppLayout>
  );
}
