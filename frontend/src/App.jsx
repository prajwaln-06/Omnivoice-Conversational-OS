import { useMemo, useState } from "react";

const API_BASE_CANDIDATES = ["http://localhost:5000", "http://localhost:8000"];
const DEFAULT_DOMAIN = "healthcare";

export default function App() {
  const [mode, setMode] = useState("autonomous");
  const [audioFile, setAudioFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [statusText, setStatusText] = useState("");
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);
  const [resolvedApiBase, setResolvedApiBase] = useState("");

  const prettyJson = useMemo(() => {
    if (!result?.extracted_data) return "";
    try {
      return JSON.stringify(result.extracted_data, null, 2);
    } catch {
      return String(result.extracted_data);
    }
  }, [result]);

  const parseErrorMessage = async (res) => {
    try {
      const data = await res.json();
      return data?.message || data?.detail || `Request failed (${res.status})`;
    } catch {
      return `Request failed (${res.status})`;
    }
  };

  const requestWithFallback = async (path, options = {}) => {
    const bases = resolvedApiBase
      ? [resolvedApiBase, ...API_BASE_CANDIDATES.filter((base) => base !== resolvedApiBase)]
      : API_BASE_CANDIDATES;

    let lastError = null;
    for (const base of bases) {
      try {
        const res = await fetch(`${base}${path}`, options);
        if (!res.ok) {
          const message = await parseErrorMessage(res);
          throw new Error(message);
        }
        const payload = await res.json();
        setResolvedApiBase(base);
        return payload;
      } catch (err) {
        lastError = err;
      }
    }

    throw lastError || new Error("Unable to reach backend");
  };

  const runAutonomous = async () => {
    setLoading(true);
    setError("");
    setResult(null);
    setStatusText("Listening & Processing...");

    try {
      const data = await requestWithFallback("/api/agent/live", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          domain: DEFAULT_DOMAIN,
          max_turns: 8,
        }),
      });
      setResult(data);
      setStatusText("Live session complete");
    } catch (err) {
      setError(
        `${err.message || "Something went wrong."} Possible causes: backend not running, CORS blocked, or endpoint mismatch.`
      );
      setStatusText("");
    } finally {
      setLoading(false);
    }
  };

  const runPassive = async () => {
    if (!audioFile) {
      setError("Please select an audio file first.");
      return;
    }

    setLoading(true);
    setError("");
    setResult(null);
    setStatusText("Uploading & Analyzing audio...");

    try {
      const formData = new FormData();
      formData.append("audio", audioFile);
      formData.append("domain", DEFAULT_DOMAIN);
      const data = await requestWithFallback("/api/agent/passive", {
        method: "POST",
        body: formData,
      });
      setResult(data);
      setStatusText("Audio analysis complete");
    } catch (err) {
      setError(
        `${err.message || "Something went wrong."} Possible causes: backend not running, CORS blocked, or endpoint mismatch.`
      );
      setStatusText("");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-900 text-white">
      <div className="pointer-events-none fixed inset-0 overflow-hidden">
        <div className="absolute -top-24 -left-24 h-96 w-96 rounded-full bg-cyan-500/20 blur-3xl" />
        <div className="absolute top-1/4 -right-24 h-96 w-96 rounded-full bg-emerald-500/20 blur-3xl" />
        <div className="absolute bottom-0 left-1/3 h-80 w-80 rounded-full bg-pink-500/20 blur-3xl" />
      </div>

      <main className="relative z-10 mx-auto max-w-6xl px-6 py-10">
        <section className="mb-8 rounded-2xl border border-white/10 bg-white/5 p-8 backdrop-blur-md shadow-[0_0_40px_rgba(34,211,238,0.15)]">
          <p className="mb-3 inline-flex items-center gap-2 rounded-full border border-cyan-400/30 bg-cyan-400/10 px-3 py-1 text-xs text-cyan-300">
            <span>⚡</span>
            AI Workflow Engine
          </p>
          <h1 className="bg-gradient-to-r from-cyan-300 via-emerald-300 to-pink-300 bg-clip-text text-4xl font-black tracking-tight text-transparent md:text-6xl">
            OmniVoice Engine
          </h1>
          <p className="mt-3 text-lg text-slate-300">Dual-Mode Conversational OS</p>
        </section>

        <section className="grid gap-5 md:grid-cols-2">
          <button
            disabled={loading}
            onClick={() => setMode("autonomous")}
            className={`rounded-2xl border p-6 text-left transition-all ${
              mode === "autonomous"
                ? "border-cyan-400/70 bg-cyan-400/10 shadow-[0_0_30px_rgba(34,211,238,0.35)]"
                : "border-white/10 bg-white/5 hover:border-cyan-300/40 hover:bg-white/10"
            } ${loading ? "cursor-not-allowed opacity-70" : ""}`}
          >
            <div className="mb-2 text-3xl">🎙️</div>
            <h2 className="text-xl font-bold">Autonomous Agent</h2>
            <p className="mt-1 text-sm text-slate-300">
              Live mic session, backend-driven conversation flow, instant PDF generation.
            </p>
          </button>

          <button
            disabled={loading}
            onClick={() => setMode("passive")}
            className={`rounded-2xl border p-6 text-left transition-all ${
              mode === "passive"
                ? "border-emerald-400/70 bg-emerald-400/10 shadow-[0_0_30px_rgba(16,185,129,0.35)]"
                : "border-white/10 bg-white/5 hover:border-emerald-300/40 hover:bg-white/10"
            } ${loading ? "cursor-not-allowed opacity-70" : ""}`}
          >
            <div className="mb-2 text-3xl">🎧</div>
            <h2 className="text-xl font-bold">Passive Listener</h2>
            <p className="mt-1 text-sm text-slate-300">
              Upload a recorded call, extract transcript + structured insights + PDF.
            </p>
          </button>
        </section>

        <section className="mt-6 rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur-md">
          {mode === "autonomous" ? (
            <div>
              <h3 className="text-lg font-semibold">Live Mic Interface</h3>
              <p className="mt-1 text-sm text-slate-300">Starts your backend live session pipeline.</p>
              <button
                onClick={runAutonomous}
                disabled={loading}
                className={`mt-5 inline-flex items-center gap-3 rounded-xl px-6 py-3 font-semibold transition ${
                  loading
                    ? "cursor-not-allowed bg-cyan-500/40"
                    : "bg-cyan-500 shadow-[0_0_30px_rgba(34,211,238,0.5)] hover:bg-cyan-400"
                }`}
              >
                <span className={loading ? "animate-pulse" : ""}>🎙️</span>
                Start Live Session (Mic)
              </button>
            </div>
          ) : (
            <div>
              <h3 className="text-lg font-semibold">Audio Upload Interface</h3>
              <p className="mt-1 text-sm text-slate-300">Upload pre-recorded conversation audio.</p>

              <div className="mt-4 flex flex-col gap-3 md:flex-row md:items-center">
                <input
                  type="file"
                  accept="audio/*"
                  disabled={loading}
                  onChange={(e) => setAudioFile(e.target.files?.[0] || null)}
                  className="block w-full rounded-lg border border-white/15 bg-slate-900/60 px-3 py-2 text-sm file:mr-4 file:rounded-md file:border-0 file:bg-emerald-500 file:px-3 file:py-2 file:text-sm file:font-semibold file:text-white hover:file:bg-emerald-400"
                />
                <button
                  onClick={runPassive}
                  disabled={loading}
                  className={`rounded-xl px-5 py-3 font-semibold transition ${
                    loading
                      ? "cursor-not-allowed bg-emerald-500/40"
                      : "bg-emerald-500 shadow-[0_0_30px_rgba(16,185,129,0.5)] hover:bg-emerald-400"
                  }`}
                >
                  Analyze Audio
                </button>
              </div>
            </div>
          )}
        </section>

        {loading && (
          <section className="mt-6 rounded-xl border border-cyan-400/30 bg-cyan-500/10 p-4">
            <div className="flex items-center gap-3">
              <div className="h-5 w-5 animate-spin rounded-full border-2 border-cyan-200 border-t-transparent" />
              <p className="font-medium text-cyan-200">{statusText || "Processing..."}</p>
            </div>
          </section>
        )}

        {error && (
          <section className="mt-6 rounded-xl border border-rose-400/30 bg-rose-500/10 p-4">
            <div className="flex items-start gap-3">
              <div className="text-xl">⚠️</div>
              <div>
                <p className="font-semibold text-rose-200">Request Failed</p>
                <p className="mt-1 whitespace-pre-wrap text-sm text-rose-100/90">{error}</p>
              </div>
            </div>
          </section>
        )}

        {result && (
          <section className="mt-6 rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur-md">
            <h3 className="mb-4 text-xl font-bold">Results</h3>

            {result?.pdf_url ? (
              <a
                href={result.pdf_url}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-2 rounded-xl bg-emerald-500 px-5 py-3 font-semibold text-white shadow-[0_0_30px_rgba(16,185,129,0.45)] transition hover:bg-emerald-400"
              >
                <span>📄</span>
                Download Generated PDF
              </a>
            ) : null}

            {result?.transcript ? (
              <div className="mt-5">
                <p className="mb-2 text-sm uppercase tracking-wider text-slate-400">Transcript</p>
                <div className="max-h-40 overflow-auto whitespace-pre-wrap rounded-lg border border-white/10 bg-slate-950/60 p-3 text-sm text-slate-200">
                  {result.transcript}
                </div>
              </div>
            ) : null}

            <div className="mt-5">
              <p className="mb-2 text-sm uppercase tracking-wider text-slate-400">Extracted Data (JSON)</p>
              <pre className="max-h-96 overflow-auto rounded-lg border border-cyan-400/20 bg-slate-950/80 p-4 text-sm text-cyan-200">
                {prettyJson || "{}"}
              </pre>
            </div>
          </section>
        )}
      </main>
    </div>
  );
}