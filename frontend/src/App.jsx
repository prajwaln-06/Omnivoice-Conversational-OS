import { BrowserRouter, Routes, Route } from "react-router-dom";
import Landing from "./pages/Landing";
import Dashboard from "./pages/Dashboard";
import ModeSelect from "./pages/ModeSelect";
import Active from "./pages/Active";
import Passive from "./pages/Passive";
import Result from "./pages/Result";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/mode" element={<ModeSelect />} />
        <Route path="/active" element={<Active />} />
        <Route path="/passive" element={<Passive />} />
        <Route path="/result" element={<Result />} />
      </Routes>
    </BrowserRouter>
  );
}