import { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { analyze, transcribe } from "../api/client";

export default function Active() {
  const nav = useNavigate();
  const location = useLocation();

  const domain = location.state?.domain || location.state?.schema?.domain || "healthcare";
  const mode = location.state?.mode || "conversational";
  const schema = location.state?.schema || null;

  const [step, setStep] = useState("idle");
  const [sessionId, setSessionId] = useState("");
  const [error, setError] = useState("");

  const startListening = async () => {
    try {
      setError("");
      setStep("processing");

      const data = await transcribe({ mode, domain });
      setSessionId(data.session_id);
      setStep("ready");
    } catch (err) {
      setError(err.message || "Failed to start active listening flow");
      setStep("idle");
    }
  };

  const goAnalyze = async () => {
    try {
      setStep("analyzing");

      const data = await analyze({ session_id: sessionId, domain });

      nav("/result", {
        state: {
          session_id: data.session_id,
          extracted_data: data.extracted_data,
          transcript: "",
          domain,
          mode,
          schema,
        },
      });
    } catch (err) {
      setError(err.message || "Failed to analyze session");
      setStep("ready");
    }
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        background:
          "radial-gradient(circle at 50% 10%, rgba(34,211,238,0.08), transparent 28%), #020617",
        color: "#e6edf7",
        fontFamily: "Plus Jakarta Sans, sans-serif",
      }}
    >
      <div
        style={{
          height: 84,
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "0 40px",
          borderBottom: "1px solid rgba(34,211,238,0.10)",
          background: "rgba(2,6,23,0.72)",
          backdropFilter: "blur(12px)",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
          <button
            onClick={() => nav("/mode")}
            style={{
              width: 42,
              height: 42,
              borderRadius: 12,
              border: "1px solid rgba(148,163,184,0.18)",
              background: "rgba(255,255,255,0.02)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "#94a3b8",
              fontSize: 20,
              cursor: "pointer",
            }}
          >
            ←
          </button>

          <div
            style={{
              fontSize: 28,
              fontWeight: 700,
              background: "linear-gradient(to right, #22d3ee, #10b981)",
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
            }}
          >
            Active Listening
          </div>

          <div
            style={{
              height: 34,
              padding: "0 14px",
              borderRadius: 999,
              border: "1px solid rgba(34,211,238,0.28)",
              display: "flex",
              alignItems: "center",
              color: "#9fe8f3",
              fontSize: 13,
              fontFamily: "JetBrains Mono, monospace",
              background: "rgba(34,211,238,0.05)",
            }}
          >
            {schema?.display_name || domain}
          </div>
        </div>

        <div
          style={{
            fontSize: 13,
            color:
              step === "analyzing"
                ? "#22d3ee"
                : step === "ready"
                ? "#10b981"
                : step === "processing"
                ? "#22d3ee"
                : "#7f8ea8",
            fontFamily: "JetBrains Mono, monospace",
          }}
        >
          {step === "idle"
            ? "Pending"
            : step === "processing"
            ? "Listening..."
            : step === "analyzing"
            ? "Analyzing..."
            : "Ready"}
        </div>
      </div>

      <div
        style={{
          padding: "34px 40px 40px",
          display: "grid",
          gridTemplateColumns: "420px 1fr",
          gap: 28,
        }}
      >
        <div
          style={{
            background: "rgba(15,23,42,0.88)",
            border: "1px solid rgba(34,211,238,0.18)",
            borderRadius: 24,
            padding: "36px 28px",
            minHeight: 390,
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <div
            style={{
              width: 168,
              height: 168,
              borderRadius: 999,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              background:
                step === "processing" || step === "analyzing"
                  ? "radial-gradient(circle, rgba(34,211,238,0.18), rgba(34,211,238,0.06))"
                  : "rgba(148,163,184,0.05)",
              border:
                step === "processing" || step === "analyzing"
                  ? "1px solid rgba(34,211,238,0.40)"
                  : "1px solid rgba(148,163,184,0.18)",
              boxShadow:
                step === "processing" || step === "analyzing"
                  ? "0 0 44px rgba(34,211,238,0.22)"
                  : "none",
              fontSize: 66,
              color:
                step === "processing" || step === "analyzing"
                  ? "#22d3ee"
                  : "#8da0bc",
            }}
          >
            🎙️
          </div>

          <div
            style={{
              marginTop: 30,
              fontSize: 30,
              fontWeight: 700,
              textAlign: "center",
            }}
          >
            {step === "idle"
              ? "Ready to Listen"
              : step === "processing"
              ? "Listening..."
              : step === "analyzing"
              ? "Analyzing..."
              : "Ready for Review"}
          </div>

          <div
            style={{
              marginTop: 12,
              fontSize: 16,
              lineHeight: 1.6,
              textAlign: "center",
              color: "#7f8ea8",
              maxWidth: 280,
            }}
          >
            {step === "idle"
              ? "Start listening to begin voice capture and backend analysis."
              : step === "processing"
              ? "OmniVoice is capturing the active session."
              : step === "analyzing"
              ? "Backend is analyzing the captured session."
              : "Session captured successfully. Proceed to review extracted output."}
          </div>

          {error ? (
            <div style={{ marginTop: 16, color: "#f87171", textAlign: "center" }}>
              {error}
            </div>
          ) : null}

          {step === "idle" && (
            <button
              onClick={startListening}
              style={{
                marginTop: 26,
                padding: "15px 26px",
                borderRadius: 12,
                border: "none",
                background: "#22d3ee",
                color: "#03111d",
                fontWeight: 700,
                fontSize: 15,
                cursor: "pointer",
                boxShadow: "0 0 28px rgba(34,211,238,0.35)",
              }}
            >
              Start Listening
            </button>
          )}

          {step === "ready" && (
            <button
              onClick={goAnalyze}
              style={{
                marginTop: 26,
                padding: "15px 26px",
                borderRadius: 12,
                border: "none",
                background: "#10b981",
                color: "#03111d",
                fontWeight: 700,
                fontSize: 15,
                cursor: "pointer",
                boxShadow: "0 0 28px rgba(16,185,129,0.25)",
              }}
            >
              Proceed to Review →
            </button>
          )}
        </div>

        <div
          style={{
            display: "flex",
            flexDirection: "column",
            gap: 24,
          }}
        >
          <div
            style={{
              background: "rgba(15,23,42,0.88)",
              border: "1px solid rgba(34,211,238,0.18)",
              borderRadius: 24,
              padding: "28px 24px",
              minHeight: 220,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            {step === "processing" || step === "analyzing" ? (
              <div
                style={{
                  display: "flex",
                  alignItems: "end",
                  gap: 8,
                  height: 76,
                }}
              >
                {[28, 46, 34, 52, 66, 40, 56, 74, 42, 58, 32, 48].map((h, i) => (
                  <div
                    key={i}
                    style={{
                      width: 10,
                      height: h,
                      borderRadius: 999,
                      background:
                        "linear-gradient(180deg, rgba(34,211,238,1), rgba(34,211,238,0.32))",
                      boxShadow: "0 0 12px rgba(34,211,238,0.28)",
                    }}
                  />
                ))}
              </div>
            ) : (
              <div
                style={{
                  color: "#7f8ea8",
                  fontSize: 15,
                  textAlign: "center",
                }}
              >
                Waveform visualization will appear while session capture is active
              </div>
            )}
          </div>

          <div
            style={{
              background: "rgba(15,23,42,0.88)",
              border: "1px solid rgba(34,211,238,0.18)",
              borderRadius: 24,
              padding: "28px",
              minHeight: 170,
              display: "flex",
              flexDirection: "column",
              justifyContent: "center",
            }}
          >
            <div
              style={{
                fontSize: 20,
                fontWeight: 700,
                marginBottom: 10,
              }}
            >
              Session Status
            </div>

            <div
              style={{
                color: "#7f8ea8",
                fontSize: 15,
                lineHeight: 1.7,
              }}
            >
              Domain: {domain}
              <br />
              Mode: {mode}
              <br />
              Session ID: {sessionId || "Not created yet"}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}