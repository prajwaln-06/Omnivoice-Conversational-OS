import { ArrowLeft } from "lucide-react";
import { useNavigate } from "react-router-dom";

export default function Navbar({ title, showBack = false, rightText = "Console v1.0" }) {
  const nav = useNavigate();

  return (
    <div className="flex justify-between items-center px-10 py-5 border-b border-cyan-400/10 bg-[rgba(2,6,23,0.72)] backdrop-blur-md">
      <div className="flex items-center gap-4">
        {showBack ? (
          <button
            onClick={() => nav(-1)}
            className="w-10 h-10 rounded-xl border border-slate-400/20 bg-white/5 flex items-center justify-center text-slate-400"
          >
            <ArrowLeft size={18} />
          </button>
        ) : (
          <div className="w-10 h-10 rounded-xl border border-cyan-400/30 flex items-center justify-center text-cyan-400 shadow-[0_0_16px_rgba(34,211,238,0.18)]">
            ✦
          </div>
        )}

        <div className="text-2xl font-bold bg-gradient-to-r from-cyan-400 to-emerald-500 bg-clip-text text-transparent">
          {title}
        </div>
      </div>

      <span className="text-gray-400 text-sm font-mono">{rightText}</span>
    </div>
  );
}