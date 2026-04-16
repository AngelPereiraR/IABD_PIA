import { BrowserRouter, Routes, Route, NavLink } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Dashboard } from "./pages/Dashboard";
import { UploadCV } from "./pages/UploadCV";

const qc = new QueryClient();

function Nav() {
  const cls = ({ isActive }) =>
    `px-4 py-2 rounded ${isActive ? "bg-indigo-600 text-white" : "text-gray-600 hover:bg-gray-100"}`;
  return (
    <nav className="flex gap-2 p-4 border-b border-gray-200 bg-white">
      <span className="font-bold text-indigo-700 mr-4">OptiCV</span>
      <NavLink to="/" end className={cls}>Dashboard</NavLink>
      <NavLink to="/upload-cv" className={cls}>CV Maestro</NavLink>
    </nav>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={qc}>
      <BrowserRouter>
        <Nav />
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/upload-cv" element={<UploadCV />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
