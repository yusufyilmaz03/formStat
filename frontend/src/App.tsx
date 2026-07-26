import { Navigate, Route, Routes } from "react-router-dom";
import GoogleConnect from "./components/GoogleConnect";
import { Link } from "react-router-dom";
import FormsList from "./pages/FormsList";
import FormBuilder from "./pages/FormBuilder";
import ResponsesPage from "./pages/ResponsesPage";
import AnalysisDashboard from "./pages/AnalysisDashboard";

export default function App() {
  return (
    <>
      <div className="topbar">
        <Link to="/" className="brand" style={{ color: "inherit" }}>
          <span className="logo">📊</span> FormStat
        </Link>
        <GoogleConnect />
      </div>
      <div className="container">
        <Routes>
          <Route path="/" element={<FormsList />} />
          <Route path="/new" element={<FormBuilder />} />
          <Route path="/forms/:id/edit" element={<FormBuilder />} />
          <Route path="/forms/:id/responses" element={<ResponsesPage />} />
          <Route path="/forms/:id/analysis" element={<AnalysisDashboard />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </div>
    </>
  );
}
